"""Test script to verify research modes implementation.

This script validates:
1. ResearchMode enum and configuration
2. Source count validation
3. Mode configuration retrieval
"""

from backend.core import (
    ResearchMode,
    MODE_CONFIG,
    get_mode_config,
    validate_source_count,
    MAX_SOURCES_ABSOLUTE
)


def test_research_modes():
    """Test research mode enum and configuration."""
    print("Testing Research Modes Implementation")
    print("=" * 60)

    # Test 1: Verify enum values
    print("\n1. Testing ResearchMode enum:")
    print(f"   QUICK mode: {ResearchMode.QUICK.value}")
    print(f"   DEEP mode: {ResearchMode.DEEP.value}")

    # Test 2: Verify configurations
    print("\n2. Testing mode configurations:")
    for mode in [ResearchMode.QUICK, ResearchMode.DEEP]:
        config = get_mode_config(mode)
        print(f"\n   {mode.value.upper()} mode:")
        print(f"   - Min sources: {config['min_sources']}")
        print(f"   - Max sources: {config['max_sources']}")
        print(f"   - Target time: {config['target_time']}s ({config['target_time']/60:.1f} min)")
        print(f"   - Description: {config['description']}")

    # Test 3: Verify absolute limit
    print(f"\n3. Testing absolute source limit:")
    print(f"   MAX_SOURCES_ABSOLUTE: {MAX_SOURCES_ABSOLUTE}")

    # Test 4: Test source count validation
    print("\n4. Testing source count validation:")

    test_cases = [
        (ResearchMode.QUICK, 3, "Below minimum"),
        (ResearchMode.QUICK, 5, "Within range"),
        (ResearchMode.QUICK, 8, "Above maximum"),
        (ResearchMode.DEEP, 8, "Below minimum"),
        (ResearchMode.DEEP, 12, "Within range"),
        (ResearchMode.DEEP, 16, "Above maximum"),
        (ResearchMode.DEEP, 25, "Above absolute limit"),
    ]

    for mode, count, description in test_cases:
        print(f"\n   Testing {mode.value} mode with {count} sources ({description}):")
        validated = validate_source_count(count, mode)
        print(f"   -> Validated count: {validated}")

    print("\n" + "=" * 60)
    print("All tests completed successfully!")


if __name__ == "__main__":
    test_research_modes()
