"""Tests for attack_surface.py — concrete attack strategy analysis."""
import pytest

from attack_surface import (
    load_problems,
    technique_arsenal,
    prerequisite_chains,
    status_proximity,
    prize_portfolio,
    cascade_simulator,
    attack_plans,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


class TestTechniqueArsenal:
    """Test technique combination effectiveness."""

    def test_returns_dict(self, problems):
        result = technique_arsenal(problems)
        assert isinstance(result, dict)

    def test_has_pairs(self, problems):
        result = technique_arsenal(problems)
        assert len(result["effective_pairs"]) > 0

    def test_pair_fields(self, problems):
        result = technique_arsenal(problems)
        for p in result["effective_pairs"]:
            assert "technique" in p
            assert "solve_rate" in p
            assert "solved_count" in p
            assert "total_count" in p

    def test_solve_rate_bounded(self, problems):
        result = technique_arsenal(problems)
        for p in result["effective_pairs"]:
            assert 0.0 <= p["solve_rate"] <= 1.0

    def test_sorted_by_effectiveness(self, problems):
        result = technique_arsenal(problems)
        pairs = result["effective_pairs"]
        for i in range(len(pairs) - 1):
            assert pairs[i]["solve_rate"] >= pairs[i + 1]["solve_rate"]

    def test_tag_effectiveness(self, problems):
        result = technique_arsenal(problems)
        assert len(result["tag_effectiveness"]) > 0
        for t in result["tag_effectiveness"]:
            assert 0.0 <= t["solve_rate"] <= 1.0


class TestPrerequisiteChains:
    """Test OEIS-linked prerequisite chain detection."""

    def test_returns_list(self, problems):
        chains = prerequisite_chains(problems)
        assert isinstance(chains, list)

    def test_chain_fields(self, problems):
        chains = prerequisite_chains(problems)
        for c in chains:
            assert "target" in c
            assert "prerequisites" in c
            assert "chain_strength" in c

    def test_prerequisites_have_numbers(self, problems):
        chains = prerequisite_chains(problems)
        for c in chains:
            for p in c["prerequisites"]:
                assert "number" in p

    def test_sorted_by_strength(self, problems):
        chains = prerequisite_chains(problems)
        for i in range(len(chains) - 1):
            assert chains[i]["chain_strength"] >= chains[i + 1]["chain_strength"]


class TestStatusProximity:
    """Test near-miss status analysis."""

    def test_returns_dict(self, problems):
        result = status_proximity(problems)
        assert isinstance(result, dict)

    def test_has_categories(self, problems):
        result = status_proximity(problems)
        assert "falsifiable" in result["near_miss"]
        assert "verifiable" in result["near_miss"]
        assert "decidable" in result["near_miss"]

    def test_falsifiable_count(self, problems):
        result = status_proximity(problems)
        assert len(result["near_miss"]["falsifiable"]) == 31

    def test_verifiable_count(self, problems):
        result = status_proximity(problems)
        assert len(result["near_miss"]["verifiable"]) == 7

    def test_decidable_count(self, problems):
        result = status_proximity(problems)
        assert len(result["near_miss"]["decidable"]) == 8

    def test_lean_coverage(self, problems):
        result = status_proximity(problems)
        assert result["lean_proved_count"] > 0


class TestPrizePortfolio:
    """Test prize-weighted portfolio optimization."""

    def test_returns_dict(self, problems):
        result = prize_portfolio(problems)
        assert isinstance(result, dict)

    def test_has_portfolio(self, problems):
        result = prize_portfolio(problems)
        assert len(result["portfolio"]) > 0

    def test_portfolio_fields(self, problems):
        result = prize_portfolio(problems)
        for p in result["portfolio"]:
            assert "number" in p
            assert "prize" in p
            assert "p_solve" in p
            assert "expected_value" in p

    def test_sorted_by_ev(self, problems):
        result = prize_portfolio(problems)
        port = result["portfolio"]
        for i in range(len(port) - 1):
            assert port[i]["expected_value"] >= port[i + 1]["expected_value"]

    def test_p_solve_bounded(self, problems):
        result = prize_portfolio(problems)
        for p in result["portfolio"]:
            assert 0.0 <= p["p_solve"] <= 1.0

    def test_total_ev_positive(self, problems):
        result = prize_portfolio(problems)
        assert result["total_expected_value"] > 0


class TestCascadeSimulator:
    """Test breakthrough cascade simulation."""

    def test_returns_list(self, problems):
        cascades = cascade_simulator(problems)
        assert isinstance(cascades, list)

    def test_cascade_fields(self, problems):
        cascades = cascade_simulator(problems)
        for c in cascades:
            assert "number" in c
            assert "problems_unlocked" in c
            assert "tag_boosts" in c
            assert "oeis_connected" in c

    def test_custom_targets(self, problems):
        cascades = cascade_simulator(problems, target_numbers=[39, 74])
        nums = {c["number"] for c in cascades}
        assert 39 in nums or 74 in nums

    def test_unlocked_nonneg(self, problems):
        cascades = cascade_simulator(problems)
        for c in cascades:
            assert c["problems_unlocked"] >= 0

    def test_sorted_by_unlocked(self, problems):
        cascades = cascade_simulator(problems)
        for i in range(len(cascades) - 1):
            assert cascades[i]["problems_unlocked"] >= cascades[i + 1]["problems_unlocked"]


class TestAttackPlans:
    """Test detailed attack plan generation."""

    def test_returns_list(self, problems):
        plans = attack_plans(problems)
        assert isinstance(plans, list)

    def test_plan_fields(self, problems):
        plans = attack_plans(problems)
        for p in plans:
            assert "number" in p
            assert "vulnerability" in p
            assert "risk" in p
            assert "approach_angles" in p
            assert "solved_similar" in p

    def test_risk_categories(self, problems):
        plans = attack_plans(problems)
        for p in plans:
            assert p["risk"] in ("low", "moderate", "high")

    def test_vulnerability_bounded(self, problems):
        plans = attack_plans(problems)
        for p in plans:
            assert 0.0 <= p["vulnerability"] <= 1.0

    def test_custom_targets(self, problems):
        plans = attack_plans(problems, target_numbers=[883])
        assert any(p["number"] == 883 for p in plans)
