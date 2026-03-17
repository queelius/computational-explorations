#!/usr/bin/env python3
"""
Adversarial verification of the claim R_cop(4) = 59.

Built ENTIRELY from scratch — no imports from coprime_ramsey_sat.py or
coprime_ramsey.py — to avoid shared bugs.  Uses CaDiCaL (via pysat)
instead of Glucose4 for solver diversity.

Attack vectors
--------------
1. Direct SAT at n=59 (try to find avoiding coloring — would DISPROVE claim)
2. Witness extraction + manual verification at n=58
3. Independent coprime 4-clique enumeration (cross-check counts)
4. Clause-level audit for specific cliques
5. Extension UNSAT verification (fix n=58 coloring, prove no extension to 59)
6. Vertex-59 connectivity check (59 is prime, should connect to all 1..58)

If ANY attack vector succeeds in finding a flaw, R_cop(4) = 59 is WRONG.
"""

import math
import time
from itertools import combinations
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from pysat.solvers import Cadical153, Glucose4


# ======================================================================
# Primitive helpers (written from scratch)
# ======================================================================

def are_coprime(a: int, b: int) -> bool:
    """True iff gcd(a, b) = 1."""
    return math.gcd(a, b) == 1


def coprime_graph_edges(n: int) -> List[Tuple[int, int]]:
    """All coprime pairs (i, j), 1 <= i < j <= n, sorted lexicographically."""
    return [(i, j) for i in range(1, n + 1)
            for j in range(i + 1, n + 1)
            if math.gcd(i, j) == 1]


def coprime_adjacency(n: int) -> Dict[int, Set[int]]:
    """Build adjacency dict for coprime graph on [n]."""
    adj: Dict[int, Set[int]] = {v: set() for v in range(1, n + 1)}
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def enumerate_coprime_kcliques(n: int, k: int) -> List[Tuple[int, ...]]:
    """
    Enumerate ALL k-element subsets of [n] that are pairwise coprime.

    Uses Bron-Kerbosch-style backtracking with pruning.
    Returns sorted tuples, each in ascending order.
    """
    if k < 1 or k > n:
        return []
    adj = coprime_adjacency(n)
    result: List[Tuple[int, ...]] = []

    def backtrack(partial: List[int], candidates: List[int]):
        if len(partial) == k:
            result.append(tuple(partial))
            return
        need = k - len(partial)
        for idx, v in enumerate(candidates):
            if len(candidates) - idx < need:
                break  # not enough left
            # v must be coprime to every member of partial
            if all(v in adj[u] for u in partial):
                # restrict future candidates to those > v and adjacent to v
                new_cand = [w for w in candidates[idx + 1:] if w in adj[v]]
                backtrack(partial + [v], new_cand)

    backtrack([], list(range(1, n + 1)))
    return result


def coprime_kcliques_containing(n: int, k: int, vertex: int,
                                adj: Dict[int, Set[int]]) -> List[Tuple[int, ...]]:
    """
    Enumerate k-cliques in coprime graph on [n] that contain `vertex`.

    Strategy: find (k-1)-cliques among neighbors of `vertex` that are < vertex
    (to avoid double-counting), then add vertex.  But we also need neighbors > vertex.
    Actually, just find all (k-1)-cliques among neighbors of vertex, then prepend.
    To avoid duplicates, we enumerate with vertex always at a canonical position.
    """
    neighbors = sorted(adj[vertex])
    # Build sub-adjacency among neighbors
    sub_adj: Dict[int, Set[int]] = {v: set() for v in neighbors}
    for v in neighbors:
        for w in neighbors:
            if v < w and w in adj[v]:
                sub_adj[v].add(w)
                sub_adj[w].add(v)

    result: List[Tuple[int, ...]] = []

    def backtrack(partial: List[int], candidates: List[int]):
        if len(partial) == k - 1:
            clique = tuple(sorted(partial + [vertex]))
            result.append(clique)
            return
        need = (k - 1) - len(partial)
        for idx, v in enumerate(candidates):
            if len(candidates) - idx < need:
                break
            if all(v in sub_adj[u] for u in partial):
                new_cand = [w for w in candidates[idx + 1:] if w in sub_adj[v]]
                backtrack(partial + [v], new_cand)

    backtrack([], neighbors)
    return result


# ======================================================================
# Attack Vector 1: Fresh SAT encoding (from scratch, CaDiCaL)
# ======================================================================

def build_sat_formula(n: int, k: int, symmetry_break: bool = False):
    """
    Build a SAT formula: does a 2-coloring of coprime edges on [n]
    avoiding monochromatic K_k exist?

    Variables: one per coprime edge.  x_e = True means color 0.
    For each coprime k-clique C with edges e_1, ..., e_{k choose 2}:
        - NOT all True:  at least one is False   -> clause [-e_1, ..., -e_m]
        - NOT all False: at least one is True     -> clause [e_1, ..., e_m]

    Returns (edge_to_var, cliques, clauses).
    """
    edges = coprime_graph_edges(n)
    edge_to_var: Dict[Tuple[int, int], int] = {}
    for idx, e in enumerate(edges, start=1):
        edge_to_var[e] = idx

    cliques = enumerate_coprime_kcliques(n, k)

    clauses: List[List[int]] = []
    if symmetry_break and (1, 2) in edge_to_var:
        clauses.append([edge_to_var[(1, 2)]])  # force edge(1,2) = color 0

    for clique in cliques:
        vlist = sorted(clique)
        m = len(vlist)
        evars = []
        for i in range(m):
            for j in range(i + 1, m):
                e = (vlist[i], vlist[j])
                evars.append(edge_to_var[e])
        # forbid all-True (monochromatic color 0)
        clauses.append([-v for v in evars])
        # forbid all-False (monochromatic color 1)
        clauses.append([v for v in evars])

    return edge_to_var, cliques, clauses


def solve_sat(clauses: List[List[int]], solver_cls=Cadical153) -> Optional[List[int]]:
    """Solve a SAT formula. Return model if SAT, None if UNSAT."""
    solver = solver_cls(bootstrap_with=clauses)
    sat = solver.solve()
    model = solver.get_model() if sat else None
    solver.delete()
    return model


def attack_direct_sat_n59(k: int = 4, verbose: bool = True) -> dict:
    """
    Attack Vector 1: Try to find an avoiding coloring at n=59.
    If SAT, R_cop(4) != 59.  If UNSAT, the claim survives this attack.

    Uses CaDiCaL (different solver from existing code that uses Glucose4).
    Tests BOTH with and without symmetry breaking.
    """
    results = {}

    for sym_break in [False, True]:
        label = "with_symbreak" if sym_break else "no_symbreak"
        if verbose:
            print(f"  AV1 [{label}]: Building SAT formula for n=59, k={k}...")
        t0 = time.time()
        etv, cliques, clauses = build_sat_formula(59, k, symmetry_break=sym_break)
        build_time = time.time() - t0
        if verbose:
            print(f"    {len(etv)} vars, {len(cliques)} cliques, {len(clauses)} clauses "
                  f"(built in {build_time:.2f}s)")

        if verbose:
            print(f"    Solving with CaDiCaL...")
        t0 = time.time()
        model = solve_sat(clauses, solver_cls=Cadical153)
        solve_time = time.time() - t0

        sat = model is not None
        if verbose:
            print(f"    Result: {'SAT (FLAW FOUND!)' if sat else 'UNSAT (claim survives)'} "
                  f"({solve_time:.2f}s)")

        results[label] = {
            "sat": sat,
            "num_vars": len(etv),
            "num_cliques": len(cliques),
            "num_clauses": len(clauses),
            "solve_time_s": solve_time,
            "model": model,
        }

    return results


# ======================================================================
# Attack Vector 2: Witness extraction + manual verification at n=58
# ======================================================================

def extract_coloring(model: List[int],
                     edge_to_var: Dict[Tuple[int, int], int]) -> Dict[Tuple[int, int], int]:
    """Convert a SAT model to an edge coloring."""
    model_set = set(model)
    coloring = {}
    for edge, var in edge_to_var.items():
        coloring[edge] = 0 if var in model_set else 1
    return coloring


def verify_coloring_avoids_mono_clique(n: int, k: int,
                                       coloring: Dict[Tuple[int, int], int],
                                       cliques: List[Tuple[int, ...]]) -> Tuple[bool, Optional[Tuple[int, ...]]]:
    """
    Check that `coloring` avoids monochromatic K_k.

    Returns (is_valid, first_bad_clique_or_None).
    Checks EVERY clique — no early termination on success, to be thorough.
    """
    bad_clique = None
    for clique in cliques:
        vlist = sorted(clique)
        colors = set()
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                e = (vlist[i], vlist[j])
                c = coloring.get(e)
                if c is None:
                    # Edge not in coloring — means (i,j) is not coprime?
                    # This would be a bug.
                    return False, clique
                colors.add(c)
        if len(colors) == 1:
            bad_clique = clique
            break  # found monochromatic clique
    return bad_clique is None, bad_clique


def attack_witness_n58(k: int = 4, verbose: bool = True) -> dict:
    """
    Attack Vector 2: Get an explicit avoiding coloring at n=58.
    Verify it by checking EVERY coprime 4-clique.

    Uses CaDiCaL for the SAT solve, then manual brute-force check.
    """
    if verbose:
        print("  AV2: Building SAT formula for n=58, k=4...")
    t0 = time.time()
    etv, cliques, clauses = build_sat_formula(58, k, symmetry_break=False)
    model = solve_sat(clauses, solver_cls=Cadical153)
    solve_time = time.time() - t0

    if model is None:
        if verbose:
            print("    CRITICAL FLAW: n=58 is UNSAT! Claim says it should be SAT.")
        return {"sat": False, "flaw": "n58_unsat"}

    coloring = extract_coloring(model, etv)
    if verbose:
        print(f"    n=58 is SAT ({solve_time:.2f}s). Verifying coloring...")

    # Manual verification
    t0 = time.time()
    is_valid, bad_clique = verify_coloring_avoids_mono_clique(58, k, coloring, cliques)
    verify_time = time.time() - t0

    if verbose:
        if is_valid:
            print(f"    Coloring verified: no monochromatic K_4 among {len(cliques)} cliques "
                  f"({verify_time:.2f}s)")
        else:
            print(f"    FLAW: monochromatic K_4 found at {bad_clique}!")

    # Also check edges: every coprime pair must be colored
    edges = coprime_graph_edges(58)
    missing = [e for e in edges if e not in coloring]

    # Color balance
    c0 = sum(1 for c in coloring.values() if c == 0)
    c1 = sum(1 for c in coloring.values() if c == 1)

    return {
        "sat": True,
        "valid_coloring": is_valid,
        "bad_clique": bad_clique,
        "num_cliques": len(cliques),
        "missing_edges": len(missing),
        "color_balance": (c0, c1),
        "verify_time_s": verify_time,
    }


# ======================================================================
# Attack Vector 3: Independent clique count cross-check
# ======================================================================

def attack_clique_count(n: int = 58, k: int = 4, verbose: bool = True) -> dict:
    """
    Attack Vector 3: Independently count coprime k-cliques and compare
    with the SAT encoding's implicit count (clauses / 2).

    Also cross-checks: every clique must be truly pairwise coprime,
    and every pairwise-coprime k-subset must appear.
    """
    if verbose:
        print(f"  AV3: Enumerating coprime {k}-cliques in [{n}]...")
    t0 = time.time()
    cliques = enumerate_coprime_kcliques(n, k)
    enum_time = time.time() - t0

    # Verify each clique is genuinely pairwise coprime
    bad_cliques = []
    for c in cliques:
        for i in range(len(c)):
            for j in range(i + 1, len(c)):
                if not are_coprime(c[i], c[j]):
                    bad_cliques.append((c, c[i], c[j]))

    # Cross-check: brute force over all k-subsets (only feasible for small n)
    # For n=58, k=4, C(58,4) = 424,270 — feasible.
    brute_count = 0
    brute_cliques_set: Set[Tuple[int, ...]] = set()
    for subset in combinations(range(1, n + 1), k):
        pairwise_coprime = all(math.gcd(subset[i], subset[j]) == 1
                               for i in range(k) for j in range(i + 1, k))
        if pairwise_coprime:
            brute_count += 1
            brute_cliques_set.add(tuple(subset))
    brute_time = time.time() - t0 - enum_time

    enum_cliques_set = set(cliques)
    missing_from_enum = brute_cliques_set - enum_cliques_set
    extra_in_enum = enum_cliques_set - brute_cliques_set

    if verbose:
        print(f"    Backtracking found {len(cliques)} cliques ({enum_time:.2f}s)")
        print(f"    Brute-force found {brute_count} cliques ({brute_time:.2f}s)")
        if missing_from_enum:
            print(f"    FLAW: {len(missing_from_enum)} cliques missing from backtracking!")
        if extra_in_enum:
            print(f"    FLAW: {len(extra_in_enum)} bogus cliques in backtracking!")
        if not missing_from_enum and not extra_in_enum:
            print("    Counts match perfectly.")

    return {
        "backtrack_count": len(cliques),
        "brute_count": brute_count,
        "match": len(cliques) == brute_count,
        "missing": len(missing_from_enum),
        "extra": len(extra_in_enum),
        "bad_cliques": bad_cliques,
    }


# ======================================================================
# Attack Vector 4: Clause-level audit for specific cliques
# ======================================================================

def attack_clause_audit(verbose: bool = True) -> dict:
    """
    Attack Vector 4: For specific known coprime 4-cliques, verify the SAT
    clauses are correct.

    Checks:
    - {1, 2, 3, 5}: all pairwise coprime? Yes.
    - The 6 edges map to 6 variables.
    - Two clauses are generated: one with all negated, one with all positive.
    - No variable appears twice in a clause.
    """
    test_cliques = [
        (1, 2, 3, 5),   # primes + 1
        (1, 2, 3, 7),
        (1, 5, 7, 11),
        (2, 3, 5, 7),   # all primes, no 1
        (1, 2, 9, 25),  # includes composites: gcd(9,25)=1, gcd(2,9)=1, gcd(2,25)=1
    ]

    # Verify these are actually coprime 4-cliques
    results = {}
    for clique in test_cliques:
        genuinely_coprime = all(math.gcd(clique[i], clique[j]) == 1
                                for i in range(4) for j in range(i + 1, 4))
        if not genuinely_coprime:
            results[clique] = {"coprime": False}
            continue

        # Build formula for n = max(clique) and check the clause
        n = max(clique)
        etv, all_cliques, clauses = build_sat_formula(n, 4, symmetry_break=False)

        # Find clauses for this specific clique
        vlist = sorted(clique)
        expected_edges = [(vlist[i], vlist[j]) for i in range(4) for j in range(i + 1, 4)]
        expected_vars = [etv[e] for e in expected_edges]

        # The two expected clauses
        expected_neg = sorted([-v for v in expected_vars])
        expected_pos = sorted([v for v in expected_vars])

        found_neg = False
        found_pos = False
        for cl in clauses:
            if sorted(cl) == expected_neg:
                found_neg = True
            if sorted(cl) == expected_pos:
                found_pos = True

        results[clique] = {
            "coprime": True,
            "edges": expected_edges,
            "vars": expected_vars,
            "neg_clause_found": found_neg,
            "pos_clause_found": found_pos,
            "correct": found_neg and found_pos,
        }
        if verbose:
            status = "OK" if found_neg and found_pos else "FLAW"
            print(f"  AV4: clique {clique}: {status} "
                  f"(neg={found_neg}, pos={found_pos})")

    return results


# ======================================================================
# Attack Vector 5: Extension UNSAT verification
# ======================================================================

def attack_extension_unsat(num_seeds: int = 20, verbose: bool = True) -> dict:
    """
    Attack Vector 5: Verify that no valid n=58 coloring extends to n=59.

    For each seed coloring from n=58:
    1. Fix the base edges to the seed's colors (as unit clauses).
    2. Add the n=59 formula's clique constraints.
    3. Solve: if SAT, the coloring extends — claim is WRONG.
    """
    if verbose:
        print("  AV5: Building n=58 base formula...")

    # Build n=58 formula
    etv58, cliques58, clauses58 = build_sat_formula(58, 4, symmetry_break=False)

    # Build n=59 formula (full)
    if verbose:
        print("  AV5: Building n=59 full formula...")
    etv59, cliques59, clauses59 = build_sat_formula(59, 4, symmetry_break=False)

    # Identify the new edges at vertex 59
    new_edges_59 = [(i, 59) for i in range(1, 59) if math.gcd(i, 59) == 1]
    if verbose:
        print(f"  AV5: {len(new_edges_59)} new edges at vertex 59")

    # Enumerate seeds from n=58
    solver58 = Cadical153(bootstrap_with=clauses58)
    seeds_checked = 0
    extensions_found = 0

    for seed_idx in range(num_seeds):
        if not solver58.solve():
            if verbose:
                print(f"    Exhausted all n=58 colorings after {seed_idx} seeds")
            break

        model58 = solver58.get_model()
        model58_set = set(model58)
        seeds_checked += 1

        # Build assumptions: fix every base edge in the n=59 formula
        assumptions = []
        for edge, var58 in etv58.items():
            var59 = etv59.get(edge)
            if var59 is not None:
                if var58 in model58_set:
                    assumptions.append(var59)
                else:
                    assumptions.append(-var59)

        # Solve n=59 with base edges fixed
        solver59 = Cadical153(bootstrap_with=clauses59)
        ext_sat = solver59.solve(assumptions=assumptions)
        solver59.delete()

        if ext_sat:
            extensions_found += 1
            if verbose:
                print(f"    Seed {seed_idx}: EXTENDS to n=59! FLAW FOUND!")
            break
        else:
            if verbose and seed_idx < 5:
                print(f"    Seed {seed_idx}: no extension (UNSAT)")

        # Block this seed
        solver58.add_clause([-lit for lit in model58])

    solver58.delete()

    all_failed = extensions_found == 0
    if verbose:
        if all_failed:
            print(f"  AV5: All {seeds_checked} seeds failed to extend. Claim survives.")
        else:
            print(f"  AV5: {extensions_found} seed(s) extended! Claim is WRONG.")

    return {
        "seeds_checked": seeds_checked,
        "extensions_found": extensions_found,
        "all_failed": all_failed,
    }


# ======================================================================
# Attack Vector 6: Vertex 59 connectivity
# ======================================================================

def attack_vertex59_connectivity(verbose: bool = True) -> dict:
    """
    Attack Vector 6: Verify that 59 is coprime to all of 1..58.
    59 is prime, so gcd(i, 59) = 1 for all 1 <= i <= 58.
    """
    non_coprime = []
    for i in range(1, 59):
        g = math.gcd(i, 59)
        if g != 1:
            non_coprime.append((i, g))

    # Verify 59 is prime
    is_prime = all(59 % d != 0 for d in range(2, int(59**0.5) + 1))

    # Number of coprime neighbors of 59 in [1..58] (Euler's totient)
    phi_59 = sum(1 for i in range(1, 59) if math.gcd(i, 59) == 1)

    if verbose:
        print(f"  AV6: 59 is prime: {is_prime}")
        print(f"  AV6: phi(59) = {phi_59} (should be 58)")
        print(f"  AV6: non-coprime neighbors: {non_coprime}")
        if not non_coprime and is_prime and phi_59 == 58:
            print("  AV6: Vertex 59 connects to ALL of 1..58. Claim survives.")
        else:
            print("  AV6: FLAW in connectivity assumption!")

    return {
        "is_prime": is_prime,
        "phi_59": phi_59,
        "non_coprime": non_coprime,
        "connects_to_all": len(non_coprime) == 0,
    }


# ======================================================================
# Attack Vector 7 (bonus): Cross-solver verification at n=59
# ======================================================================

def attack_cross_solver_n59(verbose: bool = True) -> dict:
    """
    Bonus: Solve n=59 with BOTH CaDiCaL and Glucose4.
    If they disagree, something is wrong.
    """
    if verbose:
        print("  AV7: Building formula once, solving with two solvers...")
    etv, cliques, clauses = build_sat_formula(59, 4, symmetry_break=False)

    results = {}
    for name, cls in [("cadical", Cadical153), ("glucose4", Glucose4)]:
        t0 = time.time()
        solver = cls(bootstrap_with=clauses)
        sat = solver.solve()
        dt = time.time() - t0
        solver.delete()
        results[name] = {"sat": sat, "time_s": dt}
        if verbose:
            print(f"    {name}: {'SAT' if sat else 'UNSAT'} ({dt:.2f}s)")

    agree = results["cadical"]["sat"] == results["glucose4"]["sat"]
    results["solvers_agree"] = agree
    if verbose:
        if agree:
            print("    Solvers agree. Claim survives.")
        else:
            print("    SOLVERS DISAGREE — something is wrong!")
    return results


# ======================================================================
# Attack Vector 8 (bonus): verify n=58 coloring is NOT extendable
#   by building the extension problem purely from the coloring
# ======================================================================

def attack_extension_from_coloring(verbose: bool = True) -> dict:
    """
    Take one specific n=58 avoiding coloring.  Build the extension problem
    to n=59 purely from first principles:

    For each new edge (i, 59), introduce a variable y_i in {0, 1}.
    For each coprime 4-clique containing vertex 59, the edges among
    the other 3 vertices are already colored.  The 3 edges from each
    vertex to 59 get variables y_i.  We need: the 6-edge clique is
    NOT monochromatic in either color.

    If the resulting formula is UNSAT, no extension exists for this coloring.
    """
    if verbose:
        print("  AV8: Getting an n=58 avoiding coloring...")
    etv58, cliques58, clauses58 = build_sat_formula(58, 4, symmetry_break=False)
    model58 = solve_sat(clauses58, solver_cls=Cadical153)
    if model58 is None:
        return {"flaw": "n58_unsat"}

    coloring58 = extract_coloring(model58, etv58)

    # Verify the coloring is valid
    valid, bad = verify_coloring_avoids_mono_clique(58, 4, coloring58, cliques58)
    if not valid:
        return {"flaw": f"invalid_n58_coloring_at_{bad}"}

    # Build extension variables: y_i for edge (i, 59), i = 1..58
    # 59 is coprime to all 1..58 (it's prime)
    new_edge_vars: Dict[int, int] = {}
    for i in range(1, 59):
        new_edge_vars[i] = i  # variable i represents color of edge (i, 59)

    # Find all 4-cliques containing 59 in [59]
    adj59 = coprime_adjacency(59)
    cliques_with_59 = coprime_kcliques_containing(59, 4, 59, adj59)
    if verbose:
        print(f"  AV8: {len(cliques_with_59)} coprime 4-cliques containing vertex 59")

    # Build extension clauses
    ext_clauses: List[List[int]] = []
    for clique in cliques_with_59:
        others = sorted(v for v in clique if v != 59)
        assert len(others) == 3

        # 6 edges total: 3 among others (fixed), 3 from others to 59 (variables)
        base_edges = [(others[i], others[j]) for i in range(3) for j in range(i + 1, 3)]
        base_colors = [coloring58[e] for e in base_edges]
        new_vars = [new_edge_vars[v] for v in others]  # y_{others[0]}, etc.

        # Forbid all-color-0: base edges must all be 0, and new edges must all be 0
        # If any base edge is NOT color 0, this clique is already safe from all-0
        if all(c == 0 for c in base_colors):
            # All base edges are color 0.
            # For all-0 monochromatic: need all new edges color 0 (True in SAT).
            # Forbid: at least one new edge is NOT color 0 (False).
            # Color 0 = variable True.  Forbid all True: clause [-y1, -y2, -y3]
            ext_clauses.append([-v for v in new_vars])

        # Forbid all-color-1: similarly
        if all(c == 1 for c in base_colors):
            # All base edges are color 1.
            # Color 1 = variable False.  Forbid all False: clause [y1, y2, y3]
            ext_clauses.append([v for v in new_vars])

    if verbose:
        print(f"  AV8: {len(ext_clauses)} extension clauses (58 vars)")
        print(f"  AV8: Solving extension formula...")

    t0 = time.time()
    model_ext = solve_sat(ext_clauses, solver_cls=Cadical153)
    dt = time.time() - t0
    extendable = model_ext is not None

    if verbose:
        if extendable:
            print(f"    FLAW: Extension found! ({dt:.4f}s)")
        else:
            print(f"    Extension UNSAT ({dt:.4f}s). Claim survives.")

    return {
        "extendable": extendable,
        "num_cliques_with_59": len(cliques_with_59),
        "num_extension_clauses": len(ext_clauses),
        "solve_time_s": dt,
    }


# ======================================================================
# Attack Vector 9 (bonus): Verify SAT at n=58, UNSAT at n=59 incrementally
#   with FRESH code, catching the exact transition
# ======================================================================

def attack_transition_sweep(n_start: int = 50, n_end: int = 59,
                            verbose: bool = True) -> dict:
    """
    Sweep n from n_start to n_end, checking SAT/UNSAT at each step.
    The transition from SAT to UNSAT should happen at exactly n=59.
    """
    results = {}
    if verbose:
        print(f"  AV9: Sweeping n={n_start}..{n_end} for SAT/UNSAT transition...")
    for n in range(n_start, n_end + 1):
        t0 = time.time()
        etv, cliques, clauses = build_sat_formula(n, 4, symmetry_break=True)
        model = solve_sat(clauses, solver_cls=Cadical153)
        dt = time.time() - t0
        sat = model is not None
        results[n] = {"sat": sat, "time_s": dt, "vars": len(etv),
                      "cliques": len(cliques), "clauses": len(clauses)}
        if verbose:
            print(f"    n={n}: {'SAT' if sat else 'UNSAT'} "
                  f"({len(etv)} vars, {len(cliques)} cliques, {dt:.2f}s)")

    # The claim: SAT for all n <= 58, UNSAT at n = 59
    all_sat_below = all(results[n]["sat"] for n in range(n_start, 59) if n in results)
    unsat_at_59 = not results.get(59, {}).get("sat", True)

    if verbose:
        print(f"    All n<59 SAT: {all_sat_below}")
        print(f"    n=59 UNSAT: {unsat_at_59}")
        if all_sat_below and unsat_at_59:
            print("    Transition at n=59 confirmed. Claim survives.")
        else:
            print("    FLAW in transition!")

    return {
        "per_n": results,
        "all_sat_below_59": all_sat_below,
        "unsat_at_59": unsat_at_59,
        "transition_correct": all_sat_below and unsat_at_59,
    }


# ======================================================================
# Master adversarial audit
# ======================================================================

def run_full_adversarial_audit(verbose: bool = True) -> dict:
    """Run all attack vectors and summarize."""
    print("=" * 72)
    print("ADVERSARIAL AUDIT: R_cop(4) = 59")
    print("=" * 72)
    print()

    all_results = {}

    # AV6: Quick check first
    print("[Attack Vector 6] Vertex 59 connectivity")
    all_results["av6_connectivity"] = attack_vertex59_connectivity(verbose)
    print()

    # AV3: Clique enumeration cross-check
    print("[Attack Vector 3] Clique enumeration cross-check (n=58)")
    all_results["av3_cliques"] = attack_clique_count(58, 4, verbose)
    print()

    # AV4: Clause-level audit
    print("[Attack Vector 4] Clause-level audit for specific cliques")
    all_results["av4_clauses"] = attack_clause_audit(verbose)
    print()

    # AV2: Witness at n=58
    print("[Attack Vector 2] Witness extraction + verification at n=58")
    all_results["av2_witness"] = attack_witness_n58(4, verbose)
    print()

    # AV1: Direct SAT at n=59
    print("[Attack Vector 1] Direct SAT at n=59 (CaDiCaL)")
    all_results["av1_direct"] = attack_direct_sat_n59(4, verbose)
    print()

    # AV7: Cross-solver
    print("[Attack Vector 7] Cross-solver verification")
    all_results["av7_cross"] = attack_cross_solver_n59(verbose)
    print()

    # AV5: Extension UNSAT
    print("[Attack Vector 5] Extension UNSAT (20 seeds)")
    all_results["av5_extension"] = attack_extension_unsat(20, verbose)
    print()

    # AV8: Extension from coloring
    print("[Attack Vector 8] Extension from specific coloring")
    all_results["av8_ext_coloring"] = attack_extension_from_coloring(verbose)
    print()

    # AV9: Transition sweep
    print("[Attack Vector 9] SAT/UNSAT transition sweep")
    all_results["av9_sweep"] = attack_transition_sweep(50, 59, verbose)
    print()

    # ---- Summary ----
    print("=" * 72)
    print("ADVERSARIAL AUDIT SUMMARY")
    print("=" * 72)

    flaws = []

    av6 = all_results["av6_connectivity"]
    if not av6["connects_to_all"] or not av6["is_prime"]:
        flaws.append("AV6: Vertex 59 connectivity failed")

    av3 = all_results["av3_cliques"]
    if not av3["match"] or av3["bad_cliques"]:
        flaws.append(f"AV3: Clique count mismatch ({av3['backtrack_count']} vs {av3['brute_count']})")

    av4 = all_results["av4_clauses"]
    for clique, info in av4.items():
        if info.get("coprime") and not info.get("correct"):
            flaws.append(f"AV4: Clause audit failed for clique {clique}")

    av2 = all_results["av2_witness"]
    if not av2.get("sat"):
        flaws.append("AV2: n=58 unexpectedly UNSAT")
    elif not av2.get("valid_coloring"):
        flaws.append(f"AV2: Witness coloring invalid at clique {av2.get('bad_clique')}")

    av1 = all_results["av1_direct"]
    for label, info in av1.items():
        if info.get("sat"):
            flaws.append(f"AV1: n=59 is SAT ({label}) — DISPROVES CLAIM")

    av7 = all_results["av7_cross"]
    if not av7.get("solvers_agree"):
        flaws.append("AV7: Solvers disagree on n=59")
    elif av7.get("cadical", {}).get("sat"):
        flaws.append("AV7: Both solvers say n=59 is SAT")

    av5 = all_results["av5_extension"]
    if not av5.get("all_failed"):
        flaws.append(f"AV5: {av5.get('extensions_found')} seed(s) extended to n=59")

    av8 = all_results["av8_ext_coloring"]
    if av8.get("extendable"):
        flaws.append("AV8: Specific n=58 coloring extends to n=59")

    av9 = all_results["av9_sweep"]
    if not av9.get("transition_correct"):
        flaws.append("AV9: SAT/UNSAT transition not at n=59")

    if flaws:
        print("FLAWS FOUND:")
        for f in flaws:
            print(f"  * {f}")
    else:
        print("NO FLAWS FOUND.")
        print("All 9 attack vectors failed to disprove R_cop(4) = 59.")
        print("The claim is ROBUST against independent verification.")

    print()
    return {"flaws": flaws, "details": all_results}


if __name__ == "__main__":
    run_full_adversarial_audit(verbose=True)
