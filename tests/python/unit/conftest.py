"""Shared test fixtures for the Extraction Index test suite."""

import pytest


@pytest.fixture
def sample_domain_a():
    """A domain entry from source A (e.g., World Bank)."""
    return {
        "score": 60,
        "confidence": "moderate",
        "trend": "rising",
        "sources": ["wb_wgi_corruption", "wb_reg_quality"],
        "indicators": [
            {
                "key": "wb_wgi_corruption",
                "question": "How well is corruption controlled?",
                "label": "High",
                "facts": ["Control of corruption index: -0.50"],
            },
        ],
        "justification_detail": "Auto-scored from World Bank data. WGI Control of Corruption: -0.500 (normalized: 60).",
        "_n_indicators": 2,
        "_n_sources": 1,
        "_most_recent_year": 2022,
    }


@pytest.fixture
def sample_domain_b():
    """A domain entry from source B (e.g., V-Dem)."""
    return {
        "score": 40,
        "confidence": "moderate",
        "trend": "unknown",
        "sources": ["vdem_rule_of_law"],
        "indicators": [
            {
                "key": "vdem_rule_of_law",
                "question": "How strong is the rule of law?",
                "label": "Moderate",
                "facts": ["Rule of law index: 0.65"],
            },
        ],
        "justification_detail": "Auto-scored from V-Dem. Rule of Law: 0.650 (normalized: 40).",
        "_n_indicators": 1,
        "_n_sources": 1,
        "_most_recent_year": 2024,
    }


@pytest.fixture
def sample_all_indicator_raw():
    """Raw indicator values for peer comparison tests."""
    return {
        "wb_gini": {
            "USA": 41.5,
            "CAN": 33.3,
            "DNK": 28.2,
            "SWE": 27.6,
            "NOR": 25.6,
            "FIN": 27.1,
            "BRA": 53.4,
            "ARG": 42.3,
            "CHL": 44.9,
            "COL": 51.3,
            "NGA": 35.1,
            "GHA": 43.5,
            "SEN": 40.3,
            "CIV": 37.2,
        },
    }
