"""Tests for problem_genealogy.py — intellectual lineage among Erdős problems."""
import math
import pytest

from problem_genealogy import (
    load_problems,
    build_genealogy,
    find_ancestors,
    find_terminals,
    find_orphans,
    intellectual_distance,
    diameter_sample,
    cross_family_bridges,
    genealogical_depth,
    generation_analysis,
    _number,
    _tags,
    _oeis,
    _status,
    _is_solved,
    _statement_words,
    _bigrams,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def genealogy(problems):
    return build_genealogy(problems)


@pytest.fixture(scope="module")
def genealogy_with_map(genealogy, problems):
    prob_map = {}
    for p in problems:
        n = _number(p)
        if n > 0:
            prob_map[n] = p
    genealogy["_prob_map"] = prob_map
    return genealogy


# ── Helper functions ────────────────────────────────────────────────

class TestHelpers:
    """Test internal helper functions."""

    def test_number_int(self):
        assert _number({"number": 42}) == 42

    def test_number_string(self):
        assert _number({"number": "123"}) == 123

    def test_number_missing(self):
        assert _number({}) == 0

    def test_number_invalid(self):
        assert _number({"number": "abc"}) == 0

    def test_tags_normal(self):
        assert _tags({"tags": ["a", "b"]}) == {"a", "b"}

    def test_tags_missing(self):
        assert _tags({}) == set()

    def test_oeis_normal(self):
        assert _oeis({"oeis": ["A000040", "A000079"]}) == ["A000040", "A000079"]

    def test_oeis_filters_na(self):
        assert _oeis({"oeis": ["A000040", "N/A", "possible"]}) == ["A000040"]

    def test_oeis_empty(self):
        assert _oeis({}) == []

    def test_status(self):
        assert _status({"status": {"state": "open"}}) == "open"

    def test_status_missing(self):
        assert _status({}) == "unknown"

    def test_is_solved_proved(self):
        assert _is_solved({"status": {"state": "proved"}}) is True

    def test_is_solved_open(self):
        assert _is_solved({"status": {"state": "open"}}) is False

    def test_statement_words_filters_stopwords(self):
        words = _statement_words({"statement": "The sum of all primes"})
        assert "the" not in words
        assert "sum" in words
        assert "primes" in words

    def test_statement_words_short(self):
        words = _statement_words({"statement": "If n is odd"})
        assert "if" not in words  # stopword
        assert "odd" in words

    def test_statement_words_dict_format(self):
        words = _statement_words({"statement": {"text": "chromatic number"}})
        assert "chromatic" in words
        assert "number" in words

    def test_bigrams_small(self):
        bg = _bigrams({"abc", "def", "ghi"})
        assert isinstance(bg, set)
        assert len(bg) > 0


# ── Build genealogy ─────────────────────────────────────────────────

class TestBuildGenealogy:
    """Test genealogy graph construction."""

    def test_returns_dict(self, genealogy):
        assert isinstance(genealogy, dict)

    def test_has_edges(self, genealogy):
        assert genealogy["n_edges"] > 100

    def test_has_nodes(self, genealogy):
        assert genealogy["n_nodes"] > 1000

    def test_edges_directed(self, genealogy):
        """All edges go from lower to higher number (ancestor → descendant)."""
        for (u, v) in genealogy["edges"]:
            assert u < v

    def test_edge_weights_positive(self, genealogy):
        for w in genealogy["edges"].values():
            assert w > 0

    def test_edge_reasons_nonempty(self, genealogy):
        for reasons in genealogy["edge_reasons"].values():
            assert len(reasons) > 0

    def test_connected_fraction(self, genealogy):
        """At least 40% of problems should be connected."""
        orphans = find_orphans(genealogy)
        connected = genealogy["n_nodes"] - len(orphans)
        assert connected / genealogy["n_nodes"] > 0.4

    def test_density_reasonable(self, genealogy):
        """Density should be between 0.1% and 10%."""
        n = genealogy["n_nodes"]
        density = genealogy["n_edges"] / (n * (n - 1) / 2)
        assert 0.001 < density < 0.10


# ── Ancestors ───────────────────────────────────────────────────────

class TestAncestors:
    """Test ancestral problem detection."""

    def test_returns_list(self, genealogy_with_map):
        ancestors = find_ancestors(genealogy_with_map)
        assert isinstance(ancestors, list)

    def test_nonempty(self, genealogy_with_map):
        ancestors = find_ancestors(genealogy_with_map)
        assert len(ancestors) > 0

    def test_top_ancestor_high_reachability(self, genealogy_with_map):
        ancestors = find_ancestors(genealogy_with_map)
        assert ancestors[0]["total_reachable"] > 50

    def test_sorted_by_reachability(self, genealogy_with_map):
        ancestors = find_ancestors(genealogy_with_map)
        for i in range(len(ancestors) - 1):
            assert ancestors[i]["total_reachable"] >= ancestors[i+1]["total_reachable"]

    def test_has_required_fields(self, genealogy_with_map):
        ancestors = find_ancestors(genealogy_with_map)
        for a in ancestors[:5]:
            assert "number" in a
            assert "direct_descendants" in a
            assert "total_reachable" in a


# ── Terminals ───────────────────────────────────────────────────────

class TestTerminals:
    """Test terminal problem detection."""

    def test_returns_list(self, genealogy):
        terminals = find_terminals(genealogy)
        assert isinstance(terminals, list)

    def test_nonempty(self, genealogy):
        terminals = find_terminals(genealogy)
        assert len(terminals) > 0

    def test_terminals_have_parents(self, genealogy):
        terminals = find_terminals(genealogy)
        for t in terminals:
            assert t["n_parents"] > 0

    def test_sorted_by_parents(self, genealogy):
        terminals = find_terminals(genealogy)
        for i in range(len(terminals) - 1):
            assert terminals[i]["n_parents"] >= terminals[i+1]["n_parents"]

    def test_high_numbered(self, genealogy):
        """Terminal problems should tend to have high numbers (later problems)."""
        terminals = find_terminals(genealogy)
        avg_num = sum(t["number"] for t in terminals) / len(terminals)
        assert avg_num > 500  # Should be biased toward later problems


# ── Orphans ─────────────────────────────────────────────────────────

class TestOrphans:
    """Test orphan detection."""

    def test_returns_list(self, genealogy):
        orphans = find_orphans(genealogy)
        assert isinstance(orphans, list)

    def test_sorted(self, genealogy):
        orphans = find_orphans(genealogy)
        assert orphans == sorted(orphans)

    def test_orphans_fewer_than_total(self, genealogy):
        orphans = find_orphans(genealogy)
        assert len(orphans) < genealogy["n_nodes"]

    def test_orphans_not_in_edges(self, genealogy):
        orphans = set(find_orphans(genealogy))
        for (u, v) in genealogy["edges"]:
            assert u not in orphans
            assert v not in orphans


# ── Intellectual distance ───────────────────────────────────────────

class TestIntellectualDistance:
    """Test shortest path computation."""

    def test_self_distance(self, genealogy):
        nums = genealogy["numbers"]
        # Pick a connected node
        connected = set()
        for (u, v) in genealogy["edges"]:
            connected.add(u)
            break
        if connected:
            n = connected.pop()
            result = intellectual_distance(genealogy, n, n)
            assert result["distance"] == 0
            assert result["connected"] is True

    def test_adjacent_distance(self, genealogy):
        """Two directly connected nodes should have distance 1."""
        for (u, v) in list(genealogy["edges"].keys())[:1]:
            result = intellectual_distance(genealogy, u, v)
            assert result["distance"] == 1
            assert result["connected"] is True

    def test_disconnected(self, genealogy):
        orphans = find_orphans(genealogy)
        if len(orphans) >= 2:
            result = intellectual_distance(genealogy, orphans[0], orphans[1])
            assert result["connected"] is False
            assert result["distance"] == -1

    def test_returns_path(self, genealogy):
        for (u, v) in list(genealogy["edges"].keys())[:1]:
            result = intellectual_distance(genealogy, u, v)
            assert len(result["path"]) == 2
            assert result["path"][0] == u
            assert result["path"][-1] == v


# ── Diameter sample ─────────────────────────────────────────────────

class TestDiameter:
    """Test diameter estimation."""

    def test_returns_dict(self, genealogy):
        result = diameter_sample(genealogy, n_samples=20)
        assert isinstance(result, dict)

    def test_max_distance_positive(self, genealogy):
        result = diameter_sample(genealogy, n_samples=20)
        assert result["max_distance"] > 0

    def test_avg_distance_positive(self, genealogy):
        result = diameter_sample(genealogy, n_samples=20)
        assert result["avg_distance"] > 0

    def test_has_required_fields(self, genealogy):
        result = diameter_sample(genealogy, n_samples=20)
        assert "max_distance" in result
        assert "avg_distance" in result
        assert "median_distance" in result
        assert "n_sampled" in result


# ── Cross-family bridges ───────────────────────────────────────────

class TestCrossFamilyBridges:
    """Test bridge detection between tag families."""

    def test_returns_list(self, genealogy, problems):
        bridges = cross_family_bridges(genealogy, problems)
        assert isinstance(bridges, list)

    def test_has_bridges(self, genealogy, problems):
        bridges = cross_family_bridges(genealogy, problems)
        assert len(bridges) > 0

    def test_bridge_fields(self, genealogy, problems):
        bridges = cross_family_bridges(genealogy, problems)
        for b in bridges[:5]:
            assert "from" in b
            assert "to" in b
            assert "weight" in b
            assert "reasons" in b
            assert "from_tags" in b
            assert "to_tags" in b
            assert "cross_family" in b

    def test_cross_family_exist(self, genealogy, problems):
        """At least some bridges should cross broad families."""
        bridges = cross_family_bridges(genealogy, problems)
        cross = [b for b in bridges if b["cross_family"]]
        assert len(cross) > 0


# ── Genealogical depth ─────────────────────────────────────────────

class TestGenealogicalDepth:
    """Test depth computation."""

    def test_returns_dict(self, genealogy):
        result = genealogical_depth(genealogy)
        assert isinstance(result, dict)

    def test_max_depth_positive(self, genealogy):
        result = genealogical_depth(genealogy)
        assert result["max_depth"] > 0

    def test_longest_chain_nonempty(self, genealogy):
        result = genealogical_depth(genealogy)
        assert len(result["longest_chain"]) > 1

    def test_chain_length_matches_depth(self, genealogy):
        result = genealogical_depth(genealogy)
        assert len(result["longest_chain"]) == result["max_depth"] + 1

    def test_chain_is_directed(self, genealogy):
        """Longest chain should have strictly increasing numbers."""
        result = genealogical_depth(genealogy)
        chain = result["longest_chain"]
        for i in range(len(chain) - 1):
            assert chain[i] < chain[i+1]

    def test_depth_distribution(self, genealogy):
        result = genealogical_depth(genealogy)
        assert len(result["depth_distribution"]) > 1

    def test_avg_depth_positive(self, genealogy):
        result = genealogical_depth(genealogy)
        assert result["avg_depth"] >= 0


# ── Generation analysis ────────────────────────────────────────────

class TestGenerationAnalysis:
    """Test generation partitioning."""

    def test_returns_dict(self, genealogy, problems):
        result = generation_analysis(genealogy, problems)
        assert isinstance(result, dict)

    def test_has_founders(self, genealogy, problems):
        result = generation_analysis(genealogy, problems)
        assert result["n_founders"] > 0

    def test_founders_more_than_connected(self, genealogy, problems):
        """Founders should include orphans + root nodes."""
        result = generation_analysis(genealogy, problems)
        # Orphans are also founders (no parents)
        assert result["n_founders"] > 100

    def test_generation_stats_nonempty(self, genealogy, problems):
        result = generation_analysis(genealogy, problems)
        assert len(result["generation_stats"]) > 0

    def test_solve_rates_bounded(self, genealogy, problems):
        result = generation_analysis(genealogy, problems)
        for g in result["generation_stats"]:
            assert 0.0 <= g["solve_rate"] <= 1.0

    def test_total_count_matches(self, genealogy, problems):
        result = generation_analysis(genealogy, problems)
        total = sum(g["count"] for g in result["generation_stats"])
        assert total == genealogy["n_nodes"]

    def test_founders_sample(self, genealogy, problems):
        result = generation_analysis(genealogy, problems)
        assert len(result["founders_sample"]) > 0
        # Sample should be sorted
        assert result["founders_sample"] == sorted(result["founders_sample"])


# ── Integration: full report ────────────────────────────────────────

class TestReport:
    """Test full report generation."""

    def test_report_nonempty(self, problems):
        from problem_genealogy import generate_report
        report = generate_report(problems)
        assert len(report) > 500

    def test_report_has_sections(self, problems):
        from problem_genealogy import generate_report
        report = generate_report(problems)
        assert "Ancestral Problems" in report
        assert "Terminal Problems" in report
        assert "Orphaned Problems" in report
        assert "Genealogical Depth" in report
        assert "Cross-Family Bridges" in report
        assert "Generation Analysis" in report
