"""Tests for pattern_synthesis.py — meta-pattern discovery."""
import math
import numpy as np
import pytest

from pattern_synthesis import (
    load_problems,
    build_signal_space,
    discover_archetypes,
    find_blindspots,
    solve_similarity,
    tag_archetype_map,
    prize_efficiency,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def signal_space(problems):
    return build_signal_space(problems)


@pytest.fixture(scope="module")
def archetypes(problems, signal_space):
    return discover_archetypes(problems, signal_space)


# ── build_signal_space ───────────────────────────────────────────────

class TestBuildSignalSpace:
    """Test multi-dimensional signal space construction."""

    def test_returns_dict(self, signal_space):
        assert isinstance(signal_space, dict)

    def test_has_expected_keys(self, signal_space):
        assert "features" in signal_space
        assert "dim_names" in signal_space
        assert "numbers" in signal_space
        assert "prob_by_num" in signal_space

    def test_features_shape(self, signal_space, problems):
        assert signal_space["features"].shape == (len(problems), 9)

    def test_dim_names_count(self, signal_space):
        assert len(signal_space["dim_names"]) == 9

    def test_numbers_match_problems(self, signal_space, problems):
        assert len(signal_space["numbers"]) == len(problems)

    def test_features_bounded(self, signal_space):
        F = signal_space["features"]
        assert np.all(F >= 0.0 - 1e-6)
        assert np.all(F <= 1.0 + 1e-6)

    def test_no_nan_features(self, signal_space):
        assert not np.any(np.isnan(signal_space["features"]))

    def test_formalized_has_variation(self, signal_space):
        idx = signal_space["dim_names"].index("formalized")
        col = signal_space["features"][:, idx]
        assert col.min() == 0.0
        assert col.max() == 1.0

    def test_is_solved_has_variation(self, signal_space):
        idx = signal_space["dim_names"].index("is_solved")
        col = signal_space["features"][:, idx]
        assert set(col) == {0.0, 1.0}

    def test_prize_signal_mostly_zero(self, signal_space):
        idx = signal_space["dim_names"].index("prize_signal")
        col = signal_space["features"][:, idx]
        zero_frac = np.mean(col == 0.0)
        assert zero_frac > 0.5  # Most problems have no prize


# ── discover_archetypes ──────────────────────────────────────────────

class TestDiscoverArchetypes:
    """Test k-means archetype clustering."""

    def test_returns_list(self, archetypes):
        assert isinstance(archetypes, list)

    def test_expected_count(self, archetypes):
        assert len(archetypes) == 8

    def test_sorted_by_size(self, archetypes):
        for i in range(len(archetypes) - 1):
            assert archetypes[i]["size"] >= archetypes[i + 1]["size"]

    def test_covers_all_problems(self, archetypes, problems):
        total = sum(a["size"] for a in archetypes)
        assert total == len(problems)

    def test_no_member_overlap(self, archetypes):
        seen = set()
        for a in archetypes:
            for m in a["members"]:
                assert m not in seen
                seen.add(m)

    def test_solve_rate_bounded(self, archetypes):
        for a in archetypes:
            assert 0.0 <= a["solve_rate"] <= 1.0

    def test_has_centroid(self, archetypes):
        for a in archetypes:
            assert "centroid" in a
            assert len(a["centroid"]) == 9

    def test_centroid_reasonable(self, archetypes):
        for a in archetypes:
            for dim, val in a["centroid"].items():
                assert not math.isnan(val)

    def test_has_top_tags(self, archetypes):
        for a in archetypes:
            assert isinstance(a["top_tags"], list)
            assert len(a["top_tags"]) > 0

    def test_representative_in_members(self, archetypes):
        for a in archetypes:
            assert a["representative"] in a["members"]

    def test_custom_n_clusters(self, problems, signal_space):
        result = discover_archetypes(problems, signal_space, n_clusters=4)
        assert len(result) == 4

    def test_open_count_nonneg(self, archetypes):
        for a in archetypes:
            assert a["open_count"] >= 0


# ── find_blindspots ──────────────────────────────────────────────────

class TestFindBlindspots:
    """Test analytical blindspot detection."""

    def test_returns_list(self, problems, signal_space):
        result = find_blindspots(problems, signal_space)
        assert isinstance(result, list)

    def test_sorted_by_gap(self, problems, signal_space):
        result = find_blindspots(problems, signal_space)
        for i in range(len(result) - 1):
            assert result[i]["gap"] >= result[i + 1]["gap"] - 1e-6

    def test_gap_positive(self, problems, signal_space):
        result = find_blindspots(problems, signal_space)
        for b in result:
            assert b["gap"] > 0

    def test_only_open_problems(self, problems, signal_space):
        result = find_blindspots(problems, signal_space)
        prob_by_num = {int(p.get("number", 0)): p for p in problems
                       if str(p.get("number", "")).isdigit()}
        for b in result:
            p = prob_by_num.get(b["number"])
            if p:
                assert p.get("status", {}).get("state") == "open"

    def test_fields_present(self, problems, signal_space):
        result = find_blindspots(problems, signal_space)
        for b in result:
            assert "number" in b
            assert "importance" in b
            assert "tractability" in b
            assert "gap" in b
            assert "tags" in b


# ── solve_similarity ─────────────────────────────────────────────────

class TestSolveSimilarity:
    """Test solve-similarity computation."""

    def test_returns_list(self, problems, signal_space):
        result = solve_similarity(problems, signal_space)
        assert isinstance(result, list)

    def test_respects_top_k(self, problems, signal_space):
        result = solve_similarity(problems, signal_space, top_k=10)
        assert len(result) <= 10

    def test_sorted_by_distance(self, problems, signal_space):
        result = solve_similarity(problems, signal_space)
        for i in range(len(result) - 1):
            assert result[i]["distance"] <= result[i + 1]["distance"] + 1e-6

    def test_distance_positive(self, problems, signal_space):
        result = solve_similarity(problems, signal_space)
        for s in result:
            assert s["distance"] >= 0

    def test_nearest_is_solved(self, problems, signal_space):
        result = solve_similarity(problems, signal_space)
        prob_by_num = {int(p.get("number", 0)): p for p in problems
                       if str(p.get("number", "")).isdigit()}
        for s in result:
            nearest = prob_by_num.get(s["nearest_solved"])
            if nearest:
                status = nearest.get("status", {}).get("state", "")
                assert status in ("proved", "disproved", "solved",
                                  "proved (Lean)", "disproved (Lean)", "solved (Lean)")

    def test_fields_present(self, problems, signal_space):
        result = solve_similarity(problems, signal_space)
        for s in result:
            assert "number" in s
            assert "distance" in s
            assert "nearest_solved" in s
            assert "shared_tags" in s
            assert "n_shared_tags" in s


# ── tag_archetype_map ────────────────────────────────────────────────

class TestTagArchetypeMap:
    """Test tag-archetype mapping."""

    def test_returns_list(self, problems, archetypes):
        result = tag_archetype_map(problems, archetypes)
        assert isinstance(result, list)

    def test_has_mappings(self, problems, archetypes):
        result = tag_archetype_map(problems, archetypes)
        assert len(result) > 10

    def test_sorted_by_concentration(self, problems, archetypes):
        result = tag_archetype_map(problems, archetypes)
        for i in range(len(result) - 1):
            assert result[i]["concentration"] >= result[i + 1]["concentration"] - 1e-6

    def test_concentration_bounded(self, problems, archetypes):
        result = tag_archetype_map(problems, archetypes)
        for t in result:
            assert 0.0 < t["concentration"] <= 1.0

    def test_fields_present(self, problems, archetypes):
        result = tag_archetype_map(problems, archetypes)
        for t in result:
            assert "tag" in t
            assert "primary_archetype" in t
            assert "concentration" in t
            assert "total_count" in t

    def test_min_count(self, problems, archetypes):
        result = tag_archetype_map(problems, archetypes)
        for t in result:
            assert t["total_count"] >= 3


# ── prize_efficiency ─────────────────────────────────────────────────

class TestPrizeEfficiency:
    """Test prize efficiency computation."""

    def test_returns_list(self, problems, archetypes):
        result = prize_efficiency(problems, archetypes)
        assert isinstance(result, list)

    def test_count_matches_archetypes(self, problems, archetypes):
        result = prize_efficiency(problems, archetypes)
        assert len(result) == len(archetypes)

    def test_sorted_by_efficiency(self, problems, archetypes):
        result = prize_efficiency(problems, archetypes)
        for i in range(len(result) - 1):
            assert result[i]["efficiency"] >= result[i + 1]["efficiency"] - 1e-6

    def test_efficiency_nonneg(self, problems, archetypes):
        result = prize_efficiency(problems, archetypes)
        for e in result:
            assert e["efficiency"] >= 0

    def test_fields_present(self, problems, archetypes):
        result = prize_efficiency(problems, archetypes)
        for e in result:
            assert "archetype_id" in e
            assert "size" in e
            assert "efficiency" in e
            assert "prize_total" in e
            assert "top_tags" in e
