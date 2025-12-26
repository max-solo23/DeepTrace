"""
Database layer for DeepTrace research assistant.

This module provides SQLite persistence with a clean API designed
for easy migration to PostgreSQL/Neon in the future.
"""

from .db import (
    init_db,
    save_report,
    get_report,
    get_all_reports,
    save_source,
    get_sources_for_report,
    save_log,
    get_logs_for_report,
    close_db,
)

__all__ = [
    "init_db",
    "save_report",
    "get_report",
    "get_all_reports",
    "save_source",
    "get_sources_for_report",
    "save_log",
    "get_logs_for_report",
    "close_db",
]
