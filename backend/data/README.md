# DeepTrace Database Layer

SQLite-based persistence layer for the DeepTrace research assistant MVP.

## Overview

This module provides a clean, well-documented data access layer designed for easy migration from SQLite to PostgreSQL in the future.

## Files

- `db.py` - Main database implementation with all CRUD operations
- `__init__.py` - Public API exports
- `migrations/` - Directory for future Alembic migrations (currently empty)

## Schema

### Tables

#### `reports`
Stores completed research reports with structured content.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID |
| query | TEXT | NOT NULL | User's research query |
| mode | TEXT | NOT NULL | "quick" or "deep" |
| summary | TEXT | NOT NULL | Executive summary |
| goals | TEXT | NOT NULL | Research goals |
| methodology | TEXT | NOT NULL | Research methodology |
| findings | TEXT | NOT NULL | Key findings |
| competitors | TEXT | NULLABLE | Competitor analysis |
| risks | TEXT | NOT NULL | Risk assessment |
| opportunities | TEXT | NOT NULL | Opportunities identified |
| recommendations | TEXT | NOT NULL | Recommendations |
| confidence_score | REAL | NOT NULL, 0-1 | Confidence in findings |
| created_at | TEXT | NOT NULL | ISO timestamp |

#### `sources`
Stores source references for each report.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID |
| report_id | TEXT | FOREIGN KEY | Parent report UUID |
| url | TEXT | NOT NULL | Source URL |
| reliability | REAL | NOT NULL, 0-1 | Reliability score |
| domain | TEXT | NOT NULL | Domain name |
| source_type | TEXT | NOT NULL | "gov", "academic", "media", "blog", "forum", "unknown" |
| published_at | TEXT | NULLABLE | ISO timestamp |

**Indexes:**
- `idx_sources_report_id` on `report_id` for fast lookups

#### `logs`
Stores pipeline execution logs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID |
| report_id | TEXT | FOREIGN KEY, NULLABLE | Related report UUID |
| stage | TEXT | NOT NULL | Pipeline stage name |
| message | TEXT | NOT NULL | Log message |
| timestamp | TEXT | NOT NULL | ISO timestamp |
| status | TEXT | NOT NULL | "running", "ok", "warning", "error" |

**Indexes:**
- `idx_logs_report_id` on `report_id` for fast lookups
- `idx_logs_timestamp` on `timestamp` for time-based queries

## API Reference

### Initialization

```python
from backend.data import init_db

# Initialize database (creates tables if not exist)
init_db()
```

### Reports

```python
from backend.data import save_report, get_report, get_all_reports

# Save a report
report_id = save_report({
    "query": "What are AI agents?",
    "mode": "quick",
    "summary": "...",
    "goals": "...",
    "methodology": "...",
    "findings": "...",
    "competitors": "...",  # optional
    "risks": "...",
    "opportunities": "...",
    "recommendations": "...",
    "confidence_score": 0.85
})

# Get report by ID
report = get_report(report_id)

# Get recent reports (default: 50)
reports = get_all_reports(limit=10)
```

### Sources

```python
from backend.data import save_source, get_sources_for_report

# Save a source
source_id = save_source({
    "report_id": report_id,
    "url": "https://example.com",
    "reliability": 0.75,
    "domain": "example.com",
    "source_type": "media",
    "published_at": "2024-01-15T10:00:00"  # optional
})

# Get all sources for a report
sources = get_sources_for_report(report_id)
```

### Logs

```python
from backend.data import save_log, get_logs_for_report

# Save a log entry
log_id = save_log({
    "report_id": report_id,  # optional
    "stage": "planning",
    "message": "Generating search plan",
    "status": "running"
})

# Get all logs for a report
logs = get_logs_for_report(report_id)
```

## Error Handling

Following the `ERROR_HANDLING_POLICY.md`:

- **Write operations** (save_*): Raise exceptions on failure
  - Caller must handle with try/except
  - All errors are logged before raising

- **Read operations** (get_*): Return None or empty list on failure
  - No exceptions raised
  - All errors are logged
  - Graceful degradation

- **Validation errors**: Raise `ValueError` with clear message
  - Invalid enum values
  - Missing required fields
  - Out-of-range numeric values

## PostgreSQL Migration Path

This schema is designed for easy PostgreSQL migration:

1. **UUIDs**: Using TEXT representation now, will become `UUID` type
2. **Timestamps**: Using ISO strings now, will become `TIMESTAMP WITH TIME ZONE`
3. **ENUMs**: Using CHECK constraints now, will become PostgreSQL ENUMs
4. **Foreign Keys**: Using ON DELETE CASCADE for referential integrity
5. **Indexes**: Already defined, will transfer directly

No SQLite-specific features are used (no AUTOINCREMENT, no SQLite-specific functions).

## Testing

Run the test script to verify functionality:

```bash
python test_db.py
```

This tests:
- Database initialization
- Report CRUD operations
- Source CRUD operations
- Log CRUD operations
- Validation logic
- Error handling

## Location

Database file: `research.db` in project root (gitignored)

## Future Enhancements

- [ ] Alembic migrations setup
- [ ] Connection pooling for production
- [ ] Full-text search on report content
- [ ] Pagination for large result sets
- [ ] Archive/soft delete functionality
- [ ] Query performance monitoring
