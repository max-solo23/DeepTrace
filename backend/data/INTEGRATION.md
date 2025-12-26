# Database Integration Guide

How to integrate the database layer with existing DeepTrace agents.

## Quick Start

### 1. Initialize Database on Startup

In your main application file (`deep_research.py`):

```python
from backend.data import init_db
import logging

logger = logging.getLogger(__name__)

# Call this before starting Gradio
def startup():
    """Initialize application on startup."""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# At the top of your main block
if __name__ == "__main__":
    startup()
    # ... rest of your Gradio setup
```

### 2. Save Reports After Writer Agent

In `research_manager.py`, after the Writer Agent completes:

```python
from backend.data import save_report, save_source, save_log

async def run(self, query: str, mode: str):
    """Run research pipeline with database persistence."""

    # Generate report_id early for logging
    report_id = str(uuid.uuid4())

    try:
        # Log pipeline start
        save_log({
            "report_id": report_id,
            "stage": "initialization",
            "message": f"Starting {mode} mode research for: {query}",
            "status": "running"
        })

        # ... existing planner code ...
        save_log({
            "report_id": report_id,
            "stage": "planning",
            "message": f"Generated {len(search_plan.searches)} search queries",
            "status": "ok"
        })

        # ... existing search code ...
        save_log({
            "report_id": report_id,
            "stage": "search",
            "message": f"Completed {len(search_results)} searches",
            "status": "ok"
        })

        # ... existing writer code ...
        save_log({
            "report_id": report_id,
            "stage": "writing",
            "message": "Report synthesis complete",
            "status": "ok"
        })

        # Save report to database
        try:
            # Extract sources from search results
            sources = []
            for result in search_results:
                if result and hasattr(result, 'sources'):
                    sources.extend(result.sources)

            # Save report
            saved_report_id = save_report({
                "query": query,
                "mode": mode,
                "summary": report_data.summary,
                "goals": report_data.goals,
                "methodology": report_data.methodology,
                "findings": report_data.findings,
                "competitors": report_data.competitors,
                "risks": report_data.risks,
                "opportunities": report_data.opportunities,
                "recommendations": report_data.recommendations,
                "confidence_score": report_data.confidence_score
            })

            # Save sources
            for source in sources:
                save_source({
                    "report_id": saved_report_id,
                    "url": source.url,
                    "reliability": source.reliability,
                    "domain": source.domain,
                    "source_type": source.source_type,
                    "published_at": source.published_at
                })

            save_log({
                "report_id": report_id,
                "stage": "persistence",
                "message": f"Report saved to database with {len(sources)} sources",
                "status": "ok"
            })

        except Exception as e:
            logger.error(f"Failed to save report to database: {e}")
            save_log({
                "report_id": report_id,
                "stage": "persistence",
                "message": f"Database save failed: {str(e)}",
                "status": "error"
            })
            # Don't raise - continue with email/output

        # ... rest of pipeline (email, etc.) ...

    except Exception as e:
        save_log({
            "report_id": report_id,
            "stage": "pipeline",
            "message": f"Pipeline failed: {str(e)}",
            "status": "error"
        })
        raise
```

### 3. Add History View to Gradio UI

In `deep_research.py`, add a history tab:

```python
import gradio as gr
from backend.data import get_all_reports, get_report, get_sources_for_report

def load_report_history(limit=10):
    """Load recent reports for history view."""
    reports = get_all_reports(limit=limit)
    if not reports:
        return "No reports found."

    history = []
    for report in reports:
        history.append(f"""
### {report['query']}
**Mode:** {report['mode']} | **Created:** {report['created_at']} | **Confidence:** {report['confidence_score']:.2f}

{report['summary'][:200]}...

---
""")
    return "\n".join(history)

def view_full_report(report_id):
    """Load full report by ID."""
    report = get_report(report_id)
    if not report:
        return "Report not found."

    sources = get_sources_for_report(report_id)

    markdown = f"""
# {report['query']}

**Mode:** {report['mode']} | **Created:** {report['created_at']} | **Confidence:** {report['confidence_score']:.2f}

## Summary
{report['summary']}

## Goals
{report['goals']}

## Methodology
{report['methodology']}

## Findings
{report['findings']}

## Risks
{report['risks']}

## Opportunities
{report['opportunities']}

## Recommendations
{report['recommendations']}

## Sources ({len(sources)})
"""
    for i, source in enumerate(sources, 1):
        markdown += f"\n{i}. [{source['domain']}]({source['url']}) - Reliability: {source['reliability']:.2f}, Type: {source['source_type']}\n"

    return markdown

# Add to Gradio interface
with gr.Blocks() as demo:
    with gr.Tab("Research"):
        # ... existing research UI ...
        pass

    with gr.Tab("History"):
        with gr.Row():
            refresh_btn = gr.Button("Refresh")
            limit_slider = gr.Slider(5, 50, value=10, step=5, label="Number of reports")

        history_output = gr.Markdown()

        refresh_btn.click(
            load_report_history,
            inputs=[limit_slider],
            outputs=[history_output]
        )

        # Load on tab open
        demo.load(load_report_history, inputs=[limit_slider], outputs=[history_output])
```

## Logging Strategy

### Pipeline Stage Logging

Log at each major stage:

```python
# Stage: planning
save_log({"report_id": report_id, "stage": "planning", "message": "...", "status": "running"})
# ... work ...
save_log({"report_id": report_id, "stage": "planning", "message": "...", "status": "ok"})

# Stage: search
save_log({"report_id": report_id, "stage": "search", "message": "...", "status": "running"})
# ... work ...
save_log({"report_id": report_id, "stage": "search", "message": "...", "status": "ok"})

# Stage: writing
save_log({"report_id": report_id, "stage": "writing", "message": "...", "status": "running"})
# ... work ...
save_log({"report_id": report_id, "stage": "writing", "message": "...", "status": "ok"})
```

### Error Logging

```python
try:
    # ... work ...
except Exception as e:
    save_log({
        "report_id": report_id,
        "stage": "search",
        "message": f"Search failed: {str(e)}",
        "status": "error"
    })
    # Handle error per ERROR_HANDLING_POLICY.md
```

### Warning Logging

```python
if len(search_results) < expected:
    save_log({
        "report_id": report_id,
        "stage": "search",
        "message": f"Only {len(search_results)}/{expected} searches succeeded",
        "status": "warning"
    })
```

## Source Extraction

You'll need to extract source metadata from search results. Here's a helper function:

```python
from typing import List, Dict, Any
from urllib.parse import urlparse

def extract_sources(search_results) -> List[Dict[str, Any]]:
    """
    Extract source metadata from search results.

    Adapt this based on your WebSearchTool output format.
    """
    sources = []

    for result in search_results:
        if not result:
            continue

        # Adapt to your actual search result structure
        # This is an example - adjust field names as needed
        for item in getattr(result, 'sources', []):
            url = item.get('url', '')
            domain = urlparse(url).netloc

            sources.append({
                "url": url,
                "reliability": item.get('reliability', 0.5),  # Default if not provided
                "domain": domain,
                "source_type": classify_source_type(domain),
                "published_at": item.get('published_at')  # May be None
            })

    return sources

def classify_source_type(domain: str) -> str:
    """
    Classify source type based on domain.

    This is a simple heuristic - improve as needed.
    """
    domain_lower = domain.lower()

    if any(tld in domain_lower for tld in ['.gov', '.mil']):
        return 'gov'
    elif any(term in domain_lower for term in ['edu', 'scholar', 'arxiv', 'pubmed']):
        return 'academic'
    elif any(term in domain_lower for term in ['reddit', 'hackernews', 'stackoverflow']):
        return 'forum'
    elif any(term in domain_lower for term in ['medium', 'substack', 'blogger']):
        return 'blog'
    elif any(term in domain_lower for term in ['nytimes', 'bbc', 'reuters', 'techcrunch', 'wired']):
        return 'media'
    else:
        return 'unknown'
```

## Error Handling Best Practices

Following `ERROR_HANDLING_POLICY.md`:

### 1. Never Fail Silently

```python
# BAD
try:
    save_report(data)
except:
    pass  # SILENT FAILURE - NEVER DO THIS

# GOOD
try:
    save_report(data)
except Exception as e:
    logger.error(f"Failed to save report: {e}")
    save_log({
        "report_id": report_id,
        "stage": "persistence",
        "message": f"Save failed: {str(e)}",
        "status": "error"
    })
    # Decide: retry, fallback, or raise
```

### 2. Graceful Degradation

```python
# Database save failures should not crash the pipeline
try:
    save_report(report_data)
except Exception as e:
    logger.error(f"Database save failed: {e}")
    # Continue with email/output - user still gets results
    # Just no persistence
```

### 3. Log Everything

```python
# Log success
save_log({"stage": "persistence", "message": "Report saved", "status": "ok"})

# Log warnings
save_log({"stage": "persistence", "message": "Partial save", "status": "warning"})

# Log errors
save_log({"stage": "persistence", "message": f"Error: {e}", "status": "error"})
```

## Testing Integration

After integrating, test:

1. **Full pipeline**: Run a research query and verify database entries
2. **Error handling**: Test with invalid data, verify graceful handling
3. **History view**: Load saved reports in UI
4. **Logs**: Verify all stages logged correctly

```python
# Quick integration test
from backend.data import get_all_reports, get_logs_for_report

# After running a research query
reports = get_all_reports(limit=1)
if reports:
    report = reports[0]
    print(f"Latest report: {report['query']}")

    logs = get_logs_for_report(report['id'])
    print(f"Pipeline logs: {len(logs)} entries")
    for log in logs:
        print(f"  [{log['status']}] {log['stage']}: {log['message']}")
```

## Migration Notes

When ready to migrate to PostgreSQL:

1. Export data: `sqlite3 research.db .dump > backup.sql`
2. Update connection string in `db.py`
3. Run migrations with Alembic
4. Import data to PostgreSQL
5. Update `get_connection()` to use `psycopg2` or `asyncpg`

The schema is already PostgreSQL-compatible, so migration should be straightforward.
