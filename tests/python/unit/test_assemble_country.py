"""Tests for country entry assembly."""

from score_countries import assemble_country_entry


def _make_domain(score, trend="unknown", n_indicators=1, n_sources=1, most_recent_year=2023):
    """Helper to build a minimal domain dict with internal tracking fields."""
    return {
        "score": score,
        "confidence": "moderate",
        "trend": trend,
        "sources": ["test_src"],
        "indicators": [],
        "justification_detail": "test",
        "_n_indicators": n_indicators,
        "_n_sources": n_sources,
        "_most_recent_year": most_recent_year,
    }


class TestAssembleCountryEntry:
    def test_composite_is_average_of_domains(self):
        domains = {
            "political_capture": _make_domain(80),
            "economic_concentration": _make_domain(40),
        }
        result = assemble_country_entry("Testland", domains, ["Source A"])
        assert result["composite_score"] == 60

    def test_composite_rounds(self):
        domains = {
            "a": _make_domain(33),
            "b": _make_domain(33),
            "c": _make_domain(34),
        }
        result = assemble_country_entry("Testland", domains, ["S"])
        assert result["composite_score"] == 33  # (33+33+34)/3 = 33.33 -> 33

    def test_overall_trend_majority_vote(self):
        domains = {
            "a": _make_domain(50, trend="rising"),
            "b": _make_domain(50, trend="rising"),
            "c": _make_domain(50, trend="falling"),
        }
        result = assemble_country_entry("Testland", domains, ["S"])
        assert result["overall_trend"] == "rising"

    def test_overall_trend_all_unknown(self):
        domains = {
            "a": _make_domain(50, trend="unknown"),
            "b": _make_domain(50, trend="unknown"),
        }
        result = assemble_country_entry("Testland", domains, ["S"])
        assert result["overall_trend"] == "unknown"

    def test_internal_fields_cleaned(self):
        domains = {"a": _make_domain(50)}
        result = assemble_country_entry("Testland", domains, ["S"])
        domain = result["domains"]["a"]
        assert "_n_indicators" not in domain
        assert "_n_sources" not in domain
        assert "_most_recent_year" not in domain

    def test_confidence_capped_by_domain_count(self):
        """With only 2 domains, confidence should be capped at 'low'."""
        domains = {
            "a": _make_domain(50, n_indicators=5, n_sources=3, most_recent_year=2024),
            "b": _make_domain(50, n_indicators=5, n_sources=3, most_recent_year=2024),
        }
        result = assemble_country_entry("Testland", domains, ["S1", "S2", "S3"])
        assert result["overall_confidence"] == "low"

    def test_notes_include_source_names_and_count(self):
        domains = {
            "a": _make_domain(50),
            "b": _make_domain(50),
        }
        result = assemble_country_entry("Testland", domains, ["World Bank", "V-Dem"])
        assert "V-Dem" in result["notes"]
        assert "World Bank" in result["notes"]
        assert "2/7 domains" in result["notes"]

    def test_name_preserved(self):
        domains = {"a": _make_domain(50)}
        result = assemble_country_entry("Testland", domains, ["S"])
        assert result["name"] == "Testland"

    def test_data_quality_notes_attached(self):
        domains = {"a": _make_domain(50)}
        result = assemble_country_entry("Nigeria", domains, ["S"], country_code="NGA")
        assert "data_quality_notes" in result
        assert "informal sector" in result["data_quality_notes"]

    def test_no_data_quality_notes_for_normal_country(self):
        domains = {"a": _make_domain(50)}
        result = assemble_country_entry("Testland", domains, ["S"], country_code="TST")
        assert "data_quality_notes" not in result
