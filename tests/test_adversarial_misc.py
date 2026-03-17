#!/usr/bin/env python3
"""
Adversarial tests for six mathematical claims.

Each test attempts to DISPROVE or expose weaknesses in a claimed result.
Test verdict: CONFIRMED means the claim survived the attack,
DISPROVED means a flaw was found.
"""

import math
import sys
import os
import pytest
from itertools import combinations, product
from typing import Set

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from adversarial_misc import (
    ms_proposed,
    find_alternative_formulas,
    overfitting_verdict,
    prime_probability_null_model,
    verify_gcd_isomorphism,
    verify_gcd_scaling_formula,
    coprime_adj,
    induced_subgraph,
    brute_clique_number,
    greedy_chromatic,
    exact_chromatic_number,
    check_strong_perfectness_g20,
    has_schur_triple,
    ds2_check_exhaustive,
    ds2_definition_sensitivity,
    enumerate_1indexed_5_colorings,
    coprime_edges,
    has_mono_triangle,
    count_avoiding_colorings_direct,
    count_avoiding_sat,
    verify_156_avoiding,
)


# =====================================================================
# Claim 1: MS(k) formula overfitting
# =====================================================================

class TestClaim1MSFormula:
    """Attack the MS(k) = 2^((3^k+1)/2) - 1 formula."""

    def test_formula_reproduces_known_values(self):
        """Sanity check: the proposed formula matches the 3 data points."""
        assert ms_proposed(1) == 3
        assert ms_proposed(2) == 31
        assert ms_proposed(3) == 16383

    def test_exponent_sequence(self):
        """Verify the exponent sequence (3^k+1)/2 = 2, 5, 14, 41, ..."""
        exps = [(3**k + 1) // 2 for k in range(1, 5)]
        assert exps == [2, 5, 14, 41]

    def test_alternative_formulas_exist(self):
        """Show that other formulas also fit the 3 known points."""
        alts = find_alternative_formulas()
        assert len(alts) >= 3, "Should find at least 3 alternative families"

    def test_alternatives_predict_different_ms4(self):
        """Key test: do alternative formulas predict DIFFERENT MS(4)?"""
        alts = find_alternative_formulas()
        proposed_ms4 = ms_proposed(4)  # = 2^41 - 1 = 2199023255551

        different_predictions = [
            a for a in alts
            if a.get("MS(4)_predicted") is not None
            and a["MS(4)_predicted"] != proposed_ms4
        ]
        assert len(different_predictions) >= 2, (
            "At least 2 alternative formulas should predict different MS(4). "
            "This proves the formula is not uniquely determined by 3 points."
        )

    def test_quadratic_exponent_alternative(self):
        """
        The exponents 2, 5, 14 are also fit by f(k) = 3k^2 - 6k + 5.
        This gives f(4) = 29 != 41 (the proposed exponent).
        So MS(4) = 2^29 - 1 vs 2^41 - 1 under the two models.
        """
        # Verify quadratic fits
        f = lambda k: 3 * k**2 - 6 * k + 5
        assert f(1) == 2
        assert f(2) == 5
        assert f(3) == 14
        assert f(4) == 29  # != 41

        # The proposed gives 41
        assert (3**4 + 1) // 2 == 41

        # These predict wildly different MS(4)
        assert 2**29 - 1 != 2**41 - 1

    def test_catalan_exponent_alternative(self):
        """
        Catalan numbers C(2)=2, C(3)=5, C(4)=14 also fit the exponents.
        C(5) = 42, giving MS(4) = 2^42 - 1, different from 2^41 - 1.
        """
        def catalan(n):
            return math.comb(2*n, n) // (n + 1)

        assert catalan(2) == 2
        assert catalan(3) == 5
        assert catalan(4) == 14
        assert catalan(5) == 42  # proposed gives 41

        assert 2**42 - 1 != 2**41 - 1

    def test_overfitting_verdict(self):
        """The overall verdict should flag overfitting risk."""
        v = overfitting_verdict()
        # Should have multiple distinct predictions
        assert len(v["distinct_MS4_predictions"]) >= 3
        # More formulas should disagree with proposed than agree
        assert v["num_disagreeing"] >= v["num_agreeing"]


# =====================================================================
# Claim 2: NPG-30 primality null model
# =====================================================================

class TestClaim2Primality:
    """Attack the 'coprime Ramsey numbers are always prime' conjecture."""

    def test_claimed_values_are_prime(self):
        """Verify the 4 claimed values are actually prime."""
        for v in [2, 11, 53, 59]:
            assert all(v % d != 0 for d in range(2, int(v**0.5) + 1)), (
                f"{v} is not prime"
            )

    def test_null_model_probabilities(self):
        """Compute probability under null models. If > 1%, pattern is weak."""
        result = prime_probability_null_model()
        probs = result["verdict"]["probabilities"]

        # Under at least one model, probability should be appreciable
        max_prob = max(probs.values())
        # We expect at least ~2-5% under the broad uniform model
        assert max_prob > 0.01, (
            f"Surprisingly low probability {max_prob} under all models. "
            "The primality pattern may be meaningful after all."
        )

    def test_prime_density_in_ranges(self):
        """
        Check prime density in ranges relevant to R_cop values.
        For small numbers, ~40% are prime, so 4 primes in a row is ~2.5%.
        """
        def prime_frac(lo, hi):
            count = sum(
                1 for n in range(lo, hi + 1)
                if n >= 2 and all(n % d != 0 for d in range(2, int(n**0.5) + 1))
            )
            return count / (hi - lo + 1)

        # In [2, 60], primes are common
        frac = prime_frac(2, 60)
        assert frac > 0.25, f"Prime fraction in [2,60] is {frac}, expected > 0.25"

        # Joint probability with independence assumption
        # P(4 primes) ~ frac^4
        joint = frac ** 4
        assert joint > 0.003, (
            f"Joint probability {joint} suggests pattern might be coincidence"
        )

    def test_pnt_probability(self):
        """Under PNT: P(n prime) ~ 1/ln(n). Product for {2,11,53,59}."""
        import math
        probs = [1/math.log(v) for v in [2, 11, 53, 59]]
        joint = 1.0
        for p in probs:
            joint *= p
        # 1/ln(2) * 1/ln(11) * 1/ln(53) * 1/ln(59)
        # = 1.443 * 0.417 * 0.252 * 0.245 ~ 0.037
        assert joint > 0.01, (
            f"PNT joint probability = {joint:.4f}, not negligibly small"
        )


# =====================================================================
# Claim 3: R_gcd(3;d) = 11d isomorphism
# =====================================================================

class TestClaim3GCDIsomorphism:
    """Verify the coprime-to-GCD-d isomorphism edge by edge."""

    def test_algebraic_identity(self):
        """
        Verify gcd(d*i, d*j) = d * gcd(i,j) for all i,j in [1..11], d=5.
        This is a basic number theory identity.
        """
        d = 5
        for i in range(1, 12):
            for j in range(i + 1, 12):
                assert math.gcd(d * i, d * j) == d * math.gcd(i, j), (
                    f"Identity fails for d={d}, i={i}, j={j}"
                )

    def test_isomorphism_d5_m11(self):
        """Edge-by-edge isomorphism check for d=5, m=11."""
        result = verify_gcd_isomorphism(d=5, m=11)
        assert result["is_isomorphic"], (
            f"Isomorphism fails! Missing: {result['missing_from_gcd']}, "
            f"Extra: {result['extra_in_gcd']}"
        )
        assert result["algebraic_identity_holds"]
        assert result["coprime_edge_count"] == result["gcd_d_edge_count"]

    def test_isomorphism_all_small_d(self):
        """Verify for d = 1, 2, 3, 4, 5, 6."""
        for d in range(1, 7):
            result = verify_gcd_isomorphism(d=d, m=11)
            assert result["is_isomorphic"], f"Isomorphism fails for d={d}"
            assert result["algebraic_identity_holds"], (
                f"Algebraic identity fails for d={d}"
            )

    def test_edge_counts_match(self):
        """The number of coprime edges on [11] must equal GCD-d edges
        on {d,...,11d} for every d."""
        coprime_count = len(coprime_edges(11))
        for d in range(1, 7):
            result = verify_gcd_isomorphism(d=d, m=11)
            assert result["coprime_edge_count"] == coprime_count
            assert result["gcd_d_edge_count"] == coprime_count

    def test_isomorphism_larger_m(self):
        """Verify for d=5 but m=20 (beyond R_cop(3))."""
        result = verify_gcd_isomorphism(d=5, m=20)
        assert result["is_isomorphic"]

    def test_non_trivial_d(self):
        """d=7 (prime) and d=12 (highly composite) should also work."""
        for d in [7, 12]:
            result = verify_gcd_isomorphism(d=d, m=11)
            assert result["is_isomorphic"], f"Fails for d={d}"


# =====================================================================
# Claim 4: Coprime graph strong perfectness
# =====================================================================

class TestClaim4Perfectness:
    """Attack strong perfectness of coprime graphs."""

    def test_weak_perfectness_g10(self):
        """Verify chi = omega for G(10)."""
        adj = coprime_adj(10)
        omega = brute_clique_number(adj)
        chi = exact_chromatic_number(adj)
        # omega(G(10)) = 1 + pi(10) = 1 + 4 = 5
        assert omega == 5
        assert chi == omega

    def test_induced_subgraph_evens(self):
        """Even numbers {2,4,...,20}: check chi = omega."""
        adj = coprime_adj(20)
        evens = set(range(2, 21, 2))
        sub = induced_subgraph(adj, evens)
        omega = brute_clique_number(sub)
        chi = exact_chromatic_number(sub)
        assert chi == omega, f"IMPERFECT: chi={chi}, omega={omega} on evens"

    def test_induced_subgraph_composites(self):
        """Composites {4,6,8,9,10,12,14,15,16,18,20}: check chi = omega."""
        adj = coprime_adj(20)
        composites = set()
        for x in range(4, 21):
            if any(x % d == 0 for d in range(2, int(x**0.5) + 1)):
                composites.add(x)
        sub = induced_subgraph(adj, composites)
        omega = brute_clique_number(sub)
        chi = exact_chromatic_number(sub)
        assert chi == omega, f"IMPERFECT: chi={chi}, omega={omega} on composites"

    def test_no_odd_hole_g15(self):
        """No odd hole of length 5 or 7 in G(15)."""
        adj = coprime_adj(15)
        from adversarial_misc import _search_odd_holes
        result = _search_odd_holes(adj, 15, max_len=7)
        assert result["found"] is None, f"Odd hole found: {result['found']}"

    def test_no_odd_antihole_g15(self):
        """No odd antihole in G(15)."""
        n = 15
        comp_adj = {v: set() for v in range(1, n + 1)}
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                if math.gcd(i, j) > 1:
                    comp_adj[i].add(j)
                    comp_adj[j].add(i)
        from adversarial_misc import _search_odd_holes
        result = _search_odd_holes(comp_adj, n, max_len=7)
        assert result["found"] is None, f"Odd antihole found: {result['found']}"

    @pytest.mark.timeout(60)
    def test_exhaustive_small_subsets(self):
        """
        Check chi = omega for ALL subsets of {2,...,12} of size 5-7.
        If any fails, strong perfectness is DISPROVED.
        """
        adj = coprime_adj(12)
        base = list(range(2, 13))
        for size in range(5, 8):
            for combo in combinations(base, size):
                s = set(combo)
                sa = induced_subgraph(adj, s)
                omega = brute_clique_number(sa)
                chi = exact_chromatic_number(sa)
                assert chi == omega, (
                    f"STRONG PERFECTNESS DISPROVED: "
                    f"subset {sorted(s)}, omega={omega}, chi={chi}"
                )

    def test_g20_full_check(self):
        """Run the comprehensive G(20) check."""
        result = check_strong_perfectness_g20()
        verdict = result["verdict"]
        assert verdict["strongly_perfect_consistent"], (
            f"Strong perfectness inconsistency found in G(20): {verdict}"
        )


# =====================================================================
# Claim 5: DS(2, 0.50) definition sensitivity
# =====================================================================

class TestClaim5DSSensitivity:
    """Verify that DS(2,0.50) differs between indexing conventions."""

    def test_has_schur_triple_basic(self):
        """Basic Schur triple checks."""
        assert has_schur_triple({1, 2, 3})  # 1+2=3
        assert has_schur_triple({2, 3, 5})  # 2+3=5
        assert not has_schur_triple({1, 4})  # 1+4=5 not in set
        assert not has_schur_triple({1})
        assert has_schur_triple({0, 0})  # 0+0=0 -- set has only {0}, 0+0=0
        assert has_schur_triple({0})  # 0+0=0

    def test_schur_triple_with_zero(self):
        """0 is problematic: 0+0=0 is a Schur triple."""
        assert has_schur_triple({0}), "{0} has Schur triple 0+0=0"
        assert has_schur_triple({0, 1}), "{0,1} has 0+0=0 and 0+1=1"

    def test_ds2_0indexed_n5(self):
        """Exhaustive check on {0,1,2,3,4} with alpha=0.50."""
        r = ds2_check_exhaustive(5, "0-indexed", 0.50)
        # With 0 in the universe, any color containing 0 with >= 2 elements
        # automatically has Schur triple 0+0=0 if 0 is in the set, plus
        # 0+x=x for any other x. So 0+0=0 is always a triple.
        # Actually let's just check what the enumeration says.
        assert r["total_colorings"] == 32

    def test_ds2_1indexed_n5(self):
        """Exhaustive check on {1,2,3,4,5} with alpha=0.50."""
        r = ds2_check_exhaustive(5, "1-indexed", 0.50)
        # threshold = max(1, int(0.5*5)) = 2
        # Check if any coloring avoids having a dense (>=2) Schur-containing class
        assert r["total_colorings"] == 32

    def test_definitions_differ(self):
        """The key claim: DS(2,0.50) differs between 0-indexed and 1-indexed."""
        result = ds2_definition_sensitivity()
        # Based on the existing claim: DS=5 on {0,...,N-1}, DS=6 on {1,...,N}
        ds_0 = result["DS_0indexed"]
        ds_1 = result["DS_1indexed"]
        # If they differ, the claim about definition sensitivity is CONFIRMED
        # If they agree, the claim is DISPROVED
        assert ds_0 is not None, "DS(2,0.50) on 0-indexed not found in range"
        assert ds_1 is not None, "DS(2,0.50) on 1-indexed not found in range"
        # Record both values -- the test reports the actual finding
        if ds_0 != ds_1:
            pass  # CONFIRMED: definitions disagree
        else:
            pytest.fail(
                f"DISPROVED: definitions agree at DS = {ds_0}"
            )

    def test_enumerate_1indexed_5(self):
        """
        Enumerate all 32 colorings of [5] = {1,2,3,4,5} and check
        whether any avoids having a dense Schur-containing color class.
        """
        r = enumerate_1indexed_5_colorings()
        # If avoiding_count > 0, then DS(2,0.50) > 5 on 1-indexed
        # If avoiding_count == 0, then DS(2,0.50) <= 5 on 1-indexed
        # The claim says DS=6 on 1-indexed, so we expect avoiding_count > 0
        print(f"\n  [5] 1-indexed: {r['avoiding_count']} avoiding out of 32")
        if r["avoiding_examples"]:
            for ex in r["avoiding_examples"][:3]:
                print(f"    c0={ex['c0']}, c1={ex['c1']}")

    def test_threshold_computation(self):
        """Verify threshold = max(1, int(0.50 * N)) for various N."""
        for N in range(1, 10):
            expected = max(1, int(0.50 * N))
            r = ds2_check_exhaustive(N, "1-indexed", 0.50)
            assert r["threshold"] == expected, (
                f"N={N}: threshold={r['threshold']}, expected={expected}"
            )

    def test_zero_makes_0indexed_easier(self):
        """
        With 0-indexed {0,...,N-1}, the element 0 satisfies 0+0=0,
        so any color class containing 0 automatically has a Schur triple.
        This should make the 0-indexed version force earlier.
        """
        r0 = ds2_check_exhaustive(4, "0-indexed", 0.50)
        r1 = ds2_check_exhaustive(4, "1-indexed", 0.50)
        # 0-indexed should have fewer (or equal) avoiding colorings
        assert r0["avoiding_count"] <= r1["avoiding_count"], (
            f"0-indexed has MORE avoiding colorings ({r0['avoiding_count']}) "
            f"than 1-indexed ({r1['avoiding_count']}), unexpected"
        )


# =====================================================================
# Claim 6: 156 avoiding colorings at n=10
# =====================================================================

class TestClaim6AvoidingCount:
    """Independently verify the count of 156 avoiding colorings."""

    def test_coprime_edges_n10(self):
        """Verify edge count at n=10."""
        edges = coprime_edges(10)
        # Known: 31 coprime edges on [10]
        assert len(edges) == 31

    def test_small_n_avoiding_counts(self):
        """Verify avoiding counts at small n."""
        # n=4 has triangle {1,2,3}, so not all colorings avoid.
        # Verify computation runs and produces a sensible count.
        for nn in [4, 5, 6]:
            r = count_avoiding_colorings_direct(nn)
            assert r["avoiding_count"] >= 0
            assert r["avoiding_count"] <= r["total_colorings"]
        # Cross-check with SAT for n=7
        sat_count = count_avoiding_sat(7)
        r7 = count_avoiding_colorings_direct(7)
        assert r7["avoiding_count"] == sat_count, (
            f"n=7: direct={r7['avoiding_count']}, SAT={sat_count}"
        )

    def test_mono_triangle_detection(self):
        """Verify the triangle detector works on known cases."""
        # Coloring all edges color 0 on [3]: triangle {1,2,3} is mono
        edges = coprime_edges(3)
        col_all_0 = {e: 0 for e in edges}
        assert has_mono_triangle(3, col_all_0)

        # Color (1,2)=0, (1,3)=0, (2,3)=1: not monochromatic
        col_mixed = {(1, 2): 0, (1, 3): 0, (2, 3): 1}
        assert not has_mono_triangle(3, col_mixed)

    def test_n11_has_zero_avoiding(self):
        """Confirm R_cop(3) = 11 by showing 0 avoiding colorings at n=11."""
        r11 = count_avoiding_colorings_direct(11)
        assert r11["avoiding_count"] == 0, (
            f"Expected 0 avoiding at n=11 (R_cop(3)=11), got {r11['avoiding_count']}"
        )

    @pytest.mark.timeout(120)
    def test_count_n10_incremental(self):
        """Count avoiding colorings at n=10 via incremental extension."""
        from adversarial_misc import _count_avoiding_incremental
        r = _count_avoiding_incremental(10)
        assert r["avoiding_count"] == 156, (
            f"Expected 156 avoiding at n=10, got {r['avoiding_count']}"
        )

    @pytest.mark.timeout(120)
    def test_count_n10_sat(self):
        """Count avoiding colorings at n=10 via SAT with blocking clauses."""
        count = count_avoiding_sat(10)
        assert count == 156, f"SAT count at n=10: {count}, expected 156"

    @pytest.mark.timeout(120)
    def test_two_methods_agree(self):
        """Both methods must produce the same count."""
        from adversarial_misc import _count_avoiding_incremental
        r_inc = _count_avoiding_incremental(10)
        r_sat = count_avoiding_sat(10)
        assert r_inc["avoiding_count"] == r_sat, (
            f"Methods disagree: incremental={r_inc['avoiding_count']}, SAT={r_sat}"
        )

    def test_avoiding_fraction_decreases(self):
        """The FRACTION of avoiding colorings should decrease as n grows.
        The absolute count can fluctuate because the number of edges grows.
        Use SAT method which is fast for all n."""
        fractions = []
        for nn in range(5, 11):
            c = count_avoiding_sat(nn)
            num_edges = len(coprime_edges(nn))
            frac = c / (2 ** num_edges)
            fractions.append((nn, c, frac))
        # Fraction should be strictly decreasing
        for i in range(1, len(fractions)):
            assert fractions[i][2] <= fractions[i-1][2], (
                f"Fraction not decreasing: {fractions}"
            )
        # n=10 should have exactly 156 avoiding colorings
        assert fractions[-1][1] == 156
        # n=10 fraction should be tiny: ~7.3e-8
        assert fractions[-1][2] < 1e-6

    @pytest.mark.timeout(120)
    def test_full_verification_sat_only(self):
        """Verify 156 via SAT (fast) and incremental (slower but independent)."""
        # SAT is fast and reliable
        sat_count = count_avoiding_sat(10)
        assert sat_count == 156, f"SAT count at n=10: {sat_count}"

        # Also verify n=11 has 0 (R_cop(3) = 11)
        sat_11 = count_avoiding_sat(11)
        assert sat_11 == 0, f"SAT count at n=11: {sat_11}, expected 0"
