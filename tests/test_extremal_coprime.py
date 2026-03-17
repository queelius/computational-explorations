"""Tests for extremal_coprime.py — extending Problem #883 via Bondy."""
import math
import pytest

from extremal_coprime import (
    extremal_size,
    residue_classes,
    coprime_edge_count,
    coprime_edge_density,
    turan_number,
    bondy_threshold,
    edge_density_by_threshold,
    degree_analysis,
    neighborhood_intersection,
    cycle_spectrum_via_matrix,
    pancyclicity_analysis,
    edge_density_scaling,
    bipartiteness_check,
    threshold_analysis,
)


# ── Basic functions ──────────────────────────────────────────────────

class TestBasicFunctions:
    """Test helper functions."""

    def test_extremal_size_small(self):
        # n=6: multiples of 2 or 3 in [6] = {2,3,4,6} = 4
        assert extremal_size(6) == 4

    def test_extremal_size_12(self):
        # n=12: |{2,3,4,6,8,9,10,12}| = 8
        assert extremal_size(12) == 8

    def test_extremal_approx_two_thirds(self):
        for n in [30, 60, 90, 120]:
            assert abs(extremal_size(n) / n - 2 / 3) < 0.02

    def test_residue_classes_partition(self):
        n = 30
        R = residue_classes(n)
        all_elems = set()
        for r in range(6):
            all_elems.update(R[r])
        assert all_elems == set(range(1, n + 1))

    def test_residue_classes_disjoint(self):
        R = residue_classes(20)
        for r1 in range(6):
            for r2 in range(r1 + 1, 6):
                assert not set(R[r1]) & set(R[r2])

    def test_coprime_edge_count_small(self):
        # {1,2,3}: edges (1,2), (1,3), (2,3) = 3
        assert coprime_edge_count({1, 2, 3}) == 3

    def test_coprime_edge_count_evens(self):
        # {2,4,6}: no coprime pairs
        assert coprime_edge_count({2, 4, 6}) == 0

    def test_coprime_edge_density_complete(self):
        # {1,2,3} is complete coprime graph
        assert coprime_edge_density({1, 2, 3}) == 1.0

    def test_coprime_edge_density_empty(self):
        assert coprime_edge_density({2, 4}) == 0.0

    def test_turan_triangle_free(self):
        # ex(n, K3) = floor(n²/4)
        assert turan_number(4) == 4
        assert turan_number(5) == 6
        assert turan_number(6) == 9

    def test_bondy_threshold(self):
        # Bondy threshold = floor(n²/4) + 1
        assert bondy_threshold(4) == 5
        assert bondy_threshold(10) == 26


# ── Edge density analysis ────────────────────────────────────────────

class TestEdgeDensity:
    """Test edge density computations."""

    def test_density_by_threshold_returns_dict(self):
        result = edge_density_by_threshold(12)
        assert isinstance(result, dict)

    def test_density_positive(self):
        result = edge_density_by_threshold(15)
        assert result["worst_density"] > 0

    def test_best_beats_worst(self):
        result = edge_density_by_threshold(15, num_extra=2)
        assert result["best_density"] >= result["worst_density"]

    def test_density_scaling_returns_list(self):
        result = edge_density_scaling([10, 20, 30])
        assert isinstance(result, list)
        assert len(result) == 3

    def test_density_above_zero(self):
        results = edge_density_scaling([15, 20, 25])
        for r in results:
            assert r["density"] > 0.1

    def test_density_fields(self):
        results = edge_density_scaling([20])
        r = results[0]
        assert "n" in r
        assert "density" in r
        assert "exceeds_mantel" in r
        assert "bondy_exceeded" in r


# ── Degree analysis ──────────────────────────────────────────────────

class TestDegreeAnalysis:
    """Test degree sequence analysis."""

    def test_complete_graph(self):
        # {1,2,3}: all coprime, should be complete
        result = degree_analysis({1, 2, 3})
        assert result["min_deg"] == 2
        assert result["max_deg"] == 2

    def test_empty_adjacent(self):
        # {2,4,6,8}: no coprime edges
        result = degree_analysis({2, 4, 6, 8})
        assert result["min_deg"] == 0
        assert result["max_deg"] == 0

    def test_avg_degree_consistent(self):
        A = set(range(1, 16))
        result = degree_analysis(A)
        assert result["avg_deg"] > 0
        # 2 * edges / n = avg degree
        edges = coprime_edge_count(A)
        expected_avg = 2 * edges / len(A)
        assert abs(result["avg_deg"] - expected_avg) < 0.01


# ── Bipartiteness ────────────────────────────────────────────────────

class TestBipartiteness:
    """Test bipartite structure detection."""

    def test_extremal_bipartite(self):
        # A* should be bipartite
        n = 12
        a_star = {i for i in range(1, n + 1) if i % 2 == 0 or i % 3 == 0}
        result = bipartiteness_check(a_star)
        assert result["is_bipartite"] is True

    def test_adding_coprime6_breaks(self):
        # A* + 1 should not be bipartite
        n = 12
        a_star = {i for i in range(1, n + 1) if i % 2 == 0 or i % 3 == 0}
        A = a_star | {1}
        result = bipartiteness_check(A)
        assert result["is_bipartite"] is False

    def test_evens_bipartite(self):
        # All even numbers: no coprime edges, trivially bipartite
        result = bipartiteness_check({2, 4, 6, 8, 10})
        assert result["is_bipartite"] is True


# ── Cycle spectrum ───────────────────────────────────────────────────

class TestCycleSpectrum:
    """Test cycle detection in coprime graphs."""

    def test_triangle_in_123(self):
        # {1,2,3} has a triangle
        cycles = cycle_spectrum_via_matrix({1, 2, 3})
        assert 3 in cycles

    def test_no_cycle_in_evens(self):
        # Even numbers have no coprime edges, hence no cycles
        cycles = cycle_spectrum_via_matrix({2, 4, 6, 8, 10})
        assert len(cycles) == 0

    def test_cycle_5_exists(self):
        # Large enough set should have 5-cycles
        A = set(range(1, 15))
        cycles = cycle_spectrum_via_matrix(A, max_length=7)
        assert 5 in cycles

    def test_threshold_has_triangle(self):
        # A* + 1 should have a triangle
        n = 15
        a_star = {i for i in range(1, n + 1) if i % 2 == 0 or i % 3 == 0}
        A = a_star | {1}
        cycles = cycle_spectrum_via_matrix(A, max_length=5)
        assert 3 in cycles


# ── Pancyclicity analysis ────────────────────────────────────────────

class TestPancyclicity:
    """Test pancyclicity analysis at threshold."""

    def test_returns_dict(self):
        result = pancyclicity_analysis(12)
        assert isinstance(result, dict)

    def test_has_cycles(self):
        result = pancyclicity_analysis(12)
        assert len(result["odd_cycles_found"]) > 0
        assert 3 in result["odd_cycles_found"]

    def test_all_required_for_n15(self):
        result = pancyclicity_analysis(15)
        # Required: odd cycles up to 6 (n//3+1=6)
        assert result["all_required_found"]

    def test_edges_positive(self):
        result = pancyclicity_analysis(15)
        assert result["edges"] > 0

    def test_density_above_zero(self):
        result = pancyclicity_analysis(15)
        assert result["density"] > 0.1


# ── Threshold analysis ───────────────────────────────────────────────

class TestThresholdAnalysis:
    """Test threshold comparison analysis."""

    def test_returns_dict(self):
        result = threshold_analysis([8, 10, 12])
        assert isinstance(result, dict)
        assert "results" in result
        assert "summary" in result

    def test_results_per_n(self):
        result = threshold_analysis([10, 15])
        assert len(result["results"]) == 2

    def test_non_bipartite_at_extremal_plus_one(self):
        result = threshold_analysis([10, 12, 15])
        for r in result["results"]:
            # Non-bipartiteness should trigger at |A*| + 1
            if r["non_bipartite_at"] is not None:
                assert r["non_bipartite_at"] == r["extremal_size"] + 1

    def test_summary_has_gaps(self):
        result = threshold_analysis([10, 12, 15])
        s = result["summary"]
        assert "non_bipartite_min_gap" in s
        assert s["non_bipartite_min_gap"] == 1


# ── Neighborhood intersection ────────────────────────────────────────

class TestNeighborhoodIntersection:
    """Test common neighbor analysis."""

    def test_complete_graph(self):
        result = neighborhood_intersection({1, 2, 3, 5})
        # If graph is complete, no non-adjacent pairs
        if result.get("is_complete"):
            assert result["non_adjacent_pairs"] == 0

    def test_returns_dict(self):
        A = set(range(1, 10))
        result = neighborhood_intersection(A)
        assert isinstance(result, dict)
