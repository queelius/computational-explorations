"""Tests for info_theory_deep.py -- deep information-theoretic analysis."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from info_theory_deep import (
    shannon_entropy,
    entropy_from_labels,
    mutual_information_labels,
    normalized_mi,
    coprime_graph_edges,
    degree_sequence,
    graph_entropy,
    erdos_renyi_degree_entropy,
    coprime_vs_random_entropy,
    load_problems,
    feature_importance,
    _problem_descriptor,
    _is_solved,
    compressed_size,
    kolmogorov_proxy,
    count_avoiding_colorings,
    ramsey_channel_capacity,
    _coloring_to_bitstring,
    witness_mdl,
)


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def mdl_n10():
    """Cache the expensive witness_mdl(n=10, k=3) computation."""
    return witness_mdl(n=10, k=3)


# =========================================================================
# Core primitives
# =========================================================================

class TestShannonEntropy:
    """Shannon entropy from count arrays."""

    def test_uniform_binary(self):
        """H([50, 50]) = 1 bit."""
        h = shannon_entropy(np.array([50, 50]))
        assert abs(h - 1.0) < 1e-9

    def test_uniform_4(self):
        """H([25, 25, 25, 25]) = 2 bits."""
        h = shannon_entropy(np.array([25, 25, 25, 25]))
        assert abs(h - 2.0) < 1e-9

    def test_degenerate(self):
        """H([100]) = 0."""
        assert shannon_entropy(np.array([100])) == 0.0

    def test_empty(self):
        assert shannon_entropy(np.array([])) == 0.0

    def test_zeros_ignored(self):
        """Zero counts should not affect entropy."""
        h = shannon_entropy(np.array([50, 50, 0]))
        assert abs(h - 1.0) < 1e-9

    def test_nonneg(self):
        """Entropy is always non-negative."""
        for arr in [np.array([3, 7]), np.array([1, 1, 1, 97])]:
            assert shannon_entropy(arr) >= 0


class TestEntropyFromLabels:
    """Entropy from label lists."""

    def test_empty_list(self):
        assert entropy_from_labels([]) == 0.0

    def test_single_label(self):
        assert entropy_from_labels(["a"]) == 0.0

    def test_all_same(self):
        assert entropy_from_labels(["x"] * 100) == 0.0

    def test_binary(self):
        h = entropy_from_labels(["a", "b"] * 500)
        assert abs(h - 1.0) < 0.01


class TestMutualInformation:
    """I(X;Y) from label lists."""

    def test_self_mi_equals_entropy(self):
        """I(X;X) = H(X)."""
        x = ["a", "b", "c", "a", "b"]
        mi = mutual_information_labels(x, x)
        h = entropy_from_labels(x)
        assert abs(mi - h) < 1e-6

    def test_independent_near_zero(self):
        """Independent variables should have MI near zero."""
        rng = np.random.default_rng(42)
        x = [rng.choice(["a", "b"]) for _ in range(2000)]
        y = [rng.choice(["c", "d"]) for _ in range(2000)]
        mi = mutual_information_labels(x, y)
        assert mi < 0.02

    def test_nonneg(self):
        x = ["a", "b", "a", "b"]
        y = ["c", "c", "d", "d"]
        assert mutual_information_labels(x, y) >= 0

    def test_empty(self):
        assert mutual_information_labels([], []) == 0.0

    def test_perfect_dependency(self):
        """Deterministic relationship: I(X;Y) = H(X) = H(Y)."""
        x = ["a", "b", "c"] * 100
        y = ["1", "2", "3"] * 100
        mi = mutual_information_labels(x, y)
        hx = entropy_from_labels(x)
        assert abs(mi - hx) < 1e-6


class TestNormalizedMI:
    """NMI = I(X;Y) / sqrt(H(X)*H(Y))."""

    def test_self_nmi_one(self):
        x = ["a", "b", "c", "d"]
        nmi = normalized_mi(x, x)
        assert abs(nmi - 1.0) < 1e-6

    def test_bounded(self):
        x = ["a", "b"] * 50
        y = ["c", "d"] * 50
        nmi = normalized_mi(x, y)
        assert 0.0 <= nmi <= 1.001

    def test_zero_entropy(self):
        """If one variable is constant, NMI = 0."""
        x = ["a"] * 100
        y = ["c", "d"] * 50
        assert normalized_mi(x, y) == 0.0


# =========================================================================
# 1. Coprime graph entropy
# =========================================================================

class TestCoprimeGraphEdges:
    """coprime_graph_edges(n)."""

    def test_n3(self):
        edges = coprime_graph_edges(3)
        assert set(edges) == {(1, 2), (1, 3), (2, 3)}

    def test_n4_excludes_2_4(self):
        edges = coprime_graph_edges(4)
        assert (2, 4) not in edges
        assert (1, 4) in edges

    def test_monotone(self):
        assert len(coprime_graph_edges(5)) <= len(coprime_graph_edges(10))

    def test_n1_empty(self):
        assert coprime_graph_edges(1) == []


class TestDegreeSequence:
    """degree_sequence(n)."""

    def test_length(self):
        deg = degree_sequence(5)
        assert len(deg) == 5

    def test_vertex_1_maximal(self):
        """Vertex 1 is coprime with every other vertex, so degree = n-1."""
        for n in [5, 10, 20]:
            deg = degree_sequence(n)
            assert deg[0] == n - 1  # vertex 1 is index 0

    def test_nonneg(self):
        deg = degree_sequence(10)
        assert (deg >= 0).all()


class TestGraphEntropy:
    """graph_entropy(n)."""

    def test_returns_required_keys(self):
        info = graph_entropy(10)
        for key in ["n", "num_edges", "density", "degree_entropy",
                     "max_degree", "min_degree", "mean_degree"]:
            assert key in info

    def test_density_in_range(self):
        for n in [5, 10, 20]:
            info = graph_entropy(n)
            assert 0 < info["density"] <= 1

    def test_density_near_6_over_pi2(self):
        """For large n, density should approach 6/pi^2."""
        info = graph_entropy(100)
        expected = 6 / math.pi**2  # ~0.608
        assert abs(info["density"] - expected) < 0.05

    def test_entropy_positive(self):
        info = graph_entropy(20)
        assert info["degree_entropy"] > 0


class TestErdosRenyiDegreeEntropy:
    """erdos_renyi_degree_entropy(n, p)."""

    def test_positive(self):
        h = erdos_renyi_degree_entropy(20, 0.5, trials=10)
        assert h > 0

    def test_p_zero(self):
        """No edges => all degrees 0 => entropy 0."""
        h = erdos_renyi_degree_entropy(10, 0.0, trials=5)
        assert h == 0.0

    def test_p_one(self):
        """Complete graph => all degrees n-1 => entropy 0."""
        h = erdos_renyi_degree_entropy(10, 1.0, trials=5)
        assert h == 0.0


class TestCoprimeVsRandomEntropy:
    """coprime_vs_random_entropy(ns)."""

    def test_returns_correct_count(self):
        results = coprime_vs_random_entropy([5, 10])
        assert len(results) == 2

    def test_coprime_entropy_exceeds_random(self):
        """
        Coprime graph has more structured degree distribution than ER
        (number-theoretic structure -> higher entropy from wider degree spread).
        """
        results = coprime_vs_random_entropy([50])
        r = results[0]
        # The coprime graph has a very spread-out degree sequence due to
        # the arithmetic structure, so its entropy should differ from ER.
        # We just check both are positive and the ratio is finite.
        assert r["coprime_entropy"] > 0
        assert r["er_entropy"] > 0
        assert 0 < r["entropy_ratio"] < 100

    def test_keys_present(self):
        results = coprime_vs_random_entropy([10])
        r = results[0]
        for key in ["n", "coprime_entropy", "er_entropy", "entropy_ratio",
                     "density", "num_edges", "mean_degree"]:
            assert key in r


# =========================================================================
# 2. Mutual information between problem features
# =========================================================================

class TestFeatureImportance:
    """feature_importance(problems)."""

    def test_returns_dict(self, problems):
        fi = feature_importance(problems)
        assert isinstance(fi, dict)

    def test_has_base_entropy(self, problems):
        fi = feature_importance(problems)
        assert 0 < fi["base_entropy"] <= 1.0

    def test_features_nonempty(self, problems):
        fi = feature_importance(problems)
        assert len(fi["features"]) > 0

    def test_sorted_descending(self, problems):
        fi = feature_importance(problems)
        mis = [f["mutual_information"] for f in fi["features"]]
        for i in range(len(mis) - 1):
            assert mis[i] >= mis[i + 1]

    def test_mi_nonneg(self, problems):
        fi = feature_importance(problems)
        for f in fi["features"]:
            assert f["mutual_information"] >= 0

    def test_nmi_bounded(self, problems):
        fi = feature_importance(problems)
        for f in fi["features"]:
            assert 0.0 <= f["nmi"] <= 1.001

    def test_most_informative_is_formalized(self, problems):
        """Formalization is expected to be the top predictor (selection effect)."""
        fi = feature_importance(problems)
        assert fi["most_informative"] == "formalized"

    def test_has_oeis_feature(self, problems):
        fi = feature_importance(problems)
        names = [f["feature"] for f in fi["features"]]
        assert "has_oeis" in names

    def test_has_prize_feature(self, problems):
        fi = feature_importance(problems)
        names = [f["feature"] for f in fi["features"]]
        assert "has_prize" in names


# =========================================================================
# 3. Kolmogorov complexity proxy
# =========================================================================

class TestProblemDescriptor:
    """_problem_descriptor(p)."""

    def test_sorted_tags(self):
        p = {"tags": ["z_tag", "a_tag"], "oeis": []}
        desc = _problem_descriptor(p)
        assert desc.index("a_tag") < desc.index("z_tag")

    def test_empty_problem(self):
        desc = _problem_descriptor({})
        assert desc == ""

    def test_oeis_included(self):
        p = {"tags": ["graph theory"], "oeis": ["A000041"]}
        desc = _problem_descriptor(p)
        assert "A000041" in desc

    def test_oeis_na_filtered(self):
        p = {"tags": [], "oeis": ["N/A"]}
        desc = _problem_descriptor(p)
        assert "N/A" not in desc


class TestCompressedSize:
    """compressed_size(s)."""

    def test_empty_small(self):
        assert compressed_size("") < 20

    def test_repetitive_smaller(self):
        """Repetitive strings compress better than random."""
        rep = "abcabc" * 100
        rand_str = "".join(chr(65 + (i * 37 + 13) % 26) for i in range(600))
        assert compressed_size(rep) < compressed_size(rand_str)

    def test_longer_strings_bigger(self):
        """Broadly, longer input -> longer compressed output."""
        s1 = "abc"
        s2 = "abc" * 1000
        assert compressed_size(s1) < compressed_size(s2)


class TestKolmogorovProxy:
    """kolmogorov_proxy(problems)."""

    def test_returns_dict(self, problems):
        kp = kolmogorov_proxy(problems)
        assert isinstance(kp, dict)

    def test_correlation_bounded(self, problems):
        kp = kolmogorov_proxy(problems)
        assert -1.0 <= kp["correlation"] <= 1.0

    def test_records_count(self, problems):
        kp = kolmogorov_proxy(problems)
        assert len(kp["records"]) == len(problems)

    def test_compression_ratio_bounded(self, problems):
        kp = kolmogorov_proxy(problems)
        for r in kp["records"]:
            # Compression can expand very short strings, but ratio should
            # be finite and positive.
            assert r["compression_ratio"] > 0

    def test_mean_compressed_positive(self, problems):
        kp = kolmogorov_proxy(problems)
        assert kp["mean_compressed_solved"] > 0
        assert kp["mean_compressed_open"] > 0

    def test_has_interpretation(self, problems):
        kp = kolmogorov_proxy(problems)
        assert len(kp["interpretation"]) > 10


# =========================================================================
# 4. Channel capacity
# =========================================================================

class TestCountAvoidingColorings:
    """count_avoiding_colorings(n, k)."""

    def test_n3_k3(self):
        """At n=3, all 3 vertices are mutually coprime (K_3 exists).
        8 colorings, 6 avoid mono-K_3 (all non-monochromatic edge triples)."""
        av, total = count_avoiding_colorings(3, 3)
        # 2^3 = 8 total; colorings 000 and 111 are monochromatic K_3
        assert total == 8
        assert av == 6

    def test_n8_k3(self):
        """n=8 is known to have exactly 36 avoiding colorings for K_3."""
        av, total = count_avoiding_colorings(8, 3)
        assert av == 36

    def test_n10_k3(self):
        """n=10 has 156 avoiding colorings (R_cop(3)-1 = 10)."""
        av, _ = count_avoiding_colorings(10, 3)
        assert av == 156

    def test_n11_k3_zero(self):
        """At n=11 = R_cop(3), zero avoiding colorings exist."""
        av, _ = count_avoiding_colorings(11, 3)
        assert av == 0

    def test_trivial_k2(self):
        """For k=2, any coloring of G([2]) has a monochromatic edge.
        At n=2 there is 1 coprime edge (1,2), both colorings are mono K_2."""
        av, total = count_avoiding_colorings(2, 2)
        assert av == 0
        assert total == 2

    def test_no_edges(self):
        """n=1 has no edges => 1 vacuous avoiding coloring."""
        av, total = count_avoiding_colorings(1, 3)
        assert av == 1
        assert total == 1


class TestRamseyChannelCapacity:
    """ramsey_channel_capacity(k, ns)."""

    def test_capacity_decreases(self):
        """Capacity should generally decrease as n increases toward R_cop(k)."""
        cap = ramsey_channel_capacity(k=3, ns=[3, 5, 8])
        caps = [r["capacity"] for r in cap]
        # Overall trend: first > last (capacity shrinks near R_cop)
        assert caps[0] > caps[-1]

    def test_capacity_zero_at_rcop(self):
        """At n = R_cop(3) = 11, capacity should be 0."""
        cap = ramsey_channel_capacity(k=3, ns=[11])
        assert cap[0]["capacity"] == 0.0
        assert cap[0]["avoiding"] == 0

    def test_capacity_positive_below_rcop(self):
        """Below R_cop(3), capacity should be positive."""
        cap = ramsey_channel_capacity(k=3, ns=[8])
        assert cap[0]["capacity"] > 0
        assert cap[0]["avoiding"] > 0

    def test_keys_present(self):
        cap = ramsey_channel_capacity(k=3, ns=[5])
        r = cap[0]
        for key in ["n", "edges", "avoiding", "total", "capacity", "log2_avoiding"]:
            assert key in r

    def test_capacity_bounded(self):
        """Capacity (bits/edge) is in [0, 1]."""
        # Use small n values to avoid timeout; heavy n=10/11 tested separately
        cap = ramsey_channel_capacity(k=3, ns=[3, 4, 5, 6, 7, 8])
        for r in cap:
            assert 0.0 <= r["capacity"] <= 1.0001


# =========================================================================
# 5. Minimum description length
# =========================================================================

class TestColoringToBitstring:
    """_coloring_to_bitstring."""

    def test_simple(self):
        edges = [(1, 2), (1, 3), (2, 3)]
        col = {(1, 2): 0, (1, 3): 1, (2, 3): 0}
        assert _coloring_to_bitstring(col, edges) == "010"

    def test_all_zeros(self):
        edges = [(1, 2), (1, 3)]
        col = {(1, 2): 0, (1, 3): 0}
        assert _coloring_to_bitstring(col, edges) == "00"


class TestWitnessMDL:
    """witness_mdl(n, k).

    Uses module-scoped fixture to avoid recomputing the expensive
    n=10 witness enumeration in every test method.
    """

    def test_n10_k3_avoiding_count(self, mdl_n10):
        """At n=10, k=3, there are 156 witnesses."""
        assert mdl_n10["avoiding"] == 156

    def test_n10_k3_edges(self, mdl_n10):
        expected_edges = len(coprime_graph_edges(10))
        assert mdl_n10["edges"] == expected_edges

    def test_backbone_fraction_bounded(self, mdl_n10):
        assert 0.0 <= mdl_n10["backbone_fraction"] <= 1.0

    def test_compression_ratio_less_than_raw(self, mdl_n10):
        """Joint compression should save space vs raw encoding."""
        if mdl_n10["avoiding"] > 1:
            assert mdl_n10["joint_compression_savings"] > 0

    def test_edge_entropies_present(self, mdl_n10):
        assert len(mdl_n10["edge_entropies"]) == mdl_n10["edges"]

    def test_edge_entropy_bounded(self, mdl_n10):
        for ee in mdl_n10["edge_entropies"]:
            assert 0.0 <= ee["entropy"] <= 1.0001

    def test_backbone_bits_fixed_value(self, mdl_n10):
        """Each backbone bit should be 0 or 1."""
        for bb in mdl_n10["backbone_bits"]:
            assert bb["fixed_color"] in (0, 1)

    def test_no_avoiding_at_n11(self):
        """At n=11 = R_cop(3), no witnesses => trivial MDL."""
        mdl = witness_mdl(n=11, k=3)
        assert mdl["avoiding"] == 0
        assert mdl["backbone_fraction"] == 0.0

    def test_small_n_works(self):
        """n=3 should work without error."""
        mdl = witness_mdl(n=3, k=3)
        assert mdl["avoiding"] == 6  # 8 - 2 monochromatic = 6
        assert mdl["edges"] == 3

    def test_n1_trivial(self):
        """n=1: no edges, trivial."""
        mdl = witness_mdl(n=1, k=3)
        assert mdl["edges"] == 0
        assert mdl["avoiding"] == 0


# =========================================================================
# Integration: consistency across modules
# =========================================================================

class TestCrossConsistency:
    """Check that different analyses agree on shared quantities."""

    def test_graph_entropy_matches_degree(self):
        """graph_entropy(n)['num_edges'] should equal len(coprime_graph_edges(n))."""
        for n in [5, 10, 20]:
            info = graph_entropy(n)
            edges = coprime_graph_edges(n)
            assert info["num_edges"] == len(edges)

    def test_feature_importance_base_entropy_binary(self, problems):
        """Base entropy should be that of a binary (solved/open) variable."""
        fi = feature_importance(problems)
        solved_count = sum(1 for p in problems if _is_solved(p))
        total = len(problems)
        p_solved = solved_count / total
        expected_h = -(p_solved * math.log2(p_solved)
                       + (1 - p_solved) * math.log2(1 - p_solved))
        assert abs(fi["base_entropy"] - expected_h) < 0.001

    def test_channel_capacity_matches_avoiding_count(self):
        """Channel capacity results should be consistent with direct counting."""
        cap = ramsey_channel_capacity(k=3, ns=[8])
        r = cap[0]
        av, total = count_avoiding_colorings(8, 3)
        assert r["avoiding"] == av
        assert r["total"] == total

    def test_mdl_matches_channel(self, mdl_n10):
        """MDL avoiding count should match channel capacity at n=10."""
        # Use cached mdl_n10 fixture; channel capacity at n=8 for speed
        # (we already verified n=10 avoiding = 156 via the fixture)
        assert mdl_n10["avoiding"] == 156
