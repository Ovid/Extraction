"""Tests for country code handling, exclusions, and mappings."""

from score_countries import (
    ALPHA2_TO_ALPHA3,
    COUNTRY_NAME_OVERRIDES,
    EXCLUDE_CODES,
    RSF_CODE_REMAP,
)


class TestExcludeCodes:
    def test_excludes_world_aggregate(self):
        assert "WLD" in EXCLUDE_CODES

    def test_excludes_income_groups(self):
        for code in ["HIC", "LIC", "LMC", "UMC", "MIC"]:
            assert code in EXCLUDE_CODES

    def test_excludes_regional_aggregates(self):
        for code in ["EAS", "ECS", "LAC", "MEA", "NAC", "SAS", "SSF"]:
            assert code in EXCLUDE_CODES

    def test_no_real_country_excluded(self):
        """Spot check that real countries aren't accidentally excluded."""
        real_countries = ["USA", "GBR", "CHN", "IND", "BRA", "NGA", "AUS"]
        for code in real_countries:
            assert code not in EXCLUDE_CODES


class TestCountryNameOverrides:
    def test_usa_override(self):
        assert COUNTRY_NAME_OVERRIDES["USA"] == "United States"

    def test_kor_override(self):
        assert COUNTRY_NAME_OVERRIDES["KOR"] == "South Korea"

    def test_all_overrides_are_three_letter(self):
        """All override keys must be 3-letter codes."""
        for code in COUNTRY_NAME_OVERRIDES:
            assert len(code) == 3, f"Override key '{code}' is not 3 letters"
            assert code.isalpha() and code.isupper(), f"Override key '{code}' is not uppercase alpha"


class TestAlpha2ToAlpha3:
    def test_us_to_usa(self):
        assert ALPHA2_TO_ALPHA3["US"] == "USA"

    def test_gb_to_gbr(self):
        assert ALPHA2_TO_ALPHA3["GB"] == "GBR"

    def test_all_keys_are_two_letter(self):
        for key in ALPHA2_TO_ALPHA3:
            assert len(key) == 2, f"Key '{key}' is not 2 letters"

    def test_all_values_are_three_letter(self):
        for val in ALPHA2_TO_ALPHA3.values():
            assert len(val) == 3, f"Value '{val}' is not 3 letters"

    def test_no_excluded_codes_in_values(self):
        """Alpha-3 mapping should not map to excluded codes."""
        for a2, a3 in ALPHA2_TO_ALPHA3.items():
            assert a3 not in EXCLUDE_CODES, f"{a2} maps to excluded code {a3}"


class TestRsfCodeRemap:
    def test_seychelles_remap(self):
        assert RSF_CODE_REMAP["SEY"] == "SYC"
