"""
Simple test script to verify database layer functionality.

Run this to ensure the database layer is working correctly.
"""

import logging
from datetime import datetime
from backend.data import (
    init_db,
    save_report,
    get_report,
    get_all_reports,
    save_source,
    get_sources_for_report,
    save_log,
    get_logs_for_report,
)

# Configure logging to see database operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_database_layer():
    """Test all database layer functions."""

    logger.info("=" * 60)
    logger.info("Testing DeepTrace Database Layer")
    logger.info("=" * 60)

    # Step 1: Initialize database
    logger.info("\n1. Initializing database...")
    try:
        init_db()
        logger.info("✓ Database initialized successfully")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return

    # Step 2: Create a test report
    logger.info("\n2. Creating test report...")
    test_report_data = {
        "query": "What are the latest trends in AI agents?",
        "mode": "quick",
        "summary": "AI agents are rapidly evolving with multi-agent systems becoming mainstream.",
        "goals": "Understand current AI agent landscape and identify key trends.",
        "methodology": "Web search using 3 targeted queries across different sources.",
        "findings": "Key findings include rise of LangGraph, CrewAI, and AutoGPT frameworks.",
        "competitors": "OpenAI, Anthropic, Google DeepMind leading the space.",
        "risks": "Potential for misuse, reliability concerns, and regulatory uncertainty.",
        "opportunities": "Growing enterprise adoption, new tooling ecosystems emerging.",
        "recommendations": "Focus on reliability and observability for production systems.",
        "confidence_score": 0.85
    }

    try:
        report_id = save_report(test_report_data)
        logger.info(f"✓ Report saved with ID: {report_id}")
    except Exception as e:
        logger.error(f"✗ Report save failed: {e}")
        return

    # Step 3: Retrieve the report
    logger.info("\n3. Retrieving report...")
    try:
        retrieved_report = get_report(report_id)
        if retrieved_report:
            logger.info(f"✓ Report retrieved successfully")
            logger.info(f"   Query: {retrieved_report['query']}")
            logger.info(f"   Mode: {retrieved_report['mode']}")
            logger.info(f"   Confidence: {retrieved_report['confidence_score']}")
        else:
            logger.error("✗ Report not found")
            return
    except Exception as e:
        logger.error(f"✗ Report retrieval failed: {e}")
        return

    # Step 4: Save test sources
    logger.info("\n4. Saving test sources...")
    test_sources = [
        {
            "report_id": report_id,
            "url": "https://www.deepmind.google/research/ai-agents",
            "reliability": 0.95,
            "domain": "deepmind.google",
            "source_type": "academic",
            "published_at": "2024-01-15T10:00:00"
        },
        {
            "report_id": report_id,
            "url": "https://techcrunch.com/ai-agents-2024",
            "reliability": 0.70,
            "domain": "techcrunch.com",
            "source_type": "media",
            "published_at": None  # Optional field
        },
        {
            "report_id": report_id,
            "url": "https://github.com/langchain-ai/langgraph",
            "reliability": 0.80,
            "domain": "github.com",
            "source_type": "unknown",
            "published_at": None
        }
    ]

    source_ids = []
    for source_data in test_sources:
        try:
            source_id = save_source(source_data)
            source_ids.append(source_id)
            logger.info(f"✓ Source saved: {source_data['domain']}")
        except Exception as e:
            logger.error(f"✗ Source save failed: {e}")

    # Step 5: Retrieve sources for report
    logger.info("\n5. Retrieving sources for report...")
    try:
        sources = get_sources_for_report(report_id)
        logger.info(f"✓ Retrieved {len(sources)} sources")
        for source in sources:
            logger.info(f"   - {source['domain']} (reliability: {source['reliability']})")
    except Exception as e:
        logger.error(f"✗ Source retrieval failed: {e}")

    # Step 6: Save test logs
    logger.info("\n6. Saving test logs...")
    test_logs = [
        {
            "report_id": report_id,
            "stage": "planning",
            "message": "Generating search plan for query",
            "status": "running"
        },
        {
            "report_id": report_id,
            "stage": "planning",
            "message": "Search plan generated with 3 queries",
            "status": "ok"
        },
        {
            "report_id": report_id,
            "stage": "search",
            "message": "Executing parallel web searches",
            "status": "running"
        },
        {
            "report_id": report_id,
            "stage": "search",
            "message": "All searches completed successfully",
            "status": "ok"
        },
        {
            "report_id": report_id,
            "stage": "writing",
            "message": "Synthesizing report from search results",
            "status": "running"
        },
        {
            "report_id": report_id,
            "stage": "writing",
            "message": "Report generation complete",
            "status": "ok"
        }
    ]

    log_ids = []
    for log_data in test_logs:
        try:
            log_id = save_log(log_data)
            log_ids.append(log_id)
            logger.info(f"✓ Log saved: {log_data['stage']} - {log_data['status']}")
        except Exception as e:
            logger.error(f"✗ Log save failed: {e}")

    # Step 7: Retrieve logs for report
    logger.info("\n7. Retrieving logs for report...")
    try:
        logs = get_logs_for_report(report_id)
        logger.info(f"✓ Retrieved {len(logs)} logs")
        for log in logs:
            logger.info(f"   [{log['status']}] {log['stage']}: {log['message']}")
    except Exception as e:
        logger.error(f"✗ Log retrieval failed: {e}")

    # Step 8: Get all reports
    logger.info("\n8. Retrieving all reports...")
    try:
        all_reports = get_all_reports(limit=10)
        logger.info(f"✓ Retrieved {len(all_reports)} reports")
        for report in all_reports:
            logger.info(f"   - {report['query'][:50]}... ({report['mode']}, {report['created_at']})")
    except Exception as e:
        logger.error(f"✗ All reports retrieval failed: {e}")

    # Step 9: Test validation errors
    logger.info("\n9. Testing validation (should fail gracefully)...")

    # Test invalid mode
    try:
        invalid_report = test_report_data.copy()
        invalid_report["mode"] = "invalid_mode"
        save_report(invalid_report)
        logger.error("✗ Validation should have caught invalid mode")
    except ValueError as e:
        logger.info(f"✓ Validation caught invalid mode: {e}")

    # Test missing required field
    try:
        incomplete_report = {"query": "test"}
        save_report(incomplete_report)
        logger.error("✗ Validation should have caught missing fields")
    except ValueError as e:
        logger.info(f"✓ Validation caught missing fields: {e}")

    # Test invalid source type
    try:
        invalid_source = test_sources[0].copy()
        invalid_source["source_type"] = "invalid_type"
        save_source(invalid_source)
        logger.error("✗ Validation should have caught invalid source_type")
    except ValueError as e:
        logger.info(f"✓ Validation caught invalid source_type: {e}")

    # Test invalid confidence score
    try:
        invalid_report = test_report_data.copy()
        invalid_report["confidence_score"] = 1.5  # Out of range
        save_report(invalid_report)
        logger.error("✗ Validation should have caught invalid confidence_score")
    except ValueError as e:
        logger.info(f"✓ Validation caught invalid confidence_score: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("Database layer test completed successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    test_database_layer()
