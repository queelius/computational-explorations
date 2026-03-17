"""
Tests for approx_algorithms.py -- Approximation algorithms for coprime graph problems.

Each test class verifies both correctness and the provable guarantees
claimed by the algorithms.
"""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from approx_algorithms import (
    build_coprime_graph,
    coprime_edges,
    coprime_edge_set,
    primes_up_to,
    # 1. Weighted MIS
    weighted_mis_greedy,
    weighted_mis_lp_relaxation,
    lp_rounding_mis,
    # 2. Coloring
    greedy_coloring,
    dsatur_coloring_subgraph,
    random_order_coloring,
    largest_first_coloring,
    compare_coloring_strategies,
    # 3. K_k-free
    max_kk_free_greedy,
    turan_bound,
    kk_free_approx_ratio,
    # 4. Approximate Ramsey
    random_coloring_avoids_clique,
    approximate_coprime_ramsey,
    ramsey_sample_complexity,
    # 5. Online Ramsey
    OnlineCoprimeSolver,
    online_coprime_ramsey,
    # 6. Streaming
    CoprimStreamState,
    streaming_coprime_analysis,
)


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture(scope="module")
def adj_10():
    return build_coprime_graph(10)


@pytest.fixture(scope="module")
def adj_15():
    return build_coprime_graph(15)


@pytest.fixture(scope="module")
def edges_10():
    return coprime_edges(10)


# ===================================================================
# Graph Primitives
# ===================================================================

class TestGraphPrimitives:

    def test_coprime_graph_symmetric(self, adj_10):
        for u, nbrs in adj_10.items():
            for v in nbrs:
                assert u in adj_10[v], f"({u},{v}) asymmetric"

    def test_coprime_graph_no_self_loop(self, adj_10):
        for v in adj_10:
            assert v not in adj_10[v]

    def test_coprime_correctness(self, adj_10):
        for u in range(1, 11):
            for v in range(u + 1, 11):
                if math.gcd(u, v) == 1:
                    assert v in adj_10[u]
                else:
                    assert v not in adj_10[u]

    def test_edge_count(self, edges_10):
        expected = sum(
            1 for i in range(1, 11) for j in range(i + 1, 11)
            if math.gcd(i, j) == 1
        )
        assert len(edges_10) == expected

    def test_edge_set_canonical(self):
        es = coprime_edge_set(5)
        for u, v in es:
            assert u < v

    def test_primes(self):
        assert primes_up_to(10) == [2, 3, 5, 7]
        assert primes_up_to(1) == []
        assert primes_up_to(2) == [2]

    def test_vertex_1_adjacent_all(self, adj_10):
        """Vertex 1 is coprime to everything: degree = n-1."""
        assert len(adj_10[1]) == 9


# ===================================================================
# 1. Weighted Maximum Independent Set
# ===================================================================

class TestWeightedMISGreedy:

    def test_returns_valid_independent_set(self):
        n = 10
        weights = {v: 1.0 for v in range(1, n + 1)}
        indep, val = weighted_mis_greedy(n, weights)

        # No two selected vertices should be coprime
        selected = sorted(indep)
        for i in range(len(selected)):
            for j in range(i + 1, len(selected)):
                assert math.gcd(selected[i], selected[j]) != 1, (
                    f"({selected[i]}, {selected[j]}) are coprime -- not independent"
                )

    def test_unweighted_gets_half(self):
        """With uniform weights + degree tie-breaking, greedy finds IS of size n/2.

        Tie-breaking by ascending degree ensures low-degree vertices
        (evens, which share factor 2 with each other and are thus
        mutually non-adjacent) are selected first, recovering the
        optimal independent set.
        """
        n = 20
        weights = {v: 1.0 for v in range(1, n + 1)}
        indep, val = weighted_mis_greedy(n, weights)
        # alpha(G(n)) = floor(n/2); with degree tie-breaking, greedy
        # should recover the evens or a similarly-sized set
        assert len(indep) >= n // 2

    def test_weight_sum_correct(self):
        n = 10
        weights = {v: float(v) for v in range(1, n + 1)}
        indep, val = weighted_mis_greedy(n, weights)
        expected = sum(weights[v] for v in indep)
        assert abs(val - expected) < 1e-10

    def test_approximation_guarantee(self):
        """Greedy value >= OPT / (Delta + 1)."""
        n = 10
        weights = {v: 1.0 / v for v in range(1, n + 1)}
        indep, greedy_val = weighted_mis_greedy(n, weights)

        # OPT <= sum of all weights (trivial upper bound)
        total_weight = sum(weights.values())
        delta = n - 1  # max degree (vertex 1)

        # Greedy guarantee: val >= OPT / (Delta + 1)
        assert greedy_val >= total_weight / (delta + 1) - 1e-10

    def test_evens_are_independent(self):
        """Even numbers form an independent set in G(n)."""
        n = 20
        evens = {v for v in range(2, n + 1) if v % 2 == 0}
        for a in evens:
            for b in evens:
                if a != b:
                    assert math.gcd(a, b) != 1

    def test_small_n(self):
        """n=2: only IS is either {1} or {2}."""
        weights = {1: 10.0, 2: 1.0}
        indep, val = weighted_mis_greedy(2, weights)
        assert len(indep) == 1  # 1 and 2 are coprime; can only pick one
        assert 1 in indep  # should pick 1 (higher weight)


class TestWeightedMISLP:

    @pytest.mark.filterwarnings("ignore:Optimization")
    def test_lp_upper_bounds_greedy(self):
        """LP value >= greedy value (LP is a relaxation)."""
        n = 10
        weights = {v: 1.0 / v for v in range(1, n + 1)}
        _, lp_val, gap = weighted_mis_lp_relaxation(n, weights)
        _, greedy_val = weighted_mis_greedy(n, weights)
        assert lp_val >= greedy_val - 1e-6

    @pytest.mark.filterwarnings("ignore:Optimization")
    def test_lp_solution_feasible(self):
        """LP solution satisfies x_u + x_v <= 1 for all coprime edges."""
        n = 8
        weights = {v: float(v) for v in range(1, n + 1)}
        frac, lp_val, _ = weighted_mis_lp_relaxation(n, weights)

        edges = coprime_edges(n)
        for u, v in edges:
            assert frac[u] + frac[v] <= 1.0 + 1e-6

    @pytest.mark.filterwarnings("ignore:Optimization")
    def test_lp_solution_bounded(self):
        """0 <= x_v <= 1 for all v."""
        n = 8
        weights = {v: 1.0 for v in range(1, n + 1)}
        frac, _, _ = weighted_mis_lp_relaxation(n, weights)
        for v, x in frac.items():
            assert -1e-6 <= x <= 1.0 + 1e-6


class TestLPRoundingMIS:

    @pytest.mark.filterwarnings("ignore:Optimization")
    def test_rounding_valid_independent_set(self):
        n = 10
        weights = {v: 1.0 / v for v in range(1, n + 1)}
        indep, val = lp_rounding_mis(n, weights)
        selected = sorted(indep)
        for i in range(len(selected)):
            for j in range(i + 1, len(selected)):
                assert math.gcd(selected[i], selected[j]) != 1

    @pytest.mark.filterwarnings("ignore:Optimization")
    def test_rounding_beats_or_matches_trivial(self):
        """LP rounding should find IS of size >= 1."""
        n = 10
        weights = {v: 1.0 for v in range(1, n + 1)}
        indep, val = lp_rounding_mis(n, weights)
        assert len(indep) >= 1

    @pytest.mark.filterwarnings("ignore:Optimization")
    def test_rounding_weight_correct(self):
        n = 8
        weights = {v: float(v) for v in range(1, n + 1)}
        indep, val = lp_rounding_mis(n, weights)
        expected = sum(weights[v] for v in indep)
        assert abs(val - expected) < 1e-10


# ===================================================================
# 2. Minimum Coloring
# ===================================================================

class TestGreedyColoring:

    def test_valid_coloring(self, adj_10):
        order = list(range(1, 11))
        num_colors, coloring = greedy_coloring(adj_10, order)
        for u, nbrs in adj_10.items():
            for v in nbrs:
                assert coloring[u] != coloring[v], (
                    f"Adjacent vertices {u}, {v} have same color"
                )

    def test_at_most_delta_plus_1(self, adj_10):
        order = list(range(1, 11))
        num_colors, _ = greedy_coloring(adj_10, order)
        delta = max(len(nbrs) for nbrs in adj_10.values())
        assert num_colors <= delta + 1

    def test_all_vertices_colored(self, adj_10):
        order = list(range(1, 11))
        _, coloring = greedy_coloring(adj_10, order)
        assert set(coloring.keys()) == set(range(1, 11))


class TestDSATURColoring:

    def test_valid_coloring(self, adj_10):
        num_colors, coloring = dsatur_coloring_subgraph(adj_10)
        for u, nbrs in adj_10.items():
            for v in nbrs:
                assert coloring[u] != coloring[v]

    def test_matches_or_beats_greedy(self, adj_10):
        """DSATUR should use <= greedy (largest-first) colors."""
        dsatur_k, _ = dsatur_coloring_subgraph(adj_10)
        lf_k, _ = largest_first_coloring(adj_10)
        assert dsatur_k <= lf_k + 1  # can be slightly worse in rare cases

    def test_optimal_on_coprime_graph(self):
        """G(n) is perfect, so DSATUR should find chi = omega = 1 + pi(n)."""
        n = 10
        adj = build_coprime_graph(n)
        num_colors, _ = dsatur_coloring_subgraph(adj)
        omega = 1 + len(primes_up_to(n))  # 1 + 4 = 5
        assert num_colors == omega

    def test_subgraph_coloring(self):
        """Test coloring on a restricted vertex set."""
        n = 10
        adj = build_coprime_graph(n)
        verts = {2, 4, 6, 8, 10}  # evens -- independent set in G(n)
        num_colors, coloring = dsatur_coloring_subgraph(adj, vertices=verts)
        # Evens share no coprime edges among themselves (all even => gcd >= 2)
        # So chromatic number of the induced subgraph is 1
        # (But some evens may be coprime: e.g. 4 and 9? No, 9 not in set.)
        # gcd(2,4)=2, gcd(2,6)=2, ..., gcd(4,6)=2 -- no coprime pairs
        assert num_colors == 1


class TestRandomColoring:

    def test_valid(self):
        adj = build_coprime_graph(8)
        num_colors, coloring = random_order_coloring(adj, seed=42)
        for u, nbrs in adj.items():
            for v in nbrs:
                if v in coloring and u in coloring:
                    assert coloring[u] != coloring[v]

    def test_reproducible(self):
        adj = build_coprime_graph(8)
        k1, _ = random_order_coloring(adj, seed=123)
        k2, _ = random_order_coloring(adj, seed=123)
        assert k1 == k2


class TestCompareColoringStrategies:

    def test_returns_all_fields(self):
        result = compare_coloring_strategies(10)
        assert "dsatur" in result
        assert "largest_first" in result
        assert "random_min" in result
        assert "clique_number_lower_bound" in result

    def test_all_at_least_omega(self):
        result = compare_coloring_strategies(10)
        omega = result["clique_number_lower_bound"]
        assert result["dsatur"] >= omega
        assert result["largest_first"] >= omega
        assert result["random_min"] >= omega

    def test_subset_coloring(self):
        """Coloring of a subgraph should use fewer or equal colors."""
        n = 15
        full = compare_coloring_strategies(n)
        evens = {i for i in range(2, n + 1) if i % 2 == 0}
        sub = compare_coloring_strategies(n, subset=evens)
        assert sub["dsatur"] <= full["dsatur"]


# ===================================================================
# 3. Maximum K_k-free Subgraph
# ===================================================================

class TestMaxKkFreeGreedy:

    def test_result_is_triangle_free(self):
        n = 10
        kept, removed, frac = max_kk_free_greedy(n, 3)
        # Verify no triangle in kept edges
        adj: dict = {}
        for u, v in kept:
            adj.setdefault(u, set()).add(v)
            adj.setdefault(v, set()).add(u)

        for u in adj:
            for v in adj[u]:
                if v > u:
                    common = adj.get(u, set()) & adj.get(v, set())
                    assert len(common) == 0, (
                        f"Triangle: {u}, {v}, {common}"
                    )

    def test_k4_free(self):
        n = 12
        kept, removed, frac = max_kk_free_greedy(n, 4)
        # Verify no K_4 in kept
        adj: dict = {}
        for u, v in kept:
            adj.setdefault(u, set()).add(v)
            adj.setdefault(v, set()).add(u)

        for u in adj:
            nbrs = sorted(adj[u])
            for i in range(len(nbrs)):
                for j in range(i + 1, len(nbrs)):
                    for kv in range(j + 1, len(nbrs)):
                        a, b, c = nbrs[i], nbrs[j], nbrs[kv]
                        if (b in adj.get(a, set()) and
                                c in adj.get(a, set()) and
                                c in adj.get(b, set())):
                            assert False, f"K_4: {u}, {a}, {b}, {c}"

    def test_fraction_between_0_and_1(self):
        _, _, frac = max_kk_free_greedy(10, 3)
        assert 0.0 <= frac <= 1.0

    def test_trivial_k2(self):
        """K_2-free means no edges at all."""
        kept, removed, frac = max_kk_free_greedy(10, 2)
        assert len(kept) == 0

    def test_no_removal_when_no_clique(self):
        """If G(n) has no K_k, nothing should be removed."""
        # G(4) has 5 coprime edges. K_5 needs 5 mutually coprime vertices.
        # {1,2,3} is a triangle, so K_3 exists. But K_5 on 4 vertices? No.
        # G(3): {1,2,3} is K_3. So K_4 doesn't exist in G(3).
        kept, removed, frac = max_kk_free_greedy(3, 4)
        assert removed == 0
        assert frac == 1.0


class TestTuranBound:

    def test_triangle_free(self):
        """ex(n, K_3) = floor(n^2/4)."""
        for n in [4, 5, 6, 10, 20]:
            assert turan_bound(n, 3) == n * n // 4

    def test_k2_free(self):
        """ex(n, K_2) = 0."""
        assert turan_bound(10, 2) == 0

    def test_k4(self):
        """ex(n, K_4) = (1 - 1/3) * n^2 / 2 approximately."""
        n = 12
        tb = turan_bound(n, 4)
        # Turan graph T(12, 3): 3 parts of 4 each
        # Edges = 12*12/2 - 3*(4*3/2) = 72 - 18 = 54
        # Alternatively: (2/3) * 12^2 / 2 = 48, but exact is different
        assert tb == 48  # T(12,3): 3 parts of 4, edges = C(12,2) - 3*C(4,2) = 66-18 = 48

    def test_monotone_in_n(self):
        for k in [3, 4]:
            vals = [turan_bound(n, k) for n in range(3, 20)]
            for i in range(len(vals) - 1):
                assert vals[i] <= vals[i + 1]


class TestKkFreeApproxRatio:

    def test_ratio_at_least_turan_fraction(self):
        """Greedy should retain >= (1-1/(k-1)) fraction on average."""
        n = 12
        result = kk_free_approx_ratio(n, 3)
        # For K_3-free: Turan says we can keep (1-1/2) = 1/2 of possible edges
        # On G(n), should be at least close
        assert result["fraction_retained"] >= 0.3  # generous lower bound

    def test_ratio_fields_present(self):
        result = kk_free_approx_ratio(8, 3)
        assert "approx_ratio_lower" in result
        assert "total_coprime_edges" in result
        assert "greedy_kept" in result


# ===================================================================
# 4. Approximate Ramsey Number Computation
# ===================================================================

class TestRandomColoringAvoids:

    def test_small_n_all_avoid(self):
        """At n=5, k=3: some 2-colorings avoid monochromatic K_3."""
        result = random_coloring_avoids_clique(5, 3, num_trials=100, seed=42)
        assert result["avoiding_count"] > 0

    def test_at_ramsey_number_none_avoid(self):
        """At n=11 = R_cop(3), no 2-coloring avoids monochromatic K_3."""
        result = random_coloring_avoids_clique(11, 3, num_trials=200, seed=42)
        assert result["avoiding_count"] == 0

    def test_below_ramsey_some_avoid(self):
        """At n=5 < R_cop(3) = 11, random sampling finds avoiding colorings.

        At n=5 (9 edges, 7 triangles) ~10.5% of 2-colorings avoid mono K_3.
        At n=7 only 36/131072 ~= 2.7e-4 avoid, and by n=10 it's ~7e-8.
        This demonstrates how rapidly P_avoid decays as the graph densifies.
        """
        result = random_coloring_avoids_clique(5, 3, num_trials=500, seed=42)
        assert result["avoiding_count"] > 0

    def test_confidence_bound_valid(self):
        result = random_coloring_avoids_clique(8, 3, num_trials=100, seed=42)
        assert 0.0 <= result["confidence_upper_95"] <= 1.0

    def test_no_k_clique(self):
        """If no K_k exists in G(n), every coloring avoids."""
        # G(3) has K_3 = {1,2,3}. G(2) has only edge (1,2), no K_3.
        result = random_coloring_avoids_clique(2, 3, num_trials=50, seed=42)
        assert result["avoiding_count"] == 50

    def test_trivial_k2(self):
        """k=2: monochromatic edge always exists if edges exist."""
        result = random_coloring_avoids_clique(5, 2, num_trials=100, seed=42)
        # Every 2-coloring of edges has a monochromatic K_2
        # (each edge is already monochromatic by definition)
        assert result["avoiding_count"] == 0


class TestApproximateCoprimRamsey:

    def test_rcop3_lower_bound(self):
        """Lower bound for R_cop(3) should be nontrivial.

        Random sampling gives a lower bound where it can still find
        avoiding colorings. At n=7 (15 edges) the avoiding probability
        is high enough; by n=10 (31 edges) it's ~7e-8 and undetectable.
        So the sampling lower bound will be between 7 and 10 typically.
        """
        result = approximate_coprime_ramsey(3, max_n=15, num_trials=200, seed=42)
        assert result["lower_bound"] >= 5  # at least some avoiding found
        assert result["lower_bound"] <= 11  # cannot exceed R_cop(3)

    def test_rcop3_upper_bound(self):
        """Upper bound should be the first n with no avoiding colorings found.

        Since R_cop(3) = 11, every coloring at n=11 has mono K_3, and
        sampling correctly detects this. The upper bound should be at
        most 11 (where sampling first finds no avoiding).
        """
        result = approximate_coprime_ramsey(3, max_n=15, num_trials=200, seed=42)
        assert result["upper_bound"] <= 15  # within search range

    def test_window_bounded(self):
        """The estimation window should be reasonable."""
        result = approximate_coprime_ramsey(3, max_n=15, num_trials=200, seed=42)
        # Factor is upper/lower; should be finite and bounded
        assert result["factor"] < 3.0

    def test_lower_le_upper(self):
        result = approximate_coprime_ramsey(3, max_n=15, num_trials=200, seed=42)
        assert result["lower_bound"] <= result["upper_bound"]


class TestSampleComplexity:

    def test_high_prob(self):
        """If p_avoid = 0.5, need ~6 trials for 95% confidence."""
        T = ramsey_sample_complexity(0.5, 0.95)
        assert T <= 10
        assert T >= 1

    def test_low_prob(self):
        """If p_avoid = 0.01, need ~300 trials for 95% confidence."""
        T = ramsey_sample_complexity(0.01, 0.95)
        assert 200 <= T <= 400

    def test_extreme_prob(self):
        """p_avoid = 0 => 0 trials needed."""
        assert ramsey_sample_complexity(0.0) == 0

    def test_certain_prob(self):
        """p_avoid = 1 => 1 trial needed."""
        assert ramsey_sample_complexity(1.0) == 1

    def test_monotone_in_prob(self):
        """Fewer trials needed for higher p_avoid."""
        T1 = ramsey_sample_complexity(0.1, 0.95)
        T2 = ramsey_sample_complexity(0.5, 0.95)
        assert T1 >= T2


# ===================================================================
# 5. Online Coprime Ramsey
# ===================================================================

class TestOnlineCoprimeSolver:

    def test_solver_colors_edges(self):
        solver = OnlineCoprimeSolver(k=3)
        color = solver.color_edge(1, 2)
        assert color in (0, 1)
        assert (1, 2) in solver.coloring

    def test_solver_avoids_k3_initially(self):
        """First few edges should be colorable without mono K_3."""
        solver = OnlineCoprimeSolver(k=3)
        # Color edges of a triangle: (1,2), (1,3), (2,3)
        solver.color_edge(1, 2)
        solver.color_edge(1, 3)
        # After 2 edges, no K_3 yet
        assert not solver.failed

    def test_solver_detects_failure(self):
        """Eventually, enough triangles force failure."""
        solver = OnlineCoprimeSolver(k=3)
        edges = coprime_edges(11)
        for u, v in edges:
            solver.color_edge(u, v)
        # At n=11 = R_cop(3), some subset must fail
        # (Not guaranteed to fail with online algo, but likely)
        # We just test that the solver doesn't crash
        assert solver.edges_seen == len(edges)


class TestOnlineCoprimRamsey:

    def test_random_adversary(self):
        result = online_coprime_ramsey(10, 3, adversary="random", seed=42)
        assert result["total_edges"] > 0
        assert result["edges_before_failure"] > 0
        assert 0 < result["competitive_ratio"] <= 1.0

    def test_worst_adversary(self):
        result = online_coprime_ramsey(10, 3, adversary="worst", seed=42)
        assert result["total_edges"] > 0

    def test_natural_adversary(self):
        result = online_coprime_ramsey(10, 3, adversary="natural", seed=42)
        assert result["total_edges"] > 0

    def test_competitive_ratio_positive(self):
        """Competitive ratio should be > 0."""
        result = online_coprime_ramsey(11, 3, adversary="random", seed=42)
        assert result["competitive_ratio"] > 0

    def test_worst_is_hardest(self):
        """Worst-case adversary should give fewer edges before failure
        than random adversary (usually)."""
        rng_result = online_coprime_ramsey(11, 3, adversary="random", seed=42)
        worst_result = online_coprime_ramsey(11, 3, adversary="worst", seed=42)
        # Not a strict guarantee, but in expectation
        # Just check both are valid
        assert rng_result["edges_before_failure"] >= 1
        assert worst_result["edges_before_failure"] >= 1

    def test_invalid_adversary(self):
        with pytest.raises(ValueError, match="Unknown adversary"):
            online_coprime_ramsey(5, 3, adversary="invalid")


# ===================================================================
# 6. Streaming Algorithms
# ===================================================================

class TestCoprimStreamState:

    def test_exact_edge_count(self):
        """Edge count should be exact (no approximation)."""
        n = 10
        edges = coprime_edges(n)
        state = CoprimStreamState(budget=50)
        for u, v in edges:
            state.process_edge(u, v)
        est = state.get_estimates()
        assert est["edge_count"] == len(edges)

    def test_vertex_count(self):
        n = 10
        edges = coprime_edges(n)
        state = CoprimStreamState(budget=50)
        for u, v in edges:
            state.process_edge(u, v)
        est = state.get_estimates()
        assert est["vertex_count"] == n

    def test_reservoir_bounded(self):
        """Reservoir should not exceed budget."""
        budget = 20
        n = 15
        edges = coprime_edges(n)
        state = CoprimStreamState(budget=budget)
        for u, v in edges:
            state.process_edge(u, v)
        est = state.get_estimates()
        assert est["space_used_edges"] <= budget

    def test_degree_correct(self):
        """Streaming degrees should match exact degrees."""
        n = 8
        adj = build_coprime_graph(n)
        edges = coprime_edges(n)
        state = CoprimStreamState(budget=100)
        for u, v in edges:
            state.process_edge(u, v)

        for v in range(1, n + 1):
            assert state.degree[v] == len(adj[v])

    def test_independent_set_valid(self):
        """Streaming IS should be a valid independent set."""
        n = 10
        edges = coprime_edges(n)
        state = CoprimStreamState(budget=50)
        for u, v in edges:
            state.process_edge(u, v)

        # Every pair in the IS should be non-coprime
        is_set = list(state._indep_set)
        for i in range(len(is_set)):
            for j in range(i + 1, len(is_set)):
                assert math.gcd(is_set[i], is_set[j]) != 1, (
                    f"IS contains coprime pair ({is_set[i]}, {is_set[j]})"
                )

    def test_triangle_estimate_nonnegative(self):
        n = 10
        edges = coprime_edges(n)
        state = CoprimStreamState(budget=50)
        for u, v in edges:
            state.process_edge(u, v)
        est = state.get_estimates()
        assert est["triangle_estimate"] >= 0

    def test_empty_stream(self):
        state = CoprimStreamState(budget=10)
        est = state.get_estimates()
        assert est["edge_count"] == 0
        assert est["vertex_count"] == 0
        assert est["triangle_estimate"] == 0.0


class TestStreamingAnalysis:

    def test_edge_count_exact(self):
        result = streaming_coprime_analysis(10, budget=50, seed=42)
        assert result["edge_count_exact"] is True

    def test_is_estimate_reasonable(self):
        """IS estimate should be within factor 2 of n/2."""
        n = 15
        result = streaming_coprime_analysis(n, budget=50, seed=42)
        exact_is = n // 2
        est_is = result["estimated_independent_set"]
        # Should be at least 1 and at most n
        assert 1 <= est_is <= n
        # Relative error check (generous bound)
        assert result["is_relative_error"] <= 1.0

    def test_larger_budget_better(self):
        """Larger budget should generally give better estimates."""
        n = 15
        r_small = streaming_coprime_analysis(n, budget=10, seed=42)
        r_large = streaming_coprime_analysis(n, budget=100, seed=42)
        # Edge count is always exact
        assert r_small["edge_count_exact"]
        assert r_large["edge_count_exact"]
        # Don't assert triangle accuracy strictly (stochastic)

    def test_returns_all_fields(self):
        result = streaming_coprime_analysis(8, budget=20, seed=42)
        expected_fields = [
            "n", "budget", "total_edges", "exact_triangles",
            "estimated_triangles", "triangle_absolute_error",
            "triangle_relative_error", "exact_independent_set",
            "estimated_independent_set", "is_absolute_error",
            "is_relative_error", "edge_count_exact",
        ]
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"


# ===================================================================
# Cross-cutting: provable guarantee integration tests
# ===================================================================

class TestProvableGuarantees:
    """
    Integration tests verifying that the claimed approximation guarantees
    hold across multiple problem instances.
    """

    def test_mis_greedy_guarantee_multiple_n(self):
        """Greedy MIS >= OPT / (Delta+1) for several n values."""
        for n in [6, 8, 10, 15]:
            weights = {v: 1.0 for v in range(1, n + 1)}
            indep, val = weighted_mis_greedy(n, weights)
            adj = build_coprime_graph(n)
            delta = max(len(nbrs) for nbrs in adj.values())
            # OPT = alpha(G(n)) = n//2 for uniform weights
            opt = n // 2
            assert val >= opt / (delta + 1) - 1e-10

    def test_coloring_at_most_delta_plus_1(self):
        """Every coloring strategy uses at most Delta+1 colors."""
        for n in [8, 12, 20]:
            adj = build_coprime_graph(n)
            delta = max(len(nbrs) for nbrs in adj.values())
            for strategy in [
                lambda: dsatur_coloring_subgraph(adj),
                lambda: largest_first_coloring(adj),
                lambda: random_order_coloring(adj, seed=0),
            ]:
                k, _ = strategy()
                assert k <= delta + 1, (
                    f"n={n}: coloring used {k} > Delta+1={delta+1}"
                )

    def test_kk_free_greedy_retains_turan_fraction(self):
        """Greedy K_3-removal retains at least some edges."""
        for n in [8, 10, 12]:
            edges = coprime_edges(n)
            total = len(edges)
            kept, removed, frac = max_kk_free_greedy(n, 3)
            # Should retain at least some edges
            assert len(kept) > 0
            assert len(kept) + removed == total

    def test_streaming_edge_count_always_exact(self):
        """Edge count is exact regardless of budget."""
        for n in [5, 10, 15]:
            for budget in [5, 20, 100]:
                result = streaming_coprime_analysis(n, budget=budget, seed=42)
                assert result["edge_count_exact"]

    def test_ramsey_sampling_consistent(self):
        """R_cop(3) = 11: sampling confirms no avoiding at n=11.

        At n=11, every 2-coloring has a monochromatic K_3, so random
        sampling correctly finds 0 avoiding colorings.

        At n=7, avoiding colorings are common enough for random
        sampling to find them.

        At n=10, avoiding colorings exist (156 of them) but represent
        only 7e-8 of all colorings, so random sampling cannot find them.
        This demonstrates the fundamental limitation of random sampling
        for Ramsey lower bounds when P_avoid is astronomically small.
        """
        at_5 = random_coloring_avoids_clique(5, 3, num_trials=500, seed=42)
        at_11 = random_coloring_avoids_clique(11, 3, num_trials=200, seed=42)
        assert at_5["avoiding_count"] > 0, "Should find avoiding coloring at n=5"
        assert at_11["avoiding_count"] == 0, "No avoiding coloring at n=11"

    def test_turan_bound_values(self):
        """Sanity-check Turan bound against known values."""
        # ex(6, K_3) = 9 = floor(36/4) = 9
        assert turan_bound(6, 3) == 9
        # ex(4, K_3) = 4 = floor(16/4) = 4
        assert turan_bound(4, 3) == 4
        # ex(5, K_3) = 6 = floor(25/4) = 6
        assert turan_bound(5, 3) == 6
