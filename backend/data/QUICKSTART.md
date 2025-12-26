# Database Quick Start

One-page reference for using the DeepTrace database layer.

## Import

```python
from backend.data import (
    init_db,
    save_report, get_report, get_all_reports,
    save_source, get_sources_for_report,
    save_log, get_logs_for_report
)
```

## Initialize (once at startup)

```python
init_db()  # Creates tables if not exist
```

## Save a Report

```python
report_id = save_report({
    "query": "What are AI agents?",
    "mode": "quick",  # or "deep"
    "summary": "Executive summary text...",
    "goals": "Research goals text...",
    "methodology": "Research methodology text...",
    "findings": "Key findings text...",
    "competitors": "Competitor analysis...",  # OPTIONAL
    "risks": "Risk assessment text...",
    "opportunities": "Opportunities text...",
    "recommendations": "Recommendations text...",
    "confidence_score": 0.85  # 0.0 to 1.0
})
```

## Get Reports

```python
# Get one report
report = get_report(report_id)

# Get recent reports
reports = get_all_reports(limit=10)
```

## Save Sources

```python
source_id = save_source({
    "report_id": report_id,
    "url": "https://example.com/article",
    "reliability": 0.75,  # 0.0 to 1.0
    "domain": "example.com",
    "source_type": "media",  # gov, academic, media, blog, forum, unknown
    "published_at": "2024-01-15T10:00:00"  # OPTIONAL (ISO format)
})
```

## Get Sources

```python
sources = get_sources_for_report(report_id)
```

## Save Logs

```python
log_id = save_log({
    "report_id": report_id,  # OPTIONAL
    "stage": "planning",
    "message": "Generating search plan...",
    "status": "running"  # running, ok, warning, error
})
```

## Get Logs

```python
logs = get_logs_for_report(report_id)
```

## Error Handling

### Write operations raise exceptions

```python
try:
    report_id = save_report(data)
except ValueError as e:
    # Validation error (missing fields, invalid values)
    print(f"Invalid data: {e}")
except sqlite3.Error as e:
    # Database error
    print(f"Database error: {e}")
```

### Read operations return None/empty list

```python
report = get_report(report_id)
if report is None:
    print("Report not found or error occurred")

sources = get_sources_for_report(report_id)
if not sources:
    print("No sources or error occurred")
```

## Field Constraints

### Report
- `mode`: "quick" or "deep"
- `confidence_score`: 0.0 to 1.0
- `competitors`: NULLABLE (all others required)

### Source
- `source_type`: "gov", "academic", "media", "blog", "forum", "unknown"
- `reliability`: 0.0 to 1.0
- `published_at`: NULLABLE (ISO format)

### Log
- `status`: "running", "ok", "warning", "error"
- `report_id`: NULLABLE

## Common Patterns

### Full pipeline logging

```python
# Start
save_log({"report_id": id, "stage": "planning", "message": "Starting...", "status": "running"})

# Success
save_log({"report_id": id, "stage": "planning", "message": "Complete", "status": "ok"})

# Warning
save_log({"report_id": id, "stage": "search", "message": "Partial results", "status": "warning"})

# Error
save_log({"report_id": id, "stage": "writing", "message": f"Error: {e}", "status": "error"})
```

### Graceful degradation

```python
try:
    save_report(data)
except Exception as e:
    logger.error(f"Save failed: {e}")
    save_log({"stage": "persistence", "message": f"Failed: {e}", "status": "error"})
    # Continue pipeline - user still gets results
```

## Testing

```bash
python test_db.py
```

## Database Location

`A:\MyProjects\DeepTrace\research.db` (gitignored)

## Full Documentation

- API Reference: `backend/data/README.md`
- Integration Guide: `backend/data/INTEGRATION.md`
- Implementation: `DATABASE_IMPLEMENTATION.md`
