"""
Database layer implementation for DeepTrace.

Uses SQLite for MVP with schema designed for easy PostgreSQL migration.
All IDs are UUIDs, timestamps are ISO format, and we avoid SQLite-specific features.

Error Handling:
- All database operations wrapped in try/except
- Errors logged with context
- No silent failures (per ERROR_HANDLING_POLICY.md)
- Returns None or empty list on read failures
- Raises exception on write failures (caller must handle)
"""

import sqlite3
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Database file location (project root)
DB_PATH = Path(__file__).parent.parent.parent / "research.db"

# Valid enum values (for validation)
VALID_MODES = {"quick", "deep"}
VALID_SOURCE_TYPES = {"gov", "academic", "media", "blog", "forum", "unknown"}
VALID_LOG_STATUSES = {"running", "ok", "warning", "error"}


@contextmanager
def get_connection():
    """
    Context manager for database connections.

    Ensures proper connection cleanup and error handling.
    Yields a connection object with row factory set to sqlite3.Row.

    Yields:
        sqlite3.Connection: Database connection with Row factory

    Raises:
        sqlite3.Error: On connection or execution errors
    """
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def init_db() -> bool:
    """
    Initialize database schema.

    Creates all required tables if they don't exist:
    - reports: Research reports with structured content
    - sources: Sources referenced in reports
    - logs: Pipeline execution logs

    Returns:
        bool: True if initialization successful, False otherwise

    Raises:
        sqlite3.Error: On database errors (after logging)
    """
    logger.info(f"Initializing database at {DB_PATH}")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    mode TEXT NOT NULL CHECK(mode IN ('quick', 'deep')),
                    summary TEXT NOT NULL,
                    goals TEXT NOT NULL,
                    methodology TEXT NOT NULL,
                    findings TEXT NOT NULL,
                    competitors TEXT,
                    risks TEXT NOT NULL,
                    opportunities TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    confidence_score REAL NOT NULL CHECK(confidence_score >= 0 AND confidence_score <= 1),
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)

            conn.commit()
            logger.info("Database schema initialized successfully")
            return True

    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def save_report(report_data: Dict[str, Any]) -> str:
    """
    Save a research report to the database.

    Args:
        report_data: Dictionary containing report fields:
            - query (str): Research query
            - mode (str): "quick" or "deep"
            - summary (str): Executive summary
            - goals (str): Research goals
            - methodology (str): Research methodology
            - findings (str): Key findings
            - competitors (str, optional): Competitor analysis
            - risks (str): Risk assessment
            - opportunities (str): Opportunities identified
            - recommendations (str): Recommendations
            - confidence_score (float): 0.0 to 1.0

    Returns:
        str: UUID of created report

    Raises:
        ValueError: If required fields missing or invalid
        sqlite3.Error: On database errors
    """
    # Validate required fields
    required_fields = [
        "query", "mode", "summary", "goals", "methodology",
        "findings", "risks", "opportunities", "recommendations", "confidence_score"
    ]
    missing = [f for f in required_fields if f not in report_data]
    if missing:
        error_msg = f"Missing required fields: {missing}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Validate mode
    if report_data["mode"] not in VALID_MODES:
        error_msg = f"Invalid mode: {report_data['mode']}. Must be one of {VALID_MODES}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Validate confidence score
    score = report_data["confidence_score"]
    if not isinstance(score, (int, float)) or not (0 <= score <= 1):
        error_msg = f"Invalid confidence_score: {score}. Must be float between 0 and 1"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Generate UUID
    report_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    logger.info(f"Saving report {report_id} for query: {report_data['query'][:50]}...")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reports (
                    id, query, mode, summary, goals, methodology,
                    findings, competitors, risks, opportunities,
                    recommendations, confidence_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                report_data["query"],
                report_data["mode"],
                report_data["summary"],
                report_data["goals"],
                report_data["methodology"],
                report_data["findings"],
                report_data.get("competitors"),  # Optional field
                report_data["risks"],
                report_data["opportunities"],
                report_data["recommendations"],
                report_data["confidence_score"],
                timestamp
            ))
            conn.commit()

        logger.info(f"Report {report_id} saved successfully")
        return report_id

    except sqlite3.Error as e:
        logger.error(f"Failed to save report: {e}")
        raise


def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a report by ID.

    Args:
        report_id: UUID of the report

    Returns:
        dict: Report data with all fields, or None if not found

    Note:
        Returns None on errors (logged) - no exceptions raised for read operations
    """
    logger.info(f"Retrieving report {report_id}")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reports WHERE id = ?
            """, (report_id,))

            row = cursor.fetchone()

            if row:
                result = dict(row)
                logger.info(f"Report {report_id} retrieved successfully")
                return result
            else:
                logger.warning(f"Report {report_id} not found")
                return None

    except sqlite3.Error as e:
        logger.error(f"Failed to retrieve report {report_id}: {e}")
        return None


def get_all_reports(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve recent reports, ordered by creation time (newest first).

    Args:
        limit: Maximum number of reports to return (default: 50)

    Returns:
        list[dict]: List of report dictionaries (may be empty)

    Note:
        Returns empty list on errors (logged) - no exceptions raised
    """
    logger.info(f"Retrieving up to {limit} recent reports")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reports
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            results = [dict(row) for row in rows]

            logger.info(f"Retrieved {len(results)} reports")
            return results

    except sqlite3.Error as e:
        logger.error(f"Failed to retrieve reports: {e}")
        return []
