"""Tests for meta_patterns.py — higher-order pattern mining."""
import math
import pytest

from meta_patterns import (
    load_problems,
    _prize,
    _year_solved,
    _year_posed,
    resolution_waves,
    tag_coevolution,
    difficulty_decay,
    network_motifs,
    problem_dna,
    anomaly_detection,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


class TestPrize:
    """Test _prize extraction from problem dicts."""

    def test_dollar_amount(self):
        assert _prize({"prize": "$500"}) == 500.0

    def test_large_dollar(self):
        assert _prize({"prize": "$10,000"}) == 10000.0

    def test_gbp_amount(self):
        val = _prize({"prize": "\u00a310"})
        assert abs(val - 12.7) < 0.1  # £10 * 1.27

    def test_no_prize(self):
        assert _prize({"prize": "no"}) == 0.0

    def test_missing_prize(self):
        assert _prize({}) == 0.0

    def test_non_numeric_prize(self):
        """Prize string with no numbers should return 0.0."""
        assert _prize({"prize": "TBA"}) == 0.0


class TestYearPosed:
    """Test _year_posed extraction."""

    def test_valid_date(self):
        assert _year_posed({"date": "1975-06-15"}) == 1975

    def test_year_only(self):
        assert _year_posed({"date": "1960"}) == 1960

    def test_no_date(self):
        assert _year_posed({}) is None

    def test_empty_date(self):
        assert _year_posed({"date": ""}) is None

    def test_none_date(self):
        assert _year_posed({"date": None}) is None

    def test_too_early(self):
        """Year before 1900 should be rejected."""
        assert _year_posed({"date": "1850-01-01"}) is None


class TestYearSolved:
    """Test _year_solved extraction from multiple fields."""

    def test_status_date(self):
        """Should extract from status.date first."""
        p = {"status": {"date": "2010-03-15"}}
        assert _year_solved(p) == 2010

    def test_status_last_update(self):
        """Falls back to status.last_update."""
        p = {"status": {"last_update": "2015-09-01"}}
        assert _year_solved(p) == 2015

    def test_top_level_date(self):
        """Falls back to top-level date field."""
        p = {"status": {}, "date": "1990-05-20"}
        assert _year_solved(p) == 1990

    def test_references_year(self):
        """Falls back to year extraction from references."""
        p = {"status": {}, "references": ["Smith (2005)", "Jones et al. 1998"]}
        assert _year_solved(p) == 2005  # max of extracted years

    def test_no_date_info(self):
        assert _year_solved({}) is None
        assert _year_solved({"status": {}}) is None

    def test_non_list_references(self):
        """Non-list references should be handled gracefully."""
        p = {"status": {}, "references": "single string"}
        assert _year_solved(p) is None


class TestResolutionWaves:
    """Test temporal resolution analysis."""

    def test_returns_dict(self, problems):
        r = resolution_waves(problems)
        assert isinstance(r, dict)

    def test_has_key_fields(self, problems):
        r = resolution_waves(problems)
        assert "solved_with_dates" in r
        assert "wave_count" in r
        assert "mean_per_year" in r

    def test_solved_count_nonneg(self, problems):
        r = resolution_waves(problems)
        assert r["solved_with_dates"] >= 0

    def test_wave_count_nonneg(self, problems):
        r = resolution_waves(problems)
        assert r["wave_count"] >= 0

    def test_tag_waves_format(self, problems):
        r = resolution_waves(problems)
        if r.get("tag_waves"):
            for tag, info in r["tag_waves"].items():
                assert isinstance(tag, str)
                assert info["total_solved"] > 0
                assert "peak_year" in info

    def test_period_summary(self, problems):
        r = resolution_waves(problems)
        for ps in r.get("period_summary", []):
            assert ps["count"] > 0
            assert "period" in ps


class TestTagCoevolution:
    """Test tag pair co-evolution analysis."""

    def test_returns_dict(self, problems):
        r = tag_coevolution(problems)
        assert isinstance(r, dict)

    def test_num_pairs(self, problems):
        r = tag_coevolution(problems)
        assert r["num_pairs_analyzed"] > 0

    def test_easiest_pairs_sorted(self, problems):
        r = tag_coevolution(problems)
        pairs = r["easiest_pairs"]
        for i in range(len(pairs) - 1):
            assert pairs[i][1]["solve_rate"] >= pairs[i + 1][1]["solve_rate"]

    def test_hardest_pairs_sorted(self, problems):
        r = tag_coevolution(problems)
        pairs = r["hardest_pairs"]
        for i in range(len(pairs) - 1):
            assert pairs[i][1]["solve_rate"] <= pairs[i + 1][1]["solve_rate"]

    def test_solve_rates_bounded(self, problems):
        r = tag_coevolution(problems)
        for pair, info in r["easiest_pairs"]:
            assert 0.0 <= info["solve_rate"] <= 1.0
        for pair, info in r["hardest_pairs"]:
            assert 0.0 <= info["solve_rate"] <= 1.0

    def test_synergies_have_fields(self, problems):
        r = tag_coevolution(problems)
        for s in r.get("strongest_synergies", []):
            assert "pair" in s
            assert "actual_rate" in s
            assert "expected_rate" in s
            assert "synergy" in s

    def test_synergies_sorted(self, problems):
        r = tag_coevolution(problems)
        synergies = r.get("strongest_synergies", [])
        for i in range(len(synergies) - 1):
            assert synergies[i]["synergy"] >= synergies[i + 1]["synergy"]

    def test_pair_counts_consistent(self, problems):
        r = tag_coevolution(problems)
        for pair, info in r["easiest_pairs"]:
            assert info["solved"] + info["open"] == info["total"]


class TestDifficultyDecay:
    """Test difficulty structure analysis."""

    def test_returns_dict(self, problems):
        r = difficulty_decay(problems)
        assert isinstance(r, dict)

    def test_tag_count_rates(self, problems):
        r = difficulty_decay(problems)
        rates = r["tag_count_vs_solve_rate"]
        assert len(rates) > 0
        for bucket, rate in rates.items():
            assert 0.0 <= rate <= 1.0

    def test_oeis_count_rates(self, problems):
        r = difficulty_decay(problems)
        rates = r["oeis_count_vs_solve_rate"]
        assert len(rates) > 0

    def test_quartile_rates(self, problems):
        r = difficulty_decay(problems)
        qr = r["quartile_solve_rates"]
        assert len(qr) > 0
        for q, info in qr.items():
            assert 0.0 <= info["rate"] <= 1.0
            assert info["total"] > 0
            assert info["solved"] >= 0

    def test_formalization_paradox(self, problems):
        r = difficulty_decay(problems)
        fp = r["formalization_paradox"]
        assert "not_formalized" in fp

    def test_quartile_boundaries(self, problems):
        r = difficulty_decay(problems)
        bounds = r["quartile_boundaries"]
        assert bounds["Q1"] <= bounds["Q2"] <= bounds["Q3"]


class TestNetworkMotifs:
    """Test network motif counting."""

    def test_returns_dict(self, problems):
        r = network_motifs(problems)
        assert isinstance(r, dict)

    def test_has_triangle_count(self, problems):
        r = network_motifs(problems)
        assert r["triangle_count"] >= 0

    def test_has_star_nodes(self, problems):
        r = network_motifs(problems)
        assert isinstance(r["star_nodes"], list)

    def test_component_sizes(self, problems):
        r = network_motifs(problems)
        assert r["num_components"] > 0
        assert r["largest_component"] > 0

    def test_degree_stats(self, problems):
        r = network_motifs(problems)
        stats = r["degree_stats"]
        assert stats["max"] >= stats["median"]
        assert stats["mean"] >= 0

    def test_bridge_count(self, problems):
        r = network_motifs(problems)
        assert r["bridge_count"] >= 0


class TestProblemDNA:
    """Test problem DNA fingerprinting."""

    def test_returns_dict(self, problems):
        r = problem_dna(problems)
        assert isinstance(r, dict)

    def test_has_profiles(self, problems):
        r = problem_dna(problems)
        assert "solved_profile" in r
        assert "open_profile" in r

    def test_profiles_have_fields(self, problems):
        r = problem_dna(problems)
        for profile in [r["solved_profile"], r["open_profile"]]:
            if profile:
                assert "avg_tags" in profile
                assert "avg_oeis" in profile
                assert "count" in profile

    def test_solvability_indicators(self, problems):
        r = problem_dna(problems)
        indicators = r["solvability_indicators"]
        assert len(indicators) > 0
        for tag, info in indicators:
            assert isinstance(tag, str)
            assert "enrichment" in info

    def test_total_tags_positive(self, problems):
        r = problem_dna(problems)
        assert r["total_tags"] > 0

    def test_solved_count_reasonable(self, problems):
        r = problem_dna(problems)
        solved_count = r["solved_profile"]["count"]
        assert 100 < solved_count < 800


class TestAnomalyDetection:
    """Test anomaly detection."""

    def test_returns_dict(self, problems):
        r = anomaly_detection(problems)
        assert isinstance(r, dict)

    def test_has_categories(self, problems):
        r = anomaly_detection(problems)
        assert "should_be_solved" in r
        assert "surprisingly_solved" in r
        assert "prize_orphans" in r

    def test_total_anomalies(self, problems):
        r = anomaly_detection(problems)
        assert r["total_anomalies"] >= 0

    def test_should_be_solved_format(self, problems):
        r = anomaly_detection(problems)
        for a in r["should_be_solved"]:
            assert "number" in a
            assert "vulnerability" in a

    def test_prize_orphans_have_prize(self, problems):
        r = anomaly_detection(problems)
        for po in r["prize_orphans"]:
            assert po["prize"] > 0
