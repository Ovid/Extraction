"""Tests for World Bank domain entry construction."""

import pandas as pd

from score_countries import build_wb_domain


def _make_wb_group():
    """Build a minimal pandas DataFrame resembling a WB domain group.

    Two indicators for institutional_gatekeeping, as if from groupby('domain').
    """
    return pd.DataFrame({
        "country_code": ["USA", "USA"],
        "country_name": ["United States", "United States"],
        "year": [2022, 2021],
        "value": [-0.5, 0.8],
        "normalized": [60, 30],
        "domain": ["institutional_gatekeeping", "institutional_gatekeeping"],
        "source_key": ["wb_wgi_corruption", "wb_reg_quality"],
        "indicator_name": ["WGI Control of Corruption", "WGI Regulatory Quality"],
        "indicator_file": ["wb_wgi_corruption.csv", "wb_wgi_reg_quality.csv"],
    })


class TestBuildWbDomain:
    def test_score_is_mean_of_normalized(self):
        group = _make_wb_group()
        all_indicator_raw = {"wb_wgi_corruption": {"USA": -0.5}, "wb_reg_quality": {"USA": 0.8}}
        result = build_wb_domain(group, "USA", all_indicator_raw)
        assert result["score"] == 45  # (60 + 30) / 2

    def test_has_required_keys(self):
        group = _make_wb_group()
        all_indicator_raw = {}
        result = build_wb_domain(group, "USA", all_indicator_raw)
        for key in ["score", "confidence", "trend", "sources", "indicators",
                     "justification_detail", "_n_indicators", "_n_sources", "_most_recent_year"]:
            assert key in result, f"Missing key: {key}"

    def test_n_indicators_matches_group_size(self):
        group = _make_wb_group()
        result = build_wb_domain(group, "USA", {})
        assert result["_n_indicators"] == 2

    def test_sources_list(self):
        group = _make_wb_group()
        result = build_wb_domain(group, "USA", {})
        assert "wb_wgi_corruption" in result["sources"]
        assert "wb_reg_quality" in result["sources"]

    def test_most_recent_year(self):
        group = _make_wb_group()
        result = build_wb_domain(group, "USA", {})
        assert result["_most_recent_year"] == 2022

    def test_single_indicator(self):
        group = pd.DataFrame({
            "country_code": ["USA"],
            "country_name": ["United States"],
            "year": [2023],
            "value": [41.5],
            "normalized": [72],
            "domain": ["economic_concentration"],
            "source_key": ["wb_gini"],
            "indicator_name": ["Gini Index"],
            "indicator_file": ["wb_gini.csv"],
        })
        result = build_wb_domain(group, "USA", {})
        assert result["score"] == 72
        assert result["_n_indicators"] == 1
