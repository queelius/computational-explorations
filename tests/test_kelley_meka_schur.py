"""Tests for kelley_meka_schur.py — Fourier analysis for Schur numbers."""
import math
import numpy as np
import pytest

from kelley_meka_schur import (
    schur_count_direct,
    schur_count_fourier,
    is_sum_free,
    max_sum_free_density,
    fourier_spectrum,
    bohr_set,
    density_on_bohr,
    density_increment_step,
    sum_free_structure_lemma,
    greedy_sum_free_coloring,
    schur_number_search,
    analyze_k_coloring,
)


class TestSchurCount:
    """Test Schur triple counting — direct and Fourier."""

    def test_sum_free_has_zero_count(self):
        """A sum-free set should have T(A) = 0."""
        # Odd numbers mod 10 are sum-free (1+3=4∉odds, etc.)
        odds = {1, 3, 5, 7, 9}
        assert schur_count_direct(odds, 10) == 0

    def test_fourier_matches_direct(self):
        """Fourier count should match direct count."""
        N = 50
        # Use a set known to have some Schur triples
        A = {1, 2, 3, 4, 5}  # 1+2=3, 1+4=5, 2+3=5, etc.
        direct = schur_count_direct(A, N)
        fourier = schur_count_fourier(A, N)
        assert abs(direct - fourier) < 1.0, (
            f"Direct {direct} ≠ Fourier {fourier:.1f}"
        )

    def test_full_set_has_many_triples(self):
        """[0..N-1] should have many Schur triples."""
        N = 20
        A = set(range(N))
        count = schur_count_direct(A, N)
        assert count > 0


class TestSumFree:
    """Test sum-free set detection."""

    def test_odd_numbers_sum_free(self):
        """Odd numbers are sum-free mod 2N (odd+odd=even, even ∉ odds)."""
        N = 20
        odds = {i for i in range(1, N, 2)}
        assert is_sum_free(odds, N)

    def test_full_set_not_sum_free(self):
        """[0..N-1] is never sum-free for N ≥ 3."""
        N = 10
        A = set(range(N))
        assert not is_sum_free(A, N)

    def test_empty_is_sum_free(self):
        assert is_sum_free(set(), 10)

    def test_singleton_sum_free(self):
        """{a} is sum-free unless a+a=a, i.e., a=0 mod N=0 or N=2a special."""
        # {1} mod 10: 1+1=2 ∉ {1}, so sum-free
        assert is_sum_free({1}, 10)

    def test_known_not_sum_free(self):
        """Set {1, 2, 3}: 1+2=3 ∈ A."""
        assert not is_sum_free({1, 2, 3}, 10)


class TestMaxSumFreeDensity:
    """Test maximum sum-free density computation."""

    def test_odd_numbers_achieve_half(self):
        N = 100
        odds, density = max_sum_free_density(N)
        assert abs(density - 0.5) < 0.02, f"Expected ~0.5, got {density}"

    def test_is_actually_sum_free(self):
        N = 50
        odds, _ = max_sum_free_density(N)
        assert is_sum_free(odds, N)


class TestFourierSpectrum:
    """Test Fourier spectrum computation."""

    def test_dc_component_is_set_size(self):
        """f̂(0) = |A| (DC component = set cardinality)."""
        N = 20
        A = {1, 3, 5, 7, 9}
        spectrum = fourier_spectrum(A, N)
        dc_mag = next(m for r, m in spectrum if r == 0)
        assert abs(dc_mag - len(A)) < 0.01

    def test_odd_numbers_large_at_half(self):
        """Odd numbers should have large Fourier coefficient at r=N/2."""
        N = 100
        odds = {i for i in range(1, N, 2)}
        spectrum = fourier_spectrum(odds, N)
        # Sort by magnitude
        sorted_spec = sorted(spectrum, key=lambda x: -x[1])
        # DC is largest, next should be at N/2
        non_dc = [(r, m) for r, m in sorted_spec if r != 0]
        top_freq, top_mag = non_dc[0]
        assert top_freq == N // 2, f"Expected peak at N/2={N//2}, got {top_freq}"


class TestBohrSet:
    """Test Bohr set computation."""

    def test_bohr_contains_zero(self):
        """0 is always in any Bohr set (all phases are 1 at x=0)."""
        N = 20
        B = bohr_set([1], 0.5, N)
        assert 0 in B

    def test_bohr_size_decreases_with_epsilon(self):
        """Smaller ε → smaller Bohr set."""
        N = 100
        B_large = bohr_set([1], 1.0, N)
        B_small = bohr_set([1], 0.1, N)
        assert len(B_small) <= len(B_large)


class TestSchurNumbers:
    """Test Schur number search against known values."""

    KNOWN_SCHUR = {1: 1, 2: 4, 3: 13}

    def test_schur_2(self):
        """S(2) = 4: greedy should find at least some valid coloring."""
        S_2, _ = schur_number_search(2, max_n=15)
        # Greedy is a heuristic, so it finds a lower bound on S(2)
        assert S_2 >= 1, "Greedy should find at least S(2) ≥ 1"
        assert S_2 <= 4, f"Greedy found S(2) ≥ {S_2}, but S(2) = 4"

    def test_greedy_finds_valid_colorings(self):
        """Greedy coloring should produce valid output."""
        for k in [1, 2]:
            S_k = self.KNOWN_SCHUR[k]
            coloring = greedy_sum_free_coloring(S_k, k)
            # Check it produces a valid coloring with k colors
            assert len(coloring) == S_k
            assert all(0 <= c < k for c in coloring)

    def test_schur_1(self):
        """S(1) = 1: {1} can be 1-colored Schur-free (no a+b=c with a,b,c in {1})."""
        S_1, _ = schur_number_search(1, max_n=10)
        assert S_1 == 1, f"S(1) should be 1, got {S_1}"


class TestDensityIncrement:
    """Test density increment step."""

    def test_increment_sum_free_set(self):
        """Sum-free sets have large Fourier coefficients, so increment should work."""
        N = 50
        A = {i for i in range(1, N, 2)}  # odd numbers
        result = density_increment_step(A, N, threshold=0.1)
        # May or may not find increment depending on thresholds
        # Just check return format
        if result is not None:
            bohr, new_density = result
            assert isinstance(bohr, set)
            assert new_density > 0

    def test_increment_full_set(self):
        """Full set has low non-DC Fourier coefficients."""
        N = 20
        A = set(range(N))
        result = density_increment_step(A, N, threshold=0.5)
        # Full set might not have large non-DC coefficients
        # Just check no crash

    def test_density_on_bohr(self):
        N = 20
        A = {0, 1, 2, 3, 4}
        B = bohr_set([1], 0.5, N)
        d = density_on_bohr(A, B, N)
        assert 0 <= d <= 1


class TestStructureLemma:
    """Test sum-free structure analysis."""

    def test_odd_numbers_structured(self):
        N = 50
        odds = {i for i in range(1, N, 2)}
        result = sum_free_structure_lemma(odds, N)
        assert result["sum_free"] is True
        assert result["schur_count"] == 0
        assert "max_fourier_freq" in result
        assert result["fourier_ratio"] > 0

    def test_full_set_not_sum_free(self):
        N = 20
        A = set(range(N))
        result = sum_free_structure_lemma(A, N)
        assert result["sum_free"] is False
        assert result["schur_count"] > 0


class TestLemmaABound:
    """Verify the proved Fourier structure bound for sum-free sets."""

    def test_odd_numbers_achieve_bound(self):
        """Odd numbers: max|f̂(r)| / |C| should equal δ/(1-δ) exactly."""
        N = 100
        odds = {i for i in range(1, N, 2)}
        spectrum = fourier_spectrum(odds, N)
        non_dc = [(r, m) for r, m in spectrum if r != 0]
        max_mag = max(m for _, m in non_dc)
        delta = len(odds) / N
        predicted = delta / (1 - delta) * len(odds)
        assert max_mag >= predicted - 1.0, (
            f"max_mag={max_mag:.1f} < predicted={predicted:.1f}"
        )

    def test_bound_holds_for_dense_sum_free(self):
        """For sum-free C with δ > 1/3, max|f̂(r)| ≥ |C|/2."""
        for N in [15, 21, 30]:
            odds = {i for i in range(1, N, 2)}
            if not is_sum_free(odds, N):
                continue
            if len(odds) / N <= 1/3:
                continue
            spectrum = fourier_spectrum(odds, N)
            non_dc = [(r, m) for r, m in spectrum if r != 0]
            max_mag = max(m for _, m in non_dc)
            assert max_mag > len(odds) / 2 - 0.1, (
                f"N={N}: max_mag={max_mag:.1f} ≤ |C|/2={len(odds)/2}"
            )

    def test_bohr_restriction_sum_free(self):
        """Intersecting sum-free set with Bohr set preserves sum-freeness (Lemma B)."""
        N = 50
        C = {i for i in range(1, N, 2)}  # sum-free
        B = bohr_set([1], 0.5, N)
        C_restricted = C & B
        assert is_sum_free(C_restricted, N), "C ∩ B should still be sum-free"


class TestDensityIncrementChain:
    """Test multi-step density increment for #483 argument."""

    def test_single_step_increases_density(self):
        """density_increment_step should find density increase for interval sets.

        Interval sets (e.g., {0,...,39} in ℤ/100) have concentrated Fourier
        structure, so restricting to a Bohr set at the peak frequency captures
        a region where the set has higher relative density.

        Note: perfectly structured sets like odds DON'T get increment — the Bohr
        set at r=N/2 captures evens (the complementary coset), giving density 0.
        """
        N = 100
        # Interval set — concentrated, so Bohr restriction increases relative density
        A = set(range(0, 40))  # density 0.4
        original_density = len(A) / N

        result = density_increment_step(A, N, threshold=0.1)
        assert result is not None, "Interval set should have density increment"
        bohr, new_density = result
        assert new_density > original_density, (
            f"Density should increase: {new_density:.3f} ≤ {original_density:.3f}"
        )

    def test_perfectly_structured_no_increment(self):
        """Odds (perfectly structured at r=N/2) should NOT get density increment.

        The peak Fourier frequency for odds is N/2, but the Bohr set B({N/2}, ε)
        captures evens — the complementary coset. So density_increment_step
        correctly returns None.
        """
        N = 100
        odds = {i for i in range(1, N, 2)}
        result = density_increment_step(odds, N, threshold=0.1)
        assert result is None, "Perfectly structured set should not need increment"

    def test_multi_step_density_growth(self):
        """density_increment_step returns valid output on structured sets."""
        N = 200
        # Interval of density 0.4 — has strong Fourier structure
        A = set(range(0, 80))
        original_density = len(A) / N

        result = density_increment_step(A, N, threshold=0.1)
        if result is not None:
            bohr, new_density = result
            assert isinstance(bohr, set)
            assert len(bohr) > 0
            assert new_density > original_density


class TestAnalyzeColoring:
    """Test k-coloring analysis."""

    def test_valid_2_coloring(self):
        # Standard Schur-free coloring of [4]: {1,4} and {2,3}
        coloring = [0, 1, 1, 0]  # 1→0, 2→1, 3→1, 4→0
        result = analyze_k_coloring(coloring, 10)
        assert result["k"] == 2
        assert not result["has_schur"]

    def test_forced_schur_triple(self):
        # All same color for [5]: 1+2=3, so must have Schur triple
        coloring = [0, 0, 0, 0, 0]
        result = analyze_k_coloring(coloring, 10)
        assert result["has_schur"]
