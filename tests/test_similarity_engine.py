"""Tests for similarity_engine.py — problem similarity and clustering."""
import numpy as np
import pytest

from similarity_engine import (
    load_problems,
    compute_feature_vectors,
    compute_similarity_matrix,
    hidden_twins,
    problem_families,
    isolation_index,
    transfer_candidates,
    structural_isomorphism,
    tag_embedding,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def features(problems):
    return compute_feature_vectors(problems)


class TestFeatureVectors:
    """Test problem feature vector computation."""

    def test_shape(self, features):
        X, numbers, names = features
        assert X.shape[0] == len(numbers)
        assert X.shape[1] == len(names)

    def test_numbers_populated(self, features):
        X, numbers, names = features
        assert len(numbers) > 1000

    def test_features_nonneg(self, features):
        X, _, _ = features
        assert np.all(X >= 0)

    def test_feature_names(self, features):
        _, _, names = features
        assert any("tag_" in n for n in names)
        assert "oeis_count" in names
        assert "formalized" in names

    def test_tag_features_binary(self, features):
        X, _, names = features
        tag_cols = [i for i, n in enumerate(names) if n.startswith("tag_")]
        for col in tag_cols[:10]:
            assert set(np.unique(X[:, col])).issubset({0.0, 1.0})


class TestSimilarityMatrix:
    """Test cosine similarity computation."""

    def test_shape(self, features):
        X, _, _ = features
        # Use subset for speed
        sim = compute_similarity_matrix(X[:50])
        assert sim.shape == (50, 50)

    def test_symmetric(self, features):
        X, _, _ = features
        sim = compute_similarity_matrix(X[:50])
        assert np.allclose(sim, sim.T)

    def test_bounded(self, features):
        X, _, _ = features
        sim = compute_similarity_matrix(X[:50])
        assert np.all(sim >= -1.01)
        assert np.all(sim <= 1.01)

    def test_zero_diagonal(self, features):
        X, _, _ = features
        sim = compute_similarity_matrix(X[:50])
        assert np.allclose(np.diag(sim), 0.0)


class TestHiddenTwins:
    """Test hidden twin discovery."""

    def test_returns_list(self, problems, features):
        X, numbers, _ = features
        twins = hidden_twins(problems, X, numbers, top_k=10)
        assert isinstance(twins, list)

    def test_twin_fields(self, problems, features):
        X, numbers, _ = features
        twins = hidden_twins(problems, X, numbers, top_k=10)
        for t in twins:
            assert "problem_a" in t
            assert "problem_b" in t
            assert "cosine_similarity" in t
            assert "tag_overlap" in t
            assert "surprise_score" in t

    def test_low_tag_overlap(self, problems, features):
        X, numbers, _ = features
        twins = hidden_twins(problems, X, numbers, top_k=10)
        for t in twins:
            assert t["tag_overlap"] < 0.5

    def test_sorted_by_surprise(self, problems, features):
        X, numbers, _ = features
        twins = hidden_twins(problems, X, numbers, top_k=10)
        for i in range(len(twins) - 1):
            assert twins[i]["surprise_score"] >= twins[i + 1]["surprise_score"]


class TestProblemFamilies:
    """Test k-means clustering."""

    def test_returns_list(self, problems, features):
        X, numbers, _ = features
        fams = problem_families(problems, X, numbers, n_families=5)
        assert isinstance(fams, list)

    def test_family_count(self, problems, features):
        X, numbers, _ = features
        fams = problem_families(problems, X, numbers, n_families=5)
        assert len(fams) <= 5

    def test_family_fields(self, problems, features):
        X, numbers, _ = features
        fams = problem_families(problems, X, numbers, n_families=5)
        for f in fams:
            assert "family_id" in f
            assert "size" in f
            assert "solve_rate" in f
            assert "top_tags" in f

    def test_families_cover_all(self, problems, features):
        X, numbers, _ = features
        fams = problem_families(problems, X, numbers, n_families=5)
        total = sum(f["size"] for f in fams)
        assert total == len(problems)

    def test_solve_rate_bounded(self, problems, features):
        X, numbers, _ = features
        fams = problem_families(problems, X, numbers, n_families=5)
        for f in fams:
            assert 0.0 <= f["solve_rate"] <= 1.0


class TestIsolationIndex:
    """Test isolation scoring."""

    def test_returns_list(self, problems, features):
        X, numbers, _ = features
        iso = isolation_index(problems, X, numbers)
        assert isinstance(iso, list)

    def test_covers_all(self, problems, features):
        X, numbers, _ = features
        iso = isolation_index(problems, X, numbers)
        assert len(iso) == len(problems)

    def test_sorted_by_isolation(self, problems, features):
        X, numbers, _ = features
        iso = isolation_index(problems, X, numbers)
        for i in range(len(iso) - 1):
            assert iso[i]["isolation"] >= iso[i + 1]["isolation"]

    def test_isolation_bounded(self, problems, features):
        X, numbers, _ = features
        iso = isolation_index(problems, X, numbers)
        for item in iso:
            assert 0.0 <= item["isolation"] <= 1.0


class TestTransferCandidates:
    """Test solved→open transfer candidate finding."""

    def test_returns_list(self, problems, features):
        X, numbers, _ = features
        transfers = transfer_candidates(problems, X, numbers, top_k=10)
        assert isinstance(transfers, list)

    def test_transfer_fields(self, problems, features):
        X, numbers, _ = features
        transfers = transfer_candidates(problems, X, numbers, top_k=10)
        for t in transfers:
            assert "solved_problem" in t
            assert "open_problem" in t
            assert "similarity" in t

    def test_sorted_by_similarity(self, problems, features):
        X, numbers, _ = features
        transfers = transfer_candidates(problems, X, numbers, top_k=10)
        for i in range(len(transfers) - 1):
            assert transfers[i]["similarity"] >= transfers[i + 1]["similarity"]

    def test_respects_top_k(self, problems, features):
        X, numbers, _ = features
        transfers = transfer_candidates(problems, X, numbers, top_k=5)
        assert len(transfers) <= 5


class TestStructuralIsomorphism:
    """Test structural isomorphism detection."""

    def test_returns_list(self, problems, features):
        X, numbers, _ = features
        iso = structural_isomorphism(problems, X, numbers)
        assert isinstance(iso, list)

    def test_classes_have_multiple(self, problems, features):
        X, numbers, _ = features
        iso = structural_isomorphism(problems, X, numbers)
        for ic in iso:
            assert ic["size"] >= 2

    def test_sorted_by_size(self, problems, features):
        X, numbers, _ = features
        iso = structural_isomorphism(problems, X, numbers)
        for i in range(len(iso) - 1):
            assert iso[i]["size"] >= iso[i + 1]["size"]


class TestTagEmbedding:
    """Test SVD-based tag embedding."""

    def test_returns_dict(self, problems):
        result = tag_embedding(problems)
        assert isinstance(result, dict)

    def test_has_closest(self, problems):
        result = tag_embedding(problems)
        assert len(result["closest_pairs"]) > 0

    def test_distance_nonneg(self, problems):
        result = tag_embedding(problems)
        for t1, t2, d in result["closest_pairs"]:
            assert d >= 0

    def test_variance_explained(self, problems):
        result = tag_embedding(problems)
        assert len(result["variance_explained"]) > 0
        assert sum(result["variance_explained"]) <= 1.01
