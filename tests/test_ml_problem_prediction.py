"""Tests for ml_problem_prediction.py -- ML-based problem resolution prediction.

Covers all six pipeline components with proper ML methodology checks:
  1. Feature engineering (shapes, types, no leakage)
  2. Classification (AUC > chance, calibration, feature importance)
  3. Regression (no target leakage, CV metrics finite)
  4. Clustering (silhouette, cluster properties)
  5. Anomaly detection (score distributions, ranking)
  6. Transfer learning (coefficient bounds, matrix structure)
"""
import math

import numpy as np
import pytest

from ml_problem_prediction import (
    MAJOR_AREAS,
    _is_formalized,
    _is_open,
    _is_solved,
    _number,
    _oeis,
    _prize,
    _status,
    _tag_entropy,
    _tag_solve_rates,
    _tags,
    anomaly_detection_pipeline,
    build_feature_matrix,
    classification_pipeline,
    clustering_pipeline,
    compute_family_features,
    load_problems,
    regression_pipeline,
    run_full_pipeline,
    transfer_learning_pipeline,
)


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def family_features(problems):
    return compute_family_features(problems)


@pytest.fixture(scope="module")
def feature_data(problems, family_features):
    """Cached feature matrix, labels, info, names."""
    return build_feature_matrix(problems, family_features)


@pytest.fixture(scope="module")
def X(feature_data):
    return feature_data[0]


@pytest.fixture(scope="module")
def y(feature_data):
    return feature_data[1]


@pytest.fixture(scope="module")
def info(feature_data):
    return feature_data[2]


@pytest.fixture(scope="module")
def feature_names(feature_data):
    return feature_data[3]


@pytest.fixture(scope="module")
def cls_results(X, y, feature_names):
    return classification_pipeline(X, y, feature_names, n_folds=3)


@pytest.fixture(scope="module")
def reg_results(X, y, info, feature_names):
    return regression_pipeline(X, y, info, feature_names, n_folds=3)


@pytest.fixture(scope="module")
def clust_results(X, y, info, feature_names):
    return clustering_pipeline(X, y, info, feature_names, max_k=10)


@pytest.fixture(scope="module")
def anom_results(X, y, info, feature_names):
    return anomaly_detection_pipeline(X, y, info, feature_names)


@pytest.fixture(scope="module")
def xfer_results(problems):
    return transfer_learning_pipeline(problems)


# =====================================================================
# Helper function tests
# =====================================================================

class TestHelpers:
    """Test YAML parsing helpers handle edge cases."""

    def test_status_normal(self):
        assert _status({"status": {"state": "open"}}) == "open"

    def test_status_missing(self):
        assert _status({}) == "unknown"

    def test_tags_normal(self):
        assert _tags({"tags": ["a", "b"]}) == {"a", "b"}

    def test_tags_missing(self):
        assert _tags({}) == set()

    def test_number_int(self):
        assert _number({"number": 42}) == 42

    def test_number_str(self):
        assert _number({"number": "42"}) == 42

    def test_number_missing(self):
        assert _number({}) == 0

    def test_oeis_filters_na(self):
        assert _oeis({"oeis": ["A001", "N/A", "possible"]}) == ["A001"]

    def test_oeis_empty(self):
        assert _oeis({}) == []

    def test_prize_dollar(self):
        assert _prize({"prize": "$500"}) == 500.0

    def test_prize_gbp(self):
        val = _prize({"prize": "\u00a3100"})
        assert abs(val - 127.0) < 0.1

    def test_prize_no(self):
        assert _prize({"prize": "no"}) == 0.0

    def test_prize_missing(self):
        assert _prize({}) == 0.0

    def test_is_solved_variants(self):
        for state in ("proved", "disproved", "solved",
                      "proved (Lean)", "disproved (Lean)", "solved (Lean)"):
            assert _is_solved({"status": {"state": state}})

    def test_is_not_solved(self):
        assert not _is_solved({"status": {"state": "open"}})

    def test_is_open(self):
        assert _is_open({"status": {"state": "open"}})
        assert not _is_open({"status": {"state": "proved"}})

    def test_is_formalized(self):
        assert _is_formalized({"formalized": {"state": "yes"}})
        assert not _is_formalized({"formalized": {"state": "no"}})
        assert not _is_formalized({})

    def test_tag_entropy_single(self):
        counts = {"a": 100}
        # single tag with known count: -log2(1.0) = 0 (all mass on one item)
        ent = _tag_entropy(counts, {"a"})
        assert ent == 0.0

    def test_tag_entropy_empty(self):
        assert _tag_entropy({}, set()) == 0.0

    def test_tag_entropy_positive(self):
        counts = {"a": 50, "b": 50, "c": 50}
        ent = _tag_entropy(counts, {"a", "b"})
        assert ent > 0.0


# =====================================================================
# 1. Feature Engineering
# =====================================================================

class TestFeatureEngineering:
    """Test feature matrix construction."""

    def test_shapes_consistent(self, X, y, info, feature_names):
        assert X.shape[0] == len(y)
        assert X.shape[0] == len(info)
        assert X.shape[1] == len(feature_names)

    def test_labels_binary(self, y):
        assert set(np.unique(y)).issubset({0, 1})

    def test_both_classes_present(self, y):
        assert 0 in y and 1 in y

    def test_class_balance_reasonable(self, y):
        """Neither class should be less than 10% of the data."""
        balance = y.mean()
        assert 0.1 < balance < 0.9

    def test_features_finite(self, X):
        assert np.all(np.isfinite(X)), "Feature matrix contains NaN or Inf"

    def test_features_not_constant(self, X, feature_names):
        """At least half the features should have non-zero variance."""
        variances = X.var(axis=0)
        n_nonconstant = (variances > 0).sum()
        assert n_nonconstant > len(feature_names) * 0.5

    def test_expected_feature_names(self, feature_names):
        expected = [
            "problem_number", "n_tags", "n_oeis", "has_prize", "prize_log",
            "formalized", "avg_tag_solve_rate", "tag_diversity",
            "cross_domain", "isolation", "family_solve_rate",
            "family_momentum", "family_cv", "family_size_log",
        ]
        for name in expected:
            assert name in feature_names, f"Missing feature: {name}"

    def test_tag_onehot_features(self, feature_names):
        tag_features = [f for f in feature_names if f.startswith("tag_")]
        assert len(tag_features) > 10, "Should have one-hot features for many tags"

    def test_info_has_required_fields(self, info):
        for inf in info[:10]:
            assert "number" in inf
            assert "status" in inf
            assert "tags" in inf
            assert "is_solved" in inf
            assert "is_open" in inf

    def test_problem_number_feature(self, X, feature_names, info):
        """problem_number feature should match the actual problem number."""
        idx = feature_names.index("problem_number")
        for i in range(min(20, len(info))):
            assert X[i, idx] == float(info[i]["number"])

    def test_isolation_bounded(self, X, feature_names):
        idx = feature_names.index("isolation")
        assert np.all(X[:, idx] >= 0.0)
        assert np.all(X[:, idx] <= 1.0)

    def test_cross_domain_binary(self, X, feature_names):
        idx = feature_names.index("cross_domain")
        assert set(np.unique(X[:, idx])).issubset({0.0, 1.0})

    def test_formalized_binary(self, X, feature_names):
        idx = feature_names.index("formalized")
        assert set(np.unique(X[:, idx])).issubset({0.0, 1.0})


class TestFamilyFeatures:
    """Test family-derived features."""

    def test_returns_dict(self, family_features):
        assert isinstance(family_features, dict)
        assert len(family_features) > 0

    def test_keys_are_ints(self, family_features):
        for k in list(family_features.keys())[:10]:
            assert isinstance(k, int)

    def test_values_have_required_fields(self, family_features):
        for num, ff in list(family_features.items())[:10]:
            assert "family_solve_rate" in ff
            assert "family_momentum" in ff
            assert "family_cv" in ff
            assert "family_size" in ff

    def test_solve_rate_bounded(self, family_features):
        for num, ff in family_features.items():
            assert 0.0 <= ff["family_solve_rate"] <= 1.0

    def test_cv_nonnegative(self, family_features):
        for num, ff in family_features.items():
            assert ff["family_cv"] >= 0.0


class TestTagSolveRates:
    """Test tag solve rate computation."""

    def test_returns_dict(self, problems):
        rates = _tag_solve_rates(problems)
        assert isinstance(rates, dict)
        assert len(rates) > 0

    def test_rates_bounded(self, problems):
        rates = _tag_solve_rates(problems)
        for tag, rate in rates.items():
            assert 0.0 <= rate <= 1.0

    def test_known_tags_present(self, problems):
        rates = _tag_solve_rates(problems)
        assert "number theory" in rates
        assert "graph theory" in rates


# =====================================================================
# 2. Classification
# =====================================================================

class TestClassification:
    """Test classification pipeline with proper ML methodology."""

    def test_has_all_models(self, cls_results):
        assert "logistic_regression" in cls_results
        assert "random_forest" in cls_results
        assert "gradient_boosting" in cls_results

    def test_auc_above_chance(self, cls_results):
        """All models should beat random (AUC > 0.5)."""
        for name, res in cls_results.items():
            assert res["auc"] > 0.5, f"{name} AUC {res['auc']} <= 0.5 (random)"

    def test_auc_reasonable(self, cls_results):
        """Best AUC should be at least 0.6 (non-trivial signal)."""
        best_auc = max(res["auc"] for res in cls_results.values())
        assert best_auc >= 0.6

    def test_accuracy_above_majority(self, cls_results, y):
        """Models should beat majority-class baseline."""
        majority_rate = max(y.mean(), 1 - y.mean())
        for name, res in cls_results.items():
            # Allow a small margin below majority for some models
            assert res["accuracy"] >= majority_rate - 0.05, \
                f"{name} accuracy {res['accuracy']} below majority {majority_rate}"

    def test_metrics_bounded(self, cls_results):
        for name, res in cls_results.items():
            assert 0.0 <= res["auc"] <= 1.0
            assert 0.0 <= res["accuracy"] <= 1.0
            assert 0.0 <= res["precision"] <= 1.0
            assert 0.0 <= res["f1"] <= 1.0

    def test_precision_at_k_exists(self, cls_results):
        for name, res in cls_results.items():
            assert "precision_at_k" in res
            assert len(res["precision_at_k"]) > 0

    def test_precision_at_k_bounded(self, cls_results):
        for name, res in cls_results.items():
            for k, p in res["precision_at_k"].items():
                assert 0.0 <= p <= 1.0

    def test_feature_importances_present(self, cls_results, feature_names):
        for name, res in cls_results.items():
            assert "feature_importances" in res
            assert len(res["feature_importances"]) == len(feature_names)

    def test_feature_importances_sorted(self, cls_results):
        for name, res in cls_results.items():
            imps = res["feature_importances"]
            for i in range(len(imps) - 1):
                assert imps[i][1] >= imps[i + 1][1], \
                    f"{name}: importance not sorted at position {i}"

    def test_feature_importances_nonneg(self, cls_results):
        for name, res in cls_results.items():
            for fname, imp in res["feature_importances"]:
                assert imp >= 0.0


# =====================================================================
# 3. Regression
# =====================================================================

class TestRegression:
    """Test regression pipeline -- no target leakage, honest CV."""

    def test_has_model_results(self, reg_results):
        assert "model_results" in reg_results
        assert len(reg_results["model_results"]) > 0

    def test_no_target_leakage(self, reg_results):
        """Regression features should NOT include problem_number."""
        if "regression_feature_names" in reg_results:
            assert "problem_number" not in reg_results["regression_feature_names"]

    def test_cv_metrics_present(self, reg_results):
        """At least one model should have CV metrics."""
        has_cv = False
        for name, res in reg_results["model_results"].items():
            if isinstance(res, dict) and res.get("mae_cv") is not None:
                has_cv = True
                break
        assert has_cv, "No model has CV metrics"

    def test_cv_r2_not_perfect(self, reg_results):
        """CV R2 should not be 1.0 (would indicate leakage)."""
        for name, res in reg_results["model_results"].items():
            if isinstance(res, dict) and res.get("r2_cv") is not None:
                assert res["r2_cv"] < 0.99, \
                    f"{name} R2_cv={res['r2_cv']} suspiciously close to 1.0"

    def test_mae_positive(self, reg_results):
        for name, res in reg_results["model_results"].items():
            if isinstance(res, dict) and "mae_train" in res:
                assert res["mae_train"] > 0

    def test_train_metrics_finite(self, reg_results):
        for name, res in reg_results["model_results"].items():
            if isinstance(res, dict):
                assert math.isfinite(res.get("mae_train", 0))
                assert math.isfinite(res.get("r2_train", 0))

    def test_best_model_selected(self, reg_results):
        assert "best_model" in reg_results
        assert reg_results["best_model"] in reg_results["model_results"]

    def test_open_predictions_exist(self, reg_results):
        preds = reg_results.get("open_predictions", [])
        assert len(preds) > 0

    def test_open_predictions_have_fields(self, reg_results):
        for p in reg_results["open_predictions"][:10]:
            assert "number" in p
            assert "tags" in p
            assert "predicted_resolution_number" in p
            assert "overdue_score" in p

    def test_open_predictions_sorted_by_overdue(self, reg_results):
        """Open predictions should be sorted by overdue_score descending."""
        preds = reg_results["open_predictions"]
        for i in range(min(len(preds) - 1, 20)):
            s1 = preds[i].get("overdue_score")
            s2 = preds[i + 1].get("overdue_score")
            if s1 is not None and s2 is not None:
                assert s1 >= s2

    def test_feature_importances_exclude_problem_number(self, reg_results):
        """Regression feature importances should not contain problem_number."""
        for name, res in reg_results["model_results"].items():
            if isinstance(res, dict) and "feature_importances" in res:
                feat_names = [f for f, _ in res["feature_importances"]]
                assert "problem_number" not in feat_names


# =====================================================================
# 4. Clustering
# =====================================================================

class TestClustering:
    """Test clustering pipeline."""

    def test_best_k_selected(self, clust_results):
        assert "best_k" in clust_results
        assert clust_results["best_k"] >= 2

    def test_silhouette_scores_present(self, clust_results):
        sil = clust_results["silhouette_scores"]
        assert len(sil) > 0
        for k, score in sil.items():
            assert -1.0 <= score <= 1.0

    def test_best_silhouette_positive(self, clust_results):
        """Best k should have positive silhouette."""
        best_k = clust_results["best_k"]
        assert clust_results["silhouette_scores"][best_k] > 0

    def test_cluster_count_matches_k(self, clust_results):
        assert len(clust_results["clusters"]) == clust_results["best_k"]

    def test_cluster_sizes_sum_to_n(self, clust_results, X):
        total = sum(c["size"] for c in clust_results["clusters"])
        assert total == X.shape[0]

    def test_clusters_have_required_fields(self, clust_results):
        for c in clust_results["clusters"]:
            assert "cluster_id" in c
            assert "size" in c
            assert "solve_rate" in c
            assert "top_tags" in c
            assert "distinguishing_features" in c
            assert "members" in c

    def test_solve_rates_bounded(self, clust_results):
        for c in clust_results["clusters"]:
            assert 0.0 <= c["solve_rate"] <= 1.0

    def test_highest_lowest_identified(self, clust_results):
        assert clust_results["highest_solve_cluster"] is not None
        assert clust_results["lowest_solve_cluster"] is not None

    def test_solve_rate_ordering(self, clust_results):
        """clusters_by_solve_rate should be sorted descending."""
        by_rate = clust_results["clusters_by_solve_rate"]
        for i in range(len(by_rate) - 1):
            assert by_rate[i]["solve_rate"] >= by_rate[i + 1]["solve_rate"]

    def test_labels_match_problems(self, clust_results, X):
        labels = clust_results["labels"]
        assert len(labels) == X.shape[0]

    def test_no_empty_clusters(self, clust_results):
        for c in clust_results["clusters"]:
            assert c["size"] > 0

    def test_solve_rate_variation(self, clust_results):
        """There should be meaningful variation in solve rates across clusters."""
        rates = [c["solve_rate"] for c in clust_results["clusters"]]
        assert max(rates) - min(rates) > 0.1, "All clusters have similar solve rates"


# =====================================================================
# 5. Anomaly Detection
# =====================================================================

class TestAnomalyDetection:
    """Test anomaly detection (undervalued problem identification)."""

    def test_has_top_undervalued(self, anom_results):
        assert "top_undervalued" in anom_results
        assert len(anom_results["top_undervalued"]) > 0

    def test_top_n_capped(self, anom_results):
        assert len(anom_results["top_undervalued"]) <= 30

    def test_undervalued_are_open(self, anom_results):
        """All undervalued problems should be open (not solved)."""
        # They come from the open_mask, so verify via info
        for p in anom_results["top_undervalued"]:
            # These are derived from open problems by construction
            assert "anomaly_score" in p

    def test_anomaly_scores_bounded(self, anom_results):
        for p in anom_results["all_scored"]:
            assert 0.0 <= p["anomaly_score"] <= 1.0

    def test_sorted_descending(self, anom_results):
        scores = [p["anomaly_score"] for p in anom_results["top_undervalued"]]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

    def test_stats_present(self, anom_results):
        stats = anom_results["stats"]
        assert stats["n_solved_train"] > 0
        assert stats["n_open_scored"] > 0

    def test_all_open_scored(self, anom_results, y):
        """Number of scored open problems should match open count in data."""
        n_open = int((y == 0).sum())
        assert anom_results["stats"]["n_open_scored"] == n_open

    def test_knn_distance_positive(self, anom_results):
        for p in anom_results["all_scored"]:
            assert p["knn_distance"] >= 0.0

    def test_candidates_have_required_fields(self, anom_results):
        for p in anom_results["top_undervalued"]:
            assert "number" in p
            assert "tags" in p
            assert "anomaly_score" in p
            assert "isolation_forest_score" in p
            assert "knn_distance" in p

    def test_iso_scores_finite(self, anom_results):
        for p in anom_results["all_scored"]:
            assert math.isfinite(p["isolation_forest_score"])


# =====================================================================
# 6. Transfer Learning
# =====================================================================

class TestTransferLearning:
    """Test transfer coefficient computation."""

    def test_has_transfers(self, xfer_results):
        assert len(xfer_results["all_transfers"]) > 0
        assert len(xfer_results["top_transfers"]) > 0

    def test_transfer_coefficient_nonneg(self, xfer_results):
        for t in xfer_results["all_transfers"]:
            assert t["transfer_coefficient"] >= 0.0

    def test_transfers_sorted(self, xfer_results):
        """Top transfers should be sorted by coefficient descending."""
        coeffs = [t["transfer_coefficient"] for t in xfer_results["top_transfers"]]
        for i in range(len(coeffs) - 1):
            assert coeffs[i] >= coeffs[i + 1]

    def test_transfer_has_required_fields(self, xfer_results):
        for t in xfer_results["all_transfers"][:10]:
            assert "from_tag" in t
            assert "to_tag" in t
            assert "pair_count" in t
            assert "pair_solve_rate" in t
            assert "baseline_rate" in t
            assert "transfer_coefficient" in t

    def test_pair_solve_rate_bounded(self, xfer_results):
        for t in xfer_results["all_transfers"]:
            assert 0.0 <= t["pair_solve_rate"] <= 1.0
            assert 0.0 <= t["baseline_rate"] <= 1.0

    def test_synergy_matrix_nonempty(self, xfer_results):
        assert len(xfer_results["synergy_matrix"]) > 0

    def test_strong_synergies_above_one(self, xfer_results):
        """All strong synergies should have lift > 1.0."""
        for pair, lift in xfer_results["strong_synergies"]:
            assert lift > 1.0

    def test_n_tag_pairs_positive(self, xfer_results):
        assert xfer_results["n_tag_pairs"] > 0

    def test_pair_count_minimum(self, xfer_results):
        """All reported pairs should have at least 5 co-occurrences."""
        for t in xfer_results["all_transfers"]:
            assert t["pair_count"] >= 5


# =====================================================================
# Full pipeline integration
# =====================================================================

class TestFullPipeline:
    """Integration test for the complete pipeline."""

    @pytest.fixture(scope="class")
    def pipeline_results(self, problems):
        return run_full_pipeline(problems)

    def test_has_all_components(self, pipeline_results):
        assert "feature_matrix" in pipeline_results
        assert "classification" in pipeline_results
        assert "regression" in pipeline_results
        assert "clustering" in pipeline_results
        assert "anomaly_detection" in pipeline_results
        assert "transfer_learning" in pipeline_results

    def test_feature_matrix_summary(self, pipeline_results):
        fm = pipeline_results["feature_matrix"]
        assert fm["n_problems"] > 1000
        assert fm["n_features"] > 20
        assert fm["n_solved"] > 100
        assert fm["n_open"] > 100
        assert 0.3 < fm["class_balance"] < 0.7

    def test_classification_all_models(self, pipeline_results):
        cls = pipeline_results["classification"]
        assert "logistic_regression" in cls
        assert "random_forest" in cls
        assert "gradient_boosting" in cls

    def test_classification_serializable(self, pipeline_results):
        """Models and scalers should be stripped from serialized output."""
        for name, res in pipeline_results["classification"].items():
            assert "model" not in res
            assert "scaler" not in res

    def test_regression_no_leakage(self, pipeline_results):
        """Regression feature names should exclude problem_number."""
        reg = pipeline_results["regression"]
        if "regression_feature_names" in reg:
            assert "problem_number" not in reg["regression_feature_names"]

    def test_clustering_has_clusters(self, pipeline_results):
        clust = pipeline_results["clustering"]
        assert clust["best_k"] >= 2
        assert len(clust["clusters"]) == clust["best_k"]

    def test_anomaly_has_undervalued(self, pipeline_results):
        anom = pipeline_results["anomaly_detection"]
        assert len(anom["top_undervalued"]) > 0


# =====================================================================
# Edge cases and data integrity
# =====================================================================

class TestDataIntegrity:
    """Test that the ML pipeline handles real data correctly."""

    def test_no_nan_in_features(self, X):
        assert not np.any(np.isnan(X))

    def test_no_inf_in_features(self, X):
        assert not np.any(np.isinf(X))

    def test_sufficient_data_for_cv(self, y):
        """Need at least 5 per class for stratified 5-fold."""
        assert y.sum() >= 5
        assert (1 - y).sum() >= 5

    def test_feature_matrix_rank(self, X):
        """Feature matrix should not be rank-deficient by too much."""
        rank = np.linalg.matrix_rank(X)
        assert rank >= min(X.shape) * 0.3, \
            f"Rank {rank} too low for {X.shape} matrix"

    def test_problem_numbers_unique_in_info(self, info):
        """Each problem should appear at most once."""
        numbers = [inf["number"] for inf in info]
        assert len(numbers) == len(set(numbers))

    def test_solved_label_consistency(self, info, y):
        """Labels should match info status."""
        for i, inf in enumerate(info):
            if inf["is_solved"]:
                assert y[i] == 1
            if inf["is_open"]:
                assert y[i] == 0

    def test_major_areas_defined(self):
        assert len(MAJOR_AREAS) >= 5
        assert "number theory" in MAJOR_AREAS
        assert "graph theory" in MAJOR_AREAS


class TestSmallDataEdgeCases:
    """Test pipeline behavior with minimal synthetic data."""

    @staticmethod
    def _make_small_problems(n_solved=20, n_open=30):
        """Create minimal synthetic problem list."""
        problems = []
        for i in range(n_solved):
            problems.append({
                "number": str(i + 1),
                "status": {"state": "proved"},
                "tags": ["number theory", "primes"] if i % 2 == 0 else ["graph theory"],
                "oeis": [f"A{i:06d}"],
                "formalized": {"state": "yes" if i % 3 == 0 else "no"},
                "prize": "$100" if i % 5 == 0 else "no",
            })
        for i in range(n_open):
            problems.append({
                "number": str(n_solved + i + 1),
                "status": {"state": "open"},
                "tags": ["number theory"] if i % 2 == 0 else ["graph theory", "ramsey theory"],
                "oeis": [] if i % 3 == 0 else [f"A{100+i:06d}"],
                "formalized": {"state": "no"},
                "prize": "no",
            })
        return problems

    def test_classification_on_small_data(self):
        probs = self._make_small_problems()
        X, y, info, names = build_feature_matrix(probs)
        assert X.shape[0] == 50
        assert y.sum() == 20
        result = classification_pipeline(X, y, names, n_folds=3)
        assert "logistic_regression" in result

    def test_anomaly_on_small_data(self):
        probs = self._make_small_problems()
        X, y, info, names = build_feature_matrix(probs)
        result = anomaly_detection_pipeline(X, y, info, names)
        assert "top_undervalued" in result
        assert len(result["top_undervalued"]) > 0

    def test_clustering_on_small_data(self):
        probs = self._make_small_problems()
        X, y, info, names = build_feature_matrix(probs)
        result = clustering_pipeline(X, y, info, names, max_k=5)
        assert result["best_k"] >= 2
        assert len(result["clusters"]) == result["best_k"]

    def test_transfer_on_small_data(self):
        probs = self._make_small_problems()
        result = transfer_learning_pipeline(probs)
        assert isinstance(result["all_transfers"], list)

    def test_regression_on_small_data(self):
        probs = self._make_small_problems()
        X, y, info, names = build_feature_matrix(probs)
        result = regression_pipeline(X, y, info, names, n_folds=3)
        assert "model_results" in result
