"""Tests for confidence capping by domain coverage."""

from score_countries import cap_confidence_by_coverage


class TestCapConfidenceByCoverage:
    def test_few_domains_caps_at_low(self):
        """3 or fewer domains -> cap at 'low'."""
        assert cap_confidence_by_coverage("high", 3) == "low"
        assert cap_confidence_by_coverage("moderate", 2) == "low"
        assert cap_confidence_by_coverage("low", 1) == "low"

    def test_medium_domains_caps_at_moderate(self):
        """4-5 domains -> cap at 'moderate'."""
        assert cap_confidence_by_coverage("high", 5) == "moderate"
        assert cap_confidence_by_coverage("high", 4) == "moderate"

    def test_many_domains_allows_high(self):
        """6+ domains -> no cap."""
        assert cap_confidence_by_coverage("high", 6) == "high"
        assert cap_confidence_by_coverage("high", 7) == "high"

    def test_already_below_cap_unchanged(self):
        """If confidence is already below cap, return unchanged."""
        assert cap_confidence_by_coverage("very_low", 3) == "very_low"
        assert cap_confidence_by_coverage("low", 5) == "low"

    def test_very_low_never_raised(self):
        """Capping never raises confidence."""
        assert cap_confidence_by_coverage("very_low", 7) == "very_low"
