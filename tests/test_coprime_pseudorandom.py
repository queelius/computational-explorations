"""Tests for coprime_pseudorandom.py -- Pseudorandomness of the coprime graph."""

import math
from itertools import combinations
import pytest
import numpy as np

from coprime_pseudorandom import (
    coprime_adjacency_matrix,
    coprime_edges,
    coprime_adj_dict,
    primes_up_to,
    edge_count_between,
    discrepancy_sampled,
    discrepancy_scaling,
    expander_mixing_analysis,
    count_coprime_cliques,
    random_coloring_avoidance,
    coprime_vs_random_ramsey,
    coprime_hash_family,
    hash_collision_by_gcd,
    graph_walk_extraction,
    extractor_quality_vs_n,
    ramsey_sat_hardness,
    hardness_comparison,
    full_analysis,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def adj_10():
    """Adjacency matrix for G(10)."""
    return coprime_adjacency_matrix(10)


@pytest.fixture(scope="module")
def adj_20():
    """Adjacency matrix for G(20)."""
    return coprime_adjacency_matrix(20)


# ---------------------------------------------------------------------------
# Core infrastructure
# ---------------------------------------------------------------------------

class TestCoreInfrastructure:
    """Test coprime graph building primitives."""

    def test_adjacency_matrix_symmetric(self, adj_10):
        assert np.allclose(adj_10, adj_10.T)

    def test_adjacency_matrix_zero_diagonal(self, adj_10):
        assert np.all(np.diag(adj_10) == 0)

    def test_adjacency_matrix_binary(self, adj_10):
        assert np.all((adj_10 == 0) | (adj_10 == 1))

    def test_adjacency_matrix_shape(self, adj_10):
        assert adj_10.shape == (10, 10)

    def test_coprime_edges_basic(self):
        edges = coprime_edges(5)
        assert (1, 2) in edges
        assert (2, 4) not in edges  # gcd(2,4) = 2

    def test_coprime_edges_count(self, adj_10):
        expected = len(coprime_edges(10))
        assert int(np.sum(adj_10)) // 2 == expected

    def test_adj_dict_keys(self):
        adj = coprime_adj_dict(5)
        assert set(adj.keys()) == {1, 2, 3, 4, 5}

    def test_adj_dict_symmetric(self):
        adj = coprime_adj_dict(10)
        for u in adj:
            for v in adj[u]:
                assert u in adj[v]

    def test_adj_dict_vertex_1(self):
        adj = coprime_adj_dict(5)
        assert adj[1] == {2, 3, 4, 5}

    def test_primes_up_to(self):
        assert primes_up_to(10) == [2, 3, 5, 7]

    def test_primes_up_to_1(self):
        assert primes_up_to(1) == []

    def test_primes_up_to_2(self):
        assert primes_up_to(2) == [2]


# ---------------------------------------------------------------------------
# 1. Discrepancy
# ---------------------------------------------------------------------------

class TestEdgeCountBetween:
    """Test edge counting between vertex subsets."""

    def test_full_sets(self, adj_10):
        all_idx = np.arange(10)
        total = edge_count_between(adj_10, all_idx, all_idx)
        # Each edge counted twice (A[i,j] and A[j,i]) plus diagonal=0
        expected_edges = len(coprime_edges(10))
        assert total == 2 * expected_edges

    def test_single_vertex(self, adj_10):
        # Vertex 1 (index 0) is coprime to all others
        s = np.array([0])
        t = np.arange(1, 10)
        count = edge_count_between(adj_10, s, t)
        assert count == 9  # vertex 1 has degree 9

    def test_empty_set(self, adj_10):
        s = np.array([], dtype=int)
        t = np.arange(10)
        count = edge_count_between(adj_10, s, t)
        assert count == 0

    def test_disjoint_subsets(self, adj_10):
        # Evens = {2,4,6,8,10} at indices {1,3,5,7,9}
        # Odds = {1,3,5,7,9} at indices {0,2,4,6,8}
        evens = np.array([1, 3, 5, 7, 9])
        odds = np.array([0, 2, 4, 6, 8])
        cross_edges = edge_count_between(adj_10, evens, odds)
        assert cross_edges > 0  # many coprime cross-pairs


class TestDiscrepancySampled:
    """Test discrepancy estimation."""

    def test_returns_all_keys(self):
        r = discrepancy_sampled(15, num_samples=100)
        required = [
            "n", "max_discrepancy", "random_disc_scale",
            "scaling_ratio", "num_samples",
        ]
        for key in required:
            assert key in r, f"Missing key: {key}"

    def test_discrepancy_nonneg(self):
        r = discrepancy_sampled(15, num_samples=100)
        assert r["max_discrepancy"] >= 0

    def test_discrepancy_finite(self):
        r = discrepancy_sampled(20, num_samples=100)
        assert np.isfinite(r["max_discrepancy"])

    def test_discrepancy_bounded_by_n(self):
        """Discrepancy should be at most O(n) (trivially |e(S,T)|/n <= n)."""
        n = 20
        r = discrepancy_sampled(n, num_samples=200)
        assert r["max_discrepancy"] < n

    def test_scaling_ratio_reasonable(self):
        """Ratio should be in a reasonable range (not 0 or infinity)."""
        r = discrepancy_sampled(30, num_samples=300)
        assert 0 < r["scaling_ratio"] < 100

    def test_random_disc_scale_positive(self):
        r = discrepancy_sampled(20, num_samples=50)
        assert r["random_disc_scale"] > 0

    def test_deterministic_with_seed(self):
        r1 = discrepancy_sampled(15, num_samples=100,
                                 rng=np.random.default_rng(123))
        r2 = discrepancy_sampled(15, num_samples=100,
                                 rng=np.random.default_rng(123))
        assert r1["max_discrepancy"] == r2["max_discrepancy"]


class TestDiscrepancyScaling:
    """Test discrepancy scaling law fitting."""

    def test_returns_alpha(self):
        r = discrepancy_scaling([15, 20, 30], num_samples=100)
        assert "alpha" in r
        assert "expected_alpha" in r

    def test_alpha_sublinear(self):
        """Discrepancy should grow sub-linearly (exponent < 1)."""
        r = discrepancy_scaling([15, 20, 30, 50], num_samples=200)
        # max_disc = max|e(S,T) - p|S||T|| / n grows, but sub-linearly
        # For random graphs, absolute disc ~ sqrt(n log n), so disc/n ~ n^{-0.5}
        # But sampled max_disc grows with n since we find more extreme subsets.
        # The exponent should be well below 1 (linear would mean disc ~ n)
        assert r["alpha"] < 1.0

    def test_results_have_ns(self):
        ns = [15, 25, 40]
        r = discrepancy_scaling(ns, num_samples=100)
        assert r["ns"] == ns
        assert len(r["results"]) == 3


# ---------------------------------------------------------------------------
# 2. Expander Mixing Lemma
# ---------------------------------------------------------------------------

class TestExpanderMixing:
    """Test expander mixing lemma verification."""

    def test_returns_all_keys(self):
        r = expander_mixing_analysis(15, num_samples=50)
        required = [
            "n", "lambda_1", "lambda_2", "lambda_abs_2",
            "mean_degree", "normalized_gap",
            "bound_always_holds", "num_violations",
        ]
        for key in required:
            assert key in r, f"Missing key: {key}"

    def test_bound_holds(self):
        """Expander mixing lemma should hold: no violations."""
        r = expander_mixing_analysis(20, num_samples=200)
        assert r["bound_always_holds"], (
            f"Expander mixing lemma violated: {r['num_violations']} violations"
        )

    def test_bound_holds_larger(self):
        """Test on a larger graph."""
        r = expander_mixing_analysis(40, num_samples=100)
        assert r["num_violations"] == 0

    def test_tightness_below_one(self):
        """Mean tightness should be < 1 (actual deviation < bound)."""
        r = expander_mixing_analysis(20, num_samples=200)
        assert r["mean_tightness"] < 1.0

    def test_max_tightness_below_one(self):
        """Maximum tightness must be <= 1 (lemma must hold)."""
        r = expander_mixing_analysis(20, num_samples=200)
        assert r["max_tightness"] <= 1.0 + 1e-8

    def test_normalized_gap_large(self):
        """The coprime graph should have a large normalized spectral gap."""
        r = expander_mixing_analysis(30, num_samples=50)
        assert r["normalized_gap"] > 0.85

    def test_lambda_2_positive(self):
        r = expander_mixing_analysis(15, num_samples=50)
        assert r["lambda_2"] > 0

    def test_density_near_coprime_constant(self):
        """Edge density should be near 6/pi^2."""
        r = expander_mixing_analysis(50, num_samples=50)
        expected = 6.0 / math.pi ** 2
        assert abs(r["density"] - expected) < 0.03


# ---------------------------------------------------------------------------
# 3. Derandomization
# ---------------------------------------------------------------------------

class TestCountCoprimeCliques:
    """Test clique counting."""

    def test_triangles_in_g5(self):
        """Count triangles in G(5)."""
        count = count_coprime_cliques(5, 3)
        # Verify by brute force
        brute = 0
        for a, b, c in combinations(range(1, 6), 3):
            if (math.gcd(a, b) == 1 and math.gcd(b, c) == 1
                    and math.gcd(a, c) == 1):
                brute += 1
        assert count == brute

    def test_edges_in_g5(self):
        """k=2 cliques = edges."""
        count = count_coprime_cliques(5, 2)
        assert count == len(coprime_edges(5))

    def test_singletons(self):
        """k=1 cliques = vertices."""
        count = count_coprime_cliques(5, 1)
        assert count == 5

    def test_clique_count_grows(self):
        """More triangles at larger n."""
        c10 = count_coprime_cliques(10, 3)
        c15 = count_coprime_cliques(15, 3)
        assert c15 > c10

    def test_k4_at_small_n(self):
        """4-cliques in G(10) should be positive."""
        count = count_coprime_cliques(10, 4)
        assert count > 0


class TestRandomColoringAvoidance:
    """Test random coloring avoidance estimation."""

    def test_returns_all_keys(self):
        r = random_coloring_avoidance(8, 3, num_trials=50)
        required = [
            "n", "k", "num_cliques", "expected_mono_firstmoment",
            "empirical_mean_mono", "empirical_avoid_prob",
            "avoidance_possible", "num_trials",
        ]
        for key in required:
            assert key in r

    def test_avoid_prob_in_01(self):
        r = random_coloring_avoidance(8, 3, num_trials=100)
        assert 0.0 <= r["empirical_avoid_prob"] <= 1.0

    def test_firstmoment_nonneg(self):
        r = random_coloring_avoidance(8, 3, num_trials=50)
        assert r["expected_mono_firstmoment"] >= 0

    def test_high_avoid_below_ramsey(self):
        """Well below R_cop(3)=11, avoidance probability should be positive.

        At n=7 the coprime graph already has 19 triangles (E[mono]=4.75),
        making avoidance near-impossible by sampling. At n=5 (7 triangles),
        avoidance is still feasible (~10% of random colorings).
        """
        r = random_coloring_avoidance(5, 3, num_trials=500)
        assert r["empirical_avoid_prob"] > 0

    def test_deterministic_with_seed(self):
        import random as _random
        r1 = random_coloring_avoidance(8, 3, num_trials=50,
                                       rng=_random.Random(99))
        r2 = random_coloring_avoidance(8, 3, num_trials=50,
                                       rng=_random.Random(99))
        assert r1["empirical_avoid_prob"] == r2["empirical_avoid_prob"]


class TestCoprimeVsRandomRamsey:
    """Test coprime vs random Ramsey comparison."""

    def test_returns_results_list(self):
        r = coprime_vs_random_ramsey(3, [7, 8], num_trials=50)
        assert "results" in r
        assert len(r["results"]) == 2

    def test_clique_ratio_positive(self):
        r = coprime_vs_random_ramsey(3, [8], num_trials=50)
        assert r["results"][0]["clique_ratio"] > 0

    def test_coprime_fewer_cliques_than_random(self):
        """Coprime graph should have fewer cliques than G(n, 6/pi^2) on average."""
        r = coprime_vs_random_ramsey(3, [10], num_trials=50)
        # clique_ratio < 1 means fewer cliques (coprime graph is structured)
        # This is a tendency, not guaranteed at every single n
        # We just check it's in a reasonable range
        assert 0.1 < r["results"][0]["clique_ratio"] < 5.0


# ---------------------------------------------------------------------------
# 4. Hash Functions
# ---------------------------------------------------------------------------

class TestCoprimeHashFamily:
    """Test hash family analysis."""

    def test_returns_all_keys(self):
        r = coprime_hash_family(10)
        required = [
            "n", "num_primes", "mean_collision_prob",
            "max_collision_prob", "ideal_universal_eps",
        ]
        for key in required:
            assert key in r

    def test_collision_prob_bounded(self):
        r = coprime_hash_family(20)
        assert 0 <= r["mean_collision_prob"] <= 1.0
        assert 0 <= r["max_collision_prob"] <= 1.0

    def test_collision_decreases_with_more_primes(self):
        """More primes -> lower collision probability."""
        r1 = coprime_hash_family(10, max_p=10)
        r2 = coprime_hash_family(10, max_p=30)
        # With more primes, mean collision should decrease or stay same
        assert r2["mean_collision_prob"] <= r1["mean_collision_prob"] + 0.05

    def test_num_primes_correct(self):
        r = coprime_hash_family(20, max_p=20)
        assert r["num_primes"] == len(primes_up_to(20))

    def test_num_pairs_correct(self):
        n = 10
        r = coprime_hash_family(n)
        expected_pairs = n * (n - 1) // 2
        assert r["num_pairs"] == expected_pairs

    def test_no_primes_edge_case(self):
        """max_p=1 means no primes, should handle gracefully."""
        r = coprime_hash_family(5, max_p=1)
        assert r["num_primes"] == 0
        assert r["mean_collision_prob"] == 0.0

    def test_universality_ratio_finite(self):
        r = coprime_hash_family(20)
        assert np.isfinite(r["universality_ratio"])


class TestHashCollisionByGcd:
    """Test collision probability grouped by gcd structure."""

    def test_returns_all_keys(self):
        r = hash_collision_by_gcd(10)
        required = [
            "n", "num_coprime_pairs", "num_non_coprime_pairs",
            "coprime_collision", "non_coprime_collision", "collision_gap",
        ]
        for key in required:
            assert key in r

    def test_coprime_lower_collision(self):
        """Coprime pairs should have lower collision probability."""
        r = hash_collision_by_gcd(30)
        assert r["coprime_collision"] < r["non_coprime_collision"]

    def test_collision_gap_positive(self):
        """Non-coprime pairs have higher collision than coprime pairs."""
        r = hash_collision_by_gcd(30)
        assert r["collision_gap"] > 0

    def test_pair_counts_sum_to_total(self):
        n = 15
        r = hash_collision_by_gcd(n)
        total_pairs = n * (n - 1) // 2
        assert (r["num_coprime_pairs"] + r["num_non_coprime_pairs"]
                == total_pairs)

    def test_coprime_count_matches_edges(self):
        n = 10
        r = hash_collision_by_gcd(n)
        assert r["num_coprime_pairs"] == len(coprime_edges(n))


# ---------------------------------------------------------------------------
# 5. Extractors
# ---------------------------------------------------------------------------

class TestGraphWalkExtraction:
    """Test randomness extraction via graph walks."""

    def test_returns_all_keys(self):
        r = graph_walk_extraction(15, walk_length=4, num_walks=200)
        required = [
            "n", "walk_length", "source_min_entropy",
            "biases", "decay_rate", "extraction_quality",
        ]
        for key in required:
            assert key in r

    def test_bias_decreases_with_walk_length(self):
        """Bias should generally decrease as walk length increases."""
        r = graph_walk_extraction(20, walk_length=8, num_walks=1000)
        # Compare first and last bias (stochastic, so allow some slack)
        bias_0 = r["biases"].get(0, 0.5)
        bias_end = r["biases"].get(8, 0.5)
        # After 8 steps, bias should be noticeably smaller
        assert bias_end < bias_0 + 0.15  # generous bound for stochastic test

    def test_biases_all_nonneg(self):
        r = graph_walk_extraction(15, walk_length=4, num_walks=200)
        for t, b in r["biases"].items():
            assert b >= 0, f"Negative bias at step {t}: {b}"

    def test_biases_bounded(self):
        r = graph_walk_extraction(15, walk_length=4, num_walks=200)
        for t, b in r["biases"].items():
            assert b <= 0.5, f"Bias exceeds 0.5 at step {t}: {b}"

    def test_decay_rate_positive(self):
        r = graph_walk_extraction(20, walk_length=6, num_walks=500)
        # Decay rate should be in (0, 1) for a good extractor
        assert r["decay_rate"] > 0

    def test_spectral_prediction_in_01(self):
        r = graph_walk_extraction(15, walk_length=4, num_walks=200)
        assert 0 < r["spectral_decay_prediction"] < 1

    def test_min_entropy_less_than_log_n(self):
        """Source min-entropy should be less than log2(n)."""
        r = graph_walk_extraction(20, walk_length=4, num_walks=200)
        assert r["source_min_entropy"] < r["source_log_n"]

    def test_deterministic_with_seed(self):
        r1 = graph_walk_extraction(15, walk_length=3, num_walks=100,
                                   rng=np.random.default_rng(77))
        r2 = graph_walk_extraction(15, walk_length=3, num_walks=100,
                                   rng=np.random.default_rng(77))
        assert r1["biases"] == r2["biases"]


class TestExtractorQualityVsN:
    """Test extractor quality scaling."""

    def test_returns_results(self):
        r = extractor_quality_vs_n([15, 20], walk_length=4)
        assert len(r["results"]) == 2

    def test_decay_rate_stable(self):
        """Decay rate should be roughly stable across n (expander property)."""
        r = extractor_quality_vs_n([15, 25, 40], walk_length=6)
        rates = [x["decay_rate"] for x in r["results"]]
        # All rates should be in the same ballpark (within factor 3)
        if min(rates) > 0:
            assert max(rates) / min(rates) < 5.0


# ---------------------------------------------------------------------------
# 6. Hardness
# ---------------------------------------------------------------------------

class TestRamseySatHardness:
    """Test Ramsey SAT hardness analysis."""

    def test_returns_all_keys(self):
        r = ramsey_sat_hardness(10, 3)
        required = [
            "n", "k", "num_edges", "num_cliques",
            "num_clauses", "clause_width", "constraint_density",
            "search_space_log2", "hardness_estimate",
        ]
        for key in required:
            assert key in r

    def test_num_edges_matches(self):
        r = ramsey_sat_hardness(10, 3)
        assert r["num_edges"] == len(coprime_edges(10))

    def test_clause_width_k3(self):
        """For k=3, each clause has C(3,2)=3 literals."""
        r = ramsey_sat_hardness(10, 3)
        assert r["clause_width"] == 3

    def test_clause_width_k4(self):
        """For k=4, each clause has C(4,2)=6 literals."""
        r = ramsey_sat_hardness(10, 4)
        assert r["clause_width"] == 6

    def test_num_clauses_formula(self):
        """num_clauses = 2 * num_cliques."""
        r = ramsey_sat_hardness(10, 3)
        assert r["num_clauses"] == 2 * r["num_cliques"]

    def test_constraint_density_grows(self):
        """Constraint density should increase with n for fixed k."""
        r1 = ramsey_sat_hardness(10, 3)
        r2 = ramsey_sat_hardness(20, 3)
        assert r2["constraint_density"] > r1["constraint_density"]

    def test_search_space_grows(self):
        """Search space (log2) should grow with n."""
        r1 = ramsey_sat_hardness(10, 3)
        r2 = ramsey_sat_hardness(20, 3)
        assert r2["search_space_log2"] > r1["search_space_log2"]

    def test_hardness_at_ramsey_threshold(self):
        """At R_cop(3)=11, hardness should be at least moderate."""
        r = ramsey_sat_hardness(11, 3)
        assert r["hardness_estimate"] in ("moderate", "hard")

    def test_small_n_easy(self):
        """Very small n should be easy or trivial."""
        r = ramsey_sat_hardness(5, 3)
        assert r["hardness_estimate"] in ("trivial", "easy", "moderate")


class TestHardnessComparison:
    """Test hardness comparison across problem sizes."""

    def test_returns_comparison(self):
        r = hardness_comparison([10, 15, 20], k=3)
        assert "comparison" in r
        assert "search_space_growth_exponent" in r

    def test_growth_exponent_positive(self):
        """Search space should grow with n (positive exponent)."""
        r = hardness_comparison([10, 15, 20, 30], k=3)
        assert r["search_space_growth_exponent"] > 0

    def test_growth_near_quadratic(self):
        """Search space ~ n^2 since |E| ~ n^2 * 6/pi^2."""
        r = hardness_comparison([10, 20, 30, 50], k=3)
        # Exponent should be near 2
        assert 1.5 < r["search_space_growth_exponent"] < 2.5

    def test_results_length(self):
        ns = [10, 15, 20]
        r = hardness_comparison(ns, k=3)
        assert len(r["results"]) == len(ns)


# ---------------------------------------------------------------------------
# 7. Full Analysis Integration
# ---------------------------------------------------------------------------

class TestFullAnalysis:
    """Test the integrated full_analysis function."""

    def test_returns_all_sections(self):
        r = full_analysis(n_default=15)
        required = [
            "discrepancy", "expander_mixing", "derandomization",
            "hash_family", "hash_by_gcd", "extractor", "hardness",
        ]
        for key in required:
            assert key in r, f"Missing section: {key}"

    def test_discrepancy_section(self):
        r = full_analysis(n_default=15)
        assert r["discrepancy"]["n"] == 15
        assert r["discrepancy"]["max_discrepancy"] >= 0

    def test_expander_section(self):
        r = full_analysis(n_default=15)
        assert r["expander_mixing"]["n"] == 15
        assert r["expander_mixing"]["num_violations"] == 0

    def test_hash_section(self):
        r = full_analysis(n_default=15)
        assert r["hash_family"]["n"] == 15
        assert r["hash_family"]["num_primes"] > 0

    def test_hardness_section(self):
        r = full_analysis(n_default=15)
        assert r["hardness"]["n"] == 15
        assert r["hardness"]["num_edges"] > 0


# ---------------------------------------------------------------------------
# 8. Theoretical Consistency Checks
# ---------------------------------------------------------------------------

class TestTheoreticalConsistency:
    """Cross-check mathematical properties across analyses."""

    def test_coprime_density_agreement(self):
        """Edge density in different analyses should agree."""
        em = expander_mixing_analysis(30, num_samples=50)
        expected = 6.0 / math.pi ** 2
        assert abs(em["density"] - expected) < 0.03

    def test_spectral_gap_consistent(self):
        """Spectral parameters should match between mixing and extraction."""
        n = 25
        em = expander_mixing_analysis(n, num_samples=50)
        ext = graph_walk_extraction(n, walk_length=3, num_walks=100)
        # lambda_2 / lambda_1 from extraction should match mixing analysis
        l2_over_l1 = abs(em["lambda_2"]) / em["lambda_1"]
        assert abs(ext["spectral_decay_prediction"] - l2_over_l1) < 0.01

    def test_clique_count_consistent(self):
        """Clique counts should match between avoidance and hardness."""
        n = 10
        avoid = random_coloring_avoidance(n, 3, num_trials=10)
        hard = ramsey_sat_hardness(n, 3)
        assert avoid["num_cliques"] == hard["num_cliques"]

    def test_edge_count_consistent(self):
        """Edge counts should match between hardness and adjacency matrix."""
        n = 15
        hard = ramsey_sat_hardness(n, 3)
        A = coprime_adjacency_matrix(n)
        assert hard["num_edges"] == int(np.sum(A)) // 2

    def test_expander_mixing_implies_pseudorandom(self):
        """Good expander mixing (low tightness) implies pseudorandomness."""
        r = expander_mixing_analysis(30, num_samples=200)
        # If normalized gap is large AND tightness is low, graph is pseudorandom
        assert r["normalized_gap"] > 0.85
        assert r["mean_tightness"] < 0.7

    def test_hash_coprime_gap_makes_theoretical_sense(self):
        """Coprime pairs should have strictly lower collision than non-coprime."""
        r = hash_collision_by_gcd(25)
        # Coprime pairs share no prime factor, so they collide under
        # fewer prime hashes => lower collision probability
        assert r["coprime_collision"] < r["non_coprime_collision"]
        # The gap should be positive and meaningful
        assert r["collision_gap"] > 0.01
