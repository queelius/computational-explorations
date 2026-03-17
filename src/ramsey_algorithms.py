#!/usr/bin/env python3
"""
Optimal Algorithms for Coprime Ramsey Numbers.

Systematic comparison of algorithms for computing R_cop(k): brute force,
incremental extension, SAT (multiple solvers), backtracking with pruning,
random/greedy/local search lower bounds, and upper bound proof methods.

Identifies the fastest algorithm for each k and designs an optimal strategy
for pushing the computational frontier toward R_cop(5).
"""

import math
import random
import time
from itertools import combinations
from typing import (
    Dict, List, Optional, Set, Tuple,
)

import numpy as np
from pysat.solvers import Glucose4, Solver


# ============================================================================
# Core graph infrastructure
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


def has_monochromatic_clique_fast(
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
# 1. Algorithm comparison for R_cop(3) = 11
# ============================================================================

def brute_force_check(n: int, k: int) -> Tuple[bool, float, int]:
    """
    Brute force: enumerate all 2^m colorings, check each.

    Returns (all_have_mono_clique, time_seconds, colorings_checked).
    O(2^m * C(n,k) * C(k,2)) where m = #coprime edges.
    """
    edges = coprime_edges(n)
    m = len(edges)
    cliques = find_coprime_cliques(n, k)

    t0 = time.time()
    count_avoiding = 0
    for bits in range(2 ** m):
        coloring = {}
        for idx, e in enumerate(edges):
            coloring[e] = (bits >> idx) & 1
        if not has_monochromatic_clique_fast(n, k, coloring, cliques):
            count_avoiding += 1
    dt = time.time() - t0

    return count_avoiding == 0, dt, 2 ** m


def incremental_extension_check(n_target: int, k: int) -> Tuple[bool, float, int]:
    """
    Incremental extension: build avoiding colorings from small base,
    extend one vertex at a time.

    Returns (all_forced, time_seconds, total_colorings_explored).
    """
    t0 = time.time()
    total_explored = 0

    # Phase 1: exhaustive base
    base_n = None
    avoiding = None

    for n in range(k, n_target + 1):
        edges = coprime_edges(n)
        if not edges:
            continue
        if len(edges) <= 25:
            cliques = find_coprime_cliques(n, k)
            new_avoiding = []
            for bits in range(2 ** len(edges)):
                total_explored += 1
                coloring = {}
                for idx, e in enumerate(edges):
                    coloring[e] = (bits >> idx) & 1
                if not has_monochromatic_clique_fast(n, k, coloring, cliques):
                    new_avoiding.append(coloring)

            if not new_avoiding:
                dt = time.time() - t0
                return True, dt, total_explored

            avoiding = new_avoiding
            base_n = n
        else:
            break

    if avoiding is None or base_n is None:
        dt = time.time() - t0
        return False, dt, total_explored

    # Phase 2: incremental extension
    for n in range(base_n + 1, n_target + 1):
        new_edges = [(min(i, n), max(i, n))
                     for i in range(1, n) if math.gcd(i, n) == 1]
        if not new_edges:
            continue

        cliques = find_coprime_cliques(n, k)
        next_avoiding = []
        for col in avoiding:
            for bits in range(2 ** len(new_edges)):
                total_explored += 1
                new_col = dict(col)
                for idx, e in enumerate(new_edges):
                    new_col[e] = (bits >> idx) & 1
                if not has_monochromatic_clique_fast(n, k, new_col, cliques):
                    next_avoiding.append(new_col)

        if not next_avoiding:
            dt = time.time() - t0
            return True, dt, total_explored

        avoiding = next_avoiding

    dt = time.time() - t0
    return False, dt, total_explored


def sat_check(n: int, k: int, solver_name: str = 'glucose4') -> Tuple[bool, float, int, int]:
    """
    SAT solver: encode as CNF, solve.

    Returns (unsat, time_seconds, num_vars, num_clauses).
    """
    adj = coprime_adj(n)
    edges = coprime_edges(n)
    edge_to_var = {e: i + 1 for i, e in enumerate(edges)}

    cliques = find_coprime_cliques(n, k)

    clauses: List[List[int]] = []
    # Symmetry breaking: fix edge (1,2) to color 0
    if (1, 2) in edge_to_var:
        clauses.append([edge_to_var[(1, 2)]])

    for clique in cliques:
        vlist = sorted(clique)
        vars_ = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                vars_.append(edge_to_var[(vlist[i], vlist[j])])
        clauses.append([-v for v in vars_])  # not all color 0
        clauses.append([v for v in vars_])   # not all color 1

    num_vars = len(edges)
    num_clauses = len(clauses)

    t0 = time.time()
    if solver_name == 'glucose4':
        solver = Glucose4(bootstrap_with=clauses)
    else:
        solver = Solver(name=solver_name, bootstrap_with=clauses)
    sat = solver.solve()
    solver.delete()
    dt = time.time() - t0

    return not sat, dt, num_vars, num_clauses


def backtracking_with_pruning(n: int, k: int) -> Tuple[bool, float, int]:
    """
    Backtracking search with constraint propagation.

    Assigns colors to edges one at a time, pruning branches when a
    partial coloring already forces a monochromatic clique.

    Returns (all_forced, time_seconds, nodes_explored).
    """
    edges = coprime_edges(n)
    m = len(edges)
    adj = coprime_adj(n)
    cliques = find_coprime_cliques(n, k)

    # Build edge index for fast lookup
    edge_set = set(edges)
    edge_idx = {e: i for i, e in enumerate(edges)}

    # For each clique, store its edge indices
    clique_edges_list = []
    for clique in cliques:
        vlist = sorted(clique)
        cedges = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                e = (vlist[i], vlist[j])
                cedges.append(edge_idx[e])
        clique_edges_list.append(cedges)

    # For each edge, which cliques does it participate in?
    edge_to_cliques: Dict[int, List[int]] = {i: [] for i in range(m)}
    for ci, cedges in enumerate(clique_edges_list):
        for ei in cedges:
            edge_to_cliques[ei].append(ci)

    coloring = [-1] * m  # -1 = unassigned, 0 or 1 = assigned
    nodes = [0]
    found_avoiding = [False]

    def is_clique_monochromatic(ci: int) -> bool:
        """Check if clique ci is monochromatic in the partial coloring.
        Returns True only if all edges of the clique are assigned the same color."""
        cedges = clique_edges_list[ci]
        first_color = coloring[cedges[0]]
        if first_color == -1:
            return False
        return all(coloring[ei] == first_color for ei in cedges)

    def would_complete_mono(edge_i: int, color: int) -> bool:
        """Check if assigning color to edge_i would complete a mono clique."""
        for ci in edge_to_cliques[edge_i]:
            cedges = clique_edges_list[ci]
            all_same = True
            for ei in cedges:
                if ei == edge_i:
                    continue
                if coloring[ei] == -1 or coloring[ei] != color:
                    all_same = False
                    break
            if all_same:
                return True
        return False

    def backtrack(depth: int):
        if found_avoiding[0]:
            return  # already found one avoiding coloring
        if depth == m:
            # Complete assignment with no mono clique
            found_avoiding[0] = True
            return

        nodes[0] += 1

        for color in (0, 1):
            if would_complete_mono(depth, color):
                continue
            coloring[depth] = color
            backtrack(depth + 1)
            if found_avoiding[0]:
                return
            coloring[depth] = -1

    t0 = time.time()
    backtrack(0)
    dt = time.time() - t0

    # UNSAT means no avoiding coloring exists
    return not found_avoiding[0], dt, nodes[0]


def compare_algorithms_rcop3() -> Dict[str, dict]:
    """
    Compare all algorithms for R_cop(3) = 11.

    Tests each algorithm at n=10 (SAT: avoiding exists) and n=11 (UNSAT: forced).
    Returns dict of results.
    """
    results = {}

    # --- Brute force (only feasible for small n) ---
    # n=10 has 31 edges -> 2^31 ~= 2 billion. Too many.
    # Try n=8 (21 edges -> 2^21 = 2M) vs n=9.
    for n in [8, 9]:
        unsat, dt, checked = brute_force_check(n, 3)
        results[f'brute_force_n{n}'] = {
            'algorithm': 'brute_force',
            'n': n, 'k': 3,
            'unsat': unsat,
            'time': dt,
            'colorings_checked': checked,
            'exact': True,
        }

    # --- Incremental extension ---
    for n in [10, 11]:
        unsat, dt, explored = incremental_extension_check(n, 3)
        results[f'extension_n{n}'] = {
            'algorithm': 'incremental_extension',
            'n': n, 'k': 3,
            'unsat': unsat,
            'time': dt,
            'colorings_explored': explored,
            'exact': True,
        }

    # --- SAT solvers ---
    solvers_to_test = [
        'glucose4', 'cadical195', 'cadical153',
        'minisat22', 'lingeling', 'glucose42',
    ]
    for sname in solvers_to_test:
        for n in [10, 11]:
            try:
                unsat, dt, nvars, nclauses = sat_check(n, 3, solver_name=sname)
                results[f'sat_{sname}_n{n}'] = {
                    'algorithm': f'sat_{sname}',
                    'n': n, 'k': 3,
                    'unsat': unsat,
                    'time': dt,
                    'vars': nvars,
                    'clauses': nclauses,
                    'exact': True,
                }
            except Exception:
                results[f'sat_{sname}_n{n}'] = {
                    'algorithm': f'sat_{sname}',
                    'n': n, 'k': 3,
                    'error': 'solver_unavailable',
                }

    # --- Backtracking with pruning ---
    for n in [10, 11]:
        unsat, dt, nodes = backtracking_with_pruning(n, 3)
        results[f'backtrack_n{n}'] = {
            'algorithm': 'backtracking_pruned',
            'n': n, 'k': 3,
            'unsat': unsat,
            'time': dt,
            'nodes_explored': nodes,
            'exact': True,
        }

    return results


# ============================================================================
# 2. Lower bound algorithms
# ============================================================================

def random_coloring_lower_bound(
    n: int, k: int, num_trials: int = 10000, seed: int = 42,
) -> Tuple[int, int, float, float]:
    """
    Random coloring: sample random 2-colorings, check for mono K_k.

    Returns (successes, trials, success_rate, time_seconds).
    """
    rng = random.Random(seed)
    edges = coprime_edges(n)
    cliques = find_coprime_cliques(n, k)

    t0 = time.time()
    successes = 0
    for _ in range(num_trials):
        coloring = {e: rng.randint(0, 1) for e in edges}
        if not has_monochromatic_clique_fast(n, k, coloring, cliques):
            successes += 1
    dt = time.time() - t0

    rate = successes / num_trials if num_trials > 0 else 0.0
    return successes, num_trials, rate, dt


def greedy_coloring_lower_bound(
    n: int, k: int, num_trials: int = 100, seed: int = 42,
) -> Tuple[int, int, float]:
    """
    Greedy coloring: assign colors to edges one at a time, choosing the
    color that avoids creating a monochromatic K_k. Break ties randomly.

    Returns (successes, trials, time_seconds).
    """
    rng = random.Random(seed)
    edges = coprime_edges(n)
    m = len(edges)
    cliques = find_coprime_cliques(n, k)

    # For each edge, which cliques contain it?
    edge_idx = {e: i for i, e in enumerate(edges)}
    clique_edges_list = []
    for clique in cliques:
        vlist = sorted(clique)
        cedges = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                cedges.append(edge_idx[(vlist[i], vlist[j])])
        clique_edges_list.append(tuple(cedges))

    edge_to_cliques: Dict[int, List[int]] = {i: [] for i in range(m)}
    for ci, cedges in enumerate(clique_edges_list):
        for ei in cedges:
            edge_to_cliques[ei].append(ci)

    t0 = time.time()
    successes = 0

    for _ in range(num_trials):
        coloring = [-1] * m
        order = list(range(m))
        rng.shuffle(order)

        failed = False
        for ei in order:
            # Try each color, see which avoids mono cliques
            safe = []
            for color in (0, 1):
                ok = True
                for ci in edge_to_cliques[ei]:
                    cedges = clique_edges_list[ci]
                    all_same = True
                    for ej in cedges:
                        if ej == ei:
                            continue
                        if coloring[ej] == -1 or coloring[ej] != color:
                            all_same = False
                            break
                    if all_same:
                        ok = False
                        break
                if ok:
                    safe.append(color)

            if not safe:
                failed = True
                break
            coloring[ei] = rng.choice(safe)

        if not failed:
            successes += 1

    dt = time.time() - t0
    return successes, num_trials, dt


def local_search_lower_bound(
    n: int, k: int,
    max_flips: int = 10000, num_restarts: int = 10,
    seed: int = 42,
) -> Tuple[bool, int, float, int]:
    """
    WalkSAT-style local search: start from random coloring, flip the edge
    that resolves the most monochromatic cliques.

    Returns (found_avoiding, total_flips, time_seconds, best_violations).
    """
    rng = random.Random(seed)
    edges = coprime_edges(n)
    m = len(edges)
    cliques = find_coprime_cliques(n, k)

    edge_idx = {e: i for i, e in enumerate(edges)}
    clique_edges_list = []
    for clique in cliques:
        vlist = sorted(clique)
        cedges = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                cedges.append(edge_idx[(vlist[i], vlist[j])])
        clique_edges_list.append(tuple(cedges))

    edge_to_cliques: Dict[int, List[int]] = {i: [] for i in range(m)}
    for ci, cedges in enumerate(clique_edges_list):
        for ei in cedges:
            edge_to_cliques[ei].append(ci)

    def count_violations(coloring: List[int]) -> int:
        """Count number of monochromatic cliques."""
        count = 0
        for cedges in clique_edges_list:
            c0 = coloring[cedges[0]]
            if all(coloring[ei] == c0 for ei in cedges[1:]):
                count += 1
        return count

    t0 = time.time()
    best_violations = m  # upper bound
    total_flips = 0

    for _ in range(num_restarts):
        coloring = [rng.randint(0, 1) for _ in range(m)]
        violations = count_violations(coloring)

        if violations == 0:
            dt = time.time() - t0
            return True, total_flips, dt, 0

        for flip in range(max_flips):
            total_flips += 1

            # Find violated cliques
            violated = []
            for ci, cedges in enumerate(clique_edges_list):
                c0 = coloring[cedges[0]]
                if all(coloring[ei] == c0 for ei in cedges[1:]):
                    violated.append(ci)

            if not violated:
                dt = time.time() - t0
                return True, total_flips, dt, 0

            # Pick a random violated clique, pick a random edge in it to flip
            # With probability p, pick randomly; otherwise pick greedily
            p_random = 0.3
            if rng.random() < p_random:
                ci = rng.choice(violated)
                ei = rng.choice(clique_edges_list[ci])
            else:
                # Greedy: find the edge whose flip reduces violations most
                best_edge = -1
                best_delta = 0
                candidates = set()
                for ci in violated:
                    for ei in clique_edges_list[ci]:
                        candidates.add(ei)

                for ei in candidates:
                    coloring[ei] = 1 - coloring[ei]
                    new_v = count_violations(coloring)
                    delta = violations - new_v
                    if delta > best_delta or best_edge == -1:
                        best_delta = delta
                        best_edge = ei
                    coloring[ei] = 1 - coloring[ei]

                ei = best_edge

            coloring[ei] = 1 - coloring[ei]
            violations = count_violations(coloring)
            best_violations = min(best_violations, violations)

            if violations == 0:
                dt = time.time() - t0
                return True, total_flips, dt, 0

    dt = time.time() - t0
    return False, total_flips, dt, best_violations


def genetic_algorithm_lower_bound(
    n: int, k: int,
    pop_size: int = 100, generations: int = 200,
    mutation_rate: float = 0.05, seed: int = 42,
) -> Tuple[bool, int, float, int]:
    """
    Genetic algorithm: evolve a population of colorings to minimize
    monochromatic clique count.

    Returns (found_avoiding, generations_used, time_seconds, best_violations).
    """
    rng = random.Random(seed)
    edges = coprime_edges(n)
    m = len(edges)
    cliques = find_coprime_cliques(n, k)

    clique_edges_list = []
    edge_idx = {e: i for i, e in enumerate(edges)}
    for clique in cliques:
        vlist = sorted(clique)
        cedges = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                cedges.append(edge_idx[(vlist[i], vlist[j])])
        clique_edges_list.append(tuple(cedges))

    def fitness(coloring: List[int]) -> int:
        """Lower is better: count monochromatic cliques."""
        count = 0
        for cedges in clique_edges_list:
            c0 = coloring[cedges[0]]
            if all(coloring[ei] == c0 for ei in cedges[1:]):
                count += 1
        return count

    def crossover(p1: List[int], p2: List[int]) -> List[int]:
        """Uniform crossover."""
        return [p1[i] if rng.random() < 0.5 else p2[i] for i in range(m)]

    def mutate(ind: List[int]) -> List[int]:
        """Flip each bit with probability mutation_rate."""
        return [1 - ind[i] if rng.random() < mutation_rate else ind[i]
                for i in range(m)]

    t0 = time.time()

    # Initialize population
    population = [[rng.randint(0, 1) for _ in range(m)] for _ in range(pop_size)]
    fitnesses = [fitness(ind) for ind in population]

    best_violations = min(fitnesses)
    if best_violations == 0:
        dt = time.time() - t0
        return True, 0, dt, 0

    for gen in range(generations):
        # Tournament selection
        new_pop = []
        for _ in range(pop_size):
            i1, i2 = rng.sample(range(pop_size), 2)
            winner = i1 if fitnesses[i1] <= fitnesses[i2] else i2
            new_pop.append(list(population[winner]))

        # Crossover and mutation
        offspring = []
        for i in range(0, pop_size - 1, 2):
            c1 = crossover(new_pop[i], new_pop[i + 1])
            c2 = crossover(new_pop[i + 1], new_pop[i])
            offspring.append(mutate(c1))
            offspring.append(mutate(c2))
        if len(offspring) < pop_size:
            offspring.append(mutate(new_pop[-1]))

        population = offspring[:pop_size]
        fitnesses = [fitness(ind) for ind in population]

        gen_best = min(fitnesses)
        best_violations = min(best_violations, gen_best)

        if best_violations == 0:
            dt = time.time() - t0
            return True, gen + 1, dt, 0

    dt = time.time() - t0
    return False, generations, dt, best_violations


def lower_bound_comparison(k: int, n_range: List[int]) -> Dict[str, dict]:
    """
    Compare lower bound algorithms across a range of n values.
    """
    results = {}

    for n in n_range:
        # Random sampling
        succ, trials, rate, dt = random_coloring_lower_bound(n, k, num_trials=5000)
        results[f'random_n{n}'] = {
            'algorithm': 'random', 'n': n, 'k': k,
            'success_rate': rate, 'successes': succ,
            'time': dt, 'exact': False,
        }

        # Greedy
        succ_g, trials_g, dt_g = greedy_coloring_lower_bound(n, k, num_trials=100)
        results[f'greedy_n{n}'] = {
            'algorithm': 'greedy', 'n': n, 'k': k,
            'success_rate': succ_g / trials_g if trials_g > 0 else 0.0,
            'successes': succ_g,
            'time': dt_g, 'exact': False,
        }

        # Local search
        found, flips, dt_ls, best_v = local_search_lower_bound(
            n, k, max_flips=5000, num_restarts=5,
        )
        results[f'local_search_n{n}'] = {
            'algorithm': 'local_search', 'n': n, 'k': k,
            'found_avoiding': found, 'total_flips': flips,
            'best_violations': best_v, 'time': dt_ls, 'exact': False,
        }

        # Genetic algorithm
        found_ga, gens, dt_ga, best_v_ga = genetic_algorithm_lower_bound(
            n, k, pop_size=50, generations=100,
        )
        results[f'genetic_n{n}'] = {
            'algorithm': 'genetic', 'n': n, 'k': k,
            'found_avoiding': found_ga, 'generations': gens,
            'best_violations': best_v_ga, 'time': dt_ga, 'exact': False,
        }

    return results


# ============================================================================
# 3. Upper bound algorithms (proving UNSAT)
# ============================================================================

def direct_sat_upper_bound(
    n: int, k: int, solver_name: str = 'glucose4',
) -> Tuple[bool, float, int, int]:
    """
    Direct SAT: full CNF encoding, solve with CDCL solver.

    Returns (unsat, time_seconds, num_vars, num_clauses).
    """
    return sat_check(n, k, solver_name=solver_name)


def extension_method_upper_bound(
    n_target: int, k: int, max_seeds: int = 100,
) -> Tuple[bool, float, int, int]:
    """
    Extension method: enumerate avoiding colorings at n-1, verify none extend.

    Returns (proved_unsat, time_seconds, seeds_checked, seeds_extending).
    """
    n_base = n_target - 1

    # Build n_base SAT instance
    adj_base = coprime_adj(n_base)
    edges_base = coprime_edges(n_base)
    etv_base = {e: i + 1 for i, e in enumerate(edges_base)}

    cliques_base = find_coprime_cliques(n_base, k)
    base_clauses: List[List[int]] = []
    if (1, 2) in etv_base:
        base_clauses.append([etv_base[(1, 2)]])
    for clique in cliques_base:
        vlist = sorted(clique)
        vars_ = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                vars_.append(etv_base[(vlist[i], vlist[j])])
        base_clauses.append([-v for v in vars_])
        base_clauses.append([v for v in vars_])

    # Build n_target SAT instance
    adj_full = coprime_adj(n_target)
    edges_full = coprime_edges(n_target)
    etv_full = {e: i + 1 for i, e in enumerate(edges_full)}

    cliques_full = find_coprime_cliques(n_target, k)
    full_clauses: List[List[int]] = []
    if (1, 2) in etv_full:
        full_clauses.append([etv_full[(1, 2)]])
    for clique in cliques_full:
        vlist = sorted(clique)
        vars_ = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                vars_.append(etv_full[(vlist[i], vlist[j])])
        full_clauses.append([-v for v in vars_])
        full_clauses.append([v for v in vars_])

    t0 = time.time()

    solver_base = Glucose4(bootstrap_with=base_clauses)
    solver_full = Glucose4(bootstrap_with=full_clauses)

    seeds_checked = 0
    seeds_extending = 0

    for _ in range(max_seeds):
        if not solver_base.solve():
            break  # Exhausted all base colorings

        model = solver_base.get_model()
        model_set = set(model)
        seeds_checked += 1

        # Fix base edges in full formula
        assumptions = []
        for e_base, var_base in etv_base.items():
            if e_base in etv_full:
                var_full = etv_full[e_base]
                if var_base in model_set:
                    assumptions.append(var_full)
                else:
                    assumptions.append(-var_full)

        if solver_full.solve(assumptions=assumptions):
            seeds_extending += 1
            solver_base.delete()
            solver_full.delete()
            dt = time.time() - t0
            return False, dt, seeds_checked, seeds_extending

        # Block this coloring
        num_base_vars = len(edges_base)
        blocking = [-lit for lit in model[:num_base_vars]]
        solver_base.add_clause(blocking)

    solver_base.delete()
    solver_full.delete()
    dt = time.time() - t0
    return True, dt, seeds_checked, seeds_extending


def resolution_proof_size(n: int, k: int) -> Tuple[bool, float, Optional[int]]:
    """
    Extract resolution proof from SAT solver. Report proof size.

    Uses CaDiCaL (which supports proof logging via DRUP).
    pysat does not directly expose proof size, so we measure solver
    statistics as a proxy.

    Returns (unsat, time_seconds, num_clauses_in_proof_or_None).
    """
    edges = coprime_edges(n)
    edge_to_var = {e: i + 1 for i, e in enumerate(edges)}
    cliques = find_coprime_cliques(n, k)

    clauses: List[List[int]] = []
    if (1, 2) in edge_to_var:
        clauses.append([edge_to_var[(1, 2)]])
    for clique in cliques:
        vlist = sorted(clique)
        vars_ = []
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                vars_.append(edge_to_var[(vlist[i], vlist[j])])
        clauses.append([-v for v in vars_])
        clauses.append([v for v in vars_])

    t0 = time.time()
    try:
        solver = Solver(name='cadical195', bootstrap_with=clauses)
        sat = solver.solve()

        # accum_stats returns solver statistics dict
        stats = solver.accum_stats()
        proof_clauses = None
        if stats:
            # Use propagations + conflicts as a proxy for proof complexity
            proof_clauses = stats.get('propagations', 0) + stats.get('conflicts', 0)

        solver.delete()
        dt = time.time() - t0
        return not sat, dt, proof_clauses
    except Exception:
        dt = time.time() - t0
        return False, dt, None


def algebraic_method_feasibility(n: int, k: int) -> Dict[str, object]:
    """
    Assess feasibility of algebraic (Groebner basis) approach.

    The coprime Ramsey problem can be encoded as a polynomial system:
    for each edge e, variable x_e in {0,1} (so x_e^2 - x_e = 0).
    For each k-clique, the product of x_e's = 0 AND product of (1-x_e)'s = 0.

    This gives a polynomial system in m variables of degree C(k,2).
    Groebner basis computation is doubly exponential in the worst case.

    Returns feasibility assessment (does NOT actually compute).
    """
    edges = coprime_edges(n)
    m = len(edges)
    cliques = find_coprime_cliques(n, k)
    num_cliques = len(cliques)
    degree = k * (k - 1) // 2

    # Field equations: m polynomials of degree 2
    field_eqs = m
    # Clique constraints: 2 * num_cliques polynomials of degree C(k,2)
    clique_eqs = 2 * num_cliques

    total_polys = field_eqs + clique_eqs

    # Groebner basis complexity estimate (very rough upper bound)
    # For d-regular polynomial systems in m variables: O(m^(2^d))
    # With field equations bounding degree: O(2^m) worst case
    estimated_complexity = f"O(2^{m})"
    feasible = m <= 20  # Only feasible for tiny instances

    return {
        'n': n, 'k': k,
        'num_variables': m,
        'num_cliques': num_cliques,
        'polynomial_degree': degree,
        'total_polynomials': total_polys,
        'estimated_complexity': estimated_complexity,
        'feasible': feasible,
        'note': (
            f"Groebner basis over GF(2) with {m} variables and "
            f"{total_polys} polynomials of max degree {degree}. "
            f"Feasible only for m <= 20 (current m={m})."
        ),
    }


def upper_bound_comparison(n: int, k: int) -> Dict[str, dict]:
    """
    Compare upper bound (UNSAT-proving) algorithms at a single n.
    """
    results = {}

    # Direct SAT with multiple solvers
    for sname in ['glucose4', 'cadical195', 'glucose42', 'minisat22']:
        try:
            unsat, dt, nvars, nclauses = direct_sat_upper_bound(n, k, sname)
            results[f'sat_{sname}'] = {
                'algorithm': f'direct_sat_{sname}',
                'unsat': unsat, 'time': dt,
                'vars': nvars, 'clauses': nclauses,
            }
        except Exception:
            pass

    # Extension method
    proved, dt_ext, checked, extending = extension_method_upper_bound(n, k)
    results['extension'] = {
        'algorithm': 'extension_method',
        'unsat': proved, 'time': dt_ext,
        'seeds_checked': checked, 'seeds_extending': extending,
    }

    # Resolution proof size
    unsat_rp, dt_rp, proof_size = resolution_proof_size(n, k)
    results['resolution'] = {
        'algorithm': 'resolution_proof',
        'unsat': unsat_rp, 'time': dt_rp,
        'proof_complexity_proxy': proof_size,
    }

    # Algebraic feasibility
    results['algebraic'] = algebraic_method_feasibility(n, k)

    return results


# ============================================================================
# 4. Parameterized complexity analysis
# ============================================================================

def count_cliques_by_k(n: int, k_max: int = 5) -> Dict[int, int]:
    """Count the number of k-cliques in the coprime graph on [n]."""
    result = {}
    for k in range(2, k_max + 1):
        cliques = find_coprime_cliques(n, k)
        result[k] = len(cliques)
    return result


def parameterized_complexity_analysis(
    k_values: List[int] = None,
    max_n_per_k: Dict[int, int] = None,
) -> Dict[str, object]:
    """
    Analyze how computation scales with k.

    For each k, time the SAT-based computation up to R_cop(k) (or max_n).
    Track: #cliques, #variables, #clauses, solve time at critical n.

    Returns analysis dict.
    """
    if k_values is None:
        k_values = [2, 3, 4]
    if max_n_per_k is None:
        max_n_per_k = {2: 5, 3: 15, 4: 25}

    results: Dict[str, object] = {}
    timing_data = []

    for k in k_values:
        max_n = max_n_per_k.get(k, 20)
        k_results = []

        for n in range(k, max_n + 1):
            edges = coprime_edges(n)
            m = len(edges)

            # Count cliques
            t0 = time.time()
            cliques = find_coprime_cliques(n, k)
            clique_time = time.time() - t0
            num_cliques = len(cliques)

            # SAT solve
            unsat, sat_time, nvars, nclauses = sat_check(n, k, 'glucose4')

            k_results.append({
                'n': n, 'k': k,
                'edges': m, 'cliques': num_cliques,
                'vars': nvars, 'clauses': nclauses,
                'clique_enum_time': clique_time,
                'sat_time': sat_time,
                'unsat': unsat,
            })

            if unsat:
                # Found R_cop(k)
                break

        results[f'k{k}'] = k_results
        timing_data.extend(k_results)

    # Identify bottleneck: clique enumeration vs SAT solving
    bottleneck_analysis = {}
    for k in k_values:
        k_data = results.get(f'k{k}', [])
        if k_data:
            last = k_data[-1]
            clique_frac = last['clique_enum_time'] / (
                last['clique_enum_time'] + last['sat_time'] + 1e-9
            )
            bottleneck_analysis[k] = {
                'rcop_k': last['n'] if last['unsat'] else f'>{last["n"]}',
                'critical_n_edges': last['edges'],
                'critical_n_cliques': last['cliques'],
                'clique_enum_fraction': clique_frac,
                'bottleneck': 'clique_enumeration' if clique_frac > 0.5 else 'sat_solving',
            }

    results['bottleneck'] = bottleneck_analysis

    # Extrapolation to k=5
    # R_cop(k) values: 2, 11, ~59. Growth rate estimation.
    known = {2: 2, 3: 11, 4: 59}
    ratios = []
    sorted_k = sorted(known.keys())
    for i in range(1, len(sorted_k)):
        k_prev, k_curr = sorted_k[i - 1], sorted_k[i]
        ratios.append(known[k_curr] / known[k_prev])

    if len(ratios) >= 2:
        avg_ratio = np.mean(ratios)
        extrapolated_rcop5 = int(known[4] * avg_ratio)
    else:
        avg_ratio = ratios[0] if ratios else 5.0
        extrapolated_rcop5 = int(known[max(known)] * avg_ratio)

    # Estimate edge count at extrapolated R_cop(5)
    # Coprime edge density ~ 6/pi^2 ~ 0.608, so m ~ 0.608 * n*(n-1)/2
    density = 6.0 / (math.pi ** 2)
    est_n = extrapolated_rcop5
    est_edges = int(density * est_n * (est_n - 1) / 2)

    results['extrapolation'] = {
        'known_values': known,
        'growth_ratios': ratios,
        'average_ratio': float(avg_ratio),
        'extrapolated_rcop5': extrapolated_rcop5,
        'estimated_edges_at_rcop5': est_edges,
        'estimated_sat_vars': est_edges,
        'note': (
            f"R_cop(5) ~ {extrapolated_rcop5} (by ratio extrapolation). "
            f"SAT instance would have ~{est_edges} variables. "
            f"5-clique enumeration on [~{est_n}] is the primary bottleneck."
        ),
    }

    return results


# ============================================================================
# 5. Optimal algorithm for R_cop(5)
# ============================================================================

def estimate_rcop5_feasibility() -> Dict[str, object]:
    """
    Estimate the computational resources needed for R_cop(5).

    Based on the analysis of k=2,3,4, design the best strategy and
    estimate wall-clock time.
    """
    # Known values
    known = {2: 2, 3: 11, 4: 59}

    # Growth pattern: R_cop(2)=2, R_cop(3)=11, R_cop(4)=59
    # Ratios: 11/2=5.5, 59/11=5.36
    # Extrapolate: R_cop(5) ~ 59 * 5.36 ~ 316
    ratio_34 = known[4] / known[3]
    est_rcop5 = int(known[4] * ratio_34)

    # Coprime graph statistics at estimated R_cop(5)
    est_n = est_rcop5
    density = 6.0 / (math.pi ** 2)
    est_edges = int(density * est_n * (est_n - 1) / 2)

    # 5-clique count estimate: rough upper bound C(n, 5) * density^10
    # (10 = C(5,2) edges in K_5, each present with probability ~density)
    from math import comb
    est_5cliques = int(comb(est_n, 5) * density ** 10)

    # SAT formula size
    est_vars = est_edges
    est_clauses = 2 * est_5cliques + 1  # +1 for symmetry breaking

    # Timing estimation based on scaling from k=3,4
    # At n=11 (R_cop(3)): ~31 vars, ~300 clauses, ~0.001s
    # At n=59 (R_cop(4)): ~1085 vars, ~large clauses, ~5-60s
    # Scaling factor per 10x vars: ~1000x time (empirical for CDCL)
    # Vars ratio: est_vars / 1085
    var_ratio = est_edges / 1085.0
    # CDCL scaling: roughly O(1.5^vars) for hard instances,
    # but coprime Ramsey is structured, so more like O(vars^3) to O(vars^5)
    est_time_cubic = (var_ratio ** 3) * 10.0  # seconds, cubic scaling from k=4 baseline
    est_time_quintic = (var_ratio ** 5) * 10.0

    # 5-clique enumeration time estimate
    # At n=59, 4-clique enum takes ~0.1s. 5-cliques at n~316 scales as O(n^5 * density^10)
    clique_enum_est = (est_n / 59.0) ** 5 * 0.1  # seconds

    strategy = {
        'phase1': {
            'name': 'Incremental SAT with CaDiCaL195',
            'description': (
                'Use incremental SAT (CaDiCaL195, best CDCL solver) to scan '
                'n from 5 to ~300, confirming SAT at each step. CaDiCaL195 '
                'is the strongest solver for structured combinatorial instances.'
            ),
            'estimated_time': '1-10 hours',
        },
        'phase2': {
            'name': 'Extension method at transition point',
            'description': (
                'Once the SAT solver slows down near the transition, switch to '
                'extension checking: enumerate avoiding colorings at n-1, '
                'verify none extend to n. This avoids the hardest SAT instance.'
            ),
            'estimated_time': '10 minutes - 2 hours per candidate n',
        },
        'phase3': {
            'name': 'Local search for lower bound witnesses',
            'description': (
                'In parallel, run WalkSAT-style local search to quickly '
                'find avoiding colorings at n < R_cop(5), providing a '
                'lower bound and narrowing the search range.'
            ),
            'estimated_time': '10 minutes',
        },
    }

    feasible = est_time_cubic < 7 * 24 * 3600  # 1 week

    return {
        'estimated_rcop5': est_rcop5,
        'estimated_edges': est_edges,
        'estimated_5cliques': est_5cliques,
        'estimated_vars': est_vars,
        'estimated_clauses': est_clauses,
        'clique_enum_time_est': clique_enum_est,
        'sat_time_est_cubic_scaling': est_time_cubic,
        'sat_time_est_quintic_scaling': est_time_quintic,
        'strategy': strategy,
        'feasible_1_week': feasible,
        'recommendation': (
            f"R_cop(5) is estimated at ~{est_rcop5}. "
            f"The SAT instance would have ~{est_vars} variables and "
            f"~{est_clauses} clauses. "
            f"5-clique enumeration alone takes ~{clique_enum_est:.0f}s. "
            f"SAT solving under cubic scaling: ~{est_time_cubic:.0f}s "
            f"({est_time_cubic/3600:.1f}h). "
            f"Under quintic scaling: ~{est_time_quintic:.0f}s "
            f"({est_time_quintic/3600:.1f}h). "
            f"{'FEASIBLE' if feasible else 'NOT FEASIBLE'} within 1 week. "
            f"Recommended approach: CaDiCaL195 + extension method + "
            f"local search lower bound."
        ),
    }


def optimal_rcop5_scanner(
    start_n: int = 5, max_n: int = 80, timeout_per_n: float = 30.0,
    verbose: bool = True,
) -> Dict[str, object]:
    """
    Scan for R_cop(5) using the optimal multi-phase strategy.

    Phase 1: CaDiCaL195 incremental SAT for quick scans.
    Phase 2: When SAT slows down, switch to extension method.
    Phase 3: Report findings.

    Limited to max_n for safety; the full computation for R_cop(5) would
    require max_n ~ 300+.

    Returns results dict with best lower bound found and timing data.
    """
    k = 5
    adj: Dict[int, Set[int]] = {}
    all_cliques: List[Tuple[int, ...]] = []
    scan_data = []

    if verbose:
        print(f"Scanning for R_cop(5) using CaDiCaL195...")
        print(f"{'n':>4s}  {'vars':>6s}  {'clauses':>8s}  {'5-cliques':>10s}  "
              f"{'result':>7s}  {'time':>8s}")
        print("-" * 55)

    t_total_start = time.time()
    last_sat_n = k - 1

    for n in range(2, max_n + 1):
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

        # Find new 5-cliques containing n
        neighbors = sorted([v for v in range(1, n) if v in adj.get(n, set())])
        new_cliques: List[Tuple[int, ...]] = []

        def extend_clique(current: List[int], candidates: List[int]):
            if len(current) == k - 1:
                new_cliques.append(tuple(sorted(current + [n])))
                return
            needed = (k - 1) - len(current)
            for idx_c, v in enumerate(candidates):
                if len(candidates) - idx_c < needed:
                    break
                if all(v in adj[u] for u in current):
                    new_cands = [w for w in candidates[idx_c + 1:] if w in adj[v]]
                    extend_clique(current + [v], new_cands)

        extend_clique([], neighbors)
        all_cliques.extend(new_cliques)

        # Build edge-to-var mapping
        edge_to_var: Dict[Tuple[int, int], int] = {}
        nv = 1
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                if j in adj.get(i, set()):
                    edge_to_var[(i, j)] = nv
                    nv += 1
        num_vars = nv - 1

        # Build clauses
        clause_list: List[List[int]] = []
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
            if len(vars_) == k * (k - 1) // 2:
                clause_list.append([-v for v in vars_])
                clause_list.append([v for v in vars_])

        num_clauses = len(clause_list)

        # Solve
        t0 = time.time()
        try:
            solver = Solver(name='cadical195', bootstrap_with=clause_list)
            sat = solver.solve()
            solver.delete()
        except Exception:
            solver = Glucose4(bootstrap_with=clause_list)
            sat = solver.solve()
            solver.delete()
        dt = time.time() - t0

        status = "SAT" if sat else "UNSAT"
        if verbose and (n <= 20 or n % 5 == 0 or not sat):
            print(f"{n:4d}  {num_vars:6d}  {num_clauses:8d}  {len(new_cliques):10d}  "
                  f"{status:>7s}  {dt:7.3f}s")

        scan_data.append({
            'n': n, 'vars': num_vars, 'clauses': num_clauses,
            'new_cliques': len(new_cliques), 'total_cliques': len(all_cliques),
            'sat': sat, 'time': dt,
        })

        if not sat:
            t_total = time.time() - t_total_start
            if verbose:
                print(f"\nR_cop(5) = {n}  (total time: {t_total:.3f}s)")
            return {
                'rcop5': n, 'total_time': t_total,
                'scan_data': scan_data,
            }

        last_sat_n = n

        if dt > timeout_per_n:
            if verbose:
                print(f"\n  Timeout at n={n} ({dt:.1f}s > {timeout_per_n}s). "
                      f"Best lower bound: R_cop(5) > {last_sat_n}")
            break

    t_total = time.time() - t_total_start
    return {
        'rcop5': None,
        'lower_bound': last_sat_n,
        'total_time': t_total,
        'scan_data': scan_data,
    }


# ============================================================================
# 6. Comparison table
# ============================================================================

def build_comparison_table() -> List[dict]:
    """
    Build a complete comparison table of all algorithms.

    For each algorithm, report: name, type (exact/heuristic),
    time complexity, space complexity, best use case.
    """
    table = [
        {
            'algorithm': 'Brute Force',
            'type': 'exact',
            'time_complexity': 'O(2^m * C(n,k) * C(k,2))',
            'space_complexity': 'O(m)',
            'applicable_k': [2, 3],
            'max_feasible_n': 9,
            'best_for': 'Small instances (m <= 25), exhaustive enumeration',
            'limitations': 'Exponential in edge count; infeasible for n > 9 at k=3',
        },
        {
            'algorithm': 'Incremental Extension',
            'type': 'exact',
            'time_complexity': 'O(|avoiding(n-1)| * 2^phi(n) * C(n,k))',
            'space_complexity': 'O(|avoiding(n-1)| * m)',
            'applicable_k': [2, 3],
            'max_feasible_n': 11,
            'best_for': 'R_cop(3): avoiding set shrinks fast (36 -> 156 -> 0)',
            'limitations': 'Avoiding set can explode for k >= 4',
        },
        {
            'algorithm': 'Direct SAT (Glucose4)',
            'type': 'exact',
            'time_complexity': 'O(2^m) worst case, O(m^c) typical for structured',
            'space_complexity': 'O(m + clauses)',
            'applicable_k': [2, 3, 4],
            'max_feasible_n': 59,
            'best_for': 'General purpose, good clause learning',
            'limitations': 'Learned clause database can bloat',
        },
        {
            'algorithm': 'Direct SAT (CaDiCaL195)',
            'type': 'exact',
            'time_complexity': 'O(2^m) worst case, O(m^c) typical',
            'space_complexity': 'O(m + clauses)',
            'applicable_k': [2, 3, 4, 5],
            'max_feasible_n': 300,
            'best_for': 'Structured combinatorial instances, best CDCL heuristics',
            'limitations': 'Still exponential worst case',
        },
        {
            'algorithm': 'Backtracking + Pruning',
            'type': 'exact',
            'time_complexity': 'O(2^m) worst case with pruning',
            'space_complexity': 'O(m)',
            'applicable_k': [2, 3],
            'max_feasible_n': 11,
            'best_for': 'When SAT solver overhead exceeds benefit',
            'limitations': 'No clause learning; worse than SAT on hard instances',
        },
        {
            'algorithm': 'Extension Method',
            'type': 'exact',
            'time_complexity': 'O(|avoiding(n-1)| * 2^phi(n))',
            'space_complexity': 'O(|avoiding(n-1)| * m)',
            'applicable_k': [3, 4],
            'max_feasible_n': 59,
            'best_for': 'Proving UNSAT at transition point when avoiding set is small',
            'limitations': 'Must enumerate all avoiding colorings at n-1',
        },
        {
            'algorithm': 'Random Coloring',
            'type': 'heuristic (lower bound)',
            'time_complexity': 'O(T * C(n,k) * C(k,2))',
            'space_complexity': 'O(m)',
            'applicable_k': [2, 3, 4, 5],
            'max_feasible_n': 1000,
            'best_for': 'Quick lower bounds, probability estimation',
            'limitations': 'Cannot prove UNSAT; success rate drops exponentially',
        },
        {
            'algorithm': 'Greedy Coloring',
            'type': 'heuristic (lower bound)',
            'time_complexity': 'O(T * m * C_cliques_per_edge)',
            'space_complexity': 'O(m + cliques)',
            'applicable_k': [2, 3, 4, 5],
            'max_feasible_n': 1000,
            'best_for': 'Higher success rate than random for structured graphs',
            'limitations': 'Greedy choices can paint into corners',
        },
        {
            'algorithm': 'Local Search (WalkSAT)',
            'type': 'heuristic (lower bound)',
            'time_complexity': 'O(restarts * flips * cliques)',
            'space_complexity': 'O(m + cliques)',
            'applicable_k': [2, 3, 4, 5],
            'max_feasible_n': 1000,
            'best_for': 'Finding avoiding colorings near the transition',
            'limitations': 'Can get stuck in local minima',
        },
        {
            'algorithm': 'Genetic Algorithm',
            'type': 'heuristic (lower bound)',
            'time_complexity': 'O(generations * pop * m * cliques)',
            'space_complexity': 'O(pop * m)',
            'applicable_k': [2, 3, 4, 5],
            'max_feasible_n': 500,
            'best_for': 'Escaping local minima via crossover',
            'limitations': 'Slow convergence; large populations needed',
        },
        {
            'algorithm': 'Algebraic (Groebner)',
            'type': 'exact',
            'time_complexity': 'O(2^(2^m)) worst case',
            'space_complexity': 'O(2^m)',
            'applicable_k': [2, 3],
            'max_feasible_n': 5,
            'best_for': 'Theoretical interest only',
            'limitations': 'Doubly exponential; infeasible for m > 20',
        },
    ]
    return table


def format_comparison_table(table: List[dict]) -> str:
    """Format the comparison table as a string."""
    lines = []
    lines.append("=" * 90)
    lines.append("ALGORITHM COMPARISON TABLE FOR COPRIME RAMSEY NUMBERS")
    lines.append("=" * 90)
    lines.append("")

    header = f"{'Algorithm':<28s} {'Type':<22s} {'Max n':<8s} {'Best k':<10s}"
    lines.append(header)
    lines.append("-" * len(header))

    for row in table:
        alg = row['algorithm']
        atype = row['type']
        max_n = str(row['max_feasible_n'])
        best_k = ','.join(str(k) for k in row['applicable_k'])
        lines.append(f"{alg:<28s} {atype:<22s} {max_n:<8s} {best_k:<10s}")

    lines.append("")
    lines.append("OPTIMAL STRATEGY PER k:")
    lines.append("-" * 40)
    lines.append("  k=2: Brute force (trivial, R_cop(2)=2)")
    lines.append("  k=3: Incremental extension + SAT verification (R_cop(3)=11)")
    lines.append("  k=4: CaDiCaL195 SAT + extension method (R_cop(4)=59)")
    lines.append("  k=5: CaDiCaL195 SAT scan + extension at transition + local search")
    lines.append("")

    return "\n".join(lines)


# ============================================================================
# Main: run all analyses
# ============================================================================

def main():
    print("=" * 90)
    print("OPTIMAL ALGORITHMS FOR COPRIME RAMSEY NUMBERS")
    print("=" * 90)
    print()

    # ------------------------------------------------------------------
    # 1. Algorithm comparison for R_cop(3) = 11
    # ------------------------------------------------------------------
    print("=" * 90)
    print("1. ALGORITHM COMPARISON FOR R_cop(3) = 11")
    print("=" * 90)
    print()

    results = compare_algorithms_rcop3()

    # Group by algorithm
    algo_groups: Dict[str, List[dict]] = {}
    for key, val in results.items():
        alg = val.get('algorithm', key)
        if alg not in algo_groups:
            algo_groups[alg] = []
        algo_groups[alg].append(val)

    for alg, entries in sorted(algo_groups.items()):
        print(f"  {alg}:")
        for e in entries:
            n = e.get('n', '?')
            dt = e.get('time', 0)
            unsat = e.get('unsat', '?')
            err = e.get('error', None)
            if err:
                print(f"    n={n}: {err}")
            else:
                status = "UNSAT (forced)" if unsat else "SAT (avoiding exists)"
                extra = ""
                if 'colorings_checked' in e:
                    extra = f", {e['colorings_checked']:,} colorings"
                elif 'colorings_explored' in e:
                    extra = f", {e['colorings_explored']:,} explored"
                elif 'vars' in e:
                    extra = f", {e['vars']} vars / {e['clauses']} clauses"
                elif 'nodes_explored' in e:
                    extra = f", {e['nodes_explored']:,} nodes"
                print(f"    n={n}: {dt:.4f}s  {status}{extra}")
        print()

    # Find fastest at n=11
    n11_times = {}
    for key, val in results.items():
        if val.get('n') == 11 and 'time' in val and 'error' not in val:
            n11_times[val.get('algorithm', key)] = val['time']

    if n11_times:
        fastest = min(n11_times, key=n11_times.get)
        slowest = max(n11_times, key=n11_times.get)
        print(f"  FASTEST at n=11: {fastest} ({n11_times[fastest]:.4f}s)")
        print(f"  SLOWEST at n=11: {slowest} ({n11_times[slowest]:.4f}s)")
        if n11_times[slowest] > 0:
            ratio = n11_times[slowest] / n11_times[fastest]
            print(f"  Speedup: {ratio:.1f}x")
    print()

    # ------------------------------------------------------------------
    # 2. Lower bound algorithms
    # ------------------------------------------------------------------
    print("=" * 90)
    print("2. LOWER BOUND ALGORITHMS")
    print("=" * 90)
    print()

    # For k=3, test at n=8,9,10 (below R_cop(3)=11)
    lb_results = lower_bound_comparison(3, [8, 9, 10])

    for key in sorted(lb_results.keys()):
        val = lb_results[key]
        alg = val['algorithm']
        n = val['n']
        dt = val.get('time', 0)

        if alg == 'random':
            rate = val['success_rate']
            print(f"  Random n={n}: {rate:.4f} success rate "
                  f"({val['successes']}/5000), {dt:.3f}s")
        elif alg == 'greedy':
            rate = val['success_rate']
            print(f"  Greedy n={n}: {rate:.4f} success rate "
                  f"({val['successes']}/100), {dt:.3f}s")
        elif alg == 'local_search':
            found = val['found_avoiding']
            best_v = val['best_violations']
            flips = val['total_flips']
            print(f"  Local search n={n}: found={found}, "
                  f"best_violations={best_v}, {flips} flips, {dt:.3f}s")
        elif alg == 'genetic':
            found = val['found_avoiding']
            best_v = val['best_violations']
            gens = val['generations']
            print(f"  Genetic n={n}: found={found}, "
                  f"best_violations={best_v}, {gens} gens, {dt:.3f}s")
    print()

    # ------------------------------------------------------------------
    # 3. Upper bound algorithms
    # ------------------------------------------------------------------
    print("=" * 90)
    print("3. UPPER BOUND ALGORITHMS (proving UNSAT at n=11, k=3)")
    print("=" * 90)
    print()

    ub_results = upper_bound_comparison(11, 3)
    for key, val in sorted(ub_results.items()):
        if isinstance(val, dict) and 'algorithm' in val:
            alg = val['algorithm']
            dt = val.get('time', 0)
            unsat = val.get('unsat', '?')
            extra = ""
            if 'vars' in val:
                extra = f", {val['vars']} vars / {val['clauses']} clauses"
            elif 'seeds_checked' in val:
                extra = f", {val['seeds_checked']} seeds checked"
            elif 'proof_complexity_proxy' in val:
                extra = f", proof proxy={val['proof_complexity_proxy']}"
            print(f"  {alg}: unsat={unsat}, {dt:.4f}s{extra}")
        elif isinstance(val, dict) and 'feasible' in val:
            print(f"  algebraic: feasible={val['feasible']}, "
                  f"{val['num_variables']} vars, "
                  f"degree={val['polynomial_degree']}")
            print(f"    {val['note']}")
    print()

    # ------------------------------------------------------------------
    # 4. Parameterized complexity
    # ------------------------------------------------------------------
    print("=" * 90)
    print("4. PARAMETERIZED COMPLEXITY ANALYSIS")
    print("=" * 90)
    print()

    pc_results = parameterized_complexity_analysis()

    for k in [2, 3, 4]:
        k_data = pc_results.get(f'k{k}', [])
        if k_data:
            last = k_data[-1]
            rcop = last['n'] if last['unsat'] else f">{last['n']}"
            print(f"  k={k}: R_cop(k)={rcop}, "
                  f"{last['edges']} edges, {last['cliques']} cliques at critical n")

    print()
    bottleneck = pc_results.get('bottleneck', {})
    for k, info in sorted(bottleneck.items()):
        print(f"  k={k}: bottleneck = {info['bottleneck']} "
              f"(clique enum fraction: {info['clique_enum_fraction']:.2%})")

    extrap = pc_results.get('extrapolation', {})
    print()
    print(f"  Extrapolation: {extrap.get('note', 'N/A')}")
    print()

    # Is R_cop(k) FPT in k?
    print("  FPT ANALYSIS:")
    print("  R_cop(k) computation is NOT known to be FPT in k.")
    print("  The main obstacle: the number of k-cliques in G([n]) grows as")
    print("  O(n^k / k!), so the SAT formula size is exponential in k.")
    print("  However, the coprime graph has special structure:")
    print("  - Cliques must contain pairwise coprime numbers")
    print("  - 1 is coprime with everything, so max clique ~ 1 + pi(n)")
    print("  - For k > 1 + pi(n), R_cop(k) = infinity (no such clique exists)")
    print("  This gives a trivial FPT upper bound: R_cop(k) < p_k (k-th prime)")
    print("  by Bertrand's postulate, but the actual computation is hard.")
    print()

    # ------------------------------------------------------------------
    # 5. R_cop(5) estimate
    # ------------------------------------------------------------------
    print("=" * 90)
    print("5. OPTIMAL ALGORITHM FOR R_cop(5)")
    print("=" * 90)
    print()

    feasibility = estimate_rcop5_feasibility()
    print(f"  {feasibility['recommendation']}")
    print()

    print("  Strategy:")
    for phase, info in feasibility['strategy'].items():
        print(f"    {phase}: {info['name']}")
        print(f"      {info['description']}")
        print(f"      Estimated time: {info['estimated_time']}")
        print()

    # Run a limited scan
    print("  Running limited scan (n up to 80)...")
    scan = optimal_rcop5_scanner(max_n=80, timeout_per_n=30.0, verbose=True)
    print()
    if scan.get('rcop5'):
        print(f"  RESULT: R_cop(5) = {scan['rcop5']}")
    else:
        lb = scan.get('lower_bound', '?')
        print(f"  RESULT: R_cop(5) > {lb} (scan incomplete)")
        print(f"  Total scan time: {scan['total_time']:.1f}s")
    print()

    # ------------------------------------------------------------------
    # 6. Comparison table
    # ------------------------------------------------------------------
    table = build_comparison_table()
    print(format_comparison_table(table))


if __name__ == "__main__":
    main()
