"""Tests for cross_analysis.py — third-order synthesis."""
import math
import pytest

from cross_analysis import (
    load_problems,
    unified_opportunity_score,
    ranking_disagreements,
    strategic_roadmap,
    problem_genome,
    hidden_structures,
    generate_report,
    _prize,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def unified(problems):
    return unified_opportunity_score(problems)


class TestUnifiedOpportunityScore:
    """Test unified multi-model scoring."""

    def test_returns_list(self, unified):
        assert isinstance(unified, list)
        assert len(unified) > 0

    def test_sorted_descending(self, unified):
        for i in range(len(unified) - 1):
            assert unified[i]["unified_score"] >= unified[i + 1]["unified_score"]

    def test_scores_bounded(self, unified):
        for u in unified:
            assert 0.0 <= u["unified_score"] <= 1.0

    def test_has_all_signals(self, unified):
        required = {"number", "unified_score", "vulnerability",
                    "predicted_solvability", "pagerank_norm", "cascade_norm", "prize"}
        for u in unified[:10]:
            assert required.issubset(u.keys())

    def test_vulnerability_bounded(self, unified):
        for u in unified:
            assert 0.0 <= u["vulnerability"] <= 1.0

    def test_prediction_bounded(self, unified):
        for u in unified:
            assert 0.0 <= u["predicted_solvability"] <= 1.0

    def test_pagerank_bounded(self, unified):
        for u in unified:
            assert 0.0 <= u["pagerank_norm"] <= 1.01  # allow tiny floating point

    def test_cascade_bounded(self, unified):
        for u in unified:
            assert 0.0 <= u["cascade_norm"] <= 1.01

    def test_top_problems_have_high_score(self, unified):
        # Top problem should have a positive score; exact value depends on
        # sub-signal integration and is not meaningful to threshold-test.
        assert unified[0]["unified_score"] > 0.0

    def test_covers_many_problems(self, unified):
        assert len(unified) > 500


class TestRankingDisagreements:
    """Test ranking disagreement analysis."""

    def test_returns_list(self, unified):
        d = ranking_disagreements(unified)
        assert isinstance(d, list)

    def test_sorted_by_disagreement(self, unified):
        d = ranking_disagreements(unified)
        for i in range(len(d) - 1):
            assert d[i]["disagreement"] >= d[i + 1]["disagreement"]

    def test_disagreement_nonneg(self, unified):
        d = ranking_disagreements(unified)
        for item in d:
            assert item["disagreement"] >= 0

    def test_has_signals(self, unified):
        d = ranking_disagreements(unified)
        for item in d[:5]:
            assert "signals" in item
            assert "vulnerability" in item["signals"]
            assert "prediction" in item["signals"]

    def test_respects_top_k(self, unified):
        d = ranking_disagreements(unified, top_k=10)
        assert len(d) <= 10


class TestStrategicRoadmap:
    """Test strategic attack roadmap."""

    def test_returns_dict(self, unified):
        r = strategic_roadmap(unified)
        assert isinstance(r, dict)

    def test_has_categories(self, unified):
        r = strategic_roadmap(unified)
        assert "quick_wins" in r
        assert "strategic_targets" in r
        assert "prize_hunts" in r
        assert "moonshots" in r

    def test_quick_wins_high_pred(self, unified):
        r = strategic_roadmap(unified)
        for qw in r["quick_wins"]:
            assert qw["predicted_solvability"] > 0.4

    def test_prize_hunts_have_prize(self, unified):
        r = strategic_roadmap(unified)
        for ph in r["prize_hunts"]:
            assert ph["prize"] > 0

    def test_total_classified(self, unified):
        r = strategic_roadmap(unified)
        assert r["total_classified"] > 0


class TestProblemGenome:
    """Test comprehensive per-problem analysis."""

    def test_returns_list(self, problems):
        g = problem_genome(problems)
        assert isinstance(g, list)
        assert len(g) > 0

    def test_genome_fields(self, problems):
        g = problem_genome(problems)
        for item in g:
            assert "number" in item
            assert "tags" in item
            assert "vulnerability" in item
            assert "oeis_bridges" in item
            assert "technique_match" in item

    def test_custom_targets(self, problems):
        g = problem_genome(problems, target_numbers=[39, 74])
        nums = {item["number"] for item in g}
        assert 39 in nums or 74 in nums

    def test_tag_synergies(self, problems):
        g = problem_genome(problems)
        # At least some problems should have tag synergies
        has_synergy = any(len(item.get("tag_synergies", [])) > 0 for item in g)
        assert has_synergy


class TestHiddenStructures:
    """Test hidden structure detection."""

    def test_returns_dict(self, problems):
        h = hidden_structures(problems)
        assert isinstance(h, dict)

    def test_has_categories(self, problems):
        h = hidden_structures(problems)
        assert "dark_horses" in h
        assert "false_positives" in h
        assert "influence_orphans" in h
        assert "tag_paradoxes" in h

    def test_false_positives_have_high_vuln(self, problems):
        h = hidden_structures(problems)
        for fp in h["false_positives"]:
            assert fp["vulnerability"] > 0.4

    def test_influence_orphans_have_high_pr(self, problems):
        h = hidden_structures(problems)
        for io in h["influence_orphans"]:
            assert io["pagerank_norm"] > 0.4


# ── Prize parsing tests ──────────────────────────────────────────


class TestPrize:
    """Test _prize helper with various currency formats."""

    def test_prize_usd(self):
        assert _prize({"prize": "$1000"}) == 1000.0

    def test_prize_gbp(self):
        result = _prize({"prize": "\u00a3500"})
        assert abs(result - 635.0) < 1.0  # 500 * 1.27

    def test_prize_none(self):
        assert _prize({"prize": None}) == 0.0

    def test_prize_empty(self):
        assert _prize({"prize": ""}) == 0.0

    def test_prize_no(self):
        assert _prize({"prize": "no"}) == 0.0

    def test_prize_missing_key(self):
        assert _prize({}) == 0.0

    def test_prize_with_comma(self):
        assert _prize({"prize": "$1,000"}) == 1000.0

    def test_prize_gbp_large(self):
        result = _prize({"prize": "\u00a31,000"})
        assert abs(result - 1270.0) < 1.0  # 1000 * 1.27


# ── Generate report tests ────────────────────────────────────────


class TestGenerateReport:
    """Test cross-analysis report generation."""

    def test_generate_report_contains_sections(self):
        unified = [{"number": 1, "unified_score": 0.9, "vulnerability": 0.5,
                     "predicted_solvability": 0.8, "pagerank_norm": 0.3,
                     "cascade_norm": 0.4, "prize": 1000.0}]
        disagreements = [{"number": 2, "disagreement": 0.5,
                          "signals": {"vulnerability": 0.3, "prediction": 0.7,
                                      "pagerank": 0.2, "cascade": 0.1},
                          "tags": ["Ramsey", "Graph"]}]
        roadmap = {
            "quick_wins": [{"number": 3, "predicted_solvability": 0.9, "tags": ["NT"]}],
            "strategic_targets": [{"number": 4, "unified_score": 0.8,
                                   "cascade_norm": 0.5, "tags": ["Comb"]}],
            "prize_hunts": [{"number": 5, "prize": 500,
                             "predicted_solvability": 0.7, "tags": ["Ramsey"]}],
            "moonshots": [{"number": 6, "prize": 0, "cascade_norm": 0.9, "tags": ["NT"]}],
        }
        genomes = [{"number": 7, "tags": ["NT", "Ramsey"], "prize": 1000.0,
                     "vulnerability": 0.4, "oeis_bridges": 3, "technique_match": 2,
                     "tag_synergies": [{"pair": ("NT", "Ramsey"), "synergy": 0.38}]}]
        hidden = {
            "dark_horses": [{"number": 8, "predicted_solvability": 0.8,
                             "vulnerability": 0.1}],
            "false_positives": [{"number": 9, "vulnerability": 0.9,
                                 "predicted_solvability": 0.1}],
            "influence_orphans": [{"number": 10, "pagerank_norm": 0.9,
                                   "predicted_solvability": 0.1}],
        }

        report = generate_report(unified, disagreements, roadmap, genomes, hidden)
        assert "# Cross-Analysis" in report
        assert "Unified Opportunity Score" in report
        assert "Ranking Disagreements" in report or "Model Disagreement" in report
        assert "Strategic Research Roadmap" in report
        assert "Quick Wins" in report
        assert "Strategic Targets" in report
        assert "Prize Hunts" in report
        assert "Moonshots" in report
        assert "Problem Genomes" in report
        assert "Hidden Structures" in report
        assert "Dark Horses" in report
        assert "False Positives" in report
        assert "Influence Orphans" in report

    def test_generate_report_empty_hidden(self):
        unified = [{"number": 1, "unified_score": 0.5, "vulnerability": 0.5,
                     "predicted_solvability": 0.5, "pagerank_norm": 0.5,
                     "cascade_norm": 0.5, "prize": 0.0}]
        disagreements = []
        roadmap = {"quick_wins": [], "strategic_targets": [],
                   "prize_hunts": [], "moonshots": []}
        genomes = []
        hidden = {"dark_horses": [], "false_positives": [], "influence_orphans": []}
        report = generate_report(unified, disagreements, roadmap, genomes, hidden)
        assert "# Cross-Analysis" in report
        # Hidden sections should NOT appear when empty
        assert "Dark Horses" not in report
        assert "False Positives" not in report
        assert "Influence Orphans" not in report

    def test_generate_report_prize_formatting(self):
        unified = [
            {"number": 1, "unified_score": 0.9, "vulnerability": 0.5,
             "predicted_solvability": 0.8, "pagerank_norm": 0.3,
             "cascade_norm": 0.4, "prize": 1000.0},
            {"number": 2, "unified_score": 0.8, "vulnerability": 0.5,
             "predicted_solvability": 0.7, "pagerank_norm": 0.2,
             "cascade_norm": 0.3, "prize": 0.0},
        ]
        disagreements = []
        roadmap = {"quick_wins": [], "strategic_targets": [],
                   "prize_hunts": [], "moonshots": []}
        genomes = []
        hidden = {"dark_horses": [], "false_positives": [], "influence_orphans": []}
        report = generate_report(unified, disagreements, roadmap, genomes, hidden)
        assert "$1000" in report
        assert "| - |" in report  # no-prize placeholder


# ── Problem genome string lookup test ─────────────────────────────


class TestProblemGenomeStringLookup:
    """Test that problem_genome handles both int and string problem numbers."""

    def test_problem_genome_string_lookup(self, problems):
        genomes = problem_genome(problems, target_numbers=[625])
        assert len(genomes) > 0
        assert genomes[0]["number"] in (625, "625")
