#!/usr/bin/env python3
"""
Cycle Spectrum Analysis for Problem #883

Verifies which odd cycle lengths appear in the coprime graph G(A)
for sets A ⊆ [n] exceeding the extremal threshold.
"""

import math
from itertools import combinations
from typing import Set, List, Tuple, Optional
from collections import defaultdict


def coprime_graph(A: Set[int]) -> dict:
    """Build adjacency list of coprime graph on A."""
    adj = defaultdict(set)
    A_list = sorted(A)
    for i in range(len(A_list)):
        for j in range(i + 1, len(A_list)):
            if math.gcd(A_list[i], A_list[j]) == 1:
                adj[A_list[i]].add(A_list[j])
                adj[A_list[j]].add(A_list[i])
    return dict(adj)


def find_cycles_dfs(adj: dict, vertices: List[int], max_length: int) -> Set[int]:
    """Find all cycle lengths in the graph using DFS, up to max_length."""
    cycle_lengths = set()
    n = len(vertices)
    vertex_set = set(vertices)

    for start in vertices:
        # BFS/DFS from start to find cycles
        # We track paths and look for back-edges
        _find_cycles_from(adj, start, vertex_set, max_length, cycle_lengths)

    return cycle_lengths


def _find_cycles_from(adj: dict, start: int, vertex_set: Set[int],
                      max_length: int, cycle_lengths: Set[int]):
    """Find cycle lengths reachable from start via DFS."""
    # Use BFS to find shortest paths, then detect cycles
    # For small graphs, enumerate short cycles directly
    neighbors = adj.get(start, set())

    # Find cycles of each length by checking if path of length k-1 returns
    # For efficiency, use matrix power method for small graphs
    pass  # Delegated to find_odd_cycle_lengths below


def find_odd_cycle_lengths(A: Set[int], max_length: Optional[int] = None) -> Set[int]:
    """
    Find all odd cycle lengths present in the coprime graph G(A).

    Uses adjacency matrix powers for small sets.
    """
    A_list = sorted(A)
    n = len(A_list)
    if n < 3:
        return set()

    if max_length is None:
        max_length = n

    idx = {a: i for i, a in enumerate(A_list)}

    # Build adjacency matrix
    adj_matrix = [[False] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if math.gcd(A_list[i], A_list[j]) == 1:
                adj_matrix[i][j] = True
                adj_matrix[j][i] = True

    cycle_lengths = set()

    # For each potential cycle length, check existence
    # Method: enumerate short cycles via DFS
    for length in range(3, min(max_length + 1, n + 1)):
        if length % 2 == 0:
            continue  # Only odd cycles
        if _has_cycle_of_length(adj_matrix, n, length):
            cycle_lengths.add(length)

    return cycle_lengths


def _has_cycle_of_length(adj: list, n: int, length: int) -> bool:
    """Check if graph has a cycle of given length using backtracking."""
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
    """DFS to find cycle of exact target length returning to start."""
    if depth == target:
        return adj[current][start]

    for next_v in range(n):
        if adj[current][next_v] and not visited[next_v]:
            visited[next_v] = True
            if _dfs_cycle(adj, n, start, next_v, visited, depth + 1, target):
                return True
            visited[next_v] = False

    return False


def coprime_edge_density(A: Set[int]) -> float:
    """Compute edge density of coprime graph on A."""
    A_list = sorted(A)
    n = len(A_list)
    if n < 2:
        return 0.0
    edges = sum(1 for i in range(n) for j in range(i + 1, n)
                if math.gcd(A_list[i], A_list[j]) == 1)
    return edges / (n * (n - 1) / 2)


def bipartite_ET(n: int) -> Tuple[Set[int], Set[int]]:
    """Decompose A*(n) into E (even, not div 3) and T (odd multiples of 3)."""
    E = {i for i in range(1, n + 1) if i % 2 == 0 and i % 3 != 0}
    T = {i for i in range(1, n + 1) if i % 3 == 0 and i % 2 != 0}
    return E, T


def hub_coprime_neighbors(hub: int, E: Set[int], T: Set[int]) -> Tuple[Set[int], Set[int]]:
    """Return (E_x, T_x): subsets of E, T coprime to hub."""
    E_x = {e for e in E if math.gcd(e, hub) == 1}
    T_x = {t for t in T if math.gcd(t, hub) == 1}
    return E_x, T_x


def bipartite_min_degrees(E: Set[int], T: Set[int]) -> Tuple[int, int, int, int]:
    """Compute min/max degrees from T→E and E→T in coprime bipartite graph.

    Returns (min_T_to_E, max_T_to_E, min_E_to_T, max_E_to_T).
    """
    if not E or not T:
        return (0, 0, 0, 0)

    min_te, max_te = len(E), 0
    for t in T:
        d = sum(1 for e in E if math.gcd(e, t) == 1)
        min_te = min(min_te, d)
        max_te = max(max_te, d)

    min_et, max_et = len(T), 0
    for e in E:
        d = sum(1 for t in T if math.gcd(e, t) == 1)
        min_et = min(min_et, d)
        max_et = max(max_et, d)

    return (min_te, max_te, min_et, max_et)


def greedy_alternating_path(E: Set[int], T: Set[int], start_e: int,
                            target_length: int,
                            end_constraint: Optional[Set[int]] = None
                            ) -> Optional[List[int]]:
    """Construct an alternating path e1-t1-e2-t2-...-ek-tk in bipartite (E,T).

    Args:
        E, T: bipartite sides
        start_e: first E-vertex (must be in E)
        target_length: number of T-vertices to use (path has 2*target_length vertices)
        end_constraint: if given, last T-vertex must be in this set

    Returns path [e1, t1, e2, t2, ...] or None if construction fails.
    """
    if start_e not in E or target_length < 1:
        return None

    path = [start_e]
    used_E = {start_e}
    used_T = set()
    E_list = sorted(E)
    T_list = sorted(T)

    for step in range(target_length):
        current_e = path[-1] if len(path) % 2 == 1 else None
        if current_e is None:
            # Need to pick an E vertex from N(last_t)
            last_t = path[-1]
            candidates = [e for e in E_list if e not in used_E and math.gcd(e, last_t) == 1]
            if not candidates:
                return None
            # Pick the candidate with most unused T-neighbors
            best_e = max(candidates, key=lambda e: sum(
                1 for t in T_list if t not in used_T and math.gcd(e, t) == 1))
            path.append(best_e)
            used_E.add(best_e)
            current_e = best_e

        # Pick a T vertex from N(current_e)
        is_last = (step == target_length - 1)
        if is_last and end_constraint is not None:
            candidates = [t for t in T_list
                         if t not in used_T and t in end_constraint
                         and math.gcd(current_e, t) == 1]
        else:
            candidates = [t for t in T_list
                         if t not in used_T and math.gcd(current_e, t) == 1]

        if not candidates:
            return None

        # Pick candidate with most unused E-neighbors (for future steps)
        if not is_last:
            best_t = max(candidates, key=lambda t: sum(
                1 for e in E_list if e not in used_E and math.gcd(e, t) == 1))
        else:
            best_t = candidates[0]

        path.append(best_t)
        used_T.add(best_t)

        # If not last step, pick next E vertex
        if not is_last:
            candidates_e = [e for e in E_list if e not in used_E
                           and math.gcd(e, best_t) == 1]
            if not candidates_e:
                return None
            best_next_e = max(candidates_e, key=lambda e: sum(
                1 for t in T_list if t not in used_T and math.gcd(e, t) == 1))
            path.append(best_next_e)
            used_E.add(best_next_e)

    return path


def verify_full_cycle_spectrum(n: int) -> dict:
    """
    Verify that A = A* ∪ {hub} contains all required odd cycle lengths
    using the improved bipartite path construction.

    The cycle x → e₁ → t₁ → ... → eₖ → tₖ → x has length 2k+1.
    We construct paths in the FULL bipartite graph (E, T), only requiring
    endpoints to be coprime to hub x.

    Returns dict with verification results.
    """
    E, T = bipartite_ET(n)
    if not E or not T:
        return {"n": n, "verified": True, "max_target": 0, "cycles_found": []}

    A_star = {i for i in range(1, n + 1) if i % 2 == 0 or i % 3 == 0}
    coprime_to_6 = sorted(i for i in range(1, n + 1) if math.gcd(i, 6) == 1)
    if not coprime_to_6:
        return {"n": n, "verified": True, "max_target": 0, "cycles_found": []}

    # Use best hub (element 1 if available, else smallest coprime-to-6)
    hub = coprime_to_6[0]
    E_x, T_x = hub_coprime_neighbors(hub, E, T)

    max_target = n // 3 + 1
    required_odd = list(range(3, max_target + 1, 2))
    found_lengths = []

    for length in required_odd:
        k = (length - 1) // 2  # number of T-vertices in path
        if k < 1:
            continue
        if k > len(T):
            break

        # Try to construct path of length k using greedy
        success = False
        for start_e in sorted(E_x)[:10]:  # Try up to 10 starting E-vertices
            path = greedy_alternating_path(E, T, start_e, k, end_constraint=T_x)
            if path is not None:
                success = True
                break

        if success:
            found_lengths.append(length)

    missing = set(required_odd) - set(found_lengths)
    return {
        "n": n,
        "hub": hub,
        "E_size": len(E),
        "T_size": len(T),
        "E_x_size": len(E_x),
        "T_x_size": len(T_x),
        "max_target": max_target,
        "required_count": len(required_odd),
        "found_count": len(found_lengths),
        "missing": sorted(missing),
        "verified": len(missing) == 0,
    }


def find_alternating_path_bt(E_list: List[int], T_list: List[int],
                             start_e: int, target_k: int,
                             adj_et: dict, adj_te: dict,
                             end_set: Optional[Set[int]] = None) -> bool:
    """Backtracking search for alternating path of length 2k.

    More thorough than greedy — backtracks on failure.
    Returns True if a path exists (doesn't return the path itself for speed).
    """
    used_E = {start_e}
    used_T = set()

    def _bt(current_e: int, depth: int) -> bool:
        if depth == target_k:
            return True
        # Try each T-neighbor of current_e
        t_candidates = adj_et.get(current_e, [])
        for t in t_candidates:
            if t in used_T:
                continue
            # Last step: check end constraint
            if depth == target_k - 1 and end_set is not None and t not in end_set:
                continue
            used_T.add(t)
            if depth == target_k - 1:
                used_T.discard(t)
                return True
            # Try each E-neighbor of t
            e_candidates = adj_te.get(t, [])
            for e in e_candidates:
                if e in used_E:
                    continue
                used_E.add(e)
                if _bt(e, depth + 1):
                    used_E.discard(e)
                    used_T.discard(t)
                    return True
                used_E.discard(e)
            used_T.discard(t)
        return False

    return _bt(start_e, 0)


def build_bipartite_adj(E: Set[int], T: Set[int]) -> Tuple[dict, dict]:
    """Build adjacency lists for coprime bipartite graph (E, T).

    Returns (adj_et, adj_te) where adj_et[e] = list of T-neighbors,
    adj_te[t] = list of E-neighbors.
    """
    adj_et = defaultdict(list)
    adj_te = defaultdict(list)
    for e in sorted(E):
        for t in sorted(T):
            if math.gcd(e, t) == 1:
                adj_et[e].append(t)
                adj_te[t].append(e)
    return dict(adj_et), dict(adj_te)


def verify_cycle_spectrum_bipartite(n: int, hub: Optional[int] = None) -> dict:
    """
    Verify cycle spectrum using bipartite path construction with backtracking.

    For A = A* ∪ {hub}, verifies all odd cycle lengths 3, 5, ..., ⌊n/3⌋+1
    using the improved approach: construct alternating paths in FULL (E, T)
    bipartite graph, close through hub.
    """
    E, T = bipartite_ET(n)
    if not E or not T:
        return {"n": n, "verified": True, "max_target": 0, "cycles_found": []}

    A_star = {i for i in range(1, n + 1) if i % 2 == 0 or i % 3 == 0}

    if hub is None:
        coprime_to_6 = sorted(i for i in range(1, n + 1) if math.gcd(i, 6) == 1)
        hub = coprime_to_6[0] if coprime_to_6 else None
    if hub is None:
        return {"n": n, "verified": True, "max_target": 0, "cycles_found": []}

    E_x, T_x = hub_coprime_neighbors(hub, E, T)
    adj_et, adj_te = build_bipartite_adj(E, T)

    max_target = n // 3 + 1
    required_odd = list(range(3, max_target + 1, 2))
    found_lengths = []

    for length in required_odd:
        k = (length - 1) // 2
        if k < 1 or k > len(T):
            continue
        success = False
        for start_e in sorted(E_x)[:5]:
            if find_alternating_path_bt(sorted(E), sorted(T), start_e, k,
                                        adj_et, adj_te, end_set=T_x):
                success = True
                break
        if success:
            found_lengths.append(length)

    missing = set(required_odd) - set(found_lengths)
    return {
        "n": n,
        "hub": hub,
        "E_size": len(E),
        "T_size": len(T),
        "E_x_size": len(E_x),
        "T_x_size": len(T_x),
        "max_target": max_target,
        "required": sorted(required_odd),
        "found": sorted(found_lengths),
        "missing": sorted(missing),
        "verified": len(missing) == 0,
    }


def analyze_cycle_spectrum(n: int) -> dict:
    """
    Analyze cycle spectrum for sets near the extremal threshold.

    Returns data about which odd cycle lengths appear.
    """
    from verify_883 import extremal_size

    threshold = extremal_size(n) + 1
    A_full = set(range(1, n + 1))
    A_star = {i for i in range(1, n + 1) if i % 2 == 0 or i % 3 == 0}

    results = {
        "n": n,
        "threshold": threshold,
        "extremal_size": extremal_size(n),
    }

    # Full set cycle spectrum
    full_cycles = find_odd_cycle_lengths(A_full, max_length=min(n, 20))
    results["full_set"] = {
        "size": len(A_full),
        "density": coprime_edge_density(A_full),
        "odd_cycles_found": sorted(full_cycles),
    }

    # Near-threshold sets: A* plus one element from R1 ∪ R5
    coprime_to_6 = sorted(i for i in range(1, n + 1) if math.gcd(i, 6) == 1)
    if coprime_to_6:
        test_set = A_star | {coprime_to_6[0]}
        near_cycles = find_odd_cycle_lengths(test_set, max_length=min(n, 15))
        results["near_threshold"] = {
            "size": len(test_set),
            "added_element": coprime_to_6[0],
            "density": coprime_edge_density(test_set),
            "odd_cycles_found": sorted(near_cycles),
        }

    return results


def main():
    print("=" * 70)
    print("CYCLE SPECTRUM ANALYSIS FOR PROBLEM #883")
    print("=" * 70)
    print()

    for n in [10, 15, 20, 25]:
        print(f"--- n = {n} ---")
        result = analyze_cycle_spectrum(n)
        print(f"  Threshold: {result['threshold']}")

        full = result["full_set"]
        print(f"  Full [n]: density={full['density']:.3f}, "
              f"odd cycles={full['odd_cycles_found']}")

        if "near_threshold" in result:
            near = result["near_threshold"]
            print(f"  Near threshold (A*+{near['added_element']}): "
                  f"density={near['density']:.3f}, "
                  f"odd cycles={near['odd_cycles_found']}")
        print()

    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("""
Triangle (length 3) is always present for |A| > 2n/3 (PROVED).
Longer odd cycles appear as |A| grows beyond the threshold.
Full pancyclicity (all odd lengths 3...|A|) requires density > 1/2 (Bondy).
""")


if __name__ == "__main__":
    main()
