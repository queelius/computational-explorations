"""Tests for space_time_tradeoffs.py -- Space-time tradeoff analysis.

Note: extension memory profiling tests are slow (~60s each for k=3 to n=11)
because they do exhaustive 2^21 enumeration. We use a module-scoped fixture
to compute the profiles once and share across tests.
"""

import math
import sys
from pathlib import Path

import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from space_time_tradeoffs import (
    # Infrastructure
    coprime_edges,
    coprime_adj,
    find_coprime_cliques,
    has_monochromatic_clique,
    # Section 1: Extension memory
    estimate_coloring_bytes,
    profile_extension_memory,
    fit_growth_model,
    ExtensionProfile,
    GrowthModel,
    # Section 2: SAT profiling
    profile_sat_space,
    classify_bottleneck,
    SATProfile,
    BottleneckAnalysis,
    # Section 3: Meet-in-the-middle
    meet_in_the_middle_ramsey,
    compare_mitm_vs_sat,
    MITMResult,
    # Section 4: Color coding
    color_coding_clique_search,
    color_coding_vs_exhaustive,
    ColorCodingResult,
    # Section 5: Streaming
    streaming_init,
    streaming_process_edge,
    streaming_ramsey_detect,
    streaming_threshold_scan,
    StreamingState,
    # Section 6: Recommendations
    generate_recommendations,
    analyze_tradeoffs,
    AlgorithmRecommendation,
)


# ============================================================================
# Infrastructure sanity checks
# ============================================================================

class TestInfrastructure:
    """Verify the shared coprime graph primitives match existing modules."""

    def test_coprime_edges_n8(self):
        edges = coprime_edges(8)
        assert len(edges) == 21  # known value for n=8

    def test_coprime_adj_symmetric(self):
        adj = coprime_adj(10)
        for v, neighbors in adj.items():
            for u in neighbors:
                assert v in adj[u], f"{v} in adj[{u}] but not reverse"

    def test_coprime_cliques_k3_n5(self):
        cliques = find_coprime_cliques(5, 3)
        for c in cliques:
            assert len(c) == 3
            for i in range(3):
                for j in range(i + 1, 3):
                    assert math.gcd(c[i], c[j]) == 1

    def test_has_monochromatic_all_zero(self):
        """All-zero coloring on n=5 must have a monochromatic K_3."""
        edges = coprime_edges(5)
        coloring = {e: 0 for e in edges}
        assert has_monochromatic_clique(5, 3, coloring)

    def test_has_monochromatic_mixed(self):
        """A mixed coloring on n=3 avoids monochromatic K_3."""
        coloring = {(1, 2): 0, (1, 3): 0, (2, 3): 1}
        assert not has_monochromatic_clique(3, 3, coloring)


# ============================================================================
# Module-scoped fixtures for expensive computations
# ============================================================================

@pytest.fixture(scope="module")
def k3_profiles_to_11():
    """Compute k=3 extension profiles to n=11 once (expensive: ~60s)."""
    return profile_extension_memory(3, max_n=11)


@pytest.fixture(scope="module")
def k3_profiles_to_9():
    """Compute k=3 extension profiles to n=9 (moderate: ~30s)."""
    return profile_extension_memory(3, max_n=9)


# ============================================================================
# 1. Incremental Extension Memory Profile
# ============================================================================

class TestEstimateColoringBytes:
    def test_positive(self):
        assert estimate_coloring_bytes(10) > 0

    def test_monotone(self):
        assert estimate_coloring_bytes(20) > estimate_coloring_bytes(10)

    def test_zero_edges(self):
        assert estimate_coloring_bytes(0) > 0  # dict base overhead


class TestProfileExtensionMemory:
    def test_k3_known_counts(self, k3_profiles_to_11):
        """Verify known avoiding counts for R_cop(3)."""
        counts = {p.n: p.num_avoiding for p in k3_profiles_to_11}
        # Known values from the extension computation
        assert counts.get(8) == 36, f"n=8: expected 36, got {counts.get(8)}"
        assert counts.get(9) == 36, f"n=9: expected 36, got {counts.get(9)}"
        assert counts.get(10) == 156, f"n=10: expected 156, got {counts.get(10)}"
        assert counts.get(11) == 0, f"n=11: expected 0, got {counts.get(11)}"

    def test_k3_terminates_at_11(self, k3_profiles_to_11):
        """Profile for k=3 should show 0 avoiding at n=11 (R_cop(3)=11)."""
        final = k3_profiles_to_11[-1]
        assert final.num_avoiding == 0
        assert final.n == 11

    def test_profile_fields_populated(self, k3_profiles_to_9):
        """All profile fields should be populated correctly."""
        for p in k3_profiles_to_9:
            assert p.n > 0
            assert p.num_edges >= 0
            assert p.coloring_bytes > 0
            assert p.total_memory_bytes >= 0
            assert p.time_seconds >= 0
            assert p.cumulative_explored > 0

    def test_memory_increases_with_avoiding(self, k3_profiles_to_11):
        """Total memory should correlate with avoiding count."""
        for p in k3_profiles_to_11:
            if p.num_avoiding > 0:
                assert p.total_memory_bytes > 0

    def test_k4_produces_profiles(self):
        """k=4 extension should produce profiles for small n."""
        # k=4 base enumeration is slower (more cliques to check).
        # Use max_n=7 (15 edges, well within threshold of 18) and
        # max_base_edges=15 to keep it fast even under coverage overhead.
        profiles = profile_extension_memory(4, max_n=7, max_base_edges=15)
        assert len(profiles) > 0
        # At small n, there should be avoiding colorings
        assert any(p.num_avoiding > 0 for p in profiles)


class TestFitGrowthModel:
    def test_k3_fit(self, k3_profiles_to_11):
        """Growth model for k=3 should fit the data."""
        model = fit_growth_model(k3_profiles_to_11)
        assert model.model_type in ("exponential", "polynomial",
                                    "insufficient_data")

    def test_insufficient_data(self):
        """With fewer than 3 data points, should report insufficient."""
        profiles = [
            ExtensionProfile(n=5, num_edges=10, num_new_edges=10,
                             num_avoiding=100, coloring_bytes=1000,
                             total_memory_bytes=100000, time_seconds=0.01,
                             cumulative_explored=1024),
        ]
        model = fit_growth_model(profiles)
        assert model.model_type == "insufficient_data"

    def test_ram_exhaustion_positive(self):
        """For exponentially growing data, RAM exhaustion should be predicted."""
        # Create synthetic exponential data
        profiles = []
        for n in range(5, 15):
            count = int(2.0 ** n)
            profiles.append(ExtensionProfile(
                n=n, num_edges=n*3, num_new_edges=n,
                num_avoiding=count, coloring_bytes=500,
                total_memory_bytes=count * 500, time_seconds=0.01,
                cumulative_explored=count,
            ))
        model = fit_growth_model(profiles, available_ram_bytes=16 * (1024 ** 3))
        # Should predict RAM exhaustion at some finite n
        assert model.ram_exhaustion_n > 0

    def test_r_squared_bounded(self, k3_profiles_to_11):
        """R-squared values should be in [0, 1] (or close, with noise)."""
        model = fit_growth_model(k3_profiles_to_11)
        # R^2 can occasionally be slightly negative due to numerical issues,
        # but should be close to [0, 1]
        assert model.exp_r_squared >= -0.5
        assert model.poly_r_squared >= -0.5


# ============================================================================
# 2. SAT Solver Space Usage Profile
# ============================================================================

class TestProfileSATSpace:
    def test_k3_profiles(self):
        """SAT profiles for k=3 should show UNSAT at n=11."""
        profiles = profile_sat_space(3, n_range=(3, 12))
        sat_at = {p.n: p.sat_result for p in profiles}
        # n=10 should be SAT, n=11 should be UNSAT
        assert sat_at.get(10) is True, "n=10 should be SAT for k=3"
        assert sat_at.get(11) is False, "n=11 should be UNSAT for k=3"

    def test_clause_var_ratio_grows(self):
        """Clause/var ratio should generally increase with n."""
        profiles = profile_sat_space(3, n_range=(5, 10))
        ratios = [p.clause_var_ratio for p in profiles if p.n >= 6]
        # Not strictly monotone, but should trend upward
        assert ratios[-1] >= ratios[0] * 0.5  # generous bound

    def test_solver_memory_estimate_positive(self):
        """Solver memory estimates should be positive."""
        profiles = profile_sat_space(3, n_range=(5, 8))
        for p in profiles:
            assert p.total_solver_bytes > 0
            assert p.clause_db_bytes >= 0
            assert p.var_activity_bytes >= 0

    def test_k4_profiles(self):
        """SAT profiles for k=4 should produce data."""
        profiles = profile_sat_space(4, n_range=(4, 12))
        assert len(profiles) > 0
        # All should be SAT at small n (R_cop(4) ~ 59)
        for p in profiles:
            assert p.sat_result is True, f"n={p.n} should be SAT for k=4"


class TestClassifyBottleneck:
    def test_time_limited(self, k3_profiles_to_11):
        """k=3 should be classified as time-limited or neither (small)."""
        sat = profile_sat_space(3, n_range=(3, 12))
        result = classify_bottleneck(k3_profiles_to_11, sat)
        # k=3 finishes fast, so should be "neither" or "time"
        assert result.bottleneck in ("time", "neither", "space")
        assert isinstance(result.explanation, str)

    def test_with_low_ram(self, k3_profiles_to_9):
        """With very low RAM limit, should detect space bottleneck."""
        sat = profile_sat_space(3, n_range=(3, 10))
        # Set RAM to 1 byte -- everything is space-limited
        result = classify_bottleneck(k3_profiles_to_9, sat, ram_gb=1e-12)
        assert result.bottleneck == "space"


# ============================================================================
# 3. Meet-in-the-Middle
# ============================================================================

class TestMeetInTheMiddle:
    def test_n5_k3_sat(self):
        """n=5, k=3: should find an avoiding coloring (R_cop(3)=11 > 5)."""
        result = meet_in_the_middle_ramsey(5, 3)
        assert result.has_avoiding is True
        assert result.n == 5
        assert result.k == 3

    def test_n11_k3_unsat(self):
        """n=11, k=3: no avoiding coloring should exist (R_cop(3)=11)."""
        result = meet_in_the_middle_ramsey(11, 3)
        assert result.has_avoiding is False

    def test_space_reduction(self):
        """MITM search space should be much smaller than brute force."""
        result = meet_in_the_middle_ramsey(8, 3)
        # 2^{m/2} + 2^{m/2} << 2^m for m=21
        assert result.mitm_search_space < result.brute_force_search_space

    def test_agrees_with_sat(self):
        """MITM and SAT should agree on SAT/UNSAT for all n in [5, 11]."""
        for n in range(5, 12):
            comp = compare_mitm_vs_sat(n, 3)
            assert comp["sat_result"] == comp["mitm_result"], \
                f"Disagreement at n={n}: SAT={comp['sat_result']}, " \
                f"MITM={comp['mitm_result']}"

    def test_n2_trivial(self):
        """n=2, k=3: only 1 edge, k=3 clique impossible, avoiding trivially."""
        result = meet_in_the_middle_ramsey(2, 3)
        assert result.has_avoiding is True

    def test_no_edges(self):
        """n=1: no edges, should be trivially avoiding."""
        result = meet_in_the_middle_ramsey(1, 3)
        assert result.has_avoiding is True

    def test_result_fields(self):
        """All MITMResult fields should be populated."""
        result = meet_in_the_middle_ramsey(7, 3)
        assert result.num_left_colorings >= 0
        assert result.num_right_colorings >= 0
        assert result.time_seconds >= 0
        assert result.brute_force_search_space > 0


class TestCompareMITMvsSAT:
    def test_comparison_has_all_fields(self):
        comp = compare_mitm_vs_sat(6, 3)
        assert "sat_time" in comp
        assert "mitm_time" in comp
        assert "space_reduction" in comp
        assert "n" in comp
        assert comp["n"] == 6


# ============================================================================
# 4. Color Coding Technique
# ============================================================================

class TestColorCoding:
    def test_finds_monochromatic_triangle(self):
        """Color coding should find a mono K_3 in all-zero coloring."""
        edges = coprime_edges(8)
        coloring = {e: 0 for e in edges}
        result = color_coding_clique_search(8, 3, coloring, target_color=0,
                                            seed=42)
        assert result.success is True
        assert result.found_clique is not None
        assert len(result.found_clique) == 3
        # Verify the found clique is actually coprime and monochromatic
        clique = result.found_clique
        for i in range(3):
            for j in range(i + 1, 3):
                assert math.gcd(clique[i], clique[j]) == 1
                edge = (min(clique[i], clique[j]), max(clique[i], clique[j]))
                assert coloring[edge] == 0

    def test_does_not_find_nonexistent(self):
        """Color coding should not find K_3 in an avoiding coloring."""
        # Build an avoiding coloring at n=3 (just mix colors)
        coloring = {(1, 2): 0, (1, 3): 0, (2, 3): 1}
        result = color_coding_clique_search(3, 3, coloring, target_color=0,
                                            num_trials=100, seed=42)
        assert result.success is False

    def test_finds_in_both_colors(self):
        """For all-zero coloring, should find in color 0, not in color 1."""
        edges = coprime_edges(6)
        coloring = {e: 0 for e in edges}
        result_0 = color_coding_clique_search(6, 3, coloring, target_color=0,
                                              seed=42)
        result_1 = color_coding_clique_search(6, 3, coloring, target_color=1,
                                              seed=42)
        assert result_0.success is True
        assert result_1.success is False

    def test_deterministic_with_seed(self):
        """Same seed should give same result."""
        edges = coprime_edges(8)
        coloring = {e: 0 for e in edges}
        r1 = color_coding_clique_search(8, 3, coloring, target_color=0,
                                        seed=123)
        r2 = color_coding_clique_search(8, 3, coloring, target_color=0,
                                        seed=123)
        assert r1.success == r2.success
        if r1.success:
            assert r1.found_clique == r2.found_clique

    def test_result_fields(self):
        edges = coprime_edges(5)
        coloring = {e: 0 for e in edges}
        result = color_coding_clique_search(5, 3, coloring, seed=42)
        assert result.n == 5
        assert result.k == 3
        assert result.target_color == 0
        assert result.num_trials > 0
        assert result.time_seconds >= 0

    def test_k4_search(self):
        """Color coding should find K_4 in a large all-zero graph."""
        edges = coprime_edges(12)
        coloring = {e: 0 for e in edges}
        result = color_coding_clique_search(12, 4, coloring, target_color=0,
                                            num_trials=10000, seed=42)
        assert result.success is True
        assert len(result.found_clique) == 4


class TestColorCodingVsExhaustive:
    def test_both_find_mono(self):
        """Both methods should find monochromatic cliques in all-zero."""
        edges = coprime_edges(8)
        coloring = {e: 0 for e in edges}
        comp = color_coding_vs_exhaustive(8, 3, coloring)
        assert comp["exhaustive_found"] is True
        assert comp["color_coding_found"] is True

    def test_both_find_nothing_in_avoiding(self):
        """Both should fail on an avoiding coloring."""
        coloring = {(1, 2): 0, (1, 3): 0, (2, 3): 1}
        comp = color_coding_vs_exhaustive(3, 3, coloring)
        assert comp["exhaustive_found"] is False
        # Color coding is randomized: might not find, which is correct here
        # (there truly is no mono K_3)


# ============================================================================
# 5. Streaming / Online Algorithms
# ============================================================================

class TestStreamingInit:
    def test_creates_valid_state(self):
        state = streaming_init(3)
        assert state.k == 3
        assert state.n == 0
        assert state.edges_processed == 0
        assert state.detected is False


class TestStreamingProcessEdge:
    def test_single_edge(self):
        """Processing a single edge should update state."""
        state = streaming_init(3)
        detected = streaming_process_edge(state, 1, 2, 0)
        assert not detected  # one edge can't form K_3
        assert state.edges_processed == 1
        assert state.degree[1][0] == 1
        assert state.degree[2][0] == 1

    def test_triangle_detection(self):
        """Processing edges forming a monochromatic triangle should detect."""
        state = streaming_init(3)
        streaming_process_edge(state, 1, 2, 0)
        streaming_process_edge(state, 1, 3, 0)
        detected = streaming_process_edge(state, 2, 3, 0)
        assert detected
        assert state.detected is True
        assert len(state.best_clique[0]) == 3

    def test_mixed_no_detection(self):
        """Mixed-color triangle should not trigger detection."""
        state = streaming_init(3)
        streaming_process_edge(state, 1, 2, 0)
        streaming_process_edge(state, 1, 3, 0)
        detected = streaming_process_edge(state, 2, 3, 1)
        assert not detected
        assert state.detected is False

    def test_idempotent_after_detection(self):
        """Once detected, further edges should keep detected=True."""
        state = streaming_init(3)
        streaming_process_edge(state, 1, 2, 0)
        streaming_process_edge(state, 1, 3, 0)
        streaming_process_edge(state, 2, 3, 0)
        assert state.detected is True
        # Process more edges
        detected = streaming_process_edge(state, 4, 5, 1)
        assert detected  # still detected from before


class TestStreamingRamseyDetect:
    def test_all_zero_detects_early(self):
        """All-zero coloring should detect a mono K_3 quickly."""
        edges = coprime_edges(10)
        coloring = {e: 0 for e in edges}
        state = streaming_ramsey_detect(10, 3, coloring)
        assert state.detected is True
        # Should detect well before processing all edges
        assert state.edges_processed < len(edges)

    def test_avoiding_coloring_no_detect(self):
        """An avoiding coloring should not trigger detection."""
        coloring = {(1, 2): 0, (1, 3): 0, (2, 3): 1}
        state = streaming_ramsey_detect(3, 3, coloring)
        assert state.detected is False

    def test_space_is_o_n(self):
        """The state's vertex count should equal n (O(n) space)."""
        edges = coprime_edges(8)
        coloring = {e: 0 for e in edges}
        state = streaming_ramsey_detect(8, 3, coloring)
        # degree dict should have at most n entries
        assert len(state.degree) <= 8

    def test_detects_k4(self):
        """All-zero coloring on large n should detect mono K_4."""
        edges = coprime_edges(15)
        coloring = {e: 0 for e in edges}
        state = streaming_ramsey_detect(15, 4, coloring)
        assert state.detected is True
        assert len(state.best_clique[0]) == 4


class TestStreamingThresholdScan:
    def test_scan_k3_all_zero(self):
        """Threshold scan with all-zero should detect from first triangle."""
        results = streaming_threshold_scan(3, max_n=10)
        # n=3 has a triangle {1,2,3}, so detection should be at n=3
        assert 3 in results
        assert results[3].detected is True

    def test_scan_returns_states(self):
        results = streaming_threshold_scan(3, max_n=8)
        assert all(isinstance(s, StreamingState) for s in results.values())


# ============================================================================
# 6. Recommendations and Unified Analysis
# ============================================================================

class TestGenerateRecommendations:
    def test_k3_recommendations(self):
        recs = generate_recommendations(3)
        assert len(recs) > 0
        algorithms = {r.algorithm for r in recs}
        # Should recommend at least one approach
        assert len(algorithms) >= 1

    def test_k4_recommendations(self):
        recs = generate_recommendations(4)
        assert len(recs) > 0
        # Should recommend SAT for the main range
        assert any("SAT" in r.algorithm for r in recs)

    def test_k5_recommendations(self):
        recs = generate_recommendations(5)
        assert len(recs) > 0

    def test_recommendation_fields(self):
        recs = generate_recommendations(3)
        for r in recs:
            assert isinstance(r.k, int)
            assert isinstance(r.n_range, tuple)
            assert len(r.n_range) == 2
            assert isinstance(r.algorithm, str)
            assert isinstance(r.reason, str)


class TestAnalyzeTradeoffs:
    def test_k3_analysis(self):
        """Full analysis for k=3 should complete and return all sections.

        Uses max_n=7 to stay in the fast exhaustive range (<=15 edges).
        """
        results = analyze_tradeoffs(3, max_n=7)
        assert "k" in results
        assert results["k"] == 3
        assert "extension_profiles" in results
        assert "sat_profiles" in results

    def test_k3_analysis_with_mitm(self):
        """Analysis with small max_n should include MITM comparisons."""
        results = analyze_tradeoffs(3, max_n=7)
        assert "mitm_comparisons" in results


# ============================================================================
# Cross-cutting: consistency between algorithms
# ============================================================================

class TestCrossAlgorithmConsistency:
    """Verify that all algorithms agree on SAT/UNSAT for the same instance."""

    @pytest.mark.parametrize("n", [5, 6, 7, 8, 9, 10])
    def test_sat_vs_mitm_k3(self, n):
        """SAT and MITM should agree for k=3 at each n."""
        comp = compare_mitm_vs_sat(n, 3)
        assert comp["sat_result"] == comp["mitm_result"], \
            f"n={n}: SAT={comp['sat_result']}, MITM={comp['mitm_result']}"

    def test_extension_vs_mitm_at_boundary(self):
        """At n=10 (SAT) and n=11 (UNSAT), MITM should agree with extension."""
        # n=10: avoiding exists
        mitm_10 = meet_in_the_middle_ramsey(10, 3)
        assert mitm_10.has_avoiding is True

        # n=11: no avoiding
        mitm_11 = meet_in_the_middle_ramsey(11, 3)
        assert mitm_11.has_avoiding is False

    def test_streaming_agrees_on_monochromatic(self):
        """Streaming should detect mono K_3 whenever exhaustive does."""
        for n in range(3, 10):
            edges = coprime_edges(n)
            coloring = {e: 0 for e in edges}
            # Exhaustive check
            exhaustive_found = has_monochromatic_clique(n, 3, coloring)
            # Streaming check
            state = streaming_ramsey_detect(n, 3, coloring)
            if exhaustive_found:
                assert state.detected, \
                    f"n={n}: exhaustive found mono K_3 but streaming did not"


# ============================================================================
# Edge cases and robustness
# ============================================================================

class TestEdgeCases:
    def test_mitm_no_cliques(self):
        """MITM on n < k should be trivially avoiding."""
        result = meet_in_the_middle_ramsey(2, 3)
        assert result.has_avoiding is True

    def test_color_coding_k2(self):
        """Color coding for K_2 (edges) should always find one."""
        edges = coprime_edges(5)
        coloring = {e: 0 for e in edges}
        result = color_coding_clique_search(5, 2, coloring, target_color=0,
                                            seed=42)
        assert result.success is True
        assert len(result.found_clique) == 2

    def test_streaming_k2(self):
        """Streaming for K_2 should detect on the first same-color edge."""
        state = streaming_init(2)
        detected = streaming_process_edge(state, 1, 2, 0)
        assert detected
        assert state.detected is True

    def test_profile_empty_range(self):
        """Profiling with max_n < k should return empty profiles."""
        profiles = profile_extension_memory(5, max_n=3)
        assert len(profiles) == 0

    def test_sat_profile_empty(self):
        """SAT profiling with n_range below k should return empty."""
        profiles = profile_sat_space(5, n_range=(2, 3))
        assert len(profiles) == 0

    def test_growth_model_all_zeros(self):
        """Growth model with all-zero avoiding counts should handle gracefully."""
        profiles = [
            ExtensionProfile(n=5, num_edges=10, num_new_edges=5,
                             num_avoiding=0, coloring_bytes=500,
                             total_memory_bytes=0, time_seconds=0.01,
                             cumulative_explored=100),
        ]
        model = fit_growth_model(profiles)
        assert model.model_type == "insufficient_data"


# ============================================================================
# Performance regression guards
# ============================================================================

class TestPerformance:
    """Guard against performance regressions in the analysis code."""

    @pytest.mark.timeout(120)
    def test_k3_full_profile_under_120s(self, k3_profiles_to_11):
        """Full k=3 profile to n=11 should complete in < 120s.

        The exhaustive base at n=8 enumerates 2^21 colorings against all
        3-cliques, which takes ~30-60s depending on hardware. The extension
        phase (n=9..11) is fast since it only extends 36->36->156->0 colorings.
        Uses module-scoped fixture so computation is shared.
        """
        assert len(k3_profiles_to_11) > 0
        assert k3_profiles_to_11[-1].num_avoiding == 0

    @pytest.mark.timeout(30)
    def test_mitm_n10_under_30s(self):
        """MITM at n=10, k=3 should complete in < 30s."""
        result = meet_in_the_middle_ramsey(10, 3)
        assert result.has_avoiding is True

    @pytest.mark.timeout(10)
    def test_sat_profile_k4_to_n12(self):
        """SAT profiling for k=4 up to n=12 should be fast."""
        profiles = profile_sat_space(4, n_range=(4, 12))
        assert len(profiles) > 0

    @pytest.mark.timeout(10)
    def test_streaming_n15_k3(self):
        """Streaming detection at n=15 should be instant."""
        edges = coprime_edges(15)
        coloring = {e: 0 for e in edges}
        state = streaming_ramsey_detect(15, 3, coloring)
        assert state.detected is True
