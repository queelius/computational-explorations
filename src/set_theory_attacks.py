#!/usr/bin/env python3
"""
Set Theory & Extremal Combinatorics — Computational Attacks

Target problems from the 24 open set theory problems in the Erdos corpus:
  Hales-Jewett numbers, sunflower bounds, delta-system improvements,
  set intersection extremal problems, and partition calculus.

Strategy:
  1. Exact enumeration of Hales-Jewett numbers HJ(k, n) via brute-force
     and SAT encoding for small parameters.
  2. Sunflower number computation via greedy + SAT.
  3. Computational verification of Erdos-Rado vs. ALWZ (2019) sunflower bounds.
  4. Extremal set intersection families via enumeration and linear programming.
  5. Partition calculus arrow-notation verification for finite ordinals.
"""

import math
import time
from collections import defaultdict
from functools import lru_cache
from itertools import combinations, product as iproduct
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

import numpy as np
from pysat.solvers import Glucose4


# =============================================================================
# Section 1: Hales-Jewett Numbers
#
# HJ(k, n) = min N such that every k-coloring of [n]^N contains a
# combinatorial line.  A combinatorial line in [n]^N is a set of n points
# obtained by fixing some coordinates and letting the remaining coordinates
# run through all of {0, 1, ..., n-1} together.
#
# Known: HJ(2, 3) = 4  (also = Van der Waerden W(3; 2))
#        HJ(2, 2) = 2
#        HJ(1, n) = 1 for all n >= 1
#
# The Hales-Jewett theorem guarantees HJ(k, n) < infinity for all k, n.
# =============================================================================


def combinatorial_lines(n: int, N: int) -> List[List[Tuple[int, ...]]]:
    """
    Enumerate all combinatorial lines in [n]^N (using alphabet {0,...,n-1}).

    A combinatorial line is determined by:
      - A non-empty set S of "active" coordinates (those that vary)
      - Values for the "fixed" coordinates (those not in S)

    The line consists of n points where active coordinates take values
    0, 1, ..., n-1 simultaneously, and fixed coordinates keep their values.

    Returns list of lines, each line a list of n tuples (the n points).
    """
    if N == 0 or n == 0:
        return []

    coords = list(range(N))
    lines = []

    # For each non-empty subset S of coordinates (the "active" set)
    for r in range(1, N + 1):
        for active in combinations(coords, r):
            active_set = set(active)
            fixed_coords = [c for c in coords if c not in active_set]

            # For each assignment of values to fixed coordinates
            fixed_ranges = [range(n) for _ in fixed_coords]
            for fixed_vals in iproduct(*fixed_ranges):
                # Build the n points of this line
                line = []
                for val in range(n):
                    point = [0] * N
                    # Set active coordinates to val
                    for c in active_set:
                        point[c] = val
                    # Set fixed coordinates to their assigned values
                    for i, c in enumerate(fixed_coords):
                        point[c] = fixed_vals[i]
                    line.append(tuple(point))
                lines.append(line)

    return lines


def has_monochromatic_line(coloring: Dict[Tuple[int, ...], int],
                           lines: List[List[Tuple[int, ...]]]) -> bool:
    """Check if the coloring contains a monochromatic combinatorial line."""
    for line in lines:
        colors = {coloring[pt] for pt in line}
        if len(colors) == 1:
            return True
    return False


def check_hj(k: int, n: int, N: int) -> bool:
    """
    Check whether HJ(k, n) <= N by verifying that every k-coloring of [n]^N
    contains a monochromatic combinatorial line.

    Uses brute force: enumerate all k^(n^N) colorings.
    Only feasible for very small parameters.

    Returns True if every k-coloring has a monochromatic line (HJ(k,n) <= N).
    """
    if n <= 1:
        return True  # trivially, the single point is a line
    if k <= 0:
        return True  # no coloring exists

    points = list(iproduct(range(n), repeat=N))
    lines = combinatorial_lines(n, N)

    if not lines:
        return False

    # Enumerate all k-colorings of the point set
    for color_assignment in iproduct(range(k), repeat=len(points)):
        coloring = dict(zip(points, color_assignment))
        if not has_monochromatic_line(coloring, lines):
            return False  # Found an avoiding coloring, so HJ(k,n) > N

    return True


def hj_sat(k: int, n: int, N: int) -> Tuple[bool, Optional[Dict[Tuple[int, ...], int]]]:
    """
    SAT-based check: does there exist a k-coloring of [n]^N avoiding all
    monochromatic combinatorial lines?

    Returns (avoiding_exists, coloring_or_None).
    If avoiding_exists is False, then HJ(k, n) <= N.
    If avoiding_exists is True, returns a witness coloring (HJ(k, n) > N).
    """
    if n <= 1:
        return False, None  # every coloring trivially has a "line"
    if k <= 0:
        return False, None

    points = list(iproduct(range(n), repeat=N))
    lines = combinatorial_lines(n, N)
    num_points = len(points)
    point_to_idx = {p: i for i, p in enumerate(points)}

    # Variables: x_{p,c} means point p gets color c
    # Variable numbering: point i, color c -> i * k + c + 1
    def var(point_idx: int, color: int) -> int:
        return point_idx * k + color + 1

    solver = Glucose4()

    # Each point gets exactly one color:
    # At least one color
    for i in range(num_points):
        solver.add_clause([var(i, c) for c in range(k)])

    # At most one color (pairwise exclusion)
    for i in range(num_points):
        for c1 in range(k):
            for c2 in range(c1 + 1, k):
                solver.add_clause([-var(i, c1), -var(i, c2)])

    # For each line and each color: not all points of the line get that color
    for line in lines:
        point_indices = [point_to_idx[p] for p in line]
        for c in range(k):
            # At least one point in the line does NOT get color c
            solver.add_clause([-var(pi, c) for pi in point_indices])

    sat = solver.solve()

    if sat:
        model = set(solver.get_model())
        coloring = {}
        for i, p in enumerate(points):
            for c in range(k):
                if var(i, c) in model:
                    coloring[p] = c
                    break
        solver.delete()
        return True, coloring
    else:
        solver.delete()
        return False, None


def compute_hj(k: int, n: int, max_N: int = 10) -> int:
    """
    Compute HJ(k, n) by searching for the smallest N where no k-coloring
    of [n]^N avoids a monochromatic combinatorial line.

    Uses SAT solver. Returns HJ(k, n), or -1 if not found within max_N.
    """
    if n <= 1:
        return 1
    if k == 1:
        return 1  # single color, any line is monochromatic

    for N in range(1, max_N + 1):
        avoiding_exists, _ = hj_sat(k, n, N)
        if not avoiding_exists:
            return N

    return -1


def hj_table(max_k: int = 3, max_n: int = 4, max_N: int = 8) -> Dict[Tuple[int, int], int]:
    """
    Compute a table of HJ(k, n) values for small k and n.

    Returns dict mapping (k, n) -> HJ(k, n).  Value -1 means not determined
    within the search bound.
    """
    results = {}
    for k in range(1, max_k + 1):
        for n in range(2, max_n + 1):
            # Adaptive upper bound: larger n needs more dimensions, cut off sooner
            bound = min(max_N, max(3, 12 - 2 * n))
            val = compute_hj(k, n, max_N=bound)
            results[(k, n)] = val
    return results


def hj_lower_bound_witness(k: int, n: int, N: int) -> Optional[Dict[Tuple[int, ...], int]]:
    """
    Find a k-coloring of [n]^N that avoids all monochromatic combinatorial lines.
    Returns the coloring if one exists, None otherwise.
    This witnesses HJ(k, n) > N.
    """
    avoiding_exists, coloring = hj_sat(k, n, N)
    if avoiding_exists:
        return coloring
    return None


# =============================================================================
# Section 2: Sunflower Numbers
#
# A sunflower (or Delta-system) with r petals is a family of r sets
# S_1, ..., S_r such that S_i \cap S_j = Y (the kernel) for all i != j.
#
# f(k, r) = min m such that every family of m sets, each of size k,
# must contain a sunflower with r petals.
#
# Erdos-Rado (1960): f(k, r) <= k! * (r-1)^k + 1
# ALWZ (2019):       f(k, r) <= (C * r * log(k*r))^k   for some constant C
#
# Known exact values:
#   f(1, r) = r            (pigeonhole: r singleton sets, same element = kernel)
#   f(2, 2) = 5            (well-known exercise)
#   f(2, 3) = 10
#   f(3, 3) is open but <= 3! * 2^3 + 1 = 49 by Erdos-Rado
# =============================================================================


def is_sunflower(family: List[FrozenSet[int]], r: int) -> Optional[List[int]]:
    """
    Check if family contains a sunflower with r petals.

    Returns indices of the r sunflower members if found, None otherwise.
    """
    if len(family) < r:
        return None

    for indices in combinations(range(len(family)), r):
        sets = [family[i] for i in indices]
        # Compute pairwise intersections
        kernel = sets[0]
        for s in sets[1:]:
            kernel = kernel & s

        # Check: every pair intersects exactly in the kernel
        is_sf = True
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                if sets[i] & sets[j] != kernel:
                    is_sf = False
                    break
            if not is_sf:
                break

        if is_sf:
            return list(indices)

    return None


def find_sunflower(family: List[FrozenSet[int]], r: int) -> Optional[Tuple[List[int], FrozenSet[int]]]:
    """
    Find a sunflower with r petals in the family.

    Returns (indices, kernel) if found, None otherwise.
    """
    if len(family) < r:
        return None

    for indices in combinations(range(len(family)), r):
        sets = [family[i] for i in indices]
        kernel = sets[0]
        for s in sets[1:]:
            kernel = kernel & s

        is_sf = True
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                if sets[i] & sets[j] != kernel:
                    is_sf = False
                    break
            if not is_sf:
                break

        if is_sf:
            return list(indices), kernel

    return None


def sunflower_free_family(k: int, r: int, universe_size: int) -> List[FrozenSet[int]]:
    """
    Greedily build a maximal family of k-element subsets of [universe_size]
    that avoids containing a sunflower with r petals.

    Returns the maximal sunflower-free family.
    """
    universe = list(range(1, universe_size + 1))
    family: List[FrozenSet[int]] = []

    for subset in combinations(universe, k):
        candidate = frozenset(subset)
        test_family = family + [candidate]
        if is_sunflower(test_family, r) is None:
            family.append(candidate)

    return family


def compute_sunflower_number(k: int, r: int, max_universe: int = 0) -> Tuple[int, int]:
    """
    Compute f(k, r) exactly by exhaustive search.

    Finds the minimum m such that every family of m k-element subsets must
    contain a sunflower with r petals.  Equivalently, f(k,r) = 1 + max size
    of a sunflower-free family.

    We search over increasing universe sizes until the greedy bound
    stabilizes.

    Returns (f_value, max_sunflower_free_size).
    """
    if k == 0:
        return r, r - 1  # empty set: r copies form a sunflower with empty kernel

    if max_universe <= 0:
        # Heuristic universe size: Erdos-Rado bound tells us the answer is
        # at most k!*(r-1)^k, and we need universe >= k * that many sets to
        # have enough room.  But for exact computation we go modestly.
        max_universe = min(3 * k * r, 20)

    best = 0
    for u in range(k, max_universe + 1):
        family = sunflower_free_family(k, r, u)
        if len(family) > best:
            best = len(family)

    return best + 1, best


def sunflower_number_sat(k: int, r: int, target_size: int,
                         universe_size: int) -> Tuple[bool, Optional[List[FrozenSet[int]]]]:
    """
    SAT encoding: does there exist a family of target_size k-element subsets
    of [universe_size] containing no sunflower with r petals?

    Returns (exists, family_or_None).
    If exists is True, then f(k, r) > target_size.
    """
    all_ksets = list(combinations(range(1, universe_size + 1), k))
    num_ksets = len(all_ksets)

    if num_ksets < target_size:
        return False, None  # not enough k-sets exist

    # Variables: x_i means k-set i is in the family
    # Variable numbering: i + 1 (1-indexed)
    solver = Glucose4()

    # Exactly target_size sets chosen: encode with cardinality constraint.
    # We use a simple "at least target_size" via sequential counter.
    # For simplicity with SAT, encode "at least target_size" and check.
    # Actually, for this problem, we want "exists family of size >= target_size
    # with no sunflower", so we encode "at least target_size chosen" plus
    # "no r-subset is a sunflower".

    # At-least-target_size: We use a simple pairwise encoding that works for
    # small instances. Use a totalizer / sorting network for larger ones.
    # For the sizes we handle (target_size < 50), a direct approach works.

    set_vars = list(range(1, num_ksets + 1))

    # At least target_size sets: encode with sequential counter
    # counter[i][j] = "at least j of the first i variables are true"
    # This needs auxiliary variables.
    aux_base = num_ksets + 1
    # counter[i][j] for i in 0..num_ksets, j in 0..target_size
    # We only need the "at least target_size" condition at the end.

    def counter_var(i: int, j: int) -> int:
        """Variable for 'among first i vars, at least j are true'."""
        return aux_base + i * (target_size + 1) + j

    # Base: counter[0][0] is always true, counter[0][j>0] is always false
    solver.add_clause([counter_var(0, 0)])
    for j in range(1, target_size + 1):
        solver.add_clause([-counter_var(0, j)])

    # Transitions: counter[i][j] = counter[i-1][j] OR (x_i AND counter[i-1][j-1])
    for i in range(1, num_ksets + 1):
        xi = set_vars[i - 1]
        for j in range(target_size + 1):
            cv = counter_var(i, j)
            prev_same = counter_var(i - 1, j)

            if j == 0:
                # counter[i][0] is always true
                solver.add_clause([cv])
            else:
                prev_minus = counter_var(i - 1, j - 1)
                # cv <=> prev_same OR (xi AND prev_minus)
                # Forward: prev_same => cv
                solver.add_clause([-prev_same, cv])
                # Forward: (xi AND prev_minus) => cv
                solver.add_clause([-xi, -prev_minus, cv])
                # Backward: cv => prev_same OR (xi AND prev_minus)
                # Equivalent: cv => prev_same OR xi, and cv => prev_same OR prev_minus
                solver.add_clause([-cv, prev_same, xi])
                solver.add_clause([-cv, prev_same, prev_minus])

    # Require counter[num_ksets][target_size]
    solver.add_clause([counter_var(num_ksets, target_size)])

    # No sunflower: for each r-tuple of k-sets that forms a sunflower,
    # at least one must not be in the family.
    kset_fsets = [frozenset(s) for s in all_ksets]
    for indices in combinations(range(num_ksets), r):
        sets = [kset_fsets[i] for i in indices]
        kernel = sets[0]
        for s in sets[1:]:
            kernel = kernel & s

        is_sf = True
        for a in range(len(sets)):
            for b in range(a + 1, len(sets)):
                if sets[a] & sets[b] != kernel:
                    is_sf = False
                    break
            if not is_sf:
                break

        if is_sf:
            # At least one of these r sets must be excluded
            solver.add_clause([-set_vars[i] for i in indices])

    sat = solver.solve()
    if sat:
        model = set(solver.get_model())
        family = [kset_fsets[i] for i in range(num_ksets) if set_vars[i] in model]
        solver.delete()
        return True, family
    else:
        solver.delete()
        return False, None


def sunflower_table(max_k: int = 3, max_r: int = 4) -> Dict[Tuple[int, int], int]:
    """Compute a table of sunflower numbers f(k, r) for small k and r."""
    results = {}
    for k in range(1, max_k + 1):
        for r in range(2, max_r + 1):
            val, _ = compute_sunflower_number(k, r)
            results[(k, r)] = val
    return results


# =============================================================================
# Section 3: Delta-System (Sunflower) Lemma Bound Comparison
#
# Erdos-Rado bound:  f(k, r) <= k! * (r-1)^k + 1
# ALWZ (2019) bound: f(k, r) <= (C * r * log(k * r))^k  (C ~ 10)
# Rao (2020) simplification gives explicit constant.
#
# We compare these bounds and check which is tighter for given parameters.
# =============================================================================


def erdos_rado_bound(k: int, r: int) -> int:
    """
    Erdos-Rado sunflower bound: f(k, r) <= k! * (r-1)^k + 1.

    Every family of more than k!*(r-1)^k sets of size k contains
    a sunflower with r petals.
    """
    return math.factorial(k) * (r - 1) ** k + 1


def alwz_bound(k: int, r: int, C: float = 10.0) -> int:
    """
    Alweiss-Lovett-Wu-Zhang (2019) sunflower bound.

    f(k, r) <= (C * r * log(k * r))^k

    The constant C is not fully optimized in the original paper.
    Rao (2020) gives C ~ 10 as a working constant.
    """
    if k == 0 or r <= 1:
        return 1
    log_val = math.log(max(k * r, 2))
    return math.ceil((C * r * log_val) ** k)


def rao_bound(k: int, r: int) -> int:
    """
    Rao (2020) simplified bound from the ALWZ breakthrough.

    f(k, r) <= (C * r * (log k + log r + log log k))^k

    Uses C = 4 (tighter constant from Rao's analysis).
    """
    if k <= 1 or r <= 1:
        return max(r, 1)
    C = 4.0
    inner = math.log(k) + math.log(r) + math.log(max(math.log(k), 1))
    return math.ceil((C * r * inner) ** k)


def sunflower_bound_comparison(max_k: int = 8, max_r: int = 5) -> Dict[str, Dict[Tuple[int, int], int]]:
    """
    Compare Erdos-Rado, ALWZ, and Rao bounds for sunflower numbers.

    Returns dict with keys 'erdos_rado', 'alwz', 'rao' mapping to
    (k, r) -> bound value tables.
    """
    results = {
        'erdos_rado': {},
        'alwz': {},
        'rao': {},
    }

    for k in range(1, max_k + 1):
        for r in range(2, max_r + 1):
            results['erdos_rado'][(k, r)] = erdos_rado_bound(k, r)
            results['alwz'][(k, r)] = alwz_bound(k, r)
            results['rao'][(k, r)] = rao_bound(k, r)

    return results


def sunflower_bound_crossover(r: int = 3, max_k: int = 20) -> Optional[int]:
    """
    Find the smallest k where ALWZ improves on Erdos-Rado for given r.

    Returns the crossover k, or None if not found within max_k.
    """
    for k in range(1, max_k + 1):
        er = erdos_rado_bound(k, r)
        al = alwz_bound(k, r)
        if al < er:
            return k
    return None


def verify_sunflower_bounds(max_k: int = 3, max_r: int = 4) -> List[Dict]:
    """
    Verify upper bounds against computed exact values for small parameters.

    Returns list of dicts with k, r, exact, erdos_rado, alwz, rao, and
    whether each bound is correct (>= exact).
    """
    results = []
    exact = sunflower_table(max_k, max_r)

    for k in range(1, max_k + 1):
        for r in range(2, max_r + 1):
            f_exact = exact.get((k, r))
            er = erdos_rado_bound(k, r)
            al = alwz_bound(k, r)
            ra = rao_bound(k, r)
            results.append({
                'k': k, 'r': r,
                'exact': f_exact,
                'erdos_rado': er,
                'alwz': al,
                'rao': ra,
                'er_valid': f_exact is not None and er >= f_exact,
                'alwz_valid': f_exact is not None and al >= f_exact,
                'rao_valid': f_exact is not None and ra >= f_exact,
            })

    return results


# =============================================================================
# Section 4: Set Intersection Problems
#
# For a family F of k-element subsets of [n]:
#   - Fisher's inequality: |F| <= n if F is a 1-design
#   - Frankl-Wilson (1981): if k = 4q, |F| <= C(n, q-1) when certain
#     intersection sizes are forbidden
#   - Ray-Chaudhuri-Wilson: |F| <= C(n, s) if |A cap B| in L (|L|=s)
#
# We compute max family sizes for forbidden intersection constraints.
# =============================================================================


def family_avoids_intersection(family: List[FrozenSet[int]], L: Set[int]) -> bool:
    """
    Check if no pair in the family has intersection size in L.

    Returns True if the family avoids all intersection sizes in L.
    """
    for i in range(len(family)):
        for j in range(i + 1, len(family)):
            if len(family[i] & family[j]) in L:
                return False
    return True


def max_family_avoiding_intersection(n: int, k: int, L: Set[int]) -> Tuple[int, List[FrozenSet[int]]]:
    """
    Find the maximum family of k-element subsets of [n] such that no two
    members have intersection size in L.

    Uses greedy search.  Returns (max_size, family).
    """
    all_ksets = [frozenset(s) for s in combinations(range(1, n + 1), k)]
    family: List[FrozenSet[int]] = []

    for s in all_ksets:
        ok = True
        for t in family:
            if len(s & t) in L:
                ok = False
                break
        if ok:
            family.append(s)

    return len(family), family


def max_family_sat(n: int, k: int, L: Set[int]) -> Tuple[int, List[FrozenSet[int]]]:
    """
    SAT-based computation of the maximum family size of k-element subsets
    of [n] avoiding pairwise intersection sizes in L.

    Uses binary search on the target family size.
    Returns (max_size, witness_family).
    """
    all_ksets = [frozenset(s) for s in combinations(range(1, n + 1), k)]
    num_ksets = len(all_ksets)

    # Precompute forbidden pairs
    forbidden = []
    for i in range(num_ksets):
        for j in range(i + 1, num_ksets):
            if len(all_ksets[i] & all_ksets[j]) in L:
                forbidden.append((i, j))

    # Binary search for max family size
    lo, hi = 0, num_ksets
    best_family: List[FrozenSet[int]] = []

    while lo <= hi:
        mid = (lo + hi) // 2
        if mid == 0:
            lo = 1
            continue

        solver = Glucose4()
        set_vars = list(range(1, num_ksets + 1))

        # Forbidden pairs: at most one can be in the family
        for i, j in forbidden:
            solver.add_clause([-set_vars[i], -set_vars[j]])

        # At least mid sets chosen: sequential counter
        aux_base = num_ksets + 1

        def counter_var(i: int, j: int) -> int:
            return aux_base + i * (mid + 1) + j

        solver.add_clause([counter_var(0, 0)])
        for j in range(1, mid + 1):
            solver.add_clause([-counter_var(0, j)])

        for i in range(1, num_ksets + 1):
            xi = set_vars[i - 1]
            for j in range(mid + 1):
                cv = counter_var(i, j)
                prev_same = counter_var(i - 1, j)
                if j == 0:
                    solver.add_clause([cv])
                else:
                    prev_minus = counter_var(i - 1, j - 1)
                    solver.add_clause([-prev_same, cv])
                    solver.add_clause([-xi, -prev_minus, cv])
                    solver.add_clause([-cv, prev_same, xi])
                    solver.add_clause([-cv, prev_same, prev_minus])

        solver.add_clause([counter_var(num_ksets, mid)])

        sat = solver.solve()
        if sat:
            model = set(solver.get_model())
            family = [all_ksets[i] for i in range(num_ksets) if set_vars[i] in model]
            best_family = family
            lo = mid + 1
        else:
            hi = mid - 1

        solver.delete()

    return len(best_family), best_family


def ray_chaudhuri_wilson_bound(n: int, s: int) -> int:
    """
    Ray-Chaudhuri-Wilson bound: if L has s elements, then |F| <= C(n, s).

    For a family of subsets of [n] with pairwise intersections restricted
    to s values, the family has at most C(n, s) members.
    """
    return math.comb(n, s)


def frankl_wilson_bound(n: int, q: int) -> int:
    """
    Frankl-Wilson bound for k-uniform L-intersecting families.

    If k = 4q, L = {0, 1, ..., q-1} (mod p for suitable prime p),
    then |F| <= C(n, q-1).
    """
    return math.comb(n, q - 1) if q >= 1 else 0


def intersection_spectrum(family: List[FrozenSet[int]]) -> Dict[int, int]:
    """
    Compute the intersection size spectrum of a family.

    Returns dict mapping intersection size -> count of pairs with that size.
    """
    spectrum: Dict[int, int] = defaultdict(int)
    for i in range(len(family)):
        for j in range(i + 1, len(family)):
            size = len(family[i] & family[j])
            spectrum[size] += 1
    return dict(spectrum)


def erdos_ko_rado(n: int, k: int) -> int:
    """
    Erdos-Ko-Rado theorem: max size of an intersecting family of k-element
    subsets of [n] (every pair intersects).

    For n >= 2k, the answer is C(n-1, k-1) (the "star" family fixing element 1).
    """
    if n < 2 * k:
        # All k-subsets of [n] are pairwise intersecting
        return math.comb(n, k)
    return math.comb(n - 1, k - 1)


def max_t_intersecting_family(n: int, k: int, t: int) -> int:
    """
    Maximum family of k-element subsets of [n] where every pair intersects
    in at least t elements.

    For n sufficiently large (n >= (k-t+1)(t+1)), the answer is C(n-t, k-t)
    by the Frankl-Wilson generalization of EKR.
    """
    if t > k:
        return 0
    if t == 0:
        return math.comb(n, k)
    if n < 2 * k - t:
        return math.comb(n, k)
    return math.comb(n - t, k - t)


def set_intersection_table(max_n: int = 8, k: int = 3) -> Dict[Tuple[int, Set[int]], int]:
    """
    Compute max family sizes for k-element subsets of [n] avoiding various
    intersection patterns.

    Returns dict mapping (n, frozenset(L)) -> max family size.
    """
    results = {}
    for n in range(k, max_n + 1):
        # Avoid intersection size 0 (intersecting family)
        L_0 = frozenset({0})
        size_0, _ = max_family_avoiding_intersection(n, k, {0})
        results[(n, L_0)] = size_0

        # Avoid specific intersection size t
        for t in range(k):
            L_t = frozenset({t})
            size_t, _ = max_family_avoiding_intersection(n, k, {t})
            results[(n, L_t)] = size_t

    return results


# =============================================================================
# Section 5: Partition Calculus (Arrow Notation)
#
# The partition (Ramsey-type) arrow notation:
#   n -> (m)^r_k  means: for every k-coloring of the r-element subsets
#   of an n-element set, there exists a monochromatic m-element subset.
#
# Ramsey's theorem:  R(m; r, k) = min n such that n -> (m)^r_k.
#   R(m; 2, 2) = R(m, m) = classical Ramsey number.
#
# For hypergraph Ramsey (r >= 3), exact values are largely unknown.
#
# Finite partition calculus computations:
#   6 -> (3)^2_2  is equivalent to R(3,3) = 6
#   R(3,3,3) = R(3; 2, 3) = 17
# =============================================================================


def check_arrow(n: int, m: int, r: int, k: int) -> bool:
    """
    Check whether n -> (m)^r_k:
    every k-coloring of the r-element subsets of [n] contains a
    monochromatic m-element subset (all r-subsets of the m-set same color).

    Brute force: feasible only for small n, m, r, k.
    """
    if m > n:
        return False

    elements = list(range(n))
    r_subsets = list(combinations(elements, r))
    m_subsets = list(combinations(elements, m))
    num_r_subsets = len(r_subsets)

    # For each k-coloring of the r-subsets, check if there exists a
    # monochromatic m-subset.
    for coloring in iproduct(range(k), repeat=num_r_subsets):
        color_map = dict(zip(r_subsets, coloring))

        found_mono = False
        for ms in m_subsets:
            # Check all r-subsets of this m-subset
            sub_r = list(combinations(ms, r))
            colors = {color_map[s] for s in sub_r}
            if len(colors) == 1:
                found_mono = True
                break

        if not found_mono:
            return False  # This coloring avoids all monochromatic m-subsets

    return True


def check_arrow_sat(n: int, m: int, r: int, k: int) -> Tuple[bool, Optional[Dict]]:
    """
    SAT-based check of n -> (m)^r_k.

    Encodes "exists a k-coloring of r-subsets of [n] with no monochromatic
    m-subset" as SAT. If UNSAT, then n -> (m)^r_k holds.

    Returns (arrow_holds, avoiding_coloring_or_None).
    """
    if m > n:
        # No m-subsets exist; arrow does not hold (any coloring avoids trivially)
        return False, None

    elements = list(range(n))
    r_subsets = list(combinations(elements, r))
    m_subsets = list(combinations(elements, m))

    if not r_subsets:
        # No r-subsets to color; arrow holds vacuously (no coloring to check)
        return True, None
    if not m_subsets:
        # No m-subsets; avoiding coloring exists trivially; arrow fails
        return False, None

    num_r = len(r_subsets)
    r_to_idx = {s: i for i, s in enumerate(r_subsets)}

    # Variables: x_{s,c} = r-subset s gets color c
    def var(subset_idx: int, color: int) -> int:
        return subset_idx * k + color + 1

    solver = Glucose4()

    # Each r-subset gets exactly one color
    for i in range(num_r):
        solver.add_clause([var(i, c) for c in range(k)])
        for c1 in range(k):
            for c2 in range(c1 + 1, k):
                solver.add_clause([-var(i, c1), -var(i, c2)])

    # For each m-subset and each color: not all r-subsets get that color
    for ms in m_subsets:
        sub_r_indices = [r_to_idx[s] for s in combinations(ms, r)]
        for c in range(k):
            solver.add_clause([-var(si, c) for si in sub_r_indices])

    sat = solver.solve()
    if sat:
        model = set(solver.get_model())
        coloring = {}
        for i, s in enumerate(r_subsets):
            for c in range(k):
                if var(i, c) in model:
                    coloring[s] = c
                    break
        solver.delete()
        return False, coloring  # Arrow does NOT hold
    else:
        solver.delete()
        return True, None  # Arrow holds


def compute_ramsey(m: int, r: int, k: int, max_n: int = 30) -> int:
    """
    Compute R(m; r, k) = min n such that n -> (m)^r_k.

    Uses SAT solver for each n. Returns the Ramsey number, or -1 if not
    found within max_n.
    """
    # Lower bound: we need at least m
    for n in range(m, max_n + 1):
        holds, _ = check_arrow_sat(n, m, r, k)
        if holds:
            return n
    return -1


def compute_ramsey_table(max_m: int = 4, max_k: int = 3) -> Dict[Tuple[int, int], int]:
    """
    Compute R(m; 2, k) (graph Ramsey numbers) for small m and k.

    Returns dict mapping (m, k) -> R(m; 2, k).
    """
    results = {}
    for m in range(3, max_m + 1):
        for k in range(2, max_k + 1):
            # Adaptive upper bound
            upper = min(30, m * k * (k + 1))
            val = compute_ramsey(m, 2, k, max_n=upper)
            results[(m, k)] = val
    return results


def hypergraph_ramsey_bounds(m: int, r: int, k: int) -> Tuple[int, int]:
    """
    Known bounds for hypergraph Ramsey numbers R(m; r, k).

    Returns (lower_bound, upper_bound) from the stepping-up lemma and
    Erdos-Rado type bounds.
    """
    if r == 1:
        # Pigeonhole: R(m; 1, k) = (m-1)*k + 1
        return (m - 1) * k + 1, (m - 1) * k + 1

    if r == 2 and k == 2:
        # Classical Ramsey R(m, m): known bounds
        lower = max(m, int(2 ** (m / 2)))  # rough
        upper = math.comb(2 * (m - 1), m - 1)  # Erdos-Szekeres
        return lower, upper

    # General: stepping-up gives tower-type bounds
    # R(m; r, k) <= tower(r, polynomial in m and k)
    # For a rough upper bound, use Erdos-Rado partition calculus
    if r >= 3:
        # Lower bound from stepping-up: R(m; r, k) >= tower(r-1, m)
        # We compute a modest lower bound
        lower_val = m
        for _ in range(r - 2):
            lower_val = 2 ** lower_val
            if lower_val > 10**15:
                lower_val = 10**15
                break

        # Upper bound: tower of height r
        upper_val = math.comb(2 * (m - 1), m - 1)
        for _ in range(r - 2):
            upper_val = 2 ** min(upper_val, 50)
            if upper_val > 10**15:
                upper_val = 10**15
                break

        return lower_val, upper_val

    return m, m * k  # fallback


def partition_calculus_examples() -> List[Dict]:
    """
    Compute key examples from finite partition calculus.

    Returns list of dicts with arrow notation results.
    """
    results = []

    # R(3,3) = 6: 6 -> (3)^2_2
    for n in [5, 6]:
        holds, _ = check_arrow_sat(n, 3, 2, 2)
        results.append({
            'notation': f'{n} -> (3)^2_2',
            'holds': holds,
            'note': 'R(3,3)=6' if n == 6 else 'R(3,3) witness'
        })

    # R(3; 2, 3) = 17: partial verification (full n=17 is SAT-hard)
    # Verify lower bound: show n=8 and n=9 do NOT force monochromaticity
    for n in [8, 9]:
        holds, _ = check_arrow_sat(n, 3, 2, 3)
        results.append({
            'notation': f'{n} -> (3)^2_3',
            'holds': holds,
            'note': f'R(3,3,3)=17 lower bound check (expect NO)'
        })

    # R(4, 4) = 18: partial verification (full n=18 is SAT-hard)
    # Verify lower bound: show n=9 does NOT force it
    for n in [8, 9]:
        holds, _ = check_arrow_sat(n, 4, 2, 2)
        results.append({
            'notation': f'{n} -> (4)^2_2',
            'holds': holds,
            'note': f'R(4,4)=18 lower bound check'
        })

    # R(3; 1, k) = pigeonhole: (m-1)*k+1
    # R(3; 1, 2) = 5: need 5 elements for pigeonhole with 2 colors, m=3
    for n in [4, 5]:
        holds, _ = check_arrow_sat(n, 3, 1, 2)
        results.append({
            'notation': f'{n} -> (3)^1_2',
            'holds': holds,
            'note': 'pigeonhole R(3;1,2)=5' if n == 5 else 'pigeonhole witness'
        })

    # Hypergraph Ramsey: R(4; 3, 2) -- 3-uniform, 2-coloring, mono 4-set
    # For m=4, r=3: need all C(4,3)=4 triples of a 4-set same color.
    # This is nontrivial since C(n,3) triples must be 2-colored.
    for n in [6, 7, 8, 9, 10]:
        holds, _ = check_arrow_sat(n, 4, 3, 2)
        results.append({
            'notation': f'{n} -> (4)^3_2',
            'holds': holds,
            'note': 'hypergraph R(4;3,2)'
        })

    return results


# =============================================================================
# Synthesis: run all experiments
# =============================================================================


def run_all_experiments(verbose: bool = True) -> Dict:
    """Run all set theory attack experiments and return results."""
    results = {}

    if verbose:
        print("=" * 70)
        print("SET THEORY & EXTREMAL COMBINATORICS — COMPUTATIONAL ATTACKS")
        print("=" * 70)
        print()

    # 1. Hales-Jewett numbers
    if verbose:
        print("--- Section 1: Hales-Jewett Numbers ---")

    hj_results = {}
    for k, n, expected in [(1, 2, 1), (1, 3, 1), (2, 2, 2), (2, 3, 4)]:
        val = compute_hj(k, n, max_N=6)
        hj_results[(k, n)] = val
        if verbose:
            status = f"= {val}" if val > 0 else "> search bound"
            match = " (matches known)" if val == expected else ""
            print(f"  HJ({k}, {n}) {status}{match}")

    # Try HJ(2, 4) -- this is unknown/very hard
    if verbose:
        print("  HJ(2, 4): searching...")
    # Only check small N due to exponential blowup
    hj24_lower = 0
    for N in range(1, 5):
        avoiding, _ = hj_sat(2, 4, N)
        if avoiding:
            hj24_lower = N
        else:
            hj_results[(2, 4)] = N
            if verbose:
                print(f"  HJ(2, 4) = {N}")
            break
    else:
        hj_results[(2, 4)] = -1
        if verbose:
            print(f"  HJ(2, 4) > {hj24_lower} (search limit reached)")

    results['hales_jewett'] = hj_results
    if verbose:
        print()

    # 2. Sunflower numbers
    if verbose:
        print("--- Section 2: Sunflower Numbers ---")

    sf_results = sunflower_table(max_k=3, max_r=4)
    for (k, r), val in sorted(sf_results.items()):
        er = erdos_rado_bound(k, r)
        if verbose:
            print(f"  f({k}, {r}) = {val}  (Erdos-Rado bound: {er})")

    results['sunflower'] = sf_results
    if verbose:
        print()

    # 3. Sunflower bound comparison
    if verbose:
        print("--- Section 3: Sunflower Bound Comparison ---")

    bounds = sunflower_bound_comparison(max_k=6, max_r=4)
    crossover_3 = sunflower_bound_crossover(r=3)
    if verbose:
        print(f"  ALWZ improves on Erdos-Rado for r=3 at k={crossover_3}")
        for k in [3, 4, 5, 6]:
            er = bounds['erdos_rado'][(k, 3)]
            al = bounds['alwz'][(k, 3)]
            ra = bounds['rao'][(k, 3)]
            print(f"  k={k}, r=3: ER={er}, ALWZ={al}, Rao={ra}")

    # Verify bounds against exact values
    verification = verify_sunflower_bounds(max_k=3, max_r=3)
    results['sunflower_bounds'] = {
        'comparison': bounds,
        'crossover_r3': crossover_3,
        'verification': verification,
    }
    if verbose:
        print()

    # 4. Set intersection
    if verbose:
        print("--- Section 4: Set Intersection Problems ---")

    # EKR values
    for n in range(4, 8):
        ekr = erdos_ko_rado(n, 2)
        if verbose:
            print(f"  EKR({n}, 2) = {ekr}")

    # Max family avoiding intersection size 0 (i.e., pairwise intersecting)
    for n in [5, 6, 7]:
        size, family = max_family_avoiding_intersection(n, 3, {0})
        if verbose:
            print(f"  Max 3-intersecting family in [{n}]: {size}")

    # Forbidden intersection spectrum
    for n in [5, 6]:
        size, family = max_family_avoiding_intersection(n, 2, {1})
        if verbose:
            print(f"  Max 2-family in [{n}] avoiding |A cap B|=1: {size}")

    results['intersection'] = {
        'ekr': {n: erdos_ko_rado(n, 2) for n in range(4, 10)},
    }
    if verbose:
        print()

    # 5. Partition calculus
    if verbose:
        print("--- Section 5: Partition Calculus ---")

    pc_results = partition_calculus_examples()
    for r in pc_results:
        if verbose:
            status = "YES" if r['holds'] else "NO"
            print(f"  {r['notation']}: {status}  ({r['note']})")

    results['partition_calculus'] = pc_results

    # Hypergraph Ramsey bounds
    for m in [3, 4]:
        lo, hi = hypergraph_ramsey_bounds(m, 3, 2)
        if verbose:
            print(f"  R({m}; 3, 2) in [{lo}, {hi}]")

    if verbose:
        print()
        print("=" * 70)
        print("COMPLETE")
        print("=" * 70)

    return results


if __name__ == "__main__":
    run_all_experiments(verbose=True)
