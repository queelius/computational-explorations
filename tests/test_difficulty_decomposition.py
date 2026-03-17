"""Tests for difficulty_decomposition.py — PCA factor analysis of problem difficulty."""
import math
import pytest

from difficulty_decomposition import (
    load_problems,
    build_difficulty_features,
    pca_decomposition,
    name_components,
    dimension_solvability,
    difficulty_outliers,
    difficulty_clusters,
    tag_difficulty_profiles,
    difficulty_spectrum,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


class TestBuildFeatures:
    """Test difficulty feature extraction."""

    def test_returns_tuple(self, problems):
        X, nums, names = build_difficulty_features(problems)
        assert len(X.shape) == 2
        assert len(nums) == X.shape[0]
        assert len(names) == X.shape[1]

    def test_problem_count(self, problems):
        X, nums, _ = build_difficulty_features(problems)
        assert X.shape[0] == len(problems)

    def test_has_tag_features(self, problems):
        _, _, names = build_difficulty_features(problems)
        tag_features = [n for n in names if n.startswith("tag:")]
        assert len(tag_features) > 20

    def test_has_meta_features(self, problems):
        _, _, names = build_difficulty_features(problems)
        assert "avg_tag_solve_rate" in names
        assert "prize_log" in names
        assert "formalized" in names
        assert "isolation_proxy" in names

    def test_values_bounded(self, problems):
        X, _, _ = build_difficulty_features(problems)
        # All values should be in reasonable range (most normalized to [0,1])
        assert X.min() >= -0.01
        assert X.max() <= 2.0  # some features like solve rates can go to 1.0

    def test_tag_features_binary(self, problems):
        X, _, names = build_difficulty_features(problems)
        for j, name in enumerate(names):
            if name.startswith("tag:"):
                vals = set(X[:, j].tolist())
                assert vals.issubset({0.0, 1.0})

    def test_formalized_binary(self, problems):
        X, _, names = build_difficulty_features(problems)
        idx = names.index("formalized")
        vals = set(X[:, idx].tolist())
        assert vals.issubset({0.0, 1.0})


class TestPCA:
    """Test PCA decomposition."""

    def test_returns_dict(self, problems):
        result = pca_decomposition(problems)
        assert isinstance(result, dict)

    def test_has_required_keys(self, problems):
        result = pca_decomposition(problems)
        for key in ("components", "explained_variance", "cumulative_variance",
                     "loadings", "scores", "problem_numbers", "feature_names"):
            assert key in result

    def test_explained_variance_sums_leq_1(self, problems):
        result = pca_decomposition(problems)
        total = sum(result["explained_variance"])
        assert total <= 1.01

    def test_explained_variance_descending(self, problems):
        result = pca_decomposition(problems)
        evs = result["explained_variance"]
        for i in range(len(evs) - 1):
            assert evs[i] >= evs[i + 1] - 1e-6

    def test_cumulative_nondecreasing(self, problems):
        result = pca_decomposition(problems)
        cum = result["cumulative_variance"]
        for i in range(len(cum) - 1):
            assert cum[i + 1] >= cum[i] - 1e-6

    def test_n_components_default(self, problems):
        result = pca_decomposition(problems)
        assert result["n_components"] == 10

    def test_custom_n_components(self, problems):
        result = pca_decomposition(problems, n_components=3)
        assert result["n_components"] == 3
        assert len(result["explained_variance"]) == 3

    def test_scores_shape(self, problems):
        result = pca_decomposition(problems)
        assert result["scores"].shape == (len(problems), result["n_components"])

    def test_loadings_structure(self, problems):
        result = pca_decomposition(problems)
        assert len(result["loadings"]) == result["n_components"]
        for comp_loadings in result["loadings"]:
            assert len(comp_loadings) == len(result["feature_names"])

    def test_first_component_largest(self, problems):
        result = pca_decomposition(problems)
        assert result["explained_variance"][0] >= 0.05  # at least 5%


class TestNameComponents:
    """Test component naming."""

    def test_returns_list(self, problems):
        pca = pca_decomposition(problems)
        named = name_components(pca)
        assert isinstance(named, list)

    def test_names_are_strings(self, problems):
        pca = pca_decomposition(problems)
        named = name_components(pca)
        for comp in named:
            assert isinstance(comp["name"], str)
            assert len(comp["name"]) > 3

    def test_has_required_fields(self, problems):
        pca = pca_decomposition(problems)
        named = name_components(pca)
        for comp in named:
            assert "component" in comp
            assert "name" in comp
            assert "explained_variance" in comp
            assert "top_positive" in comp
            assert "top_negative" in comp

    def test_component_indices_sequential(self, problems):
        pca = pca_decomposition(problems)
        named = name_components(pca)
        for i, comp in enumerate(named):
            assert comp["component"] == i


class TestDimensionSolvability:
    """Test dimension-solvability correlation."""

    def test_returns_list(self, problems):
        pca = pca_decomposition(problems)
        result = dimension_solvability(problems, pca)
        assert isinstance(result, list)

    def test_has_all_components(self, problems):
        pca = pca_decomposition(problems)
        result = dimension_solvability(problems, pca)
        assert len(result) == pca["n_components"]

    def test_correlation_bounded(self, problems):
        pca = pca_decomposition(problems)
        result = dimension_solvability(problems, pca)
        for d in result:
            assert -1.01 <= d["correlation"] <= 1.01

    def test_separation_nonneg(self, problems):
        pca = pca_decomposition(problems)
        result = dimension_solvability(problems, pca)
        for d in result:
            assert d["separation"] >= 0

    def test_sorted_by_abs_correlation(self, problems):
        pca = pca_decomposition(problems)
        result = dimension_solvability(problems, pca)
        for i in range(len(result) - 1):
            assert abs(result[i]["correlation"]) >= abs(result[i + 1]["correlation"]) - 1e-6

    def test_some_significant_correlation(self, problems):
        pca = pca_decomposition(problems)
        result = dimension_solvability(problems, pca)
        max_corr = max(abs(d["correlation"]) for d in result)
        assert max_corr > 0.05  # at least one dimension predicts solvability


class TestDifficultyOutliers:
    """Test difficulty outlier detection."""

    def test_returns_list(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_outliers(problems, pca)
        assert isinstance(result, list)

    def test_has_outliers(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_outliers(problems, pca)
        assert len(result) > 0

    def test_outlier_fields(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_outliers(problems, pca)
        for o in result:
            assert "number" in o
            assert "component" in o
            assert "score" in o
            assert "direction" in o
            assert "status" in o

    def test_directions(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_outliers(problems, pca)
        directions = set(o["direction"] for o in result)
        assert "high" in directions
        assert "low" in directions

    def test_z_scores_extreme(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_outliers(problems, pca)
        for o in result:
            assert abs(o["score"]) > 0.5  # outliers should have notable z-scores


class TestDifficultyClusters:
    """Test difficulty clustering."""

    def test_returns_dict(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_clusters(problems, pca)
        assert isinstance(result, dict)

    def test_has_clusters(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_clusters(problems, pca)
        assert result["n_clusters"] > 0

    def test_cluster_fields(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_clusters(problems, pca)
        for cl in result["clusters"]:
            assert "size" in cl
            assert "solve_rate" in cl
            assert "top_tags" in cl

    def test_solve_rate_bounded(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_clusters(problems, pca)
        for cl in result["clusters"]:
            assert 0.0 <= cl["solve_rate"] <= 1.0

    def test_total_size(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_clusters(problems, pca)
        total = sum(cl["size"] for cl in result["clusters"])
        assert total == len(problems)

    def test_silhouette_bounded(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_clusters(problems, pca)
        assert -1.0 <= result["silhouette"] <= 1.0

    def test_sorted_by_solve_rate(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_clusters(problems, pca)
        rates = [cl["solve_rate"] for cl in result["clusters"]]
        for i in range(len(rates) - 1):
            assert rates[i] <= rates[i + 1] + 1e-6


class TestTagDifficultyProfiles:
    """Test tag difficulty profiling."""

    def test_returns_list(self, problems):
        pca = pca_decomposition(problems)
        result = tag_difficulty_profiles(problems, pca)
        assert isinstance(result, list)

    def test_has_tags(self, problems):
        pca = pca_decomposition(problems)
        result = tag_difficulty_profiles(problems, pca)
        assert len(result) > 10

    def test_profile_length(self, problems):
        pca = pca_decomposition(problems)
        result = tag_difficulty_profiles(problems, pca)
        for tp in result:
            assert len(tp["profile"]) == min(pca["n_components"], 5)

    def test_solve_rate_bounded(self, problems):
        pca = pca_decomposition(problems)
        result = tag_difficulty_profiles(problems, pca)
        for tp in result:
            assert 0.0 <= tp["solve_rate"] <= 1.0

    def test_sorted_by_strength(self, problems):
        pca = pca_decomposition(problems)
        result = tag_difficulty_profiles(problems, pca)
        for i in range(len(result) - 1):
            assert result[i]["dominant_strength"] >= result[i + 1]["dominant_strength"] - 1e-6


class TestDifficultySpectrum:
    """Test per-problem difficulty scoring."""

    def test_returns_list(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_spectrum(problems, pca)
        assert isinstance(result, list)

    def test_only_open_problems(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_spectrum(problems, pca)
        open_count = sum(1 for p in problems if p.get("status", {}).get("state") == "open")
        assert len(result) == open_count

    def test_sorted_by_difficulty(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_spectrum(problems, pca)
        for i in range(len(result) - 1):
            assert result[i]["difficulty_score"] >= result[i + 1]["difficulty_score"] - 1e-6

    def test_has_required_fields(self, problems):
        pca = pca_decomposition(problems)
        result = difficulty_spectrum(problems, pca)
        for s in result:
            assert "number" in s
            assert "difficulty_score" in s
            assert "pc_scores" in s
            assert "tags" in s
