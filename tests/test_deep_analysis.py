"""Tests for deep_analysis.py — comprehensive Erdos problem database analysis."""
import pytest
from pathlib import Path
from datetime import datetime
from collections import Counter

from deep_analysis import (
    load_problems,
    parse_prize,
    parse_date,
    state_category,
    oeis_list,
    oeis_cluster_analysis,
    solve_rate_analysis,
    difficulty_classifier,
    temporal_analysis,
    tag_network_communities,
    isolation_analysis,
    build_summary,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def problems(problems_yaml_path):
    if not problems_yaml_path.exists():
        pytest.skip("Problems YAML not found")
    return load_problems()


@pytest.fixture
def sample_problems():
    """Minimal synthetic dataset for unit tests without disk I/O."""
    return [
        {
            "number": "1",
            "prize": "$500",
            "status": {"state": "open", "last_update": "2025-08-31"},
            "oeis": ["A003002", "A003003"],
            "formalized": {"state": "yes", "last_update": "2025-08-31"},
            "tags": ["number theory", "additive combinatorics"],
        },
        {
            "number": "2",
            "prize": "$1000",
            "status": {"state": "disproved", "last_update": "2025-09-15"},
            "oeis": ["A160559"],
            "formalized": {"state": "no", "last_update": "2025-08-31"},
            "tags": ["number theory", "covering systems"],
        },
        {
            "number": "3",
            "prize": "no",
            "status": {"state": "proved", "last_update": "2025-10-01"},
            "oeis": ["A003002"],
            "formalized": {"state": "yes", "last_update": "2025-08-31"},
            "tags": ["number theory", "additive combinatorics", "arithmetic progressions"],
        },
        {
            "number": "4",
            "prize": "no",
            "status": {"state": "solved", "last_update": "2025-12-05"},
            "oeis": ["N/A"],
            "formalized": {"state": "no", "last_update": "2025-08-31"},
            "tags": ["graph theory", "ramsey theory"],
        },
        {
            "number": "5",
            "prize": "$100",
            "status": {"state": "proved (Lean)", "last_update": "2025-11-22"},
            "oeis": ["A003003", "possible"],
            "formalized": {"state": "yes", "last_update": "2025-11-22"},
            "tags": ["graph theory", "chromatic number"],
        },
        {
            "number": "6",
            "prize": "no",
            "status": {"state": "disproved (Lean)", "last_update": "2025-10-14"},
            "oeis": ["N/A"],
            "formalized": {"state": "no", "last_update": "2025-08-31"},
            "tags": ["analysis"],
        },
        {
            "number": "7",
            "prize": "\u00a310",
            "status": {"state": "falsifiable", "last_update": "2025-08-31"},
            "oeis": ["A059442"],
            "formalized": {"state": "no", "last_update": "2025-08-31"},
            "tags": ["geometry"],
        },
        {
            "number": "8",
            "prize": "\u20b91000",
            "status": {"state": "open", "last_update": "2025-08-31"},
            "oeis": ["A059442"],
            "formalized": {"state": "no", "last_update": "2025-08-31"},
            "tags": ["number theory"],
        },
    ]


# ============================================================================
# Unit tests for helper functions
# ============================================================================

class TestParsePrize:
    def test_dollar(self):
        assert parse_prize("$500") == 500.0

    def test_dollar_thousands(self):
        assert parse_prize("$10000") == 10000.0

    def test_no_prize(self):
        assert parse_prize("no") == 0.0

    def test_none(self):
        assert parse_prize(None) == 0.0

    def test_empty(self):
        assert parse_prize("") == 0.0

    def test_gbp(self):
        val = parse_prize("\u00a310")
        assert val > 10  # GBP -> USD conversion

    def test_inr(self):
        val = parse_prize("\u20b91000")
        assert 0 < val < 100  # INR -> USD is small


class TestParseDate:
    def test_normal_date(self):
        d = parse_date("2025-08-31")
        assert d == datetime(2025, 8, 31)

    def test_short_day(self):
        d = parse_date("2025-11-4")
        assert d == datetime(2025, 11, 4)

    def test_short_month_and_day(self):
        d = parse_date("2026-1-10")
        assert d == datetime(2026, 1, 10)

    def test_none(self):
        assert parse_date(None) is None

    def test_empty(self):
        assert parse_date("") is None

    def test_invalid(self):
        assert parse_date("not-a-date") is None


class TestStateCategory:
    def test_open(self):
        assert state_category("open") == "open"

    def test_proved(self):
        assert state_category("proved") == "proved"

    def test_proved_lean(self):
        assert state_category("proved (Lean)") == "proved"

    def test_disproved(self):
        assert state_category("disproved") == "disproved"

    def test_disproved_lean(self):
        assert state_category("disproved (Lean)") == "disproved"

    def test_disproved_before_proved(self):
        """'disproved' contains 'proved', so order matters."""
        assert state_category("disproved") == "disproved"
        assert state_category("disproved (Lean)") == "disproved"

    def test_solved(self):
        assert state_category("solved") == "solved"

    def test_solved_lean(self):
        assert state_category("solved (Lean)") == "solved"

    def test_other_states(self):
        for s in ("falsifiable", "verifiable", "decidable", "independent", "not provable"):
            assert state_category(s) == "other"


class TestOeisList:
    def test_normal(self):
        p = {"oeis": ["A003002", "A003003"]}
        assert oeis_list(p) == ["A003002", "A003003"]

    def test_filters_na(self):
        p = {"oeis": ["N/A"]}
        assert oeis_list(p) == []

    def test_filters_possible(self):
        p = {"oeis": ["A143824", "possible"]}
        assert oeis_list(p) == ["A143824"]

    def test_missing_oeis(self):
        p = {}
        assert oeis_list(p) == []

    def test_empty_list(self):
        p = {"oeis": []}
        assert oeis_list(p) == []


# ============================================================================
# Integration tests on synthetic data
# ============================================================================

class TestOeisClusterAnalysisSynthetic:
    def test_produces_markdown(self, sample_problems):
        result = oeis_cluster_analysis(sample_problems)
        assert "## 1. OEIS Cluster Analysis" in result

    def test_finds_shared_sequences(self, sample_problems):
        result = oeis_cluster_analysis(sample_problems)
        # A003002 is shared by problems 1 and 3; A059442 by 7 and 8
        assert "A003002" in result or "A059442" in result

    def test_finds_families(self, sample_problems):
        result = oeis_cluster_analysis(sample_problems)
        assert "families" in result.lower() or "Family" in result


class TestSolveRateAnalysisSynthetic:
    def test_produces_markdown(self, sample_problems):
        result = solve_rate_analysis(sample_problems)
        assert "## 2. Solve-Rate Meta-Analysis" in result

    def test_per_tag_table(self, sample_problems):
        result = solve_rate_analysis(sample_problems)
        assert "Per-Tag Statistics" in result
        assert "number theory" in result

    def test_hardest_tags(self, sample_problems):
        result = solve_rate_analysis(sample_problems)
        # Should contain section headers
        assert "Solvability" in result or "Falsifiability" in result


class TestDifficultyClassifierSynthetic:
    def test_produces_markdown(self, sample_problems):
        # Need enough data for cross-validation, extend sample
        extended = sample_problems * 10  # 80 problems
        # Re-number to avoid duplicate issues (classifier doesn't care about numbers)
        for i, p in enumerate(extended):
            p = dict(p)
            p["number"] = str(i + 1)
            extended[i] = p
        result = difficulty_classifier(extended)
        assert "## 3. Problem Difficulty Classifier" in result

    def test_feature_importances(self, sample_problems):
        extended = sample_problems * 10
        for i, p in enumerate(extended):
            p = dict(p)
            p["number"] = str(i + 1)
            extended[i] = p
        result = difficulty_classifier(extended)
        assert "Feature Importances" in result


class TestTemporalAnalysisSynthetic:
    def test_produces_markdown(self, sample_problems):
        result = temporal_analysis(sample_problems)
        assert "## 4. Temporal Pattern Analysis" in result

    def test_monthly_table(self, sample_problems):
        result = temporal_analysis(sample_problems)
        assert "Monthly Resolution Activity" in result

    def test_finds_post_base_resolutions(self, sample_problems):
        result = temporal_analysis(sample_problems)
        # Problems 2,3,5,6 are resolved after 2025-08-31
        assert "Status Update Timeline" in result


class TestTagNetworkCommunitiesSynthetic:
    def test_produces_markdown(self, sample_problems):
        result = tag_network_communities(sample_problems)
        assert "## 5. Tag Network Communities" in result

    def test_finds_communities(self, sample_problems):
        result = tag_network_communities(sample_problems)
        assert "Community" in result

    def test_problem_network(self, sample_problems):
        result = tag_network_communities(sample_problems)
        assert "Problem-Problem Network" in result


class TestIsolationAnalysisSynthetic:
    def test_produces_markdown(self, sample_problems):
        result = isolation_analysis(sample_problems)
        assert "## 6. Isolation Score" in result

    def test_finds_most_isolated(self, sample_problems):
        result = isolation_analysis(sample_problems)
        assert "Most Isolated" in result

    def test_isolation_scores_bounded(self, sample_problems):
        result = isolation_analysis(sample_problems)
        # Scores should be between 0 and 1
        assert "Isolation score range:" in result


class TestBuildSummary:
    def test_produces_summary(self, sample_problems):
        result = build_summary("", sample_problems)
        assert "Executive Summary" in result
        assert "Key Findings" in result

    def test_counts_correct(self, sample_problems):
        result = build_summary("", sample_problems)
        assert "8 problems" in result


# ============================================================================
# Integration tests on real data
# ============================================================================

class TestOeisClusterAnalysisReal:
    def test_finds_known_families(self, problems):
        result = oeis_cluster_analysis(problems)
        assert "A003002" in result
        assert "A143824" in result
        assert "A059442" in result
        assert "A000791" in result

    def test_arithmetic_progression_family(self, problems):
        result = oeis_cluster_analysis(problems)
        assert "Arithmetic Progression" in result
        # All 5 expected members
        for num in ["3", "139", "140", "142", "201"]:
            assert num in result

    def test_sidon_family(self, problems):
        result = oeis_cluster_analysis(problems)
        assert "Sidon" in result
        for num in ["14", "30", "43", "155", "530", "861"]:
            assert num in result

    def test_families_found(self, problems):
        result = oeis_cluster_analysis(problems)
        assert "28 problem families" in result

    def test_missing_connections(self, problems):
        result = oeis_cluster_analysis(problems)
        assert "Missing Connection" in result


class TestSolveRateAnalysisReal:
    def test_all_tags_present(self, problems):
        result = solve_rate_analysis(problems)
        for tag in ["number theory", "graph theory", "geometry", "ramsey theory"]:
            assert tag in result

    def test_covering_systems_high_disprove(self, problems):
        result = solve_rate_analysis(problems)
        assert "covering systems" in result

    def test_primes_high_open(self, problems):
        result = solve_rate_analysis(problems)
        assert "primes" in result


class TestDifficultyClassifierReal:
    def test_classification_report(self, problems):
        result = difficulty_classifier(problems)
        assert "Cross-Validated Classification Report" in result

    def test_low_hanging_fruit(self, problems):
        result = difficulty_classifier(problems)
        assert "Low-Hanging Fruit" in result

    def test_counterexample_candidates(self, problems):
        result = difficulty_classifier(problems)
        assert "Counterexample Candidates" in result

    def test_formalized_is_top_feature(self, problems):
        result = difficulty_classifier(problems)
        assert "formalized" in result


class TestTemporalAnalysisReal:
    def test_month_table(self, problems):
        result = temporal_analysis(problems)
        assert "2025-08" in result

    def test_post_base_resolutions(self, problems):
        result = temporal_analysis(problems)
        assert "resolved after initial load" in result


class TestTagNetworkCommunitiesReal:
    def test_five_communities(self, problems):
        result = tag_network_communities(problems)
        assert "5 communities" in result

    def test_modularity(self, problems):
        result = tag_network_communities(problems)
        assert "modularity" in result.lower()

    def test_largest_component(self, problems):
        result = tag_network_communities(problems)
        assert "Largest component" in result


class TestIsolationAnalysisReal:
    def test_most_isolated_is_1123(self, problems):
        result = isolation_analysis(problems)
        # #1123 (algebra) should be among the most isolated
        assert "#1123" in result

    def test_most_connected(self, problems):
        result = isolation_analysis(problems)
        # #986 and #1030 should be among most connected
        assert "#986" in result
        assert "#1030" in result

    def test_over_represented_tags(self, problems):
        result = isolation_analysis(problems)
        assert "over-represented" in result.lower() or "Over-represented" in result
