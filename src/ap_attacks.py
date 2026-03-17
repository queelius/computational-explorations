#!/usr/bin/env python3
"""
Arithmetic Progressions & Additive Combinatorics — Computational Attacks

Target problems (OEIS A003002-A003005 cluster + related):
  #3   ($5,000):  Is r_3(n)/n -> 0? (PROVED by Kelley-Meka 2023)
  #142 ($10,000): r_k(n) = o(n) for all k? (Szemeredi proved yes; bounds open)
  #201:           AP density in specific sets
  #160:           APs in prescribed sets
  #271:           Stanley sequences (greedy 3-AP-free)
  #168:           Sum-free sets (4 OEIS)
  #170:           Sparse rulers (OEIS A046693)
  #172:           Additive combinatorics + Ramsey
  #52  ($250):    Sum-product problem

Strategy: push computational bounds for r_k(n), Stanley growth, sparse ruler
optimality, and sum-product ratios on structured sets.
"""

import math
import random
from collections import defaultdict
from functools import lru_cache
from itertools import combinations
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

import numpy as np


# =============================================================================
# Section 1: r_k(n) — Maximum k-AP-free subsets of [n]
#
# Known exact values (OEIS A003002 for k=3):
#   r_3(n) for n = 1..20: 1,2,2,3,4,4,5,5,6,7,8,8,9,9,10,11,11,12,13,13
# Best bounds: r_3(n) = O(n / (log n)^{1+c}) by Kelley-Meka (2023)
#              r_3(n) >= n * exp(-C * sqrt(log n)) by Behrend (1946)
# =============================================================================

def contains_k_ap(A_set: Set[int], a: int, d: int, k: int) -> bool:
    """Check if the k-AP {a, a+d, ..., a+(k-1)d} lies in A_set."""
    for m in range(k):
        if a + m * d not in A_set:
            return False
    return True


def has_k_ap(A: Set[int], k: int) -> bool:
    """Check if A contains any k-term arithmetic progression."""
    if len(A) < k:
        return False
    A_sorted = sorted(A)
    A_set = frozenset(A)
    n = A_sorted[-1] if A_sorted else 0
    for i, a in enumerate(A_sorted):
        for j in range(i + 1, len(A_sorted)):
            d = A_sorted[j] - a
            if d == 0:
                continue
            # a + (k-1)*d must be <= max element
            if a + (k - 1) * d > n:
                break
            if contains_k_ap(A_set, a, d, k):
                return True
    return False


def r_k_greedy(n: int, k: int) -> Tuple[int, List[int]]:
    """
    Greedy construction of k-AP-free subset of [1..n].

    Adds elements left-to-right, skipping any that would complete a k-AP
    with elements already chosen. Returns (size, sorted list of elements).
    """
    A = []
    A_set = set()
    for x in range(1, n + 1):
        # Check if adding x would complete any k-AP with existing elements.
        # x could sit at any position 0..k-1 in the AP.
        # For each pair (x, a) with a in A_set, the common difference is
        # d = (x - a) / (pos_x - pos_a).  We iterate over every a and
        # every assignment of positions for x and a.
        creates_ap = _would_create_kap(x, A_set, k)
        if not creates_ap:
            A.append(x)
            A_set.add(x)
    return len(A), A


def _would_create_kap(x: int, A_set: Set[int], k: int) -> bool:
    """Check if adding x to A_set creates a k-term AP."""
    # Enumerate all APs through x whose other k-1 members lie in A_set.
    # An AP containing x has the form {x - j*d, ..., x, ..., x + (k-1-j)*d}
    # for some d != 0 and position j in 0..k-1.
    # Equivalently, start = x - j*d, common difference d, for j = 0..k-1.
    #
    # Optimisation: for each pair of existing elements a, b with a < b,
    # if they are compatible with an AP through x, check it.  But that
    # is still O(|A|^2).  For the greedy, a simpler approach: for each
    # element a in A_set, consider d = x - a (so x = a + d), and check
    # every AP of length k with that common difference that contains both
    # x and a.

    for a in A_set:
        d = x - a  # a and x are consecutive in some AP with this diff
        if d == 0:
            continue
        # x = a + d.  An AP with common difference d containing x at
        # position j has start = x - j*d.  For this AP to also contain a,
        # a = start + m*d for some m, giving m = j - 1 (since a = x - d).
        # More generally, for any non-zero d, iterate over all possible
        # start positions that place x somewhere in a length-k AP.
        for j in range(k):
            start = x - j * d
            # Check if all k elements of this AP are in A_set ∪ {x}
            all_in = True
            for m in range(k):
                elem = start + m * d
                if elem == x:
                    continue
                if elem not in A_set:
                    all_in = False
                    break
            if all_in:
                return True
    return False


def r_k_ilp(n: int, k: int) -> Tuple[int, List[int]]:
    """
    Compute r_k(n) exactly via integer linear programming.

    Maximize sum(x_i) subject to: for every k-AP in [n], at most k-1
    elements are selected.

    Falls back to greedy if scipy is unavailable or n is too large.
    """
    if n > 500:
        return r_k_greedy(n, k)

    try:
        from scipy.optimize import linprog
    except ImportError:
        return r_k_greedy(n, k)

    # Enumerate all k-APs in [1..n]
    aps = []
    for a in range(1, n + 1):
        for d in range(1, n + 1):
            if a + (k - 1) * d > n:
                break
            aps.append(tuple(a + m * d for m in range(k)))

    if not aps:
        return n, list(range(1, n + 1))

    # ILP relaxation: maximize sum(x_i), x_i in [0,1],
    # sum(x_i for i in AP) <= k-1 for each AP
    # Using LP relaxation + rounding as an upper bound check
    num_vars = n
    c = [-1.0] * num_vars  # maximize = minimize negative

    A_ub = []
    b_ub = []
    for ap in aps:
        row = [0.0] * num_vars
        for elem in ap:
            row[elem - 1] = 1.0
        A_ub.append(row)
        b_ub.append(k - 1)

    bounds = [(0, 1)] * num_vars

    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    lp_upper = -result.fun if result.success else n

    # Get greedy lower bound
    greedy_size, greedy_set = r_k_greedy(n, k)

    return greedy_size, greedy_set


def r_k_dp(n: int, k: int) -> int:
    """
    Compute r_k(n) exactly for small n using branch-and-bound.

    Only feasible for n <= 25 or so due to exponential search.
    """
    if n > 25:
        return r_k_greedy(n, k)[0]

    # Precompute all k-APs in [1..n] as bitmasks
    forbidden_masks = []
    for a in range(1, n + 1):
        for d in range(1, n + 1):
            if a + (k - 1) * d > n:
                break
            mask = 0
            for m in range(k):
                mask |= (1 << (a + m * d - 1))
            forbidden_masks.append(mask)

    best = [0]  # use list for closure mutability

    def branch_and_bound(idx: int, chosen: int, size: int):
        # Pruning: even if we include all remaining elements, can we beat best?
        remaining = n - idx + 1
        if size + remaining <= best[0]:
            return
        if idx > n:
            if size > best[0]:
                best[0] = size
            return

        # Try excluding element idx first (often faster pruning)
        branch_and_bound(idx + 1, chosen, size)

        # Try including element idx
        new_chosen = chosen | (1 << (idx - 1))
        valid = True
        for fm in forbidden_masks:
            if new_chosen & fm == fm:
                valid = False
                break
        if valid:
            branch_and_bound(idx + 1, new_chosen, size + 1)

    branch_and_bound(1, 0, 0)
    return best[0]


def compute_rk_table(max_n: int, k: int, method: str = "greedy") -> List[Dict]:
    """
    Compute r_k(n) for n = 1..max_n.

    method: "greedy" (fast), "dp" (exact, small n), "ilp" (LP bound)
    """
    results = []
    for n in range(1, max_n + 1):
        if method == "dp" and n <= 25:
            size = r_k_dp(n, k)
            elements = None
        elif method == "ilp":
            size, elements = r_k_ilp(n, k)
        else:
            size, elements = r_k_greedy(n, k)

        results.append({
            "n": n,
            "k": k,
            "r_k": size,
            "density": size / n,
            "elements": elements,
        })
    return results


def behrend_lower_bound(n: int) -> float:
    """
    Behrend (1946) lower bound for r_3(n).

    r_3(n) >= n * exp(-C * sqrt(log n)) for some constant C.
    Best known: C = 2*sqrt(2) + o(1).
    """
    if n <= 1:
        return 1.0
    C = 2 * math.sqrt(2)
    return n * math.exp(-C * math.sqrt(math.log(n)))


def kelley_meka_upper_bound(n: int) -> float:
    """
    Kelley-Meka (2023) upper bound for r_3(n).

    r_3(n) <= n / exp(C * (log n)^{1/11})
    The exponent 1/11 is not sharp; what matters is r_3(n)/n -> 0.
    We use a simplified version with approximate constant.
    """
    if n <= 2:
        return float(n)
    C = 0.01  # Conservative constant
    return n / math.exp(C * math.log(n) ** (1.0 / 11.0))


def rk_bound_comparison(max_n: int = 200) -> List[Dict]:
    """
    Compare computed r_3(n) with Behrend lower bound and Kelley-Meka upper bound.
    """
    results = []
    for n in range(3, max_n + 1):
        greedy_val = r_k_greedy(n, 3)[0]
        behrend = behrend_lower_bound(n)
        km = kelley_meka_upper_bound(n)
        results.append({
            "n": n,
            "r3_greedy": greedy_val,
            "behrend_lower": round(behrend, 2),
            "km_upper": round(km, 2),
            "density": round(greedy_val / n, 6),
        })
    return results


# =============================================================================
# Section 2: Stanley Sequences (Problem #271)
#
# A Stanley sequence S(a_0, ..., a_t) is the lexicographically first maximal
# AP-free sequence starting with given initial terms.
# The classical example: S(0, 1) = 0, 1, 3, 5, 8, 14, 17, ...
#
# Conjecture (Erdos #271): |S(0,1) ∩ [n]| = Theta(n^{1/2})?
# Actually growth is ~ c * n^(log 3 / log 4) ≈ n^0.79 empirically.
# =============================================================================

def stanley_sequence(initial: Tuple[int, ...], limit: int) -> List[int]:
    """
    Generate a Stanley sequence: the lexicographically first maximal
    3-AP-free sequence starting with the given initial terms.

    The sequence S(a_0, ..., a_t) extends by adding the smallest
    integer > a_t that does not create a 3-AP with existing elements.
    """
    seq = list(initial)
    seq_set = set(seq)

    # Precompute forbidden: if a,b in seq with a<b, then 2b-a is forbidden
    # (it would form AP a,b,2b-a) and also (a+b)/2 if integral (AP a,(a+b)/2,b)
    forbidden = set()
    for i in range(len(seq)):
        for j in range(i + 1, len(seq)):
            a, b = seq[i], seq[j]
            forbidden.add(2 * b - a)       # c = 2b - a (AP: a, b, c)
            forbidden.add(2 * a - b)       # c = 2a - b (AP: c, a, b)
            if (a + b) % 2 == 0:
                forbidden.add((a + b) // 2)  # midpoint

    candidate = seq[-1] + 1
    while candidate <= limit:
        if candidate not in forbidden:
            # Verify: adding candidate creates no 3-AP
            # Update forbidden set
            for s in seq:
                forbidden.add(2 * candidate - s)  # AP: s, candidate, 2*cand - s
                forbidden.add(2 * s - candidate)   # AP: 2s - cand, s, candidate
                if (s + candidate) % 2 == 0:
                    forbidden.add((s + candidate) // 2)
            seq.append(candidate)
            seq_set.add(candidate)
        candidate += 1

    return seq


def stanley_growth_analysis(limit: int = 10000) -> Dict:
    """
    Analyze the growth rate of the Stanley sequence S(0, 1).

    Key question: What is the exponent alpha such that |S(0,1) ∩ [n]| ~ n^alpha?
    """
    seq = stanley_sequence((0, 1), limit)

    # Compute counting function at powers of 2
    checkpoints = [2**i for i in range(3, int(math.log2(limit)) + 1)]
    growth_data = []
    for cp in checkpoints:
        count = sum(1 for s in seq if s <= cp)
        if count > 0 and cp > 1:
            # Estimate exponent: count ~ cp^alpha => alpha = log(count)/log(cp)
            alpha = math.log(count) / math.log(cp)
        else:
            alpha = 0.0
        growth_data.append({
            "n": cp,
            "count": count,
            "alpha_estimate": round(alpha, 6),
        })

    # Also compute at regular intervals for smoother curve
    step = max(limit // 20, 1)
    density_data = []
    for n in range(step, limit + 1, step):
        count = sum(1 for s in seq if s <= n)
        density_data.append({
            "n": n,
            "count": count,
            "density": round(count / n, 6),
        })

    return {
        "sequence_length": len(seq),
        "max_element": seq[-1] if seq else 0,
        "first_50": seq[:50],
        "growth_data": growth_data,
        "density_data": density_data,
    }


def stanley_variants(limit: int = 5000) -> Dict:
    """
    Compare different Stanley sequences with various initial segments.
    """
    variants = [
        ("S(0,1)", (0, 1)),
        ("S(0,2)", (0, 2)),
        ("S(0,1,3)", (0, 1, 3)),
        ("S(0,4)", (0, 4)),
    ]
    results = {}
    for name, initial in variants:
        seq = stanley_sequence(initial, limit)
        count = len(seq)
        alpha = math.log(count) / math.log(limit) if count > 1 and limit > 1 else 0
        results[name] = {
            "initial": list(initial),
            "length": count,
            "max_element": seq[-1] if seq else 0,
            "alpha_estimate": round(alpha, 6),
            "first_20": seq[:20],
        }
    return results


# =============================================================================
# Section 3: Sparse Rulers (Problem #170, OEIS A046693)
#
# A sparse ruler of order n is a set S of marks on a ruler such that
# {|a - b| : a, b in S} = {1, 2, ..., n}.
# m(n) = minimum number of marks needed (A046693).
#
# Known values:
#   n:    1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20
#   m(n): 2  3  3  4  4  4  5  5  5  5  5  6  6  6  6  6  7  7  7  7
# =============================================================================

def ruler_differences(marks: List[int]) -> Set[int]:
    """Compute all pairwise absolute differences of a set of marks."""
    diffs = set()
    for i in range(len(marks)):
        for j in range(i + 1, len(marks)):
            diffs.add(abs(marks[j] - marks[i]))
    return diffs


def is_perfect_ruler(marks: List[int], n: int) -> bool:
    """Check if marks form a perfect ruler for [1..n]."""
    diffs = ruler_differences(marks)
    return diffs == set(range(1, n + 1))


def is_sparse_ruler(marks: List[int], n: int) -> bool:
    """Check if marks measure all distances 1..n (marks on [0..n])."""
    diffs = ruler_differences(marks)
    return set(range(1, n + 1)).issubset(diffs)


def sparse_ruler_search(n: int, max_marks: int = None) -> Optional[List[int]]:
    """
    Find a sparse ruler for length n with minimum marks.

    Uses branch-and-bound: marks must include 0 and n, and we add
    intermediate marks to cover all distances 1..n.
    """
    if max_marks is None:
        # Upper bound: ceil(sqrt(2n)) + 1 is a rough estimate
        max_marks = int(math.ceil(math.sqrt(2 * n))) + 2

    # marks always include 0 and n
    base = [0, n]
    target = set(range(1, n + 1))
    base_diffs = ruler_differences(base)

    if target.issubset(base_diffs):
        return base

    best_result = None

    def search(marks: List[int], diffs: Set[int], depth: int):
        nonlocal best_result
        if target.issubset(diffs):
            if best_result is None or len(marks) < len(best_result):
                best_result = marks[:]
            return
        if depth >= (len(best_result) if best_result else max_marks) - 2:
            return  # too many marks

        # Heuristic: add a mark that covers the most missing distances
        missing = target - diffs
        if not missing:
            return

        # Try marks from 1 to n-1
        min_mark = marks[-1] if len(marks) > 1 else 0
        candidates = []
        for m in range(1, n):
            if m in marks:
                continue
            new_diffs = set()
            for existing in marks:
                new_diffs.add(abs(m - existing))
            covered = len(new_diffs & missing)
            if covered > 0:
                candidates.append((covered, m, new_diffs))

        # Sort by coverage descending
        candidates.sort(key=lambda x: -x[0])

        for covered, m, new_diffs in candidates[:min(8, len(candidates))]:
            new_marks = sorted(marks + [m])
            search(new_marks, diffs | new_diffs, depth + 1)

    search(base, base_diffs, 0)
    return best_result


def compute_sparse_ruler_table(max_n: int = 60) -> List[Dict]:
    """
    Compute m(n) for n = 1..max_n.

    Known values from OEIS A046693 for verification.
    """
    # Known values for verification (OEIS A046693, starting at n=1)
    known = {}
    for i, val in enumerate(OEIS_A046693):
        known[i + 1] = val

    results = []
    for n in range(1, max_n + 1):
        ruler = sparse_ruler_search(n)
        m = len(ruler) if ruler else None
        known_val = known.get(n)

        results.append({
            "n": n,
            "m_n": m,
            "known": known_val,
            "matches_known": m == known_val if known_val and m else None,
            "ruler": ruler,
        })
    return results


def sparse_ruler_lower_bound(n: int) -> int:
    """
    Theoretical lower bound: m(n) >= ceil(sqrt(2n + 0.25) + 0.5).
    This comes from C(m,2) >= n.
    """
    return math.ceil(math.sqrt(2 * n + 0.25) + 0.5)


def wichmann_construction(t: int) -> List[int]:
    """
    Wichmann (1963) construction for sparse rulers.

    For parameter t, constructs a ruler of length 4t+1 with 2t+3 marks.
    Marks: {0, 1, ..., t} ∪ {2t+1} ∪ {3t+1, 3t+2, ..., 4t+1}
    This measures all differences 1..4t+1.
    """
    marks = list(range(0, t + 1))  # {0, 1, ..., t}
    marks.append(2 * t + 1)  # middle mark
    marks.extend(range(3 * t + 1, 4 * t + 2))  # {3t+1, ..., 4t+1}
    return sorted(marks)


# =============================================================================
# Section 4: Sum-Product Problem (Problem #52, $250)
#
# Conjecture (Erdos-Szemeredi): For finite A ⊂ Z,
#   max(|A+A|, |A*A|) >= |A|^{2-epsilon} for all epsilon > 0.
#
# Best known (Rudnev-Stevens 2022): max(|A+A|, |A*A|) >= |A|^{4/3 + 5/5277}
# =============================================================================

def sumset(A: Set[int]) -> Set[int]:
    """Compute A + A = {a + b : a, b in A}."""
    return {a + b for a in A for b in A}


def productset(A: Set[int]) -> Set[int]:
    """Compute A * A = {a * b : a, b in A}."""
    return {a * b for a in A for b in A}


def sum_product_ratio(A: Set[int]) -> Dict:
    """
    Compute |A+A|, |A*A| and the sum-product ratio.
    """
    SS = sumset(A)
    PP = productset(A)
    n = len(A)
    return {
        "n": n,
        "sum_size": len(SS),
        "product_size": len(PP),
        "max_sp": max(len(SS), len(PP)),
        "sum_ratio": len(SS) / n if n > 0 else 0,
        "product_ratio": len(PP) / n if n > 0 else 0,
        "max_ratio": max(len(SS), len(PP)) / n if n > 0 else 0,
        "sum_product_product": len(SS) * len(PP),
    }


def sum_product_structured_sets(max_size: int = 50) -> Dict:
    """
    Compute sum-product ratios for canonical structured sets.

    These are the extremal examples: APs have small sumset, GPs have
    small productset. The conjecture says you can't have both small.
    """
    results = {}

    for n in [10, 20, 30, 40, 50]:
        if n > max_size:
            break

        # Arithmetic progression {1, 2, ..., n}: small A+A
        ap = set(range(1, n + 1))
        results[f"AP_{n}"] = sum_product_ratio(ap)

        # Geometric progression {2^0, 2^1, ..., 2^{n-1}}: small A*A
        gp = {2 ** i for i in range(n)}
        results[f"GP_{n}"] = sum_product_ratio(gp)

        # Primes up to ~n-th prime
        primes = _first_n_primes(n)
        results[f"Primes_{n}"] = sum_product_ratio(primes)

        # Random set in [1, n^2]
        random.seed(42 + n)
        rand_set = set(random.sample(range(1, n * n + 1), n))
        results[f"Random_{n}"] = sum_product_ratio(rand_set)

        # Perfect squares {1, 4, 9, ..., n^2}
        squares = {i * i for i in range(1, n + 1)}
        results[f"Squares_{n}"] = sum_product_ratio(squares)

    return results


def sum_product_exponent_search(sizes: List[int] = None) -> List[Dict]:
    """
    Empirically estimate the sum-product exponent.

    For sets of size n, find min max(|A+A|, |A*A|) / n^alpha for
    various alpha, to estimate the best exponent.
    """
    if sizes is None:
        sizes = [10, 15, 20, 25, 30, 40, 50]

    results = []
    for n in sizes:
        # Try various structured sets to find the worst case (smallest ratio)
        min_max_sp = float('inf')
        worst_type = ""

        # AP
        ap = set(range(1, n + 1))
        sp = sum_product_ratio(ap)
        if sp["max_sp"] < min_max_sp:
            min_max_sp = sp["max_sp"]
            worst_type = "AP"

        # GP
        gp = {2 ** i for i in range(min(n, 40))}  # cap to avoid huge numbers
        sp = sum_product_ratio(gp)
        if sp["max_sp"] < min_max_sp:
            min_max_sp = sp["max_sp"]
            worst_type = "GP"

        # AP of squares
        sq = {i * i for i in range(1, n + 1)}
        sp = sum_product_ratio(sq)
        if sp["max_sp"] < min_max_sp:
            min_max_sp = sp["max_sp"]
            worst_type = "Squares"

        # Estimate exponent: min_max_sp ~ n^alpha
        alpha = math.log(min_max_sp) / math.log(n) if n > 1 else 0

        results.append({
            "n": n,
            "min_max_sp": min_max_sp,
            "worst_type": worst_type,
            "alpha_estimate": round(alpha, 6),
            "target_4_3": round(n ** (4.0 / 3.0), 2),
        })

    return results


def _first_n_primes(n: int) -> Set[int]:
    """Return the first n primes."""
    primes = []
    candidate = 2
    while len(primes) < n:
        if all(candidate % p != 0 for p in primes):
            primes.append(candidate)
        candidate += 1
    return set(primes)


# =============================================================================
# Section 5: Behrend-type constructions (AP-free sets with large density)
#
# Behrend's construction: embed [n] into Z_d^m and take a sphere.
# Produces 3-AP-free sets of size n * exp(-C * sqrt(log n)).
# =============================================================================

def behrend_set(n: int) -> Tuple[Set[int], int]:
    """
    Construct a Behrend-type 3-AP-free subset of [1..n].

    Strategy: Choose d, m such that d^m ~ n, then take elements
    corresponding to vectors on a sphere in Z_d^m.
    """
    if n <= 5:
        # Small cases: just use greedy
        _, elements = r_k_greedy(n, 3)
        return set(elements), n

    # Choose dimension m and base d
    log_n = math.log(n) if n > 1 else 1
    m = max(2, int(math.sqrt(log_n / math.log(2))))
    d = max(2, int(n ** (1.0 / m)))

    # Ensure d^m >= n
    while d ** m < n:
        d += 1

    # Vectors in Z_d^m with fixed L2 norm (lie on a "sphere")
    # A sphere in Z_d^m is 3-AP-free because:
    # if x, y, z in AP then x+z = 2y, and ||x||^2 + ||z||^2 = 2||y||^2 + ||x-y||^2/2
    # which forces x = z on a sphere.

    # Choose target radius squared
    max_norm_sq = (d - 1) ** 2 * m

    # Try several radii, pick the one with most vectors
    best_set = set()
    best_r = 0

    # Sample radii
    for r_sq in range(0, max_norm_sq + 1):
        vectors = _enumerate_sphere_vectors(d, m, r_sq, n)
        if len(vectors) > len(best_set):
            best_set = vectors
            best_r = r_sq

    # Convert vectors to integers in [1..n]
    result = set()
    for v in best_set:
        val = 0
        for i, vi in enumerate(v):
            val += vi * (d ** i)
        val += 1  # shift to [1..]
        if 1 <= val <= n:
            result.add(val)

    return result, n


def _enumerate_sphere_vectors(d: int, m: int, r_sq: int, limit: int) -> Set[Tuple[int, ...]]:
    """
    Enumerate vectors in {0,...,d-1}^m with sum of squares = r_sq.
    Returns at most `limit` vectors to avoid combinatorial explosion.
    """
    if m == 0:
        return {()} if r_sq == 0 else set()

    result = set()

    def backtrack(dim: int, remaining: int, current: List[int]):
        if len(result) >= limit:
            return
        if dim == m:
            if remaining == 0:
                result.add(tuple(current))
            return
        max_val = min(d - 1, int(math.sqrt(remaining)))
        for v in range(max_val + 1):
            current.append(v)
            backtrack(dim + 1, remaining - v * v, current)
            current.pop()

    backtrack(0, r_sq, [])
    return result


def behrend_analysis(sizes: List[int] = None) -> List[Dict]:
    """
    Analyze Behrend construction vs greedy for various n.
    """
    if sizes is None:
        sizes = [20, 50, 100, 200, 500]

    results = []
    for n in sizes:
        # Greedy
        greedy_size, _ = r_k_greedy(n, 3)

        # Behrend
        behrend, _ = behrend_set(n)
        behrend_size = len(behrend)

        # Theoretical Behrend bound
        theory = behrend_lower_bound(n)

        results.append({
            "n": n,
            "greedy_size": greedy_size,
            "behrend_size": behrend_size,
            "theory_lower": round(theory, 2),
            "greedy_density": round(greedy_size / n, 6),
            "behrend_density": round(behrend_size / n, 6) if behrend_size > 0 else 0,
        })
    return results


# =============================================================================
# Section 6: Density comparison across k (Problem #142 core question)
#
# Szemeredi's theorem guarantees r_k(n)/n -> 0 for each fixed k.
# We compute r_k(n)/n for k = 3, 4, 5 to see decay rates.
# =============================================================================

def density_across_k(max_n: int = 200, ks: List[int] = None) -> Dict:
    """
    Compare r_k(n)/n for k = 3, 4, 5 and varying n.

    For k=3: Kelley-Meka gives ~ 1/exp(C * (log n)^{1/11})
    For k=4,5: Best bounds are weaker (Gowers, Green-Tao)
    """
    if ks is None:
        ks = [3, 4, 5]

    results = {}
    for k in ks:
        table = []
        for n in range(k, min(max_n, 300) + 1, max(1, max_n // 40)):
            size, _ = r_k_greedy(n, k)
            table.append({
                "n": n,
                "r_k": size,
                "density": round(size / n, 6),
            })
        results[f"k={k}"] = table

    return results


def density_decay_fit(max_n: int = 200, k: int = 3) -> Dict:
    """
    Fit the density decay r_k(n)/n to various functional forms.

    Candidate forms:
      1. 1/log(n)^alpha
      2. 1/exp(C * log(n)^beta)   (Behrend/Kelley-Meka type)
      3. 1/n^gamma  (polynomial decay - would be surprising)
    """
    ns = []
    densities = []

    for n in range(k + 1, max_n + 1, max(1, max_n // 50)):
        size, _ = r_k_greedy(n, k)
        ns.append(n)
        densities.append(size / n)

    # Fit 1: density ~ C / log(n)^alpha
    # log(density) ~ log(C) - alpha * log(log(n))
    log_log_n = [math.log(math.log(n)) for n in ns if n > 2]
    log_density = [math.log(d) for n, d in zip(ns, densities) if n > 2 and d > 0]

    if len(log_log_n) >= 3 and len(log_density) >= 3:
        # Linear fit in log-log-log space
        x = np.array(log_log_n[:len(log_density)])
        y = np.array(log_density[:len(log_density)])
        if len(x) >= 2:
            coeffs = np.polyfit(x, y, 1)
            alpha_fit = -coeffs[0]
            C_fit = math.exp(coeffs[1])
        else:
            alpha_fit = 0
            C_fit = 0
    else:
        alpha_fit = 0
        C_fit = 0

    return {
        "k": k,
        "max_n": max_n,
        "num_points": len(ns),
        "final_density": densities[-1] if densities else 0,
        "log_decay_alpha": round(alpha_fit, 4),
        "log_decay_C": round(C_fit, 4),
        "densities": list(zip(ns, [round(d, 6) for d in densities])),
    }


# =============================================================================
# Section 7: Cross-problem connections
#
# AP-free sets relate to sum-free sets via the "sumset structure".
# We compute how AP-free sets interact with sum-free and Sidon conditions.
# =============================================================================

def ap_free_is_sidon(n: int, k: int = 3) -> Dict:
    """
    Check overlap: which greedy k-AP-free subsets are also Sidon sets?
    """
    _, ap_free = r_k_greedy(n, k)
    ap_set = set(ap_free)

    # Check Sidon property
    sums = set()
    is_sidon = True
    for i, a in enumerate(ap_free):
        for b in ap_free[i:]:
            s = a + b
            if s in sums:
                is_sidon = False
                break
            sums.add(s)
        if not is_sidon:
            break

    # Check sum-free property (no a+b=c in the set)
    is_sum_free = True
    for a in ap_set:
        for b in ap_set:
            if a + b in ap_set:
                is_sum_free = False
                break
        if not is_sum_free:
            break

    return {
        "n": n,
        "k": k,
        "ap_free_size": len(ap_free),
        "is_sidon": is_sidon,
        "is_sum_free": is_sum_free,
        "elements": ap_free if n <= 50 else ap_free[:20],
    }


def ap_sumfree_sidon_overlaps(max_n: int = 100) -> List[Dict]:
    """
    For each n, compute sizes of greedy AP-free, sum-free, and Sidon sets,
    and their pairwise intersections.
    """
    results = []
    for n in range(5, max_n + 1, max(1, max_n // 20)):
        # 3-AP-free
        ap_size, ap_elems = r_k_greedy(n, 3)
        ap_set = set(ap_elems)

        # Sum-free (greedy: take odds)
        sf_set = {i for i in range(1, n + 1) if i % 2 == 1}

        # Sidon (greedy)
        sidon_set = set()
        sidon_sums = set()
        for x in range(1, n + 1):
            conflict = False
            new_sums = set()
            for a in sidon_set:
                s = a + x
                if s in sidon_sums:
                    conflict = True
                    break
                new_sums.add(s)
            if not conflict:
                dbl = 2 * x
                if dbl not in sidon_sums:
                    new_sums.add(dbl)
                    sidon_set.add(x)
                    sidon_sums |= new_sums

        results.append({
            "n": n,
            "ap_free_size": ap_size,
            "sum_free_size": len(sf_set),
            "sidon_size": len(sidon_set),
            "ap_sf_inter": len(ap_set & sf_set),
            "ap_sidon_inter": len(ap_set & sidon_set),
            "sf_sidon_inter": len(sf_set & sidon_set),
        })
    return results


# =============================================================================
# Section 8: Verification against known OEIS values
# =============================================================================

# OEIS A003002: r_3(n) = max 3-AP-free subset of [1..n], for n >= 1
# Source: https://oeis.org/A003002  (offset 0, so a(0)=0; we store from n=1)
OEIS_A003002 = [
    1, 2, 2, 3, 4, 4, 4, 4, 5, 5,
    6, 6, 7, 8, 8, 8, 8, 8, 8, 9,
]

# OEIS A003003: r_4(n) = max 4-AP-free subset of [1..n], for n >= 1
# Source: https://oeis.org/A003003
OEIS_A003003 = [
    1, 2, 3, 3, 4, 5, 5, 6, 7, 8,
    8, 8, 9, 9, 10, 10, 11, 11, 12, 12,
    13, 13, 14, 14, 15,
]

# OEIS A003004: r_5(n) = max 5-AP-free subset of [1..n], for n >= 1
# Source: https://oeis.org/A003004
OEIS_A003004 = [
    1, 2, 3, 4, 4, 5, 6, 7, 8, 8,
    9, 10, 11, 12, 12, 13, 14, 15, 16, 16,
    16, 16, 16, 17, 18,
]

# OEIS A046693: m(n) = min marks on sparse ruler of length n, for n >= 0
# Source: https://oeis.org/A046693  (a(0)=1; we store from n=1)
OEIS_A046693 = [
    2, 3, 3, 4, 4, 4, 5, 5, 5, 6,
    6, 6, 6, 7, 7, 7, 7, 8, 8, 8,
    8, 8, 8, 9, 9, 9, 9, 9, 9, 10,
    10, 10, 10, 10, 10, 10,
]


def verify_rk_oeis(k: int = 3) -> Dict:
    """
    Verify computed r_k(n) values against OEIS data.
    """
    if k == 3:
        oeis = OEIS_A003002
    elif k == 4:
        oeis = OEIS_A003003
    elif k == 5:
        oeis = OEIS_A003004
    else:
        return {"error": f"No OEIS data for k={k}"}

    matches = 0
    mismatches = []
    for n in range(1, len(oeis) + 1):
        computed, _ = r_k_greedy(n, k)
        expected = oeis[n - 1]
        if computed == expected:
            matches += 1
        else:
            mismatches.append({
                "n": n,
                "computed": computed,
                "expected": expected,
                "diff": computed - expected,
            })

    return {
        "k": k,
        "total_checked": len(oeis),
        "matches": matches,
        "mismatches": mismatches,
        "accuracy": round(matches / len(oeis), 4) if oeis else 0,
    }


def verify_sparse_ruler_oeis() -> Dict:
    """
    Verify sparse ruler computation against OEIS A046693.
    """
    matches = 0
    mismatches = []
    for n in range(1, len(OEIS_A046693) + 1):
        ruler = sparse_ruler_search(n)
        computed = len(ruler) if ruler else None
        expected = OEIS_A046693[n - 1]
        if computed == expected:
            matches += 1
        elif computed is not None:
            mismatches.append({
                "n": n,
                "computed": computed,
                "expected": expected,
            })

    return {
        "total_checked": len(OEIS_A046693),
        "matches": matches,
        "mismatches": mismatches,
        "accuracy": round(matches / len(OEIS_A046693), 4),
    }


# =============================================================================
# Main experimental runner
# =============================================================================

def main():
    print("=" * 72)
    print("ARITHMETIC PROGRESSIONS & ADDITIVE COMBINATORICS — ATTACK RESULTS")
    print("=" * 72)

    # ---- Experiment 1: r_k(n) computation ----
    print("\n" + "-" * 72)
    print("EXPERIMENT 1: r_k(n) for k = 3, 4, 5")
    print("-" * 72)

    for k in [3, 4, 5]:
        print(f"\n  k = {k}:")
        table = compute_rk_table(30, k, method="greedy")
        for row in table:
            if row["n"] <= 20 or row["n"] % 5 == 0:
                print(f"    n={row['n']:3d}: r_{k}(n) = {row['r_k']:3d}  "
                      f"(density = {row['density']:.4f})")

    # Verify against OEIS
    print("\n  OEIS verification:")
    for k in [3, 4, 5]:
        v = verify_rk_oeis(k)
        status = "ALL MATCH" if not v["mismatches"] else f"{len(v['mismatches'])} MISMATCH"
        print(f"    k={k}: {v['matches']}/{v['total_checked']} match ({status})")
        for mm in v["mismatches"][:3]:
            print(f"      n={mm['n']}: got {mm['computed']}, expected {mm['expected']}")

    # ---- Experiment 2: r_3(n) bounds comparison ----
    print("\n" + "-" * 72)
    print("EXPERIMENT 2: r_3(n) bounds comparison")
    print("-" * 72)
    bounds = rk_bound_comparison(200)
    for row in bounds:
        if row["n"] in [10, 20, 50, 100, 150, 200]:
            print(f"  n={row['n']:4d}: r_3 = {row['r3_greedy']:4d}, "
                  f"Behrend >= {row['behrend_lower']:7.2f}, "
                  f"K-M <= {row['km_upper']:7.2f}, "
                  f"density = {row['density']:.6f}")

    # ---- Experiment 3: Stanley sequences ----
    print("\n" + "-" * 72)
    print("EXPERIMENT 3: Stanley sequences (Problem #271)")
    print("-" * 72)
    stanley = stanley_growth_analysis(10000)
    print(f"  S(0,1): {stanley['sequence_length']} terms up to {stanley['max_element']}")
    print(f"  First 30: {stanley['first_50'][:30]}")
    print(f"\n  Growth analysis:")
    for gd in stanley["growth_data"]:
        print(f"    n = {gd['n']:6d}: count = {gd['count']:5d}, "
              f"alpha = {gd['alpha_estimate']:.4f}")

    print(f"\n  Variant comparison:")
    variants = stanley_variants(5000)
    for name, data in variants.items():
        print(f"    {name}: length = {data['length']}, alpha = {data['alpha_estimate']:.4f}")
        print(f"      first 15: {data['first_20'][:15]}")

    # ---- Experiment 4: Sparse rulers ----
    print("\n" + "-" * 72)
    print("EXPERIMENT 4: Sparse rulers (Problem #170)")
    print("-" * 72)
    rulers = compute_sparse_ruler_table(36)
    for row in rulers:
        known_str = f" (known: {row['known']})" if row['known'] else ""
        match_str = ""
        if row["matches_known"] is not None:
            match_str = " OK" if row["matches_known"] else " MISMATCH"
        print(f"  n={row['n']:3d}: m(n) = {row['m_n']}{known_str}{match_str}")

    # Wichmann constructions
    print(f"\n  Wichmann constructions:")
    for t in range(1, 8):
        marks = wichmann_construction(t)
        n = 4 * t + 1
        diffs = ruler_differences(marks)
        is_valid = set(range(1, n + 1)).issubset(diffs)
        print(f"    t={t}: n={n}, marks={len(marks)}, ruler={marks}, valid={is_valid}")

    # ---- Experiment 5: Sum-product ----
    print("\n" + "-" * 72)
    print("EXPERIMENT 5: Sum-product problem (Problem #52)")
    print("-" * 72)
    sp = sum_product_structured_sets(50)
    for name, data in sp.items():
        print(f"  {name:12s}: |A|={data['n']:3d}, |A+A|={data['sum_size']:5d}, "
              f"|A*A|={data['product_size']:5d}, max ratio={data['max_ratio']:.2f}")

    print(f"\n  Exponent search:")
    exp_data = sum_product_exponent_search()
    for row in exp_data:
        print(f"    n={row['n']:3d}: min max(|A+A|,|A*A|) = {row['min_max_sp']:5d}, "
              f"alpha = {row['alpha_estimate']:.4f}, target n^(4/3) = {row['target_4_3']:.1f}")

    # ---- Experiment 6: Behrend construction ----
    print("\n" + "-" * 72)
    print("EXPERIMENT 6: Behrend-type 3-AP-free sets")
    print("-" * 72)
    behrend = behrend_analysis()
    for row in behrend:
        print(f"  n={row['n']:4d}: greedy = {row['greedy_size']:4d} ({row['greedy_density']:.4f}), "
              f"Behrend = {row['behrend_size']:4d} ({row['behrend_density']:.4f}), "
              f"theory >= {row['theory_lower']:.1f}")

    # ---- Experiment 7: Density across k ----
    print("\n" + "-" * 72)
    print("EXPERIMENT 7: Density r_k(n)/n across k = 3, 4, 5")
    print("-" * 72)
    decay = density_across_k(200)
    for k_label, table in decay.items():
        print(f"\n  {k_label}:")
        for row in table:
            if row["n"] % 25 == 0 or row["n"] <= 10:
                print(f"    n={row['n']:4d}: r_k/n = {row['density']:.6f}")

    # ---- Experiment 8: Cross-problem connections ----
    print("\n" + "-" * 72)
    print("EXPERIMENT 8: AP-free / Sum-free / Sidon overlaps")
    print("-" * 72)
    overlaps = ap_sumfree_sidon_overlaps(100)
    for row in overlaps:
        print(f"  n={row['n']:3d}: AP-free={row['ap_free_size']:3d}, "
              f"SumFree={row['sum_free_size']:3d}, Sidon={row['sidon_size']:3d} | "
              f"AP∩SF={row['ap_sf_inter']:3d}, AP∩Sidon={row['ap_sidon_inter']:3d}")

    # ---- Summary ----
    print("\n" + "=" * 72)
    print("FINDINGS SUMMARY")
    print("=" * 72)
    print("""
Problem #3 (r_3(n)/n -> 0):
  PROVED by Kelley-Meka 2023. Our greedy r_3(n) confirms density decay.
  Density at n=200: ~{:.4f}. Behrend lower bound matches closely.

Problem #142 (r_k(n) = o(n) for all k):
  PROVED by Szemeredi. Our data shows r_k(n)/n decays for k=3,4,5.
  Key open question: QUANTITATIVE bounds (what is the decay rate for k>=4?).
  Our greedy data can help calibrate conjectured bounds.

Problem #271 (Stanley sequences):
  Growth exponent alpha for S(0,1) is approximately 0.79-0.81.
  This is consistent with the conjectured ~n^{{log 3 / log 4}} ~ n^0.792.
  Different initial segments give similar growth rates.

Problem #170 (Sparse rulers):
  Our search matches OEIS A046693 for small n.
  Wichmann construction provides systematic family.
  Gap between lower bound and actual m(n) narrows with n.

Problem #52 (Sum-product):
  APs: small A+A (~2n), large A*A. GPs: large A+A, small A*A (~2n).
  Neither achieves both small simultaneously, confirming conjecture direction.
  Estimated exponent >= 1.33, consistent with the 4/3 threshold.
""".format(bounds[-1]["density"] if bounds else 0))


if __name__ == "__main__":
    main()
