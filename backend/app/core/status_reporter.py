"""Status reporting and streaming updates for research pipeline."""

from backend.app.core.types import ResearchMode
from backend.app.agents.planner_agent import WebSearchItem


class StatusReporter:
    """Manages status log and streaming updates for research pipeline."""

    def __init__(self, mode: ResearchMode, trace_url: str):
        """
        Initialize status reporter.

        Args:
            mode: Research mode (QUICK or DEEP)
            trace_url: OpenAI trace URL for debugging
        """
        self.mode = mode
        self.trace_url = trace_url
        self.status_log: list[str] = []
        self._header = self._build_header()

    def _build_header(self) -> str:
        """Build header with mode and trace link."""
        return f"""# 🔬 Deep Research - {self.mode.value.upper()} Mode

**OpenAI Trace:** [View detailed agent trace]({self.trace_url})

---

## 📊 Progress Log

"""

    def add(self, message: str) -> None:
        """Add a status message to the log."""
        self.status_log.append(message)

    def add_multiple(self, messages: list[str]) -> None:
        """Add multiple status messages to the log."""
        self.status_log.extend(messages)

    def get_current_status(self) -> str:
        """Get current status report with header and all logged messages."""
        return self._header + "\n".join(self.status_log)

    # ========== Phase-specific status methods ==========

    def add_starting(self) -> None:
        """Add research starting status."""
        self.add("🚀 **Starting research...**")

    def add_planning_start(self) -> None:
        """Add planning start status."""
        self.add("🧠 **Planning searches...**")

    def add_planning_complete(self, num_searches: int, searches: list[WebSearchItem]) -> None:
        """
        Add planning complete status with search plan details.

        Args:
            num_searches: Number of searches planned
            searches: List of WebSearchItem objects with query and reason
        """
        messages = [
            f"✅ **Planning complete** - {num_searches} searches planned",
            "",
            "### 📋 Search Plan:",
            ""
        ]

        for i, search_item in enumerate(searches, 1):
            messages.extend([
                f"**{i}. {search_item.query}**",
                f"   *Reason:* {search_item.reason}",
                ""
            ])

        messages.extend(["---", ""])
        self.add_multiple(messages)

    def add_search_start(self) -> None:
        """Add search start status."""
        self.add_multiple(["🔍 **Starting searches...**", ""])

    def add_search_progress(self, completed: int, total: int, successful: int, success: bool) -> None:
        """
        Add search progress update.

        Args:
            completed: Number of searches completed so far
            total: Total number of searches
            successful: Number of successful searches so far
            success: Whether this particular search succeeded
        """
        if success:
            self.add(f"   ✓ Search {completed}/{total} completed - {successful} successful so far")
        else:
            self.add(f"   ✗ Search {completed}/{total} failed")

    def add_search_complete(self, successful: int, total: int) -> None:
        """
        Add search completion status.

        Args:
            successful: Number of successful searches
            total: Total number of searches attempted
        """
        self.add_multiple([
            "",
            f"✅ **Searches complete** - {successful}/{total} successful",
            "",
            "---",
            ""
        ])

    def add_writing_start(self) -> None:
        """Add writing start status."""
        self.add("✍️ **Writing comprehensive report...**")

    def add_writing_complete(self, confidence_score: float, confidence_label: str) -> None:
        """
        Add writing completion status.

        Args:
            confidence_score: Confidence score (0.0-1.0)
            confidence_label: Human-readable confidence label
        """
        self.add_multiple([
            f"✅ **Report complete** - Confidence: {confidence_label} ({confidence_score:.2f})",
            ""
        ])

    def add_database_saving(self) -> None:
        """Add database save start status."""
        self.add("💾 **Saving to database...**")

    def add_database_saved(self, report_id: str) -> None:
        """
        Add database save success status.

        Args:
            report_id: The database report ID (will be truncated for display)
        """
        self.add(f"✅ **Saved to database** - Report ID: {report_id[:8]}...")

    def add_database_error(self, error_type: str) -> None:
        """
        Add database save error status.

        Args:
            error_type: Type of error that occurred
        """
        self.add_multiple([
            f"⚠️ **Database save failed** - {error_type}",
            "   *(Report still available but not persisted)*"
        ])

    def add_email_sending(self) -> None:
        """Add email sending status."""
        self.add("📧 **Sending email...**")

    def add_email_success(self) -> None:
        """Add email success status."""
        self.add("✅ **Email sent successfully**")

    def add_email_failure(self) -> None:
        """Add email failure status."""
        self.add("⚠️ **Email failed** (check configuration)")

    def add_completion(self) -> None:
        """Add research completion status."""
        self.add_multiple([
            "",
            "---",
            "",
            "## ✨ Research Complete!",
            ""
        ])

    def add_stopped_by_user(self) -> None:
        """Add user stop status."""
        self.add_multiple([
            "",
            "---",
            "",
            "## ⚠️ Research Stopped by User",
            "",
            "Partial results shown above (if any). Results not saved to database."
        ])

    def add_error(self, message: str) -> None:
        """
        Add error status.

        Args:
            message: Error message to display
        """
        self.add(f"❌ **{message}**")
