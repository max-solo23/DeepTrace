"""
Test script for database integration.

Tests that reports are saved to the database after research completion.
"""
import asyncio
from dotenv import load_dotenv
from backend.app.core.orchestrator import ResearchManager
from backend.app.core import ResearchMode
from backend.app.data import init_db
import sqlite3

# Load environment
load_dotenv(override=True)

async def test_database_integration():
    """Test that research saves to database."""
    print("=" * 60)
    print("DATABASE INTEGRATION TEST")
    print("=" * 60)

    # 1. Initialize database
    print("\n1. Initializing database...")
    try:
        init_db()
        print("   [OK] Database initialized")
    except Exception as e:
        print(f"   [FAIL] Failed to initialize database: {e}")
        return False

    # 2. Run a quick research query
    print("\n2. Running test research query...")
    print("   Query: 'What is Python?'")
    print("   Mode: QUICK")

    manager = ResearchManager()

    try:
        print("\n   --- Research Output ---")
        async for chunk in manager.run("What is Python?", mode=ResearchMode.QUICK):
            # Print only key status updates (not full report)
            if "**" in chunk and len(chunk) < 500:
                print(f"   {chunk.split('**')[-2] if '**' in chunk else chunk[:100]}")

        print("   --- End Output ---")
        print("\n   [OK] Research completed")
    except Exception as e:
        print(f"\n   [FAIL] Research failed: {e}")
        return False

    # 3. Verify report saved to database
    print("\n3. Verifying database save...")
    try:
        conn = sqlite3.connect("research.db")
        cursor = conn.cursor()

        # Check if reports table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reports'")
        if not cursor.fetchone():
            print("   [FAIL] Reports table does not exist")
            return False
        print("   [OK] Reports table exists")

        # Check if report was saved
        cursor.execute("SELECT id, query, mode, confidence_score, created_at FROM reports ORDER BY created_at DESC LIMIT 1")
        report = cursor.fetchone()

        if not report:
            print("   [FAIL] No reports found in database")
            return False

        report_id, query, mode, confidence, created_at = report
        print(f"   [OK] Report saved successfully!")
        print(f"      - ID: {report_id}")
        print(f"      - Query: {query}")
        print(f"      - Mode: {mode}")
        print(f"      - Confidence: {confidence:.2f}")
        print(f"      - Created: {created_at}")

        # Check total reports
        cursor.execute("SELECT COUNT(*) FROM reports")
        count = cursor.fetchone()[0]
        print(f"\n   Total reports in database: {count}")

        conn.close()

    except Exception as e:
        print(f"   [FAIL] Database verification failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("[SUCCESS] DATABASE INTEGRATION TEST PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_database_integration())
    exit(0 if success else 1)
