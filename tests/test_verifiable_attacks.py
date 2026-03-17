#!/usr/bin/env python3
"""Tests for verifiable_attacks.py — Erdős problems #364, #366, #647."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from verifiable_attacks import (
    is_k_full,
    is_powerful,
    powerful_numbers_up_to,
    consecutive_powerful_pairs,
    compute_A060355,
    powerful_pairs_diff_2,
    compute_A076445,
    search_three_consecutive_powerful,
    prove_no_three_consecutive_powerful,
    k_full_numbers_up_to,
    search_366,
    divisor_count,
    compute_n_plus_tau,
    compute_A062249,
    find_A087280,
    analyze_647_gaps,
    search_647_extended,
    pell_solutions,
    consecutive_powerful_from_pell,
    _primes_up_to,
)


# ---------------------------------------------------------------------------
# k-full numbers
# ---------------------------------------------------------------------------

class TestKFull:
    def test_is_powerful_basic(self):
        assert is_powerful(1)
        assert is_powerful(4)    # 2²
        assert is_powerful(8)    # 2³
        assert is_powerful(9)    # 3²
        assert is_powerful(16)   # 2⁴
        assert is_powerful(25)   # 5²
        assert is_powerful(27)   # 3³
        assert is_powerful(32)   # 2⁵
        assert is_powerful(36)   # 2²·3²
        assert is_powerful(72)   # 2³·3²
        assert is_powerful(100)  # 2²·5²

    def test_is_not_powerful(self):
        assert not is_powerful(2)
        assert not is_powerful(3)
        assert not is_powerful(5)
        assert not is_powerful(6)
        assert not is_powerful(10)
        assert not is_powerful(12)  # 2²·3, but 3 has exp 1

    def test_is_3full(self):
        assert is_k_full(8, 3)    # 2³
        assert is_k_full(27, 3)   # 3³
        assert is_k_full(64, 3)   # 2⁶
        assert is_k_full(216, 3)  # 2³·3³
        assert not is_k_full(4, 3)  # 2², exponent 2 < 3
        assert not is_k_full(9, 3)  # 3², exponent 2 < 3

    def test_powerful_numbers_up_to_100(self):
        # Known: 1, 4, 8, 9, 16, 25, 27, 32, 36, 49, 64, 72, 81, 100
        pn = powerful_numbers_up_to(100)
        assert pn == [1, 4, 8, 9, 16, 25, 27, 32, 36, 49, 64, 72, 81, 100]

    def test_powerful_count(self):
        # Asymptotically, powerful numbers up to N ~ c√N where c = ζ(3/2)/ζ(3)
        pn = powerful_numbers_up_to(10000)
        # Should be roughly √10000 * c ≈ 100 * 2.17 ≈ 217
        assert 50 < len(pn) < 500  # loose bounds

    def test_k_full_3_up_to_1000(self):
        cubeful = k_full_numbers_up_to(1000, 3)
        # Must include: 1, 8, 16, 27, 32, 64, 81, 125, 128, 216, 243, 256, 343, 512, 625, 729, 1000
        assert 1 in cubeful
        assert 8 in cubeful
        assert 27 in cubeful
        assert 125 in cubeful
        assert 216 in cubeful  # 6³
        assert 1000 in cubeful  # 10³ = 2³·5³
        # Non-cubeful
        assert 4 not in cubeful
        assert 9 not in cubeful
        assert 12 not in cubeful


# ---------------------------------------------------------------------------
# Problem #364: Consecutive powerful numbers (A060355)
# ---------------------------------------------------------------------------

class TestProblem364:
    def test_A060355_known_values(self):
        """OEIS A060355: 8, 288, 675, 9800, 12167, ..."""
        pairs = compute_A060355(15000)
        # Known values below 15000
        assert 8 in pairs       # 8=2³, 9=3²
        assert 288 in pairs     # 288=2⁵·3², 289=17²
        assert 675 in pairs     # 675=3³·5², 676=26²=2²·13²
        assert 9800 in pairs    # 9800=2³·5²·7², 9801=99²=3⁴·11²
        assert 12167 in pairs   # 12167=23³, 12168=2³·3²·13²

    def test_consecutive_pairs_all_powerful(self):
        """Both members of each pair must be powerful."""
        pairs = consecutive_powerful_pairs(10000)
        for n, np1 in pairs:
            assert is_powerful(n), f"{n} is not powerful"
            assert is_powerful(np1), f"{np1} is not powerful"
            assert np1 == n + 1

    def test_A076445_known(self):
        """OEIS A076445: 25, 70225, ..."""
        a076445 = compute_A076445(200000)
        assert 25 in a076445  # 25=5², 27=3³ — both powerful, differ by 2

    def test_no_triples(self):
        """No three consecutive powerful numbers up to 10^6."""
        triples = search_three_consecutive_powerful(10**6)
        assert triples == []

    def test_mod4_proof_status(self):
        """Verify the proof status is correctly OPEN."""
        proof = prove_no_three_consecutive_powerful()
        assert 'OPEN' in proof['status']
        # No powerful number is ≡ 2 mod 4
        assert proof['powerful_equiv_2_mod4'] == []


# ---------------------------------------------------------------------------
# Problem #366: 2-full n with n+1 being 3-full
# ---------------------------------------------------------------------------

class TestProblem366:
    def test_known_reverse_pairs(self):
        """Known: 8 (3-full) with 9 (2-full), 12167 (3-full) with 12168 (2-full)."""
        result = search_366(20000)
        reverse = result['3full_n_2full_n1']
        assert (8, 9) in reverse
        assert (12167, 12168) in reverse

    def test_no_forward_pairs_small(self):
        """No 2-full n with n+1 being 3-full found for small N."""
        result = search_366(100000)
        assert result['2full_n_3full_n1'] == []

    def test_8_is_3full_9_is_2full(self):
        assert is_k_full(8, 3)   # 2³
        assert is_k_full(9, 2)   # 3²
        assert not is_k_full(9, 3)  # 3² has exponent 2 < 3

    def test_12167_is_3full(self):
        # 12167 = 23³
        assert is_k_full(12167, 3)
        assert 12167 == 23 ** 3

    def test_12168_is_2full(self):
        # 12168 = 2³ · 3² · 13² — all exponents >= 2
        assert is_k_full(12168, 2)
        assert 12168 == 8 * 9 * 169  # 2³ · 3² · 13²


# ---------------------------------------------------------------------------
# Problem #647 (£25 prize): n + τ(n)
# ---------------------------------------------------------------------------

class TestProblem647:
    def test_divisor_count(self):
        assert divisor_count(1) == 1
        assert divisor_count(2) == 2
        assert divisor_count(6) == 4
        assert divisor_count(12) == 6
        assert divisor_count(24) == 8
        assert divisor_count(60) == 12

    def test_A062249_first_values(self):
        """A062249: n + d(n) for n=1,2,..."""
        a = compute_A062249(10)
        # 1+1=2, 2+2=4, 3+2=5, 4+3=7, 5+2=7, 6+4=10, 7+2=9, 8+4=12, 9+3=12, 10+4=14
        assert a == [2, 4, 5, 7, 7, 10, 9, 12, 12, 14]

    def test_A087280_known(self):
        """A087280: n where max_{m<n}(m+τ(m)) ≤ n+2. Known: 5, 8, 10, 12, 24."""
        solutions = find_A087280(10000)
        # Should include 1..6, 8, 10, 12, 24
        assert 5 in solutions
        assert 8 in solutions
        assert 10 in solutions
        assert 12 in solutions
        assert 24 in solutions
        # Should NOT include values > 24
        assert all(s <= 24 for s in solutions)

    def test_no_solution_after_24(self):
        """No solution after n=24 up to 10^6."""
        solutions = find_A087280(10**6)
        assert max(solutions) == 24

    def test_gap_analysis(self):
        gap = analyze_647_gaps(1000)
        # All solutions should be ≤ 24
        for n, rm, g in gap['solutions']:
            assert n <= 24
        # Near misses exist
        assert gap['near_misses_count'] > 0

    def test_647_extended_search(self):
        result = search_647_extended(100000)
        assert result['num_solutions'] > 0
        assert max(result['solutions']) == 24
        assert result['min_gap_after_24'] >= 1

    def test_n_plus_tau_sieve_vs_direct(self):
        """Verify sieve-based τ matches direct computation."""
        N = 200
        sieve = compute_n_plus_tau(N)
        for i in range(N):
            n = i + 1
            assert sieve[i] == n + divisor_count(n), f"Mismatch at n={n}"


# ---------------------------------------------------------------------------
# Pell equations and powerful pair generation
# ---------------------------------------------------------------------------

class TestPell:
    def test_pell_D2(self):
        """x² - 2y² = 1: fundamental solution (3, 2)."""
        sols = pell_solutions(2, max_solutions=5)
        assert len(sols) >= 1
        assert sols[0] == (3, 2)
        # Check: 9 - 2·4 = 1 ✓
        for x, y in sols:
            assert x * x - 2 * y * y == 1

    def test_pell_D5(self):
        """x² - 5y² = 1: fundamental solution (9, 4)."""
        sols = pell_solutions(5, max_solutions=3)
        assert len(sols) >= 1
        assert sols[0] == (9, 4)

    def test_pell_perfect_square(self):
        """D = 4 (perfect square): no solution."""
        sols = pell_solutions(4)
        assert sols == []

    def test_pell_all_solutions_valid(self):
        """All returned solutions satisfy Pell's equation."""
        for D in [2, 3, 5, 6, 7, 10, 11, 13]:
            sols = pell_solutions(D, max_solutions=5)
            for x, y in sols:
                assert x * x - D * y * y == 1, \
                    f"Failed for D={D}: {x}²-{D}·{y}²={x*x-D*y*y}"

    def test_consecutive_powerful_from_pell(self):
        pairs = consecutive_powerful_from_pell(max_D=50, max_val=10**8)
        # Should include 8 (since 8=2·2², 9=3²)
        assert 8 in pairs
        # All entries should give consecutive powerful pairs
        for n in pairs:
            assert is_powerful(n), f"{n} not powerful"
            assert is_powerful(n + 1), f"{n+1} not powerful"


# ---------------------------------------------------------------------------
# Primes utility
# ---------------------------------------------------------------------------

class TestPrimes:
    def test_primes_up_to_30(self):
        assert _primes_up_to(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

    def test_primes_up_to_1(self):
        assert _primes_up_to(1) == []


# ---------------------------------------------------------------------------
# Edge cases and validation
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_is_powerful_zero(self):
        assert not is_powerful(0)

    def test_is_powerful_negative(self):
        assert not is_powerful(-4)

    def test_powerful_numbers_up_to_zero(self):
        assert powerful_numbers_up_to(0) == []

    def test_divisor_count_zero(self):
        assert divisor_count(0) == 0

    def test_k_full_edge(self):
        assert is_k_full(1, 100)  # vacuously true
        assert not is_k_full(0, 1)


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

class TestPellNegative:
    def test_pell_D_negative(self):
        sols = pell_solutions(-1)
        assert sols == []

    def test_pell_D_zero(self):
        sols = pell_solutions(0)
        assert sols == []


class TestGapAnalysisDetails:
    def test_gap_largest_values(self):
        gap = analyze_647_gaps(500)
        # Should return largest n+tau values
        assert len(gap['largest_n_plus_tau']) > 0
        # Each should be (value, n) pair
        for val, n in gap['largest_n_plus_tau']:
            assert val == n + divisor_count(n)

    def test_gap_at_checkpoints(self):
        gap = analyze_647_gaps(1000)
        assert gap['gap_at_100'] is not None
        assert gap['gap_at_100'] > 0  # positive debt
        assert gap['gap_at_1000'] is not None
        assert gap['gap_at_1000'] > 0

    def test_647_min_gap_positive(self):
        """After n=24, the gap is always > 0."""
        result = search_647_extended(10000)
        assert result['min_gap_after_24'] >= 1
        # The minimum gap of 1 occurs at n=35
        assert result['min_gap_at_n'] == 35


class TestIntegration:
    @pytest.mark.timeout(120)
    def test_run_verifiable_experiments(self):
        """Full integration test (may take ~60s)."""
        # Just test the fast parts
        from verifiable_attacks import (
            prove_no_three_consecutive_powerful,
            compute_A060355,
            search_366,
            find_A087280,
        )
        proof = prove_no_three_consecutive_powerful()
        assert 'OPEN' in proof['status']

        a060355 = compute_A060355(20000)
        assert 8 in a060355
        assert 288 in a060355
        assert 675 in a060355
        assert 9800 in a060355
        assert 12167 in a060355

        res_366 = search_366(20000)
        assert len(res_366['2full_n_3full_n1']) == 0

        solutions = find_A087280(100000)
        assert max(solutions) == 24
