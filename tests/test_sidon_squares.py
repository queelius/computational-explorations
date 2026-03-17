"""Tests for sidon_squares.py -- Problem #773: Sidon sets among perfect squares."""
import math
import pytest

from sidon_squares import (
    is_sidon,
    squares_up_to,
    max_sidon_in_squares,
    max_sidon_in_squares_exhaustive,
    sidon_squares_sequence,
    analyze_sidon_squares,
    _greedy_sidon_squares,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def verify_is_sidon_set(S):
    """Independent check that all pairwise sums are distinct."""
    elements = sorted(S)
    seen = set()
    for i, a in enumerate(elements):
        for b in elements[i:]:
            s = a + b
            if s in seen:
                return False
            seen.add(s)
    return True


def verify_all_squares(S):
    """Check every element of S is a perfect square >= 1."""
    for x in S:
        root = math.isqrt(x)
        assert root * root == x and root >= 1, f"{x} is not a perfect square"


# ---------------------------------------------------------------------------
# TestIsSidon -- basic validation of the Sidon checker
# ---------------------------------------------------------------------------

class TestIsSidon:
    def test_empty(self):
        assert is_sidon(set())

    def test_singleton(self):
        assert is_sidon({1})
        assert is_sidon({100})

    def test_pair_always_sidon(self):
        """Any two distinct elements form a Sidon set."""
        assert is_sidon({1, 4})
        assert is_sidon({9, 25})

    def test_known_sidon_squares(self):
        """{1, 4, 9} has sums 2, 5, 8, 10, 13, 18 -- all distinct."""
        assert is_sidon({1, 4, 9})

    def test_non_sidon(self):
        """{1, 4, 9, 16}: 1+16=17 and 4+... let's verify manually.
        Sums: 2, 5, 8, 10, 13, 18, 20, 25, 32.
        Wait -- {1,4,9,16}: 1+1=2, 1+4=5, 1+9=10, 1+16=17,
        4+4=8, 4+9=13, 4+16=20, 9+9=18, 9+16=25, 16+16=32. All distinct!
        So {1,4,9,16} IS Sidon.
        Let's use a known non-Sidon set."""
        # {1, 5, 7, 10}: 1+10=11, 5+7=12 -- but all distinct? Check properly.
        # Easier: just use a set we *know* has a collision.
        # 3+7=10 and 4+6=10 -> {3,4,6,7} is NOT Sidon
        assert not is_sidon({3, 4, 6, 7})

    def test_sidon_with_squares_four_elements(self):
        """{1, 4, 9, 16} -- verify independently."""
        S = {1, 4, 9, 16}
        sums = []
        elems = sorted(S)
        for i, a in enumerate(elems):
            for b in elems[i:]:
                sums.append(a + b)
        assert len(sums) == len(set(sums)), f"Duplicate in {sums}"
        assert is_sidon(S)


# ---------------------------------------------------------------------------
# TestSquaresUpTo
# ---------------------------------------------------------------------------

class TestSquaresUpTo:
    def test_small(self):
        assert squares_up_to(1) == [1]
        assert squares_up_to(2) == [1, 4]
        assert squares_up_to(3) == [1, 4, 9]
        assert squares_up_to(5) == [1, 4, 9, 16, 25]

    def test_values_are_squares(self):
        for x in squares_up_to(20):
            root = math.isqrt(x)
            assert root * root == x

    def test_length(self):
        for n in range(1, 15):
            assert len(squares_up_to(n)) == n


# ---------------------------------------------------------------------------
# TestMaxSidonExhaustive -- ground truth for small n
# ---------------------------------------------------------------------------

class TestMaxSidonExhaustive:
    """Verify exhaustive search gives correct results for small n."""

    def test_n1(self):
        """Only {1}; a(1) = 1."""
        S, size = max_sidon_in_squares_exhaustive(1)
        assert size == 1
        assert S == {1}
        assert is_sidon(S)

    def test_n2(self):
        """{1, 4}: sums 2, 5, 8 -- all distinct. a(2) = 2."""
        S, size = max_sidon_in_squares_exhaustive(2)
        assert size == 2
        assert is_sidon(S)
        verify_all_squares(S)

    def test_n3(self):
        """{1, 4, 9}: sums 2, 5, 8, 10, 13, 18 -- all distinct. a(3) = 3."""
        S, size = max_sidon_in_squares_exhaustive(3)
        assert size == 3
        assert is_sidon(S)
        verify_all_squares(S)

    def test_n4(self):
        """{1, 4, 9, 16}: all 10 sums distinct. a(4) = 4."""
        # Verify: 2,5,8,10,13,17,18,20,25,32 -- all distinct
        S, size = max_sidon_in_squares_exhaustive(4)
        assert size == 4
        assert is_sidon(S)
        verify_all_squares(S)

    def test_n5(self):
        """Check a(5). {1,4,9,16,25}: 1+25=26, 4+25=29, 9+25=34, 16+25=41,
        25+25=50, plus previous 10 sums. Need to check for collisions."""
        S, size = max_sidon_in_squares_exhaustive(5)
        assert size >= 4  # At least {1,4,9,16} is Sidon
        assert is_sidon(S)
        verify_all_squares(S)
        # All elements should be from {1, 4, 9, 16, 25}
        assert S.issubset({1, 4, 9, 16, 25})

    def test_results_are_sidon(self):
        """For n=1..12, the output must be a valid Sidon set of squares."""
        for n in range(1, 13):
            S, size = max_sidon_in_squares_exhaustive(n)
            assert is_sidon(S), f"n={n}: {S} is not Sidon"
            verify_all_squares(S)
            assert len(S) == size


# ---------------------------------------------------------------------------
# TestMaxSidonInSquares -- main solver
# ---------------------------------------------------------------------------

class TestMaxSidonInSquares:
    """Test the primary max_sidon_in_squares function."""

    def test_n0(self):
        S, size = max_sidon_in_squares(0)
        assert size == 0
        assert S == set()

    def test_n1(self):
        S, size = max_sidon_in_squares(1)
        assert size == 1

    def test_result_is_sidon(self):
        """All results must be Sidon sets of perfect squares."""
        for n in range(1, 25):
            S, size = max_sidon_in_squares(n)
            assert is_sidon(S), f"n={n}: {S} is not Sidon"
            verify_all_squares(S)
            assert len(S) == size

    def test_agrees_with_exhaustive(self):
        """For small n, backtracking must match exhaustive results."""
        for n in range(1, 13):
            _, size_bt = max_sidon_in_squares(n)
            _, size_ex = max_sidon_in_squares_exhaustive(n)
            assert size_bt == size_ex, (
                f"n={n}: backtracking={size_bt}, exhaustive={size_ex}"
            )

    def test_subset_of_squares(self):
        """Every element in the result must be a square in {1^2, ..., n^2}."""
        for n in [5, 10, 15, 20]:
            S, _ = max_sidon_in_squares(n)
            valid = set(squares_up_to(n))
            assert S.issubset(valid), f"n={n}: {S - valid} not in squares"

    def test_larger_n_completes(self):
        """Verify the solver terminates for moderate n."""
        S, size = max_sidon_in_squares(40)
        assert size >= 4
        assert is_sidon(S)


# ---------------------------------------------------------------------------
# TestGreedySidonSquares
# ---------------------------------------------------------------------------

class TestGreedySidonSquares:
    def test_output_is_sidon(self):
        for n in [10, 20, 50]:
            sq = squares_up_to(n)
            S = _greedy_sidon_squares(sq)
            assert is_sidon(S), f"n={n}: greedy {S} is not Sidon"

    def test_output_are_squares(self):
        sq = squares_up_to(30)
        S = _greedy_sidon_squares(sq)
        verify_all_squares(S)

    def test_nonempty(self):
        sq = squares_up_to(10)
        S = _greedy_sidon_squares(sq)
        assert len(S) >= 1


# ---------------------------------------------------------------------------
# TestSidonSquaresSequence
# ---------------------------------------------------------------------------

class TestSidonSquaresSequence:
    def test_starts_at_zero(self):
        seq = sidon_squares_sequence(5)
        assert seq[0] == 0

    def test_a1(self):
        seq = sidon_squares_sequence(5)
        assert seq[1] == 1

    def test_non_decreasing(self):
        """a(n) <= a(n+1) since {1^2,...,n^2} subset of {1^2,...,(n+1)^2}."""
        seq = sidon_squares_sequence(20)
        for i in range(1, len(seq) - 1):
            assert seq[i] <= seq[i + 1], (
                f"a({i})={seq[i]} > a({i+1})={seq[i+1]} -- not non-decreasing"
            )

    def test_length(self):
        seq = sidon_squares_sequence(10)
        assert len(seq) == 11  # indices 0..10

    def test_lower_bound(self):
        """a(n) >= 1 for all n >= 1 (at least one square is Sidon)."""
        seq = sidon_squares_sequence(15)
        for n in range(1, 16):
            assert seq[n] >= 1

    def test_upper_bound_trivial(self):
        """a(n) <= n (cannot have more than n elements from an n-element set)."""
        seq = sidon_squares_sequence(15)
        for n in range(1, 16):
            assert seq[n] <= n


# ---------------------------------------------------------------------------
# TestAnalyzeSidonSquares
# ---------------------------------------------------------------------------

class TestAnalyzeSidonSquares:
    @pytest.fixture(scope="class")
    def analysis(self):
        return analyze_sidon_squares(20)

    def test_has_sequence(self, analysis):
        assert "sequence" in analysis
        assert len(analysis["sequence"]) == 21

    def test_has_ratios(self, analysis):
        assert "ratios" in analysis
        assert "a(n)/sqrt(n)" in analysis["ratios"]
        assert "a(n)/n" in analysis["ratios"]

    def test_has_regression(self, analysis):
        assert "regression" in analysis
        reg = analysis["regression"]
        assert "alpha" in reg
        assert "C" in reg
        # Exponent should be between 0.3 and 1.1
        assert 0.3 <= reg["alpha"] <= 1.1, (
            f"alpha={reg['alpha']} out of plausible range"
        )

    def test_ratios_positive(self, analysis):
        for name, pairs in analysis["ratios"].items():
            for n, r in pairs:
                assert r > 0, f"Ratio {name} at n={n} is non-positive"


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_is_sidon_empty(self):
        assert is_sidon(set())

    def test_is_sidon_single_element(self):
        assert is_sidon({49})

    def test_max_sidon_n0(self):
        S, size = max_sidon_in_squares(0)
        assert size == 0
        assert S == set()

    def test_max_sidon_n1_returns_one(self):
        S, size = max_sidon_in_squares(1)
        assert size == 1
        assert 1 in S

    def test_squares_up_to_zero(self):
        """Edge case: n=0 should return empty list."""
        # squares_up_to uses range(1, n+1) so n=0 -> range(1,1) = []
        assert squares_up_to(0) == []

    def test_large_square_is_sidon_element(self):
        """A single large square is trivially Sidon."""
        assert is_sidon({10000})

    def test_two_large_squares(self):
        """{100, 10000} is Sidon: sums 200, 10100, 20000 -- all distinct."""
        assert is_sidon({100, 10000})

    def test_sequence_consistent_with_max(self):
        """sidon_squares_sequence must agree with max_sidon_in_squares."""
        seq = sidon_squares_sequence(10)
        for n in range(1, 11):
            _, size = max_sidon_in_squares(n)
            assert seq[n] == size, f"n={n}: seq={seq[n]}, direct={size}"
