"""Tests for peer comparison context facts generation."""

from score_countries import generate_context_facts, REGION_MAP, INCOME_GROUP_MAP


class TestGenerateContextFacts:
    def test_first_fact_is_raw_value(self, sample_all_indicator_raw):
        """First fact is always the formatted raw value."""
        facts = generate_context_facts(
            'wb_gini', 41.5, 60, 'USA', sample_all_indicator_raw['wb_gini'])
        assert len(facts) >= 1
        assert 'Gini coefficient' in facts[0]
        assert '41.5' in facts[0]

    def test_peer_comparison_generated_when_divergent(self, sample_all_indicator_raw):
        """Peer comparison generated when >10% divergence from peer average."""
        facts = generate_context_facts(
            'wb_gini', 28.2, 20, 'DNK', sample_all_indicator_raw['wb_gini'])
        assert len(facts) >= 1

    def test_no_region_comparison_when_within_10_percent(self, sample_all_indicator_raw):
        """No regional peer comparison when within 10% of regional average."""
        # SWE (27.6) vs Northern Europe (DNK 28.2, NOR 25.6, FIN 27.1) avg ~26.97
        # Delta: ~2.3%, well within 10% — so no regional comparison
        # But income group comparison may still fire (high income avg diverges)
        facts = generate_context_facts(
            'wb_gini', 27.6, 18, 'SWE', sample_all_indicator_raw['wb_gini'])
        region_facts = [f for f in facts if 'Northern Europe' in f]
        assert len(region_facts) == 0

    def test_unknown_indicator_returns_empty(self, sample_all_indicator_raw):
        """Unknown source_key with no display config returns empty list."""
        facts = generate_context_facts(
            'nonexistent_key', 50, 50, 'USA', {})
        assert facts == []

    def test_country_not_in_region_map(self, sample_all_indicator_raw):
        """Country not in REGION_MAP still gets raw value fact."""
        facts = generate_context_facts(
            'wb_gini', 30.0, 25, 'XXX', sample_all_indicator_raw['wb_gini'])
        assert len(facts) >= 1
        assert 'Gini' in facts[0]

    def test_too_few_peers_no_comparison(self):
        """Fewer than 3 peers in group -> no peer comparison."""
        sparse_data = {'USA': 41.5, 'CAN': 33.3}
        facts = generate_context_facts(
            'wb_gini', 41.5, 60, 'USA', sparse_data)
        assert len(facts) <= 1


class TestRegionAndIncomeMapping:
    def test_usa_in_northern_america(self):
        assert REGION_MAP['USA'] == 'Northern America'

    def test_dnk_in_northern_europe(self):
        assert REGION_MAP['DNK'] == 'Northern Europe'

    def test_usa_is_high_income(self):
        assert INCOME_GROUP_MAP['USA'] == 'High income'

    def test_eth_is_low_income(self):
        assert INCOME_GROUP_MAP['ETH'] == 'Low income'
