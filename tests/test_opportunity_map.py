"""Tests for opportunity_map.py — unified opportunity scoring."""
import math
import pytest

from opportunity_map import (
    load_problems,
    collect_signals,
    compute_opportunity_scores,
    opportunity_tiers,
    tag_opportunities,
    signal_contributions,
    prize_weighted_ranking,
    research_portfolio,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def scored(problems):
    return compute_opportunity_scores(problems)


class TestCollectSignals:
    """Test signal collection from multiple modules."""

    def test_returns_list(self, problems):
        result = collect_signals(problems)
        assert isinstance(result, list)

    def test_only_open_problems(self, problems):
        result = collect_signals(problems)
        open_count = sum(1 for p in problems if p.get("status", {}).get("state") == "open")
        assert len(result) == open_count

    def test_has_signals_dict(self, problems):
        result = collect_signals(problems)
        for item in result:
            assert "signals" in item
            assert isinstance(item["signals"], dict)

    def test_signal_names(self, problems):
        result = collect_signals(problems)
        expected_signals = {
            "vulnerability", "avg_tag_solve_rate", "max_tag_solve_rate",
            "oeis_bridge_ratio", "cascade_potential", "best_pair_rate",
            "near_miss", "prize_signal", "oeis_count", "not_formalized",
        }
        for item in result:
            assert set(item["signals"].keys()) == expected_signals

    def test_signals_bounded(self, problems):
        result = collect_signals(problems)
        for item in result:
            for name, val in item["signals"].items():
                assert 0.0 <= val <= 1.01, f"{name}={val} out of bounds"

    def test_has_problem_metadata(self, problems):
        result = collect_signals(problems)
        for item in result:
            assert "number" in item
            assert "tags" in item
            assert "prize" in item

    def test_vulnerability_nonneg(self, problems):
        result = collect_signals(problems)
        for item in result:
            assert item["signals"]["vulnerability"] >= 0.0


class TestOpportunityScores:
    """Test composite scoring."""

    def test_returns_list(self, scored):
        assert isinstance(scored, list)

    def test_has_opportunity_score(self, scored):
        for item in scored:
            assert "opportunity_score" in item

    def test_sorted_descending(self, scored):
        for i in range(len(scored) - 1):
            assert scored[i]["opportunity_score"] >= scored[i + 1]["opportunity_score"] - 1e-6

    def test_scores_positive(self, scored):
        for item in scored:
            assert item["opportunity_score"] >= 0.0

    def test_scores_bounded(self, scored):
        for item in scored:
            assert item["opportunity_score"] <= 1.0

    def test_custom_weights(self, problems):
        # Emphasize only prize
        weights = {
            "vulnerability": 0.0,
            "avg_tag_solve_rate": 0.0,
            "oeis_bridge_ratio": 0.0,
            "best_pair_rate": 0.0,
            "cascade_potential": 0.0,
            "prize_signal": 1.0,
            "near_miss": 0.0,
            "max_tag_solve_rate": 0.0,
            "not_formalized": 0.0,
            "oeis_count": 0.0,
        }
        result = compute_opportunity_scores(problems, weights=weights)
        # Top should have highest prize
        top = result[0]
        assert top["prize"] > 0

    def test_covers_all_open(self, problems, scored):
        open_count = sum(1 for p in problems if p.get("status", {}).get("state") == "open")
        assert len(scored) == open_count


class TestOpportunityTiers:
    """Test tier classification."""

    def test_returns_dict(self, scored):
        tiers = opportunity_tiers(scored)
        assert isinstance(tiers, dict)

    def test_has_all_tiers(self, scored):
        tiers = opportunity_tiers(scored)
        assert "platinum" in tiers
        assert "gold" in tiers
        assert "silver" in tiers
        assert "bronze" in tiers

    def test_tier_sizes_sum(self, scored):
        tiers = opportunity_tiers(scored)
        total = sum(len(t) for t in tiers.values())
        assert total == len(scored)

    def test_platinum_best(self, scored):
        tiers = opportunity_tiers(scored)
        if tiers["platinum"] and tiers["bronze"]:
            plat_avg = sum(t["opportunity_score"] for t in tiers["platinum"]) / len(tiers["platinum"])
            bronze_avg = sum(t["opportunity_score"] for t in tiers["bronze"]) / len(tiers["bronze"])
            assert plat_avg > bronze_avg

    def test_platinum_small(self, scored):
        tiers = opportunity_tiers(scored)
        assert len(tiers["platinum"]) <= max(int(len(scored) * 0.06), 2)


class TestTagOpportunities:
    """Test tag-level opportunity analysis."""

    def test_returns_list(self, scored):
        result = tag_opportunities(scored)
        assert isinstance(result, list)

    def test_has_tags(self, scored):
        result = tag_opportunities(scored)
        assert len(result) > 5

    def test_sorted_by_avg_opportunity(self, scored):
        result = tag_opportunities(scored)
        for i in range(len(result) - 1):
            assert result[i]["avg_opportunity"] >= result[i + 1]["avg_opportunity"] - 1e-6

    def test_fields(self, scored):
        result = tag_opportunities(scored)
        for t in result:
            assert "tag" in t
            assert "avg_opportunity" in t
            assert "open_count" in t
            assert "total_prize" in t

    def test_avg_opportunity_bounded(self, scored):
        result = tag_opportunities(scored)
        for t in result:
            assert 0.0 <= t["avg_opportunity"] <= 1.0

    def test_open_count_positive(self, scored):
        result = tag_opportunities(scored)
        for t in result:
            assert t["open_count"] >= 3  # filtered < 3


class TestSignalContributions:
    """Test signal contribution analysis."""

    def test_returns_dict(self, scored):
        result = signal_contributions(scored)
        assert isinstance(result, dict)

    def test_has_stats(self, scored):
        result = signal_contributions(scored)
        assert "signal_stats" in result
        assert len(result["signal_stats"]) > 0

    def test_correlation_bounded(self, scored):
        result = signal_contributions(scored)
        for s in result["signal_stats"]:
            assert -1.01 <= s["correlation"] <= 1.01

    def test_dominant_signals(self, scored):
        result = signal_contributions(scored)
        assert "dominant_signals" in result

    def test_sorted_by_abs_correlation(self, scored):
        result = signal_contributions(scored)
        stats = result["signal_stats"]
        for i in range(len(stats) - 1):
            assert abs(stats[i]["correlation"]) >= abs(stats[i + 1]["correlation"]) - 1e-6


class TestPrizeWeighted:
    """Test prize-weighted ranking."""

    def test_returns_list(self, scored):
        result = prize_weighted_ranking(scored)
        assert isinstance(result, list)

    def test_only_prize_problems(self, scored):
        result = prize_weighted_ranking(scored)
        for item in result:
            assert item["prize"] > 0

    def test_sorted_by_ev(self, scored):
        result = prize_weighted_ranking(scored)
        for i in range(len(result) - 1):
            assert result[i]["prize_ev"] >= result[i + 1]["prize_ev"] - 1e-6

    def test_ev_positive(self, scored):
        result = prize_weighted_ranking(scored)
        for item in result:
            assert item["prize_ev"] > 0

    def test_ev_bounded(self, scored):
        result = prize_weighted_ranking(scored)
        for item in result:
            assert item["prize_ev"] <= item["prize"]  # EV ≤ prize (score ≤ 1)


class TestResearchPortfolio:
    """Test portfolio optimization."""

    def test_returns_dict(self, scored):
        result = research_portfolio(scored)
        assert isinstance(result, dict)

    def test_portfolio_size(self, scored):
        result = research_portfolio(scored)
        assert len(result["portfolio"]) == 10

    def test_custom_budget(self, scored):
        result = research_portfolio(scored, budget=5)
        assert len(result["portfolio"]) == 5

    def test_topic_diversity(self, scored):
        result = research_portfolio(scored)
        assert result["n_topics"] > 5  # should cover diverse topics

    def test_total_score_positive(self, scored):
        result = research_portfolio(scored)
        assert result["total_score"] > 0

    def test_portfolio_problems_unique(self, scored):
        result = research_portfolio(scored)
        numbers = [p["number"] for p in result["portfolio"]]
        assert len(numbers) == len(set(numbers))

    def test_topic_coverage_set(self, scored):
        result = research_portfolio(scored)
        assert isinstance(result["topic_coverage"], list)
        assert len(result["topic_coverage"]) == result["n_topics"]
