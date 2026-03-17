"""Tests for problem_families.py — structural family detection."""
import pytest

from problem_families import (
    load_problems,
    build_affinity_graph,
    detect_families,
    family_entry_points,
    cross_family_bridges,
    family_momentum,
    family_taxonomy,
    oeis_family_clusters,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def graph(problems):
    return build_affinity_graph(problems)


@pytest.fixture(scope="module")
def families(problems, graph):
    return detect_families(problems, graph)


# ── build_affinity_graph ─────────────────────────────────────────────

class TestBuildAffinityGraph:
    """Test IDF-weighted affinity graph construction."""

    def test_returns_dict(self, graph):
        assert isinstance(graph, dict)

    def test_has_expected_keys(self, graph):
        assert "adjacency" in graph
        assert "n_nodes" in graph
        assert "n_edges" in graph
        assert "edge_type_counts" in graph
        assert "prob_by_num" in graph

    def test_node_count(self, graph, problems):
        assert graph["n_nodes"] == len(problems)

    def test_has_edges(self, graph):
        assert graph["n_edges"] > 0

    def test_has_strong_oeis_edges(self, graph):
        assert "strong_oeis" in graph["edge_type_counts"]
        assert graph["edge_type_counts"]["strong_oeis"] > 0

    def test_adjacency_symmetric(self, graph):
        adj = graph["adjacency"]
        for src, edges in adj.items():
            for tgt, w in edges:
                # Check reverse edge exists
                found = False
                for rev_tgt, rev_w in adj.get(tgt, []):
                    if rev_tgt == src:
                        found = True
                        break
                assert found, f"Edge {src}->{tgt} has no reverse"

    def test_weights_positive(self, graph):
        for src, edges in graph["adjacency"].items():
            for tgt, w in edges:
                assert w > 0

    def test_no_self_loops(self, graph):
        for src, edges in graph["adjacency"].items():
            for tgt, w in edges:
                assert tgt != src


# ── detect_families ──────────────────────────────────────────────────

class TestDetectFamilies:
    """Test family detection."""

    def test_returns_list(self, families):
        assert isinstance(families, list)

    def test_has_families(self, families):
        assert len(families) > 5

    def test_sorted_by_size(self, families):
        for i in range(len(families) - 1):
            assert families[i]["size"] >= families[i + 1]["size"]

    def test_min_family_size(self, families):
        for fam in families:
            assert fam["size"] >= 3

    def test_solve_rate_bounded(self, families):
        for fam in families:
            assert 0.0 <= fam["solve_rate"] <= 1.0

    def test_open_count_nonneg(self, families):
        for fam in families:
            assert fam["open_count"] >= 0

    def test_solved_open_sum(self, families):
        for fam in families:
            # solved + open <= size (some may be neither)
            assert fam["solved_count"] + fam["open_count"] <= fam["size"]

    def test_family_has_tags(self, families):
        for fam in families:
            assert isinstance(fam["tags"], list)
            assert len(fam["tags"]) > 0

    def test_family_has_patriarch(self, families):
        for fam in families:
            assert "patriarch" in fam
            assert fam["patriarch"] in fam["members"]

    def test_family_type_present(self, families):
        for fam in families:
            assert "family_type" in fam
            assert fam["family_type"] in (
                "oeis", "tag_signature", "oeis+tag_signature"
            )

    def test_no_member_overlap(self, families):
        """Each problem should appear in at most one family."""
        seen = set()
        for fam in families:
            for m in fam["members"]:
                assert m not in seen, f"Problem {m} in multiple families"
                seen.add(m)

    def test_members_sorted(self, families):
        for fam in families:
            assert fam["members"] == sorted(fam["members"])

    def test_custom_min_weight(self, problems, graph):
        strict = detect_families(problems, graph, min_weight=10.0)
        relaxed = detect_families(problems, graph, min_weight=5.0)
        assert len(strict) <= len(relaxed) + 5  # allow some variation from merging

    def test_custom_min_family_size(self, problems, graph):
        small = detect_families(problems, graph, min_family_size=3)
        large = detect_families(problems, graph, min_family_size=10)
        for fam in large:
            assert fam["size"] >= 10
        assert len(large) <= len(small)


# ── family_entry_points ──────────────────────────────────────────────

class TestFamilyEntryPoints:
    """Test entry point identification."""

    def test_returns_list(self, problems, families):
        result = family_entry_points(problems, families)
        assert isinstance(result, list)

    def test_sorted_by_score(self, problems, families):
        result = family_entry_points(problems, families)
        for i in range(len(result) - 1):
            assert result[i]["entry_score"] >= result[i + 1]["entry_score"] - 1e-6

    def test_score_bounded(self, problems, families):
        result = family_entry_points(problems, families)
        for e in result:
            assert 0.0 <= e["entry_score"] <= 1.0

    def test_has_required_fields(self, problems, families):
        result = family_entry_points(problems, families)
        for e in result:
            assert "number" in e
            assert "entry_score" in e
            assert "tags" in e
            assert "oeis_count" in e
            assert "tag_solve_rate" in e
            assert "family_size" in e
            assert "family_solve_rate" in e

    def test_tag_solve_rate_bounded(self, problems, families):
        result = family_entry_points(problems, families)
        for e in result:
            assert 0.0 <= e["tag_solve_rate"] <= 1.0

    def test_one_per_family(self, problems, families):
        """Each family should contribute at most one entry point."""
        result = family_entry_points(problems, families)
        families_with_open = sum(1 for f in families if f["open_count"] > 0)
        assert len(result) <= families_with_open


# ── cross_family_bridges ─────────────────────────────────────────────

class TestCrossFamilyBridges:
    """Test cross-family bridge detection."""

    def test_returns_list(self, problems, families, graph):
        result = cross_family_bridges(problems, families, graph)
        assert isinstance(result, list)

    def test_bridge_fields(self, problems, families, graph):
        result = cross_family_bridges(problems, families, graph)
        for b in result:
            assert "number" in b
            assert "families_connected" in b
            assert "is_open" in b
            assert "tags" in b

    def test_sorted_by_connections(self, problems, families, graph):
        result = cross_family_bridges(problems, families, graph)
        for i in range(len(result) - 1):
            assert result[i]["families_connected"] >= result[i + 1]["families_connected"]

    def test_min_two_families(self, problems, families, graph):
        result = cross_family_bridges(problems, families, graph)
        for b in result:
            assert b["families_connected"] >= 2


# ── family_momentum ──────────────────────────────────────────────────

class TestFamilyMomentum:
    """Test family momentum computation."""

    def test_returns_list(self, problems, families):
        result = family_momentum(problems, families)
        assert isinstance(result, list)

    def test_count_matches_families(self, problems, families):
        result = family_momentum(problems, families)
        assert len(result) == len(families)

    def test_sorted_by_momentum(self, problems, families):
        result = family_momentum(problems, families)
        for i in range(len(result) - 1):
            assert result[i]["momentum"] >= result[i + 1]["momentum"] - 1e-6

    def test_momentum_bounded(self, problems, families):
        result = family_momentum(problems, families)
        for m in result:
            assert -1.0 <= m["momentum"] <= 1.0

    def test_rates_bounded(self, problems, families):
        result = family_momentum(problems, families)
        for m in result:
            assert 0.0 <= m["early_rate"] <= 1.0
            assert 0.0 <= m["late_rate"] <= 1.0

    def test_has_required_fields(self, problems, families):
        result = family_momentum(problems, families)
        for m in result:
            assert "family_patriarch" in m
            assert "family_size" in m
            assert "momentum" in m
            assert "tags" in m


# ── family_taxonomy ──────────────────────────────────────────────────

class TestFamilyTaxonomy:
    """Test family classification."""

    def test_returns_dict(self, problems, families):
        result = family_taxonomy(problems, families)
        assert isinstance(result, dict)

    def test_has_four_categories(self, problems, families):
        result = family_taxonomy(problems, families)
        assert set(result.keys()) == {"nearly_solved", "active", "stalled", "emerging"}

    def test_categories_are_lists(self, problems, families):
        result = family_taxonomy(problems, families)
        for cat, items in result.items():
            assert isinstance(items, list)

    def test_covers_all_families(self, problems, families):
        result = family_taxonomy(problems, families)
        total = sum(len(items) for items in result.values())
        assert total == len(families)

    def test_nearly_solved_high_rate(self, problems, families):
        result = family_taxonomy(problems, families)
        for item in result["nearly_solved"]:
            assert item["solve_rate"] > 0.7

    def test_stalled_low_rate(self, problems, families):
        result = family_taxonomy(problems, families)
        for item in result["stalled"]:
            assert item["solve_rate"] <= 0.3
            assert item["size"] > 5


# ── oeis_family_clusters ─────────────────────────────────────────────

class TestOEISFamilyClusters:
    """Test OEIS-based cluster detection."""

    def test_returns_list(self, problems):
        result = oeis_family_clusters(problems)
        assert isinstance(result, list)

    def test_has_clusters(self, problems):
        result = oeis_family_clusters(problems)
        assert len(result) > 0

    def test_sorted_by_size(self, problems):
        result = oeis_family_clusters(problems)
        for i in range(len(result) - 1):
            assert result[i]["size"] >= result[i + 1]["size"]

    def test_cluster_fields(self, problems):
        result = oeis_family_clusters(problems)
        for c in result:
            assert "members" in c
            assert "size" in c
            assert "connecting_sequences" in c
            assert "n_sequences" in c
            assert "solve_rate" in c

    def test_solve_rate_bounded(self, problems):
        result = oeis_family_clusters(problems)
        for c in result:
            assert 0.0 <= c["solve_rate"] <= 1.0

    def test_size_matches_members(self, problems):
        result = oeis_family_clusters(problems)
        for c in result:
            assert c["size"] == len(c["members"])

    def test_no_member_overlap(self, problems):
        result = oeis_family_clusters(problems)
        seen = set()
        for c in result:
            for m in c["members"]:
                assert m not in seen
                seen.add(m)
