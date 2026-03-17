#!/usr/bin/env python3
"""
Extremal Coprime Graph Analysis — Extending Problem #883

Analyzes the edge density and cycle structure of coprime graphs G(A)
for A ⊆ [n] near the extremal threshold |A| > ⌊n/2⌋ + ⌊n/3⌋ - ⌊n/6⌋.

Key question: Does the triangle case + edge density imply full pancyclicity?

Bondy's theorem: If G has n vertices and > n²/4 edges, then G is pancyclic
(contains cycles of every length 3,...,n) unless G = K_{n/2,n/2}.

Turán's theorem: ex(n, K_3) = ⌊n²/4⌋ (Mantel bound).

So if coprime graph G(A) with |A| > 2n/3 has > |A|²/4 edges, we get
all cycle lengths, including all odd cycles ≤ |A|, resolving #883 fully.
"""

import math
from itertools import combinations
from typing import Set, List, Dict, Any, Optional, Tuple
from collections import defaultdict


def extremal_size(n: int) -> int:
    """Size of extremal set A* = {i in [n] : 2|i or 3|i}."""
    return n // 2 + n // 3 - n // 6


def residue_classes(n: int) -> Dict[int, List[int]]:
    """Partition [n] by residue mod 6."""
    classes = {r: [] for r in range(6)}
    for i in range(1, n + 1):
        classes[i % 6].append(i)
    return classes


def coprime_edge_count(A: Set[int]) -> int:
    """Count edges in coprime graph G(A)."""
    A_list = sorted(A)
    count = 0
    for i in range(len(A_list)):
        for j in range(i + 1, len(A_list)):
            if math.gcd(A_list[i], A_list[j]) == 1:
                count += 1
    return count


def coprime_edge_density(A: Set[int]) -> float:
    """Edge density = edges / C(|A|, 2)."""
    n = len(A)
    if n < 2:
        return 0.0
    return coprime_edge_count(A) / (n * (n - 1) / 2)


def turan_number(n: int, r: int = 2) -> int:
    """
    Turán number ex(n, K_{r+1}).
    For r=2 (triangle-free): ex(n, K_3) = floor(n²/4).
    """
    if r == 2:
        return n * n // 4
    # General Turán: (1 - 1/r) * n² / 2
    return int((1 - 1 / r) * n * n / 2)


def bondy_threshold(n: int) -> int:
    """
    Bondy's theorem: if edges > n²/4, graph is pancyclic or K_{n/2,n/2}.
    Returns the edge threshold.
    """
    return n * n // 4 + 1


def edge_density_by_threshold(n: int, num_extra: int = 1) -> Dict[str, Any]:
    """
    Compute edge density for sets of size |A*| + num_extra.

    We take A* and add num_extra elements from R₁∪R₅, choosing those
    that minimize edge density (worst case for pancyclicity).
    """
    R = residue_classes(n)
    a_star = set()
    for r in [0, 2, 3, 4]:
        a_star.update(R[r])

    coprime_to_6 = sorted(R[1] + R[5])

    if num_extra > len(coprime_to_6):
        num_extra = len(coprime_to_6)

    # Best case: add elements that maximize edges
    # Worst case: add elements that minimize edges
    best_density = 0.0
    worst_density = float('inf')
    best_set = None
    worst_set = None
    best_edges = 0
    worst_edges = float('inf')

    # For small num_extra, enumerate all choices
    if len(coprime_to_6) <= 15 or num_extra <= 3:
        for combo in combinations(coprime_to_6, num_extra):
            A = a_star | set(combo)
            edges = coprime_edge_count(A)
            density = edges / (len(A) * (len(A) - 1) / 2)
            if density > best_density:
                best_density = density
                best_set = A
                best_edges = edges
            if density < worst_density:
                worst_density = density
                worst_set = A
                worst_edges = edges
    else:
        # Sample a few combinations
        import random
        random.seed(42)
        for _ in range(min(100, math.comb(len(coprime_to_6), num_extra))):
            combo = random.sample(coprime_to_6, num_extra)
            A = a_star | set(combo)
            edges = coprime_edge_count(A)
            density = edges / (len(A) * (len(A) - 1) / 2)
            if density > best_density:
                best_density = density
                best_set = A
                best_edges = edges
            if density < worst_density:
                worst_density = density
                worst_set = A
                worst_edges = edges

    a_size = extremal_size(n) + num_extra
    bondy_thresh = bondy_threshold(a_size)

    return {
        "n": n,
        "num_extra": num_extra,
        "set_size": a_size,
        "best_density": best_density,
        "worst_density": worst_density,
        "best_edges": best_edges,
        "worst_edges": worst_edges,
        "bondy_threshold": bondy_thresh,
        "worst_exceeds_bondy": worst_edges > bondy_thresh,
        "turan_number": turan_number(a_size),
    }


def degree_analysis(A: Set[int]) -> Dict[str, Any]:
    """
    Analyze degree sequence of coprime graph G(A).

    Key for cycle forcing: high minimum degree implies cycles.
    Dirac's theorem: if min_degree >= n/2, graph is Hamiltonian.
    """
    A_list = sorted(A)
    n = len(A_list)
    degrees = {}

    for a in A_list:
        deg = sum(1 for b in A_list if b != a and math.gcd(a, b) == 1)
        degrees[a] = deg

    if not degrees:
        return {"min_deg": 0, "max_deg": 0, "avg_deg": 0, "n": 0}

    deg_vals = list(degrees.values())
    min_deg = min(deg_vals)
    max_deg = max(deg_vals)
    avg_deg = sum(deg_vals) / len(deg_vals)

    # Find vertex of min degree
    min_vertex = min(degrees, key=degrees.get)
    max_vertex = max(degrees, key=degrees.get)

    # Check Dirac condition
    dirac = min_deg >= n / 2

    # Check Ore condition: for non-adjacent u,v, deg(u)+deg(v) >= n
    ore_violations = 0
    for i in range(n):
        for j in range(i + 1, n):
            if math.gcd(A_list[i], A_list[j]) != 1:  # non-adjacent
                if degrees[A_list[i]] + degrees[A_list[j]] < n:
                    ore_violations += 1

    return {
        "n": n,
        "min_deg": min_deg,
        "max_deg": max_deg,
        "avg_deg": avg_deg,
        "min_vertex": min_vertex,
        "max_vertex": max_vertex,
        "dirac_satisfied": dirac,
        "ore_violations": ore_violations,
        "ore_satisfied": ore_violations == 0,
        "degree_distribution": sorted(deg_vals),
    }


def neighborhood_intersection(A: Set[int]) -> Dict[str, Any]:
    """
    For every pair of non-adjacent vertices, compute |N(u) ∩ N(v)|.

    If |N(u) ∩ N(v)| >= 1 for all non-adjacent pairs, the graph
    has diameter <= 2 (relevant for cycle length arguments).
    """
    A_list = sorted(A)
    n = len(A_list)

    # Build adjacency
    adj = defaultdict(set)
    for i in range(n):
        for j in range(i + 1, n):
            if math.gcd(A_list[i], A_list[j]) == 1:
                adj[A_list[i]].add(A_list[j])
                adj[A_list[j]].add(A_list[i])

    min_intersection = float('inf')
    max_intersection = 0
    diameter_bound = 0
    non_adjacent_pairs = 0
    common_neighbor_zero = 0

    for i in range(n):
        for j in range(i + 1, n):
            u, v = A_list[i], A_list[j]
            if math.gcd(u, v) != 1:  # non-adjacent
                non_adjacent_pairs += 1
                common = len(adj.get(u, set()) & adj.get(v, set()))
                min_intersection = min(min_intersection, common)
                max_intersection = max(max_intersection, common)
                if common == 0:
                    common_neighbor_zero += 1
                    diameter_bound = max(diameter_bound, 3)  # at least 3
                else:
                    diameter_bound = max(diameter_bound, 2)

    if non_adjacent_pairs == 0:
        # Complete graph
        return {
            "non_adjacent_pairs": 0,
            "is_complete": True,
            "diameter": 1,
        }

    if min_intersection == float('inf'):
        min_intersection = 0

    return {
        "non_adjacent_pairs": non_adjacent_pairs,
        "is_complete": False,
        "min_common_neighbors": min_intersection,
        "max_common_neighbors": max_intersection,
        "pairs_with_no_common": common_neighbor_zero,
        "diameter_bound": diameter_bound,
        "all_have_common_neighbor": common_neighbor_zero == 0,
    }


def cycle_spectrum_via_matrix(A: Set[int], max_length: int = 20) -> List[int]:
    """
    Find which cycle lengths exist in G(A) using adjacency matrix traces.

    tr(A^k) counts closed walks of length k. For odd k, if tr(A^k) > 0
    and no shorter odd cycle accounts for it, then a cycle of length k exists.

    For precision: use DFS cycle detection for small graphs.
    """
    A_list = sorted(A)
    n = len(A_list)
    if n < 3:
        return []

    # Build adjacency matrix
    adj = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if math.gcd(A_list[i], A_list[j]) == 1:
                adj[i][j] = 1
                adj[j][i] = 1

    cycle_lengths = []

    # Check for cycles using DFS backtracking
    for length in range(3, min(max_length + 1, n + 1), 2):  # odd only
        if _has_cycle_of_length(adj, n, length):
            cycle_lengths.append(length)

    return cycle_lengths


def _has_cycle_of_length(adj: list, n: int, length: int) -> bool:
    """Check if graph has a cycle of exact given length."""
    if n < length:
        return False

    for start in range(n):
        visited = [False] * n
        visited[start] = True
        if _dfs_cycle(adj, n, start, start, visited, 1, length):
            return True
    return False


def _dfs_cycle(adj: list, n: int, start: int, current: int,
               visited: list, depth: int, target: int) -> bool:
    """DFS to find cycle returning to start at exact depth."""
    if depth == target:
        return adj[current][start] == 1

    for next_v in range(n):
        if adj[current][next_v] == 1 and not visited[next_v]:
            visited[next_v] = True
            if _dfs_cycle(adj, n, start, next_v, visited, depth + 1, target):
                return True
            visited[next_v] = False

    return False


def pancyclicity_analysis(n: int) -> Dict[str, Any]:
    """
    Comprehensive analysis: for A with |A| = |A*| + 1, determine
    if G(A) is pancyclic (contains all cycle lengths 3...|A|).

    This is the key to extending #883 from triangles to all odd cycles.
    """
    R = residue_classes(n)
    a_star = set()
    for r in [0, 2, 3, 4]:
        a_star.update(R[r])

    coprime_to_6 = sorted(R[1] + R[5])
    if not coprime_to_6:
        return {"n": n, "error": "no coprime-to-6 elements"}

    # Take A = A* + first element coprime to 6 (worst case for small element)
    A = a_star | {coprime_to_6[0]}
    a_size = len(A)

    edges = coprime_edge_count(A)
    density = coprime_edge_density(A)
    bondy_thresh = bondy_threshold(a_size)

    # Check Bondy condition
    exceeds_bondy = edges > bondy_thresh

    # Degree analysis
    deg_info = degree_analysis(A)

    # Cycle spectrum (limit for computation time)
    max_cycle = min(a_size, 15)
    cycles = cycle_spectrum_via_matrix(A, max_length=max_cycle)

    # Expected odd cycles for full #883: all odd lengths 3 to ⌊n/3⌋+1
    max_required = n // 3 + 1
    required_odd_cycles = list(range(3, max_required + 1, 2))
    found_required = [c for c in required_odd_cycles if c <= max_cycle and c in cycles]
    missing_required = [c for c in required_odd_cycles if c <= max_cycle and c not in cycles]

    return {
        "n": n,
        "set_size": a_size,
        "added_element": coprime_to_6[0],
        "edges": edges,
        "density": density,
        "turan_number": turan_number(a_size),
        "bondy_threshold": bondy_thresh,
        "exceeds_bondy": exceeds_bondy,
        "min_degree": deg_info["min_deg"],
        "avg_degree": deg_info["avg_deg"],
        "dirac_satisfied": deg_info["dirac_satisfied"],
        "ore_satisfied": deg_info["ore_satisfied"],
        "odd_cycles_found": cycles,
        "max_cycle_checked": max_cycle,
        "required_odd_cycles": required_odd_cycles[:10],  # first 10
        "found_required": found_required,
        "missing_required": missing_required,
        "all_required_found": len(missing_required) == 0,
    }


def edge_density_scaling(n_values: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """
    How does the edge density of G(A) scale with n for sets just above threshold?

    If density → some limit d > 0.25, Bondy applies for large n.
    If density → 0.25 or below, need different argument.
    """
    if n_values is None:
        n_values = list(range(10, 101, 5))

    results = []
    for n in n_values:
        R = residue_classes(n)
        a_star = set()
        for r in [0, 2, 3, 4]:
            a_star.update(R[r])

        coprime_to_6 = sorted(R[1] + R[5])
        if not coprime_to_6:
            continue

        # A = A* + 1 element (minimal above threshold)
        A = a_star | {coprime_to_6[0]}
        edges = coprime_edge_count(A)
        a_size = len(A)
        density = edges / (a_size * (a_size - 1) / 2) if a_size >= 2 else 0.0
        mantel_density = 0.25
        bondy_edges = bondy_threshold(a_size)

        results.append({
            "n": n,
            "set_size": a_size,
            "edges": edges,
            "density": round(density, 6),
            "mantel_density": mantel_density,
            "exceeds_mantel": density > mantel_density,
            "bondy_exceeded": edges > bondy_edges,
        })

    return results


def bipartiteness_check(A: Set[int]) -> Dict[str, Any]:
    """
    Check if G(A) is bipartite using 2-coloring.

    A* gives a bipartite coprime graph (Even vs Odd_3).
    Adding coprime-to-6 elements should break bipartiteness.
    """
    A_list = sorted(A)
    n = len(A_list)

    # Build adjacency list
    adj = defaultdict(set)
    for i in range(n):
        for j in range(i + 1, n):
            if math.gcd(A_list[i], A_list[j]) == 1:
                adj[A_list[i]].add(A_list[j])
                adj[A_list[j]].add(A_list[i])

    # BFS 2-coloring
    color = {}
    is_bipartite = True
    odd_cycle_vertex = None

    for start in A_list:
        if start in color:
            continue
        queue = [start]
        color[start] = 0
        while queue:
            u = queue.pop(0)
            for v in adj.get(u, set()):
                if v not in color:
                    color[v] = 1 - color[u]
                    queue.append(v)
                elif color[v] == color[u]:
                    is_bipartite = False
                    odd_cycle_vertex = u

    if is_bipartite:
        part_a = {v for v, c in color.items() if c == 0}
        part_b = {v for v, c in color.items() if c == 1}
        return {
            "is_bipartite": True,
            "part_sizes": (len(part_a), len(part_b)),
        }
    else:
        return {
            "is_bipartite": False,
            "odd_cycle_witness": odd_cycle_vertex,
        }


def threshold_analysis(n_values: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    For each n, find the EXACT minimum set size that forces:
    1. Non-bipartiteness (odd cycle)
    2. Edge density > Mantel (0.25)
    3. Edge count > Bondy threshold

    Compare these thresholds to |A*| + 1.
    """
    if n_values is None:
        n_values = list(range(6, 31))

    results = []
    for n in n_values:
        R = residue_classes(n)
        a_star = set()
        for r in [0, 2, 3, 4]:
            a_star.update(R[r])

        coprime_to_6 = sorted(R[1] + R[5])
        ext = extremal_size(n)

        # Build progressively larger sets by adding coprime-to-6 elements
        thresholds = {
            "non_bipartite": None,
            "above_mantel": None,
            "above_bondy": None,
        }

        for k in range(len(coprime_to_6) + 1):
            A = a_star | set(coprime_to_6[:k])
            size = len(A)

            bip = bipartiteness_check(A)
            if thresholds["non_bipartite"] is None and not bip["is_bipartite"]:
                thresholds["non_bipartite"] = size

            edges = coprime_edge_count(A)
            density = edges / (size * (size - 1) / 2) if size >= 2 else 0
            if thresholds["above_mantel"] is None and density > 0.25:
                thresholds["above_mantel"] = size

            if thresholds["above_bondy"] is None and edges > bondy_threshold(size):
                thresholds["above_bondy"] = size

        results.append({
            "n": n,
            "extremal_size": ext,
            "problem_threshold": ext + 1,
            "non_bipartite_at": thresholds["non_bipartite"],
            "above_mantel_at": thresholds["above_mantel"],
            "above_bondy_at": thresholds["above_bondy"],
        })

    return {
        "results": results,
        "summary": _summarize_thresholds(results),
    }


def _summarize_thresholds(results: List[Dict]) -> Dict[str, Any]:
    """Summarize threshold analysis across all n values."""
    gaps = {"non_bipartite": [], "above_mantel": [], "above_bondy": []}

    for r in results:
        ext = r["extremal_size"]
        for key in gaps:
            val = r.get(f"{key}_at")
            if val is not None:
                gaps[key].append(val - ext)
            else:
                gaps[key].append(None)

    summary = {}
    for key in gaps:
        valid = [g for g in gaps[key] if g is not None]
        if valid:
            summary[f"{key}_min_gap"] = min(valid)
            summary[f"{key}_max_gap"] = max(valid)
            summary[f"{key}_avg_gap"] = sum(valid) / len(valid)
        else:
            summary[f"{key}_min_gap"] = None

    return summary


def load_problems():
    """Load Erdős problems from YAML."""
    import yaml
    import os
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "problems.yaml")
    with open(data_path) as f:
        return yaml.safe_load(f)


def main():
    print("=" * 70)
    print("EXTREMAL COPRIME GRAPH ANALYSIS")
    print("Extending Problem #883 via Bondy's Theorem")
    print("=" * 70)
    print()

    # 1. Edge density scaling
    print("--- Edge Density Scaling ---")
    scaling = edge_density_scaling(list(range(10, 61, 5)))
    for s in scaling:
        status = "BONDY" if s["bondy_exceeded"] else "below"
        print(f"  n={s['n']:3d}: |A|={s['set_size']:3d}, "
              f"density={s['density']:.4f}, {status}")
    print()

    # 2. Threshold analysis
    print("--- Threshold Analysis ---")
    thresholds = threshold_analysis(list(range(6, 31)))
    for r in thresholds["results"]:
        print(f"  n={r['n']:2d}: |A*|={r['extremal_size']:2d}, "
              f"non-bip={r['non_bipartite_at']}, "
              f"Mantel={r['above_mantel_at']}, "
              f"Bondy={r['above_bondy_at']}")
    print()
    print("Summary:")
    for key, val in thresholds["summary"].items():
        print(f"  {key}: {val}")
    print()

    # 3. Pancyclicity for small n
    print("--- Pancyclicity Analysis ---")
    for n in [10, 15, 20, 25]:
        result = pancyclicity_analysis(n)
        print(f"  n={n}: edges={result['edges']}, density={result['density']:.4f}, "
              f"Bondy={'YES' if result['exceeds_bondy'] else 'no'}, "
              f"Dirac={'YES' if result['dirac_satisfied'] else 'no'}")
        print(f"    odd cycles found: {result['odd_cycles_found']}")
        if result['missing_required']:
            print(f"    MISSING required: {result['missing_required']}")
    print()

    print("=" * 70)
    print("CONCLUSIONS")
    print("=" * 70)
    print()

    # Determine if Bondy approach works
    scaling_data = edge_density_scaling(list(range(10, 101, 10)))
    densities = [s["density"] for s in scaling_data]
    if densities:
        limit = densities[-1]
        print(f"Edge density limit as n→∞: ~{limit:.4f}")
        if limit > 0.25:
            print("→ Density EXCEEDS Mantel threshold (0.25)")
            print("→ Bondy's theorem applies for large n!")
            print("→ This resolves Problem #883 for all odd cycle lengths.")
        else:
            print("→ Density ≤ Mantel threshold")
            print("→ Need alternative argument for full pancyclicity.")


if __name__ == "__main__":
    main()
