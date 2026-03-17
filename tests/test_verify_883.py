"""Tests for verify_883.py — Problem #883 exhaustive and optimized verification."""
import math
import pytest

from verify_883 import (
    extremal_size,
    has_coprime_triple,
    find_coprime_triple,
    verify_exhaustive,
    check_near_extremal_sets,
    verify_proof_cases,
)


class TestExtremalSize:
    """Test extremal set size computation."""

    def test_known_values(self):
        """Verify ⌊n/2⌋ + ⌊n/3⌋ - ⌊n/6⌋ for specific n."""
        assert extremal_size(6) == 4    # 3 + 2 - 1
        assert extremal_size(12) == 8   # 6 + 4 - 2
        assert extremal_size(30) == 20  # 15 + 10 - 5

    def test_approximately_two_thirds(self):
        for n in [60, 120, 180]:
            size = extremal_size(n)
            ratio = size / n
            assert abs(ratio - 2/3) < 0.02, f"n={n}: ratio={ratio}"


class TestHasCoprimeTriplet:
    """Test coprime triple detection."""

    def test_trivial_triple(self):
        """1 is coprime to everything, so {1, 2, 3} works."""
        assert has_coprime_triple({1, 2, 3})

    def test_no_triple_even(self):
        """All even numbers share factor 2 — hard to find triple."""
        # {4, 6, 10}: gcd(4,6)=2, gcd(4,10)=2, gcd(6,10)=2
        assert not has_coprime_triple({4, 6, 10})

    def test_primes_form_triple(self):
        """Any 3 distinct primes are mutually coprime."""
        assert has_coprime_triple({5, 7, 11})

    def test_extremal_set_no_triple(self):
        """The extremal set A* should NOT contain a coprime triple for small n."""
        # A* for n=6: {2, 3, 4, 6} — gcd(2,3)=1, gcd(2,4)=2, gcd(3,4)=1, gcd(3,6)=3
        # Actually {2,3,4} has gcd(2,3)=1, gcd(3,4)=1 but gcd(2,4)=2 → not mutually coprime
        # {2,3,6}: gcd(2,3)=1, gcd(2,6)=2 → no
        # So A* may or may not have coprime triples depending on n
        # For small n it generally doesn't
        a_star = {i for i in range(1, 7) if i % 2 == 0 or i % 3 == 0}
        # {2, 3, 4, 6} — check manually
        # (2,3,4): gcd(2,4)=2 → no
        # (2,3,6): gcd(2,6)=2 → no
        # (2,4,6): gcd(2,4)=2 → no
        # (3,4,6): gcd(3,6)=3 → no
        assert not has_coprime_triple(a_star)


class TestFindCoprimeTriplet:
    """Test finding coprime triples."""

    def test_returns_valid_triple(self):
        A = {1, 2, 3, 4, 5}
        triple = find_coprime_triple(A)
        assert triple is not None
        a, b, c = triple
        assert math.gcd(a, b) == 1
        assert math.gcd(b, c) == 1
        assert math.gcd(a, c) == 1

    def test_returns_none_when_impossible(self):
        assert find_coprime_triple({4, 6, 10}) is None


class TestVerifyExhaustive:
    """Test exhaustive verification."""

    def test_small_n_pass(self):
        """Problem #883 should hold for small n."""
        for n in range(3, 15):
            result, counter = verify_exhaustive(n)
            assert result, f"n={n}: found counterexample {counter}"

    def test_n_equals_3(self):
        """n=3: |A*|=2, threshold=3. Only set is {1,2,3} which has triple (1,2,3)."""
        result, _ = verify_exhaustive(3)
        assert result


class TestVerifyOptimized:
    """Test optimized verification for larger n."""

    @pytest.mark.slow
    def test_medium_n(self):
        """Verify for n up to 50."""
        for n in [30, 40, 50]:
            result, counter = check_near_extremal_sets(n)
            assert result, f"n={n}: counterexample {counter}"


class TestVerifyProofCases:
    """Test individual proof cases."""

    def test_case1_triangle_2_3_x(self):
        """x coprime to 6, so gcd(x,2)=gcd(x,3)=gcd(2,3)=1."""
        cases = verify_proof_cases(30)
        assert cases["case1_2_3_x"] is True

    def test_case2_element_1(self):
        """1 is coprime to everything → many coprime pairs available."""
        cases = verify_proof_cases(30)
        assert cases["case2_1_coprime_pairs"] > 0

    def test_case3_forced_for_large_n(self):
        """For n ≥ 7, the case without 2 and 3 still forces a triangle."""
        cases = verify_proof_cases(30)
        if "case3_triangle_forced" in cases:
            assert cases["case3_triangle_forced"] is True
