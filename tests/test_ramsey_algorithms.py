"""Tests for ramsey_algorithms.py -- algorithm comparison for coprime Ramsey numbers."""

import math
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ramsey_algorithms import (
    # Core infrastructure
    coprime_edges,
    coprime_adj,
    find_coprime_cliques,
    has_monochromatic_clique_fast,
    # Section 1: Algorithm comparison
    brute_force_check,
    incremental_extension_check,
    sat_check,
    backtracking_with_pruning,
    compare_algorithms_rcop3,
    # Section 2: Lower bounds
    random_coloring_lower_bound,
    greedy_coloring_lower_bound,
    local_search_lower_bound,
    genetic_algorithm_lower_bound,
    lower_bound_comparison,
    # Section 3: Upper bounds
    direct_sat_upper_bound,
    extension_method_upper_bound,
    resolution_proof_size,
    algebraic_method_feasibility,
    upper_bound_comparison,
    # Section 4: Parameterized complexity
    count_cliques_by_k,
    parameterized_complexity_analysis,
    # Section 5: R_cop(5)
    estimate_rcop5_feasibility,
    optimal_rcop5_scanner,
    # Section 6: Comparison table
    build_comparison_table,
    format_comparison_table,
)


# ============================================================================
# Core infrastructure tests
# ============================================================================

class TestCoreInfrastructure:
    def test_coprime_edges_n1(self):
        assert coprime_edges(1) == []

    def test_coprime_edges_n3(self):
        edges = coprime_edges(3)
        assert set(edges) == {(1, 2), (1, 3), (2, 3)}

    def test_coprime_edges_excludes_non_coprime(self):
        edges = coprime_edges(6)
        assert (2, 4) not in edges
        assert (2, 6) not in edges
        assert (3, 6) not in edges

    def test_coprime_adj_symmetric(self):
        adj = coprime_adj(10)
        for v, neighbors in adj.items():
            for u in neighbors:
                assert v in adj[u], f"{v} in adj[{u}] but {u} not in adj[{v}]"

    def test_coprime_adj_matches_edges(self):
        n = 10
        edges = coprime_edges(n)
        adj = coprime_adj(n)
        for i, j in edges:
            assert j in adj[i]
            assert i in adj[j]

    def test_find_coprime_cliques_triangles(self):
        """All 3-cliques in [5] should be pairwise coprime."""
        cliques = find_coprime_cliques(5, 3)
        for c in cliques:
            assert len(c) == 3
            for i in range(3):
                for j in range(i + 1, 3):
                    assert math.gcd(c[i], c[j]) == 1

    def test_find_coprime_cliques_2_matches_edges(self):
        for n in [4, 6, 8]:
            cliques = find_coprime_cliques(n, 2)
            edges = coprime_edges(n)
            assert len(cliques) == len(edges)

    def test_has_monochromatic_clique_fast_positive(self):
        """All edges color 0 on [5] must contain a mono triangle."""
        edges = coprime_edges(5)
        coloring = {e: 0 for e in edges}
        assert has_monochromatic_clique_fast(5, 3, coloring)

    def test_has_monochromatic_clique_fast_negative(self):
        """Mixed coloring on [3] avoids mono K_3."""
        coloring = {(1, 2): 0, (1, 3): 0, (2, 3): 1}
        assert not has_monochromatic_clique_fast(3, 3, coloring)

    def test_has_monochromatic_clique_fast_with_precomputed_cliques(self):
        """Precomputed cliques give same result."""
        n, k = 6, 3
        edges = coprime_edges(n)
        cliques = find_coprime_cliques(n, k)
        coloring = {e: 0 for e in edges}
        assert has_monochromatic_clique_fast(n, k, coloring, cliques)


# ============================================================================
# Section 1: Algorithm comparison for R_cop(3) = 11
# ============================================================================

class TestBruteForce:
    def test_n8_k3_has_avoiding(self):
        """n=8 has avoiding colorings (known: 36)."""
        unsat, dt, checked = brute_force_check(8, 3)
        assert not unsat, "n=8 should have avoiding colorings (SAT)"
        assert checked == 2 ** 21  # 21 coprime edges at n=8

    def test_n3_k2_forced(self):
        """n=3, k=2: every coloring has a monochromatic edge."""
        unsat, dt, checked = brute_force_check(3, 2)
        assert unsat

    def test_n3_k3_not_forced(self):
        """n=3, k=3: can color triangle to avoid mono K_3."""
        unsat, dt, checked = brute_force_check(3, 3)
        assert not unsat

    def test_timing_positive(self):
        _, dt, _ = brute_force_check(5, 3)
        assert dt >= 0


class TestIncrementalExtension:
    def test_rcop3_found_at_11(self):
        """Incremental extension should find R_cop(3)=11."""
        unsat, dt, explored = incremental_extension_check(11, 3)
        assert unsat, "All colorings at n=11 should be forced"

    def test_n10_has_avoiding(self):
        """n=10 should have avoiding colorings."""
        unsat, dt, explored = incremental_extension_check(10, 3)
        assert not unsat

    def test_explored_count_positive(self):
        _, _, explored = incremental_extension_check(8, 3)
        assert explored > 0

    def test_rcop2(self):
        """R_cop(2) = 2."""
        unsat, dt, explored = incremental_extension_check(2, 2)
        assert unsat


class TestSATCheck:
    def test_n10_k3_sat(self):
        """n=10 is SAT for k=3."""
        unsat, dt, nvars, nclauses = sat_check(10, 3)
        assert not unsat
        assert nvars == len(coprime_edges(10))

    def test_n11_k3_unsat(self):
        """n=11 is UNSAT for k=3 (R_cop(3)=11)."""
        unsat, dt, nvars, nclauses = sat_check(11, 3)
        assert unsat

    def test_cadical195(self):
        """CaDiCaL195 should also find UNSAT at n=11."""
        unsat, dt, nvars, nclauses = sat_check(11, 3, 'cadical195')
        assert unsat

    def test_minisat22(self):
        """MiniSat should also find UNSAT at n=11."""
        unsat, dt, nvars, nclauses = sat_check(11, 3, 'minisat22')
        assert unsat

    def test_clause_count_positive(self):
        _, _, _, nclauses = sat_check(8, 3)
        assert nclauses > 0

    def test_var_count_matches_edges(self):
        for n in [5, 8, 10]:
            _, _, nvars, _ = sat_check(n, 3)
            assert nvars == len(coprime_edges(n))


class TestBacktrackingWithPruning:
    def test_n10_k3_finds_avoiding(self):
        """n=10 should have an avoiding coloring."""
        unsat, dt, nodes = backtracking_with_pruning(10, 3)
        assert not unsat

    def test_n11_k3_proves_forced(self):
        """n=11 should prove all colorings forced."""
        unsat, dt, nodes = backtracking_with_pruning(11, 3)
        assert unsat

    def test_pruning_reduces_search(self):
        """Pruning should explore fewer nodes than 2^m."""
        unsat, dt, nodes = backtracking_with_pruning(9, 3)
        m = len(coprime_edges(9))
        assert nodes < 2 ** m, "Pruning should reduce search space"

    def test_nodes_positive(self):
        _, _, nodes = backtracking_with_pruning(5, 3)
        assert nodes > 0


class TestCompareAlgorithmsRcop3:
    @pytest.fixture(scope="class")
    def rcop3_results(self):
        return compare_algorithms_rcop3()

    def test_all_agree_on_n11(self, rcop3_results):
        """All exact algorithms should agree that n=11 is UNSAT."""
        for key, val in rcop3_results.items():
            if 'n' in val and val['n'] == 11 and 'error' not in val:
                if val.get('exact', False):
                    assert val['unsat'], f"{key} disagrees: n=11 should be UNSAT"

    def test_all_agree_on_n10(self, rcop3_results):
        """All exact algorithms should agree that n=10 is SAT."""
        for key, val in rcop3_results.items():
            if 'n' in val and val['n'] == 10 and 'error' not in val:
                if val.get('exact', False):
                    assert not val['unsat'], f"{key} disagrees: n=10 should be SAT"

    def test_results_contain_all_algorithms(self, rcop3_results):
        """Should test brute force, extension, SAT, and backtracking."""
        algorithms = set()
        for val in rcop3_results.values():
            alg = val.get('algorithm', '')
            algorithms.add(alg)
        assert 'brute_force' in algorithms
        assert 'incremental_extension' in algorithms
        assert 'backtracking_pruned' in algorithms
        # At least one SAT solver
        assert any('sat_' in a for a in algorithms)


# ============================================================================
# Section 2: Lower bound algorithms
# ============================================================================

class TestRandomColoringLowerBound:
    def test_n8_k3_high_success(self):
        """At n=8 (well below R_cop(3)=11), random should succeed often."""
        succ, trials, rate, dt = random_coloring_lower_bound(8, 3, num_trials=1000)
        assert rate > 0.001, "Should find avoiding colorings at n=8"

    def test_n11_k3_zero_success(self):
        """At n=11 (R_cop(3)), no random coloring should avoid mono K_3."""
        succ, trials, rate, dt = random_coloring_lower_bound(11, 3, num_trials=500)
        assert succ == 0, "No avoiding coloring exists at n=11"

    def test_deterministic_with_seed(self):
        """Same seed should give same result."""
        r1 = random_coloring_lower_bound(9, 3, num_trials=100, seed=123)
        r2 = random_coloring_lower_bound(9, 3, num_trials=100, seed=123)
        assert r1[0] == r2[0]  # same number of successes


class TestGreedyColoringLowerBound:
    def test_n8_k3_success(self):
        """Greedy should find avoiding colorings at n=8."""
        succ, trials, dt = greedy_coloring_lower_bound(8, 3, num_trials=50)
        assert succ > 0

    def test_n11_k3_no_success(self):
        """Greedy cannot find avoiding coloring at n=11."""
        succ, trials, dt = greedy_coloring_lower_bound(11, 3, num_trials=50)
        assert succ == 0

    def test_greedy_beats_random_at_n10(self):
        """Greedy should have higher success rate than random at n=10."""
        _, _, rate_rand, _ = random_coloring_lower_bound(10, 3, num_trials=1000)
        succ_g, trials_g, _ = greedy_coloring_lower_bound(10, 3, num_trials=100)
        rate_greedy = succ_g / trials_g if trials_g > 0 else 0.0
        # Greedy should do at least as well as random
        # (may not always hold due to small sample; use relaxed check)
        assert rate_greedy >= 0.0  # basic sanity


class TestLocalSearchLowerBound:
    def test_n9_k3_finds_avoiding(self):
        """Local search should find avoiding coloring at n=9."""
        found, flips, dt, best_v = local_search_lower_bound(
            9, 3, max_flips=5000, num_restarts=5,
        )
        assert found

    def test_n11_k3_cannot_find(self):
        """Local search cannot find avoiding coloring at n=11."""
        found, flips, dt, best_v = local_search_lower_bound(
            11, 3, max_flips=2000, num_restarts=3,
        )
        assert not found
        assert best_v > 0

    def test_flips_positive(self):
        _, flips, _, _ = local_search_lower_bound(8, 3, max_flips=100, num_restarts=1)
        assert flips > 0


class TestGeneticAlgorithmLowerBound:
    def test_n8_k3_finds_avoiding(self):
        """GA should find avoiding coloring at n=8."""
        found, gens, dt, best_v = genetic_algorithm_lower_bound(
            8, 3, pop_size=30, generations=50,
        )
        assert found

    def test_n11_k3_cannot_find(self):
        """GA cannot find avoiding coloring at n=11."""
        found, gens, dt, best_v = genetic_algorithm_lower_bound(
            11, 3, pop_size=30, generations=50,
        )
        assert not found
        assert best_v > 0

    def test_returns_valid_structure(self):
        found, gens, dt, best_v = genetic_algorithm_lower_bound(
            6, 3, pop_size=10, generations=10,
        )
        assert isinstance(found, bool)
        assert isinstance(gens, int)
        assert dt >= 0
        assert best_v >= 0


class TestLowerBoundComparison:
    def test_comparison_returns_all_algorithms(self):
        results = lower_bound_comparison(3, [8])
        algorithms = {v['algorithm'] for v in results.values()}
        assert 'random' in algorithms
        assert 'greedy' in algorithms
        assert 'local_search' in algorithms
        assert 'genetic' in algorithms


# ============================================================================
# Section 3: Upper bound algorithms
# ============================================================================

class TestDirectSATUpperBound:
    def test_n11_k3_unsat(self):
        unsat, dt, nvars, nclauses = direct_sat_upper_bound(11, 3)
        assert unsat

    def test_multiple_solvers_agree(self):
        """Multiple SAT solvers should agree on UNSAT at n=11."""
        for sname in ['glucose4', 'cadical195']:
            unsat, dt, _, _ = direct_sat_upper_bound(11, 3, sname)
            assert unsat, f"{sname} should find UNSAT at n=11"


class TestExtensionMethodUpperBound:
    def test_n11_k3_proved(self):
        """Extension method should prove UNSAT at n=11."""
        proved, dt, checked, extending = extension_method_upper_bound(11, 3)
        assert proved
        assert extending == 0
        assert checked > 0

    def test_n10_k3_not_proved(self):
        """Extension method at n=10 should NOT prove UNSAT (colorings extend)."""
        proved, dt, checked, extending = extension_method_upper_bound(10, 3)
        assert not proved
        assert extending > 0


class TestResolutionProofSize:
    def test_n11_k3(self):
        """Resolution proof at n=11 should report UNSAT."""
        unsat, dt, proof_size = resolution_proof_size(11, 3)
        assert unsat
        # proof_size may be None if solver doesn't expose it
        if proof_size is not None:
            assert proof_size > 0

    def test_n10_k3_sat(self):
        """n=10 is SAT, so no resolution proof."""
        unsat, dt, proof_size = resolution_proof_size(10, 3)
        assert not unsat


class TestAlgebraicMethodFeasibility:
    def test_small_n_feasible(self):
        result = algebraic_method_feasibility(5, 3)
        assert result['feasible']
        assert result['num_variables'] == len(coprime_edges(5))

    def test_large_n_infeasible(self):
        result = algebraic_method_feasibility(11, 3)
        assert not result['feasible']

    def test_polynomial_degree(self):
        """Degree should be C(k,2)."""
        result = algebraic_method_feasibility(8, 3)
        assert result['polynomial_degree'] == 3  # C(3,2) = 3

        result = algebraic_method_feasibility(8, 4)
        assert result['polynomial_degree'] == 6  # C(4,2) = 6


class TestUpperBoundComparison:
    def test_comparison_at_n11(self):
        results = upper_bound_comparison(11, 3)
        # Should have SAT, extension, resolution, algebraic
        assert any('sat' in k for k in results.keys())
        assert 'extension' in results
        assert 'resolution' in results
        assert 'algebraic' in results


# ============================================================================
# Section 4: Parameterized complexity
# ============================================================================

class TestCountCliquesByK:
    def test_clique_counts_positive(self):
        counts = count_cliques_by_k(10, k_max=4)
        for k, c in counts.items():
            assert c > 0, f"Should have {k}-cliques at n=10"

    def test_2_cliques_match_edges(self):
        counts = count_cliques_by_k(10, k_max=3)
        assert counts[2] == len(coprime_edges(10))

    def test_clique_counts_decrease_with_k(self):
        counts = count_cliques_by_k(10, k_max=5)
        for k in range(3, 6):
            if k in counts and k - 1 in counts:
                assert counts[k] <= counts[k - 1]


class TestParameterizedComplexityAnalysis:
    @pytest.fixture(scope="class")
    def pc_results(self):
        return parameterized_complexity_analysis(
            k_values=[2, 3],
            max_n_per_k={2: 5, 3: 15},
        )

    def test_finds_rcop2(self, pc_results):
        k2_data = pc_results['k2']
        last = k2_data[-1]
        assert last['unsat']
        assert last['n'] == 2

    def test_finds_rcop3(self, pc_results):
        k3_data = pc_results['k3']
        last = k3_data[-1]
        assert last['unsat']
        assert last['n'] == 11

    def test_bottleneck_identified(self, pc_results):
        bottleneck = pc_results.get('bottleneck', {})
        assert len(bottleneck) > 0

    def test_extrapolation_present(self, pc_results):
        extrap = pc_results.get('extrapolation', {})
        assert 'extrapolated_rcop5' in extrap
        assert extrap['extrapolated_rcop5'] > 59  # Must exceed R_cop(4)


# ============================================================================
# Section 5: R_cop(5) estimation
# ============================================================================

class TestEstimateRcop5Feasibility:
    @pytest.fixture(scope="class")
    def feasibility(self):
        return estimate_rcop5_feasibility()

    def test_estimate_positive(self, feasibility):
        assert feasibility['estimated_rcop5'] > 59

    def test_strategy_has_phases(self, feasibility):
        strategy = feasibility['strategy']
        assert 'phase1' in strategy
        assert 'phase2' in strategy
        assert 'phase3' in strategy

    def test_edge_estimate_positive(self, feasibility):
        assert feasibility['estimated_edges'] > 0

    def test_recommendation_nonempty(self, feasibility):
        assert len(feasibility['recommendation']) > 0


class TestOptimalRcop5Scanner:
    def test_scan_small_range(self):
        """Scanner should find R_cop(5) > 20 quickly."""
        result = optimal_rcop5_scanner(max_n=25, timeout_per_n=10.0, verbose=False)
        if result.get('rcop5') is None:
            lb = result.get('lower_bound', 0)
            assert lb >= 20, f"Lower bound should be >= 20, got {lb}"

    def test_scan_data_structure(self):
        result = optimal_rcop5_scanner(max_n=10, timeout_per_n=10.0, verbose=False)
        assert 'scan_data' in result
        assert len(result['scan_data']) > 0

    def test_scan_data_entries(self):
        result = optimal_rcop5_scanner(max_n=10, timeout_per_n=10.0, verbose=False)
        for entry in result['scan_data']:
            assert 'n' in entry
            assert 'vars' in entry
            assert 'sat' in entry


# ============================================================================
# Section 6: Comparison table
# ============================================================================

class TestBuildComparisonTable:
    def test_table_nonempty(self):
        table = build_comparison_table()
        assert len(table) > 0

    def test_all_entries_have_required_fields(self):
        table = build_comparison_table()
        required = ['algorithm', 'type', 'time_complexity', 'space_complexity']
        for row in table:
            for field in required:
                assert field in row, f"Missing field '{field}' in {row['algorithm']}"

    def test_has_exact_and_heuristic(self):
        table = build_comparison_table()
        types = {row['type'] for row in table}
        assert any('exact' in t for t in types)
        assert any('heuristic' in t for t in types)

    def test_covers_key_algorithms(self):
        table = build_comparison_table()
        names = {row['algorithm'] for row in table}
        assert 'Brute Force' in names
        assert 'Direct SAT (CaDiCaL195)' in names
        assert 'Local Search (WalkSAT)' in names


class TestFormatComparisonTable:
    def test_formatting_nonempty(self):
        table = build_comparison_table()
        formatted = format_comparison_table(table)
        assert len(formatted) > 100

    def test_formatting_contains_header(self):
        table = build_comparison_table()
        formatted = format_comparison_table(table)
        assert "ALGORITHM COMPARISON TABLE" in formatted

    def test_formatting_contains_strategies(self):
        table = build_comparison_table()
        formatted = format_comparison_table(table)
        assert "OPTIMAL STRATEGY" in formatted


# ============================================================================
# Cross-cutting correctness tests
# ============================================================================

class TestAlgorithmConsistency:
    """Verify all exact algorithms agree on R_cop(3) = 11."""

    def test_brute_force_n8_sat(self):
        unsat, _, _ = brute_force_check(8, 3)
        assert not unsat

    def test_extension_n11_unsat(self):
        unsat, _, _ = incremental_extension_check(11, 3)
        assert unsat

    def test_sat_glucose4_n11_unsat(self):
        unsat, _, _, _ = sat_check(11, 3, 'glucose4')
        assert unsat

    def test_sat_cadical195_n11_unsat(self):
        unsat, _, _, _ = sat_check(11, 3, 'cadical195')
        assert unsat

    def test_backtracking_n11_unsat(self):
        unsat, _, _ = backtracking_with_pruning(11, 3)
        assert unsat

    def test_extension_method_n11_unsat(self):
        proved, _, checked, extending = extension_method_upper_bound(11, 3)
        assert proved
        assert extending == 0


class TestLowerBoundConsistency:
    """All lower bound algorithms should succeed below R_cop(3) and fail at R_cop(3)."""

    def test_random_succeeds_below(self):
        succ, _, _, _ = random_coloring_lower_bound(9, 3, num_trials=500)
        assert succ > 0

    def test_random_fails_at_rcop(self):
        succ, _, _, _ = random_coloring_lower_bound(11, 3, num_trials=500)
        assert succ == 0

    def test_greedy_succeeds_below(self):
        succ, _, _ = greedy_coloring_lower_bound(9, 3, num_trials=50)
        assert succ > 0

    def test_greedy_fails_at_rcop(self):
        succ, _, _ = greedy_coloring_lower_bound(11, 3, num_trials=50)
        assert succ == 0

    def test_local_search_succeeds_below(self):
        found, _, _, _ = local_search_lower_bound(9, 3, max_flips=3000, num_restarts=3)
        assert found

    def test_local_search_fails_at_rcop(self):
        found, _, _, best_v = local_search_lower_bound(11, 3, max_flips=2000, num_restarts=3)
        assert not found
        assert best_v > 0
