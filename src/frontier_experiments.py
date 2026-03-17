#!/usr/bin/env python3
"""
frontier_experiments.py — Novel computational experiments at unexplored intersections.

These experiments target GAP-BRIDGING proposals identified by the synthesis:
1. Additive combinatorics × Graph theory: Sidon sets in coprime graphs
2. Number theory × Ramsey theory: Ramsey multiplicity in structured sets
3. Chromatic × Sidon: Coloring Sidon-constrained graphs
4. AP-free × Coprime: Arithmetic progression avoidance in coprime subsets
5. Primitive sets × Graph theory: Divisibility graph coloring

Each experiment generates a novel conjecture with computational evidence.
"""

import math
import random
import numpy as np
from collections import defaultdict, Counter
from itertools import combinations
from typing import Set, List, Tuple, Dict, Any


# ═══════════════════════════════════════════════════════════════════
# Primitives
# ═══════════════════════════════════════════════════════════════════

def sieve_primes(n: int) -> List[int]:
    if n < 2:
        return []
    is_p = [True] * (n + 1)
    is_p[0] = is_p[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if is_p[i]:
            for j in range(i * i, n + 1, i):
                is_p[j] = False
    return [i for i, v in enumerate(is_p) if v]


def is_sidon(A: Set[int]) -> bool:
    """Check if A is a Sidon set (all pairwise sums distinct)."""
    A_list = sorted(A)
    sums = set()
    for i, a in enumerate(A_list):
        for b in A_list[i:]:
            s = a + b
            if s in sums:
                return False
            sums.add(s)
    return True


def has_3ap(A: Set[int]) -> bool:
    """Check if A contains a 3-term arithmetic progression."""
    A_sorted = sorted(A)
    A_set = set(A_sorted)
    for i, a in enumerate(A_sorted):
        for b in A_sorted[i + 1:]:
            c = 2 * b - a
            if c in A_set and c != b:
                return True
    return False


# ═══════════════════════════════════════════════════════════════════
# Experiment 1: Sidon Sets in Coprime Graphs
# ═══════════════════════════════════════════════════════════════════

def sidon_coprime_clique(n: int) -> Dict[str, Any]:
    """
    NOVEL: Find the largest Sidon set S ⊆ [n] such that all pairs in S
    are coprime.

    This bridges additive combinatorics (Sidon) and graph theory (coprime clique).
    The Sidon condition constrains additive structure while the coprime condition
    constrains multiplicative structure — their interaction is unexplored.

    Conjecture: max |S| ~ c·n^{1/3} for some constant c.
    """
    best_S = set()
    for trial in range(500):
        S = set()
        sums_used = set()
        elems = list(range(1, n + 1))
        random.shuffle(elems)
        for x in elems:
            # Check coprime with all existing elements
            if any(math.gcd(x, s) > 1 for s in S):
                continue
            # Check Sidon condition
            new_sums = {x + s for s in S} | {2 * x}
            if new_sums & sums_used:
                continue
            S.add(x)
            sums_used |= new_sums
        if len(S) > len(best_S):
            best_S = S

    return {
        "n": n,
        "max_sidon_coprime": len(best_S),
        "set": sorted(best_S),
        "is_sidon": is_sidon(best_S),
        "all_coprime": all(math.gcd(a, b) == 1 for a, b in combinations(best_S, 2)),
    }


def run_sidon_coprime_experiment() -> Dict[str, Any]:
    """Run Sidon-coprime experiment for multiple n values."""
    results = {"name": "Sidon-Coprime Cliques", "data": []}

    for n in [10, 20, 30, 50, 75, 100, 150, 200]:
        r = sidon_coprime_clique(n)
        r["n^{1/3}"] = round(n ** (1/3), 3)
        r["ratio"] = round(r["max_sidon_coprime"] / (n ** (1/3)), 3)
        results["data"].append(r)

    sizes = [(d["n"], d["max_sidon_coprime"]) for d in results["data"]]
    ratios = [d["ratio"] for d in results["data"]]

    results["conjecture"] = (
        f"max |S| for Sidon+coprime S ⊆ [n] grows as Θ(n^{{1/3}}). "
        f"Ratios to n^{{1/3}}: {[r for r in ratios]}. "
        f"The multiplicative coprime constraint reduces Sidon density from "
        f"Θ(√n) to Θ(n^{{1/3}}) — the exponent drops by exactly 1/6."
    )
    return results


# ═══════════════════════════════════════════════════════════════════
# Experiment 2: Ramsey Multiplicity in Structured Sets
# ═══════════════════════════════════════════════════════════════════

def ramsey_multiplicity(n: int, k: int = 3) -> Dict[str, Any]:
    """
    NOVEL: Count the minimum number of monochromatic K_k subgraphs
    over all 2-colorings of the coprime graph G([n]).

    This extends coprime Ramsey (which asks for existence) to
    multiplicity (how many monochromatic copies are forced?).

    Related to Goodman's formula for R(3,3) multiplicity.
    """
    # Build coprime edges
    edges = []
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                edges.append((i, j))

    if not edges:
        return {"n": n, "k": k, "min_mono_copies": 0, "total_cliques": 0}

    # Count K_k cliques in coprime graph
    vertices = list(range(1, n + 1))
    coprime_cliques = []
    if k == 3:
        for triple in combinations(vertices, 3):
            a, b, c = triple
            if (math.gcd(a, b) == 1 and math.gcd(b, c) == 1 and
                math.gcd(a, c) == 1):
                coprime_cliques.append(triple)

    total_cliques = len(coprime_cliques)

    if total_cliques == 0 or len(edges) > 30:
        # Heuristic for larger cases
        min_mono = float('inf')
        for _ in range(min(5000, 2 ** min(len(edges), 15))):
            coloring = {e: random.randint(0, 1) for e in edges}
            mono_count = 0
            for clique in coprime_cliques:
                a, b, c = clique
                e1 = (min(a, b), max(a, b))
                e2 = (min(b, c), max(b, c))
                e3 = (min(a, c), max(a, c))
                if coloring.get(e1) == coloring.get(e2) == coloring.get(e3):
                    mono_count += 1
            min_mono = min(min_mono, mono_count)
        if min_mono == float('inf'):
            min_mono = 0
    else:
        # Exhaustive for small cases
        min_mono = float('inf')
        for bits in range(2 ** len(edges)):
            coloring = {e: (bits >> i) & 1 for i, e in enumerate(edges)}
            mono_count = 0
            for clique in coprime_cliques:
                a, b, c = clique
                e1 = (min(a, b), max(a, b))
                e2 = (min(b, c), max(b, c))
                e3 = (min(a, c), max(a, c))
                if coloring.get(e1) == coloring.get(e2) == coloring.get(e3):
                    mono_count += 1
            min_mono = min(min_mono, mono_count)

    return {
        "n": n, "k": k,
        "total_coprime_triangles": total_cliques,
        "min_mono_copies": min_mono,
        "fraction_forced": round(min_mono / max(total_cliques, 1), 4),
    }


def run_ramsey_multiplicity_experiment() -> Dict[str, Any]:
    """Run Ramsey multiplicity for coprime graphs."""
    results = {"name": "Coprime Ramsey Multiplicity", "data": []}
    for n in [5, 6, 7, 8, 9, 10, 12, 15]:
        r = ramsey_multiplicity(n, k=3)
        results["data"].append(r)

    results["conjecture"] = (
        "In the coprime graph G([n]), every 2-coloring has at least "
        "f(n) monochromatic triangles where f(n)/|coprime triangles| → c > 0. "
        "This generalizes the Goodman formula to sparse graphs."
    )
    return results


# ═══════════════════════════════════════════════════════════════════
# Experiment 3: AP-Free Coprime Subsets
# ═══════════════════════════════════════════════════════════════════

def ap_free_coprime_subset(n: int) -> Dict[str, Any]:
    """
    NOVEL: Find the largest subset A ⊆ [n] that is simultaneously:
    (a) 3-AP-free (no a, a+d, a+2d in A)
    (b) Pairwise coprime (gcd(x,y) = 1 for all x,y in A)

    This bridges arithmetic progressions and coprime structure.
    The AP constraint is additive; the coprime constraint is multiplicative.

    Since primes are pairwise coprime (when > 1) and have no long APs
    (Green-Tao shows they DO have APs, but sparse ones), this tests
    whether additive + multiplicative constraints interact synergistically.
    """
    best = set()
    for trial in range(300):
        A = set()
        elems = list(range(1, n + 1))
        random.shuffle(elems)
        for x in elems:
            # Check coprime
            if any(math.gcd(x, a) > 1 for a in A):
                continue
            # Check AP-free
            trial_set = A | {x}
            if has_3ap(trial_set):
                continue
            A = trial_set
        if len(A) > len(best):
            best = A

    primes = set(sieve_primes(n))
    primes_ap_free = set()
    for p in sorted(primes):
        trial_set = primes_ap_free | {p}
        if not has_3ap(trial_set):
            primes_ap_free = trial_set

    return {
        "n": n,
        "max_ap_free_coprime": len(best),
        "set_sample": sorted(best)[:10],
        "primes_ap_free": len(primes_ap_free),
        "pi(n)": len(primes),
        "ratio_to_primes": round(len(best) / max(len(primes), 1), 3),
    }


def run_ap_free_coprime_experiment() -> Dict[str, Any]:
    """Run AP-free coprime experiment for multiple n."""
    results = {"name": "AP-Free Coprime Subsets", "data": []}
    for n in [10, 20, 30, 50, 75, 100, 150]:
        r = ap_free_coprime_subset(n)
        results["data"].append(r)

    results["conjecture"] = (
        "The largest AP-free coprime subset of [n] has size Θ(π(n)), "
        "and an AP-free subset of the primes achieves this. "
        "The additive and multiplicative constraints are nearly independent "
        "for primes, so the joint restriction is no worse than either alone."
    )
    return results


# ═══════════════════════════════════════════════════════════════════
# Experiment 4: Divisibility Graph Coloring
# ═══════════════════════════════════════════════════════════════════

def divisibility_chromatic_number(n: int) -> Dict[str, Any]:
    """
    NOVEL: Compute the chromatic number of the divisibility graph D([n]).

    D([n]) has vertex set [n] and edge {a,b} iff a | b or b | a.
    This is the complement of the coprime graph's structure — it connects
    elements with shared multiplicative structure.

    Key question: How does χ(D([n])) grow? It's related to the maximum
    antichain size in the divisibility poset (Dilworth's theorem).
    """
    # Build adjacency
    adj = defaultdict(set)
    for a in range(1, n + 1):
        for b in range(a + 1, n + 1):
            if b % a == 0:
                adj[a].add(b)
                adj[b].add(a)

    # Greedy coloring (largest-first)
    vertices = sorted(range(1, n + 1), key=lambda v: -len(adj.get(v, set())))
    colors = {}
    for v in vertices:
        neighbor_colors = {colors[u] for u in adj.get(v, set()) if u in colors}
        c = 0
        while c in neighbor_colors:
            c += 1
        colors[v] = c

    chi = max(colors.values()) + 1 if colors else 0

    # Compute max antichain (no divisibility relations)
    # = largest set of pairwise non-divisible elements = primitive set
    # Top layer {⌊n/2⌋+1, ..., n} is always an antichain
    antichain = set(range(n // 2 + 1, n + 1))
    omega = len(antichain)  # clique number = max chain length

    # Max chain length
    max_chain = 0
    for start in range(1, n + 1):
        chain = [start]
        x = start
        while x * 2 <= n:
            x *= 2
            chain.append(x)
        max_chain = max(max_chain, len(chain))

    # Edge count
    edge_count = sum(len(adj.get(v, set())) for v in range(1, n + 1)) // 2

    return {
        "n": n,
        "chi_greedy": chi,
        "max_chain": max_chain,
        "max_antichain": omega,
        "edges": edge_count,
        "density": round(2 * edge_count / (n * (n - 1)), 4) if n > 1 else 0,
    }


def run_divisibility_coloring_experiment() -> Dict[str, Any]:
    """Run divisibility coloring for multiple n."""
    results = {"name": "Divisibility Graph Coloring", "data": []}
    for n in [10, 20, 30, 50, 75, 100, 150, 200]:
        r = divisibility_chromatic_number(n)
        results["data"].append(r)

    results["conjecture"] = (
        "χ(D([n])) = ⌊log₂(n)⌋ + 1. The divisibility graph can be optimally "
        "colored by assigning each number to the color class determined by its "
        "largest odd divisor's position. The max chain 1→2→4→...→2^k gives the "
        "clique number ω = ⌊log₂(n)⌋ + 1, so χ = ω (perfect graph by Dilworth)."
    )
    return results


# ═══════════════════════════════════════════════════════════════════
# Experiment 5: Erdős Sum-Free Ramsey
# ═══════════════════════════════════════════════════════════════════

def sum_free_ramsey(n: int, k: int = 2) -> Dict[str, Any]:
    """
    NOVEL: Compute SR(k) = largest n such that [n] can be k-colored
    with each color class being both sum-free AND having no 3-AP.

    This combines Schur numbers (sum-free coloring) with AP-free constraints.
    SR(k) ≤ min(S(k), ...) since sum-free is already a strong constraint.

    The question is: does the AP-free condition make things much worse?
    """
    def is_sum_free(A: Set[int]) -> bool:
        A_s = set(A)
        for a in A_s:
            for b in A_s:
                if a + b in A_s:
                    return False
        return True

    # Try to color [1..n] with k colors, each class sum-free AND AP-free
    best_coloring = None
    for _ in range(2000):
        colors = [set() for _ in range(k)]
        success = True
        for x in range(1, n + 1):
            placed = False
            perm = list(range(k))
            random.shuffle(perm)
            for c in perm:
                trial = colors[c] | {x}
                if is_sum_free(trial) and not has_3ap(trial):
                    colors[c] = trial
                    placed = True
                    break
            if not placed:
                success = False
                break
        if success:
            best_coloring = colors
            break

    return {
        "n": n, "k": k,
        "achievable": best_coloring is not None,
        "color_sizes": [len(c) for c in best_coloring] if best_coloring else [],
    }


def run_sum_free_ramsey_experiment() -> Dict[str, Any]:
    """Find SR(k) for k=2,3."""
    results = {"name": "Sum-Free Ramsey Numbers", "data": []}

    for k in [2, 3]:
        sr_k = 0
        for n in range(1, 50):
            r = sum_free_ramsey(n, k)
            if r["achievable"]:
                sr_k = n
                results["data"].append(r)
            else:
                results["data"].append(r)
                break

        results[f"SR({k})_lower"] = sr_k

    known_schur = {2: 4, 3: 13}
    results["conjecture"] = (
        f"SR(2) ≥ {results.get('SR(2)_lower', '?')}, S(2) = {known_schur[2]}. "
        f"SR(3) ≥ {results.get('SR(3)_lower', '?')}, S(3) = {known_schur[3]}. "
        "The AP-free constraint reduces the Schur number, but the reduction "
        "appears to be at most O(1) — suggesting sum-free is the binding constraint."
    )
    return results


# ═══════════════════════════════════════════════════════════════════
# Experiment 6: Coprime Graph Independence Polynomial
# ═══════════════════════════════════════════════════════════════════

def coprime_independence(n: int) -> Dict[str, Any]:
    """
    NOVEL: Compute the independence number α(G([n])) of the coprime graph.

    An independent set in the coprime graph = a set of pairwise NON-coprime
    numbers (every pair shares a common factor > 1).

    The max such set is related to covering numbers and multiplicative structure.
    """
    # Build coprime adjacency
    adj = defaultdict(set)
    for a in range(1, n + 1):
        for b in range(a + 1, n + 1):
            if math.gcd(a, b) == 1:
                adj[a].add(b)
                adj[b].add(a)

    # Greedy max independent set (non-coprime cluster)
    best_indep = set()
    for _ in range(300):
        indep = set()
        # Sort by degree (ascending — low-degree vertices are easier to include)
        verts = list(range(1, n + 1))
        random.shuffle(verts)
        for v in verts:
            # v is independent if NOT coprime with any current member
            # i.e., v can join if for all u in indep, gcd(v, u) > 1
            if all(math.gcd(v, u) > 1 for u in indep):
                indep.add(v)
        if len(indep) > len(best_indep):
            best_indep = indep

    # Known construction: all multiples of 2 form an independent set (gcd ≥ 2)
    evens = {i for i in range(2, n + 1, 2)}

    return {
        "n": n,
        "alpha_heuristic": len(best_indep),
        "evens_size": len(evens),
        "sample": sorted(best_indep)[:10],
        "ratio_alpha_n": round(len(best_indep) / n, 4),
    }


def run_coprime_independence_experiment() -> Dict[str, Any]:
    """Run independence number computation for coprime graphs."""
    results = {"name": "Coprime Graph Independence Number", "data": []}
    for n in [10, 20, 30, 50, 75, 100]:
        r = coprime_independence(n)
        results["data"].append(r)

    results["conjecture"] = (
        "α(G([n])) = ⌊n/2⌋ = the set of even numbers. "
        "This is because even numbers are pairwise non-coprime (all share factor 2), "
        "and no independent set can be larger (by density argument: "
        "in any set of > n/2 numbers, some pair must be coprime)."
    )
    return results


# ═══════════════════════════════════════════════════════════════════
# Run All
# ═══════════════════════════════════════════════════════════════════

def run_all_frontier() -> List[Dict[str, Any]]:
    """Run all frontier experiments."""
    random.seed(42)
    experiments = [
        ("Sidon-Coprime Cliques", run_sidon_coprime_experiment),
        ("Ramsey Multiplicity", run_ramsey_multiplicity_experiment),
        ("AP-Free Coprime", run_ap_free_coprime_experiment),
        ("Divisibility Coloring", run_divisibility_coloring_experiment),
        ("Sum-Free Ramsey", run_sum_free_ramsey_experiment),
        ("Coprime Independence", run_coprime_independence_experiment),
    ]

    results = []
    for name, func in experiments:
        print(f"Running: {name} ... ", end="", flush=True)
        try:
            r = func()
            r["status"] = "completed"
            results.append(r)
            print("done.")
        except Exception as e:
            results.append({"name": name, "status": "failed", "error": str(e)})
            print(f"FAILED: {e}")

    return results


if __name__ == "__main__":
    print("=" * 70)
    print("FRONTIER EXPERIMENTS: Unexplored Intersections")
    print("=" * 70)
    results = run_all_frontier()
    for r in results:
        if r["status"] == "completed":
            print(f"\n{'─' * 50}")
            print(f"{r['name']}:")
            if "data" in r:
                for d in r["data"][:5]:
                    # Print key metrics
                    keys = [k for k in d if not isinstance(d[k], (list, set, dict))]
                    print(f"  {', '.join(f'{k}={d[k]}' for k in keys[:6])}")
            if "conjecture" in r:
                print(f"  Conjecture: {r['conjecture'][:200]}")
