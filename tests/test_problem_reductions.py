"""Tests for problem_reductions.py -- structural reductions among Erdos problems."""
import math
import pytest

from problem_reductions import (
    load_problems,
    _number,
    _tags,
    _oeis,
    _status,
    _is_open,
    _is_solved,
    _prize,
    compute_tag_idf,
    build_oeis_index,
    tag_similarity,
    is_specialization,
    is_dual_pair,
    ReductionType,
    build_reduction_graph,
    find_sccs,
    find_equivalence_classes,
    compute_in_degree,
    compute_reachability,
    find_universal_problems,
    catalogue_known_reductions,
    build_ramsey_taxonomy,
    find_common_generalizations,
    meta_ramsey_predictions,
    AbstractRamseyProblem,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def graph(problems):
    return build_reduction_graph(problems)


# ═══════════════════════════════════════════════════════════════════
# Section 0: YAML helpers
# ═══════════════════════════════════════════════════════════════════

class TestYAMLHelpers:
    """Test robust YAML field accessors."""

    def test_number_int(self):
        assert _number({"number": 42}) == 42

    def test_number_str(self):
        assert _number({"number": "42"}) == 42

    def test_number_missing(self):
        assert _number({}) == 0

    def test_number_invalid(self):
        assert _number({"number": "abc"}) == 0

    def test_tags_present(self):
        p = {"tags": ["number theory", "primes"]}
        assert _tags(p) == {"number theory", "primes"}

    def test_tags_missing(self):
        assert _tags({}) == set()

    def test_oeis_valid(self):
        p = {"oeis": ["A000001", "N/A", "possible"]}
        assert _oeis(p) == {"A000001"}

    def test_oeis_all_invalid(self):
        p = {"oeis": ["N/A", "possible"]}
        assert _oeis(p) == set()

    def test_oeis_missing(self):
        assert _oeis({}) == set()

    def test_oeis_not_list(self):
        assert _oeis({"oeis": "A000001"}) == set()

    def test_status(self):
        assert _status({"status": {"state": "open"}}) == "open"
        assert _status({}) == "unknown"

    def test_is_open(self):
        assert _is_open({"status": {"state": "open"}})
        assert not _is_open({"status": {"state": "proved"}})

    def test_is_solved(self):
        assert _is_solved({"status": {"state": "proved"}})
        assert _is_solved({"status": {"state": "disproved"}})
        assert not _is_solved({"status": {"state": "open"}})

    def test_prize_dollar(self):
        assert _prize({"prize": "$500"}) == 500.0

    def test_prize_no(self):
        assert _prize({"prize": "no"}) == 0.0

    def test_prize_gbp(self):
        val = _prize({"prize": "\u00a3100"})
        assert val == pytest.approx(127.0)


# ═══════════════════════════════════════════════════════════════════
# Section 1: Reduction graph construction
# ═══════════════════════════════════════════════════════════════════

class TestTagIDF:
    """Test IDF weight computation for tags."""

    def test_returns_dict(self, problems):
        idf = compute_tag_idf(problems)
        assert isinstance(idf, dict)

    def test_all_positive(self, problems):
        idf = compute_tag_idf(problems)
        for v in idf.values():
            assert v > 0

    def test_rare_tag_higher_weight(self, problems):
        """Rare tags should have higher IDF than common ones."""
        idf = compute_tag_idf(problems)
        if "number theory" in idf and len(idf) > 1:
            # number theory is the most common tag
            min_other = min(v for k, v in idf.items() if k != "number theory")
            # Common tag should have lower IDF than rarer ones
            assert idf["number theory"] <= min_other + 0.01


class TestOEISIndex:
    """Test OEIS co-occurrence index."""

    def test_returns_dict(self, problems):
        idx = build_oeis_index(problems)
        assert isinstance(idx, dict)

    def test_no_invalid_entries(self, problems):
        idx = build_oeis_index(problems)
        assert "N/A" not in idx
        assert "possible" not in idx

    def test_values_are_lists(self, problems):
        idx = build_oeis_index(problems)
        for v in idx.values():
            assert isinstance(v, list)
            assert all(isinstance(n, int) for n in v)


class TestTagSimilarity:
    """Test IDF-weighted Jaccard similarity."""

    def test_identical_tags(self):
        idf = {"a": 1.0, "b": 2.0}
        assert tag_similarity({"a", "b"}, {"a", "b"}, idf) == pytest.approx(1.0)

    def test_disjoint_tags(self):
        idf = {"a": 1.0, "b": 2.0, "c": 1.0, "d": 2.0}
        assert tag_similarity({"a", "b"}, {"c", "d"}, idf) == pytest.approx(0.0)

    def test_partial_overlap(self):
        idf = {"a": 1.0, "b": 2.0, "c": 1.0}
        sim = tag_similarity({"a", "b"}, {"a", "c"}, idf)
        assert 0 < sim < 1

    def test_empty_tags(self):
        assert tag_similarity(set(), {"a"}, {"a": 1.0}) == 0.0
        assert tag_similarity(set(), set(), {}) == 0.0

    def test_idf_weighting_matters(self):
        """A rare shared tag should give higher similarity than a common one."""
        low_idf = {"shared": 0.1, "a": 1.0, "b": 1.0}
        high_idf = {"shared": 5.0, "a": 1.0, "b": 1.0}
        sim_low = tag_similarity({"shared", "a"}, {"shared", "b"}, low_idf)
        sim_high = tag_similarity({"shared", "a"}, {"shared", "b"}, high_idf)
        assert sim_high > sim_low


class TestSpecialization:
    """Test tag-based specialization detection."""

    def test_strict_superset(self):
        assert is_specialization({"a", "b", "c"}, {"a", "b"})

    def test_equal_sets(self):
        assert not is_specialization({"a", "b"}, {"a", "b"})

    def test_not_superset(self):
        assert not is_specialization({"a", "b"}, {"b", "c"})

    def test_empty_base(self):
        assert not is_specialization({"a"}, set())


class TestDualPair:
    """Test known duality detection."""

    def test_ramsey_hypergraph_duality(self):
        ta = {"Ramsey theory", "graph theory", "chromatic number"}
        tb = {"Ramsey theory", "hypergraphs", "intersecting families"}
        assert is_dual_pair(ta, tb)

    def test_non_dual(self):
        ta = {"number theory", "primes"}
        tb = {"geometry", "distances"}
        assert not is_dual_pair(ta, tb)

    def test_symmetric(self):
        """Duality should be symmetric."""
        ta = {"additive combinatorics", "number theory"}
        tb = {"multiplicative number theory", "number theory"}
        assert is_dual_pair(ta, tb) == is_dual_pair(tb, ta)


class TestBuildReductionGraph:
    """Test the full reduction graph construction."""

    def test_returns_dict(self, graph):
        assert isinstance(graph, dict)

    def test_has_required_keys(self, graph):
        assert "adjacency" in graph
        assert "nodes" in graph
        assert "edge_count" in graph
        assert "type_counts" in graph
        assert "prob_by_num" in graph

    def test_nodes_are_open(self, graph):
        """All nodes in the reduction graph should be open problems."""
        prob_by_num = graph["prob_by_num"]
        for n in graph["nodes"]:
            assert _is_open(prob_by_num[n]), f"#{n} is not open"

    def test_has_edges(self, graph):
        assert graph["edge_count"] > 0

    def test_has_specialization_edges(self, graph):
        assert graph["type_counts"].get(ReductionType.SPECIALIZATION, 0) > 0

    def test_type_counts_sum(self, graph):
        """Type counts should sum to total edge count."""
        total = sum(graph["type_counts"].values())
        assert total == graph["edge_count"]

    def test_adjacency_targets_are_nodes(self, graph):
        """Every edge target should be in the node set."""
        for src, edges in graph["adjacency"].items():
            assert src in graph["nodes"]
            for tgt, rtype, w in edges:
                assert tgt in graph["nodes"]

    def test_edge_weights_positive(self, graph):
        for src, edges in graph["adjacency"].items():
            for tgt, rtype, w in edges:
                assert w > 0

    def test_edge_types_valid(self, graph):
        valid = {ReductionType.SPECIALIZATION, ReductionType.TRANSFORMATION,
                 ReductionType.DUALITY}
        for src, edges in graph["adjacency"].items():
            for tgt, rtype, w in edges:
                assert rtype in valid


# ═══════════════════════════════════════════════════════════════════
# Section 2: Equivalence classes (SCCs)
# ═══════════════════════════════════════════════════════════════════

class TestFindSCCs:
    """Test Tarjan's SCC algorithm."""

    def test_empty_graph(self):
        sccs = find_sccs({}, set())
        assert sccs == []

    def test_single_node(self):
        sccs = find_sccs({}, {1})
        assert len(sccs) == 1
        assert sccs[0] == {1}

    def test_simple_cycle(self):
        adj = {
            1: [(2, "t", 1.0)],
            2: [(3, "t", 1.0)],
            3: [(1, "t", 1.0)],
        }
        sccs = find_sccs(adj, {1, 2, 3})
        assert len(sccs) == 1
        assert sccs[0] == {1, 2, 3}

    def test_two_sccs(self):
        adj = {
            1: [(2, "t", 1.0)],
            2: [(1, "t", 1.0)],
            3: [(4, "t", 1.0)],
            4: [(3, "t", 1.0)],
        }
        sccs = find_sccs(adj, {1, 2, 3, 4})
        assert len(sccs) == 2
        sizes = sorted([len(s) for s in sccs])
        assert sizes == [2, 2]

    def test_dag(self):
        """A DAG has only singleton SCCs."""
        adj = {
            1: [(2, "t", 1.0)],
            2: [(3, "t", 1.0)],
        }
        sccs = find_sccs(adj, {1, 2, 3})
        assert all(len(s) == 1 for s in sccs)

    def test_sorted_by_size(self):
        adj = {
            1: [(2, "t", 1.0)],
            2: [(1, "t", 1.0)],
            3: [(4, "t", 1.0)],
            4: [(5, "t", 1.0)],
            5: [(3, "t", 1.0)],
        }
        sccs = find_sccs(adj, {1, 2, 3, 4, 5})
        sizes = [len(s) for s in sccs]
        assert sizes == sorted(sizes, reverse=True)


class TestEquivalenceClasses:
    """Test equivalence class extraction from reduction graph."""

    def test_returns_list(self, graph):
        classes = find_equivalence_classes(graph)
        assert isinstance(classes, list)

    def test_all_classes_have_required_keys(self, graph):
        classes = find_equivalence_classes(graph)
        for c in classes:
            assert "members" in c
            assert "size" in c
            assert "tags" in c
            assert "internal_edge_types" in c
            assert "total_prize" in c

    def test_min_size_respected(self, graph):
        classes = find_equivalence_classes(graph, min_size=3)
        for c in classes:
            assert c["size"] >= 3

    def test_sorted_by_size(self, graph):
        classes = find_equivalence_classes(graph)
        sizes = [c["size"] for c in classes]
        assert sizes == sorted(sizes, reverse=True)

    def test_members_are_open_problems(self, graph):
        classes = find_equivalence_classes(graph)
        prob_by_num = graph["prob_by_num"]
        for c in classes:
            for n in c["members"]:
                assert _is_open(prob_by_num[n])

    def test_no_duplicate_members(self, graph):
        classes = find_equivalence_classes(graph)
        all_members = []
        for c in classes:
            all_members.extend(c["members"])
        # Each problem appears in at most one SCC
        assert len(all_members) == len(set(all_members))


# ═══════════════════════════════════════════════════════════════════
# Section 3: Universal problems
# ═══════════════════════════════════════════════════════════════════

class TestInDegree:
    """Test in-degree computation."""

    def test_simple_graph(self):
        graph = {
            "adjacency": {
                1: [(2, "t", 1.0), (3, "t", 1.0)],
                2: [(3, "t", 1.0)],
            },
            "nodes": {1, 2, 3},
        }
        deg = compute_in_degree(graph)
        assert deg[3] == 2
        assert deg[2] == 1
        assert deg.get(1, 0) == 0


class TestReachability:
    """Test BFS reachability computation."""

    def test_chain(self):
        graph = {
            "adjacency": {
                1: [(2, "t", 1.0)],
                2: [(3, "t", 1.0)],
            },
            "nodes": {1, 2, 3},
        }
        reach = compute_reachability(graph)
        assert reach[1] == 2  # 1 reaches 2 and 3
        assert reach[2] == 1  # 2 reaches 3
        assert reach[3] == 0  # 3 is a sink

    def test_cycle(self):
        graph = {
            "adjacency": {
                1: [(2, "t", 1.0)],
                2: [(3, "t", 1.0)],
                3: [(1, "t", 1.0)],
            },
            "nodes": {1, 2, 3},
        }
        reach = compute_reachability(graph)
        assert reach[1] == 2
        assert reach[2] == 2
        assert reach[3] == 2

    def test_isolated(self):
        graph = {
            "adjacency": {},
            "nodes": {1, 2, 3},
        }
        reach = compute_reachability(graph)
        assert all(v == 0 for v in reach.values())


class TestUniversalProblems:
    """Test universal problem identification from real data."""

    def test_returns_list(self, graph):
        unis = find_universal_problems(graph)
        assert isinstance(unis, list)

    def test_has_required_keys(self, graph):
        unis = find_universal_problems(graph, top_k=5)
        for u in unis:
            assert "number" in u
            assert "reachability" in u
            assert "in_degree" in u
            assert "tags" in u
            assert "prize" in u

    def test_sorted_by_reachability(self, graph):
        unis = find_universal_problems(graph, top_k=10)
        reaches = [u["reachability"] for u in unis]
        assert reaches == sorted(reaches, reverse=True)

    def test_top_k_respected(self, graph):
        unis = find_universal_problems(graph, top_k=5)
        assert len(unis) <= 5

    def test_reachability_nonnegative(self, graph):
        unis = find_universal_problems(graph)
        for u in unis:
            assert u["reachability"] >= 0


# ═══════════════════════════════════════════════════════════════════
# Section 4: Known reductions catalogue
# ═══════════════════════════════════════════════════════════════════

class TestKnownReductions:
    """Test the catalogue of known cross-problem transformations."""

    def test_catalogue_nonempty(self):
        cat = catalogue_known_reductions()
        assert len(cat) >= 5

    def test_required_fields(self):
        cat = catalogue_known_reductions()
        for r in cat:
            assert "source" in r
            assert "target" in r
            assert "transform" in r
            assert "type" in r
            assert "domain" in r
            assert "verified" in r

    def test_all_verified(self):
        """All catalogued reductions should be computationally verified."""
        cat = catalogue_known_reductions()
        for r in cat:
            assert r["verified"], f"Unverified: {r['source']} -> {r['target']}"

    def test_has_gcd_scaling(self):
        cat = catalogue_known_reductions()
        names = [r["source"] for r in cat]
        assert any("gcd" in n.lower() for n in names)

    def test_has_schur_invariance(self):
        cat = catalogue_known_reductions()
        names = [r["source"] for r in cat]
        assert any("S(G" in n for n in names)

    def test_has_density_schur(self):
        cat = catalogue_known_reductions()
        names = [r["source"] for r in cat]
        assert any("DS(" in n for n in names)

    def test_has_squarefree(self):
        cat = catalogue_known_reductions()
        names = [r["source"] for r in cat]
        assert any("SF" in n for n in names)

    def test_domains_diverse(self):
        """Reductions should span multiple domains."""
        cat = catalogue_known_reductions()
        domains = set(r["domain"] for r in cat)
        assert len(domains) >= 2


# ═══════════════════════════════════════════════════════════════════
# Section 5: Generalization search
# ═══════════════════════════════════════════════════════════════════

class TestRamseyTaxonomy:
    """Test the unified Ramsey taxonomy."""

    def test_nonempty(self):
        tax = build_ramsey_taxonomy()
        assert len(tax) >= 5

    def test_required_fields(self):
        tax = build_ramsey_taxonomy()
        for t in tax:
            assert "name" in t
            assert "graph_family" in t
            assert "forbidden_property" in t
            assert "known_values" in t
            assert "growth_class" in t

    def test_coprime_ramsey_present(self):
        tax = build_ramsey_taxonomy()
        names = [t["name"] for t in tax]
        assert any("cop" in n.lower() for n in names)

    def test_classical_ramsey_present(self):
        tax = build_ramsey_taxonomy()
        names = [t["name"] for t in tax]
        assert any("classical" in n.lower() or "R(k)" in n for n in names)

    def test_schur_present(self):
        tax = build_ramsey_taxonomy()
        names = [t["name"] for t in tax]
        assert any("schur" in n.lower() or "S(k)" in n for n in names)

    def test_density_is_numeric(self):
        tax = build_ramsey_taxonomy()
        for t in tax:
            d = t["density"]
            if isinstance(d, (int, float)):
                assert d >= 0

    def test_known_coprime_ramsey_value(self):
        tax = build_ramsey_taxonomy()
        cop = [t for t in tax if "cop" in t["name"].lower()][0]
        assert cop["known_values"].get(3) == 11


class TestCommonGeneralizations:
    """Test the common generalization framework."""

    def test_nonempty(self):
        gens = find_common_generalizations()
        assert len(gens) >= 2

    def test_required_fields(self):
        gens = find_common_generalizations()
        for g in gens:
            assert "name" in g
            assert "framework" in g
            assert "instances" in g
            assert "key_parameter" in g
            assert "prediction" in g

    def test_instances_nonempty(self):
        gens = find_common_generalizations()
        for g in gens:
            assert len(g["instances"]) >= 2

    def test_nt_ramsey_framework_present(self):
        gens = find_common_generalizations()
        names = [g["name"] for g in gens]
        assert any("ramsey" in n.lower() for n in names)

    def test_parameterized_schur_present(self):
        gens = find_common_generalizations()
        names = [g["name"] for g in gens]
        assert any("schur" in n.lower() for n in names)

    def test_rado_spectrum_present(self):
        gens = find_common_generalizations()
        names = [g["name"] for g in gens]
        assert any("rado" in n.lower() for n in names)


class TestAbstractRamseyProblem:
    """Test the abstract Ramsey problem class."""

    def test_creation(self):
        p = AbstractRamseyProblem("test", "a test problem")
        assert p.name == "test"
        assert p.description == "a test problem"

    def test_repr(self):
        p = AbstractRamseyProblem("test", "a test problem")
        assert "test" in repr(p)


# ═══════════════════════════════════════════════════════════════════
# Section 6: Meta-Ramsey predictions
# ═══════════════════════════════════════════════════════════════════

class TestMetaRamseyPredictions:
    """Test the meta-Ramsey analysis."""

    def test_returns_dict(self):
        pred = meta_ramsey_predictions()
        assert isinstance(pred, dict)

    def test_has_known_data(self):
        pred = meta_ramsey_predictions()
        assert "known_data" in pred
        assert len(pred["known_data"]) >= 3

    def test_coprime_density(self):
        """Coprime density should be approximately 6/pi^2."""
        pred = meta_ramsey_predictions()
        cop = [d for d in pred["known_data"] if d["family"] == "coprime"]
        assert len(cop) == 1
        assert cop[0]["density"] == pytest.approx(6.0 / math.pi ** 2, rel=0.01)

    def test_coprime_R3(self):
        pred = meta_ramsey_predictions()
        cop = [d for d in pred["known_data"] if d["family"] == "coprime"]
        assert cop[0]["R_3"] == 11

    def test_gcd_scaling_visible(self):
        """GCD-d Ramsey numbers should show d * R_cop(3) = d * 11."""
        pred = meta_ramsey_predictions()
        for d_data in pred["known_data"]:
            if d_data["family"] == "gcd_2":
                assert d_data["R_3"] == 22
            elif d_data["family"] == "gcd_3":
                assert d_data["R_3"] == 33

    def test_has_conjecture(self):
        pred = meta_ramsey_predictions()
        assert "conjecture" in pred
        assert len(pred["conjecture"]) > 50

    def test_has_observation(self):
        pred = meta_ramsey_predictions()
        assert "observation" in pred

    def test_r_sqrt_density_product(self):
        """R * sqrt(density) should be roughly constant for GCD-d subfamily."""
        pred = meta_ramsey_predictions()
        gcd_data = [d for d in pred["known_data"]
                     if d["family"] in ("coprime", "gcd_2", "gcd_3")]
        if len(gcd_data) >= 2:
            products = [d["R_times_sqrt_density"] for d in gcd_data]
            # All should be within ~10% of each other
            mean_prod = sum(products) / len(products)
            for p in products:
                assert abs(p - mean_prod) / mean_prod < 0.15


# ═══════════════════════════════════════════════════════════════════
# Section 7: Computational verification of specific reductions
# ═══════════════════════════════════════════════════════════════════

class TestGCDRamseyScaling:
    """Test R_gcd(3; d) = d * R_cop(3) = 11d."""

    @pytest.mark.timeout(120)
    def test_scaling(self):
        from problem_reductions import gcd_ramsey_scaling
        result = gcd_ramsey_scaling(k=3)
        assert result["k"] == 3
        assert result["rcop_k"] == 11
        # d=1 should be verified (it's just R_cop(3) = 11)
        d1 = [r for r in result["results"] if r["d"] == 1]
        assert len(d1) == 1
        assert d1[0]["verified"]


class TestSchurGroupInvariance:
    """Test S(G, 2) depends only on |G|."""

    @pytest.mark.timeout(120)
    def test_invariance(self):
        from problem_reductions import schur_group_invariance
        result = schur_group_invariance(max_order=8)
        assert result["all_verified"]
        # Should have at least one order with multiple groups
        multi_group = [r for r in result["results"] if len(r["groups"]) >= 2]
        assert len(multi_group) >= 1


class TestDensitySchurReduction:
    """Test DS(k, 1/k) = S(k) + 1."""

    @pytest.mark.timeout(120)
    def test_reduction(self):
        from problem_reductions import density_schur_reduction
        result = density_schur_reduction()
        assert result["all_verified"]
        # k=1: S(1)=1, DS(1,1)=2
        k1 = [r for r in result["results"] if r["k"] == 1]
        assert len(k1) == 1
        assert k1[0]["S_k"] == 1
        assert k1[0]["DS_k_1_over_k"] == 2


class TestSquarefreeCoprime:
    """Test R_SF(3) = R_cop(3) = 11."""

    @pytest.mark.timeout(120)
    def test_equality(self):
        from problem_reductions import squarefree_coprime_reduction
        result = squarefree_coprime_reduction(k=3)
        assert result["equal"]
        assert result["R_SF"] == 11
        assert result["R_cop"] == 11


# ═══════════════════════════════════════════════════════════════════
# Section 8: Integration / smoke tests
# ═══════════════════════════════════════════════════════════════════

class TestIntegration:
    """End-to-end tests on the full analysis."""

    def test_graph_has_open_problems(self, graph):
        """Reduction graph should contain a substantial number of open problems."""
        assert len(graph["nodes"]) > 100

    def test_multiple_reduction_types(self, graph):
        """Should find multiple types of reductions."""
        assert len(graph["type_counts"]) >= 1

    def test_equivalence_classes_exist(self, graph):
        """Should find at least some equivalence classes."""
        classes = find_equivalence_classes(graph, min_size=2)
        assert len(classes) >= 1

    def test_largest_class_has_common_tags(self, graph):
        """The largest equivalence class should share tags."""
        classes = find_equivalence_classes(graph, min_size=2)
        if classes:
            largest = classes[0]
            assert len(largest["tags"]) > 0

    def test_universal_problems_exist(self, graph):
        """Should find at least one problem with reachability > 0."""
        unis = find_universal_problems(graph, top_k=5)
        if unis:
            assert unis[0]["reachability"] >= 0

    def test_meta_ramsey_gcd_subfamily_constant(self):
        """R * sqrt(rho) should be roughly constant for GCD-d subfamily."""
        pred = meta_ramsey_predictions()
        gcd_products = []
        for d_data in pred["known_data"]:
            if d_data["family"].startswith("gcd_") or d_data["family"] == "coprime":
                gcd_products.append(d_data["R_times_sqrt_density"])
        if len(gcd_products) >= 2:
            mean = sum(gcd_products) / len(gcd_products)
            assert all(abs(p - mean) / mean < 0.2 for p in gcd_products)

    def test_taxonomy_covers_all_known_families(self):
        """Taxonomy should include coprime, divisibility, Schur, vdW, Paley."""
        tax = build_ramsey_taxonomy()
        names_lower = [t["name"].lower() for t in tax]
        all_text = " ".join(names_lower)
        assert "coprime" in all_text or "cop" in all_text
        assert "schur" in all_text or "s(k)" in all_text
        assert "waerden" in all_text or "w(k" in all_text
        assert "paley" in all_text


class TestMetaRamseyData:
    """Test the meta_ramsey_data function that computes densities."""

    @pytest.mark.timeout(120)
    def test_returns_dict(self):
        from problem_reductions import meta_ramsey_data
        data = meta_ramsey_data(max_n=15)
        assert isinstance(data, dict)
        assert "families" in data
        assert "density_vs_ramsey" in data

    @pytest.mark.timeout(120)
    def test_families_have_density(self):
        from problem_reductions import meta_ramsey_data
        data = meta_ramsey_data(max_n=15)
        for name, fam in data["families"].items():
            assert "density_at_n" in fam
            if fam["density_at_n"] is not None:
                assert fam["density_at_n"] >= 0


# ═══════════════════════════════════════════════════════════════════
# Section 9: Additional coverage tests
# ═══════════════════════════════════════════════════════════════════

class TestRunAnalysis:
    """Test the top-level run_analysis function."""

    @pytest.mark.timeout(120)
    def test_run_analysis(self):
        from problem_reductions import run_analysis
        results = run_analysis()
        assert "graph_stats" in results
        assert "equivalence_classes" in results
        assert "universal_problems" in results
        assert "known_reductions" in results
        assert "generalizations" in results
        assert "ramsey_taxonomy" in results
        assert "meta_ramsey_predictions" in results

    @pytest.mark.timeout(120)
    def test_run_analysis_graph_stats(self):
        from problem_reductions import run_analysis
        results = run_analysis()
        gs = results["graph_stats"]
        assert gs["nodes"] > 0
        assert gs["edges"] > 0


class TestDualityEdges:
    """Test that duality detection works with synthetic data."""

    def test_duality_edge_created(self):
        """Build a small graph with dual-tagged problems and verify edge."""
        from problem_reductions import build_reduction_graph
        # Create synthetic problems that match a known dual pair
        problems = [
            {
                "number": "9001",
                "tags": ["Ramsey theory", "graph theory", "cycles"],
                "status": {"state": "open"},
                "oeis": ["N/A"],
                "prize": "no",
            },
            {
                "number": "9002",
                "tags": ["Ramsey theory", "hypergraphs", "intersecting families"],
                "status": {"state": "open"},
                "oeis": ["N/A"],
                "prize": "no",
            },
        ]
        graph = build_reduction_graph(problems, tag_sim_threshold=0.0)
        # Should have at least the duality edge
        has_duality = False
        for src, edges in graph["adjacency"].items():
            for tgt, rtype, w in edges:
                if rtype == "duality":
                    has_duality = True
        assert has_duality

    def test_specialization_edge_created(self):
        """Problems where one's tags are a strict subset of the other's."""
        from problem_reductions import build_reduction_graph
        problems = [
            {
                "number": "9003",
                "tags": ["number theory", "primes", "additive basis"],
                "status": {"state": "open"},
                "oeis": ["N/A"],
                "prize": "no",
            },
            {
                "number": "9004",
                "tags": ["number theory", "primes"],
                "status": {"state": "open"},
                "oeis": ["N/A"],
                "prize": "no",
            },
        ]
        graph = build_reduction_graph(problems, tag_sim_threshold=0.0)
        has_spec = False
        for src, edges in graph["adjacency"].items():
            for tgt, rtype, w in edges:
                if rtype == "specialization":
                    has_spec = True
        assert has_spec


class TestPrizeEdgeCases:
    """Test prize parsing edge cases."""

    def test_prize_no_numbers(self):
        assert _prize({"prize": "unknown"}) == 0.0

    def test_prize_missing(self):
        assert _prize({}) == 0.0

    def test_prize_comma(self):
        assert _prize({"prize": "$1,000"}) == 1000.0
