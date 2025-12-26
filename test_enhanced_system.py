"""
Test script for enhanced agent system

Tests:
1. Confidence scoring
2. Retry logic
3. ReportData schema
4. Clarifying agent
"""

import asyncio
from backend.core import calculate_confidence, get_confidence_label
from writer_agent import ReportData
from clarifying_agent import ClarificationResult


def test_confidence_scoring():
    """Test confidence scoring with different scenarios"""
    print("\n=== Testing Confidence Scoring ===")

    # Test 1: No sources
    score1 = calculate_confidence(0, [])
    print(f"Test 1 - No sources: {score1:.2f} - {get_confidence_label(score1)}")
    assert score1 == 0.0, "No sources should return 0.0"

    # Test 2: Few sources with basic content
    score2 = calculate_confidence(3, [
        "Basic information about the topic",
        "Some additional details here",
        "More context provided"
    ])
    print(f"Test 2 - Basic sources: {score2:.2f} - {get_confidence_label(score2)}")
    assert 0.3 <= score2 <= 0.6, "Basic sources should be low-moderate confidence"

    # Test 3: Many sources with quality indicators
    score3 = calculate_confidence(10, [
        "According to a study published in 2024 by MIT researchers",
        "Government data from .gov shows statistics of 45.7%",
        "Recent research from Nature journal indicates",
        "Analysis from Bloomberg reveals market trends",
        "IEEE standards document specifies technical requirements",
        "University research paper from .edu domain",
        "Official policy from government sources",
        "Latest data from 2025 shows improvements",
        "WHO guidelines recommend specific protocols",
        "Published scientific paper with peer review"
    ])
    print(f"Test 3 - Quality sources: {score3:.2f} - {get_confidence_label(score3)}")
    assert 0.7 <= score3 <= 1.0, "Quality sources should be high confidence"

    print("Confidence scoring tests PASSED")


def test_report_data_schema():
    """Test that ReportData schema has all required fields"""
    print("\n=== Testing ReportData Schema ===")

    # Create a test report with all required fields
    report = ReportData(
        summary="Test summary",
        goals="Test goals",
        methodology="Test methodology",
        findings="Test findings",
        competitors="Test competitors",
        risks="Test risks",
        opportunities="Test opportunities",
        recommendations="Test recommendations",
        confidence_score=0.75,
        markdown_report="# Test Report",
        follow_up_questions=["Question 1", "Question 2", "Question 3"]
    )

    # Verify all fields are present
    assert hasattr(report, 'summary'), "Missing summary field"
    assert hasattr(report, 'goals'), "Missing goals field"
    assert hasattr(report, 'methodology'), "Missing methodology field"
    assert hasattr(report, 'findings'), "Missing findings field"
    assert hasattr(report, 'competitors'), "Missing competitors field"
    assert hasattr(report, 'risks'), "Missing risks field"
    assert hasattr(report, 'opportunities'), "Missing opportunities field"
    assert hasattr(report, 'recommendations'), "Missing recommendations field"
    assert hasattr(report, 'confidence_score'), "Missing confidence_score field"
    assert hasattr(report, 'markdown_report'), "Missing markdown_report field"
    assert hasattr(report, 'follow_up_questions'), "Missing follow_up_questions field"

    # Verify confidence score validation
    assert 0.0 <= report.confidence_score <= 1.0, "Confidence score out of range"

    print("ReportData schema tests PASSED")


def test_clarification_result_schema():
    """Test that ClarificationResult schema works"""
    print("\n=== Testing ClarificationResult Schema ===")

    # Create a test clarification result
    result = ClarificationResult(
        needs_clarification=True,
        clarifying_questions=[
            "What specific aspect are you interested in?",
            "What is the timeframe for this research?",
            "Are you looking for technical or business information?"
        ],
        reasoning="Query is too broad and lacks specific context"
    )

    # Verify fields
    assert hasattr(result, 'needs_clarification'), "Missing needs_clarification field"
    assert hasattr(result, 'clarifying_questions'), "Missing clarifying_questions field"
    assert hasattr(result, 'reasoning'), "Missing reasoning field"

    assert isinstance(result.needs_clarification, bool), "needs_clarification should be bool"
    assert isinstance(result.clarifying_questions, list), "clarifying_questions should be list"
    assert len(result.clarifying_questions) == 3, "Should have 3 questions"

    print("ClarificationResult schema tests PASSED")


async def test_retry_logic_import():
    """Test that retry logic can be imported and has correct signature"""
    print("\n=== Testing Retry Logic Import ===")

    from backend.core import retry_with_backoff, with_retry, retry_with_fallback

    # Test that functions exist
    assert callable(retry_with_backoff), "retry_with_backoff should be callable"
    assert callable(with_retry), "with_retry should be callable"
    assert callable(retry_with_fallback), "retry_with_fallback should be callable"

    # Test simple retry scenario
    call_count = 0

    async def test_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Test error")
        return "Success"

    result = await retry_with_backoff(test_func, max_attempts=3, base_delay=0.1)
    assert result == "Success", "Retry should succeed on second attempt"
    assert call_count == 2, "Should have called function twice"

    print("Retry logic tests PASSED")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("ENHANCED AGENT SYSTEM TEST SUITE")
    print("=" * 60)

    try:
        # Synchronous tests
        test_confidence_scoring()
        test_report_data_schema()
        test_clarification_result_schema()

        # Async tests
        asyncio.run(test_retry_logic_import())

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSystem is ready for use.")

    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
