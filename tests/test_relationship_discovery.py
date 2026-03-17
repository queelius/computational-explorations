"""Tests for relationship_discovery.py -- Erdos problems relationship discovery engine."""
import pytest
import numpy as np
from itertools import combinations
from pathlib import Path

from relationship_discovery import (
    load_problems,
    get_status,
    get_oeis,
    is_open,
    is_solved,
    get_prize_value,
    _investigate_bridge,
    find_oeis_hidden_bridges,
    tag_gap_analysis,
    find_rare_intersections,
    build_technique_transfer_map,
    summarize_technique_transfers,
    find_structural_isomorphisms,
    summarize_isomorphisms,
    generate_novel_problems,
    generate_report,
    build_problem_genome,
    find_nearest_neighbors,
    find_surprising_neighbors,
    run_all_analyses,
    MAJOR_TAGS,
    TECHNIQUE_TAGS,
    AREA_TAGS,
)


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def problems(problems_yaml_path):
    """Load the full problems dataset."""
    if not problems_yaml_path.exists():
        pytest.skip("Problems YAML not found")
    return load_problems()


@pytest.fixture
def small_problems():
    """A small hand-crafted problem set for unit testing."""
    return [
        {
            "number": "1",
            "prize": "$500",
            "status": {"state": "open"},
            "oeis": ["A000001"],
            "formalized": {"state": "yes"},
            "tags": ["number theory", "additive combinatorics"],
        },
        {
            "number": "2",
            "prize": "no",
            "status": {"state": "proved"},
            "oeis": ["A000001"],
            "formalized": {"state": "no"},
            "tags": ["graph theory", "ramsey theory"],
        },
        {
            "number": "3",
            "prize": "$100",
            "status": {"state": "open"},
            "oeis": ["A000002"],
            "formalized": {"state": "yes"},
            "tags": ["number theory", "additive combinatorics", "arithmetic progressions"],
        },
        {
            "number": "4",
            "prize": "no",
            "status": {"state": "proved"},
            "oeis": ["A000002", "A000003"],
            "formalized": {"state": "yes"},
            "tags": ["number theory", "additive combinatorics", "arithmetic progressions"],
        },
        {
            "number": "5",
            "prize": "no",
            "status": {"state": "disproved"},
            "oeis": ["N/A"],
            "formalized": {"state": "no"},
            "tags": ["geometry", "distances"],
        },
        {
            "number": "6",
            "prize": "$1000",
            "status": {"state": "open"},
            "oeis": ["A000003"],
            "formalized": {"state": "no"},
            "tags": ["graph theory", "chromatic number"],
        },
        {
            "number": "7",
            "prize": "no",
            "status": {"state": "proved"},
            "oeis": [],
            "formalized": {"state": "yes"},
            "tags": ["analysis"],
        },
        {
            "number": "8",
            "prize": "no",
            "status": {"state": "open"},
            "oeis": ["A000004"],
            "formalized": {"state": "no"},
            "tags": ["ramsey theory", "additive combinatorics"],
        },
        {
            "number": "9",
            "prize": "no",
            "status": {"state": "solved"},
            "oeis": ["A000004"],
            "formalized": {"state": "no"},
            "tags": ["combinatorics", "discrepancy"],
        },
    ]


# ── Helper function tests ────────────────────────────────────────


class TestHelperFunctions:
    """Test basic helper functions."""

    def test_get_status_normal(self):
        p = {"status": {"state": "open"}}
        assert get_status(p) == "open"

    def test_get_status_missing(self):
        assert get_status({}) == "unknown"

    def test_get_oeis_filters_na(self):
        p = {"oeis": ["A000001", "N/A", "possible", "A000002"]}
        assert get_oeis(p) == ["A000001", "A000002"]

    def test_get_oeis_empty(self):
        assert get_oeis({"oeis": []}) == []
        assert get_oeis({}) == []

    def test_is_open(self):
        assert is_open({"status": {"state": "open"}})
        assert is_open({"status": {"state": "falsifiable"}})
        assert is_open({"status": {"state": "verifiable"}})
        assert not is_open({"status": {"state": "proved"}})
        assert not is_open({"status": {"state": "disproved"}})

    def test_is_solved(self):
        assert is_solved({"status": {"state": "proved"}})
        assert is_solved({"status": {"state": "disproved"}})
        assert is_solved({"status": {"state": "solved"}})
        assert is_solved({"status": {"state": "proved (Lean)"}})
        assert not is_solved({"status": {"state": "open"}})

    def test_get_prize_value(self):
        assert get_prize_value({"prize": "$500"}) == 500
        assert get_prize_value({"prize": "$10000"}) == 10000
        assert get_prize_value({"prize": "no"}) == 0
        assert get_prize_value({}) == 0
        assert get_prize_value({"prize": "$1,000"}) == 1000


# ── Section 1: OEIS Hidden Bridges ───────────────────────────────


class TestOEISHiddenBridges:
    """Test hidden OEIS bridge discovery."""

    def test_finds_bridges_in_small_set(self, small_problems):
        bridges = find_oeis_hidden_bridges(small_problems)
        # Problems 1 and 2 share A000001 but have NO shared tags
        assert len(bridges) > 0

    def test_bridge_has_required_fields(self, small_problems):
        bridges = find_oeis_hidden_bridges(small_problems)
        for b in bridges:
            assert "problem_1" in b
            assert "problem_2" in b
            assert "shared_oeis" in b
            assert "tags_1" in b
            assert "tags_2" in b
            assert "jaccard" in b
            assert "investigation" in b

    def test_zero_overlap_bridge(self, small_problems):
        bridges = find_oeis_hidden_bridges(small_problems)
        # Problems 1 (number theory, additive combinatorics) and 2 (graph theory, ramsey theory)
        # share A000001 but have zero tag overlap
        zero_bridges = [b for b in bridges if b["jaccard"] == 0]
        assert len(zero_bridges) >= 1
        p1_p2 = {(b["problem_1"], b["problem_2"]) for b in zero_bridges}
        assert ("1", "2") in p1_p2 or ("2", "1") in p1_p2

    def test_low_overlap_bridge(self, small_problems):
        bridges = find_oeis_hidden_bridges(small_problems, max_jaccard=0.5)
        # Should include pairs with some but low overlap
        assert all(b["jaccard"] <= 0.5 for b in bridges)

    def test_no_self_bridges(self, small_problems):
        bridges = find_oeis_hidden_bridges(small_problems)
        for b in bridges:
            assert b["problem_1"] != b["problem_2"]

    def test_full_dataset_bridges(self, problems):
        bridges = find_oeis_hidden_bridges(problems)
        assert len(bridges) >= 1
        # All bridges should have Jaccard <= 0.5
        for b in bridges:
            assert b["jaccard"] <= 0.5

    def test_stricter_threshold(self, small_problems):
        strict = find_oeis_hidden_bridges(small_problems, max_jaccard=0.0)
        loose = find_oeis_hidden_bridges(small_problems, max_jaccard=0.5)
        assert len(strict) <= len(loose)


# ── Section 2: Tag Gap Analysis ──────────────────────────────────


class TestTagGapAnalysis:
    """Test tag gap analysis."""

    def test_covers_all_major_tag_pairs(self, problems):
        gap = tag_gap_analysis(problems)
        expected_pairs = len(list(combinations(MAJOR_TAGS, 2)))
        assert len(gap) == expected_pairs

    def test_gap_has_required_fields(self, problems):
        gap = tag_gap_analysis(problems)
        for pair_key, data in gap.items():
            assert "count" in data
            assert "problems" in data
            assert "bridging_subtopics" in data
            assert "missing_bridges" in data
            assert "category_1_size" in data
            assert "category_2_size" in data

    def test_intersection_count_nonnegative(self, problems):
        gap = tag_gap_analysis(problems)
        for data in gap.values():
            assert data["count"] >= 0

    def test_known_large_intersection(self, problems):
        gap = tag_gap_analysis(problems)
        # graph theory x ramsey theory should have many problems
        key = "graph theory x ramsey theory"
        assert gap[key]["count"] > 50

    def test_known_empty_intersection(self, problems):
        gap = tag_gap_analysis(problems)
        # geometry x additive combinatorics should have 0 or very few
        key = "geometry x additive combinatorics"
        assert gap[key]["count"] <= 2

    def test_rare_intersections(self, problems):
        gap = tag_gap_analysis(problems)
        rare = find_rare_intersections(gap)
        assert len(rare) > 0
        # All rare should have count <= 5
        for r in rare:
            assert r["count"] <= 5

    def test_rare_includes_empty(self, problems):
        gap = tag_gap_analysis(problems)
        rare = find_rare_intersections(gap)
        empty = [r for r in rare if r["count"] == 0]
        assert len(empty) >= 1


# ── Section 3: Technique Transfer ────────────────────────────────


class TestTechniqueTransfer:
    """Test technique transfer mapping."""

    def test_finds_transfers(self, problems):
        transfers = build_technique_transfer_map(problems)
        assert len(transfers) > 0

    def test_transfer_has_required_fields(self, problems):
        transfers = build_technique_transfer_map(problems)
        for t in transfers[:10]:
            assert "solved_problem" in t
            assert "open_problem" in t
            assert "shared_techniques" in t
            assert "solved_areas" in t
            assert "open_areas" in t

    def test_transfer_solved_is_solved(self, problems):
        prob_map = {p["number"]: p for p in problems}
        transfers = build_technique_transfer_map(problems)
        for t in transfers[:50]:
            assert is_solved(prob_map[t["solved_problem"]])

    def test_transfer_open_is_open(self, problems):
        prob_map = {p["number"]: p for p in problems}
        transfers = build_technique_transfer_map(problems)
        for t in transfers[:50]:
            assert is_open(prob_map[t["open_problem"]])

    def test_transfer_has_shared_technique(self, problems):
        transfers = build_technique_transfer_map(problems)
        for t in transfers[:50]:
            assert len(t["shared_techniques"]) > 0

    def test_transfer_has_different_areas(self, problems):
        transfers = build_technique_transfer_map(problems)
        for t in transfers[:50]:
            # Solved areas and open areas should differ
            # (symmetric difference should be non-empty)
            s = set(t["solved_areas"])
            o = set(t["open_areas"])
            assert s ^ o  # non-empty symmetric difference

    def test_transfer_summary(self, problems):
        transfers = build_technique_transfer_map(problems)
        summary = summarize_technique_transfers(transfers)
        assert "by_technique" in summary
        assert "top_area_transfers" in summary
        assert len(summary["by_technique"]) > 0

    def test_small_transfers(self, small_problems):
        transfers = build_technique_transfer_map(small_problems)
        # Problem 2 (proved, ramsey theory/graph theory) and 8 (open, ramsey theory/additive combinatorics)
        # share ramsey theory but have different areas
        assert len(transfers) > 0


# ── Section 4: Structural Isomorphism ────────────────────────────


class TestStructuralIsomorphism:
    """Test structural isomorphism detection."""

    def test_finds_isomorphisms_small(self, small_problems):
        isos = find_structural_isomorphisms(small_problems)
        # Problems 3 and 4 have identical tags and different status
        assert len(isos) > 0

    def test_isomorphism_has_required_fields(self, small_problems):
        isos = find_structural_isomorphisms(small_problems)
        for iso in isos:
            assert "tags" in iso
            assert "solved_problem" in iso
            assert "open_problem" in iso

    def test_identical_tags(self, small_problems):
        isos = find_structural_isomorphisms(small_problems)
        for iso in isos:
            # Verify the paired problems have exactly the same tags
            prob_map = {p["number"]: p for p in small_problems}
            s_tags = sorted(prob_map[iso["solved_problem"]].get("tags", []))
            o_tags = sorted(prob_map[iso["open_problem"]].get("tags", []))
            assert s_tags == o_tags

    def test_mixed_status(self, small_problems):
        isos = find_structural_isomorphisms(small_problems)
        for iso in isos:
            prob_map = {p["number"]: p for p in small_problems}
            assert is_solved(prob_map[iso["solved_problem"]])
            assert is_open(prob_map[iso["open_problem"]])

    def test_full_dataset_isomorphisms(self, problems):
        isos = find_structural_isomorphisms(problems)
        assert len(isos) > 0

    def test_iso_summary(self, problems):
        isos = find_structural_isomorphisms(problems)
        summary = summarize_isomorphisms(isos)
        assert len(summary) > 0
        for s in summary:
            assert s["solved_count"] > 0
            assert s["open_count"] > 0


# ── Section 5: Novel Problem Generation ──────────────────────────


class TestNovelProblems:
    """Test novel problem generation."""

    def test_generates_five_problems(self, problems):
        gap = tag_gap_analysis(problems)
        rare = find_rare_intersections(gap)
        transfers = build_technique_transfer_map(problems)
        transfer_summary = summarize_technique_transfers(transfers)
        novel = generate_novel_problems(gap, rare, transfer_summary, problems)
        assert len(novel) == 5

    def test_novel_has_required_fields(self, problems):
        gap = tag_gap_analysis(problems)
        rare = find_rare_intersections(gap)
        transfers = build_technique_transfer_map(problems)
        transfer_summary = summarize_technique_transfers(transfers)
        novel = generate_novel_problems(gap, rare, transfer_summary, problems)
        for np_item in novel:
            assert "id" in np_item
            assert "title" in np_item
            assert "intersection" in np_item
            assert "question" in np_item
            assert "why_novel" in np_item
            assert "approach" in np_item
            assert "related_problems" in np_item

    def test_novel_ids_unique(self, problems):
        gap = tag_gap_analysis(problems)
        rare = find_rare_intersections(gap)
        transfers = build_technique_transfer_map(problems)
        transfer_summary = summarize_technique_transfers(transfers)
        novel = generate_novel_problems(gap, rare, transfer_summary, problems)
        ids = [n["id"] for n in novel]
        assert len(ids) == len(set(ids))

    def test_novel_target_underexplored(self, problems):
        gap = tag_gap_analysis(problems)
        rare = find_rare_intersections(gap)
        transfers = build_technique_transfer_map(problems)
        transfer_summary = summarize_technique_transfers(transfers)
        novel = generate_novel_problems(gap, rare, transfer_summary, problems)
        # All novel problems should target intersections with few existing problems
        for np_item in novel:
            assert np_item["existing_count"] <= 5


# ── Section 6: Problem Genome ────────────────────────────────────


class TestProblemGenome:
    """Test problem genome and nearest-neighbor analysis."""

    def test_genome_shape(self, small_problems):
        matrix, prob_nums, feature_names = build_problem_genome(small_problems)
        assert matrix.shape[0] == len(small_problems)
        assert matrix.shape[1] == len(feature_names)
        assert len(prob_nums) == len(small_problems)

    def test_genome_binary_tags(self, small_problems):
        matrix, prob_nums, feature_names = build_problem_genome(small_problems)
        # Tag features should be 0 or 1
        n_tags = matrix.shape[1] - 4
        tag_matrix = matrix[:, :n_tags]
        assert np.all((tag_matrix == 0) | (tag_matrix == 1))

    def test_genome_oeis_count(self, small_problems):
        matrix, prob_nums, feature_names = build_problem_genome(small_problems)
        oeis_idx = feature_names.index("oeis_count")
        # Problem 4 has 2 OEIS sequences
        p4_idx = prob_nums.index("4")
        assert matrix[p4_idx, oeis_idx] == 2

    def test_genome_prize(self, small_problems):
        matrix, prob_nums, feature_names = build_problem_genome(small_problems)
        prize_idx = feature_names.index("prize_log")
        # Problem 1 ($500) should have higher prize than problem 2 (no prize)
        p1_idx = prob_nums.index("1")
        p2_idx = prob_nums.index("2")
        assert matrix[p1_idx, prize_idx] > matrix[p2_idx, prize_idx]

    def test_genome_status(self, small_problems):
        matrix, prob_nums, feature_names = build_problem_genome(small_problems)
        open_idx = feature_names.index("status_open")
        solved_idx = feature_names.index("status_solved")
        # Problem 1 is open
        p1_idx = prob_nums.index("1")
        assert matrix[p1_idx, open_idx] == 1.0
        assert matrix[p1_idx, solved_idx] == 0.0
        # Problem 2 is proved
        p2_idx = prob_nums.index("2")
        assert matrix[p2_idx, open_idx] == 0.0
        assert matrix[p2_idx, solved_idx] == 1.0

    def test_nearest_neighbors(self, small_problems):
        matrix, prob_nums, feature_names = build_problem_genome(small_problems)
        pairs = find_nearest_neighbors(matrix, prob_nums, small_problems, k=3)
        assert len(pairs) > 0

    def test_nn_has_required_fields(self, small_problems):
        matrix, prob_nums, feature_names = build_problem_genome(small_problems)
        pairs = find_nearest_neighbors(matrix, prob_nums, small_problems, k=3)
        for p in pairs[:5]:
            assert "problem_1" in p
            assert "problem_2" in p
            assert "cosine_distance" in p
            assert "shared_tags" in p
            assert "jaccard_similarity" in p

    def test_nn_distance_nonnegative(self, small_problems):
        matrix, prob_nums, feature_names = build_problem_genome(small_problems)
        pairs = find_nearest_neighbors(matrix, prob_nums, small_problems, k=3)
        for p in pairs:
            assert p["cosine_distance"] >= 0

    def test_surprising_neighbors(self, small_problems):
        matrix, prob_nums, feature_names = build_problem_genome(small_problems)
        pairs = find_nearest_neighbors(matrix, prob_nums, small_problems, k=3)
        surprising = find_surprising_neighbors(pairs, top_n=5)
        # May or may not find surprising pairs in small set
        for s in surprising:
            assert "surprise_score" in s
            assert s["surprise_score"] > 0

    def test_full_dataset_genome(self, problems):
        matrix, prob_nums, feature_names = build_problem_genome(problems)
        assert matrix.shape[0] == len(problems)
        assert matrix.shape[1] >= 40  # at least 40 tags + extras

    def test_full_dataset_surprising(self, problems):
        matrix, prob_nums, feature_names = build_problem_genome(problems)
        pairs = find_nearest_neighbors(matrix, prob_nums, problems, k=5)
        surprising = find_surprising_neighbors(pairs, top_n=30)
        assert len(surprising) > 0


# ── Integration Tests ────────────────────────────────────────────


class TestIntegration:
    """Integration tests running all analyses."""

    def test_run_all_analyses(self, problems):
        results = run_all_analyses(problems)
        assert "oeis_bridges" in results
        assert "gap_analysis" in results
        assert "rare_intersections" in results
        assert "transfers" in results
        assert "transfer_summary" in results
        assert "isomorphisms" in results
        assert "iso_summary" in results
        assert "novel_problems" in results
        assert "surprising_neighbors" in results
        assert "genome_stats" in results

    def test_results_nonempty(self, problems):
        results = run_all_analyses(problems)
        assert len(results["gap_analysis"]) > 0
        assert len(results["transfers"]) > 0
        assert len(results["iso_summary"]) > 0
        assert len(results["novel_problems"]) == 5
        assert len(results["surprising_neighbors"]) > 0


# ── Bridge Investigation Tests ───────────────────────────────────


class TestInvestigateBridge:
    """Test hypothesis generation for OEIS bridge connections."""

    def test_nt_graph_bridge(self):
        """NT in tags1, graph in tags2: encodes structure."""
        result = _investigate_bridge({"number theory"}, {"graph theory"}, "A000001")
        assert "Number-theoretic sequence encodes graph-theoretic structure" in result

    def test_graph_nt_bridge(self):
        """Graph in tags1, NT in tags2: reflects sequence."""
        result = _investigate_bridge({"graph theory"}, {"number theory"}, "A000002")
        assert "Graph structure reflects number-theoretic sequence" in result

    def test_geometry_nt_bridge(self):
        result = _investigate_bridge({"geometry"}, {"number theory"}, "A000003")
        assert "Geometric counting sequence" in result

    def test_ramsey_nt_bridge(self):
        result = _investigate_bridge({"ramsey theory"}, {"number theory"}, "A000004")
        assert "Ramsey-type extremal function" in result

    def test_analysis_combinatorics_bridge(self):
        result = _investigate_bridge({"analysis"}, {"combinatorics"}, "A000005")
        assert "Analytic extremal bound" in result

    def test_additive_graph_bridge(self):
        result = _investigate_bridge({"additive combinatorics"}, {"graph theory"}, "A000006")
        assert "Additive structure and graph density" in result

    def test_covering_systems_bridge(self):
        result = _investigate_bridge({"covering systems"}, {"primes"}, "A000007")
        assert "Covering system sequence" in result

    def test_generic_bridge(self):
        """Tags with no specific pattern: should include diff tags in message."""
        result = _investigate_bridge({"topology"}, {"algebra"}, "A999999")
        assert "A999999" in result

    def test_no_diff_tags_bridge(self):
        """Identical tags: symmetric difference is empty."""
        result = _investigate_bridge({"primes"}, {"primes"}, "A000010")
        assert "hidden structural parallel" in result


# ── Report Output Test ───────────────────────────────────────────


class TestReportOutput:
    """Test that the generated report exists and has content."""

    def test_report_file_exists(self):
        report_path = Path(__file__).parent.parent / "docs" / "relationship_report.md"
        assert report_path.exists(), "Report file should exist (run the script first)"

    def test_report_has_all_sections(self):
        report_path = Path(__file__).parent.parent / "docs" / "relationship_report.md"
        if not report_path.exists():
            pytest.skip("Report not generated yet")
        content = report_path.read_text()
        assert "## 1. Hidden Connections via OEIS" in content
        assert "## 2. Tag Gap Analysis" in content
        assert "## 3. Technique Transfer Map" in content
        assert "## 4. Structural Isomorphism" in content
        assert "## 5. Novel Problem Generation" in content
        assert "## 6. Problem 'Genome'" in content
        assert "## Summary of Key Discoveries" in content

    def test_report_has_novel_problems(self):
        report_path = Path(__file__).parent.parent / "docs" / "relationship_report.md"
        if not report_path.exists():
            pytest.skip("Report not generated yet")
        content = report_path.read_text()
        assert "NRD-1" in content
        assert "NRD-2" in content
        assert "NRD-3" in content
        assert "NRD-4" in content
        assert "NRD-5" in content


# ── Generate Report Function Tests ───────────────────────────────


class TestGenerateReport:
    """Test the generate_report function directly with synthetic data."""

    def test_report_structure(self, small_problems):
        oeis_bridges = [{"problem_1": "1", "status_1": "open", "tags_1": ["NT"],
                         "problem_2": "2", "status_2": "open", "tags_2": ["Graph"],
                         "shared_oeis": "A000001", "shared_tags": [],
                         "jaccard": 0.0, "investigation": "Test bridge"}]
        gap_analysis = {}
        rare = []
        transfers = [{"solved_problem": "2", "open_problem": "1",
                       "shared_techniques": ["density"],
                       "solved_areas": ["graph theory"],
                       "open_areas": ["number theory"],
                       "solved_status": "proved", "open_prize": 500}]
        transfer_summary = {"by_technique": {"density": 5},
                            "top_area_transfers": [{"from_areas": ["graph theory"],
                                                    "to_areas": ["number theory"],
                                                    "count": 5,
                                                    "example_solved": "2",
                                                    "example_open": "1"}]}
        isos = []
        iso_summary = []
        novel = [{"id": "NRD-1", "title": "Test", "intersection": "NT x Graph",
                  "existing_count": 0, "question": "Test question?",
                  "why_novel": "Bridge", "approach": "Density",
                  "related_problems": ["1", "2"]}]
        surprising = []
        genome_stats = {"total_problems": 9, "total_edges": 5,
                        "n_features": 20, "n_tags": 16}

        report = generate_report(
            small_problems, oeis_bridges, gap_analysis, rare, transfers,
            transfer_summary, isos, iso_summary, novel, surprising, genome_stats
        )

        assert isinstance(report, str)
        assert "# Erdos Problems: Relationship Discovery Report" in report
        assert "Hidden Connections via OEIS" in report
        assert "zero-overlap" in report.lower() or "Zero-overlap" in report

    def test_report_no_bridges(self, small_problems):
        report = generate_report(
            small_problems, [],
            {}, [], [],
            {"by_technique": {}, "top_area_transfers": []},
            [], [], [], [],
            {"total_problems": 0, "total_edges": 0,
             "n_features": 20, "n_tags": 16}
        )
        assert "No hidden bridges found" in report

    def test_report_has_all_sections(self, small_problems):
        report = generate_report(
            small_problems, [],
            {}, [], [],
            {"by_technique": {}, "top_area_transfers": []},
            [], [], [], [],
            {"total_problems": 0, "total_edges": 0,
             "n_features": 20, "n_tags": 16}
        )
        assert "## 1." in report
        assert "## 2." in report or "Tag Gap" in report
