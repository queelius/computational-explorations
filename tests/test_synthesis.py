"""Tests for synthesis.py — cross-cutting analysis of Erdős problems."""
import math
import pytest

from synthesis import (
    load_problems,
    problem_status,
    problem_tags,
    problem_oeis,
    problem_number,
    parse_prize,
    compute_vulnerability_scores,
    detect_dualities,
    build_conjecture_network,
    resolution_cascade,
    gap_bridging_proposals,
    difficulty_taxonomy,
    technique_effectiveness,
    problem_similarity_clusters,
    _compute_tag_solve_rates,
    _technique_coverage,
)


@pytest.fixture(scope="module")
def problems():
    """Load problems once for all tests."""
    return load_problems()


class TestDataLoading:
    """Test data loading and helper functions."""

    def test_load_problems(self, problems):
        assert len(problems) > 1000

    def test_problem_status(self, problems):
        states = {problem_status(p) for p in problems}
        assert "open" in states
        assert "proved" in states or "disproved" in states

    def test_problem_tags(self, problems):
        tagged = [p for p in problems if problem_tags(p)]
        assert len(tagged) > 500

    def test_problem_number(self, problems):
        nums = [problem_number(p) for p in problems]
        # Numbers may be stored as strings in YAML
        assert all(isinstance(n, (int, str)) for n in nums)
        int_nums = [int(n) for n in nums if str(n).isdigit()]
        assert max(int_nums) > 900

    def test_problem_oeis(self, problems):
        with_oeis = [p for p in problems if problem_oeis(p)]
        assert len(with_oeis) > 100

    def test_parse_prize_dollar(self):
        assert parse_prize({"prize": "$500"}) == 500.0

    def test_parse_prize_no(self):
        assert parse_prize({"prize": "no"}) == 0.0

    def test_parse_prize_missing(self):
        assert parse_prize({}) == 0.0

    def test_parse_prize_gbp(self):
        val = parse_prize({"prize": "\u00a325"})
        assert val > 25  # GBP conversion multiplier

    def test_parse_prize_large(self):
        assert parse_prize({"prize": "$5,000"}) == 5000.0


class TestVulnerabilityScores:
    """Test the multi-signal vulnerability scoring system."""

    def test_returns_list(self, problems):
        scores = compute_vulnerability_scores(problems)
        assert isinstance(scores, list)
        assert len(scores) > 0

    def test_all_open(self, problems):
        """All scored problems should be open."""
        scores = compute_vulnerability_scores(problems)
        open_nums = {problem_number(p) for p in problems if problem_status(p) == "open"}
        for s in scores:
            assert s["number"] in open_nums

    def test_scores_bounded(self, problems):
        """Vulnerability scores should be between 0 and 1."""
        scores = compute_vulnerability_scores(problems)
        for s in scores:
            assert 0.0 <= s["vulnerability"] <= 1.0

    def test_sorted_descending(self, problems):
        """Results should be sorted by vulnerability descending."""
        scores = compute_vulnerability_scores(problems)
        for i in range(len(scores) - 1):
            assert scores[i]["vulnerability"] >= scores[i + 1]["vulnerability"]

    def test_has_required_fields(self, problems):
        scores = compute_vulnerability_scores(problems)
        required = {"number", "tags", "vulnerability", "tag_solvability",
                    "oeis_bridges", "technique_match", "prize"}
        for s in scores[:10]:
            assert required.issubset(s.keys())

    def test_technique_match_nonneg(self, problems):
        scores = compute_vulnerability_scores(problems)
        for s in scores:
            assert s["technique_match"] >= 0


class TestTagSolveRates:
    """Test tag solve rate computation."""

    def test_rates_bounded(self, problems):
        rates = _compute_tag_solve_rates(problems)
        for tag, rate in rates.items():
            assert 0.0 <= rate <= 1.0

    def test_common_tags_present(self, problems):
        rates = _compute_tag_solve_rates(problems)
        assert "number theory" in rates
        assert "graph theory" in rates

    def test_rates_nonzero_for_some(self, problems):
        rates = _compute_tag_solve_rates(problems)
        nonzero = [r for r in rates.values() if r > 0]
        assert len(nonzero) > 0


class TestTechniqueCoverage:
    """Test technique coverage mapping."""

    def test_returns_dict(self):
        tc = _technique_coverage()
        assert isinstance(tc, dict)
        assert len(tc) >= 8

    def test_values_are_sets(self):
        tc = _technique_coverage()
        for name, tags in tc.items():
            assert isinstance(tags, set)
            assert len(tags) >= 1


class TestDualities:
    """Test duality detection."""

    def test_returns_list(self, problems):
        duals = detect_dualities(problems)
        assert isinstance(duals, list)

    def test_has_types(self, problems):
        duals = detect_dualities(problems)
        types = {d["type"] for d in duals}
        # Should find at least some types
        assert len(types) >= 1

    def test_twin_problems_have_shared_oeis(self, problems):
        duals = detect_dualities(problems)
        twins = [d for d in duals if d["type"] == "twin_problems"]
        for t in twins:
            assert len(t["shared_oeis"]) > 0

    def test_cross_domain_has_multiple_domains(self, problems):
        duals = detect_dualities(problems)
        cross = [d for d in duals if d["type"] == "cross_domain_oeis"]
        for c in cross:
            assert len(c["domains"]) >= 2


class TestConjectureNetwork:
    """Test conjecture network construction."""

    def test_network_structure(self, problems):
        net = build_conjecture_network(problems)
        assert "num_nodes" in net
        assert "num_edges" in net
        assert "num_components" in net

    def test_nodes_are_open(self, problems):
        net = build_conjecture_network(problems)
        open_count = sum(1 for p in problems if problem_status(p) == "open")
        assert net["num_nodes"] == open_count

    def test_edges_positive(self, problems):
        net = build_conjecture_network(problems)
        assert net["num_edges"] > 0

    def test_components_partition(self, problems):
        net = build_conjecture_network(problems)
        assert net["largest_component"] <= net["num_nodes"]
        assert net["isolated_nodes"] >= 0

    def test_hub_problems_sorted(self, problems):
        net = build_conjecture_network(problems)
        hubs = net["hub_problems"]
        if len(hubs) > 1:
            for i in range(len(hubs) - 1):
                assert hubs[i][1] >= hubs[i + 1][1]


class TestResolutionCascade:
    """Test resolution cascade analysis."""

    def test_returns_list(self, problems):
        cascade = resolution_cascade(problems)
        assert isinstance(cascade, list)
        assert len(cascade) > 0

    def test_sorted_by_cascade(self, problems):
        cascade = resolution_cascade(problems)
        for i in range(len(cascade) - 1):
            assert cascade[i]["total_cascade"] >= cascade[i + 1]["total_cascade"]

    def test_has_required_fields(self, problems):
        cascade = resolution_cascade(problems)
        required = {"number", "direct_influence", "indirect_influence", "total_cascade"}
        for c in cascade[:10]:
            assert required.issubset(c.keys())

    def test_influence_nonneg(self, problems):
        cascade = resolution_cascade(problems)
        for c in cascade:
            assert c["direct_influence"] >= 0
            assert c["indirect_influence"] >= 0
            assert c["total_cascade"] >= 0


class TestGapBridging:
    """Test gap-bridging proposals."""

    def test_returns_list(self, problems):
        proposals = gap_bridging_proposals(problems)
        assert isinstance(proposals, list)
        assert len(proposals) > 0

    def test_proposals_have_domain_pair(self, problems):
        proposals = gap_bridging_proposals(problems)
        for p in proposals:
            assert "domain_pair" in p
            assert len(p["domain_pair"]) == 2

    def test_sorted_by_existing_count(self, problems):
        proposals = gap_bridging_proposals(problems)
        for i in range(len(proposals) - 1):
            assert proposals[i]["existing_open"] <= proposals[i + 1]["existing_open"]


class TestDifficultyTaxonomy:
    """Test difficulty taxonomy construction."""

    def test_has_tiers(self, problems):
        tax = difficulty_taxonomy(problems)
        assert "tier_counts" in tax
        assert "ripe" in tax["tier_counts"]
        assert "fortress" in tax["tier_counts"]

    def test_tier_counts_sum_to_open(self, problems):
        tax = difficulty_taxonomy(problems)
        total = sum(tax["tier_counts"].values())
        open_count = sum(1 for p in problems if problem_status(p) == "open")
        assert total == open_count

    def test_ripe_top10_format(self, problems):
        tax = difficulty_taxonomy(problems)
        ripe = tax.get("ripe_top10", [])
        for r in ripe:
            assert "number" in r
            assert "vulnerability" in r


class TestTechniqueEffectiveness:
    """Test technique effectiveness analysis."""

    def test_returns_list(self, problems):
        eff = technique_effectiveness(problems)
        assert isinstance(eff, list)
        assert len(eff) >= 8

    def test_sorted_by_power(self, problems):
        eff = technique_effectiveness(problems)
        for i in range(len(eff) - 1):
            assert eff[i]["power_score"] >= eff[i + 1]["power_score"]

    def test_solve_rate_bounded(self, problems):
        eff = technique_effectiveness(problems)
        for e in eff:
            assert 0.0 <= e["solve_rate"] <= 1.0

    def test_has_required_fields(self, problems):
        eff = technique_effectiveness(problems)
        required = {"technique", "matched_open", "matched_solved", "solve_rate", "power_score"}
        for e in eff:
            assert required.issubset(e.keys())


class TestProblemClusters:
    """Test problem similarity clustering."""

    def test_returns_dict(self, problems):
        result = problem_similarity_clusters(problems, n_clusters=4)
        assert "n_clusters" in result
        assert "clusters" in result

    def test_cluster_count(self, problems):
        result = problem_similarity_clusters(problems, n_clusters=4)
        assert len(result["clusters"]) == 4

    def test_clusters_cover_all(self, problems):
        result = problem_similarity_clusters(problems, n_clusters=4)
        total = sum(c["size"] for c in result["clusters"])
        assert total == len(problems)

    def test_cluster_fields(self, problems):
        result = problem_similarity_clusters(problems, n_clusters=4)
        for c in result["clusters"]:
            assert "cluster_id" in c
            assert "size" in c
            assert "dominant_tags" in c
            assert "open_count" in c
            assert c["size"] > 0
