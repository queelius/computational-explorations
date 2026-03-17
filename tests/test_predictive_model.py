"""Tests for predictive_model.py — problem resolution forecasting."""
import math
import numpy as np
import pytest

from predictive_model import (
    load_problems,
    compute_features,
    train_logistic_regression,
    predict_probabilities,
    cross_validate,
    feature_importance,
    predict_next_solved,
    _sigmoid,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def features(problems):
    return compute_features(problems)


class TestSigmoid:
    """Test sigmoid helper."""

    def test_zero(self):
        assert abs(_sigmoid(np.array([0.0]))[0] - 0.5) < 1e-10

    def test_large_positive(self):
        assert _sigmoid(np.array([100.0]))[0] > 0.99

    def test_large_negative(self):
        assert _sigmoid(np.array([-100.0]))[0] < 0.01

    def test_symmetric(self):
        s_pos = _sigmoid(np.array([2.0]))[0]
        s_neg = _sigmoid(np.array([-2.0]))[0]
        assert abs(s_pos + s_neg - 1.0) < 1e-10

    def test_overflow_safe(self):
        """Should not overflow for extreme values."""
        result = _sigmoid(np.array([1000.0]))
        assert np.isfinite(result[0])
        result = _sigmoid(np.array([-1000.0]))
        assert np.isfinite(result[0])


class TestComputeFeatures:
    """Test feature matrix computation."""

    def test_returns_tuple(self, features):
        X, y, info, names = features
        assert isinstance(X, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert isinstance(info, list)
        assert isinstance(names, list)

    def test_shapes_consistent(self, features):
        X, y, info, names = features
        assert X.shape[0] == len(y)
        assert X.shape[0] == len(info)
        assert X.shape[1] == len(names)

    def test_labels_binary(self, features):
        _, y, _, _ = features
        assert set(np.unique(y)).issubset({0, 1})

    def test_both_classes(self, features):
        _, y, _, _ = features
        assert 0 in y
        assert 1 in y

    def test_features_finite(self, features):
        X, _, _, _ = features
        assert np.all(np.isfinite(X))

    def test_feature_names_nonempty(self, features):
        _, _, _, names = features
        assert len(names) > 10
        assert "avg_tag_solve_rate" in names

    def test_info_has_fields(self, features):
        _, _, info, _ = features
        for i in info[:5]:
            assert "number" in i
            assert "status" in i
            assert "tags" in i


class TestTrainModel:
    """Test logistic regression training."""

    def test_returns_weights(self, features):
        X, y, _, _ = features
        w, b, mean, std = train_logistic_regression(X, y, n_iter=50)
        assert len(w) == X.shape[1]
        assert isinstance(b, float)

    def test_weights_finite(self, features):
        X, y, _, _ = features
        w, b, mean, std = train_logistic_regression(X, y, n_iter=50)
        assert np.all(np.isfinite(w))
        assert math.isfinite(b)

    def test_predictions_bounded(self, features):
        X, y, _, _ = features
        w, b, mean, std = train_logistic_regression(X, y, n_iter=100)
        probs = predict_probabilities(X, w, b, mean, std)
        assert np.all(probs >= 0)
        assert np.all(probs <= 1)

    def test_regularization_effect(self, features):
        """Higher regularization should produce smaller weights."""
        X, y, _, _ = features
        w_low, _, _, _ = train_logistic_regression(X, y, reg=0.01, n_iter=100)
        w_high, _, _, _ = train_logistic_regression(X, y, reg=10.0, n_iter=100)
        assert np.linalg.norm(w_high) <= np.linalg.norm(w_low)


class TestCrossValidate:
    """Test cross-validation."""

    def test_returns_dict(self, features):
        X, y, _, _ = features
        cv = cross_validate(X, y, n_folds=3)
        assert isinstance(cv, dict)

    def test_has_required_fields(self, features):
        X, y, _, _ = features
        cv = cross_validate(X, y, n_folds=3)
        assert "avg_accuracy" in cv
        assert "avg_precision" in cv
        assert "avg_recall" in cv
        assert "folds" in cv

    def test_metrics_bounded(self, features):
        X, y, _, _ = features
        cv = cross_validate(X, y, n_folds=3)
        assert 0.0 <= cv["avg_accuracy"] <= 1.0
        assert 0.0 <= cv["avg_precision"] <= 1.0
        assert 0.0 <= cv["avg_recall"] <= 1.0

    def test_fold_count(self, features):
        X, y, _, _ = features
        cv = cross_validate(X, y, n_folds=3)
        assert len(cv["folds"]) == 3

    def test_accuracy_above_chance(self, features):
        """Model should beat random guessing."""
        X, y, _, _ = features
        cv = cross_validate(X, y, n_folds=3)
        # Random = ~50% for binary, our model should do better
        assert cv["avg_accuracy"] > 0.50


class TestFeatureImportance:
    """Test feature importance computation."""

    def test_returns_list(self, features):
        X, y, _, names = features
        w, b, mean, std = train_logistic_regression(X, y, n_iter=100)
        imp = feature_importance(w, std, names)
        assert isinstance(imp, list)
        assert len(imp) == len(names)

    def test_sorted_descending(self, features):
        X, y, _, names = features
        w, b, mean, std = train_logistic_regression(X, y, n_iter=100)
        imp = feature_importance(w, std, names)
        for i in range(len(imp) - 1):
            assert imp[i][1] >= imp[i + 1][1]

    def test_nonnegative(self, features):
        X, y, _, names = features
        w, b, mean, std = train_logistic_regression(X, y, n_iter=100)
        imp = feature_importance(w, std, names)
        for name, val in imp:
            assert val >= 0


class TestPredictNextSolved:
    """Test full prediction pipeline."""

    def test_returns_dict(self, problems):
        r = predict_next_solved(problems, top_k=5)
        assert isinstance(r, dict)

    def test_has_predictions(self, problems):
        r = predict_next_solved(problems, top_k=5)
        assert len(r["top_predictions"]) > 0

    def test_predictions_sorted(self, problems):
        r = predict_next_solved(problems, top_k=10)
        preds = r["top_predictions"]
        for i in range(len(preds) - 1):
            assert preds[i]["predicted_solvability"] >= preds[i + 1]["predicted_solvability"]

    def test_solvability_bounded(self, problems):
        r = predict_next_solved(problems, top_k=10)
        for p in r["top_predictions"]:
            assert 0.0 <= p["predicted_solvability"] <= 1.0

    def test_score_separation_positive(self, problems):
        """Solved problems should score higher on average."""
        r = predict_next_solved(problems, top_k=10)
        assert r["model_stats"]["score_separation"] >= 0

    def test_model_stats_format(self, problems):
        r = predict_next_solved(problems, top_k=5)
        stats = r["model_stats"]
        assert stats["n_features"] > 0
        assert stats["n_train"] > 0
        assert stats["n_predict"] > 0
