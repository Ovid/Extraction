"""Tests for resource capture moderation by democratic accountability."""

from score_countries import apply_resource_moderation


def _make_resource_domain(score, confidence="moderate", facts=None):
    """Build a minimal resource_capture domain entry."""
    return {
        "score": score,
        "confidence": confidence,
        "trend": "unknown",
        "sources": ["wb_natural_rents"],
        "indicators": [
            {
                "key": "wb_natural_rents",
                "question": "How dependent is the economy on natural resources?",
                "label": "High",
                "facts": facts or ["Natural resource rents: 25.0% of GDP"],
            }
        ],
        "justification_detail": "Auto-scored from World Bank data.",
        "_n_indicators": 1,
        "_n_sources": 1,
        "_most_recent_year": 2022,
    }


class TestApplyResourceModeration:
    def test_with_polyarchy_moderates_score(self):
        """High democracy reduces resource capture score."""
        domains = {"resource_capture": _make_resource_domain(80)}
        apply_resource_moderation(domains, raw_polyarchy=0.8)
        # 80 * (100 - 80) / 100 = 16
        assert domains["resource_capture"]["score"] == 16

    def test_with_polyarchy_adds_vdem_source(self):
        domains = {"resource_capture": _make_resource_domain(60)}
        apply_resource_moderation(domains, raw_polyarchy=0.5)
        assert "vdem_electoral_democracy" in domains["resource_capture"]["sources"]

    def test_with_polyarchy_rebuilds_indicators(self):
        domains = {"resource_capture": _make_resource_domain(60)}
        apply_resource_moderation(domains, raw_polyarchy=0.5)
        inds = domains["resource_capture"]["indicators"]
        assert len(inds) == 1
        assert inds[0]["key"] == "resource_capture_composite"
        assert inds[0]["question"] == "How vulnerable is resource wealth to elite capture?"

    def test_with_polyarchy_preserves_rents_facts(self):
        """Original resource rents facts should appear in moderated indicator."""
        domains = {"resource_capture": _make_resource_domain(60, facts=["Rents: 15.0% of GDP"])}
        apply_resource_moderation(domains, raw_polyarchy=0.5)
        facts = domains["resource_capture"]["indicators"][0]["facts"]
        assert "Rents: 15.0% of GDP" in facts
        assert any("Moderated by democratic accountability" in f for f in facts)

    def test_with_polyarchy_updates_justification(self):
        domains = {"resource_capture": _make_resource_domain(60)}
        apply_resource_moderation(domains, raw_polyarchy=0.5)
        j = domains["resource_capture"]["justification_detail"]
        assert "Composite:" in j
        assert "accountability" in j

    def test_without_polyarchy_keeps_score(self):
        """No V-Dem data -> score unchanged."""
        domains = {"resource_capture": _make_resource_domain(60)}
        apply_resource_moderation(domains, raw_polyarchy=None)
        assert domains["resource_capture"]["score"] == 60

    def test_without_polyarchy_caps_confidence(self):
        """No V-Dem data -> confidence capped at 'low'."""
        domains = {"resource_capture": _make_resource_domain(60, confidence="high")}
        apply_resource_moderation(domains, raw_polyarchy=None)
        assert domains["resource_capture"]["confidence"] == "low"

    def test_without_polyarchy_low_confidence_unchanged(self):
        """Already low confidence stays low."""
        domains = {"resource_capture": _make_resource_domain(60, confidence="very_low")}
        apply_resource_moderation(domains, raw_polyarchy=None)
        assert domains["resource_capture"]["confidence"] == "very_low"

    def test_without_polyarchy_adds_no_data_fact(self):
        domains = {"resource_capture": _make_resource_domain(60)}
        apply_resource_moderation(domains, raw_polyarchy=None)
        facts = domains["resource_capture"]["indicators"][0]["facts"]
        assert any("No democratic accountability data" in f for f in facts)

    def test_no_resource_capture_domain_is_noop(self):
        """If resource_capture not in domains, function does nothing."""
        domains = {"economic_concentration": {"score": 50}}
        apply_resource_moderation(domains, raw_polyarchy=0.8)
        assert "resource_capture" not in domains

    def test_zero_polyarchy_full_capture(self):
        """Authoritarian state: polyarchy 0 -> score unchanged."""
        domains = {"resource_capture": _make_resource_domain(75)}
        apply_resource_moderation(domains, raw_polyarchy=0.0)
        assert domains["resource_capture"]["score"] == 75
