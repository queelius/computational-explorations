"""Tests for problem_survival.py — Survival analysis of Erdos problem resolution.

Tests cover:
  - Data preparation and status classification
  - Kaplan-Meier estimator (correctness, edge cases, monotonicity)
  - Cox proportional hazards (likelihood, gradient, fit)
  - Competing risks CIF (Aalen-Johansen, tag analysis)
  - Changepoint detection (piecewise hazard)
  - AFT models (Weibull, log-normal, log-logistic)
  - Log-rank tests
  - Integration tests on the real dataset
"""

import numpy as np
import pytest
from scipy import stats

from problem_survival import (
    TAG_CATEGORIES,
    _assign_tag_category,
    _classify_status,
    _concordance_index,
    _exponential_loglik,
    _log_rank_test,
    _parse_prize,
    build_survival_dataframe,
    compare_aft_distributions,
    competing_risks_by_tag,
    competing_risks_cif,
    cox_partial_likelihood,
    cox_partial_likelihood_grad,
    fit_aft_model,
    fit_cox_model,
    kaplan_meier,
    km_summary,
    load_problems,
    log_rank_by_category,
    piecewise_hazard_model,
    run_full_analysis,
)


# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------


@pytest.fixture(scope="module")
def problems():
    """Load the full problems dataset."""
    return load_problems()


@pytest.fixture(scope="module")
def survival_data():
    """Build survival dataframe from the real dataset."""
    return build_survival_dataframe()


@pytest.fixture
def simple_survival():
    """Small hand-constructed survival dataset for deterministic tests.

    10 subjects:
      - Times: 1..10
      - Events at t=2, 4, 6, 8 (subjects 2,4,6,8 resolve)
      - Censored at t=1, 3, 5, 7, 9, 10
    """
    time = np.arange(1, 11, dtype=float)
    event = np.array(
        [False, True, False, True, False, True, False, True, False, False]
    )
    return time, event


@pytest.fixture
def competing_data():
    """Small dataset for competing risks tests.

    20 subjects:
      - Times: 1..20
      - Cause 1 (proved) at t=3, 7, 11, 15, 19
      - Cause 2 (disproved) at t=5, 10, 20
      - Rest censored
    """
    n = 20
    time = np.arange(1, n + 1, dtype=float)
    event_type = np.array(["open"] * n, dtype=object)
    event_type[2] = "proved"
    event_type[6] = "proved"
    event_type[10] = "proved"
    event_type[14] = "proved"
    event_type[18] = "proved"
    event_type[4] = "disproved"
    event_type[9] = "disproved"
    event_type[19] = "disproved"
    event = event_type != "open"
    return {
        "time": time,
        "event": event,
        "event_type": event_type,
        "problem_number": np.arange(1, n + 1),
        "n_tags": np.ones(n, dtype=int),
        "has_prize": np.zeros(n, dtype=bool),
        "prize_usd": np.zeros(n),
        "has_oeis": np.zeros(n, dtype=bool),
        "tag_category": np.array(["number_theory"] * n, dtype=object),
        "is_formalized": np.zeros(n, dtype=bool),
    }


# ===================================================================
# Status classification & data prep
# ===================================================================


class TestParsePrice:
    def test_no_prize(self):
        assert _parse_prize("no") == 0.0

    def test_dollar_prize(self):
        assert _parse_prize("$500") == 500.0

    def test_large_dollar(self):
        assert _parse_prize("$10000") == 10000.0

    def test_gbp_prize(self):
        val = _parse_prize("£250")
        assert abs(val - 250 * 1.27) < 0.01

    def test_empty_string(self):
        assert _parse_prize("") == 0.0

    def test_none(self):
        assert _parse_prize(None) == 0.0

    def test_garbage(self):
        assert _parse_prize("free beer") == 0.0


class TestClassifyStatus:
    def test_proved(self):
        assert _classify_status("proved") == "proved"

    def test_proved_lean(self):
        assert _classify_status("proved (Lean)") == "proved"

    def test_disproved(self):
        assert _classify_status("disproved") == "disproved"

    def test_disproved_lean(self):
        assert _classify_status("disproved (Lean)") == "disproved"

    def test_solved(self):
        assert _classify_status("solved") == "solved"

    def test_solved_lean(self):
        assert _classify_status("solved (Lean)") == "solved"

    def test_open(self):
        assert _classify_status("open") == "open"

    def test_verifiable(self):
        assert _classify_status("verifiable") == "open"

    def test_unknown(self):
        assert _classify_status("some_weird_state") == "open"


class TestAssignTagCategory:
    def test_number_theory(self):
        assert _assign_tag_category(["number theory", "primes"]) == "number_theory"

    def test_graph_theory(self):
        assert _assign_tag_category(["graph theory", "cycles"]) == "graph_theory"

    def test_ramsey(self):
        assert _assign_tag_category(["ramsey theory"]) == "ramsey"

    def test_geometry(self):
        assert _assign_tag_category(["geometry", "distances"]) == "geometry"

    def test_empty_tags(self):
        assert _assign_tag_category([]) == "other"

    def test_priority_order(self):
        """If multiple categories match, the first in TAG_CATEGORIES wins."""
        cats = list(TAG_CATEGORIES.keys())
        # A tag list that matches at least two categories
        result = _assign_tag_category(["number theory", "graph theory"])
        # Should return whichever comes first in iteration order
        assert result in cats


class TestBuildSurvivalDataframe:
    def test_returns_dict(self, survival_data):
        assert isinstance(survival_data, dict)

    def test_has_required_keys(self, survival_data):
        required = {
            "problem_number", "time", "event", "event_type",
            "n_tags", "has_prize", "prize_usd", "has_oeis",
            "tag_category", "is_formalized",
        }
        assert required <= set(survival_data.keys())

    def test_correct_length(self, survival_data):
        n = len(survival_data["time"])
        assert n > 1100  # ~1183 problems
        for key in survival_data:
            assert len(survival_data[key]) == n

    def test_time_equals_problem_number(self, survival_data):
        np.testing.assert_array_equal(
            survival_data["time"],
            survival_data["problem_number"].astype(float),
        )

    def test_event_types_valid(self, survival_data):
        valid = {"proved", "disproved", "solved", "open"}
        unique = set(survival_data["event_type"])
        assert unique <= valid

    def test_event_consistent_with_type(self, survival_data):
        """event=True iff event_type != 'open'."""
        for i in range(len(survival_data["time"])):
            if survival_data["event"][i]:
                assert survival_data["event_type"][i] != "open"
            else:
                assert survival_data["event_type"][i] == "open"

    def test_prize_nonzero_implies_has_prize(self, survival_data):
        for i in range(len(survival_data["time"])):
            if survival_data["prize_usd"][i] > 0:
                assert survival_data["has_prize"][i]

    def test_tag_categories_valid(self, survival_data):
        valid_cats = set(TAG_CATEGORIES.keys()) | {"other"}
        for cat in survival_data["tag_category"]:
            assert cat in valid_cats


# ===================================================================
# 1. Kaplan-Meier
# ===================================================================


class TestKaplanMeier:
    def test_starts_at_one(self, simple_survival):
        """S(t) should start at 1.0 (or very close for first event)."""
        t, e = simple_survival
        km = kaplan_meier(t, e)
        # First event at t=2; S(2) = 1 - 1/10 since 10 at risk, 1 event
        # Actually: at t=2, n_at_risk = 10 (all have time >= 2 except none),
        # wait: times are 1..10, so at t=2, risk set is {t >= 2} = 9 subjects
        assert km["survival"][0] <= 1.0
        assert km["survival"][0] > 0.5

    def test_monotone_decreasing(self, simple_survival):
        t, e = simple_survival
        km = kaplan_meier(t, e)
        diffs = np.diff(km["survival"])
        assert np.all(diffs <= 0), "KM survival must be non-increasing"

    def test_all_events(self):
        """When all subjects have events, S should go to zero."""
        t = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        e = np.array([True, True, True, True, True])
        km = kaplan_meier(t, e)
        assert km["survival"][-1] == 0.0

    def test_no_events(self):
        """When all subjects are censored, no events means empty timeline."""
        t = np.array([1.0, 2.0, 3.0])
        e = np.array([False, False, False])
        km = kaplan_meier(t, e)
        assert len(km["timeline"]) == 0
        assert km["median_survival"] is None

    def test_single_event(self):
        """One event among many censored."""
        t = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        e = np.array([False, False, True, False, False])
        km = kaplan_meier(t, e)
        assert len(km["timeline"]) == 1
        assert km["timeline"][0] == 3.0
        # At t=3, risk set is {3, 4, 5} = 3 subjects, 1 event
        assert abs(km["survival"][0] - (1.0 - 1.0 / 3)) < 1e-10

    def test_median_computation(self):
        """Median should be the time when S first drops to 0.5."""
        # 6 subjects, events at t=1,2,3,4,5,6 -- S drops 1/6 each time
        t = np.arange(1, 7, dtype=float)
        e = np.ones(6, dtype=bool)
        km = kaplan_meier(t, e)
        # S(3) = (5/6)(4/5)(3/4) = 3/6 = 0.5 exactly
        assert km["median_survival"] == 3.0

    def test_tied_event_times(self):
        """Multiple events at the same time."""
        t = np.array([1.0, 1.0, 1.0, 2.0, 2.0])
        e = np.array([True, True, False, True, False])
        km = kaplan_meier(t, e)
        # At t=1: 5 at risk, 2 events -> S(1) = 1 - 2/5 = 0.6
        assert abs(km["survival"][0] - 0.6) < 1e-10
        # At t=2: risk set = {time >= 2} = 2 subjects, 1 event
        #   -> S(2) = 0.6 * (1 - 1/2) = 0.3
        assert abs(km["survival"][1] - 0.3) < 1e-10

    def test_confidence_interval_contains_estimate(self, simple_survival):
        t, e = simple_survival
        km = kaplan_meier(t, e)
        assert np.all(km["ci_lower"] <= km["survival"] + 1e-10)
        assert np.all(km["ci_upper"] >= km["survival"] - 1e-10)

    def test_ci_within_01(self, simple_survival):
        t, e = simple_survival
        km = kaplan_meier(t, e)
        assert np.all(km["ci_lower"] >= 0.0)
        assert np.all(km["ci_upper"] <= 1.0)


class TestKMSummary:
    def test_returns_expected_keys(self, survival_data):
        res = km_summary(survival_data)
        assert "n_total" in res
        assert "n_events" in res
        assert "n_censored" in res
        assert "median_survival" in res
        assert "survival_at_quartiles" in res

    def test_event_counts_add_up(self, survival_data):
        res = km_summary(survival_data)
        assert res["n_events"] + res["n_censored"] == res["n_total"]

    def test_more_censored_than_events(self, survival_data):
        """In the Erdos dataset, more problems are open than solved."""
        res = km_summary(survival_data)
        assert res["n_censored"] > res["n_events"]

    def test_median_is_reasonable(self, survival_data):
        """Median should be in the valid range of problem numbers."""
        res = km_summary(survival_data)
        if res["median_survival"] is not None:
            assert 1 <= res["median_survival"] <= 1183

    def test_survival_decreasing_over_quartiles(self, survival_data):
        res = km_summary(survival_data)
        sq = res["survival_at_quartiles"]
        vals = [sq[q] for q in sorted(sq) if sq[q] is not None]
        for i in range(len(vals) - 1):
            assert vals[i] >= vals[i + 1] - 1e-10


# ===================================================================
# 2. Cox Proportional Hazards
# ===================================================================


class TestCoxLikelihood:
    def test_zero_beta_finite(self):
        """Likelihood at beta=0 should be finite."""
        t = np.array([1, 2, 3, 4, 5], dtype=float)
        e = np.array([True, False, True, False, True])
        X = np.random.RandomState(42).randn(5, 2)
        beta = np.zeros(2)
        ll = cox_partial_likelihood(beta, t, e, X)
        assert np.isfinite(ll)

    def test_gradient_zero_at_optimum(self):
        """At the MLE, gradient should be approximately zero."""
        rng = np.random.RandomState(42)
        n = 100
        t = rng.exponential(5, n)
        X = rng.randn(n, 2)
        # Events: everyone has an event for simplicity
        e = np.ones(n, dtype=bool)

        from scipy.optimize import minimize

        result = minimize(
            cox_partial_likelihood,
            np.zeros(2),
            args=(t, e, X),
            jac=cox_partial_likelihood_grad,
            method="L-BFGS-B",
        )
        grad = cox_partial_likelihood_grad(result.x, t, e, X)
        assert np.allclose(grad, 0, atol=1e-4)

    def test_gradient_matches_numerical(self):
        """Analytical gradient should match finite-difference gradient."""
        rng = np.random.RandomState(123)
        n = 50
        t = rng.exponential(3, n)
        X = rng.randn(n, 3)
        e = rng.rand(n) > 0.4

        beta = rng.randn(3) * 0.1
        grad_analytic = cox_partial_likelihood_grad(beta, t, e, X)

        # Numerical gradient
        eps = 1e-6
        grad_num = np.zeros(3)
        for i in range(3):
            bp = beta.copy()
            bm = beta.copy()
            bp[i] += eps
            bm[i] -= eps
            grad_num[i] = (
                cox_partial_likelihood(bp, t, e, X)
                - cox_partial_likelihood(bm, t, e, X)
            ) / (2 * eps)

        np.testing.assert_allclose(grad_analytic, grad_num, atol=1e-4)


class TestCoxModel:
    def test_fit_converges(self, survival_data):
        res = fit_cox_model(survival_data)
        assert res["converged"]

    def test_correct_number_of_coefficients(self, survival_data):
        res = fit_cox_model(survival_data)
        assert len(res["coefficients"]) == len(res["column_names"])

    def test_hazard_ratios_positive(self, survival_data):
        res = fit_cox_model(survival_data)
        assert np.all(res["hazard_ratios"] > 0)

    def test_ci_lower_less_than_upper(self, survival_data):
        res = fit_cox_model(survival_data)
        assert np.all(res["ci_lower"] <= res["ci_upper"])

    def test_concordance_above_chance(self, survival_data):
        """C-index should be better than random (0.5)."""
        res = fit_cox_model(survival_data)
        assert res["concordance"] > 0.5

    def test_p_values_between_0_and_1(self, survival_data):
        res = fit_cox_model(survival_data)
        assert np.all(res["p_values"] >= 0)
        assert np.all(res["p_values"] <= 1)

    def test_prize_increases_hazard(self, survival_data):
        """Having a prize should increase resolution hazard (HR > 1)."""
        res = fit_cox_model(survival_data)
        idx = res["column_names"].index("has_prize")
        assert res["hazard_ratios"][idx] > 1.0

    def test_known_covariate_direction(self, survival_data):
        """Formalized problems in the data are LESS likely solved (selection effect)."""
        res = fit_cox_model(survival_data)
        idx = res["column_names"].index("is_formalized")
        # HR < 1 means formalized = lower hazard of resolution
        assert res["hazard_ratios"][idx] < 1.0


class TestConcordanceIndex:
    def test_perfect_concordance(self):
        """If risk score perfectly predicts order, C = 1."""
        t = np.array([1, 2, 3, 4, 5], dtype=float)
        e = np.ones(5, dtype=bool)
        # Higher risk = shorter survival
        risk = np.array([5, 4, 3, 2, 1], dtype=float)
        c = _concordance_index(t, e, risk)
        assert c == 1.0

    def test_anti_concordance(self):
        """If risk score is inverse, C = 0."""
        t = np.array([1, 2, 3, 4, 5], dtype=float)
        e = np.ones(5, dtype=bool)
        risk = np.array([1, 2, 3, 4, 5], dtype=float)
        c = _concordance_index(t, e, risk)
        assert c == 0.0

    def test_random_near_half(self):
        """Random risk scores should give C ~ 0.5."""
        rng = np.random.RandomState(42)
        n = 200
        t = rng.exponential(5, n)
        e = np.ones(n, dtype=bool)
        risk = rng.randn(n)
        c = _concordance_index(t, e, risk)
        assert 0.35 < c < 0.65


# ===================================================================
# 3. Competing Risks
# ===================================================================


class TestCompetingRisksCIF:
    def test_cif_sums_below_one(self, survival_data):
        """CIF_proved(t) + CIF_disproved(t) <= 1 at all times."""
        res = competing_risks_cif(survival_data)
        total = res["proved"]["cif"] + res["disproved"]["cif"]
        assert np.all(total <= 1.0 + 1e-10)

    def test_cif_monotone(self, survival_data):
        """CIF curves should be non-decreasing."""
        res = competing_risks_cif(survival_data)
        for cause in ("proved", "disproved"):
            diffs = np.diff(res[cause]["cif"])
            assert np.all(diffs >= -1e-10), f"CIF for {cause} not monotone"

    def test_event_counts(self, survival_data):
        res = competing_risks_cif(survival_data)
        # More proved than disproved
        assert res["proved"]["n_events"] > res["disproved"]["n_events"]

    def test_small_dataset(self, competing_data):
        """Test on hand-constructed data."""
        res = competing_risks_cif(competing_data)
        assert res["proved"]["n_events"] == 5
        assert res["disproved"]["n_events"] == 3

    def test_gray_test_returns_valid_p(self, survival_data):
        res = competing_risks_cif(survival_data)
        assert 0 <= res["gray_test"]["p_value"] <= 1
        assert res["gray_test"]["statistic"] >= 0


class TestCompetingRisksByTag:
    def test_all_categories_present(self, survival_data):
        res = competing_risks_by_tag(survival_data)
        cats = set(survival_data["tag_category"])
        assert set(res.keys()) == cats

    def test_proved_plus_disproved_leq_total(self, survival_data):
        res = competing_risks_by_tag(survival_data)
        for cat, r in res.items():
            mask = survival_data["tag_category"] == cat
            total = int(mask.sum())
            assert r["n_proved"] + r["n_disproved"] + r["n_open"] == total

    def test_ratio_positive(self, survival_data):
        res = competing_risks_by_tag(survival_data)
        for cat, r in res.items():
            assert r["ratio"] > 0

    def test_fisher_p_valid(self, survival_data):
        res = competing_risks_by_tag(survival_data)
        for cat, r in res.items():
            assert 0 <= r["fisher_p"] <= 1

    def test_ramsey_low_ratio(self, survival_data):
        """Ramsey theory should have among the lowest proved:disproved ratios."""
        res = competing_risks_by_tag(survival_data)
        if "ramsey" in res:
            # Ramsey has equal proved/disproved in our data
            assert res["ramsey"]["ratio"] <= 5.0


# ===================================================================
# 4. Changepoint Detection
# ===================================================================


class TestPiecewiseHazard:
    def test_returns_valid_structure(self, survival_data):
        res = piecewise_hazard_model(survival_data)
        assert "best_changepoint" in res
        assert "ai_multiplier" in res
        assert "p_value" in res
        assert "all_candidates" in res

    def test_hazards_positive(self, survival_data):
        res = piecewise_hazard_model(survival_data)
        assert res["hazard_before"] >= 0
        assert res["hazard_after"] >= 0

    def test_multiplier_consistent(self, survival_data):
        res = piecewise_hazard_model(survival_data)
        if res["hazard_before"] > 0:
            expected = res["hazard_after"] / res["hazard_before"]
            assert abs(res["ai_multiplier"] - expected) < 1e-6

    def test_lr_nonneg(self, survival_data):
        res = piecewise_hazard_model(survival_data)
        assert res["log_likelihood_ratio"] >= -1e-10

    def test_custom_changepoints(self, survival_data):
        res = piecewise_hazard_model(survival_data, candidate_changepoints=[500])
        assert len(res["all_candidates"]) == 1
        assert res["best_changepoint"] == 500

    def test_bonferroni_correction(self, survival_data):
        """Corrected p-value should be >= raw p-value."""
        res = piecewise_hazard_model(survival_data)
        assert res["p_value"] >= res["raw_p_value"] - 1e-10

    def test_significant_changepoint(self, survival_data):
        """There should be a significant structural break in the data."""
        res = piecewise_hazard_model(survival_data)
        # Even after correction, the changepoint should be significant
        assert res["p_value"] < 0.05

    def test_changepoint_in_valid_range(self, survival_data):
        res = piecewise_hazard_model(survival_data)
        assert 100 <= res["best_changepoint"] <= 1100

    def test_ai_multiplier_above_one(self, survival_data):
        """Later problems should have higher hazard (more solved per unit)."""
        res = piecewise_hazard_model(survival_data)
        assert res["ai_multiplier"] > 1.0


class TestExponentialLoglik:
    def test_positive_lambda(self):
        t = np.array([1.0, 2.0, 3.0])
        e = np.array([True, True, False])
        ll = _exponential_loglik(t, e, 0.5)
        assert np.isfinite(ll)

    def test_zero_lambda_negative_inf(self):
        t = np.array([1.0, 2.0])
        e = np.array([True, True])
        assert _exponential_loglik(t, e, 0.0) == -np.inf

    def test_maximized_at_mle(self):
        """MLE of exponential is d / sum(t)."""
        t = np.array([2.0, 4.0, 6.0, 8.0])
        e = np.array([True, True, True, True])
        mle = e.sum() / t.sum()  # 4/20 = 0.2
        ll_mle = _exponential_loglik(t, e, mle)
        ll_other = _exponential_loglik(t, e, mle * 1.5)
        assert ll_mle > ll_other


# ===================================================================
# 5. AFT Models
# ===================================================================


class TestAFTModel:
    def test_weibull_converges(self, survival_data):
        res = fit_aft_model(survival_data, dist="weibull")
        assert res["converged"]

    def test_lognormal_converges(self, survival_data):
        res = fit_aft_model(survival_data, dist="lognormal")
        assert res["converged"]

    def test_loglogistic_converges(self, survival_data):
        res = fit_aft_model(survival_data, dist="loglogistic")
        assert res["converged"]

    def test_sigma_positive(self, survival_data):
        for dist in ("weibull", "lognormal", "loglogistic"):
            res = fit_aft_model(survival_data, dist=dist)
            assert res["sigma"] > 0

    def test_aic_finite(self, survival_data):
        for dist in ("weibull", "lognormal", "loglogistic"):
            res = fit_aft_model(survival_data, dist=dist)
            assert np.isfinite(res["aic"])

    def test_bic_greater_than_aic(self, survival_data):
        """BIC penalizes more than AIC for n > e^2 ~ 7.4."""
        for dist in ("weibull", "lognormal", "loglogistic"):
            res = fit_aft_model(survival_data, dist=dist)
            # BIC >= AIC when n is large (which it is: ~1183)
            assert res["bic"] >= res["aic"] - 1  # allow small numerical slack

    def test_acceleration_factors_positive(self, survival_data):
        res = fit_aft_model(survival_data, dist="weibull")
        assert np.all(res["acceleration_factors"] > 0)

    def test_prize_acceleration_below_one(self, survival_data):
        """Prize should accelerate failure (AF < 1 means shorter survival)."""
        res = fit_aft_model(survival_data, dist="weibull")
        covariate_names = res["column_names"][1:]  # skip intercept
        idx = covariate_names.index("has_prize")
        assert res["acceleration_factors"][idx] < 1.0

    def test_coefficient_count(self, survival_data):
        res = fit_aft_model(survival_data, dist="weibull")
        # intercept + covariates
        assert len(res["coefficients"]) == len(res["column_names"])


class TestCompareAFT:
    def test_returns_all_three(self, survival_data):
        res = compare_aft_distributions(survival_data)
        assert "weibull" in res["models"]
        assert "lognormal" in res["models"]
        assert "loglogistic" in res["models"]

    def test_best_is_valid(self, survival_data):
        res = compare_aft_distributions(survival_data)
        assert res["best_distribution"] in ("weibull", "lognormal", "loglogistic")

    def test_best_has_lowest_aic(self, survival_data):
        res = compare_aft_distributions(survival_data)
        best = res["best_distribution"]
        best_aic = res["aic_table"][best]
        for d, aic in res["aic_table"].items():
            assert best_aic <= aic + 1e-6


# ===================================================================
# Log-rank test
# ===================================================================


class TestLogRank:
    def test_identical_groups(self):
        """Same distributions should give non-significant test."""
        rng = np.random.RandomState(42)
        n = 100
        t1 = rng.exponential(5, n)
        t2 = rng.exponential(5, n)
        e1 = np.ones(n, dtype=bool)
        e2 = np.ones(n, dtype=bool)
        stat, p = _log_rank_test(t1, e1, t2, e2)
        # Should NOT be significant (p > 0.01 with high probability)
        assert p > 0.01

    def test_different_groups(self):
        """Very different distributions should give significant test."""
        rng = np.random.RandomState(42)
        n = 100
        t1 = rng.exponential(2, n)  # fast failures
        t2 = rng.exponential(20, n)  # slow failures
        e1 = np.ones(n, dtype=bool)
        e2 = np.ones(n, dtype=bool)
        stat, p = _log_rank_test(t1, e1, t2, e2)
        assert p < 0.05

    def test_no_events_returns_zero(self):
        t1 = np.array([1.0, 2.0])
        t2 = np.array([3.0, 4.0])
        e1 = np.array([False, False])
        e2 = np.array([False, False])
        stat, p = _log_rank_test(t1, e1, t2, e2)
        assert stat == 0.0
        assert p == 1.0


class TestLogRankByCategory:
    def test_all_categories_tested(self, survival_data):
        res = log_rank_by_category(survival_data)
        cats = set(survival_data["tag_category"])
        assert set(res.keys()) == cats

    def test_p_values_valid(self, survival_data):
        res = log_rank_by_category(survival_data)
        for cat, r in res.items():
            assert 0 <= r["p_value"] <= 1

    def test_ramsey_significant(self, survival_data):
        """Ramsey theory should differ significantly from the rest."""
        res = log_rank_by_category(survival_data)
        if "ramsey" in res:
            assert res["ramsey"]["p_value"] < 0.05


# ===================================================================
# Integration: full analysis pipeline
# ===================================================================


class TestFullAnalysis:
    def test_runs_without_error(self, survival_data):
        """The full pipeline should execute cleanly."""
        # We pass data in to avoid re-loading
        # Just test the individual components return valid results
        km = km_summary(survival_data)
        assert km["n_total"] > 0

        cox = fit_cox_model(survival_data)
        assert cox["converged"]

        cr = competing_risks_cif(survival_data)
        assert cr["proved"]["n_events"] > 0

        cp = piecewise_hazard_model(
            survival_data, candidate_changepoints=[500, 750]
        )
        assert cp["best_changepoint"] in (500, 750)

        aft = fit_aft_model(survival_data, dist="weibull")
        assert aft["converged"]


class TestStatisticalSanity:
    """Cross-checks between different models for consistency."""

    def test_km_and_cox_agree_on_direction(self, survival_data):
        """Problems with prize should have higher resolution in both models."""
        # KM: split by prize
        prize_mask = survival_data["has_prize"]
        km_prize = kaplan_meier(
            survival_data["time"][prize_mask],
            survival_data["event"][prize_mask],
        )
        km_no_prize = kaplan_meier(
            survival_data["time"][~prize_mask],
            survival_data["event"][~prize_mask],
        )
        # Prize problems should resolve faster (lower median or lower S)
        # Check at t=500: S_prize < S_no_prize
        idx_p = np.searchsorted(km_prize["timeline"], 500, side="right") - 1
        idx_n = np.searchsorted(km_no_prize["timeline"], 500, side="right") - 1
        if idx_p >= 0 and idx_n >= 0:
            s_prize = km_prize["survival"][idx_p]
            s_no = km_no_prize["survival"][idx_n]
            assert s_prize < s_no  # prize problems resolve faster

        # Cox: HR for has_prize > 1
        cox = fit_cox_model(survival_data)
        idx = cox["column_names"].index("has_prize")
        assert cox["hazard_ratios"][idx] > 1.0

    def test_aft_and_cox_prize_direction(self, survival_data):
        """AFT acceleration factor < 1 is consistent with Cox HR > 1."""
        cox = fit_cox_model(survival_data)
        aft = fit_aft_model(survival_data, dist="weibull")

        cox_idx = cox["column_names"].index("has_prize")
        aft_names = aft["column_names"][1:]
        aft_idx = aft_names.index("has_prize")

        # Cox HR > 1 (higher hazard) <-> AFT AF < 1 (shorter time)
        assert cox["hazard_ratios"][cox_idx] > 1.0
        assert aft["acceleration_factors"][aft_idx] < 1.0

    def test_total_events_match(self, survival_data):
        """Proved + disproved + solved should match total events."""
        et = survival_data["event_type"]
        n_proved = np.sum(et == "proved")
        n_disproved = np.sum(et == "disproved")
        n_solved = np.sum(et == "solved")
        n_events = int(survival_data["event"].sum())
        assert n_proved + n_disproved + n_solved == n_events

    def test_competing_risks_add_to_km(self, survival_data):
        """CIF_proved + CIF_disproved should approximate 1 - KM at the end."""
        cr = competing_risks_cif(survival_data)
        km = kaplan_meier(survival_data["time"], survival_data["event"])

        # At the last event time, CIF1 + CIF2 should approximate 1 - S(last)
        if len(cr["proved"]["timeline"]) > 0 and len(km["timeline"]) > 0:
            cif_total = cr["proved"]["cif"][-1] + cr["disproved"]["cif"][-1]
            km_complement = 1 - km["survival"][-1]
            # These should be close (they're equivalent in theory)
            assert abs(cif_total - km_complement) < 0.05
