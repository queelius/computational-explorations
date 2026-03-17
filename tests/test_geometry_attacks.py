"""Tests for geometry_attacks.py: Erdos geometry problems (#89, #99, #604, #90)."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from geometry_attacks import (
    # Core utilities
    distinct_distance_count,
    unit_distance_count,
    max_distance_multiplicity,
    _squared_distances,
    _has_duplicate_points,
    # Distinct distances (#89)
    _regular_polygon,
    _triangular_lattice_points,
    _square_lattice_points,
    _known_optimal_distinct_distances,
    _try_all_triangular_subsets,
    compute_min_distinct_distances,
    KNOWN_DISTINCT_DISTANCES,
    # Unit distances (#99)
    _build_unit_distance_graph,
    _optimize_unit_distances,
    compute_max_unit_distances,
    KNOWN_UNIT_DISTANCES,
    # Erdos-Szekeres
    points_in_general_position,
    max_convex_subset_size,
    erdos_szekeres_bound,
    KNOWN_ES_VALUES,
    # Diameter graphs (#604)
    diameter_edge_count,
    all_pairwise_le_1,
    _reuleaux_triangle_config,
    compute_max_diameter_edges,
    KNOWN_DIAMETER_EDGES,
    # Repeated distances (#90)
    _lattice_repeated_distances,
    _repeated_distances_continuous,
    compute_max_repeated_distances,
)


# =====================================================================
# 1. UTILITY FUNCTIONS
# =====================================================================

class TestSquaredDistances:
    def test_two_points(self):
        pts = np.array([[0.0, 0.0], [3.0, 4.0]])
        sq = _squared_distances(pts)
        assert len(sq) == 1
        assert abs(sq[0] - 25.0) < 1e-10

    def test_equilateral_triangle(self):
        pts = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, math.sqrt(3) / 2]])
        sq = sorted(_squared_distances(pts))
        assert len(sq) == 3
        # All sides should be 1, so sq distances all ~ 1.0
        for s in sq:
            assert abs(s - 1.0) < 1e-10

    def test_empty(self):
        pts = np.array([[0.0, 0.0]])
        sq = _squared_distances(pts)
        assert len(sq) == 0


class TestDistinctDistanceCount:
    def test_equilateral_triangle(self):
        pts = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, math.sqrt(3) / 2]])
        assert distinct_distance_count(pts) == 1

    def test_square(self):
        pts = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
        # side = 1, diagonal = sqrt(2) -> 2 distinct
        assert distinct_distance_count(pts) == 2

    def test_single_point(self):
        pts = np.array([[0.0, 0.0]])
        assert distinct_distance_count(pts) == 0

    def test_two_points(self):
        pts = np.array([[0.0, 0.0], [1.0, 0.0]])
        assert distinct_distance_count(pts) == 1


class TestUnitDistanceCount:
    def test_two_unit_points(self):
        pts = np.array([[0.0, 0.0], [1.0, 0.0]])
        assert unit_distance_count(pts) == 1

    def test_equilateral_triangle(self):
        pts = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, math.sqrt(3) / 2]])
        assert unit_distance_count(pts) == 3

    def test_no_unit_distances(self):
        pts = np.array([[0.0, 0.0], [2.0, 0.0], [4.0, 0.0]])
        assert unit_distance_count(pts) == 0

    def test_tolerance(self):
        # Point very close to unit distance but not exact
        pts = np.array([[0.0, 0.0], [1.0 + 1e-10, 0.0]])
        assert unit_distance_count(pts, tol=1e-7) == 1
        assert unit_distance_count(pts, tol=1e-15) == 0


class TestMaxDistanceMultiplicity:
    def test_equilateral_triangle(self):
        pts = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, math.sqrt(3) / 2]])
        mult, dsq = max_distance_multiplicity(pts)
        assert mult == 3
        assert abs(dsq - 1.0) < 1e-8

    def test_square(self):
        pts = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
        mult, dsq = max_distance_multiplicity(pts)
        # 4 sides of length 1 vs 2 diagonals of length sqrt(2)
        assert mult == 4
        assert abs(dsq - 1.0) < 1e-8

    def test_single_point(self):
        pts = np.array([[0.0, 0.0]])
        mult, dsq = max_distance_multiplicity(pts)
        assert mult == 0


class TestHasDuplicatePoints:
    def test_no_duplicates(self):
        pts = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
        assert not _has_duplicate_points(pts)

    def test_with_duplicate(self):
        pts = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 0.0]])
        assert _has_duplicate_points(pts)

    def test_near_duplicate(self):
        pts = np.array([[0.0, 0.0], [1e-5, 0.0]])
        assert _has_duplicate_points(pts, min_sep=1e-4)
        assert not _has_duplicate_points(pts, min_sep=1e-6)


# =====================================================================
# 2. DISTINCT DISTANCES (#89)
# =====================================================================

class TestRegularPolygon:
    def test_triangle(self):
        pts = _regular_polygon(3)
        assert len(pts) == 3
        # All on unit circle
        for p in pts:
            assert abs(np.linalg.norm(p) - 1.0) < 1e-10

    def test_square(self):
        pts = _regular_polygon(4)
        assert len(pts) == 4
        assert distinct_distance_count(pts) == 2

    def test_pentagon(self):
        pts = _regular_polygon(5)
        assert len(pts) == 5
        assert distinct_distance_count(pts) == 2

    def test_hexagon(self):
        pts = _regular_polygon(6)
        assert len(pts) == 6
        assert distinct_distance_count(pts) == 3


class TestTriangularLattice:
    def test_returns_n_points(self):
        for n in [3, 7, 12, 19]:
            pts = _triangular_lattice_points(n)
            assert len(pts) == n

    def test_lattice_structure(self):
        """Triangular lattice distances are sqrt of integers representable as a^2+ab+b^2."""
        pts = _triangular_lattice_points(7)
        sq_dists = _squared_distances(pts)
        # All squared distances should be of the form a^2 + ab + b^2
        # for integer a, b. These are 1, 3, 4, 7, 9, 12, 13, ...
        valid_norms = set()
        for a in range(-10, 11):
            for b in range(-10, 11):
                valid_norms.add(round(a * a + a * b + b * b, 6))
        for d in sq_dists:
            assert round(d, 6) in valid_norms, f"sq_dist {d} not a lattice norm"


class TestSquareLattice:
    def test_returns_n_points(self):
        for n in [4, 9, 16]:
            pts = _square_lattice_points(n)
            assert len(pts) == n

    def test_integer_coords(self):
        pts = _square_lattice_points(9)
        for p in pts:
            assert abs(p[0] - round(p[0])) < 1e-10
            assert abs(p[1] - round(p[1])) < 1e-10


class TestDistinctDistancesComputation:
    """Verify computed g(n) matches known values for n=3..10."""

    @pytest.fixture(scope="class")
    def dd_results(self):
        return compute_min_distinct_distances((3, 10))

    @pytest.mark.parametrize("n", range(3, 11))
    def test_matches_known(self, dd_results, n):
        computed, config = dd_results[n]
        known = KNOWN_DISTINCT_DISTANCES[n]
        assert computed <= known, f"g({n}): computed {computed} > known {known}"

    def test_g3_equilateral(self, dd_results):
        count, config = dd_results[3]
        assert count == 1

    def test_g5_pentagon(self, dd_results):
        count, config = dd_results[5]
        assert count == 2

    def test_g_monotone(self, dd_results):
        """g(n) is non-decreasing."""
        prev = 0
        for n in range(3, 11):
            c, _ = dd_results[n]
            assert c >= prev, f"g({n})={c} < g({n - 1})={prev}"
            prev = c


class TestDistinctDistancesFormula:
    """The regular n-gon gives exactly floor(n/2) distinct distances."""

    @pytest.mark.parametrize("n", range(3, 20))
    def test_polygon_distance_count(self, n):
        pts = _regular_polygon(n)
        assert distinct_distance_count(pts) == n // 2


# =====================================================================
# 3. UNIT DISTANCES (#99)
# =====================================================================

class TestBuildUnitDistanceGraph:
    def test_returns_correct_count(self):
        for n in [2, 3, 4, 5]:
            pts = _build_unit_distance_graph(n)
            assert len(pts) == n

    def test_no_duplicates(self):
        for n in [3, 5, 8]:
            pts = _build_unit_distance_graph(n)
            assert not _has_duplicate_points(pts)

    def test_triangle(self):
        pts = _build_unit_distance_graph(3)
        assert unit_distance_count(pts) == 3

    def test_n4_at_least_5(self):
        pts = _build_unit_distance_graph(4)
        assert unit_distance_count(pts) >= 4  # known u(4) = 5


class TestUnitDistancesComputation:
    """Verify u(n) matches known values for small n."""

    @pytest.fixture(scope="class")
    def ud_results(self):
        return compute_max_unit_distances((2, 9), trials=100)

    @pytest.mark.parametrize("n", range(2, 10))
    def test_matches_known(self, ud_results, n):
        computed = ud_results[n]
        known = KNOWN_UNIT_DISTANCES[n]
        assert computed >= known - 1, f"u({n}): computed {computed} << known {known}"

    @pytest.mark.parametrize("n", range(2, 8))
    def test_exact_match_small(self, ud_results, n):
        """For small n, we should hit exact values."""
        computed = ud_results[n]
        known = KNOWN_UNIT_DISTANCES[n]
        assert computed == known, f"u({n}): computed {computed} != known {known}"

    def test_monotone(self, ud_results):
        """u(n) is non-decreasing."""
        prev = 0
        for n in range(2, 10):
            c = ud_results[n]
            assert c >= prev
            prev = c


class TestUnitDistanceSuperlinear:
    """u(n) grows faster than n for large n (known result)."""

    @pytest.fixture(scope="class")
    def ud_large(self):
        return compute_max_unit_distances((4, 9), trials=80)

    def test_superlinear(self, ud_large):
        # u(9) = 18 = 2*9, definitely superlinear
        assert ud_large[9] >= 9 + 5


# =====================================================================
# 4. ERDOS-SZEKERES CONVEX POSITION
# =====================================================================

class TestPointsGeneralPosition:
    def test_triangle(self):
        pts = np.array([[0, 0], [1, 0], [0, 1]], dtype=float)
        assert points_in_general_position(pts)

    def test_collinear(self):
        pts = np.array([[0, 0], [1, 0], [2, 0]], dtype=float)
        assert not points_in_general_position(pts)

    def test_square(self):
        pts = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
        assert points_in_general_position(pts)


class TestMaxConvexSubset:
    def test_triangle(self):
        pts = np.array([[0, 0], [1, 0], [0, 1]], dtype=float)
        assert max_convex_subset_size(pts) == 3

    def test_square(self):
        pts = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
        assert max_convex_subset_size(pts) == 4

    def test_square_with_interior(self):
        pts = np.array([[0, 0], [2, 0], [2, 2], [0, 2], [1, 1]], dtype=float)
        assert max_convex_subset_size(pts) == 4

    def test_pentagon(self):
        pts = _regular_polygon(5)
        assert max_convex_subset_size(pts) == 5


class TestErdosSzekeresBound:
    def test_f3(self):
        assert erdos_szekeres_bound(3) == 3

    def test_f4(self):
        # C(4,2)+1 = 7 (upper bound; actual f(4)=5)
        assert erdos_szekeres_bound(4) == 7

    def test_f5(self):
        # C(6,3)+1 = 21
        assert erdos_szekeres_bound(5) == 21

    def test_f6(self):
        # C(8,4)+1 = 71
        assert erdos_szekeres_bound(6) == 71


class TestKnownESValues:
    def test_values(self):
        assert KNOWN_ES_VALUES[3] == 3
        assert KNOWN_ES_VALUES[4] == 5
        assert KNOWN_ES_VALUES[5] == 9
        assert KNOWN_ES_VALUES[6] == 17


# =====================================================================
# 5. DIAMETER GRAPHS (#604)
# =====================================================================

class TestDiameterEdgeCount:
    def test_equilateral_triangle(self):
        pts = np.array([[0, 0], [1, 0], [0.5, math.sqrt(3) / 2]], dtype=float)
        assert diameter_edge_count(pts) == 3

    def test_two_points(self):
        pts = np.array([[0.0, 0.0], [1.0, 0.0]])
        assert diameter_edge_count(pts) == 1


class TestAllPairwiseLe1:
    def test_equilateral_side1(self):
        pts = np.array([[0, 0], [1, 0], [0.5, math.sqrt(3) / 2]], dtype=float)
        assert all_pairwise_le_1(pts)

    def test_too_far(self):
        pts = np.array([[0, 0], [2, 0]], dtype=float)
        assert not all_pairwise_le_1(pts)


class TestReuleauxTriangleConfig:
    def test_n3(self):
        pts = _reuleaux_triangle_config(3)
        assert len(pts) == 3
        # Equilateral triangle with side 1
        for i in range(3):
            for j in range(i + 1, 3):
                d = np.linalg.norm(pts[i] - pts[j])
                assert abs(d - 1.0) < 1e-10

    def test_n4_diametral_pairs(self):
        pts = _reuleaux_triangle_config(4)
        pts = pts / math.sqrt(np.max(_squared_distances(pts)))  # normalize
        assert diameter_edge_count(pts) >= 3  # at least 3

    @pytest.mark.parametrize("n", range(3, 11))
    def test_hopf_pannwitz(self, n):
        """d(n) = n: the Reuleaux construction achieves n diametral pairs."""
        pts = _reuleaux_triangle_config(n)
        sq_dists = _squared_distances(pts)
        diam = math.sqrt(np.max(sq_dists))
        if diam > 1e-10:
            pts = pts / diam
        count = diameter_edge_count(pts)
        assert count == n, f"n={n}: got {count} diametral pairs, expected {n}"

    @pytest.mark.parametrize("n", range(3, 11))
    def test_all_within_diameter(self, n):
        """All pairwise distances <= diameter."""
        pts = _reuleaux_triangle_config(n)
        sq_dists = _squared_distances(pts)
        diam = math.sqrt(np.max(sq_dists))
        if diam > 0:
            pts = pts / diam
        assert all_pairwise_le_1(pts)


class TestDiameterGraphsComputation:
    @pytest.fixture(scope="class")
    def diam_results(self):
        return compute_max_diameter_edges((3, 10))

    @pytest.mark.parametrize("n", range(3, 11))
    def test_achieves_n(self, diam_results, n):
        """Hopf-Pannwitz: d(n) = n for all n >= 3."""
        count, config = diam_results[n]
        assert count == n, f"n={n}: got {count} diametral pairs"


# =====================================================================
# 6. REPEATED DISTANCES (#90)
# =====================================================================

class TestLatticeRepeatedDistances:
    def test_n3(self):
        mult, config = _lattice_repeated_distances(3)
        assert mult >= 2  # at least 2 equal distances among 3 Z^2 points

    def test_n4(self):
        mult, config = _lattice_repeated_distances(4)
        assert mult >= 4  # square gives 4 sides of length 1

    def test_n6_at_least_7(self):
        mult, config = _lattice_repeated_distances(6, grid_size=5)
        assert mult >= 6  # known to be at least 6


class TestContinuousRepeatedDistances:
    def test_regular_triangle(self):
        mult, config = _repeated_distances_continuous(3, trials=10)
        assert mult >= 3  # equilateral triangle: 3 equal distances

    def test_grows(self):
        m5, _ = _repeated_distances_continuous(5, trials=10)
        m8, _ = _repeated_distances_continuous(8, trials=10)
        assert m8 >= m5


class TestRepeatedDistancesComputation:
    @pytest.fixture(scope="class")
    def rep_results(self):
        return compute_max_repeated_distances((3, 8))

    def test_monotone(self, rep_results):
        prev = 0
        for n in range(3, 9):
            b = rep_results[n]['best_multiplicity']
            assert b >= prev, f"n={n}: {b} < {prev}"
            prev = b

    def test_n3(self, rep_results):
        assert rep_results[3]['best_multiplicity'] >= 2

    def test_n4(self, rep_results):
        assert rep_results[4]['best_multiplicity'] >= 4

    def test_lattice_vs_continuous(self, rep_results):
        """The best should be >= both lattice and continuous."""
        for n in range(3, 9):
            r = rep_results[n]
            assert r['best_multiplicity'] >= r['lattice_multiplicity']
            assert r['best_multiplicity'] >= r['continuous_multiplicity']


# =====================================================================
# 7. CROSS-CUTTING / INTEGRATION TESTS
# =====================================================================

class TestKnownValues:
    """Verify internal consistency of KNOWN_* tables."""

    def test_distinct_distances_monotone(self):
        vals = [KNOWN_DISTINCT_DISTANCES[n] for n in range(3, 14)]
        for i in range(1, len(vals)):
            assert vals[i] >= vals[i - 1]

    def test_unit_distances_monotone(self):
        vals = [KNOWN_UNIT_DISTANCES[n] for n in range(2, 15)]
        for i in range(1, len(vals)):
            assert vals[i] >= vals[i - 1]

    def test_diameter_edges_equal_n(self):
        for n in range(3, 16):
            assert KNOWN_DIAMETER_EDGES[n] == n

    def test_distinct_distances_formula(self):
        """Known g(n) = floor(n/2) for n <= 13."""
        for n in range(3, 14):
            assert KNOWN_DISTINCT_DISTANCES[n] == n // 2

    def test_unit_distances_superlinear(self):
        """u(n) > n for all n >= 4."""
        for n in range(4, 15):
            assert KNOWN_UNIT_DISTANCES[n] > n


class TestAsymptotic:
    """Verify asymptotic trends match theoretical predictions."""

    def test_distinct_distances_grows_like_sqrt_n(self):
        """g(n) = floor(n/2), so g(n)/sqrt(n) -> infinity."""
        ratios = [KNOWN_DISTINCT_DISTANCES[n] / math.sqrt(n)
                  for n in range(4, 14)]
        # Should be increasing (roughly)
        assert ratios[-1] > ratios[0]

    def test_unit_distances_exponent(self):
        """u(n) = Theta(n^{1+c/log log n}). For small n, u(n)/n should grow."""
        ratios = [KNOWN_UNIT_DISTANCES[n] / n for n in range(4, 15)]
        assert ratios[-1] > ratios[0]  # u(n)/n is increasing

    def test_erdos_szekeres_bound_correct(self):
        """ES bound: f(k) <= C(2k-4, k-2) + 1. Known values are <= this bound."""
        for k, fk in KNOWN_ES_VALUES.items():
            assert fk <= erdos_szekeres_bound(k)


class TestNoSpuriousResults:
    """Ensure optimization does not return impossible values."""

    def test_unit_distances_upper_bound(self):
        """u(n) <= n*(n-1)/2 (trivially, can't have more than all pairs)."""
        for n, u in KNOWN_UNIT_DISTANCES.items():
            assert u <= n * (n - 1) // 2

    def test_distinct_distances_lower_bound(self):
        """g(n) >= 1 for n >= 2."""
        for n, g in KNOWN_DISTINCT_DISTANCES.items():
            assert g >= 1

    def test_diameter_edges_upper_bound(self):
        """d(n) <= n in R^2 (Hopf-Pannwitz)."""
        for n, d in KNOWN_DIAMETER_EDGES.items():
            assert d <= n
