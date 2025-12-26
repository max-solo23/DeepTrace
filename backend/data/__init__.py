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
)

__all__ = [
    "init_db",
    "save_report",
    "get_report",
    "get_all_reports",
]
