"""Performance monitoring and tracking for research operations.

This module provides tools for tracking execution time and performance metrics
across different phases of the research pipeline.
"""

import time
from typing import Optional
from .types import ResearchMode, get_mode_config


class PerformanceTracker:
    """Tracks performance metrics for research operations.

    Monitors execution time across different phases:
    - Planning: Time spent generating search plan
    - Searching: Time spent executing searches
    - Writing: Time spent generating report
    - Total: End-to-end execution time

    Logs warnings when execution exceeds target times for the research mode.
    """

    def __init__(self, mode: ResearchMode):
        """Initialize performance tracker.

        Args:
            mode: Research mode to track performance for
        """
        self.mode = mode
        self.config = get_mode_config(mode)
        self.target_time = self.config["target_time"]

        # Timing metrics
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.planning_start: Optional[float] = None
        self.planning_end: Optional[float] = None
        self.search_start: Optional[float] = None
        self.search_end: Optional[float] = None
        self.writing_start: Optional[float] = None
        self.writing_end: Optional[float] = None

    def start(self):
        """Start tracking overall execution time."""
        self.start_time = time.time()
        print(f"[PERFORMANCE] Starting {self.mode.value} mode research (target: {self.target_time}s)")

    def start_planning(self):
        """Mark start of planning phase."""
        self.planning_start = time.time()
        print("[PERFORMANCE] Planning phase started")

    def end_planning(self):
        """Mark end of planning phase and log duration."""
        if self.planning_start is None:
            print("[PERFORMANCE] WARNING: Planning end called without start")
            return
        self.planning_end = time.time()
        duration = self.planning_end - self.planning_start
        print(f"[PERFORMANCE] Planning phase completed in {duration:.2f}s")

    def start_searching(self):
        """Mark start of search phase."""
        self.search_start = time.time()
        print("[PERFORMANCE] Search phase started")

    def end_searching(self):
        """Mark end of search phase and log duration."""
        if self.search_start is None:
            print("[PERFORMANCE] WARNING: Search end called without start")
            return
        self.search_end = time.time()
        duration = self.search_end - self.search_start
        print(f"[PERFORMANCE] Search phase completed in {duration:.2f}s")

    def start_writing(self):
        """Mark start of writing phase."""
        self.writing_start = time.time()
        print("[PERFORMANCE] Writing phase started")

    def end_writing(self):
        """Mark end of writing phase and log duration."""
        if self.writing_start is None:
            print("[PERFORMANCE] WARNING: Writing end called without start")
            return
        self.writing_end = time.time()
        duration = self.writing_end - self.writing_start
        print(f"[PERFORMANCE] Writing phase completed in {duration:.2f}s")

    def end(self):
        """Complete tracking and log final metrics."""
        if self.start_time is None:
            print("[PERFORMANCE] WARNING: Tracker end called without start")
            return

        self.end_time = time.time()
        total_time = self.end_time - self.start_time

        # Calculate phase times
        planning_time = (self.planning_end - self.planning_start) if (self.planning_end and self.planning_start) else 0
        search_time = (self.search_end - self.search_start) if (self.search_end and self.search_start) else 0
        writing_time = (self.writing_end - self.writing_start) if (self.writing_end and self.writing_start) else 0

        # Log summary
        print("\n" + "="*60)
        print(f"[PERFORMANCE] Research completed in {total_time:.2f}s (target: {self.target_time}s)")
        print(f"[PERFORMANCE] Mode: {self.mode.value}")
        print(f"[PERFORMANCE] Breakdown:")
        print(f"  - Planning: {planning_time:.2f}s")
        print(f"  - Searching: {search_time:.2f}s")
        print(f"  - Writing: {writing_time:.2f}s")

        # Check if we exceeded target
        if total_time > self.target_time:
            over_time = total_time - self.target_time
            print(f"[PERFORMANCE] WARNING: Exceeded target time by {over_time:.2f}s ({(over_time/self.target_time)*100:.1f}%)")
        else:
            under_time = self.target_time - total_time
            print(f"[PERFORMANCE] SUCCESS: Completed {under_time:.2f}s under target")

        print("="*60 + "\n")

    def get_metrics(self) -> dict:
        """Get current performance metrics.

        Returns:
            Dictionary with timing metrics for all phases
        """
        if self.start_time is None:
            return {
                "total_time": 0,
                "planning_time": 0,
                "search_time": 0,
                "writing_time": 0,
                "target_time": self.target_time,
                "mode": self.mode.value,
            }

        current_time = self.end_time if self.end_time else time.time()
        total_time = current_time - self.start_time

        planning_time = (self.planning_end - self.planning_start) if (self.planning_end and self.planning_start) else 0
        search_time = (self.search_end - self.search_start) if (self.search_end and self.search_start) else 0
        writing_time = (self.writing_end - self.writing_start) if (self.writing_end and self.writing_start) else 0

        return {
            "total_time": total_time,
            "planning_time": planning_time,
            "search_time": search_time,
            "writing_time": writing_time,
            "target_time": self.target_time,
            "mode": self.mode.value,
            "exceeded_target": total_time > self.target_time,
        }
