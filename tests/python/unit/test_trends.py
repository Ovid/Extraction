"""Tests for trend estimation."""

import pandas as pd

from score_countries import estimate_trend_from_data, estimate_vdem_trend


class TestEstimateTrendFromData:
    def test_rising(self):
        """>=10% increase -> rising."""
        data = pd.DataFrame(
            {
                "year": [2012, 2013, 2019, 2020],
                "value": [100, 100, 115, 115],
            }
        )
        assert estimate_trend_from_data(data, inverted=False) == "rising"

    def test_falling(self):
        """>=10% decrease -> falling."""
        data = pd.DataFrame(
            {
                "year": [2012, 2013, 2019, 2020],
                "value": [100, 100, 85, 85],
            }
        )
        assert estimate_trend_from_data(data, inverted=False) == "falling"

    def test_stable(self):
        """<10% change -> stable."""
        data = pd.DataFrame(
            {
                "year": [2012, 2013, 2019, 2020],
                "value": [100, 100, 105, 105],
            }
        )
        assert estimate_trend_from_data(data, inverted=False) == "stable"

    def test_boundary_exactly_10_percent(self):
        """Exactly 10% change -> stable (< 0.10, not <=)."""
        data = pd.DataFrame(
            {
                "year": [2012, 2013, 2019, 2020],
                "value": [100, 100, 110, 110],
            }
        )
        assert estimate_trend_from_data(data, inverted=False) == "stable"

    def test_inverted_falling_raw_means_rising_extraction(self):
        """For inverted indicators, falling raw = rising extraction."""
        data = pd.DataFrame(
            {
                "year": [2012, 2013, 2019, 2020],
                "value": [100, 100, 85, 85],
            }
        )
        assert estimate_trend_from_data(data, inverted=True) == "rising"

    def test_inverted_rising_raw_means_falling_extraction(self):
        """For inverted indicators, rising raw = falling extraction."""
        data = pd.DataFrame(
            {
                "year": [2012, 2013, 2019, 2020],
                "value": [100, 100, 115, 115],
            }
        )
        assert estimate_trend_from_data(data, inverted=True) == "falling"

    def test_too_few_rows(self):
        """Fewer than 2 data points -> unknown."""
        data = pd.DataFrame({"year": [2020], "value": [50]})
        assert estimate_trend_from_data(data, inverted=False) == "unknown"

    def test_no_recent_data(self):
        """All data before 2018 -> unknown (no recent values)."""
        data = pd.DataFrame(
            {
                "year": [2010, 2012, 2014],
                "value": [100, 105, 110],
            }
        )
        assert estimate_trend_from_data(data, inverted=False) == "unknown"

    def test_no_old_data(self):
        """All data after 2015 -> unknown (no older baseline)."""
        data = pd.DataFrame(
            {
                "year": [2018, 2019, 2020],
                "value": [100, 105, 110],
            }
        )
        assert estimate_trend_from_data(data, inverted=False) == "unknown"

    def test_older_baseline_zero(self):
        """Older baseline is 0 -> unknown (avoid division by zero)."""
        data = pd.DataFrame(
            {
                "year": [2012, 2013, 2019, 2020],
                "value": [0, 0, 50, 50],
            }
        )
        assert estimate_trend_from_data(data, inverted=False) == "unknown"

    def test_empty_dataframe(self):
        """Empty dataframe -> unknown."""
        data = pd.DataFrame({"year": [], "value": []})
        assert estimate_trend_from_data(data, inverted=False) == "unknown"


class TestEstimateVdemTrend:
    def _make_vdem_df(self):
        return pd.DataFrame(
            {
                "country_text_id": ["USA"] * 4 + ["DNK"] * 4,
                "year": [2012, 2013, 2020, 2023] * 2,
                "v2x_corr": [0.05, 0.06, 0.15, 0.17, 0.03, 0.03, 0.04, 0.04],
                "v2x_polyarchy": [0.89, 0.89, 0.86, 0.87, 0.92, 0.92, 0.93, 0.93],
            }
        )

    def test_rising_direct(self):
        """USA corruption rising (direct: higher = more extraction)."""
        df = self._make_vdem_df()
        result = estimate_vdem_trend(df, "USA", "v2x_corr", inverted=False)
        assert result == "rising"

    def test_stable_inverted(self):
        """DNK polyarchy roughly stable."""
        df = self._make_vdem_df()
        result = estimate_vdem_trend(df, "DNK", "v2x_polyarchy", inverted=True)
        assert result == "stable"

    def test_missing_country(self):
        df = self._make_vdem_df()
        assert estimate_vdem_trend(df, "XYZ", "v2x_corr", inverted=False) == "unknown"

    def test_missing_variable(self):
        df = self._make_vdem_df()
        assert estimate_vdem_trend(df, "USA", "nonexistent", inverted=False) == "unknown"

    def test_empty_dataframe(self):
        assert estimate_vdem_trend(pd.DataFrame(), "USA", "v2x_corr", inverted=False) == "unknown"
