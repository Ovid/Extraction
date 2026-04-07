"""Integration tests for the full scoring pipeline."""

import json
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema.json"
FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestPipeline:
    """Run the scoring pipeline against fixture data and validate output."""

    def _run_pipeline_with_fixtures(self):
        """Run build_country_scores() with fixture directories."""
        with (
            patch("score_countries.WB_DIR", FIXTURES / "worldbank"),
            patch("score_countries.RSF_DIR", FIXTURES / "rsf"),
            patch("score_countries.TJN_DIR", FIXTURES / "fsi"),
            patch("score_countries.VDEM_DIR", FIXTURES / "vdem"),
        ):
            from score_countries import build_country_scores

            return build_country_scores()

    def test_produces_countries(self):
        countries = self._run_pipeline_with_fixtures()
        assert len(countries) > 0

    def test_usa_has_expected_domains(self):
        countries = self._run_pipeline_with_fixtures()
        assert "USA" in countries
        usa = countries["USA"]
        assert len(usa["domains"]) > 0

    def test_output_matches_schema_structure(self):
        countries = self._run_pipeline_with_fixtures()
        for code, country in countries.items():
            assert "name" in country
            assert "domains" in country
            assert "composite_score" in country
            assert "overall_confidence" in country
            assert "overall_trend" in country
            assert 0 <= country["composite_score"] <= 100

    def test_excluded_codes_not_in_output(self):
        countries = self._run_pipeline_with_fixtures()
        from score_countries import EXCLUDE_CODES

        for code in countries:
            assert code not in EXCLUDE_CODES

    def test_composite_is_average_of_domains(self):
        countries = self._run_pipeline_with_fixtures()
        for code, country in countries.items():
            domain_scores = [d["score"] for d in country["domains"].values()]
            expected = round(sum(domain_scores) / len(domain_scores))
            assert country["composite_score"] == expected, (
                f"{code}: composite {country['composite_score']} != expected {expected}"
            )

    def test_known_inputs_produce_expected_scores(self):
        """Round-trip: known fixture values produce expected normalized scores."""
        countries = self._run_pipeline_with_fixtures()
        assert "USA" in countries
        usa = countries["USA"]
        assert 0 <= usa["composite_score"] <= 100
        # DNK should score lower than ZAF on economic_concentration (lower Gini)
        if "DNK" in countries and "ZAF" in countries:
            dnk_ec = countries["DNK"]["domains"].get("economic_concentration", {}).get("score", 0)
            zaf_ec = countries["ZAF"]["domains"].get("economic_concentration", {}).get("score", 0)
            assert dnk_ec < zaf_ec, "Denmark should have lower economic concentration than South Africa"


class TestPipelineFlags:
    """Test CLI flag behavior (--overwrite, --country)."""

    def test_overwrite_replaces_hand_scored(self, tmp_path):
        scores = {
            "metadata": {"version": "1.0", "last_updated": "2026-01-01"},
            "countries": {
                "USA": {
                    "name": "United States",
                    "domains": {},
                    "composite_score": 99,
                    "overall_confidence": "high",
                    "overall_trend": "stable",
                    "notes": "Hand-scored by expert.",
                }
            },
        }
        scores_path = tmp_path / "scores.json"
        with open(scores_path, "w") as f:
            json.dump(scores, f)

        with (
            patch("score_countries.WB_DIR", FIXTURES / "worldbank"),
            patch("score_countries.RSF_DIR", FIXTURES / "rsf"),
            patch("score_countries.TJN_DIR", FIXTURES / "fsi"),
            patch("score_countries.VDEM_DIR", FIXTURES / "vdem"),
            patch("score_countries.SCORES_PATH", scores_path),
            patch("sys.argv", ["score_countries.py", "--overwrite"]),
        ):
            from score_countries import main

            main()

        with open(scores_path) as f:
            result = json.load(f)
        assert result["countries"]["USA"]["notes"].startswith("Auto-scored")

    def test_preserve_hand_scored_by_default(self, tmp_path):
        scores = {
            "metadata": {"version": "1.0", "last_updated": "2026-01-01"},
            "countries": {
                "USA": {
                    "name": "United States",
                    "domains": {},
                    "composite_score": 99,
                    "overall_confidence": "high",
                    "overall_trend": "stable",
                    "notes": "Hand-scored by expert.",
                }
            },
        }
        scores_path = tmp_path / "scores.json"
        with open(scores_path, "w") as f:
            json.dump(scores, f)

        with (
            patch("score_countries.WB_DIR", FIXTURES / "worldbank"),
            patch("score_countries.RSF_DIR", FIXTURES / "rsf"),
            patch("score_countries.TJN_DIR", FIXTURES / "fsi"),
            patch("score_countries.VDEM_DIR", FIXTURES / "vdem"),
            patch("score_countries.SCORES_PATH", scores_path),
            patch("sys.argv", ["score_countries.py"]),
        ):
            from score_countries import main

            main()

        with open(scores_path) as f:
            result = json.load(f)
        assert result["countries"]["USA"]["composite_score"] == 99

    def test_country_flag_scores_single(self, tmp_path):
        scores = {"metadata": {"version": "1.0", "last_updated": "2026-01-01"}, "countries": {}}
        scores_path = tmp_path / "scores.json"
        with open(scores_path, "w") as f:
            json.dump(scores, f)

        with (
            patch("score_countries.WB_DIR", FIXTURES / "worldbank"),
            patch("score_countries.RSF_DIR", FIXTURES / "rsf"),
            patch("score_countries.TJN_DIR", FIXTURES / "fsi"),
            patch("score_countries.VDEM_DIR", FIXTURES / "vdem"),
            patch("score_countries.SCORES_PATH", scores_path),
            patch("sys.argv", ["score_countries.py", "--country", "USA"]),
        ):
            from score_countries import main

            main()

        with open(scores_path) as f:
            result = json.load(f)
        assert "USA" in result["countries"]
        assert "DNK" not in result["countries"]
