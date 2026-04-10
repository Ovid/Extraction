"""Tests for FSI financial secrecy data loading."""

from pathlib import Path
from unittest.mock import patch

from score_countries import load_fsi_data

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestLoadFsiData:
    def test_loads_scores(self):
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            result = load_fsi_data()
        assert isinstance(result, dict)
        assert "USA" in result
        assert "value" in result["USA"]

    def test_returns_fsi_value(self):
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            result = load_fsi_data()
        # Should use index_value, not index_score
        assert result["USA"]["value"] == 1900.2  # fsi2024 index_value

    def test_includes_secrecy_score(self):
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            result = load_fsi_data()
        assert result["USA"]["secrecy"] == 63.12

    def test_alpha2_to_alpha3_conversion(self):
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            result = load_fsi_data()
        assert "CHE" in result  # CH -> CHE
        assert "CYM" in result  # KY -> CYM
        assert "SGP" in result  # SG -> SGP

    def test_uses_latest_methodology(self):
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            result = load_fsi_data()
        assert result["USA"]["value"] == 1900.2  # fsi2024, not fsi2022

    def test_missing_file_returns_empty(self):
        with patch("score_countries.TJN_DIR", FIXTURES / "nonexistent"):
            result = load_fsi_data()
        assert result == {}
