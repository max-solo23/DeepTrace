"""
Confidence Scoring Module

Calculates confidence scores for research reports based on:
- Number of sources
- Source quality indicators
- Information consistency
- Recency of data

Confidence scores range from 0.0 (no confidence) to 1.0 (high confidence).
"""

import re
from typing import List


def calculate_confidence(num_sources: int, search_results: List[str]) -> float:
    """
    Calculate confidence score for a research report.

    Args:
        num_sources: Number of sources successfully retrieved
        search_results: List of search result summaries

    Returns:
        float: Confidence score between 0.0 and 1.0

    Algorithm:
        - Base score starts at 0.3 (minimum confidence)
        - Source count bonus: +0.05 per source (max +0.35 for 7+ sources)
        - Quality indicators: +0.05 per indicator found (max +0.25)
        - Consistency check: +0.10 if multiple sources agree

    Quality indicators:
        - Academic/research mentions (.edu, study, research, university)
        - Government sources (.gov, policy, regulation)
        - Technical depth (specific numbers, data, statistics)
        - Recent information (2024, 2025, recent, latest)
        - Reputable organizations (WHO, NASA, NIH, etc.)
    """
    if num_sources == 0:
        return 0.0

    # Base confidence score
    base_score = 0.3

    # Source count contribution (0.0 to 0.35)
    # More sources = higher confidence, but with diminishing returns
    source_score = min(num_sources * 0.05, 0.35)

    # Quality indicators scoring (0.0 to 0.25)
    quality_score = _calculate_quality_score(search_results)

    # Consistency scoring (0.0 to 0.10)
    consistency_score = _calculate_consistency_score(search_results)

    # Combine all scores
    total_score = base_score + source_score + quality_score + consistency_score

    # Ensure score is within valid range
    return min(max(total_score, 0.0), 1.0)


def _calculate_quality_score(search_results: List[str]) -> float:
    """
    Calculate quality score based on content indicators.

    Returns value between 0.0 and 0.25
    """
    if not search_results:
        return 0.0

    quality_indicators = {
        'academic': [r'\.edu', r'\bstudy\b', r'\bresearch\b', r'\buniversity\b',
                    r'\bjournal\b', r'\bpublished\b', r'\bpaper\b'],
        'government': [r'\.gov', r'\bpolicy\b', r'\bregulation\b', r'\bofficial\b'],
        'technical': [r'\d+%', r'\d+\.\d+', r'\bdata\b', r'\bstatistics\b',
                     r'\bmetrics\b', r'\banalysis\b'],
        'recent': [r'2025', r'2024', r'\brecent\b', r'\blatest\b', r'\bcurrent\b'],
        'reputable': [r'\bWHO\b', r'\bNASA\b', r'\bNIH\b', r'\bIEEE\b',
                     r'\bNature\b', r'\bScience\b', r'\bReuters\b', r'\bBloomberg\b']
    }

    # Combine all results into one text
    combined_text = ' '.join(search_results)

    # Count unique indicator categories found
    categories_found = 0
    for category, patterns in quality_indicators.items():
        for pattern in patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                categories_found += 1
                break  # Count each category only once

    # Convert to score: 0.05 per category, max 0.25 (5 categories)
    max_categories = len(quality_indicators)
    quality_score = (categories_found / max_categories) * 0.25

    return quality_score


def _calculate_consistency_score(search_results: List[str]) -> float:
    """
    Calculate consistency score based on overlapping themes/concepts.

    Returns value between 0.0 and 0.10

    Simple heuristic: if we have multiple sources and they share common
    meaningful words (filtered for stopwords), this indicates consistency.
    """
    if len(search_results) < 2:
        return 0.0

    # Extract meaningful words (crude but effective heuristic)
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
                'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
                'does', 'did', 'will', 'would', 'could', 'should', 'may',
                'might', 'must', 'can', 'this', 'that', 'these', 'those'}

    # Get word frequency across all results
    word_counts = {}
    for result in search_results:
        words = re.findall(r'\b[a-z]{4,}\b', result.lower())
        for word in words:
            if word not in stopwords:
                word_counts[word] = word_counts.get(word, 0) + 1

    # Count words that appear in multiple sources
    if not word_counts:
        return 0.0

    multi_source_words = sum(1 for count in word_counts.values() if count >= 2)
    total_unique_words = len(word_counts)

    if total_unique_words == 0:
        return 0.0

    # Ratio of shared words to unique words, scaled to 0.10 max
    consistency_ratio = multi_source_words / total_unique_words
    consistency_score = min(consistency_ratio * 0.10, 0.10)

    return consistency_score


def get_confidence_label(score: float) -> str:
    """
    Convert numeric confidence score to human-readable label.

    Args:
        score: Confidence score between 0.0 and 1.0

    Returns:
        str: Label describing confidence level
    """
    if score >= 0.8:
        return "High Confidence"
    elif score >= 0.6:
        return "Moderate-High Confidence"
    elif score >= 0.4:
        return "Moderate Confidence"
    elif score >= 0.2:
        return "Low-Moderate Confidence"
    else:
        return "Low Confidence"
