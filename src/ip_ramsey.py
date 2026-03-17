#!/usr/bin/env python3
"""
IP-Ramsey Experiments for Erdős Problem #948.

Problem: In any k-colouring of ℕ, does there exist a sequence a₁ < a₂ < ...
with aₙ < f(n) for infinitely many n, whose FS-set (all finite subset sums)
misses at least one colour?

Hindman (#532): Without growth constraints, monochromatic FS-sets exist.
Galvin: With growth constraints, monochromatic FS-sets cannot be forced.
#948: Can we at least force the FS-set to MISS one colour?

This module implements computational experiments to explore the landscape.
"""

import math
from itertools import combinations
from typing import Set, List, Tuple, Dict, FrozenSet, Optional, Callable


# ── FS-Set (IP-set) computation ──────────────────────────────────────

def fs_set(seq: List[int], max_size: Optional[int] = None) -> Set[int]:
    """Compute the FS-set (all nonempty finite subset sums) of a sequence.

    For efficiency, limits to subsets of size ≤ max_size if given.
    """
    result = set()
    n = len(seq)
    if max_size is None:
        max_size = n
    for size in range(1, min(max_size, n) + 1):
        for combo in combinations(seq, size):
            result.add(sum(combo))
    return result


def fs_set_incremental(seq: List[int]) -> Set[int]:
    """Compute FS-set incrementally (faster for full computation).

    Uses the identity: FS({a₁,...,aₙ}) = FS({a₁,...,aₙ₋₁}) ∪ {aₙ + s : s ∈ FS({a₁,...,aₙ₋₁})} ∪ {aₙ}.
    """
    result = set()
    for a in seq:
        new_sums = {a + s for s in result}
        new_sums.add(a)
        result |= new_sums
    return result


# ── Colouring schemes ────────────────────────────────────────────────

def galvin_coloring(n: int, k: int) -> int:
    """Galvin-style colouring using 2-adic valuation mod k.

    Colour(n) = v₂(n) mod k, where v₂(n) is the 2-adic valuation.
    This is the classical obstruction to monochromatic FS-sets.
    """
    if n == 0:
        return 0
    v = 0
    m = abs(n)
    while m % 2 == 0:
        v += 1
        m //= 2
    return v % k


def padic_coloring(n: int, p: int, k: int) -> int:
    """p-adic valuation coloring mod k."""
    if n == 0:
        return 0
    v = 0
    m = abs(n)
    while m % p == 0:
        v += 1
        m //= p
    return v % k


def irrational_rotation_coloring(n: int, k: int, theta: float = 0.0) -> int:
    """Katznelson-style colouring via irrational rotation.

    Colour(n) = ⌊k · {θn}⌋ where {x} = x - ⌊x⌋ is the fractional part.
    Used in the resolution of #894 (lacunary sequences).
    """
    if theta == 0.0:
        theta = (math.sqrt(5) - 1) / 2  # golden ratio
    frac = (theta * n) % 1.0
    return int(frac * k) % k


def random_coloring(n: int, k: int, seed: int = 42) -> int:
    """Pseudorandom colouring (deterministic via seed)."""
    import hashlib
    h = hashlib.md5(f"{n}:{seed}".encode()).hexdigest()
    return int(h, 16) % k


# ── Experiment 1: FS-set colour coverage under Galvin ────────────────

def experiment_galvin_fs(N: int = 100, k: int = 3,
                         growth: str = "polynomial") -> Dict:
    """Test how many colours the FS-set hits under Galvin colouring.

    Generates subsequences of [1..N] with various growth rates,
    computes their FS-sets, and counts how many of k colours appear.

    Args:
        N: upper limit for sequence elements
        k: number of colours
        growth: "polynomial" (a_n ~ n²), "linear" (a_n ~ 2n), or "log" (a_n ~ n log n)

    Returns:
        Dict with statistics on colour coverage.
    """
    # Generate candidate sequences with given growth rate
    if growth == "polynomial":
        seq = [n**2 for n in range(1, int(N**0.5) + 1) if n**2 <= N]
    elif growth == "linear":
        seq = list(range(1, N + 1, 2))[:20]  # odd numbers, capped
    elif growth == "log":
        seq = []
        n = 1
        while n <= N:
            seq.append(n)
            n = max(n + 1, int(n * math.log(max(n, 2))))
    elif growth == "lacunary":
        seq = []
        a = 1
        while a <= N:
            seq.append(a)
            a = max(a + 1, int(a * 1.5))
    else:
        seq = list(range(1, min(N + 1, 16)))

    # Compute FS-set (limit subset size for performance)
    max_subset = min(len(seq), 12)
    sums = fs_set(seq, max_size=max_subset)

    # Count colours
    colour_counts = [0] * k
    for s in sums:
        c = galvin_coloring(s, k)
        colour_counts[c] += 1

    colours_hit = sum(1 for c in colour_counts if c > 0)
    colours_missed = k - colours_hit

    return {
        "N": N, "k": k, "growth": growth,
        "seq_len": len(seq), "seq_sample": seq[:10],
        "fs_size": len(sums),
        "max_subset_size": max_subset,
        "colour_counts": colour_counts,
        "colours_hit": colours_hit,
        "colours_missed": colours_missed,
        "all_colours_hit": colours_hit == k,
    }


# ── Experiment 2: Greedy colouring to minimize FS coverage ───────────

def greedy_minimize_fs_coverage(N: int, k: int, seq_len: int = 8) -> Dict:
    """Greedily colour {1..N} to minimize max colour coverage of FS-sets.

    For each n in order, assign the colour that minimizes the number of
    distinct colours appearing in FS-sets of subsequences of length ≤ seq_len.

    This is the computational dual of #948: if even greedy can't prevent
    all colours appearing, the answer to #948 is likely "yes".
    """
    colours = {}

    for n in range(1, N + 1):
        best_c = 0
        best_score = float('inf')

        for c in range(k):
            colours[n] = c
            # Quick score: count how many colours the FS-set of {1..n} hits
            # (simplified - just check the first few sums involving n)
            recent = [m for m in range(max(1, n - seq_len), n + 1)]
            sums = fs_set_incremental(recent)
            score = len({colours.get(s, -1) for s in sums if s in colours} - {-1})
            if score < best_score:
                best_score = score
                best_c = c

        colours[n] = best_c

    # Evaluate: find the subsequence whose FS-set hits the most colours
    best_coverage = 0
    best_seq = []
    # Try arithmetic-like subsequences
    for start in range(1, min(N + 1, 20)):
        for step in range(1, min(N // 2 + 1, 10)):
            seq = [start + i * step for i in range(seq_len) if start + i * step <= N]
            if len(seq) < 3:
                continue
            sums = fs_set_incremental(seq)
            coverage = len({colours.get(s, -1) for s in sums if s in colours} - {-1})
            if coverage > best_coverage:
                best_coverage = coverage
                best_seq = seq

    return {
        "N": N, "k": k,
        "best_coverage": best_coverage,
        "best_seq": best_seq,
        "all_colours_hit": best_coverage == k,
        "colouring_sample": {n: colours[n] for n in range(1, min(N + 1, 21))},
    }


# ── Experiment 3: Compare colouring schemes ──────────────────────────

def compare_colorings(N: int = 200, k: int = 3) -> List[Dict]:
    """Compare different colouring schemes on FS-set colour coverage.

    For each scheme, generate many subsequences and measure how
    frequently the FS-set hits all k colours vs. misses at least one.
    """
    schemes = [
        ("galvin", lambda n: galvin_coloring(n, k)),
        ("3-adic", lambda n: padic_coloring(n, 3, k)),
        ("golden_rotation", lambda n: irrational_rotation_coloring(n, k)),
        ("random_42", lambda n: random_coloring(n, k, seed=42)),
    ]

    results = []
    for name, colour_fn in schemes:
        total_seqs = 0
        all_hit_count = 0
        miss_count = 0

        # Test various starting points and growth rates
        for start in range(1, min(N // 2, 30)):
            for rate in [1, 2, 3, 5]:
                seq = []
                a = start
                for _ in range(10):
                    if a > N:
                        break
                    seq.append(a)
                    a += rate * (len(seq) + 1)

                if len(seq) < 3:
                    continue

                sums = fs_set_incremental(seq)
                colours_seen = set()
                for s in sums:
                    if 1 <= s <= N:
                        colours_seen.add(colour_fn(s))

                total_seqs += 1
                if len(colours_seen) == k:
                    all_hit_count += 1
                if len(colours_seen) < k:
                    miss_count += 1

        results.append({
            "scheme": name,
            "total_seqs": total_seqs,
            "all_colours_hit": all_hit_count,
            "missed_at_least_one": miss_count,
            "frac_all_hit": all_hit_count / max(total_seqs, 1),
        })

    return results


# ── Experiment 4: Growth rate phase transition ───────────────────────

def growth_phase_transition(N: int = 500, k: int = 2) -> List[Dict]:
    """Test whether there's a growth rate threshold for FS-set colour coverage.

    For sequences with growth rate a_n ~ C·n^α, vary α from 1 to 3
    and measure the probability that the FS-set hits all colours.
    """
    results = []
    for alpha_times_10 in range(10, 31, 2):  # α from 1.0 to 3.0
        alpha = alpha_times_10 / 10
        total = 0
        all_hit = 0

        for trial in range(20):
            seq = []
            for n in range(1, 30):
                a = int((n + trial) ** alpha)
                if a > N:
                    break
                if a > 0 and (not seq or a > seq[-1]):
                    seq.append(a)

            if len(seq) < 4:
                continue

            sums = fs_set_incremental(seq)
            colours = {galvin_coloring(s, k) for s in sums if 1 <= s <= N}

            total += 1
            if len(colours) == k:
                all_hit += 1

        results.append({
            "alpha": alpha,
            "total": total,
            "all_hit": all_hit,
            "frac_all_hit": all_hit / max(total, 1),
        })

    return results


# ── Experiment 5: Deep phase transition around α=2 ───────────────────

def deep_phase_transition(N: int = 2000, k: int = 2,
                          alpha_min: float = 1.5, alpha_max: float = 2.5,
                          alpha_steps: int = 21, trials: int = 100,
                          coloring: str = "galvin") -> List[Dict]:
    """High-resolution phase transition analysis around α≈2.

    Uses finer α grid, more trials, larger N, and multiple coloring schemes
    to precisely locate the critical exponent.

    Args:
        N: upper limit for sequence elements
        k: number of colours
        alpha_min, alpha_max: range of growth exponents
        alpha_steps: number of α values to test
        trials: number of random starting offsets per α
        coloring: "galvin", "3-adic", "rotation", or "random"

    Returns:
        List of dicts with α, coverage statistics, and sequence metadata.
    """
    colour_fn: Callable[[int], int]
    if coloring == "galvin":
        colour_fn = lambda n: galvin_coloring(n, k)
    elif coloring == "3-adic":
        colour_fn = lambda n: padic_coloring(n, 3, k)
    elif coloring == "rotation":
        colour_fn = lambda n: irrational_rotation_coloring(n, k)
    elif coloring == "random":
        colour_fn = lambda n: random_coloring(n, k, seed=42)
    else:
        colour_fn = lambda n: galvin_coloring(n, k)

    results = []
    for step in range(alpha_steps):
        alpha = alpha_min + (alpha_max - alpha_min) * step / max(alpha_steps - 1, 1)
        total = 0
        all_hit = 0
        miss_examples = []
        avg_seq_len = 0
        avg_fs_size = 0

        for trial in range(trials):
            seq = []
            offset = trial * 0.37  # irrational offset for variety
            for n in range(1, 60):
                a = int((n + offset) ** alpha)
                if a > N:
                    break
                if a > 0 and (not seq or a > seq[-1]):
                    seq.append(a)

            if len(seq) < 4:
                continue

            sums = fs_set_incremental(seq)
            colours = {colour_fn(s) for s in sums if 1 <= s <= N}

            total += 1
            avg_seq_len += len(seq)
            avg_fs_size += len(sums)
            if len(colours) == k:
                all_hit += 1
            elif len(miss_examples) < 3:
                missed = set(range(k)) - colours
                miss_examples.append({
                    "seq_prefix": seq[:6],
                    "seq_len": len(seq),
                    "fs_size": len(sums),
                    "colours_hit": len(colours),
                    "missed_colours": sorted(missed),
                })

        frac = all_hit / max(total, 1)
        results.append({
            "alpha": round(alpha, 3),
            "total": total,
            "all_hit": all_hit,
            "frac_all_hit": frac,
            "avg_seq_len": avg_seq_len / max(total, 1),
            "avg_fs_size": avg_fs_size / max(total, 1),
            "miss_examples": miss_examples,
            "coloring": coloring,
        })

    return results


def multi_scheme_phase_transition(N: int = 2000, k: int = 2) -> Dict[str, List[Dict]]:
    """Run deep phase transition for all colouring schemes.

    Returns dict mapping scheme name to results list.
    """
    schemes = ["galvin", "3-adic", "rotation", "random"]
    all_results = {}
    for scheme in schemes:
        all_results[scheme] = deep_phase_transition(
            N=N, k=k, alpha_min=1.5, alpha_max=2.5,
            alpha_steps=21, trials=80, coloring=scheme,
        )
    return all_results


def phase_transition_summary(results: List[Dict]) -> Dict:
    """Summarize phase transition results to find critical exponent.

    Finds the α where coverage drops below 95% and 50%.
    """
    alphas = [r["alpha"] for r in results]
    fracs = [r["frac_all_hit"] for r in results]

    # Find critical exponents (first α where frac drops below threshold)
    alpha_95 = None
    alpha_50 = None
    for alpha, frac in zip(alphas, fracs):
        if frac < 0.95 and alpha_95 is None:
            alpha_95 = alpha
        if frac < 0.50 and alpha_50 is None:
            alpha_50 = alpha

    # Find minimum coverage
    min_idx = min(range(len(fracs)), key=lambda i: fracs[i])

    return {
        "alpha_95": alpha_95,
        "alpha_50": alpha_50,
        "min_frac": fracs[min_idx],
        "min_alpha": alphas[min_idx],
        "alphas": alphas,
        "fracs": fracs,
    }


# ── Experiment 6: Higher colour counts (k=4,5) ──────────────────────

def higher_k_phase_transition(N: int = 500, k_values: Optional[List[int]] = None,
                               alpha_min: float = 1.0, alpha_max: float = 3.0,
                               alpha_steps: int = 11, trials: int = 50) -> Dict[int, List[Dict]]:
    """Phase transition for higher colour counts under Galvin colouring.

    For each k in k_values, sweep α from alpha_min to alpha_max and record
    what fraction of trials hit all k colours.  This reveals how α_95 shifts
    with the number of colours.

    Args:
        N: upper limit for sequence elements
        k_values: list of colour counts to test (default [4, 5])
        alpha_min, alpha_max: range of growth exponents
        alpha_steps: number of α values
        trials: random starting offsets per α

    Returns:
        Dict mapping k -> list of per-α result dicts (same schema as
        deep_phase_transition).
    """
    if k_values is None:
        k_values = [4, 5]

    all_results: Dict[int, List[Dict]] = {}
    for k in k_values:
        colour_fn = lambda n, _k=k: galvin_coloring(n, _k)
        per_alpha: List[Dict] = []
        for step in range(alpha_steps):
            alpha = alpha_min + (alpha_max - alpha_min) * step / max(alpha_steps - 1, 1)
            total = 0
            all_hit = 0
            avg_seq_len = 0.0
            avg_fs_size = 0.0
            miss_examples: List[Dict] = []

            for trial in range(trials):
                seq: List[int] = []
                offset = trial * 0.37
                for n in range(1, 60):
                    a = int((n + offset) ** alpha)
                    if a > N:
                        break
                    if a > 0 and (not seq or a > seq[-1]):
                        seq.append(a)

                if len(seq) < 4:
                    continue

                sums = fs_set_incremental(seq)
                colours = {colour_fn(s) for s in sums if 1 <= s <= N}

                total += 1
                avg_seq_len += len(seq)
                avg_fs_size += len(sums)
                if len(colours) == k:
                    all_hit += 1
                elif len(miss_examples) < 3:
                    missed = set(range(k)) - colours
                    miss_examples.append({
                        "seq_prefix": seq[:6],
                        "seq_len": len(seq),
                        "fs_size": len(sums),
                        "colours_hit": len(colours),
                        "missed_colours": sorted(missed),
                    })

            frac = all_hit / max(total, 1)
            per_alpha.append({
                "alpha": round(alpha, 3),
                "k": k,
                "total": total,
                "all_hit": all_hit,
                "frac_all_hit": frac,
                "avg_seq_len": avg_seq_len / max(total, 1),
                "avg_fs_size": avg_fs_size / max(total, 1),
                "miss_examples": miss_examples,
                "coloring": "galvin",
            })
        all_results[k] = per_alpha
    return all_results


# ── Experiment 7: Fine alpha grid, multi-scheme, k=2 ────────────────

def fine_grid_phase_transition(N: int = 1000,
                                alpha_min: float = 1.5,
                                alpha_max: float = 2.5,
                                alpha_steps: int = 51,
                                trials: int = 50,
                                schemes: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
    """Fine-grained α sweep (0.02 spacing) for k=2 across multiple schemes.

    The finer grid reveals whether the phase transition is a sharp step
    function or a gradual sigmoid, and allows more precise location of α_95.

    Args:
        N: upper limit for sequence elements
        alpha_min, alpha_max: range of growth exponents
        alpha_steps: number of α values (51 gives ~0.02 spacing over [1.5,2.5])
        trials: random starting offsets per α
        schemes: colouring scheme names (default ["galvin", "3-adic", "random"])

    Returns:
        Dict mapping scheme name -> list of per-α result dicts.
    """
    if schemes is None:
        schemes = ["galvin", "3-adic", "random"]

    k = 2
    all_results: Dict[str, List[Dict]] = {}
    for scheme in schemes:
        results = deep_phase_transition(
            N=N, k=k,
            alpha_min=alpha_min, alpha_max=alpha_max,
            alpha_steps=alpha_steps, trials=trials,
            coloring=scheme,
        )
        all_results[scheme] = results
    return all_results


# ── Main ─────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("IP-RAMSEY EXPERIMENTS (ERDŐS #948)")
    print("=" * 70)

    print("\n--- Experiment 1: Galvin FS-Set Coverage ---")
    for growth in ["polynomial", "linear", "lacunary"]:
        r = experiment_galvin_fs(N=200, k=3, growth=growth)
        print(f"  {growth:12s}: seq_len={r['seq_len']:3d}, FS_size={r['fs_size']:6d}, "
              f"colours_hit={r['colours_hit']}/{r['k']}, missed={r['colours_missed']}")

    print("\n--- Experiment 2: Greedy Minimization ---")
    for k in [2, 3]:
        r = greedy_minimize_fs_coverage(N=50, k=k)
        print(f"  k={k}: best_coverage={r['best_coverage']}/{k}, "
              f"all_hit={r['all_colours_hit']}, seq={r['best_seq']}")

    print("\n--- Experiment 3: Colouring Scheme Comparison ---")
    results = compare_colorings(N=200, k=3)
    for r in results:
        print(f"  {r['scheme']:20s}: {r['frac_all_hit']:.1%} all-hit "
              f"({r['all_colours_hit']}/{r['total_seqs']} seqs)")

    print("\n--- Experiment 4: Growth Rate Phase Transition ---")
    results = growth_phase_transition(N=500, k=2)
    for r in results:
        print(f"  α={r['alpha']:.1f}: {r['frac_all_hit']:.0%} all-hit "
              f"({r['all_hit']}/{r['total']} trials)")

    print("\n--- Experiment 5: Deep Phase Transition (α=1.5..2.5) ---")
    for scheme in ["galvin", "3-adic", "rotation"]:
        print(f"\n  [{scheme}] (N={2000}, k=2, 80 trials/α)")
        results = deep_phase_transition(
            N=2000, k=2, alpha_min=1.5, alpha_max=2.5,
            alpha_steps=21, trials=80, coloring=scheme,
        )
        summary = phase_transition_summary(results)
        for r in results:
            marker = " ←" if r["frac_all_hit"] < 0.95 else ""
            print(f"    α={r['alpha']:.2f}: {r['frac_all_hit']:5.1%} all-hit "
                  f"({r['all_hit']:3d}/{r['total']:3d}), "
                  f"avg_seq={r['avg_seq_len']:.1f}, avg_fs={r['avg_fs_size']:.0f}{marker}")
        print(f"  Summary: α_95={summary['alpha_95']}, α_50={summary['alpha_50']}, "
              f"min={summary['min_frac']:.1%} at α={summary['min_alpha']}")

    print("\n--- Experiment 6: Higher Colour Counts (k=4,5), Galvin ---")
    higher_k = higher_k_phase_transition(
        N=500, k_values=[4, 5],
        alpha_min=1.0, alpha_max=3.0, alpha_steps=11, trials=50,
    )
    for k_val, data in sorted(higher_k.items()):
        summary = phase_transition_summary(data)
        print(f"\n  [k={k_val}] (N=500, 50 trials/α)")
        for r in data:
            marker = " <-" if r["frac_all_hit"] < 0.95 else ""
            print(f"    α={r['alpha']:.2f}: {r['frac_all_hit']:5.1%} all-hit "
                  f"({r['all_hit']:3d}/{r['total']:3d}), "
                  f"avg_seq={r['avg_seq_len']:.1f}, avg_fs={r['avg_fs_size']:.0f}{marker}")
        print(f"  Summary: α_95={summary['alpha_95']}, α_50={summary['alpha_50']}, "
              f"min={summary['min_frac']:.1%} at α={summary['min_alpha']}")

    print("\n--- Experiment 7: Fine α Grid (0.02 spacing), k=2, 3 schemes ---")
    fine = fine_grid_phase_transition(
        N=1000, alpha_min=1.5, alpha_max=2.5, alpha_steps=51, trials=50,
    )
    for scheme, data in fine.items():
        summary = phase_transition_summary(data)
        print(f"\n  [{scheme}] (N=1000, k=2, 50 trials/α, 51 α-steps)")
        # Print every 5th point for readability
        for i, r in enumerate(data):
            if i % 5 == 0 or r["alpha"] == summary.get("alpha_95"):
                marker = " <-95" if r["alpha"] == summary.get("alpha_95") else ""
                print(f"    α={r['alpha']:.3f}: {r['frac_all_hit']:5.1%} all-hit "
                      f"({r['all_hit']:3d}/{r['total']:3d}){marker}")
        print(f"  Summary: α_95={summary['alpha_95']}, α_50={summary['alpha_50']}, "
              f"min={summary['min_frac']:.1%} at α={summary['min_alpha']}")


if __name__ == "__main__":
    main()
