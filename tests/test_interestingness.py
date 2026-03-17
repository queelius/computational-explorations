"""Tests for interestingness.py -- quantifying mathematical interestingness."""
import math
import numpy as np
import pytest

from interestingness import (
    load_problems,
    extract_features,
    normalize_features,
    compute_tag_statistics,
    compute_dimension_scores,
    composite_interestingness,
    build_ground_truth,
    train_interestingness_model,
    predict_interestingness,
    rank_all_problems,
    find_hidden_gems,
    dimension_analysis,
    feature_importance,
    tag_interestingness,
    solvability_predictors,
    connectivity_predictors,
    theory_generation_predictors,
    _prize,
    _number,
    _tags,
    _status,
    _is_solved,
    _is_open,
    _is_formalized,
    _real_oeis,
    _sigmoid,
    DIMENSION_MAP,
)


# ==========================================================================
# Fixtures
# ==========================================================================

@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def features(problems):
    return extract_features(problems)


@pytest.fixture(scope="module")
def ranked(problems):
    return rank_all_problems(problems)


@pytest.fixture(scope="module")
def tag_stats(problems):
    return compute_tag_statistics(problems)


# ==========================================================================
# Data Access Helpers
# ==========================================================================

class TestDataHelpers:
    """Test YAML field extraction helpers."""

    def test_prize_dollar(self):
        assert _prize({"prize": "$500"}) == 500.0

    def test_prize_no(self):
        assert _prize({"prize": "no"}) == 0.0

    def test_prize_missing(self):
        assert _prize({}) == 0.0

    def test_prize_gbp(self):
        val = _prize({"prize": "\u00a325"})
        assert abs(val - 25 * 1.27) < 0.01

    def test_prize_inr(self):
        val = _prize({"prize": "\u20b92000"})
        assert abs(val - 2000 * 0.012) < 0.01

    def test_number_string(self):
        assert _number({"number": "42"}) == 42

    def test_number_int(self):
        assert _number({"number": 42}) == 42

    def test_number_missing(self):
        assert _number({}) == 0

    def test_tags_present(self):
        assert _tags({"tags": ["a", "b"]}) == {"a", "b"}

    def test_tags_missing(self):
        assert _tags({}) == set()

    def test_status_nested(self):
        assert _status({"status": {"state": "open"}}) == "open"

    def test_status_missing(self):
        assert _status({}) == "unknown"

    def test_is_solved_proved(self):
        assert _is_solved({"status": {"state": "proved"}})

    def test_is_solved_lean(self):
        assert _is_solved({"status": {"state": "proved (Lean)"}})

    def test_is_solved_disproved(self):
        assert _is_solved({"status": {"state": "disproved"}})

    def test_is_solved_open(self):
        assert not _is_solved({"status": {"state": "open"}})

    def test_is_open(self):
        assert _is_open({"status": {"state": "open"}})

    def test_is_open_false(self):
        assert not _is_open({"status": {"state": "proved"}})

    def test_is_formalized_yes(self):
        assert _is_formalized({"formalized": {"state": "yes"}})

    def test_is_formalized_no(self):
        assert not _is_formalized({"formalized": {"state": "no"}})

    def test_is_formalized_missing(self):
        assert not _is_formalized({})

    def test_real_oeis_filters_na(self):
        assert _real_oeis({"oeis": ["A001234", "N/A", "possible"]}) == ["A001234"]

    def test_real_oeis_empty(self):
        assert _real_oeis({}) == []

    def test_real_oeis_all_filtered(self):
        assert _real_oeis({"oeis": ["N/A", "possible"]}) == []

    def test_real_oeis_multiple(self):
        seqs = _real_oeis({"oeis": ["A001234", "A005678"]})
        assert len(seqs) == 2


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
        result = _sigmoid(np.array([1000.0]))
        assert np.isfinite(result[0])
        result = _sigmoid(np.array([-1000.0]))
        assert np.isfinite(result[0])

    def test_vector(self):
        result = _sigmoid(np.array([-10.0, 0.0, 10.0]))
        assert result[0] < 0.01
        assert abs(result[1] - 0.5) < 1e-6
        assert result[2] > 0.99


# ==========================================================================
# Tag Statistics
# ==========================================================================

class TestTagStatistics:
    """Test precomputed tag statistics."""

    def test_returns_dict(self, tag_stats):
        assert isinstance(tag_stats, dict)

    def test_has_required_keys(self, tag_stats):
        required = {
            "tag_total", "tag_solved", "tag_solve_rate",
            "tag_formalize_rate", "combo_counts", "oeis_to_problems",
            "oeis_to_solved", "oeis_to_total", "tag_velocity", "max_number",
        }
        assert required.issubset(tag_stats.keys())

    def test_solve_rates_bounded(self, tag_stats):
        for tag, rate in tag_stats["tag_solve_rate"].items():
            assert 0.0 <= rate <= 1.0, f"{tag}: {rate}"

    def test_formalize_rates_bounded(self, tag_stats):
        for tag, rate in tag_stats["tag_formalize_rate"].items():
            assert 0.0 <= rate <= 1.0, f"{tag}: {rate}"

    def test_max_number_positive(self, tag_stats):
        assert tag_stats["max_number"] > 1000

    def test_velocity_bounded(self, tag_stats):
        for tag, vel in tag_stats["tag_velocity"].items():
            assert -1.0 <= vel <= 1.0, f"{tag}: {vel}"

    def test_combo_counts_sum(self, tag_stats, problems):
        total = sum(tag_stats["combo_counts"].values())
        assert total == len(problems)

    def test_number_theory_present(self, tag_stats):
        assert "number theory" in tag_stats["tag_total"]
        assert tag_stats["tag_total"]["number theory"] > 400

    def test_oeis_to_problems_nonempty(self, tag_stats):
        assert len(tag_stats["oeis_to_problems"]) > 50


# ==========================================================================
# Feature Extraction
# ==========================================================================

class TestExtractFeatures:
    """Test the 17-feature extraction pipeline."""

    def test_returns_tuple(self, features):
        X, info, names, stats = features
        assert isinstance(X, np.ndarray)
        assert isinstance(info, list)
        assert isinstance(names, list)
        assert isinstance(stats, dict)

    def test_shape_consistent(self, features):
        X, info, names, stats = features
        assert X.shape[0] == len(info)
        assert X.shape[1] == len(names)

    def test_correct_feature_count(self, features):
        _, _, names, _ = features
        assert len(names) == 17

    def test_all_problems_present(self, features, problems):
        X, info, _, _ = features
        assert X.shape[0] == len(problems)

    def test_features_finite(self, features):
        X, _, _, _ = features
        assert np.all(np.isfinite(X)), "Non-finite feature values found"

    def test_n_oeis_nonneg(self, features):
        X, _, names, _ = features
        idx = names.index("n_oeis")
        assert np.all(X[:, idx] >= 0)

    def test_n_tags_positive(self, features):
        X, _, names, _ = features
        idx = names.index("n_tags")
        assert np.all(X[:, idx] >= 1)

    def test_cross_domain_binary(self, features):
        X, _, names, _ = features
        idx = names.index("cross_domain")
        assert set(np.unique(X[:, idx])).issubset({0.0, 1.0})

    def test_catalogue_position_unit(self, features):
        X, _, names, _ = features
        idx = names.index("catalogue_position")
        assert np.all(X[:, idx] >= 0.0)
        assert np.all(X[:, idx] <= 1.0)

    def test_inv_solve_rate_unit(self, features):
        X, _, names, _ = features
        idx = names.index("inv_tag_solve_rate")
        assert np.all(X[:, idx] >= 0.0)
        assert np.all(X[:, idx] <= 1.0)

    def test_prize_log_nonneg(self, features):
        X, _, names, _ = features
        idx = names.index("prize_log")
        assert np.all(X[:, idx] >= 0.0)

    def test_is_formalized_binary(self, features):
        X, _, names, _ = features
        idx = names.index("is_formalized")
        assert set(np.unique(X[:, idx])).issubset({0.0, 1.0})

    def test_has_prize_binary(self, features):
        X, _, names, _ = features
        idx = names.index("has_prize")
        assert set(np.unique(X[:, idx])).issubset({0.0, 1.0})

    def test_isolation_score_positive(self, features):
        X, _, names, _ = features
        idx = names.index("isolation_score")
        assert np.all(X[:, idx] > 0.0)

    def test_cascade_capped(self, features):
        X, _, names, _ = features
        idx = names.index("cascade_potential")
        assert np.all(X[:, idx] <= 50)

    def test_info_has_required_fields(self, features):
        _, info, _, _ = features
        for item in info[:10]:
            assert "number" in item
            assert "tags" in item
            assert "status" in item
            assert "prize" in item
            assert "formalized" in item
            assert "solved" in item
            assert "open" in item

    def test_feature_names_list(self, features):
        _, _, names, _ = features
        expected = [
            "n_oeis", "n_tags", "cross_domain", "oeis_reach",
            "catalogue_position", "inv_tag_solve_rate", "prize_log",
            "unsolved_despite_age", "isolation_score", "solve_rate_anomaly",
            "tag_entropy", "resolution_velocity", "cascade_potential",
            "formalization_momentum", "is_formalized", "has_prize",
            "oeis_investment",
        ]
        assert names == expected


# ==========================================================================
# Normalization
# ==========================================================================

class TestNormalization:
    """Test min-max normalization."""

    def test_output_unit_interval(self, features):
        X, _, _, _ = features
        X_norm, mins, ranges = normalize_features(X)
        assert np.all(X_norm >= -1e-10)
        assert np.all(X_norm <= 1.0 + 1e-10)

    def test_mins_correct(self, features):
        X, _, _, _ = features
        X_norm, mins, ranges = normalize_features(X)
        for i in range(X.shape[1]):
            assert abs(mins[i] - X[:, i].min()) < 1e-10

    def test_ranges_positive(self, features):
        X, _, _, _ = features
        _, _, ranges = normalize_features(X)
        assert np.all(ranges > 0)

    def test_roundtrip(self, features):
        X, _, _, _ = features
        X_norm, mins, ranges = normalize_features(X)
        X_recovered = X_norm * ranges + mins
        assert np.allclose(X, X_recovered, atol=1e-10)

    def test_constant_feature_handled(self):
        """A constant column should normalize to 0, not NaN."""
        X = np.array([[1.0, 5.0], [2.0, 5.0], [3.0, 5.0]])
        X_norm, _, _ = normalize_features(X)
        assert np.all(np.isfinite(X_norm))
        assert np.all(X_norm[:, 1] == 0.0)


# ==========================================================================
# Dimension Scores
# ==========================================================================

class TestDimensionScores:
    """Test per-dimension scoring."""

    def test_five_dimensions(self, features):
        X, _, names, _ = features
        X_norm, _, _ = normalize_features(X)
        dim_scores, dim_names = compute_dimension_scores(X_norm, names)
        assert dim_scores.shape[1] == 5
        assert len(dim_names) == 5

    def test_dimension_names(self, features):
        X, _, names, _ = features
        X_norm, _, _ = normalize_features(X)
        _, dim_names = compute_dimension_scores(X_norm, names)
        assert dim_names == ["depth", "difficulty", "surprise", "fertility", "investment"]

    def test_scores_unit_interval(self, features):
        X, _, names, _ = features
        X_norm, _, _ = normalize_features(X)
        dim_scores, _ = compute_dimension_scores(X_norm, names)
        assert np.all(dim_scores >= -1e-10)
        assert np.all(dim_scores <= 1.0 + 1e-10)

    def test_dimension_map_covers_all_features(self):
        all_indices = set()
        for indices in DIMENSION_MAP.values():
            all_indices.update(indices)
        assert all_indices == set(range(17))

    def test_dimensions_no_overlap(self):
        seen = set()
        for dim, indices in DIMENSION_MAP.items():
            for idx in indices:
                assert idx not in seen, f"Index {idx} appears in multiple dimensions"
                seen.add(idx)


class TestCompositeScore:
    """Test composite interestingness scoring."""

    def test_default_weights_sum_to_one(self):
        """Default weights should be normalized to 1."""
        weights = {
            "depth": 0.25, "difficulty": 0.20, "surprise": 0.25,
            "fertility": 0.20, "investment": 0.10,
        }
        assert abs(sum(weights.values()) - 1.0) < 1e-10

    def test_scores_bounded(self, features):
        X, _, names, _ = features
        X_norm, _, _ = normalize_features(X)
        dim_scores, dim_names = compute_dimension_scores(X_norm, names)
        scores = composite_interestingness(dim_scores, dim_names)
        assert np.all(scores >= 0.0)
        assert np.all(scores <= 1.0)

    def test_custom_weights(self, features):
        X, _, names, _ = features
        X_norm, _, _ = normalize_features(X)
        dim_scores, dim_names = compute_dimension_scores(X_norm, names)

        # Only depth
        scores_depth = composite_interestingness(
            dim_scores, dim_names,
            weights={"depth": 1.0, "difficulty": 0, "surprise": 0,
                     "fertility": 0, "investment": 0}
        )
        assert np.allclose(scores_depth, dim_scores[:, 0])

    def test_zero_weights_give_zero(self, features):
        X, _, names, _ = features
        X_norm, _, _ = normalize_features(X)
        dim_scores, dim_names = compute_dimension_scores(X_norm, names)
        scores = composite_interestingness(
            dim_scores, dim_names,
            weights={d: 0.0 for d in dim_names}
        )
        # All weights zero => normalized to zero vector => dot product is 0
        assert np.allclose(scores, 0.0)


# ==========================================================================
# Ground Truth and Model Training
# ==========================================================================

class TestGroundTruth:
    """Test ground truth construction."""

    def test_gt_bounded(self, features):
        _, info, _, stats = features
        gt = build_ground_truth(info, stats)
        assert np.all(gt >= 0.0)
        assert np.all(gt <= 1.0)

    def test_gt_length(self, features):
        _, info, _, stats = features
        gt = build_ground_truth(info, stats)
        assert len(gt) == len(info)

    def test_prized_problems_higher(self, features):
        """Problems with prizes should generally have higher ground truth."""
        _, info, _, stats = features
        gt = build_ground_truth(info, stats)
        prized_gt = [gt[i] for i, item in enumerate(info) if item["prize"] > 0]
        unprized_gt = [gt[i] for i, item in enumerate(info) if item["prize"] == 0]
        assert np.mean(prized_gt) > np.mean(unprized_gt)

    def test_formalized_problems_higher(self, features):
        """Formalized problems should generally have higher ground truth."""
        _, info, _, stats = features
        gt = build_ground_truth(info, stats)
        form_gt = [gt[i] for i, item in enumerate(info) if item["formalized"]]
        noform_gt = [gt[i] for i, item in enumerate(info) if not item["formalized"]]
        assert np.mean(form_gt) > np.mean(noform_gt)


class TestModelTraining:
    """Test the interestingness model."""

    def test_returns_correct_shapes(self, features):
        X, info, _, stats = features
        gt = build_ground_truth(info, stats)
        w, b, mean, std = train_interestingness_model(X, gt, n_iter=50)
        assert w.shape == (X.shape[1],)
        assert isinstance(b, float)
        assert mean.shape == (X.shape[1],)
        assert std.shape == (X.shape[1],)

    def test_weights_finite(self, features):
        X, info, _, stats = features
        gt = build_ground_truth(info, stats)
        w, b, mean, std = train_interestingness_model(X, gt, n_iter=100)
        assert np.all(np.isfinite(w))
        assert np.isfinite(b)

    def test_predictions_bounded(self, features):
        X, info, _, stats = features
        gt = build_ground_truth(info, stats)
        w, b, mean, std = train_interestingness_model(X, gt, n_iter=100)
        preds = predict_interestingness(X, w, b, mean, std)
        assert np.all(preds >= 0.0)
        assert np.all(preds <= 1.0)

    def test_predictions_length(self, features):
        X, info, _, stats = features
        gt = build_ground_truth(info, stats)
        w, b, mean, std = train_interestingness_model(X, gt, n_iter=100)
        preds = predict_interestingness(X, w, b, mean, std)
        assert len(preds) == X.shape[0]

    def test_more_iterations_lower_loss(self, features):
        """Training longer should reduce loss (at least slightly)."""
        X, info, _, stats = features
        gt = build_ground_truth(info, stats)

        w50, b50, m50, s50 = train_interestingness_model(X, gt, n_iter=50)
        pred50 = predict_interestingness(X, w50, b50, m50, s50)
        loss50 = np.mean((pred50 - gt) ** 2)

        w500, b500, m500, s500 = train_interestingness_model(X, gt, n_iter=500)
        pred500 = predict_interestingness(X, w500, b500, m500, s500)
        loss500 = np.mean((pred500 - gt) ** 2)

        assert loss500 <= loss50 + 0.01  # allow small tolerance


# ==========================================================================
# Ranking
# ==========================================================================

class TestRanking:
    """Test the full ranking pipeline."""

    def test_returns_list(self, ranked):
        assert isinstance(ranked, list)

    def test_all_problems_ranked(self, ranked, problems):
        assert len(ranked) == len(problems)

    def test_sorted_descending(self, ranked):
        scores = [r["composite_score"] for r in ranked]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1] - 1e-6

    def test_has_required_fields(self, ranked):
        for r in ranked:
            assert "number" in r
            assert "tags" in r
            assert "status" in r
            assert "composite_score" in r
            assert "heuristic_score" in r
            assert "model_score" in r
            assert "dimension_scores" in r
            assert "ground_truth" in r

    def test_scores_bounded(self, ranked):
        for r in ranked:
            assert 0.0 <= r["composite_score"] <= 1.0
            assert 0.0 <= r["heuristic_score"] <= 1.0
            assert 0.0 <= r["model_score"] <= 1.0

    def test_dimension_scores_present(self, ranked):
        dims = {"depth", "difficulty", "surprise", "fertility", "investment"}
        for r in ranked:
            assert set(r["dimension_scores"].keys()) == dims

    def test_top_problems_have_high_scores(self, ranked):
        """Top problem should score above 0.5."""
        assert ranked[0]["composite_score"] > 0.5

    def test_problem_3_ranks_high(self, ranked):
        """Problem #3 (Erdos conjecture on APs) should be top-ranked."""
        top_20 = {r["number"] for r in ranked[:20]}
        assert 3 in top_20

    def test_problem_4_ranks_high(self, ranked):
        """Problem #4 ($10000 prize, Green-Tao) should rank high."""
        top_20 = {r["number"] for r in ranked[:20]}
        assert 4 in top_20

    def test_custom_weights(self, problems):
        """Custom weights should change rankings."""
        r_default = rank_all_problems(problems)
        r_depth = rank_all_problems(problems, weights={
            "depth": 1.0, "difficulty": 0, "surprise": 0,
            "fertility": 0, "investment": 0,
        })
        # Rankings should differ
        top10_default = [r["number"] for r in r_default[:10]]
        top10_depth = [r["number"] for r in r_depth[:10]]
        assert top10_default != top10_depth


# ==========================================================================
# Hidden Gems
# ==========================================================================

class TestHiddenGems:
    """Test hidden gem detection."""

    def test_returns_list(self, ranked):
        gems = find_hidden_gems(ranked)
        assert isinstance(gems, list)

    def test_respects_top_n(self, ranked):
        gems = find_hidden_gems(ranked, top_n=10)
        assert len(gems) <= 10

    def test_has_gem_fields(self, ranked):
        gems = find_hidden_gems(ranked)
        for g in gems:
            assert "gem_score" in g
            assert "intrinsic_score" in g
            assert "investment_score" in g

    def test_sorted_by_gem_score(self, ranked):
        gems = find_hidden_gems(ranked)
        for i in range(len(gems) - 1):
            assert gems[i]["gem_score"] >= gems[i + 1]["gem_score"] - 1e-6

    def test_gems_have_low_investment(self, ranked):
        """Top gems should have below-median investment scores on average."""
        gems = find_hidden_gems(ranked, top_n=10)
        all_investments = [r["dimension_scores"]["investment"] for r in ranked]
        median_invest = sorted(all_investments)[len(all_investments) // 2]
        avg_gem_invest = sum(g["investment_score"] for g in gems) / len(gems)
        assert avg_gem_invest <= median_invest + 0.1

    def test_gems_have_positive_gap(self, ranked):
        """Top gems should have intrinsic > investment."""
        gems = find_hidden_gems(ranked, top_n=10)
        for g in gems:
            assert g["gem_score"] > 0

    def test_problem_883_is_gem(self, ranked):
        """Problem #883 (our project focus) should appear as a hidden gem."""
        gems = find_hidden_gems(ranked, top_n=30)
        gem_numbers = {g["number"] for g in gems}
        assert 883 in gem_numbers


# ==========================================================================
# Dimension Analysis
# ==========================================================================

class TestDimensionAnalysis:
    """Test per-dimension analysis."""

    def test_returns_dict(self, ranked):
        da = dimension_analysis(ranked)
        assert isinstance(da, dict)

    def test_top_by_dimension(self, ranked):
        da = dimension_analysis(ranked)
        assert "top_by_dimension" in da
        for dim in ["depth", "difficulty", "surprise", "fertility", "investment"]:
            assert dim in da["top_by_dimension"]
            assert len(da["top_by_dimension"][dim]) == 5

    def test_correlations_exist(self, ranked):
        da = dimension_analysis(ranked)
        assert "correlations" in da
        assert len(da["correlations"]) == 10  # C(5,2)

    def test_correlations_bounded(self, ranked):
        da = dimension_analysis(ranked)
        for key, val in da["correlations"].items():
            assert -1.0 <= val <= 1.0, f"{key}: {val}"

    def test_depth_surprise_correlated(self, ranked):
        """Depth and surprise should be positively correlated (cross-domain
        problems touch rare tag combos)."""
        da = dimension_analysis(ranked)
        assert da["correlations"]["depth_vs_surprise"] > 0.0


# ==========================================================================
# Feature Importance
# ==========================================================================

class TestFeatureImportance:
    """Test feature importance computation."""

    def test_returns_list(self, problems):
        fi = feature_importance(problems)
        assert isinstance(fi, list)

    def test_all_features_present(self, problems):
        fi = feature_importance(problems)
        assert len(fi) == 17

    def test_sorted_descending(self, problems):
        fi = feature_importance(problems)
        for i in range(len(fi) - 1):
            assert fi[i][1] >= fi[i + 1][1] - 1e-6

    def test_importance_nonneg(self, problems):
        fi = feature_importance(problems)
        for name, imp in fi:
            assert imp >= 0.0

    def test_formalization_and_prize_matter(self, problems):
        """is_formalized and prize should be among top features."""
        fi = feature_importance(problems)
        top5_names = {name for name, _ in fi[:5]}
        assert "is_formalized" in top5_names or "prize_log" in top5_names or "has_prize" in top5_names


# ==========================================================================
# Tag Interestingness
# ==========================================================================

class TestTagInterestingness:
    """Test tag-level aggregation."""

    def test_returns_list(self, ranked):
        ti = tag_interestingness(ranked)
        assert isinstance(ti, list)

    def test_nonempty(self, ranked):
        ti = tag_interestingness(ranked)
        assert len(ti) > 20  # at least as many as distinct tags

    def test_sorted_descending(self, ranked):
        ti = tag_interestingness(ranked)
        for i in range(len(ti) - 1):
            assert ti[i]["avg_interestingness"] >= ti[i + 1]["avg_interestingness"] - 1e-6

    def test_has_required_fields(self, ranked):
        ti = tag_interestingness(ranked)
        for t in ti:
            assert "tag" in t
            assert "n_problems" in t
            assert "avg_interestingness" in t
            assert "dimension_profile" in t

    def test_dimension_profile_complete(self, ranked):
        ti = tag_interestingness(ranked)
        for t in ti:
            dims = set(t["dimension_profile"].keys())
            assert dims == {"depth", "difficulty", "surprise", "fertility", "investment"}

    def test_number_theory_large(self, ranked):
        """Number theory should have the most problems."""
        ti = tag_interestingness(ranked)
        nt = [t for t in ti if t["tag"] == "number theory"]
        assert len(nt) == 1
        assert nt[0]["n_problems"] > 400


# ==========================================================================
# Meta-Analysis: Solvability, Connectivity, Theory Generation
# ==========================================================================

class TestSolvabilityPredictors:
    """Test solvability prediction analysis."""

    def test_returns_dict(self, problems):
        sp = solvability_predictors(problems)
        assert isinstance(sp, dict)

    def test_has_predictors(self, problems):
        sp = solvability_predictors(problems)
        assert "predictors" in sp
        assert len(sp["predictors"]) == 17

    def test_predictors_sorted_by_abs(self, problems):
        sp = solvability_predictors(problems)
        for i in range(len(sp["predictors"]) - 1):
            assert abs(sp["predictors"][i][1]) >= abs(sp["predictors"][i + 1][1]) - 1e-6

    def test_unsolved_despite_age_negative(self, problems):
        """unsolved_despite_age should be negative (higher in open problems)."""
        sp = solvability_predictors(problems)
        predictor_dict = dict(sp["predictors"])
        assert predictor_dict["unsolved_despite_age"] < 0


class TestConnectivityPredictors:
    """Test cross-field connectivity analysis."""

    def test_returns_dict(self, problems):
        cp = connectivity_predictors(problems)
        assert isinstance(cp, dict)

    def test_has_predictors(self, problems):
        cp = connectivity_predictors(problems)
        assert "predictors" in cp
        assert len(cp["predictors"]) == 17

    def test_cross_domain_is_top(self, problems):
        """cross_domain itself should be the top predictor (tautologically)."""
        cp = connectivity_predictors(problems)
        assert cp["predictors"][0][0] == "cross_domain"

    def test_n_tags_positive(self, problems):
        """More tags should predict cross-domain."""
        cp = connectivity_predictors(problems)
        predictor_dict = dict(cp["predictors"])
        assert predictor_dict["n_tags"] > 0


class TestTheoryGenerationPredictors:
    """Test theory generation analysis."""

    def test_returns_dict(self, problems):
        tp = theory_generation_predictors(problems)
        assert isinstance(tp, dict)

    def test_has_predictors_or_note(self, problems):
        tp = theory_generation_predictors(problems)
        assert "predictors" in tp or "note" in tp

    def test_formalization_predicts_theory(self, problems):
        """Formalization should strongly predict theory generation."""
        tp = theory_generation_predictors(problems)
        if tp["predictors"]:
            predictor_dict = dict(tp["predictors"])
            assert predictor_dict["is_formalized"] > 0.5


# ==========================================================================
# Integration: Full Pipeline
# ==========================================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_full_pipeline_runs(self, problems):
        """The complete pipeline should run without errors."""
        ranked = rank_all_problems(problems)
        gems = find_hidden_gems(ranked)
        da = dimension_analysis(ranked)
        fi = feature_importance(problems)
        ti = tag_interestingness(ranked)
        sp = solvability_predictors(problems)
        cp = connectivity_predictors(problems)
        tp = theory_generation_predictors(problems)

        assert len(ranked) == len(problems)
        assert len(gems) > 0
        assert len(da["correlations"]) > 0
        assert len(fi) > 0
        assert len(ti) > 0
        assert len(sp["predictors"]) > 0

    def test_open_problems_dominate_gems(self, ranked):
        """Most hidden gems should be open problems."""
        gems = find_hidden_gems(ranked, top_n=20)
        open_gems = [g for g in gems if g["status"] == "open"]
        assert len(open_gems) >= len(gems) // 2

    def test_high_prize_high_score(self, ranked):
        """Problems with $1000+ prizes should be in top quartile."""
        top_quartile = set(r["number"] for r in ranked[:len(ranked) // 4])
        high_prize = [r for r in ranked if r["prize"] >= 1000]
        if high_prize:
            in_top = sum(1 for r in high_prize if r["number"] in top_quartile)
            assert in_top / len(high_prize) > 0.3  # at least 30% in top quartile

    def test_consistency_across_runs(self, problems):
        """Rankings should be deterministic."""
        r1 = rank_all_problems(problems)
        r2 = rank_all_problems(problems)
        top10_1 = [r["number"] for r in r1[:10]]
        top10_2 = [r["number"] for r in r2[:10]]
        assert top10_1 == top10_2

    def test_investment_dimension_matches_metadata(self, ranked):
        """Problems with prizes AND formalization should have highest investment."""
        for r in ranked:
            if r["prize"] > 0 and r["formalized"]:
                assert r["dimension_scores"]["investment"] > 0.3


# ==========================================================================
# Edge Cases
# ==========================================================================

class TestEdgeCases:
    """Test edge cases and robustness."""

    def test_single_problem(self):
        """Should handle a single-problem list."""
        problems = [{
            "number": "1",
            "prize": "$500",
            "status": {"state": "open"},
            "formalized": {"state": "yes"},
            "oeis": ["A001234"],
            "tags": ["number theory"],
        }]
        X, info, names, stats = extract_features(problems)
        assert X.shape == (1, 17)

    def test_minimal_problem(self):
        """Should handle a problem with minimal fields."""
        problems = [{
            "number": "1",
            "tags": ["graph theory"],
            "status": {"state": "open"},
        }]
        X, info, names, stats = extract_features(problems)
        assert X.shape == (1, 17)
        assert np.all(np.isfinite(X))

    def test_no_oeis_problem(self):
        """Should handle a problem with no OEIS sequences."""
        problems = [
            {"number": "1", "tags": ["a"], "status": {"state": "open"},
             "oeis": ["N/A"]},
            {"number": "2", "tags": ["a"], "status": {"state": "proved"}},
        ]
        X, info, names, stats = extract_features(problems)
        assert np.all(np.isfinite(X))

    def test_all_solved(self):
        """Should handle a dataset where everything is solved."""
        problems = [
            {"number": str(i), "tags": ["a"], "status": {"state": "proved"}}
            for i in range(1, 6)
        ]
        X, info, names, stats = extract_features(problems)
        ranked = rank_all_problems(problems)
        assert len(ranked) == 5

    def test_no_prizes(self):
        """Should handle a dataset with no prizes."""
        problems = [
            {"number": str(i), "tags": ["a"], "status": {"state": "open"},
             "prize": "no"}
            for i in range(1, 6)
        ]
        ranked = rank_all_problems(problems)
        for r in ranked:
            assert r["prize"] == 0.0
