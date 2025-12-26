"""Research mode types and configuration.

This module defines the research modes (Quick vs Deep) and their associated
configuration parameters for source counts and performance targets.
"""

from enum import Enum


class ResearchMode(Enum):
    """Research mode enum defining quick vs deep research approaches.

    QUICK: Faster research with fewer sources (4-6 sources, ~2 min target)
    DEEP: Comprehensive research with more sources (10-14 sources, ~8 min target)
    """
    QUICK = "quick"
    DEEP = "deep"


# Absolute hard cap on sources - NEVER exceed this limit
MAX_SOURCES_ABSOLUTE = 20

MODE_CONFIG = {
    ResearchMode.QUICK: {
        "min_sources": 4,
        "max_sources": 6,
        "target_time": 120,  # seconds (2 minutes)
        "description": "Quick research mode with 4-6 sources in ~2 minutes"
    },
    ResearchMode.DEEP: {
        "min_sources": 10,
        "max_sources": 14,
        "target_time": 480,  # seconds (8 minutes)
        "description": "Deep research mode with 10-14 sources in ~8 minutes"
    }
}


def get_mode_config(mode: ResearchMode) -> dict:
    """Get configuration for a research mode.

    Args:
        mode: The research mode to get config for

    Returns:
        Dictionary with mode configuration (min_sources, max_sources, target_time)
    """
    return MODE_CONFIG[mode]


def validate_source_count(count: int, mode: ResearchMode) -> int:
    """Validate and adjust source count to be within mode limits.

    Args:
        count: Requested source count
        mode: Research mode to validate against

    Returns:
        Adjusted source count within valid range
    """
    config = get_mode_config(mode)

    # Enforce absolute hard cap first
    if count > MAX_SOURCES_ABSOLUTE:
        print(f"WARNING: Source count {count} exceeds absolute limit {MAX_SOURCES_ABSOLUTE}. Capping to {MAX_SOURCES_ABSOLUTE}.")
        count = MAX_SOURCES_ABSOLUTE

    # Enforce mode-specific max
    if count > config["max_sources"]:
        print(f"WARNING: Source count {count} exceeds {mode.value} mode limit {config['max_sources']}. Capping to {config['max_sources']}.")
        count = config["max_sources"]

    # Warn if below minimum
    if count < config["min_sources"]:
        print(f"WARNING: Source count {count} below {mode.value} mode minimum {config['min_sources']}. Using {count} anyway.")

    return count
