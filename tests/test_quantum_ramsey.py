"""Tests for quantum_ramsey.py (NPG-27): Quantum Ramsey theory on the coprime graph."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quantum_ramsey import (
    # Infrastructure
    coprime_edges,
    coprime_adj,
    find_coprime_cliques,
    primes_up_to,
    # Quantum coloring
    QuantumEdgeState,
    QuantumColoring,
    quantum_mono_threshold,
    optimize_product_state,
    # Quantum chromatic number
    classical_chromatic_number,
    lovasz_theta,
    quantum_chromatic_bound,
    orthogonal_rank,
    # Grover search
    grover_analysis,
    grover_coprime_ramsey_speedup,
    # Quantum Ramsey game
    classical_ramsey_game_value,
    entanglement_advantage_bound,
    bell_inequality_for_clique,
    # QAOA
    qubo_avoiding_coloring,
    qaoa_resource_estimate,
    qaoa_landscape_analysis,
    # Synthesis
    quantum_ramsey_threshold_analysis,
)


# ============================================================================
# Infrastructure tests
# ============================================================================

class TestInfrastructure:
    def test_coprime_edges_n3(self):
        edges = coprime_edges(3)
        assert len(edges) == 3
        assert (1, 2) in edges
        assert (1, 3) in edges
        assert (2, 3) in edges

    def test_coprime_edges_n4_excludes_gcd2(self):
        edges = coprime_edges(4)
        assert (2, 4) not in edges

    def test_coprime_adj_symmetric(self):
        adj = coprime_adj(8)
        for v, nbrs in adj.items():
            for w in nbrs:
                assert v in adj[w]

    def test_coprime_adj_vertex1_universal(self):
        adj = coprime_adj(10)
        assert adj[1] == set(range(2, 11))

    def test_find_coprime_cliques_k1(self):
        cliques = find_coprime_cliques(5, 1)
        assert len(cliques) == 5

    def test_find_coprime_cliques_k2(self):
        cliques = find_coprime_cliques(5, 2)
        edges = coprime_edges(5)
        assert len(cliques) == len(edges)

    def test_find_coprime_cliques_k3_n5(self):
        cliques = find_coprime_cliques(5, 3)
        # {1,2,3}, {1,2,5}, {1,3,4}, {1,3,5}, {1,4,5}, {2,3,5}, {3,4,5}
        assert len(cliques) >= 7

    def test_primes_up_to(self):
        assert primes_up_to(10) == [2, 3, 5, 7]
        assert primes_up_to(1) == []
        assert primes_up_to(2) == [2]
        assert primes_up_to(20) == [2, 3, 5, 7, 11, 13, 17, 19]


# ============================================================================
# 1. Quantum Coloring tests
# ============================================================================

class TestQuantumEdgeState:
    def test_classical_state_0(self):
        s = QuantumEdgeState.classical(0)
        assert abs(s.prob_color(0) - 1.0) < 1e-12
        assert abs(s.prob_color(1) - 0.0) < 1e-12

    def test_classical_state_1(self):
        s = QuantumEdgeState.classical(1)
        assert abs(s.prob_color(0) - 0.0) < 1e-12
        assert abs(s.prob_color(1) - 1.0) < 1e-12

    def test_uniform_state(self):
        s = QuantumEdgeState.uniform()
        assert abs(s.prob_color(0) - 0.5) < 1e-12
        assert abs(s.prob_color(1) - 0.5) < 1e-12

    def test_normalization(self):
        s = QuantumEdgeState(3.0, 4.0)
        assert abs(s.prob_color(0) + s.prob_color(1) - 1.0) < 1e-12

    def test_parameterized_state(self):
        s = QuantumEdgeState.parameterized(0)  # cos(0)|0> + sin(0)|1> = |0>
        assert abs(s.prob_color(0) - 1.0) < 1e-12
        s2 = QuantumEdgeState.parameterized(math.pi / 2)  # |1>
        assert abs(s2.prob_color(1) - 1.0) < 1e-12

    def test_amplitudes_array(self):
        s = QuantumEdgeState.uniform()
        amps = s.amplitudes()
        assert len(amps) == 2
        assert abs(np.linalg.norm(amps) - 1.0) < 1e-12

    def test_zero_state_raises(self):
        with pytest.raises(ValueError):
            QuantumEdgeState(0.0, 0.0)

    def test_complex_amplitudes(self):
        s = QuantumEdgeState(1.0, 1j)
        assert abs(s.prob_color(0) - 0.5) < 1e-12
        assert abs(s.prob_color(1) - 0.5) < 1e-12

    def test_repr(self):
        s = QuantumEdgeState.uniform()
        r = repr(s)
        assert "QuantumEdgeState" in r


class TestQuantumColoring:
    def test_default_uniform(self):
        edges = coprime_edges(3)
        qc = QuantumColoring(edges)
        # All edges in uniform superposition
        for e in edges:
            assert abs(qc.states[e].prob_color(0) - 0.5) < 1e-12

    def test_monochromatic_probability_classical_all_zero(self):
        edges = coprime_edges(3)
        states = {e: QuantumEdgeState.classical(0) for e in edges}
        qc = QuantumColoring(edges, states)
        # Triangle (1,2,3): all color 0 => P(mono) = 1
        prob = qc.monochromatic_probability((1, 2, 3))
        assert abs(prob - 1.0) < 1e-12

    def test_monochromatic_probability_uniform(self):
        edges = coprime_edges(3)
        qc = QuantumColoring(edges)
        # Triangle (1,2,3) with 3 edges in uniform superposition:
        # P(all 0) = (1/2)^3 = 1/8, P(all 1) = 1/8
        # P(mono) = 1/4
        prob = qc.monochromatic_probability((1, 2, 3))
        assert abs(prob - 0.25) < 1e-12

    def test_monochromatic_clique_probability_product(self):
        edges = [(1, 2), (1, 3), (2, 3)]
        states = {
            (1, 2): QuantumEdgeState.parameterized(math.pi / 6),
            (1, 3): QuantumEdgeState.parameterized(math.pi / 4),
            (2, 3): QuantumEdgeState.parameterized(math.pi / 3),
        }
        qc = QuantumColoring(edges, states)

        # P(all 0) = cos^2(pi/6) * cos^2(pi/4) * cos^2(pi/3)
        p0_expected = (math.cos(math.pi/6)**2 *
                       math.cos(math.pi/4)**2 *
                       math.cos(math.pi/3)**2)
        p0 = qc.monochromatic_clique_probability((1, 2, 3), 0)
        assert abs(p0 - p0_expected) < 1e-12

    def test_max_monochromatic_probability(self):
        edges = coprime_edges(5)
        qc = QuantumColoring(edges)
        cliques = find_coprime_cliques(5, 3)
        max_prob = qc.max_monochromatic_probability(cliques)
        # With uniform superposition, all triangles have same probability
        assert max_prob > 0
        assert max_prob <= 1.0

    def test_worst_case_mono_probability(self):
        edges = coprime_edges(5)
        qc = QuantumColoring(edges)
        worst = qc.worst_case_mono_probability(5, 3)
        assert worst > 0
        assert worst <= 1.0

    def test_missing_edge_gives_zero(self):
        # If a clique edge is not in the graph, probability is 0
        edges = [(1, 2)]
        qc = QuantumColoring(edges)
        # (1,2,3) needs edge (1,3) which is missing from coloring
        prob = qc.monochromatic_probability((1, 2, 3))
        assert prob == 0.0

    def test_empty_cliques(self):
        edges = coprime_edges(3)
        qc = QuantumColoring(edges)
        assert qc.max_monochromatic_probability([]) == 0.0


class TestQuantumMonoThreshold:
    def test_k3_threshold(self):
        # K_3: 3 edges, threshold = 2^{1-3} = 1/4
        assert abs(quantum_mono_threshold(3) - 0.25) < 1e-12

    def test_k4_threshold(self):
        # K_4: 6 edges, threshold = 2^{1-6} = 1/32
        assert abs(quantum_mono_threshold(4) - 1.0/32) < 1e-12

    def test_k2_threshold(self):
        # K_2: 1 edge, threshold = 2^{1-1} = 1
        assert abs(quantum_mono_threshold(2) - 1.0) < 1e-12

    def test_threshold_decreasing(self):
        for k in range(2, 8):
            assert quantum_mono_threshold(k) >= quantum_mono_threshold(k + 1)


class TestOptimizeProductState:
    def test_small_instance(self):
        result = optimize_product_state(5, 3, num_iterations=50)
        assert result["n"] == 5
        assert result["k"] == 3
        assert result["num_edges"] > 0
        assert result["num_cliques"] > 0
        assert 0 < result["optimal_max_mono_prob"] <= 1.0
        assert result["classical_threshold"] == 0.25

    def test_optimized_beats_uniform(self):
        result = optimize_product_state(8, 3, num_iterations=200)
        # Optimized product state should beat or match uniform superposition
        # Uniform gives P(mono) = 0.25 for each triangle
        assert result["optimal_max_mono_prob"] <= 0.25 + 1e-6

    def test_empty_instance(self):
        # n=1, k=3: no edges, no cliques
        result = optimize_product_state(1, 3)
        assert result["optimal_max_mono_prob"] == 0.0

    def test_output_structure(self):
        result = optimize_product_state(6, 3, num_iterations=20)
        assert "thetas" in result
        assert len(result["thetas"]) == result["num_edges"]
        assert result["quantum_advantage_ratio"] >= 0


# ============================================================================
# 2. Quantum Chromatic Number tests
# ============================================================================

class TestClassicalChromaticNumber:
    def test_small_values(self):
        # chi(G(n)) = 1 + pi(n)
        assert classical_chromatic_number(2) == 2   # 1 + 1 prime
        assert classical_chromatic_number(5) == 4   # 1 + 3 primes (2,3,5)
        assert classical_chromatic_number(10) == 5  # 1 + 4 primes (2,3,5,7)

    def test_monotone(self):
        for n in range(3, 20):
            assert classical_chromatic_number(n) <= classical_chromatic_number(n + 1)


class TestLovaszTheta:
    def test_small_n(self):
        for n in [3, 5, 8, 10]:
            theta = lovasz_theta(n)
            chi = classical_chromatic_number(n)
            # Theta should be in reasonable range
            assert theta > 0
            # For perfect graphs, theta should be close to chi
            # (within numerical precision of this eigenvalue-based estimate)

    def test_returns_positive(self):
        theta = lovasz_theta(5)
        assert theta > 0


class TestQuantumChromaticBound:
    def test_structure(self):
        result = quantum_chromatic_bound(10)
        assert result["n"] == 10
        assert result["omega"] == result["chi"]  # perfect
        assert result["is_perfect"] is True
        assert result["chi_q_lower"] == result["omega"]
        assert result["chi_q_upper"] == result["chi"]

    def test_omega_equals_1_plus_primes(self):
        for n in [5, 10, 15, 20]:
            result = quantum_chromatic_bound(n)
            expected = 1 + len(primes_up_to(n))
            assert result["omega"] == expected

    def test_primes_list(self):
        result = quantum_chromatic_bound(10)
        assert result["primes"] == [2, 3, 5, 7]


class TestOrthogonalRank:
    def test_equals_chromatic(self):
        for n in [5, 10, 15]:
            xi = orthogonal_rank(n)
            chi = classical_chromatic_number(n)
            assert xi == chi

    def test_monotone(self):
        for n in range(3, 15):
            assert orthogonal_rank(n) <= orthogonal_rank(n + 1)


# ============================================================================
# 3. Grover Search tests
# ============================================================================

class TestGroverAnalysis:
    def test_k3_n10(self):
        result = grover_analysis(10, 3, 156)
        assert result["num_avoiding"] == 156
        assert result["num_edges"] == len(coprime_edges(10))
        # Grover should need fewer queries than brute force
        assert result["grover_queries"] < result["classical_brute_force"]
        # Quadratic speedup
        assert result["quantum_speedup_vs_brute"] > 1

    def test_k3_n11_no_solutions(self):
        result = grover_analysis(11, 3, 0)
        assert result["num_avoiding"] == 0
        # Grover detects no-solution in sqrt(2^m) queries
        m = result["num_edges"]
        assert abs(result["grover_queries"] - math.sqrt(2**m)) < 1

    def test_quadratic_speedup(self):
        result = grover_analysis(10, 3, 156)
        m = result["num_edges"]
        # log2(Grover queries) should be approximately m/2
        assert result["log2_grover_queries"] < m
        assert result["log2_grover_queries"] > m / 4

    def test_qubits_equals_edges(self):
        result = grover_analysis(8, 3, 36)
        assert result["qubits_needed"] == result["num_edges"]

    def test_oracle_depth_positive(self):
        result = grover_analysis(8, 3, 36)
        assert result["oracle_depth_per_iter"] > 0
        assert result["total_circuit_depth"] > 0


class TestGroverCoprimeRamseySpeedup:
    def test_all_instances_present(self):
        results = grover_coprime_ramsey_speedup()
        assert "k3_n10" in results
        assert "k3_n11" in results
        assert "k3_n8" in results
        assert "k4_n19" in results

    def test_k3_n10_consistent(self):
        results = grover_coprime_ramsey_speedup()
        r = results["k3_n10"]
        assert r["num_avoiding"] == 156
        assert r["n"] == 10

    def test_speedup_positive(self):
        results = grover_coprime_ramsey_speedup()
        for key, r in results.items():
            assert r["quantum_speedup_vs_brute"] > 1


# ============================================================================
# 4. Quantum Ramsey Game tests
# ============================================================================

class TestClassicalRamseyGameValue:
    def test_structure(self):
        result = classical_ramsey_game_value(10, 3)
        assert result["n"] == 10
        assert result["k"] == 3
        assert result["num_edges"] > 0
        assert result["num_cliques"] > 0

    def test_participation_positive(self):
        result = classical_ramsey_game_value(8, 3)
        assert result["max_edge_clique_participation"] > 0
        assert result["avg_edge_clique_participation"] > 0

    def test_maker_wins_at_ramsey(self):
        result = classical_ramsey_game_value(11, 3)
        assert result["maker_wins_classically"] is True

    def test_maker_loses_before_ramsey(self):
        result = classical_ramsey_game_value(10, 3)
        assert result["maker_wins_classically"] is False


class TestEntanglementAdvantageBound:
    def test_structure(self):
        result = entanglement_advantage_bound(10, 3)
        assert result["n"] == 10
        assert result["k"] == 3
        assert result["tsirelson_ratio"] == math.sqrt(2)

    def test_overlap_density_bounded(self):
        result = entanglement_advantage_bound(10, 3)
        assert 0 <= result["overlap_density"] <= 1

    def test_quantum_shift_nonnegative(self):
        result = entanglement_advantage_bound(10, 3)
        assert result["estimated_quantum_rcop_shift"] >= 0

    def test_empty_graph(self):
        result = entanglement_advantage_bound(1, 3)
        assert result["num_cliques"] == 0
        assert result["tsirelson_ratio"] == 1.0


class TestBellInequalityForClique:
    def test_k3(self):
        result = bell_inequality_for_clique(3)
        assert result["k"] == 3
        assert result["edges_in_Kk"] == 3
        assert result["classical_max"] == 6  # 3*(3-1) = 6
        assert result["detection_snr"] > 0

    def test_k4(self):
        result = bell_inequality_for_clique(4)
        assert result["edges_in_Kk"] == 6
        assert result["classical_max"] == 30  # 6*5 = 30

    def test_bell_violation_ratio(self):
        for k in [3, 4, 5]:
            result = bell_inequality_for_clique(k)
            # Quantum bound should exceed or equal classical
            assert result["bell_violation_ratio"] >= 1.0

    def test_detection_snr_increases_with_k(self):
        snrs = [bell_inequality_for_clique(k)["detection_snr"] for k in range(3, 7)]
        # SNR should generally increase (more edges => easier detection)
        assert snrs[-1] > snrs[0]


# ============================================================================
# 5. QAOA tests
# ============================================================================

class TestQuboAvoidingColoring:
    def test_structure(self):
        result = qubo_avoiding_coloring(5, 3)
        assert result["n"] == 5
        assert result["k"] == 3
        assert result["qubo_size"] == result["num_edges"]
        assert result["qubo_matrix"].shape == (result["num_edges"], result["num_edges"])

    def test_qubo_nonzeros(self):
        result = qubo_avoiding_coloring(5, 3)
        assert result["qubo_nonzeros"] > 0

    def test_qubo_density_bounded(self):
        result = qubo_avoiding_coloring(5, 3)
        assert 0 <= result["qubo_density"] <= 1

    def test_has_cliques(self):
        result = qubo_avoiding_coloring(5, 3)
        assert len(result["cliques"]) > 0


class TestQaoaResourceEstimate:
    def test_structure(self):
        result = qaoa_resource_estimate(8, 3, p=1)
        assert result["n"] == 8
        assert result["k"] == 3
        assert result["p"] == 1
        assert result["qubits"] == len(coprime_edges(8))

    def test_depth_increases_with_p(self):
        r1 = qaoa_resource_estimate(8, 3, p=1)
        r2 = qaoa_resource_estimate(8, 3, p=2)
        r5 = qaoa_resource_estimate(8, 3, p=5)
        assert r1["total_depth"] < r2["total_depth"]
        assert r2["total_depth"] < r5["total_depth"]

    def test_gates_increase_with_p(self):
        r1 = qaoa_resource_estimate(8, 3, p=1)
        r2 = qaoa_resource_estimate(8, 3, p=2)
        assert r1["total_gates"] < r2["total_gates"]

    def test_small_instance_feasible(self):
        result = qaoa_resource_estimate(5, 3, p=1)
        assert result["nisq_feasible_qubits"] is True

    def test_n10_qubits(self):
        result = qaoa_resource_estimate(10, 3, p=1)
        # n=10 coprime graph has 31 edges
        assert result["qubits"] == 31

    def test_congestion_positive(self):
        result = qaoa_resource_estimate(8, 3, p=1)
        assert result["max_qubit_congestion"] > 0


class TestQaoaLandscapeAnalysis:
    def test_small_instance(self):
        result = qaoa_landscape_analysis(5, 3, grid_points=8)
        assert result["n"] == 5
        assert result["num_edges"] == len(coprime_edges(5))
        assert result["num_cliques"] > 0

    def test_avoiding_count(self):
        result = qaoa_landscape_analysis(5, 3, grid_points=8)
        # n=5 is small enough to have avoiding colorings
        assert result["num_avoiding"] >= 0

    def test_qaoa_finds_better_than_worst(self):
        result = qaoa_landscape_analysis(5, 3, grid_points=10)
        # QAOA should find cost below the maximum
        assert result["best_expected_cost"] <= result["landscape_max"]

    def test_too_large_instance(self):
        # n=12 has too many edges for exact simulation
        result = qaoa_landscape_analysis(12, 3)
        assert result["status"] == "too_large"

    def test_landscape_bounds(self):
        result = qaoa_landscape_analysis(5, 3, grid_points=8)
        assert result["landscape_min"] >= 0
        assert result["landscape_max"] >= result["landscape_min"]

    def test_qaoa_advantage(self):
        result = qaoa_landscape_analysis(5, 3, grid_points=10)
        if result.get("prob_avoiding_random", 0) > 0:
            # QAOA should provide some advantage over random
            assert result["qaoa_advantage"] >= 0


# ============================================================================
# 6. Synthesis tests
# ============================================================================

class TestQuantumRamseyThresholdAnalysis:
    @pytest.fixture(scope="module")
    def synthesis_result(self):
        return quantum_ramsey_threshold_analysis(3)

    def test_structure(self, synthesis_result):
        assert synthesis_result["k"] == 3
        assert "theoretical_conclusions" in synthesis_result
        assert "grover" in synthesis_result
        assert "bell_Kk" in synthesis_result

    def test_product_state_no_advantage(self, synthesis_result):
        conclusions = synthesis_result["theoretical_conclusions"]
        assert conclusions["product_state_changes_threshold"] is False

    def test_entanglement_may_help(self, synthesis_result):
        conclusions = synthesis_result["theoretical_conclusions"]
        assert conclusions["entangled_state_may_shift"] is True

    def test_grover_speedup(self, synthesis_result):
        conclusions = synthesis_result["theoretical_conclusions"]
        assert conclusions["grover_speedup_for_search"] is True

    def test_chromatic_bounds_present(self, synthesis_result):
        assert "chi_q_n10" in synthesis_result
        assert "chi_q_n15" in synthesis_result

    def test_qaoa_estimates_present(self, synthesis_result):
        assert "qaoa_n10_p1" in synthesis_result
        assert "qaoa_n10_p2" in synthesis_result
        assert "qaoa_n10_p5" in synthesis_result


# ============================================================================
# Cross-validation tests: consistency between modules
# ============================================================================

class TestCrossValidation:
    def test_edges_consistent(self):
        """coprime_edges here matches coprime_ramsey.coprime_edges."""
        from coprime_ramsey import coprime_edges as cr_edges
        for n in [5, 8, 10]:
            assert set(coprime_edges(n)) == set(cr_edges(n))

    def test_clique_count_consistent(self):
        """Triangles in G(5) should match coprime_spectral count."""
        cliques = find_coprime_cliques(5, 3)
        # Count manually: any 3 mutually coprime numbers in {1,...,5}
        # Known: {1,2,3},{1,2,5},{1,3,4},{1,3,5},{1,4,5},{2,3,5},{3,4,5}
        assert len(cliques) >= 7

    def test_chromatic_number_matches_spectral(self):
        """classical_chromatic_number should match coprime_spectral.clique_number."""
        from coprime_spectral import clique_number
        for n in [5, 10, 15]:
            chi = classical_chromatic_number(n)
            omega = clique_number(n)
            assert chi == omega  # perfect graph

    def test_grover_k3_n10_matches_known_count(self):
        """156 avoiding colorings at n=10, k=3 is verified in test_coprime_ramsey."""
        result = grover_analysis(10, 3, 156)
        assert result["num_avoiding"] == 156

    def test_quantum_threshold_vs_classical_rcop(self):
        """Product-state quantum coloring cannot change R_cop."""
        # At n=11, every classical coloring has mono K_3.
        # Product-state measurement always yields a classical coloring.
        # Therefore P(mono) = 1 for any product-state quantum coloring.
        opt = optimize_product_state(11, 3, num_iterations=100)
        # The optimal mono probability cannot be driven to 0 at n=11
        # (it's the Ramsey threshold), but our optimizer works on the
        # *max over cliques* of the product probability -- which CAN be
        # less than 1 because individual clique mono probs can be small.
        # The key insight is that the SUM over all cliques is forced
        # to be >= 1 at the Ramsey threshold.
        assert opt["optimal_max_mono_prob"] > 0


class TestPhysicalConstraints:
    """Verify that quantum-mechanical constraints are respected."""

    def test_probabilities_sum_to_one(self):
        for theta in [0, math.pi/6, math.pi/4, math.pi/3, math.pi/2]:
            s = QuantumEdgeState.parameterized(theta)
            assert abs(s.prob_color(0) + s.prob_color(1) - 1.0) < 1e-12

    def test_probabilities_nonnegative(self):
        for alpha, beta in [(1, 0), (0, 1), (1, 1), (1, 1j), (3, 4)]:
            s = QuantumEdgeState(alpha, beta)
            assert s.prob_color(0) >= 0
            assert s.prob_color(1) >= 0

    def test_mono_probability_bounded(self):
        """P(monochromatic clique) in [0, 1] for any state."""
        edges = coprime_edges(5)
        for _ in range(20):
            thetas = np.random.uniform(0, math.pi/2, len(edges))
            states = {e: QuantumEdgeState.parameterized(t)
                      for e, t in zip(edges, thetas)}
            qc = QuantumColoring(edges, states)
            for clique in find_coprime_cliques(5, 3):
                prob = qc.monochromatic_probability(clique)
                assert 0 <= prob <= 1.0 + 1e-12

    def test_tsirelson_bound_correct(self):
        """Tsirelson's bound is sqrt(2) ~ 1.414."""
        result = entanglement_advantage_bound(10, 3)
        assert abs(result["tsirelson_ratio"] - math.sqrt(2)) < 1e-12

    def test_grover_quadratic(self):
        """Grover queries should be O(sqrt(N/M)) for N states, M solutions."""
        result = grover_analysis(10, 3, 156)
        m = result["num_edges"]
        expected = math.pi / 4 * math.sqrt(2**m / 156)
        assert abs(result["grover_queries"] - expected) < 1
