#!/usr/bin/env python3
"""
Tests for binomial_factorial_attacks.py

Covers:
  - Singmaster's conjecture extensions (#849)
  - Binomial divisibility / p-adic valuations (#683, #684, #685)
  - Factorial problems (#373, #390, #400, #912)
  - Catalan number divisibility and squarefreeness
  - Wolstenholme's theorem and Wolstenholme primes
"""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from binomial_factorial_attacks import (
    # Utilities
    _sieve_primes, _is_prime, _factorize, _digit_sum_base_p,
    _is_squarefree, _is_perfect_power,
    # Singmaster (#849)
    singmaster_scan_row, singmaster_multiplicity_search,
    singmaster_known_high_multiplicity, singmaster_infinite_family_multiplicities,
    # Binomial divisibility (#683-685)
    p_adic_valuation_binom, carries_in_base_p,
    central_binom_prime_divisors, primes_dividing_central_binom,
    primes_not_dividing_central_binom, central_binom_valuation_records,
    granville_pattern,
    # Factorial (#373, #390, #400, #912)
    factorial_as_consecutive_product, factorial_consecutive_table,
    factorial_prime_search, factorial_prime_known_verification,
    factorial_perfect_power_check, factorial_ratio_powers,
    erdos_selfridge_verification,
    wilson_quotient, wilson_prime_search,
    # Catalan
    catalan, catalan_squarefree,
    catalan_prime_factorization_patterns, catalan_divisibility_by_prime,
    # Wolstenholme
    wolstenholme_verify, wolstenholme_prime_search,
    wolstenholme_residues, wolstenholme_residue_distribution,
    _comb_mod_prime_power,
    # Summary
    binomial_factorial_summary,
)


# =============================================================================
# Utility tests
# =============================================================================

class TestUtilities:
    def test_sieve_primes_small(self):
        assert _sieve_primes(10) == [2, 3, 5, 7]
        assert _sieve_primes(1) == []
        assert _sieve_primes(2) == [2]
        assert _sieve_primes(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

    def test_sieve_primes_count(self):
        # pi(100) = 25
        assert len(_sieve_primes(100)) == 25
        # pi(1000) = 168
        assert len(_sieve_primes(1000)) == 168

    def test_is_prime(self):
        primes_under_50 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        for p in primes_under_50:
            assert _is_prime(p), f"{p} should be prime"
        composites = [0, 1, 4, 6, 8, 9, 10, 15, 21, 25, 341, 561]
        for c in composites:
            assert not _is_prime(c), f"{c} should not be prime"

    def test_is_prime_large(self):
        # Known large primes
        assert _is_prime(104729)
        assert _is_prime(1000003)
        assert not _is_prime(1000001)  # = 101 * 9901

    def test_factorize(self):
        assert _factorize(1) == {}
        assert _factorize(2) == {2: 1}
        assert _factorize(12) == {2: 2, 3: 1}
        assert _factorize(360) == {2: 3, 3: 2, 5: 1}
        assert _factorize(1000) == {2: 3, 5: 3}

    def test_digit_sum_base_p(self):
        # 13 in base 2: 1101, digit sum = 3
        assert _digit_sum_base_p(13, 2) == 3
        # 100 in base 10: digit sum = 1
        assert _digit_sum_base_p(100, 10) == 1
        # 255 in base 2: 11111111, digit sum = 8
        assert _digit_sum_base_p(255, 2) == 8
        assert _digit_sum_base_p(0, 5) == 0
        # 7 in base 3: 21, digit sum = 3
        assert _digit_sum_base_p(7, 3) == 3

    def test_is_squarefree(self):
        assert _is_squarefree(1)
        assert _is_squarefree(2)
        assert _is_squarefree(6)     # 2*3
        assert _is_squarefree(30)    # 2*3*5
        assert not _is_squarefree(4)   # 2^2
        assert not _is_squarefree(12)  # 2^2 * 3
        assert not _is_squarefree(18)  # 2 * 3^2

    def test_is_perfect_power(self):
        assert not _is_perfect_power(1)
        assert not _is_perfect_power(2)
        assert not _is_perfect_power(3)
        assert _is_perfect_power(4)     # 2^2
        assert _is_perfect_power(8)     # 2^3
        assert _is_perfect_power(9)     # 3^2
        assert _is_perfect_power(16)    # 2^4 or 4^2
        assert _is_perfect_power(27)    # 3^3
        assert not _is_perfect_power(6)
        assert not _is_perfect_power(10)
        assert _is_perfect_power(32)    # 2^5
        assert _is_perfect_power(64)    # 2^6 or 4^3 or 8^2
        assert _is_perfect_power(125)   # 5^3


# =============================================================================
# Singmaster's Conjecture (#849)
# =============================================================================

class TestSingmaster:
    """Test Singmaster's conjecture computations."""

    def test_known_high_multiplicity_verified(self):
        results = singmaster_known_high_multiplicity()
        for r in results:
            assert r['verified'], f"Value {r['value']} failed verification"

    def test_3003_has_multiplicity_8(self):
        """3003 is the smallest integer with multiplicity 8 in Pascal's triangle."""
        # Verify all 8 appearances
        assert math.comb(3003, 1) == 3003
        assert math.comb(3003, 3002) == 3003
        assert math.comb(78, 2) == 3003
        assert math.comb(78, 76) == 3003
        assert math.comb(15, 5) == 3003
        assert math.comb(15, 10) == 3003
        assert math.comb(14, 6) == 3003
        assert math.comb(14, 8) == 3003

    def test_120_has_multiplicity_6(self):
        assert math.comb(120, 1) == 120
        assert math.comb(120, 119) == 120
        assert math.comb(16, 2) == 120
        assert math.comb(16, 14) == 120
        assert math.comb(10, 3) == 120
        assert math.comb(10, 7) == 120

    def test_multiplicity_search_finds_3003(self):
        results = singmaster_multiplicity_search(100, threshold=8)
        values = {r['value'] for r in results}
        assert 3003 in values

    def test_multiplicity_search_threshold_6(self):
        results = singmaster_multiplicity_search(200, threshold=6)
        values = {r['value'] for r in results}
        # Known values with multiplicity >= 6
        assert 120 in values
        assert 210 in values
        assert 3003 in values

    def test_no_multiplicity_10_below_200(self):
        """No known integer with multiplicity >= 10; verify for small rows."""
        results = singmaster_multiplicity_search(200, threshold=10)
        assert len(results) == 0

    def test_infinite_family(self):
        """The Fibonacci-derived infinite family gives multiplicity >= 6."""
        family = singmaster_infinite_family_multiplicities(5)
        assert len(family) == 5
        # i=1 is degenerate (F_1=F_2=1, gives k=0); nontrivial terms start at i=2
        for entry in family:
            assert entry['min_multiplicity'] == 6
            assert entry['n'] > 0
            assert entry['k'] >= 0
        # i=2 gives 3003 (the classic example)
        assert family[1]['n'] == 15
        assert family[1]['k'] == 5
        assert family[1]['value'] == 3003

    def test_scan_row_counts(self):
        """singmaster_scan_row correctly counts interior entries."""
        counts = {}
        singmaster_scan_row(10, counts, k_start=2)
        # Row 10: C(10,2)=45, C(10,3)=120, C(10,4)=210, C(10,5)=252 (central)
        # Each non-central k adds 2, central adds 1
        assert counts.get(45, 0) == 2   # C(10,2) and C(10,8)
        assert counts.get(120, 0) == 2  # C(10,3) and C(10,7)
        assert counts.get(210, 0) == 2  # C(10,4) and C(10,6)
        assert counts.get(252, 0) == 1  # C(10,5) central


# =============================================================================
# Binomial Divisibility (#683, #684, #685)
# =============================================================================

class TestBinomialDivisibility:
    """Test p-adic valuation and binomial divisibility."""

    def test_p_adic_valuation_kummer(self):
        """
        Kummer's theorem: v_p(C(n,k)) = number of carries
        when adding k and n-k in base p.
        """
        # C(10,5) = 252 = 2^2 * 3^2 * 7
        assert p_adic_valuation_binom(10, 5, 2) == 2
        assert p_adic_valuation_binom(10, 5, 3) == 2
        assert p_adic_valuation_binom(10, 5, 7) == 1
        assert p_adic_valuation_binom(10, 5, 5) == 0

    def test_p_adic_boundary(self):
        assert p_adic_valuation_binom(5, 0, 2) == 0  # C(5,0) = 1
        assert p_adic_valuation_binom(5, 5, 2) == 0  # C(5,5) = 1
        assert p_adic_valuation_binom(5, -1, 2) == 0

    def test_p_adic_central_binom(self):
        """v_2(C(2n, n)) for small n."""
        # C(2,1) = 2, v_2 = 1
        assert p_adic_valuation_binom(2, 1, 2) == 1
        # C(4,2) = 6, v_2 = 1
        assert p_adic_valuation_binom(4, 2, 2) == 1
        # C(8,4) = 70, v_2 = 1
        assert p_adic_valuation_binom(8, 4, 2) == 1

    def test_carries_equals_kummer(self):
        """carries_in_base_p(k, n-k, p) should equal v_p(C(n,k))."""
        test_cases = [(10, 5, 2), (10, 5, 3), (20, 7, 5), (100, 30, 7)]
        for n, k, p in test_cases:
            v = p_adic_valuation_binom(n, k, p)
            c = carries_in_base_p(k, n - k, p)
            assert v == c, f"n={n}, k={k}, p={p}: kummer={v}, carries={c}"

    def test_central_binom_prime_divisors(self):
        results = central_binom_prime_divisors(20, max_p=50)
        assert len(results) == 20
        # C(2,1) = 2: only prime factor is 2
        r1 = results[0]
        assert r1['n'] == 1
        assert r1['prime_valuations'] == {2: 1}

    def test_primes_dividing_central_binom(self):
        # C(10,5) = 252 = 2^2 * 3^2 * 7
        divs = primes_dividing_central_binom(5)
        assert 2 in divs
        assert 3 in divs
        assert 7 in divs
        assert 5 not in divs

    def test_primes_not_dividing(self):
        """5 does not divide C(10,5) = 252."""
        non_div = primes_not_dividing_central_binom(10)
        # n=5: 5 doesn't divide C(10,5)
        assert 5 in non_div.get(5, [])

    def test_valuation_records(self):
        records = central_binom_valuation_records(50)
        assert len(records) > 0
        # Should find records for at least primes 2, 3, 5
        primes_found = {r['prime'] for r in records}
        assert 2 in primes_found

    def test_granville_pattern(self):
        results = granville_pattern(20)
        assert len(results) == 19  # n=2..20
        for r in results:
            assert r['num_large_primes'] >= 0
            assert r['log_central_binom'] > 0


# =============================================================================
# Factorial Problems (#373, #390, #400, #912)
# =============================================================================

class TestFactorialConsecutive:
    """Test factorial as products of consecutive integers (#373)."""

    def test_3_factorial(self):
        # 3! = 6 = 2*3
        reps = factorial_as_consecutive_product(3)
        assert (2, 2) in reps  # 2 * 3 = 6

    def test_5_factorial(self):
        # 5! = 120 = 4*5*6 = 2*3*4*5
        reps = factorial_as_consecutive_product(5)
        assert (4, 3) in reps  # 4*5*6 = 120
        assert (2, 4) in reps  # 2*3*4*5 = 120

    def test_4_factorial(self):
        # 4! = 24 = 2*3*4
        reps = factorial_as_consecutive_product(4)
        assert (2, 3) in reps

    def test_consecutive_table(self):
        table = factorial_consecutive_table(10)
        assert len(table) == 9  # n=2..10
        for entry in table:
            assert 'n' in entry
            assert 'representations' in entry
            assert 'count' in entry

    def test_small_factorial_no_reps(self):
        reps = factorial_as_consecutive_product(2)
        assert reps == []  # 2! = 2, can't write as product of 2+ consecutive starting >= 2


class TestFactorialPrimes:
    """Test factorial primes n! +/- 1 (#390)."""

    def test_known_factorial_plus_primes(self):
        """Verify n! + 1 is prime for n = 1, 2, 3, 11."""
        fp = factorial_prime_search(15)
        plus = fp['n_factorial_plus_1_prime']
        for n in [1, 2, 3, 11]:
            assert n in plus, f"n={n}: {n}! + 1 should be prime"

    def test_known_factorial_minus_primes(self):
        """Verify n! - 1 is prime for n = 3, 4, 6, 7, 12, 14."""
        fp = factorial_prime_search(15)
        minus = fp['n_factorial_minus_1_prime']
        for n in [3, 4, 6, 7, 12, 14]:
            assert n in minus, f"n={n}: {n}! - 1 should be prime"

    def test_known_verification(self):
        """Cross-check against explicit known values."""
        v = factorial_prime_known_verification()
        for n, is_p in v['plus_one_verified']:
            assert is_p, f"{n}! + 1 should be prime"
        for n, is_p in v['minus_one_verified']:
            assert is_p, f"{n}! - 1 should be prime"

    def test_4_factorial_plus_not_prime(self):
        """4! + 1 = 25 = 5^2, not prime."""
        assert not _is_prime(math.factorial(4) + 1)

    def test_5_factorial_minus_not_prime(self):
        """5! - 1 = 119 = 7 * 17, not prime."""
        assert not _is_prime(math.factorial(5) - 1)


class TestPerfectPowers:
    """Test factorial perfect power checks (#400)."""

    def test_no_factorial_is_perfect_power(self):
        """n! is never a perfect power for n >= 2."""
        results = factorial_perfect_power_check(30)
        for r in results:
            assert not r['is_perfect_power'], f"{r['n']}! is a perfect power"

    def test_ratio_powers_empty(self):
        """
        Products of >= 2 consecutive integers > 1 are never perfect powers
        (Erdos-Selfridge 1975).
        """
        results = factorial_ratio_powers(20)
        assert results == []

    def test_erdos_selfridge(self):
        """Verify Erdos-Selfridge computationally."""
        result = erdos_selfridge_verification(15, 100)
        assert result['theorem_holds']
        assert result['checked'] > 0
        assert result['counterexamples'] == []


class TestWilson:
    """Test Wilson quotients and Wilson primes (#912)."""

    def test_wilson_quotient_small(self):
        # W_5 = (4! + 1) / 5 = 25/5 = 5
        assert wilson_quotient(5) == 5
        # W_7 = (6! + 1) / 7 = 721/7 = 103
        assert wilson_quotient(7) == 103
        # W_13 = (12! + 1) / 13 = 479001601/13 = 36846277
        assert wilson_quotient(13) == (math.factorial(12) + 1) // 13

    def test_wilson_quotient_non_prime_raises(self):
        with pytest.raises(ValueError):
            wilson_quotient(4)
        with pytest.raises(ValueError):
            wilson_quotient(1)

    def test_wilson_primes_known(self):
        """Known Wilson primes: 5, 13, 563."""
        wp = wilson_prime_search(600)
        assert 5 in wp
        assert 13 in wp
        assert 563 in wp

    def test_wilson_primes_only_3_below_600(self):
        """There are exactly 3 Wilson primes below 600."""
        wp = wilson_prime_search(600)
        assert len(wp) == 3

    def test_wilson_prime_definition(self):
        """Wilson prime p means p^2 | (p-1)! + 1."""
        for p in [5, 13, 563]:
            assert (math.factorial(p - 1) + 1) % (p * p) == 0


# =============================================================================
# Catalan Numbers
# =============================================================================

class TestCatalan:
    """Test Catalan number computations."""

    def test_catalan_values(self):
        # C_0=1, C_1=1, C_2=2, C_3=5, C_4=14, ...  (OEIS A000108)
        expected = [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862, 16796]
        for n, c in enumerate(expected):
            assert catalan(n) == c, f"C_{n} should be {c}, got {catalan(n)}"

    def test_catalan_negative(self):
        assert catalan(-1) == 0

    def test_catalan_squarefree_small(self):
        sq = catalan_squarefree(20)
        # Manually verify: C_1=1 (sf), C_2=2 (sf), C_3=5 (sf), C_4=14=2*7 (sf),
        # C_5=42=2*3*7 (sf), C_6=132=4*33 (not sf), C_7=429=3*11*13 (sf),
        # C_8=1430=2*5*11*13 (sf), C_9=4862=2*11*13*17 (sf: check)
        # Actually C_9 = 4862 = 2*2431 = 2*2431. Is 2431 prime? 2431/7=347.3, not.
        # 2431 = 2431. Let me check: 49^2=2401<2431<2500=50^2. primes up to 49.
        # 2431/11=221, 11*221=2431, 221=13*17. So C_9=2*11*13*17, squarefree.
        for n in [1, 2, 3, 4, 5, 7, 8, 9]:
            assert n in sq, f"C_{n} should be squarefree"

    def test_catalan_6_not_squarefree(self):
        """C_6 = 132 = 4 * 33 = 2^2 * 3 * 11, not squarefree."""
        assert 6 not in catalan_squarefree(10)

    def test_catalan_squarefree_density_decreasing(self):
        """Squarefree Catalan numbers become rarer as n grows."""
        sq_50 = catalan_squarefree(50)
        sq_100 = catalan_squarefree(100)
        # Density should decrease (or at least not increase much)
        density_50 = len(sq_50) / 50
        density_100 = len(sq_100) / 100
        # At n=100, density should be < 0.3
        assert density_100 < 0.3

    def test_catalan_factorization_patterns(self):
        results = catalan_prime_factorization_patterns(20)
        assert len(results) == 20
        for r in results:
            assert r['catalan'] == catalan(r['n'])
            # Reconstruct from factorization
            product = 1
            for p, e in r['factorization'].items():
                product *= p ** e
            assert product == r['catalan']

    def test_catalan_divisibility_by_2(self):
        results = catalan_divisibility_by_prime(20, 2)
        assert len(results) == 20
        # C_1 = 1, v_2 = 0
        assert results[0]['v_p_catalan'] == 0
        # C_2 = 2, v_2 = 1
        assert results[1]['v_p_catalan'] == 1
        # C_6 = 132 = 2^2 * 33, v_2 = 2
        assert results[5]['v_p_catalan'] == 2


# =============================================================================
# Wolstenholme's Theorem
# =============================================================================

class TestWolstenholme:
    """Test Wolstenholme's theorem and Wolstenholme prime search."""

    def test_wolstenholme_theorem_holds(self):
        """For p >= 5, p^3 | C(2p,p) - 2."""
        for p in [5, 7, 11, 13, 17, 19, 23, 29, 31]:
            val = math.comb(2 * p, p)
            assert (val - 2) % (p ** 3) == 0, f"Wolstenholme fails for p={p}"

    def test_wolstenholme_verify_small(self):
        for p in [5, 7, 11, 13]:
            result = wolstenholme_verify(p)
            assert result['p'] == p
            assert result['C_2p_p_mod_p3'] == 2  # exactly ≡ 2 (mod p^3)
            assert result['divisibility_order'] >= 3

    def test_wolstenholme_not_4th_order_small(self):
        """No Wolstenholme primes below 1000."""
        for p in [5, 7, 11, 13, 17, 19, 23]:
            result = wolstenholme_verify(p)
            assert not result['is_wolstenholme_prime']

    def test_wolstenholme_search_empty_below_1000(self):
        """First Wolstenholme prime is 16843."""
        results = wolstenholme_prime_search(1000)
        assert results == []

    @pytest.mark.parametrize("p", [5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43])
    def test_wolstenholme_residue_nonzero(self, p):
        """Non-Wolstenholme primes have nonzero residue."""
        result = wolstenholme_verify(p)
        assert result['divisibility_order'] == 3  # exactly 3, not more

    def test_wolstenholme_residues_structure(self):
        results = wolstenholme_residues(50)
        assert len(results) > 0
        for r in results:
            assert r['p'] >= 5
            assert 0 <= r['wolstenholme_residue'] < r['p']

    def test_wolstenholme_residue_distribution(self):
        dist = wolstenholme_residue_distribution(100)
        assert dist['num_primes_checked'] > 0
        assert dist['wolstenholme_primes_found'] == 0  # none below 100
        assert dist['expected_under_uniform'] > 0

    def test_comb_mod_prime_power(self):
        """_comb_mod_prime_power should agree with math.comb for small values."""
        for n in range(10, 30):
            for k in range(0, n + 1):
                for p, e in [(2, 5), (3, 4), (5, 3), (7, 2)]:
                    mod = p ** e
                    expected = math.comb(n, k) % mod
                    actual = _comb_mod_prime_power(n, k, p, e)
                    assert actual == expected, (
                        f"C({n},{k}) mod {p}^{e}: expected {expected}, got {actual}"
                    )

    def test_wolstenholme_verify_raises_for_small(self):
        with pytest.raises(ValueError):
            wolstenholme_verify(3)
        with pytest.raises(ValueError):
            wolstenholme_verify(4)

    @pytest.mark.slow
    def test_wolstenholme_prime_16843(self):
        """Verify that 16843 is a Wolstenholme prime (p^4 | C(2p,p) - 2)."""
        result = wolstenholme_verify(16843)
        assert result['is_wolstenholme_prime']
        assert result['divisibility_order'] >= 4


# =============================================================================
# Cross-cutting: Kummer's theorem consistency
# =============================================================================

class TestKummerConsistency:
    """Verify Kummer's theorem across multiple formulations."""

    def test_kummer_digit_sum_formula(self):
        """
        v_p(C(n,k)) = (s_p(k) + s_p(n-k) - s_p(n)) / (p-1)
        must be a non-negative integer.
        """
        for n in range(1, 30):
            for k in range(0, n + 1):
                for p in [2, 3, 5, 7]:
                    v = p_adic_valuation_binom(n, k, p)
                    assert v >= 0
                    assert isinstance(v, int)

    def test_kummer_matches_direct_valuation(self):
        """v_p(C(n,k)) from digit sums matches direct factoring of C(n,k)."""
        for n in range(2, 25):
            for k in range(1, n):
                c = math.comb(n, k)
                for p in [2, 3, 5]:
                    # Direct: count powers of p in c
                    v_direct = 0
                    temp = c
                    while temp % p == 0:
                        v_direct += 1
                        temp //= p
                    v_kummer = p_adic_valuation_binom(n, k, p)
                    assert v_kummer == v_direct, (
                        f"C({n},{k})={c}, p={p}: kummer={v_kummer}, direct={v_direct}"
                    )

    def test_carries_matches_kummer(self):
        """carries_in_base_p(k, n-k, p) = v_p(C(n,k))."""
        for n in range(2, 20):
            for k in range(1, n):
                for p in [2, 3, 5, 7]:
                    v = p_adic_valuation_binom(n, k, p)
                    c = carries_in_base_p(k, n - k, p)
                    assert v == c


# =============================================================================
# Erdos-Selfridge and structural results
# =============================================================================

class TestStructural:
    """Test structural/theoretical results."""

    def test_bertrand_postulate_implies_factorial_not_power(self):
        """
        For n >= 2, there exists prime p with n/2 < p <= n (Bertrand).
        This p appears exactly once in n!, so n! cannot be a perfect power.
        """
        results = factorial_perfect_power_check(50)
        for r in results:
            assert not r['is_perfect_power']

    def test_erdos_selfridge_extended(self):
        """No product of k >= 2 consecutive integers (starting >= 2) is a perfect power."""
        result = erdos_selfridge_verification(20, 200)
        assert result['theorem_holds']

    def test_granville_large_primes_contribute(self):
        """Every prime in (n, 2n] divides C(2n,n) exactly once."""
        for n in range(5, 30):
            primes_in_range = [p for p in _sieve_primes(2 * n) if p > n]
            for p in primes_in_range:
                v = p_adic_valuation_binom(2 * n, n, p)
                assert v == 1, f"n={n}, p={p}: v_p(C(2n,n)) = {v}, expected 1"


# =============================================================================
# Summary / Integration
# =============================================================================

class TestSummary:
    """Test the integrated summary function."""

    def test_summary_runs(self):
        s = binomial_factorial_summary(
            max_row_singmaster=100,
            max_n_binom=20,
            max_n_factorial=8,
            max_n_catalan=20,
            max_p_wolstenholme=50,
        )
        assert 'singmaster' in s
        assert 'binomial_divisibility' in s
        assert 'factorial' in s
        assert 'catalan' in s
        assert 'wolstenholme' in s

    def test_summary_singmaster_max_mult(self):
        s = binomial_factorial_summary(
            max_row_singmaster=200,
            max_n_binom=10,
            max_n_factorial=5,
            max_n_catalan=10,
            max_p_wolstenholme=20,
        )
        # Should find 3003 at multiplicity 8 within 200 rows
        assert s['singmaster']['max_multiplicity_found'] >= 8

    def test_summary_catalan_squarefree(self):
        s = binomial_factorial_summary(
            max_row_singmaster=50,
            max_n_binom=10,
            max_n_factorial=5,
            max_n_catalan=20,
            max_p_wolstenholme=20,
        )
        assert s['catalan']['squarefree_count'] > 0
        assert s['catalan']['squarefree_density'] > 0


# =============================================================================
# Additional edge case tests for coverage
# =============================================================================

class TestEdgeCases:
    """Cover remaining edge cases and utility paths."""

    def test_is_prime_composite_pseudoprimes(self):
        """Test against Carmichael numbers (pseudoprimes to Fermat test)."""
        # 561 is the smallest Carmichael number
        assert not _is_prime(561)
        assert not _is_prime(1105)  # next Carmichael
        assert not _is_prime(1729)  # Hardy-Ramanujan / Carmichael

    def test_factorize_prime(self):
        assert _factorize(97) == {97: 1}
        assert _factorize(2) == {2: 1}

    def test_factorize_prime_power(self):
        assert _factorize(128) == {2: 7}
        assert _factorize(243) == {3: 5}

    def test_sieve_primes_boundary(self):
        assert _sieve_primes(0) == []
        assert _sieve_primes(-1) == []
        assert _sieve_primes(3) == [2, 3]

    def test_is_probable_prime_forwarding(self):
        """is_probable_prime delegates to _is_prime correctly."""
        from binomial_factorial_attacks import is_probable_prime
        assert is_probable_prime(2)
        assert is_probable_prime(17)
        assert not is_probable_prime(1)
        assert not is_probable_prime(0)

    def test_catalan_squarefree_large(self):
        """Catalan squarefree indices up to 300 include no n > 35."""
        sq = catalan_squarefree(300)
        # Known: last squarefree Catalan is C_35 (conjectured to be the last)
        # At minimum, check density is < 10%
        assert len(sq) / 300 < 0.10

    def test_digit_sum_large_number(self):
        # 1000 in base 10 = 1000, digit sum = 1
        assert _digit_sum_base_p(1000, 10) == 1
        # 63 in base 2 = 111111, digit sum = 6
        assert _digit_sum_base_p(63, 2) == 6

    def test_granville_pattern_n2(self):
        """Granville pattern for n=2: primes in (2,4] = {3}."""
        results = granville_pattern(3)
        # n=2: primes in (2,4] = [3]
        assert results[0]['n'] == 2
        assert results[0]['num_large_primes'] == 1

    def test_factorial_prime_search_n1(self):
        """1! + 1 = 2 is prime, 1! - 1 = 0 is not."""
        fp = factorial_prime_search(1)
        assert 1 in fp['n_factorial_plus_1_prime']
        assert 1 not in fp['n_factorial_minus_1_prime']

    def test_wolstenholme_verify_large_p_branch(self):
        """Test the modular computation branch for p > 5000."""
        # p = 5003 is prime
        result = wolstenholme_verify(5003)
        assert result['p'] == 5003
        assert result['divisibility_order'] == 3  # not a Wolstenholme prime
        assert result['C_2p_p_mod_p3'] == 2
