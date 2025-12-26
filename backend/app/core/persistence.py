"""Database persistence layer for research reports."""

import logging
from backend.app.core.types import ResearchMode
from backend.app.core.status_reporter import StatusReporter
from backend.app.agents.writer_agent import ReportData
from backend.app.data import save_report


logger = logging.getLogger(__name__)


class DatabasePersistence:
    """Handles database operations for research reports."""

    def __init__(self, logger_instance: logging.Logger = None):
        """
        Initialize database persistence handler.

        Args:
            logger_instance: Optional logger instance (defaults to module logger)
        """
        self.logger = logger_instance or logger

    def save_report_safely(
        self,
        query: str,
        mode: ResearchMode,
        report: ReportData,
        status_reporter: StatusReporter
    ) -> str | None:
        """
        Save report to database with error handling.

        Args:
            query: The research query
            mode: Research mode (QUICK or DEEP)
            report: The completed report
            status_reporter: Status reporter for updating user

        Returns:
            str: Report ID if successful, None if failed
        """
        status_reporter.add_database_saving()

        try:
            report_dict = self._convert_to_dict(query, mode, report)
            report_id = save_report(report_dict)

            self.logger.info(f"Report saved to database with ID: {report_id}")
            return report_id

        except Exception as db_error:
            # Log error but don't fail the research
            self.logger.error(
                f"Failed to save report to database: "
                f"{type(db_error).__name__}: {str(db_error)}"
            )
            return None

    def _convert_to_dict(
        self,
        query: str,
        mode: ResearchMode,
        report: ReportData
    ) -> dict:
        """
        Convert ReportData to database dictionary.

        Args:
            query: The research query
            mode: Research mode
            report: The report data to convert

        Returns:
            dict: Database-compatible report dictionary
        """
        return {
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
