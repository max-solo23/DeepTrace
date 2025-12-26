# Database Layer Code Examples

Real-world usage examples for the DeepTrace database layer.

## Example 1: Complete Research Pipeline Integration

```python
import uuid
import logging
from backend.data import init_db, save_report, save_source, save_log

logger = logging.getLogger(__name__)

async def run_research_with_persistence(query: str, mode: str):
    """Run research pipeline with full database persistence."""

    # Initialize database (if not already done)
    init_db()

    # Generate report ID for logging
    report_id = str(uuid.uuid4())

    try:
        # Log pipeline start
        save_log({
            "report_id": report_id,
            "stage": "initialization",
            "message": f"Starting {mode} research: {query}",
            "status": "running"
        })

        # === PLANNING STAGE ===
        save_log({
            "report_id": report_id,
            "stage": "planning",
            "message": "Generating search plan",
            "status": "running"
        })

        # ... call planner agent ...
        # search_plan = await planner_agent.generate_plan(query, mode)

        save_log({
            "report_id": report_id,
            "stage": "planning",
            "message": f"Generated {len(search_plan.searches)} queries",
            "status": "ok"
        })

        # === SEARCH STAGE ===
        save_log({
            "report_id": report_id,
            "stage": "search",
            "message": f"Executing {len(search_plan.searches)} searches",
            "status": "running"
        })

        # ... call search agent ...
        # search_results = await search_agent.execute(search_plan)

        successful_searches = sum(1 for r in search_results if r is not None)

        if successful_searches < len(search_plan.searches):
            save_log({
                "report_id": report_id,
                "stage": "search",
                "message": f"Completed {successful_searches}/{len(search_plan.searches)} searches",
                "status": "warning"
            })
        else:
            save_log({
                "report_id": report_id,
                "stage": "search",
                "message": f"All {successful_searches} searches completed",
                "status": "ok"
            })

        # === WRITING STAGE ===
        save_log({
            "report_id": report_id,
            "stage": "writing",
            "message": "Synthesizing report",
            "status": "running"
        })

        # ... call writer agent ...
        # report_data = await writer_agent.synthesize(search_results)

        save_log({
            "report_id": report_id,
            "stage": "writing",
            "message": "Report synthesis complete",
            "status": "ok"
        })

        # === PERSISTENCE STAGE ===
        save_log({
            "report_id": report_id,
            "stage": "persistence",
            "message": "Saving to database",
            "status": "running"
        })

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
        source_count = 0
        for result in search_results:
            if result and hasattr(result, 'sources'):
                for source in result.sources:
                    save_source({
                        "report_id": saved_report_id,
                        "url": source.url,
                        "reliability": source.reliability,
                        "domain": source.domain,
                        "source_type": source.source_type,
                        "published_at": source.published_at
                    })
                    source_count += 1

        save_log({
            "report_id": report_id,
            "stage": "persistence",
            "message": f"Saved report with {source_count} sources",
            "status": "ok"
        })

        logger.info(f"Research complete: {saved_report_id}")
        return saved_report_id

    except Exception as e:
        logger.error(f"Research pipeline failed: {e}")
        save_log({
            "report_id": report_id,
            "stage": "pipeline",
            "message": f"Pipeline failed: {str(e)}",
            "status": "error"
        })
        raise
```

## Example 2: Source Extraction Helper

```python
from typing import List, Dict, Any
from urllib.parse import urlparse

def extract_sources_from_search_results(
    search_results: List[Any],
    report_id: str
) -> List[str]:
    """
    Extract and save sources from search results.

    Returns list of source IDs.
    """
    from backend.data import save_source

    source_ids = []

    for result in search_results:
        if not result:
            continue

        # Extract sources from result
        # Adapt this to your actual search result structure
        for item in getattr(result, 'items', []):
            url = item.get('url', '')
            if not url:
                continue

            domain = urlparse(url).netloc

            source_data = {
                "report_id": report_id,
                "url": url,
                "reliability": calculate_reliability(item),
                "domain": domain,
                "source_type": classify_source_type(domain),
                "published_at": item.get('published_date')
            }

            try:
                source_id = save_source(source_data)
                source_ids.append(source_id)
            except Exception as e:
                logger.warning(f"Failed to save source {url}: {e}")
                continue

    return source_ids


def calculate_reliability(item: Dict[str, Any]) -> float:
    """Calculate source reliability score (0.0 to 1.0)."""
    base_score = 0.5

    # Boost for certain domains
    domain = urlparse(item.get('url', '')).netloc.lower()

    if any(tld in domain for tld in ['.gov', '.edu']):
        base_score += 0.3
    elif 'arxiv' in domain or 'scholar' in domain:
        base_score += 0.25

    # Boost for recent content
    if item.get('published_date'):
        # More recent = more reliable (simplified)
        base_score += 0.1

    # Cap at 1.0
    return min(base_score, 1.0)


def classify_source_type(domain: str) -> str:
    """Classify source type based on domain."""
    domain_lower = domain.lower()

    gov_domains = ['.gov', '.mil']
    academic_domains = ['edu', 'scholar', 'arxiv', 'pubmed', 'jstor']
    forum_domains = ['reddit', 'hackernews', 'stackoverflow', 'github']
    blog_domains = ['medium', 'substack', 'blogger', 'wordpress']
    media_domains = [
        'nytimes', 'bbc', 'reuters', 'ap.org', 'bloomberg',
        'techcrunch', 'wired', 'arstechnica', 'theverge'
    ]

    if any(tld in domain_lower for tld in gov_domains):
        return 'gov'
    elif any(term in domain_lower for term in academic_domains):
        return 'academic'
    elif any(term in domain_lower for term in forum_domains):
        return 'forum'
    elif any(term in domain_lower for term in blog_domains):
        return 'blog'
    elif any(term in domain_lower for term in media_domains):
        return 'media'
    else:
        return 'unknown'
```

## Example 3: Gradio History UI

```python
import gradio as gr
from backend.data import get_all_reports, get_report, get_sources_for_report, get_logs_for_report

def create_history_ui():
    """Create Gradio history tab."""

    def load_report_list(limit: int = 10):
        """Load recent reports as a table."""
        reports = get_all_reports(limit=limit)

        if not reports:
            return [["-", "-", "-", "-", "-"]]

        # Convert to table format
        table_data = []
        for report in reports:
            table_data.append([
                report['id'][:8] + "...",  # Short ID
                report['query'][:50] + ("..." if len(report['query']) > 50 else ""),
                report['mode'],
                report['confidence_score'],
                report['created_at'][:19]  # Remove milliseconds
            ])

        return table_data

    def view_report(report_id_short: str):
        """View full report by short ID."""
        # Get full ID from table (would need to track mapping)
        # For now, assume we have the full ID

        reports = get_all_reports(limit=100)
        report = None
        for r in reports:
            if r['id'].startswith(report_id_short.replace("...", "")):
                report = r
                break

        if not report:
            return "Report not found."

        # Get sources and logs
        sources = get_sources_for_report(report['id'])
        logs = get_logs_for_report(report['id'])

        # Build markdown
        md = f"""# {report['query']}

**Mode:** {report['mode']} | **Created:** {report['created_at']} | **Confidence:** {report['confidence_score']:.0%}

---

## Summary

{report['summary']}

## Goals

{report['goals']}

## Methodology

{report['methodology']}

## Key Findings

{report['findings']}

## Risks

{report['risks']}

## Opportunities

{report['opportunities']}

## Recommendations

{report['recommendations']}

---

## Sources ({len(sources)})

"""
        for i, source in enumerate(sources, 1):
            md += f"{i}. **{source['domain']}** - [{source['source_type']}] (Reliability: {source['reliability']:.0%})\n"
            md += f"   {source['url']}\n\n"

        md += f"\n---\n\n## Pipeline Logs ({len(logs)})\n\n"
        for log in logs:
            status_emoji = {
                "running": "🔄",
                "ok": "✅",
                "warning": "⚠️",
                "error": "❌"
            }.get(log['status'], "ℹ️")

            md += f"- {status_emoji} **{log['stage']}**: {log['message']} ({log['timestamp'][:19]})\n"

        return md

    # Create UI
    with gr.Column():
        gr.Markdown("## Research History")

        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh", size="sm")
            limit_slider = gr.Slider(5, 50, value=10, step=5, label="Results")

        # Reports table
        reports_table = gr.Dataframe(
            headers=["ID", "Query", "Mode", "Confidence", "Created"],
            datatype=["str", "str", "str", "number", "str"],
            label="Recent Reports"
        )

        # View report section
        gr.Markdown("### Report Details")
        report_id_input = gr.Textbox(
            label="Report ID (copy from table)",
            placeholder="e.g., 4f3a2b1c..."
        )
        view_btn = gr.Button("View Full Report")
        report_output = gr.Markdown()

        # Event handlers
        refresh_btn.click(
            load_report_list,
            inputs=[limit_slider],
            outputs=[reports_table]
        )

        view_btn.click(
            view_report,
            inputs=[report_id_input],
            outputs=[report_output]
        )

        # Load on mount
        reports_table.value = load_report_list(10)

    return reports_table, report_output
```

## Example 4: Error Handling Patterns

```python
from backend.data import save_report, save_source, save_log
import logging

logger = logging.getLogger(__name__)

# Pattern 1: Graceful Degradation
def save_with_fallback(report_data, report_id):
    """Save report with graceful degradation."""
    try:
        saved_id = save_report(report_data)
        save_log({
            "report_id": report_id,
            "stage": "persistence",
            "message": "Report saved successfully",
            "status": "ok"
        })
        return saved_id
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        save_log({
            "report_id": report_id,
            "stage": "persistence",
            "message": f"Save failed: {str(e)}",
            "status": "error"
        })
        # Return None but don't crash pipeline
        return None


# Pattern 2: Retry with Backoff
import time

def save_with_retry(report_data, max_retries=3):
    """Save with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            return save_report(report_data)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                raise
            else:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)


# Pattern 3: Batch Save with Partial Success
def save_sources_batch(sources, report_id):
    """Save multiple sources, track successes and failures."""
    successes = []
    failures = []

    for source in sources:
        try:
            source_id = save_source({
                **source,
                "report_id": report_id
            })
            successes.append(source_id)
        except Exception as e:
            logger.warning(f"Failed to save source {source.get('url')}: {e}")
            failures.append({
                "source": source,
                "error": str(e)
            })

    # Log results
    if failures:
        save_log({
            "report_id": report_id,
            "stage": "persistence",
            "message": f"Saved {len(successes)}/{len(sources)} sources",
            "status": "warning" if successes else "error"
        })
    else:
        save_log({
            "report_id": report_id,
            "stage": "persistence",
            "message": f"Saved all {len(successes)} sources",
            "status": "ok"
        })

    return successes, failures


# Pattern 4: Validation Before Save
def validate_and_save_report(report_data):
    """Validate report data before saving."""

    # Check required fields
    required = [
        "query", "mode", "summary", "goals", "methodology",
        "findings", "risks", "opportunities", "recommendations",
        "confidence_score"
    ]

    missing = [f for f in required if not report_data.get(f)]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    # Check confidence score
    score = report_data.get("confidence_score", 0)
    if not isinstance(score, (int, float)) or not (0 <= score <= 1):
        raise ValueError(f"Invalid confidence_score: {score}")

    # Check mode
    if report_data.get("mode") not in ["quick", "deep"]:
        raise ValueError(f"Invalid mode: {report_data.get('mode')}")

    # All valid, save
    return save_report(report_data)
```

## Example 5: Analytics Queries

```python
from backend.data.db import get_connection
from typing import Dict, List

def get_research_analytics() -> Dict[str, any]:
    """Get analytics on research history."""

    with get_connection() as conn:
        cursor = conn.cursor()

        # Total reports
        cursor.execute("SELECT COUNT(*) as total FROM reports")
        total_reports = cursor.fetchone()['total']

        # Reports by mode
        cursor.execute("""
            SELECT mode, COUNT(*) as count
            FROM reports
            GROUP BY mode
        """)
        by_mode = {row['mode']: row['count'] for row in cursor.fetchall()}

        # Average confidence
        cursor.execute("SELECT AVG(confidence_score) as avg FROM reports")
        avg_confidence = cursor.fetchone()['avg']

        # Most common source types
        cursor.execute("""
            SELECT source_type, COUNT(*) as count
            FROM sources
            GROUP BY source_type
            ORDER BY count DESC
            LIMIT 5
        """)
        top_sources = [
            {"type": row['source_type'], "count": row['count']}
            for row in cursor.fetchall()
        ]

        # Recent activity (reports per day, last 7 days)
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM reports
            WHERE created_at >= DATE('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        recent_activity = [
            {"date": row['date'], "count": row['count']}
            for row in cursor.fetchall()
        ]

        return {
            "total_reports": total_reports,
            "by_mode": by_mode,
            "avg_confidence": avg_confidence,
            "top_source_types": top_sources,
            "recent_activity": recent_activity
        }


def get_low_confidence_reports(threshold: float = 0.6) -> List[Dict]:
    """Find reports with low confidence scores."""

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, query, confidence_score, created_at
            FROM reports
            WHERE confidence_score < ?
            ORDER BY confidence_score ASC
            LIMIT 10
        """, (threshold,))

        return [dict(row) for row in cursor.fetchall()]
```

## Example 6: Export/Backup

```python
import json
from datetime import datetime
from backend.data import get_all_reports, get_sources_for_report

def export_all_reports_to_json(output_file: str = None):
    """Export all reports with sources to JSON."""

    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"reports_backup_{timestamp}.json"

    reports = get_all_reports(limit=1000)  # Adjust as needed
    export_data = []

    for report in reports:
        sources = get_sources_for_report(report['id'])

        export_data.append({
            "report": report,
            "sources": sources
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(reports)} reports to {output_file}")
    return output_file
```

---

**See Also:**
- [API Reference](README.md)
- [Integration Guide](INTEGRATION.md)
- [Quick Reference](QUICKSTART.md)
