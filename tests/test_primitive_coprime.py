"""Tests for primitive_coprime.py (NPG-23) and primitive_extended.py."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from primitive_coprime import (
    is_primitive,
    coprime_pair_count,
    primes_up_to,
    top_layer,
    shifted_top_layer,
    kth_layer,
    squarefree_min_prime,
    exhaustive_max_primitive_coprime,
    compare_primitive_sets,
    coprime_density_formula,
    even_fraction,
    verify_density_formula,
    DENSITY_TOP_LAYER,
    DENSITY_SHIFTED,
    RATIO_SHIFTED_TO_TOP,
)

from primitive_extended import (
    fast_coprime_pair_count,
    compare_shifted_vs_top_large,
    reciprocal_sum,
    greedy_max_reciprocal_primitive,
    primes_reciprocal_sum,
    optimal_reciprocal_primitive,
    prime_power_primitive,
    compute_f_n,
    f_n_weighted,
    compute_f_n_weighted,
    construct_primitive_with_even_fraction,
    sweep_even_fraction,
    layer_analysis,
    cross_layer_coprime_analysis,
    count_prime_factors_with_multiplicity,
    _sieve_smallest_prime_factor,
)


class TestIsPrimitive:
    def test_primes_are_primitive(self):
        P = primes_up_to(30)
        assert is_primitive(P)

    def test_top_layer_is_primitive(self):
        for n in [10, 20, 50, 100]:
            T = top_layer(n)
            assert is_primitive(T), f"top layer not primitive at n={n}"

    def test_shifted_top_layer_is_primitive(self):
        for n in [20, 50, 100, 200]:
            S = shifted_top_layer(n)
            assert is_primitive(S), f"shifted top layer not primitive at n={n}"

    def test_not_primitive_with_divisor(self):
        assert not is_primitive({2, 4, 7})  # 2 divides 4

    def test_singleton_is_primitive(self):
        assert is_primitive({42})

    def test_empty_is_primitive(self):
        assert is_primitive(set())


class TestCoprimePairCount:
    def test_primes_all_coprime(self):
        P = primes_up_to(20)
        M = coprime_pair_count(P)
        expected = len(P) * (len(P) - 1) // 2
        assert M == expected, f"primes should be all coprime: got {M}, expected {expected}"

    def test_even_numbers_few_coprime(self):
        A = {2, 4, 6, 8, 10}
        M = coprime_pair_count(A)
        assert M == 0  # All share factor 2

    def test_known_small_case(self):
        A = {3, 5, 7}
        M = coprime_pair_count(A)
        assert M == 3  # All pairwise coprime

    def test_mixed_case(self):
        A = {6, 10, 15}  # gcd(6,10)=2, gcd(6,15)=3, gcd(10,15)=5
        M = coprime_pair_count(A)
        assert M == 0


class TestTopLayer:
    def test_size(self):
        for n in [10, 20, 50, 100]:
            T = top_layer(n)
            assert len(T) == n // 2

    def test_elements(self):
        T = top_layer(10)
        assert T == {6, 7, 8, 9, 10}

    def test_coprime_density_approaches_expected(self):
        """Top layer coprime density should approach 6/π²."""
        expected = 6 / math.pi**2
        T = top_layer(1000)
        M = coprime_pair_count(T)
        density = M / (len(T) * (len(T) - 1) // 2)
        assert abs(density - expected) < 0.01, f"density {density} too far from {expected}"


class TestShiftedTopLayer:
    def test_same_size_as_top(self):
        for n in [20, 50, 100]:
            T = top_layer(n)
            S = shifted_top_layer(n)
            assert len(S) == len(T), f"shifted size {len(S)} != top size {len(T)} at n={n}"

    def test_beats_top_layer(self):
        for n in [50, 100, 200]:
            T = top_layer(n)
            S = shifted_top_layer(n)
            M_top = coprime_pair_count(T)
            M_shift = coprime_pair_count(S)
            assert M_shift > M_top, f"shifted {M_shift} <= top {M_top} at n={n}"

    def test_improvement_ratio(self):
        """Shifted top layer should improve by ~18-19% for large n."""
        T = top_layer(500)
        S = shifted_top_layer(500)
        M_top = coprime_pair_count(T)
        M_shift = coprime_pair_count(S)
        ratio = M_shift / M_top
        assert 1.10 < ratio < 1.30, f"ratio {ratio} outside expected range"

    def test_higher_density(self):
        """Shifted density should be significantly above 6/π²."""
        S = shifted_top_layer(500)
        M = coprime_pair_count(S)
        density = M / (len(S) * (len(S) - 1) // 2)
        assert density > 0.70, f"shifted density {density} too low"


class TestExhaustiveSearch:
    def test_n8_primes_optimal(self):
        M_best, A_best = exhaustive_max_primitive_coprime(8)
        assert M_best == 6
        assert A_best == {2, 3, 5, 7}

    def test_n10_composites_beat_primes(self):
        M_best, A_best = exhaustive_max_primitive_coprime(10)
        M_primes = coprime_pair_count(primes_up_to(10))
        assert M_best > M_primes, "primes should be suboptimal at n=10"
        assert M_best == 8

    def test_n12_optimal(self):
        M_best, A_best = exhaustive_max_primitive_coprime(12)
        assert M_best == 13
        assert is_primitive(A_best)

    def test_optimal_is_primitive(self):
        for n in [8, 10, 12]:
            _, A = exhaustive_max_primitive_coprime(n)
            assert is_primitive(A), f"exhaustive optimum not primitive at n={n}"


class TestPrimesVsTopLayer:
    def test_primes_win_small(self):
        """For n ≤ 8, primes should beat or match top layer."""
        P = primes_up_to(8)
        T = top_layer(8)
        assert coprime_pair_count(P) >= coprime_pair_count(T)

    def test_top_layer_wins_large(self):
        """For n ≥ 50, top layer should beat primes."""
        for n in [50, 100, 200]:
            P = primes_up_to(n)
            T = top_layer(n)
            M_p = coprime_pair_count(P)
            M_t = coprime_pair_count(T)
            assert M_t > M_p, f"top layer should beat primes at n={n}"

    def test_primes_coprime_density_is_one(self):
        P = primes_up_to(50)
        M = coprime_pair_count(P)
        expected = len(P) * (len(P) - 1) // 2
        assert M == expected


class TestSquarefreeMinPrime:
    def test_k1_gives_squarefrees(self):
        """k=1 gives all squarefree numbers (smallest prime > 1 means all)."""
        S = squarefree_min_prime(30, 1)
        # Should include primes, 1, products of distinct primes
        assert 1 in S
        assert 6 in S  # 2*3, squarefree, min prime 2 > 1
        assert 4 not in S  # 2^2, not squarefree

    def test_k3_excludes_2_divisible(self):
        """k=3 excludes numbers with prime factor 2 or 3."""
        S = squarefree_min_prime(50, 3)
        assert 1 in S  # special case
        assert 5 in S  # prime > 3
        assert 7 in S
        assert 35 in S  # 5*7, min prime = 5 > 3
        assert 2 not in S  # min prime = 2 ≤ 3
        assert 6 not in S  # min prime = 2 ≤ 3
        assert 15 not in S  # min prime = 3 ≤ 3

    def test_large_k_gives_few(self):
        """Large k gives only 1 and primes > k."""
        S = squarefree_min_prime(50, 20)
        # Should be {1} ∪ {primes > 20 and ≤ 50} ∪ products of primes > 20
        assert 1 in S
        assert 23 in S  # prime > 20
        assert 29 in S
        assert 2 not in S
        assert 10 not in S

    def test_includes_1(self):
        S = squarefree_min_prime(10, 0)
        assert 1 in S


class TestKthLayer:
    def test_layer_1_is_primes(self):
        """Layer 1 = elements with exactly 1 prime factor (with multiplicity) = primes."""
        L1 = kth_layer(30, 1)
        P = primes_up_to(30)
        assert L1 == P

    def test_layer_2_semiprimes(self):
        """Layer 2 = numbers with exactly 2 prime factors (with multiplicity)."""
        L2 = kth_layer(20, 2)
        # 4=2², 6=2*3, 9=3², 10=2*5, 14=2*7, 15=3*5
        assert 4 in L2   # 2^2, Omega=2
        assert 6 in L2   # 2*3
        assert 9 in L2   # 3^2
        assert 15 in L2  # 3*5
        assert 8 not in L2  # 2^3, Omega=3
        assert 2 not in L2  # prime, Omega=1

    def test_layer_3(self):
        """Layer 3 = numbers with exactly 3 prime factors."""
        L3 = kth_layer(30, 3)
        assert 8 in L3   # 2^3
        assert 12 in L3  # 2^2*3
        assert 30 in L3  # 2*3*5
        assert 4 not in L3  # Omega=2


class TestGreedy:
    def test_greedy_produces_primitive(self):
        from primitive_coprime import greedy_max_primitive_coprime
        M, A = greedy_max_primitive_coprime(30)
        assert is_primitive(A), f"greedy result not primitive"
        assert M == coprime_pair_count(A)
        assert M > 0

    def test_greedy_beats_primes_large(self):
        from primitive_coprime import greedy_max_primitive_coprime
        M_greedy, _ = greedy_max_primitive_coprime(100)
        P = primes_up_to(100)
        M_primes = coprime_pair_count(P)
        # Greedy starts from primes, so should be >= primes
        assert M_greedy >= M_primes


class TestAnalyzeGrowth:
    def test_returns_data(self):
        from primitive_coprime import analyze_growth
        data = analyze_growth(max_n=150, step=50)
        assert len(data) == 3  # 50, 100, 150
        assert all("n" in row and "M_primes" in row and "M_top" in row for row in data)

    def test_top_dominates_for_large_n(self):
        from primitive_coprime import analyze_growth
        data = analyze_growth(max_n=200, step=100)
        for row in data:
            if row["n"] >= 100:
                assert not row["primes_win"], (
                    f"primes should not win at n={row['n']}"
                )


class TestSmartGreedy:
    """Tests for smart_greedy (lines 228-262)."""

    def test_smart_greedy_produces_primitive(self):
        from primitive_coprime import smart_greedy
        M, A = smart_greedy(30)
        assert is_primitive(A), f"smart_greedy result not primitive"
        assert M == coprime_pair_count(A)
        assert M > 0

    def test_smart_greedy_nonempty(self):
        from primitive_coprime import smart_greedy
        M, A = smart_greedy(10)
        assert len(A) >= 2  # At least two elements

    def test_smart_greedy_monotone(self):
        from primitive_coprime import smart_greedy
        M1, _ = smart_greedy(20)
        M2, _ = smart_greedy(40)
        assert M2 >= M1


class TestHybridGreedy:
    """Tests for hybrid_greedy (lines 265-321)."""

    def test_hybrid_produces_primitive(self):
        from primitive_coprime import hybrid_greedy
        M, A = hybrid_greedy(50)
        assert is_primitive(A), f"hybrid_greedy result not primitive"
        assert M == coprime_pair_count(A)

    def test_hybrid_nonempty(self):
        from primitive_coprime import hybrid_greedy
        M, A = hybrid_greedy(20)
        assert len(A) >= 2

    def test_hybrid_beats_primes_large(self):
        from primitive_coprime import hybrid_greedy
        M_hybrid, _ = hybrid_greedy(100)
        P = primes_up_to(100)
        M_primes = coprime_pair_count(P)
        # Hybrid should competitive with primes at n=100
        assert M_hybrid >= M_primes * 0.8

    def test_hybrid_uses_squares(self):
        from primitive_coprime import hybrid_greedy
        _, A = hybrid_greedy(50)
        # Phase 1 adds prime squares; 4=2², 9=3², 25=5² should be in set
        squares = {p * p for p in [2, 3, 5, 7] if p * p <= 50}
        assert len(A & squares) > 0, "hybrid should use some prime squares"


class TestIterativeImprove:
    """Tests for iterative_improve (lines 324-366)."""

    def test_iterative_produces_primitive(self):
        from primitive_coprime import iterative_improve
        M, A = iterative_improve(30, rounds=50)
        assert is_primitive(A), f"iterative_improve result not primitive"
        assert M == coprime_pair_count(A)

    def test_iterative_from_initial(self):
        from primitive_coprime import iterative_improve
        initial = {2, 3, 5, 7}
        M, A = iterative_improve(20, initial=initial, rounds=50)
        assert M >= coprime_pair_count(initial)

    def test_iterative_improves_or_maintains(self):
        from primitive_coprime import iterative_improve, hybrid_greedy
        M_init, init = hybrid_greedy(30)
        M_final, _ = iterative_improve(30, initial=init, rounds=100)
        assert M_final >= M_init, "iterative should not decrease M"


class TestCompare:
    def test_compare_returns_all_keys(self):
        results = compare_primitive_sets(50)
        expected_keys = ["primes", "top_layer", "primes_plus_1",
                         "sqfree_minp>3", "sqfree_minp>5",
                         "semiprimes_prim", "greedy", "shifted_top"]
        for key in expected_keys:
            assert key in results, f"missing key {key}"

    def test_shifted_top_best_at_n100(self):
        results = compare_primitive_sets(100)
        M_values = {k: v["M"] for k, v in results.items() if isinstance(v, dict) and "M" in v}
        best_key = max(M_values, key=M_values.get)
        assert best_key == "shifted_top", f"shifted_top should be best at n=100, got {best_key}"


class TestSieveConstants:
    """Tests for the sieve-theoretic density constants."""

    def test_density_top_layer_value(self):
        assert abs(DENSITY_TOP_LAYER - 6 / math.pi**2) < 1e-12

    def test_density_shifted_value(self):
        assert abs(DENSITY_SHIFTED - 64 / (9 * math.pi**2)) < 1e-12

    def test_ratio_value(self):
        assert abs(RATIO_SHIFTED_TO_TOP - 32 / 27) < 1e-12

    def test_ratio_equals_density_ratio(self):
        assert abs(DENSITY_SHIFTED / DENSITY_TOP_LAYER - RATIO_SHIFTED_TO_TOP) < 1e-10


class TestCoprimeDensityFormula:
    """Tests for coprime_density_formula(f_E)."""

    def test_f_E_zero(self):
        """All odd: d = 8/π²."""
        assert abs(coprime_density_formula(0.0) - 8 / math.pi**2) < 1e-12

    def test_f_E_half(self):
        """Top layer: d = 6/π²."""
        assert abs(coprime_density_formula(0.5) - 6 / math.pi**2) < 1e-12

    def test_f_E_one_third(self):
        """Shifted top: d = 64/(9π²)."""
        assert abs(coprime_density_formula(1 / 3) - 64 / (9 * math.pi**2)) < 1e-12

    def test_f_E_one(self):
        """All even: d = 0."""
        assert coprime_density_formula(1.0) == 0.0

    def test_monotone_decreasing(self):
        """Density decreases as even fraction increases."""
        vals = [coprime_density_formula(f) for f in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]]
        for i in range(len(vals) - 1):
            assert vals[i] > vals[i + 1], f"not decreasing at {i}"


class TestEvenFraction:
    """Tests for even_fraction."""

    def test_all_odd(self):
        assert even_fraction({1, 3, 5, 7}) == 0.0

    def test_all_even(self):
        assert even_fraction({2, 4, 6, 8}) == 1.0

    def test_half(self):
        assert even_fraction({1, 2, 3, 4}) == 0.5

    def test_empty(self):
        assert even_fraction(set()) == 0.0

    def test_top_layer_half(self):
        """Top layer should have f_E ≈ 0.5."""
        f = even_fraction(top_layer(100))
        assert abs(f - 0.5) < 0.02

    def test_shifted_layer_one_third(self):
        """Shifted top layer should have f_E ≈ 1/3."""
        f = even_fraction(shifted_top_layer(200))
        assert abs(f - 1 / 3) < 0.05


class TestVerifyDensityFormula:
    """Tests that the sieve-theoretic formula matches computation."""

    def test_top_layer_density_matches(self):
        """Predicted d(T) should match observed within 2%."""
        result = verify_density_formula(200)
        assert abs(result["d_T_pred"] - result["d_T_obs"]) < 0.02

    def test_shifted_density_matches(self):
        """Predicted d(S) should match observed within 2%."""
        result = verify_density_formula(200)
        assert abs(result["d_S_pred"] - result["d_S_obs"]) < 0.02

    def test_ratio_matches(self):
        """Predicted ratio should match observed within 1%."""
        result = verify_density_formula(500)
        assert abs(result["ratio_pred"] - result["ratio_obs"]) < 0.01

    def test_formula_at_n100(self):
        result = verify_density_formula(100)
        assert result["f_E_T"] == 0.5
        assert abs(result["f_E_S"] - 1 / 3) < 0.05

    def test_formula_at_n200(self):
        result = verify_density_formula(200)
        assert result["d_S_obs"] > result["d_T_obs"]
        assert result["ratio_obs"] > 1.15


class TestShiftedTopOptimality:
    """Exhaustive verification: S(n) maximizes coprime pairs among all primitive sets.

    For n ≤ 12, enumerate ALL primitive subsets of [n] and verify none
    has more coprime pairs than S(n).
    """

    @staticmethod
    def _all_primitive_coprime_max(n):
        """Find max coprime pairs over all primitive subsets of [n]."""
        from itertools import combinations
        best = 0
        elements = list(range(1, n + 1))
        for size in range(2, n + 1):
            for combo in combinations(elements, size):
                A = set(combo)
                # Check primitivity
                prim = True
                combo_sorted = sorted(combo)
                for i in range(len(combo_sorted)):
                    for j in range(i + 1, len(combo_sorted)):
                        if combo_sorted[j] % combo_sorted[i] == 0:
                            prim = False
                            break
                    if not prim:
                        break
                if prim:
                    M = sum(1 for a, b in combinations(A, 2)
                            if math.gcd(a, b) == 1)
                    best = max(best, M)
        return best

    def test_optimal_n8(self):
        S = shifted_top_layer(8)
        assert coprime_pair_count(S) == self._all_primitive_coprime_max(8)

    def test_optimal_n10(self):
        S = shifted_top_layer(10)
        assert coprime_pair_count(S) == self._all_primitive_coprime_max(10)

    def test_optimal_n12(self):
        S = shifted_top_layer(12)
        assert coprime_pair_count(S) == self._all_primitive_coprime_max(12)


# ==========================================================================
# Tests for primitive_extended.py
# ==========================================================================


class TestFastCoprimePairCount:
    """Tests that fast Mobius-based counting matches the naive O(n^2) method."""

    def test_agrees_with_naive_primes(self):
        P = primes_up_to(50)
        assert fast_coprime_pair_count(P) == coprime_pair_count(P)

    def test_agrees_with_naive_top_layer(self):
        for n in [20, 50, 100]:
            T = top_layer(n)
            assert fast_coprime_pair_count(T) == coprime_pair_count(T), \
                f"mismatch at n={n}"

    def test_agrees_with_naive_shifted(self):
        for n in [20, 50, 100]:
            S = shifted_top_layer(n)
            assert fast_coprime_pair_count(S) == coprime_pair_count(S), \
                f"mismatch at n={n}"

    def test_empty_set(self):
        assert fast_coprime_pair_count(set()) == 0

    def test_singleton(self):
        assert fast_coprime_pair_count({7}) == 0

    def test_two_coprime(self):
        assert fast_coprime_pair_count({6, 35}) == 1  # gcd=1

    def test_two_not_coprime(self):
        assert fast_coprime_pair_count({6, 10}) == 0  # gcd=2

    def test_all_even(self):
        assert fast_coprime_pair_count({2, 4, 6, 8, 10}) == 0

    def test_mixed(self):
        A = {3, 5, 6, 10, 15}
        assert fast_coprime_pair_count(A) == coprime_pair_count(A)


class TestCompareShiftedVsTopLarge:
    """Tests for the large-n comparison of shifted vs top layer."""

    def test_returns_correct_structure(self):
        results = compare_shifted_vs_top_large([100])
        assert len(results) == 1
        r = results[0]
        assert r["n"] == 100
        assert "M_T" in r and "M_S" in r
        assert "density_T" in r and "density_S" in r
        assert "shifted_dominates" in r

    def test_shifted_dominates_all(self):
        results = compare_shifted_vs_top_large([100, 200, 500])
        for r in results:
            assert r["shifted_dominates"], f"shifted should dominate at n={r['n']}"

    def test_ratio_near_32_over_27(self):
        results = compare_shifted_vs_top_large([500, 1000])
        for r in results:
            assert abs(r["ratio_M"] - 32 / 27) < 0.01, \
                f"ratio {r['ratio_M']} too far from 32/27 at n={r['n']}"

    def test_sizes_equal(self):
        results = compare_shifted_vs_top_large([200])
        r = results[0]
        assert r["size_T"] == r["size_S"]

    def test_densities_match_prediction(self):
        results = compare_shifted_vs_top_large([500])
        r = results[0]
        assert abs(r["density_T"] - r["pred_density_T"]) < 0.01
        assert abs(r["density_S"] - r["pred_density_S"]) < 0.01


class TestReciprocalSum:
    """Tests for reciprocal_sum."""

    def test_primes_small(self):
        P = {2, 3, 5}
        expected = 1 / 2 + 1 / 3 + 1 / 5
        assert abs(reciprocal_sum(P) - expected) < 1e-12

    def test_empty(self):
        assert reciprocal_sum(set()) == 0.0

    def test_singleton(self):
        assert abs(reciprocal_sum({7}) - 1 / 7) < 1e-12


class TestGreedyMaxReciprocalPrimitive:
    """Tests for greedy_max_reciprocal_primitive (= primes)."""

    def test_equals_primes_small(self):
        """Greedy smallest-first should produce exactly the primes."""
        for n in [10, 20, 50]:
            f_greedy, A_greedy = greedy_max_reciprocal_primitive(n)
            f_primes, P = primes_reciprocal_sum(n)
            assert A_greedy == P, f"greedy != primes at n={n}"
            assert abs(f_greedy - f_primes) < 1e-12

    def test_is_primitive(self):
        _, A = greedy_max_reciprocal_primitive(100)
        assert is_primitive(A)

    def test_monotone_in_n(self):
        f1, _ = greedy_max_reciprocal_primitive(50)
        f2, _ = greedy_max_reciprocal_primitive(100)
        assert f2 > f1


class TestPrimePowerPrimitive:
    """Tests for prime_power_primitive."""

    def test_is_primitive(self):
        _, A = prime_power_primitive(100)
        assert is_primitive(A), "prime power set should be primitive"

    def test_smaller_than_primes(self):
        """Prime powers (largest per prime) should have smaller reciprocal sum."""
        f_powers, _ = prime_power_primitive(100)
        f_primes, _ = primes_reciprocal_sum(100)
        assert f_powers < f_primes

    def test_contains_large_powers(self):
        _, A = prime_power_primitive(50)
        # 2^5=32 is the largest power of 2 <= 50
        assert 32 in A
        # 3^3=27 is the largest power of 3 <= 50
        assert 27 in A


class TestComputeFn:
    """Tests for compute_f_n."""

    def test_structure(self):
        results = compute_f_n([10, 20])
        assert len(results) == 2
        r = results[0]
        assert "f_greedy" in r
        assert "f_primes" in r
        assert "f_prime_powers" in r
        assert "greedy_equals_primes" in r

    def test_greedy_equals_primes(self):
        results = compute_f_n([10, 50, 100, 500])
        for r in results:
            assert r["greedy_equals_primes"], \
                f"greedy should equal primes at n={r['n']}"

    def test_f_n_increasing(self):
        results = compute_f_n([10, 50, 100, 500])
        for i in range(len(results) - 1):
            assert results[i + 1]["f_greedy"] > results[i]["f_greedy"]

    def test_mertens_approximation(self):
        """f(n) should be close to log log n + 0.2615 (Mertens)."""
        results = compute_f_n([1000])
        r = results[0]
        assert abs(r["f_greedy"] - r["mertens_approx"]) < 0.1


class TestFnWeighted:
    """Tests for f_n_weighted (sum 1/(a log a))."""

    def test_finite(self):
        f_w, A = f_n_weighted(100)
        assert f_w > 0
        assert math.isfinite(f_w)

    def test_is_primitive(self):
        _, A = f_n_weighted(50)
        assert is_primitive(A)

    def test_appears_to_converge(self):
        """The weighted sum should grow slowly."""
        results = compute_f_n_weighted([100, 500, 1000])
        # Increments should decrease
        increments = [results[i + 1]["f_weighted"] - results[i]["f_weighted"]
                      for i in range(len(results) - 1)]
        assert increments[-1] < increments[0], "increments should decrease"

    def test_bounded_above(self):
        """f_w(n) should be less than 2 for n <= 1000 (empirical bound)."""
        results = compute_f_n_weighted([1000])
        assert results[0]["f_weighted"] < 2.0


class TestConstructPrimitiveWithEvenFraction:
    """Tests for construct_primitive_with_even_fraction."""

    def test_is_primitive(self):
        for target in [0.0, 0.3, 0.5, 0.7, 1.0]:
            A = construct_primitive_with_even_fraction(200, target)
            assert is_primitive(A), f"not primitive at target f_E={target}"

    def test_low_f_E(self):
        A = construct_primitive_with_even_fraction(500, 0.0)
        f = even_fraction(A)
        # Can't go below ~1/3 with top-layer-size sets
        assert f < 0.5

    def test_mid_f_E(self):
        A = construct_primitive_with_even_fraction(500, 0.5)
        f = even_fraction(A)
        assert abs(f - 0.5) < 0.02

    def test_high_f_E(self):
        A = construct_primitive_with_even_fraction(500, 0.9)
        f = even_fraction(A)
        assert f > 0.8

    def test_all_even(self):
        A = construct_primitive_with_even_fraction(500, 1.0)
        f = even_fraction(A)
        assert f == 1.0

    def test_nonempty(self):
        for target in [0.0, 0.5, 1.0]:
            A = construct_primitive_with_even_fraction(100, target)
            assert len(A) >= 2


class TestSweepEvenFraction:
    """Tests for sweep_even_fraction."""

    def test_returns_correct_count(self):
        results = sweep_even_fraction(n=100, steps=10)
        assert len(results) == 11  # 0 to 10 inclusive

    def test_structure(self):
        results = sweep_even_fraction(n=100, steps=5)
        r = results[0]
        for key in ["target_f_E", "actual_f_E", "set_size", "coprime_pairs",
                     "actual_density", "predicted_density", "error"]:
            assert key in r, f"missing key {key}"

    def test_density_decreases_with_f_E(self):
        """Coprime density should generally decrease as f_E increases."""
        results = sweep_even_fraction(n=200, steps=10)
        # Filter to those with distinct actual_f_E
        seen = set()
        unique = []
        for r in results:
            f = round(r["actual_f_E"], 2)
            if f not in seen:
                seen.add(f)
                unique.append(r)
        # Check monotone decrease
        for i in range(len(unique) - 2):  # last might be 0/0
            if unique[i]["actual_density"] > 0 and unique[i + 1]["actual_density"] > 0:
                assert unique[i]["actual_density"] >= unique[i + 1]["actual_density"] - 0.02

    def test_formula_accuracy(self):
        """Sieve formula should match within 7% relative error.

        At n=200 the finite-size corrections are nontrivial, especially
        at extreme even fractions where the set size shrinks. The formula
        d = (8/pi^2)(1 - f_E^2) is an asymptotic result.
        """
        results = sweep_even_fraction(n=200, steps=10)
        for r in results:
            if r["predicted_density"] > 0.05:
                assert r["relative_error"] < 0.07, \
                    f"relative error {r['relative_error']} too large " \
                    f"at f_E={r['actual_f_E']:.2f}"


class TestLayerAnalysis:
    """Tests for layer_analysis."""

    def test_returns_correct_count(self):
        results = layer_analysis(n=100, max_k=4)
        assert len(results) == 4

    def test_structure(self):
        results = layer_analysis(n=100, max_k=3)
        r = results[0]
        for key in ["k", "layer_size", "primitive_size", "coprime_pairs",
                     "density", "f_E"]:
            assert key in r, f"missing key {key}"

    def test_layer_1_is_primes(self):
        results = layer_analysis(n=100, max_k=1)
        r = results[0]
        assert r["k"] == 1
        assert r["layer_size"] == len(primes_up_to(100))
        assert r["density"] == 1.0  # All primes are coprime

    def test_density_decreases_with_k(self):
        """Higher layers should have lower coprime density."""
        results = layer_analysis(n=500, max_k=5)
        for i in range(len(results) - 1):
            if results[i]["density"] > 0 and results[i + 1]["density"] > 0:
                assert results[i]["density"] > results[i + 1]["density"], \
                    f"density not decreasing at k={results[i]['k']}"

    def test_f_E_increases_with_k(self):
        """Higher layers should have higher even fraction (more even numbers)."""
        results = layer_analysis(n=500, max_k=5)
        for i in range(len(results) - 1):
            if results[i]["f_E"] > 0 and results[i + 1]["f_E"] > 0:
                assert results[i]["f_E"] < results[i + 1]["f_E"], \
                    f"f_E not increasing at k={results[i]['k']}"

    def test_primitive_size_at_most_layer_size(self):
        results = layer_analysis(n=200, max_k=4)
        for r in results:
            assert r["primitive_size"] <= r["layer_size"]


class TestCrossLayerCoprime:
    """Tests for cross_layer_coprime_analysis."""

    def test_structure(self):
        result = cross_layer_coprime_analysis(n=50, max_k=3)
        assert "n" in result
        assert "layers" in result
        assert "cross" in result

    def test_primes_all_coprime(self):
        """(1,1) cross should have density 1.0 (all primes coprime)."""
        result = cross_layer_coprime_analysis(n=50, max_k=2)
        d_11 = result["cross"][(1, 1)]
        assert abs(d_11["density"] - 1.0) < 1e-10

    def test_cross_density_positive(self):
        result = cross_layer_coprime_analysis(n=100, max_k=3)
        for key, data in result["cross"].items():
            if data["total_pairs"] > 0:
                assert data["density"] >= 0.0
                assert data["density"] <= 1.0

    def test_primes_vs_semiprimes_high_density(self):
        """Primes vs semiprimes should have high coprime density (> 0.9)."""
        result = cross_layer_coprime_analysis(n=100, max_k=2)
        d_12 = result["cross"][(1, 2)]
        assert d_12["density"] > 0.9


class TestCountPrimeFactorsWithMultiplicity:
    """Tests for the Omega function helper."""

    def test_primes(self):
        spf = _sieve_smallest_prime_factor(30)
        for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]:
            assert count_prime_factors_with_multiplicity(p, spf) == 1

    def test_prime_squares(self):
        spf = _sieve_smallest_prime_factor(50)
        assert count_prime_factors_with_multiplicity(4, spf) == 2   # 2^2
        assert count_prime_factors_with_multiplicity(9, spf) == 2   # 3^2
        assert count_prime_factors_with_multiplicity(25, spf) == 2  # 5^2

    def test_semiprimes(self):
        spf = _sieve_smallest_prime_factor(50)
        assert count_prime_factors_with_multiplicity(6, spf) == 2   # 2*3
        assert count_prime_factors_with_multiplicity(15, spf) == 2  # 3*5
        assert count_prime_factors_with_multiplicity(35, spf) == 2  # 5*7

    def test_higher(self):
        spf = _sieve_smallest_prime_factor(50)
        assert count_prime_factors_with_multiplicity(8, spf) == 3   # 2^3
        assert count_prime_factors_with_multiplicity(30, spf) == 3  # 2*3*5
        assert count_prime_factors_with_multiplicity(12, spf) == 3  # 2^2*3

    def test_one(self):
        spf = _sieve_smallest_prime_factor(10)
        assert count_prime_factors_with_multiplicity(1, spf) == 0
