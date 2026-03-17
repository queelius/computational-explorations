"""Tests for technique_transfer.py — matching proof techniques to open problems."""
import math
import numpy as np
import pytest

from technique_transfer import (
    load_problems,
    classify_technique,
    technique_profile,
    structure_similarity,
    transfer_recommendations,
    technique_gaps,
    cross_pollination,
    technique_cooccurrence,
    TECHNIQUE_FAMILIES,
    _number,
    _tags,
    _statement_words,
    _structure_vector,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def profile(problems):
    return technique_profile(problems)


# ── Helpers ─────────────────────────────────────────────────────────

class TestHelpers:
    """Test internal helper functions."""

    def test_statement_words_filters(self):
        words = _statement_words({"statement": "The chromatic number of a random graph"})
        assert "chromatic" in words
        assert "the" not in words

    def test_statement_words_short_words(self):
        words = _statement_words({"statement": "If n is at most k"})
        assert "at" not in words  # too short

    def test_structure_vector_shape(self):
        p = {"tags": ["graph theory"], "oeis": [], "statement": "test"}
        v = _structure_vector(p)
        assert len(v) == len(TECHNIQUE_FAMILIES) + 3  # techniques + tags + oeis + prize


# ── Technique classification ────────────────────────────────────────

class TestClassifyTechnique:
    """Test technique family classification."""

    def test_returns_dict(self):
        p = {"statement": "random graph probability", "tags": []}
        result = classify_technique(p)
        assert isinstance(result, dict)

    def test_all_families_present(self):
        p = {"statement": "test", "tags": []}
        result = classify_technique(p)
        for family in TECHNIQUE_FAMILIES:
            assert family in result

    def test_scores_bounded(self):
        p = {"statement": "random graph probability expected", "tags": ["probability"]}
        result = classify_technique(p)
        for score in result.values():
            assert 0.0 <= score <= 1.0

    def test_probabilistic_detected(self):
        p = {"statement": "random graph with probability", "tags": ["probability"]}
        result = classify_technique(p)
        assert result["probabilistic"] > 0.3

    def test_combinatorial_detected(self):
        p = {"statement": "extremal graph coloring ramsey counting",
             "tags": ["combinatorics"]}
        result = classify_technique(p)
        assert result["combinatorial"] > 0.3

    def test_analytic_detected(self):
        p = {"statement": "asymptotic density logarithm sum series",
             "tags": ["number theory"]}
        result = classify_technique(p)
        assert result["analytic"] > 0.3

    def test_geometric_detected(self):
        p = {"statement": "convex distance point plane incidence",
             "tags": ["geometry"]}
        result = classify_technique(p)
        assert result["geometric"] > 0.3

    def test_additive_detected(self):
        p = {"statement": "arithmetic progression sumset sidon",
             "tags": ["additive combinatorics"]}
        result = classify_technique(p)
        assert result["additive"] > 0.3

    def test_empty_problem_zero(self):
        result = classify_technique({"statement": "", "tags": []})
        assert all(v == 0 for v in result.values())


# ── Technique profile ──────────────────────────────────────────────

class TestTechniqueProfile:
    """Test technique profiling over all problems."""

    def test_returns_dict(self, profile):
        assert isinstance(profile, dict)

    def test_solved_count(self, profile):
        assert profile["n_solved"] > 400

    def test_open_count(self, profile):
        assert profile["n_open"] > 500

    def test_effectiveness_has_entries(self, profile):
        assert len(profile["technique_effectiveness"]) >= 5

    def test_solve_rates_bounded(self, profile):
        for fam, stats in profile["technique_effectiveness"].items():
            assert 0.0 <= stats["solve_rate"] <= 1.0

    def test_analytic_largest(self, profile):
        """Analytic should be the most common technique family."""
        eff = profile["technique_effectiveness"]
        if "analytic" in eff:
            assert eff["analytic"]["total"] > 100

    def test_dominant_techniques_nonempty(self, profile):
        assert len(profile["solved_dominant_techniques"]) > 0
        assert len(profile["open_dominant_techniques"]) > 0


# ── Structure similarity ───────────────────────────────────────────

class TestStructureSimilarity:
    """Test cosine similarity between problem structures."""

    def test_self_similarity(self):
        p = {"statement": "random graph probability", "tags": ["probability"],
             "oeis": [], "prize": None}
        assert structure_similarity(p, p) == pytest.approx(1.0, abs=0.001)

    def test_similar_problems(self):
        p1 = {"statement": "chromatic number coloring", "tags": ["graph theory"],
              "oeis": [], "prize": None}
        p2 = {"statement": "chromatic number graph", "tags": ["graph theory"],
              "oeis": [], "prize": None}
        sim = structure_similarity(p1, p2)
        assert sim > 0.5

    def test_different_problems(self):
        p1 = {"statement": "random graph probability", "tags": ["probability"],
              "oeis": [], "prize": None}
        p2 = {"statement": "convex distance point lattice", "tags": ["geometry"],
              "oeis": [], "prize": None}
        sim = structure_similarity(p1, p2)
        assert sim < 0.8

    def test_empty_zero(self):
        p1 = {"statement": "", "tags": [], "oeis": [], "prize": None}
        p2 = {"statement": "test", "tags": ["graph theory"], "oeis": [], "prize": None}
        assert structure_similarity(p1, p2) == 0.0

    def test_bounded(self):
        p1 = {"statement": "arithmetic progression", "tags": ["additive combinatorics"],
              "oeis": ["A000040"], "prize": 500}
        p2 = {"statement": "prime number sieve", "tags": ["number theory"],
              "oeis": ["A000040"], "prize": None}
        sim = structure_similarity(p1, p2)
        assert 0.0 <= sim <= 1.0


# ── Transfer recommendations ──────────────────────────────────────

class TestTransferRecommendations:
    """Test technique transfer recommendations."""

    def test_returns_list(self, problems):
        recs = transfer_recommendations(problems, top_k=10)
        assert isinstance(recs, list)

    def test_nonempty(self, problems):
        recs = transfer_recommendations(problems, top_k=10)
        assert len(recs) > 0

    def test_fields_present(self, problems):
        recs = transfer_recommendations(problems, top_k=5)
        for r in recs:
            assert "open_problem" in r
            assert "recommended_technique" in r
            assert "evidence_problem" in r
            assert "similarity" in r
            assert "score" in r

    def test_scores_positive(self, problems):
        recs = transfer_recommendations(problems, top_k=10)
        for r in recs:
            assert r["score"] > 0

    def test_similarity_bounded(self, problems):
        recs = transfer_recommendations(problems, top_k=10)
        for r in recs:
            assert 0.0 <= r["similarity"] <= 1.0

    def test_techniques_valid(self, problems):
        recs = transfer_recommendations(problems, top_k=10)
        for r in recs:
            assert r["recommended_technique"] in TECHNIQUE_FAMILIES

    def test_sorted_by_score(self, problems):
        recs = transfer_recommendations(problems, top_k=10)
        for i in range(len(recs) - 1):
            assert recs[i]["score"] >= recs[i+1]["score"]

    def test_diversified(self, problems):
        """No single evidence problem should appear more than 3 times."""
        recs = transfer_recommendations(problems, top_k=20)
        from collections import Counter
        ev_counts = Counter(r["evidence_problem"] for r in recs)
        for count in ev_counts.values():
            assert count <= 3


# ── Technique gaps ─────────────────────────────────────────────────

class TestTechniqueGaps:
    """Test technique coverage gap analysis."""

    def test_returns_dict(self, problems):
        result = technique_gaps(problems)
        assert isinstance(result, dict)

    def test_has_gaps(self, problems):
        result = technique_gaps(problems)
        assert result["n_gaps"] > 0

    def test_gap_fields(self, problems):
        result = technique_gaps(problems)
        for g in result["gaps"]:
            assert "tag" in g
            assert "missing_in_open" in g
            assert "n_open_with_tag" in g

    def test_missing_nonempty(self, problems):
        result = technique_gaps(problems)
        for g in result["gaps"]:
            assert len(g["missing_in_open"]) > 0


# ── Cross-pollination ──────────────────────────────────────────────

class TestCrossPollination:
    """Test cross-pollination opportunity detection."""

    def test_returns_dict(self, problems):
        result = cross_pollination(problems)
        assert isinstance(result, dict)

    def test_has_opportunities(self, problems):
        result = cross_pollination(problems)
        assert result["n_opportunities"] > 0

    def test_opportunity_fields(self, problems):
        result = cross_pollination(problems)
        for o in result["opportunities"][:5]:
            assert "technique" in o
            assert "strong_in" in o
            assert "weak_in" in o
            assert "strong_solve_rate" in o

    def test_strong_rate_high(self, problems):
        result = cross_pollination(problems)
        for o in result["opportunities"]:
            assert o["strong_solve_rate"] > 0.5


# ── Technique co-occurrence ────────────────────────────────────────

class TestTechniqueCooccurrence:
    """Test technique co-occurrence analysis."""

    def test_returns_dict(self, problems):
        result = technique_cooccurrence(problems)
        assert isinstance(result, dict)

    def test_technique_counts(self, problems):
        result = technique_cooccurrence(problems)
        assert len(result["technique_counts"]) > 3

    def test_lift_pairs(self, problems):
        result = technique_cooccurrence(problems)
        assert len(result["top_pairs_by_lift"]) > 0

    def test_lift_positive(self, problems):
        result = technique_cooccurrence(problems)
        for pair in result["top_pairs_by_lift"]:
            assert pair["lift"] > 0

    def test_pair_fields(self, problems):
        result = technique_cooccurrence(problems)
        for pair in result["top_pairs_by_lift"]:
            assert "technique_1" in pair
            assert "technique_2" in pair
            assert "co_occurrences" in pair
            assert "lift" in pair

    def test_n_solved_positive(self, problems):
        result = technique_cooccurrence(problems)
        assert result["n_solved_classified"] > 400
