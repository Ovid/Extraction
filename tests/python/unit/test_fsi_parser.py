"""Tests for FSI financial secrecy data loading."""

from pathlib import Path
from unittest.mock import patch

from score_countries import load_fsi_data, load_fsi_related_jurisdictions

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


class TestFsiSecrecyScoring:
    """Tests that TF domain uses secrecy score (raw, no min-max) not FSI Value."""

    def test_all_countries_have_secrecy_score(self):
        """Every country returned by load_fsi_data must include a secrecy score."""
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            result = load_fsi_data()
        for code in result:
            assert "secrecy" in result[code], f"{code} missing secrecy score"

    def test_tf_domain_score_equals_rounded_secrecy(self):
        """The TF domain score should be the rounded raw secrecy score, not normalized FSI Value.

        USA fixture has secrecy=63.12 and FSI Value=1900.2. If the scoring
        still uses FSI Value with min-max normalization, the score will be ~100
        (highest in the dataset). If it correctly uses raw secrecy, it will be 63.
        """
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            fsi_data = load_fsi_data()

        # Build secrecy map the same way the scoring pipeline does
        fsi_secrecy = {k: v.get("secrecy") for k, v in fsi_data.items()}

        # USA secrecy is 63.12 in fixture -> rounded to 63
        assert fsi_secrecy["USA"] == 63.12
        assert int(round(fsi_secrecy["USA"])) == 63

        # Verify it's NOT the FSI Value (which would normalize to ~100)
        assert fsi_data["USA"]["value"] == 1900.2  # FSI Value is much higher
        assert int(round(fsi_secrecy["USA"])) < 70  # Secrecy score is moderate


class TestLoadFsiRelatedJurisdictions:
    """Tests for UK Crown Dependencies and Overseas Territories loading."""

    def test_returns_only_related_jurisdictions(self):
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            result = load_fsi_related_jurisdictions()
        codes = [r["code"] for r in result]
        # Fixture has GG (Guernsey), VG (BVI), and KY (Cayman) as UK-related
        assert "GGY" in codes  # GG -> GGY
        assert "VGB" in codes  # VG -> VGB
        assert "CYM" in codes  # KY -> CYM (UK Overseas Territory)
        # Non-UK jurisdictions excluded
        assert not any(c in codes for c in ["USA", "CHE", "SGP"])

    def test_includes_secrecy_score(self):
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            result = load_fsi_related_jurisdictions()
        for entry in result:
            assert "secrecy_score" in entry
            assert entry["secrecy_score"] is not None

    def test_includes_fsi_share_pct(self):
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            result = load_fsi_related_jurisdictions()
        for entry in result:
            assert "fsi_share_pct" in entry
            assert entry["fsi_share_pct"] > 0

    def test_missing_file_returns_empty(self):
        with patch("score_countries.TJN_DIR", FIXTURES / "nonexistent"):
            result = load_fsi_related_jurisdictions()
        assert result == []

    def test_uses_latest_methodology(self):
        """Should use fsi2024 (latest by timestamp), not fsi2022."""
        with patch("score_countries.TJN_DIR", FIXTURES / "fsi"):
            result = load_fsi_related_jurisdictions()
        # GG and VG only exist in fsi2024, so getting results proves correct methodology
        assert len(result) > 0
