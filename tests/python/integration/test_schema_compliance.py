"""Integration tests validating scores.json against schema.json."""

import json
from pathlib import Path

import jsonschema

from score_countries import EXCLUDE_CODES

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCORES_PATH = PROJECT_ROOT / "data" / "scores.json"
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema.json"


class TestSchemaCompliance:
    @classmethod
    def setup_class(cls):
        with open(SCORES_PATH) as f:
            cls.scores = json.load(f)
        with open(SCHEMA_PATH) as f:
            cls.schema = json.load(f)

    def test_validates_against_schema(self):
        jsonschema.validate(self.scores, self.schema)

    def test_all_country_codes_are_alpha3(self):
        for code in self.scores["countries"]:
            assert len(code) == 3, f"Code '{code}' is not 3 letters"
            assert code.isalpha() and code.isupper(), f"Code '{code}' is not uppercase alpha"

    def test_no_excluded_codes_in_output(self):
        for code in self.scores["countries"]:
            assert code not in EXCLUDE_CODES, f"Excluded code '{code}' found in scores"

    def test_all_scores_in_range(self):
        for code, country in self.scores["countries"].items():
            composite = country["composite_score"]
            assert 0 <= composite <= 100, f"{code} composite {composite} out of range"
            for domain_name, domain in country["domains"].items():
                score = domain["score"]
                assert 0 <= score <= 100, f"{code}.{domain_name} score {score} out of range"

    def test_no_nan_scores(self):
        for code, country in self.scores["countries"].items():
            assert country["composite_score"] is not None, f"{code} composite is None"
            for domain_name, domain in country["domains"].items():
                assert domain["score"] is not None, f"{code}.{domain_name} score is None"

    def test_confidence_levels_valid(self):
        valid = {"high", "moderate", "low", "very_low"}
        for code, country in self.scores["countries"].items():
            assert country["overall_confidence"] in valid
            for dname, domain in country["domains"].items():
                assert domain["confidence"] in valid

    def test_trend_values_valid(self):
        valid = {"rising", "falling", "stable", "unknown"}
        for code, country in self.scores["countries"].items():
            assert country["overall_trend"] in valid
            for dname, domain in country["domains"].items():
                if "trend" in domain:
                    assert domain["trend"] in valid

    def test_every_domain_has_sources(self):
        for code, country in self.scores["countries"].items():
            for dname, domain in country["domains"].items():
                sources = domain.get("sources", [])
                assert len(sources) > 0, f"{code}.{dname} has no sources"

    def test_has_metadata(self):
        assert "metadata" in self.scores
        assert "version" in self.scores["metadata"]
        assert "last_updated" in self.scores["metadata"]
