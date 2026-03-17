"""Tests for research_frontier.py — frontier detection and momentum analysis."""
import math
import pytest

from research_frontier import (
    load_problems,
    tag_momentum,
    research_waves,
    breakthrough_detection,
    stagnation_analysis,
    emerging_connections,
    frontier_scores,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


class TestTagMomentum:
    """Test tag momentum computation."""

    def test_returns_list(self, problems):
        result = tag_momentum(problems)
        assert isinstance(result, list)

    def test_has_tags(self, problems):
        result = tag_momentum(problems)
        assert len(result) > 10

    def test_fields(self, problems):
        result = tag_momentum(problems)
        for m in result:
            assert "tag" in m
            assert "momentum" in m
            assert "early_solve_rate" in m
            assert "late_solve_rate" in m

    def test_sorted_by_momentum(self, problems):
        result = tag_momentum(problems)
        for i in range(len(result) - 1):
            assert result[i]["momentum"] >= result[i + 1]["momentum"] - 1e-6

    def test_solve_rates_bounded(self, problems):
        result = tag_momentum(problems)
        for m in result:
            assert 0.0 <= m["early_solve_rate"] <= 1.0
            assert 0.0 <= m["late_solve_rate"] <= 1.0

    def test_no_nan_momentum(self, problems):
        result = tag_momentum(problems)
        for m in result:
            assert not math.isnan(m["momentum"])

    def test_custom_window(self, problems):
        result = tag_momentum(problems, window=300)
        assert isinstance(result, list)
        assert len(result) > 0


class TestResearchWaves:
    """Test research wave detection."""

    def test_returns_list(self, problems):
        result = research_waves(problems)
        assert isinstance(result, list)

    def test_has_waves(self, problems):
        result = research_waves(problems)
        assert len(result) > 10

    def test_wave_fields(self, problems):
        result = research_waves(problems)
        for w in result:
            assert "tag" in w
            assert "wave_length" in w
            assert "problems" in w
            assert "start" in w
            assert "end" in w

    def test_sorted_by_length(self, problems):
        result = research_waves(problems)
        for i in range(len(result) - 1):
            assert result[i]["wave_length"] >= result[i + 1]["wave_length"]

    def test_minimum_wave_length(self, problems):
        result = research_waves(problems)
        for w in result:
            assert w["wave_length"] >= 2

    def test_span_consistent(self, problems):
        result = research_waves(problems)
        for w in result:
            assert w["span"] == w["end"] - w["start"]
            assert w["span"] >= 0


class TestBreakthroughDetection:
    """Test breakthrough/stagnation detection."""

    def test_returns_list(self, problems):
        result = breakthrough_detection(problems)
        assert isinstance(result, list)

    def test_has_breakthroughs(self, problems):
        result = breakthrough_detection(problems)
        bt = [b for b in result if b["breakthrough"]]
        assert len(bt) > 0

    def test_fields(self, problems):
        result = breakthrough_detection(problems)
        for b in result:
            assert "tag" in b
            assert "z_score" in b
            assert "solve_rate" in b
            assert "breakthrough" in b
            assert "stagnant" in b

    def test_sorted_by_zscore(self, problems):
        result = breakthrough_detection(problems)
        for i in range(len(result) - 1):
            assert result[i]["z_score"] >= result[i + 1]["z_score"] - 1e-6

    def test_solve_rate_bounded(self, problems):
        result = breakthrough_detection(problems)
        for b in result:
            assert 0.0 <= b["solve_rate"] <= 1.0

    def test_breakthrough_zscore_positive(self, problems):
        result = breakthrough_detection(problems)
        for b in result:
            if b["breakthrough"]:
                assert b["z_score"] > 2.0

    def test_stagnant_zscore_negative(self, problems):
        result = breakthrough_detection(problems)
        for b in result:
            if b["stagnant"]:
                assert b["z_score"] < -2.0


class TestStagnationAnalysis:
    """Test stagnation run detection."""

    def test_returns_list(self, problems):
        result = stagnation_analysis(problems)
        assert isinstance(result, list)

    def test_sorted_by_stagnation(self, problems):
        result = stagnation_analysis(problems)
        for i in range(len(result) - 1):
            assert result[i]["longest_stagnation"] >= result[i + 1]["longest_stagnation"]

    def test_stagnation_positive(self, problems):
        result = stagnation_analysis(problems)
        for s in result:
            assert s["longest_stagnation"] >= 0

    def test_open_fraction_bounded(self, problems):
        result = stagnation_analysis(problems)
        for s in result:
            assert 0.0 <= s["open_fraction"] <= 1.0

    def test_geometry_most_stagnant(self, problems):
        # geometry has the longest stagnation run based on our analysis
        result = stagnation_analysis(problems)
        assert result[0]["tag"] == "geometry"


class TestEmergingConnections:
    """Test emerging tag pair detection."""

    def test_returns_list(self, problems):
        result = emerging_connections(problems)
        assert isinstance(result, list)

    def test_has_pairs(self, problems):
        result = emerging_connections(problems)
        assert len(result) > 5

    def test_pair_fields(self, problems):
        result = emerging_connections(problems)
        for e in result:
            assert "tag_a" in e
            assert "tag_b" in e
            assert "emergence_ratio" in e
            assert "early_count" in e
            assert "late_count" in e

    def test_sorted_by_emergence(self, problems):
        result = emerging_connections(problems)
        for i in range(len(result) - 1):
            assert result[i]["emergence_ratio"] >= result[i + 1]["emergence_ratio"] - 1e-6

    def test_emergence_nonneg(self, problems):
        result = emerging_connections(problems)
        for e in result:
            assert e["emergence_ratio"] >= 0


class TestFrontierScores:
    """Test composite frontier scoring."""

    def test_returns_list(self, problems):
        result = frontier_scores(problems)
        assert isinstance(result, list)

    def test_has_scores(self, problems):
        result = frontier_scores(problems)
        assert len(result) > 10

    def test_score_bounded(self, problems):
        result = frontier_scores(problems)
        for f in result:
            assert 0.0 <= f["frontier_score"] <= 1.0

    def test_sorted_by_score(self, problems):
        result = frontier_scores(problems)
        for i in range(len(result) - 1):
            assert result[i]["frontier_score"] >= result[i + 1]["frontier_score"] - 1e-6

    def test_fields(self, problems):
        result = frontier_scores(problems)
        for f in result:
            assert "tag" in f
            assert "frontier_score" in f
            assert "momentum" in f
            assert "z_score" in f
            assert "open_count" in f

    def test_ramsey_top_frontier(self, problems):
        result = frontier_scores(problems)
        # Ramsey theory should be near the top
        top_tags = [f["tag"] for f in result[:5]]
        assert "ramsey theory" in top_tags
