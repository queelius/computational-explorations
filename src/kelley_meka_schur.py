#!/usr/bin/env python3
"""
Kelley-Meka Style Fourier Analysis for Schur Numbers

This implements the key computational components of the K-M technique
adapted for Schur triples (a + b = c) instead of 3-APs (a, a+d, a+2d).

Key differences from K-M:
1. Sum-free sets can have density 1/2 (vs AP-free → 0)
2. Need to exploit k-coloring structure, not single set
3. Schur constraint x + y = z is asymmetric

Goal: Show that S(k) < c^k for some constant c.
"""

import numpy as np
from typing import List, Set, Tuple, Optional
import math


def schur_count_direct(A: Set[int], N: int) -> int:
    """Count Schur triples (a + b = c with a, b, c in A) directly."""
    A_set = set(a % N for a in A)
    count = 0
    for a in A_set:
        for b in A_set:
            if (a + b) % N in A_set:
                count += 1
    return count


def schur_count_fourier(A: Set[int], N: int) -> float:
    """
    Count Schur triples using Fourier transform.

    T(A) = |{(a,b,c) ∈ A³ : a + b ≡ c (mod N)}|

    Fourier formula (derived from convolution theorem):
    T(A) = (1/N) Σ_r |f̂(r)|² · f̂(r)

    where f̂(r) = Σ_{x∈A} e^{-2πirx/N} (standard DFT convention).

    Derivation: The constraint a+b=c mod N gives δ(a+b-c) = (1/N) Σ_r e^{2πir(a+b-c)/N},
    so T = (1/N) Σ_r [Σ_a f(a)e^{2πira/N}]² [Σ_c f(c)e^{-2πirc/N}]
         = (1/N) Σ_r conj(f̂(r))² · f̂(r)
         = (1/N) Σ_r |f̂(r)|² · f̂(r)     [sum identity: substitute r→-r, use f̂(-r)=conj(f̂(r)) for real f]
    """
    # Build indicator function
    f = np.zeros(N, dtype=complex)
    for a in A:
        f[a % N] = 1

    # Fourier transform
    f_hat = np.fft.fft(f)

    # Compute T(A) = (1/N) Σ_r |f̂(r)|² · f̂(r)
    T = np.sum(np.abs(f_hat)**2 * f_hat) / N

    return np.real(T)


def is_sum_free(A: Set[int], N: int) -> bool:
    """Check if A is sum-free modulo N."""
    A_set = set(a % N for a in A)
    for a in A_set:
        for b in A_set:
            if (a + b) % N in A_set:
                return False
    return True


def max_sum_free_density(N: int) -> Tuple[Set[int], float]:
    """
    Find maximum density sum-free set in ℤ/Nℤ.

    Known: odd numbers achieve density 1/2.
    """
    # Odd numbers mod N
    odds = {i for i in range(1, N, 2)}

    # Verify sum-free
    assert is_sum_free(odds, N), "Odds should be sum-free"

    return odds, len(odds) / N


def fourier_spectrum(A: Set[int], N: int) -> List[Tuple[int, float]]:
    """
    Compute the Fourier spectrum |f̂(r)| for all r.

    Returns list of (r, |f̂(r)|) sorted by magnitude.
    """
    f = np.zeros(N, dtype=complex)
    for a in A:
        f[a % N] = 1

    f_hat = np.fft.fft(f)
    magnitudes = [(r, np.abs(f_hat[r])) for r in range(N)]

    # Sort by magnitude, descending
    magnitudes.sort(key=lambda x: -x[1])

    return magnitudes


def bohr_set(S: List[int], epsilon: float, N: int) -> Set[int]:
    """
    Compute Bohr set B(S, ε) = {x ∈ ℤ/Nℤ : |e(rx/N) - 1| < ε for all r ∈ S}.

    Bohr sets are subgroups-like structures used in density increment.
    """
    B = set()
    for x in range(N):
        in_bohr = True
        for r in S:
            phase = np.exp(2j * np.pi * r * x / N)
            if np.abs(phase - 1) >= epsilon:
                in_bohr = False
                break
        if in_bohr:
            B.add(x)
    return B


def density_on_bohr(A: Set[int], B: Set[int], N: int) -> float:
    """Compute density of A restricted to Bohr set B."""
    A_mod = set(a % N for a in A)
    intersection = A_mod & B
    return len(intersection) / len(B) if B else 0


def density_increment_step(A: Set[int], N: int, threshold: float = 0.1) -> Optional[Tuple[Set[int], float]]:
    """
    Perform one step of density increment.

    If A has a large Fourier coefficient at r ≠ 0, restrict to Bohr set B({r}, ε).
    The restricted set A ∩ B has higher density than A.

    Returns (Bohr set, new density) or None if no large coefficient.
    """
    A_mod = set(a % N for a in A)
    original_density = len(A_mod) / N

    # Find largest non-DC Fourier coefficient
    spectrum = fourier_spectrum(A_mod, N)

    # Skip DC component (r=0)
    for r, mag in spectrum:
        if r == 0:
            continue

        # Check if coefficient is "large" (> threshold * |A|)
        if mag > threshold * len(A_mod):
            # Restrict to Bohr set
            epsilon = 0.5  # Tunable parameter
            B = bohr_set([r], epsilon, N)

            if len(B) > 0:
                new_density = density_on_bohr(A_mod, B, N)
                if new_density > original_density:
                    return B, new_density

    return None


def sum_free_structure_lemma(A: Set[int], N: int) -> dict:
    """
    Analyze structure of sum-free set A.

    Key lemma (to prove rigorously):
    If A is sum-free with |A| > N/3, then A has special structure:
    - Large Fourier coefficient, OR
    - Contained in arithmetic progression, OR
    - Close to interval

    This is the analogue of Kelley-Meka's structure theorem for AP-free sets.
    """
    A_mod = set(a % N for a in A)
    density = len(A_mod) / N

    result = {
        "size": len(A_mod),
        "density": density,
        "sum_free": is_sum_free(A_mod, N),
        "schur_count": schur_count_direct(A_mod, N)
    }

    # Fourier analysis
    spectrum = fourier_spectrum(A_mod, N)
    # Find largest non-DC coefficient
    non_dc = [(r, m) for r, m in spectrum if r != 0]
    if non_dc:
        r_max, mag_max = non_dc[0]
        result["max_fourier_freq"] = r_max
        result["max_fourier_mag"] = mag_max
        result["fourier_ratio"] = mag_max / len(A_mod)

    # Check if contained in interval
    A_sorted = sorted(A_mod)
    if A_sorted:
        span = (A_sorted[-1] - A_sorted[0]) % N
        result["span"] = span
        result["is_interval_like"] = span < N / 2

    return result


def analyze_k_coloring(coloring: List[int], N: int) -> dict:
    """
    Analyze a k-coloring of {1,...,N} for Schur structure.

    coloring[i] = color of element (i+1), so coloring is 0-indexed list
    representing elements 1..N.
    """
    k = max(coloring) + 1

    colors = [set() for _ in range(k)]
    for i, c in enumerate(coloring):
        colors[c].add(i + 1)  # Elements are 1-indexed

    result = {
        "N": N,
        "k": k,
        "colors": []
    }

    for i, C in enumerate(colors):
        color_info = sum_free_structure_lemma(C, N)
        color_info["color_id"] = i
        result["colors"].append(color_info)

    # Check if any color has Schur triple
    result["has_schur"] = any(c["schur_count"] > 0 for c in result["colors"])

    return result


def greedy_sum_free_coloring(N: int, k: int) -> List[int]:
    """
    Greedily construct a k-coloring of {1,...,N} trying to avoid Schur triples.

    Uses the standard convention [1..N] (not 0-indexed) to match Schur number
    definitions where S(k) is the largest N such that [N] can be k-colored sum-free.

    This helps find upper bounds on S(k).
    """
    coloring = [-1] * (N + 1)  # 1-indexed: coloring[1..N]
    colors = [set() for _ in range(k)]

    for x in range(1, N + 1):
        # Try to find a color that doesn't create Schur triple
        placed = False
        for c in range(k):
            # Check if adding x to color c creates Schur triple
            creates_schur = False
            for a in colors[c]:
                # a + x = b (where b already in colors[c])
                if a + x in colors[c]:
                    creates_schur = True
                    break
                # a + b = x (where a, b already in colors[c])
                if x - a in colors[c] and x - a > 0:
                    creates_schur = True
                    break

            if not creates_schur:
                coloring[x] = c
                colors[c].add(x)
                placed = True
                break

        if not placed:
            # Force into first color (will create Schur)
            coloring[x] = 0
            colors[0].add(x)

    return coloring[1:]  # Return 0-indexed list for compatibility


def _has_integer_schur_triple(color_sets: list) -> bool:
    """Check if any color class has a Schur triple a+b=c in integers."""
    for C in color_sets:
        for a in C:
            for b in C:
                if a + b in C:
                    return True
    return False


def schur_number_search(k: int, max_n: int = 200) -> Tuple[int, List[int]]:
    """
    Search for Schur number S(k) by trying to color {1,...,n} for increasing n.

    Uses integer arithmetic (a+b=c, not mod N) to match the standard Schur
    number definition. Returns (S(k) estimate, best coloring).
    """
    best_n = 0
    best_coloring = []

    for n in range(1, max_n + 1):
        coloring = greedy_sum_free_coloring(n, k)
        # Build 1-indexed color classes
        colors = [set() for _ in range(k)]
        for i, c in enumerate(coloring):
            colors[c].add(i + 1)

        if not _has_integer_schur_triple(colors):
            best_n = n
            best_coloring = coloring
        else:
            break

    return best_n, best_coloring


def main():
    print("=" * 70)
    print("KELLEY-MEKA STYLE ANALYSIS FOR SCHUR NUMBERS")
    print("=" * 70)
    print()

    # Test 1: Verify Fourier formula
    print("-" * 70)
    print("TEST 1: Fourier Formula Verification")
    print("-" * 70)
    N = 50
    A = {1, 5, 9, 13, 17, 21, 25}  # Arithmetic progression mod 4

    direct = schur_count_direct(A, N)
    fourier = schur_count_fourier(A, N)
    print(f"  Set A = {A}")
    print(f"  Direct count: {direct}")
    print(f"  Fourier count: {fourier:.2f}")
    print(f"  Match: {abs(direct - fourier) < 0.01}")
    print()

    # Test 2: Sum-free set analysis
    print("-" * 70)
    print("TEST 2: Sum-Free Set Structure")
    print("-" * 70)
    N = 100

    # Odd numbers (max sum-free)
    odds = {i for i in range(1, N, 2)}
    odds_analysis = sum_free_structure_lemma(odds, N)
    print(f"  Odd numbers in [0, {N}):")
    print(f"    Size: {odds_analysis['size']}, Density: {odds_analysis['density']:.3f}")
    print(f"    Sum-free: {odds_analysis['sum_free']}")
    print(f"    Max Fourier freq: {odds_analysis.get('max_fourier_freq', 'N/A')}")
    print(f"    Fourier ratio: {odds_analysis.get('fourier_ratio', 0):.3f}")
    print()

    # Test 3: Density increment
    print("-" * 70)
    print("TEST 3: Density Increment Step")
    print("-" * 70)
    N = 100
    # Random-ish set
    A = {i for i in range(N) if (i * 7 + 3) % 11 < 5}
    print(f"  Original set size: {len(A)}, density: {len(A)/N:.3f}")

    result = density_increment_step(A, N)
    if result:
        B, new_density = result
        print(f"  Bohr set size: {len(B)}")
        print(f"  New density: {new_density:.3f}")
        print(f"  Density increase: {new_density - len(A)/N:.3f}")
    else:
        print("  No density increment found (set is Fourier-uniform)")
    print()

    # Test 4: Schur number search
    print("-" * 70)
    print("TEST 4: Schur Number Search")
    print("-" * 70)
    known_schur = {1: 1, 2: 4, 3: 13, 4: 44, 5: 160}

    for k in range(1, 5):
        S_k, coloring = schur_number_search(k, max_n=known_schur.get(k, 50) + 10)
        print(f"  S({k}): greedy finds {S_k}, known value is {known_schur.get(k, '?')}")
    print()

    # Test 5: k-coloring analysis
    print("-" * 70)
    print("TEST 5: K-Coloring Structure Analysis")
    print("-" * 70)
    k = 2
    N = 5  # S(2) + 1 = 5, so [5] forces Schur in some color

    coloring = greedy_sum_free_coloring(N, k)
    analysis = analyze_k_coloring(coloring, N)

    print(f"  {k}-coloring of [{N}]:")
    print(f"  Has Schur triple: {analysis['has_schur']}")
    for c in analysis["colors"]:
        print(f"    Color {c['color_id']}: size={c['size']}, sum_free={c['sum_free']}, schur_count={c['schur_count']}")
    print()

    print("=" * 70)
    print("KEY INSIGHTS FOR K-M → SCHUR EXTENSION")
    print("=" * 70)
    print("""
1. FOURIER FORMULA WORKS: T(A) = (1/N) Σ_r f̂(r)² f̂(-r)* correctly counts
   Schur triples, analogous to AP counting formula.

2. DENSITY INCREMENT EXISTS: Sets with non-uniform Fourier spectrum can
   be restricted to Bohr sets with higher density.

3. SUM-FREE BARRIER: Unlike AP-free sets (density → 0), sum-free sets
   can have density 1/2. This is the main obstacle.

4. MULTICOLOR STRUCTURE: Must exploit that k colors partition [N].
   If all colors have small density, total is < N. Contradiction for k ≥ 2.

5. PROPOSED ATTACK:
   - Show medium-density sum-free sets (1/k < δ < 1/2) have structure
   - Use structure to force restriction
   - After O(k) iterations, reach contradiction

EXPECTED RESULT: S(k) < c^k for some constant c (resolving #483).
""")


if __name__ == "__main__":
    main()
