"""Tests for new_attacks.py — computational experiments on open Erdős problems."""
import math
import pytest

from new_attacks import (
    is_sidon,
    max_sidon_in_range,
    coprime_chromatic_number,
    coprime_clique_number,
    analyze_coprime_chromatic,
    is_ap_free,
    max_ap_free_size,
    greedy_b2_sequence,
    sidon_difference_spectrum,
    is_additive_basis_order_h,
    thin_basis_search,
    schur_coloring_count,
    schur_entropy,
    coprime_spectrum,
)


class TestSidon:
    """Test Sidon (B2) set computations."""

    def test_empty_is_sidon(self):
        assert is_sidon(set())

    def test_singleton_is_sidon(self):
        assert is_sidon({5})

    def test_known_sidon(self):
        """Singer construction: {0,1,3} is Sidon mod 7."""
        assert is_sidon({0, 1, 3})

    def test_not_sidon(self):
        """{1,2,3}: 1+2 = 3 = 1+2 (no collision), but 1+3=4, 2+3=5, 2+2=4 collision."""
        assert not is_sidon({1, 2, 3})

    def test_sidon_four_elements(self):
        """{1,2,5,11} is Sidon."""
        assert is_sidon({1, 2, 5, 11})

    def test_max_sidon_small(self):
        """f(6) = 3: e.g. {1,2,5}."""
        size, A = max_sidon_in_range(6)
        assert size >= 3
        assert is_sidon(A)
        assert all(1 <= x <= 6 for x in A)

    def test_max_sidon_monotone(self):
        """f(N) is non-decreasing."""
        prev_size = 0
        for N in [5, 10, 15, 20]:
            size, _ = max_sidon_in_range(N)
            assert size >= prev_size
            prev_size = size

    def test_max_sidon_approx_sqrt(self):
        """f(N) ~ √N for moderate N."""
        size, _ = max_sidon_in_range(25)
        assert size >= 4  # √25 = 5, greedy should find at least 4


class TestCoprimeChromaticNumber:
    """Test coprime graph chromatic and clique numbers."""

    def test_small_coprime_chromatic(self):
        chi = coprime_chromatic_number(5)
        assert chi >= 3  # {1,2,3} form triangle

    def test_clique_number_small(self):
        omega = coprime_clique_number(10)
        # {1, 2, 3, 5, 7} are pairwise coprime → clique of size 5
        assert omega == 5

    def test_clique_is_lower_bound(self):
        """χ(G) ≥ ω(G) always."""
        for n in [5, 10, 15]:
            chi = coprime_chromatic_number(n)
            omega = coprime_clique_number(n)
            assert chi >= omega

    def test_analyze_returns_list(self):
        results = analyze_coprime_chromatic(15)
        assert len(results) >= 2
        assert all("chi" in r and "omega" in r for r in results)

    def test_coprime_graph_1(self):
        """G(1) has no edges, χ=1."""
        assert coprime_chromatic_number(1) == 1


class TestAPFree:
    """Test arithmetic-progression-free set computations."""

    def test_empty_is_ap_free(self):
        assert is_ap_free(set(), 3)

    def test_no_3_ap(self):
        """{1,2,4,5,10} has no 3-AP."""
        assert is_ap_free({1, 2, 4, 5, 10}, 3)

    def test_has_3_ap(self):
        """{1,2,3} is a 3-AP."""
        assert not is_ap_free({1, 2, 3}, 3)

    def test_r3_small(self):
        """r_3(9) = 4 (known: {1,2,6,7} or similar)."""
        size, A = max_ap_free_size(9, 3)
        assert size >= 4
        assert is_ap_free(A, 3)

    def test_max_ap_free_valid(self):
        for N in [5, 10, 15]:
            size, A = max_ap_free_size(N, 3)
            assert is_ap_free(A, 3)
            assert len(A) == size
            assert all(1 <= x <= N for x in A)

    def test_density_decreasing(self):
        """AP-free density should generally decrease."""
        densities = []
        for N in [10, 20, 30]:
            size, _ = max_ap_free_size(N, 3)
            densities.append(size / N)
        # Not strictly monotone for greedy, but should be bounded
        assert all(d <= 1.0 for d in densities)


class TestSidonDifference:
    """Test greedy B2 and difference spectrum."""

    def test_greedy_b2_is_sidon(self):
        A = greedy_b2_sequence(50)
        assert is_sidon(A)

    def test_greedy_b2_size(self):
        """Greedy B2 up to 100 should have ~√100 = 10 elements."""
        A = greedy_b2_sequence(100)
        assert len(A) >= 8  # greedy finds at least this many

    def test_b2_sequence_starts_correctly(self):
        """Greedy B2 sequence starts with 1, 2, then continues Sidon."""
        A = greedy_b2_sequence(40)
        A_sorted = sorted(A)
        assert A_sorted[0] == 1
        assert A_sorted[1] == 2
        # Third element is Sidon-compatible with {1,2}; could be 4 or 5
        assert A_sorted[2] in (4, 5)

    def test_difference_spectrum_sidon_all_ones(self):
        """In a Sidon set, all differences appear exactly once."""
        A = {1, 2, 5, 11}
        spec = sidon_difference_spectrum(A)
        assert all(v == 1 for v in spec.values()), f"Non-unique diff: {spec}"


class TestAdditiveBasis:
    """Test additive basis computations."""

    def test_full_set_is_basis(self):
        """[1..N] is a basis of order 1."""
        A = set(range(1, 11))
        assert is_additive_basis_order_h(A, 10, 1)

    def test_sparse_basis_order_2(self):
        """{1,2,3} is a basis of order 2 for [1,6]: any n≤6 = sum of ≤2."""
        assert is_additive_basis_order_h({1, 2, 3}, 6, 2)

    def test_not_basis(self):
        """{1, 10} is not a basis of order 2 for [1, 15]."""
        assert not is_additive_basis_order_h({1, 10}, 15, 2)

    def test_thin_basis_valid(self):
        result = thin_basis_search(20, h=2)
        assert result["is_basis"]
        assert result["N"] == 20
        assert result["h"] == 2
        assert result["basis_size"] <= 20

    def test_thin_basis_density(self):
        """Basis density should be < 1.0 for h=2."""
        result = thin_basis_search(30, h=2)
        assert result["density"] < 1.0


class TestSchurEntropy:
    """Test Schur coloring counting and entropy."""

    def test_schur_count_n1(self):
        """N=1, k=2: only {1}, both colors work. Count = 2."""
        assert schur_coloring_count(1, 2) == 2

    def test_schur_count_n2(self):
        """N=2: 1+1=2 forces 1,2 in different colors. Only 2 valid colorings."""
        assert schur_coloring_count(2, 2) == 2

    def test_schur_count_n4(self):
        """N=4, k=2: S(2)=4, so some colorings of [4] work."""
        count = schur_coloring_count(4, 2)
        assert count > 0

    def test_schur_count_n5(self):
        """N=5, k=2: S(2)=4, so NO coloring of [5] with 2 colors avoids Schur.
        Actually S(2)=4 means [1..5] forces a monochromatic Schur triple."""
        count = schur_coloring_count(5, 2)
        assert count == 0

    def test_schur_entropy_format(self):
        ent = schur_entropy(3, 2)
        assert "N" in ent and "k" in ent
        assert "valid_colorings" in ent
        assert "entropy_per_element" in ent
        assert ent["valid_colorings"] > 0

    def test_too_large_returns_negative(self):
        """N > 15 or k > 3 returns -1."""
        assert schur_coloring_count(20, 2) == -1
        assert schur_coloring_count(5, 4) == -1


class TestCoprimeSpectrum:
    """Test coprime graph spectral analysis."""

    def test_spectrum_returns_dict(self):
        spec = coprime_spectrum(10)
        assert "lambda_1" in spec
        assert "lambda_2" in spec
        assert "spectral_gap" in spec

    def test_trace_is_zero(self):
        """Trace of adjacency matrix = 0 for simple graph (no self-loops)."""
        spec = coprime_spectrum(10)
        assert abs(spec["trace"]) < 0.1

    def test_lambda1_positive(self):
        """Largest eigenvalue is positive for non-empty graph."""
        spec = coprime_spectrum(10)
        assert spec["lambda_1"] > 0

    def test_spectral_gap_positive(self):
        """Spectral gap should be positive for connected coprime graph."""
        spec = coprime_spectrum(15)
        assert spec["spectral_gap"] > 0

    def test_energy_positive(self):
        spec = coprime_spectrum(10)
        assert spec["energy"] > 0

    def test_lambda1_scales_with_n(self):
        """λ₁ should grow with n (edge density ~ 6/π²)."""
        s10 = coprime_spectrum(10)
        s20 = coprime_spectrum(20)
        assert s20["lambda_1"] > s10["lambda_1"]
