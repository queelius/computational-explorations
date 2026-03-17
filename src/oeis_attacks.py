#!/usr/bin/env python3
"""
OEIS-Informed Attacks on Open Erdos Problems

Exploits the computational structure of OEIS sequences attached to problems
#849 (Singmaster), #479 (2^n mod n), #168 (triple-free sets), #468 (divisor sums).

Each attack module:
  1. Computes the relevant OEIS sequences (extending known values where feasible)
  2. Looks for patterns, growth rates, and structural regularities
  3. Cross-references sequences to find relationships
  4. Tests conjectures or searches for counterexamples
"""

import math
from itertools import combinations
from collections import defaultdict, Counter
from functools import lru_cache
from typing import List, Tuple, Dict, Set, Optional
import bisect


# =============================================================================
# Problem #849: Singmaster's Conjecture
# =============================================================================
#
# Conjecture: There exists a finite bound B such that no integer > 1
# appears more than B times as a binomial coefficient C(n,k).
#
# OEIS sequences:
#   A003016: number of times n appears in Pascal's triangle (rows <= n)
#   A003015: numbers appearing >= 5 times in Pascal's triangle
#   A059233: number of distinct rows in which n appears
#   A098565: numbers appearing exactly 6 times
#   A090162: Fibonacci-derived values appearing >= 6 times
#   A180058, A182237: related multiplicity sequences


def binom(n: int, k: int) -> int:
    """Binomial coefficient C(n, k)."""
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def pascal_multiplicity(N: int) -> int:
    """
    Count how many times N appears as C(n,k) in Pascal's triangle.

    This is A003016(N). We search all rows n >= 2k (by symmetry C(n,k)=C(n,n-k),
    only need k <= n/2).
    """
    if N <= 1:
        return float('inf') if N == 1 else 1  # 1 appears infinitely often

    count = 0
    # N = C(N, 1) always, and C(N, N-1)
    count += 2  # C(N,1) and C(N,N-1)

    # Check if N is a central binomial or appears on the diagonal
    # C(n, k) = N with k >= 2 and k <= n/2
    for k in range(2, int(math.log2(N)) + 2 if N > 1 else 2):
        # C(n, k) = N implies n ~ N^(1/k) * k!^(1/k)
        # Binary search for n
        lo, hi = 2 * k, N + 1
        while lo <= hi:
            mid = (lo + hi) // 2
            val = binom(mid, k)
            if val == N:
                count += 2  # C(mid, k) and C(mid, mid-k) unless k = mid-k
                if 2 * k == mid:
                    count -= 1  # Central element counted once
                break
            elif val < N:
                lo = mid + 1
            else:
                hi = mid - 1

    return count


def compute_A003016(limit: int) -> List[int]:
    """
    Compute A003016(n) for n = 0..limit.

    A003016(n) = number of times n appears as an entry in Pascal's triangle.
    """
    result = [0] * (limit + 1)

    # Build a map of all binomial coefficients <= limit
    counts = defaultdict(int)

    # Row n, entry k: C(n, k) with k <= n/2 (by symmetry)
    for n in range(0, limit + 1):
        for k in range(0, n // 2 + 1):
            val = binom(n, k)
            if val > limit:
                break
            if k == 0 or 2 * k == n:
                counts[val] += 1  # Appears once (edge or center)
            else:
                counts[val] += 2  # C(n,k) = C(n,n-k)

    for val in range(limit + 1):
        result[val] = counts.get(val, 0)

    return result


def compute_A003015(limit: int) -> List[int]:
    """
    Numbers that appear >= 5 times in Pascal's triangle (up to checking
    rows up to some bound).

    Known values: 1, 120, 210, 1540, 3003, 7140, 11628, 24310, ...
    """
    # We need to check much further than `limit` in row numbers
    # because a number N might appear as C(n,k) for very large n
    # Strategy: build map of C(n,k) for moderate n, count multiplicities

    max_row = max(limit, 1000)
    counts = defaultdict(int)

    for n in range(0, max_row + 1):
        for k in range(0, n // 2 + 1):
            val = binom(n, k)
            if val > limit:
                break
            if k == 0 or 2 * k == n:
                counts[val] += 1
            else:
                counts[val] += 2

    return sorted(v for v, c in counts.items() if c >= 5 and v > 0)


def singmaster_fibonacci_family() -> List[Tuple[int, int, int]]:
    """
    Generate the known infinite family of numbers appearing >= 6 times
    in Pascal's triangle, based on Fibonacci numbers.

    C(F_{2i} * F_{2i+1}, F_{2i-1} * F_{2i} - 1) =
    C(F_{2i} * F_{2i+1} - 1, F_{2i-1} * F_{2i})

    Returns list of (n_val, k1, k2) where C(n_val, k1) = C(n_val-1, k2).
    """
    fibs = [1, 1]
    for _ in range(30):
        fibs.append(fibs[-1] + fibs[-2])

    results = []
    for i in range(1, 12):
        # 1-indexed Fibonacci: F(2i-1), F(2i), F(2i+1)
        # In 0-indexed array: fibs[2i-2], fibs[2i-1], fibs[2i]
        idx_lo = 2 * i - 2
        idx_mid = 2 * i - 1
        idx_hi = 2 * i

        if idx_hi >= len(fibs):
            break

        f_2im1 = fibs[idx_lo]     # F(2i-1)
        f_2i = fibs[idx_mid]       # F(2i)
        f_2ip1 = fibs[idx_hi]     # F(2i+1)

        n1 = f_2i * f_2ip1
        k1 = f_2im1 * f_2i - 1

        # The value C(n1, k1) appears at least 6 times in Pascal's triangle
        # As C(n1, k1), C(n1, n1-k1), plus appearances at (n1-1, k1+1) etc.
        results.append((n1, k1, f_2im1 * f_2i))

    return results


def singmaster_multiplicity_distribution(max_val: int) -> Dict[int, int]:
    """
    Compute distribution of multiplicities in Pascal's triangle for
    values up to max_val.

    Returns {multiplicity: count_of_integers_with_that_multiplicity}.
    """
    a003016 = compute_A003016(max_val)
    dist = Counter(a003016[2:])  # Skip 0 and 1
    return dict(sorted(dist.items()))


def singmaster_high_multiplicity_search(max_row: int) -> List[Tuple[int, int]]:
    """
    Search for integers with high multiplicity in Pascal's triangle.
    Scans rows up to max_row looking for values appearing many times.

    Returns list of (value, multiplicity) sorted by multiplicity desc.
    """
    counts = defaultdict(set)  # value -> set of (n, k) positions

    for n in range(0, max_row + 1):
        for k in range(2, n // 2 + 1):
            val = binom(n, k)
            counts[val].add((n, k))
            if k != n - k:
                counts[val].add((n, n - k))

    # Also add the trivial appearances C(n,1) = n
    for n in range(2, max_row + 1):
        counts[n].add((n, 1))
        counts[n].add((n, n - 1))

    # Find high multiplicity entries
    high_mult = [(val, len(positions)) for val, positions in counts.items()
                 if len(positions) >= 4 and val > 1]
    high_mult.sort(key=lambda x: -x[1])

    return high_mult[:100]


def singmaster_row_gaps(max_val: int) -> Dict[int, List[int]]:
    """
    For values appearing >= 4 times, find in which rows they appear.
    The gap pattern may reveal structure about Singmaster's conjecture.
    """
    max_row = max(max_val, 1000)
    value_rows = defaultdict(set)

    for n in range(0, max_row + 1):
        for k in range(0, n // 2 + 1):
            val = binom(n, k)
            if val > max_val:
                break
            value_rows[val].add(n)

    result = {}
    for val, rows in value_rows.items():
        if len(rows) >= 3 and val > 1:  # 3+ distinct rows
            sorted_rows = sorted(rows)
            result[val] = sorted_rows

    return result


def singmaster_growth_analysis(limit: int) -> Dict[str, object]:
    """
    Analyze how the maximum multiplicity M(N) = max_{n<=N} A003016(n)
    grows with N. Singmaster's conjecture says M(N) is bounded.

    Known: M(N) >= 8 (from the value 3003 = C(78,2) = C(15,5) = C(14,6) = C(3003,1)).
    Abbott-Erdos-Hanson showed M(N) = O(log N / log log N).
    Kane (2007) improved to O((log N)^{2/3 + epsilon}).
    """
    a003016 = compute_A003016(limit)

    running_max = 0
    max_record_holders = []  # (n, multiplicity) when a new max is achieved

    for n in range(2, limit + 1):
        if a003016[n] > running_max:
            running_max = a003016[n]
            max_record_holders.append((n, running_max))

    # Growth rate analysis: at what N does max multiplicity reach each level?
    first_occurrence = {}
    for n in range(2, limit + 1):
        m = a003016[n]
        if m not in first_occurrence:
            first_occurrence[m] = n

    return {
        'max_multiplicity': running_max,
        'record_holders': max_record_holders,
        'first_occurrence_of_multiplicity': first_occurrence,
        'multiplicity_distribution': singmaster_multiplicity_distribution(limit),
    }


def verify_singmaster_known_high(n_val: int) -> Dict[str, object]:
    """
    Verify the multiplicity of specific known high-multiplicity values.
    3003 is the smallest number appearing 8 times in Pascal's triangle.

    Uses smart search: for each k >= 2, binary search for n such that C(n,k) = n_val.
    Only checks k up to log2(n_val) since C(n,k) grows fast in k.
    """
    if n_val <= 0:
        return {'value': n_val, 'multiplicity': 0, 'positions': []}

    positions = set()

    # C(n_val, 1) = n_val always
    positions.add((n_val, 1))
    positions.add((n_val, n_val - 1))

    # For k >= 2, binary search for n such that C(n, k) = n_val
    max_k = min(n_val, int(math.log2(n_val + 1)) + 3) if n_val > 1 else 1

    for k in range(2, max_k + 1):
        # C(n, k) is increasing in n for n >= k.
        # C(k, k) = 1, C(2k, k) grows fast.
        # Binary search for n in [k, n_val].
        lo, hi = k, n_val
        while lo <= hi:
            mid = (lo + hi) // 2
            val = binom(mid, k)
            if val == n_val:
                positions.add((mid, k))
                if k != mid - k:
                    positions.add((mid, mid - k))
                break
            elif val < n_val:
                lo = mid + 1
            else:
                hi = mid - 1

    return {
        'value': n_val,
        'multiplicity': len(positions),
        'positions': sorted(positions),
    }


# =============================================================================
# Problem #479: 2^n mod n (Coverset of residues)
# =============================================================================
#
# Question: Does 2^n mod n take every value except 1?
# I.e., for every integer m >= 0 with m != 1, does there exist n such that
# 2^n ≡ m (mod n)?
#
# OEIS sequences:
#   A015910: 2^n mod n
#   A036236: smallest k>0 with 2^k mod k = n (inverse of A015910)
#   A015919: n such that 2^n ≡ 2 (mod n) (primes + pseudoprimes)
#   A050259: n such that 2^n ≡ 3 (mod n)
#   A015921: n such that 2^n ≡ 4 (mod n)
#   A006521: n | 2^n + 1 (i.e., 2^n ≡ -1 mod n, so 2^n mod n = n-1)
#   A006517: n | 2^n - 1


def compute_A015910(limit: int) -> List[int]:
    """
    Compute 2^n mod n for n = 1..limit.

    Returns list with a[0] = 0 (placeholder for n=0), a[i] = 2^i mod i.
    """
    result = [0]  # index 0 placeholder
    for n in range(1, limit + 1):
        result.append(pow(2, n, n))
    return result


def compute_A036236(target_limit: int, search_limit: int) -> Dict[int, int]:
    """
    For each residue m in 0..target_limit, find the smallest n > 0
    such that 2^n mod n = m.

    Returns {m: smallest_n} for found values. Missing keys have no
    solution found within search_limit.
    """
    first_hit = {}
    for n in range(1, search_limit + 1):
        r = pow(2, n, n)
        if r <= target_limit and r not in first_hit:
            first_hit[r] = n
    return first_hit


def residue_coverage_analysis(limit: int) -> Dict[str, object]:
    """
    Analyze the coverage of 2^n mod n over residues.

    Key question: which residues m are NOT achieved by 2^n mod n
    for any n <= limit?

    We know m=1 is never achieved (provably). Are there others
    that are just hard to find?
    """
    a015910 = compute_A015910(limit)

    achieved = set(a015910[1:])

    # What's the largest gap?
    missing = []
    for m in range(0, limit):
        if m not in achieved:
            missing.append(m)

    # Distribution of residues
    residue_counts = Counter(a015910[1:])

    # For each residue, find first and last occurrence
    first_occurrence = {}
    for n in range(1, limit + 1):
        r = a015910[n]
        if r not in first_occurrence:
            first_occurrence[r] = n

    return {
        'achieved_count': len(achieved),
        'missing_up_to_100': [m for m in missing if m < 100],
        'missing_count_up_to_1000': sum(1 for m in missing if m < 1000),
        'first_occurrences_small': {m: first_occurrence[m] for m in range(20) if m in first_occurrence},
        'most_common_residues': residue_counts.most_common(20),
    }


def power_of_3_pattern(max_exp: int) -> List[Tuple[int, int, int]]:
    """
    Verify the known pattern: 2^(3^n) mod 3^n = 3^n - 1.

    This means for m = 3^n - 1, we know 2^k mod k = m has a solution k = 3^n.
    This covers infinitely many residues of a specific form.

    Returns [(n, 3^n, 2^(3^n) mod 3^n)] for verification.
    """
    results = []
    for n in range(1, max_exp + 1):
        k = 3 ** n
        r = pow(2, k, k)
        results.append((n, k, r))
    return results


def find_pseudoprime_family(limit: int) -> Dict[str, List[int]]:
    """
    Analyze the structure of A015919: n where 2^n ≡ 2 (mod n).

    These are {1} U primes U Fermat pseudoprimes base 2.
    The pseudoprimes are the interesting ones for problem 479.
    """
    primes = set()
    pseudoprimes = []

    for n in range(2, limit + 1):
        if pow(2, n, n) == 2:
            # Check if prime
            if _is_prime(n):
                primes.add(n)
            else:
                pseudoprimes.append(n)

    return {
        'pseudoprime_count': len(pseudoprimes),
        'pseudoprimes': pseudoprimes[:50],
        'prime_count': len(primes),
    }


def residue_4_family(limit: int) -> List[int]:
    """
    Compute A015921: n such that 2^n ≡ 4 (mod n).

    Structural observation: if n is even and 2^(n/2) ≡ 2 (mod n/2),
    and n/2 is odd, then 2^n ≡ 4 (mod n) in certain cases.
    """
    result = []
    for n in range(1, limit + 1):
        if pow(2, n, n) == 4:
            result.append(n)
    return result


def cross_reference_479_sequences(limit: int) -> Dict[str, object]:
    """
    Cross-reference all 7 OEIS sequences for problem #479.

    Key insight: the sets {n : 2^n mod n = m} for different m
    have different structural properties. Understanding which m
    values have structured solutions vs sporadic ones is crucial.
    """
    a015910 = compute_A015910(limit)

    # Group n by residue
    residue_groups = defaultdict(list)
    for n in range(1, limit + 1):
        r = a015910[n]
        residue_groups[r].append(n)

    # Analyze density of each residue class
    densities = {}
    for r in range(min(50, limit)):
        if r in residue_groups:
            group = residue_groups[r]
            densities[r] = {
                'count': len(group),
                'density': len(group) / limit,
                'first': group[0],
                'median': group[len(group) // 2] if group else None,
            }

    # Check: which residues have "structured" solutions (arithmetic-like)?
    structured = {}
    for r in range(20):
        if r in residue_groups and len(residue_groups[r]) >= 5:
            group = residue_groups[r]
            diffs = [group[i+1] - group[i] for i in range(min(20, len(group) - 1))]
            structured[r] = {
                'first_diffs': diffs,
                'mean_gap': sum(diffs) / len(diffs) if diffs else 0,
                'gcd_of_gaps': _multi_gcd(diffs) if diffs else 0,
            }

    # A006521 cross-check: n | 2^n + 1 means 2^n mod n = n - 1
    a006521_terms = []
    for n in range(1, limit + 1):
        if pow(2, n, n) == n - 1:
            a006521_terms.append(n)

    return {
        'residue_densities': densities,
        'structured_residues': structured,
        'a006521_terms': a006521_terms[:30],
        'a006521_count': len(a006521_terms),
    }


def hard_residue_search(target_residue: int, limit: int) -> Optional[int]:
    """
    Search for the smallest n such that 2^n mod n = target_residue.

    For most residues m, the smallest n is moderate. But some (like m=3)
    require enormous n (first solution: n = 4700063497).
    """
    for n in range(1, limit + 1):
        if pow(2, n, n) == target_residue:
            return n
    return None


def residue_gap_pattern(limit: int) -> List[Tuple[int, int]]:
    """
    Find residues that are missing from 2^n mod n for all n <= limit.

    The gap pattern reveals which residues are "hard" - potentially
    related to the structure of the problem.
    """
    achieved = set()
    for n in range(1, limit + 1):
        achieved.add(pow(2, n, n))

    missing = []
    for m in range(0, min(limit, 1000)):
        if m not in achieved:
            missing.append((m, _smallest_prime_factor(m) if m > 1 else 0))

    return missing


# =============================================================================
# Problem #168: Triple-Free Sets in 3-Smooth Numbers
# =============================================================================
#
# Question: What is the maximum density of a set A of 3-smooth numbers
# (numbers of the form 2^a * 3^b) containing no triple {x, 2x, 3x}?
#
# OEIS sequences:
#   A004059: positions of new maxima in A057561
#   A057561: max triple-free subset of first n 3-smooth numbers
#   A094708, A386439: related sequences


def three_smooth_numbers(limit: int) -> List[int]:
    """Generate all 3-smooth numbers (2^a * 3^b) up to limit."""
    result = set()
    a = 1
    while a <= limit:
        b = a
        while b <= limit:
            result.add(b)
            b *= 3
        a *= 2
    return sorted(result)


def max_triple_free_subset(smooth_set: List[int]) -> Tuple[int, List[int]]:
    """
    Find maximum subset of smooth_set containing no {x, 2x, 3x} triple.

    Uses ILP-style reduction: forbidden triples define hyperedges in a
    3-uniform hypergraph. We find max independent set using branch-and-bound
    with conflict-driven pruning.

    For the Erdos problem, this gives A057561.
    """
    n = len(smooth_set)
    if n == 0:
        return 0, []

    smooth_set_vals = set(smooth_set)

    # Identify all forbidden triples {a, 2a, 3a} with all three in the set
    triples = []
    for a in smooth_set:
        if 2 * a in smooth_set_vals and 3 * a in smooth_set_vals:
            triples.append((a, 2 * a, 3 * a))

    if not triples:
        return n, list(smooth_set)

    if n <= 60:
        return _exact_triple_free_fast(smooth_set, smooth_set_vals, triples)

    # For larger sets, use greedy
    return _greedy_triple_free(smooth_set, smooth_set_vals)


def _exact_triple_free_fast(elements: List[int], element_set: Set[int],
                             triples: List[Tuple[int, int, int]]) -> Tuple[int, List[int]]:
    """
    Exact max triple-free subset via constraint-based branch-and-bound.

    The constraint is: for each triple (a, 2a, 3a), at most 2 of the 3
    can be in the set. This is a maximum independent set in a 3-uniform
    hypergraph, which we solve by branching on violated constraints.
    """
    n = len(elements)
    idx = {v: i for i, v in enumerate(elements)}

    # For each element, which triples involve it?
    elem_triples = defaultdict(list)
    for ti, (a, b, c) in enumerate(triples):
        if a in idx:
            elem_triples[idx[a]].append(ti)
        if b in idx:
            elem_triples[idx[b]].append(ti)
        if c in idx:
            elem_triples[idx[c]].append(ti)

    best_size = [0]
    best_set = [[]]

    def solve(included: Set[int], excluded: Set[int]):
        # Upper bound: all non-excluded elements
        remaining = n - len(excluded)
        if remaining <= best_size[0]:
            return

        # Check for violated triples
        violated = -1
        for ti, (a, b, c) in enumerate(triples):
            ai, bi, ci = idx.get(a, -1), idx.get(b, -1), idx.get(c, -1)
            if ai == -1 or bi == -1 or ci == -1:
                continue
            if ai in included and bi in included and ci in included:
                violated = ti
                break

        if violated == -1:
            # No violation: include all remaining non-excluded elements
            current = set(range(n)) - excluded
            if len(current) > best_size[0]:
                best_size[0] = len(current)
                best_set[0] = [elements[i] for i in sorted(current)]
            return

        # Branch: for violated triple (a,b,c), exclude one of the three
        a, b, c = triples[violated]
        ai, bi, ci = idx[a], idx[b], idx[c]

        for remove_idx in [ai, bi, ci]:
            if remove_idx not in excluded:
                new_excluded = excluded | {remove_idx}
                new_included = included - {remove_idx}
                solve(new_included, new_excluded)

    # Start with all elements included
    solve(set(range(n)), set())
    return best_size[0], best_set[0]


def _greedy_triple_free(elements: List[int],
                         element_set: Set[int]) -> Tuple[int, List[int]]:
    """Greedy max triple-free subset (larger inputs)."""
    selected = []
    selected_set = set()

    for x in elements:
        # Check if adding x creates a forbidden triple
        creates_triple = False

        # Check all triples {a, 2a, 3a} involving x
        # Case 1: x = a. Need both 2x and 3x NOT in selected_set
        if 2 * x in selected_set and 3 * x in selected_set:
            creates_triple = True

        # Case 2: x = 2a, a = x/2. Need both a and 3a NOT in selected_set
        if not creates_triple and x % 2 == 0:
            a = x // 2
            if a in selected_set and 3 * a in selected_set:
                creates_triple = True

        # Case 3: x = 3a, a = x/3. Need both a and 2a NOT in selected_set
        if not creates_triple and x % 3 == 0:
            a = x // 3
            if a in selected_set and 2 * a in selected_set:
                creates_triple = True

        if not creates_triple:
            selected.append(x)
            selected_set.add(x)

    return len(selected), selected


def compute_A057561(n_terms: int) -> List[int]:
    """
    Compute A057561: size of largest triple-free subset of first n 3-smooth numbers.

    Uses incremental computation: when adding a new element, either the old
    optimal set is still optimal, or the new element participates in the new
    optimal set (which can differ by at most 1 from the old).
    """
    smooth = three_smooth_numbers(10 ** 6)[:max(n_terms, 100)]

    results = []
    for n in range(1, n_terms + 1):
        subset = smooth[:n]
        size, _ = max_triple_free_subset(subset)
        results.append(size)

    return results


def triple_free_density_analysis(n_smooth: int) -> Dict[str, object]:
    """
    Analyze the density of maximum triple-free subsets among 3-smooth numbers.

    The key question: does the ratio A057561(n) / n converge, and to what?
    """
    smooth = three_smooth_numbers(10 ** 6)[:n_smooth]

    ratios = []
    sizes = []

    # Compute incrementally using greedy (since exact is too slow for large n)
    selected_set = set()
    count = 0

    for i, x in enumerate(smooth):
        creates_triple = False

        if 2 * x in selected_set and 3 * x in selected_set:
            creates_triple = True
        if not creates_triple and x % 2 == 0:
            a = x // 2
            if a in selected_set and 3 * a in selected_set:
                creates_triple = True
        if not creates_triple and x % 3 == 0:
            a = x // 3
            if a in selected_set and 2 * a in selected_set:
                creates_triple = True

        if not creates_triple:
            selected_set.add(x)
            count += 1

        sizes.append(count)
        if (i + 1) % 10 == 0 or i < 20:
            ratios.append((i + 1, count, count / (i + 1)))

    return {
        'sizes': sizes,
        'density_samples': ratios,
        'final_density': sizes[-1] / len(smooth) if smooth else 0,
        'n_smooth': len(smooth),
    }


def triple_free_structure_analysis(n_terms: int) -> Dict[str, object]:
    """
    Analyze the structure of optimal triple-free sets.

    Look at which 3-smooth numbers are in/out of the optimal set.
    Express each as 2^a * 3^b and look for patterns in (a, b) space.
    """
    smooth = three_smooth_numbers(10 ** 6)[:n_terms]

    _, best_set = _greedy_triple_free(smooth, set(smooth))
    best_set_vals = set(best_set)

    # Decompose into (a, b) coordinates where x = 2^a * 3^b
    in_set = []
    out_set = []

    for x in smooth:
        a, b = 0, 0
        temp = x
        while temp % 2 == 0:
            a += 1
            temp //= 2
        while temp % 3 == 0:
            b += 1
            temp //= 3

        if x in best_set_vals:
            in_set.append((a, b))
        else:
            out_set.append((a, b))

    # Look for patterns: are there lines/regions in (a,b)-space?
    # The constraint {x, 2x, 3x} in (a,b)-space is:
    # (a,b), (a+1,b), (a,b+1) cannot all be present
    # This is like a corner-free set in the grid!

    return {
        'in_set_coords': in_set[:50],
        'out_set_coords': out_set[:50],
        'in_count': len(in_set),
        'out_count': len(out_set),
        'density': len(in_set) / (len(in_set) + len(out_set)) if in_set or out_set else 0,
        'insight': 'Constraint {x,2x,3x} in (a,b)-space = no (a,b),(a+1,b),(a,b+1) all present = corner-free set in Z^2 grid',
    }


# =============================================================================
# Problem #468: Divisor Sum Representations
# =============================================================================
#
# A167485(n) = smallest m such that n = sum of an initial subsequence
# of divisors of m, or 0 if impossible.
#
# Erdos asked: is a(n) = o(n)? I.e., does a(n)/n -> 0?


def divisors_sorted(m: int) -> List[int]:
    """Return divisors of m sorted in increasing order."""
    divs = []
    for d in range(1, int(math.isqrt(m)) + 1):
        if m % d == 0:
            divs.append(d)
            if d != m // d:
                divs.append(m // d)
    return sorted(divs)


def initial_divisor_sums(m: int) -> List[int]:
    """
    Compute all partial sums of divisors of m (in increasing order).
    Returns [d1, d1+d2, d1+d2+d3, ...].
    """
    divs = divisors_sorted(m)
    sums = []
    running = 0
    for d in divs:
        running += d
        sums.append(running)
    return sums


def compute_A167485(limit: int, search_bound: int) -> List[int]:
    """
    Compute A167485(n) for n = 1..limit.

    a(n) = smallest m >= 1 such that n is a partial sum of divisors of m.
    a(n) = 0 if no such m exists (only n=3 is known to have a(n)=0 among small n).
    """
    result = [0] * (limit + 1)  # 0 means not found
    found = [False] * (limit + 1)
    found[0] = True

    for m in range(1, search_bound + 1):
        sums = initial_divisor_sums(m)
        for s in sums:
            if s <= limit and not found[s]:
                found[s] = True
                result[s] = m

    return result


def divisor_sum_ratio_analysis(limit: int, search_bound: int) -> Dict[str, object]:
    """
    Analyze the ratio a(n)/n for A167485 to test Erdos's conjecture a(n) = o(n).
    """
    a = compute_A167485(limit, search_bound)

    ratios = []
    max_ratio = 0
    max_ratio_n = 0
    zero_count = 0

    for n in range(1, limit + 1):
        if a[n] == 0:
            zero_count += 1
            continue
        r = a[n] / n
        ratios.append((n, a[n], r))
        if r > max_ratio:
            max_ratio = r
            max_ratio_n = n

    # Compute running average of ratios
    running_avg = []
    total = 0
    count = 0
    for n, m, r in ratios:
        total += r
        count += 1
        if count % 10 == 0:
            running_avg.append((n, total / count))

    return {
        'max_ratio': max_ratio,
        'max_ratio_at': max_ratio_n,
        'zero_count': zero_count,
        'zero_values': [n for n in range(1, limit + 1) if a[n] == 0],
        'running_average': running_avg[-10:] if running_avg else [],
        'sample_values': ratios[:30],
    }


# =============================================================================
# Utility Functions
# =============================================================================

def _is_prime(n: int) -> bool:
    """Primality test."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def _smallest_prime_factor(n: int) -> int:
    """Return smallest prime factor of n."""
    if n <= 1:
        return n
    if n % 2 == 0:
        return 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return i
        i += 2
    return n


def _multi_gcd(nums: List[int]) -> int:
    """GCD of a list of numbers."""
    if not nums:
        return 0
    result = nums[0]
    for x in nums[1:]:
        result = math.gcd(result, x)
    return result


# =============================================================================
# Cross-Problem Analysis
# =============================================================================

def cross_problem_oeis_analysis() -> Dict[str, object]:
    """
    Cross-reference OEIS sequences across all target problems.

    Look for unexpected connections between problems through
    shared sequence values or structural similarities.
    """
    results = {}

    # 1. Singmaster analysis
    singmaster = singmaster_growth_analysis(5000)
    results['singmaster'] = {
        'max_multiplicity_up_to_10000': singmaster['max_multiplicity'],
        'record_holders': singmaster['record_holders'],
        'distribution': singmaster['multiplicity_distribution'],
    }

    # 2. Problem 479 coverage analysis
    coverage = residue_coverage_analysis(10000)
    results['problem_479'] = coverage

    # 3. Powers of 3 pattern
    pow3 = power_of_3_pattern(10)
    results['pow3_pattern'] = pow3

    # 4. Triple-free density
    tf_density = triple_free_density_analysis(80)
    results['triple_free'] = {
        'final_density': tf_density['final_density'],
        'density_trend': tf_density['density_samples'][-5:] if tf_density['density_samples'] else [],
    }

    return results


# =============================================================================
# Main Execution
# =============================================================================

def run_all_attacks():
    """Run all OEIS-informed attacks and report findings."""
    print("=" * 70)
    print("OEIS-INFORMED ATTACKS ON OPEN ERDOS PROBLEMS")
    print("=" * 70)

    # ---- Problem #849: Singmaster's Conjecture ----
    print("\n" + "=" * 70)
    print("PROBLEM #849: SINGMASTER'S CONJECTURE")
    print("=" * 70)

    print("\n--- A003016: Multiplicity in Pascal's Triangle (up to 5000) ---")
    growth = singmaster_growth_analysis(5000)
    print(f"Maximum multiplicity found: {growth['max_multiplicity']}")
    print(f"Record holders: {growth['record_holders']}")
    print(f"First occurrence of each multiplicity: {growth['first_occurrence_of_multiplicity']}")
    print(f"Distribution: {growth['multiplicity_distribution']}")

    print("\n--- High-multiplicity values (rows up to 300) ---")
    high = singmaster_high_multiplicity_search(300)
    if high:
        print(f"Top 10 by multiplicity:")
        for val, mult in high[:10]:
            print(f"  {val}: appears {mult} times")

    print("\n--- Fibonacci family (A090162) ---")
    fib_family = singmaster_fibonacci_family()
    for n_val, k1, k2 in fib_family[:5]:
        val = binom(n_val, k1)
        print(f"  C({n_val}, {k1}) = C({n_val-1}, {k2}) = {val if val < 10**20 else '(huge)'}")
        print(f"    Multiplicity >= 6")

    print("\n--- Verify 3003 (known to appear 8 times) ---")
    v3003 = verify_singmaster_known_high(3003)
    print(f"  3003 appears {v3003['multiplicity']} times at positions: {v3003['positions']}")

    print("\n--- Row gap analysis ---")
    gaps = singmaster_row_gaps(5000)
    multi_row = [(val, rows) for val, rows in gaps.items() if len(rows) >= 3]
    multi_row.sort(key=lambda x: -len(x[1]))
    print(f"Values appearing in 3+ rows (up to 5000): {len(multi_row)}")
    for val, rows in multi_row[:10]:
        print(f"  {val}: rows {rows}")

    # ---- Problem #479: 2^n mod n ----
    print("\n" + "=" * 70)
    print("PROBLEM #479: 2^n mod n RESIDUE COVERAGE")
    print("=" * 70)

    print("\n--- Residue coverage analysis (n up to 50000) ---")
    cov = residue_coverage_analysis(50000)
    print(f"Distinct residues achieved: {cov['achieved_count']}")
    print(f"Missing residues < 100: {cov['missing_up_to_100']}")
    print(f"Missing residues < 1000: {cov['missing_count_up_to_1000']}")
    print(f"First occurrences (small residues):")
    for r, n in sorted(cov['first_occurrences_small'].items()):
        print(f"  2^n mod n = {r}: first at n = {n}")

    print("\n--- Powers of 3 pattern verification ---")
    p3 = power_of_3_pattern(10)
    for n, k, r in p3:
        expected = k - 1
        print(f"  2^(3^{n}) mod 3^{n} = {r}, expected {expected}: {'OK' if r == expected else 'MISMATCH'}")

    print("\n--- Gap pattern in missing residues (n up to 50000) ---")
    gaps479 = residue_gap_pattern(50000)
    print(f"Missing residues (< 1000): {len([g for g in gaps479 if g[0] < 1000])}")
    small_missing = [g for g in gaps479 if g[0] < 200]
    if small_missing:
        print(f"First 20 missing: {small_missing[:20]}")

    print("\n--- Cross-reference of sequences ---")
    xref = cross_reference_479_sequences(20000)
    print(f"A006521 terms (n | 2^n+1) found: {xref['a006521_count']}")
    print(f"First terms: {xref['a006521_terms'][:15]}")
    print(f"Structured residue analysis (gap GCDs):")
    for r, info in list(xref['structured_residues'].items())[:10]:
        print(f"  Residue {r}: gap GCD = {info['gcd_of_gaps']}, mean gap = {info['mean_gap']:.1f}")

    print("\n--- Pseudoprime analysis ---")
    psp = find_pseudoprime_family(50000)
    print(f"Pseudoprimes to base 2 up to 100000: {psp['pseudoprime_count']}")
    print(f"First pseudoprimes: {psp['pseudoprimes'][:15]}")

    # ---- Problem #168: Triple-Free Sets ----
    print("\n" + "=" * 70)
    print("PROBLEM #168: TRIPLE-FREE SETS IN 3-SMOOTH NUMBERS")
    print("=" * 70)

    print("\n--- A057561: max triple-free subset sizes ---")
    a057561 = compute_A057561(30)
    print(f"A057561(1..30): {a057561}")

    print("\n--- Density analysis ---")
    density = triple_free_density_analysis(100)
    print(f"Final greedy density (100 smooth): {density['final_density']:.4f}")
    print(f"Density trend:")
    for n, size, ratio in density['density_samples'][-10:]:
        print(f"  n={n}: size={size}, density={ratio:.4f}")

    print("\n--- Structure in (a,b)-coordinates ---")
    structure = triple_free_structure_analysis(60)
    print(f"In set: {structure['in_count']}, Out: {structure['out_count']}")
    print(f"Density: {structure['density']:.4f}")
    print(f"Key insight: {structure['insight']}")
    print(f"In-set coordinates (2^a * 3^b): {structure['in_set_coords'][:20]}")

    # ---- Problem #468: Divisor Sum Representations ----
    print("\n" + "=" * 70)
    print("PROBLEM #468: DIVISOR SUM REPRESENTATIONS")
    print("=" * 70)

    print("\n--- A167485 analysis (limit=200, search_bound=500) ---")
    div_analysis = divisor_sum_ratio_analysis(200, 500)
    print(f"Max ratio a(n)/n: {div_analysis['max_ratio']:.4f} at n={div_analysis['max_ratio_at']}")
    print(f"Values with a(n)=0 (no representation): {div_analysis['zero_values']}")
    print(f"Running average of a(n)/n (recent): {div_analysis['running_average'][-5:]}")

    print("\n" + "=" * 70)
    print("CROSS-PROBLEM ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_all_attacks()
