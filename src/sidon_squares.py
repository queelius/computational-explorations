#!/usr/bin/env python3
"""
Problem #773: Sidon Sets Among Perfect Squares

A Sidon set (B2 set) is a set where all pairwise sums are distinct.
Problem #773 asks about the maximum size of a Sidon subset of {1^2, 2^2, ..., n^2}.

Key distinction: the ELEMENTS are squares. For S = {a1^2, ..., ak^2},
the Sidon condition requires all ai^2 + aj^2 (i <= j) to be distinct.
This is NOT the same as requiring all ai + aj to be distinct.

Known: For a general Sidon set in {1, ..., N}, the max size is ~sqrt(N).
Here N = n^2, so the trivial bound is ~sqrt(n^2) = n.
But the algebraic structure of squares may allow larger or force smaller sets.

We compute a(n) = max |S| where S is a Sidon subset of {1^2, 2^2, ..., n^2}
and analyze the growth rate.
"""

import math
from itertools import combinations
from typing import List, Optional, Set, Tuple

import numpy as np


def is_sidon(S: Set[int]) -> bool:
    """
    Check if S is a Sidon set (all pairwise sums a + b with a <= b are distinct).

    This includes self-sums 2*a for each a in S.
    """
    elements = sorted(S)
    sums = set()
    for i, a in enumerate(elements):
        for b in elements[i:]:
            s = a + b
            if s in sums:
                return False
            sums.add(s)
    return True


def squares_up_to(n: int) -> List[int]:
    """Return the list [1^2, 2^2, ..., n^2]."""
    return [i * i for i in range(1, n + 1)]


def max_sidon_in_squares_exhaustive(n: int) -> Tuple[Set[int], int]:
    """
    Find the largest Sidon subset of {1^2, 2^2, ..., n^2} by exhaustive search.

    Tries all subsets from largest to smallest size.
    Suitable for small n (up to about 15-18).

    Returns (best_set, size).
    """
    sq = squares_up_to(n)

    # Try subsets from largest possible down to 1
    for size in range(len(sq), 0, -1):
        for subset in combinations(sq, size):
            if is_sidon(set(subset)):
                return set(subset), size

    return set(), 0


def _backtrack_sidon_squares(
    sq: List[int],
    idx: int,
    current: List[int],
    current_sums: Set[int],
    best: List[int],
    counter: List[int],
    node_limit: int,
) -> None:
    """
    Backtracking search for max Sidon subset of squares.

    Prunes branches where remaining elements cannot beat current best.
    counter[0] tracks visited nodes; search stops at node_limit.
    """
    counter[0] += 1
    if counter[0] >= node_limit:
        return

    remaining = len(sq) - idx
    if len(current) + remaining <= len(best):
        return

    if len(current) > len(best):
        best.clear()
        best.extend(current)

    for i in range(idx, len(sq)):
        if counter[0] >= node_limit:
            return
        # Tighter pruning: remaining from position i onward
        if len(current) + (len(sq) - i) <= len(best):
            return
        x = sq[i]
        new_sums = set()
        conflict = False
        for c in current:
            s = c + x
            if s in current_sums or s in new_sums:
                conflict = True
                break
            new_sums.add(s)
        if conflict:
            continue
        self_sum = 2 * x
        if self_sum in current_sums or self_sum in new_sums:
            continue
        new_sums.add(self_sum)

        current.append(x)
        current_sums |= new_sums
        _backtrack_sidon_squares(
            sq, i + 1, current, current_sums, best, counter, node_limit
        )
        current.pop()
        current_sums -= new_sums


def _multi_greedy_sidon_squares(sq: List[int], trials: int = 50) -> Set[int]:
    """
    Run multiple randomized greedy constructions and return the best.

    Each trial shuffles the input order, then greedily builds a Sidon set.
    """
    import random
    best = _greedy_sidon_squares(sq)
    for _ in range(trials - 1):
        perm = list(sq)
        random.shuffle(perm)
        candidate = _greedy_sidon_squares(perm)
        if len(candidate) > len(best):
            best = candidate
    return best


def max_sidon_in_squares(n: int) -> Tuple[Set[int], int]:
    """
    Find the largest Sidon subset of {1^2, 2^2, ..., n^2}.

    Strategy:
    - n <= 25: exhaustive backtracking (exact)
    - 26 <= n: multi-start greedy + bounded backtracking (heuristic)

    Returns (best_set, size).
    """
    if n <= 0:
        return set(), 0
    if n == 1:
        return {1}, 1

    sq = squares_up_to(n)

    # Seed with greedy solution
    if n <= 25:
        greedy_set = _greedy_sidon_squares(sq)
        best = sorted(greedy_set)
        # Exact backtracking with generous node limit
        counter = [0]
        _backtrack_sidon_squares(sq, 0, [], set(), best, counter, 5_000_000)
    else:
        # For larger n, use multi-start greedy + bounded backtrack
        greedy_set = _multi_greedy_sidon_squares(sq, trials=80)
        best = sorted(greedy_set)
        counter = [0]
        # Bounded backtracking: will improve if possible within budget
        _backtrack_sidon_squares(sq, 0, [], set(), best, counter, 2_000_000)

    result = set(best)
    return result, len(result)


def _greedy_sidon_squares(sq: List[int]) -> Set[int]:
    """Greedy construction of a Sidon subset from a list of squares."""
    selected = []
    sums = set()
    for x in sq:
        new_sums = set()
        conflict = False
        for s in selected:
            pair_sum = s + x
            if pair_sum in sums or pair_sum in new_sums:
                conflict = True
                break
            new_sums.add(pair_sum)
        if conflict:
            continue
        self_sum = 2 * x
        if self_sum in sums or self_sum in new_sums:
            continue
        new_sums.add(self_sum)
        selected.append(x)
        sums |= new_sums
    return set(selected)


def sidon_squares_sequence(max_n: int) -> List[int]:
    """
    Compute the sequence a(n) = max |S| where S is a Sidon subset of {1^2, ..., n^2}.

    Uses an incremental approach: for each n, checks whether adding n^2 to the
    previous best can yield an improvement. Falls back to a full solve when the
    incremental check is ambiguous.

    Returns a list where result[i] = a(i) for i in 0..max_n.
    (result[0] = 0 by convention.)
    """
    seq = [0]  # a(0) = 0
    prev_set: Set[int] = set()
    prev_size = 0

    for n in range(1, max_n + 1):
        new_sq = n * n
        # Quick check: can we just add n^2 to previous best?
        candidate = prev_set | {new_sq}
        if is_sidon(candidate):
            # Adding n^2 preserves Sidon -- this is at least as good
            # But there might be an even better set. For small n, find exact.
            if n <= 25:
                best_set, best_size = max_sidon_in_squares(n)
            else:
                # For large n, accept the extension if it works;
                # also try a fresh greedy to see if we can do better
                sq = squares_up_to(n)
                fresh = _multi_greedy_sidon_squares(sq, trials=40)
                if len(fresh) > len(candidate):
                    best_set, best_size = fresh, len(fresh)
                else:
                    best_set, best_size = candidate, len(candidate)
        else:
            # n^2 doesn't fit -- previous set might still be optimal,
            # or we might need a different set
            if n <= 25:
                best_set, best_size = max_sidon_in_squares(n)
            else:
                sq = squares_up_to(n)
                fresh = _multi_greedy_sidon_squares(sq, trials=40)
                if len(fresh) > prev_size:
                    best_set, best_size = fresh, len(fresh)
                else:
                    best_set, best_size = prev_set, prev_size

        seq.append(best_size)
        prev_set = best_set
        prev_size = best_size

    return seq


def analyze_sidon_squares(max_n: int) -> dict:
    """
    Analyze the growth rate of a(n) = max Sidon subset of {1^2, ..., n^2}.

    Compares to:
    - sqrt(n): the trivial bound from Sidon sets in [1, n]
    - n: the trivial bound from Sidon sets in [1, n^2] (since sqrt(n^2) = n)
    - n^{2/3}: a plausible intermediate growth rate

    Returns a dict with the sequence, ratios, and regression results.
    """
    seq = sidon_squares_sequence(max_n)

    results = {
        "sequence": seq,
        "n_values": list(range(max_n + 1)),
        "ratios": {},
    }

    # Compute ratios for n >= 2
    n_vals = np.array(range(2, max_n + 1), dtype=float)
    a_vals = np.array(seq[2:], dtype=float)

    # Ratio to various growth rates
    results["ratios"]["a(n)/sqrt(n)"] = [
        (int(n), float(a / math.sqrt(n)))
        for n, a in zip(n_vals, a_vals)
    ]
    results["ratios"]["a(n)/n"] = [
        (int(n), float(a / n))
        for n, a in zip(n_vals, a_vals)
    ]
    results["ratios"]["a(n)/n^(2/3)"] = [
        (int(n), float(a / n ** (2 / 3)))
        for n, a in zip(n_vals, a_vals)
    ]

    # Log-log regression to estimate exponent: a(n) ~ C * n^alpha
    # Only use n >= 3 to avoid small-n noise
    if max_n >= 5:
        fit_n = n_vals[1:]  # n >= 3
        fit_a = a_vals[1:]
        mask = fit_a > 0
        if np.sum(mask) >= 2:
            log_n = np.log(fit_n[mask])
            log_a = np.log(fit_a[mask])
            # Linear regression: log(a) = alpha * log(n) + log(C)
            coeffs = np.polyfit(log_n, log_a, 1)
            alpha = coeffs[0]
            C = math.exp(coeffs[1])
            results["regression"] = {
                "alpha": float(alpha),
                "C": float(C),
                "model": f"a(n) ~ {C:.4f} * n^{alpha:.4f}",
            }

    return results


def print_table(seq: List[int], max_n: int) -> None:
    """Print the sequence in a formatted table."""
    print(f"{'n':>4} | {'n^2':>6} | {'a(n)':>5} | {'a(n)/sqrt(n)':>12} | "
          f"{'a(n)/n':>8} | {'a(n)/n^(2/3)':>12}")
    print("-" * 65)
    for n in range(1, max_n + 1):
        a_n = seq[n]
        ratio_sqrt = a_n / math.sqrt(n)
        ratio_n = a_n / n
        ratio_23 = a_n / n ** (2 / 3)
        print(f"{n:>4} | {n*n:>6} | {a_n:>5} | {ratio_sqrt:>12.4f} | "
              f"{ratio_n:>8.4f} | {ratio_23:>12.4f}")


def print_sidon_sets(max_n: int) -> None:
    """Print the actual Sidon sets found for each n."""
    print(f"\n{'n':>4} | {'Max Sidon subset of {{1^2, ..., n^2}}':>50}")
    print("-" * 60)
    for n in range(1, min(max_n + 1, 31)):
        best_set, size = max_sidon_in_squares(n)
        # Show as bases: if set contains k^2, show k
        bases = sorted(int(math.isqrt(x)) for x in best_set)
        squares_str = ", ".join(f"{b}^2" for b in bases)
        print(f"{n:>4} | {{{squares_str}}}  (size {size})")


def main():
    import time

    print("=" * 70)
    print("PROBLEM #773: SIDON SETS AMONG PERFECT SQUARES")
    print("=" * 70)
    print()
    print("For S a Sidon subset of {1^2, 2^2, ..., n^2},")
    print("compute a(n) = max |S|.")
    print()
    print("Sidon condition: all pairwise sums of SQUARES are distinct.")
    print("i.e., all a_i^2 + a_j^2 (i <= j) are distinct.")
    print()

    # --- Phase 1: Compute the full sequence ---
    large_max = 100
    print("-" * 70)
    print(f"PHASE 1: Computing a(n) for n = 1..{large_max}")
    print("-" * 70)
    print()

    t0 = time.time()
    seq = sidon_squares_sequence(large_max)
    elapsed = time.time() - t0
    print(f"Computed in {elapsed:.1f}s")
    print()

    # --- Phase 2: Show table for all computed values ---
    print("-" * 70)
    print("PHASE 2: Full Sequence Table")
    print("-" * 70)
    print()
    print_table(seq, large_max)
    print()

    # --- Phase 3: Show actual Sidon sets for small n ---
    print("-" * 70)
    print("PHASE 3: Actual Sidon Subsets Found (n <= 25)")
    print("-" * 70)
    print_sidon_sets(25)
    print()

    # --- Phase 4: Growth rate analysis ---
    print("-" * 70)
    print("PHASE 4: Growth Rate Analysis")
    print("-" * 70)
    print()

    # Compute regression directly from the already-computed sequence
    n_vals = np.array(range(3, large_max + 1), dtype=float)
    a_vals = np.array(seq[3:], dtype=float)
    mask = a_vals > 0
    if np.sum(mask) >= 2:
        log_n = np.log(n_vals[mask])
        log_a = np.log(a_vals[mask])
        coeffs = np.polyfit(log_n, log_a, 1)
        alpha = coeffs[0]
        C = math.exp(coeffs[1])
        print(f"Log-log regression: a(n) ~ {C:.4f} * n^{alpha:.4f}")
        print(f"  Estimated exponent alpha = {alpha:.4f}")
        print(f"  Estimated constant C     = {C:.4f}")
        print()

        if abs(alpha - 0.5) < 0.1:
            print("  --> Growth is close to sqrt(n)")
        elif abs(alpha - 2 / 3) < 0.1:
            print("  --> Growth is close to n^{2/3}")
        elif abs(alpha - 1.0) < 0.1:
            print("  --> Growth is close to n (linear)")
        else:
            print(f"  --> Growth exponent {alpha:.3f} does not match standard rates")

    # a(n)/n ratio for selected values
    print()
    print("Selected a(n)/n ratios:")
    for n in [10, 20, 30, 50, 75, 100]:
        if n <= large_max:
            print(f"  n={n:3d}: a(n)={seq[n]:3d}, a(n)/n = {seq[n]/n:.4f}")

    # Monotonicity check
    non_decreasing = all(seq[i] <= seq[i + 1]
                         for i in range(1, len(seq) - 1))
    print(f"\nSequence is non-decreasing: {non_decreasing}")

    # Report where sequence increases
    increases = [(i, seq[i]) for i in range(2, len(seq))
                 if seq[i] > seq[i - 1]]
    print(f"Sequence increases at n = {[n for n, _ in increases]}")
    print()

    # --- Phase 5: Spot-check larger values ---
    print("-" * 70)
    print("PHASE 5: Spot Checks at Larger n")
    print("-" * 70)
    print()
    for n in [120, 150, 200]:
        t0 = time.time()
        S, size = max_sidon_in_squares(n)
        dt = time.time() - t0
        assert is_sidon(S), f"VERIFICATION FAILED at n={n}"
        print(f"  n={n:3d}: a(n) >= {size:3d}, a(n)/n = {size/n:.4f}, "
              f"a(n)/n^(2/3) = {size/n**(2/3):.4f}  ({dt:.1f}s)")
    print()

    # --- Theoretical comparison ---
    print("-" * 70)
    print("PHASE 6: Theoretical Context")
    print("-" * 70)
    print("""
BOUNDS AND CONTEXT:
- A Sidon set in {1, ..., N} has at most ~sqrt(N) + O(N^{1/4}) elements.
- For {1^2, ..., n^2}, the ambient set lives in {1, ..., n^2}, so N = n^2.
- Trivial upper bound: a(n) <= sqrt(n^2) + O(n^{1/2}) = n + O(n^{1/2}).
- But squares have extra structure: a^2 + b^2 = c^2 + d^2 is constrained.

QUESTION: Does the algebraic structure of squares allow a(n) to approach n,
or does it force a(n) = o(n)?

Sums of two squares have special properties (Fermat's theorem on sums of
two squares, representation counts). The number of representations of m as
a sum of two squares from {1^2, ..., n^2} is related to divisor functions.

If a(n)/n -> c for some constant 0 < c <= 1, this suggests the density
of a maximal Sidon set among squares is positive.
If a(n)/n -> 0, the Sidon constraint is genuinely restrictive on squares.
""")

    print("=" * 70)
    print("EXPERIMENT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
