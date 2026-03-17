"""Tests for sidon_disjoint.py — Problem #43: Sidon sets with disjoint differences."""
import math
import pytest

from sidon_disjoint import (
    is_sidon,
    difference_set,
    are_diff_disjoint,
    num_pairs,
    singer_sidon,
    random_sidon,
    compatible_sidon,
    exhaustive_search,
    greedy_sidon_pair,
    find_optimal_sidon_pair,
)


class TestIsSidon:
    """Test Sidon set validation."""

    def test_empty_is_sidon(self):
        assert is_sidon(set())

    def test_singleton_is_sidon(self):
        assert is_sidon({5})

    def test_pair_is_sidon(self):
        assert is_sidon({1, 3})

    def test_known_sidon(self):
        """The set {0, 1, 3} is Sidon: sums 0+0=0, 0+1=1, 0+3=3, 1+1=2, 1+3=4, 3+3=6 — all distinct."""
        assert is_sidon({0, 1, 3})

    def test_known_not_sidon(self):
        """{0, 1, 2, 3}: 0+3=3 and 1+2=3 — repeated sum."""
        assert not is_sidon({0, 1, 2, 3})

    def test_singer_constructions(self):
        """Singer Sidon sets should be valid."""
        for q in [2, 3, 4]:
            S = singer_sidon(q)
            if S:
                assert is_sidon(S), f"Singer(q={q})={S} should be Sidon"


class TestDifferenceSet:
    """Test difference set computation."""

    def test_singleton(self):
        """A-A = {0} for singleton."""
        assert difference_set({5}) == {0}

    def test_pair(self):
        """{a, b}: A-A = {0, a-b, b-a}."""
        diffs = difference_set({1, 4})
        assert diffs == {0, 3, -3}

    def test_sidon_diff_size(self):
        """For Sidon A, |A-A| = |A|²-|A|+1."""
        A = {0, 1, 3}  # Sidon set
        diffs = difference_set(A)
        expected = len(A)**2 - len(A) + 1
        assert len(diffs) == expected, (
            f"|A-A|={len(diffs)}, expected {expected}"
        )


class TestDiffDisjoint:
    """Test disjoint difference property."""

    def test_disjoint_simple(self):
        """Disjoint difference: intersection is {0}."""
        A = {1, 3}  # A-A = {0, 2, -2}
        B = {5, 8}  # B-B = {0, 3, -3}
        assert are_diff_disjoint(A, B)

    def test_not_disjoint(self):
        A = {1, 4}  # A-A = {0, 3, -3}
        B = {2, 5}  # B-B = {0, 3, -3}
        assert not are_diff_disjoint(A, B)


class TestNumPairs:
    """Test C(n,2) computation."""

    def test_known_values(self):
        assert num_pairs(set()) == 0
        assert num_pairs({1}) == 0
        assert num_pairs({1, 2}) == 1
        assert num_pairs({1, 2, 3}) == 3
        assert num_pairs({1, 2, 3, 4}) == 6
        assert num_pairs({1, 2, 3, 4, 5}) == 10


class TestRandomSidon:
    """Test random Sidon set generation."""

    def test_output_is_sidon(self):
        """Random Sidon generator should produce valid Sidon sets."""
        for _ in range(10):
            A = random_sidon(50)
            assert is_sidon(A), f"Random Sidon {A} is not Sidon"

    def test_nonempty(self):
        A = random_sidon(50)
        assert len(A) > 0


class TestCompatibleSidon:
    """Test finding compatible Sidon sets."""

    def test_produces_valid_sidon(self):
        A = {0, 1, 3}
        B = compatible_sidon(A, 20)
        if B:
            assert is_sidon(B), f"Compatible {B} is not Sidon"

    def test_disjoint_diffs(self):
        A = {0, 1, 3}
        B = compatible_sidon(A, 20)
        if B:
            assert are_diff_disjoint(A, B)


class TestGreedySidonPair:
    """Test greedy Sidon pair construction."""

    def test_produces_valid_sidon_sets(self):
        A, B = greedy_sidon_pair(20)
        if A:
            assert is_sidon(A), f"A={A} is not Sidon"
        if B:
            assert is_sidon(B), f"B={B} is not Sidon"

    def test_produces_disjoint_diffs(self):
        A, B = greedy_sidon_pair(20)
        if A and B:
            assert are_diff_disjoint(A, B), f"A={A}, B={B} not diff-disjoint"

    def test_nonempty_for_moderate_n(self):
        A, B = greedy_sidon_pair(30)
        assert len(A) > 0, "greedy should produce nonempty A"


class TestFindOptimalSidonPair:
    """Test optimal Sidon pair finder."""

    def test_returns_correct_total(self):
        A, B, total = find_optimal_sidon_pair(15, max_attempts=100)
        assert total == num_pairs(A) + num_pairs(B)

    def test_optimal_beats_single_pair(self):
        A, B, total = find_optimal_sidon_pair(20, max_attempts=200)
        # Should find at least a non-trivial solution
        assert total >= 1, "should find at least one pair of Sidon sets"


class TestExhaustiveSearch:
    """Test exhaustive search for small N."""

    def test_conjecture_holds_small(self):
        """Problem #43 conjecture should hold for small N."""
        for N in range(5, 11):
            result = exhaustive_search(N)
            assert result["conjecture_holds"], (
                f"N={N}: conjecture violated! "
                f"total={result['total_pairs']}, bound={result['conjectured_bound']}"
            )

    def test_finds_sidon_sets(self):
        result = exhaustive_search(8)
        assert result["sidon_sets_found"] > 0

    def test_rejects_large_n(self):
        result = exhaustive_search(20)
        assert "error" in result
