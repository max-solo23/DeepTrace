from agents import Runner, trace, gen_trace_id
from backend.app.agents.search_agent import search_agent
from backend.app.agents.planner_agent import create_planner_agent, WebSearchItem, WebSearchPlan
from backend.app.agents.writer_agent import writer_agent, ReportData
from backend.app.agents.email_agent import email_agent
from backend.app.core import (
    ResearchMode,
    validate_source_count,
    PerformanceTracker,
    calculate_confidence,
    get_confidence_label,
)
from backend.app.core.retry import retry_with_backoff, get_retry_config
from backend.app.core.status_reporter import StatusReporter
from backend.app.core.error_handling import ErrorReportGenerator
from backend.app.core.persistence import DatabasePersistence
import asyncio
import os
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SEARCH_TIMEOUT_SECONDS = 60


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
        """
        self._stop_requested.clear()
        tracker = PerformanceTracker(mode)
        tracker.start()
        trace_id = gen_trace_id()

        try:
            with trace("Research trace", trace_id=trace_id):
                trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
                print(f"View trace: {trace_url}")

                status_reporter = StatusReporter(mode, trace_url)
                status_reporter.add_starting()
                yield status_reporter.get_current_status()

                logger.info(f"Starting research for query: {query} in {mode.value.upper()} mode")

                # === PLANNING PHASE ===
                self._check_if_stopped()
                status_reporter.add_planning_start()
                yield status_reporter.get_current_status()

                search_plan = await self._run_planning_phase(query, mode, tracker)

                if search_plan is None:
                    logger.error("Planning failed after retries")
                    status_reporter.add_error("Planning failed after retries")
                    yield status_reporter.get_current_status()
                    yield ErrorReportGenerator.create_planning_failure_report(query).markdown_report
                    return

                status_reporter.add_planning_complete(len(search_plan.searches), search_plan.searches)
                yield status_reporter.get_current_status()

                # === SEARCH PHASE ===
                self._check_if_stopped()
                status_reporter.add_search_start()
                yield status_reporter.get_current_status()

                tracker.start_searching()
                num_searches = len(search_plan.searches)
                logger.info(f"Starting {num_searches} searches in {mode.value} mode...")

                tasks = [asyncio.create_task(self._search_with_retry(item)) for item in search_plan.searches]
                search_results: list[str] = []
                num_completed = 0

                try:
                    for task in asyncio.as_completed(tasks):
                        self._check_if_stopped()
                        result = await task
                        num_completed += 1
                        success = result is not None

                        if result is not None:
                            search_results.append(result)
                            logger.info(f"Search successful (total: {len(search_results)})")
                        else:
                            logger.warning("Search failed after retries")

                        status_reporter.add_search_progress(num_completed, num_searches, len(search_results), success)
                        yield status_reporter.get_current_status()

                except asyncio.CancelledError:
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
                    raise

                tracker.end_searching()

                if not search_results:
                    logger.error("All searches failed")
                    status_reporter.add_error("All searches failed")
                    yield status_reporter.get_current_status()
                    yield ErrorReportGenerator.create_search_failure_report(query).markdown_report
                    return

                status_reporter.add_search_complete(len(search_results), num_searches)
                yield status_reporter.get_current_status()

                # === WRITING PHASE ===
                self._check_if_stopped()
                status_reporter.add_writing_start()
                yield status_reporter.get_current_status()

                report = await self._run_writing_phase(query, search_results, tracker)

                if report is None:
                    logger.error("Report generation failed after retries")
                    status_reporter.add_error("Report generation failed after retries")
                    yield status_reporter.get_current_status()
                    yield ErrorReportGenerator.create_writing_failure_report(query, search_results).markdown_report
                    return

                confidence_label = get_confidence_label(report.confidence_score)
                logger.info(f"Report completed with confidence: {confidence_label} ({report.confidence_score:.2f})")
                status_reporter.add_writing_complete(report.confidence_score, confidence_label)
                yield status_reporter.get_current_status()

                # === PERSISTENCE PHASE ===
                self._check_if_stopped()
                report_id = await self._run_persistence_phase(query, mode, report, status_reporter)

                if report_id:
                    status_reporter.add_database_saved(report_id)
                else:
                    status_reporter.add_database_error("Database error")
                yield status_reporter.get_current_status()

                # === EMAIL PHASE ===
                self._check_if_stopped()
                if os.environ.get("SENDGRID_API_KEY"):
                    status_reporter.add_email_sending()
                    yield status_reporter.get_current_status()

                email_sent, _ = await self.send_email(report)
                if email_sent:
                    status_reporter.add_email_success()
                elif os.environ.get("SENDGRID_API_KEY"):
                    status_reporter.add_email_failure()

                tracker.end()
                status_reporter.add_completion()
                yield status_reporter.get_current_status()
                yield report.markdown_report

        except asyncio.CancelledError:
            logger.info("Research cancelled by user request - showing partial results")
            status_reporter.add_stopped_by_user()
            yield status_reporter.get_current_status()

        except Exception as exc:
            logger.error(f"Unexpected error in research pipeline: {type(exc).__name__}: {str(exc)}")
            yield f"Unexpected error occurred: {type(exc).__name__}"
            error_report = ErrorReportGenerator.create_unexpected_error_report(query, exc)
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
            return False, ["SENDGRID_API_KEY not set; skipping email."]

        try:
            logger.info("Attempting to send email...")
            messages = ["Sending email..."]
            await Runner.run(
                email_agent,
                report.markdown_report,
            )
            logger.info("Email sent successfully")
            messages.append("Email sent.")
            return True, messages
        except Exception as exc:
            logger.error(f"Email failed: {type(exc).__name__}: {str(exc)}")
            return False, [f"Email failed ({type(exc).__name__}). Check SendGrid config."]

    # ========== Pipeline Phase Methods ==========

    async def _run_planning_phase(
        self,
        query: str,
        mode: ResearchMode,
        tracker: PerformanceTracker
    ) -> WebSearchPlan | None:
        """Execute the planning phase.

        Returns:
            WebSearchPlan if successful, None if failed
        """
        tracker.start_planning()
        search_plan = await self._plan_searches_with_retry(query, mode)
        tracker.end_planning()
        return search_plan

    async def _run_writing_phase(
        self,
        query: str,
        search_results: list[str],
        tracker: PerformanceTracker
    ) -> ReportData | None:
        """Execute the writing phase.

        Returns:
            ReportData if successful, None if failed
        """
        tracker.start_writing()
        report = await self._write_report_with_retry(query, search_results)
        tracker.end_writing()

        if report:
            report.confidence_score = calculate_confidence(len(search_results), search_results)

        return report

    async def _run_persistence_phase(
        self,
        query: str,
        mode: ResearchMode,
        report: ReportData,
        status_reporter: StatusReporter
    ) -> str | None:
        """Execute the database persistence phase.

        Returns:
            Report ID if saved successfully, None otherwise
        """
        db_persistence = DatabasePersistence(logger)
        return db_persistence.save_report_safely(query, mode, report, status_reporter)

    # ========== Resilient Methods with Retry Logic ==========

    async def _plan_searches_with_retry(self, query: str, mode: ResearchMode) -> WebSearchPlan | None:
        """
        Plan searches with retry logic.

        Returns:
            WebSearchPlan if successful, None if all attempts fail
        """
        logger.info(f"Planning searches with retry logic for {mode.value} mode...")

        async def _plan():
            planner_agent = create_planner_agent(mode)
            result = await Runner.run(
                planner_agent,
                f"Query: {query}"
            )
            plan = result.final_output_as(WebSearchPlan)

            # Validate and potentially limit search count
            num_searches = len(plan.searches)
            validated_count = validate_source_count(num_searches, mode)

            # If we need to truncate, do so
            if validated_count < num_searches:
                logger.info(f"Truncating from {num_searches} to {validated_count} searches")
                plan.searches = plan.searches[:validated_count]

            return plan

        config = get_retry_config("planning")
        search_plan = await retry_with_backoff(
            _plan,
            max_attempts=config.max_attempts,
            base_delay=config.base_delay
        )

        if search_plan:
            logger.info(f"Successfully planned {len(search_plan.searches)} searches")
        else:
            logger.error("Failed to plan searches after all retry attempts")

        return search_plan


    async def _search_with_retry(self, item: WebSearchItem, timeout: int = SEARCH_TIMEOUT_SECONDS) -> str | None:
        """
        Perform a single search with retry logic and timeout.

        Args:
            item: Search item to execute
            timeout: Maximum seconds to wait for this search

        Returns:
            Search result string if successful, None if timeout or failure
        """
        async def _search():
            input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
            result = await Runner.run(
                search_agent,
                input_text,
            )
            return str(result.final_output)

        config = get_retry_config("search")

        try:
            # Wrap retry logic with timeout to prevent hanging
            return await asyncio.wait_for(
                retry_with_backoff(
                    _search,
                    max_attempts=config.max_attempts,
                    base_delay=config.base_delay
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            # Graceful degradation - log and continue with other searches
            logger.warning(f"Search timed out after {timeout}s:  {item.query}")
            return None

    async def _write_report_with_retry(self, query: str, search_results: list[str]) -> ReportData | None:
        """
        Write report with retry logic.

        Returns:
            ReportData if successful, None if all attempts fail
        """
        logger.info(f"Writing report with retry logic from {len(search_results)} sources...")

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

        config = get_retry_config("writing")
        report = await retry_with_backoff(
            _write,
            max_attempts=config.max_attempts,
            base_delay=config.base_delay
        )

        if report:
            logger.info("Successfully generated report")
        else:
            logger.error("Failed to generate report after all retry attempts")

        return report
