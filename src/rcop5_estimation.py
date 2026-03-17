#!/usr/bin/env python3
"""
R_cop(5) Estimation — Pushing the frontier of coprime Ramsey numbers.

Known: R_cop(2)=2, R_cop(3)=11, R_cop(4)=59. All prime.
Prime indices: pi(2)=1, pi(11)=5, pi(59)=17.

Competing predictions for R_cop(5):
  - Quadratic index: pi(R_cop(k)) = 4k^2 - 8k + 5 => pi(R_cop(5))=37, R_cop(5)=p_37=157
  - Exponential index: pi(R_cop(k)) = 2*3^(k-1)-1 => pi(R_cop(5))=53, R_cop(5)=p_53=241
  - Ratio extrapolation: R_cop(5) ~ 59 * (59/11) ~ 316

Methods:
  1. SAT lower bound (pysat Glucose4 / CaDiCaL)
  2. Coprime 5-clique counting
  3. Extension-based upper bound
  4. Monte Carlo avoiding fraction estimation
  5. Phase transition analysis synthesizing all signals
"""

import math
import os
import random
import time
from itertools import combinations
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from pysat.solvers import Glucose4, Solver


# ============================================================================
# Constants and known values
# ============================================================================

KNOWN_RCOP = {2: 2, 3: 11, 4: 59}
COPRIME_DENSITY = 6.0 / (math.pi ** 2)  # ~0.6079

# Predictions
PRED_QUADRATIC = 157   # p_37 via 4k^2 - 8k + 5
PRED_EXPONENTIAL = 241  # p_53 via 2*3^(k-1) - 1
PRED_RATIO = 316        # 59 * (59/11)


# ============================================================================
# Graph infrastructure (optimized for large n)
# ============================================================================

def coprime_adj_sets(n: int) -> Dict[int, Set[int]]:
    """Build adjacency sets for the coprime graph on [n], using sieve."""
    adj: Dict[int, Set[int]] = {v: set() for v in range(1, n + 1)}
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def coprime_edge_list(n: int) -> List[Tuple[int, int]]:
    """All coprime pairs (i,j) with 1 <= i < j <= n."""
    edges = []
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                edges.append((i, j))
    return edges


def coprime_edge_count(n: int) -> int:
    """Count coprime pairs without storing them."""
    count = 0
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                count += 1
    return count


# ============================================================================
# 5-clique enumeration (incremental)
# ============================================================================

def enumerate_5cliques_containing(v: int, adj: Dict[int, Set[int]]) -> List[Tuple[int, ...]]:
    """
    Find all 5-cliques containing vertex v, where all other members are < v.

    This is for incremental enumeration: when adding vertex v to the graph,
    these are exactly the NEW 5-cliques.
    """
    neighbors = sorted([u for u in adj.get(v, set()) if u < v])
    cliques = []

    # Need 4 vertices from neighbors that are mutually coprime
    def extend(current: List[int], candidates: List[int]):
        if len(current) == 4:
            cliques.append(tuple(sorted(current + [v])))
            return
        needed = 4 - len(current)
        for idx, w in enumerate(candidates):
            if len(candidates) - idx < needed:
                break
            if all(w in adj[u] for u in current):
                new_cands = [x for x in candidates[idx + 1:] if x in adj[w]]
                extend(current + [w], new_cands)

    extend([], neighbors)
    return cliques


def count_5cliques_up_to(n: int) -> Tuple[int, Dict[int, Set[int]]]:
    """
    Count total 5-cliques in coprime graph on [n], building incrementally.

    Returns (total_count, adjacency_dict).
    """
    adj: Dict[int, Set[int]] = {}
    total = 0

    for v in range(1, n + 1):
        adj[v] = set()
        for u in range(1, v):
            if math.gcd(u, v) == 1:
                adj[v].add(u)
                adj[u].add(v)

        if v >= 5:
            new = enumerate_5cliques_containing(v, adj)
            total += len(new)

    return total, adj


# ============================================================================
# 1. SAT lower bound (incremental, with timing)
# ============================================================================

def sat_lower_bound(
    max_n: int = 120,
    timeout_per_n: float = 60.0,
    verbose: bool = True,
    solver_name: str = 'glucose4',
) -> Dict:
    """
    Push R_cop(5) lower bound using incremental SAT.

    At each n, encode "exists a 2-coloring of coprime edges on [n] avoiding
    monochromatic K_5" and solve. SAT means R_cop(5) > n.

    The encoding forbids monochromatic 5-cliques: for each 5-clique C with
    edges e1..e10, add clauses:
      - NOT(all color 0): at least one e_i is True
      - NOT(all color 1): at least one e_i is False

    Uses fresh solver at each n (avoids learned-clause bloat).
    """
    k = 5
    adj: Dict[int, Set[int]] = {}
    all_cliques: List[Tuple[int, ...]] = []
    scan_data = []
    best_lower = k - 1

    if verbose:
        print(f"{'n':>4s}  {'edges':>6s}  {'5-clqs':>8s}  {'clauses':>8s}  "
              f"{'result':>7s}  {'time':>8s}")
        print("-" * 52)

    t_total_start = time.time()

    # Seed vertex 1
    adj[1] = set()

    for n in range(2, max_n + 1):
        # Build adjacency incrementally
        adj[n] = set()
        for u in range(1, n):
            if math.gcd(u, n) == 1:
                adj[n].add(u)
                adj[u].add(n)

        if n < k:
            continue

        # Find new 5-cliques containing n
        new_cliques = enumerate_5cliques_containing(n, adj)
        all_cliques.extend(new_cliques)

        # Build edge-to-var mapping for [n]
        edge_to_var: Dict[Tuple[int, int], int] = {}
        nv = 1
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                if j in adj.get(i, set()):
                    edge_to_var[(i, j)] = nv
                    nv += 1
        num_vars = nv - 1

        # Build clause list
        clause_list: List[List[int]] = []
        # Symmetry breaking: fix edge (1,2) to color 0
        if (1, 2) in edge_to_var:
            clause_list.append([edge_to_var[(1, 2)]])

        for clique in all_cliques:
            vlist = sorted(clique)
            vars_ = []
            for i in range(len(vlist)):
                for j in range(i + 1, len(vlist)):
                    e = (vlist[i], vlist[j])
                    if e in edge_to_var:
                        vars_.append(edge_to_var[e])
            if len(vars_) == 10:  # C(5,2) = 10
                clause_list.append([-v for v in vars_])
                clause_list.append([v for v in vars_])

        num_clauses = len(clause_list)

        # Solve
        t0 = time.time()
        try:
            solver = Solver(name='cadical195', bootstrap_with=clause_list)
        except Exception:
            solver = Glucose4(bootstrap_with=clause_list)
        sat = solver.solve()
        solver.delete()
        dt = time.time() - t0

        status = "SAT" if sat else "UNSAT"

        record = {
            'n': n, 'edges': num_vars, 'cliques_5': len(all_cliques),
            'clauses': num_clauses, 'sat': sat, 'time': dt,
            'new_cliques': len(new_cliques),
        }
        scan_data.append(record)

        # Print selectively: every n up to 30, then every 5, or on event
        if verbose and (n <= 30 or n % 5 == 0 or not sat or dt > 1.0):
            print(f"{n:4d}  {num_vars:6d}  {len(all_cliques):8d}  "
                  f"{num_clauses:8d}  {status:>7s}  {dt:7.3f}s")

        if not sat:
            t_total = time.time() - t_total_start
            if verbose:
                print(f"\n  R_cop(5) = {n}  [total: {t_total:.1f}s]")
            return {
                'result': 'exact',
                'rcop5': n,
                'lower_bound': n - 1,
                'upper_bound': n,
                'total_time': t_total,
                'scan_data': scan_data,
            }

        best_lower = n

        if dt > timeout_per_n:
            t_total = time.time() - t_total_start
            if verbose:
                print(f"\n  Timeout at n={n} ({dt:.1f}s > {timeout_per_n}s)")
                print(f"  Best lower bound: R_cop(5) > {best_lower}")
            return {
                'result': 'lower_bound',
                'lower_bound': best_lower,
                'total_time': t_total,
                'scan_data': scan_data,
                'timeout_n': n,
            }

    t_total = time.time() - t_total_start
    if verbose:
        print(f"\n  Scanned to n={max_n}. R_cop(5) > {best_lower}")
        print(f"  Total time: {t_total:.1f}s")

    return {
        'result': 'lower_bound',
        'lower_bound': best_lower,
        'total_time': t_total,
        'scan_data': scan_data,
    }


# ============================================================================
# 2. Clique counting heuristic
# ============================================================================

def clique_counting_analysis(max_n: int = 200, verbose: bool = True) -> Dict:
    """
    Count coprime 5-cliques at each n. The growth rate indicates where SAT
    becomes hard (phase transition onset).

    The key insight: near R_cop(k), the number of k-cliques is large enough
    that the pigeonhole argument forces monochromatic copies. The transition
    from "many avoiding colorings" to "none" is sharp and coincides with
    rapid clique-count growth.

    We also compute the clique-to-edge ratio: when C(5) / |E| exceeds a
    threshold, the constraint density forces UNSAT.
    """
    adj: Dict[int, Set[int]] = {1: set()}
    cumulative_5cliques = 0
    data = []

    if verbose:
        print(f"{'n':>4s}  {'edges':>6s}  {'5-clqs':>10s}  "
              f"{'new_5clqs':>10s}  {'clqs/edge':>10s}")
        print("-" * 50)

    for n in range(2, max_n + 1):
        adj[n] = set()
        for u in range(1, n):
            if math.gcd(u, n) == 1:
                adj[n].add(u)
                adj[u].add(n)

        if n < 5:
            continue

        new_cliques = enumerate_5cliques_containing(n, adj)
        cumulative_5cliques += len(new_cliques)

        # Count edges
        num_edges = sum(len(adj[v]) for v in range(1, n + 1)) // 2

        ratio = cumulative_5cliques / max(num_edges, 1)

        record = {
            'n': n, 'edges': num_edges, 'total_5cliques': cumulative_5cliques,
            'new_5cliques': len(new_cliques), 'clique_edge_ratio': ratio,
        }
        data.append(record)

        if verbose and (n <= 30 or n % 10 == 0):
            print(f"{n:4d}  {num_edges:6d}  {cumulative_5cliques:10d}  "
                  f"{len(new_cliques):10d}  {ratio:10.2f}")

    # Analyze growth rate
    ns = np.array([d['n'] for d in data])
    clqs = np.array([d['total_5cliques'] for d in data], dtype=float)

    # Fit log(cliques) ~ a*log(n) + b to estimate polynomial growth exponent
    mask = clqs > 0
    if mask.sum() > 2:
        log_n = np.log(ns[mask])
        log_c = np.log(clqs[mask])
        # Linear fit in log-log space
        coeffs = np.polyfit(log_n, log_c, 1)
        growth_exponent = coeffs[0]
    else:
        growth_exponent = None

    # Estimate constraint density at predicted R_cop(5) values
    predictions = {}
    for name, pred_n in [('quadratic', PRED_QUADRATIC),
                         ('exponential', PRED_EXPONENTIAL),
                         ('ratio', PRED_RATIO)]:
        # Extrapolate 5-clique count at pred_n
        # C_5(n) ~ (6/pi^2)^10 * C(n,5) for large n
        d10 = COPRIME_DENSITY ** 10
        est_cliques = math.comb(pred_n, 5) * d10
        est_edges = int(COPRIME_DENSITY * pred_n * (pred_n - 1) / 2)
        est_ratio = est_cliques / max(est_edges, 1)
        predictions[name] = {
            'n': pred_n,
            'est_5cliques': int(est_cliques),
            'est_edges': est_edges,
            'est_clique_edge_ratio': est_ratio,
        }

    if verbose:
        print(f"\n  Growth exponent (log-log fit): {growth_exponent:.2f}")
        print(f"  Expected for coprime 5-cliques: ~5 (since C(n,5) ~ n^5)")
        print()
        for name, p in predictions.items():
            print(f"  At {name} prediction n={p['n']}:")
            print(f"    est 5-cliques: {p['est_5cliques']:,}")
            print(f"    est edges: {p['est_edges']:,}")
            print(f"    clique/edge ratio: {p['est_clique_edge_ratio']:.1f}")

    return {
        'data': data,
        'growth_exponent': growth_exponent,
        'predictions': predictions,
    }


# ============================================================================
# 3. Extension-based upper bound
# ============================================================================

def extension_upper_bound(
    start_n: int,
    max_n: int = 200,
    num_samples: int = 500,
    timeout_per_n: float = 60.0,
    verbose: bool = True,
) -> Dict:
    """
    Extension method: at each n, sample avoiding colorings at n via SAT,
    then check if any extend to n+1. When no extensions exist, R_cop(5) <= n+1.

    This is practical only once we have a good lower bound (start_n).
    For each n:
      1. Find an avoiding coloring at n (via SAT).
      2. Fix those edge colors, add new edges to n+1.
      3. Check if new-edge assignment can avoid all new 5-cliques.
      4. If no sample extends, declare R_cop(5) <= n+1 (heuristic).
    """
    k = 5
    results = []

    adj: Dict[int, Set[int]] = {}
    all_cliques: List[Tuple[int, ...]] = []

    # Build graph up to start_n
    for v in range(1, start_n + 1):
        adj[v] = set()
        for u in range(1, v):
            if math.gcd(u, v) == 1:
                adj[v].add(u)
                adj[u].add(v)
        if v >= k:
            new_c = enumerate_5cliques_containing(v, adj)
            all_cliques.extend(new_c)

    if verbose:
        print(f"  Extension method: starting from n={start_n}")
        print(f"  Graph has {len(all_cliques)} 5-cliques at n={start_n}")

    for n in range(start_n, max_n):
        n_next = n + 1
        t0 = time.time()

        # Extend adjacency to n_next
        adj[n_next] = set()
        for u in range(1, n_next):
            if math.gcd(u, n_next) == 1:
                adj[n_next].add(u)
                adj[u].add(n_next)

        # New 5-cliques at n_next
        new_cliques = enumerate_5cliques_containing(n_next, adj)
        all_cliques.extend(new_cliques)

        # New edges from n_next to [1..n]
        new_edges = [(min(u, n_next), max(u, n_next))
                     for u in range(1, n_next) if math.gcd(u, n_next) == 1]
        num_new_edges = len(new_edges)

        if num_new_edges == 0:
            results.append({'n': n_next, 'extends': True, 'time': 0,
                            'new_edges': 0, 'new_cliques': 0})
            continue

        # Build full SAT instance at n
        edge_to_var_n: Dict[Tuple[int, int], int] = {}
        nv = 1
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                if j in adj.get(i, set()):
                    edge_to_var_n[(i, j)] = nv
                    nv += 1

        # Cliques that only involve [1..n]
        cliques_n = [c for c in all_cliques if max(c) <= n]

        clauses_n: List[List[int]] = []
        if (1, 2) in edge_to_var_n:
            clauses_n.append([edge_to_var_n[(1, 2)]])
        for clique in cliques_n:
            vlist = sorted(clique)
            vars_ = []
            for i in range(len(vlist)):
                for j in range(i + 1, len(vlist)):
                    e = (vlist[i], vlist[j])
                    if e in edge_to_var_n:
                        vars_.append(edge_to_var_n[e])
            if len(vars_) == 10:
                clauses_n.append([-v for v in vars_])
                clauses_n.append([v for v in vars_])

        # Build full SAT instance at n_next
        edge_to_var_full: Dict[Tuple[int, int], int] = {}
        nv_full = 1
        for i in range(1, n_next + 1):
            for j in range(i + 1, n_next + 1):
                if j in adj.get(i, set()):
                    edge_to_var_full[(i, j)] = nv_full
                    nv_full += 1

        clauses_full: List[List[int]] = []
        if (1, 2) in edge_to_var_full:
            clauses_full.append([edge_to_var_full[(1, 2)]])
        for clique in all_cliques:
            if max(clique) <= n_next:
                vlist = sorted(clique)
                vars_ = []
                for i in range(len(vlist)):
                    for j in range(i + 1, len(vlist)):
                        e = (vlist[i], vlist[j])
                        if e in edge_to_var_full:
                            vars_.append(edge_to_var_full[e])
                if len(vars_) == 10:
                    clauses_full.append([-v for v in vars_])
                    clauses_full.append([v for v in vars_])

        # Sample avoiding colorings at n, try to extend each
        try:
            solver_n = Solver(name='cadical195', bootstrap_with=clauses_n)
        except Exception:
            solver_n = Glucose4(bootstrap_with=clauses_n)

        try:
            solver_full = Solver(name='cadical195', bootstrap_with=clauses_full)
        except Exception:
            solver_full = Glucose4(bootstrap_with=clauses_full)

        found_extension = False
        samples_checked = 0

        for _ in range(num_samples):
            if time.time() - t0 > timeout_per_n:
                break

            if not solver_n.solve():
                break  # No more avoiding colorings at n

            model = solver_n.get_model()
            model_set = set(model)
            samples_checked += 1

            # Fix base edges in full solver
            assumptions = []
            for edge, var_n in edge_to_var_n.items():
                if edge in edge_to_var_full:
                    var_full = edge_to_var_full[edge]
                    if var_n in model_set:
                        assumptions.append(var_full)
                    else:
                        assumptions.append(-var_full)

            sat_ext = solver_full.solve(assumptions=assumptions)
            if sat_ext:
                found_extension = True
                solver_n.delete()
                solver_full.delete()
                break

            # Block this coloring
            num_vars_n = len(edge_to_var_n)
            solver_n.add_clause([-lit for lit in model[:num_vars_n]])

        else:
            solver_n.delete()
            solver_full.delete()

        dt = time.time() - t0
        results.append({
            'n': n_next, 'extends': found_extension,
            'samples_checked': samples_checked,
            'new_edges': num_new_edges, 'new_cliques': len(new_cliques),
            'time': dt,
        })

        if verbose:
            ext_str = "EXTENDS" if found_extension else "BLOCKED"
            print(f"  n={n_next:4d}: {ext_str} ({samples_checked} samples, "
                  f"{num_new_edges} new edges, {len(new_cliques)} new 5-clqs, "
                  f"{dt:.1f}s)")

        if not found_extension:
            if verbose:
                print(f"\n  Extension blocked at n={n_next}.")
                print(f"  Heuristic upper bound: R_cop(5) <= {n_next}")
            return {
                'upper_bound': n_next,
                'results': results,
                'samples_per_n': num_samples,
            }

    return {
        'upper_bound': None,
        'results': results,
        'note': f'All n up to {max_n} had extensions',
    }


# ============================================================================
# 4. Monte Carlo avoiding fraction estimation
# ============================================================================

def monte_carlo_avoiding_fraction(
    ns: List[int],
    num_samples: int = 10000,
    clique_enum_limit: int = 80,
    verbose: bool = True,
) -> Dict:
    """
    At each n, estimate the fraction of random 2-colorings that avoid
    monochromatic K_5.

    Two-tier approach:
      - n <= clique_enum_limit: enumerate all 5-cliques, sample colorings,
        check exhaustively (exact MC).
      - n > clique_enum_limit: for each random coloring, sample random
        coprime 5-tuples and check if any are monochromatic (stochastic MC).
        This is an UPPER bound on the avoiding fraction.

    Near the transition, this fraction drops from O(1) to nearly 0.
    """
    results = []

    if verbose:
        print(f"{'n':>4s}  {'edges':>6s}  {'5-clqs':>8s}  "
              f"{'samples':>7s}  {'avoiding':>8s}  {'fraction':>12s}  {'method':>8s}")
        print("-" * 70)

    for n in ns:
        # Build coprime graph
        adj: Dict[int, Set[int]] = {}
        edges = []
        for v in range(1, n + 1):
            adj[v] = set()
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                if math.gcd(i, j) == 1:
                    adj[i].add(j)
                    adj[j].add(i)
                    edges.append((i, j))

        num_edges = len(edges)
        if num_edges == 0:
            continue

        edge_index = {e: i for i, e in enumerate(edges)}

        if n <= clique_enum_limit:
            # Tier 1: enumerate all 5-cliques
            cliques: List[Tuple[int, ...]] = []
            vertices = list(range(1, n + 1))

            def find_cliques(current: List[int], candidates: List[int]):
                if len(current) == 5:
                    cliques.append(tuple(current))
                    return
                needed = 5 - len(current)
                for idx, v in enumerate(candidates):
                    if len(candidates) - idx < needed:
                        break
                    if all(v in adj[u] for u in current):
                        new_cands = [w for w in candidates[idx + 1:] if w in adj[v]]
                        find_cliques(current + [v], new_cands)

            find_cliques([], vertices)
            num_cliques = len(cliques)

            if not cliques:
                results.append({'n': n, 'edges': num_edges, 'cliques': 0,
                                'avoiding': num_samples, 'fraction': 1.0,
                                'method': 'exact'})
                if verbose:
                    print(f"{n:4d}  {num_edges:6d}  {0:8d}  "
                          f"{num_samples:7d}  {num_samples:8d}  {1.0:12.6e}  {'exact':>8s}")
                continue

            # Pre-compute clique edge indices
            clique_edge_indices = []
            for clique in cliques:
                vlist = sorted(clique)
                indices = []
                for a in range(5):
                    for b in range(a + 1, 5):
                        e = (vlist[a], vlist[b])
                        indices.append(edge_index[e])
                clique_edge_indices.append(indices)

            # Sample random colorings
            avoiding_count = 0
            for _ in range(num_samples):
                coloring = np.random.randint(0, 2, size=num_edges)
                has_mono = False
                for idx_list in clique_edge_indices:
                    colors = coloring[idx_list]
                    if np.all(colors == 0) or np.all(colors == 1):
                        has_mono = True
                        break
                if not has_mono:
                    avoiding_count += 1

            fraction = avoiding_count / num_samples
            method = 'exact'

        else:
            # Tier 2: sample random coprime 5-tuples
            # For each coloring, we sample random 5-cliques and check.
            # If the graph has C_5 5-cliques, and we sample S of them,
            # then each coloring has probability (1-2/2^10)^C_5 of avoiding.
            # We sample enough 5-tuples to detect with good probability.

            # Pre-build list of primes <= n (they form a clique with 1)
            primes = [p for p in range(2, n + 1)
                      if all(p % d != 0 for d in range(2, int(p**0.5) + 1))]
            vertices = list(range(1, n + 1))

            # Sample coprime 5-cliques by starting from random subsets
            num_checks_per_coloring = min(10000, max(1000, n * 20))
            num_cliques = -1  # unknown

            avoiding_count = 0
            for _ in range(num_samples):
                coloring = np.random.randint(0, 2, size=num_edges)
                has_mono = False

                for _ in range(num_checks_per_coloring):
                    # Sample a random 5-tuple
                    sample = random.sample(vertices, 5)
                    sample.sort()

                    # Check if pairwise coprime
                    all_coprime = True
                    for a in range(5):
                        for b in range(a + 1, 5):
                            if math.gcd(sample[a], sample[b]) != 1:
                                all_coprime = False
                                break
                        if not all_coprime:
                            break

                    if not all_coprime:
                        continue

                    # Check if monochromatic
                    colors = set()
                    for a in range(5):
                        for b in range(a + 1, 5):
                            e = (sample[a], sample[b])
                            colors.add(coloring[edge_index[e]])
                            if len(colors) > 1:
                                break
                        if len(colors) > 1:
                            break

                    if len(colors) == 1:
                        has_mono = True
                        break

                if not has_mono:
                    avoiding_count += 1

            fraction = avoiding_count / num_samples
            method = 'sampled'

        results.append({
            'n': n, 'edges': num_edges, 'cliques': num_cliques,
            'avoiding': avoiding_count, 'fraction': fraction,
            'method': method,
        })

        if verbose:
            clq_str = f"{num_cliques:8d}" if num_cliques >= 0 else "   ~est."
            print(f"{n:4d}  {num_edges:6d}  {clq_str}  "
                  f"{num_samples:7d}  {avoiding_count:8d}  {fraction:12.6e}  {method:>8s}")

    return {'data': results}


# ============================================================================
# 5. Phase transition analysis
# ============================================================================

def phase_transition_analysis(
    sat_data: Optional[List[Dict]] = None,
    clique_data: Optional[List[Dict]] = None,
    mc_data: Optional[List[Dict]] = None,
    verbose: bool = True,
) -> Dict:
    """
    Synthesize SAT timing, clique counts, and Monte Carlo data to locate
    the phase transition for R_cop(5).

    The transition is where:
      - SAT time spikes (exponential blowup)
      - Clique constraint density crosses a threshold
      - Avoiding fraction drops to ~0

    Returns estimated R_cop(5) range and evidence summary.
    """
    analysis = {}

    # Analyze SAT timing curve
    if sat_data:
        sat_ns = [d['n'] for d in sat_data]
        sat_times = [d['time'] for d in sat_data]
        sat_results = [d['sat'] for d in sat_data]

        # Find where time starts growing fast
        # Look for first n where time > 1s
        slow_ns = [d['n'] for d in sat_data if d['time'] > 1.0]
        analysis['sat_slow_start'] = min(slow_ns) if slow_ns else None

        # Best lower bound from SAT
        sat_lower = max(d['n'] for d in sat_data if d['sat'])
        analysis['sat_lower_bound'] = sat_lower

        # Extrapolate: fit log(time) vs n for the SAT region
        sat_mask = np.array([d['sat'] for d in sat_data])
        if sat_mask.sum() > 5:
            ns_arr = np.array([d['n'] for d in sat_data])[sat_mask]
            times_arr = np.array([d['time'] for d in sat_data])[sat_mask]
            pos = times_arr > 0
            if pos.sum() > 3:
                log_times = np.log(times_arr[pos] + 1e-10)
                # Fit log(time) ~ a*n + b
                try:
                    coeffs = np.polyfit(ns_arr[pos].astype(float), log_times, 1)
                    # Extrapolate: at what n does time hit 1 hour?
                    target_log_time = np.log(3600)
                    if coeffs[0] > 0:
                        n_1hour = (target_log_time - coeffs[1]) / coeffs[0]
                        analysis['sat_extrapolated_1hour'] = float(n_1hour)
                except (np.linalg.LinAlgError, ValueError):
                    pass

    # Analyze clique density
    if clique_data:
        # At known R_cop values, what is the clique/edge ratio?
        # R_cop(3)=11: triangles vs edges
        # R_cop(4)=59: 4-cliques vs edges
        # For k=5, the critical ratio should be comparable

        clique_ns = [d['n'] for d in clique_data]
        clique_ratios = [d['clique_edge_ratio'] for d in clique_data]
        analysis['max_clique_ratio_computed'] = max(clique_ratios) if clique_ratios else 0

    # Analyze Monte Carlo
    if mc_data:
        # Find transition: where avoiding fraction drops below threshold
        mc_ns = [d['n'] for d in mc_data]
        mc_fracs = [d['fraction'] for d in mc_data]

        # Find first n where fraction < 0.5
        half_ns = [d['n'] for d in mc_data if d['fraction'] < 0.5]
        analysis['mc_half_transition'] = min(half_ns) if half_ns else None

        # Find first n where fraction = 0 in samples
        zero_ns = [d['n'] for d in mc_data if d['fraction'] == 0]
        analysis['mc_zero_transition'] = min(zero_ns) if zero_ns else None

        # Fit logistic to estimate transition center
        if len(mc_fracs) > 3:
            ns_arr = np.array(mc_ns, dtype=float)
            fracs_arr = np.array(mc_fracs, dtype=float)
            # Simple: find where fraction crosses 0.01
            cross_01 = [d['n'] for d in mc_data if d['fraction'] < 0.01]
            analysis['mc_001_transition'] = min(cross_01) if cross_01 else None

    # Synthesize: combine all evidence
    evidence_points = []
    if 'sat_lower_bound' in analysis:
        evidence_points.append(('SAT lower bound', analysis['sat_lower_bound']))
    if 'sat_extrapolated_1hour' in analysis:
        evidence_points.append(('SAT 1-hour extrapolation', analysis['sat_extrapolated_1hour']))
    if 'mc_half_transition' in analysis:
        evidence_points.append(('MC 50% transition', analysis['mc_half_transition']))
    if 'mc_zero_transition' in analysis:
        evidence_points.append(('MC 0% transition', analysis['mc_zero_transition']))

    analysis['evidence_points'] = evidence_points

    # Compare with predictions
    analysis['predictions'] = {
        'quadratic (p_37)': PRED_QUADRATIC,
        'exponential (p_53)': PRED_EXPONENTIAL,
        'ratio extrapolation': PRED_RATIO,
    }

    if verbose:
        print("\n  Phase Transition Evidence:")
        for name, val in evidence_points:
            print(f"    {name}: n ~ {val:.0f}" if isinstance(val, float)
                  else f"    {name}: n = {val}")
        print()
        print("  Predictions:")
        for name, val in analysis['predictions'].items():
            print(f"    {name}: {val}")

    return analysis


# ============================================================================
# 6. Full report
# ============================================================================

def generate_report(
    sat_result: Dict,
    clique_result: Dict,
    mc_result: Dict,
    phase_result: Dict,
    extension_result: Optional[Dict] = None,
    verbose: bool = True,
) -> str:
    """
    Generate a comprehensive report on R_cop(5) estimation.
    """
    lines = []
    lines.append("=" * 72)
    lines.append("R_cop(5) ESTIMATION REPORT")
    lines.append("=" * 72)
    lines.append("")

    # Known values
    lines.append("Known values:")
    lines.append("  R_cop(2) = 2 = p_1")
    lines.append("  R_cop(3) = 11 = p_5")
    lines.append("  R_cop(4) = 59 = p_17")
    lines.append(f"  Coprime graph density: 6/pi^2 ~ {COPRIME_DENSITY:.4f}")
    lines.append("")

    # Competing predictions
    lines.append("Competing predictions:")
    lines.append(f"  Quadratic index:  4k^2 - 8k + 5 => pi(R_cop(5))=37, R_cop(5) = p_37 = {PRED_QUADRATIC}")
    lines.append(f"  Exponential index: 2*3^(k-1)-1 => pi(R_cop(5))=53, R_cop(5) = p_53 = {PRED_EXPONENTIAL}")
    lines.append(f"  Ratio extrapolation: 59 * (59/11) ~ {PRED_RATIO}")
    lines.append("")

    # SAT results
    lines.append("-" * 72)
    lines.append("1. SAT LOWER BOUND")
    lines.append("-" * 72)
    if sat_result.get('result') == 'exact':
        lines.append(f"  EXACT: R_cop(5) = {sat_result['rcop5']}")
    else:
        lb = sat_result.get('lower_bound', '?')
        lines.append(f"  Best lower bound: R_cop(5) > {lb}")
        if 'timeout_n' in sat_result:
            lines.append(f"  Timeout at n={sat_result['timeout_n']}")
        lines.append(f"  Total SAT time: {sat_result.get('total_time', 0):.1f}s")

        # SAT timing trend
        scan = sat_result.get('scan_data', [])
        if scan:
            last_few = [d for d in scan[-5:] if d['sat']]
            if last_few:
                lines.append("  Last SAT timings:")
                for d in last_few:
                    lines.append(f"    n={d['n']}: {d['time']:.3f}s "
                                 f"({d['edges']} edges, {d['cliques_5']} 5-clqs)")
    lines.append("")

    # Clique counting
    lines.append("-" * 72)
    lines.append("2. CLIQUE COUNTING HEURISTIC")
    lines.append("-" * 72)
    if clique_result.get('growth_exponent') is not None:
        lines.append(f"  5-clique growth exponent: {clique_result['growth_exponent']:.2f}")
        lines.append(f"  (Expected: ~5 for C(n,5) * density^10)")
    for name, p in clique_result.get('predictions', {}).items():
        lines.append(f"  At {name} prediction n={p['n']}:")
        lines.append(f"    est 5-cliques: {p['est_5cliques']:,}")
        lines.append(f"    est constraint density (clqs/edge): {p['est_clique_edge_ratio']:.1f}")
    lines.append("")

    # Extension
    if extension_result:
        lines.append("-" * 72)
        lines.append("3. EXTENSION UPPER BOUND")
        lines.append("-" * 72)
        ub = extension_result.get('upper_bound')
        if ub:
            lines.append(f"  Extension blocked at n={ub}")
            lines.append(f"  Heuristic upper bound: R_cop(5) <= {ub}")
        else:
            lines.append(f"  Extensions found at all tested n")
        lines.append("")

    # Monte Carlo
    lines.append("-" * 72)
    lines.append("4. MONTE CARLO ESTIMATION")
    lines.append("-" * 72)
    mc_data = mc_result.get('data', [])
    for d in mc_data:
        if d['fraction'] < 1.0 or d['n'] <= 30:
            lines.append(f"  n={d['n']:4d}: avoiding = {d['fraction']:.6e} "
                         f"({d['avoiding']}/{d.get('cliques', '?')} cliques)")
    lines.append("")

    # Phase transition
    lines.append("-" * 72)
    lines.append("5. PHASE TRANSITION ANALYSIS")
    lines.append("-" * 72)
    for name, val in phase_result.get('evidence_points', []):
        if isinstance(val, float):
            lines.append(f"  {name}: n ~ {val:.0f}")
        else:
            lines.append(f"  {name}: n = {val}")
    lines.append("")

    # Timing extrapolation
    timing_ext = phase_result.get('timing_extrapolation', {})
    if timing_ext:
        lines.append("-" * 72)
        lines.append("5b. SAT TIMING EXTRAPOLATION")
        lines.append("-" * 72)
        if 'doubling_interval' in timing_ext:
            lines.append(f"  SAT time doubles every {timing_ext['doubling_interval']:.1f} n-steps")
        for name, n_val in timing_ext.get('extrapolations', {}).items():
            lines.append(f"  Solving takes {name} at n ~ {n_val:.0f}")
        for name, t in timing_ext.get('prediction_times', {}).items():
            n_vals = {'quadratic': PRED_QUADRATIC, 'exponential': PRED_EXPONENTIAL,
                      'ratio': PRED_RATIO}
            n_v = n_vals.get(name, '?')
            if t < 3600:
                lines.append(f"  At {name} (n={n_v}): est. SAT time ~ {t:.0f}s")
            elif t < 86400:
                lines.append(f"  At {name} (n={n_v}): est. SAT time ~ {t/3600:.0f}h")
            else:
                lines.append(f"  At {name} (n={n_v}): est. SAT time ~ {t/86400:.0f} days")
        lines.append("")

    # Verdict
    lines.append("=" * 72)
    lines.append("VERDICT")
    lines.append("=" * 72)

    lb = sat_result.get('lower_bound', 0)
    if sat_result.get('result') == 'exact':
        rcop5 = sat_result['rcop5']
        lines.append(f"  R_cop(5) = {rcop5} (EXACT)")
        if rcop5 == PRED_QUADRATIC:
            lines.append(f"  MATCHES quadratic index formula: 4k^2 - 8k + 5")
        elif rcop5 == PRED_EXPONENTIAL:
            lines.append(f"  MATCHES exponential index formula: 2*3^(k-1) - 1")
        else:
            lines.append(f"  Does NOT match either predicted value ({PRED_QUADRATIC}, {PRED_EXPONENTIAL})")
    else:
        lines.append(f"  Best lower bound: R_cop(5) > {lb}")

        # Which prediction is more consistent?
        if lb >= PRED_QUADRATIC:
            lines.append(f"  RULES OUT quadratic prediction ({PRED_QUADRATIC})")
            if lb < PRED_EXPONENTIAL:
                lines.append(f"  Exponential prediction ({PRED_EXPONENTIAL}) still viable")
            elif lb >= PRED_EXPONENTIAL:
                lines.append(f"  RULES OUT exponential prediction ({PRED_EXPONENTIAL})")
                lines.append(f"  Ratio extrapolation ({PRED_RATIO}) or higher")
        else:
            lines.append(f"  Both predictions still viable (lb < {PRED_QUADRATIC})")

        # Use timing extrapolation
        ext_1day = timing_ext.get('extrapolations', {}).get('1 day')
        ext_1h = phase_result.get('sat_extrapolated_1hour')
        ref_n = ext_1day or ext_1h
        if ref_n:
            lines.append(f"  SAT timing extrapolation suggests solving becomes intractable near n ~ {ref_n:.0f}")
            if ref_n and abs(ref_n - PRED_QUADRATIC) < abs(ref_n - PRED_EXPONENTIAL):
                lines.append(f"  This is closest to the QUADRATIC prediction ({PRED_QUADRATIC})")
                lines.append(f"  The quadratic formula (4k^2 - 8k + 5 for the prime index)")
                lines.append(f"  is the most computationally consistent prediction")
            elif ref_n:
                lines.append(f"  This is closest to the EXPONENTIAL prediction ({PRED_EXPONENTIAL})")

        # Monte Carlo evidence
        mc_half = phase_result.get('mc_half_transition')
        mc_zero = phase_result.get('mc_zero_transition')
        if mc_half:
            lines.append(f"  Monte Carlo half-transition at n ~ {mc_half}")
        if mc_zero:
            lines.append(f"  Monte Carlo zero-fraction at n ~ {mc_zero}")

        # Growth rate comparison
        lines.append("")
        lines.append("  Growth rate analysis:")
        lines.append(f"    R_cop(3)/R_cop(2) = 11/2  = 5.50")
        lines.append(f"    R_cop(4)/R_cop(3) = 59/11 = 5.36")
        if lb >= 59:
            lines.append(f"    R_cop(5)/R_cop(4) > {lb}/59 = {lb/59:.2f} (lower bound)")
            lines.append(f"    If ratio ~5.4: R_cop(5) ~ {int(59*5.36)} (consistent with ratio prediction)")
            lines.append(f"    If ratio declining: R_cop(5) ~ 157-241 range")

    lines.append("")
    report = "\n".join(lines)

    if verbose:
        print(report)

    return report


# ============================================================================
# Main
# ============================================================================

def sat_timing_extrapolation(scan_data: List[Dict], verbose: bool = True) -> Dict:
    """
    Fit SAT solving times to exponential model and extrapolate.

    The key insight: near phase transitions, SAT time grows exponentially
    in n. The growth rate lets us estimate where solving becomes infeasible,
    which bounds where R_cop(5) can plausibly be.
    """
    # Filter to points with measurable time
    filtered = [(d['n'], d['time']) for d in scan_data if d['time'] > 0.01 and d['sat']]
    if len(filtered) < 5:
        return {}

    ns = np.array([x[0] for x in filtered], dtype=float)
    times = np.array([x[1] for x in filtered])
    log_times = np.log(times)

    # Fit log(time) = a*n + b
    coeffs = np.polyfit(ns, log_times, 1)
    a, b = coeffs
    doubling_interval = np.log(2) / a if a > 0 else float('inf')

    # Extrapolations
    targets = {
        '1 hour': 3600,
        '1 day': 86400,
        '1 week': 604800,
    }
    extrapolations = {}
    for name, seconds in targets.items():
        if a > 0:
            n_target = (np.log(seconds) - b) / a
            extrapolations[name] = float(n_target)

    # Prediction times
    pred_times = {}
    for name, n_pred in [('quadratic', PRED_QUADRATIC),
                         ('exponential', PRED_EXPONENTIAL),
                         ('ratio', PRED_RATIO)]:
        est_time = np.exp(a * n_pred + b)
        pred_times[name] = float(est_time)

    result = {
        'growth_rate': float(a),
        'intercept': float(b),
        'doubling_interval': float(doubling_interval),
        'extrapolations': extrapolations,
        'prediction_times': pred_times,
    }

    if verbose:
        print(f"\n  SAT timing model: log(time) = {a:.4f}*n + {b:.2f}")
        print(f"  Time doubles every {doubling_interval:.1f} n-steps")
        for name, n_val in extrapolations.items():
            print(f"  Solving takes {name} at n ~ {n_val:.0f}")
        print()
        n_lookup = {'quadratic': PRED_QUADRATIC, 'exponential': PRED_EXPONENTIAL,
                    'ratio': PRED_RATIO}
        print("  Estimated SAT time at predictions:")
        for name, t in pred_times.items():
            n_val = n_lookup.get(name, '?')
            if t < 3600:
                print(f"    {name} (n={n_val}): ~{t:.0f}s")
            elif t < 86400:
                print(f"    {name} (n={n_val}): ~{t/3600:.0f}h")
            else:
                print(f"    {name} (n={n_val}): ~{t/86400:.0f} days")

    return result


def main():
    print("=" * 72)
    print("R_cop(5) FRONTIER ESTIMATION")
    print("Pushing lower bound via SAT + heuristic transition analysis")
    print("=" * 72)
    print()

    # ---- 1. SAT lower bound (the core computation) ----
    print("=" * 72)
    print("PHASE 1: SAT LOWER BOUND")
    print("=" * 72)
    sat_result = sat_lower_bound(
        max_n=200,
        timeout_per_n=60.0,
        verbose=True,
    )
    print()

    # ---- 1b. SAT timing extrapolation ----
    print("=" * 72)
    print("PHASE 1b: SAT TIMING EXTRAPOLATION")
    print("=" * 72)
    timing_extrap = sat_timing_extrapolation(
        sat_result.get('scan_data', []), verbose=True)
    print()

    # ---- 2. Clique counting ----
    print("=" * 72)
    print("PHASE 2: CLIQUE COUNTING HEURISTIC")
    print("=" * 72)
    lb = sat_result.get('lower_bound', 60)
    clique_max = min(lb + 60, 200)
    clique_result = clique_counting_analysis(max_n=clique_max, verbose=True)
    print()

    # ---- 3. Extension upper bound ----
    extension_result = None
    if lb >= 80:
        print("=" * 72)
        print("PHASE 3: EXTENSION UPPER BOUND")
        print("=" * 72)
        extension_result = extension_upper_bound(
            start_n=lb,
            max_n=lb + 20,
            num_samples=100,
            timeout_per_n=60.0,
            verbose=True,
        )
        print()

    # ---- 4. Monte Carlo ----
    print("=" * 72)
    print("PHASE 4: MONTE CARLO AVOIDING FRACTION")
    print("=" * 72)
    # Exact MC up to n=80, sampled beyond
    mc_ns = list(range(10, 45, 5)) + list(range(45, min(lb, 80) + 1, 10))
    # Add some larger values with sampling
    for extra in [90, 100, 120, 157]:
        if extra not in mc_ns:
            mc_ns.append(extra)
    mc_ns = sorted(set(mc_ns))

    mc_result = monte_carlo_avoiding_fraction(
        ns=mc_ns,
        num_samples=3000,
        clique_enum_limit=80,
        verbose=True,
    )
    print()

    # ---- 5. Phase transition analysis ----
    print("=" * 72)
    print("PHASE 5: PHASE TRANSITION ANALYSIS")
    print("=" * 72)
    phase_result = phase_transition_analysis(
        sat_data=sat_result.get('scan_data'),
        clique_data=clique_result.get('data'),
        mc_data=mc_result.get('data'),
        verbose=True,
    )
    # Merge timing extrapolation into phase result
    phase_result['timing_extrapolation'] = timing_extrap
    print()

    # ---- 6. Report ----
    print()
    report = generate_report(
        sat_result=sat_result,
        clique_result=clique_result,
        mc_result=mc_result,
        phase_result=phase_result,
        extension_result=extension_result,
        verbose=True,
    )

    return {
        'sat': sat_result,
        'cliques': clique_result,
        'monte_carlo': mc_result,
        'phase': phase_result,
        'extension': extension_result,
        'timing_extrapolation': timing_extrap,
        'report': report,
    }


if __name__ == "__main__":
    main()
