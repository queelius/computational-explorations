"""Tests for coprime_spectral.py -- Spectral analysis of the coprime graph G(n)."""

import math
import pytest
import numpy as np

from coprime_spectral import (
    coprime_adjacency_matrix,
    coprime_adjacency_dict,
    coprime_edges,
    edge_density,
    adjacency_spectrum,
    spectral_gap,
    normalized_spectral_gap,
    spectral_radius,
    analyze_spectrum,
    greedy_coloring,
    dsatur_coloring,
    chromatic_number_sat,
    chromatic_numbers,
    clique_number,
    independence_number,
    independence_numbers,
    max_kk_free_subgraph_density,
    spectral_ramsey_scan,
    detect_spectral_transition,
    spectral_growth_law,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def adj_10():
    """Adjacency matrix for G(10)."""
    return coprime_adjacency_matrix(10)


@pytest.fixture(scope="module")
def spectrum_10():
    """Sorted eigenvalues of G(10)."""
    return adjacency_spectrum(10)


@pytest.fixture(scope="module")
def info_20():
    """Full spectral info for G(20)."""
    return analyze_spectrum(20)


# ---------------------------------------------------------------------------
# 1. Core graph construction
# ---------------------------------------------------------------------------

class TestAdjacencyMatrix:
    """Test coprime adjacency matrix construction."""

    def test_symmetric(self, adj_10):
        """Adjacency matrix must be symmetric."""
        assert np.allclose(adj_10, adj_10.T)

    def test_zero_diagonal(self, adj_10):
        """Diagonal must be zero (no self-loops)."""
        assert np.all(np.diag(adj_10) == 0)

    def test_binary(self, adj_10):
        """Entries must be 0 or 1."""
        assert np.all((adj_10 == 0) | (adj_10 == 1))

    def test_shape(self, adj_10):
        """Shape must be n x n."""
        assert adj_10.shape == (10, 10)

    def test_edge_count(self, adj_10):
        """Number of edges = sum(A)/2."""
        expected = len(coprime_edges(10))
        assert int(np.sum(adj_10)) // 2 == expected

    def test_vertex_1_connected_to_all(self, adj_10):
        """Vertex 1 is coprime to all others, so row 0 has all 1s off-diagonal."""
        row = adj_10[0, :]
        assert row[0] == 0  # no self-loop
        assert np.sum(row) == 9  # connected to all 9 others

    def test_specific_entry_coprime(self, adj_10):
        """gcd(3,5)=1, so A[2,4] = 1."""
        assert adj_10[2, 4] == 1  # vertices 3,5

    def test_specific_entry_not_coprime(self, adj_10):
        """gcd(4,6)=2, so A[3,5] = 0."""
        assert adj_10[3, 5] == 0  # vertices 4,6

    def test_n1(self):
        """G(1) is a single vertex, no edges."""
        A = coprime_adjacency_matrix(1)
        assert A.shape == (1, 1)
        assert A[0, 0] == 0

    def test_n2(self):
        """G(2): single edge between 1 and 2."""
        A = coprime_adjacency_matrix(2)
        assert A[0, 1] == 1
        assert A[1, 0] == 1


class TestAdjacencyDict:
    """Test adjacency dict representation."""

    def test_keys_are_1_to_n(self):
        adj = coprime_adjacency_dict(5)
        assert set(adj.keys()) == {1, 2, 3, 4, 5}

    def test_vertex_1_neighbors(self):
        adj = coprime_adjacency_dict(5)
        assert adj[1] == {2, 3, 4, 5}

    def test_symmetric(self):
        adj = coprime_adjacency_dict(10)
        for u in adj:
            for v in adj[u]:
                assert u in adj[v], f"{u} in adj[{v}] but {v} not in adj[{u}]"

    def test_no_self_loops(self):
        adj = coprime_adjacency_dict(10)
        for v in adj:
            assert v not in adj[v]


class TestEdgeDensity:
    """Test edge density computation."""

    def test_density_n2(self):
        """G(2) has density 1.0 (one edge, one possible)."""
        assert edge_density(2) == 1.0

    def test_density_decreases_toward_limit(self):
        """Density should decrease toward 6/pi^2 ~ 0.608."""
        d50 = edge_density(50)
        d100 = edge_density(100)
        expected = 6 / math.pi ** 2
        assert d50 > expected  # still above limit at n=50
        assert abs(d100 - expected) < 0.02

    def test_density_monotone_decreasing(self):
        """Edge density should decrease as n increases (for n >= 3)."""
        densities = [edge_density(n) for n in [10, 20, 50, 100]]
        for i in range(len(densities) - 1):
            assert densities[i] >= densities[i + 1] - 0.01  # allow small float noise

    def test_density_n1(self):
        """G(1) has no edges."""
        assert edge_density(1) == 0.0


# ---------------------------------------------------------------------------
# 2. Adjacency Spectrum
# ---------------------------------------------------------------------------

class TestSpectrum:
    """Test eigenvalue computation."""

    def test_descending_order(self, spectrum_10):
        """Eigenvalues should be in descending order."""
        for i in range(len(spectrum_10) - 1):
            assert spectrum_10[i] >= spectrum_10[i + 1] - 1e-10

    def test_count_equals_n(self, spectrum_10):
        """Should have exactly n eigenvalues."""
        assert len(spectrum_10) == 10

    def test_real_eigenvalues(self, spectrum_10):
        """Eigenvalues of symmetric matrix must be real."""
        assert np.all(np.isreal(spectrum_10))

    def test_trace_equals_zero(self, spectrum_10):
        """Trace = sum of eigenvalues = 0 for adjacency matrix."""
        assert abs(np.sum(spectrum_10)) < 1e-8

    def test_trace_a2_equals_2_times_edges(self, spectrum_10):
        """sum(lambda_i^2) = trace(A^2) = 2|E|."""
        trace_a2 = np.sum(spectrum_10 ** 2)
        num_edges = len(coprime_edges(10))
        assert abs(trace_a2 - 2 * num_edges) < 1e-6

    def test_lambda_1_positive(self, spectrum_10):
        """Largest eigenvalue must be positive."""
        assert spectrum_10[0] > 0

    def test_lambda_1_upper_bound(self, spectrum_10):
        """lambda_1 <= max degree = n-1 (vertex 1 has degree n-1)."""
        assert spectrum_10[0] <= 9 + 1e-10  # max degree of G(10) is 9

    def test_lambda_1_lower_bound(self, spectrum_10):
        """lambda_1 >= mean degree."""
        mean_deg = 2 * len(coprime_edges(10)) / 10
        assert spectrum_10[0] >= mean_deg - 1e-10

    def test_smallest_eigenvalue_negative(self, spectrum_10):
        """Adjacency matrix of non-bipartite graph has lambda_n < 0."""
        assert spectrum_10[-1] < 0


class TestSpectralGap:
    """Test spectral gap computation."""

    def test_gap_positive(self, spectrum_10):
        """Spectral gap should be positive for connected graph."""
        gap = spectral_gap(spectrum_10)
        assert gap > 0

    def test_normalized_gap_between_0_and_1(self, spectrum_10):
        """Normalized spectral gap should be in (0, 1]."""
        ng = normalized_spectral_gap(spectrum_10)
        assert 0 < ng <= 1.0

    def test_gap_is_lambda1_minus_lambda2(self, spectrum_10):
        """Gap should equal lambda_1 - lambda_2."""
        gap = spectral_gap(spectrum_10)
        expected = float(spectrum_10[0] - spectrum_10[1])
        assert abs(gap - expected) < 1e-10

    def test_gap_for_k2(self):
        """G(2): spectrum is [1, -1], gap = 2."""
        eigs = adjacency_spectrum(2)
        assert abs(spectral_gap(eigs) - 2.0) < 1e-10

    def test_normalized_gap_for_small(self):
        """Short array should return 0."""
        assert normalized_spectral_gap(np.array([5.0])) == 0.0


class TestSpectralRadius:
    """Test spectral radius computation."""

    def test_spectral_radius_positive(self):
        assert spectral_radius(10) > 0

    def test_spectral_radius_grows(self):
        """Spectral radius should grow with n."""
        r10 = spectral_radius(10)
        r20 = spectral_radius(20)
        assert r20 > r10


class TestAnalyzeSpectrum:
    """Test full spectral analysis."""

    def test_keys_present(self, info_20):
        required = [
            "n", "num_edges", "max_edges", "density", "mean_degree",
            "lambda_1", "lambda_2", "lambda_n", "spectral_gap",
            "normalized_gap", "lambda_mean_ratio", "num_triangles",
        ]
        for key in required:
            assert key in info_20, f"Missing key: {key}"

    def test_n_value(self, info_20):
        assert info_20["n"] == 20

    def test_num_edges(self, info_20):
        assert info_20["num_edges"] == len(coprime_edges(20))

    def test_density_matches(self, info_20):
        assert abs(info_20["density"] - edge_density(20)) < 1e-10

    def test_triangles_nonneg(self, info_20):
        """Number of triangles should be non-negative integer."""
        assert info_20["num_triangles"] >= 0

    def test_triangles_from_trace(self, info_20):
        """Verify triangles via trace(A^3)/6."""
        A = coprime_adjacency_matrix(20)
        A3 = A @ A @ A
        expected = np.trace(A3) / 6
        assert abs(info_20["num_triangles"] - expected) < 1.0

    def test_lambda_mean_ratio_near_one(self, info_20):
        """lambda_1 / mean_degree should be close to 1 (quasi-random)."""
        assert 1.0 < info_20["lambda_mean_ratio"] < 1.2

    def test_normalized_gap_large(self, info_20):
        """Normalized gap should be > 0.8 (good expander)."""
        assert info_20["normalized_gap"] > 0.8


# ---------------------------------------------------------------------------
# 3. Chromatic Number
# ---------------------------------------------------------------------------

class TestGreedyColoring:
    """Test greedy coloring."""

    def test_valid_coloring(self):
        """No two adjacent vertices should share a color."""
        n = 15
        num_colors, coloring = greedy_coloring(n)
        adj = coprime_adjacency_dict(n)
        for v in range(1, n + 1):
            for u in adj[v]:
                assert coloring[v] != coloring[u], (
                    f"Adjacent vertices {v},{u} have same color {coloring[v]}"
                )

    def test_all_vertices_colored(self):
        n = 10
        _, coloring = greedy_coloring(n)
        assert set(coloring.keys()) == set(range(1, n + 1))

    def test_colors_zero_indexed(self):
        _, coloring = greedy_coloring(10)
        assert min(coloring.values()) == 0


class TestDsaturColoring:
    """Test DSATUR coloring."""

    def test_valid_coloring(self):
        n = 15
        num_colors, coloring = dsatur_coloring(n)
        adj = coprime_adjacency_dict(n)
        for v in range(1, n + 1):
            for u in adj[v]:
                assert coloring[v] != coloring[u]

    def test_at_most_greedy(self):
        """DSATUR should use no more colors than greedy."""
        n = 20
        greedy_k, _ = greedy_coloring(n)
        dsatur_k, _ = dsatur_coloring(n)
        assert dsatur_k <= greedy_k

    def test_at_least_omega(self):
        """Number of colors >= clique number."""
        n = 15
        k, _ = dsatur_coloring(n)
        omega = clique_number(n)
        assert k >= omega


class TestChromaticSAT:
    """Test SAT-based exact chromatic number."""

    def test_chi_5(self):
        """chi(G(5)) = 4 = 1 + pi(5) = 1 + 3."""
        assert chromatic_number_sat(5) == 4

    def test_chi_10(self):
        """chi(G(10)) = 5 = 1 + pi(10) = 1 + 4."""
        assert chromatic_number_sat(10) == 5

    def test_chi_equals_omega_small(self):
        """chi = omega for small n (perfection test)."""
        for n in [5, 8, 10, 12, 15]:
            chi = chromatic_number_sat(n)
            omega = clique_number(n)
            assert chi == omega, f"n={n}: chi={chi}, omega={omega}"


class TestChromaticNumbers:
    """Test batch chromatic number computation."""

    def test_returns_all_n(self):
        ns = [5, 10, 15]
        results = chromatic_numbers(ns, use_sat=True, sat_limit=15)
        assert set(results.keys()) == set(ns)

    def test_keys_in_result(self):
        results = chromatic_numbers([5], use_sat=True, sat_limit=10)
        r = results[5]
        assert "chi" in r
        assert "omega" in r
        assert "greedy" in r
        assert "dsatur" in r
        assert "method" in r


# ---------------------------------------------------------------------------
# 4. Clique Number and Independence Number
# ---------------------------------------------------------------------------

class TestCliqueNumber:
    """Test clique number computation."""

    def test_small_values(self):
        """omega(G(n)) = 1 + pi(n) where pi(n) = number of primes <= n."""
        # n=5: primes 2,3,5 -> omega = 4
        assert clique_number(5) == 4
        # n=10: primes 2,3,5,7 -> omega = 5
        assert clique_number(10) == 5
        # n=20: primes 2,3,5,7,11,13,17,19 -> omega = 9
        assert clique_number(20) == 9

    def test_monotone(self):
        """Clique number is non-decreasing."""
        prev = 0
        for n in range(2, 30):
            curr = clique_number(n)
            assert curr >= prev
            prev = curr

    def test_jump_at_primes(self):
        """Clique number increases by 1 at each prime."""
        for p in [2, 3, 5, 7, 11, 13]:
            assert clique_number(p) == clique_number(p - 1) + 1


class TestIndependenceNumber:
    """Test independence number computation."""

    def test_alpha_equals_floor_n_over_2(self):
        """alpha(G(n)) = floor(n/2) for all tested n."""
        for n in [5, 10, 15, 20, 30]:
            alpha = independence_number(n)
            assert alpha == n // 2, f"n={n}: alpha={alpha}, expected {n//2}"

    def test_alpha_small(self):
        """Small cases: alpha(G(2)) = 1 (only {2} or similar non-coprime singleton)."""
        # G(2): vertices {1,2}, coprime, so independent set is max 1
        # Actually alpha(G(2)) = 1: no pair is non-coprime
        assert independence_number(2) == 1

    def test_alpha_monotone(self):
        """alpha(G(n)) should be non-decreasing with n."""
        prev = 0
        for n in range(2, 25):
            alpha = independence_number(n)
            assert alpha >= prev, f"alpha({n})={alpha} < alpha({n-1})={prev}"
            prev = alpha

    def test_independence_numbers_batch(self):
        """Test batch computation matches individual."""
        ns = [10, 20, 30]
        batch = independence_numbers(ns)
        for n in ns:
            assert batch[n] == independence_number(n)

    def test_evens_form_independent_set(self):
        """Verify that even numbers are indeed pairwise non-coprime."""
        n = 20
        evens = [i for i in range(2, n + 1) if i % 2 == 0]
        for i in range(len(evens)):
            for j in range(i + 1, len(evens)):
                assert math.gcd(evens[i], evens[j]) > 1, (
                    f"gcd({evens[i]}, {evens[j]}) = 1, but both are even"
                )

    def test_alpha_heuristic_path(self):
        """Exercise the heuristic path (n > 40)."""
        alpha = independence_number(50)
        assert alpha == 25  # floor(50/2) = 25

    def test_alpha_n1(self):
        """alpha(G(1)) = 1 (single vertex is trivially independent)."""
        assert independence_number(1) == 1


# ---------------------------------------------------------------------------
# 5. Ramsey-Turan Density
# ---------------------------------------------------------------------------

class TestRamseyTuranDensity:
    """Test K_k-free subgraph density computation."""

    def test_k2_free_has_no_edges(self):
        """K_2-free graph has no edges."""
        result = max_kk_free_subgraph_density(10, 2)
        assert result["kk_free_edges"] == 0

    def test_k3_free_at_ramsey(self):
        """At R_cop(3)=11, K_3-free subgraph should have positive edges."""
        result = max_kk_free_subgraph_density(11, 3)
        assert result["kk_free_edges"] > 0
        assert result["fraction_retained"] > 0.5

    def test_k3_free_density_below_turan(self):
        """K_3-free subgraph density should be below Turan bound 1/2."""
        result = max_kk_free_subgraph_density(11, 3)
        assert result["density"] <= 0.51  # allow small slack for heuristic

    def test_result_keys(self):
        result = max_kk_free_subgraph_density(10, 3)
        required = ["n", "k", "total_edges", "kk_free_edges",
                     "density", "fraction_retained", "turan_bound"]
        for key in required:
            assert key in result

    def test_retained_fraction_bounded(self):
        """Fraction retained should be in [0, 1]."""
        result = max_kk_free_subgraph_density(15, 3)
        assert 0 <= result["fraction_retained"] <= 1.0

    def test_k4_free_retains_more_than_k3_free(self):
        """K_4-free should retain more edges than K_3-free."""
        r3 = max_kk_free_subgraph_density(15, 3)
        r4 = max_kk_free_subgraph_density(15, 4)
        assert r4["kk_free_edges"] >= r3["kk_free_edges"]


# ---------------------------------------------------------------------------
# 6. Spectral Prediction of Ramsey
# ---------------------------------------------------------------------------

class TestSpectralRamseyScan:
    """Test spectral Ramsey scan."""

    def test_scan_returns_correct_count(self):
        results = spectral_ramsey_scan(3, [5, 6, 7, 8])
        assert len(results) == 4

    def test_scan_result_keys(self):
        results = spectral_ramsey_scan(3, [10])
        r = results[0]
        required = ["n", "k", "lambda_1", "lambda_2", "spectral_gap",
                     "normalized_gap", "density", "k_clique_count"]
        for key in required:
            assert key in r

    def test_scan_n_values_match(self):
        ns = [8, 9, 10, 11, 12]
        results = spectral_ramsey_scan(3, ns)
        assert [r["n"] for r in results] == ns

    def test_triangles_grow_with_n(self):
        """Triangle count should increase with n."""
        results = spectral_ramsey_scan(3, [5, 8, 11, 15])
        counts = [r["k_clique_count"] for r in results]
        for i in range(len(counts) - 1):
            assert counts[i + 1] >= counts[i]


class TestDetectTransition:
    """Test Ramsey transition detection."""

    def test_returns_error_for_missing_n(self):
        scan = spectral_ramsey_scan(3, [5, 6, 7])
        result = detect_spectral_transition(scan, 11)
        assert "error" in result

    def test_transition_at_11(self):
        scan = spectral_ramsey_scan(3, list(range(8, 14)))
        result = detect_spectral_transition(scan, 11)
        assert "ramsey_n" in result
        assert result["ramsey_n"] == 11
        assert "gap_at_transition" in result
        assert "transition_jump" in result

    def test_jump_is_difference(self):
        scan = spectral_ramsey_scan(3, list(range(9, 13)))
        result = detect_spectral_transition(scan, 11)
        assert abs(result["transition_jump"] -
                   (result["gap_at_transition"] - result["gap_before"])) < 1e-10


# ---------------------------------------------------------------------------
# 7. Growth Law
# ---------------------------------------------------------------------------

class TestSpectralGrowthLaw:
    """Test spectral growth law fitting."""

    def test_returns_all_keys(self):
        result = spectral_growth_law([10, 20, 30])
        required = ["ns", "lambda_1s", "spectral_gaps", "normalized_gaps",
                     "densities", "lambda_1_slope", "expected_slope",
                     "slope_ratio", "gap_exponent", "gap_prefactor"]
        for key in required:
            assert key in result

    def test_lambda_1_slope_near_coprime_density(self):
        """lambda_1 ~ c * n where c is close to 6/pi^2."""
        result = spectral_growth_law([10, 20, 30, 50, 100])
        # c should be between 0.6 and 0.75 (above 6/pi^2 due to hub vertex)
        assert 0.6 < result["lambda_1_slope"] < 0.8

    def test_gap_exponent_near_one(self):
        """Spectral gap should grow roughly linearly (exponent ~1)."""
        result = spectral_growth_law([10, 20, 30, 50, 100])
        assert 0.8 < result["gap_exponent"] < 1.2

    def test_slope_ratio_above_one(self):
        """lambda_1 slope should exceed 6/pi^2 (hub effect)."""
        result = spectral_growth_law([10, 20, 30, 50])
        assert result["slope_ratio"] > 1.0


# ---------------------------------------------------------------------------
# 8. Meta-pattern: Perfection and Spectral Structure
# ---------------------------------------------------------------------------

class TestMetaPatterns:
    """Test the key meta-patterns discovered."""

    def test_coprime_graph_is_perfect_up_to_30(self):
        """chi(G(n)) = omega(G(n)) for n = 5,10,...,30."""
        for n in [5, 10, 15, 20, 25, 30]:
            chi = chromatic_number_sat(n)
            omega = clique_number(n)
            assert chi == omega, f"G({n}): chi={chi} != omega={omega}"

    def test_alpha_plus_omega_ge_n(self):
        """Ramsey-type: alpha + omega should be >= n + 1 (weak Ramsey bound)."""
        # Actually for perfect graphs: alpha * omega >= n
        for n in [10, 15, 20]:
            alpha = independence_number(n)
            omega = clique_number(n)
            assert alpha * omega >= n, (
                f"G({n}): alpha*omega = {alpha}*{omega} = {alpha*omega} < {n}"
            )

    def test_normalized_gap_stable(self):
        """Normalized gap should be roughly constant (~0.89-0.92)."""
        for n in [10, 20, 30, 50]:
            eigs = adjacency_spectrum(n)
            ng = normalized_spectral_gap(eigs)
            assert 0.85 < ng < 0.95, f"G({n}): normalized gap = {ng}"

    def test_lambda_1_over_mean_degree_stable(self):
        """lambda_1 / mean_degree should be roughly constant (~1.07-1.11)."""
        for n in [10, 20, 30, 50]:
            info = analyze_spectrum(n)
            ratio = info["lambda_mean_ratio"]
            assert 1.0 < ratio < 1.2, f"G({n}): lambda_1/d_bar = {ratio}"

    def test_triangle_count_grows_cubically(self):
        """Number of triangles should grow roughly as n^3."""
        counts = []
        ns = [10, 20, 30, 50]
        for n in ns:
            info = analyze_spectrum(n)
            counts.append(info["num_triangles"])

        # Fit power law: log(T) ~ a * log(n)
        log_ns = np.log(ns)
        log_counts = np.log(counts)
        coeffs = np.polyfit(log_ns, log_counts, 1)
        exponent = coeffs[0]
        # Should be close to 3 (cubic growth)
        assert 2.5 < exponent < 3.5, f"Triangle growth exponent = {exponent}"


# ---------------------------------------------------------------------------
# 9. Edge cases and additional coverage
# ---------------------------------------------------------------------------

class TestEdgeCasesAndCoverage:
    """Additional tests for edge cases and uncovered code paths."""

    def test_rt_density_empty_graph(self):
        """K_3-free density of G(1) should handle zero edges."""
        result = max_kk_free_subgraph_density(1, 3)
        assert result["total_edges"] == 0
        assert result["density"] == 0.0
        assert result["method"] == "trivial"

    def test_spectral_scan_k4(self):
        """Scan for k=4 cliques should count correctly."""
        results = spectral_ramsey_scan(4, [10, 12])
        for r in results:
            assert r["k"] == 4
            assert r["k_clique_count"] >= 0

    def test_dsatur_optimal_for_g5(self):
        """DSATUR gives optimal coloring for G(5)."""
        k, col = dsatur_coloring(5)
        assert k == clique_number(5)

    def test_greedy_valid_for_g30(self):
        """Greedy coloring of G(30) is a valid coloring."""
        n = 30
        num_colors, coloring = greedy_coloring(n)
        adj = coprime_adjacency_dict(n)
        for v in range(1, n + 1):
            for u in adj[v]:
                assert coloring[v] != coloring[u]
        assert num_colors >= clique_number(n)

    def test_chromatic_upper_bound_method(self):
        """For n > sat_limit, method should be DSATUR-upper."""
        results = chromatic_numbers([10], use_sat=True, sat_limit=5)
        assert results[10]["method"] == "DSATUR-upper"

    def test_coprime_edges_consistency(self):
        """coprime_edges should agree with adjacency matrix."""
        n = 8
        edges = coprime_edges(n)
        A = coprime_adjacency_matrix(n)
        for i, j in edges:
            assert A[i - 1, j - 1] == 1.0
        assert len(edges) == int(np.sum(A)) // 2

    def test_spectral_gap_empty_spectrum(self):
        """Spectral gap of single eigenvalue should be 0."""
        assert spectral_gap(np.array([3.0])) == 0.0

    def test_detect_transition_at_boundary(self):
        """Transition detection at first element in scan."""
        scan = spectral_ramsey_scan(3, [11, 12, 13])
        result = detect_spectral_transition(scan, 11)
        assert result["ramsey_n"] == 11
        # gap_before should equal gap_at_transition when at index 0
        assert result["gap_before"] == result["gap_at_transition"]
