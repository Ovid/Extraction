"""Tests for World Bank indicator loading and parsing."""

from pathlib import Path

from score_countries import EXCLUDE_CODES, load_indicator

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestLoadIndicator:
    def test_loads_csv_successfully(self):
        df = load_indicator(FIXTURES / "worldbank" / "wb_gini.csv")
        assert not df.empty
        assert "country_code" in df.columns
        assert "value" in df.columns

    def test_most_recent_year_per_country(self):
        df = load_indicator(FIXTURES / "worldbank" / "wb_gini.csv")
        usa = df[df["country_code"] == "USA"]
        assert len(usa) == 1
        assert usa.iloc[0]["year"] == 2020

    def test_excludes_aggregate_codes(self):
        df = load_indicator(FIXTURES / "worldbank" / "wb_gini.csv")
        for code in EXCLUDE_CODES:
            assert code not in df["country_code"].values

    def test_filters_non_alpha3(self):
        df = load_indicator(FIXTURES / "worldbank" / "wb_gini.csv")
        assert all(len(c) == 3 for c in df["country_code"].values)

    def test_missing_file_returns_empty(self):
        df = load_indicator(FIXTURES / "worldbank" / "nonexistent.csv")
        assert df.empty
