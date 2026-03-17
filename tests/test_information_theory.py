"""Tests for information_theory.py — information-theoretic analysis."""
import math
import pytest

from information_theory import (
    load_problems,
    entropy,
    conditional_entropy,
    mutual_information,
    normalized_mutual_information,
    information_gain,
    kl_divergence,
    feature_mutual_information,
    tag_mutual_information,
    surprise_scores,
    redundancy_analysis,
    channel_capacity,
    optimal_split_tree,
    status_entropy_by_tag,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


class TestEntropy:
    """Test Shannon entropy computation."""

    def test_empty(self):
        assert entropy([]) == 0.0

    def test_single(self):
        assert entropy(["a"]) == 0.0

    def test_uniform_binary(self):
        # H(50/50) = 1 bit
        assert abs(entropy(["a", "b"] * 50) - 1.0) < 0.01

    def test_uniform_quad(self):
        # H(25/25/25/25) = 2 bits
        assert abs(entropy(["a", "b", "c", "d"] * 25) - 2.0) < 0.01

    def test_concentrated(self):
        # H(99/1) ≈ 0.08 bits
        labels = ["a"] * 99 + ["b"]
        assert entropy(labels) < 0.1

    def test_nonneg(self):
        assert entropy(["a", "a", "b", "c"]) >= 0


class TestConditionalEntropy:
    """Test conditional entropy H(Y|X)."""

    def test_identical(self):
        # H(Y|Y) = 0
        labels = ["a", "b", "a", "b"]
        assert conditional_entropy(labels, labels) == 0.0

    def test_independent(self):
        # H(Y|X) ≈ H(Y) when X is independent
        y = ["a", "b"] * 50
        x = list(range(100))  # all unique
        h = conditional_entropy(y, x)
        assert h == 0.0  # every condition has 1 element → H=0

    def test_bounded(self):
        labels = ["a", "b", "a", "a"]
        conds = [1, 1, 2, 2]
        h = conditional_entropy(labels, conds)
        assert 0 <= h <= entropy(labels)


class TestMutualInformation:
    """Test mutual information I(X;Y)."""

    def test_self_mi(self):
        # I(X;X) = H(X)
        x = ["a", "b", "a", "b", "c"]
        mi = mutual_information(x, x)
        h = entropy(x)
        assert abs(mi - h) < 0.01

    def test_independent(self):
        # I(X;Y) ≈ 0 for independent variables (with enough data)
        import random
        random.seed(42)
        x = [random.choice(["a", "b"]) for _ in range(1000)]
        y = [random.choice(["c", "d"]) for _ in range(1000)]
        mi = mutual_information(x, y)
        assert mi < 0.05  # should be near zero

    def test_nonneg(self):
        x = ["a", "b", "a", "b"]
        y = ["c", "c", "d", "d"]
        assert mutual_information(x, y) >= 0


class TestNMI:
    """Test normalized mutual information."""

    def test_self_nmi(self):
        x = ["a", "b", "c", "d"]
        nmi = normalized_mutual_information(x, x)
        assert abs(nmi - 1.0) < 0.01

    def test_bounded(self):
        x = ["a", "b", "a"]
        y = ["c", "d", "c"]
        nmi = normalized_mutual_information(x, y)
        assert 0.0 <= nmi <= 1.01


class TestKLDivergence:
    """Test KL divergence."""

    def test_identical(self):
        p = {"a": 0.5, "b": 0.5}
        assert kl_divergence(p, p) == 0.0

    def test_nonneg(self):
        p = {"a": 0.7, "b": 0.3}
        q = {"a": 0.5, "b": 0.5}
        assert kl_divergence(p, q) >= 0

    def test_asymmetric(self):
        p = {"a": 0.9, "b": 0.1}
        q = {"a": 0.5, "b": 0.5}
        assert kl_divergence(p, q) != kl_divergence(q, p)


class TestFeatureMI:
    """Test feature mutual information computation."""

    def test_returns_dict(self, problems):
        result = feature_mutual_information(problems)
        assert isinstance(result, dict)

    def test_has_features(self, problems):
        result = feature_mutual_information(problems)
        assert len(result["features"]) > 0

    def test_base_entropy(self, problems):
        result = feature_mutual_information(problems)
        assert 0 < result["base_entropy"] <= 1.0

    def test_mi_nonneg(self, problems):
        result = feature_mutual_information(problems)
        for f in result["features"]:
            assert f["mutual_information"] >= 0

    def test_formalized_most_informative(self, problems):
        result = feature_mutual_information(problems)
        assert result["features"][0]["feature"] == "formalized"

    def test_entropy_reduction_bounded(self, problems):
        result = feature_mutual_information(problems)
        for f in result["features"]:
            assert 0 <= f["entropy_reduction"] <= 1


class TestTagMI:
    """Test tag-tag mutual information."""

    def test_returns_dict(self, problems):
        result = tag_mutual_information(problems)
        assert isinstance(result, dict)

    def test_has_pairs(self, problems):
        result = tag_mutual_information(problems)
        assert len(result["tag_pairs"]) > 0

    def test_mi_positive(self, problems):
        result = tag_mutual_information(problems)
        for pair in result["tag_pairs"]:
            assert pair["mutual_information"] > 0

    def test_graph_nt_top(self, problems):
        result = tag_mutual_information(problems)
        top = result["tag_pairs"][0]
        assert "graph theory" in (top["tag_a"], top["tag_b"])
        assert "number theory" in (top["tag_a"], top["tag_b"])


class TestSurpriseScores:
    """Test surprise scoring."""

    def test_returns_list(self, problems):
        result = surprise_scores(problems)
        assert isinstance(result, list)

    def test_covers_all(self, problems):
        result = surprise_scores(problems)
        assert len(result) == len(problems)

    def test_surprise_nonneg(self, problems):
        result = surprise_scores(problems)
        for s in result:
            assert s["surprise"] >= 0

    def test_sorted_by_surprise(self, problems):
        result = surprise_scores(problems)
        for i in range(len(result) - 1):
            assert result[i]["surprise"] >= result[i + 1]["surprise"]

    def test_direction_categories(self, problems):
        result = surprise_scores(problems)
        directions = set(s["direction"] for s in result)
        assert "expected" in directions


class TestRedundancy:
    """Test redundancy analysis."""

    def test_returns_dict(self, problems):
        result = redundancy_analysis(problems)
        assert isinstance(result, dict)

    def test_has_redundant(self, problems):
        result = redundancy_analysis(problems)
        assert len(result["redundant_pairs"]) > 0

    def test_has_complementary(self, problems):
        result = redundancy_analysis(problems)
        assert len(result["complementary_pairs"]) > 0


class TestChannelCapacity:
    """Test channel capacity analysis."""

    def test_returns_dict(self, problems):
        result = channel_capacity(problems)
        assert isinstance(result, dict)

    def test_has_channels(self, problems):
        result = channel_capacity(problems)
        assert len(result["tag_channels"]) > 0

    def test_mi_nonneg(self, problems):
        result = channel_capacity(problems)
        for tc in result["tag_channels"]:
            assert tc["channel_mi"] >= 0

    def test_capacity_ratio_bounded(self, problems):
        result = channel_capacity(problems)
        for tc in result["tag_channels"]:
            assert 0 <= tc["capacity_ratio"] <= 1.01


class TestClassificationTree:
    """Test optimal classification tree."""

    def test_returns_dict(self, problems):
        result = optimal_split_tree(problems)
        assert isinstance(result, dict)
        assert "tree" in result

    def test_tree_has_root(self, problems):
        result = optimal_split_tree(problems)
        assert result["tree"]["type"] in ("split", "leaf")

    def test_root_is_formalized(self, problems):
        result = optimal_split_tree(problems)
        assert result["tree"]["feature"] == "formalized"

    def test_max_depth_respected(self, problems):
        result = optimal_split_tree(problems, max_depth=2)

        def max_depth(node):
            if node["type"] == "leaf":
                return 0
            return 1 + max(max_depth(node["yes"]), max_depth(node["no"]))

        assert max_depth(result["tree"]) <= 2


class TestStatusEntropy:
    """Test status entropy by tag."""

    def test_returns_list(self, problems):
        result = status_entropy_by_tag(problems)
        assert isinstance(result, list)

    def test_sorted_by_entropy(self, problems):
        result = status_entropy_by_tag(problems)
        for i in range(len(result) - 1):
            assert result[i]["status_entropy"] <= result[i + 1]["status_entropy"]

    def test_entropy_nonneg(self, problems):
        result = status_entropy_by_tag(problems)
        for se in result:
            assert se["status_entropy"] >= 0

    def test_base_representations_zero_entropy(self, problems):
        result = status_entropy_by_tag(problems)
        br = next((s for s in result if s["tag"] == "base representations"), None)
        if br:
            assert br["status_entropy"] < 0.01  # all open
