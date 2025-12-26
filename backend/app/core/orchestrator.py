from agents import Runner, trace, gen_trace_id
from backend.app.agents.search_agent import search_agent
from backend.app.agents.planner_agent import create_planner_agent, WebSearchItem, WebSearchPlan
from backend.app.agents.writer_agent import writer_agent, ReportData
from backend.app.agents.email_agent import email_agent
from backend.app.core import (
    ResearchMode,
    validate_source_count,
    PerformanceTracker,
    retry_with_backoff,
    calculate_confidence,
    get_confidence_label,
)
from backend.app.data import init_db, save_report
import asyncio
import os
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ResearchManager:
    """
    Orchestrates the deep research process with resilience features.

    Features:
    - Retry logic with exponential backoff
    - Partial results handling (continues with available data)
    - Graceful degradation (never fails completely)
    - Comprehensive logging
    - Confidence scoring
    - Stop button support (immediate cancellation)
    """

    def __init__(self):
        self._stop_requested = asyncio.Event()

    def request_stop(self) -> None:
        """Request that the current research operation stop at the next checkpoint."""
        self._stop_requested.set()
        logger.info("Stop requested by user - will halt at next checkpoint")

    def _check_if_stopped(self) -> None:
        """Check if stop was requested and raise CancelledError if so."""
        if self._stop_requested.is_set():
            logger.info("Research stopped by user at checkpoint")
            raise asyncio.CancelledError("Stopped by user")

    async def run(self, query: str, mode: ResearchMode = ResearchMode.QUICK):
        """Run the deep research process, yielding status updates and the final report.

        Args:
            query: The research query to investigate
            mode: Research mode (QUICK or DEEP) - defaults to QUICK

        Yields:
            Status messages and final markdown report

        Error Handling:
            - Planning failures: return partial report with error
            - Search failures: continue with successful searches
            - Writing failures: return structured error report
            - Email failures: log but don't block completion
        """
        # Reset stop flag for new run
        self._stop_requested.clear()

        # Initialize performance tracker
        tracker = PerformanceTracker(mode)
        tracker.start()

        # Accumulate status messages for running log
        status_log = []

        trace_id = gen_trace_id()

        try:
            with trace("Research trace", trace_id=trace_id):
                trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
                print(f"View trace: {trace_url}")

                # Build header with trace link
                header = f"""# 🔬 Deep Research - {mode.value.upper()} Mode

**OpenAI Trace:** [View detailed agent trace]({trace_url})

---

## 📊 Progress Log

"""
                status_log.append("🚀 **Starting research...**")
                yield header + "\n".join(status_log)

                logger.info(f"Starting research for query: {query} in {mode.value.upper()} mode")
                print(f"[RESEARCH] Starting research in {mode.value.upper()} mode...")

                # CHECKPOINT: Before planning
                self._check_if_stopped()

                # Planning phase with retry
                status_log.append("🧠 **Planning searches...**")
                yield header + "\n".join(status_log)

                tracker.start_planning()
                search_plan = await self._plan_searches_with_retry(query, mode)
                tracker.end_planning()

                if search_plan is None:
                    # Planning failed completely - return error report
                    logger.error("Planning failed after retries")
                    status_log.append("❌ **Planning failed after retries**")
                    yield header + "\n".join(status_log)
                    error_report = self._create_error_report(
                        query,
                        "Failed to plan research searches",
                        []
                    )
                    yield error_report.markdown_report
                    return

                # Show the planned searches with reasoning
                status_log.append(f"✅ **Planning complete** - {len(search_plan.searches)} searches planned")
                status_log.append("")
                status_log.append("### 📋 Search Plan:")
                status_log.append("")
                for i, search_item in enumerate(search_plan.searches, 1):
                    status_log.append(f"**{i}. {search_item.query}**")
                    status_log.append(f"   *Reason:* {search_item.reason}")
                    status_log.append("")
                status_log.append("---")
                status_log.append("")
                yield header + "\n".join(status_log)

                # CHECKPOINT: After planning, before searching
                self._check_if_stopped()

                # Search phase with partial results handling
                status_log.append("🔍 **Starting searches...**")
                status_log.append("")
                yield header + "\n".join(status_log)

                tracker.start_searching()

                # Perform searches with real-time updates
                num_searches = len(search_plan.searches)
                logger.info(f"Starting {num_searches} searches in {mode.value} mode...")
                print(f"[SEARCH] Starting {num_searches} searches in {mode.value} mode...")

                num_completed = 0
                tasks = [asyncio.create_task(self._search_with_retry(item)) for item in search_plan.searches]
                search_results = []

                try:
                    for task in asyncio.as_completed(tasks):
                        self._check_if_stopped()

                        result = await task
                        num_completed += 1

                        if result is not None:
                            search_results.append(result)
                            logger.info(f"Search successful (total successful: {len(search_results)})")
                            status_log.append(f"   ✓ Search {num_completed}/{num_searches} completed - {len(search_results)} successful so far")
                        else:
                            logger.warning("Search failed after retries")
                            status_log.append(f"   ✗ Search {num_completed}/{num_searches} failed")

                        print(f"[SEARCH] Progress: {num_completed}/{len(tasks)} completed ({len(search_results)} successful)")

                        # Yield updated status after each search completes
                        yield header + "\n".join(status_log)

                except asyncio.CancelledError:
                    # Stop requested - cancel all pending tasks to prevent resource leaks
                    logger.info("Stop requested - cancelling pending search tasks")
                    for task in tasks:
                        if not task.done():
                            task.cancel()

                    # Wait for all cancellations to complete
                    await asyncio.gather(*tasks, return_exceptions=True)
                    raise  # Re-raise to propagate cancellation

                tracker.end_searching()

                if not search_results:
                    # No searches succeeded - return error report
                    logger.error("All searches failed")
                    status_log.append("❌ **All searches failed**")
                    yield header + "\n".join(status_log)
                    error_report = self._create_error_report(
                        query,
                        "All search attempts failed",
                        []
                    )
                    yield error_report.markdown_report
                    return

                status_log.append("")
                status_log.append(f"✅ **Searches complete** - {len(search_results)}/{len(search_plan.searches)} successful")
                status_log.append("")
                status_log.append("---")
                status_log.append("")
                yield header + "\n".join(status_log)

                # CHECKPOINT: After searching, before writing
                self._check_if_stopped()

                # Writing phase with retry
                status_log.append("✍️ **Writing comprehensive report...**")
                yield header + "\n".join(status_log)

                tracker.start_writing()
                report = await self._write_report_with_retry(query, search_results)
                tracker.end_writing()

                if report is None:
                    # Report generation failed - return structured error
                    logger.error("Report generation failed after retries")
                    status_log.append("❌ **Report generation failed after retries**")
                    yield header + "\n".join(status_log)
                    error_report = self._create_error_report(
                        query,
                        "Failed to generate structured report",
                        search_results
                    )
                    yield error_report.markdown_report
                    return

                # Recalculate confidence score using our heuristic
                report.confidence_score = calculate_confidence(
                    len(search_results),
                    search_results
                )
                confidence_label = get_confidence_label(report.confidence_score)

                logger.info(f"Report completed with confidence: {confidence_label} ({report.confidence_score:.2f})")
                status_log.append(f"✅ **Report complete** - Confidence: {confidence_label} ({report.confidence_score:.2f})")
                status_log.append("")
                yield header + "\n".join(status_log)

                # CHECKPOINT: After writing, before database save
                self._check_if_stopped()

                # Save to database
                status_log.append("💾 **Saving to database...**")
                yield header + "\n".join(status_log)

                report_id = None
                try:
                    # Convert ReportData to dictionary for database
                    report_dict = {
                        "query": query,
                        "mode": mode.value,  # "quick" or "deep"
                        "summary": report.summary,
                        "goals": report.goals,
                        "methodology": report.methodology,
                        "findings": report.findings,
                        "competitors": report.competitors,
                        "risks": report.risks,
                        "opportunities": report.opportunities,
                        "recommendations": report.recommendations,
                        "confidence_score": report.confidence_score,
                    }

                    report_id = save_report(report_dict)
                    logger.info(f"Report saved to database with ID: {report_id}")
                    status_log.append(f"✅ **Saved to database** - Report ID: {report_id[:8]}...")
                    yield header + "\n".join(status_log)

                except Exception as db_error:
                    # Log error but don't fail the research
                    logger.error(f"Failed to save report to database: {type(db_error).__name__}: {str(db_error)}")
                    status_log.append(f"⚠️ **Database save failed** - {type(db_error).__name__}")
                    status_log.append("   *(Report still available but not persisted)*")
                    yield header + "\n".join(status_log)

                # CHECKPOINT: After database, before email
                self._check_if_stopped()

                # Email phase (optional, failure doesn't block)
                if os.environ.get("SENDGRID_API_KEY"):
                    status_log.append("📧 **Sending email...**")
                    yield header + "\n".join(status_log)

                email_sent, email_messages = await self.send_email(report)
                if email_sent:
                    status_log.append("✅ **Email sent successfully**")
                elif os.environ.get("SENDGRID_API_KEY"):
                    status_log.append("⚠️ **Email failed** (check configuration)")

                # Complete performance tracking
                tracker.end()

                status_log.append("")
                status_log.append("---")
                status_log.append("")
                status_log.append("## ✨ Research Complete!")
                status_log.append("")
                yield header + "\n".join(status_log)

                # Final yield: show the full report
                yield report.markdown_report

        except asyncio.CancelledError:
            # User requested stop - return gracefully with partial results
            logger.info("Research cancelled by user request - showing partial results")
            status_log.append("")
            status_log.append("---")
            status_log.append("")
            status_log.append("## ⚠️ Research Stopped by User")
            status_log.append("")
            status_log.append("Partial results shown above (if any). Results not saved to database.")
            yield header + "\n".join(status_log)
            return

        except Exception as exc:
            # Catch-all for unexpected errors - graceful degradation
            logger.error(f"Unexpected error in research pipeline: {type(exc).__name__}: {str(exc)}")
            yield f"Unexpected error occurred: {type(exc).__name__}"

            # Return a graceful error report
            error_report = self._create_error_report(
                query,
                f"Unexpected system error: {type(exc).__name__}",
                []
            )
            yield error_report.markdown_report

    async def send_email(self, report: ReportData) -> tuple[bool, list[str]]:
        """Send the report via email (optional).

        Args:
            report: The completed report

        Returns:
            Tuple of (success, messages)
        """
        if not os.environ.get("SENDGRID_API_KEY"):
            logger.info("SENDGRID_API_KEY not set; skipping email")
            print("[EMAIL] SENDGRID_API_KEY not set; skipping email.")
            return False, ["SENDGRID_API_KEY not set; skipping email."]

        try:
            logger.info("Attempting to send email...")
            print("[EMAIL] Sending report via email...")
            messages = ["Sending email..."]
            await Runner.run(
                email_agent,
                report.markdown_report,
            )
            logger.info("Email sent successfully")
            print("[EMAIL] Email sent successfully")
            messages.append("Email sent.")
            return True, messages
        except Exception as exc:
            logger.error(f"Email failed: {type(exc).__name__}: {str(exc)}")
            print(f"[EMAIL] Email failed: {type(exc).__name__}")
            return False, [f"Email failed ({type(exc).__name__}). Check SendGrid config."]

    # ========== Resilient Methods with Retry Logic ==========

    async def _plan_searches_with_retry(self, query: str, mode: ResearchMode) -> WebSearchPlan | None:
        """
        Plan searches with retry logic.

        Returns:
            WebSearchPlan if successful, None if all attempts fail
        """
        logger.info(f"Planning searches with retry logic for {mode.value} mode...")
        print(f"[PLANNING] Planning searches for {mode.value} mode...")

        async def _plan():
            planner_agent = create_planner_agent(mode)
            result = await Runner.run(
                planner_agent,
                f"Query: {query}"
            )
            plan = result.final_output_as(WebSearchPlan)

            # Validate and potentially limit search count
            num_searches = len(plan.searches)
            print(f"[PLANNING] Planner proposed {num_searches} searches")

            validated_count = validate_source_count(num_searches, mode)

            # If we need to truncate, do so
            if validated_count < num_searches:
                print(f"[PLANNING] Truncating from {num_searches} to {validated_count} searches")
                plan.searches = plan.searches[:validated_count]

            return plan

        search_plan = await retry_with_backoff(
            _plan,
            max_attempts=3,
            base_delay=1.0
        )

        if search_plan:
            logger.info(f"Successfully planned {len(search_plan.searches)} searches")
            print(f"[PLANNING] Will perform {len(search_plan.searches)} searches")
        else:
            logger.error("Failed to plan searches after all retry attempts")
            print("[PLANNING] Failed to plan searches")

        return search_plan


    async def _search_with_retry(self, item: WebSearchItem) -> str | None:
        """
        Perform a single search with retry logic.

        Returns:
            Search result string if successful, None if all attempts fail
        """
        async def _search():
            input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
            result = await Runner.run(
                search_agent,
                input_text,
            )
            return str(result.final_output)

        return await retry_with_backoff(
            _search,
            max_attempts=2,  # Fewer retries for individual searches
            base_delay=0.5
        )

    async def _write_report_with_retry(self, query: str, search_results: list[str]) -> ReportData | None:
        """
        Write report with retry logic.

        Returns:
            ReportData if successful, None if all attempts fail
        """
        logger.info(f"Writing report with retry logic from {len(search_results)} sources...")
        print(f"[WRITER] Synthesizing report from {len(search_results)} sources...")

        async def _write():
            input_text = (
                f"Original query: {query}\n\n"
                f"Number of sources: {len(search_results)}\n\n"
                f"Summarized search results:\n{search_results}"
            )
            result = await Runner.run(
                writer_agent,
                input_text,
            )
            return result.final_output_as(ReportData)

        report = await retry_with_backoff(
            _write,
            max_attempts=3,
            base_delay=1.0
        )

        if report:
            logger.info("Successfully generated report")
            print("[WRITER] Report completed")
        else:
            logger.error("Failed to generate report after all retry attempts")
            print("[WRITER] Failed to write report")

        return report

    def _create_error_report(
        self,
        query: str,
        error_message: str,
        partial_results: list[str]
    ) -> ReportData:
        """
        Create a structured error report when pipeline fails.

        This ensures we ALWAYS return something useful, even on failure.

        Args:
            query: The original query
            error_message: Description of what went wrong
            partial_results: Any search results that were retrieved

        Returns:
            ReportData with error information and partial results
        """
        logger.info(f"Creating error report: {error_message}")

        # Build partial findings if we have any results
        findings_text = "[Error occurred during research]\n\n"
        if partial_results:
            findings_text += "**Partial Results Retrieved:**\n\n"
            for i, result in enumerate(partial_results, 1):
                findings_text += f"{i}. {result}\n\n"
        else:
            findings_text += "No search results were retrieved before the error occurred."

        markdown_report = f"""# Research Report: {query}

## Error Notice

**Status:** Research pipeline encountered an error
**Error:** {error_message}
**Partial Results:** {'Yes' if partial_results else 'No'}

---

## Summary

This research attempt was unable to complete successfully due to a system error. {'Some partial results were retrieved and are included below.' if partial_results else 'No results were retrieved.'}

---

## Findings

{findings_text}

---

## Recommendations

- Retry the research query
- Simplify the query if it was complex
- Check system logs for detailed error information
- Contact support if the issue persists

---

*This is an automatically generated error report. The research pipeline failed gracefully to provide this structured output.*
"""

        return ReportData(
            summary=f"Research failed: {error_message}",
            goals=f"Attempted to research: {query}",
            methodology="Research pipeline encountered an error before completion",
            findings=findings_text,
            competitors="[Information not available due to error]",
            risks="System error prevented complete research execution",
            opportunities="Retry may succeed; consider query refinement",
            recommendations="Retry the query or contact support",
            confidence_score=0.0,
            markdown_report=markdown_report,
            follow_up_questions=[
                "Should the query be rephrased or simplified?",
                "Are there system issues affecting research execution?",
                "Would breaking the query into smaller parts help?"
            ]
        )
