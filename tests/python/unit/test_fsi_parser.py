"""Tests for FSI financial secrecy data loading."""

from pathlib import Path
from unittest.mock import patch

from score_countries import load_fsi_data, ALPHA2_TO_ALPHA3

FIXTURES = Path(__file__).parent.parent / 'fixtures'


class TestLoadFsiData:
    def test_loads_scores(self):
        with patch('score_countries.TJN_DIR', FIXTURES / 'fsi'):
            result = load_fsi_data()
        assert isinstance(result, dict)
        assert 'USA' in result

    def test_alpha2_to_alpha3_conversion(self):
        with patch('score_countries.TJN_DIR', FIXTURES / 'fsi'):
            result = load_fsi_data()
        assert 'CHE' in result  # CH -> CHE
        assert 'CYM' in result  # KY -> CYM
        assert 'SGP' in result  # SG -> SGP

    def test_uses_latest_methodology(self):
        with patch('score_countries.TJN_DIR', FIXTURES / 'fsi'):
            result = load_fsi_data()
        assert result['USA'] == 63.12  # fsi2024, not fsi2022

    def test_missing_file_returns_empty(self):
        with patch('score_countries.TJN_DIR', FIXTURES / 'nonexistent'):
            result = load_fsi_data()
        assert result == {}
