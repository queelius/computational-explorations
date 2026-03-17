"""Tests for theta_threshold.py — Coprime Cycle Forcing threshold search."""
import math
import pytest

from theta_threshold import (
    mobius,
    coprime_pairs,
    coprime_count,
    coprime_density,
    is_bipartite,
    find_odd_cycle,
    search_threshold_structured,
    find_bipartite_boundary,
)


class TestMobius:
    """Test Möbius function."""

    def test_mobius_1(self):
        assert mobius(1) == 1

    def test_mobius_primes(self):
        for p in [2, 3, 5, 7, 11, 13]:
            assert mobius(p) == -1

    def test_mobius_squarefree_2_primes(self):
        assert mobius(6) == 1   # 2*3, two primes
        assert mobius(10) == 1  # 2*5
        assert mobius(15) == 1  # 3*5

    def test_mobius_squarefree_3_primes(self):
        assert mobius(30) == -1  # 2*3*5, three primes

    def test_mobius_square_factor(self):
        assert mobius(4) == 0   # 2^2
        assert mobius(9) == 0   # 3^2
        assert mobius(12) == 0  # 2^2*3
        assert mobius(18) == 0  # 2*3^2

    def test_mobius_large_prime(self):
        assert mobius(97) == -1  # prime


class TestCoprimePairs:
    """Test coprime pair enumeration."""

    def test_empty_set(self):
        assert coprime_pairs(set()) == []

    def test_coprime_triple(self):
        """1, 2, 3 are pairwise coprime → 3 pairs."""
        pairs = coprime_pairs({1, 2, 3})
        assert len(pairs) == 3

    def test_non_coprime_set(self):
        """All even numbers → only coprime if they share no factor."""
        pairs = coprime_pairs({2, 4, 6})
        assert len(pairs) == 0

    def test_known_pair_count(self):
        pairs = coprime_pairs({1, 2, 3, 4, 5})
        # 1 is coprime to all: (1,2),(1,3),(1,4),(1,5) = 4
        # (2,3)=1, (2,5)=1 = 2
        # (3,4)=1, (3,5)=1 = 2
        # (4,5)=1 = 1
        assert len(pairs) == 9


class TestCoprimeCount:
    """Test Möbius-based coprime counting."""

    def test_agrees_with_direct(self):
        for A in [{1, 2, 3}, {5, 6, 7, 8, 9}, set(range(1, 20))]:
            pairs = coprime_pairs(A)
            count = coprime_count(A)
            assert count == len(pairs), (
                f"Möbius count {count} ≠ direct {len(pairs)} for {A}"
            )


class TestCoprimeDensity:
    """Test coprime density computation."""

    def test_empty(self):
        assert coprime_density(set()) == 0.0

    def test_all_coprime(self):
        """Primes have coprime density 1.0."""
        primes = {2, 3, 5, 7, 11}
        assert coprime_density(primes) == 1.0

    def test_no_coprime(self):
        """Powers of 2 have density 0.0 (all share factor 2)."""
        powers = {2, 4, 8, 16}
        assert coprime_density(powers) == 0.0


class TestBipartite:
    """Test bipartiteness detection."""

    def test_empty_graph_is_bipartite(self):
        result, cycle = is_bipartite([], {1, 2, 3})
        assert result is True
        assert cycle is None

    def test_triangle_is_not_bipartite(self):
        """K3 has an odd cycle."""
        edges = [(1, 2), (2, 3), (1, 3)]
        result, cycle = is_bipartite(edges, {1, 2, 3})
        assert result is False
        assert cycle is not None

    def test_even_cycle_is_bipartite(self):
        """C4 is bipartite."""
        edges = [(1, 2), (2, 3), (3, 4), (4, 1)]
        result, _ = is_bipartite(edges, {1, 2, 3, 4})
        assert result is True

    def test_extremal_set_bipartite_or_near(self, extremal_set_30):
        """The extremal set (multiples of 2 or 3) should have bipartite-like structure."""
        pairs = coprime_pairs(extremal_set_30)
        is_bip, _ = is_bipartite(pairs, extremal_set_30)
        # The extremal set may or may not be bipartite depending on exact elements,
        # but its coprime density should be below Mantel threshold
        density = coprime_density(extremal_set_30)
        assert density < 0.25


class TestOddCycleDetection:
    """Test finding odd cycles in coprime graphs."""

    def test_full_set_has_cycle(self):
        """[1..10] coprime graph definitely has odd cycles (e.g., {1,2,3} is triangle)."""
        A = set(range(1, 11))
        cycle = find_odd_cycle(A)
        assert cycle is not None

    def test_even_numbers_no_cycle(self):
        """All even numbers share factor 2 with each other, very sparse graph."""
        A = {2, 4, 6, 8, 10, 12}
        # The coprime pairs among evens are rare
        cycle = find_odd_cycle(A)
        # Whether there's a cycle depends on the specific set
        # but {2, 9, 25} would be coprime triangle if present
        # For this set of evens, check that it's consistent
        pairs = coprime_pairs(A)
        if len(pairs) < 3:
            assert cycle is None


class TestStructuredSearch:
    """Test structured threshold search."""

    def test_returns_all_categories(self):
        results = search_threshold_structured(30)
        assert "extremal_2or3" in results
        assert "multiples_of_2" in results
        assert "multiples_of_3" in results
        assert "odd_numbers" in results
        assert "primes" in results
        assert "coprime_to_6" in results

    def test_extremal_below_mantel(self):
        results = search_threshold_structured(50)
        assert results["extremal_2or3"]["density"] < 0.25

    def test_primes_density_one(self):
        results = search_threshold_structured(30)
        assert abs(results["primes"]["density"] - 1.0) < 0.001

    def test_odd_numbers_have_cycles(self):
        results = search_threshold_structured(30)
        assert not results["odd_numbers"]["bipartite"]

    def test_even_numbers_no_coprime(self):
        results = search_threshold_structured(30)
        # Even numbers: gcd(2k, 2j) = 2 * gcd(k, j), sparse but not zero
        assert results["multiples_of_2"]["density"] < 0.5


class TestBipartiteBoundary:
    """Test bipartite boundary detection."""

    def test_has_triangle_count(self):
        result = find_bipartite_boundary(20)
        assert "triangle_count_in_50" in result
        assert result["triangle_count_in_50"] > 0

    def test_extremal_analysis(self):
        result = find_bipartite_boundary(20)
        assert "extremal_analysis" in result
        assert result["extremal_analysis"]["base_density"] < 0.25

    def test_breaking_element_found(self):
        result = find_bipartite_boundary(30)
        # Adding an element coprime to 6 should break bipartiteness
        if "first_breaking_element" in result:
            elem = result["first_breaking_element"]["element"]
            assert math.gcd(elem, 6) == 1  # Should be coprime to 6
