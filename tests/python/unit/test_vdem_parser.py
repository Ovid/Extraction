"""Tests for V-Dem data loading and parsing."""

from pathlib import Path
from unittest.mock import patch

from score_countries import load_vdem_data

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestLoadVdemData:
    def test_loads_data_successfully(self):
        with patch("score_countries.VDEM_DIR", FIXTURES / "vdem"):
            result = load_vdem_data()
        assert isinstance(result, dict)
        assert "USA" in result

    def test_extracts_all_nine_variables(self):
        with patch("score_countries.VDEM_DIR", FIXTURES / "vdem"):
            result = load_vdem_data()
        usa = result["USA"]
        expected_vars = [
            "v2x_polyarchy",
            "v2x_corr",
            "v2xnp_client",
            "v2x_freexp_altinf",
            "v2xme_altinf",
            "v2x_clphy",
            "v2x_rule",
            "v2x_egal",
            "v2x_partipdem",
        ]
        for var in expected_vars:
            assert var in usa, f"Missing variable: {var}"

    def test_most_recent_year_per_country(self):
        with patch("score_countries.VDEM_DIR", FIXTURES / "vdem"):
            result = load_vdem_data()
        assert result["USA"]["v2x_polyarchy"] == 0.87  # 2023 value

    def test_excludes_excluded_codes(self):
        with patch("score_countries.VDEM_DIR", FIXTURES / "vdem"):
            result = load_vdem_data()
        assert "PSG" not in result

    def test_missing_file_returns_empty(self):
        with patch("score_countries.VDEM_DIR", FIXTURES / "nonexistent"):
            result = load_vdem_data()
        assert result == {}
