"""Tests for coprime_analysis.py — Coprime Graph Analysis for Problem #883."""
import math
import pytest

from coprime_analysis import (
    mobius,
    coprime_count_direct,
    coprime_count_mobius,
    extremal_set,
    primes_up_to,
    analyze_set,
)


class TestMobius:
    """Test the Möbius function implementation."""

    def test_mobius_1(self):
        assert mobius(1) == 1

    def test_mobius_primes(self):
        """μ(p) = -1 for any prime p."""
        for p in [2, 3, 5, 7, 11, 13]:
            assert mobius(p) == -1, f"μ({p}) should be -1"

    def test_mobius_prime_squares(self):
        """μ(p²) = 0 for any prime p."""
        for p in [2, 3, 5, 7]:
            assert mobius(p * p) == 0, f"μ({p}²) should be 0"

    def test_mobius_squarefree_two_primes(self):
        """μ(pq) = 1 for distinct primes p, q."""
        assert mobius(6) == 1   # 2 * 3
        assert mobius(10) == 1  # 2 * 5
        assert mobius(15) == 1  # 3 * 5

    def test_mobius_three_primes(self):
        """μ(pqr) = -1 for distinct primes p, q, r."""
        assert mobius(30) == -1  # 2 * 3 * 5

    def test_mobius_with_square_factor(self):
        """μ(n) = 0 when n has a squared prime factor."""
        assert mobius(12) == 0   # 4 * 3
        assert mobius(18) == 0   # 2 * 9
        assert mobius(50) == 0   # 2 * 25

    def test_mobius_sum_property(self):
        """Σ_{d|n} μ(d) = 0 for n > 1 (fundamental identity)."""
        for n in range(2, 30):
            divisor_sum = sum(mobius(d) for d in range(1, n + 1) if n % d == 0)
            assert divisor_sum == 0, f"Σ μ(d) for d|{n} should be 0"


class TestCoprimeCount:
    """Test coprime pair counting — direct vs Möbius."""

    def test_empty_set(self):
        assert coprime_count_direct(set()) == 0
        assert coprime_count_mobius(set()) == 0

    def test_singleton(self):
        assert coprime_count_direct({5}) == 0
        assert coprime_count_mobius({5}) == 0

    def test_coprime_pair(self):
        """Two coprime numbers → 1 pair."""
        assert coprime_count_direct({2, 3}) == 1
        assert coprime_count_mobius({2, 3}) == 1

    def test_non_coprime_pair(self):
        """Two non-coprime numbers → 0 pairs."""
        assert coprime_count_direct({4, 6}) == 0
        assert coprime_count_mobius({4, 6}) == 0

    def test_direct_equals_mobius(self):
        """Direct and Möbius methods should agree on any input."""
        test_sets = [
            {1, 2, 3, 4, 5},
            {2, 4, 6, 8, 10},
            {1, 7, 11, 13, 17},
            set(range(1, 20)),
        ]
        for A in test_sets:
            direct = coprime_count_direct(A)
            mobius_count = coprime_count_mobius(A)
            assert direct == mobius_count, (
                f"Direct ({direct}) ≠ Möbius ({mobius_count}) for {A}"
            )

    def test_full_set_density_approaches_expected(self):
        """For [n], coprime density should approach 6/π² ≈ 0.608."""
        expected = 6 / math.pi**2
        for n in [50, 100, 200]:
            A = set(range(1, n + 1))
            M = coprime_count_mobius(A)
            max_pairs = n * (n - 1) // 2
            density = M / max_pairs
            assert abs(density - expected) < 0.05, (
                f"n={n}: density {density:.4f} not close to {expected:.4f}"
            )


class TestExtremalSet:
    """Test extremal set construction."""

    def test_extremal_set_contains_correct_elements(self):
        A = extremal_set(12)
        for i in range(1, 13):
            if i % 2 == 0 or i % 3 == 0:
                assert i in A, f"{i} should be in A*"
            else:
                assert i not in A, f"{i} should not be in A*"

    def test_extremal_set_size(self):
        """Size should be ⌊n/2⌋ + ⌊n/3⌋ - ⌊n/6⌋."""
        for n in [6, 12, 30, 100]:
            A = extremal_set(n)
            expected = n // 2 + n // 3 - n // 6
            assert len(A) == expected, (
                f"n={n}: |A*|={len(A)}, expected {expected}"
            )

    def test_extremal_density_below_mantel(self):
        """Extremal set coprime density should be below 0.25 (Mantel threshold)."""
        for n in [50, 100]:
            A = extremal_set(n)
            result = analyze_set(A)
            assert result["density"] < 0.25, (
                f"n={n}: extremal density {result['density']:.4f} ≥ 0.25"
            )


class TestPrimes:
    """Test prime generation and coprime structure."""

    def test_primes_known_values(self):
        primes = primes_up_to(30)
        assert primes == {2, 3, 5, 7, 11, 13, 17, 19, 23, 29}

    def test_primes_empty_for_small_n(self):
        assert primes_up_to(1) == set()
        assert primes_up_to(0) == set()

    def test_primes_coprime_density_near_one(self):
        """Primes are pairwise coprime (except 2,2), so density ≈ 1.0."""
        primes = primes_up_to(100)
        result = analyze_set(primes, "primes")
        assert result["density"] > 0.99, (
            f"Primes density {result['density']:.4f} should be ≈ 1.0"
        )


class TestAnalyzeSet:
    """Test the analyze_set aggregation function."""

    def test_returns_expected_keys(self):
        A = {1, 2, 3}
        result = analyze_set(A)
        assert "size" in result
        assert "coprime_pairs" in result
        assert "density" in result
        assert "above_mantel" in result

    def test_above_mantel_flag(self):
        """Full [n] should have density > 0.25."""
        A = set(range(1, 51))
        result = analyze_set(A)
        assert result["above_mantel"] is True
