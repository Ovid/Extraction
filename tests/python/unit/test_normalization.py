"""Tests for min-max normalization."""

import pandas as pd

from score_countries import normalize_minmax, normalize_minmax_log


class TestNormalizeMinmax:
    def test_normal_range(self):
        """Known values scale to expected 0-100 range."""
        s = pd.Series([0, 50, 100])
        result = normalize_minmax(s)
        assert list(result) == [0, 50, 100]

    def test_min_maps_to_zero(self):
        s = pd.Series([10, 20, 30])
        result = normalize_minmax(s)
        assert result.iloc[0] == 0

    def test_max_maps_to_100(self):
        s = pd.Series([10, 20, 30])
        result = normalize_minmax(s)
        assert result.iloc[2] == 100

    def test_inverted(self):
        """Inverted: highest raw -> 0, lowest raw -> 100."""
        s = pd.Series([0, 50, 100])
        result = normalize_minmax(s, inverted=True)
        assert list(result) == [100, 50, 0]

    def test_all_identical_returns_50(self):
        """All same values -> all 50."""
        s = pd.Series([42, 42, 42])
        result = normalize_minmax(s)
        assert list(result) == [50, 50, 50]

    def test_single_value_returns_50(self):
        """Single value -> 50 (hi == lo)."""
        s = pd.Series([7.5])
        result = normalize_minmax(s)
        assert result.iloc[0] == 50

    def test_negative_values(self):
        """Negative values normalize correctly (WGI uses -2.5 to 2.5)."""
        s = pd.Series([-2.5, 0.0, 2.5])
        result = normalize_minmax(s)
        assert list(result) == [0, 50, 100]

    def test_result_is_int(self):
        """Results are rounded integers."""
        s = pd.Series([0, 33, 100])
        result = normalize_minmax(s)
        assert all(isinstance(v, (int,)) for v in result)


class TestNormalizeMinmaxLog:
    def test_spreads_compressed_distribution(self):
        """Log transform gives middle values higher scores than linear."""
        s = pd.Series([0.0, 25.0, 61.0])
        linear = normalize_minmax(s)
        log = normalize_minmax_log(s)
        assert log.iloc[1] > linear.iloc[1]

    def test_extremes_unchanged(self):
        """Min still maps to 0, max still maps to 100."""
        s = pd.Series([0.0, 25.0, 61.0])
        result = normalize_minmax_log(s)
        assert result.iloc[0] == 0
        assert result.iloc[2] == 100

    def test_inverted(self):
        """Inverted log normalization flips correctly."""
        s = pd.Series([0.0, 25.0, 61.0])
        result = normalize_minmax_log(s, inverted=True)
        assert result.iloc[0] == 100
        assert result.iloc[2] == 0

    def test_all_identical_returns_50(self):
        """All same values -> all 50."""
        s = pd.Series([42.0, 42.0, 42.0])
        result = normalize_minmax_log(s)
        assert list(result) == [50, 50, 50]

    def test_all_zeros_returns_50(self):
        """All zeros -> log(1)=0 for all -> all 50."""
        s = pd.Series([0.0, 0.0, 0.0])
        result = normalize_minmax_log(s)
        assert list(result) == [50, 50, 50]
