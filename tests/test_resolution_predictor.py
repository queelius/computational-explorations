"""Tests for resolution_predictor.py — KNN resolution probability."""
import math
import numpy as np
import pytest

from resolution_predictor import (
    load_problems,
    build_features,
    predict_resolution,
    cross_validate,
    feature_importance,
    surprise_problems,
    tag_forecast,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def feature_data(problems):
    return build_features(problems)


@pytest.fixture(scope="module")
def predictions(problems, feature_data):
    return predict_resolution(problems, feature_data)


# ── build_features ───────────────────────────────────────────────────

class TestBuildFeatures:
    """Test feature matrix construction."""

    def test_returns_dict(self, feature_data):
        assert isinstance(feature_data, dict)

    def test_feature_shape(self, feature_data, problems):
        assert feature_data["features"].shape == (len(problems), 7)

    def test_dim_names_count(self, feature_data):
        assert len(feature_data["dim_names"]) == 7

    def test_no_is_solved_feature(self, feature_data):
        assert "is_solved" not in feature_data["dim_names"]

    def test_no_formalized_feature(self, feature_data):
        assert "formalized" not in feature_data["dim_names"]

    def test_features_bounded(self, feature_data):
        F = feature_data["features"]
        assert np.all(F >= 0.0 - 1e-6)
        assert np.all(F <= 1.0 + 1e-6)

    def test_no_nan(self, feature_data):
        assert not np.any(np.isnan(feature_data["features"]))

    def test_labels_present(self, feature_data):
        labels = feature_data["labels"]
        assert set(np.unique(labels)).issubset({-1, 0, 1})

    def test_has_solved_and_open(self, feature_data):
        labels = feature_data["labels"]
        assert (labels == 1).sum() > 100  # Many solved
        assert (labels == 0).sum() > 100  # Many open


# ── predict_resolution ───────────────────────────────────────────────

class TestPredictResolution:
    """Test KNN resolution probability."""

    def test_returns_list(self, predictions):
        assert isinstance(predictions, list)

    def test_only_open_problems(self, predictions, feature_data):
        open_nums = set(feature_data["numbers"][i]
                        for i in range(len(feature_data["labels"]))
                        if feature_data["labels"][i] == 0)
        for p in predictions:
            assert p["number"] in open_nums

    def test_sorted_by_probability(self, predictions):
        for i in range(len(predictions) - 1):
            assert predictions[i]["probability"] >= predictions[i + 1]["probability"] - 1e-6

    def test_probability_bounded(self, predictions):
        for p in predictions:
            assert 0.0 <= p["probability"] <= 1.0

    def test_has_fields(self, predictions):
        for p in predictions:
            assert "number" in p
            assert "probability" in p
            assert "tags" in p
            assert "prize" in p
            assert "nearest_solved" in p

    def test_nearest_solved_are_solved(self, predictions, problems):
        solved_states = {"proved", "disproved", "solved",
                         "proved (Lean)", "disproved (Lean)", "solved (Lean)"}
        solved_nums = {int(p.get("number", 0)) for p in problems
                       if p.get("status", {}).get("state") in solved_states}
        for pred in predictions[:20]:
            for ns in pred["nearest_solved"]:
                assert ns in solved_nums

    def test_count_matches_open(self, predictions, feature_data):
        n_open = (feature_data["labels"] == 0).sum()
        assert len(predictions) == n_open


# ── cross_validate ───────────────────────────────────────────────────

class TestCrossValidate:
    """Test leave-one-out cross-validation."""

    def test_returns_dict(self, problems, feature_data):
        cv = cross_validate(problems, feature_data)
        assert isinstance(cv, dict)

    def test_accuracy_above_chance(self, problems, feature_data):
        cv = cross_validate(problems, feature_data)
        # Base rate is ~59% (majority class), should beat it
        assert cv["accuracy"] > 0.55

    def test_precision_positive(self, problems, feature_data):
        cv = cross_validate(problems, feature_data)
        assert cv["precision"] > 0

    def test_recall_positive(self, problems, feature_data):
        cv = cross_validate(problems, feature_data)
        assert cv["recall"] > 0

    def test_confusion_matrix_sums(self, problems, feature_data):
        cv = cross_validate(problems, feature_data)
        total = cv["tp"] + cv["fp"] + cv["fn"] + cv["tn"]
        assert total == cv["n_valid"]

    def test_has_calibration(self, problems, feature_data):
        cv = cross_validate(problems, feature_data)
        assert "calibration" in cv
        assert len(cv["calibration"]) > 0

    def test_calibration_counts_positive(self, problems, feature_data):
        cv = cross_validate(problems, feature_data)
        for c in cv["calibration"]:
            assert c["count"] > 0


# ── feature_importance ───────────────────────────────────────────────

class TestFeatureImportance:
    """Test permutation-based feature importance."""

    def test_returns_list(self, problems, feature_data):
        result = feature_importance(problems, feature_data)
        assert isinstance(result, list)

    def test_count_matches_dims(self, problems, feature_data):
        result = feature_importance(problems, feature_data)
        assert len(result) == len(feature_data["dim_names"])

    def test_sorted_by_importance(self, problems, feature_data):
        result = feature_importance(problems, feature_data)
        for i in range(len(result) - 1):
            assert result[i]["importance"] >= result[i + 1]["importance"] - 1e-6

    def test_importance_nonneg(self, problems, feature_data):
        result = feature_importance(problems, feature_data)
        for fi in result:
            assert fi["importance"] >= 0

    def test_tag_solve_rate_important(self, problems, feature_data):
        result = feature_importance(problems, feature_data)
        # tag_solve_rate should be in top 3
        top3 = [r["feature"] for r in result[:3]]
        assert "tag_solve_rate" in top3

    def test_has_fields(self, problems, feature_data):
        result = feature_importance(problems, feature_data)
        for fi in result:
            assert "feature" in fi
            assert "importance" in fi
            assert "baseline_accuracy" in fi
            assert "permuted_accuracy" in fi


# ── surprise_problems ────────────────────────────────────────────────

class TestSurpriseProblems:
    """Test surprise and stuck problem detection."""

    def test_returns_dict(self, problems, feature_data):
        result = surprise_problems(problems, feature_data)
        assert isinstance(result, dict)

    def test_has_keys(self, problems, feature_data):
        result = surprise_problems(problems, feature_data)
        assert "surprises" in result
        assert "stuck" in result

    def test_surprises_are_solved(self, problems, feature_data):
        result = surprise_problems(problems, feature_data)
        for s in result["surprises"]:
            assert s["actual"] == "solved"

    def test_stuck_are_open(self, problems, feature_data):
        result = surprise_problems(problems, feature_data)
        for s in result["stuck"]:
            assert s["actual"] == "open"

    def test_surprise_low_prob(self, problems, feature_data):
        result = surprise_problems(problems, feature_data)
        for s in result["surprises"]:
            assert s["predicted_prob"] <= 0.3

    def test_stuck_high_prob(self, problems, feature_data):
        result = surprise_problems(problems, feature_data)
        for s in result["stuck"]:
            assert s["predicted_prob"] >= 0.7

    def test_sorted(self, problems, feature_data):
        result = surprise_problems(problems, feature_data)
        for i in range(len(result["surprises"]) - 1):
            assert result["surprises"][i]["predicted_prob"] <= result["surprises"][i + 1]["predicted_prob"]
        for i in range(len(result["stuck"]) - 1):
            assert result["stuck"][i]["predicted_prob"] >= result["stuck"][i + 1]["predicted_prob"]


# ── tag_forecast ─────────────────────────────────────────────────────

class TestTagForecast:
    """Test tag resolution forecast."""

    def test_returns_list(self, problems, predictions):
        result = tag_forecast(problems, predictions)
        assert isinstance(result, list)

    def test_has_tags(self, problems, predictions):
        result = tag_forecast(problems, predictions)
        assert len(result) > 10

    def test_sorted_by_expected(self, problems, predictions):
        result = tag_forecast(problems, predictions)
        for i in range(len(result) - 1):
            assert result[i]["expected_resolutions"] >= result[i + 1]["expected_resolutions"] - 1e-6

    def test_expected_nonneg(self, problems, predictions):
        result = tag_forecast(problems, predictions)
        for f in result:
            assert f["expected_resolutions"] >= 0

    def test_avg_prob_bounded(self, problems, predictions):
        result = tag_forecast(problems, predictions)
        for f in result:
            assert 0.0 <= f["avg_probability"] <= 1.0

    def test_number_theory_top(self, problems, predictions):
        result = tag_forecast(problems, predictions)
        # Number theory has most open problems, should have most expected
        assert result[0]["tag"] == "number theory"

    def test_has_fields(self, problems, predictions):
        result = tag_forecast(problems, predictions)
        for f in result:
            assert "tag" in f
            assert "expected_resolutions" in f
            assert "avg_probability" in f
            assert "open_count" in f
