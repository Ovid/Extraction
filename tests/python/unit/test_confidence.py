"""Tests for confidence assessment."""

from score_countries import assess_domain_confidence


class TestAssessDomainConfidence:
    def test_high_confidence(self):
        """4+ indicators, 3+ sources, year >= 2022 -> high."""
        assert assess_domain_confidence(4, 3, 2023) == 'high'

    def test_moderate_confidence(self):
        """2 indicators, 2 sources, year 2020 -> moderate (1+2+2=5)."""
        assert assess_domain_confidence(2, 2, 2020) == 'moderate'

    def test_low_confidence(self):
        """1 indicator, 1 source, year 2016 -> low (0+1+1=2)... wait, check this."""
        # completeness: 1 indicator -> 0 points
        # diversity: 1 source -> 1 point
        # recency: 2016 -> 1 point
        # total = 2 -> very_low, not low!
        assert assess_domain_confidence(1, 1, 2016) == 'very_low'

    def test_very_low_confidence(self):
        """1 indicator, 0 sources, old year -> very_low."""
        assert assess_domain_confidence(1, 0, 2010) == 'very_low'

    def test_no_year_data(self):
        """None year -> recency = 0."""
        assert assess_domain_confidence(1, 1, None) == 'very_low'

    def test_boundary_high_at_7(self):
        """Total = 7 -> high."""
        # 3 indicators (completeness=2), 2 sources (diversity=2), 2022 (recency=3) = 7
        assert assess_domain_confidence(3, 2, 2022) == 'high'

    def test_boundary_moderate_at_5(self):
        """Total = 5 -> moderate."""
        # 2 indicators (completeness=1), 1 source (diversity=1), 2022 (recency=3) = 5
        assert assess_domain_confidence(2, 1, 2022) == 'moderate'

    def test_boundary_low_at_3(self):
        """Total = 3 -> low."""
        # 2 indicators (completeness=1), 2 sources (diversity=2), None (recency=0) = 3
        assert assess_domain_confidence(2, 2, None) == 'low'

    def test_boundary_very_low_at_2(self):
        """Total = 2 -> very_low."""
        # 2 indicators (completeness=1), 1 source (diversity=1), None (recency=0) = 2
        assert assess_domain_confidence(2, 1, None) == 'very_low'

    def test_recency_before_2015(self):
        """Year < 2015 -> recency = 0."""
        # 4 indicators (3), 3 sources (3), 2014 (0) = 6 -> moderate
        assert assess_domain_confidence(4, 3, 2014) == 'moderate'
