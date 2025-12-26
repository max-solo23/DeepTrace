from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import create_planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from backend.core import (
    ResearchMode,
    validate_source_count,
    PerformanceTracker,
    retry_with_backoff,
    calculate_confidence,
    get_confidence_label,
)
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
    """

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
        # Initialize performance tracker
        tracker = PerformanceTracker(mode)
        tracker.start()

        trace_id = gen_trace_id()

        try:
            with trace("Research trace", trace_id=trace_id):
                print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
                yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

                logger.info(f"Starting research for query: {query} in {mode.value.upper()} mode")
                print(f"[RESEARCH] Starting research in {mode.value.upper()} mode...")
                yield f"Starting {mode.value.upper()} mode research..."

                # Planning phase with retry
                tracker.start_planning()
                search_plan = await self._plan_searches_with_retry(query, mode)
                tracker.end_planning()

                if search_plan is None:
                    # Planning failed completely - return error report
                    logger.error("Planning failed after retries")
                    yield "Planning failed after retries. Returning error report."
                    error_report = self._create_error_report(
                        query,
                        "Failed to plan research searches",
                        []
                    )
                    yield error_report.markdown_report
                    return

                yield f"Searches planned ({len(search_plan.searches)} searches), starting to search..."

                # Search phase with partial results handling
                tracker.start_searching()
                search_results = await self._perform_searches_resilient(search_plan, mode)
                tracker.end_searching()

                if not search_results:
                    # No searches succeeded - return error report
                    logger.error("All searches failed")
                    yield "All searches failed. Returning error report."
                    error_report = self._create_error_report(
                        query,
                        "All search attempts failed",
                        []
                    )
                    yield error_report.markdown_report
                    return

                yield f"Searches complete ({len(search_results)}/{len(search_plan.searches)} successful), writing report..."

                # Writing phase with retry
                tracker.start_writing()
                report = await self._write_report_with_retry(query, search_results)
                tracker.end_writing()

                if report is None:
                    # Report generation failed - return structured error
                    logger.error("Report generation failed after retries")
                    yield "Report generation failed after retries. Returning partial results."
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
                yield f"Report written. Confidence: {confidence_label} ({report.confidence_score:.2f})"

                # Email phase (optional, failure doesn't block)
                email_sent, email_messages = await self.send_email(report)
                for message in email_messages:
                    yield message

                # Complete performance tracking
                tracker.end()

                if email_sent:
                    yield "Research complete."
                else:
                    yield "Research complete (email not sent)."

                yield report.markdown_report

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

    async def plan_searches(self, query: str, mode: ResearchMode) -> WebSearchPlan:
        """Plan the searches to perform for the query.

        Args:
            query: The research query
            mode: Research mode to configure search count

        Returns:
            WebSearchPlan with validated search count
        """
        print(f"[PLANNING] Planning searches for {mode.value} mode...")

        # Create mode-specific planner agent
        planner_agent = create_planner_agent(mode)

        result = await Runner.run(
            planner_agent,
            f"Query: {query}"
        )

        plan = result.final_output_as(WebSearchPlan)
        num_searches = len(plan.searches)

        print(f"[PLANNING] Planner proposed {num_searches} searches")

        # Validate and potentially limit search count
        validated_count = validate_source_count(num_searches, mode)

        # If we need to truncate, do so
        if validated_count < num_searches:
            print(f"[PLANNING] Truncating from {num_searches} to {validated_count} searches")
            plan.searches = plan.searches[:validated_count]

        print(f"[PLANNING] Will perform {len(plan.searches)} searches")
        return plan

    async def perform_searches(self, search_plan: WebSearchPlan, mode: ResearchMode) -> list[str]:
        """Perform the searches for the query.

        Args:
            search_plan: The validated search plan
            mode: Research mode (for logging)

        Returns:
            List of search result summaries
        """
        num_searches = len(search_plan.searches)
        print(f"[SEARCH] Starting {num_searches} searches in {mode.value} mode...")

        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []

        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"[SEARCH] Progress: {num_completed}/{len(tasks)} completed")

        successful_searches = len(results)
        failed_searches = num_searches - successful_searches

        print(f"[SEARCH] Completed: {successful_searches} successful, {failed_searches} failed")

        # Warn if we got too few results
        if successful_searches == 0:
            print("[SEARCH] ERROR: All searches failed. Report quality will be severely impacted.")
        elif failed_searches > 0:
            print(f"[SEARCH] WARNING: {failed_searches} searches failed. Report may be incomplete.")

        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """Perform a single search.

        Args:
            item: Search item with query and reason

        Returns:
            Search result summary or None if failed
        """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception as e:
            print(f"[SEARCH] Search failed for '{item.query}': {type(e).__name__}")
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """Write the final research report.

        Args:
            query: Original research query
            search_results: List of search summaries

        Returns:
            ReportData with markdown report
        """
        print(f"[WRITER] Synthesizing report from {len(search_results)} sources...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )
        print("[WRITER] Report completed")
        return result.final_output_as(ReportData)

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

    async def _perform_searches_resilient(self, search_plan: WebSearchPlan, mode: ResearchMode) -> list[str]:
        """
        Perform searches with resilience - continues with partial results.

        Returns:
            List of successful search results (may be partial)
        """
        num_searches = len(search_plan.searches)
        logger.info(f"Starting {num_searches} searches in {mode.value} mode...")
        print(f"[SEARCH] Starting {num_searches} searches in {mode.value} mode...")

        num_completed = 0
        tasks = [asyncio.create_task(self._search_with_retry(item)) for item in search_plan.searches]
        results = []

        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
                logger.info(f"Search successful (total successful: {len(results)})")
            else:
                logger.warning("Search failed after retries")

            num_completed += 1
            print(f"[SEARCH] Progress: {num_completed}/{len(tasks)} completed ({len(results)} successful)")

        successful_searches = len(results)
        failed_searches = num_searches - successful_searches

        logger.info(f"Finished searching. {successful_searches}/{num_searches} successful")
        print(f"[SEARCH] Completed: {successful_searches} successful, {failed_searches} failed")

        # Warn if we got too few results
        if successful_searches == 0:
            logger.error("All searches failed. Report quality will be severely impacted.")
            print("[SEARCH] ERROR: All searches failed. Report quality will be severely impacted.")
        elif failed_searches > 0:
            logger.warning(f"{failed_searches} searches failed. Report may be incomplete.")
            print(f"[SEARCH] WARNING: {failed_searches} searches failed. Report may be incomplete.")

        return results

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
