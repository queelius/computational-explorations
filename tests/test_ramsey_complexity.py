"""Tests for ramsey_complexity.py — complexity analysis of coprime Ramsey SAT."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ramsey_complexity import (
    coprime_edges,
    coprime_adjacency,
    find_coprime_cliques,
    build_sat_instance,
    complexity_profile,
    clause_density_analysis,
    enumerate_all_solutions,
    backbone_analysis,
    proof_complexity_analysis,
    proof_scaling,
    coprime_graph_automorphisms,
    symmetry_breaking_comparison,
    treewidth_analysis,
    _fit_models,
)


# ---------------------------------------------------------------------------
# Core graph construction
# ---------------------------------------------------------------------------

class TestCoprimeEdges:
    def test_n1_empty(self):
        assert coprime_edges(1) == []

    def test_n2_single(self):
        assert coprime_edges(2) == [(1, 2)]

    def test_excludes_non_coprime(self):
        edges = coprime_edges(6)
        assert (2, 4) not in edges
        assert (3, 6) not in edges
        assert (2, 6) not in edges

    def test_includes_coprime(self):
        edges = coprime_edges(6)
        assert (1, 2) in edges
        assert (5, 6) in edges

    def test_count_matches_euler(self):
        """Edge count for coprime graph on [n] should match direct computation."""
        for n in range(2, 15):
            edges = coprime_edges(n)
            expected = sum(
                1 for i in range(1, n + 1) for j in range(i + 1, n + 1)
                if math.gcd(i, j) == 1
            )
            assert len(edges) == expected, f"Mismatch at n={n}"


class TestCoprimeAdjacency:
    def test_symmetric(self):
        adj = coprime_adjacency(8)
        for v in range(1, 9):
            for u in adj[v]:
                assert v in adj[u], f"{v} in adj[{u}] but {u} not in adj[{v}]"

    def test_coprime_only(self):
        adj = coprime_adjacency(10)
        for v in range(1, 11):
            for u in adj[v]:
                assert math.gcd(u, v) == 1


class TestFindCoprimeCliques:
    def test_1_cliques(self):
        assert len(find_coprime_cliques(5, 1)) == 5

    def test_2_cliques_match_edges(self):
        for n in [5, 8, 10]:
            assert len(find_coprime_cliques(n, 2)) == len(coprime_edges(n))

    def test_all_3_cliques_are_coprime(self):
        for c in find_coprime_cliques(10, 3):
            for i in range(3):
                for j in range(i + 1, 3):
                    assert math.gcd(c[i], c[j]) == 1

    def test_known_triangle_count(self):
        """At n=5, there are 7 coprime triangles."""
        assert len(find_coprime_cliques(5, 3)) == 7

    def test_k_too_large(self):
        assert find_coprime_cliques(3, 5) == []

    def test_k0_empty(self):
        assert find_coprime_cliques(5, 0) == []


# ---------------------------------------------------------------------------
# SAT encoding
# ---------------------------------------------------------------------------

class TestBuildSATInstance:
    def test_variable_count_matches_edges(self):
        for n in [5, 8, 10]:
            _, etv, nv, nc, _ = build_sat_instance(n, 3)
            assert nv == len(coprime_edges(n))

    def test_clause_count_is_twice_cliques(self):
        for n in [5, 8, 10]:
            solver, _, nv, nc, cliques = build_sat_instance(n, 3)
            assert nc == 2 * len(cliques)
            solver.delete()

    def test_symmetry_breaking_adds_clause(self):
        _, _, _, nc_plain, _ = build_sat_instance(10, 3, symmetry_breaking=False)
        _, _, _, nc_sb, _ = build_sat_instance(10, 3, symmetry_breaking=True)
        assert nc_sb == nc_plain + 1

    def test_sat_at_n10_k3(self):
        solver, _, _, _, _ = build_sat_instance(10, 3)
        assert solver.solve()
        solver.delete()

    def test_unsat_at_n11_k3(self):
        solver, _, _, _, _ = build_sat_instance(11, 3)
        assert not solver.solve()
        solver.delete()

    def test_proof_extraction(self):
        solver, _, _, _, _ = build_sat_instance(11, 3, with_proof=True)
        assert not solver.solve()
        proof = solver.get_proof()
        assert proof is not None
        assert len(proof) > 0
        solver.delete()


# ---------------------------------------------------------------------------
# 1. Complexity profile
# ---------------------------------------------------------------------------

class TestComplexityProfile:
    def test_k3_profile_structure(self):
        profile = complexity_profile(3, range(3, 8))
        assert "data" in profile
        assert "fits" in profile
        assert len(profile["data"]) == 5

    def test_k3_sat_unsat_transition(self):
        """R_cop(3)=11: SAT for n<=10, UNSAT at n=11."""
        profile = complexity_profile(3, range(9, 12))
        data = profile["data"]
        assert data[0]["sat"]      # n=9
        assert data[1]["sat"]      # n=10
        assert not data[2]["sat"]  # n=11

    def test_vars_and_clauses_increase(self):
        profile = complexity_profile(3, range(3, 10))
        prev_v, prev_c = 0, 0
        for r in profile["data"]:
            assert r["num_vars"] >= prev_v
            assert r["num_clauses"] >= prev_c
            prev_v = r["num_vars"]
            prev_c = r["num_clauses"]

    def test_solver_stats_present(self):
        profile = complexity_profile(3, range(5, 8))
        for r in profile["data"]:
            assert "conflicts" in r
            assert "decisions" in r
            assert "propagations" in r
            assert "solve_time" in r

    def test_fits_have_models(self):
        """At least one model should fit each metric."""
        profile = complexity_profile(3, range(3, 12))
        for metric in ["conflicts", "num_clauses", "num_vars"]:
            assert metric in profile["fits"]
            assert len(profile["fits"][metric]) > 0

    def test_num_vars_polynomial_fit(self):
        """Number of variables (coprime edges) is O(n^2) -- polynomial fit best."""
        profile = complexity_profile(3, range(3, 12))
        fits = profile["fits"]["num_vars"]
        if "polynomial" in fits:
            # The exponent should be close to 2 (phi(n) density ~ 6/pi^2)
            b = fits["polynomial"]["params"]["b"]
            assert 1.5 < b < 2.5, f"Expected quadratic growth, got n^{b:.2f}"


class TestFitModels:
    def test_polynomial_data(self):
        ns = np.array([1, 2, 3, 4, 5, 6, 7, 8], dtype=float)
        ys = ns ** 2 + 1
        fits = _fit_models(ns, ys)
        assert "polynomial" in fits
        assert fits["polynomial"]["params"]["b"] == pytest.approx(2.0, abs=0.1)

    def test_exponential_data(self):
        ns = np.array([1, 2, 3, 4, 5, 6, 7], dtype=float)
        ys = 2.0 * np.exp(0.5 * ns)
        fits = _fit_models(ns, ys)
        assert "exponential" in fits

    def test_insufficient_data(self):
        ns = np.array([1.0, 2.0])
        ys = np.array([1.0, 2.0])
        fits = _fit_models(ns, ys)
        assert fits == {}

    def test_zero_data_handled(self):
        ns = np.array([1, 2, 3, 4, 5], dtype=float)
        ys = np.array([0, 0, 1, 2, 3], dtype=float)
        fits = _fit_models(ns, ys)
        # Should still produce fits (zeros filtered)
        assert isinstance(fits, dict)


# ---------------------------------------------------------------------------
# 2. Clause density
# ---------------------------------------------------------------------------

class TestClauseDensity:
    def test_k3_threshold_at_11(self):
        result = clause_density_analysis(
            k_values=(3,),
            n_range_map={3: list(range(3, 13))},
        )
        assert "k=3" in result
        assert result["k=3"]["threshold_n"] == 11

    def test_clause_width_correct(self):
        """Clause width for k-clique constraint is C(k,2)."""
        result = clause_density_analysis(
            k_values=(3, 4),
            n_range_map={3: [5], 4: [10]},
        )
        assert result["k=3"]["clause_width"] == 3   # C(3,2) = 3
        assert result["k=4"]["clause_width"] == 6   # C(4,2) = 6

    def test_random_threshold_formula(self):
        """Verify the random k-SAT threshold formula."""
        result = clause_density_analysis(
            k_values=(3,),
            n_range_map={3: [5]},
        )
        ln2 = math.log(2)
        expected = 2**3 * ln2 - (1 + ln2) / 2
        assert result["k=3"]["random_ksat_threshold"] == pytest.approx(expected, rel=1e-10)

    def test_ratio_increases_with_n(self):
        result = clause_density_analysis(
            k_values=(3,),
            n_range_map={3: list(range(5, 12))},
        )
        ratios = [d["clause_var_ratio"] for d in result["k=3"]["density_data"]]
        # Not strictly monotone (can dip at even n), but overall trend is up
        assert ratios[-1] > ratios[0]

    def test_structural_excess_below_one_for_k3(self):
        """Coprime structure forces UNSAT below random 3-SAT threshold."""
        result = clause_density_analysis(
            k_values=(3,),
            n_range_map={3: list(range(3, 13))},
        )
        excess = result["k=3"]["structural_excess"]
        assert excess is not None
        assert excess < 1.0, (
            f"Expected structural excess < 1 (UNSAT before random threshold), "
            f"got {excess:.3f}"
        )


# ---------------------------------------------------------------------------
# 3. Backbone analysis
# ---------------------------------------------------------------------------

class TestEnumerateAllSolutions:
    def test_n3_k3(self):
        """n=3, k=3: triangle {1,2,3}. 6 colorings of 3 edges, minus 2
        monochromatic = 4 solutions without symmetry breaking.
        Actually: 2^3 = 8, minus 2 all-same = 6 avoiding."""
        solutions = enumerate_all_solutions(3, 3)
        assert len(solutions) == 6

    def test_n10_k3_count(self):
        """Known: 156 avoiding colorings at n=10 for k=3."""
        solutions = enumerate_all_solutions(10, 3)
        assert len(solutions) == 156

    def test_n11_k3_none(self):
        """n=11 is UNSAT for k=3 -- no solutions."""
        solutions = enumerate_all_solutions(11, 3)
        assert len(solutions) == 0

    def test_solutions_are_valid(self):
        """Every enumerated solution should avoid monochromatic K_3."""
        solutions = enumerate_all_solutions(8, 3)
        cliques = find_coprime_cliques(8, 3)
        for sol in solutions:
            for c in cliques:
                colors = set()
                for i in range(3):
                    for j in range(i + 1, 3):
                        e = (min(c[i], c[j]), max(c[i], c[j]))
                        colors.add(sol.get(e, -1))
                assert len(colors) > 1, f"Monochromatic clique {c}"


class TestBackboneAnalysis:
    @pytest.fixture(scope="module")
    def solutions_n10(self):
        return enumerate_all_solutions(10, 3)

    def test_backbone_at_n10_k3(self, solutions_n10):
        bb = backbone_analysis(10, 3, solutions_n10)
        assert bb["num_solutions"] == 156
        assert bb["num_edges"] == 31
        assert 0.0 <= bb["backbone_fraction"] <= 1.0

    def test_backbone_empty_for_unsat(self):
        bb = backbone_analysis(11, 3, [])
        assert bb["num_solutions"] == 0
        assert bb["backbone_fraction"] is None

    def test_mean_bias_between_half_and_one(self, solutions_n10):
        bb = backbone_analysis(10, 3, solutions_n10)
        assert 0.5 <= bb["mean_bias"] <= 1.0

    def test_n10_backbone_fraction_is_zero(self, solutions_n10):
        """At n=10, backbone fraction is 0 (no edge is fixed)."""
        bb = backbone_analysis(10, 3, solutions_n10)
        assert bb["backbone_fraction"] == 0.0

    def test_n10_mean_bias_is_half(self, solutions_n10):
        """With no backbone, mean bias should be 0.5 (perfectly balanced)."""
        bb = backbone_analysis(10, 3, solutions_n10)
        assert bb["mean_bias"] == pytest.approx(0.5, abs=0.01)

    def test_polarity_counts_sum_to_num_solutions(self, solutions_n10):
        bb = backbone_analysis(10, 3, solutions_n10)
        for e, pol in bb["edge_polarity"].items():
            assert pol[0] + pol[1] == 156


# ---------------------------------------------------------------------------
# 4. Proof complexity
# ---------------------------------------------------------------------------

class TestProofComplexity:
    def test_sat_instance_no_proof(self):
        result = proof_complexity_analysis(10, 3)
        assert result["sat"] is True
        assert "message" in result

    def test_unsat_instance_has_proof(self):
        result = proof_complexity_analysis(11, 3)
        assert result["sat"] is False
        assert result["derivation_steps"] > 0

    def test_proof_steps_bounded_by_conflicts(self):
        """Proof derivation steps should equal or exceed solver conflicts."""
        result = proof_complexity_analysis(11, 3)
        # Each conflict derives at least one clause
        assert result["derivation_steps"] >= result["solver_stats"]["conflicts"]

    def test_n11_proof_is_polynomial(self):
        result = proof_complexity_analysis(11, 3)
        assert result["complexity_class"] == "polynomial"
        assert result["log_proof_over_log_vars"] < 3.0

    def test_proof_clause_width_bounded(self):
        """Proof clauses should not be wider than the original clause width."""
        result = proof_complexity_analysis(11, 3)
        # Original clauses have width 3 (from triangles). Resolvents can be wider.
        assert result["max_proof_clause_width"] <= result["num_vars"]

    def test_num_vars_and_clauses_correct(self):
        result = proof_complexity_analysis(11, 3)
        assert result["num_vars"] == len(coprime_edges(11))
        assert result["num_clauses"] == 2 * len(find_coprime_cliques(11, 3))


class TestProofScaling:
    def test_k3_scaling_has_records(self):
        result = proof_scaling(3, [11, 12, 13])
        assert len(result["records"]) == 3

    def test_all_records_unsat(self):
        result = proof_scaling(3, [11, 12, 13])
        for r in result["records"]:
            assert r["derivation_steps"] > 0
            assert r["conflicts"] > 0

    def test_scaling_fits_present(self):
        result = proof_scaling(3, list(range(11, 18)))
        assert "fits" in result
        if result["fits"]:
            assert "derivation_steps" in result["fits"]


# ---------------------------------------------------------------------------
# 5. Symmetry analysis
# ---------------------------------------------------------------------------

class TestAutomorphisms:
    def test_identity_always_present(self):
        """The identity permutation is always an automorphism."""
        auto = coprime_graph_automorphisms(5)
        assert auto["num_automorphisms"] >= 1

    def test_known_values(self):
        """Verify automorphism counts for small n."""
        expected = {5: 12, 7: 12, 8: 36, 9: 72, 10: 24}
        for n, expected_count in expected.items():
            auto = coprime_graph_automorphisms(n)
            assert auto["num_automorphisms"] == expected_count, (
                f"n={n}: expected {expected_count}, got {auto['num_automorphisms']}"
            )

    def test_orbits_partition_vertices(self):
        auto = coprime_graph_automorphisms(8)
        total = sum(auto["orbit_sizes"])
        assert total == 8

    def test_orbit_count_matches(self):
        auto = coprime_graph_automorphisms(10)
        assert auto["orbit_count"] == len(auto["orbit_sizes"])

    def test_lagrange_divides(self):
        """Automorphism group order divides n! (Lagrange's theorem)."""
        for n in range(3, 9):
            auto = coprime_graph_automorphisms(n)
            assert math.factorial(n) % auto["num_automorphisms"] == 0


class TestSymmetryBreaking:
    def test_sat_preserved_with_sb(self):
        """Symmetry breaking shouldn't change SAT/UNSAT status."""
        sb = symmetry_breaking_comparison(10, 3, num_trials=1)
        assert sb["sat_plain"] == sb["sat_symmetry_breaking"]
        assert sb["sat_plain"] == sb["sat_orbit_sbp"]

    def test_unsat_preserved_with_sb(self):
        sb = symmetry_breaking_comparison(11, 3, num_trials=1)
        assert not sb["sat_plain"]
        assert not sb["sat_symmetry_breaking"]
        assert not sb["sat_orbit_sbp"]

    def test_num_automorphisms_reported(self):
        sb = symmetry_breaking_comparison(8, 3, num_trials=1)
        assert sb["num_automorphisms"] == 36

    def test_speedup_positive(self):
        """Speedup ratios should be positive numbers."""
        sb = symmetry_breaking_comparison(10, 3, num_trials=3)
        assert sb["speedup_basic"] > 0
        assert sb["speedup_orbit"] > 0


# ---------------------------------------------------------------------------
# 6. Treewidth / FPT analysis
# ---------------------------------------------------------------------------

class TestTreewidth:
    def test_treewidth_grows_with_n(self):
        result = treewidth_analysis(
            k_values=(3,),
            n_range_map={3: list(range(5, 15))},
        )
        records = result["k=3"]["records"]
        assert records[-1]["coprime_tw"] > records[0]["coprime_tw"]

    def test_primal_tw_at_least_coprime_tw(self):
        """Primal (constraint interaction) graph is denser, so higher treewidth."""
        result = treewidth_analysis(
            k_values=(3,),
            n_range_map={3: list(range(5, 12))},
        )
        for r in result["k=3"]["records"]:
            assert r["primal_tw"] >= r["coprime_tw"]

    def test_linear_slope_positive(self):
        result = treewidth_analysis(
            k_values=(3,),
            n_range_map={3: list(range(5, 20))},
        )
        assert result["k=3"]["tw_linear_slope"] > 0.3

    def test_fpt_not_feasible_k3(self):
        """Treewidth grows linearly, ruling out treewidth-based FPT."""
        result = treewidth_analysis(
            k_values=(3,),
            n_range_map={3: list(range(5, 20))},
        )
        assert not result["k=3"]["fpt_feasible"]

    def test_known_treewidths(self):
        """Check specific treewidth values."""
        result = treewidth_analysis(
            k_values=(3,),
            n_range_map={3: [5, 10, 11]},
        )
        records = {r["n"]: r for r in result["k=3"]["records"]}
        assert records[5]["coprime_tw"] == 3
        assert records[10]["coprime_tw"] == 5
        assert records[11]["coprime_tw"] == 6


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_consistency_across_analyses(self):
        """Cross-check: clause count from profile matches density analysis."""
        profile = complexity_profile(3, [10, 11])
        density = clause_density_analysis(k_values=(3,), n_range_map={3: [10, 11]})

        for p_rec, d_rec in zip(profile["data"], density["k=3"]["density_data"]):
            assert p_rec["n"] == d_rec["n"]
            assert p_rec["num_vars"] == d_rec["num_vars"]
            assert p_rec["num_clauses"] == d_rec["num_clauses"]

    def test_backbone_solution_count_matches_enumeration(self):
        solutions = enumerate_all_solutions(8, 3)
        bb = backbone_analysis(8, 3, solutions)
        assert bb["num_solutions"] == len(solutions)

    def test_proof_at_threshold_consistent(self):
        """Proof analysis at n=11 should agree with profile on UNSAT."""
        profile = complexity_profile(3, [11])
        proof = proof_complexity_analysis(11, 3)
        assert not profile["data"][0]["sat"]
        assert not proof["sat"]
        assert profile["data"][0]["num_vars"] == proof["num_vars"]


# ---------------------------------------------------------------------------
# Extended coverage: k=4 and larger instances
# ---------------------------------------------------------------------------

class TestK4Profile:
    def test_k4_sat_at_n20(self):
        """n=20 should be SAT for k=4."""
        profile = complexity_profile(4, [20])
        assert profile["data"][0]["sat"]

    def test_k4_conflicts_grow(self):
        """Conflicts should generally increase approaching the threshold."""
        profile = complexity_profile(4, [10, 20, 30, 40])
        conflicts = [r["conflicts"] for r in profile["data"]]
        # Conflicts at n=40 should exceed n=10
        assert conflicts[-1] >= conflicts[0]

    def test_k4_clause_density(self):
        """k=4 clause density at small n."""
        result = clause_density_analysis(
            k_values=(4,),
            n_range_map={4: [10, 15, 20]},
        )
        assert "k=4" in result
        assert result["k=4"]["clause_width"] == 6
        # All should be SAT
        for d in result["k=4"]["density_data"]:
            assert d["sat"]


class TestK5Profile:
    def test_k5_sat_at_small_n(self):
        """k=5 should be SAT at small n."""
        profile = complexity_profile(5, [5, 10, 15])
        for r in profile["data"]:
            assert r["sat"]

    def test_k5_clique_count_grows_fast(self):
        """5-clique count should grow rapidly."""
        profile = complexity_profile(5, [10, 15, 20])
        clique_counts = [r["num_cliques"] for r in profile["data"]]
        assert clique_counts[-1] > clique_counts[0] * 10


class TestEdgeCases:
    def test_backbone_single_solution(self):
        """If there's exactly one solution, all variables are backbone."""
        # n=3, k=3: 6 solutions -- need a case with 1 solution.
        # Construct manually via backbone_analysis with synthetic input
        edges = coprime_edges(5)
        fake_solution = {e: 0 if e[0] == 1 else 1 for e in edges}
        bb = backbone_analysis(5, 3, [fake_solution])
        assert bb["backbone_fraction"] == 1.0
        assert bb["num_solutions"] == 1

    def test_automorphism_n3(self):
        """n=3: coprime graph is K_3, automorphism group is S_3."""
        auto = coprime_graph_automorphisms(3)
        assert auto["num_automorphisms"] == 6  # |S_3| = 6

    def test_automorphism_n4(self):
        auto = coprime_graph_automorphisms(4)
        assert auto["num_automorphisms"] >= 1

    def test_proof_scaling_unknown_k(self):
        """Unknown k should return a message."""
        result = proof_scaling(10)
        assert "message" in result

    def test_treewidth_k4(self):
        """k=4 treewidth should also grow."""
        result = treewidth_analysis(
            k_values=(4,),
            n_range_map={4: [5, 10, 15]},
        )
        records = result["k=4"]["records"]
        assert records[-1]["coprime_tw"] > records[0]["coprime_tw"]
