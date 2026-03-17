"""Tests for difficulty_evolution.py — how problem hardness evolves."""
import math
import numpy as np
import pytest

from difficulty_evolution import (
    load_problems,
    resolution_density,
    era_analysis,
    breakthrough_cascades,
    difficulty_features,
    survival_analysis,
    tag_difficulty_ranking,
    difficulty_concentration,
    _number,
    _tags,
    _is_solved,
    _has_prize,
    _prize_value,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


# ── Helpers ─────────────────────────────────────────────────────────

class TestHelpers:
    """Test internal helper functions."""

    def test_number_valid(self):
        assert _number({"number": 42}) == 42

    def test_number_string(self):
        assert _number({"number": "42"}) == 42

    def test_number_missing(self):
        assert _number({}) == 0

    def test_tags(self):
        assert _tags({"tags": ["a", "b"]}) == {"a", "b"}

    def test_has_prize_yes(self):
        assert _has_prize({"prize": 500}) is True

    def test_has_prize_no(self):
        assert _has_prize({"prize": None}) is False

    def test_prize_value(self):
        assert _prize_value({"prize": 500}) == 500.0

    def test_prize_value_string(self):
        assert _prize_value({"prize": "$1000"}) == 1000.0

    def test_prize_value_none(self):
        assert _prize_value({}) == 0.0


# ── Resolution density ─────────────────────────────────────────────

class TestResolutionDensity:
    """Test resolution density by problem number window."""

    def test_returns_dict(self, problems):
        result = resolution_density(problems)
        assert isinstance(result, dict)

    def test_has_windows(self, problems):
        result = resolution_density(problems)
        assert len(result["windows"]) > 10

    def test_solve_rates_bounded(self, problems):
        result = resolution_density(problems)
        for w in result["windows"]:
            assert 0.0 <= w["solve_rate"] <= 1.0

    def test_overall_rate_reasonable(self, problems):
        result = resolution_density(problems)
        assert 0.3 < result["overall_solve_rate"] < 0.6

    def test_trend_valid(self, problems):
        result = resolution_density(problems)
        assert result["trend"] in ("increasing", "decreasing", "stable",
                                    "insufficient_data")

    def test_window_numbers_increasing(self, problems):
        result = resolution_density(problems)
        starts = [w["start_num"] for w in result["windows"]]
        assert starts == sorted(starts)


# ── Era analysis ───────────────────────────────────────────────────

class TestEraAnalysis:
    """Test era-based analysis."""

    def test_returns_dict(self, problems):
        result = era_analysis(problems)
        assert isinstance(result, dict)

    def test_has_eras(self, problems):
        result = era_analysis(problems)
        assert result["n_eras"] >= 5

    def test_era_fields(self, problems):
        result = era_analysis(problems)
        for e in result["eras"]:
            assert "era" in e
            assert "solve_rate" in e
            assert "n_problems" in e
            assert "dominant_tags" in e

    def test_solve_rates_bounded(self, problems):
        result = era_analysis(problems)
        for e in result["eras"]:
            assert 0.0 <= e["solve_rate"] <= 1.0

    def test_early_era_high_prize(self, problems):
        """Early era should have highest prize fraction."""
        result = era_analysis(problems)
        early = [e for e in result["eras"] if e["era"] == "Early"]
        assert len(early) == 1
        assert early[0]["prize_fraction"] > 0.2

    def test_total_problems(self, problems):
        result = era_analysis(problems)
        total = sum(e["n_problems"] for e in result["eras"])
        assert total > 1000


# ── Breakthrough cascades ──────────────────────────────────────────

class TestBreakthroughCascades:
    """Test breakthrough cascade detection."""

    def test_returns_dict(self, problems):
        result = breakthrough_cascades(problems)
        assert isinstance(result, dict)

    def test_has_cascades(self, problems):
        result = breakthrough_cascades(problems)
        assert result["n_cascades"] > 5

    def test_cascade_sizes_positive(self, problems):
        result = breakthrough_cascades(problems)
        for c in result["cascades"]:
            assert c["size"] >= 3

    def test_cascade_sorted_by_size(self, problems):
        result = breakthrough_cascades(problems)
        for i in range(len(result["cascades"]) - 1):
            assert result["cascades"][i]["size"] >= result["cascades"][i+1]["size"]

    def test_largest_cascade_substantial(self, problems):
        result = breakthrough_cascades(problems)
        assert result["largest_cascade"] > 10

    def test_cascade_fraction_high(self, problems):
        """Most solved problems should be in cascades."""
        result = breakthrough_cascades(problems)
        assert result["cascade_fraction"] > 0.5

    def test_cascade_has_tags(self, problems):
        result = breakthrough_cascades(problems)
        for c in result["cascades"][:5]:
            assert len(c["dominant_tags"]) > 0

    def test_cascade_span_consistent(self, problems):
        result = breakthrough_cascades(problems)
        for c in result["cascades"]:
            assert c["span"] == c["end"] - c["start"]


# ── Difficulty features ────────────────────────────────────────────

class TestDifficultyFeatures:
    """Test difficulty feature comparison."""

    def test_returns_dict(self, problems):
        result = difficulty_features(problems)
        assert isinstance(result, dict)

    def test_has_comparisons(self, problems):
        result = difficulty_features(problems)
        assert len(result["comparisons"]) >= 4

    def test_n_tags_present(self, problems):
        result = difficulty_features(problems)
        assert "n_tags" in result["comparisons"]

    def test_number_present(self, problems):
        result = difficulty_features(problems)
        assert "number" in result["comparisons"]

    def test_counts_positive(self, problems):
        result = difficulty_features(problems)
        assert result["n_solved"] > 400
        assert result["n_open"] > 500


# ── Survival analysis ──────────────────────────────────────────────

class TestSurvivalAnalysis:
    """Test survival analysis of open problems."""

    def test_returns_dict(self, problems):
        result = survival_analysis(problems)
        assert isinstance(result, dict)

    def test_has_curve(self, problems):
        result = survival_analysis(problems)
        assert len(result["survival_curve"]) > 5

    def test_survival_decreasing(self, problems):
        result = survival_analysis(problems)
        probs = [b["survival_prob"] for b in result["survival_curve"]]
        # Survival probability should generally decrease
        assert probs[0] >= probs[-1]

    def test_survival_bounded(self, problems):
        result = survival_analysis(problems)
        for b in result["survival_curve"]:
            assert 0.0 <= b["survival_prob"] <= 1.0

    def test_events_positive(self, problems):
        result = survival_analysis(problems)
        assert result["n_events"] > 400

    def test_censored_positive(self, problems):
        result = survival_analysis(problems)
        assert result["n_censored"] > 500

    def test_median_exists(self, problems):
        result = survival_analysis(problems)
        # May or may not reach 50% survival
        assert result["median_survival_age"] is None or isinstance(
            result["median_survival_age"], str)


# ── Tag difficulty ranking ─────────────────────────────────────────

class TestTagDifficultyRanking:
    """Test tag difficulty ranking."""

    def test_returns_dict(self, problems):
        result = tag_difficulty_ranking(problems)
        assert isinstance(result, dict)

    def test_has_rankings(self, problems):
        result = tag_difficulty_ranking(problems)
        assert result["n_ranked"] > 15

    def test_sorted_by_solve_rate(self, problems):
        result = tag_difficulty_ranking(problems)
        rates = [r["solve_rate"] for r in result["rankings"]]
        assert rates == sorted(rates)

    def test_rates_bounded(self, problems):
        result = tag_difficulty_ranking(problems)
        for r in result["rankings"]:
            assert 0.0 <= r["solve_rate"] <= 1.0

    def test_hardest_is_hard(self, problems):
        result = tag_difficulty_ranking(problems)
        assert result["rankings"][0]["solve_rate"] < 0.35

    def test_easiest_is_easy(self, problems):
        result = tag_difficulty_ranking(problems)
        assert result["rankings"][-1]["solve_rate"] > 0.45


# ── Difficulty concentration ───────────────────────────────────────

class TestDifficultyConcentration:
    """Test difficulty concentration measurement."""

    def test_returns_dict(self, problems):
        result = difficulty_concentration(problems)
        assert isinstance(result, dict)

    def test_gini_bounded(self, problems):
        result = difficulty_concentration(problems)
        assert 0.0 <= result["gini"] <= 1.0

    def test_distribution_valid(self, problems):
        result = difficulty_concentration(problems)
        assert result["distribution"] in ("concentrated", "moderately_spread",
                                          "uniform", "insufficient_data")

    def test_range_positive(self, problems):
        result = difficulty_concentration(problems)
        assert result["range"] > 0

    def test_min_less_than_max(self, problems):
        result = difficulty_concentration(problems)
        assert result["min_rate"] < result["max_rate"]


# ── Integration ────────────────────────────────────────────────────

class TestReport:
    """Test full report generation."""

    def test_report_nonempty(self, problems):
        from difficulty_evolution import generate_report
        report = generate_report(problems)
        assert len(report) > 500

    def test_report_sections(self, problems):
        from difficulty_evolution import generate_report
        report = generate_report(problems)
        assert "Resolution Density" in report
        assert "Era Analysis" in report
        assert "Breakthrough Cascades" in report
        assert "Survival Analysis" in report
        assert "Tag Difficulty Ranking" in report
