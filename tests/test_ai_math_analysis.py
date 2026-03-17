"""Tests for ai_math_analysis.py -- AI impact on mathematical discovery."""
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import ai_math_analysis as ama


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def problems():
    """Load the full problems YAML once per module."""
    return ama.load_problems()


@pytest.fixture
def mini_corpus():
    """A small synthetic corpus for unit testing."""
    return [
        # Resolved pre-AI
        {"number": "10", "status": {"state": "proved", "last_update": "2025-08-31"},
         "formalized": {"state": "no", "last_update": "2025-08-31"},
         "tags": ["number theory"], "prize": "$500", "oeis": ["A000001"]},
        {"number": "20", "status": {"state": "disproved", "last_update": "2025-08-31"},
         "formalized": {"state": "yes", "last_update": "2025-08-31"},
         "tags": ["graph theory"], "prize": "no", "oeis": ["N/A"]},
        # Resolved in AI era
        {"number": "30", "status": {"state": "proved (Lean)", "last_update": "2025-10-15"},
         "formalized": {"state": "yes", "last_update": "2025-10-15"},
         "tags": ["graph theory", "ramsey theory"], "prize": "no", "oeis": ["A000002"]},
        {"number": "40", "status": {"state": "proved", "last_update": "2025-12-20"},
         "formalized": {"state": "yes", "last_update": "2025-12-20"},
         "tags": ["number theory", "primes"], "prize": "$100", "oeis": ["A000003"]},
        {"number": "50", "status": {"state": "solved (Lean)", "last_update": "2026-01-10"},
         "formalized": {"state": "yes", "last_update": "2026-01-10"},
         "tags": ["analysis"], "prize": "no", "oeis": ["A000004", "A000005"]},
        {"number": "60", "status": {"state": "proved (Lean)", "last_update": "2026-01-20"},
         "formalized": {"state": "yes", "last_update": "2026-01-20"},
         "tags": ["graph theory", "distances"], "prize": "no", "oeis": []},
        # Open problems
        {"number": "70", "status": {"state": "open", "last_update": "2025-08-31"},
         "formalized": {"state": "yes", "last_update": "2025-08-31"},
         "tags": ["number theory", "additive combinatorics"], "prize": "$1000",
         "oeis": ["A000006"]},
        {"number": "80", "status": {"state": "open", "last_update": "2025-08-31"},
         "formalized": {"state": "no", "last_update": "2025-08-31"},
         "tags": ["graph theory"], "prize": "no", "oeis": ["N/A"]},
        {"number": "90", "status": {"state": "open", "last_update": "2025-08-31"},
         "formalized": {"state": "yes", "last_update": "2025-08-31"},
         "tags": ["analysis", "irrationality"], "prize": "no", "oeis": []},
        {"number": "100", "status": {"state": "open", "last_update": "2026-03-14"},
         "formalized": {"state": "no", "last_update": "2025-08-31"},
         "tags": ["number theory"], "prize": "no", "oeis": ["possible"]},
    ]


# ── Helper Tests ──────────────────────────────────────────────────────

class TestHelpers:
    """Tests for data extraction helpers."""

    def test_normalize_date_standard(self):
        assert ama._normalize_date("2025-09-07") == "2025-09-07"

    def test_normalize_date_missing_zero(self):
        assert ama._normalize_date("2025-11-4") == "2025-11-04"
        assert ama._normalize_date("2025-9-3") == "2025-09-03"

    def test_normalize_date_bad_input(self):
        assert ama._normalize_date("bad") == "bad"
        assert ama._normalize_date("") == ""

    def test_number_str(self):
        assert ama._number({"number": "42"}) == 42

    def test_number_int(self):
        assert ama._number({"number": 42}) == 42

    def test_number_missing(self):
        assert ama._number({}) == 0

    def test_number_invalid(self):
        assert ama._number({"number": "abc"}) == 0

    def test_status(self):
        p = {"status": {"state": "proved"}}
        assert ama._status(p) == "proved"

    def test_status_missing(self):
        assert ama._status({}) == "unknown"

    def test_tags_present(self):
        p = {"tags": ["number theory", "primes"]}
        assert ama._tags(p) == {"number theory", "primes"}

    def test_tags_missing(self):
        assert ama._tags({}) == set()

    def test_is_resolved_proved(self):
        assert ama._is_resolved({"status": {"state": "proved"}})

    def test_is_resolved_lean(self):
        assert ama._is_resolved({"status": {"state": "proved (Lean)"}})
        assert ama._is_resolved({"status": {"state": "disproved (Lean)"}})
        assert ama._is_resolved({"status": {"state": "solved (Lean)"}})

    def test_is_resolved_open(self):
        assert not ama._is_resolved({"status": {"state": "open"}})

    def test_is_lean(self):
        assert ama._is_lean({"status": {"state": "proved (Lean)"}})
        assert not ama._is_lean({"status": {"state": "proved"}})

    def test_is_formalized(self):
        assert ama._is_formalized({"formalized": {"state": "yes"}})
        assert not ama._is_formalized({"formalized": {"state": "no"}})
        assert not ama._is_formalized({})

    def test_prize_value_dollar(self):
        assert ama._prize_value({"prize": "$500"}) == 500.0

    def test_prize_value_pound(self):
        val = ama._prize_value({"prize": "\u00a325"})
        assert abs(val - 25 * 1.27) < 0.01

    def test_prize_value_rupee(self):
        val = ama._prize_value({"prize": "\u20b92000"})
        assert abs(val - 2000 * 0.012) < 0.01

    def test_prize_value_none(self):
        assert ama._prize_value({"prize": "no"}) == 0.0
        assert ama._prize_value({}) == 0.0

    def test_month_key(self):
        assert ama._month_key("2026-01-23") == "2026-01"
        assert ama._month_key("2025-08-31") == "2025-08"

    def test_date_to_months_since(self):
        m = ama._date_to_months_since("2025-09-01", "2025-08-01")
        assert 0.9 < m < 1.1  # approximately 1 month

    def test_date_to_months_since_same(self):
        assert ama._date_to_months_since("2025-08-01", "2025-08-01") == 0.0


# ── Act 1: Resolution Velocity ────────────────────────────────────────

class TestResolutionVelocity:
    """Tests for resolution velocity analysis."""

    def test_mini_corpus_counts(self, mini_corpus):
        result = ama.resolution_velocity(mini_corpus)
        assert result["total_recent"] == 4  # 4 AI-era resolved

    def test_mini_corpus_monthly(self, mini_corpus):
        result = ama.resolution_velocity(mini_corpus)
        mc = result["monthly_counts"]
        assert mc.get("2025-10", 0) == 1
        assert mc.get("2025-12", 0) == 1
        assert mc.get("2026-01", 0) == 2

    def test_cumulative_monotonic(self, mini_corpus):
        result = ama.resolution_velocity(mini_corpus)
        cumul = [c for _, c in result["cumulative"]]
        assert cumul == sorted(cumul)

    def test_fits_present(self, mini_corpus):
        result = ama.resolution_velocity(mini_corpus)
        # With only 3 months, fits may or may not converge
        assert isinstance(result["fits"], dict)

    def test_ai_multiplier_positive(self, mini_corpus):
        result = ama.resolution_velocity(mini_corpus)
        assert result["ai_multiplier"] > 0

    def test_best_model_valid(self, mini_corpus):
        result = ama.resolution_velocity(mini_corpus)
        assert result["best_model"] in {"linear", "exponential", "logistic", "none"}

    def test_full_corpus_213_recent(self, problems):
        result = ama.resolution_velocity(problems)
        assert result["total_recent"] == 213

    def test_full_corpus_7_months(self, problems):
        result = ama.resolution_velocity(problems)
        assert len(result["monthly_counts"]) == 7  # Sep 2025 through Mar 2026

    def test_full_corpus_multiplier_large(self, problems):
        result = ama.resolution_velocity(problems)
        # AI era should be much faster than 80 years of human effort
        assert result["ai_multiplier"] > 50

    def test_full_corpus_cumulative_213(self, problems):
        result = ama.resolution_velocity(problems)
        cumul = [c for _, c in result["cumulative"]]
        assert cumul[-1] == 213

    def test_full_corpus_fits_have_aic(self, problems):
        result = ama.resolution_velocity(problems)
        for model, info in result["fits"].items():
            assert "aic" in info
            assert "residual" in info
            assert info["residual"] >= 0

    def test_aic_computation(self):
        """AIC should penalize models with more parameters."""
        # Same RSS, more params -> higher AIC
        aic2 = ama._aic(10, 100.0, 2)
        aic4 = ama._aic(10, 100.0, 4)
        assert aic4 > aic2

    def test_aic_lower_rss_better(self):
        """Lower RSS -> lower AIC for same number of params."""
        aic_low = ama._aic(10, 50.0, 2)
        aic_high = ama._aic(10, 200.0, 2)
        assert aic_low < aic_high


# ── Act 2: Problem Type Analysis ──────────────────────────────────────

class TestProblemTypeAnalysis:
    """Tests for tag family acceleration analysis."""

    def test_mini_corpus_structured_deep(self, mini_corpus):
        result = ama.problem_type_analysis(mini_corpus)
        sd = result["structured_vs_deep"]
        assert sd["structured"]["total"] > 0
        assert sd["deep"]["total"] > 0

    def test_tag_acceleration_keys(self, mini_corpus):
        result = ama.problem_type_analysis(mini_corpus)
        for tag, info in result["tag_acceleration"].items():
            assert "total" in info
            assert "ai_era_solved" in info
            assert "multiplier" in info

    def test_full_corpus_top_accelerated(self, problems):
        result = ama.problem_type_analysis(problems)
        top = result["top_accelerated"]
        assert len(top) > 0
        # Each entry should have multiplier >= 1 (faster than baseline)
        for tag, info in top:
            if info["multiplier"] is not None:
                assert info["multiplier"] > 0

    def test_full_corpus_structured_deep_populated(self, problems):
        result = ama.problem_type_analysis(problems)
        sd = result["structured_vs_deep"]
        assert sd["structured"]["total"] > 100
        assert sd["deep"]["total"] > 100

    def test_full_corpus_all_counts_consistent(self, problems):
        """AI-era solved should not exceed total for any tag."""
        result = ama.problem_type_analysis(problems)
        for tag, info in result["tag_acceleration"].items():
            assert info["ai_era_solved"] <= info["total"]
            assert info["pre_ai_solved"] <= info["total"]

    def test_structured_families_defined(self):
        """Structured families should include graph-theoretic tags."""
        assert "graph theory" in ama.STRUCTURED_FAMILIES
        assert "ramsey theory" in ama.STRUCTURED_FAMILIES

    def test_deep_families_defined(self):
        """Deep families should include number theory tags."""
        assert "number theory" in ama.DEEP_FAMILIES
        assert "analysis" in ama.DEEP_FAMILIES


# ── Act 3: Lean Formalization Factor ──────────────────────────────────

class TestLeanFactor:
    """Tests for Lean formalization analysis."""

    def test_mini_corpus_lean_counts(self, mini_corpus):
        result = ama.lean_factor_analysis(mini_corpus)
        # 3 Lean-status resolved (proved (Lean) + solved (Lean))
        assert result["ai_era_lean"] == 3

    def test_mini_corpus_formalized_count(self, mini_corpus):
        result = ama.lean_factor_analysis(mini_corpus)
        # Count yes states: #20, #30, #40, #50, #60, #70, #90 = 7
        assert result["total_formalized"] == 7

    def test_phi_coefficient_range(self, mini_corpus):
        result = ama.lean_factor_analysis(mini_corpus)
        assert -1.0 <= result["phi_coefficient"] <= 1.0

    def test_contingency_sums(self, mini_corpus):
        result = ama.lean_factor_analysis(mini_corpus)
        ct = result["contingency_table"]
        total_from_table = (ct["formalized_resolved"] + ct["formalized_open"]
                            + ct["not_formalized_resolved"] + ct["not_formalized_open"])
        # Should account for all problems (some may be in other states)
        assert total_from_table <= result["total_problems"]

    def test_full_corpus_120_lean(self, problems):
        result = ama.lean_factor_analysis(problems)
        assert result["total_lean_resolved"] == 120

    def test_full_corpus_118_recent_lean(self, problems):
        result = ama.lean_factor_analysis(problems)
        assert result["ai_era_lean"] == 118

    def test_full_corpus_formalization_paradox(self, problems):
        """Known finding: negative phi (formalized = less likely resolved)."""
        result = ama.lean_factor_analysis(problems)
        assert result["phi_coefficient"] < 0

    def test_full_corpus_ai_era_lean_fraction(self, problems):
        result = ama.lean_factor_analysis(problems)
        # 118/213 ~ 55%
        assert 0.5 < result["ai_era_lean_fraction"] < 0.6

    def test_lean_monthly_timeline(self, problems):
        result = ama.lean_factor_analysis(problems)
        # Should have monthly Lean resolution data
        assert len(result["lean_resolution_monthly"]) > 0


# ── Act 4: Difficulty Curve ───────────────────────────────────────────

class TestDifficultyCurve:
    """Tests for difficulty trajectory analysis."""

    def test_mini_corpus_monthly(self, mini_corpus):
        result = ama.difficulty_curve(mini_corpus)
        assert len(result["monthly_avg_number"]) > 0

    def test_mini_corpus_avg_number_reasonable(self, mini_corpus):
        result = ama.difficulty_curve(mini_corpus)
        for m, avg in result["monthly_avg_number"].items():
            assert 0 < avg < 200  # mini corpus numbers are 10-100

    def test_mini_corpus_avg_tags_reasonable(self, mini_corpus):
        result = ama.difficulty_curve(mini_corpus)
        for m, avg in result["monthly_avg_tags"].items():
            assert 0 < avg < 10

    def test_full_corpus_7_months(self, problems):
        result = ama.difficulty_curve(problems)
        assert len(result["sorted_months"]) == 7

    def test_full_corpus_trend_slope(self, problems):
        result = ama.difficulty_curve(problems)
        # Slope is defined (some value)
        assert isinstance(result["difficulty_trend_slope"], float)

    def test_full_corpus_halves_populated(self, problems):
        result = ama.difficulty_curve(problems)
        assert result["first_half_avg_number"] > 0
        assert result["second_half_avg_number"] > 0

    def test_full_corpus_moving_to_harder(self, problems):
        """The data shows AI is moving to harder (lower-numbered) problems."""
        result = ama.difficulty_curve(problems)
        assert result["low_hanging_fruit_depleted"]


# ── Act 5: Prediction ─────────────────────────────────────────────────

class TestPrediction:
    """Tests for the resolution predictor."""

    def test_mini_corpus_predictions(self, mini_corpus):
        result = ama.predict_next_solved(mini_corpus, top_n=5)
        # Should predict from the 4 open problems
        assert result["total_open"] == 4
        assert len(result["top_predictions"]) <= 5

    def test_mini_corpus_scores_bounded(self, mini_corpus):
        result = ama.predict_next_solved(mini_corpus, top_n=10)
        for p in result["top_predictions"]:
            assert 0.0 <= p["score"] <= 1.0

    def test_mini_corpus_sorted_by_score(self, mini_corpus):
        result = ama.predict_next_solved(mini_corpus, top_n=10)
        scores = [p["score"] for p in result["top_predictions"]]
        assert scores == sorted(scores, reverse=True)

    def test_feature_weights_sum_to_one(self, mini_corpus):
        result = ama.predict_next_solved(mini_corpus)
        weights = list(result["feature_weights"].values())
        assert abs(sum(weights) - 1.0) < 0.01

    def test_feature_weights_non_negative(self, mini_corpus):
        result = ama.predict_next_solved(mini_corpus)
        for w in result["feature_weights"].values():
            assert w >= 0.0

    def test_full_corpus_top_20(self, problems):
        result = ama.predict_next_solved(problems, top_n=20)
        assert len(result["top_predictions"]) == 20

    def test_full_corpus_all_open(self, problems):
        result = ama.predict_next_solved(problems)
        assert result["total_open"] == 650

    def test_full_corpus_predictions_are_open(self, problems):
        """All predicted problems must actually be open."""
        result = ama.predict_next_solved(problems)
        open_numbers = {ama._number(p) for p in problems if ama._is_open(p)}
        for pred in result["top_predictions"]:
            assert pred["number"] in open_numbers

    def test_full_corpus_features_present(self, problems):
        result = ama.predict_next_solved(problems)
        for pred in result["top_predictions"]:
            assert "features" in pred
            assert len(pred["features"]) == 8

    def test_full_corpus_8_feature_names(self, problems):
        result = ama.predict_next_solved(problems)
        assert len(result["feature_names"]) == 8


# ── Narrative Synthesis ───────────────────────────────────────────────

class TestSynthesis:
    """Tests for the full narrative synthesis."""

    def test_mini_corpus_narrative(self, mini_corpus):
        n = ama.synthesize_narrative(mini_corpus)
        assert n["corpus_size"] == 10
        assert n["total_resolved"] == 6
        assert n["total_open"] == 4

    def test_mini_corpus_headlines(self, mini_corpus):
        n = ama.synthesize_narrative(mini_corpus)
        assert len(n["headlines"]) >= 5

    def test_full_corpus_narrative(self, problems):
        n = ama.synthesize_narrative(problems)
        assert n["corpus_size"] == 1183
        assert n["total_resolved"] == 483
        assert n["total_open"] == 650

    def test_full_corpus_all_acts_present(self, problems):
        n = ama.synthesize_narrative(problems)
        assert "act1_velocity" in n
        assert "act2_types" in n
        assert "act3_lean" in n
        assert "act4_difficulty" in n
        assert "act5_predictions" in n


# ── Report Generation ─────────────────────────────────────────────────

class TestReport:
    """Tests for markdown report generation."""

    def test_report_has_title(self, mini_corpus):
        n = ama.synthesize_narrative(mini_corpus)
        report = ama.generate_report(n)
        assert "# How AI Is Changing Mathematical Discovery" in report

    def test_report_has_five_acts(self, mini_corpus):
        n = ama.synthesize_narrative(mini_corpus)
        report = ama.generate_report(n)
        assert "Act 1" in report
        assert "Act 2" in report
        assert "Act 3" in report
        assert "Act 4" in report
        assert "Act 5" in report

    def test_report_has_tables(self, mini_corpus):
        n = ama.synthesize_narrative(mini_corpus)
        report = ama.generate_report(n)
        assert "|" in report

    def test_report_has_epilogue(self, mini_corpus):
        n = ama.synthesize_narrative(mini_corpus)
        report = ama.generate_report(n)
        assert "Epilogue" in report


# ── Curve Fitting Functions ───────────────────────────────────────────

class TestCurveFunctions:
    """Tests for the mathematical curve functions."""

    def test_linear_identity(self):
        assert ama._linear(0, 1, 0) == 0
        assert ama._linear(5, 2, 3) == 13

    def test_exponential_at_zero(self):
        # a * exp(b*0) + c = a + c
        assert abs(ama._exponential(0, 2, 1, 3) - 5.0) < 1e-10

    def test_logistic_at_midpoint(self):
        # At t=t0, logistic = L/2 + b
        val = ama._logistic(5.0, L=100, k=1, t0=5.0, b=0)
        assert abs(val - 50.0) < 1e-10

    def test_logistic_monotonic(self):
        """Logistic should be monotonically increasing for k > 0."""
        t = np.linspace(0, 20, 100)
        y = ama._logistic(t, L=100, k=0.5, t0=10, b=0)
        diffs = np.diff(y)
        assert np.all(diffs >= 0)

    def test_logistic_bounded(self):
        """Logistic should approach L + b."""
        val = ama._logistic(1000.0, L=100, k=1, t0=5, b=10)
        assert abs(val - 110.0) < 0.01


# ── Data Integrity ────────────────────────────────────────────────────

class TestDataIntegrity:
    """Tests that verify known properties of the dataset."""

    def test_total_problems(self, problems):
        assert len(problems) == 1183

    def test_resolved_count(self, problems):
        resolved = sum(1 for p in problems if ama._is_resolved(p))
        assert resolved == 483

    def test_open_count(self, problems):
        open_count = sum(1 for p in problems if ama._is_open(p))
        assert open_count == 650

    def test_lean_resolved_count(self, problems):
        lean = sum(1 for p in problems if ama._is_lean(p))
        assert lean == 120

    def test_recent_resolutions(self, problems):
        recent = sum(1 for p in problems
                     if ama._is_resolved(p) and ama._status_date(p) > ama.BASELINE_DATE)
        assert recent == 213

    def test_recent_lean(self, problems):
        recent_lean = sum(1 for p in problems
                          if ama._is_lean(p) and ama._status_date(p) > ama.BASELINE_DATE)
        assert recent_lean == 118

    def test_formalized_count(self, problems):
        formalized = sum(1 for p in problems if ama._is_formalized(p))
        assert formalized == 383

    def test_jan_2026_spike(self, problems):
        """January 2026 had the most resolutions -- the GPT-5.2 effect."""
        monthly = Counter()
        for p in problems:
            if ama._is_resolved(p) and ama._status_date(p) > ama.BASELINE_DATE:
                monthly[ama._month_key(ama._status_date(p))] += 1
        assert monthly["2026-01"] == 60
        assert monthly["2026-01"] == max(monthly.values())

    def test_number_theory_most_common_tag(self, problems):
        """Number theory should be the most common tag among AI-era resolutions."""
        tag_counts = Counter()
        for p in problems:
            if ama._is_resolved(p) and ama._status_date(p) > ama.BASELINE_DATE:
                for t in ama._tags(p):
                    tag_counts[t] += 1
        assert tag_counts.most_common(1)[0][0] == "number theory"
