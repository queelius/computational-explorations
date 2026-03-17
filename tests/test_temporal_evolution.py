"""Tests for temporal_evolution.py — structural evolution analysis."""
import math
import numpy as np
import pytest

from temporal_evolution import (
    load_problems,
    problem_epochs,
    tag_emergence,
    difficulty_gradient,
    status_landscape,
    tag_succession,
    complexity_drift,
    named_problem_analysis,
    _entropy,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


class TestEntropy:
    """Test Shannon entropy helper."""

    def test_empty(self):
        from collections import Counter
        assert _entropy(Counter()) == 0.0

    def test_uniform(self):
        from collections import Counter
        c = Counter({"a": 10, "b": 10, "c": 10, "d": 10})
        assert abs(_entropy(c) - 2.0) < 0.01  # log2(4) = 2

    def test_concentrated(self):
        from collections import Counter
        c = Counter({"a": 100})
        assert _entropy(c) == 0.0

    def test_nonnegative(self):
        from collections import Counter
        c = Counter({"a": 5, "b": 3, "c": 1})
        assert _entropy(c) >= 0


class TestProblemEpochs:
    """Test problem epoch computation."""

    def test_returns_list(self, problems):
        epochs = problem_epochs(problems)
        assert isinstance(epochs, list)
        assert len(epochs) > 0

    def test_epoch_fields(self, problems):
        epochs = problem_epochs(problems)
        for e in epochs:
            assert "epoch_start" in e
            assert "epoch_end" in e
            assert "solve_rate" in e
            assert "dominant_tag" in e
            assert "avg_tags" in e

    def test_solve_rate_bounded(self, problems):
        epochs = problem_epochs(problems)
        for e in epochs:
            assert 0.0 <= e["solve_rate"] <= 1.0

    def test_epochs_cover_problems(self, problems):
        epochs = problem_epochs(problems)
        total = sum(e["size"] for e in epochs)
        assert total == len(problems)

    def test_epoch_ordering(self, problems):
        epochs = problem_epochs(problems)
        for i in range(len(epochs) - 1):
            assert epochs[i]["epoch_end"] < epochs[i + 1]["epoch_end"]

    def test_custom_epoch_size(self, problems):
        epochs = problem_epochs(problems, epoch_size=200)
        assert len(epochs) < 12  # fewer epochs with larger size


class TestTagEmergence:
    """Test tag lifecycle analysis."""

    def test_returns_dict(self, problems):
        result = tag_emergence(problems)
        assert isinstance(result, dict)

    def test_has_categories(self, problems):
        result = tag_emergence(problems)
        assert "emerging" in result
        assert "established" in result
        assert "declining" in result

    def test_tag_profiles_exist(self, problems):
        result = tag_emergence(problems)
        assert len(result["tag_profiles"]) > 0

    def test_profile_fields(self, problems):
        result = tag_emergence(problems)
        for tag, prof in list(result["tag_profiles"].items())[:5]:
            assert "first_appearance" in prof
            assert "count" in prof
            assert "solve_rate" in prof
            assert "density_curve" in prof

    def test_solve_rate_bounded(self, problems):
        result = tag_emergence(problems)
        for tag, prof in result["tag_profiles"].items():
            assert 0.0 <= prof["solve_rate"] <= 1.0

    def test_established_has_count(self, problems):
        result = tag_emergence(problems)
        for tag, count, rate in result["established"]:
            assert count > 0
            assert 0 <= rate <= 1


class TestDifficultyGradient:
    """Test difficulty gradient analysis."""

    def test_returns_dict(self, problems):
        result = difficulty_gradient(problems)
        assert isinstance(result, dict)

    def test_has_trend(self, problems):
        result = difficulty_gradient(problems)
        assert "trend_direction" in result
        assert result["trend_direction"] in ("getting easier", "getting harder", "stable", "insufficient data")

    def test_gradient_points(self, problems):
        result = difficulty_gradient(problems)
        assert len(result["gradient_points"]) > 0

    def test_solve_rate_bounded(self, problems):
        result = difficulty_gradient(problems)
        for gp in result["gradient_points"]:
            assert 0.0 <= gp["solve_rate"] <= 1.0

    def test_cliff_magnitude_bounded(self, problems):
        result = difficulty_gradient(problems)
        assert 0.0 <= result["cliff_magnitude"] <= 1.0


class TestStatusLandscape:
    """Test status landscape mapping."""

    def test_returns_dict(self, problems):
        result = status_landscape(problems)
        assert isinstance(result, dict)

    def test_has_landscape(self, problems):
        result = status_landscape(problems)
        assert len(result["landscape"]) > 0

    def test_rates_sum_approx_one(self, problems):
        result = status_landscape(problems)
        for lp in result["landscape"]:
            total = lp["proved"] + lp["disproved"] + lp["solved"] + lp["open"] + lp["tractable"]
            assert 0.8 <= total <= 1.2  # allow rounding

    def test_golden_zones(self, problems):
        result = status_landscape(problems)
        for center, rate in result["golden_zones"]:
            assert rate > 0.50


class TestTagSuccession:
    """Test tag succession pattern analysis."""

    def test_returns_dict(self, problems):
        result = tag_succession(problems)
        assert isinstance(result, dict)

    def test_successor_fields(self, problems):
        result = tag_succession(problems)
        for s in result["strongest_successors"]:
            assert "from_tag" in s
            assert "to_tag" in s
            assert "probability" in s
            assert 0.0 <= s["probability"] <= 1.0

    def test_self_reinforcing_bounded(self, problems):
        result = tag_succession(problems)
        for sr in result["self_reinforcing"]:
            assert 0.0 <= sr["self_prob"] <= 1.0

    def test_tag_momentum(self, problems):
        result = tag_succession(problems)
        assert len(result["tag_momentum"]) > 0
        for tag, mom in list(result["tag_momentum"].items())[:5]:
            assert mom["max_run"] >= 1
            assert mom["avg_run"] > 0


class TestComplexityDrift:
    """Test complexity drift analysis."""

    def test_returns_dict(self, problems):
        result = complexity_drift(problems)
        assert isinstance(result, dict)

    def test_has_drift_points(self, problems):
        result = complexity_drift(problems)
        assert len(result["drift_points"]) > 0

    def test_avg_tags_positive(self, problems):
        result = complexity_drift(problems)
        for dp in result["drift_points"]:
            assert dp["avg_tags"] > 0

    def test_entropy_nonneg(self, problems):
        result = complexity_drift(problems)
        for dp in result["drift_points"]:
            assert dp["tag_entropy"] >= 0


class TestNamedProblemAnalysis:
    """Test named problem analysis."""

    def test_returns_dict(self, problems):
        result = named_problem_analysis(problems)
        assert isinstance(result, dict)

    def test_named_count(self, problems):
        result = named_problem_analysis(problems)
        assert result["named_stats"]["count"] == 61

    def test_unnamed_count(self, problems):
        result = named_problem_analysis(problems)
        assert result["unnamed_stats"]["count"] == 1074

    def test_named_problems_list(self, problems):
        result = named_problem_analysis(problems)
        assert len(result["named_problems"]) == 61

    def test_named_have_comments(self, problems):
        result = named_problem_analysis(problems)
        for np_ in result["named_problems"]:
            assert np_["name"]  # non-empty comment

    def test_solve_rates_bounded(self, problems):
        result = named_problem_analysis(problems)
        assert 0 <= result["named_stats"]["solve_rate"] <= 1
        assert 0 <= result["unnamed_stats"]["solve_rate"] <= 1
