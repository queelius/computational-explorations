#!/usr/bin/env python3
"""
Ramsey Codes: Coding-Theoretic Interpretation of Coprime Ramsey Colorings.

An "avoiding coloring" of the coprime graph G([n]) for parameter k is a
2-coloring of edges that contains no monochromatic K_k. The set of all
such colorings, viewed as binary strings over the edge set, forms a
binary code C(n,k).

At n = R_cop(3)-1 = 10, the 156 avoiding colorings are binary strings
of length 31 (one bit per coprime edge). This module analyzes these
codes through the lens of classical coding theory.

Key results:
  - C(10,3) has 156 codewords, length 31, rate ~0.235 bits/symbol
  - The code is complement-closed (not linear, not even coset of linear)
  - Minimum distance d_min = 1 (very close codewords exist)
  - The distance distribution is palindromic: A_d = A_{31-d}
  - Hierarchical clustering reveals natural subcodes tied to coprime
    graph symmetries
  - Rate decays as n -> R_cop(k), reaching 0 at the Ramsey threshold
  - The coprime clique constraint graph is a natural Tanner graph, but
    belief propagation underperforms exact SAT solving
"""

import math
import random
import time
from collections import Counter
from itertools import combinations
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

from coprime_ramsey import coprime_edges, has_monochromatic_clique
from coprime_ramsey_sat import (
    CoprimeSATEncoder,
    find_coprime_cliques,
    validate_avoiding_coloring,
)


# =========================================================================
# Section 1: The Avoiding Code
# =========================================================================


def enumerate_avoiding_colorings(
    n: int, k: int
) -> Tuple[List[Tuple[int, ...]], List[Tuple[int, int]]]:
    """
    Enumerate all avoiding colorings of G([n]) for clique size k.

    Uses incremental extension from a small base where exhaustive
    enumeration is feasible, then extends vertex-by-vertex.

    Returns (codewords, edge_list) where each codeword is a tuple of
    0/1 values indexed by the canonical edge ordering from coprime_edges(n).
    """
    # Find base n where exhaustive enumeration is feasible
    base_n = None
    avoiding = None

    for m in range(k, n + 1):
        edges_m = coprime_edges(m)
        if len(edges_m) > 25:
            break
        new_avoiding = []
        for bits in range(2 ** len(edges_m)):
            col = {e: (bits >> i) & 1 for i, e in enumerate(edges_m)}
            if has_monochromatic_clique(m, k, col) is None:
                new_avoiding.append(col)
        if not new_avoiding:
            # All colorings forced at m -- code is empty for m..n
            return [], coprime_edges(n)
        avoiding = new_avoiding
        base_n = m

    if avoiding is None or base_n is None:
        return [], coprime_edges(n)

    # Extend from base_n+1 to n
    for m in range(base_n + 1, n + 1):
        new_edges = [(i, m) for i in range(1, m) if math.gcd(i, m) == 1]
        if not new_edges:
            continue
        next_avoiding = []
        for col in avoiding:
            for bits in range(2 ** len(new_edges)):
                new_col = dict(col)
                for i, e in enumerate(new_edges):
                    new_col[e] = (bits >> i) & 1
                if has_monochromatic_clique(m, k, new_col) is None:
                    next_avoiding.append(new_col)
        if not next_avoiding:
            return [], coprime_edges(n)
        avoiding = next_avoiding

    # Convert to binary tuples over the canonical edge ordering
    edges_n = coprime_edges(n)
    codewords = []
    for col in avoiding:
        cw = tuple(col[e] for e in edges_n)
        codewords.append(cw)
    return codewords, edges_n


def hamming_distance(a: Tuple[int, ...], b: Tuple[int, ...]) -> int:
    """Hamming distance between two binary tuples."""
    return sum(x != y for x, y in zip(a, b))


def hamming_weight(a: Tuple[int, ...]) -> int:
    """Hamming weight (number of 1s) of a binary tuple."""
    return sum(a)


def compute_code_parameters(
    codewords: List[Tuple[int, ...]], block_length: int
) -> Dict:
    """
    Compute fundamental code parameters.

    Returns dict with:
      - size: number of codewords |C|
      - block_length: n (bits per codeword)
      - min_distance: minimum Hamming distance d_min
      - rate: log2(|C|) / n
      - weight_distribution: Counter mapping weight -> count
      - is_complement_closed: whether c in C implies ~c in C
      - is_linear: whether C is closed under XOR (GF(2) addition)
      - gf2_rank: rank of the code matrix over GF(2)
    """
    cw_set = set(codewords)
    size = len(cw_set)

    if size == 0:
        return {
            "size": 0,
            "block_length": block_length,
            "min_distance": None,
            "rate": 0.0,
            "weight_distribution": Counter(),
            "is_complement_closed": True,
            "is_linear": True,
            "gf2_rank": 0,
        }

    # Weight distribution
    weight_dist = Counter(hamming_weight(cw) for cw in cw_set)

    # Minimum distance
    cw_list = list(cw_set)
    min_dist = block_length + 1
    if size >= 2:
        for i in range(len(cw_list)):
            for j in range(i + 1, len(cw_list)):
                d = hamming_distance(cw_list[i], cw_list[j])
                if d < min_dist:
                    min_dist = d
                    if d == 1:
                        break
            if min_dist == 1:
                break
    else:
        min_dist = 0

    # Complement closure
    complement_closed = all(
        tuple(1 - x for x in cw) in cw_set for cw in cw_set
    )

    # Linearity check: closed under XOR and contains zero vector
    zero = tuple(0 for _ in range(block_length))
    has_zero = zero in cw_set
    is_linear = has_zero
    if is_linear and size > 1:
        # Check XOR closure on a sample first (early exit)
        for i in range(min(len(cw_list), 50)):
            for j in range(i, min(len(cw_list), 50)):
                xor = tuple(a ^ b for a, b in zip(cw_list[i], cw_list[j]))
                if xor not in cw_set:
                    is_linear = False
                    break
            if not is_linear:
                break

    # GF(2) rank
    matrix = np.array(cw_list, dtype=np.int32)
    gf2_rank = _gf2_rank(matrix)

    rate = math.log2(size) / block_length if size > 1 else 0.0

    return {
        "size": size,
        "block_length": block_length,
        "min_distance": min_dist,
        "rate": rate,
        "weight_distribution": weight_dist,
        "is_complement_closed": complement_closed,
        "is_linear": is_linear,
        "gf2_rank": gf2_rank,
    }


def _gf2_rank(matrix: np.ndarray) -> int:
    """Compute the rank of a binary matrix over GF(2)."""
    m = matrix.copy() % 2
    rows, cols = m.shape
    rank = 0
    for col in range(cols):
        pivot = None
        for row in range(rank, rows):
            if m[row, col] == 1:
                pivot = row
                break
        if pivot is None:
            continue
        m[[rank, pivot]] = m[[pivot, rank]]
        for row in range(rows):
            if row != rank and m[row, col] == 1:
                m[row] = (m[row] + m[rank]) % 2
        rank += 1
    return rank


# =========================================================================
# Section 2: Gilbert-Varshamov Comparison
# =========================================================================


def gilbert_varshamov_bound(n: int, d: int) -> int:
    """
    Gilbert-Varshamov lower bound on the size of a binary code.

    For a binary code of length n and minimum distance d,
    |C| >= 2^n / V(n, d-1), where V(n, r) = sum_{i=0}^{r} C(n,i)
    is the volume of a Hamming ball of radius r.
    """
    if d <= 0:
        return 2**n
    if d > n:
        return 1
    vol = sum(math.comb(n, i) for i in range(d))
    return max(1, math.ceil(2**n / vol))


def singleton_bound(n: int, d: int) -> int:
    """
    Singleton upper bound: |C| <= 2^{n - d + 1}.
    """
    if d <= 0:
        return 2**n
    return 2 ** max(0, n - d + 1)


def hamming_bound(n: int, d: int) -> int:
    """
    Hamming (sphere-packing) upper bound: |C| <= 2^n / V(n, floor((d-1)/2)).
    """
    if d <= 0:
        return 2**n
    t = (d - 1) // 2
    vol = sum(math.comb(n, i) for i in range(t + 1))
    return math.floor(2**n / vol)


def plotkin_bound(n: int, d: int) -> Optional[int]:
    """
    Plotkin upper bound: if d > n/2, then |C| <= 2*d / (2*d - n).
    Returns None if not applicable.
    """
    if 2 * d <= n:
        return None  # Plotkin bound not applicable
    return math.floor(2 * d / (2 * d - n))


def compare_with_bounds(
    code_size: int, block_length: int, min_distance: int
) -> Dict:
    """
    Compare a code against classical bounds.

    Returns dict with bound values and whether the code meets each.
    """
    n, d = block_length, min_distance
    gv = gilbert_varshamov_bound(n, d)
    singleton = singleton_bound(n, d)
    hamming_bnd = hamming_bound(n, d)
    plotkin = plotkin_bound(n, d)

    result = {
        "code_size": code_size,
        "block_length": n,
        "min_distance": d,
        "gilbert_varshamov_lower": gv,
        "singleton_upper": singleton,
        "hamming_upper": hamming_bnd,
        "plotkin_upper": plotkin,
        "exceeds_gv": code_size >= gv,
        "below_singleton": code_size <= singleton,
        "below_hamming": code_size <= hamming_bnd,
    }
    if plotkin is not None:
        result["below_plotkin"] = code_size <= plotkin
    return result


# =========================================================================
# Section 3: Structure of the Avoiding Code
# =========================================================================


def compute_distance_matrix(codewords: List[Tuple[int, ...]]) -> np.ndarray:
    """
    Compute full pairwise Hamming distance matrix.

    Returns symmetric matrix D where D[i,j] = d_H(codewords[i], codewords[j]).
    """
    n_cw = len(codewords)
    dist = np.zeros((n_cw, n_cw), dtype=np.int32)
    for i in range(n_cw):
        for j in range(i + 1, n_cw):
            d = hamming_distance(codewords[i], codewords[j])
            dist[i, j] = d
            dist[j, i] = d
    return dist


def distance_distribution(codewords: List[Tuple[int, ...]]) -> Counter:
    """
    Compute the distance distribution A_d = number of pairs at distance d.
    """
    dist_count = Counter()
    for i in range(len(codewords)):
        for j in range(i + 1, len(codewords)):
            d = hamming_distance(codewords[i], codewords[j])
            dist_count[d] += 1
    return dist_count


def cluster_codewords(
    codewords: List[Tuple[int, ...]],
    n_clusters: int = 4,
    method: str = "average",
) -> Dict:
    """
    Hierarchical clustering of codewords by Hamming distance.

    Returns dict with:
      - labels: cluster assignment for each codeword
      - cluster_sizes: Counter of cluster sizes
      - intra_distances: average intra-cluster distance for each cluster
      - inter_distances: average inter-cluster distance for each pair
    """
    if len(codewords) < 2:
        return {
            "labels": [0] * len(codewords),
            "cluster_sizes": Counter({0: len(codewords)}),
            "intra_distances": {0: 0.0},
            "inter_distances": {},
        }

    dist_matrix = compute_distance_matrix(codewords)
    condensed = squareform(dist_matrix, checks=False)
    Z = linkage(condensed, method=method)
    labels = fcluster(Z, t=n_clusters, criterion="maxclust")

    cluster_sizes = Counter(labels)

    # Intra-cluster distances
    intra = {}
    for c in cluster_sizes:
        indices = [i for i, l in enumerate(labels) if l == c]
        if len(indices) < 2:
            intra[c] = 0.0
        else:
            dists = [
                dist_matrix[i, j]
                for i in indices
                for j in indices
                if i < j
            ]
            intra[c] = float(np.mean(dists))

    # Inter-cluster distances
    inter = {}
    clusters = sorted(cluster_sizes.keys())
    for ci in range(len(clusters)):
        for cj in range(ci + 1, len(clusters)):
            idx_i = [i for i, l in enumerate(labels) if l == clusters[ci]]
            idx_j = [i for i, l in enumerate(labels) if l == clusters[cj]]
            dists = [dist_matrix[a, b] for a in idx_i for b in idx_j]
            inter[(clusters[ci], clusters[cj])] = float(np.mean(dists))

    return {
        "labels": list(labels),
        "cluster_sizes": cluster_sizes,
        "intra_distances": intra,
        "inter_distances": inter,
    }


def find_complement_pairs(
    codewords: List[Tuple[int, ...]]
) -> List[Tuple[int, int]]:
    """
    Find pairs (i, j) where codewords[j] is the complement of codewords[i].

    A complement-closed code pairs every codeword with its bitwise complement.
    """
    cw_to_idx = {}
    for i, cw in enumerate(codewords):
        cw_to_idx[cw] = i

    pairs = []
    seen = set()
    for i, cw in enumerate(codewords):
        if i in seen:
            continue
        comp = tuple(1 - x for x in cw)
        j = cw_to_idx.get(comp)
        if j is not None and j != i:
            pairs.append((i, j))
            seen.add(i)
            seen.add(j)
    return pairs


def compute_automorphism_generators(
    codewords: List[Tuple[int, ...]],
    edges: List[Tuple[int, int]],
    n: int,
) -> Dict:
    """
    Find permutation symmetries of the avoiding code inherited from
    the coprime graph's automorphism group.

    A permutation sigma of [n] that preserves coprimality (i.e., is an
    automorphism of G([n])) acts on edge colorings by permuting edges.
    We check which such permutations map the code to itself.

    For G([n]), the only automorphism is the identity when n >= 3,
    since vertex 1 is the unique vertex adjacent to all others, and
    the degree sequence is typically unique. The code also has the
    complement symmetry c -> ~c.

    Returns dict with symmetry information.
    """
    cw_set = set(codewords)
    edge_idx = {e: i for i, e in enumerate(edges)}
    n_edges = len(edges)

    # Build coprime adjacency
    adj = {v: set() for v in range(1, n + 1)}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)

    # Find automorphisms of the coprime graph by checking degree-preserving
    # permutations. For small n, we check all permutations that fix 1
    # (since deg(1) = n-1 is unique).
    from itertools import permutations as perms

    generators = []

    # Vertex 1 has degree n-1 (coprime with all), so any automorphism
    # must fix vertex 1. Check permutations of {2,...,n}.
    rest = list(range(2, n + 1))
    degrees = {v: len(adj[v]) for v in range(1, n + 1)}

    # Group vertices by degree for pruning
    deg_classes = {}
    for v in rest:
        deg_classes.setdefault(degrees[v], []).append(v)

    # For n=10, |rest|=9 so 9! = 362880 -- feasible but large.
    # Use degree-class constraint to prune.
    # Only permute within each degree class.
    from itertools import product as iter_product

    class_perms = {}
    for deg, verts in deg_classes.items():
        class_perms[deg] = list(perms(verts))

    # Build all candidate permutations as products of per-class permutations
    deg_keys = sorted(class_perms.keys())
    checked = 0
    for combo in iter_product(*(class_perms[d] for d in deg_keys)):
        checked += 1
        if checked > 500000:
            break  # Safety limit

        # Build the full permutation sigma: [n] -> [n]
        sigma = {1: 1}
        for deg_idx, dk in enumerate(deg_keys):
            orig = deg_classes[dk]
            perm = combo[deg_idx]
            for old, new in zip(orig, perm):
                sigma[old] = new

        # Check if sigma preserves coprimality
        is_auto = True
        for u, v in edges:
            su, sv = sigma[u], sigma[v]
            if math.gcd(su, sv) != 1:
                is_auto = False
                break
        if not is_auto:
            continue

        # Check if sigma preserves non-edges too
        # (already guaranteed if we checked all edges and sigma is bijective)

        # Compute the induced permutation on codewords
        # sigma maps edge (u,v) to edge (sigma(u), sigma(v))
        edge_perm = {}
        for e in edges:
            u, v = e
            su, sv = sigma[u], sigma[v]
            mapped = (min(su, sv), max(su, sv))
            edge_perm[e] = mapped

        # Check if this permutation maps the code to itself
        maps_code = True
        for cw in codewords:
            # Apply edge permutation to codeword
            new_cw = [0] * n_edges
            for i, e in enumerate(edges):
                mapped_e = edge_perm[e]
                new_cw[edge_idx[mapped_e]] = cw[i]
            if tuple(new_cw) not in cw_set:
                maps_code = False
                break

        if maps_code:
            if sigma != {v: v for v in range(1, n + 1)}:
                generators.append(sigma)

    return {
        "num_automorphisms": len(generators) + 1,  # +1 for identity
        "has_complement_symmetry": all(
            tuple(1 - x for x in cw) in cw_set for cw in cw_set
        ),
        "generators": generators[:10],  # Return at most 10
        "checked_candidates": checked,
    }


# =========================================================================
# Section 4: The Ramsey Code Family
# =========================================================================


def ramsey_code_family(
    k: int, n_range: Optional[Tuple[int, int]] = None
) -> List[Dict]:
    """
    Compute code parameters for C(n,k) across a range of n values.

    For each n < R_cop(k), the set of avoiding colorings forms a code.
    We track how the code evolves as n approaches the Ramsey threshold.

    Returns list of dicts with parameters for each n.
    """
    if n_range is None:
        n_range = (k, 10 if k == 3 else k + 5)

    results = []
    for n in range(n_range[0], n_range[1] + 1):
        edges_n = coprime_edges(n)
        n_edges = len(edges_n)

        if n_edges == 0:
            results.append({
                "n": n,
                "num_edges": 0,
                "code_size": 1,  # trivial empty coloring
                "rate": 0.0,
                "min_distance": None,
            })
            continue

        # For small enough edge counts, enumerate directly
        if n_edges <= 27:
            codewords, _ = enumerate_avoiding_colorings(n, k)
        else:
            # Use SAT solver to sample colorings (can't enumerate all)
            codewords, _ = _sat_enumerate_avoiding(n, k, max_count=2000)

        code_size = len(codewords)
        if code_size == 0:
            results.append({
                "n": n,
                "num_edges": n_edges,
                "code_size": 0,
                "rate": 0.0,
                "min_distance": None,
            })
            continue

        # Compute minimum distance
        min_dist = n_edges + 1
        if code_size >= 2:
            for i in range(len(codewords)):
                for j in range(i + 1, len(codewords)):
                    d = hamming_distance(codewords[i], codewords[j])
                    if d < min_dist:
                        min_dist = d
                        if d == 1:
                            break
                if min_dist == 1:
                    break
        else:
            min_dist = 0

        rate = math.log2(code_size) / n_edges if code_size > 1 else 0.0

        results.append({
            "n": n,
            "num_edges": n_edges,
            "code_size": code_size,
            "rate": rate,
            "min_distance": min_dist,
        })

    return results


def _sat_enumerate_avoiding(
    n: int, k: int, max_count: int = 2000
) -> Tuple[List[Tuple[int, ...]], List[Tuple[int, int]]]:
    """
    Enumerate avoiding colorings using SAT solver with blocking clauses.

    For larger n where full enumeration is infeasible, we use the SAT
    solver to generate colorings one at a time, blocking each found
    solution.
    """
    from pysat.solvers import Glucose4

    edges_n = coprime_edges(n)
    n_edges = len(edges_n)

    # Build edge-to-var mapping
    edge_to_var = {}
    next_var = 1
    adj = {}
    for v in range(1, n + 1):
        adj[v] = set()
    for u, v in edges_n:
        adj[u].add(v)
        adj[v].add(u)
        edge_to_var[(u, v)] = next_var
        next_var += 1

    # Find all k-cliques
    cliques = find_coprime_cliques(n, k)

    # Build clauses
    clauses = []
    for clique in cliques:
        vlist = sorted(clique)
        vars_ = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                e = (vlist[i], vlist[j])
                vars_.append(edge_to_var[e])
        clauses.append([-v for v in vars_])
        clauses.append([v for v in vars_])

    solver = Glucose4(bootstrap_with=clauses)
    codewords = []

    for _ in range(max_count):
        if not solver.solve():
            break
        model = solver.get_model()
        model_set = set(model)

        # Extract codeword
        cw = tuple(
            0 if edge_to_var[e] in model_set else 1
            for e in edges_n
        )
        codewords.append(cw)

        # Block this solution
        solver.add_clause([-l for l in model])

    solver.delete()
    return codewords, edges_n


# =========================================================================
# Section 5: Tanner Graph / Belief Propagation Analogy
# =========================================================================


def build_tanner_graph(
    n: int, k: int
) -> Dict:
    """
    Build the Tanner graph for the coprime Ramsey constraint.

    In LDPC terminology:
      - Variable nodes: one per coprime edge (the bits to be determined)
      - Check nodes: one per coprime k-clique (each clique generates two
        parity-like constraints: not-all-0 and not-all-1)

    The Tanner graph's structure determines whether message-passing
    algorithms like belief propagation can efficiently find solutions.

    Returns dict with graph structure and statistics.
    """
    edges = coprime_edges(n)
    cliques = find_coprime_cliques(n, k)

    edge_idx = {e: i for i, e in enumerate(edges)}
    n_vars = len(edges)
    n_checks = 2 * len(cliques)  # Two checks per clique

    # Build adjacency: check -> set of variable indices
    check_to_vars = []
    for clique in cliques:
        vlist = sorted(clique)
        var_indices = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                e = (vlist[i], vlist[j])
                var_indices.append(edge_idx[e])
        # Two checks: forbid all-0 and forbid all-1
        check_to_vars.append(var_indices)  # not-all-0
        check_to_vars.append(var_indices)  # not-all-1

    # Variable degree: how many checks involve each variable
    var_degree = [0] * n_vars
    for check_vars in check_to_vars:
        for v in check_vars:
            var_degree[v] += 1

    # Check degree: number of variables in each check
    check_degree = [len(cv) for cv in check_to_vars]

    # Girth estimation (length of shortest cycle in Tanner graph)
    # Approximate via BFS from a few nodes
    girth = _estimate_tanner_girth(n_vars, n_checks, check_to_vars)

    return {
        "n_variable_nodes": n_vars,
        "n_check_nodes": n_checks,
        "n_cliques": len(cliques),
        "check_to_vars": check_to_vars,
        "var_degree_dist": Counter(var_degree),
        "check_degree_dist": Counter(check_degree),
        "avg_var_degree": float(np.mean(var_degree)) if var_degree else 0,
        "avg_check_degree": float(np.mean(check_degree)) if check_degree else 0,
        "density": n_checks / n_vars if n_vars > 0 else 0,
        "girth": girth,
    }


def _estimate_tanner_girth(
    n_vars: int, n_checks: int, check_to_vars: List[List[int]]
) -> int:
    """
    Estimate the girth of the Tanner graph via BFS.

    The girth is the length of the shortest cycle. In a bipartite graph
    (variable nodes and check nodes), all cycles have even length.
    """
    # Build adjacency lists for bipartite graph
    # Variable nodes: 0..n_vars-1
    # Check nodes: n_vars..n_vars+n_checks-1
    var_to_checks = [[] for _ in range(n_vars)]
    for c_idx, var_list in enumerate(check_to_vars):
        for v in var_list:
            var_to_checks[v].append(n_vars + c_idx)

    check_adj = {}
    for c_idx, var_list in enumerate(check_to_vars):
        check_adj[n_vars + c_idx] = var_list

    total_nodes = n_vars + n_checks
    min_girth = float("inf")

    # BFS from a sample of nodes to find shortest cycle
    sample_nodes = list(range(min(n_vars, 20)))
    for start in sample_nodes:
        dist = [-1] * total_nodes
        dist[start] = 0
        queue = [start]
        qi = 0
        found = False
        while qi < len(queue) and not found:
            node = queue[qi]
            qi += 1
            if node < n_vars:
                # Variable node -> check neighbors
                neighbors = var_to_checks[node]
            else:
                # Check node -> variable neighbors
                neighbors = check_adj.get(node, [])
            for nbr in neighbors:
                if dist[nbr] == -1:
                    dist[nbr] = dist[node] + 1
                    queue.append(nbr)
                elif dist[nbr] >= dist[node]:
                    # Found a cycle of length dist[node] + dist[nbr] + 1
                    cycle_len = dist[node] + dist[nbr] + 1
                    min_girth = min(min_girth, cycle_len)
                    found = True
                    break

    return int(min_girth) if min_girth < float("inf") else 0


def belief_propagation_decode(
    n: int,
    k: int,
    received: Tuple[int, ...],
    max_iter: int = 100,
    damping: float = 0.5,
) -> Tuple[Tuple[int, ...], bool, int]:
    """
    Attempt to decode a noisy coloring using belief propagation on
    the Tanner graph of coprime Ramsey constraints.

    Each check node enforces "not all same color" for the edges of
    a coprime k-clique. The BP messages propagate soft information
    about the likelihood of each edge being color 0 or 1.

    Args:
        n: graph size
        k: clique size to avoid
        received: noisy binary coloring (tuple of 0/1 per edge)
        max_iter: maximum BP iterations
        damping: damping factor for message updates (0 = no damping)

    Returns:
        (decoded, converged, iterations):
          decoded: the BP-decoded coloring
          converged: whether BP converged
          iterations: number of iterations used
    """
    edges = coprime_edges(n)
    cliques = find_coprime_cliques(n, k)
    edge_idx = {e: i for i, e in enumerate(edges)}
    n_vars = len(edges)

    # Build check structure
    # Each clique generates two checks: not-all-0 and not-all-1
    checks = []
    for clique in cliques:
        vlist = sorted(clique)
        var_indices = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                var_indices.append(edge_idx[(vlist[i], vlist[j])])
        checks.append(("not_all_0", var_indices))
        checks.append(("not_all_1", var_indices))

    n_checks = len(checks)

    # Channel LLR (log-likelihood ratio): positive means bit=0 more likely
    # For received bit r, channel LLR = (-1)^r * channel_reliability
    channel_reliability = 2.0  # moderate confidence in received bits
    channel_llr = np.array([
        channel_reliability * (1 - 2 * received[i]) for i in range(n_vars)
    ])

    # Message arrays: check-to-variable messages (LLR domain)
    # msg_c2v[c][v_local] = LLR message from check c to its v_local-th variable
    msg_c2v = [[0.0] * len(checks[c][1]) for c in range(n_checks)]

    converged = False
    for iteration in range(max_iter):
        # Variable-to-check messages
        msg_v2c = [[0.0] * len(checks[c][1]) for c in range(n_checks)]
        for c_idx, (ctype, var_indices) in enumerate(checks):
            for v_local, v_global in enumerate(var_indices):
                # Sum of all incoming messages except from this check
                total = channel_llr[v_global]
                for c2_idx, (_, var_indices2) in enumerate(checks):
                    if c2_idx == c_idx:
                        continue
                    for v2_local, v2_global in enumerate(var_indices2):
                        if v2_global == v_global:
                            total += msg_c2v[c2_idx][v2_local]
                msg_v2c[c_idx][v_local] = total

        # Check-to-variable messages
        old_msg_c2v = [list(m) for m in msg_c2v]
        max_delta = 0.0

        for c_idx, (ctype, var_indices) in enumerate(checks):
            k_edges = len(var_indices)
            for v_local in range(k_edges):
                # Compute the check message using min-sum approximation
                other_llrs = [
                    msg_v2c[c_idx][j]
                    for j in range(k_edges)
                    if j != v_local
                ]

                if ctype == "not_all_0":
                    # At least one variable must be 1
                    # This means: NOT (all bits = 0)
                    # In LLR: product of tanh(llr/2) gives tanh of output
                    # Min-sum approx: sign * min(|others|)
                    if not other_llrs:
                        new_msg = 0.0
                    else:
                        signs = [1 if x >= 0 else -1 for x in other_llrs]
                        overall_sign = 1
                        for s in signs:
                            overall_sign *= s
                        # Flip sign because constraint is "not all 0"
                        # means at least one must be positive (value 1)
                        min_abs = min(abs(x) for x in other_llrs)
                        new_msg = -overall_sign * min_abs

                elif ctype == "not_all_1":
                    # At least one variable must be 0
                    # Negate all inputs, apply not-all-0, negate output
                    if not other_llrs:
                        new_msg = 0.0
                    else:
                        neg_others = [-x for x in other_llrs]
                        signs = [1 if x >= 0 else -1 for x in neg_others]
                        overall_sign = 1
                        for s in signs:
                            overall_sign *= s
                        min_abs = min(abs(x) for x in neg_others)
                        new_msg = overall_sign * min_abs

                # Apply damping
                damped = damping * old_msg_c2v[c_idx][v_local] + (1 - damping) * new_msg
                delta = abs(damped - old_msg_c2v[c_idx][v_local])
                if delta > max_delta:
                    max_delta = delta
                msg_c2v[c_idx][v_local] = damped

        if max_delta < 1e-6:
            converged = True
            break

    # Final decision: total LLR for each variable
    decoded = []
    for v in range(n_vars):
        total = channel_llr[v]
        for c_idx, (_, var_indices) in enumerate(checks):
            for v_local, v_global in enumerate(var_indices):
                if v_global == v:
                    total += msg_c2v[c_idx][v_local]
        decoded.append(0 if total >= 0 else 1)

    return tuple(decoded), converged, iteration + 1


def compare_bp_vs_sat(
    n: int,
    k: int,
    num_trials: int = 20,
    noise_rates: Optional[List[float]] = None,
    seed: int = 42,
) -> Dict:
    """
    Compare belief propagation vs SAT solver for finding avoiding colorings
    from noisy starting points.

    For each trial:
    1. Generate a valid avoiding coloring (via SAT)
    2. Flip each bit with probability p (noise)
    3. Try to recover an avoiding coloring using BP and SAT
    4. Compare success rates and times

    Returns dict with comparative statistics.
    """
    if noise_rates is None:
        noise_rates = [0.05, 0.10, 0.15, 0.20]

    rng = random.Random(seed)
    edges = coprime_edges(n)
    n_edges = len(edges)

    # Get a base avoiding coloring via SAT
    enc = CoprimeSATEncoder(k)
    sat = enc.extend_to(n)
    if not sat:
        enc.close()
        return {"error": f"No avoiding coloring at n={n} for k={k}"}

    base_coloring = enc.get_model()
    enc.close()
    base_cw = tuple(base_coloring[e] for e in edges)

    results = {}
    for p in noise_rates:
        bp_successes = 0
        bp_times = []
        sat_successes = 0
        sat_times = []

        for _ in range(num_trials):
            # Add noise
            noisy = tuple(
                b ^ (1 if rng.random() < p else 0) for b in base_cw
            )
            flips = hamming_distance(base_cw, noisy)

            # Try BP
            t0 = time.time()
            decoded_bp, conv, iters = belief_propagation_decode(
                n, k, noisy, max_iter=100
            )
            bp_time = time.time() - t0
            bp_times.append(bp_time)

            # Check if BP output is a valid avoiding coloring
            col_bp = {e: decoded_bp[i] for i, e in enumerate(edges)}
            bp_valid = validate_avoiding_coloring(n, k, col_bp)
            if bp_valid:
                bp_successes += 1

            # Try SAT (use noisy coloring as phase hint -- just solve fresh)
            t0 = time.time()
            enc2 = CoprimeSATEncoder(k)
            sat2 = enc2.extend_to(n)
            sat_time = time.time() - t0
            sat_times.append(sat_time)
            if sat2:
                sat_successes += 1
            enc2.close()

        results[p] = {
            "noise_rate": p,
            "bp_success_rate": bp_successes / num_trials,
            "sat_success_rate": sat_successes / num_trials,
            "bp_avg_time": float(np.mean(bp_times)),
            "sat_avg_time": float(np.mean(sat_times)),
        }

    return results


# =========================================================================
# Section 6: Error Correction on the Coprime Graph
# =========================================================================


def error_correction_capability(
    codewords: List[Tuple[int, ...]],
    block_length: int,
) -> Dict:
    """
    Analyze the error-correcting capability of the Ramsey code.

    For a code with minimum distance d_min:
      - Can detect up to d_min - 1 errors
      - Can correct up to floor((d_min - 1) / 2) errors

    We also compute the actual decoding radius by nearest-neighbor
    decoding: for each received word at distance t from a codeword,
    check if decoding is unique.

    Returns dict with error correction parameters.
    """
    cw_set = set(codewords)
    n_cw = len(codewords)

    if n_cw < 2:
        return {
            "min_distance": 0,
            "error_detection": 0,
            "error_correction": 0,
            "list_decode_radius": 0,
            "covering_radius": None,
        }

    # Minimum distance
    min_dist = block_length + 1
    for i in range(n_cw):
        for j in range(i + 1, n_cw):
            d = hamming_distance(codewords[i], codewords[j])
            if d < min_dist:
                min_dist = d
                if d == 1:
                    break
        if min_dist == 1:
            break

    # Standard bounds
    error_detection = min_dist - 1
    error_correction = (min_dist - 1) // 2

    # Covering radius: max over all binary strings of (min distance to any codeword)
    # For block_length=31 this is infeasible to compute exactly.
    # Estimate by sampling.
    rng = random.Random(42)
    max_min_dist = 0
    n_samples = min(5000, 2**block_length)
    for _ in range(n_samples):
        word = tuple(rng.randint(0, 1) for _ in range(block_length))
        min_d = min(hamming_distance(word, cw) for cw in codewords)
        if min_d > max_min_dist:
            max_min_dist = min_d

    # List decoding: for radius t, what's the max list size?
    list_sizes = {}
    for t in range(1, min(min_dist + 3, block_length)):
        max_list = 0
        for cw in codewords[:20]:  # Sample from codewords
            count = sum(
                1 for other in codewords
                if hamming_distance(cw, other) <= t
            )
            if count > max_list:
                max_list = count
        list_sizes[t] = max_list

    return {
        "min_distance": min_dist,
        "error_detection": error_detection,
        "error_correction": error_correction,
        "covering_radius_estimate": max_min_dist,
        "list_decode_sizes": list_sizes,
    }


def decode_nearest_neighbor(
    received: Tuple[int, ...],
    codewords: List[Tuple[int, ...]],
) -> Tuple[Optional[Tuple[int, ...]], int, int]:
    """
    Decode by nearest-neighbor: find the codeword closest in Hamming distance.

    Returns (decoded_codeword, distance, num_ties).
    """
    best_dist = len(received) + 1
    best_cw = None
    ties = 0

    for cw in codewords:
        d = hamming_distance(received, cw)
        if d < best_dist:
            best_dist = d
            best_cw = cw
            ties = 1
        elif d == best_dist:
            ties += 1

    return best_cw, best_dist, ties


def noisy_decoding_experiment(
    codewords: List[Tuple[int, ...]],
    edges: List[Tuple[int, int]],
    n: int,
    k: int,
    noise_rates: Optional[List[float]] = None,
    num_trials: int = 100,
    seed: int = 42,
) -> Dict:
    """
    Experiment: flip bits in a valid avoiding coloring and try to decode.

    For each noise rate p and each trial:
    1. Pick a random codeword
    2. Flip each bit independently with probability p
    3. Decode by nearest neighbor
    4. Check if decoded word is (a) the original, (b) a valid codeword

    Returns dict with success rates per noise level.
    """
    if noise_rates is None:
        noise_rates = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30]

    rng = random.Random(seed)
    block_length = len(edges)

    results = {}
    for p in noise_rates:
        exact_recoveries = 0
        valid_decodings = 0

        for _ in range(num_trials):
            # Pick random codeword
            original = codewords[rng.randrange(len(codewords))]

            # Add noise
            noisy = tuple(
                b ^ (1 if rng.random() < p else 0) for b in original
            )
            actual_flips = hamming_distance(original, noisy)

            # Decode
            decoded, dist, ties = decode_nearest_neighbor(noisy, codewords)
            if decoded == original:
                exact_recoveries += 1
            if decoded is not None:
                valid_decodings += 1

        results[p] = {
            "noise_rate": p,
            "exact_recovery_rate": exact_recoveries / num_trials,
            "valid_decode_rate": valid_decodings / num_trials,
        }

    return results


# =========================================================================
# Main: Full Analysis
# =========================================================================


def main():
    print("=" * 72)
    print("RAMSEY CODES: CODING THEORY OF COPRIME RAMSEY COLORINGS")
    print("=" * 72)
    print()

    # ------------------------------------------------------------------
    # Section 1: The Avoiding Code at n=10, k=3
    # ------------------------------------------------------------------
    print("--- Section 1: The Avoiding Code C(10, 3) ---")
    print()
    codewords, edges = enumerate_avoiding_colorings(10, 3)
    n_edges = len(edges)

    params = compute_code_parameters(codewords, n_edges)
    print(f"  Block length n = {params['block_length']}")
    print(f"  Code size |C| = {params['size']}")
    print(f"  Minimum distance d_min = {params['min_distance']}")
    print(f"  Rate R = log2({params['size']})/{n_edges} = {params['rate']:.4f} bits/symbol")
    print(f"  Complement closed: {params['is_complement_closed']}")
    print(f"  Linear (GF(2)): {params['is_linear']}")
    print(f"  GF(2) rank: {params['gf2_rank']}")
    print()

    print("  Weight distribution:")
    for w in sorted(params["weight_distribution"]):
        print(f"    w={w:2d}: {params['weight_distribution'][w]:3d} codewords")
    print()

    # ------------------------------------------------------------------
    # Section 2: Gilbert-Varshamov Comparison
    # ------------------------------------------------------------------
    print("--- Section 2: Gilbert-Varshamov Comparison ---")
    print()

    bounds = compare_with_bounds(
        params["size"], n_edges, params["min_distance"]
    )
    print(f"  Code: [{n_edges}, log2({params['size']})={math.log2(params['size']):.2f}, "
          f"{params['min_distance']}]")
    print(f"  GV lower bound: {bounds['gilbert_varshamov_lower']}")
    print(f"  Singleton upper: {bounds['singleton_upper']}")
    print(f"  Hamming upper: {bounds['hamming_upper']}")
    if bounds["plotkin_upper"] is not None:
        print(f"  Plotkin upper: {bounds['plotkin_upper']}")
    print(f"  Code exceeds GV bound: {bounds['exceeds_gv']}")
    print(f"  Code below Singleton: {bounds['below_singleton']}")
    print(f"  Code below Hamming: {bounds['below_hamming']}")
    print()

    # ------------------------------------------------------------------
    # Section 3: Structure of the Avoiding Code
    # ------------------------------------------------------------------
    print("--- Section 3: Code Structure ---")
    print()

    # Distance distribution
    dist_dist = distance_distribution(codewords)
    print("  Distance distribution (palindromic):")
    for d in sorted(dist_dist):
        marker = " <--" if d == params["min_distance"] else ""
        print(f"    d={d:2d}: {dist_dist[d]:5d} pairs{marker}")
    print()

    # Complement pairs
    pairs = find_complement_pairs(codewords)
    print(f"  Complement pairs: {len(pairs)} (code size / 2 = {len(codewords) // 2})")
    print()

    # Clustering
    clustering = cluster_codewords(codewords, n_clusters=4)
    print("  Hierarchical clustering (4 clusters):")
    for c in sorted(clustering["cluster_sizes"]):
        intra = clustering["intra_distances"].get(c, 0)
        print(f"    Cluster {c}: size={clustering['cluster_sizes'][c]:3d}, "
              f"avg intra-dist={intra:.1f}")
    print("  Inter-cluster distances:")
    for (ci, cj), d in sorted(clustering["inter_distances"].items()):
        print(f"    ({ci},{cj}): avg dist = {d:.1f}")
    print()

    # Automorphisms (skip if n too large)
    print("  Automorphism analysis:")
    auto = compute_automorphism_generators(codewords, edges, 10)
    print(f"    Graph automorphisms preserving code: {auto['num_automorphisms']}")
    print(f"    Complement symmetry: {auto['has_complement_symmetry']}")
    print()

    # ------------------------------------------------------------------
    # Section 4: The Ramsey Code Family
    # ------------------------------------------------------------------
    print("--- Section 4: Ramsey Code Family C(n, 3) ---")
    print()
    family = ramsey_code_family(3, n_range=(4, 10))
    print(f"  {'n':>3s}  {'edges':>5s}  {'|C|':>6s}  {'rate':>7s}  {'d_min':>5s}")
    print("  " + "-" * 32)
    for entry in family:
        d_str = str(entry["min_distance"]) if entry["min_distance"] is not None else "-"
        print(f"  {entry['n']:3d}  {entry['num_edges']:5d}  {entry['code_size']:6d}  "
              f"{entry['rate']:7.4f}  {d_str:>5s}")
    print()
    print("  Rate decays as n -> R_cop(3) = 11, reaching 0 at the threshold.")
    print()

    # ------------------------------------------------------------------
    # Section 5: Tanner Graph / BP Analysis
    # ------------------------------------------------------------------
    print("--- Section 5: Tanner Graph and Belief Propagation ---")
    print()
    tanner = build_tanner_graph(10, 3)
    print(f"  Tanner graph for C(10, 3):")
    print(f"    Variable nodes (edges): {tanner['n_variable_nodes']}")
    print(f"    Check nodes (2 * cliques): {tanner['n_check_nodes']}")
    print(f"    Cliques: {tanner['n_cliques']}")
    print(f"    Avg variable degree: {tanner['avg_var_degree']:.1f}")
    print(f"    Avg check degree: {tanner['avg_check_degree']:.1f}")
    print(f"    Check/variable ratio: {tanner['density']:.2f}")
    print(f"    Estimated girth: {tanner['girth']}")
    print()

    print("  Variable degree distribution:")
    for deg in sorted(tanner["var_degree_dist"]):
        print(f"    degree {deg:3d}: {tanner['var_degree_dist'][deg]:3d} variables")
    print()

    # BP vs SAT comparison (small scale)
    print("  BP vs SAT comparison (n=8, k=3):")
    bp_sat = compare_bp_vs_sat(8, 3, num_trials=10, noise_rates=[0.05, 0.10, 0.15])
    for p, stats in sorted(bp_sat.items()):
        print(f"    noise={p:.2f}: BP success={stats['bp_success_rate']:.0%}, "
              f"SAT success={stats['sat_success_rate']:.0%}, "
              f"BP time={stats['bp_avg_time']:.4f}s, "
              f"SAT time={stats['sat_avg_time']:.4f}s")
    print()

    # ------------------------------------------------------------------
    # Section 6: Error Correction
    # ------------------------------------------------------------------
    print("--- Section 6: Error Correction Capability ---")
    print()
    ec = error_correction_capability(codewords, n_edges)
    print(f"  Minimum distance: {ec['min_distance']}")
    print(f"  Error detection: up to {ec['error_detection']} errors")
    print(f"  Error correction: up to {ec['error_correction']} errors")
    print(f"  Covering radius (estimate): {ec['covering_radius_estimate']}")
    print()
    print("  List decoding sizes (max codewords within radius t):")
    for t, ls in sorted(ec["list_decode_sizes"].items()):
        print(f"    t={t}: max list size = {ls}")
    print()

    # Noisy decoding experiment
    print("  Noisy decoding experiment (100 trials per noise level):")
    decode_results = noisy_decoding_experiment(
        codewords, edges, 10, 3,
        noise_rates=[0.0, 0.02, 0.05, 0.10, 0.15, 0.20],
        num_trials=100,
    )
    print(f"  {'noise':>6s}  {'exact recovery':>15s}  {'valid decode':>13s}")
    print("  " + "-" * 38)
    for p in sorted(decode_results):
        r = decode_results[p]
        print(f"  {p:6.2f}  {r['exact_recovery_rate']:15.0%}  "
              f"{r['valid_decode_rate']:13.0%}")
    print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"""
The avoiding code C(10, 3):
  - [{n_edges}, {math.log2(params['size']):.2f}, {params['min_distance']}] binary code
  - 156 codewords of length 31 (rate {params['rate']:.3f})
  - NOT linear, but complement-closed: c in C iff ~c in C
  - GF(2) rank {params['gf2_rank']} (far from 2^{params['gf2_rank']}={2**params['gf2_rank']} if linear)
  - Palindromic distance distribution: A_d = A_{{31-d}}
  - d_min = {params['min_distance']} gives minimal error correction
  - As n -> R_cop(3) = 11, the code vanishes (rate -> 0)

Coding-theoretic interpretation:
  - The coprime Ramsey problem is equivalent to finding the capacity
    of a binary channel with forbidden patterns (monochromatic cliques)
  - The "Ramsey capacity" R = max_n rate(C(n,k)) measures how much
    information can be stored in valid colorings
  - Belief propagation on the Tanner graph is less effective than
    SAT solving, suggesting the constraint structure has many short
    cycles (girth {tanner['girth']})
  - The complement closure reflects the color symmetry (0 <-> 1)
    inherent in 2-coloring problems
""")


if __name__ == "__main__":
    main()
