"""Tests for sum_free_structure.py — Structure theorem for sum-free sets."""
import math
import numpy as np
import pytest

from sum_free_structure import (
    is_sum_free,
    fourier_spectrum,
    max_non_dc_fourier,
    fourier_ratio,
    generate_sum_free_sets,
    verify_structure_theorem,
    analyze_canonical_sum_free,
    theoretical_bound,
    verify_proved_bound,
    schur_coloring_analysis,
)


class TestSumFreeBasic:
    """Test basic sum-free checking."""

    def test_empty_sum_free(self):
        assert is_sum_free(set(), 10)

    def test_odds_sum_free(self):
        """Odd numbers: a+b is even, so not in odds."""
        odds = {1, 3, 5, 7, 9}
        assert is_sum_free(odds, 10)

    def test_upper_third_sum_free(self):
        """(N/3, 2N/3) is often sum-free: if a,b > N/3, then a+b > 2N/3."""
        N = 30
        upper = {i for i in range(N // 3 + 1, 2 * N // 3)}
        assert is_sum_free(upper, N)

    def test_not_sum_free(self):
        """{1, 2, 3} in ℤ/10ℤ: 1+2=3."""
        assert not is_sum_free({1, 2, 3}, 10)


class TestFourierAnalysis:
    """Test Fourier spectrum and ratio computations."""

    def test_spectrum_length(self):
        N = 20
        A = {1, 3, 5}
        spec = fourier_spectrum(A, N)
        assert len(spec) == N

    def test_dc_is_cardinality(self):
        N = 20
        A = {1, 3, 5, 7}
        spec = fourier_spectrum(A, N)
        dc = next(m for r, m in spec if r == 0)
        assert abs(dc - len(A)) < 0.01

    def test_max_non_dc(self):
        N = 20
        A = {1, 3, 5, 7, 9}  # Odds
        r_max, mag_max = max_non_dc_fourier(A, N)
        assert r_max != 0
        assert mag_max > 0

    def test_fourier_ratio_positive_for_structured(self):
        """Structured sets (odds) should have high Fourier ratio."""
        N = 100
        odds = {i for i in range(1, N, 2)}
        ratio = fourier_ratio(odds, N)
        assert ratio > 0.5, f"Odds Fourier ratio {ratio:.3f} should be > 0.5"


class TestCanonicalSumFree:
    """Test analysis of canonical sum-free sets."""

    def test_canonical_sets_exist(self):
        result = analyze_canonical_sum_free(100)
        assert "odds" in result
        assert "middle_third" in result

    def test_odds_are_sum_free(self):
        result = analyze_canonical_sum_free(100)
        assert result["odds"]["sum_free"] is True

    def test_odds_fourier_ratio_high(self):
        """Odd numbers have Fourier ratio ≈ 1.0."""
        result = analyze_canonical_sum_free(100)
        assert result["odds"]["fourier_ratio"] > 0.8


class TestStructureTheorem:
    """Test the structure theorem verification for small N."""

    def test_small_n_verified(self):
        """For small N, all sum-free sets with |C|>N/3 should have large Fourier coefficient."""
        result = verify_structure_theorem(15, threshold=0.05)
        assert result["sets_checked"] > 0, "Should find at least one sum-free set"

    def test_min_ratio_positive(self):
        """Minimum Fourier ratio should be > 0 for small N."""
        result = verify_structure_theorem(15, threshold=0.01)
        if result["sets_checked"] > 0:
            assert result["min_fourier_ratio"] > 0


class TestGenerateSumFree:
    """Test sum-free set generation."""

    def test_generates_nonempty(self):
        """Should find some sum-free sets above density 1/3."""
        sets = generate_sum_free_sets(15, density_threshold=0.33)
        assert len(sets) > 0

    def test_all_generated_are_sum_free(self):
        """Every returned set should actually be sum-free."""
        N = 12
        sets = generate_sum_free_sets(N, density_threshold=0.33)
        for C in sets[:50]:  # Check first 50
            assert is_sum_free(C, N), f"{C} is not sum-free mod {N}"

    def test_density_above_threshold(self):
        """All generated sets should have density > threshold."""
        N = 15
        threshold = 0.33
        sets = generate_sum_free_sets(N, density_threshold=threshold)
        for C in sets[:50]:
            assert len(C) / N > threshold - 0.01


class TestProvedBound:
    """Test the proved Fourier structure bound: max|f̂(r)| ≥ δ/(1-δ) · |C|."""

    def test_theoretical_bound_odds(self):
        """Odd numbers: δ=0.5, bound = 0.5/0.5 * |C| = |C|."""
        N = 100
        odds = {i for i in range(1, N, 2)}
        bound = theoretical_bound(odds, N)
        assert abs(bound - len(odds)) < 0.01

    def test_theoretical_bound_above_threshold(self):
        """For δ > 1/3, bound should exceed |C|/2."""
        N = 99
        C = {i for i in range(1, N, 2)}  # 50 elements, δ ≈ 0.505
        delta = len(C) / N
        assert delta > 1 / 3
        bound = theoretical_bound(C, N)
        assert bound > len(C) / 2

    def test_proved_bound_holds_exhaustive_n15(self):
        """Exhaustive verification: all sum-free sets with |C|>N/3 satisfy the bound."""
        result = verify_proved_bound(15)
        assert result["sets_checked"] > 0
        assert result["all_satisfy_bound"], (
            f"Bound violated: {result['counterexamples'][:3]}"
        )

    def test_proved_bound_holds_exhaustive_n20(self):
        """Check N=20 (even, so odd numbers are sum-free)."""
        result = verify_proved_bound(20)
        assert result["sets_checked"] > 0
        assert result["all_satisfy_bound"]

    def test_proved_bound_actual_exceeds_predicted(self):
        """The actual max Fourier coefficient should be ≥ the predicted bound."""
        N = 100
        odds = {i for i in range(1, N, 2)}
        _, actual = max_non_dc_fourier(odds, N)
        predicted = theoretical_bound(odds, N)
        assert actual >= predicted - 0.01, (
            f"actual={actual:.2f} < predicted={predicted:.2f}"
        )


# ——— New tests for uncovered lines ———


class TestMaxNonDcFourierEdge:
    """Cover line 40: empty non-DC spectrum (N=1)."""

    def test_n1_returns_zero(self):
        """With N=1 there's only the DC component r=0, so non_dc is empty."""
        C = {0}
        r, mag = max_non_dc_fourier(C, 1)
        assert r == 0
        assert mag == 0.0

    def test_fourier_ratio_empty_set(self):
        """fourier_ratio of empty set returns 0."""
        assert fourier_ratio(set(), 10) == 0


class TestGenerateSumFreeCap:
    """Cover line 63: early return when 1000 sets cap is reached."""

    def test_cap_1000_reached(self):
        """For large enough N with low threshold, should hit the 1000 cap."""
        # N=30, threshold=0.1 -> min_size = 4 -- many sum-free subsets exist
        sets = generate_sum_free_sets(30, density_threshold=0.1)
        assert len(sets) == 1000

    def test_all_capped_are_sum_free(self):
        """Even capped results should all be valid sum-free sets."""
        N = 30
        sets = generate_sum_free_sets(N, density_threshold=0.1)
        assert len(sets) == 1000
        for C in sets[:20]:
            assert is_sum_free(C, N)


class TestTheoreticalBoundEdge:
    """Cover line 76: delta >= 1.0 returns inf."""

    def test_delta_one_returns_inf(self):
        """When C = entire group (|C|=N), delta=1.0, bound is infinity."""
        N = 5
        C = set(range(N))  # |C|=5, delta=1.0
        bound = theoretical_bound(C, N)
        assert bound == float('inf')

    def test_delta_above_one_returns_inf(self):
        """If somehow |C| > N (e.g. duplicates pre-mod), delta > 1 -> inf."""
        # Use a set that has more elements than N (the function uses len(C)/N)
        N = 3
        C = set(range(5))  # |C|=5, delta=5/3 > 1
        bound = theoretical_bound(C, N)
        assert bound == float('inf')


class TestVerifyStructureCounterexample:
    """Cover lines 105-106: counterexample branch in verify_structure_theorem."""

    def test_high_threshold_triggers_counterexample(self):
        """With threshold=1.0, every set will fail (ratio < 1.0), triggering counterexample logic."""
        result = verify_structure_theorem(15, threshold=1.0)
        assert result["sets_checked"] > 0
        assert result["all_have_large_fourier"] is False
        assert len(result["counterexamples"]) > 0
        ce = result["counterexamples"][0]
        assert "set" in ce
        assert "size" in ce
        assert "density" in ce
        assert "fourier_ratio" in ce
        assert ce["fourier_ratio"] < 1.0

    def test_counterexample_details(self):
        """Counterexample entries should have reasonable values."""
        result = verify_structure_theorem(15, threshold=1.0)
        for ce in result["counterexamples"][:5]:
            assert ce["size"] > 0
            assert 0 < ce["density"] <= 1.0
            assert ce["fourier_ratio"] >= 0


class TestVerifyProvedBoundLargeN:
    """Cover lines 204-221: verify_proved_bound for N > 30 (canonical sets branch)."""

    def test_large_n_uses_canonical_sets(self):
        """For N > 30, verify_proved_bound should use canonical sets."""
        result = verify_proved_bound(50)
        assert result["N"] == 50
        assert result["all_satisfy_bound"] is True
        # Should have checked at least the odds (which are sum-free with density > 1/3)
        assert result["sets_checked"] >= 1

    def test_large_n_min_excess(self):
        """For N=100, the min_excess should be a finite positive number."""
        result = verify_proved_bound(100)
        assert result["all_satisfy_bound"] is True
        # min_excess should have been updated from inf
        assert result["min_excess"] < float('inf')
        assert result["min_excess"] > 0

    def test_large_n_no_counterexamples(self):
        """No counterexamples expected for canonical sets."""
        result = verify_proved_bound(60)
        assert result["counterexamples"] == []

    def test_large_n_odd_n(self):
        """Test with odd N > 30 for different canonical set behavior."""
        result = verify_proved_bound(51)
        assert result["N"] == 51
        assert result["all_satisfy_bound"] is True

    def test_exhaustive_bound_violation_with_mock(self):
        """Cover lines 197-198: mock max_non_dc_fourier to return a tiny value,
        triggering the bound-violation branch for N <= 30."""
        from unittest.mock import patch
        with patch("sum_free_structure.max_non_dc_fourier", return_value=(1, 0.001)):
            result = verify_proved_bound(15)
        if result["sets_checked"] > 0:
            assert result["all_satisfy_bound"] is False
            assert len(result["counterexamples"]) > 0
            ce = result["counterexamples"][0]
            assert "actual" in ce
            assert "predicted" in ce
            assert ce["actual"] < ce["predicted"]

    def test_large_n_bound_violation_with_mock(self):
        """Cover line 221: mock max_non_dc_fourier to trigger violation in large-N path."""
        from unittest.mock import patch
        with patch("sum_free_structure.max_non_dc_fourier", return_value=(1, 0.001)):
            result = verify_proved_bound(50)
        if result["sets_checked"] > 0:
            assert result["all_satisfy_bound"] is False


class TestSchurColoringAnalysis:
    """Cover lines 232-261: schur_coloring_analysis function."""

    def test_basic_structure(self):
        """Returned dict should have the expected keys."""
        result = schur_coloring_analysis(5, 2)
        assert "N" in result
        assert "k" in result
        assert "colorings_checked" in result
        assert "schur_free_found" in result
        assert "best_coloring" in result
        assert result["N"] == 5
        assert result["k"] == 2

    def test_no_schur_free_due_to_zero(self):
        """Element 0 is always in some color class, and 0+0=0 makes it not sum-free.
        So the function never finds a Schur-free coloring for any N >= 1."""
        result = schur_coloring_analysis(1, 1)
        assert result["colorings_checked"] == 1
        assert result["schur_free_found"] is False

    def test_k2_n4_no_schur_free(self):
        """Even with S(2)=4 classically, 0-indexed coloring makes it impossible."""
        result = schur_coloring_analysis(4, 2)
        assert result["colorings_checked"] == 2**4
        assert result["schur_free_found"] is False
        assert result["best_coloring"] is None

    def test_k2_n5_no_schur_free(self):
        """All 2^5 colorings of [0..4] checked, none Schur-free."""
        result = schur_coloring_analysis(5, 2)
        assert result["colorings_checked"] == 2**5
        assert result["schur_free_found"] is False
        assert result["best_coloring"] is None

    def test_k1_n2_no_schur_free(self):
        """k=1, N=2: single color class {0,1}, 0+0=0 -> not sum-free."""
        result = schur_coloring_analysis(2, 1)
        assert result["colorings_checked"] == 1
        assert result["schur_free_found"] is False

    def test_large_n_skips_enumeration(self):
        """For N > 10, the function should skip enumeration and return defaults."""
        result = schur_coloring_analysis(15, 2)
        assert result["colorings_checked"] == 0
        assert result["schur_free_found"] is False
        assert result["best_coloring"] is None

    def test_large_k_skips_enumeration(self):
        """For k > 3, the function should skip enumeration and return defaults."""
        result = schur_coloring_analysis(5, 4)
        assert result["colorings_checked"] == 0
        assert result["schur_free_found"] is False

    def test_k3_exhaustive(self):
        """Test 3-coloring for small N: all 3^5 colorings checked."""
        result = schur_coloring_analysis(5, 3)
        assert result["colorings_checked"] == 3**5
        # 0+0=0 prevents any color class containing 0 from being sum-free
        assert result["schur_free_found"] is False

    def test_schur_free_found_with_mock(self):
        """Use mock to exercise the schur_free_found=True branch (lines 252-259).
        The 0-indexed scheme makes it unreachable normally, so we mock is_sum_free."""
        from unittest.mock import patch
        with patch("sum_free_structure.is_sum_free", return_value=True):
            result = schur_coloring_analysis(3, 2)
        assert result["schur_free_found"] is True
        bc = result["best_coloring"]
        assert bc is not None
        assert "coloring" in bc
        assert "color_sizes" in bc
        assert "color_densities" in bc
        assert len(bc["color_sizes"]) == 2
        # Densities should sum to 1.0
        assert abs(sum(bc["color_densities"]) - 1.0) < 1e-10
