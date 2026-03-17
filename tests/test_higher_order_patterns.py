"""Tests for higher_order_patterns.py -- meta-patterns across discoveries."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from higher_order_patterns import (
    # Utilities
    sieve_primes,
    is_prime,
    prime_index,
    euler_totient,
    mobius,
    coprime_edges,
    # Pattern 1: Primality
    KNOWN_COPRIME_INVARIANTS,
    CLASSICAL_RAMSEY,
    SCHUR_NUMBERS,
    primality_census,
    totient_ratio_analysis,
    coprime_graph_edge_count_at_value,
    gcd_ramsey_number,
    paley_ramsey_test,
    primality_meta_pattern,
    # Pattern 2: Convergence at 13
    convergence_analysis,
    scan_convergence_points,
    special_primes_survey,
    convergence_at_13_full,
    # Pattern 3: Formula zoo
    mersenne_schur_formula,
    chromatic_number_formula,
    schur_cyclic_formula,
    gcd_ramsey_linear_formula,
    formula_structure_analysis,
    # Pattern 4: Zeta(2) web
    build_zeta2_web,
    verify_zeta2_appearances,
    # Pattern 5: Acceleration
    measure_coprime_edge_growth,
    measure_clique_enumeration_growth,
    fit_growth_curve,
    # Synthesis
    higher_order_synthesis,
)


# ===========================================================================
# Utility tests
# ===========================================================================

class TestUtilities:
    def test_sieve_primes_small(self):
        assert sieve_primes(10) == [2, 3, 5, 7]

    def test_sieve_primes_empty(self):
        assert sieve_primes(1) == []

    def test_is_prime_known(self):
        assert is_prime(2)
        assert is_prime(11)
        assert is_prime(59)
        assert is_prime(53)
        assert not is_prime(1)
        assert not is_prime(4)
        assert not is_prime(9)

    def test_prime_index(self):
        assert prime_index(2) == 1
        assert prime_index(11) == 5
        assert prime_index(13) == 6
        assert prime_index(59) == 17
        assert prime_index(4) is None  # not prime

    def test_euler_totient_prime(self):
        """phi(p) = p - 1 for primes."""
        for p in [2, 3, 5, 7, 11, 13]:
            assert euler_totient(p) == p - 1

    def test_euler_totient_composite(self):
        assert euler_totient(6) == 2   # phi(6) = 2
        assert euler_totient(12) == 4  # phi(12) = 4

    def test_mobius_function(self):
        assert mobius(1) == 1
        assert mobius(2) == -1
        assert mobius(6) == 1   # 2*3, two distinct primes
        assert mobius(4) == 0   # 2^2
        assert mobius(30) == -1  # 2*3*5

    def test_coprime_edges_n4(self):
        edges = coprime_edges(4)
        # Pairs: (1,2), (1,3), (1,4), (2,3), (3,4) are coprime
        # (2,4) is NOT coprime
        assert (2, 4) not in edges
        assert (1, 2) in edges
        assert (1, 4) in edges
        assert (3, 4) in edges


# ===========================================================================
# 1. Primality meta-pattern tests
# ===========================================================================

class TestPrimalityCensus:
    def test_coprime_invariants_prime_rich(self):
        """Coprime invariants should be significantly enriched for primes."""
        result = primality_census(KNOWN_COPRIME_INVARIANTS)
        # At least 10 of 18 should be prime (we know it is 15)
        assert result["prime_count"] >= 10
        assert result["enrichment"] > 1.0  # Above random baseline

    def test_classical_ramsey_less_prime(self):
        """Classical Ramsey numbers are mostly composite."""
        result = primality_census(CLASSICAL_RAMSEY)
        # R(3,3)=6, R(4,4)=18, R(3,3,3)=17, R(3,4)=9, R(3,5)=14, R(4,5)=25
        # Only 17 is prime => 1/6
        assert result["prime_count"] <= 2

    def test_enrichment_coprime_gt_classical(self):
        """Coprime invariants should show higher primality enrichment."""
        cop = primality_census(KNOWN_COPRIME_INVARIANTS)
        cla = primality_census(CLASSICAL_RAMSEY)
        assert cop["enrichment"] > cla["enrichment"]

    def test_known_prime_invariants(self):
        """Verify specific known-prime invariants."""
        assert is_prime(KNOWN_COPRIME_INVARIANTS["R_cop(3)"])   # 11
        assert is_prime(KNOWN_COPRIME_INVARIANTS["R_cop(4)"])   # 59
        assert is_prime(KNOWN_COPRIME_INVARIANTS["R_cop(3;3)"]) # 53
        assert is_prime(KNOWN_COPRIME_INVARIANTS["GR_cop(3;3)"])  # 29

    def test_known_composite_invariants(self):
        """Verify specific known-composite invariants."""
        assert not is_prime(KNOWN_COPRIME_INVARIANTS["P_cop(5)"])  # 9
        assert not is_prime(KNOWN_COPRIME_INVARIANTS["P_cop(6)"])  # 10
        assert not is_prime(KNOWN_COPRIME_INVARIANTS["C_cop(4)"])  # 8


class TestTotientAnalysis:
    def test_primes_have_high_totient_ratio(self):
        """Prime invariant values should have phi(v)/v = (v-1)/v, which is high."""
        result = totient_ratio_analysis(KNOWN_COPRIME_INVARIANTS)
        for name, data in result.items():
            if data["is_prime"]:
                assert data["phi_over_v"] > 0.4

    def test_composites_lower_totient(self):
        """Composite values tend to have lower phi(v)/v."""
        result = totient_ratio_analysis(KNOWN_COPRIME_INVARIANTS)
        prime_ratios = [d["phi_over_v"] for d in result.values() if d["is_prime"] and d["value"] > 5]
        comp_ratios = [d["phi_over_v"] for d in result.values() if not d["is_prime"]]
        if prime_ratios and comp_ratios:
            assert sum(prime_ratios) / len(prime_ratios) > sum(comp_ratios) / len(comp_ratios)


class TestGcdRamseyScaling:
    def test_rgcd_3_1_equals_rcop_3(self):
        """R_gcd(3; 1) = R_cop(3) = 11."""
        assert gcd_ramsey_number(3, 1, max_n=15) == 11

    def test_rgcd_3_2_equals_22(self):
        """R_gcd(3; 2) = 22 (linear scaling)."""
        assert gcd_ramsey_number(3, 2, max_n=25) == 22

    def test_rgcd_3_3_equals_33(self):
        """R_gcd(3; 3) = 33 (linear scaling)."""
        assert gcd_ramsey_number(3, 3, max_n=40) == 33

    def test_linear_scaling(self):
        """R_gcd(3; d) = 11 * d for d = 1, 2, 3."""
        for d in range(1, 4):
            val = gcd_ramsey_number(3, d, max_n=40)
            assert val == 11 * d, f"R_gcd(3;{d}) = {val}, expected {11 * d}"

    def test_linear_implies_non_prime_for_d_gt_1(self):
        """R_gcd(3; d) = 11d is composite for d > 1 (since 11d has factor d)."""
        for d in range(2, 4):
            val = gcd_ramsey_number(3, d, max_n=40)
            assert not is_prime(val), f"R_gcd(3;{d}) = {val} should be composite"


class TestPaleyGraphs:
    def test_paley_densities_are_half(self):
        """Paley graphs are (p-1)/2-regular => density 1/2."""
        results = paley_ramsey_test(max_p=30)
        for r in results:
            assert abs(r["density"] - 0.5) < 0.01

    def test_paley_clique_grows(self):
        """Clique number of Paley graphs should grow with p."""
        results = paley_ramsey_test(max_p=50)
        if len(results) >= 2:
            assert results[-1]["omega"] >= results[0]["omega"]


class TestCoprimGraphAtValue:
    def test_edge_density_converges_to_zeta2(self):
        """Edge density at large n should approach 6/pi^2."""
        _, _, density = coprime_graph_edge_count_at_value(50)
        assert abs(density - 6 / math.pi**2) < 0.05


# ===========================================================================
# 2. Convergence at 13 tests
# ===========================================================================

class TestConvergenceAt13:
    def test_13_is_prime(self):
        result = convergence_analysis(13)
        assert result["is_prime"]

    def test_pi_13_equals_6(self):
        """pi(13) = 6, the 6th prime."""
        result = convergence_analysis(13)
        assert result["prime_index"] == 6

    def test_pi_13_equals_R33(self):
        """pi(13) = 6 = R(3,3)."""
        result = convergence_analysis(13)
        assert result["pi_target_eq_Rkk"] == 3  # k=3 matches

    def test_13_has_multiple_families(self):
        """At least 3 independent families produce 13."""
        result = convergence_analysis(13)
        assert result["num_families"] >= 3

    def test_convergence_at_13_families(self):
        """S(3), P_cop(7), P_cop(8), C_cop(5) all equal 13."""
        assert SCHUR_NUMBERS["S(3)"] == 13
        assert KNOWN_COPRIME_INVARIANTS["P_cop(7)"] == 13
        assert KNOWN_COPRIME_INVARIANTS["P_cop(8)"] == 13
        assert KNOWN_COPRIME_INVARIANTS["C_cop(5)"] == 13


class TestConvergencePoints:
    def test_scan_finds_13(self):
        """13 should appear as a convergence point."""
        points = scan_convergence_points()
        values = [p["value"] for p in points]
        assert 13 in values

    def test_scan_finds_11(self):
        """11 should appear (R_cop(3) = C_cop(3) = C_cop(6) = 11)."""
        points = scan_convergence_points()
        values = [p["value"] for p in points]
        assert 11 in values

    def test_convergence_points_non_empty(self):
        points = scan_convergence_points()
        assert len(points) >= 2

    def test_13_has_most_families(self):
        """13 should have the most families among convergence points."""
        points = scan_convergence_points()
        max_fam = max(p["num_families"] for p in points)
        point_13 = [p for p in points if p["value"] == 13]
        assert len(point_13) == 1
        assert point_13[0]["num_families"] == max_fam


class TestSpecialPrimes:
    def test_p_6_is_13(self):
        """The 6th prime is 13."""
        result = special_primes_survey()
        assert result[3]["p_R(k,k)"] == 13

    def test_p_2_is_3(self):
        """The 2nd prime is 3."""
        result = special_primes_survey()
        assert result[2]["p_R(k,k)"] == 3

    def test_13_has_most_matches(self):
        """p_R(3,3) = 13 should have the most invariant matches."""
        result = special_primes_survey()
        matches_at_13 = result[3]["num_invariant_matches"]
        matches_at_3 = result[2]["num_invariant_matches"]
        assert matches_at_13 > matches_at_3


# ===========================================================================
# 3. Formula zoo tests
# ===========================================================================

class TestMersenneSchur:
    def test_ms1(self):
        """MS(1) = 2^2 - 1 = 3."""
        assert mersenne_schur_formula(1) == 3

    def test_ms2(self):
        """MS(2) = 2^5 - 1 = 31."""
        assert mersenne_schur_formula(2) == 31

    def test_ms1_prime(self):
        assert is_prime(mersenne_schur_formula(1))

    def test_ms2_prime(self):
        assert is_prime(mersenne_schur_formula(2))

    def test_ms3_composite(self):
        """MS(3) = 2^14 - 1 = 16383 = 3 * 43 * 127."""
        val = mersenne_schur_formula(3)
        assert val == 16383
        assert not is_prime(val)


class TestChromaticFormula:
    def test_chi_small(self):
        """chi(G(n)) = 1 + pi(n) for small n."""
        assert chromatic_number_formula(2) == 2   # 1 + pi(2) = 1 + 1
        assert chromatic_number_formula(5) == 4   # 1 + pi(5) = 1 + 3
        assert chromatic_number_formula(10) == 5  # 1 + pi(10) = 1 + 4
        assert chromatic_number_formula(13) == 7  # 1 + pi(13) = 1 + 6

    def test_chi_monotone(self):
        """Chromatic number is non-decreasing."""
        prev = chromatic_number_formula(2)
        for n in range(3, 30):
            curr = chromatic_number_formula(n)
            assert curr >= prev
            prev = curr


class TestSchurCyclicFormula:
    def test_prime_5(self):
        """S(Z/5Z, 1) ~ |{x : 5/3 < x < 10/3}| = |{2, 3}| = 2."""
        val = schur_cyclic_formula(5)
        assert val == 2

    def test_prime_7(self):
        """S(Z/7Z, 1) ~ |{x : 7/3 < x < 14/3}| = |{3, 4}| = 2."""
        val = schur_cyclic_formula(7)
        assert val == 2

    def test_prime_13(self):
        """S(Z/13Z, 1) ~ |{x : 13/3 < x < 26/3}| = |{5,6,7,8}| = 4."""
        val = schur_cyclic_formula(13)
        assert val == 4

    def test_scales_linearly_with_p(self):
        """S(Z/pZ, 1) / (p/3) -> 1 for large p."""
        for p in sieve_primes(100):
            if p < 7:
                continue
            val = schur_cyclic_formula(p)
            ratio = val / (p / 3)
            assert 0.8 < ratio < 1.2, f"p={p}: ratio={ratio}"


class TestGcdRamseyFormula:
    def test_formula_matches_for_k3(self):
        """Formula R_gcd(k;d) = R_cop(k)*d matches for k=3."""
        for d in range(1, 4):
            assert gcd_ramsey_linear_formula(3, d) == 11 * d


class TestFormulaStructure:
    def test_rational_constant_pairs_found(self):
        """Analysis should find rational pairs among formula constants."""
        result = formula_structure_analysis()
        assert len(result["rational_constant_pairs"]) >= 2

    def test_coprime_shifted_ratio_is_27_32(self):
        """coprime_density / shifted_density = 27/32."""
        result = formula_structure_analysis()
        pairs = result["rational_constant_pairs"]
        found = any(p["pair"] == ("coprime_density", "shifted_density")
                    and p["rational_form"] == "27/32"
                    for p in pairs)
        assert found

    def test_coprime_all_odd_ratio_is_3_4(self):
        """coprime_density / all_odd_density = 3/4."""
        result = formula_structure_analysis()
        pairs = result["rational_constant_pairs"]
        found = any(p["pair"] == ("coprime_density", "all_odd_density")
                    and p["rational_form"] == "3/4"
                    for p in pairs)
        assert found


# ===========================================================================
# 4. Zeta(2) web tests
# ===========================================================================

class TestZeta2Web:
    def test_web_has_independent_origins(self):
        web = build_zeta2_web()
        assert web["independent_origins"] >= 3

    def test_coprime_density_is_root(self):
        web = build_zeta2_web()
        apps = {a["name"]: a for a in web["appearances"]}
        assert apps["coprime_density"]["derived_from"] is None
        assert apps["coprime_density"]["independent"]

    def test_derived_appearances_trace_to_roots(self):
        web = build_zeta2_web()
        apps = {a["name"]: a for a in web["appearances"]}
        for a in web["appearances"]:
            if a["derived_from"] is not None:
                assert a["derived_from"] in apps

    def test_deepest_chain_non_trivial(self):
        web = build_zeta2_web()
        assert web["max_dependency_depth"] >= 2

    def test_deepest_chain_starts_at_root(self):
        web = build_zeta2_web()
        chain = web["deepest_chain"]
        apps = {a["name"]: a for a in web["appearances"]}
        assert apps[chain[0]]["independent"]

    def test_total_exceeds_independent(self):
        web = build_zeta2_web()
        assert web["total_appearances"] > web["independent_origins"]


class TestZeta2Verification:
    def test_coprime_density_close_to_target(self):
        v = verify_zeta2_appearances()
        assert v["coprime_density"]["relative_error"] < 0.01

    def test_squarefree_density_close(self):
        v = verify_zeta2_appearances()
        assert v["squarefree_density"]["error"] < 0.005

    def test_top_layer_density_close(self):
        v = verify_zeta2_appearances()
        assert v["top_layer_density"]["error"] < 0.01


# ===========================================================================
# 5. Acceleration pattern tests
# ===========================================================================

class TestEdgeGrowth:
    def test_edges_quadratic(self):
        """Coprime edge count grows as ~n^2."""
        data = measure_coprime_edge_growth()
        fit = fit_growth_curve(data, "n", "edges")
        assert "power_law" in fit
        # Exponent should be close to 2
        assert 1.8 < fit["power_law"]["exponent"] < 2.2

    def test_edge_growth_r_squared_high(self):
        data = measure_coprime_edge_growth()
        fit = fit_growth_curve(data, "n", "edges")
        assert fit["power_law"]["r_squared"] > 0.99


class TestCliqueGrowth:
    def test_triangle_growth_cubic(self):
        """3-clique count grows roughly as n^3."""
        data = measure_clique_enumeration_growth(k=3)
        fit = fit_growth_curve(data, "n", "num_cliques")
        assert "power_law" in fit
        # Exponent should be around 3 (each triangle ~ three coprime pairs)
        assert 2.5 < fit["power_law"]["exponent"] < 4.0

    def test_k4_clique_growth_higher_than_k3(self):
        """4-clique growth exponent should exceed 3-clique growth exponent."""
        data3 = measure_clique_enumeration_growth(k=3)
        data4 = measure_clique_enumeration_growth(k=4)
        fit3 = fit_growth_curve(data3, "n", "num_cliques")
        fit4 = fit_growth_curve(data4, "n", "num_cliques")
        if "power_law" in fit3 and "power_law" in fit4:
            assert fit4["power_law"]["exponent"] > fit3["power_law"]["exponent"]


class TestFitGrowthCurve:
    def test_pure_quadratic(self):
        """Fitting y = x^2 data should find exponent ~2."""
        data = [{"x": x, "y": x**2} for x in range(1, 20)]
        fit = fit_growth_curve(data, "x", "y")
        assert abs(fit["power_law"]["exponent"] - 2.0) < 0.05

    def test_pure_exponential(self):
        """Fitting y = 2^x should find exponential base ~2."""
        data = [{"x": x, "y": 2**x} for x in range(1, 15)]
        fit = fit_growth_curve(data, "x", "y")
        assert "exponential" in fit
        assert abs(fit["exponential"]["base"] - 2.0) < 0.1

    def test_insufficient_data(self):
        """With < 3 points, should report insufficient data."""
        data = [{"x": 1, "y": 1}, {"x": 2, "y": 4}]
        fit = fit_growth_curve(data, "x", "y")
        assert fit["model"] == "insufficient_data"


# ===========================================================================
# Cross-investigation and synthesis tests
# ===========================================================================

class TestSynthesis:
    def test_synthesis_has_all_sections(self):
        result = higher_order_synthesis()
        assert "primality" in result
        assert "convergence_13" in result
        assert "formula_zoo" in result
        assert "zeta2_web" in result
        assert "zeta2_verification" in result
        assert "acceleration" in result
        assert "cross_connections" in result

    def test_cross_connections_non_empty(self):
        result = higher_order_synthesis()
        assert len(result["cross_connections"]) >= 3

    def test_prime_indices_of_rcop(self):
        """pi(R_cop(k)) = 1, 5, 17 (differences 4, 12)."""
        assert prime_index(2) == 1
        assert prime_index(11) == 5
        assert prime_index(59) == 17
        # Differences: 5-1=4, 17-5=12, ratio 12/4=3
        diffs = [5 - 1, 17 - 5]
        assert diffs == [4, 12]
        assert diffs[1] / diffs[0] == 3


class TestInvariantValues:
    """Verify the known invariant values are self-consistent."""

    def test_rcop_monotone(self):
        """R_cop(k) increases with k."""
        assert KNOWN_COPRIME_INVARIANTS["R_cop(2)"] < KNOWN_COPRIME_INVARIANTS["R_cop(3)"]
        assert KNOWN_COPRIME_INVARIANTS["R_cop(3)"] < KNOWN_COPRIME_INVARIANTS["R_cop(4)"]

    def test_pcop_monotone(self):
        """P_cop(k) is non-decreasing."""
        for k in range(3, 8):
            curr = KNOWN_COPRIME_INVARIANTS[f"P_cop({k})"]
            nxt = KNOWN_COPRIME_INVARIANTS[f"P_cop({k + 1})"]
            assert nxt >= curr, f"P_cop({k+1})={nxt} < P_cop({k})={curr}"

    def test_ccop3_equals_rcop3(self):
        """C_cop(3) = R_cop(3) since 3-cycles are triangles."""
        assert KNOWN_COPRIME_INVARIANTS["C_cop(3)"] == KNOWN_COPRIME_INVARIANTS["R_cop(3)"]

    def test_coprime_exceeds_classical(self):
        """R_cop(k) > R(k,k) for k >= 3."""
        assert KNOWN_COPRIME_INVARIANTS["R_cop(3)"] > CLASSICAL_RAMSEY["R(3,3)"]
        assert KNOWN_COPRIME_INVARIANTS["R_cop(4)"] > CLASSICAL_RAMSEY["R(4,4)"]
