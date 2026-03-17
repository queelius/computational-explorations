"""
Tests for tda_problems.py -- Topological Data Analysis of the Erdos problem space.

Tests the full stack: point-cloud construction, distance matrix, persistent
homology (H0, H1), persistence statistics, Betti curves, Mapper algorithm,
and the solved-vs-open comparison pipeline.
"""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tda_problems import (
    UnionFind,
    _is_formalized,
    _is_open,
    _is_solved,
    _number,
    _oeis_valid,
    _prize,
    _status,
    _tags,
    betti_curve,
    build_point_cloud,
    build_tag_vocabulary,
    compare_solved_vs_open,
    compute_distance_matrix,
    compute_persistence,
    compute_persistence_h0,
    find_significant_features,
    load_problems,
    mapper,
    persistence_entropy,
    persistence_to_lifetimes,
    problem_to_feature_vector,
    split_by_status,
    topological_signature,
    total_persistence,
    _build_vr_simplices,
    _boundary_matrix_mod2,
    _reduce_boundary_matrix,
    _sorted_edges,
)


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def problems():
    """Load the full problem corpus once per module."""
    return load_problems()


@pytest.fixture(scope="module")
def point_cloud(problems):
    """Build the point cloud once per module."""
    return build_point_cloud(problems)


@pytest.fixture(scope="module")
def small_distance_matrix(point_cloud):
    """Distance matrix for first 30 problems."""
    X, _, _ = point_cloud
    return compute_distance_matrix(X[:30])


# =====================================================================
# Data helpers
# =====================================================================

class TestDataHelpers:
    """Test YAML data access helpers."""

    def test_load_problems_count(self, problems):
        assert len(problems) >= 1100

    def test_status_extraction(self, problems):
        for p in problems[:20]:
            s = _status(p)
            assert isinstance(s, str)
            assert len(s) > 0

    def test_tags_returns_set(self, problems):
        for p in problems[:20]:
            tags = _tags(p)
            assert isinstance(tags, set)

    def test_number_is_int(self, problems):
        for p in problems[:20]:
            n = _number(p)
            assert isinstance(n, int)
            assert n >= 0

    def test_prize_nonnegative(self, problems):
        for p in problems[:50]:
            assert _prize(p) >= 0.0

    def test_oeis_valid_filters_na(self):
        p = {"oeis": ["A000001", "N/A", "possible", "A000002"]}
        valid = _oeis_valid(p)
        assert valid == ["A000001", "A000002"]

    def test_oeis_valid_empty(self):
        assert _oeis_valid({}) == []
        assert _oeis_valid({"oeis": "not a list"}) == []

    def test_is_solved_states(self):
        for state in ("proved", "disproved", "solved",
                      "proved (Lean)", "disproved (Lean)", "solved (Lean)"):
            p = {"status": {"state": state}}
            assert _is_solved(p)

    def test_is_solved_rejects_open(self):
        assert not _is_solved({"status": {"state": "open"}})

    def test_is_open(self):
        assert _is_open({"status": {"state": "open"}})
        assert not _is_open({"status": {"state": "proved"}})

    def test_is_formalized(self):
        assert _is_formalized({"formalized": {"state": "yes"}})
        assert not _is_formalized({"formalized": {"state": "no"}})
        assert not _is_formalized({})

    def test_prize_gbp_conversion(self):
        p = {"prize": "\u00a3100"}
        assert _prize(p) == pytest.approx(127.0)

    def test_prize_usd(self):
        p = {"prize": "$500"}
        assert _prize(p) == pytest.approx(500.0)

    def test_prize_no(self):
        assert _prize({"prize": "no"}) == 0.0
        assert _prize({}) == 0.0


# =====================================================================
# Point cloud
# =====================================================================

class TestPointCloud:
    """Test point-cloud construction."""

    def test_tag_vocabulary_sorted(self, problems):
        vocab = build_tag_vocabulary(problems)
        assert vocab == sorted(vocab)
        assert len(vocab) >= 30  # we know there are 41 tags

    def test_tag_vocabulary_no_duplicates(self, problems):
        vocab = build_tag_vocabulary(problems)
        assert len(vocab) == len(set(vocab))

    def test_feature_vector_shape(self, problems):
        vocab = build_tag_vocabulary(problems)
        tag_index = {t: i for i, t in enumerate(vocab)}
        vec = problem_to_feature_vector(problems[0], vocab, tag_index)
        assert vec.shape == (len(vocab) + 6,)

    def test_feature_vector_tag_indicators(self, problems):
        vocab = build_tag_vocabulary(problems)
        tag_index = {t: i for i, t in enumerate(vocab)}
        p = problems[0]
        vec = problem_to_feature_vector(p, vocab, tag_index)
        for t in _tags(p):
            assert vec[tag_index[t]] == 1.0

    def test_point_cloud_shape(self, point_cloud):
        X, vocab, numbers = point_cloud
        assert X.ndim == 2
        assert X.shape[0] >= 1100
        assert X.shape[1] == len(vocab) + 6
        assert len(numbers) == X.shape[0]

    def test_standardized_zero_mean(self, point_cloud):
        X, _, _ = point_cloud
        # After StandardScaler, mean should be ~0 (within float tolerance)
        means = np.abs(X.mean(axis=0))
        assert np.all(means < 1e-10)

    def test_unstandardized_option(self, problems):
        X, _, _ = build_point_cloud(problems, standardize=False)
        # Tag indicators are 0/1, so max should be 1.0 in those cols
        assert X.max() >= 1.0

    def test_numbers_match_problems(self, problems, point_cloud):
        _, _, numbers = point_cloud
        for i in range(min(20, len(problems))):
            assert numbers[i] == _number(problems[i])


# =====================================================================
# Distance matrix
# =====================================================================

class TestDistanceMatrix:

    def test_symmetric(self, small_distance_matrix):
        D = small_distance_matrix
        np.testing.assert_allclose(D, D.T)

    def test_zero_diagonal(self, small_distance_matrix):
        D = small_distance_matrix
        np.testing.assert_allclose(np.diag(D), 0.0)

    def test_non_negative(self, small_distance_matrix):
        assert np.all(small_distance_matrix >= 0)

    def test_triangle_inequality(self, small_distance_matrix):
        D = small_distance_matrix
        n = D.shape[0]
        # Check a sample of triples
        rng = np.random.RandomState(42)
        for _ in range(200):
            i, j, k = rng.choice(n, 3, replace=False)
            assert D[i, j] <= D[i, k] + D[k, j] + 1e-10


# =====================================================================
# Union-Find
# =====================================================================

class TestUnionFind:

    def test_initial_components(self):
        uf = UnionFind(5)
        assert uf.n_components == 5

    def test_union_reduces_components(self):
        uf = UnionFind(5)
        assert uf.union(0, 1)
        assert uf.n_components == 4

    def test_redundant_union(self):
        uf = UnionFind(5)
        uf.union(0, 1)
        assert not uf.union(0, 1)
        assert uf.n_components == 4

    def test_find_after_union(self):
        uf = UnionFind(5)
        uf.union(0, 1)
        uf.union(1, 2)
        assert uf.find(0) == uf.find(2)

    def test_path_compression(self):
        uf = UnionFind(100)
        for i in range(99):
            uf.union(i, i + 1)
        assert uf.n_components == 1
        # After find with path compression, all point to root
        root = uf.find(0)
        for i in range(100):
            assert uf.find(i) == root

    def test_disjoint_components(self):
        uf = UnionFind(6)
        uf.union(0, 1)
        uf.union(2, 3)
        uf.union(4, 5)
        assert uf.n_components == 3
        assert uf.find(0) != uf.find(2)
        assert uf.find(2) != uf.find(4)


# =====================================================================
# H0 persistence
# =====================================================================

class TestPersistenceH0:

    def test_n_intervals_equals_n_points(self, small_distance_matrix):
        h0 = compute_persistence_h0(small_distance_matrix)
        assert len(h0) == small_distance_matrix.shape[0]

    def test_exactly_one_infinite(self, small_distance_matrix):
        h0 = compute_persistence_h0(small_distance_matrix)
        inf_count = sum(1 for _, d in h0 if math.isinf(d))
        assert inf_count == 1

    def test_births_at_zero(self, small_distance_matrix):
        h0 = compute_persistence_h0(small_distance_matrix)
        for b, _ in h0:
            assert b == 0.0

    def test_deaths_non_negative(self, small_distance_matrix):
        h0 = compute_persistence_h0(small_distance_matrix)
        for _, d in h0:
            assert d >= 0.0

    def test_deaths_nondecreasing(self, small_distance_matrix):
        h0 = compute_persistence_h0(small_distance_matrix)
        finite_deaths = sorted(d for _, d in h0 if not math.isinf(d))
        for i in range(len(finite_deaths) - 1):
            assert finite_deaths[i] <= finite_deaths[i + 1]

    def test_empty_matrix(self):
        h0 = compute_persistence_h0(np.zeros((0, 0)))
        assert h0 == []

    def test_single_point(self):
        h0 = compute_persistence_h0(np.zeros((1, 1)))
        assert len(h0) == 1
        assert math.isinf(h0[0][1])

    def test_two_points(self):
        D = np.array([[0.0, 3.0], [3.0, 0.0]])
        h0 = compute_persistence_h0(D)
        assert len(h0) == 2
        deaths = sorted(d for _, d in h0)
        assert deaths[0] == 3.0
        assert math.isinf(deaths[1])

    def test_known_triangle(self):
        """Three points at distances 1, 2, 3: two merges."""
        D = np.array([
            [0.0, 1.0, 3.0],
            [1.0, 0.0, 2.0],
            [3.0, 2.0, 0.0],
        ])
        h0 = compute_persistence_h0(D)
        assert len(h0) == 3
        finite = sorted(d for _, d in h0 if not math.isinf(d))
        assert finite == [1.0, 2.0]


# =====================================================================
# Vietoris-Rips simplices
# =====================================================================

class TestVRSimplices:

    def test_vertices_at_zero(self):
        D = np.array([[0, 1], [1, 0]], dtype=float)
        simplices = _build_vr_simplices(D, max_dim=1, max_edge_length=2.0)
        vertices = [(f, s) for f, s in simplices if len(s) == 1]
        assert len(vertices) == 2
        for f, _ in vertices:
            assert f == 0.0

    def test_edge_filtration_value(self):
        D = np.array([[0, 5], [5, 0]], dtype=float)
        simplices = _build_vr_simplices(D, max_dim=1, max_edge_length=10.0)
        edges = [(f, s) for f, s in simplices if len(s) == 2]
        assert len(edges) == 1
        assert edges[0][0] == 5.0

    def test_triangle_filtration_value(self):
        """Triangle enters at the max pairwise distance."""
        D = np.array([
            [0, 1, 3],
            [1, 0, 2],
            [3, 2, 0],
        ], dtype=float)
        simplices = _build_vr_simplices(D, max_dim=2, max_edge_length=5.0)
        triangles = [(f, s) for f, s in simplices if len(s) == 3]
        assert len(triangles) == 1
        assert triangles[0][0] == 3.0  # max(1, 2, 3) = 3

    def test_edge_cutoff(self):
        D = np.array([[0, 1, 10], [1, 0, 10], [10, 10, 0]], dtype=float)
        simplices = _build_vr_simplices(D, max_dim=1, max_edge_length=5.0)
        edges = [(f, s) for f, s in simplices if len(s) == 2]
        assert len(edges) == 1  # only edge (0,1) at distance 1

    def test_sorted_by_filtration(self):
        D = np.array([
            [0, 3, 1],
            [3, 0, 2],
            [1, 2, 0],
        ], dtype=float)
        simplices = _build_vr_simplices(D, max_dim=2, max_edge_length=5.0)
        filtration_values = [f for f, _ in simplices]
        for i in range(len(filtration_values) - 1):
            assert filtration_values[i] <= filtration_values[i + 1]

    def test_no_simplices_beyond_cutoff(self):
        D = np.array([[0, 100], [100, 0]], dtype=float)
        simplices = _build_vr_simplices(D, max_dim=1, max_edge_length=1.0)
        assert len(simplices) == 2  # just the two vertices


# =====================================================================
# Full persistence (H0 + H1 + H2)
# =====================================================================

class TestComputePersistence:

    def test_returns_all_dimensions(self, small_distance_matrix):
        intervals = compute_persistence(small_distance_matrix, max_dim=2,
                                        max_edge_pct=0.3)
        assert 0 in intervals
        assert 1 in intervals
        assert 2 in intervals

    def test_h0_has_intervals(self, small_distance_matrix):
        intervals = compute_persistence(small_distance_matrix, max_dim=1,
                                        max_edge_pct=0.3)
        assert len(intervals[0]) > 0

    def test_births_before_deaths(self, small_distance_matrix):
        intervals = compute_persistence(small_distance_matrix, max_dim=1,
                                        max_edge_pct=0.3)
        for dim in (0, 1):
            for b, d in intervals[dim]:
                assert b <= d

    def test_known_circle_h1(self):
        """
        Four points on a square should produce at least one H1 feature
        (a loop).  We need max_dim=2 so that triangles are present to
        kill the cycle and produce a finite H1 interval.
        """
        pts = np.array([
            [0, 0], [1, 0], [1, 1], [0, 1],
        ], dtype=float)
        D = np.zeros((4, 4))
        for i in range(4):
            for j in range(4):
                D[i, j] = np.linalg.norm(pts[i] - pts[j])
        intervals = compute_persistence(D, max_dim=2, max_edge_pct=1.0)
        # The square cycle is born at edge-length 1 and killed at sqrt(2)
        h1_finite = [(b, d) for b, d in intervals[1] if not math.isinf(d)]
        assert len(h1_finite) >= 1
        # The longest H1 bar should be [1.0, sqrt(2))
        longest = max(h1_finite, key=lambda x: x[1] - x[0])
        assert longest[0] == pytest.approx(1.0, abs=0.01)
        assert longest[1] == pytest.approx(math.sqrt(2), abs=0.01)

    def test_empty_distance_matrix(self):
        intervals = compute_persistence(np.zeros((0, 0)), max_dim=1)
        assert intervals[0] == []
        assert intervals[1] == []

    def test_single_point(self):
        D = np.zeros((1, 1))
        intervals = compute_persistence(D, max_dim=1, max_edge_pct=1.0)
        # Single point: one infinite H0 feature, nothing else
        assert len(intervals[0]) >= 1


# =====================================================================
# Persistence statistics
# =====================================================================

class TestPersistenceStats:

    def test_lifetimes_finite_only(self):
        intervals = [(0.0, 1.0), (0.0, 3.0), (0.0, float("inf"))]
        lt = persistence_to_lifetimes(intervals)
        assert len(lt) == 2
        np.testing.assert_allclose(lt, [1.0, 3.0])

    def test_lifetimes_empty(self):
        assert len(persistence_to_lifetimes([])) == 0

    def test_lifetimes_all_infinite(self):
        intervals = [(0.0, float("inf")), (1.0, float("inf"))]
        assert len(persistence_to_lifetimes(intervals)) == 0

    def test_significant_features_threshold(self):
        # Median lifetime = 2.0, threshold = 4.0
        intervals = [(0.0, 1.0), (0.0, 2.0), (0.0, 3.0), (0.0, 10.0)]
        sig = find_significant_features(intervals, threshold_factor=2.0)
        # 10.0 lifetime is definitely above 2 * median(1,2,3,10)=2*2.5=5
        assert any(lt >= 5.0 for _, _, lt in sig)

    def test_significant_features_empty(self):
        assert find_significant_features([]) == []

    def test_persistence_entropy_uniform(self):
        """Equal lifetimes -> maximum entropy for that count."""
        intervals = [(0.0, 1.0)] * 8
        ent = persistence_entropy(intervals)
        assert ent == pytest.approx(3.0, abs=0.01)  # log2(8) = 3

    def test_persistence_entropy_single(self):
        intervals = [(0.0, 5.0)]
        ent = persistence_entropy(intervals)
        assert ent == pytest.approx(0.0)  # single feature -> 0 entropy

    def test_persistence_entropy_empty(self):
        assert persistence_entropy([]) == 0.0

    def test_total_persistence_l1(self):
        intervals = [(0.0, 1.0), (0.0, 3.0), (0.0, float("inf"))]
        tp = total_persistence(intervals, p=1.0)
        assert tp == pytest.approx(4.0)

    def test_total_persistence_l2(self):
        intervals = [(0.0, 1.0), (0.0, 3.0)]
        tp = total_persistence(intervals, p=2.0)
        assert tp == pytest.approx(1.0 + 9.0)

    def test_total_persistence_empty(self):
        assert total_persistence([]) == 0.0


# =====================================================================
# Betti curves
# =====================================================================

class TestBettiCurve:

    def test_shape(self):
        intervals = [(0.0, 1.0), (0.5, 2.0)]
        t, betti = betti_curve(intervals, n_steps=50)
        assert len(t) == 50
        assert len(betti) == 50

    def test_empty_intervals(self):
        t, betti = betti_curve([], n_steps=20)
        assert len(t) == 20
        np.testing.assert_array_equal(betti, 0)

    def test_single_interval(self):
        intervals = [(0.0, 1.0)]
        t, betti = betti_curve(intervals, n_steps=100, t_range=(0.0, 1.0))
        # At t=0 the interval is active, at t=1 it has died
        assert betti[0] == 1
        assert betti[-1] == 0

    def test_overlapping_intervals(self):
        intervals = [(0.0, 2.0), (0.0, 2.0), (0.0, 2.0)]
        t, betti = betti_curve(intervals, n_steps=50, t_range=(0.0, 2.0))
        # At the start, all three are active
        assert betti[0] == 3

    def test_nonnegative(self):
        intervals = [(0.0, 1.0), (0.5, 3.0), (1.0, 2.0)]
        _, betti = betti_curve(intervals, n_steps=100)
        assert np.all(betti >= 0)


# =====================================================================
# Mapper
# =====================================================================

class TestMapper:

    def test_basic_structure(self):
        rng = np.random.RandomState(42)
        X = rng.randn(50, 3)
        lens = X[:, 0]
        result = mapper(X, lens, n_intervals=5, overlap_frac=0.3)
        assert "nodes" in result
        assert "edges" in result
        assert "node_sizes" in result
        assert "n_components" in result
        assert len(result["nodes"]) > 0

    def test_all_points_covered(self):
        """Every point should appear in at least one Mapper node."""
        rng = np.random.RandomState(42)
        X = rng.randn(30, 2)
        lens = X[:, 0]
        result = mapper(X, lens, n_intervals=5, overlap_frac=0.5)
        covered = set()
        for _, members in result["nodes"]:
            covered.update(members)
        assert covered == set(range(30))

    def test_edges_connect_overlapping_nodes(self):
        """Edges should only connect nodes that share members."""
        rng = np.random.RandomState(42)
        X = rng.randn(30, 2)
        lens = X[:, 0]
        result = mapper(X, lens, n_intervals=5, overlap_frac=0.5)
        node_members = {nid: set(members) for nid, members in result["nodes"]}
        for a, b in result["edges"]:
            assert node_members[a] & node_members[b], \
                f"Edge ({a}, {b}) connects nodes with no shared members"

    def test_empty_input(self):
        X = np.empty((0, 3))
        lens = np.array([])
        result = mapper(X, lens)
        assert result["nodes"] == []
        assert result["edges"] == []
        assert result["n_components"] == 0

    def test_single_point(self):
        X = np.array([[1.0, 2.0, 3.0]])
        lens = np.array([1.0])
        result = mapper(X, lens, n_intervals=3)
        assert len(result["nodes"]) >= 1

    def test_components_count(self):
        """Two well-separated clusters should yield >= 2 components."""
        rng = np.random.RandomState(42)
        c1 = rng.randn(25, 2) + np.array([10, 10])
        c2 = rng.randn(25, 2) + np.array([-10, -10])
        X = np.vstack([c1, c2])
        lens = X[:, 0]
        result = mapper(X, lens, n_intervals=10, overlap_frac=0.3,
                        cluster_eps=2.0)
        assert result["n_components"] >= 2

    def test_node_sizes_sum(self):
        """Sum of node sizes >= n_points (overlap means double-counting)."""
        rng = np.random.RandomState(42)
        X = rng.randn(40, 3)
        lens = X[:, 0]
        result = mapper(X, lens, n_intervals=5, overlap_frac=0.3)
        total_members = sum(result["node_sizes"])
        assert total_members >= 40  # at least n_points, possibly more


# =====================================================================
# Boundary matrix and reduction
# =====================================================================

class TestBoundaryMatrix:

    def test_vertex_boundary_empty(self):
        simplices = [(0.0, (0,)), (0.0, (1,)), (1.0, (0, 1))]
        cols, idx = _boundary_matrix_mod2(simplices)
        # Vertices have empty boundary
        assert cols[idx[(0,)]] == set()
        assert cols[idx[(1,)]] == set()

    def test_edge_boundary(self):
        simplices = [(0.0, (0,)), (0.0, (1,)), (1.0, (0, 1))]
        cols, idx = _boundary_matrix_mod2(simplices)
        edge_col = cols[idx[(0, 1)]]
        # boundary of (0,1) = (1) + (0) mod 2
        assert edge_col == {idx[(0,)], idx[(1,)]}

    def test_triangle_boundary(self):
        simplices = [
            (0.0, (0,)), (0.0, (1,)), (0.0, (2,)),
            (1.0, (0, 1)), (1.0, (0, 2)), (1.0, (1, 2)),
            (2.0, (0, 1, 2)),
        ]
        cols, idx = _boundary_matrix_mod2(simplices)
        tri_col = cols[idx[(0, 1, 2)]]
        # boundary of (0,1,2) = (1,2) + (0,2) + (0,1) mod 2
        expected = {idx[(0, 1)], idx[(0, 2)], idx[(1, 2)]}
        assert tri_col == expected

    def test_reduction_produces_low_to_col(self):
        simplices = [
            (0.0, (0,)), (0.0, (1,)), (0.0, (2,)),
            (1.0, (0, 1)), (2.0, (0, 2)), (3.0, (1, 2)),
        ]
        cols, idx = _boundary_matrix_mod2(simplices)
        reduced, low_to_col = _reduce_boundary_matrix(cols, len(simplices))
        # low_to_col should map some row indices to column indices
        assert isinstance(low_to_col, dict)


# =====================================================================
# Solved vs. open comparison
# =====================================================================

class TestSolvedVsOpen:

    def test_split_by_status(self, problems, point_cloud):
        X, _, _ = point_cloud
        X_solved, X_open, si, oi = split_by_status(problems, X)
        assert X_solved.shape[0] == len(si)
        assert X_open.shape[0] == len(oi)
        assert X_solved.shape[0] + X_open.shape[0] <= len(problems)
        # No overlap
        assert set(si) & set(oi) == set()

    def test_topological_signature_keys(self, small_distance_matrix):
        sig = topological_signature(small_distance_matrix, max_dim=1,
                                    max_edge_pct=0.3)
        assert "n_points" in sig
        assert "h0_n_features" in sig
        assert "h0_entropy" in sig
        assert "h1_n_features" in sig

    def test_topological_signature_empty(self):
        sig = topological_signature(np.zeros((0, 0)))
        assert sig["n_points"] == 0
        assert sig["h0_n_features"] == 0

    def test_compare_returns_both_groups(self, problems, point_cloud):
        X, _, _ = point_cloud
        result = compare_solved_vs_open(problems, X, max_points=50)
        assert "solved" in result
        assert "open" in result
        assert result["solved"]["n_points"] > 0
        assert result["open"]["n_points"] > 0


# =====================================================================
# Full pipeline integration
# =====================================================================

class TestFullPipeline:

    def test_analyze_returns_expected_keys(self):
        from tda_problems import analyze_problem_topology
        results = analyze_problem_topology(max_points=50, max_dim=1,
                                           max_edge_pct=0.25)
        expected_keys = {
            "n_problems", "n_features", "n_subsampled", "tag_vocab",
            "intervals", "significant_features", "entropies",
            "total_persistence", "betti_curves",
            "mapper_pca1", "mapper_problem_number", "mapper_eccentricity",
            "solved_vs_open",
        }
        assert expected_keys <= set(results.keys())

    def test_n_problems_consistent(self):
        from tda_problems import analyze_problem_topology
        results = analyze_problem_topology(max_points=50, max_dim=1,
                                           max_edge_pct=0.25)
        assert results["n_problems"] >= 1100
        assert results["n_subsampled"] <= 50
        assert results["n_features"] == len(results["tag_vocab"]) + 6

    def test_betti_curves_present(self):
        from tda_problems import analyze_problem_topology
        results = analyze_problem_topology(max_points=30, max_dim=1,
                                           max_edge_pct=0.3)
        assert 0 in results["betti_curves"]
        assert 1 in results["betti_curves"]
        bc0 = results["betti_curves"][0]
        assert "t" in bc0
        assert "betti" in bc0

    def test_mapper_has_nodes(self):
        from tda_problems import analyze_problem_topology
        results = analyze_problem_topology(max_points=50, max_dim=1,
                                           max_edge_pct=0.25)
        for key in ("mapper_pca1", "mapper_problem_number",
                    "mapper_eccentricity"):
            assert len(results[key]["nodes"]) > 0


# =====================================================================
# Topological correctness: known configurations
# =====================================================================

class TestTopologicalCorrectness:
    """
    Test persistence on synthetic configurations where the answer is known.
    """

    def test_two_clusters_h0(self):
        """Two tight clusters far apart -> one long H0 bar."""
        rng = np.random.RandomState(42)
        c1 = rng.randn(10, 2) * 0.1
        c2 = rng.randn(10, 2) * 0.1 + 100
        X = np.vstack([c1, c2])
        D = compute_distance_matrix(X)
        h0 = compute_persistence_h0(D)
        finite = [(b, d) for b, d in h0 if not math.isinf(d)]
        lifetimes = sorted([d - b for b, d in finite], reverse=True)
        # The longest H0 bar should be much longer than the rest
        assert lifetimes[0] > 10 * lifetimes[1]

    def test_three_clusters_h0(self):
        """Three clusters -> two long H0 bars."""
        rng = np.random.RandomState(42)
        c1 = rng.randn(8, 2) * 0.1
        c2 = rng.randn(8, 2) * 0.1 + 50
        c3 = rng.randn(8, 2) * 0.1 + 100
        X = np.vstack([c1, c2, c3])
        D = compute_distance_matrix(X)
        h0 = compute_persistence_h0(D)
        lifetimes = sorted(
            [d - b for b, d in h0 if not math.isinf(d)],
            reverse=True)
        # Top 2 lifetimes should dominate
        assert lifetimes[0] > 5 * lifetimes[2]
        assert lifetimes[1] > 5 * lifetimes[2]

    def test_collinear_no_h1(self):
        """Points on a line -> no H1 features."""
        X = np.array([[i, 0] for i in range(10)], dtype=float)
        D = compute_distance_matrix(X)
        intervals = compute_persistence(D, max_dim=1, max_edge_pct=1.0)
        h1_finite = [(b, d) for b, d in intervals[1] if not math.isinf(d)]
        assert len(h1_finite) == 0

    def test_square_has_h1(self):
        """Four points forming a square -> at least one finite H1 loop.
        Need max_dim=2 so triangles can kill the cycle."""
        pts = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
        D = compute_distance_matrix(pts)
        intervals = compute_persistence(D, max_dim=2, max_edge_pct=1.0)
        h1_finite = [(b, d) for b, d in intervals[1] if not math.isinf(d)]
        assert len(h1_finite) >= 1


# =====================================================================
# Edge cases
# =====================================================================

class TestEdgeCases:

    def test_identical_points(self):
        """All-zero distances -> all components merge at 0."""
        D = np.zeros((5, 5))
        h0 = compute_persistence_h0(D)
        finite = [(b, d) for b, d in h0 if not math.isinf(d)]
        # All merges happen at distance 0
        for b, d in finite:
            assert d == 0.0

    def test_single_point_persistence(self):
        D = np.zeros((1, 1))
        intervals = compute_persistence(D, max_dim=1, max_edge_pct=1.0)
        assert len(intervals[0]) >= 1
        assert len(intervals[1]) == 0

    def test_persistence_entropy_all_infinite(self):
        """All-infinite intervals have 0 entropy (no finite lifetimes)."""
        intervals = [(0.0, float("inf")), (0.0, float("inf"))]
        assert persistence_entropy(intervals) == 0.0

    def test_total_persistence_infinite_excluded(self):
        intervals = [(0.0, 1.0), (0.0, float("inf"))]
        tp = total_persistence(intervals, p=1.0)
        assert tp == pytest.approx(1.0)

    def test_sorted_edges_count(self):
        D = np.array([[0, 1, 2], [1, 0, 3], [2, 3, 0]], dtype=float)
        edges = _sorted_edges(D)
        assert len(edges) == 3  # n*(n-1)/2 = 3

    def test_sorted_edges_order(self):
        D = np.array([[0, 5, 1], [5, 0, 3], [1, 3, 0]], dtype=float)
        edges = _sorted_edges(D)
        weights = [w for w, _, _ in edges]
        assert weights == sorted(weights)
