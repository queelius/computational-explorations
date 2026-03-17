"""Tests for meta_analysis_new.py — cross-cutting meta-pattern discovery.

Validates internal consistency of data, model fits, conjectures, and
discovered patterns across the five analysis domains.
"""

import math
import numpy as np
import pytest

from meta_analysis_new import (
    RCOP_DATA,
    CLASSICAL_RAMSEY,
    SCHUR_NUMBERS,
    DS_DATA,
    S_CYCLIC_K2,
    S_CYCLIC_K3,
    S_K3_FAILURES,
    FOURIER_FLATNESS,
    COMPUTATION_OUTCOMES,
    IP_RAMSEY_COVERAGE,
    fit_exponential,
    fit_polynomial,
    fit_superexponential,
    rcop_growth_analysis,
    ds_schur_relationship,
    invariance_boundary_analysis,
    fourier_obstruction_analysis,
    difficulty_prediction,
    cross_pattern_discovery,
    run_all_analyses,
    _is_prime,
    _encode_features,
    _sigmoid,
    _logistic_regression,
    _feature_names,
)


# ═════════════════════════════════════════════════════════════════════
# Module-scoped fixtures for expensive computations
# ═════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def rcop_analysis():
    return rcop_growth_analysis()


@pytest.fixture(scope="module")
def ds_analysis():
    return ds_schur_relationship()


@pytest.fixture(scope="module")
def inv_analysis():
    return invariance_boundary_analysis()


@pytest.fixture(scope="module")
def fourier_analysis():
    return fourier_obstruction_analysis()


@pytest.fixture(scope="module")
def difficulty_analysis():
    return difficulty_prediction()


@pytest.fixture(scope="module")
def cross_analysis():
    return cross_pattern_discovery()


@pytest.fixture(scope="module")
def all_results():
    return run_all_analyses()


# ═════════════════════════════════════════════════════════════════════
# Data integrity tests
# ═════════════════════════════════════════════════════════════════════

class TestDataIntegrity:
    """Verify that the hardcoded data is internally consistent."""

    def test_rcop_values_positive(self):
        for k, v in RCOP_DATA.items():
            assert v > 0, f"R_cop({k}) must be positive"

    def test_rcop_monotone(self):
        vals = [RCOP_DATA[k] for k in sorted(RCOP_DATA)]
        for i in range(len(vals) - 1):
            assert vals[i] < vals[i + 1], "R_cop(k) must be strictly increasing"

    def test_rcop_ge_classical(self):
        for k in RCOP_DATA:
            if k in CLASSICAL_RAMSEY:
                assert RCOP_DATA[k] >= CLASSICAL_RAMSEY[k], (
                    f"R_cop({k}) >= R({k},{k})"
                )

    def test_schur_numbers_known(self):
        assert SCHUR_NUMBERS[1] == 1
        assert SCHUR_NUMBERS[2] == 4
        assert SCHUR_NUMBERS[3] == 13
        assert SCHUR_NUMBERS[4] == 44
        assert SCHUR_NUMBERS[5] == 160

    def test_ds_monotone_in_alpha(self):
        """DS(k, alpha) is non-decreasing in alpha for fixed k."""
        k2_data = sorted((a, v) for (kk, a), v in DS_DATA.items() if kk == 2)
        for i in range(len(k2_data) - 1):
            assert k2_data[i][1] <= k2_data[i + 1][1], (
                f"DS(2, {k2_data[i][0]}) = {k2_data[i][1]} should be <= "
                f"DS(2, {k2_data[i + 1][0]}) = {k2_data[i + 1][1]}"
            )

    def test_ds_ge_schur_plus_1(self):
        """DS(k, alpha) >= S(k) + 1 always (at least need Schur forcing)."""
        for (k, alpha), v in DS_DATA.items():
            assert v >= SCHUR_NUMBERS[k] + 1, (
                f"DS({k}, {alpha}) = {v} must be >= S({k})+1 = {SCHUR_NUMBERS[k]+1}"
            )

    def test_s_cyclic_k2_positive(self):
        for n, s in S_CYCLIC_K2.items():
            assert 0 < s <= n, f"S(Z/{n}Z, 2) = {s} out of range"

    def test_s_cyclic_k3_le_n_minus_1(self):
        for n, s in S_CYCLIC_K3.items():
            assert s <= n - 1, (
                f"S(Z/{n}Z, 3) = {s} should be <= {n-1} (0 always excluded)"
            )

    def test_fourier_flatness_gap(self):
        """Sum-free sets always have much higher flatness than Sidon."""
        for N, (sf, sid) in FOURIER_FLATNESS.items():
            assert sf > 10 * sid, (
                f"At N={N}, sum-free flatness {sf} should be >> Sidon {sid}"
            )

    def test_computation_outcomes_format(self):
        for entry in COMPUTATION_OUTCOMES:
            assert len(entry) == 5
            pid, tags, success, method, complexity = entry
            assert isinstance(pid, int)
            assert isinstance(tags, list)
            assert isinstance(success, bool)
            assert isinstance(method, str)
            assert complexity in ("low", "medium", "high", "hard")


# ═════════════════════════════════════════════════════════════════════
# Utility function tests
# ═════════════════════════════════════════════════════════════════════

class TestUtilities:
    """Test helper functions."""

    def test_is_prime_small(self):
        primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59}
        for n in range(60):
            assert _is_prime(n) == (n in primes), f"_is_prime({n}) wrong"

    def test_is_prime_rcop_values(self):
        assert _is_prime(2)
        assert _is_prime(11)
        assert _is_prime(59)

    def test_sigmoid_range(self):
        z = np.linspace(-10, 10, 100)
        s = _sigmoid(z)
        assert np.all(s >= 0)
        assert np.all(s <= 1)
        assert abs(s[50] - 0.5) < 0.1  # near z=0

    def test_sigmoid_monotone(self):
        z = np.linspace(-5, 5, 100)
        s = _sigmoid(z)
        assert np.all(np.diff(s) >= 0)

    def test_encode_features_length(self):
        feats = _encode_features(["number theory", "graph theory"])
        assert len(feats) == len(_feature_names())

    def test_encode_features_cross_domain(self):
        # Two major categories => cross_domain = 1
        feats = _encode_features(["number theory", "graph theory"])
        assert feats[-1] == 1.0
        # One major category => cross_domain = 0
        feats = _encode_features(["number theory"])
        assert feats[-1] == 0.0

    def test_encode_features_tag_count(self):
        feats = _encode_features(["a", "b", "c"])
        assert feats[0] == 3.0

    def test_logistic_regression_separable(self):
        """Test logistic regression on perfectly separable data."""
        X = np.array([[0], [0], [1], [1]], dtype=float)
        y = np.array([0, 0, 1, 1], dtype=float)
        w, b, acc = _logistic_regression(X, y, lr=1.0, epochs=1000)
        assert acc >= 0.75, f"Should separate cleanly, got accuracy {acc}"


# ═════════════════════════════════════════════════════════════════════
# Fitting function tests
# ═════════════════════════════════════════════════════════════════════

class TestFitting:
    """Test the growth rate fitting functions."""

    def test_fit_exponential_returns_dict(self):
        ks = np.array([2, 3, 4], dtype=float)
        vals = np.array([2, 11, 59], dtype=float)
        result = fit_exponential(ks, vals)
        assert "a" in result and "b" in result and "residual" in result

    def test_fit_exponential_b_gt_1(self):
        """For growing data, base b should exceed 1."""
        ks = np.array([2, 3, 4], dtype=float)
        vals = np.array([2, 11, 59], dtype=float)
        result = fit_exponential(ks, vals)
        assert result["b"] > 1, f"Exponential base should be > 1, got {result['b']}"

    def test_fit_polynomial_returns_dict(self):
        ks = np.array([2, 3, 4], dtype=float)
        vals = np.array([2, 11, 59], dtype=float)
        result = fit_polynomial(ks, vals)
        assert "a" in result and "c" in result and "residual" in result

    def test_fit_polynomial_c_positive(self):
        ks = np.array([2, 3, 4], dtype=float)
        vals = np.array([2, 11, 59], dtype=float)
        result = fit_polynomial(ks, vals)
        assert result["c"] > 0, f"Polynomial exponent should be > 0, got {result['c']}"

    def test_fit_superexponential_returns_dict(self):
        ks = np.array([2, 3, 4], dtype=float)
        vals = np.array([2, 11, 59], dtype=float)
        result = fit_superexponential(ks, vals)
        assert "a" in result and "b" in result and "residual" in result

    def test_fit_exponential_exact_data(self):
        """If data is exactly exponential, residual should be near 0."""
        ks = np.array([1, 2, 3, 4], dtype=float)
        vals = np.array([3, 9, 27, 81], dtype=float)  # 3^k
        result = fit_exponential(ks, vals)
        assert result["residual"] < 1e-10
        assert abs(result["b"] - 3.0) < 0.01

    def test_fit_polynomial_exact_data(self):
        """If data is exactly polynomial, residual should be near 0."""
        ks = np.array([1, 2, 3, 4], dtype=float)
        vals = np.array([2, 8, 18, 32], dtype=float)  # 2*k^2
        result = fit_polynomial(ks, vals)
        assert result["residual"] < 0.1
        assert abs(result["c"] - 2.0) < 0.2

    def test_predicted_length_matches_input(self):
        ks = np.array([2, 3, 4], dtype=float)
        vals = np.array([2, 11, 59], dtype=float)
        for fit_fn in [fit_exponential, fit_polynomial, fit_superexponential]:
            result = fit_fn(ks, vals)
            assert len(result["predicted"]) == 3


# ═════════════════════════════════════════════════════════════════════
# 1. R_cop(k) Growth Rate Analysis
# ═════════════════════════════════════════════════════════════════════

class TestRcopGrowth:
    """Test R_cop(k) growth analysis."""

    def test_returns_dict(self, rcop_analysis):
        assert isinstance(rcop_analysis, dict)

    def test_has_all_models(self, rcop_analysis):
        assert "exponential" in rcop_analysis
        assert "polynomial" in rcop_analysis
        assert "superexponential" in rcop_analysis

    def test_best_model_valid(self, rcop_analysis):
        assert rcop_analysis["best_model"] in (
            "exponential", "polynomial", "superexponential"
        )

    def test_ratios_computed(self, rcop_analysis):
        ratios = rcop_analysis["ratios"]
        assert len(ratios) >= 3
        assert ratios[2] == pytest.approx(1.0)
        assert ratios[3] == pytest.approx(11.0 / 6.0, rel=0.01)
        assert ratios[4] == pytest.approx(59.0 / 18.0, rel=0.01)

    def test_ratios_increasing(self, rcop_analysis):
        """R_cop(k)/R(k,k) should be non-decreasing."""
        ratios = rcop_analysis["ratios"]
        vals = [ratios[k] for k in sorted(ratios)]
        for i in range(len(vals) - 1):
            assert vals[i] <= vals[i + 1], "Ratio sequence should be non-decreasing"

    def test_primality(self, rcop_analysis):
        """All known R_cop values are prime."""
        for k, info in rcop_analysis["primality"].items():
            assert info["is_prime"], f"R_cop({k}) = {info['value']} should be prime"

    def test_all_prime(self, rcop_analysis):
        assert rcop_analysis["all_prime"] is True

    def test_rcop5_predictions_positive(self, rcop_analysis):
        for model, val in rcop_analysis["rcop5_predictions"].items():
            assert val > RCOP_DATA[4], (
                f"{model} prediction {val} should exceed R_cop(4)={RCOP_DATA[4]}"
            )

    def test_acceleration_positive(self, rcop_analysis):
        acc = rcop_analysis["acceleration"]
        assert acc["accelerating"], "R_cop should have positive second differences"

    def test_ratio_growth_present(self, rcop_analysis):
        rg = rcop_analysis["ratio_growth"]
        assert "linear_coeffs" in rg or "note" in rg


# ═════════════════════════════════════════════════════════════════════
# 2. DS(k, alpha) vs S(k)
# ═════════════════════════════════════════════════════════════════════

class TestDSSchur:
    """Test density-Schur relationship analysis."""

    def test_returns_dict(self, ds_analysis):
        assert isinstance(ds_analysis, dict)

    def test_conjecture_a_k2_holds(self, ds_analysis):
        """DS(2, 0.5) = S(2) + 1 = 5."""
        assert ds_analysis["conjecture_a"]["k2"]["holds"]

    def test_schur_growth_ratios(self, ds_analysis):
        ratios = ds_analysis["schur_growth_ratios"]
        # S(k+1)/S(k) should be between 2 and 5
        for entry in ratios:
            assert 2.0 <= entry["ratio"] <= 5.0, (
                f"S({entry['k']+1})/S({entry['k']}) = {entry['ratio']} out of range"
            )

    def test_regime_analysis_present(self, ds_analysis):
        ra = ds_analysis["regime_analysis"]
        assert "k2_regimes" in ra
        assert len(ra["k2_regimes"]) == 3

    def test_alpha_threshold_k2(self, ds_analysis):
        """The threshold (S(k)-1)/(S(k)+1) should match k=2 data."""
        at = ds_analysis["alpha_threshold_conjecture"]
        threshold = at["k2"]["threshold"]
        assert abs(threshold - 0.6) < 0.01, (
            f"Threshold should be 3/5=0.6, got {threshold}"
        )

    def test_ds_vs_schur_plus_1(self, ds_analysis):
        entries = ds_analysis["ds_vs_schur_plus_1"]
        assert len(entries) >= 2
        # k=2: ratio should be 1.0
        assert entries[0]["ratio"] == pytest.approx(1.0)

    def test_regime_pattern_k2(self, ds_analysis):
        """The pattern formula 3/(S(k)+1) should predict k=2 first jump."""
        pattern = ds_analysis["regime_analysis"]["pattern"]
        assert pattern["k2_match"], (
            f"3/(S(2)+1) = {pattern['k2_prediction']} should match 0.60"
        )


# ═════════════════════════════════════════════════════════════════════
# 3. Invariance boundary
# ═════════════════════════════════════════════════════════════════════

class TestInvarianceBoundary:
    """Test order-invariance boundary analysis."""

    def test_returns_dict(self, inv_analysis):
        assert isinstance(inv_analysis, dict)

    def test_exponent_analysis(self, inv_analysis):
        exp = inv_analysis["exponent_analysis"]
        assert exp["k3"]["break_exponent"] == 3

    def test_rank_analysis(self, inv_analysis):
        rank = inv_analysis["rank_analysis"]
        assert "refinement" in rank
        assert "prediction_k4" in rank["refinement"]

    def test_n_minus_1_pattern(self, inv_analysis):
        p = inv_analysis["n_minus_1_pattern"]
        assert p["break_point"] == 15
        assert p["break_value"] == 13

    def test_n_minus_1_holds_before_break(self):
        """Verify S(Z/nZ, 3) = n-1 for n=2..14."""
        for n in range(2, 15):
            assert S_CYCLIC_K3[n] == n - 1, f"S(Z/{n}Z, 3) = {S_CYCLIC_K3[n]} != {n-1}"

    def test_n_minus_1_fails_at_15(self):
        """S(Z/15Z, 3) = 13 = 15-2, not 15-1."""
        assert S_CYCLIC_K3[15] == 13

    def test_cyclic_k2_bounded(self, inv_analysis):
        """S(Z/nZ, 2) / n should stay in (0, 1)."""
        ratios = inv_analysis["cyclic_k2_ratios"]
        for n, info in ratios.items():
            assert 0 < info["ratio"] < 1.0, (
                f"S(Z/{n}Z, 2)/n = {info['ratio']} should be in (0,1)"
            )

    def test_k3_break_groups_differ(self):
        """Verify S(Z/9Z,3) != S(Z/3Z x Z/3Z, 3) from stored data."""
        assert S_K3_FAILURES[((9,), 8)]
        assert S_K3_FAILURES[((3, 3), 7)]


# ═════════════════════════════════════════════════════════════════════
# 4. Fourier obstruction
# ═════════════════════════════════════════════════════════════════════

class TestFourierObstruction:
    """Test Fourier obstruction analysis."""

    def test_returns_dict(self, fourier_analysis):
        assert isinstance(fourier_analysis, dict)

    def test_flatness_growth(self, fourier_analysis):
        growth = fourier_analysis["flatness_growth"]
        assert len(growth) == 3

    def test_sum_free_flatness_linear(self, fourier_analysis):
        """Sum-free flatness / N should be approximately 1."""
        for entry in fourier_analysis["flatness_growth"]:
            norm = entry["sum_free_normalized"]
            assert 0.8 < norm < 1.2, (
                f"Sum-free flatness/N = {norm}, expected ~1.0"
            )

    def test_sidon_flatness_bounded(self, fourier_analysis):
        """Sidon flatness / sqrt(N) should be bounded."""
        for entry in fourier_analysis["flatness_growth"]:
            norm = entry["sidon_normalized"]
            assert norm < 1.0, (
                f"Sidon flatness/sqrt(N) = {norm}, should be bounded"
            )

    def test_gap_grows(self, fourier_analysis):
        """Gap between sum-free and Sidon flatness should grow with N."""
        gaps = [e["gap"] for e in fourier_analysis["flatness_growth"]]
        assert gaps[-1] > gaps[0], "Spectral gap should grow with N"

    def test_hierarchy_ordered(self, fourier_analysis):
        h = fourier_analysis["rigidity_hierarchy"]
        orders = [e["FO_order"] for e in h]
        assert orders == sorted(orders, reverse=True)

    def test_mutual_exclusion(self, fourier_analysis):
        me = fourier_analysis["mutual_exclusion"]
        assert "O(N^{-1/4})" in me["max_density_sum_free_and_sidon"]

    def test_ip_ramsey_coverage_decreasing(self, fourier_analysis):
        """IP Ramsey coverage should decrease with k."""
        ip = fourier_analysis["ip_ramsey_fourier"]
        coverages = [ip[k]["min_coverage"] for k in sorted(ip.keys())]
        for i in range(len(coverages) - 1):
            assert coverages[i] >= coverages[i + 1], (
                "IP Ramsey coverage should decrease with k"
            )


# ═════════════════════════════════════════════════════════════════════
# 5. Difficulty prediction
# ═════════════════════════════════════════════════════════════════════

class TestDifficultyPrediction:
    """Test difficulty prediction model."""

    def test_returns_dict(self, difficulty_analysis):
        assert isinstance(difficulty_analysis, dict)

    def test_model_present(self, difficulty_analysis):
        assert "model" in difficulty_analysis
        assert "weights" in difficulty_analysis["model"]

    def test_weights_length(self, difficulty_analysis):
        w = difficulty_analysis["model"]["weights"]
        assert len(w) == len(_feature_names())

    def test_accuracy_above_random(self, difficulty_analysis):
        """Model should beat random guessing (>50%)."""
        acc = difficulty_analysis["model"]["train_accuracy"]
        assert acc >= 0.50, f"Accuracy {acc} should be >= 0.50"

    def test_feature_importance_sorted(self, difficulty_analysis):
        fi = difficulty_analysis["feature_importance"]
        magnitudes = [abs(e["weight"]) for e in fi]
        assert magnitudes == sorted(magnitudes, reverse=True)

    def test_key_findings_present(self, difficulty_analysis):
        assert len(difficulty_analysis["key_findings"]) > 0


# ═════════════════════════════════════════════════════════════════════
# 6. Cross-pattern discovery
# ═════════════════════════════════════════════════════════════════════

class TestCrossPatterns:
    """Test cross-cutting pattern discovery."""

    def test_returns_dict(self, cross_analysis):
        assert isinstance(cross_analysis, dict)

    def test_primality_wall(self, cross_analysis):
        pw = cross_analysis["primality_wall"]
        assert pw["all_rcop_prime"]

    def test_pi_sq_pattern(self, cross_analysis):
        p = cross_analysis["pi_sq_universality"]
        assert abs(p["coprime_density"] - 6.0 / math.pi ** 2) < 1e-10

    def test_acceleration_both(self, cross_analysis):
        acc = cross_analysis["acceleration"]
        assert acc["rcop"]["accelerating"]
        assert acc["schur"]["accelerating"]

    def test_ratio_conjecture_has_fit(self, cross_analysis):
        rc = cross_analysis["ratio_conjecture"]
        assert "exponential_fit" in rc

    def test_ratio_conjecture_beta_gt_1(self, cross_analysis):
        """The ratio R_cop(k)/R(k,k) should grow, so beta > 1."""
        ef = cross_analysis["ratio_conjecture"]["exponential_fit"]
        assert ef["beta"] > 1.0

    def test_rcop5_prediction_positive(self, cross_analysis):
        ef = cross_analysis["ratio_conjecture"]["exponential_fit"]
        assert ef["rcop5_value_prediction"] > RCOP_DATA[4]

    def test_duality_thresholds(self, cross_analysis):
        dt = cross_analysis["duality_thresholds"]
        assert dt["invariance_break"]["critical_k"] == 3
        assert dt["ip_coverage_break"]["critical_k"] == 5


# ═════════════════════════════════════════════════════════════════════
# Integration: run_all_analyses
# ═════════════════════════════════════════════════════════════════════

class TestRunAll:
    """Test the combined analysis runner."""

    def test_returns_dict(self, all_results):
        assert isinstance(all_results, dict)

    def test_has_all_keys(self, all_results):
        expected = {
            "rcop_growth", "ds_schur", "invariance_boundary",
            "fourier_obstruction", "difficulty_prediction", "cross_patterns",
        }
        assert expected == set(all_results.keys())

    def test_all_subdicts_nonempty(self, all_results):
        for key, val in all_results.items():
            assert isinstance(val, dict), f"{key} should be a dict"
            assert len(val) > 0, f"{key} should be non-empty"


# ═════════════════════════════════════════════════════════════════════
# Mathematical consistency tests (cross-domain)
# ═════════════════════════════════════════════════════════════════════

class TestMathematicalConsistency:
    """Test mathematical relationships that must hold across domains."""

    def test_rcop_exceeds_ramsey(self):
        """R_cop(k) >= R(k,k) by definition (coprime graph is subgraph of K_n)."""
        for k in RCOP_DATA:
            if k in CLASSICAL_RAMSEY:
                assert RCOP_DATA[k] >= CLASSICAL_RAMSEY[k]

    def test_schur_numbers_increasing(self):
        for k in range(1, 5):
            assert SCHUR_NUMBERS[k] < SCHUR_NUMBERS[k + 1]

    def test_ds_at_zero_equals_schur_plus_1(self):
        """At alpha close to 0, DS(k, alpha) should equal S(k) + 1."""
        assert DS_DATA[(2, 0.10)] == SCHUR_NUMBERS[2] + 1

    def test_schur_ratio_convergence(self):
        """S(k+1)/S(k) should converge (bounded away from 0 and infinity)."""
        for k in range(1, 5):
            ratio = SCHUR_NUMBERS[k + 1] / SCHUR_NUMBERS[k]
            assert 2.0 < ratio < 5.0

    def test_rcop_second_differences_positive(self):
        """R_cop has positive second differences (superlinear growth)."""
        vals = [RCOP_DATA[k] for k in [2, 3, 4]]
        d1 = vals[1] - vals[0]  # 9
        d2 = vals[2] - vals[1]  # 48
        assert d2 > d1, f"Second difference {d2-d1} should be positive"

    def test_fourier_gap_exceeds_30(self):
        """Spectral gap between sum-free and Sidon is at least 30x."""
        for N, (sf, sid) in FOURIER_FLATNESS.items():
            gap = sf / sid
            assert gap >= 30, f"Gap at N={N} is {gap:.1f}, expected >= 30"

    def test_ip_coverage_below_half_at_k5(self):
        """k=5 is the first point where coverage < 50%."""
        _, cov5 = IP_RAMSEY_COVERAGE[5]
        assert cov5 < 0.50
        _, cov4 = IP_RAMSEY_COVERAGE[4]
        assert cov4 >= 0.50

    def test_cyclic_k3_sum_to_n_minus_1(self):
        """S(Z/nZ, 3) = n-1 for small n."""
        for n in range(2, 15):
            assert S_CYCLIC_K3[n] == n - 1

    def test_rcop_values_all_prime(self):
        """Conjecture C1: all known R_cop values are prime."""
        for k, v in RCOP_DATA.items():
            assert _is_prime(v), f"R_cop({k}) = {v} is not prime"

    def test_ds2_threshold_formula(self):
        """Conjecture C2: first jump at alpha = (S(k)-1)/(S(k)+1) for k=2."""
        threshold = (SCHUR_NUMBERS[2] - 1) / (SCHUR_NUMBERS[2] + 1)
        assert abs(threshold - 0.6) < 0.001
