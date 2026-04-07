"""Tests for V-Dem indicator normalization."""

from score_countries import normalize_vdem_indicators

VDEM_VARS_CONFIG = {
    "v2x_corr": {"domain": "political_capture", "inverted": False, "name": "Political Corruption"},
    "v2x_polyarchy": {"domain": "political_capture", "inverted": True, "name": "Electoral Democracy"},
}


class TestNormalizeVdemIndicators:
    def test_basic_normalization(self):
        """Two countries, one variable — normalized to 0-100."""
        vdem_raw = {
            "USA": {"v2x_corr": 0.2},
            "NGA": {"v2x_corr": 0.8},
        }
        config = {"v2x_corr": {"domain": "political_capture", "inverted": False, "name": "Corruption"}}
        result = normalize_vdem_indicators(vdem_raw, config)
        assert "USA" in result
        assert "NGA" in result
        assert result["USA"]["v2x_corr"]["score"] < result["NGA"]["v2x_corr"]["score"]

    def test_inverted_variable(self):
        """Inverted: higher raw = less extraction -> lower score."""
        vdem_raw = {
            "USA": {"v2x_polyarchy": 0.9},
            "NGA": {"v2x_polyarchy": 0.4},
        }
        result = normalize_vdem_indicators(vdem_raw, VDEM_VARS_CONFIG)
        assert result["USA"]["v2x_polyarchy"]["score"] < result["NGA"]["v2x_polyarchy"]["score"]

    def test_output_structure(self):
        """Each entry has score, raw, name, domain, var."""
        vdem_raw = {"USA": {"v2x_corr": 0.5}, "DNK": {"v2x_corr": 0.1}}
        config = {"v2x_corr": {"domain": "political_capture", "inverted": False, "name": "Corruption"}}
        result = normalize_vdem_indicators(vdem_raw, config)
        entry = result["USA"]["v2x_corr"]
        assert set(entry.keys()) == {"score", "raw", "name", "domain", "var"}
        assert entry["raw"] == 0.5
        assert entry["name"] == "Corruption"
        assert entry["domain"] == "political_capture"
        assert entry["var"] == "v2x_corr"

    def test_missing_variable_skipped(self):
        """Country missing a variable -> variable absent from output."""
        vdem_raw = {
            "USA": {"v2x_corr": 0.2},
            "NGA": {"v2x_corr": 0.8, "v2x_polyarchy": 0.4},
        }
        result = normalize_vdem_indicators(vdem_raw, VDEM_VARS_CONFIG)
        assert "v2x_polyarchy" not in result.get("USA", {})

    def test_single_country_gets_score_50(self):
        """When min == max, normalize_minmax returns 50."""
        vdem_raw = {"USA": {"v2x_corr": 0.5}}
        config = {"v2x_corr": {"domain": "political_capture", "inverted": False, "name": "Corruption"}}
        result = normalize_vdem_indicators(vdem_raw, config)
        assert result["USA"]["v2x_corr"]["score"] == 50

    def test_empty_input(self):
        vdem_raw = {}
        result = normalize_vdem_indicators(vdem_raw, VDEM_VARS_CONFIG)
        assert result == {}

    def test_variable_not_in_any_country(self):
        """Config has a variable that no country reports -> skip it."""
        vdem_raw = {"USA": {"v2x_corr": 0.5}}
        config = {
            "v2x_corr": {"domain": "political_capture", "inverted": False, "name": "Corruption"},
            "v2x_missing": {"domain": "political_capture", "inverted": False, "name": "Missing"},
        }
        result = normalize_vdem_indicators(vdem_raw, config)
        assert "v2x_missing" not in result.get("USA", {})
