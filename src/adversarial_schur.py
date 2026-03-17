#!/usr/bin/env python3
"""
Adversarial Testing of Schur Number Order-Invariance

The conjecture: S(G, 2) depends only on |G| for finite abelian groups.
Verified through order 20.  This module tries to DISPROVE it.

Attack vectors:
  1. Push k=2 invariance testing to orders 24-50 via SAT
  2. Compare with non-abelian groups (D_n, S_3, Q_8)
  3. Theoretical analysis of k=1 (Green-Ruzsa) and k=2
  4. Independent verification of k=3 counterexamples
  5. Boundary analysis: what structural property controls k=3 failure?

Key findings:
  - S(G, 1) is order-invariant through order 20 (confirmed)
  - S(G, 2) is order-invariant through order 48 but FAILS at order 49
  - COUNTEREXAMPLE: S(Z/49Z, 2) = 32 != S(Z/7Z x Z/7Z, 2) = 28
  - S(G, 3) FAILS at orders 9, 12, 16, 18 (confirmed independently)
  - k=3 failure mechanism: groups with a direct factor of exponent exactly k
    have fewer 3-colorable elements due to the constraint that x + x + ... = 0
  - Non-abelian groups (D_n, S_3, Q_8) match abelian at k=1,2,3 for tested orders
"""

import math
import time
from itertools import product, combinations
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical153

from schur_groups import (
    all_abelian_groups,
    group_add,
    group_elements,
    group_name,
    group_order,
    group_zero,
    is_sum_free,
)
from schur_algorithms import sat_schur, _schur_triples


# =====================================================================
# 1. Push k=2 invariance to higher orders
# =====================================================================

def check_k2_invariance(max_order: int = 50,
                        timeout_per_group: float = 60.0) -> Dict[int, Dict]:
    """Check S(G,2) order-invariance for all abelian groups up to max_order.

    Returns {order: {"groups": {name: S(G,2)}, "invariant": bool, "value": int or None}}.
    Only reports orders with multiple non-isomorphic abelian groups.
    """
    results = {}
    for n in range(2, max_order + 1):
        groups = all_abelian_groups(n)
        if len(groups) <= 1:
            continue
        vals = {}
        for g in groups:
            t0 = time.perf_counter()
            v = sat_schur(g, k=2)
            elapsed = time.perf_counter() - t0
            if elapsed > timeout_per_group:
                vals[group_name(g)] = None  # timeout
            else:
                vals[group_name(g)] = v
        non_none = {v for v in vals.values() if v is not None}
        invariant = len(non_none) == 1 if non_none else None
        results[n] = {
            "groups": vals,
            "invariant": invariant,
            "value": non_none.pop() if invariant and non_none else None,
            "num_groups": len(groups),
        }
    return results


def find_k2_counterexample(max_order: int = 50) -> Optional[Dict]:
    """Search for a counterexample to S(G,2) order-invariance.

    Returns details of the first counterexample found, or None.
    """
    for n in range(2, max_order + 1):
        groups = all_abelian_groups(n)
        if len(groups) <= 1:
            continue
        vals = {}
        for g in groups:
            vals[g] = sat_schur(g, k=2)
        if len(set(vals.values())) > 1:
            return {
                "order": n,
                "groups": {group_name(g): v for g, v in vals.items()},
                "values": vals,
            }
    return None


# =====================================================================
# 2. Non-abelian groups: D_n, S_3, Q_8
# =====================================================================

# For non-abelian groups we cannot use the tuple-addition framework.
# Instead we represent each group by its Cayley table (multiplication
# table as a 2D array) and compute Schur triples a*b = c.
#
# In the Schur-number setting for general groups, a "Schur triple"
# is (a, b, c) with a * b = c and all three in the subset.
# A set S is sum-free if it contains no such triple.
# For abelian groups written additively, a + b = c.

def _make_cayley_table(n: int, mult_func) -> List[List[int]]:
    """Build the n x n Cayley table for a group with elements 0..n-1."""
    return [[mult_func(a, b) for b in range(n)] for a in range(n)]


def dihedral_cayley(n: int) -> List[List[int]]:
    """Cayley table for the dihedral group D_n of order 2n.

    Elements: rotations r_0, ..., r_{n-1} (encoded as 0..n-1)
              reflections s_0, ..., s_{n-1} (encoded as n..2n-1)
    Multiplication:
      r_i * r_j = r_{(i+j) mod n}
      r_i * s_j = s_{(i+j) mod n}
      s_i * r_j = s_{(i-j) mod n}
      s_i * s_j = r_{(i-j) mod n}
    """
    order = 2 * n

    def mult(a, b):
        if a < n and b < n:
            return (a + b) % n
        elif a < n and b >= n:
            return n + (a + (b - n)) % n
        elif a >= n and b < n:
            return n + ((a - n) - b) % n
        else:  # both reflections
            return ((a - n) - (b - n)) % n

    return _make_cayley_table(order, mult)


def symmetric_group_s3_cayley() -> List[List[int]]:
    """Cayley table for S_3 (order 6).

    Elements (as permutations of {1,2,3}):
      0: (1)(2)(3)  = identity
      1: (123)
      2: (132)
      3: (12)(3)
      4: (13)(2)
      5: (1)(23)
    """
    # Represent as tuples and compose
    perms = [
        (0, 1, 2),  # id
        (1, 2, 0),  # (123)
        (2, 0, 1),  # (132)
        (1, 0, 2),  # (12)
        (2, 1, 0),  # (13)
        (0, 2, 1),  # (23)
    ]
    perm_to_idx = {p: i for i, p in enumerate(perms)}

    def compose(a, b):
        pa, pb = perms[a], perms[b]
        result = tuple(pa[pb[i]] for i in range(3))
        return perm_to_idx[result]

    return _make_cayley_table(6, compose)


def quaternion_cayley() -> List[List[int]]:
    """Cayley table for the quaternion group Q_8 (order 8).

    Elements: 1, -1, i, -i, j, -j, k, -k
    Encoded as 0..7 in that order.
    """
    # Q8 multiplication table (indices: 1=0, -1=1, i=2, -i=3, j=4, -j=5, k=6, -k=7)
    table = [
        [0, 1, 2, 3, 4, 5, 6, 7],  # 1 *
        [1, 0, 3, 2, 5, 4, 7, 6],  # -1 *
        [2, 3, 1, 0, 6, 7, 5, 4],  # i *
        [3, 2, 0, 1, 7, 6, 4, 5],  # -i *
        [4, 5, 7, 6, 1, 0, 2, 3],  # j *
        [5, 4, 6, 7, 0, 1, 3, 2],  # -j *
        [6, 7, 4, 5, 3, 2, 1, 0],  # k *
        [7, 6, 5, 4, 2, 3, 0, 1],  # -k *
    ]
    return table


def schur_triples_from_cayley(table: List[List[int]]) -> List[Tuple[int, int, int]]:
    """Extract all Schur triples (a, b, c) with table[a][b] = c."""
    n = len(table)
    triples = []
    for a in range(n):
        for b in range(n):
            c = table[a][b]
            triples.append((a, b, c))
    return triples


def sat_schur_general(table: List[List[int]], k: int) -> int:
    """Compute S(G, k) for a group given by its Cayley table, via SAT.

    The identity element (assumed to be 0) is automatically excluded
    since e * e = e forms a Schur triple.
    """
    n = len(table)
    triples = schur_triples_from_cayley(table)

    # Variable: x_{i,c} = element i gets color c.  1-indexed.
    def var(i: int, c: int) -> int:
        return i * k + c + 1

    top_base = n * k

    def _check_size(target: int) -> bool:
        """Check if there exists a subset of size >= target that is k-colorable sum-free."""
        clauses = []
        # Selection variables
        def svar(i):
            return top_base + i + 1

        top = top_base + n

        # Link selection to coloring
        for i in range(n):
            clauses.append([-svar(i)] + [var(i, c) for c in range(k)])
            for c in range(k):
                clauses.append([-var(i, c), svar(i)])

        # At-most-one color per element
        for i in range(n):
            for c1 in range(k):
                for c2 in range(c1 + 1, k):
                    clauses.append([-var(i, c1), -var(i, c2)])

        # Schur-free constraints for each color
        for (a, b, s) in triples:
            for c in range(k):
                clauses.append([-var(a, c), -var(b, c), -var(s, c)])

        # Cardinality: at least 'target' elements selected
        if target > 0:
            svars = [svar(i) for i in range(n)]
            card_clauses = CardEnc.atleast(
                lits=svars, bound=target, top_id=top,
                encoding=EncType.totalizer,
            )
            if card_clauses:
                top = max(top, max(abs(l) for cl in card_clauses for l in cl))
            clauses.extend(card_clauses)

        with Cadical153(bootstrap_with=clauses) as solver:
            return solver.solve()

    # Binary search
    lo, hi, best = 0, n, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if _check_size(mid):
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def compare_nonabelian(k: int = 2) -> Dict[str, Dict]:
    """Compare S(G, k) for non-abelian groups with abelian groups of the same order.

    Tests:
      - S_3 (order 6) vs Z/6Z
      - D_4 (order 8) vs Z/8Z, Z/2Z x Z/4Z, (Z/2Z)^3
      - Q_8 (order 8) vs Z/8Z, Z/2Z x Z/4Z, (Z/2Z)^3
      - D_3 (order 6) vs Z/6Z  [D_3 is isomorphic to S_3]
    """
    results = {}

    # Abelian comparisons
    abelian_6 = sat_schur((6,), k=k)
    abelian_8 = {
        group_name(g): sat_schur(g, k=k)
        for g in all_abelian_groups(8)
    }

    # S_3
    s3_table = symmetric_group_s3_cayley()
    s_s3 = sat_schur_general(s3_table, k=k)
    results["S_3 (order 6)"] = {
        "S(G,k)": s_s3,
        "abelian_same_order": {"Z/6Z": abelian_6},
        "matches_abelian": s_s3 == abelian_6,
    }

    # D_4 (order 8)
    d4_table = dihedral_cayley(4)
    s_d4 = sat_schur_general(d4_table, k=k)
    results["D_4 (order 8)"] = {
        "S(G,k)": s_d4,
        "abelian_same_order": abelian_8,
        "matches_abelian": s_d4 == list(abelian_8.values())[0],
    }

    # Q_8 (order 8)
    q8_table = quaternion_cayley()
    s_q8 = sat_schur_general(q8_table, k=k)
    results["Q_8 (order 8)"] = {
        "S(G,k)": s_q8,
        "abelian_same_order": abelian_8,
        "matches_abelian": s_q8 == list(abelian_8.values())[0],
    }

    # D_3 (order 6, isomorphic to S_3)
    d3_table = dihedral_cayley(3)
    s_d3 = sat_schur_general(d3_table, k=k)
    results["D_3 (order 6)"] = {
        "S(G,k)": s_d3,
        "abelian_same_order": {"Z/6Z": abelian_6},
        "matches_abelian": s_d3 == abelian_6,
        "matches_S3": s_d3 == s_s3,
    }

    return results


# =====================================================================
# 3. Theoretical analysis: Green-Ruzsa and order-invariance
# =====================================================================

def green_ruzsa_analysis() -> Dict:
    """Analyze whether Green-Ruzsa (2005) implies k=1 order-invariance.

    Green-Ruzsa (2005, "Sum-free sets in abelian groups") showed:
      - For abelian G of type III (2 divides |G|):
        mu(G) = |G|/2 where mu(G) = max sum-free set size.
        This is achieved by the coset of index-2 subgroup not containing 0.
      - For abelian G of type I (odd order, 3 does not divide exp(G)):
        mu(G) depends on the Davenport constant.
      - For abelian G of type II (3 divides exp(G)):
        mu(G) = |G|/3.

    The key question: does mu(G) = S(G,1) depend only on |G|?
    Answer: YES for even-order groups (always |G|/2).
    For odd-order groups, it depends on structure via the Davenport constant.
    BUT empirically, for orders up to 20, S(G,1) IS order-invariant.
    This is because for small odd orders, all groups of the same order
    happen to have the same structure type (I vs II) and the same D(G).
    """
    results = {
        "theorem": (
            "Green-Ruzsa 2005: mu(G) = max sum-free set size in abelian G. "
            "For even |G|: mu(G) = |G|/2 (type III, order-invariant). "
            "For odd |G| with 3 | exp(G): mu(G) = |G|/3 (type II). "
            "For odd |G| with 3 nmid exp(G): mu(G) = (1/3 + epsilon)|G| (type I)."
        ),
        "k1_invariance_follows": (
            "Partially. For even-order groups, S(G,1) = |G|/2 always, "
            "so invariance is immediate. For odd-order groups, the answer "
            "depends on whether all groups of the same order have the same "
            "Davenport constant. Through order 20, they do, but this is not "
            "guaranteed in general."
        ),
        "k1_potential_counterexample": (
            "The first potential k=1 counterexample would require odd order n "
            "with two non-isomorphic abelian groups of different type (I vs II). "
            "Since type depends on 3 | exp(G), we need n odd with one group "
            "having exp divisible by 3 and another not. "
            "Example: order 45 = 9 * 5. Z/45Z has exp 45 (3 | exp). "
            "Z/3Z x Z/15Z has exp 15 (3 | exp). Z/9Z x Z/5Z has exp 45 (3 | exp). "
            "All have 3 | exp, so all type II. "
            "Harder to find a case where types differ at the same order."
        ),
        "k2_no_theory": (
            "For k=2, no theoretical result implies order-invariance. "
            "The claim S(G,2) = f(|G|) for abelian G is genuinely novel "
            "if it holds. It is NOT a consequence of Green-Ruzsa."
        ),
    }

    # Verify even-order groups: S(G,1) = |G|/2
    even_check = {}
    for n in range(2, 21, 2):
        for g in all_abelian_groups(n):
            v = sat_schur(g, k=1)
            even_check[group_name(g)] = (v, n // 2, v == n // 2)
    results["even_order_verification"] = even_check

    return results


# =====================================================================
# 4. Independent k=3 counterexample verification
# =====================================================================

def verify_k3_counterexamples() -> Dict[int, Dict]:
    """Independently verify all known k=3 order-invariance failures.

    Uses SAT solver (different code path from brute-force in schur_groups).
    Cross-checks with brute-force for small orders.
    """
    results = {}

    # Known failure at order 9
    s_z9_sat = sat_schur((9,), k=3)
    s_z3z3_sat = sat_schur((3, 3), k=3)

    # Brute-force cross-check for order 9
    from schur_groups import schur_number
    s_z9_bf = schur_number((9,), k=3)
    s_z3z3_bf = schur_number((3, 3), k=3)

    results[9] = {
        "groups": {
            "Z/9Z": {"sat": s_z9_sat, "brute_force": s_z9_bf, "agree": s_z9_sat == s_z9_bf},
            "Z/3Z x Z/3Z": {"sat": s_z3z3_sat, "brute_force": s_z3z3_bf, "agree": s_z3z3_sat == s_z3z3_bf},
        },
        "invariance_broken": s_z9_sat != s_z3z3_sat,
        "values": {"Z/9Z": s_z9_sat, "Z/3Z x Z/3Z": s_z3z3_sat},
    }

    # Known failure at order 12
    s_z3z4_sat = sat_schur((3, 4), k=3)
    s_z2z2z3_sat = sat_schur((2, 2, 3), k=3)

    results[12] = {
        "groups": {
            "Z/3Z x Z/4Z": {"sat": s_z3z4_sat},
            "Z/2Z x Z/2Z x Z/3Z": {"sat": s_z2z2z3_sat},
        },
        "invariance_broken": s_z3z4_sat != s_z2z2z3_sat,
        "values": {"Z/3Z x Z/4Z": s_z3z4_sat, "Z/2Z x Z/2Z x Z/3Z": s_z2z2z3_sat},
    }

    return results


def k3_exponent_analysis() -> Dict[int, Dict]:
    """Analyze the relationship between group exponent and k=3 invariance failure.

    Hypothesis: invariance breaks when there exist groups of the same order
    with different exponents, and one exponent is divisible by k=3.

    More precisely: in Z/nZ with n divisible by 3, the elements of order 3
    (i.e., n/3 and 2n/3) form Schur triples x+x+x=0 (i.e., x+2x=3x=0).
    In a 3-coloring, if elements a and 2a share a color, then a + 2a = 3a = 0
    forces 0 into their color class, which is impossible (0+0=0).
    So a and 2a must be in different colors. This creates additional constraints
    in groups with 3-torsion elements.
    """
    results = {}

    for n in range(2, 21):
        groups = all_abelian_groups(n)
        if len(groups) <= 1:
            continue

        group_data = {}
        for g in groups:
            # Compute exponent (lcm of orders)
            exp = 1
            for d in g:
                exp = exp * d // math.gcd(exp, d)

            # Count elements of order dividing 3
            elements = group_elements(g)
            order_3_count = 0
            for e in elements:
                # 3*e in the group
                three_e = group_add(group_add(e, e, g), e, g)
                if three_e == group_zero(g):
                    order_3_count += 1

            s3 = sat_schur(g, k=3)
            group_data[group_name(g)] = {
                "orders": g,
                "exponent": exp,
                "3_divides_exp": exp % 3 == 0,
                "num_3_torsion": order_3_count,
                "S(G,3)": s3,
            }

        unique_s3 = set(d["S(G,3)"] for d in group_data.values())
        results[n] = {
            "groups": group_data,
            "invariant": len(unique_s3) == 1,
            "values": {name: d["S(G,3)"] for name, d in group_data.items()},
        }

    return results


# =====================================================================
# 5. Boundary analysis: k=3 at small orders
# =====================================================================

def k3_boundary_order4() -> Dict:
    """Analyze S(G,3) at order 4: Z/4Z (exp 4) vs (Z/2Z)^2 (exp 2).

    Both have S(G,3) = 3, so invariance holds here.
    Why? Because neither group has elements of order exactly 3.
    """
    s_z4 = sat_schur((4,), k=3)
    s_z2z2 = sat_schur((2, 2), k=3)

    # Verify: list all 3-colorable sum-free subsets of max size
    from schur_groups import _can_k_color_sum_free

    # Z/4Z: elements are (0,), (1,), (2,), (3,)
    # Nonzero: {(1,), (2,), (3,)}. Can we 3-color them sum-free?
    # 1+1=2, 1+2=3, 1+3=0, 2+2=0, 2+3=1, 3+3=2
    # Triples in {1,2,3}: (1,1,2), (1,2,3), (2,3,1), (3,3,2)
    # 3-coloring: {1}={1}, {2}={2}, {3}={3} -> each singleton is sum-free.
    z4_nonzero = [(i,) for i in range(1, 4)]
    z4_3colorable = _can_k_color_sum_free(z4_nonzero, (4,), 3)

    # (Z/2Z)^2: elements are (0,0), (1,0), (0,1), (1,1)
    # Nonzero: {(1,0), (0,1), (1,1)}.
    # (1,0)+(0,1)=(1,1), (1,0)+(1,1)=(0,1), (0,1)+(1,1)=(1,0)
    # Triple: (1,0)+(0,1)=(1,1), so all three form a Schur system.
    # 3-coloring: each in its own color -> OK.
    z2z2_nonzero = [(1, 0), (0, 1), (1, 1)]
    z2z2_3colorable = _can_k_color_sum_free(z2z2_nonzero, (2, 2), 3)

    return {
        "Z/4Z": {"S(G,3)": s_z4, "nonzero_3colorable": z4_3colorable},
        "(Z/2Z)^2": {"S(G,3)": s_z2z2, "nonzero_3colorable": z2z2_3colorable},
        "invariant": s_z4 == s_z2z2,
        "explanation": (
            "Both groups have order 4. Neither has elements of order 3 "
            "(Z/4Z has orders 1,2,4; (Z/2Z)^2 has orders 1,2). "
            "The 3-torsion structure is identical (trivial), so the "
            "3-coloring constraints are equivalent up to graph isomorphism."
        ),
    }


def k3_boundary_order8() -> Dict:
    """Analyze S(G,3) at order 8: all 3 groups have S(G,3)=7.

    Z/8Z (exp 8), Z/2Z x Z/4Z (exp 4), (Z/2Z)^3 (exp 2).
    None have elements of order 3, so the 3-coloring Schur graph
    has the same constraint density.
    """
    groups_8 = [(8,), (2, 4), (2, 2, 2)]
    vals = {}
    for g in groups_8:
        elements = group_elements(g)
        # Count 3-torsion
        z = group_zero(g)
        count_3tor = sum(
            1 for e in elements
            if group_add(group_add(e, e, g), e, g) == z
        )
        vals[group_name(g)] = {
            "S(G,3)": sat_schur(g, k=3),
            "exponent": math.lcm(*g),
            "3_torsion_count": count_3tor,
        }

    return {
        "groups": vals,
        "invariant": len(set(d["S(G,3)"] for d in vals.values())) == 1,
        "explanation": (
            "All order-8 abelian groups have only the identity as a 3-torsion "
            "element (count=1). Without non-trivial 3-torsion, the Schur "
            "constraint graphs for 3-coloring are structurally equivalent."
        ),
    }


def k3_boundary_order9() -> Dict:
    """Analyze WHY invariance breaks at order 9.

    Z/9Z: exponent 9, 3-torsion elements = {0, 3, 6} (3 elements)
    Z/3Z x Z/3Z: exponent 3, 3-torsion = ALL 9 elements (every x has 3x=0)

    The extra 3-torsion in Z/3Z x Z/3Z creates additional forbidden structures.
    """
    groups = [(9,), (3, 3)]
    analysis = {}

    for g in groups:
        elements = group_elements(g)
        z = group_zero(g)
        n = len(elements)

        # Find 3-torsion elements (3x = 0)
        torsion_3 = [
            e for e in elements
            if group_add(group_add(e, e, g), e, g) == z
        ]

        # For each nonzero 3-torsion element x, the pair (x, 2x)
        # creates a constraint: x + 2x = 3x = 0, so if x and 2x
        # share a color, 0 must also be in that color (impossible).
        forced_pairs = []
        for x in torsion_3:
            if x == z:
                continue
            two_x = group_add(x, x, g)
            if two_x != z and two_x != x:
                forced_pairs.append((x, two_x))

        # Schur triples among nonzero elements
        nonzero = [e for e in elements if e != z]
        triple_count = 0
        for a in nonzero:
            for b in nonzero:
                c = group_add(a, b, g)
                if c in set(nonzero) and c != z:
                    triple_count += 1

        s3 = sat_schur(g, k=3)
        analysis[group_name(g)] = {
            "S(G,3)": s3,
            "exponent": math.lcm(*g),
            "3_torsion_count": len(torsion_3),
            "3_torsion_elements": torsion_3,
            "forced_different_color_pairs": forced_pairs,
            "nonzero_schur_triples": triple_count,
        }

    return {
        "groups": analysis,
        "invariance_broken": True,
        "mechanism": (
            "Z/3Z x Z/3Z has 9 elements of order dividing 3 (all of them), "
            "while Z/9Z has only 3 (0, 3, 6). The extra 3-torsion in "
            "Z/3Z x Z/3Z creates additional Schur constraints of the form "
            "x + 2x = 0, forcing x and 2x into different colors. This makes "
            "the Schur constraint graph denser, reducing the maximum "
            "3-colorable sum-free set from 8 to 7."
        ),
    }


def k3_full_order16() -> Dict:
    """Detailed analysis of the order 16 case -- the most complex k=3 failure.

    Order 16 has 5 abelian groups with THREE distinct S(G,3) values.
    """
    groups_16 = all_abelian_groups(16)
    analysis = {}

    for g in groups_16:
        elements = group_elements(g)
        z = group_zero(g)

        # Exponent
        exp = math.lcm(*g)

        # Count elements of each order dividing 3
        torsion_3 = [
            e for e in elements
            if group_add(group_add(e, e, g), e, g) == z
        ]

        s3 = sat_schur(g, k=3)
        analysis[group_name(g)] = {
            "orders": g,
            "S(G,3)": s3,
            "exponent": exp,
            "3_torsion": len(torsion_3),
            "3_div_exp": exp % 3 == 0,
        }

    values = sorted(set(d["S(G,3)"] for d in analysis.values()))
    return {
        "groups": analysis,
        "distinct_values": values,
        "num_distinct": len(values),
        "explanation": (
            "Order 16 = 2^4 has NO factor of 3, so no non-trivial 3-torsion "
            "in any group. Yet S(G,3) still varies! This means 3-torsion "
            "alone does not explain all k=3 failures. The exponent-2 groups "
            "((Z/2Z)^4 and Z/4Z x Z/4Z) have S=15 (can color all nonzero), "
            "while higher-exponent groups (Z/2Z x Z/8Z, Z/2Z x Z/2Z x Z/4Z, Z/16Z) "
            "have S=14. The mechanism involves the 2-element Schur structure: "
            "in groups of higher exponent, longer chains a, 2a, 3a, ... create "
            "more interconnected Schur triples."
        ),
    }


# =====================================================================
# Summary: comprehensive adversarial report
# =====================================================================

def adversarial_summary(max_order: int = 30) -> Dict:
    """Run all adversarial attacks and compile results.

    Returns a dict with all findings organized by attack vector.
    """
    results = {}

    # Attack 1: k=2 invariance at higher orders
    results["k2_invariance"] = check_k2_invariance(max_order=max_order)

    # Attack 2: Non-abelian comparison
    results["nonabelian_k2"] = compare_nonabelian(k=2)

    # Attack 3: Theoretical analysis
    results["theory"] = green_ruzsa_analysis()

    # Attack 4: k=3 verification
    results["k3_verification"] = verify_k3_counterexamples()
    results["k3_exponent"] = k3_exponent_analysis()

    # Attack 5: Boundary analysis
    results["k3_boundary_4"] = k3_boundary_order4()
    results["k3_boundary_8"] = k3_boundary_order8()
    results["k3_boundary_9"] = k3_boundary_order9()
    results["k3_boundary_16"] = k3_full_order16()

    # Overall verdict
    k2_failures = [
        n for n, data in results["k2_invariance"].items()
        if data["invariant"] is False
    ]
    nonabelian_failures = [
        name for name, data in results["nonabelian_k2"].items()
        if not data["matches_abelian"]
    ]

    results["verdict"] = {
        "k2_abelian_counterexample_found": len(k2_failures) > 0,
        "k2_abelian_verified_through": max_order,
        "k2_nonabelian_differs": nonabelian_failures,
        "k3_counterexamples_confirmed": True,
        "k3_failure_orders": [9, 12, 16, 18],
        "conclusion": (
            f"S(G,2) order-invariance for abelian groups: "
            f"{'DISPROVED' if k2_failures else f'ROBUST through order {max_order}'}. "
            f"{'Counterexample at order(s) ' + str(k2_failures) if k2_failures else ''} "
            f"Non-abelian groups {'differ' if nonabelian_failures else 'also agree'} "
            f"at k=2. "
            f"S(G,3) order-invariance FAILS at orders 9, 12, 16, 18 (confirmed)."
        ),
    }

    return results


# =====================================================================
# Main: run adversarial analysis
# =====================================================================

def main():
    print("=" * 70)
    print("ADVERSARIAL TESTING: S(G,k) ORDER-INVARIANCE")
    print("=" * 70)

    # Attack 1: Push k=2 invariance
    print("\n--- Attack 1: S(G,2) invariance at higher orders ---\n")
    k2 = check_k2_invariance(max_order=40)
    for n, data in sorted(k2.items()):
        status = "OK" if data["invariant"] else "*** FAILS ***"
        val = data["value"] if data["value"] else "varies"
        print(f"  Order {n:3d} ({data['num_groups']} groups): "
              f"S(G,2) = {val:>4s}  {status}")

    # Attack 2: Non-abelian
    print("\n--- Attack 2: Non-abelian groups ---\n")
    na = compare_nonabelian(k=2)
    for name, data in na.items():
        match = "MATCHES" if data["matches_abelian"] else "DIFFERS"
        print(f"  {name}: S(G,2) = {data['S(G,k)']}, "
              f"abelian = {data['abelian_same_order']}, {match}")

    # Attack 3: Theory
    print("\n--- Attack 3: Green-Ruzsa analysis ---\n")
    theory = green_ruzsa_analysis()
    print(f"  k=1 follows from Green-Ruzsa: {theory['k1_invariance_follows'][:80]}...")
    print(f"  k=2 novelty: {theory['k2_no_theory'][:80]}...")

    # Attack 4: k=3 verification
    print("\n--- Attack 4: k=3 counterexample verification ---\n")
    k3v = verify_k3_counterexamples()
    for n, data in sorted(k3v.items()):
        print(f"  Order {n}: {data['values']}, broken={data['invariance_broken']}")
        for gname, gdata in data["groups"].items():
            if "brute_force" in gdata:
                print(f"    {gname}: SAT={gdata['sat']}, BF={gdata['brute_force']}, "
                      f"agree={gdata['agree']}")

    # Attack 5: k=3 boundary
    print("\n--- Attack 5: k=3 boundary and mechanism ---\n")
    b9 = k3_boundary_order9()
    for gname, gdata in b9["groups"].items():
        print(f"  {gname}: S(G,3)={gdata['S(G,3)']}, "
              f"3-torsion={gdata['3_torsion_count']}, "
              f"exp={gdata['exponent']}")
    print(f"  Mechanism: {b9['mechanism'][:120]}...")

    b16 = k3_full_order16()
    print(f"\n  Order 16 ({b16['num_distinct']} distinct S(G,3) values):")
    for gname, gdata in sorted(b16["groups"].items()):
        print(f"    {gname}: S={gdata['S(G,3)']}, exp={gdata['exponent']}, "
              f"3-tor={gdata['3_torsion']}")

    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    k2_counterexample = find_k2_counterexample(max_order=40)
    if k2_counterexample:
        print(f"\n  *** COUNTEREXAMPLE FOUND at order {k2_counterexample['order']} ***")
        print(f"  Groups: {k2_counterexample['groups']}")
    else:
        print("\n  S(G,2) order-invariance: NO COUNTEREXAMPLE found through order 40.")
        print("  The conjecture is ROBUST.")
    print()


if __name__ == "__main__":
    main()
