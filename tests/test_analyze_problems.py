"""Tests for analyze_problems.py — Erdős problems relationship analysis."""
import json
import pytest
from pathlib import Path

from analyze_problems import (
    load_problems,
    analyze_status_distribution,
    analyze_tags,
    find_cross_category_problems,
    build_problem_graph,
    find_gateway_problems,
    find_open_formalization_opportunities,
    analyze_prize_problems,
)


@pytest.fixture
def problems(problems_yaml_path):
    """Load the problems dataset."""
    if not problems_yaml_path.exists():
        pytest.skip("Problems YAML not found")
    return load_problems()


class TestLoadProblems:
    """Test YAML loading."""

    def test_loads_nonempty(self, problems):
        assert len(problems) > 0

    def test_expected_count(self, problems):
        """Database should have ~1135 problems."""
        assert len(problems) > 1000

    def test_has_required_fields(self, problems):
        """Each problem should have a 'number' field."""
        for p in problems[:10]:
            assert "number" in p

    def test_has_tags(self, problems):
        """Most problems should have tags."""
        tagged = sum(1 for p in problems if p.get("tags"))
        assert tagged > len(problems) * 0.5


class TestStatusDistribution:
    """Test status analysis."""

    def test_returns_status_counts(self, problems):
        result = analyze_status_distribution(problems)
        assert "status" in result
        assert "formalized" in result

    def test_open_problems_exist(self, problems):
        result = analyze_status_distribution(problems)
        assert result["status"].get("open", 0) > 0


class TestTagAnalysis:
    """Test tag analysis."""

    def test_returns_tag_counts(self, problems):
        result = analyze_tags(problems)
        assert "tag_counts" in result
        assert len(result["tag_counts"]) > 0

    def test_common_tags_present(self, problems):
        """Expect common math categories in tags."""
        result = analyze_tags(problems)
        tags = set(result["tag_counts"].keys())
        # At least some of these should be present
        expected_some = {"number theory", "graph theory", "combinatorics", "geometry"}
        assert len(tags & expected_some) >= 2

    def test_tag_pairs(self, problems):
        result = analyze_tags(problems)
        assert "tag_pairs" in result


class TestCrossCategory:
    """Test cross-category problem detection."""

    def test_finds_cross_category(self, problems):
        cross = find_cross_category_problems(problems)
        assert len(cross) > 0

    def test_has_multiple_categories(self, problems):
        cross = find_cross_category_problems(problems)
        for p in cross[:5]:
            assert len(p["major_categories"]) >= 2


class TestProblemGraph:
    """Test problem graph construction."""

    def test_graph_has_nodes(self, problems):
        G = build_problem_graph(problems)
        assert G.number_of_nodes() > 0

    def test_graph_has_edges(self, problems):
        G = build_problem_graph(problems)
        assert G.number_of_edges() > 0

    def test_gateway_problems(self, problems):
        G = build_problem_graph(problems)
        gateways = find_gateway_problems(G, top_n=10)
        assert len(gateways) > 0
        # Gateway problems should have high degree
        assert gateways[0]["degree"] > 10


class TestFormalizationOpportunities:
    """Test formalization opportunity detection."""

    def test_finds_opportunities(self, problems):
        opps = find_open_formalization_opportunities(problems)
        assert len(opps) > 0


class TestPrizeProblems:
    """Test prize problem analysis."""

    def test_finds_prize_problems(self, problems):
        prizes = analyze_prize_problems(problems)
        assert len(prizes) > 0

    def test_prize_has_value(self, problems):
        prizes = analyze_prize_problems(problems)
        for p in prizes[:5]:
            assert p["prize"] != "no"
