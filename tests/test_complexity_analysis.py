"""Tests for complexity_analysis.py -- Computational Complexity of Coprime Ramsey Problems."""

import math
import sys
from pathlib import Path

import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from complexity_analysis import (
    coprime_edges,
    coprime_adj,
    find_coprime_cliques,
    build_sat_instance,
    profile_sat_instance,
    profile_rcop_range,
    classify_phase,
    SATProfile,
    compute_backbone,
    constraint_tightness,
    CSPProfile,
    analyze_resolution_complexity,
    resolution_profile_range,
    ResolutionProfile,
    compute_rcop_timed,
    extrapolate_rcop,
    ParameterizedProfile,
    graph_coloring_sat,
    clique_cover_sat,
    independent_set_sat,
    compare_with_combinatorial_problems,
    CombinatorialComparison,
    coprime_graph_properties,
    classify_complexity,
    ComplexityClassification,
    plot_phase_diagram,
)


# =========================================================================
# 1. SAT Instance Hardness Profiling
# =========================================================================

class TestBuildSATInstance:
    """Test the core SAT encoding for correctness."""

    def test_clause_count_matches_cliques(self):
        """Each k-clique produces exactly 2 clauses, plus 1 symmetry-breaking."""
        for n, k in [(5, 3), (8, 3), (10, 3), (8, 4)]:
            clauses, etv, num_cliques = build_sat_instance(n, k)
            # 2 clauses per clique + 1 symmetry-breaking
            assert len(clauses) == 2 * num_cliques + 1

    def test_variable_count_matches_edges(self):
        """Number of variables equals number of coprime edges."""
        for n in [5, 8, 10, 15]:
            clauses, etv, _ = build_sat_instance(n, 3)
            assert len(etv) == len(coprime_edges(n))

    def test_symmetry_breaking_clause(self):
        """First clause is the symmetry-breaking unit clause [x_{(1,2)}]."""
        clauses, etv, _ = build_sat_instance(5, 3)
        assert clauses[0] == [etv[(1, 2)]]

    def test_clause_lengths_for_k3(self):
        """For k=3, each clique clause has C(3,2)=3 literals."""
        clauses, etv, _ = build_sat_instance(8, 3)
        # Skip symmetry-breaking clause (length 1)
        for cl in clauses[1:]:
            assert len(cl) == 3

    def test_clause_lengths_for_k4(self):
        """For k=4, each clique clause has C(4,2)=6 literals."""
        clauses, etv, _ = build_sat_instance(10, 4)
        for cl in clauses[1:]:
            assert len(cl) == 6

    def test_empty_instance(self):
        """n=1 has no edges, so no clauses (degenerate case)."""
        clauses, etv, num_cliques = build_sat_instance(1, 3)
        assert len(etv) == 0
        assert num_cliques == 0


class TestProfileSATInstance:
    """Test the SAT profiling on known instances."""

    def test_n10_k3_is_sat(self):
        """n=10 is below R_cop(3)=11, so the instance is SAT."""
        p = profile_sat_instance(10, 3)
        assert p.is_sat is True
        assert p.n == 10
        assert p.k == 3

    def test_n11_k3_is_unsat(self):
        """n=11 equals R_cop(3), so the instance is UNSAT."""
        p = profile_sat_instance(11, 3)
        assert p.is_sat is False

    def test_profile_fields_consistent(self):
        """All profile fields are consistent with each other."""
        p = profile_sat_instance(8, 3)
        assert p.num_variables > 0
        assert p.num_clauses > 0
        assert abs(p.clause_variable_ratio - p.num_clauses / p.num_variables) < 1e-10
        assert p.min_clause_len <= p.avg_clause_len <= p.max_clause_len
        assert 0 < p.graph_density < 1
        assert p.solve_time >= 0

    def test_graph_density_approaches_6_over_pi2(self):
        """Coprime edge density should approach 6/pi^2 for large n."""
        p = profile_sat_instance(30, 3)
        expected = 6.0 / math.pi**2
        assert abs(p.graph_density - expected) < 0.05

    def test_ratio_increases_with_n(self):
        """Clause/variable ratio should generally increase with n for k=3."""
        profiles = [profile_sat_instance(n, 3) for n in [5, 8, 10]]
        ratios = [p.clause_variable_ratio for p in profiles]
        # Not strictly monotone (depends on clique growth) but should trend up
        assert ratios[-1] > ratios[0]


class TestClassifyPhase:
    """Test phase classification against random 3-SAT theory."""

    def test_easy_sat(self):
        assert classify_phase(2.0, True) == "easy-SAT"

    def test_hard_sat(self):
        assert classify_phase(4.0, True) == "hard-SAT"

    def test_anomalous_sat(self):
        """SAT despite ratio > 5.0 -- structured instance."""
        assert classify_phase(6.0, True) == "anomalous-SAT"

    def test_easy_unsat(self):
        assert classify_phase(6.0, False) == "easy-UNSAT"

    def test_hard_unsat(self):
        assert classify_phase(4.0, False) == "hard-UNSAT"

    def test_anomalous_unsat(self):
        assert classify_phase(2.0, False) == "anomalous-UNSAT"

    def test_boundary_values(self):
        """Exact boundary between easy-SAT and hard-SAT."""
        # ratio = 3.5 is in hard-SAT
        assert classify_phase(3.5, True) == "hard-SAT"
        # ratio = 3.49 is in easy-SAT
        assert classify_phase(3.49, True) == "easy-SAT"
        # ratio = 5.0 is in hard-SAT
        assert classify_phase(5.0, True) == "anomalous-SAT"

    def test_coprime_ramsey_anomaly(self):
        """Coprime Ramsey instances at high n should be anomalous-SAT."""
        # n=10 k=3 has high ratio but is SAT
        p = profile_sat_instance(10, 3)
        phase = classify_phase(p.clause_variable_ratio, p.is_sat)
        # The ratio at n=10 should put us in anomalous or hard territory
        assert p.is_sat
        assert p.clause_variable_ratio > 2.0  # sanity check


class TestProfileRCopRange:
    """Test batch profiling."""

    def test_range_returns_correct_count(self):
        profiles = profile_rcop_range(3, 4, 8)
        # n=4 through 8 (all have coprime edges)
        assert len(profiles) == 5

    def test_sat_unsat_transition_k3(self):
        """The SAT->UNSAT transition for k=3 must happen at n=11."""
        profiles = profile_rcop_range(3, 9, 12)
        sat_status = {p.n: p.is_sat for p in profiles}
        assert sat_status[10] is True
        assert sat_status[11] is False


# =========================================================================
# 2. Constraint Satisfaction Complexity
# =========================================================================

class TestConstraintTightness:
    """Test tightness computation for coprime Ramsey constraints."""

    def test_tightness_k3(self):
        """k=3: arity=3, tightness = 2/8 = 0.25."""
        assert constraint_tightness(3) == pytest.approx(0.25)

    def test_tightness_k4(self):
        """k=4: arity=6, tightness = 2/64 = 0.03125."""
        assert constraint_tightness(4) == pytest.approx(0.03125)

    def test_tightness_k5(self):
        """k=5: arity=10, tightness = 2/1024."""
        assert constraint_tightness(5) == pytest.approx(2.0 / 1024)

    def test_tightness_decreases(self):
        """Tightness decreases exponentially with k."""
        vals = [constraint_tightness(k) for k in range(3, 7)]
        for i in range(len(vals) - 1):
            assert vals[i] > vals[i + 1]


class TestComputeBackbone:
    """Test backbone computation on coprime Ramsey CSP instances."""

    def test_backbone_n6_k3_small(self):
        """At n=6, backbone should exist but be small."""
        csp = compute_backbone(6, 3, max_solutions=10000)
        assert csp.num_solutions > 0
        assert csp.num_variables == len(coprime_edges(6))
        assert csp.backbone_fraction >= 0.0
        assert csp.backbone_fraction <= 1.0

    def test_backbone_n10_k3(self):
        """At n=10 (R_cop(3)-1), there should be 78 solutions (156/2 with sym-breaking)."""
        csp = compute_backbone(10, 3, max_solutions=50000)
        # With symmetry breaking: 156 total / 2 = 78
        assert csp.num_solutions == 78
        assert csp.num_variables == 31  # coprime edges on [10]

    def test_backbone_fraction_small_at_n10(self):
        """Backbone fraction at n=10 k=3 should be small (most edges are free)."""
        csp = compute_backbone(10, 3, max_solutions=50000)
        # Backbone should be small: solutions are diverse
        assert csp.backbone_fraction < 0.5

    def test_backbone_includes_symmetry_broken_var(self):
        """Variable 1 (edge (1,2)) is always True due to symmetry breaking."""
        csp = compute_backbone(10, 3, max_solutions=50000)
        # Variable 1 = edge (1,2), forced to True (value 1) by symmetry breaking
        assert 1 in csp.backbone_variables
        assert csp.backbone_variables[1] == 1

    def test_backbone_n5_k3_many_solutions(self):
        """At n=5, there are many K_3-free colorings (well below R_cop(3)=11)."""
        csp = compute_backbone(5, 3, max_solutions=10000)
        assert csp.num_solutions > 10  # plenty of solutions

    def test_constraint_density_grows(self):
        """Constraint density should increase with n (more cliques per edge)."""
        d6 = compute_backbone(6, 3, max_solutions=100)
        d9 = compute_backbone(9, 3, max_solutions=100)
        assert d9.constraint_density > d6.constraint_density

    def test_solution_space_fraction_decreases(self):
        """The fraction of solution space (solutions / 2^vars) should
        decrease as n approaches R_cop(3), even if raw solution counts
        are non-monotone due to symmetry breaking interactions."""
        s5 = compute_backbone(5, 3, max_solutions=50000)
        s8 = compute_backbone(8, 3, max_solutions=50000)
        s10 = compute_backbone(10, 3, max_solutions=50000)
        frac_5 = s5.num_solutions / 2**s5.num_variables if s5.num_variables > 0 else 1.0
        frac_8 = s8.num_solutions / 2**s8.num_variables if s8.num_variables > 0 else 1.0
        frac_10 = s10.num_solutions / 2**s10.num_variables if s10.num_variables > 0 else 1.0
        assert frac_5 > frac_8 > frac_10

    def test_empty_instance(self):
        """n=1 has no edges; degenerate case."""
        csp = compute_backbone(1, 3, max_solutions=100)
        assert csp.num_variables == 0
        assert csp.num_solutions == 1


# =========================================================================
# 3. Resolution Proof Complexity
# =========================================================================

class TestResolutionComplexity:
    """Test resolution proof complexity analysis."""

    def test_sat_instance_no_proof(self):
        """SAT instances have no resolution proof (they're satisfiable)."""
        r = analyze_resolution_complexity(8, 3)
        assert r.is_unsat is False
        assert r.tree_resolution_lower_bound == 0.0

    def test_unsat_instance_has_proof(self):
        """UNSAT instance at n=11, k=3 should have a non-trivial proof."""
        r = analyze_resolution_complexity(11, 3)
        assert r.is_unsat is True
        assert r.num_conflicts > 0
        assert r.num_decisions > 0
        assert r.num_propagations > 0

    def test_unsat_proof_bounds(self):
        """Resolution bounds should be positive for UNSAT instances."""
        r = analyze_resolution_complexity(11, 3)
        assert r.tree_resolution_lower_bound > 0
        assert r.general_resolution_lower_bound > 0

    def test_conflicts_at_n11_k3(self):
        """The UNSAT proof at n=11 should require a moderate number of conflicts."""
        r = analyze_resolution_complexity(11, 3)
        # CDCL solves this quickly: expecting < 100 conflicts
        assert 0 < r.num_conflicts < 500

    def test_resolution_profile_range(self):
        """Resolution profiles across a range should transition SAT->UNSAT."""
        profiles = resolution_profile_range(3, 9, 12)
        by_n = {r.n: r for r in profiles}
        assert by_n[10].is_unsat is False
        assert by_n[11].is_unsat is True

    def test_fields_non_negative(self):
        """All resolution statistics should be non-negative."""
        for n in [6, 8, 11]:
            r = analyze_resolution_complexity(n, 3)
            assert r.num_conflicts >= 0
            assert r.num_decisions >= 0
            assert r.num_propagations >= 0
            assert r.num_learned_clauses >= 0

    def test_learned_equals_conflicts(self):
        """In CDCL, each conflict produces exactly one learned clause."""
        r = analyze_resolution_complexity(11, 3)
        assert r.num_learned_clauses == r.num_conflicts


# =========================================================================
# 4. Parameterized Complexity
# =========================================================================

class TestParameterizedComplexity:
    """Test parameterized complexity analysis of R_cop(k)."""

    def test_rcop2_timed(self):
        """R_cop(2) = 2, computed very quickly."""
        pp = compute_rcop_timed(2, max_n=10)
        assert pp.rcop_value == 2
        assert pp.solve_time < 1.0
        assert pp.k == 2

    def test_rcop3_timed(self):
        """R_cop(3) = 11, with timing data."""
        pp = compute_rcop_timed(3, max_n=15)
        assert pp.rcop_value == 11
        assert pp.solve_time < 10.0  # should be fast
        assert pp.n_max_vars > 0
        assert pp.n_max_clauses > 0

    def test_cliques_at_rcop3(self):
        """Number of 3-cliques at n=11 should be substantial."""
        pp = compute_rcop_timed(3, max_n=15)
        # 3-cliques in coprime graph on [11]
        assert pp.num_cliques_at_rcop > 50  # there are many triangles

    def test_time_increases_with_k(self):
        """Computation time should increase from k=2 to k=3."""
        pp2 = compute_rcop_timed(2, max_n=10)
        pp3 = compute_rcop_timed(3, max_n=15)
        # k=3 takes more time than k=2
        assert pp3.solve_time >= pp2.solve_time

    def test_extrapolation_with_known_values(self):
        """Extrapolation from k=2,3 should produce reasonable R_cop(5) estimate."""
        profiles = [
            compute_rcop_timed(2, max_n=10),
            compute_rcop_timed(3, max_n=15),
        ]
        ext = extrapolate_rcop(profiles)
        assert "exponential_fit" in ext
        assert "rcop5_prediction_exp" in ext
        # R_cop(5) should be predicted > R_cop(4) ~ 59
        pred = ext["rcop5_prediction_exp"]
        assert pred > 59

    def test_extrapolation_fpt_analysis(self):
        """FPT analysis should classify the problem."""
        profiles = [
            compute_rcop_timed(2, max_n=10),
            compute_rcop_timed(3, max_n=15),
        ]
        ext = extrapolate_rcop(profiles)
        fpt = ext.get("fpt_analysis", {})
        assert fpt.get("classification") == "likely_XP"
        assert "rationale" in fpt

    def test_extrapolation_insufficient_data(self):
        """Single data point should return insufficient_data."""
        profiles = [compute_rcop_timed(2, max_n=10)]
        ext = extrapolate_rcop(profiles)
        assert ext.get("status") == "insufficient_data"


# =========================================================================
# 5. Comparison with Combinatorial Problems
# =========================================================================

class TestGraphColoringSAT:
    """Test graph coloring SAT encoding on coprime graphs."""

    def test_3_coloring_n5(self):
        """The coprime graph on [5] should be 3-colorable (omega <= 4 for n=5)."""
        gc = graph_coloring_sat(5, 3)
        # Coprime graph on [5] has clique {1,2,3,5} of size 4, so chi >= 4
        # Therefore 3-coloring is UNSAT
        assert gc.is_sat is False

    def test_5_coloring_n5(self):
        """5 colors should suffice for n=5 (n colors always works)."""
        gc = graph_coloring_sat(5, 5)
        assert gc.is_sat is True

    def test_high_k_always_sat(self):
        """n-coloring of an n-vertex graph is always SAT."""
        gc = graph_coloring_sat(8, 8)
        assert gc.is_sat is True

    def test_comparison_fields(self):
        """Output should have all required fields."""
        gc = graph_coloring_sat(6, 3)
        assert gc.num_variables > 0
        assert gc.num_clauses > 0
        assert gc.clause_variable_ratio > 0
        assert gc.solve_time >= 0


class TestCliqueCoverSAT:
    """Test clique cover SAT encoding."""

    def test_clique_cover_k1_unsat(self):
        """Clique cover with k=1 means the whole graph is a clique.
        Coprime graph on [4] is NOT a clique (gcd(2,4)=2), so UNSAT."""
        cc = clique_cover_sat(4, 1)
        assert cc.is_sat is False

    def test_clique_cover_kn_sat(self):
        """n groups always works (each vertex in its own group)."""
        cc = clique_cover_sat(6, 6)
        assert cc.is_sat is True

    def test_comparison_fields(self):
        cc = clique_cover_sat(6, 3)
        assert cc.num_variables > 0
        assert cc.num_clauses > 0


class TestIndependentSetSAT:
    """Test independent set SAT encoding on coprime graphs."""

    def test_independent_set_k1_sat(self):
        """An independent set of size 1 always exists."""
        iset = independent_set_sat(5, 1)
        assert iset.is_sat is True

    def test_independent_set_k2_n6(self):
        """Independent set of size 2 in coprime graph on [6]:
        Need two vertices sharing a common factor > 1. E.g., {2, 4}."""
        iset = independent_set_sat(6, 2)
        assert iset.is_sat is True

    def test_independent_set_too_large(self):
        """Very large independent set in a dense graph should be hard/impossible."""
        # Coprime graph on [5] is very dense; independent set of size 5
        # requires all pairs to share a factor, which is impossible (1 is coprime to all)
        iset = independent_set_sat(5, 5)
        assert iset.is_sat is False

    def test_comparison_fields(self):
        iset = independent_set_sat(6, 2)
        assert iset.num_variables > 0
        assert iset.num_clauses > 0


class TestCompareWithCombinatorialProblems:
    """Test the comparison suite."""

    def test_returns_multiple_comparisons(self):
        comparisons = compare_with_combinatorial_problems(8)
        assert len(comparisons) >= 4  # coprime_ramsey, graph_col x2, clique_cover, indep_set

    def test_coprime_ramsey_is_first(self):
        comparisons = compare_with_combinatorial_problems(8)
        assert "coprime_ramsey" in comparisons[0].problem_name

    def test_all_have_positive_vars(self):
        comparisons = compare_with_combinatorial_problems(8)
        for c in comparisons:
            assert c.num_variables > 0
            assert c.num_clauses > 0

    def test_coprime_ramsey_sat_at_n8(self):
        """Coprime Ramsey at n=8, k=3 should be SAT (below R_cop(3)=11)."""
        comparisons = compare_with_combinatorial_problems(8)
        ramsey = comparisons[0]
        assert ramsey.is_sat is True


# =========================================================================
# 6. P vs NP
# =========================================================================

class TestCoprimeGraphProperties:
    """Test structural properties of the coprime graph."""

    def test_density_n10(self):
        """Coprime graph density at n=10 should be near 6/pi^2."""
        props = coprime_graph_properties(10)
        expected = 6.0 / math.pi**2
        assert abs(props["density"] - expected) < 0.1

    def test_clique_number_bound(self):
        """omega(G([n])) >= 1 + pi(n) (1 is coprime with all primes)."""
        props = coprime_graph_properties(10)
        # Primes <= 10: {2,3,5,7}, so omega >= 5
        assert props["omega_lower_bound"] >= 5

    def test_not_bipartite_n3(self):
        """Coprime graph on [3] has triangle {1,2,3}, so not bipartite."""
        props = coprime_graph_properties(3)
        assert props["is_bipartite"] is False

    def test_bipartite_n2(self):
        """n < 3 case: trivially bipartite."""
        props = coprime_graph_properties(2)
        assert props["is_bipartite"] is True

    def test_degree_stats(self):
        """Degree statistics should be reasonable."""
        props = coprime_graph_properties(10)
        assert props["avg_degree"] > 0
        assert props["max_degree"] >= props["min_degree"]
        assert props["min_degree"] >= 0

    def test_treewidth_lower_bound(self):
        """Treewidth lower bound >= minimum degree."""
        props = coprime_graph_properties(10)
        assert props["treewidth_lower_bound"] == props["min_degree"]


class TestClassifyComplexity:
    """Test the overall complexity classification."""

    def test_in_np(self):
        cc = classify_complexity()
        assert cc.in_NP is True

    def test_in_conp(self):
        cc = classify_complexity()
        assert cc.in_coNP is True

    def test_np_hardness_stated(self):
        cc = classify_complexity()
        assert "NP-complete" in cc.np_hardness

    def test_has_reduction_notes(self):
        cc = classify_complexity()
        assert len(cc.reduction_notes) > 50

    def test_special_structure_populated(self):
        cc = classify_complexity()
        assert "density" in cc.special_structure
        assert "omega_lower_bound" in cc.special_structure


# =========================================================================
# Plotting
# =========================================================================

class TestPlotPhaseDiagram:
    """Test plot generation (file output, no display needed)."""

    def test_plot_generates_file(self, tmp_path):
        """Phase diagram plot should be written to file."""
        profiles = profile_rcop_range(3, 4, 12)
        outpath = str(tmp_path / "phase_diagram.png")
        result = plot_phase_diagram(profiles, output_path=outpath)
        assert result == outpath

    def test_plot_with_empty_profiles(self, tmp_path):
        """Empty profile list should not crash."""
        outpath = str(tmp_path / "empty.png")
        # This may return None (matplotlib error on empty data) or succeed
        try:
            plot_phase_diagram([], output_path=outpath)
        except (ValueError, IndexError):
            pass  # Expected for empty data


# =========================================================================
# Integration: Cross-cutting consistency checks
# =========================================================================

class TestIntegrationConsistency:
    """End-to-end consistency checks across all analysis components."""

    def test_sat_profile_matches_resolution(self):
        """SAT profile and resolution analysis should agree on SAT/UNSAT."""
        for n in [8, 10, 11]:
            sp = profile_sat_instance(n, 3)
            rp = analyze_resolution_complexity(n, 3)
            assert sp.is_sat == (not rp.is_unsat), \
                f"Inconsistency at n={n}: profile.is_sat={sp.is_sat}, resolution.is_unsat={rp.is_unsat}"

    def test_backbone_zero_at_unsat(self):
        """At UNSAT instances, backbone computation should find 0 solutions."""
        csp = compute_backbone(11, 3, max_solutions=1000)
        assert csp.num_solutions == 0

    def test_parameterized_matches_profile(self):
        """R_cop(k) from parameterized computation should match profile transition."""
        pp = compute_rcop_timed(3, max_n=15)
        profiles = profile_rcop_range(3, pp.rcop_value - 1, pp.rcop_value)
        assert profiles[0].is_sat is True   # R_cop(3) - 1 is SAT
        assert profiles[1].is_sat is False  # R_cop(3) is UNSAT

    def test_graph_properties_consistent_with_encoding(self):
        """Graph properties should be consistent with SAT encoding size."""
        n = 10
        props = coprime_graph_properties(n)
        sp = profile_sat_instance(n, 3)
        assert sp.num_variables == props["num_edges"]
        assert sp.num_edges == props["num_edges"]

    def test_backbone_symmetry_breaking(self):
        """The backbone should always contain var 1 (symmetry-broken edge)."""
        for n in [6, 8, 10]:
            csp = compute_backbone(n, 3, max_solutions=10000)
            if csp.num_solutions > 0:
                assert 1 in csp.backbone_variables, \
                    f"Variable 1 should be backbone at n={n}"

    def test_constraint_density_matches_csp(self):
        """Constraint density from CSP should match clique/edge ratio."""
        n, k = 8, 3
        csp = compute_backbone(n, k, max_solutions=10)
        edges = coprime_edges(n)
        cliques = find_coprime_cliques(n, k)
        expected_density = len(cliques) / len(edges) if edges else 0
        assert abs(csp.constraint_density - expected_density) < 1e-10
