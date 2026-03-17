"""Tests for schur_sidon_bridge.py -- Schur-Sidon obstruction bridge."""
import math
import random

import numpy as np
import pytest

from schur_sidon_bridge import (
    fourier_coefficients,
    fourier_flatness_ratio,
    max_non_dc_coefficient,
    odd_numbers,
    maximal_sidon,
    random_sum_free,
    random_sidon_target,
    experiment_spectrum_comparison,
    experiment_density_tradeoff,
    experiment_obstruction,
    experiment_mutual_exclusion,
    max_sum_free_sidon,
)
from kelley_meka_schur import is_sum_free
from sidon_disjoint import is_sidon


@pytest.fixture(autouse=True)
def _seed():
    """Fix random seed for reproducibility."""
    random.seed(12345)
    np.random.seed(12345)


# ---------------------------------------------------------------------------
# Fourier helpers
# ---------------------------------------------------------------------------

class TestFourierCoefficients:
    """Test raw Fourier coefficient computation."""

    def test_dc_equals_set_size(self):
        N = 50
        A = {1, 3, 7, 11, 23}
        mags = fourier_coefficients(A, N)
        assert abs(mags[0] - len(A)) < 1e-10

    def test_empty_set_all_zero(self):
        N = 20
        mags = fourier_coefficients(set(), N)
        assert np.allclose(mags, 0.0)

    def test_full_set_dc_dominates(self):
        """For the full set, f_hat(0) = N and f_hat(r) = 0 for r != 0."""
        N = 30
        A = set(range(N))
        mags = fourier_coefficients(A, N)
        assert abs(mags[0] - N) < 1e-10
        assert np.allclose(mags[1:], 0.0, atol=1e-10)

    def test_parseval(self):
        """Parseval: sum |f_hat(r)|^2 = N * |A|."""
        N = 60
        A = {2, 5, 17, 33, 44, 59}
        mags = fourier_coefficients(A, N)
        assert abs(np.sum(mags**2) - N * len(A)) < 1e-6


class TestFourierFlatnessRatio:
    """Test flatness ratio computation."""

    def test_full_set_degenerate(self):
        """Full set has all non-DC coefficients = 0 -> ratio 0."""
        N = 20
        A = set(range(N))
        assert fourier_flatness_ratio(A, N) == 0.0

    def test_odds_spiky(self):
        """Odds have a huge peak at N/2 -> high flatness ratio."""
        N = 100
        ratio = fourier_flatness_ratio(odd_numbers(N), N)
        assert ratio > 5.0, f"Odds should be very spiky, got ratio={ratio:.2f}"

    def test_singleton(self):
        """Singleton: |f_hat(r)| = 1 for all r -> ratio = 1."""
        N = 50
        ratio = fourier_flatness_ratio({7}, N)
        assert abs(ratio - 1.0) < 0.01

    def test_positive(self):
        """Flatness ratio is always non-negative."""
        N = 40
        A = {1, 5, 13, 29}
        assert fourier_flatness_ratio(A, N) >= 0.0


class TestMaxNonDC:
    """Test max non-DC coefficient extraction."""

    def test_odds_peak_at_half(self):
        """Odd numbers in Z/NZ peak at r=N/2."""
        N = 100
        r, mag = max_non_dc_coefficient(odd_numbers(N), N)
        assert r == N // 2

    def test_magnitude_positive(self):
        N = 50
        _, mag = max_non_dc_coefficient({1, 3, 7}, N)
        assert mag > 0

    def test_full_set_zero(self):
        """Full set has all non-DC coefficients zero."""
        N = 20
        _, mag = max_non_dc_coefficient(set(range(N)), N)
        assert mag < 1e-10


# ---------------------------------------------------------------------------
# Set generators
# ---------------------------------------------------------------------------

class TestOddNumbers:
    """Test odd number generator."""

    def test_sum_free(self):
        for N in [20, 50, 100]:
            assert is_sum_free(odd_numbers(N), N)

    def test_size(self):
        N = 100
        assert len(odd_numbers(N)) == N // 2

    def test_all_odd(self):
        for x in odd_numbers(80):
            assert x % 2 == 1


class TestMaximalSidon:
    """Test maximal Sidon set builder."""

    def test_is_valid_sidon(self):
        N = 50
        sid = maximal_sidon(N)
        assert is_sidon(sid), f"{sorted(sid)} is not Sidon"

    def test_nonempty(self):
        assert len(maximal_sidon(30)) > 0

    def test_size_bound(self):
        """Maximal Sidon in [N] should have size ~sqrt(N)."""
        N = 100
        sid = maximal_sidon(N)
        assert len(sid) <= int(math.sqrt(N)) + 5


class TestRandomSumFree:
    """Test random sum-free set generator."""

    def test_is_sum_free(self):
        N = 60
        for _ in range(10):
            sf = random_sum_free(N, 0.3)
            if sf:
                assert is_sum_free(sf, N)

    def test_approximate_density(self):
        N = 100
        sf = random_sum_free(N, 0.3)
        assert sf is not None
        # Allow generous tolerance
        assert len(sf) / N > 0.1

    def test_returns_none_gracefully(self):
        """Extremely high density may fail -- should return something or None."""
        # density 0.6 may be unreachable for sum-free in Z/NZ
        sf = random_sum_free(20, 0.6, max_attempts=50)
        if sf is not None:
            assert is_sum_free(sf, 20)


class TestRandomSidonTarget:
    """Test targeted Sidon set generator."""

    def test_low_density_achievable(self):
        N = 100
        sid = random_sidon_target(N, 0.05)
        assert sid is not None
        assert is_sidon(sid)

    def test_high_density_rejected(self):
        """Density > 1/sqrt(N) + epsilon should be unreachable."""
        N = 100
        sid = random_sidon_target(N, 0.5)
        assert sid is None

    def test_output_valid_when_returned(self):
        for _ in range(5):
            sid = random_sidon_target(50, 0.08)
            if sid:
                assert is_sidon(sid)


# ---------------------------------------------------------------------------
# Experiment (a): Spectrum comparison
# ---------------------------------------------------------------------------

class TestSpectrumComparison:
    """Test experiment (a)."""

    def test_returns_correct_fields(self):
        results = experiment_spectrum_comparison([30])
        assert len(results) == 1
        r = results[0]
        for key in ("N", "sum_free_size", "sidon_size", "sum_free_max_coeff",
                     "sidon_max_coeff", "sum_free_flatness", "sidon_flatness"):
            assert key in r, f"Missing key: {key}"

    def test_sum_free_spikier_than_sidon(self):
        """Core hypothesis: sum-free flatness > sidon flatness."""
        results = experiment_spectrum_comparison([50, 100])
        for r in results:
            assert r["sum_free_flatness"] > r["sidon_flatness"], (
                f"N={r['N']}: SF flat={r['sum_free_flatness']:.2f} "
                f"<= Sid flat={r['sidon_flatness']:.2f}"
            )

    def test_sum_free_max_coeff_large(self):
        """Odds should have max coeff = |A| = N/2."""
        results = experiment_spectrum_comparison([100])
        r = results[0]
        expected = r["sum_free_size"]
        assert abs(r["sum_free_max_coeff"] - expected) < 1.0


# ---------------------------------------------------------------------------
# Experiment (b): Density-Fourier tradeoff
# ---------------------------------------------------------------------------

class TestDensityTradeoff:
    """Test experiment (b)."""

    def test_returns_all_densities(self):
        densities = [0.1, 0.2, 0.3]
        results = experiment_density_tradeoff(N=50, densities=densities, trials=5)
        assert len(results) == len(densities)

    def test_sidon_unavailable_at_high_density(self):
        """At density 0.4, Sidon sets in [50] are unreachable (need 20 > sqrt(50))."""
        results = experiment_density_tradeoff(N=50, densities=[0.4], trials=5)
        assert results[0]["sidon_count"] == 0

    def test_sum_free_available_at_moderate_density(self):
        """Sum-free sets should be findable at density 0.2."""
        results = experiment_density_tradeoff(N=60, densities=[0.2], trials=10)
        assert results[0]["sum_free_count"] > 0


# ---------------------------------------------------------------------------
# Experiment (c): Obstruction / Lemma A
# ---------------------------------------------------------------------------

class TestObstruction:
    """Test experiment (c)."""

    def test_lemma_a_no_violations(self):
        """Lemma A should hold for all dense sum-free sets."""
        obs = experiment_obstruction(N=30)
        assert obs["lemma_a_fails"] == 0, (
            f"{obs['lemma_a_fails']} violations found: {obs['violations']}"
        )

    def test_finds_some_sets(self):
        obs = experiment_obstruction(N=30)
        assert obs["sets_found"] > 0

    def test_sidon_overlap_zero_for_dense(self):
        """Dense sum-free sets (|A| > N/3) should NOT be Sidon for N >= 30."""
        obs = experiment_obstruction(N=40)
        assert obs["also_sidon_count"] == 0, (
            f"Found {obs['also_sidon_count']} dense sum-free Sidon sets"
        )

    def test_correct_threshold(self):
        obs = experiment_obstruction(N=50)
        assert obs["threshold"] == 17  # floor(50/3) + 1


# ---------------------------------------------------------------------------
# Experiment (d): Mutual exclusion
# ---------------------------------------------------------------------------

class TestMutualExclusion:
    """Test experiment (d)."""

    def test_both_is_sum_free_and_sidon(self):
        """max_sum_free_sidon should return a set that is both."""
        result = max_sum_free_sidon(30, trials=100)
        A = set(result["max_both_set"])
        if A:
            assert is_sum_free(A, 30), f"{sorted(A)} not sum-free"
            assert is_sidon(A), f"{sorted(A)} not Sidon"

    def test_both_smaller_than_either_alone(self):
        """max(both) < max(sum-free) for N >= 20."""
        results = experiment_mutual_exclusion([20, 30])
        for r in results:
            assert r["max_both"] <= r["max_sum_free"], (
                f"N={r['N']}: both={r['max_both']} > sum_free={r['max_sum_free']}"
            )

    def test_both_bounded_by_sidon(self):
        """max(both) <= max(Sidon) since the Sidon constraint is tighter."""
        results = experiment_mutual_exclusion([30, 40])
        for r in results:
            # Allow +1 slack for randomness in Sidon search
            assert r["max_both"] <= r["max_sidon"] + 1, (
                f"N={r['N']}: both={r['max_both']} > sidon={r['max_sidon']}+1"
            )

    def test_returns_correct_fields(self):
        results = experiment_mutual_exclusion([20])
        r = results[0]
        for key in ("N", "max_sum_free", "max_sidon", "max_both",
                     "max_both_set", "both_density"):
            assert key in r

    def test_both_grows_sublinearly(self):
        """max(both) should grow slower than N."""
        results = experiment_mutual_exclusion([20, 50])
        if len(results) == 2:
            r20, r50 = results
            # If both grows linearly, max_both(50)/50 ~ max_both(20)/20
            # Sublinear means the density decreases
            d20 = r20["max_both"] / r20["N"]
            d50 = r50["max_both"] / r50["N"]
            assert d50 <= d20 + 0.05, (
                f"Density should decrease: d(20)={d20:.3f}, d(50)={d50:.3f}"
            )


# ---------------------------------------------------------------------------
# Cross-cutting structural tests
# ---------------------------------------------------------------------------

class TestFourierDuality:
    """Tests verifying the core Fourier duality hypothesis."""

    def test_sidon_coefficients_bounded(self):
        """Sidon set Fourier coefficients bounded by O(sqrt(N))."""
        N = 100
        sid = maximal_sidon(N)
        mags = fourier_coefficients(sid, N)
        # For Sidon set of size ~sqrt(N), max |f_hat| should be ~ sqrt(N)
        # (each f_hat(r) is a sum of ~sqrt(N) roots of unity with distinct pairwise sums)
        assert np.max(mags[1:]) <= 2 * math.sqrt(N) + len(sid), (
            f"Sidon max coeff {np.max(mags[1:]):.1f} exceeds bound"
        )

    def test_sum_free_large_coefficient(self):
        """Dense sum-free set must have a large Fourier coefficient (Lemma A)."""
        N = 80
        odds = odd_numbers(N)
        delta = len(odds) / N
        _, mag = max_non_dc_coefficient(odds, N)
        bound = delta / (1 - delta) * len(odds)
        assert mag >= bound - 1e-6

    def test_no_dense_sum_free_sidon(self):
        """No set with |A| > sqrt(N) + 5 can be both sum-free and Sidon."""
        N = 50
        result = max_sum_free_sidon(N, trials=300)
        threshold = int(math.sqrt(N)) + 5
        assert result["max_both_size"] <= threshold, (
            f"Found sum-free Sidon set of size {result['max_both_size']} > {threshold}"
        )
