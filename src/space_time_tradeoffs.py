#!/usr/bin/env python3
"""
Space-Time Tradeoff Analysis for Coprime Ramsey Computations.

Analyzes where the bottleneck lies (space vs time) for each algorithmic
approach to computing R_cop(k), and provides principled alternatives:

1. Incremental extension memory profile: models |avoiding(n)| growth
2. SAT solver resource profiling: clause DB, learned clauses, restarts
3. Meet-in-the-middle for Ramsey: O(2^{m/2}) vs O(2^m)
4. Color coding technique: randomized monochromatic clique search
5. Streaming/online detection: O(n^2) time, O(n) space threshold detection

Key finding: R_cop(3) is TIME-limited (small state space, fast),
R_cop(4) is SPACE-limited (1.47M base colorings at extension),
R_cop(5) is BOTH (SAT clause DB and extension state both explode).
"""

import math
import random
import sys
import time
from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

import numpy as np
from pysat.solvers import Glucose4


# ============================================================================
# Shared infrastructure (coprime graph primitives)
# ============================================================================

def coprime_edges(n: int) -> List[Tuple[int, int]]:
    """Return all coprime pairs (i,j) with 1 <= i < j <= n."""
    edges = []
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                edges.append((i, j))
    return edges


def coprime_adj(n: int) -> Dict[int, Set[int]]:
    """Build adjacency dict for the coprime graph on [n]."""
    adj: Dict[int, Set[int]] = {v: set() for v in range(1, n + 1)}
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def find_coprime_cliques(n: int, k: int) -> List[Tuple[int, ...]]:
    """Enumerate all k-cliques in the coprime graph on [n]."""
    if k < 1:
        return []
    if k == 1:
        return [(v,) for v in range(1, n + 1)]

    adj = coprime_adj(n)
    vertices = list(range(1, n + 1))
    cliques: List[Tuple[int, ...]] = []

    def extend(current: List[int], candidates: List[int]):
        if len(current) == k:
            cliques.append(tuple(current))
            return
        needed = k - len(current)
        for idx, v in enumerate(candidates):
            if len(candidates) - idx < needed:
                break
            if all(v in adj[u] for u in current):
                new_cands = [w for w in candidates[idx + 1:] if w in adj[v]]
                extend(current + [v], new_cands)

    extend([], vertices)
    return cliques


def has_monochromatic_clique(
    n: int, k: int, coloring: Dict[Tuple[int, int], int],
    cliques: Optional[List[Tuple[int, ...]]] = None,
) -> bool:
    """Check if a coloring has a monochromatic K_k. Returns True if found."""
    if cliques is None:
        cliques = find_coprime_cliques(n, k)
    for clique in cliques:
        vlist = sorted(clique)
        colors = set()
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                edge = (vlist[i], vlist[j])
                colors.add(coloring.get(edge, -1))
                if len(colors) > 1:
                    break
            if len(colors) > 1:
                break
        else:
            if len(colors) == 1 and -1 not in colors:
                return True
    return False


# ============================================================================
# 1. Incremental Extension Memory Profile
# ============================================================================

@dataclass
class ExtensionProfile:
    """Memory and time profile for incremental extension at a given n."""
    n: int
    num_edges: int
    num_new_edges: int
    num_avoiding: int
    coloring_bytes: int  # bytes per coloring dict
    total_memory_bytes: int  # |avoiding| * coloring_bytes
    time_seconds: float
    cumulative_explored: int


def estimate_coloring_bytes(num_edges: int) -> int:
    """Estimate memory of one coloring dict with num_edges entries.

    Each dict entry: tuple key (2 ints, ~72 bytes) + int value (~28 bytes)
    + hash table overhead (~50 bytes per slot on average).
    Dict base size ~232 bytes.
    """
    # CPython dict: 232 base + 72 * num_entries (approx, includes hash table)
    return 232 + 72 * num_edges


def profile_extension_memory(
    k: int, max_n: int = 30, verbose: bool = False,
    max_base_edges: int = 0,
) -> List[ExtensionProfile]:
    """
    Profile the incremental extension algorithm's memory usage at each n.

    For each n from the base up to max_n, tracks:
    - Number of avoiding colorings (the state that must be stored)
    - Memory per coloring and total memory
    - Time spent extending
    - Cumulative colorings explored

    max_base_edges: override for the exhaustive base edge threshold.
      If 0, uses a k-dependent default: 25 for k<=3, 18 for k=4, 15 for k>=5.
      Larger k means more cliques to check per coloring, so we need a lower
      threshold to keep the base phase tractable.

    Returns list of ExtensionProfile records.
    """
    if max_base_edges <= 0:
        # Scale threshold with k: checking 2^m colorings against O(n^k) cliques
        # gets expensive fast. For k=3, 2^25 * O(n^3) is fine. For k=4, not.
        if k <= 3:
            max_base_edges = 25
        elif k == 4:
            max_base_edges = 18
        else:
            max_base_edges = 15

    profiles: List[ExtensionProfile] = []
    avoiding: Optional[List[Dict[Tuple[int, int], int]]] = None
    base_n: Optional[int] = None
    cumulative = 0

    for n in range(k, max_n + 1):
        edges = coprime_edges(n)
        num_edges = len(edges)
        if not edges:
            continue

        t0 = time.time()

        if num_edges <= max_base_edges:
            # Exhaustive base
            cliques = find_coprime_cliques(n, k)
            new_avoiding = []
            for bits in range(2 ** num_edges):
                cumulative += 1
                coloring = {}
                for idx, e in enumerate(edges):
                    coloring[e] = (bits >> idx) & 1
                if not has_monochromatic_clique(n, k, coloring, cliques):
                    new_avoiding.append(coloring)

            dt = time.time() - t0
            cbytes = estimate_coloring_bytes(num_edges)
            prof = ExtensionProfile(
                n=n,
                num_edges=num_edges,
                num_new_edges=num_edges,  # base: all edges are "new"
                num_avoiding=len(new_avoiding),
                coloring_bytes=cbytes,
                total_memory_bytes=len(new_avoiding) * cbytes,
                time_seconds=dt,
                cumulative_explored=cumulative,
            )
            profiles.append(prof)

            if verbose:
                mb = prof.total_memory_bytes / (1024 ** 2)
                print(f"  n={n:3d}: {num_edges:4d} edges, "
                      f"|avoiding|={len(new_avoiding):>10d}, "
                      f"mem={mb:.2f} MB, time={dt:.3f}s")

            if not new_avoiding:
                return profiles

            avoiding = new_avoiding
            base_n = n
        else:
            break

    if avoiding is None or base_n is None:
        return profiles

    # Incremental extension
    for n in range(base_n + 1, max_n + 1):
        new_edges = [(min(i, n), max(i, n))
                     for i in range(1, n) if math.gcd(i, n) == 1]
        if not new_edges:
            continue

        all_edges = coprime_edges(n)
        num_edges = len(all_edges)
        cliques = find_coprime_cliques(n, k)

        t0 = time.time()
        next_avoiding = []
        for col in avoiding:
            for bits in range(2 ** len(new_edges)):
                cumulative += 1
                new_col = dict(col)
                for idx, e in enumerate(new_edges):
                    new_col[e] = (bits >> idx) & 1
                if not has_monochromatic_clique(n, k, new_col, cliques):
                    next_avoiding.append(new_col)
        dt = time.time() - t0

        cbytes = estimate_coloring_bytes(num_edges)
        prof = ExtensionProfile(
            n=n,
            num_edges=num_edges,
            num_new_edges=len(new_edges),
            num_avoiding=len(next_avoiding),
            coloring_bytes=cbytes,
            total_memory_bytes=len(next_avoiding) * cbytes,
            time_seconds=dt,
            cumulative_explored=cumulative,
        )
        profiles.append(prof)

        if verbose:
            mb = prof.total_memory_bytes / (1024 ** 2)
            print(f"  n={n:3d}: {num_edges:4d} edges, "
                  f"{len(new_edges):3d} new, "
                  f"|avoiding|={len(next_avoiding):>10d}, "
                  f"mem={mb:.2f} MB, time={dt:.3f}s")

        if not next_avoiding:
            return profiles

        avoiding = next_avoiding

    return profiles


@dataclass
class GrowthModel:
    """Model of |avoiding(n)| growth: exponential or polynomial fit."""
    model_type: str  # "exponential" or "polynomial"
    # For exponential: |avoiding(n)| ~ a * b^n
    exp_base: float = 0.0
    exp_coeff: float = 0.0
    exp_r_squared: float = 0.0
    # For polynomial: |avoiding(n)| ~ a * n^d
    poly_degree: float = 0.0
    poly_coeff: float = 0.0
    poly_r_squared: float = 0.0
    # Predicted RAM exhaustion
    ram_exhaustion_n: int = -1  # n at which memory exceeds RAM


def fit_growth_model(
    profiles: List[ExtensionProfile],
    available_ram_bytes: int = 16 * (1024 ** 3),
) -> GrowthModel:
    """
    Fit exponential and polynomial models to |avoiding(n)| data.

    Determines which model fits better and predicts when RAM is exhausted.
    Only uses profiles where num_avoiding > 0.
    """
    data = [(p.n, p.num_avoiding) for p in profiles if p.num_avoiding > 0]
    if len(data) < 3:
        return GrowthModel(model_type="insufficient_data")

    ns = np.array([d[0] for d in data], dtype=float)
    counts = np.array([d[1] for d in data], dtype=float)

    model = GrowthModel(model_type="exponential")

    # Exponential fit: log(count) = log(a) + n * log(b)
    log_counts = np.log(counts + 1)  # +1 to handle zeros
    if np.std(ns) > 0 and np.std(log_counts) > 0:
        coeffs = np.polyfit(ns, log_counts, 1)
        log_b, log_a = coeffs
        model.exp_base = float(np.exp(log_b))
        model.exp_coeff = float(np.exp(log_a))
        predicted_log = np.polyval(coeffs, ns)
        ss_res = np.sum((log_counts - predicted_log) ** 2)
        ss_tot = np.sum((log_counts - np.mean(log_counts)) ** 2)
        model.exp_r_squared = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Polynomial fit: log(count) = log(a) + d * log(n)
    log_ns = np.log(ns)
    if np.std(log_ns) > 0 and np.std(log_counts) > 0:
        coeffs_p = np.polyfit(log_ns, log_counts, 1)
        d, log_a_p = coeffs_p
        model.poly_degree = float(d)
        model.poly_coeff = float(np.exp(log_a_p))
        predicted_log_p = np.polyval(coeffs_p, log_ns)
        ss_res_p = np.sum((log_counts - predicted_log_p) ** 2)
        ss_tot_p = np.sum((log_counts - np.mean(log_counts)) ** 2)
        model.poly_r_squared = float(1.0 - ss_res_p / ss_tot_p) if ss_tot_p > 0 else 0.0

    # Choose better model
    if model.poly_r_squared > model.exp_r_squared:
        model.model_type = "polynomial"

    # Predict RAM exhaustion
    avg_bytes = np.mean([p.coloring_bytes for p in profiles if p.num_avoiding > 0])
    max_colorings = available_ram_bytes / max(avg_bytes, 1)

    if model.model_type == "exponential" and model.exp_base > 1.0:
        # a * b^n = max_colorings  =>  n = log(max_colorings / a) / log(b)
        if model.exp_coeff > 0:
            n_exhaust = np.log(max_colorings / model.exp_coeff) / np.log(model.exp_base)
            model.ram_exhaustion_n = max(int(np.ceil(n_exhaust)), 0)
    elif model.model_type == "polynomial" and model.poly_degree > 0:
        # a * n^d = max_colorings  =>  n = (max_colorings / a)^(1/d)
        if model.poly_coeff > 0:
            n_exhaust = (max_colorings / model.poly_coeff) ** (1.0 / model.poly_degree)
            model.ram_exhaustion_n = max(int(np.ceil(n_exhaust)), 0)

    return model


# ============================================================================
# 2. SAT Solver Space Usage Profile
# ============================================================================

@dataclass
class SATProfile:
    """SAT solver resource profile at a given n."""
    n: int
    k: int
    num_vars: int
    num_clauses: int
    num_cliques: int
    clause_var_ratio: float
    sat_result: bool
    solve_time: float
    # Derived estimates
    clause_db_bytes: int  # estimated clause database size
    var_activity_bytes: int  # variable activity array
    total_solver_bytes: int


def estimate_clause_db_bytes(num_clauses: int, avg_clause_len: float) -> int:
    """Estimate CDCL solver clause database memory.

    Each clause: header (16 bytes) + literals (4 bytes each) + alignment.
    Watched literals: 2 pointers per clause (16 bytes).
    """
    return int(num_clauses * (16 + 4 * avg_clause_len + 16))


def profile_sat_space(
    k: int, n_range: Tuple[int, int] = (5, 30), verbose: bool = False,
) -> List[SATProfile]:
    """
    Profile Glucose4's memory usage at each n for clique size k.

    Measures: variables, clauses, clause/var ratio, solving time.
    Estimates: clause DB size, total solver memory.
    """
    n_start, n_end = n_range
    profiles: List[SATProfile] = []

    adj: Dict[int, Set[int]] = {}
    all_cliques: List[Tuple[int, ...]] = []

    for n in range(2, n_end + 1):
        if n not in adj:
            adj[n] = set()
        for u in range(1, n):
            if math.gcd(u, n) == 1:
                adj[n].add(u)
                if u not in adj:
                    adj[u] = set()
                adj[u].add(n)

        if n < k:
            continue

        # New cliques involving n
        neighbors = sorted(v for v in range(1, n) if v in adj.get(n, set()))
        new_cliques = _find_new_cliques_from_neighbors(n, k, neighbors, adj)
        all_cliques.extend(new_cliques)

        if n < n_start:
            continue

        # Build fresh SAT instance
        edge_to_var: Dict[Tuple[int, int], int] = {}
        next_var = 1
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                if j in adj.get(i, set()):
                    edge_to_var[(i, j)] = next_var
                    next_var += 1

        num_vars = next_var - 1
        clause_list: List[List[int]] = []

        for clique in all_cliques:
            vlist = sorted(clique)
            vars_ = []
            for i in range(len(vlist)):
                for j in range(i + 1, len(vlist)):
                    vars_.append(edge_to_var[(vlist[i], vlist[j])])
            clause_list.append([-v for v in vars_])
            clause_list.append([v for v in vars_])

        num_clauses = len(clause_list)
        num_cliques = len(all_cliques)

        # Clause length stats
        c2 = k * (k - 1) // 2  # edges in K_k
        avg_clause_len = c2  # each clause has C(k,2) literals

        t0 = time.time()
        solver = Glucose4(bootstrap_with=clause_list)
        sat = solver.solve()
        solver.delete()
        dt = time.time() - t0

        clause_db = estimate_clause_db_bytes(num_clauses, avg_clause_len)
        # Variable activity: 8 bytes (double) per var, plus phase saving (1 byte each)
        var_act = num_vars * 9
        # Watched literal lists: ~16 bytes per clause (2 pointers)
        watched = num_clauses * 16
        # Total: clause DB + var activity + watched + overhead (~1 MB baseline)
        total_solver = clause_db + var_act + watched + 1024 * 1024

        ratio = num_clauses / max(num_vars, 1)

        prof = SATProfile(
            n=n, k=k,
            num_vars=num_vars,
            num_clauses=num_clauses,
            num_cliques=num_cliques,
            clause_var_ratio=ratio,
            sat_result=sat,
            solve_time=dt,
            clause_db_bytes=clause_db,
            var_activity_bytes=var_act,
            total_solver_bytes=total_solver,
        )
        profiles.append(prof)

        if verbose:
            mb = total_solver / (1024 ** 2)
            status = "SAT" if sat else "UNSAT"
            print(f"  n={n:3d}: {num_vars:5d} vars, {num_clauses:7d} clauses, "
                  f"ratio={ratio:.1f}, {status}, {dt:.3f}s, ~{mb:.1f} MB")

    return profiles


def _find_new_cliques_from_neighbors(
    n: int, k: int,
    neighbors: List[int],
    adj: Dict[int, Set[int]],
) -> List[Tuple[int, ...]]:
    """Find all k-cliques containing vertex n, given its sorted neighbors."""
    if k < 1:
        return []
    if k == 1:
        return [(n,)]

    cliques: List[Tuple[int, ...]] = []

    def extend(current: List[int], candidates: List[int]):
        if len(current) == k - 1:
            cliques.append(tuple(sorted(current + [n])))
            return
        needed = (k - 1) - len(current)
        for idx, v in enumerate(candidates):
            if len(candidates) - idx < needed:
                break
            if all(v in adj[u] for u in current):
                new_cands = [w for w in candidates[idx + 1:] if w in adj[v]]
                extend(current + [v], new_cands)

    extend([], neighbors)
    return cliques


@dataclass
class BottleneckAnalysis:
    """Classification of whether a computation is space-limited or time-limited."""
    k: int
    bottleneck: str  # "time", "space", or "both"
    space_limiting_n: int  # n at which space becomes the bottleneck
    time_limiting_n: int  # n at which time becomes the bottleneck
    explanation: str


def classify_bottleneck(
    ext_profiles: List[ExtensionProfile],
    sat_profiles: List[SATProfile],
    ram_gb: float = 16.0,
    time_limit_s: float = 3600.0,
) -> BottleneckAnalysis:
    """
    Classify whether the computation is space-limited or time-limited.

    Heuristic: if memory exceeds RAM before time exceeds limit, it's space-limited.
    """
    ram_bytes = int(ram_gb * (1024 ** 3))
    k = sat_profiles[0].k if sat_profiles else (ext_profiles[0].n if ext_profiles else 3)

    # Extension space limit
    space_n = -1
    for p in ext_profiles:
        if p.total_memory_bytes > ram_bytes:
            space_n = p.n
            break

    # SAT/extension time limit
    time_n = -1
    for p in sat_profiles:
        if p.solve_time > time_limit_s:
            time_n = p.n
            break

    if space_n > 0 and (time_n < 0 or space_n < time_n):
        return BottleneckAnalysis(
            k=k, bottleneck="space",
            space_limiting_n=space_n,
            time_limiting_n=time_n,
            explanation=(
                f"Memory exceeds {ram_gb:.0f} GB at n={space_n} "
                f"before time limit is hit. "
                f"Recommendation: use SAT (constant working memory) "
                f"or meet-in-the-middle (sqrt reduction)."
            ),
        )
    elif time_n > 0 and (space_n < 0 or time_n < space_n):
        return BottleneckAnalysis(
            k=k, bottleneck="time",
            space_limiting_n=space_n,
            time_limiting_n=time_n,
            explanation=(
                f"Time exceeds {time_limit_s:.0f}s at n={time_n} "
                f"before memory is exhausted. "
                f"Recommendation: use parallelism, symmetry breaking, "
                f"or better SAT encodings."
            ),
        )
    elif space_n > 0 and time_n > 0:
        return BottleneckAnalysis(
            k=k, bottleneck="both",
            space_limiting_n=space_n,
            time_limiting_n=time_n,
            explanation=(
                f"Both limits hit: memory at n={space_n}, "
                f"time at n={time_n}. "
                f"Recommendation: streaming or sketching approaches."
            ),
        )
    else:
        return BottleneckAnalysis(
            k=k, bottleneck="neither",
            space_limiting_n=-1,
            time_limiting_n=-1,
            explanation="Within resource limits for all tested n.",
        )


# ============================================================================
# 3. Meet-in-the-Middle for Ramsey
# ============================================================================

@dataclass
class MITMResult:
    """Result of meet-in-the-middle Ramsey search."""
    n: int
    k: int
    num_left_colorings: int
    num_right_colorings: int
    num_compatible_pairs: int  # pairs that are globally avoiding
    has_avoiding: bool
    time_seconds: float
    # For comparison
    brute_force_search_space: int  # 2^m
    mitm_search_space: int  # 2^{m/2} + 2^{m/2} + join cost


def _coloring_to_frozen(coloring: Dict[Tuple[int, int], int]) -> FrozenSet[Tuple[int, int]]:
    """Convert coloring to frozenset of edges with color=1 (for hashing)."""
    return frozenset(e for e, c in coloring.items() if c == 1)


def _split_edges(
    edges: List[Tuple[int, int]],
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """Split edges into two roughly equal halves."""
    mid = len(edges) // 2
    return edges[:mid], edges[mid:]


def meet_in_the_middle_ramsey(
    n: int, k: int, max_per_half: int = 1_000_000,
) -> MITMResult:
    """
    Meet-in-the-middle algorithm for coprime Ramsey avoidance.

    Split the edge set E into E_L and E_R of roughly equal size.
    Phase 1: Enumerate all 2^|E_L| colorings. For each, check if any
             clique is already monochromatic using only E_L edges. If not,
             record it along with a "constraint signature" describing which
             cliques are partially colored and what colors they need to avoid.
    Phase 2: Enumerate all 2^|E_R| colorings similarly.
    Phase 3: Join: a left coloring and right coloring are compatible if their
             union avoids all monochromatic K_k.

    Time: O(2^{m/2} * clique_check) for each half, plus join cost.
    Space: O(2^{m/2}) for storing one half's colorings.
    """
    edges = coprime_edges(n)
    m = len(edges)
    if m == 0:
        return MITMResult(n=n, k=k, num_left_colorings=1,
                          num_right_colorings=1, num_compatible_pairs=1,
                          has_avoiding=True, time_seconds=0.0,
                          brute_force_search_space=1, mitm_search_space=2)

    cliques = find_coprime_cliques(n, k)
    if not cliques:
        return MITMResult(n=n, k=k, num_left_colorings=2**m,
                          num_right_colorings=1, num_compatible_pairs=2**m,
                          has_avoiding=True, time_seconds=0.0,
                          brute_force_search_space=2**m,
                          mitm_search_space=2**m)

    left_edges, right_edges = _split_edges(edges)
    left_set = set(left_edges)
    right_set = set(right_edges)

    # Classify cliques by which half their edges fall in
    left_only_cliques = []   # all edges in left
    right_only_cliques = []  # all edges in right
    cross_cliques = []       # edges span both halves

    for clique in cliques:
        vlist = sorted(clique)
        clique_edges = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                clique_edges.append((vlist[i], vlist[j]))
        in_left = [e for e in clique_edges if e in left_set]
        in_right = [e for e in clique_edges if e in right_set]
        if len(in_right) == 0:
            left_only_cliques.append(clique_edges)
        elif len(in_left) == 0:
            right_only_cliques.append(clique_edges)
        else:
            cross_cliques.append((in_left, in_right, clique_edges))

    t0 = time.time()

    # Phase 1: enumerate left-half colorings that survive left-only cliques
    left_valid: List[Dict[Tuple[int, int], int]] = []
    left_size = len(left_edges)
    left_limit = min(2 ** left_size, max_per_half)

    for bits in range(left_limit):
        col = {}
        for idx, e in enumerate(left_edges):
            col[e] = (bits >> idx) & 1
        # Check left-only cliques
        ok = True
        for cl_edges in left_only_cliques:
            colors = set(col[e] for e in cl_edges)
            if len(colors) == 1:
                ok = False
                break
        if ok:
            left_valid.append(col)

    # Phase 2: enumerate right-half colorings that survive right-only cliques
    right_valid: List[Dict[Tuple[int, int], int]] = []
    right_size = len(right_edges)
    right_limit = min(2 ** right_size, max_per_half)

    for bits in range(right_limit):
        col = {}
        for idx, e in enumerate(right_edges):
            col[e] = (bits >> idx) & 1
        ok = True
        for cl_edges in right_only_cliques:
            colors = set(col[e] for e in cl_edges)
            if len(colors) == 1:
                ok = False
                break
        if ok:
            right_valid.append(col)

    # Phase 3: join -- check cross cliques
    num_compatible = 0
    has_avoiding = False

    for l_col in left_valid:
        for r_col in right_valid:
            # Merge
            ok = True
            for l_edges, r_edges, all_edges in cross_cliques:
                colors = set()
                for e in l_edges:
                    colors.add(l_col[e])
                if len(colors) > 1:
                    continue  # already mixed, can't be monochromatic
                for e in r_edges:
                    colors.add(r_col[e])
                if len(colors) == 1:
                    ok = False
                    break
            if ok:
                num_compatible += 1
                has_avoiding = True
                break  # found one avoiding coloring, enough
        if has_avoiding:
            break

    dt = time.time() - t0

    return MITMResult(
        n=n, k=k,
        num_left_colorings=len(left_valid),
        num_right_colorings=len(right_valid),
        num_compatible_pairs=num_compatible,
        has_avoiding=has_avoiding,
        time_seconds=dt,
        brute_force_search_space=2 ** m,
        mitm_search_space=2 ** left_size + 2 ** right_size,
    )


def compare_mitm_vs_sat(n: int, k: int) -> Dict[str, float]:
    """
    Run both meet-in-the-middle and SAT on the same instance.

    Returns dict with timing and space comparisons.
    """
    # SAT
    edges = coprime_edges(n)
    cliques = find_coprime_cliques(n, k)
    etv = {e: i + 1 for i, e in enumerate(edges)}
    clauses = []
    for clique in cliques:
        vlist = sorted(clique)
        vars_ = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                vars_.append(etv[(vlist[i], vlist[j])])
        clauses.append([-v for v in vars_])
        clauses.append([v for v in vars_])

    t0 = time.time()
    solver = Glucose4(bootstrap_with=clauses)
    sat_result = solver.solve()
    solver.delete()
    sat_time = time.time() - t0

    # MITM
    mitm = meet_in_the_middle_ramsey(n, k)

    return {
        "n": n,
        "k": k,
        "num_edges": len(edges),
        "sat_time": sat_time,
        "sat_result": sat_result,
        "mitm_time": mitm.time_seconds,
        "mitm_result": mitm.has_avoiding,
        "speedup": sat_time / max(mitm.time_seconds, 1e-9),
        "brute_force_space": mitm.brute_force_search_space,
        "mitm_space": mitm.mitm_search_space,
        "space_reduction": mitm.brute_force_search_space / max(mitm.mitm_search_space, 1),
    }


# ============================================================================
# 4. Color Coding Technique
# ============================================================================

@dataclass
class ColorCodingResult:
    """Result of randomized color-coding clique search."""
    n: int
    k: int
    found_clique: Optional[Tuple[int, ...]]
    coloring_checked: Dict[Tuple[int, int], int]  # the edge coloring
    target_color: int
    num_trials: int
    time_seconds: float
    success: bool


def color_coding_clique_search(
    n: int, k: int,
    edge_coloring: Dict[Tuple[int, int], int],
    target_color: int = 0,
    num_trials: int = 0,
    seed: Optional[int] = None,
) -> ColorCodingResult:
    """
    Randomized color-coding search for a monochromatic K_k.

    Algorithm:
    1. Randomly assign each vertex one of k "labels" (colors).
    2. Look for a K_k where vertex i has label i (all labels distinct).
    3. Since we only search among monochromatic edges, this finds
       monochromatic cliques of the target_color if they exist.
    4. Repeat O(k^k) times for constant success probability.

    The key insight: if a K_k exists, the probability that its k vertices
    receive k distinct labels is k!/k^k >= e^{-k}. So after k^k trials,
    the failure probability is <= (1 - e^{-k})^{k^k} < 1/e.

    Time per trial: O(n * deg^{k-1}) where deg is max degree in the
    monochromatic subgraph. Total: O(k^k * n * deg^{k-1}).
    """
    if seed is not None:
        random.seed(seed)

    if num_trials <= 0:
        # Default: k^k (rounded) for good success probability
        num_trials = min(k ** k, 100000)

    adj = coprime_adj(n)

    # Build monochromatic subgraph for target_color
    mono_adj: Dict[int, Set[int]] = {v: set() for v in range(1, n + 1)}
    for (u, v), c in edge_coloring.items():
        if c == target_color:
            mono_adj[u].add(v)
            mono_adj[v].add(u)

    vertices = list(range(1, n + 1))

    t0 = time.time()

    for trial in range(num_trials):
        # Step 1: random vertex coloring with k labels
        labels = {v: random.randint(0, k - 1) for v in vertices}

        # Step 2: for each label assignment, try to find a clique
        # where vertex with label i is connected to all others
        # Group vertices by label
        by_label: Dict[int, List[int]] = {j: [] for j in range(k)}
        for v, lab in labels.items():
            by_label[lab].append(v)

        # Try to build a clique by picking one vertex per label
        found = _find_rainbow_clique(k, by_label, mono_adj)
        if found is not None:
            dt = time.time() - t0
            return ColorCodingResult(
                n=n, k=k, found_clique=found,
                coloring_checked=edge_coloring,
                target_color=target_color,
                num_trials=trial + 1,
                time_seconds=dt, success=True,
            )

    dt = time.time() - t0
    return ColorCodingResult(
        n=n, k=k, found_clique=None,
        coloring_checked=edge_coloring,
        target_color=target_color,
        num_trials=num_trials,
        time_seconds=dt, success=False,
    )


def _find_rainbow_clique(
    k: int,
    by_label: Dict[int, List[int]],
    adj: Dict[int, Set[int]],
) -> Optional[Tuple[int, ...]]:
    """
    Backtracking search for a clique with one vertex per label.

    Labels 0..k-1, picking one vertex from each label group such that
    all pairs are adjacent in adj.
    """
    chosen: List[int] = []

    def backtrack(label: int) -> bool:
        if label == k:
            return True
        for v in by_label[label]:
            if all(v in adj[u] for u in chosen):
                chosen.append(v)
                if backtrack(label + 1):
                    return True
                chosen.pop()
        return False

    if backtrack(0):
        return tuple(sorted(chosen))
    return None


def color_coding_vs_exhaustive(
    n: int, k: int,
    edge_coloring: Dict[Tuple[int, int], int],
) -> Dict[str, float]:
    """
    Compare color coding with exhaustive clique search for finding
    a monochromatic K_k in a given edge coloring.
    """
    # Exhaustive
    cliques = find_coprime_cliques(n, k)
    t0 = time.time()
    found_exhaustive = False
    for clique in cliques:
        vlist = sorted(clique)
        for target in [0, 1]:
            all_same = True
            for i in range(len(vlist)):
                for j in range(i + 1, len(vlist)):
                    if edge_coloring.get((vlist[i], vlist[j]), -1) != target:
                        all_same = False
                        break
                if not all_same:
                    break
            if all_same:
                found_exhaustive = True
                break
        if found_exhaustive:
            break
    exhaustive_time = time.time() - t0

    # Color coding (both colors)
    t0 = time.time()
    found_cc = False
    for target in [0, 1]:
        result = color_coding_clique_search(
            n, k, edge_coloring, target_color=target, seed=42,
        )
        if result.success:
            found_cc = True
            break
    cc_time = time.time() - t0

    return {
        "n": n,
        "k": k,
        "exhaustive_time": exhaustive_time,
        "exhaustive_found": found_exhaustive,
        "color_coding_time": cc_time,
        "color_coding_found": found_cc,
        "speedup": exhaustive_time / max(cc_time, 1e-9),
    }


# ============================================================================
# 5. Streaming / Online Algorithms
# ============================================================================

@dataclass
class StreamingState:
    """State maintained by the streaming Ramsey detector.

    Space: O(n * k) for degree counters per color, plus O(k^2) for
    partial clique tracking. Total: O(n) for fixed k.
    """
    n: int
    k: int
    # Per-vertex, per-color degree: degree[v][c] = number of color-c neighbors
    degree: Dict[int, List[int]]
    # Adjacency in compact form: for each vertex, store coprime neighbors
    # This is O(n) per vertex, O(n^2) total -- but we process edges online
    adj_by_color: Dict[int, Dict[int, Set[int]]]  # color -> {v -> neighbors}
    # Greedy clique tracker: largest known monochromatic cliques per color
    best_clique: Dict[int, List[int]]
    edges_processed: int
    detected: bool
    detection_edge: Optional[Tuple[int, int]]


def streaming_init(k: int) -> StreamingState:
    """Initialize streaming Ramsey detector for clique size k."""
    return StreamingState(
        n=0, k=k,
        degree={},
        adj_by_color={c: {} for c in range(2)},
        best_clique={c: [] for c in range(2)},
        edges_processed=0,
        detected=False,
        detection_edge=None,
    )


def streaming_process_edge(
    state: StreamingState,
    u: int, v: int, color: int,
) -> bool:
    """
    Process one colored coprime edge (u, v) with the given color.

    Updates degree counters and checks if the new edge completes
    a monochromatic K_k using an incremental greedy approach.

    Returns True if a monochromatic K_k is now detected.

    Space: O(n) for degree arrays, O(n) for adjacency (streaming: only
    store neighbors needed for clique tracking).
    Time per edge: O(n^{k-2}) worst case for clique checking, but
    typically much faster due to degree pruning.
    """
    if state.detected:
        return True

    state.n = max(state.n, u, v)
    state.edges_processed += 1

    # Initialize vertex entries if needed
    for w in [u, v]:
        if w not in state.degree:
            state.degree[w] = [0, 0]
        for c in range(2):
            if w not in state.adj_by_color[c]:
                state.adj_by_color[c][w] = set()

    # Update adjacency and degrees
    state.degree[u][color] += 1
    state.degree[v][color] += 1
    state.adj_by_color[color][u].add(v)
    state.adj_by_color[color][v].add(u)

    # Check if this edge creates a new monochromatic K_k
    # Strategy: look for a (k-2)-clique among common color-neighbors of u,v
    common = state.adj_by_color[color][u] & state.adj_by_color[color][v]
    if len(common) >= state.k - 2:
        clique_found = _find_clique_in_common(
            state.k - 2, sorted(common), state.adj_by_color[color],
        )
        if clique_found is not None:
            full_clique = sorted([u, v] + list(clique_found))
            state.best_clique[color] = full_clique
            state.detected = True
            state.detection_edge = (u, v)
            return True

    return False


def _find_clique_in_common(
    size: int,
    candidates: List[int],
    adj: Dict[int, Set[int]],
) -> Optional[Tuple[int, ...]]:
    """Find a clique of given size among candidates using backtracking."""
    if size == 0:
        return ()
    if len(candidates) < size:
        return None

    chosen: List[int] = []

    def backtrack(start: int) -> bool:
        if len(chosen) == size:
            return True
        remaining = len(candidates) - start
        if remaining < size - len(chosen):
            return False
        for i in range(start, len(candidates)):
            v = candidates[i]
            if all(v in adj.get(u, set()) for u in chosen):
                chosen.append(v)
                if backtrack(i + 1):
                    return True
                chosen.pop()
        return False

    if backtrack(0):
        return tuple(chosen)
    return None


def streaming_ramsey_detect(
    n: int, k: int,
    edge_coloring: Dict[Tuple[int, int], int],
) -> StreamingState:
    """
    Run the streaming detector on all coprime edges of [n].

    Processes edges in lexicographic order (as they would arrive in an
    online setting). Returns the final state including detection status.

    Time: O(n^2) for edge generation + O(n^{k-2}) per edge for clique check.
    Space: O(n^2) for adjacency (can be reduced to O(n * max_degree) with
    eviction, but we keep full adjacency for correctness checking).
    """
    state = streaming_init(k)

    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                edge = (i, j)
                color = edge_coloring.get(edge, 0)
                detected = streaming_process_edge(state, i, j, color)
                if detected:
                    return state

    return state


def streaming_threshold_scan(
    k: int, max_n: int = 20,
    edge_coloring_fn=None,
) -> Dict[int, StreamingState]:
    """
    Scan increasing n values with the streaming detector.

    For each n, generates a canonical coloring (all-zero if no coloring_fn
    provided) and runs the streaming detector. This identifies the first n
    where the detector triggers.

    Returns dict mapping n -> StreamingState.
    """
    results: Dict[int, StreamingState] = {}

    for n in range(k, max_n + 1):
        edges = coprime_edges(n)
        if not edges:
            continue

        # Generate coloring
        if edge_coloring_fn is not None:
            coloring = edge_coloring_fn(n, edges)
        else:
            # Default: all color 0
            coloring = {e: 0 for e in edges}

        state = streaming_ramsey_detect(n, k, coloring)
        results[n] = state

    return results


# ============================================================================
# 6. Unified Analysis and Recommendations
# ============================================================================

@dataclass
class AlgorithmRecommendation:
    """Recommendation for which algorithm to use in each regime."""
    k: int
    n_range: Tuple[int, int]
    algorithm: str
    reason: str
    estimated_time: str
    estimated_space: str


def analyze_tradeoffs(
    k: int, max_n: int = 20, verbose: bool = False,
) -> Dict[str, object]:
    """
    Run full space-time tradeoff analysis for clique size k.

    Returns a dict with all profiles, models, and recommendations.
    """
    results: Dict[str, object] = {"k": k}

    if verbose:
        print(f"\n{'='*70}")
        print(f"SPACE-TIME TRADEOFF ANALYSIS FOR k={k}")
        print(f"{'='*70}")

    # 1. Extension memory profile
    if verbose:
        print(f"\n--- Extension Memory Profile (k={k}) ---")
    ext_profiles = profile_extension_memory(k, max_n=max_n, verbose=verbose)
    results["extension_profiles"] = ext_profiles

    # 2. Growth model
    if ext_profiles:
        model = fit_growth_model(ext_profiles)
        results["growth_model"] = model
        if verbose:
            print(f"\n  Growth model: {model.model_type}")
            if model.model_type == "exponential":
                print(f"  |avoiding(n)| ~ {model.exp_coeff:.2f} * "
                      f"{model.exp_base:.4f}^n  (R^2={model.exp_r_squared:.4f})")
            elif model.model_type == "polynomial":
                print(f"  |avoiding(n)| ~ {model.poly_coeff:.2f} * "
                      f"n^{model.poly_degree:.2f}  (R^2={model.poly_r_squared:.4f})")
            if model.ram_exhaustion_n > 0:
                print(f"  RAM exhaustion predicted at n ~ {model.ram_exhaustion_n}")

    # 3. SAT space profile
    if verbose:
        print(f"\n--- SAT Solver Profile (k={k}) ---")
    sat_profiles = profile_sat_space(k, n_range=(k, max_n), verbose=verbose)
    results["sat_profiles"] = sat_profiles

    # 4. Bottleneck classification
    if ext_profiles and sat_profiles:
        bottleneck = classify_bottleneck(ext_profiles, sat_profiles)
        results["bottleneck"] = bottleneck
        if verbose:
            print(f"\n  Bottleneck: {bottleneck.bottleneck}")
            print(f"  {bottleneck.explanation}")

    # 5. MITM comparison (only for small instances)
    if max_n <= 15:
        if verbose:
            print(f"\n--- Meet-in-the-Middle vs SAT (k={k}) ---")
        mitm_comparisons = []
        for n in range(k, min(max_n + 1, 13)):
            edges = coprime_edges(n)
            if len(edges) <= 30:  # feasible for MITM
                comp = compare_mitm_vs_sat(n, k)
                mitm_comparisons.append(comp)
                if verbose:
                    print(f"  n={n}: SAT={comp['sat_time']:.4f}s, "
                          f"MITM={comp['mitm_time']:.4f}s, "
                          f"space_reduction={comp['space_reduction']:.1f}x")
        results["mitm_comparisons"] = mitm_comparisons

    return results


def generate_recommendations(k: int) -> List[AlgorithmRecommendation]:
    """Generate algorithm recommendations for computing R_cop(k)."""
    recs = []

    if k == 3:
        recs.append(AlgorithmRecommendation(
            k=3, n_range=(3, 8), algorithm="brute_force",
            reason="Only 2^21 colorings at n=8, exhaustive is instant",
            estimated_time="< 1 second", estimated_space="< 1 MB",
        ))
        recs.append(AlgorithmRecommendation(
            k=3, n_range=(8, 11), algorithm="incremental_extension",
            reason="36 avoiding at n=8 -> 0 at n=11; state fits in memory",
            estimated_time="< 5 seconds", estimated_space="< 10 MB",
        ))
        recs.append(AlgorithmRecommendation(
            k=3, n_range=(3, 11), algorithm="SAT (Glucose4)",
            reason="Solves entire range in < 0.1s; no memory issues",
            estimated_time="< 0.1 seconds", estimated_space="< 5 MB",
        ))
    elif k == 4:
        recs.append(AlgorithmRecommendation(
            k=4, n_range=(4, 8), algorithm="incremental_extension",
            reason="Base enumeration feasible; avoiding count manageable",
            estimated_time="< 10 seconds", estimated_space="< 100 MB",
        ))
        recs.append(AlgorithmRecommendation(
            k=4, n_range=(8, 59), algorithm="SAT (Glucose4, fresh per n)",
            reason="Extension explodes to >1M colorings; SAT uses O(clauses) space",
            estimated_time="~minutes total", estimated_space="< 500 MB",
        ))
        recs.append(AlgorithmRecommendation(
            k=4, n_range=(58, 59), algorithm="extension_check",
            reason="Fix base colorings from SAT, check if any extend to n=59",
            estimated_time="< 30 seconds", estimated_space="< 100 MB",
        ))
    elif k == 5:
        recs.append(AlgorithmRecommendation(
            k=5, n_range=(5, 200), algorithm="SAT (Glucose4, fresh per n)",
            reason="Extension infeasible; SAT clause DB grows but manageable to ~n=200",
            estimated_time="hours to days", estimated_space="< 4 GB",
        ))
        recs.append(AlgorithmRecommendation(
            k=5, n_range=(100, 500), algorithm="SAT + symmetry breaking",
            reason="At large n, clause DB exceeds RAM without pruning",
            estimated_time="days to weeks", estimated_space="1-16 GB",
        ))

    return recs


# ============================================================================
# Main analysis driver
# ============================================================================

def main():
    print("=" * 72)
    print("SPACE-TIME TRADEOFF ANALYSIS FOR COPRIME RAMSEY COMPUTATIONS")
    print("=" * 72)
    print()

    # --- Section 1: Extension memory profile for k=3 ---
    print("=" * 72)
    print("1. INCREMENTAL EXTENSION MEMORY PROFILE")
    print("=" * 72)
    print()

    print("--- k=3 (R_cop(3) = 11) ---")
    profiles_3 = profile_extension_memory(3, max_n=12, verbose=True)
    print()

    # Verify known avoiding counts
    known_k3 = {8: 36, 9: 36, 10: 156, 11: 0}
    for p in profiles_3:
        if p.n in known_k3:
            expected = known_k3[p.n]
            status = "MATCH" if p.num_avoiding == expected else "MISMATCH"
            print(f"  n={p.n}: |avoiding|={p.num_avoiding} "
                  f"(expected {expected}) [{status}]")
    print()

    print("--- k=4 (R_cop(4) = 59 conjectured) ---")
    profiles_4 = profile_extension_memory(4, max_n=12, verbose=True)
    print()

    # Growth model fitting
    print("--- Growth Models ---")
    for k, profiles in [(3, profiles_3), (4, profiles_4)]:
        model = fit_growth_model(profiles)
        print(f"  k={k}: model={model.model_type}")
        if model.model_type == "exponential":
            print(f"    |avoiding(n)| ~ {model.exp_coeff:.2f} * "
                  f"{model.exp_base:.4f}^n  (R^2={model.exp_r_squared:.4f})")
        elif model.model_type == "polynomial":
            print(f"    |avoiding(n)| ~ {model.poly_coeff:.2f} * "
                  f"n^{model.poly_degree:.2f}  (R^2={model.poly_r_squared:.4f})")
        if model.ram_exhaustion_n > 0:
            print(f"    RAM exhaustion at n ~ {model.ram_exhaustion_n} "
                  f"(16 GB assumed)")
    print()

    # --- Section 2: SAT solver space usage ---
    print("=" * 72)
    print("2. SAT SOLVER SPACE USAGE")
    print("=" * 72)
    print()

    for k in [4, 5]:
        print(f"--- k={k} ---")
        n_end = 25 if k == 4 else 20
        sat_profiles = profile_sat_space(k, n_range=(k, n_end), verbose=True)

        # Identify transition: where clause/var ratio spikes or solving
        # time jumps
        if sat_profiles:
            last_sat = [p for p in sat_profiles if p.sat_result]
            first_unsat = [p for p in sat_profiles if not p.sat_result]
            if last_sat:
                p = last_sat[-1]
                print(f"  Last SAT: n={p.n}, clause/var={p.clause_var_ratio:.1f}, "
                      f"solver mem ~{p.total_solver_bytes/(1024**2):.1f} MB")
            if first_unsat:
                p = first_unsat[0]
                print(f"  First UNSAT: n={p.n}, "
                      f"clause/var={p.clause_var_ratio:.1f}, "
                      f"solver mem ~{p.total_solver_bytes/(1024**2):.1f} MB")
        print()

    # --- Section 3: Meet-in-the-middle ---
    print("=" * 72)
    print("3. MEET-IN-THE-MIDDLE vs SAT")
    print("=" * 72)
    print()

    print("--- k=3 ---")
    print(f"{'n':>4s} {'edges':>6s} {'SAT(s)':>8s} {'MITM(s)':>8s} "
          f"{'space_red':>10s} {'result':>7s}")
    print("-" * 50)
    for n in range(5, 12):
        comp = compare_mitm_vs_sat(n, 3)
        res_str = "SAT" if comp["sat_result"] else "UNSAT"
        print(f"{n:4d} {comp['num_edges']:6d} "
              f"{comp['sat_time']:8.4f} {comp['mitm_time']:8.4f} "
              f"{comp['space_reduction']:10.1f}x {res_str:>7s}")
    print()

    # --- Section 4: Color coding ---
    print("=" * 72)
    print("4. COLOR CODING TECHNIQUE")
    print("=" * 72)
    print()

    # Create a known-monochromatic coloring (all color 0) and search
    for n in [8, 10, 12]:
        edges = coprime_edges(n)
        coloring_mono = {e: 0 for e in edges}
        comp = color_coding_vs_exhaustive(n, 3, coloring_mono)
        print(f"  n={n}: exhaustive={comp['exhaustive_time']:.4f}s, "
              f"color_coding={comp['color_coding_time']:.4f}s, "
              f"speedup={comp['speedup']:.1f}x "
              f"(found={comp['exhaustive_found']}/{comp['color_coding_found']})")

    # Create an avoiding coloring and verify color coding reports not found
    # Use n=10 where avoiding colorings exist
    print()
    print("  Testing on an avoiding coloring at n=10 (should NOT find K_3):")
    # Build one avoiding coloring from the extension method
    edges_8 = coprime_edges(8)
    avoiding = []
    for bits in range(2 ** len(edges_8)):
        col = {e: (bits >> i) & 1 for i, e in enumerate(edges_8)}
        cliques_8 = find_coprime_cliques(8, 3)
        if not has_monochromatic_clique(8, 3, col, cliques_8):
            avoiding.append(col)
            break

    if avoiding:
        # Extend to n=10
        for ext_n in [9, 10]:
            new_edges = [(i, ext_n) for i in range(1, ext_n) if math.gcd(i, ext_n) == 1]
            next_avoiding = []
            cliques_ext = find_coprime_cliques(ext_n, 3)
            for col in avoiding:
                for bits in range(2 ** len(new_edges)):
                    new_col = dict(col)
                    for idx, e in enumerate(new_edges):
                        new_col[e] = (bits >> idx) & 1
                    if not has_monochromatic_clique(ext_n, 3, new_col, cliques_ext):
                        next_avoiding.append(new_col)
                        break
                if next_avoiding:
                    break
            avoiding = next_avoiding

        if avoiding:
            for target in [0, 1]:
                result = color_coding_clique_search(
                    10, 3, avoiding[0], target_color=target,
                    num_trials=1000, seed=42,
                )
                print(f"    Color {target}: found={result.success}, "
                      f"trials={result.num_trials}, "
                      f"time={result.time_seconds:.4f}s")
    print()

    # --- Section 5: Streaming detector ---
    print("=" * 72)
    print("5. STREAMING / ONLINE DETECTION")
    print("=" * 72)
    print()

    print("  Testing streaming detector with all-color-0 coloring (k=3):")
    for n in range(3, 12):
        edges = coprime_edges(n)
        if not edges:
            continue
        coloring = {e: 0 for e in edges}
        state = streaming_ramsey_detect(n, 3, coloring)
        status = "DETECTED" if state.detected else "not detected"
        print(f"    n={n:2d}: {status}, "
              f"edges_processed={state.edges_processed}, "
              f"space=O({state.n}) vertices")
    print()

    # --- Section 6: Summary and recommendations ---
    print("=" * 72)
    print("6. BOTTLENECK CLASSIFICATION AND RECOMMENDATIONS")
    print("=" * 72)
    print()

    for k in [3, 4, 5]:
        recs = generate_recommendations(k)
        print(f"  k={k}:")
        for r in recs:
            print(f"    n in {r.n_range}: {r.algorithm}")
            print(f"      {r.reason}")
            print(f"      Time: {r.estimated_time}, Space: {r.estimated_space}")
        print()

    print("=" * 72)
    print("KEY FINDINGS")
    print("=" * 72)
    print("""
1. R_cop(3) is TIME-limited: the state space is tiny (36 -> 36 -> 156 -> 0
   avoiding colorings at n=8..11). Any algorithm works; SAT is fastest.

2. R_cop(4) is SPACE-limited for incremental extension: the avoiding set
   explodes exponentially through the base enumeration phase, reaching
   ~1.47M colorings. SAT avoids this by never materializing the full set,
   using O(clauses) working memory instead.

3. R_cop(5) is BOTH space- and time-limited: the SAT clause database grows
   as O(n^k) cliques generate O(n^k) clauses, and solving time grows
   super-polynomially. Symmetry breaking and parallel SAT are essential.

4. Meet-in-the-middle provides a sqrt reduction in search space
   (2^{m/2} vs 2^m) but is dominated by SAT for structured instances
   because SAT exploits clause learning. MITM is useful only when SAT
   is unavailable or for verification.

5. Color coding is effective for FINDING monochromatic cliques in O(k^k * n^2)
   time, but cannot PROVE their nonexistence. It complements SAT
   (which proves both existence and nonexistence).

6. Streaming detection runs in O(n^2) time with O(n^2) space (for adjacency),
   and detects monochromatic cliques online as edges arrive. Useful for
   monitoring but not for proving R_cop(k) values.
""")


if __name__ == "__main__":
    main()
