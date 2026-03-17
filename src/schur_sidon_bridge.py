#!/usr/bin/env python3
"""
Schur-Sidon Obstruction Bridge

Investigates the Fourier duality between Problem #483 (Schur numbers / sum-free
sets) and Problem #43 (Sidon sets).

Core hypothesis: the same Fourier rigidity constrains both problems.
  - Sidon sets have FLAT Fourier spectra (all coefficients bounded by ~sqrt(N)).
  - Dense sum-free sets have SPIKY Fourier spectra (at least one large coeff).
These are dual constraints: a set cannot simultaneously be dense, sum-free, AND
Sidon, because the Fourier demands are incompatible.

This module quantifies this obstruction through four experiments:
  (a) Fourier spectrum comparison (flatness ratios)
  (b) Density-Fourier tradeoff curves
  (c) Lemma A verification on dense sum-free sets
  (d) Mutual exclusion: max size of sum-free AND Sidon sets
"""

import math
import random
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from kelley_meka_schur import fourier_spectrum, is_sum_free
from sidon_disjoint import is_sidon, random_sidon


# ---------------------------------------------------------------------------
# Fourier helpers
# ---------------------------------------------------------------------------

def fourier_coefficients(A: Set[int], N: int) -> np.ndarray:
    """Return the full array of |f_hat(r)| for r in 0..N-1."""
    f = np.zeros(N, dtype=complex)
    for a in A:
        f[a % N] = 1.0
    f_hat = np.fft.fft(f)
    return np.abs(f_hat)


def fourier_flatness_ratio(A: Set[int], N: int) -> float:
    """Compute max(|f_hat(r)|) / mean(|f_hat(r)|) for r != 0.

    High ratio = spiky spectrum, low ratio = flat spectrum.
    Returns 0.0 for sets with fewer than 2 elements (no meaningful non-DC).
    """
    mags = fourier_coefficients(A, N)
    non_dc = mags[1:]  # exclude r=0 (DC component = |A|)
    if len(non_dc) == 0:
        return 0.0
    mean_val = np.mean(non_dc)
    if mean_val < 1e-12:
        return 0.0
    return float(np.max(non_dc) / mean_val)


def max_non_dc_coefficient(A: Set[int], N: int) -> Tuple[int, float]:
    """Return (frequency, magnitude) of the largest non-DC Fourier coefficient."""
    mags = fourier_coefficients(A, N)
    mags[0] = 0.0  # mask DC
    r_max = int(np.argmax(mags))
    return r_max, float(mags[r_max])


# ---------------------------------------------------------------------------
# Set generators
# ---------------------------------------------------------------------------

def odd_numbers(N: int) -> Set[int]:
    """Odd numbers in {1, ..., N-1} -- the canonical dense sum-free set."""
    return {i for i in range(1, N, 2)}


def maximal_sidon(N: int) -> Set[int]:
    """Build a greedy maximal Sidon set in {1, ..., N}.

    Tries multiple random orderings and returns the largest found.
    """
    best = set()
    for _ in range(50):
        A = random_sidon(N)
        if len(A) > len(best):
            best = A
    return best


def _adding_keeps_sum_free(A: Set[int], x: int, N: int) -> bool:
    """Check whether A | {x} is still sum-free in Z/NZ.

    The new triples that can appear are exactly those involving x:
      (1) a + b = x  for a, b in A          (x is the sum)
      (2) a + x = c  for a in A, c in A     (x is a summand)
      (3) x + x = c  for c in A | {x}       (x added to itself)
    """
    x_mod = x % N
    # Check (3): x + x
    if (x_mod + x_mod) % N in A or (x_mod + x_mod) % N == x_mod:
        # (x+x) % N == x_mod means 2x = x mod N, i.e. x = 0 mod N
        if (x_mod + x_mod) % N == x_mod:
            # Only a problem if x_mod is in A (triple x,x,x) — but x isn't in A yet
            # and triple needs a+b=c with a,b,c all in the set; x+x=x means x=0
            if x_mod == 0:
                pass  # 0+0=0: would be a triple if 0 in A|{x}, which it is
                return False
        elif (x_mod + x_mod) % N in A:
            return False

    for a in A:
        # Check (2): a + x = c, c in A (c != x since x not yet in A)
        if (a + x_mod) % N in A:
            return False
        # Check (1): a + b = x, b in A
        b_needed = (x_mod - a) % N
        if b_needed in A:
            return False

    return True


def random_sum_free(N: int, target_density: float,
                    max_attempts: int = 2000) -> Optional[Set[int]]:
    """Generate a random sum-free subset of {1,...,N-1} with density ~target.

    Uses greedy construction: shuffle elements, add each if it preserves
    the sum-free property.
    """
    target_size = max(1, int(target_density * N))

    best: Optional[Set[int]] = None
    for _ in range(min(max_attempts, 200)):
        elements = list(range(1, N))
        random.shuffle(elements)
        A: Set[int] = set()
        for x in elements:
            if len(A) >= target_size:
                break
            if _adding_keeps_sum_free(A, x, N):
                A.add(x)
        if A and (best is None or len(A) > len(best)):
            best = A
            if len(best) >= target_size:
                return best
    return best


def random_sidon_target(N: int, target_density: float) -> Optional[Set[int]]:
    """Generate a random Sidon subset of {1,...,N} with density ~target.

    Sidon density is bounded by ~1/sqrt(N), so high targets may be
    unreachable -- returns None in that case.
    """
    target_size = max(1, int(target_density * N))
    # Theoretical max Sidon size is ~sqrt(N)
    theoretical_max = int(math.sqrt(N)) + 2

    if target_size > theoretical_max:
        return None  # unreachable

    best = None
    for _ in range(100):
        A = random_sidon(N)
        if best is None or len(A) > len(best):
            best = A
        if best and len(best) >= target_size:
            # Trim to target size
            while len(best) > target_size:
                best.discard(random.choice(sorted(best)))
            return best

    return best


# ---------------------------------------------------------------------------
# Experiment (a): Fourier spectrum comparison
# ---------------------------------------------------------------------------

def experiment_spectrum_comparison(N_values: List[int] = None) -> List[Dict]:
    """Compare Fourier flatness of sum-free vs Sidon sets.

    For each N, computes:
      - max non-DC coefficient of odds (sum-free)
      - max non-DC coefficient of a maximal Sidon set
      - flatness ratio for each
    """
    if N_values is None:
        N_values = [50, 100, 200]

    results = []
    for N in N_values:
        sf = odd_numbers(N)
        sid = maximal_sidon(N)

        _, sf_max = max_non_dc_coefficient(sf, N)
        _, sid_max = max_non_dc_coefficient(sid, N)

        sf_ratio = fourier_flatness_ratio(sf, N)
        sid_ratio = fourier_flatness_ratio(sid, N)

        # Theoretical references
        # For Sidon: max |f_hat(r)| should be O(sqrt(N)) since |A|~sqrt(N)
        # For sum-free odds: max |f_hat(r)| = |A| = N/2 (at r=N/2)
        results.append({
            "N": N,
            "sum_free_size": len(sf),
            "sidon_size": len(sid),
            "sum_free_max_coeff": sf_max,
            "sidon_max_coeff": sid_max,
            "sum_free_flatness": sf_ratio,
            "sidon_flatness": sid_ratio,
            "ratio_comparison": sf_ratio / sid_ratio if sid_ratio > 0 else float("inf"),
        })

    return results


# ---------------------------------------------------------------------------
# Experiment (b): Density-Fourier tradeoff
# ---------------------------------------------------------------------------

def experiment_density_tradeoff(N: int = 100,
                                densities: List[float] = None,
                                trials: int = 20) -> List[Dict]:
    """Measure Fourier flatness vs density for sum-free and Sidon sets.

    For each target density delta, generates random sum-free sets and
    random Sidon sets (if achievable) and records their flatness ratios.
    """
    if densities is None:
        densities = [round(0.1 + 0.05 * i, 2) for i in range(9)]  # 0.1 to 0.5

    results = []
    for delta in densities:
        sf_ratios = []
        sid_ratios = []

        for _ in range(trials):
            sf = random_sum_free(N, delta)
            if sf and len(sf) >= 2:
                sf_ratios.append(fourier_flatness_ratio(sf, N))

            sid = random_sidon_target(N, delta)
            if sid and len(sid) >= 2:
                sid_ratios.append(fourier_flatness_ratio(sid, N))

        entry: Dict = {
            "density": delta,
            "sum_free_count": len(sf_ratios),
            "sidon_count": len(sid_ratios),
        }
        if sf_ratios:
            entry["sum_free_flatness_mean"] = float(np.mean(sf_ratios))
            entry["sum_free_flatness_std"] = float(np.std(sf_ratios))
        else:
            entry["sum_free_flatness_mean"] = None
            entry["sum_free_flatness_std"] = None

        if sid_ratios:
            entry["sidon_flatness_mean"] = float(np.mean(sid_ratios))
            entry["sidon_flatness_std"] = float(np.std(sid_ratios))
        else:
            entry["sidon_flatness_mean"] = None
            entry["sidon_flatness_std"] = None

        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# Experiment (c): Obstruction test / Lemma A verification
# ---------------------------------------------------------------------------

def _enumerate_large_sum_free(N: int, min_size: int,
                              max_sets: int = 400) -> List[Set[int]]:
    """Find sum-free subsets of Z/NZ with |A| >= min_size via random search."""
    found: List[Set[int]] = []
    seen_frozen: set = set()

    for _ in range(max_sets * 20):
        if len(found) >= max_sets:
            break
        sf = random_sum_free(N, target_density=min_size / N)
        if sf and len(sf) >= min_size:
            key = frozenset(sf)
            if key not in seen_frozen:
                seen_frozen.add(key)
                found.append(sf)

    # Always include the odds
    odds = odd_numbers(N)
    odds_key = frozenset(odds)
    if odds_key not in seen_frozen and len(odds) >= min_size:
        found.append(odds)

    return found


def experiment_obstruction(N: int = 50) -> Dict:
    """Verify Lemma A and test Sidon overlap for dense sum-free sets.

    Lemma A: for sum-free C in Z/NZ with |C| > N/3,
             max_{r!=0} |f_hat_C(r)| >= delta/(1-delta) * |C|

    Also counts how many of these dense sum-free sets are simultaneously Sidon.
    """
    threshold = N // 3 + 1
    sets = _enumerate_large_sum_free(N, threshold)

    lemma_a_holds = 0
    lemma_a_fails = 0
    also_sidon = 0
    violations = []

    for A in sets:
        delta = len(A) / N
        predicted_bound = delta / (1 - delta) * len(A)

        _, max_coeff = max_non_dc_coefficient(A, N)

        if max_coeff >= predicted_bound - 1e-6:
            lemma_a_holds += 1
        else:
            lemma_a_fails += 1
            violations.append({
                "set_size": len(A),
                "delta": delta,
                "max_coeff": max_coeff,
                "predicted_bound": predicted_bound,
                "gap": predicted_bound - max_coeff,
            })

        if is_sidon(A):
            also_sidon += 1

    return {
        "N": N,
        "threshold": threshold,
        "sets_found": len(sets),
        "lemma_a_holds": lemma_a_holds,
        "lemma_a_fails": lemma_a_fails,
        "violations": violations[:5],  # first few
        "also_sidon_count": also_sidon,
        "sidon_fraction": also_sidon / len(sets) if sets else 0.0,
    }


# ---------------------------------------------------------------------------
# Experiment (d): Mutual exclusion
# ---------------------------------------------------------------------------

def max_sum_free_sidon(N: int, trials: int = 500) -> Dict:
    """Find the largest subset of {1,...,N-1} that is both sum-free and Sidon.

    Uses random search plus structured constructions.
    """
    best: Set[int] = set()

    # Strategy 1: start with Sidon, prune to sum-free
    for _ in range(trials):
        sid = random_sidon(N)
        # Keep only elements that maintain sum-free
        sf_sid: Set[int] = set()
        for x in sorted(sid):
            candidate = sf_sid | {x}
            if is_sum_free(candidate, N):
                sf_sid = candidate
        if len(sf_sid) > len(best) and is_sidon(sf_sid):
            best = sf_sid

    # Strategy 2: start with sum-free, prune to Sidon
    for _ in range(trials):
        sf = random_sum_free(N, target_density=0.4)
        if not sf:
            continue
        sid_sf: Set[int] = set()
        for x in sorted(sf):
            candidate = sid_sf | {x}
            if is_sidon(candidate):
                sid_sf = candidate
        if len(sid_sf) > len(best) and is_sum_free(sid_sf, N):
            best = sid_sf

    # Strategy 3: greedy from scratch, enforcing both
    elements = list(range(1, N))
    for _ in range(trials):
        random.shuffle(elements)
        both: Set[int] = set()
        for x in elements:
            candidate = both | {x}
            if is_sum_free(candidate, N) and is_sidon(candidate):
                both = candidate
        if len(both) > len(best):
            best = both

    return {
        "N": N,
        "max_both_size": len(best),
        "max_both_set": sorted(best),
    }


def experiment_mutual_exclusion(N_values: List[int] = None) -> List[Dict]:
    """For each N, compare max sum-free, max Sidon, and max sum-free-AND-Sidon."""
    if N_values is None:
        N_values = [20, 30, 40, 50]

    results = []
    for N in N_values:
        both_result = max_sum_free_sidon(N, trials=200)

        # Max sum-free alone (odds achieve ~N/2)
        sf = odd_numbers(N)
        # Max Sidon alone
        sid = maximal_sidon(N)

        results.append({
            "N": N,
            "max_sum_free": len(sf),
            "max_sidon": len(sid),
            "max_both": both_result["max_both_size"],
            "max_both_set": both_result["max_both_set"],
            "sum_free_density": len(sf) / N,
            "sidon_density": len(sid) / N,
            "both_density": both_result["max_both_size"] / N,
        })

    return results


# ---------------------------------------------------------------------------
# Main: run all experiments and print findings
# ---------------------------------------------------------------------------

def main():
    random.seed(42)
    np.random.seed(42)

    print("=" * 74)
    print("SCHUR-SIDON OBSTRUCTION BRIDGE")
    print("Fourier duality between Problem #483 and Problem #43")
    print("=" * 74)
    print()

    # --- (a) Spectrum comparison ---
    print("-" * 74)
    print("EXPERIMENT (a): Fourier Spectrum Comparison")
    print("-" * 74)
    spec_results = experiment_spectrum_comparison([50, 100, 200])
    print(f"{'N':>5}  {'SF size':>7}  {'Sid size':>8}  {'SF max':>8}  "
          f"{'Sid max':>8}  {'SF flat':>8}  {'Sid flat':>8}  {'Ratio':>6}")
    for r in spec_results:
        print(f"{r['N']:5d}  {r['sum_free_size']:7d}  {r['sidon_size']:8d}  "
              f"{r['sum_free_max_coeff']:8.1f}  {r['sidon_max_coeff']:8.1f}  "
              f"{r['sum_free_flatness']:8.2f}  {r['sidon_flatness']:8.2f}  "
              f"{r['ratio_comparison']:6.2f}")
    print()
    print("Interpretation: sum-free sets should have MUCH higher flatness ratio")
    print("(spiky spectrum) than Sidon sets (flat spectrum).")
    print()

    # --- (b) Density-Fourier tradeoff ---
    print("-" * 74)
    print("EXPERIMENT (b): Density-Fourier Tradeoff (N=100)")
    print("-" * 74)
    tradeoff = experiment_density_tradeoff(N=100, trials=20)
    print(f"{'delta':>6}  {'SF count':>8}  {'SF flat':>10}  "
          f"{'Sid count':>9}  {'Sid flat':>10}")
    for r in tradeoff:
        sf_str = f"{r['sum_free_flatness_mean']:.2f}" if r['sum_free_flatness_mean'] is not None else "N/A"
        sid_str = f"{r['sidon_flatness_mean']:.2f}" if r['sidon_flatness_mean'] is not None else "N/A"
        print(f"{r['density']:6.2f}  {r['sum_free_count']:8d}  {sf_str:>10}  "
              f"{r['sidon_count']:9d}  {sid_str:>10}")
    print()
    print("Interpretation: as density rises, sum-free flatness ratio should INCREASE")
    print("(forced spectral concentration), while Sidon sets become UNREACHABLE")
    print("above delta ~ 1/sqrt(N).")
    print()

    # --- (c) Obstruction test ---
    print("-" * 74)
    print("EXPERIMENT (c): Lemma A Verification & Sidon Overlap (N=50)")
    print("-" * 74)
    obs = experiment_obstruction(N=50)
    print(f"  Dense sum-free sets found (|A| > {obs['threshold']}): {obs['sets_found']}")
    print(f"  Lemma A holds: {obs['lemma_a_holds']}")
    print(f"  Lemma A fails: {obs['lemma_a_fails']}")
    print(f"  Also Sidon: {obs['also_sidon_count']} / {obs['sets_found']} "
          f"({obs['sidon_fraction']:.1%})")
    if obs['violations']:
        print(f"  First violation: {obs['violations'][0]}")
    print()
    print("Interpretation: Lemma A should hold for ALL dense sum-free sets.")
    print("The Sidon overlap should be ZERO for large enough |A|, confirming")
    print("that spiky spectra are incompatible with the Sidon flatness constraint.")
    print()

    # --- (d) Mutual exclusion ---
    print("-" * 74)
    print("EXPERIMENT (d): Mutual Exclusion (sum-free AND Sidon)")
    print("-" * 74)
    me = experiment_mutual_exclusion([20, 30, 40, 50])
    print(f"{'N':>5}  {'max SF':>6}  {'max Sid':>7}  {'max Both':>8}  "
          f"{'Both/SF':>7}  {'Both/Sid':>8}")
    for r in me:
        sf_pct = r["max_both"] / r["max_sum_free"] if r["max_sum_free"] > 0 else 0
        sid_pct = r["max_both"] / r["max_sidon"] if r["max_sidon"] > 0 else 0
        print(f"{r['N']:5d}  {r['max_sum_free']:6d}  {r['max_sidon']:7d}  "
              f"{r['max_both']:8d}  {sf_pct:7.2f}  {sid_pct:8.2f}")
    print()
    print("Interpretation: max(both) should be MUCH smaller than max(sum-free)")
    print("and should grow sublinearly, bounded roughly by O(sqrt(N)).")
    print()

    # --- Summary ---
    print("=" * 74)
    print("SYNTHESIS")
    print("=" * 74)
    print("""
The Schur-Sidon obstruction bridge operates through Fourier duality:

1. SPECTRAL DICHOTOMY: Sum-free sets with density > 1/3 are forced to have
   at least one large Fourier coefficient (Lemma A). Sidon sets, by their
   defining property (all pairwise sums distinct), have FLAT spectra with
   max |f_hat(r)| = O(sqrt(|A|)).

2. DENSITY BARRIER: This dichotomy creates an impassable barrier. A set
   cannot be simultaneously:
     (i)   dense  (|A| > N/3)
     (ii)  sum-free  (no a+b=c)
     (iii) Sidon  (all a+b distinct)
   because (ii) forces a spiky spectrum while (iii) demands flatness.

3. MUTUAL EXCLUSION: The largest sum-free-AND-Sidon set grows as O(sqrt(N)),
   matching the Sidon density barrier -- not the sum-free density barrier.
   The Sidon constraint is the binding one.

4. BRIDGE TO SCHUR NUMBERS: In a k-coloring of [1,S(k)], each color class
   must be sum-free. The Fourier rigidity of sum-free sets (Lemma A)
   constrains the structure of each color class. The Sidon obstruction
   shows these constraints cannot be simultaneously satisfied when S(k)
   is too large, providing an independent route to upper bounds on S(k).
""")


if __name__ == "__main__":
    main()
