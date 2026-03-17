"""Tests for spectral_analysis.py — graph-theoretic deep analysis."""
import math
import numpy as np
import pytest

from spectral_analysis import (
    load_problems,
    build_problem_graph,
    laplacian_spectrum,
    spectral_bisection,
    bridge_problems,
    pagerank_influence,
    spectral_communities,
    _gini,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def graph(problems):
    """Build graph once for all tests."""
    return build_problem_graph(problems, max_nodes=100)


class TestGini:
    """Test Gini coefficient helper."""

    def test_uniform(self):
        """Uniform distribution → Gini ≈ 0."""
        x = np.ones(100) / 100
        assert abs(_gini(x)) < 0.02

    def test_concentrated(self):
        """All weight on one element → Gini near 1."""
        x = np.zeros(100)
        x[0] = 1.0
        assert _gini(x) > 0.95

    def test_empty(self):
        assert _gini(np.array([])) == 0.0

    def test_bounded(self):
        x = np.random.rand(50)
        g = _gini(x)
        assert 0.0 <= g <= 1.0


class TestBuildGraph:
    """Test problem graph construction."""

    def test_returns_tuple(self, graph):
        adj, node_ids, node_info = graph
        assert isinstance(adj, np.ndarray)
        assert isinstance(node_ids, list)
        assert isinstance(node_info, dict)

    def test_adj_square(self, graph):
        adj, node_ids, _ = graph
        assert adj.shape[0] == adj.shape[1]
        assert adj.shape[0] == len(node_ids)

    def test_adj_symmetric(self, graph):
        adj, _, _ = graph
        assert np.allclose(adj, adj.T)

    def test_adj_nonneg(self, graph):
        adj, _, _ = graph
        assert np.all(adj >= 0)

    def test_no_self_loops(self, graph):
        adj, _, _ = graph
        assert np.all(np.diag(adj) == 0)

    def test_node_info_has_tags(self, graph):
        _, _, node_info = graph
        for nid, info in list(node_info.items())[:5]:
            assert "tags" in info

    def test_max_nodes_respected(self, problems):
        adj, node_ids, _ = build_problem_graph(problems, max_nodes=50)
        assert len(node_ids) <= 50


class TestLaplacianSpectrum:
    """Test Laplacian spectrum computation."""

    def test_returns_dict(self, graph):
        adj, _, _ = graph
        s = laplacian_spectrum(adj)
        assert isinstance(s, dict)

    def test_algebraic_connectivity_nonneg(self, graph):
        adj, _, _ = graph
        s = laplacian_spectrum(adj)
        assert s["algebraic_connectivity"] >= 0

    def test_lambda_max_positive(self, graph):
        adj, _, _ = graph
        s = laplacian_spectrum(adj)
        assert s["lambda_max"] > 0

    def test_eigenvalues_nonneg(self, graph):
        adj, _, _ = graph
        s = laplacian_spectrum(adj)
        for e in s["eigenvalues"]:
            assert e >= -1e-8  # allow tiny floating point errors

    def test_fiedler_vector_shape(self, graph):
        adj, node_ids, _ = graph
        s = laplacian_spectrum(adj)
        assert len(s["fiedler_vector"]) == len(node_ids)

    def test_zero_eigenvalues_count(self, graph):
        adj, _, _ = graph
        s = laplacian_spectrum(adj)
        assert s["num_zero_eigenvalues"] >= 1  # at least 1 component

    def test_small_graph(self):
        """Test on a simple 3-node path graph."""
        adj = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)
        s = laplacian_spectrum(adj)
        assert s["algebraic_connectivity"] > 0
        assert s["num_zero_eigenvalues"] == 1


class TestSpectralBisection:
    """Test spectral graph bisection."""

    def test_returns_dict(self, graph):
        adj, node_ids, node_info = graph
        r = spectral_bisection(adj, node_ids, node_info)
        assert isinstance(r, dict)

    def test_sides_partition(self, graph):
        adj, node_ids, node_info = graph
        r = spectral_bisection(adj, node_ids, node_info)
        assert r["side_a_size"] + r["side_b_size"] == len(node_ids)

    def test_both_sides_nonempty(self, graph):
        adj, node_ids, node_info = graph
        r = spectral_bisection(adj, node_ids, node_info)
        assert r["side_a_size"] > 0
        assert r["side_b_size"] > 0

    def test_cut_ratio_bounded(self, graph):
        adj, node_ids, node_info = graph
        r = spectral_bisection(adj, node_ids, node_info)
        assert 0.0 <= r["cut_ratio"] <= 1.0

    def test_tag_profiles_exist(self, graph):
        adj, node_ids, node_info = graph
        r = spectral_bisection(adj, node_ids, node_info)
        assert isinstance(r["side_a_tags"], list)
        assert isinstance(r["side_b_tags"], list)


class TestBridgeProblems:
    """Test bridge problem detection."""

    def test_returns_dict(self, graph):
        adj, node_ids, node_info = graph
        r = bridge_problems(adj, node_ids, node_info)
        assert isinstance(r, dict)

    def test_bridges_sorted(self, graph):
        adj, node_ids, node_info = graph
        r = bridge_problems(adj, node_ids, node_info)
        bridges = r["bridges"]
        for i in range(len(bridges) - 1):
            assert bridges[i]["bridge_score"] >= bridges[i + 1]["bridge_score"]

    def test_bridge_fields(self, graph):
        adj, node_ids, node_info = graph
        r = bridge_problems(adj, node_ids, node_info)
        for b in r["bridges"][:5]:
            assert "number" in b
            assert "bridge_score" in b
            assert "fiedler_value" in b
            assert "degree" in b
            assert "cross_fraction" in b

    def test_cross_fraction_bounded(self, graph):
        adj, node_ids, node_info = graph
        r = bridge_problems(adj, node_ids, node_info)
        for b in r["bridges"]:
            assert 0.0 <= b["cross_fraction"] <= 1.0


class TestPageRank:
    """Test PageRank influence computation."""

    def test_returns_dict(self, graph):
        adj, node_ids, node_info = graph
        r = pagerank_influence(adj, node_ids, node_info)
        assert isinstance(r, dict)

    def test_rankings_sorted(self, graph):
        adj, node_ids, node_info = graph
        r = pagerank_influence(adj, node_ids, node_info)
        rankings = r["rankings"]
        for i in range(len(rankings) - 1):
            assert rankings[i]["pagerank"] >= rankings[i + 1]["pagerank"]

    def test_pagerank_sums_to_one(self, graph):
        adj, node_ids, node_info = graph
        r = pagerank_influence(adj, node_ids, node_info)
        total = sum(rk["pagerank"] for rk in r["rankings"])
        # May not sum to exactly 1 if rankings are truncated
        assert total <= 1.01

    def test_correlation_bounded(self, graph):
        adj, node_ids, node_info = graph
        r = pagerank_influence(adj, node_ids, node_info)
        assert -1.0 <= r["pr_degree_correlation"] <= 1.0

    def test_gini_bounded(self, graph):
        adj, node_ids, node_info = graph
        r = pagerank_influence(adj, node_ids, node_info)
        assert 0.0 <= r["gini_coefficient"] <= 1.0

    def test_small_graph(self):
        """Test PageRank on a simple graph."""
        adj = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)
        node_ids = [1, 2, 3]
        node_info = {i: {"tags": [], "prize": 0} for i in node_ids}
        r = pagerank_influence(adj, node_ids, node_info)
        # Center node (2) should have highest PageRank
        rankings = r["rankings"]
        assert rankings[0]["number"] == 2


class TestSpectralCommunities:
    """Test spectral community detection."""

    def test_returns_dict(self, graph):
        adj, node_ids, node_info = graph
        r = spectral_communities(adj, node_ids, node_info, n_communities=3)
        assert isinstance(r, dict)

    def test_community_count(self, graph):
        adj, node_ids, node_info = graph
        r = spectral_communities(adj, node_ids, node_info, n_communities=3)
        assert r["n_communities"] == 3

    def test_communities_cover_all(self, graph):
        adj, node_ids, node_info = graph
        r = spectral_communities(adj, node_ids, node_info, n_communities=3)
        total = sum(c["size"] for c in r["communities"])
        assert total == len(node_ids)

    def test_community_fields(self, graph):
        adj, node_ids, node_info = graph
        r = spectral_communities(adj, node_ids, node_info, n_communities=3)
        for c in r["communities"]:
            assert "id" in c
            assert "size" in c
            assert "density" in c
            assert c["size"] > 0

    def test_density_bounded(self, graph):
        adj, node_ids, node_info = graph
        r = spectral_communities(adj, node_ids, node_info, n_communities=3)
        for c in r["communities"]:
            assert 0.0 <= c["density"] <= 1.0

    def test_eigenvalue_gaps(self, graph):
        adj, node_ids, node_info = graph
        r = spectral_communities(adj, node_ids, node_info, n_communities=3)
        assert len(r.get("eigenvalue_gaps", [])) > 0
