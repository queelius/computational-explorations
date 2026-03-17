#!/usr/bin/env python3
"""
Extremal Colorings at Schur Numbers (Problem #483)

Profile the structure of colorings at the exact boundary S(k):
- Enumerate all valid k-colorings of [1..S(k)]
- Analyze their Fourier spectra and density distributions
- Study what happens at S(k)+1 (forced Schur triples)
- Track the maximum sum-free density as N grows

Known Schur numbers: S(1)=1, S(2)=4, S(3)=13, S(4)=44, S(5)=160.
"""

import numpy as np
from itertools import product as iproduct
from typing import List, Set, Tuple, Dict, Optional
import random


# ── Core Schur primitives ────────────────────────────────────────

def has_schur_triple(S: Set[int]) -> bool:
    """Check if S contains a Schur triple a+b=c with a,b,c in S (integers)."""
    for a in S:
        for b in S:
            if a + b in S:
                return True
    return False


def count_schur_triples(S: Set[int]) -> int:
    """Count ordered Schur triples (a,b,c) with a+b=c, a,b,c in S."""
    count = 0
    for a in S:
        for b in S:
            if a + b in S:
                count += 1
    return count


def is_valid_schur_coloring(coloring: List[int], N: int) -> bool:
    """Check if a coloring of [1..N] avoids monochromatic Schur triples.

    coloring: 0-indexed list where coloring[i] = color of element (i+1).
    """
    k = max(coloring) + 1
    color_classes = [set() for _ in range(k)]
    for i, c in enumerate(coloring):
        color_classes[c].add(i + 1)
    return all(not has_schur_triple(C) for C in color_classes)


# ── Experiment (a): Enumerate extremal colorings at S(2)=4 ──────

def enumerate_extremal_colorings_k2(N: int = 4) -> List[List[int]]:
    """Enumerate ALL valid 2-colorings of [1..N] avoiding Schur triples.

    Returns list of colorings, each a 0-indexed list of length N.
    """
    valid = []
    for bits in range(2 ** N):
        coloring = []
        for i in range(N):
            coloring.append((bits >> i) & 1)
        if is_valid_schur_coloring(coloring, N):
            valid.append(coloring)
    return valid


def analyze_color_classes(coloring: List[int], N: int) -> Dict:
    """Analyze the color classes of a coloring of [1..N]."""
    k = max(coloring) + 1
    classes = [set() for _ in range(k)]
    for i, c in enumerate(coloring):
        classes[c].add(i + 1)

    result = {
        "k": k,
        "N": N,
        "classes": [sorted(C) for C in classes],
        "sizes": [len(C) for C in classes],
        "densities": [len(C) / N for C in classes],
    }
    return result


# ── Fourier spectrum for integer subsets ─────────────────────────

def fourier_spectrum_integer(S: Set[int], N: int) -> List[Tuple[int, float]]:
    """Compute the Fourier spectrum of indicator of S in Z/MZ where M = 2*N+1.

    Uses M = 2*N+1 to embed [1..N] into a cyclic group large enough
    that integer sums a+b=c (with a,b,c <= N) correspond to modular sums.

    Returns list of (frequency, magnitude) sorted by magnitude descending.
    """
    M = 2 * N + 1
    f = np.zeros(M, dtype=complex)
    for x in S:
        f[x % M] = 1.0

    f_hat = np.fft.fft(f)
    spectrum = [(r, float(np.abs(f_hat[r]))) for r in range(M)]
    spectrum.sort(key=lambda x: -x[1])
    return spectrum


def top_fourier_features(S: Set[int], N: int, top_k: int = 5) -> Dict:
    """Extract key features from the Fourier spectrum of S."""
    spec = fourier_spectrum_integer(S, N)
    # DC component (r=0) = |S|
    dc_mag = next(mag for r, mag in spec if r == 0)
    non_dc = [(r, mag) for r, mag in spec if r != 0]

    if not non_dc or len(S) == 0:
        return {
            "dc": dc_mag,
            "top_non_dc": [],
            "max_non_dc_ratio": 0.0,
            "l2_energy": 0.0,
        }

    top = non_dc[:top_k]
    max_ratio = top[0][1] / len(S) if len(S) > 0 else 0.0
    # L2 energy of non-DC coefficients (Parseval: sum |f_hat(r)|^2)
    l2 = sum(mag ** 2 for _, mag in non_dc)

    return {
        "dc": dc_mag,
        "top_non_dc": top,
        "max_non_dc_ratio": max_ratio,
        "l2_energy": l2,
    }


# ── Experiment (b): Find extremal 3-colorings at S(3)=13 ────────

def random_schur_coloring(N: int, k: int, max_attempts: int = 100000,
                          rng: Optional[random.Random] = None) -> Optional[List[int]]:
    """Find a valid k-coloring of [1..N] by random search.

    Uses greedy-random: for each element, try a random permutation of colors.
    Falls back to pure random if greedy fails.
    """
    if rng is None:
        rng = random.Random(42)

    for _ in range(max_attempts):
        color_classes = [set() for _ in range(k)]
        coloring = []
        success = True

        for x in range(1, N + 1):
            order = list(range(k))
            rng.shuffle(order)
            placed = False
            for c in order:
                # Check if adding x to color c creates a Schur triple
                creates_triple = False
                for a in color_classes[c]:
                    if a + x in color_classes[c]:
                        creates_triple = True
                        break
                    if x - a in color_classes[c] and x - a > 0:
                        creates_triple = True
                        break
                if not creates_triple:
                    coloring.append(c)
                    color_classes[c].add(x)
                    placed = True
                    break

            if not placed:
                success = False
                break

        if success and len(coloring) == N:
            return coloring

    return None


def find_extremal_colorings_k3(N: int = 13, num_search: int = 50000,
                               seed: int = 42) -> List[List[int]]:
    """Find valid 3-colorings of [1..N] by repeated random greedy search.

    Returns deduplicated list of valid colorings found.
    """
    rng = random.Random(seed)
    found = set()

    for _ in range(num_search):
        coloring = random_schur_coloring(N, 3, max_attempts=1, rng=rng)
        if coloring is not None:
            found.add(tuple(coloring))

    return [list(c) for c in sorted(found)]


def analyze_extremal_k3(colorings: List[List[int]], N: int = 13) -> Dict:
    """Analyze the structural patterns in extremal 3-colorings at S(3)=13."""
    if not colorings:
        return {"count": 0}

    all_sizes = []
    all_max_fourier = []
    all_density_spreads = []

    for col in colorings:
        info = analyze_color_classes(col, N)
        all_sizes.append(tuple(sorted(info["sizes"])))

        # Fourier analysis per color class
        k = info["k"]
        color_sets = [set() for _ in range(k)]
        for i, c in enumerate(col):
            color_sets[c].add(i + 1)

        max_ratios = []
        for C in color_sets:
            if len(C) > 0:
                feat = top_fourier_features(C, N)
                max_ratios.append(feat["max_non_dc_ratio"])
        all_max_fourier.append(max(max_ratios) if max_ratios else 0.0)

        densities = sorted(info["densities"])
        spread = densities[-1] - densities[0]
        all_density_spreads.append(spread)

    # Frequency of size distributions
    from collections import Counter
    size_dist = Counter(all_sizes)

    return {
        "count": len(colorings),
        "size_distributions": dict(size_dist.most_common()),
        "mean_max_fourier_ratio": float(np.mean(all_max_fourier)),
        "mean_density_spread": float(np.mean(all_density_spreads)),
        "min_density_spread": float(min(all_density_spreads)),
        "max_density_spread": float(max(all_density_spreads)),
    }


# ── Experiment (c): Structure at S(k)+1 ─────────────────────────

def min_schur_triples_at_boundary(N: int, k: int) -> Tuple[int, List[int]]:
    """At N = S(k)+1, find the coloring that minimizes the total Schur triples.

    For small N, exhaustively searches all k^N colorings.
    Returns (min_triples, best_coloring).
    """
    if k ** N > 500000:
        return _min_triples_heuristic(N, k)

    best_count = float("inf")
    best_coloring = None

    for coloring_tuple in iproduct(range(k), repeat=N):
        coloring = list(coloring_tuple)
        color_classes = [set() for _ in range(k)]
        for i, c in enumerate(coloring):
            color_classes[c].add(i + 1)

        total = sum(count_schur_triples(C) for C in color_classes)
        if total < best_count:
            best_count = total
            best_coloring = coloring

    return best_count, best_coloring


def _min_triples_heuristic(N: int, k: int, num_trials: int = 10000) -> Tuple[int, List[int]]:
    """Heuristic search for coloring minimizing Schur triples at S(k)+1."""
    rng = random.Random(42)
    best_count = float("inf")
    best_coloring = None

    for _ in range(num_trials):
        coloring = [rng.randint(0, k - 1) for _ in range(N)]
        color_classes = [set() for _ in range(k)]
        for i, c in enumerate(coloring):
            color_classes[c].add(i + 1)

        total = sum(count_schur_triples(C) for C in color_classes)
        if total < best_count:
            best_count = total
            best_coloring = coloring

    return best_count, best_coloring


def forced_color_analysis(N: int, k: int) -> Dict:
    """Analyze which colors get forced at S(k)+1.

    For k=2, N=5: every 2-coloring has a monochromatic Schur triple.
    Identify which color class is forced to contain the triple.
    """
    if k ** N > 500000:
        return _forced_color_heuristic(N, k)

    triple_in_color = [0] * k
    total_colorings = 0

    for coloring_tuple in iproduct(range(k), repeat=N):
        coloring = list(coloring_tuple)
        total_colorings += 1

        color_classes = [set() for _ in range(k)]
        for i, c in enumerate(coloring):
            color_classes[c].add(i + 1)

        for c in range(k):
            if has_schur_triple(color_classes[c]):
                triple_in_color[c] += 1

    return {
        "N": N,
        "k": k,
        "total_colorings": total_colorings,
        "triples_in_color": triple_in_color,
        "fraction_with_triple": [t / total_colorings for t in triple_in_color],
    }


def _forced_color_heuristic(N: int, k: int, num_trials: int = 10000) -> Dict:
    """Heuristic version of forced_color_analysis for large search spaces."""
    rng = random.Random(42)
    triple_in_color = [0] * k
    total_colorings = num_trials

    for _ in range(num_trials):
        coloring = [rng.randint(0, k - 1) for _ in range(N)]
        color_classes = [set() for _ in range(k)]
        for i, c in enumerate(coloring):
            color_classes[c].add(i + 1)

        for c in range(k):
            if has_schur_triple(color_classes[c]):
                triple_in_color[c] += 1

    return {
        "N": N,
        "k": k,
        "total_colorings": total_colorings,
        "triples_in_color": triple_in_color,
        "fraction_with_triple": [t / total_colorings for t in triple_in_color],
    }


# ── Experiment (d): Density barrier analysis ─────────────────────

def max_sum_free_density_integer(N: int) -> Tuple[Set[int], float]:
    """Find the maximum-density sum-free subset of [1..N] (integer arithmetic).

    Uses the known optimal construction: odd numbers in [ceil(N/3)+1, N].
    For general N, the maximum sum-free subset of [1..N] has size
    ceil(N/2) (achieved by the odd numbers, or by the "upper third"
    {ceil(N/3)+1, ..., ceil(2N/3)}).

    Returns (best_set, density).
    """
    # Construction 1: odd numbers
    odds = {x for x in range(1, N + 1) if x % 2 == 1}

    # Construction 2: upper-interval {floor(N/2)+1, ..., N}
    upper = set(range(N // 2 + 1, N + 1))

    # Construction 3: third interval {floor(N/3)+1, ..., floor(2N/3)}
    third = set(range(N // 3 + 1, 2 * N // 3 + 1))

    best_set = set()
    best_size = 0

    for candidate in [odds, upper, third]:
        if not has_schur_triple(candidate) and len(candidate) > best_size:
            best_set = candidate
            best_size = len(candidate)

    return best_set, best_size / N if N > 0 else 0.0


def density_vs_N(max_N: int = 100) -> List[Tuple[int, float]]:
    """Compute maximum sum-free density in [1..N] for N = 1..max_N.

    Returns list of (N, max_density).
    """
    results = []
    for N in range(1, max_N + 1):
        _, density = max_sum_free_density_integer(N)
        results.append((N, density))
    return results


def density_barrier_by_k(k: int, max_N: int = 50) -> List[Tuple[int, float, bool]]:
    """For k colors, what is the minimum density a color MUST have in [1..N]?

    By pigeonhole, at least one color class has density >= 1/k.
    We track: for each N, the maximum density achievable while
    remaining sum-free, and whether this exceeds 1/k.

    Returns list of (N, max_sum_free_density, exceeds_1_over_k).
    """
    results = []
    for N in range(1, max_N + 1):
        _, max_density = max_sum_free_density_integer(N)
        exceeds = max_density >= 1.0 / k
        results.append((N, max_density, exceeds))
    return results


# ── Symmetry analysis ────────────────────────────────────────────

def coloring_equivalence_classes(colorings: List[List[int]]) -> Dict[str, List[List[int]]]:
    """Group colorings by equivalence under color permutation.

    Two colorings are equivalent if one can be obtained from the other
    by permuting color labels.
    """
    from itertools import permutations

    seen = set()
    classes = {}

    for col in colorings:
        col_tuple = tuple(col)
        if col_tuple in seen:
            continue

        k = max(col) + 1
        canonical = col_tuple
        for perm in permutations(range(k)):
            permuted = tuple(perm[c] for c in col)
            seen.add(permuted)
            if permuted < canonical:
                canonical = permuted

        key = str(list(canonical))
        if key not in classes:
            classes[key] = []
        classes[key].append(col)

    return classes


# ── Main experiment runner ───────────────────────────────────────

def run_all_experiments() -> Dict:
    """Run all extremal coloring experiments and return results."""
    results = {}

    # (a) S(2)=4: enumerate all valid 2-colorings
    print("=" * 70)
    print("EXPERIMENT (a): Extremal 2-colorings at S(2)=4")
    print("=" * 70)

    colorings_k2 = enumerate_extremal_colorings_k2(4)
    equiv_k2 = coloring_equivalence_classes(colorings_k2)
    results["k2_total"] = len(colorings_k2)
    results["k2_equiv_classes"] = len(equiv_k2)

    print(f"  Total valid 2-colorings of [1..4]: {len(colorings_k2)}")
    print(f"  Equivalence classes (up to color swap): {len(equiv_k2)}")
    print()

    for col in colorings_k2:
        info = analyze_color_classes(col, 4)
        c0 = {i + 1 for i, c in enumerate(col) if c == 0}
        c1 = {i + 1 for i, c in enumerate(col) if c == 1}
        feat0 = top_fourier_features(c0, 4)
        feat1 = top_fourier_features(c1, 4)
        print(f"  Color 0: {sorted(c0)}, Color 1: {sorted(c1)}")
        print(f"    Densities: {info['densities']}")
        print(f"    Max Fourier ratio (c0): {feat0['max_non_dc_ratio']:.3f}")
        print(f"    Max Fourier ratio (c1): {feat1['max_non_dc_ratio']:.3f}")
    print()

    # Verify N=5 has no valid 2-coloring
    colorings_k2_5 = enumerate_extremal_colorings_k2(5)
    results["k2_at_5"] = len(colorings_k2_5)
    print(f"  Valid 2-colorings of [1..5]: {len(colorings_k2_5)} (should be 0)")
    print()

    # (b) S(3)=13: find 3-colorings
    print("=" * 70)
    print("EXPERIMENT (b): Extremal 3-colorings at S(3)=13")
    print("=" * 70)

    colorings_k3 = find_extremal_colorings_k3(13, num_search=50000)
    analysis_k3 = analyze_extremal_k3(colorings_k3, 13)
    results["k3_found"] = analysis_k3["count"]

    print(f"  Valid 3-colorings found: {analysis_k3['count']}")
    if analysis_k3["count"] > 0:
        print(f"  Size distributions: {analysis_k3['size_distributions']}")
        print(f"  Mean max Fourier ratio: {analysis_k3['mean_max_fourier_ratio']:.3f}")
        print(f"  Density spread: [{analysis_k3['min_density_spread']:.3f}, "
              f"{analysis_k3['max_density_spread']:.3f}]")

        # Show a few examples
        for i, col in enumerate(colorings_k3[:3]):
            info = analyze_color_classes(col, 13)
            print(f"\n  Example {i + 1}: sizes={info['sizes']}, densities={[f'{d:.3f}' for d in info['densities']]}")
            for c_idx, cls in enumerate(info["classes"]):
                print(f"    Color {c_idx}: {cls}")
    print()

    # (c) Structure at S(k)+1
    print("=" * 70)
    print("EXPERIMENT (c): Forced Schur triples at S(k)+1")
    print("=" * 70)

    # k=2, N=5
    print("\n  k=2, N=5 (S(2)+1):")
    min_trips_k2, best_col_k2 = min_schur_triples_at_boundary(5, 2)
    forced_k2 = forced_color_analysis(5, 2)
    results["k2_min_triples_at_5"] = min_trips_k2

    print(f"    Minimum Schur triples: {min_trips_k2}")
    print(f"    Best coloring: {best_col_k2}")
    print(f"    Fraction of colorings with triple in color c: "
          f"{forced_k2['fraction_with_triple']}")

    # k=3, N=14
    print("\n  k=3, N=14 (S(3)+1):")
    min_trips_k3, best_col_k3 = min_schur_triples_at_boundary(14, 3)
    results["k3_min_triples_at_14"] = min_trips_k3

    print(f"    Minimum Schur triples (heuristic): {min_trips_k3}")
    if best_col_k3:
        info = analyze_color_classes(best_col_k3, 14)
        print(f"    Best coloring sizes: {info['sizes']}")
    print()

    # (d) Density barrier analysis
    print("=" * 70)
    print("EXPERIMENT (d): Maximum sum-free density in [1..N]")
    print("=" * 70)

    density_data = density_vs_N(60)
    results["density_data"] = density_data

    print("\n  N    max density    construction")
    for N, d in density_data:
        if N <= 20 or N % 10 == 0:
            best_set, _ = max_sum_free_density_integer(N)
            desc = "odds" if all(x % 2 == 1 for x in best_set) else "interval"
            print(f"  {N:3d}  {d:.4f}         {desc}")

    # k=2 barrier
    print("\n  k=2 density barrier (need density < 1/2 to force triple):")
    barrier_k2 = density_barrier_by_k(2, 30)
    for N, d, exceeds in barrier_k2:
        if N <= 10 or N == 20 or N == 30:
            status = "CAN avoid" if exceeds else "FORCED"
            print(f"    N={N:3d}: max_sf_density={d:.4f}, {status}")
    results["barrier_k2"] = barrier_k2

    # k=3 barrier
    print("\n  k=3 density barrier (need density < 1/3 to force triple):")
    barrier_k3 = density_barrier_by_k(3, 30)
    for N, d, exceeds in barrier_k3:
        if N <= 10 or N == 20 or N == 30:
            status = "CAN avoid" if exceeds else "FORCED"
            print(f"    N={N:3d}: max_sf_density={d:.4f}, {status}")
    results["barrier_k3"] = barrier_k3

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY OF FINDINGS")
    print("=" * 70)
    print(f"""
  Extremal colorings at S(2)=4:
    {results['k2_total']} total valid 2-colorings
    {results['k2_equiv_classes']} equivalence classes (up to color swap)
    All have equal partition sizes (2,2)
    No valid coloring at N=5: {results['k2_at_5']} found

  Extremal colorings at S(3)=13:
    {results['k3_found']} colorings found (by random search, not exhaustive)

  Forced Schur triples at boundary:
    S(2)+1=5: minimum {results['k2_min_triples_at_5']} Schur triples
    S(3)+1=14: minimum {results['k3_min_triples_at_14']} Schur triples (heuristic)

  Density barrier:
    Max sum-free density in [1..N] approaches 1/2 (achieved by odd numbers)
    For k=2: density ~1/2 means single color class CAN be large
    For k=3: density ~1/2 >> 1/3 means density alone doesn't force triples
    => Schur number bounds require COMBINATORIAL structure, not just density
""")

    return results


if __name__ == "__main__":
    run_all_experiments()
