"""Tests for resource capture composite formula."""

from score_countries import compute_resource_capture


class TestComputeResourceCapture:
    def test_with_vdem_data(self):
        """normalized_resource * (100 - round(polyarchy * 100)) / 100"""
        # 60 * (100 - 80) / 100 = 60 * 20 / 100 = 12
        assert compute_resource_capture(60, 0.8) == 12

    def test_zero_resource_rents(self):
        """Zero resources = zero capture regardless of democracy."""
        assert compute_resource_capture(0, 0.3) == 0

    def test_zero_polyarchy(self):
        """No democracy = full resource capture."""
        assert compute_resource_capture(75, 0.0) == 75

    def test_full_polyarchy(self):
        """Full democracy = zero resource capture."""
        assert compute_resource_capture(50, 1.0) == 0

    def test_none_polyarchy_returns_unchanged(self):
        """Missing V-Dem data returns raw normalized score unchanged."""
        assert compute_resource_capture(45, None) == 45

    def test_rounding(self):
        """Verify rounding behavior matches production code."""
        # 80 * (100 - round(0.73 * 100)) / 100 = 80 * 27 / 100 = 21.6 -> 22
        assert compute_resource_capture(80, 0.73) == 22

    def test_high_resource_low_democracy(self):
        """Classic petro-state scenario: high rents, low democracy."""
        # 95 * (100 - round(0.15 * 100)) / 100 = 95 * 85 / 100 = 80.75 -> 81
        assert compute_resource_capture(95, 0.15) == 81
