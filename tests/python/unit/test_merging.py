"""Tests for multi-source domain merging."""

from score_countries import merge_domain_scores


class TestMergeDomainScores:
    def test_scores_averaged(self, sample_domain_a, sample_domain_b):
        """Two sources for same domain -> scores averaged."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        assert merged['score'] == 50  # (60 + 40) / 2

    def test_indicators_merged(self, sample_domain_a, sample_domain_b):
        """Indicator lists are concatenated."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        assert len(merged['indicators']) == 2
        keys = [i['key'] for i in merged['indicators']]
        assert 'wb_wgi_corruption' in keys
        assert 'vdem_rule_of_law' in keys

    def test_sources_merged(self, sample_domain_a, sample_domain_b):
        """Source lists are concatenated."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        assert 'wb_wgi_corruption' in merged['sources']
        assert 'wb_reg_quality' in merged['sources']
        assert 'vdem_rule_of_law' in merged['sources']

    def test_confidence_recalculated(self, sample_domain_a, sample_domain_b):
        """Confidence recalculated from combined n_indicators, n_sources, most_recent_year."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        # Combined: 3 indicators, 2 sources, year 2024
        # completeness=2 (3 indicators), diversity=2 (2 sources), recency=3 (2024)
        # total=7 -> 'high'
        assert merged['confidence'] == 'high'

    def test_trend_preserves_known(self, sample_domain_a, sample_domain_b):
        """Known trend from source A preserved when B is unknown."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        assert merged['trend'] == 'rising'

    def test_most_recent_year_takes_max(self, sample_domain_a, sample_domain_b):
        """Internal _most_recent_year is max of both sources."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        assert merged['_most_recent_year'] == 2024

    def test_justification_combined(self, sample_domain_a, sample_domain_b):
        """Justification detail strings are concatenated."""
        merged = merge_domain_scores(sample_domain_a, sample_domain_b)
        assert 'World Bank' in merged['justification_detail']
        assert 'V-Dem' in merged['justification_detail']
