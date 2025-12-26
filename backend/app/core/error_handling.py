"""Error report generation for research pipeline failures."""

import logging
from backend.app.agents.writer_agent import ReportData


logger = logging.getLogger(__name__)


class ErrorReportGenerator:
    """Generates structured error reports for pipeline failures."""

    @staticmethod
    def create_planning_failure_report(query: str) -> ReportData:
        """
        Create error report for planning failure.

        Args:
            query: The original research query

        Returns:
            ReportData with error information
        """
        return ErrorReportGenerator._create_error_report(
            query,
            "Failed to plan research searches",
            []
        )

    @staticmethod
    def create_search_failure_report(query: str) -> ReportData:
        """
        Create error report for all searches failing.

        Args:
            query: The original research query

        Returns:
            ReportData with error information
        """
        return ErrorReportGenerator._create_error_report(
            query,
            "All search attempts failed",
            []
        )

    @staticmethod
    def create_writing_failure_report(query: str, search_results: list[str]) -> ReportData:
        """
        Create error report for writing failure.

        Args:
            query: The original research query
            search_results: Search results that were retrieved before failure

        Returns:
            ReportData with error information and partial results
        """
        return ErrorReportGenerator._create_error_report(
            query,
            "Failed to generate structured report",
            search_results
        )

    @staticmethod
    def create_unexpected_error_report(query: str, error: Exception) -> ReportData:
        """
        Create error report for unexpected errors.

        Args:
            query: The original research query
            error: The exception that was caught

        Returns:
            ReportData with error information
        """
        return ErrorReportGenerator._create_error_report(
            query,
            f"Unexpected system error: {type(error).__name__}",
            []
        )

    @staticmethod
    def _create_error_report(
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
