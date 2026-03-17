"""Tests for saliency_scanner.py -- critical threshold problem detection."""

import math
import pytest
import numpy as np
from pathlib import Path

import saliency_scanner as ss


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def problems():
    """Load the full problems database (cached per module)."""
    return ss.load_problems()


@pytest.fixture(scope="module")
def stats(problems):
    """Precomputed tag stats."""
    return ss._build_tag_stats(problems)


@pytest.fixture(scope="module")
def near_resolved(problems, stats):
    return ss.near_resolved_problems(problems, stats)


@pytest.fixture(scope="module")
def gap(problems, stats):
    return ss.gap_analysis(problems, stats)


@pytest.fixture(scope="module")
def bottlenecks(problems, stats):
    return ss.technique_bottlenecks(problems, stats)


@pytest.fixture(scope="module")
def bridges(problems, stats):
    return ss.cross_field_bridges(problems, stats)


@pytest.fixture(scope="module")
def top10(problems, near_resolved, gap, bottlenecks, bridges, stats):
    return ss.ensemble_predict_next_10(
        problems, near_resolved, gap, bottlenecks, bridges, stats
    )


# ═══════════════════════════════════════════════════════════════════
# Helper function tests
# ═══════════════════════════════════════════════════════════════════

class TestHelpers:
    def test_load_problems_nonempty(self, problems):
        assert len(problems) > 1000

    def test_oeis_numeric_parsing(self):
        assert ss._oeis_numeric("A387053") == 387053
        assert ss._oeis_numeric("A000001") == 1
        assert ss._oeis_numeric("not-oeis") == 0

    def test_oeis_recency_score_new(self):
        """A387xxx should score 1.0 (2025 tier)."""
        assert ss._oeis_recency_score("A387053") == 1.0

    def test_oeis_recency_score_old(self):
        """A000001 should score 0.0 (below threshold)."""
        assert ss._oeis_recency_score("A000001") == 0.0

    def test_oeis_recency_score_mid(self):
        """A360xxx should score 0.55 (early 2024)."""
        assert ss._oeis_recency_score("A360000") == 0.55

    def test_oeis_recency_tiers_monotone(self):
        """Higher OEIS IDs should have equal or higher recency scores."""
        scores = [
            ss._oeis_recency_score(f"A{n:06d}")
            for n in [100000, 350000, 360000, 370000, 380000, 387000]
        ]
        for i in range(1, len(scores)):
            assert scores[i] >= scores[i - 1], \
                f"Recency not monotone: {scores[i-1]} > {scores[i]}"

    def test_real_oeis_filters(self):
        """_real_oeis filters out N/A, possible, and bogus entries."""
        p = {"oeis": ["A123456", "N/A", "possible", "", "A000001"]}
        result = ss._real_oeis(p)
        assert "N/A" not in result
        assert "possible" not in result
        assert "" not in result
        assert "A123456" in result

    def test_real_oeis_empty(self):
        assert ss._real_oeis({}) == []
        assert ss._real_oeis({"oeis": None}) == []

    def test_number_int_and_str(self):
        """Problem numbers can be int or string in YAML."""
        assert ss._number({"number": 42}) == 42
        assert ss._number({"number": "42"}) == 42
        assert ss._number({}) == 0

    def test_prize_parsing(self):
        assert ss._prize({"prize": "$500"}) == 500.0
        assert ss._prize({"prize": "no"}) == 0.0
        assert ss._prize({}) == 0.0

    def test_status_helpers(self):
        assert ss._is_open({"status": {"state": "open"}})
        assert not ss._is_open({"status": {"state": "proved"}})
        assert ss._is_solved({"status": {"state": "proved"}})
        assert ss._is_solved({"status": {"state": "proved (Lean)"}})
        assert not ss._is_solved({"status": {"state": "open"}})


# ═══════════════════════════════════════════════════════════════════
# Tag stats tests
# ═══════════════════════════════════════════════════════════════════

class TestTagStats:
    def test_tag_solve_rate_bounded(self, stats):
        """All tag solve rates should be in [0, 1]."""
        for tag, rate in stats["tag_solve_rate"].items():
            assert 0.0 <= rate <= 1.0, f"Tag {tag} has invalid rate {rate}"

    def test_known_tags_present(self, stats):
        """Common tags should appear in the stats."""
        for tag in ["number theory", "graph theory", "ramsey theory"]:
            assert tag in stats["tag_total"]
            assert stats["tag_total"][tag] > 10

    def test_oeis_maps_consistent(self, stats):
        """oeis_to_solved <= oeis_to_total for every sequence."""
        for seq in stats["oeis_to_total"]:
            assert stats["oeis_to_solved"].get(seq, 0) <= stats["oeis_to_total"][seq]

    def test_pair_solve_rate_bounded(self, stats):
        for pair, rate in stats["pair_solve_rate"].items():
            assert 0.0 <= rate <= 1.0, f"Pair {pair} has invalid rate {rate}"


# ═══════════════════════════════════════════════════════════════════
# 1. Near-resolved problems
# ═══════════════════════════════════════════════════════════════════

class TestNearResolved:
    def test_returns_list(self, near_resolved):
        assert isinstance(near_resolved, list)

    def test_nonempty(self, near_resolved):
        """There should be multiple open problems with recent OEIS."""
        assert len(near_resolved) >= 10

    def test_sorted_by_score(self, near_resolved):
        scores = [r["near_resolved_score"] for r in near_resolved]
        assert scores == sorted(scores, reverse=True)

    def test_all_open(self, near_resolved, problems):
        """All returned problems should be open."""
        open_nums = {ss._number(p) for p in problems if ss._is_open(p)}
        for r in near_resolved:
            assert r["number"] in open_nums, \
                f"Problem #{r['number']} is not open"

    def test_all_have_recent_oeis(self, near_resolved):
        for r in near_resolved:
            assert len(r["recent_oeis"]) > 0
            # At least one OEIS ID should be >= A350000
            assert any(
                ss._oeis_numeric(s) >= ss.OEIS_RECENT_THRESHOLD
                for s in r["recent_oeis"]
            )

    def test_score_positive(self, near_resolved):
        for r in near_resolved:
            assert r["near_resolved_score"] > 0

    def test_required_fields(self, near_resolved):
        required = {"number", "tags", "prize", "recent_oeis", "all_oeis",
                     "max_recency", "n_recent_oeis", "near_resolved_score",
                     "avg_tag_tractability", "n_oeis_connections"}
        for r in near_resolved:
            assert required <= set(r.keys()), \
                f"Missing fields: {required - set(r.keys())}"

    def test_max_recency_bounded(self, near_resolved):
        for r in near_resolved:
            assert 0.0 < r["max_recency"] <= 1.0

    def test_top_result_score_reasonable(self, near_resolved):
        """Top score should be nontrivially high."""
        assert near_resolved[0]["near_resolved_score"] > 0.3


# ═══════════════════════════════════════════════════════════════════
# 2. Gap analysis (frontier problems)
# ═══════════════════════════════════════════════════════════════════

class TestGapAnalysis:
    def test_returns_dict(self, gap):
        assert "frontier_by_tag" in gap
        assert "all_frontiers" in gap

    def test_all_frontiers_nonempty(self, gap):
        assert len(gap["all_frontiers"]) > 100

    def test_sorted_by_frontier_score(self, gap):
        scores = [f["frontier_score"] for f in gap["all_frontiers"]]
        assert scores == sorted(scores, reverse=True)

    def test_frontier_score_bounded(self, gap):
        for f in gap["all_frontiers"]:
            assert 0.0 <= f["frontier_score"] <= 1.0, \
                f"Problem #{f['number']} has frontier score {f['frontier_score']}"

    def test_frontier_by_tag_covers_major_tags(self, gap):
        """Major tags should have a frontier problem."""
        for tag in ["number theory", "graph theory", "geometry"]:
            assert tag in gap["frontier_by_tag"], \
                f"No frontier problem for tag '{tag}'"

    def test_frontier_problem_is_open(self, gap, problems):
        open_nums = {ss._number(p) for p in problems if ss._is_open(p)}
        for f in gap["all_frontiers"][:50]:
            assert f["number"] in open_nums

    def test_top_k_density_bounded(self, gap):
        for f in gap["all_frontiers"]:
            assert 0.0 <= f["top_k_solved_density"] <= 1.0

    def test_required_fields(self, gap):
        required = {"number", "tags", "frontier_score",
                     "top_k_solved_density", "avg_tag_solve_rate",
                     "n_solved_neighbours"}
        for f in gap["all_frontiers"][:10]:
            assert required <= set(f.keys())


# ═══════════════════════════════════════════════════════════════════
# 3. Technique bottlenecks
# ═══════════════════════════════════════════════════════════════════

class TestTechniqueBottlenecks:
    def test_returns_dict(self, bottlenecks):
        assert "clusters" in bottlenecks
        assert "bottleneck_sizes" in bottlenecks
        assert "leverage_ranking" in bottlenecks

    def test_clusters_nonempty(self, bottlenecks):
        assert len(bottlenecks["clusters"]) >= 5, \
            "Should have at least 5 technique families"

    def test_all_families_recognized(self, bottlenecks):
        """All cluster keys should be known technique families."""
        for family in bottlenecks["clusters"]:
            assert family in ss.TECHNIQUE_SIGNATURES

    def test_cluster_members_are_open(self, bottlenecks, problems):
        open_nums = {ss._number(p) for p in problems if ss._is_open(p)}
        for family, members in bottlenecks["clusters"].items():
            for m in members[:10]:
                assert m["number"] in open_nums

    def test_leverage_ranking_sorted(self, bottlenecks):
        counts = [c for _, c in bottlenecks["leverage_ranking"]]
        assert counts == sorted(counts, reverse=True)

    def test_bottleneck_sizes_sum(self, bottlenecks):
        """Total problems across all clusters should not exceed open problems."""
        total = sum(bottlenecks["bottleneck_sizes"].values())
        # Some open problems may not classify into any bottleneck
        # (e.g., no matching tags), so total <= 650
        assert total <= 700

    def test_sieve_is_largest_bottleneck(self, bottlenecks):
        """Sieve methods should be the largest cluster (number theory dominant)."""
        ranking = bottlenecks["leverage_ranking"]
        # sieve_methods should be in top 2
        top_families = [f for f, _ in ranking[:2]]
        assert "sieve_methods" in top_families

    def test_shared_pairs_structure(self, bottlenecks):
        for sp in bottlenecks["shared_pairs"]:
            assert "problems" in sp
            assert len(sp["problems"]) == 2
            assert sp["shared_bottleneck"] in ss.TECHNIQUE_SIGNATURES

    def test_classify_bottleneck_no_tags(self):
        """Empty tags should return empty classification."""
        assert ss._classify_bottleneck(set()) == []

    def test_classify_bottleneck_known(self):
        """Ramsey theory tag should classify as ramsey_partition."""
        result = ss._classify_bottleneck({"ramsey theory"})
        families = [f for f, _ in result]
        assert "ramsey_partition" in families

    def test_classify_returns_sorted(self):
        result = ss._classify_bottleneck(
            {"graph theory", "ramsey theory", "combinatorics"}
        )
        scores = [s for _, s in result]
        assert scores == sorted(scores, reverse=True)


# ═══════════════════════════════════════════════════════════════════
# 4. Cross-field bridges
# ═══════════════════════════════════════════════════════════════════

class TestCrossFieldBridges:
    def test_returns_list(self, bridges):
        assert isinstance(bridges, list)

    def test_nonempty(self, bridges):
        assert len(bridges) >= 20

    def test_sorted_by_score(self, bridges):
        scores = [b["cross_field_score"] for b in bridges]
        assert scores == sorted(scores, reverse=True)

    def test_all_open(self, bridges, problems):
        open_nums = {ss._number(p) for p in problems if ss._is_open(p)}
        for b in bridges[:20]:
            assert b["number"] in open_nums

    def test_has_bridge_pair(self, bridges):
        for b in bridges[:20]:
            assert b["best_bridge_pair"] is not None
            assert len(b["best_bridge_pair"]) == 2

    def test_bridge_details_sorted(self, bridges):
        for b in bridges[:10]:
            if len(b["bridge_details"]) >= 2:
                scores = [d["bridge_score"] for d in b["bridge_details"]]
                assert scores == sorted(scores, reverse=True)

    def test_problem_883_is_bridge(self, bridges):
        """#883 (graph theory + number theory) should appear as a bridge."""
        nums = {b["number"] for b in bridges}
        assert 883 in nums, "#883 should be identified as a cross-field bridge"

    def test_score_positive(self, bridges):
        for b in bridges:
            assert b["cross_field_score"] >= 0

    def test_required_fields(self, bridges):
        required = {"number", "tags", "best_bridge_pair",
                     "best_bridge_score", "bridge_details",
                     "avg_tag_tractability", "cross_field_score"}
        for b in bridges[:5]:
            assert required <= set(b.keys())


# ═══════════════════════════════════════════════════════════════════
# 5. Ensemble prediction
# ═══════════════════════════════════════════════════════════════════

class TestEnsemblePrediction:
    def test_returns_10(self, top10):
        assert len(top10) == 10

    def test_sorted_by_ensemble_score(self, top10):
        scores = [t["ensemble_score"] for t in top10]
        assert scores == sorted(scores, reverse=True)

    def test_all_open(self, top10, problems):
        open_nums = {ss._number(p) for p in problems if ss._is_open(p)}
        for t in top10:
            assert t["number"] in open_nums

    def test_ensemble_score_bounded(self, top10):
        for t in top10:
            assert 0.0 <= t["ensemble_score"] <= 1.5, \
                f"#{t['number']} has score {t['ensemble_score']}"

    def test_has_explanation(self, top10):
        for t in top10:
            assert isinstance(t["why"], str)
            assert len(t["why"]) > 10

    def test_has_technique_suggestion(self, top10):
        for t in top10:
            assert isinstance(t["technique_suggestion"], str)
            assert len(t["technique_suggestion"]) > 3

    def test_signals_dict_complete(self, top10):
        expected_signals = {
            "knn_probability", "near_resolved", "frontier_proximity",
            "survival_hazard", "cross_field_bridge", "bottleneck_relevance",
            "prize_signal", "formalization",
        }
        for t in top10:
            assert expected_signals <= set(t["signals"].keys())

    def test_dominant_signal_is_highest(self, top10):
        """The dominant signal should be the one with the highest value."""
        for t in top10:
            dom_name = t["dominant_signal"]
            dom_val = t["dominant_value"]
            max_val = max(t["signals"].values())
            assert abs(dom_val - max_val) < 1e-10, \
                f"#{t['number']}: dominant {dom_name}={dom_val} != max {max_val}"

    def test_required_fields(self, top10):
        required = {"number", "tags", "prize", "formalized",
                     "ensemble_score", "signals", "dominant_signal",
                     "dominant_value", "technique_suggestion", "why"}
        for t in top10:
            assert required <= set(t.keys())

    def test_unique_problems(self, top10):
        nums = [t["number"] for t in top10]
        assert len(set(nums)) == 10, "Top 10 should be 10 distinct problems"


# ═══════════════════════════════════════════════════════════════════
# Survival hazard
# ═══════════════════════════════════════════════════════════════════

class TestSurvivalHazard:
    def test_hazard_nonnegative(self):
        """Hazard should always be >= 0."""
        for num in [1, 100, 500, 1000, 1200]:
            p = {"number": num, "status": {"state": "open", "last_update": "2025-08-31"}}
            h = ss._survival_hazard_score(p, 1200)
            assert h >= 0.0, f"Problem #{num} has negative hazard {h}"

    def test_recent_update_boosts_hazard(self):
        old = {"number": 500, "status": {"state": "open", "last_update": "2025-08-31"}}
        new = {"number": 500, "status": {"state": "open", "last_update": "2026-03-14"}}
        h_old = ss._survival_hazard_score(old, 1200)
        h_new = ss._survival_hazard_score(new, 1200)
        assert h_new > h_old, "Recent update should boost hazard"

    def test_middle_problems_higher_hazard(self):
        """Problems in the middle of the catalogue should have higher base hazard."""
        low = {"number": 10, "status": {"state": "open", "last_update": "2025-08-31"}}
        mid = {"number": 600, "status": {"state": "open", "last_update": "2025-08-31"}}
        high = {"number": 1180, "status": {"state": "open", "last_update": "2025-08-31"}}
        h_mid = ss._survival_hazard_score(mid, 1200)
        h_low = ss._survival_hazard_score(low, 1200)
        h_high = ss._survival_hazard_score(high, 1200)
        assert h_mid > h_low
        assert h_mid > h_high


# ═══════════════════════════════════════════════════════════════════
# KNN probabilities
# ═══════════════════════════════════════════════════════════════════

class TestKNNProbabilities:
    def test_all_open_have_probabilities(self, problems, stats):
        knn = ss._build_knn_probabilities(problems, stats)
        open_nums = {ss._number(p) for p in problems if ss._is_open(p)}
        for num in open_nums:
            assert num in knn, f"#{num} missing from KNN probabilities"

    def test_probabilities_bounded(self, problems, stats):
        knn = ss._build_knn_probabilities(problems, stats)
        for num, prob in knn.items():
            assert 0.0 <= prob <= 1.0, f"#{num} has probability {prob}"


# ═══════════════════════════════════════════════════════════════════
# Report generation
# ═══════════════════════════════════════════════════════════════════

class TestReportGeneration:
    def test_report_generates(self, problems):
        report = ss.generate_report(problems)
        assert isinstance(report, str)
        assert len(report) > 1000

    def test_report_has_sections(self, problems):
        report = ss.generate_report(problems)
        assert "## 1. Near-Resolved Problems" in report
        assert "## 2. Frontier Problems" in report
        assert "## 3. Technique Bottlenecks" in report
        assert "## 4. Cross-Field Bridge Problems" in report
        assert "## 5. PREDICTION: Next 10 Problems" in report

    def test_report_file_exists(self):
        """After running main, the report file should exist."""
        report_path = ss.REPORT_PATH
        assert report_path.exists()


# ═══════════════════════════════════════════════════════════════════
# Edge cases and integration
# ═══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_empty_problems_list(self):
        """All analyses should handle empty input gracefully."""
        result = ss.near_resolved_problems([], ss._build_tag_stats([]))
        assert result == []

    def test_single_problem(self):
        """Should handle a single open problem."""
        single = [{
            "number": "999",
            "status": {"state": "open", "last_update": "2025-08-31"},
            "tags": ["number theory"],
            "oeis": ["A387053"],
            "prize": "no",
            "formalized": {"state": "no", "last_update": "2025-08-31"},
        }]
        stats = ss._build_tag_stats(single)
        nr = ss.near_resolved_problems(single, stats)
        assert len(nr) == 1
        assert nr[0]["number"] == 999

    def test_no_oeis_problem_excluded_from_near_resolved(self):
        """Problems without OEIS should not appear in near-resolved."""
        probs = [{
            "number": "100",
            "status": {"state": "open"},
            "tags": ["geometry"],
            "oeis": [],
            "prize": "no",
            "formalized": {"state": "no"},
        }]
        stats = ss._build_tag_stats(probs)
        nr = ss.near_resolved_problems(probs, stats)
        assert len(nr) == 0

    def test_single_tag_problem_no_bridge(self):
        """Single-tag problems can't have bridge pairs."""
        probs = [{
            "number": "100",
            "status": {"state": "open"},
            "tags": ["geometry"],
            "oeis": [],
            "prize": "no",
            "formalized": {"state": "no"},
        }]
        stats = ss._build_tag_stats(probs)
        br = ss.cross_field_bridges(probs, stats)
        assert len(br) == 0


# ═══════════════════════════════════════════════════════════════════
# Cross-validation: known properties
# ═══════════════════════════════════════════════════════════════════

class TestKnownProperties:
    def test_problem_1_is_fourier_bottleneck(self, bottlenecks):
        """Problem #1 (Erdos-Turan conjecture) should be in fourier_analytic."""
        fourier_nums = {
            m["number"]
            for m in bottlenecks["clusters"].get("fourier_analytic", [])
        }
        assert 1 in fourier_nums, \
            "#1 should be classified under fourier_analytic"

    def test_problem_3_in_density_increment(self, bottlenecks):
        """Problem #3 (arithmetic progressions) should involve density_increment."""
        p3 = None
        for family, members in bottlenecks["clusters"].items():
            for m in members:
                if m["number"] == 3:
                    p3 = m
                    break
        assert p3 is not None, "#3 should appear in some bottleneck"
        # It should have density_increment as primary or secondary
        has_density = (
            p3["primary_bottleneck"] == "density_increment"
            or p3.get("secondary_bottleneck") == "density_increment"
        )
        assert has_density, f"#3 bottleneck is {p3['primary_bottleneck']}"

    def test_geometry_problems_are_topological(self, bottlenecks, problems):
        """Geometry-only problems should classify as topological_geometric."""
        geo_only = [
            ss._number(p) for p in problems
            if ss._is_open(p) and ss._tags(p) == {"geometry"}
        ]
        topo_nums = {
            m["number"]
            for m in bottlenecks["clusters"].get("topological_geometric", [])
        }
        # At least some geometry-only problems should be in this cluster
        overlap = set(geo_only) & topo_nums
        assert len(overlap) > 0 or len(geo_only) == 0, \
            "Geometry-only problems should classify as topological_geometric"

    def test_near_resolved_includes_multi_oeis(self, near_resolved):
        """Problems with 3+ recent OEIS should appear high in near-resolved."""
        multi_oeis = [r for r in near_resolved if r["n_recent_oeis"] >= 3]
        assert len(multi_oeis) > 0, "Expected some problems with 3+ recent OEIS"
        # They should generally score higher than single-OEIS problems
        multi_scores = [r["near_resolved_score"] for r in multi_oeis]
        avg_multi = sum(multi_scores) / len(multi_scores)
        avg_all = sum(r["near_resolved_score"] for r in near_resolved) / len(near_resolved)
        assert avg_multi >= avg_all, \
            "Multi-OEIS problems should score at or above average"
