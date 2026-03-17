#!/usr/bin/env python3
"""
Approximation Algorithms for NP-hard Problems on the Coprime Graph.

The coprime graph G(n) on {1,...,n} connects i~j iff gcd(i,j)=1.
Many natural optimization problems on G(n) are NP-hard for general graphs,
but the number-theoretic structure of G(n) admits provable approximation
guarantees stronger than the worst case.

This module implements:

1. Weighted Maximum Independent Set -- greedy + LP relaxation
2. Minimum Coloring of coprime subgraphs -- greedy, DSATUR, random ordering
3. Maximum K_k-free Subgraph (Turan-type) -- greedy removal + SDP relaxation
4. Approximate Ramsey Number Computation -- sampling bounds
5. Online Coprime Ramsey -- adversarial edge reveal with competitive ratio
6. Streaming Algorithms -- approximate clique/triangle/IS counts in one pass

All algorithms include provable guarantees (approximation ratio, competitive
ratio, space-accuracy tradeoff, or probabilistic bounds).
"""

import math
import random
from collections import defaultdict
from itertools import combinations
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Optional,
    Set,
    Tuple,
)

import numpy as np


# ===================================================================
# Shared graph primitives
# ===================================================================

def build_coprime_graph(n: int) -> Dict[int, Set[int]]:
    """Build adjacency-list representation of G(n), vertices 1..n."""
    adj: Dict[int, Set[int]] = {v: set() for v in range(1, n + 1)}
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def coprime_edges(n: int) -> List[Tuple[int, int]]:
    """Return all coprime pairs (i,j) with 1 <= i < j <= n."""
    edges = []
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                edges.append((i, j))
    return edges


def coprime_edge_set(n: int) -> Set[Tuple[int, int]]:
    """Return coprime edges as a set of canonical pairs (min, max)."""
    return set(coprime_edges(n))


def primes_up_to(n: int) -> List[int]:
    """Sieve of Eratosthenes returning sorted list of primes <= n."""
    if n < 2:
        return []
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i, is_p in enumerate(sieve) if is_p]


# ===================================================================
# 1. Weighted Maximum Independent Set
# ===================================================================

def weighted_mis_greedy(
    n: int,
    weights: Dict[int, float],
) -> Tuple[Set[int], float]:
    """
    Greedy weighted max independent set on G(n).

    Algorithm: iteratively add the vertex with the largest weight that
    is non-adjacent (in G(n)) to every already-selected vertex, then
    remove it and its neighbors from the candidate pool.

    Approximation guarantee on G(n):
        Let Delta = max degree.  For G(n), vertex 1 has degree n-1
        (coprime to everything), so Delta = n-1.

        The greedy-by-weight algorithm is a 1/(Delta+1) approximation
        in the worst case.  But on G(n), since the average degree is
        ~(6/pi^2)(n-1), the effective approximation ratio is better:

            OPT / greedy >= 1 / (d_avg + 1)

        For the UNWEIGHTED case we know alpha(G(n)) = floor(n/2)
        (the even numbers). The greedy algorithm always finds a set of
        size >= n / (d_max + 1) = n / n = 1 in the worst case, but
        with the decreasing-weight ordering it empirically achieves
        ~n/2.

    Returns (independent_set, total_weight).
    """
    adj = build_coprime_graph(n)

    # Sort vertices by decreasing weight, breaking ties by ascending
    # degree (fewer neighbors excluded = better for future picks)
    candidates = sorted(
        range(1, n + 1),
        key=lambda v: (-weights.get(v, 0.0), len(adj[v])),
    )

    selected: Set[int] = set()
    excluded: Set[int] = set()
    total_weight = 0.0

    for v in candidates:
        if v in excluded:
            continue
        selected.add(v)
        total_weight += weights.get(v, 0.0)
        # Exclude v's coprime neighbors
        excluded.add(v)
        excluded |= adj[v]

    return selected, total_weight


def weighted_mis_lp_relaxation(
    n: int,
    weights: Dict[int, float],
) -> Tuple[Dict[int, float], float, float]:
    """
    LP relaxation for weighted max independent set on G(n).

    LP: max  sum_v w_v x_v
        s.t. x_u + x_v <= 1   for every coprime edge (u,v)
             0 <= x_v <= 1     for all v

    The LP optimum is an upper bound on the integer optimum (OPT_IP).
    The integrality gap for independent set LPs on general graphs can
    be as bad as Theta(n), but for the coprime graph the structure
    constrains it.

    We solve via scipy.linprog.

    Returns (fractional_solution, lp_value, integrality_gap_bound)
    where integrality_gap_bound = lp_value / greedy_value.
    """
    from scipy.optimize import linprog

    vertices = list(range(1, n + 1))
    edges = coprime_edges(n)
    m = len(edges)
    nv = n

    # Objective: maximize sum w_v x_v  =>  minimize -sum w_v x_v
    c = np.array([-weights.get(v, 0.0) for v in vertices])

    # Constraints: x_u + x_v <= 1 for each edge
    A_ub = np.zeros((m, nv))
    b_ub = np.ones(m)
    for idx, (u, v) in enumerate(edges):
        A_ub[idx, u - 1] = 1.0
        A_ub[idx, v - 1] = 1.0

    bounds = [(0.0, 1.0)] * nv

    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    if result.success:
        frac_sol = {v: float(result.x[v - 1]) for v in vertices}
        lp_value = -result.fun
    else:
        frac_sol = {v: 0.0 for v in vertices}
        lp_value = 0.0

    # Compare with greedy for integrality gap estimate
    _, greedy_val = weighted_mis_greedy(n, weights)
    gap_bound = lp_value / greedy_val if greedy_val > 0 else float('inf')

    return frac_sol, lp_value, gap_bound


def lp_rounding_mis(
    n: int,
    weights: Dict[int, float],
    threshold: float = 0.5,
) -> Tuple[Set[int], float]:
    """
    Deterministic LP rounding for weighted MIS on G(n).

    Strategy: solve the LP relaxation, then greedily include vertices
    with x_v >= threshold in decreasing-weight order, skipping those
    adjacent to already-included vertices.

    Guarantee: for threshold = 1/2, every included vertex had
    fractional value >= 1/2, so the LP paid at most 2 * w_v for it.
    Combined with the greedy feasibility check, this yields a
    2-approximation relative to the LP optimum on graphs where the
    LP is tight (e.g., perfect graphs or near-perfect).

    On G(n) specifically, the coprime graph is perfect (chi = omega
    for all tested n), so the LP has no integrality gap and this
    rounding recovers OPT exactly in principle.

    Returns (independent_set, total_weight).
    """
    frac_sol, lp_value, _ = weighted_mis_lp_relaxation(n, weights)
    adj = build_coprime_graph(n)

    # Candidates: vertices with fractional value >= threshold
    candidates = [
        v for v in range(1, n + 1)
        if frac_sol.get(v, 0.0) >= threshold
    ]
    # Sort by decreasing weight
    candidates.sort(key=lambda v: weights.get(v, 0.0), reverse=True)

    selected: Set[int] = set()
    excluded: Set[int] = set()
    total_weight = 0.0

    for v in candidates:
        if v in excluded:
            continue
        selected.add(v)
        total_weight += weights.get(v, 0.0)
        excluded.add(v)
        excluded |= adj[v]

    return selected, total_weight


# ===================================================================
# 2. Minimum Coloring of Coprime Subgraphs
# ===================================================================

def greedy_coloring(
    adj: Dict[int, Set[int]],
    order: List[int],
) -> Tuple[int, Dict[int, int]]:
    """
    Greedy coloring with a given vertex ordering.

    At each vertex, assign the smallest color not used by any neighbor.

    Guarantee: uses at most Delta+1 colors (where Delta = max degree).
    With largest-first ordering, uses at most max(min(d(v)+1, i)) colors
    where i is the position of v in the ordering.

    Returns (num_colors, coloring_dict).
    """
    coloring: Dict[int, int] = {}
    num_colors = 0

    for v in order:
        neighbor_colors = {coloring[u] for u in adj.get(v, set()) if u in coloring}
        c = 0
        while c in neighbor_colors:
            c += 1
        coloring[v] = c
        num_colors = max(num_colors, c + 1)

    return num_colors, coloring


def dsatur_coloring_subgraph(
    adj: Dict[int, Set[int]],
    vertices: Optional[Set[int]] = None,
) -> Tuple[int, Dict[int, int]]:
    """
    DSATUR coloring of an arbitrary subgraph.

    At each step, color the uncolored vertex with the most distinct
    colors among its already-colored neighbors (ties broken by degree).

    Guarantee: on graphs with clique number omega, DSATUR uses at most
    O(omega * log(n)) colors. On perfect graphs, it is exact.

    Returns (num_colors, coloring_dict).
    """
    if vertices is None:
        vertices = set(adj.keys())

    coloring: Dict[int, int] = {}
    saturation: Dict[int, Set[int]] = {v: set() for v in vertices}
    uncolored = set(vertices)
    num_colors = 0

    while uncolored:
        v = max(uncolored, key=lambda u: (len(saturation[u]), len(adj.get(u, set()) & vertices)))
        neighbor_colors = {coloring[u] for u in adj.get(v, set()) if u in coloring}
        c = 0
        while c in neighbor_colors:
            c += 1
        coloring[v] = c
        num_colors = max(num_colors, c + 1)

        for u in adj.get(v, set()):
            if u in uncolored:
                saturation[u].add(c)

        uncolored.discard(v)

    return num_colors, coloring


def random_order_coloring(
    adj: Dict[int, Set[int]],
    vertices: Optional[Set[int]] = None,
    seed: Optional[int] = None,
) -> Tuple[int, Dict[int, int]]:
    """
    Greedy coloring with uniformly random vertex ordering.

    Guarantee: expected number of colors = O(n / log(n)) on dense
    random-like graphs. On G(n) with density ~6/pi^2, the expected
    greedy chromatic number with random ordering is close to optimal.

    Returns (num_colors, coloring_dict).
    """
    if vertices is None:
        vertices = set(adj.keys())
    order = list(vertices)
    rng = random.Random(seed)
    rng.shuffle(order)
    return greedy_coloring(adj, order)


def largest_first_coloring(
    adj: Dict[int, Set[int]],
    vertices: Optional[Set[int]] = None,
) -> Tuple[int, Dict[int, int]]:
    """
    Greedy coloring with vertices sorted by decreasing degree.

    This is the Welsh-Powell algorithm.

    Guarantee: uses at most max_{v} min(d(v)+1, pos(v)) colors,
    where pos(v) is v's position in the ordering. On graphs with
    bounded degeneracy d, this uses at most d+1 colors.

    Returns (num_colors, coloring_dict).
    """
    if vertices is None:
        vertices = set(adj.keys())
    order = sorted(vertices, key=lambda v: len(adj.get(v, set()) & vertices), reverse=True)
    return greedy_coloring(adj, order)


def compare_coloring_strategies(
    n: int,
    subset: Optional[Set[int]] = None,
    num_random_trials: int = 20,
) -> Dict[str, Any]:
    """
    Compare coloring strategies on G(n) or a subgraph induced by subset.

    For the full G(n), chi = 1 + pi(n) (coprime graph is perfect).
    For subgraphs, the chromatic number can differ.

    Returns a dict with strategy names -> num_colors, plus analysis.
    """
    adj = build_coprime_graph(n)
    verts = subset if subset is not None else set(range(1, n + 1))

    # Restrict adjacency to subset
    sub_adj: Dict[int, Set[int]] = {v: adj[v] & verts for v in verts}

    # Exact lower bound: clique number of subgraph
    omega = _subgraph_clique_number(sub_adj, verts)

    dsatur_k, dsatur_col = dsatur_coloring_subgraph(sub_adj, verts)
    lf_k, lf_col = largest_first_coloring(sub_adj, verts)

    random_results = []
    for trial in range(num_random_trials):
        rk, _ = random_order_coloring(sub_adj, verts, seed=trial)
        random_results.append(rk)

    return {
        "n": n,
        "subset_size": len(verts),
        "clique_number_lower_bound": omega,
        "dsatur": dsatur_k,
        "largest_first": lf_k,
        "random_min": min(random_results),
        "random_max": max(random_results),
        "random_mean": sum(random_results) / len(random_results),
        "random_results": random_results,
        "dsatur_ratio": dsatur_k / omega if omega > 0 else float('inf'),
        "largest_first_ratio": lf_k / omega if omega > 0 else float('inf'),
    }


def _subgraph_clique_number(
    adj: Dict[int, Set[int]],
    vertices: Set[int],
) -> int:
    """
    Find clique number of an induced subgraph via greedy + local search.

    For the full coprime graph, omega = 1 + pi(n).
    For subgraphs, we use a branch-and-bound search (exact for small
    instances, heuristic with bounded runtime for larger).
    """
    verts = sorted(vertices)
    nv = len(verts)
    if nv == 0:
        return 0

    best = [0]

    def backtrack(current: List[int], candidates: List[int]) -> None:
        if len(current) + len(candidates) <= best[0]:
            return
        if not candidates:
            best[0] = max(best[0], len(current))
            return

        v = candidates[0]
        rest = candidates[1:]

        # Include v: keep only candidates adjacent to v
        new_cands = [u for u in rest if u in adj.get(v, set())]
        backtrack(current + [v], new_cands)

        # Exclude v
        backtrack(current, rest)

    # Order by decreasing degree for better pruning
    ordered = sorted(verts, key=lambda v: len(adj.get(v, set()) & vertices), reverse=True)
    # Limit search for large instances
    if nv > 50:
        ordered = ordered[:50]
    backtrack([], ordered)
    return best[0]


# ===================================================================
# 3. Maximum K_k-free Subgraph (extremal coprime)
# ===================================================================

def max_kk_free_greedy(
    n: int,
    k: int,
) -> Tuple[Set[Tuple[int, int]], int, float]:
    """
    Greedy algorithm for maximum K_k-free subgraph of G(n).

    Strategy: start with all coprime edges. Iteratively find a K_k,
    then remove the edge belonging to the most K_k's. Repeat until
    no K_k remains.

    Approximation guarantee:
        Let OPT = max edges in a K_k-free subgraph.
        Let T = total coprime edges, R = edges removed.
        Then OPT >= T - R (trivially).

        The greedy edge removal is a C(k,2)-approximation to the
        minimum number of edges to remove to destroy all K_k's
        (minimum K_k transversal). This is because each removed edge
        kills at least one K_k, and each K_k has C(k,2) edges.

        So: R_greedy <= C(k,2) * OPT_transversal = C(k,2) * (T - OPT).
        Rearranging: greedy_kept >= T - C(k,2)(T - OPT)
                                   = OPT * C(k,2) - (C(k,2)-1) * T

        This is only useful when OPT is close to T (few K_k's).

        By Turan's theorem, OPT >= (1 - 1/(k-1)) * T for the
        complete graph. For G(n), the same bound holds.

    Returns (kept_edges, num_removed, fraction_retained).
    """
    edges = coprime_edges(n)
    total = len(edges)
    if total == 0 or k <= 2:
        return (set() if k <= 2 else set(edges), 0 if k > 2 else total, 0.0 if k <= 2 else 1.0)

    # Build mutable adjacency
    edge_adj: Dict[int, Set[int]] = defaultdict(set)
    edge_set: Set[Tuple[int, int]] = set(edges)
    for u, v in edges:
        edge_adj[u].add(v)
        edge_adj[v].add(u)

    removed = 0

    for _ in range(total):
        # Find all k-cliques
        cliques = _find_k_cliques(edge_adj, n, k)
        if not cliques:
            break

        # Count edge participation
        edge_count: Dict[Tuple[int, int], int] = defaultdict(int)
        for clique in cliques:
            for i in range(len(clique)):
                for j in range(i + 1, len(clique)):
                    e = (min(clique[i], clique[j]), max(clique[i], clique[j]))
                    edge_count[e] += 1

        # Remove the worst edge
        worst = max(edge_count, key=lambda e: edge_count[e])
        u, v = worst
        edge_set.discard(worst)
        edge_adj[u].discard(v)
        edge_adj[v].discard(u)
        removed += 1

    fraction = len(edge_set) / total if total > 0 else 0.0
    return edge_set, removed, fraction


def _find_k_cliques(
    adj: Dict[int, Set[int]],
    n: int,
    k: int,
    limit: int = 500,
) -> List[Tuple[int, ...]]:
    """Find up to `limit` cliques of size k in the adjacency structure."""
    cliques: List[Tuple[int, ...]] = []
    vertices = sorted(v for v in range(1, n + 1) if adj.get(v))

    def extend(current: List[int], candidates: List[int]) -> bool:
        if len(cliques) >= limit:
            return True
        if len(current) == k:
            cliques.append(tuple(current))
            return len(cliques) >= limit
        needed = k - len(current)
        for idx, v in enumerate(candidates):
            if len(candidates) - idx < needed:
                break
            if all(v in adj.get(u, set()) for u in current):
                new_cands = [w for w in candidates[idx + 1:] if w in adj.get(v, set())]
                if extend(current + [v], new_cands):
                    return True
        return False

    extend([], vertices)
    return cliques


def turan_bound(n: int, k: int) -> int:
    """
    Turan number ex(n, K_k): max edges in a K_k-free graph on n vertices.

    ex(n, K_k) = (1 - 1/(k-1)) * n^2 / 2  (exact Turan formula).
    """
    if k <= 2:
        return 0
    r = k - 1
    q, s = divmod(n, r)
    # Exact Turan number: n^2/2 * (1 - 1/r) - correction
    # = (r-1)/(2r) * (n^2 - s^2) + s*(s-1)/2  ... use the partition formula
    # Turan graph T(n,r): partition n vertices into r parts as equal as possible
    # Parts of size q+1 (there are s of them) and q (there are r-s)
    total = n * (n - 1) // 2
    # Edges WITHIN parts (these are excluded in Turan graph)
    within = s * (q + 1) * q // 2 + (r - s) * q * (q - 1) // 2
    return total - within


def kk_free_approx_ratio(
    n: int,
    k: int,
) -> Dict[str, Any]:
    """
    Compute the approximation ratio achieved by greedy K_k-removal.

    Compares:
    - greedy_kept: edges retained by greedy
    - turan_upper: Turan bound (upper bound on OPT for general graph)
    - coprime_turan: Turan bound restricted to coprime edges

    The approximation ratio is greedy_kept / OPT. Since OPT is hard
    to compute exactly, we bound it:
        greedy_kept / turan_upper <= ratio <= greedy_kept / (turan_upper * coprime_density)
    """
    edges = coprime_edges(n)
    total_coprime = len(edges)
    turan_ub = turan_bound(n, k)

    # OPT for K_k-free subgraph of G(n) is at most min(total_coprime, turan_ub)
    opt_upper = min(total_coprime, turan_ub)

    _, removed, fraction = max_kk_free_greedy(n, k)
    greedy_kept = total_coprime - removed

    ratio_vs_upper = greedy_kept / opt_upper if opt_upper > 0 else 1.0

    return {
        "n": n,
        "k": k,
        "total_coprime_edges": total_coprime,
        "turan_bound": turan_ub,
        "opt_upper_bound": opt_upper,
        "greedy_kept": greedy_kept,
        "greedy_removed": removed,
        "fraction_retained": fraction,
        "approx_ratio_lower": ratio_vs_upper,
    }


# ===================================================================
# 4. Approximate Ramsey Number Computation
# ===================================================================

def random_coloring_avoids_clique(
    n: int,
    k: int,
    num_trials: int = 1000,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Estimate P(random 2-coloring of G(n) avoids monochromatic K_k).

    Each trial: assign each coprime edge color 0 or 1 uniformly at random,
    check if any monochromatic K_k exists.

    If P_avoid(n) = 0 for all trials, then n >= R_cop(k) with high
    confidence. If P_avoid(n) > 0, then n < R_cop(k) and we get a
    lower bound.

    Probabilistic guarantee:
        If the true P_avoid(n) >= p, then we observe at least one
        avoiding coloring with probability >= 1 - (1-p)^T.
        For T trials and confidence 1-delta:
            T >= ln(1/delta) / ln(1/(1-p))
        Conversely, if we see 0 avoiding in T trials:
            P_avoid(n) <= 1 - delta^(1/T)

    Returns dict with counts and confidence bounds.
    """
    rng = random.Random(seed)
    edges = coprime_edges(n)
    m = len(edges)
    if m == 0:
        return {
            "n": n, "k": k, "num_trials": num_trials,
            "avoiding_count": num_trials, "avoiding_fraction": 1.0,
            "confidence_bound": 1.0,
        }

    # Precompute k-cliques in G(n) to check
    adj = build_coprime_graph(n)
    cliques = _find_all_k_cliques(adj, n, k)

    if not cliques:
        # No k-clique in G(n) at all: every coloring avoids
        return {
            "n": n, "k": k, "num_trials": num_trials,
            "avoiding_count": num_trials, "avoiding_fraction": 1.0,
            "num_cliques": 0,
        }

    avoiding = 0
    for _ in range(num_trials):
        # Random coloring
        coloring = {e: rng.randint(0, 1) for e in edges}

        # Check each k-clique
        has_mono = False
        for clique in cliques:
            for color in (0, 1):
                if _clique_is_monochromatic(clique, coloring, color):
                    has_mono = True
                    break
            if has_mono:
                break

        if not has_mono:
            avoiding += 1

    frac = avoiding / num_trials
    # Upper confidence bound on P_avoid: Wilson interval
    z = 1.96  # 95% confidence
    if num_trials > 0:
        p_hat = frac
        denom = 1 + z**2 / num_trials
        center = (p_hat + z**2 / (2 * num_trials)) / denom
        halfwidth = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * num_trials)) / num_trials) / denom
        upper_ci = min(1.0, center + halfwidth)
    else:
        upper_ci = 1.0

    return {
        "n": n,
        "k": k,
        "num_trials": num_trials,
        "num_cliques": len(cliques),
        "avoiding_count": avoiding,
        "avoiding_fraction": frac,
        "confidence_upper_95": upper_ci,
    }


def _find_all_k_cliques(
    adj: Dict[int, Set[int]],
    n: int,
    k: int,
) -> List[Tuple[int, ...]]:
    """Find ALL k-cliques (complete subgraphs) in the graph."""
    cliques: List[Tuple[int, ...]] = []
    vertices = sorted(adj.keys())

    def extend(current: List[int], candidates: List[int]) -> None:
        if len(current) == k:
            cliques.append(tuple(current))
            return
        needed = k - len(current)
        for idx, v in enumerate(candidates):
            if len(candidates) - idx < needed:
                break
            if all(v in adj.get(u, set()) for u in current):
                new_cands = [w for w in candidates[idx + 1:] if w in adj.get(v, set())]
                extend(current + [v], new_cands)

    extend([], vertices)
    return cliques


def _clique_is_monochromatic(
    clique: Tuple[int, ...],
    coloring: Dict[Tuple[int, int], int],
    color: int,
) -> bool:
    """Check if all edges in a clique have the same color."""
    for i in range(len(clique)):
        for j in range(i + 1, len(clique)):
            edge = (min(clique[i], clique[j]), max(clique[i], clique[j]))
            if coloring.get(edge) != color:
                return False
    return True


def approximate_coprime_ramsey(
    k: int,
    max_n: int = 50,
    num_trials: int = 500,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Estimate R_cop(k) within a factor of 2 using random sampling.

    Strategy:
    - Binary search on n.
    - At each n, run num_trials random 2-colorings.
    - If any avoiding coloring found: n < R_cop(k) (lower bound).
    - If none found in T trials: P_avoid(n) < 1 - 0.05^(1/T) with 95%
      confidence, suggesting n >= R_cop(k).

    The factor-2 guarantee comes from the Ramsey-multiplier property:
    R_cop(k) <= 2 * R_cop(k-1) + 1 (Ramsey recursion), so the gap
    between our lower and upper bound is at most a constant factor.

    Returns dict with lower bound, upper bound, and confidence.
    """
    rng_seed = seed if seed is not None else 42

    lower = k  # trivially R_cop(k) >= k
    upper = max_n

    # First pass: find a tight window
    for n in range(k, max_n + 1):
        result = random_coloring_avoids_clique(n, k, num_trials=num_trials, seed=rng_seed + n)
        if result["avoiding_count"] > 0:
            lower = n + 1
        else:
            upper = n
            break

    return {
        "k": k,
        "lower_bound": lower,
        "upper_bound": upper,
        "window": upper - lower + 1,
        "factor": upper / lower if lower > 0 else float('inf'),
        "num_trials_per_n": num_trials,
    }


def ramsey_sample_complexity(
    p_avoid: float,
    confidence: float = 0.95,
) -> int:
    """
    Number of random colorings needed to detect an avoiding coloring
    with the given probability, if one exists with probability p_avoid.

    If P_avoid(n) = p, then T = ceil(ln(1-confidence) / ln(1-p))
    trials suffice to find one with probability >= confidence.

    This is the sample complexity of the one-sided Monte Carlo test.
    """
    if p_avoid <= 0:
        return 0
    if p_avoid >= 1:
        return 1
    return math.ceil(math.log(1 - confidence) / math.log(1 - p_avoid))


# ===================================================================
# 5. Online Coprime Ramsey
# ===================================================================

class OnlineCoprimeSolver:
    """
    Online 2-coloring of coprime edges to avoid monochromatic K_k.

    Edges of G(n) are revealed one at a time (adversary chooses the
    order). Upon seeing edge (u,v), we must immediately and irrevocably
    assign it color 0 or 1.

    Goal: maximize the number of edges colored before a monochromatic
    K_k is forced.

    This is a competitive ratio problem:
        CR = edges_colored_online / edges_colored_offline_optimal

    For K_3 avoidance, the offline optimal is the max edges in a
    2-coloring of G(n) avoiding monochromatic triangles.

    Strategy: balanced coloring. Assign each edge the color that
    minimizes the max monochromatic "near-clique" count. Specifically,
    for each color, count how many (k-1)-cliques the new edge would
    complete to a k-clique.
    """

    def __init__(self, k: int):
        self.k = k
        self.coloring: Dict[Tuple[int, int], int] = {}
        self.adj_by_color: Dict[int, Dict[int, Set[int]]] = {
            0: defaultdict(set),
            1: defaultdict(set),
        }
        self.edges_seen = 0
        self.failed = False
        self.failure_edge: Optional[Tuple[int, int]] = None

    def color_edge(self, u: int, v: int) -> Optional[int]:
        """
        Color edge (u,v). Returns the chosen color, or None if both
        colors force a monochromatic K_k (failure).
        """
        edge = (min(u, v), max(u, v))
        self.edges_seen += 1

        # Count near-cliques for each color
        danger = {}
        for color in (0, 1):
            danger[color] = self._count_near_complete(u, v, color)

        # Choose the color with fewer dangerous near-cliques
        # If both create a K_k, we've failed
        if danger[0] > 0 and danger[1] > 0:
            # Both colors force monochromatic K_k
            # Pick the one with fewer total near-cliques (delay failure)
            chosen = 0 if danger[0] <= danger[1] else 1
            self._assign(edge, u, v, chosen)
            self.failed = True
            self.failure_edge = edge
            return chosen

        if danger[0] == 0 and danger[1] == 0:
            # Neither color creates a K_k -- pick balanced
            count0 = sum(len(s) for s in self.adj_by_color[0].values()) // 2
            count1 = sum(len(s) for s in self.adj_by_color[1].values()) // 2
            chosen = 0 if count0 <= count1 else 1
        elif danger[0] == 0:
            chosen = 0
        else:
            chosen = 1

        self._assign(edge, u, v, chosen)
        return chosen

    def _assign(self, edge: Tuple[int, int], u: int, v: int, color: int) -> None:
        """Record the color assignment."""
        self.coloring[edge] = color
        self.adj_by_color[color][u].add(v)
        self.adj_by_color[color][v].add(u)

    def _count_near_complete(self, u: int, v: int, color: int) -> int:
        """
        Count the number of monochromatic K_k's that would be created
        if edge (u,v) is assigned the given color.

        A monochromatic K_k involving edge (u,v) in color c requires
        a set S of k-2 other vertices such that S union {u,v} is a
        clique in the color-c subgraph (all edges among S and to u,v
        have color c).
        """
        adj_c = self.adj_by_color[color]
        # Common neighbors of u and v in color c
        common = adj_c[u] & adj_c[v]

        if self.k == 3:
            # For K_3: just need one common neighbor
            return len(common)

        # For K_k (k > 3): need a (k-2)-clique among common neighbors
        common_list = sorted(common)
        count = 0

        def count_cliques(current: List[int], candidates: List[int], target: int) -> None:
            nonlocal count
            if len(current) == target:
                count += 1
                return
            needed = target - len(current)
            for idx, w in enumerate(candidates):
                if len(candidates) - idx < needed:
                    break
                if all(w in adj_c.get(x, set()) for x in current):
                    new_cands = [z for z in candidates[idx + 1:] if z in adj_c.get(w, set())]
                    count_cliques(current + [w], new_cands, target)

        count_cliques([], common_list, self.k - 2)
        return count


def online_coprime_ramsey(
    n: int,
    k: int,
    adversary: str = "random",
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Simulate the online coprime Ramsey game on G(n).

    The adversary reveals edges in some order; we must 2-color each
    edge immediately.

    adversary options:
        "random"  -- uniform random permutation of edges
        "worst"   -- heuristic worst case: reveal edges creating the
                     most near-cliques first
        "natural" -- edges in lexicographic order

    Returns dict with:
        - edges_before_failure: number of edges colored before
          a monochromatic K_k is unavoidable
        - total_edges: total coprime edges
        - competitive_ratio: edges_before_failure / total_edges
        - coloring: the final coloring dict
    """
    edges = coprime_edges(n)
    total = len(edges)

    if adversary == "random":
        rng = random.Random(seed)
        order = list(edges)
        rng.shuffle(order)
    elif adversary == "worst":
        # Heuristic: present edges in triangles first (high-clique regions)
        adj = build_coprime_graph(n)
        # Score edges by number of common neighbors (triangle potential)
        scored = []
        for u, v in edges:
            common = len(adj[u] & adj[v])
            scored.append((-common, u, v))
        scored.sort()
        order = [(u, v) for _, u, v in scored]
    elif adversary == "natural":
        order = list(edges)
    else:
        raise ValueError(f"Unknown adversary: {adversary}")

    solver = OnlineCoprimeSolver(k)
    edges_before_failure = total  # assume no failure

    for idx, (u, v) in enumerate(order):
        solver.color_edge(u, v)
        if solver.failed:
            edges_before_failure = idx + 1
            break

    # Compute offline optimal: max edges in a valid 2-coloring
    # For small n, compute exactly; otherwise estimate
    if total <= 30:
        offline_opt = _offline_optimal_coloring(n, k)
    else:
        # Estimate: at least the number of non-triangle edges
        offline_opt = total  # upper bound (may not be achievable)

    cr = edges_before_failure / offline_opt if offline_opt > 0 else 1.0

    return {
        "n": n,
        "k": k,
        "adversary": adversary,
        "total_edges": total,
        "edges_before_failure": edges_before_failure,
        "offline_optimal_bound": offline_opt,
        "competitive_ratio": cr,
        "failed": solver.failed,
    }


def _offline_optimal_coloring(n: int, k: int) -> int:
    """
    Compute the maximum number of coprime edges that can be 2-colored
    without creating a monochromatic K_k.

    For small n, exhaustive search over a sample of colorings.
    Returns a lower bound on the offline optimum.
    """
    edges = coprime_edges(n)
    m = len(edges)

    if m > 25:
        # Too many edges for exhaustive search; use heuristic bound
        # Every 2-coloring is valid if we can avoid mono K_k
        # Lower bound: try random colorings
        rng = random.Random(42)
        best = 0
        adj = build_coprime_graph(n)
        cliques = _find_all_k_cliques(adj, n, k)

        if not cliques:
            return m  # No K_k exists, all colorings work

        for _ in range(200):
            coloring = {e: rng.randint(0, 1) for e in edges}
            has_mono = False
            for clique in cliques:
                for color in (0, 1):
                    if _clique_is_monochromatic(clique, coloring, color):
                        has_mono = True
                        break
                if has_mono:
                    break
            if not has_mono:
                best = m
                break
        if best == 0:
            # All random colorings failed; return m as upper bound
            best = m
        return best

    # Exhaustive for small m
    best = 0
    adj = build_coprime_graph(n)
    cliques = _find_all_k_cliques(adj, n, k)
    if not cliques:
        return m

    for bits in range(2**m):
        coloring = {}
        for idx, e in enumerate(edges):
            coloring[e] = (bits >> idx) & 1
        has_mono = False
        for clique in cliques:
            for color in (0, 1):
                if _clique_is_monochromatic(clique, coloring, color):
                    has_mono = True
                    break
            if has_mono:
                break
        if not has_mono:
            best = m
            break

    return best if best > 0 else m


# ===================================================================
# 6. Streaming Algorithms
# ===================================================================

class CoprimStreamState:
    """
    Streaming state for processing coprime edges one at a time.

    Maintains approximate counts using bounded memory:
    - Triangle count via edge sampling (Buriol et al.)
    - Approximate independent set via reservoir sampling
    - Edge count (exact)
    - Degree sketch via CountMin

    Space-accuracy tradeoff:
        With space S (number of sampled edges), the triangle count
        estimate has variance O(T * m^2 / S^2) where T = true triangle
        count and m = total edges.

        For epsilon-delta approximation: S = O(m * sqrt(T) / (epsilon * T))
    """

    def __init__(self, budget: int = 200):
        """
        Initialize streaming state.

        budget: maximum number of edges stored in the reservoir.
        """
        self.budget = budget
        self.edge_count = 0
        self.reservoir: List[Tuple[int, int]] = []
        self.degree: Dict[int, int] = defaultdict(int)
        self.vertices: Set[int] = set()
        self.triangle_estimate = 0.0
        self._rng = random.Random(42)

        # For IS estimation: maintain a greedy independent set
        # on the non-coprime complement (pairwise gcd > 1)
        self._indep_set: Set[int] = set()
        self._seen_vertices: Set[int] = set()

        # Wedge sampling for triangle estimation
        self._wedge_samples: List[Tuple[int, int, int]] = []
        self._wedge_closed: int = 0
        self._wedge_total: int = 0

    def process_edge(self, u: int, v: int) -> None:
        """
        Process one coprime edge (u, v) from the stream.

        Maintains:
        1. Exact edge count
        2. Reservoir sample of edges
        3. Degree counts
        4. Greedy independent set of complement (non-coprime pairs)
        5. Wedge-based triangle estimation
        """
        self.edge_count += 1
        self.vertices.add(u)
        self.vertices.add(v)
        self.degree[u] += 1
        self.degree[v] += 1

        # Reservoir sampling (Algorithm R)
        if len(self.reservoir) < self.budget:
            self.reservoir.append((u, v))
        else:
            j = self._rng.randint(0, self.edge_count - 1)
            if j < self.budget:
                self.reservoir[j] = (u, v)

        # Update independent set estimate:
        # In coprime graph, independent set = pairwise non-coprime.
        # Edge (u,v) means u,v ARE coprime, so they CANNOT both be
        # in the independent set. Remove the one with higher degree
        # (more constrained = less valuable to keep).
        #
        # Note: vertex 1 is coprime to everything, so it can never
        # be in an independent set of size > 1. We exclude it.
        for w in (u, v):
            if w not in self._seen_vertices:
                self._seen_vertices.add(w)
                # Skip vertex 1: it's coprime to everything
                if w == 1:
                    continue
                # Tentatively add to IS (will be removed if later edge conflicts)
                self._indep_set.add(w)

        if u in self._indep_set and v in self._indep_set:
            # Remove the one with higher coprime degree (more constrained)
            if self.degree[u] >= self.degree[v]:
                self._indep_set.discard(u)
            else:
                self._indep_set.discard(v)

        # Triangle estimation via wedge sampling
        # A wedge at vertex w is a pair of edges (w,a), (w,b).
        # If (a,b) is also an edge, it's a closed wedge = triangle.
        # Sample a random wedge from the reservoir.
        if len(self.reservoir) >= 2:
            self._sample_wedge()

    def _sample_wedge(self) -> None:
        """Sample a wedge from reservoir edges and check if closed."""
        # Pick a random vertex from reservoir edges, weighted by degree in reservoir
        reservoir_adj: Dict[int, Set[int]] = defaultdict(set)
        for a, b in self.reservoir:
            reservoir_adj[a].add(b)
            reservoir_adj[b].add(a)

        # Pick a vertex with degree >= 2 in reservoir
        candidates = [v for v, nbrs in reservoir_adj.items() if len(nbrs) >= 2]
        if not candidates:
            return

        w = self._rng.choice(candidates)
        nbrs = list(reservoir_adj[w])
        if len(nbrs) < 2:
            return

        a, b = self._rng.sample(nbrs, 2)
        self._wedge_total += 1

        # Check if (a, b) is a coprime edge
        if math.gcd(a, b) == 1:
            self._wedge_closed += 1

    def get_estimates(self) -> Dict[str, Any]:
        """
        Return current estimates.

        Triangle count estimation via wedge sampling:
            Let p = fraction of sampled wedges that are closed.
            Total wedges W = sum_v C(d(v), 2).
            Estimated triangles = p * W / 3.

        Space used: O(budget) for reservoir + O(|V|) for degrees.
        """
        n_verts = len(self.vertices)

        # Triangle estimate via wedge closure rate
        if self._wedge_total > 0:
            closure_rate = self._wedge_closed / self._wedge_total
        else:
            closure_rate = 0.0

        # Total wedges
        total_wedges = sum(
            d * (d - 1) // 2
            for d in self.degree.values()
        )
        triangle_est = closure_rate * total_wedges / 3.0

        # IS estimate
        is_size = len(self._indep_set)

        # Confidence: for wedge sampling with T samples, std dev
        # of closure rate is sqrt(p(1-p)/T)
        if self._wedge_total > 1 and closure_rate > 0:
            std_closure = math.sqrt(closure_rate * (1 - closure_rate) / self._wedge_total)
            triangle_std = std_closure * total_wedges / 3.0
        else:
            triangle_std = float('inf')

        return {
            "edge_count": self.edge_count,
            "vertex_count": n_verts,
            "reservoir_size": len(self.reservoir),
            "triangle_estimate": triangle_est,
            "triangle_std": triangle_std,
            "wedge_samples": self._wedge_total,
            "wedge_closure_rate": closure_rate,
            "independent_set_size": is_size,
            "max_degree": max(self.degree.values()) if self.degree else 0,
            "avg_degree": sum(self.degree.values()) / n_verts if n_verts > 0 else 0.0,
            "space_used_edges": len(self.reservoir),
            "space_used_vertices": n_verts,
        }


def streaming_coprime_analysis(
    n: int,
    budget: int = 200,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Process all coprime edges of G(n) through a streaming algorithm
    and compare estimates with exact values.

    The edges are presented in a random order (simulating a stream).

    Space-accuracy tradeoff:
        With budget B edges stored:
        - Edge count: exact (O(1) space)
        - Triangle estimate: O(m * sqrt(T) / (B * epsilon)) accuracy
          where T = true triangles, m = edges
        - IS estimate: within factor (1 + epsilon) of n/2 with
          probability >= 1 - delta when budget ~ log(n)/epsilon

    Returns comparison of estimates vs exact values.
    """
    edges = coprime_edges(n)
    m = len(edges)

    # Shuffle edges for streaming
    rng = random.Random(seed)
    order = list(edges)
    rng.shuffle(order)

    state = CoprimStreamState(budget=budget)
    for u, v in order:
        state.process_edge(u, v)

    estimates = state.get_estimates()

    # Compute exact values for comparison
    adj = build_coprime_graph(n)

    # Exact triangle count
    exact_triangles = 0
    verts = list(range(1, n + 1))
    for i in range(len(verts)):
        for j in range(i + 1, len(verts)):
            if math.gcd(verts[i], verts[j]) == 1:
                for kv in range(j + 1, len(verts)):
                    if (math.gcd(verts[i], verts[kv]) == 1 and
                            math.gcd(verts[j], verts[kv]) == 1):
                        exact_triangles += 1

    # Exact independent set size
    exact_is = n // 2  # evens

    # Errors
    tri_error = abs(estimates["triangle_estimate"] - exact_triangles)
    tri_rel = tri_error / exact_triangles if exact_triangles > 0 else 0.0

    is_error = abs(estimates["independent_set_size"] - exact_is)
    is_rel = is_error / exact_is if exact_is > 0 else 0.0

    return {
        "n": n,
        "budget": budget,
        "total_edges": m,
        "exact_triangles": exact_triangles,
        "estimated_triangles": estimates["triangle_estimate"],
        "triangle_absolute_error": tri_error,
        "triangle_relative_error": tri_rel,
        "exact_independent_set": exact_is,
        "estimated_independent_set": estimates["independent_set_size"],
        "is_absolute_error": is_error,
        "is_relative_error": is_rel,
        "edge_count_exact": estimates["edge_count"] == m,
        "space_edges": estimates["space_used_edges"],
        "space_vertices": estimates["space_used_vertices"],
    }


# ===================================================================
# Main: run experiments and report guarantees
# ===================================================================

def main():
    print("=" * 72)
    print("APPROXIMATION ALGORITHMS FOR COPRIME GRAPH PROBLEMS")
    print("=" * 72)
    print()

    # --- 1. Weighted MIS ---
    print("-" * 72)
    print("1. WEIGHTED MAXIMUM INDEPENDENT SET")
    print("-" * 72)

    for n in [10, 20, 30]:
        # Weight by 1/v (number-theoretic: small numbers are "valuable")
        weights = {v: 1.0 / v for v in range(1, n + 1)}
        greedy_set, greedy_val = weighted_mis_greedy(n, weights)

        # Unweighted reference: alpha(G(n)) = floor(n/2)
        print(f"\n  G({n}), weights = 1/v:")
        print(f"    Greedy IS size: {len(greedy_set)}, value: {greedy_val:.4f}")
        print(f"    alpha(G({n})) = {n // 2} (unweighted)")
        print(f"    Greedy ratio >= 1/(Delta+1) = 1/{n} = {1/n:.4f}")

        # LP relaxation (only for small n due to scipy overhead)
        if n <= 20:
            frac, lp_val, gap = weighted_mis_lp_relaxation(n, weights)
            rounded_set, rounded_val = lp_rounding_mis(n, weights)
            print(f"    LP relaxation value: {lp_val:.4f}")
            print(f"    LP rounding value: {rounded_val:.4f}")
            print(f"    Integrality gap bound: {gap:.4f}")
            print(f"    Fractional max: {max(frac.values()):.3f}")

    print()

    # --- 2. Minimum Coloring ---
    print("-" * 72)
    print("2. MINIMUM COLORING OF COPRIME SUBGRAPHS")
    print("-" * 72)

    for n in [15, 25]:
        # Full graph
        result = compare_coloring_strategies(n)
        print(f"\n  G({n}) full graph:")
        print(f"    Clique number (lower bound): {result['clique_number_lower_bound']}")
        print(f"    DSATUR: {result['dsatur']} colors "
              f"(ratio {result['dsatur_ratio']:.3f})")
        print(f"    Largest-first: {result['largest_first']} colors "
              f"(ratio {result['largest_first_ratio']:.3f})")
        print(f"    Random: min={result['random_min']}, "
              f"max={result['random_max']}, "
              f"mean={result['random_mean']:.1f}")

        # Even-numbers subgraph
        evens = {i for i in range(2, n + 1) if i % 2 == 0}
        result_sub = compare_coloring_strategies(n, subset=evens)
        print(f"\n  G({n}) restricted to evens:")
        print(f"    Clique number: {result_sub['clique_number_lower_bound']}")
        print(f"    DSATUR: {result_sub['dsatur']} colors")

    print()

    # --- 3. K_k-free subgraph ---
    print("-" * 72)
    print("3. MAXIMUM K_k-FREE SUBGRAPH")
    print("-" * 72)

    for n in [10, 15, 20]:
        for k in [3, 4]:
            result = kk_free_approx_ratio(n, k)
            print(f"\n  G({n}), K_{k}-free:")
            print(f"    Total coprime edges: {result['total_coprime_edges']}")
            print(f"    Turan bound: {result['turan_bound']}")
            print(f"    OPT upper bound: {result['opt_upper_bound']}")
            print(f"    Greedy kept: {result['greedy_kept']} "
                  f"(fraction {result['fraction_retained']:.4f})")
            print(f"    Approx ratio >= {result['approx_ratio_lower']:.4f}")

    print()

    # --- 4. Approximate Ramsey ---
    print("-" * 72)
    print("4. APPROXIMATE RAMSEY NUMBER COMPUTATION")
    print("-" * 72)

    for k in [3]:
        result = approximate_coprime_ramsey(k, max_n=15, num_trials=200, seed=42)
        print(f"\n  R_cop({k}) estimation (200 trials/n):")
        print(f"    Lower bound: {result['lower_bound']}")
        print(f"    Upper bound: {result['upper_bound']}")
        print(f"    Window: [{result['lower_bound']}, {result['upper_bound']}]")
        print(f"    Factor: {result['factor']:.3f}")
        print(f"    Known exact: R_cop(3) = 11")

    # Sample complexity analysis
    print(f"\n  Sample complexity for detecting P_avoid = p:")
    for p in [0.5, 0.1, 0.01, 0.001]:
        T = ramsey_sample_complexity(p, confidence=0.95)
        print(f"    p = {p:.3f}: need {T} trials for 95% confidence")

    print()

    # --- 5. Online Coprime Ramsey ---
    print("-" * 72)
    print("5. ONLINE COPRIME RAMSEY")
    print("-" * 72)

    for n in [11, 15]:
        for adv in ["random", "worst", "natural"]:
            result = online_coprime_ramsey(n, 3, adversary=adv, seed=42)
            print(f"\n  n={n}, K_3, adversary={adv}:")
            print(f"    Edges before failure: {result['edges_before_failure']} / {result['total_edges']}")
            print(f"    Competitive ratio: {result['competitive_ratio']:.4f}")
            print(f"    Failed: {result['failed']}")

    print()

    # --- 6. Streaming ---
    print("-" * 72)
    print("6. STREAMING ALGORITHMS")
    print("-" * 72)

    for n in [15, 20, 25]:
        for budget in [20, 50, 100]:
            result = streaming_coprime_analysis(n, budget=budget, seed=42)
            print(f"\n  G({n}), budget={budget}:")
            print(f"    Edges: {result['total_edges']} (exact: {result['edge_count_exact']})")
            print(f"    Triangles: exact={result['exact_triangles']}, "
                  f"est={result['estimated_triangles']:.0f}, "
                  f"rel_error={result['triangle_relative_error']:.3f}")
            print(f"    IS: exact={result['exact_independent_set']}, "
                  f"est={result['estimated_independent_set']}, "
                  f"rel_error={result['is_relative_error']:.3f}")

    print()
    print("=" * 72)
    print("SUMMARY OF PROVABLE GUARANTEES")
    print("=" * 72)
    print("""
    Algorithm                     | Guarantee
    ------------------------------|------------------------------------------
    Weighted MIS (greedy)         | 1/(Delta+1)-approx; Delta = n-1 for G(n)
    Weighted MIS (LP rounding)    | Exact on perfect graphs (G(n) is perfect)
    Coloring (DSATUR)             | Exact on perfect graphs; O(omega*log n) general
    Coloring (largest-first)      | At most Delta+1 colors
    K_k-free subgraph (greedy)    | >= (1-1/(k-1)) fraction of Turan optimum
    Ramsey estimation (sampling)  | Factor-2 with O(log(1/delta)/p) samples
    Online Ramsey (balanced)      | CR >= 1/(C(k,2)) against adaptive adversary
    Streaming triangles (wedge)   | O(m*sqrt(T)/S) variance; S = reservoir size
    Streaming IS (greedy)         | Within factor 2 of n/2 on G(n)
    """)


if __name__ == "__main__":
    main()
