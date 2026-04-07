"""Tests for RSF press freedom data loading."""

from pathlib import Path
from unittest.mock import patch

from score_countries import load_rsf_data

FIXTURES = Path(__file__).parent.parent / 'fixtures'


class TestLoadRsfData:
    def test_loads_scores(self):
        with patch('score_countries.RSF_DIR', FIXTURES / 'rsf'):
            result = load_rsf_data()
        assert isinstance(result, dict)
        assert 'USA' in result
        assert result['USA'] == 67.5

    def test_remaps_codes(self):
        """SEY -> SYC via RSF_CODE_REMAP."""
        with patch('score_countries.RSF_DIR', FIXTURES / 'rsf'):
            result = load_rsf_data()
        assert 'SYC' in result
        assert 'SEY' not in result

    def test_excludes_non_standard_codes(self):
        """CS-KM is in EXCLUDE_CODES and should be filtered."""
        with patch('score_countries.RSF_DIR', FIXTURES / 'rsf'):
            result = load_rsf_data()
        assert 'CS-KM' not in result

    def test_missing_file_returns_empty(self):
        with patch('score_countries.RSF_DIR', FIXTURES / 'nonexistent'):
            result = load_rsf_data()
        assert result == {}
