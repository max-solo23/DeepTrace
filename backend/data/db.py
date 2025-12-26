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

            # Sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    report_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    reliability REAL NOT NULL CHECK(reliability >= 0 AND reliability <= 1),
                    domain TEXT NOT NULL,
                    source_type TEXT NOT NULL CHECK(source_type IN ('gov', 'academic', 'media', 'blog', 'forum', 'unknown')),
                    published_at TEXT,
                    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
                )
            """)

            # Create index on report_id for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sources_report_id
                ON sources(report_id)
            """)

            # Logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id TEXT PRIMARY KEY,
                    report_id TEXT,
                    stage TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                    status TEXT NOT NULL CHECK(status IN ('running', 'ok', 'warning', 'error')),
                    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
                )
            """)

            # Create index on report_id for faster log lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_report_id
                ON logs(report_id)
            """)

            # Create index on timestamp for time-based queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp
                ON logs(timestamp)
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


def save_source(source_data: Dict[str, Any]) -> str:
    """
    Save a source reference to the database.

    Args:
        source_data: Dictionary containing:
            - report_id (str): UUID of parent report
            - url (str): Source URL
            - reliability (float): 0.0 to 1.0
            - domain (str): Domain name
            - source_type (str): One of VALID_SOURCE_TYPES
            - published_at (str, optional): ISO format timestamp

    Returns:
        str: UUID of created source

    Raises:
        ValueError: If required fields missing or invalid
        sqlite3.Error: On database errors
    """
    # Validate required fields
    required_fields = ["report_id", "url", "reliability", "domain", "source_type"]
    missing = [f for f in required_fields if f not in source_data]
    if missing:
        error_msg = f"Missing required fields: {missing}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Validate source_type
    if source_data["source_type"] not in VALID_SOURCE_TYPES:
        error_msg = f"Invalid source_type: {source_data['source_type']}. Must be one of {VALID_SOURCE_TYPES}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Validate reliability
    reliability = source_data["reliability"]
    if not isinstance(reliability, (int, float)) or not (0 <= reliability <= 1):
        error_msg = f"Invalid reliability: {reliability}. Must be float between 0 and 1"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Generate UUID
    source_id = str(uuid.uuid4())

    logger.info(f"Saving source {source_id} for report {source_data['report_id']}")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sources (
                    id, report_id, url, reliability, domain, source_type, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                source_id,
                source_data["report_id"],
                source_data["url"],
                source_data["reliability"],
                source_data["domain"],
                source_data["source_type"],
                source_data.get("published_at")  # Optional field
            ))
            conn.commit()

        logger.info(f"Source {source_id} saved successfully")
        return source_id

    except sqlite3.Error as e:
        logger.error(f"Failed to save source: {e}")
        raise


def get_sources_for_report(report_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all sources for a specific report.

    Args:
        report_id: UUID of the report

    Returns:
        list[dict]: List of source dictionaries (may be empty)

    Note:
        Returns empty list on errors (logged) - no exceptions raised
    """
    logger.info(f"Retrieving sources for report {report_id}")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sources WHERE report_id = ?
            """, (report_id,))

            rows = cursor.fetchall()
            results = [dict(row) for row in rows]

            logger.info(f"Retrieved {len(results)} sources for report {report_id}")
            return results

    except sqlite3.Error as e:
        logger.error(f"Failed to retrieve sources for report {report_id}: {e}")
        return []


def save_log(log_data: Dict[str, Any]) -> str:
    """
    Save a log entry to the database.

    Args:
        log_data: Dictionary containing:
            - report_id (str, optional): UUID of related report
            - stage (str): Pipeline stage name
            - message (str): Log message
            - status (str): One of VALID_LOG_STATUSES

    Returns:
        str: UUID of created log entry

    Raises:
        ValueError: If required fields missing or invalid
        sqlite3.Error: On database errors
    """
    # Validate required fields
    required_fields = ["stage", "message", "status"]
    missing = [f for f in required_fields if f not in log_data]
    if missing:
        error_msg = f"Missing required fields: {missing}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Validate status
    if log_data["status"] not in VALID_LOG_STATUSES:
        error_msg = f"Invalid status: {log_data['status']}. Must be one of {VALID_LOG_STATUSES}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Generate UUID and timestamp
    log_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    logger.debug(f"Saving log {log_id} for stage {log_data['stage']}")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO logs (
                    id, report_id, stage, message, timestamp, status
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                log_data.get("report_id"),  # Optional field
                log_data["stage"],
                log_data["message"],
                timestamp,
                log_data["status"]
            ))
            conn.commit()

        logger.debug(f"Log {log_id} saved successfully")
        return log_id

    except sqlite3.Error as e:
        logger.error(f"Failed to save log: {e}")
        raise


def get_logs_for_report(report_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all logs for a specific report, ordered by timestamp.

    Args:
        report_id: UUID of the report

    Returns:
        list[dict]: List of log dictionaries (may be empty)

    Note:
        Returns empty list on errors (logged) - no exceptions raised
    """
    logger.info(f"Retrieving logs for report {report_id}")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM logs
                WHERE report_id = ?
                ORDER BY timestamp ASC
            """, (report_id,))

            rows = cursor.fetchall()
            results = [dict(row) for row in rows]

            logger.info(f"Retrieved {len(results)} logs for report {report_id}")
            return results

    except sqlite3.Error as e:
        logger.error(f"Failed to retrieve logs for report {report_id}: {e}")
        return []


def close_db():
    """
    Close database connections.

    Note: With context managers, connections auto-close, but this
    function is provided for explicit cleanup if needed.
    Currently a no-op but reserved for future connection pooling.
    """
    logger.info("Database cleanup called (no-op with current architecture)")
    pass
