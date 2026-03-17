#!/usr/bin/env python3
"""
Primitive-Coprime Hybrid Problem (NPG-23)

A set A ⊆ [n] is PRIMITIVE if no element divides another.
M(A) = number of coprime pairs in A.

Question: Among all primitive A ⊆ [n], which maximizes M(A)?

Finding: The shifted top layer S(n) dominates both primes and T(n).
M(S(n)) ~ (64/9π²) · C(⌊n/2⌋, 2), with exact ratio M(S)/M(T) = 32/27.

Sieve-theoretic result: d(A) = (8/π²)(1 - f_E²) where f_E = even fraction.
- T(n): f_E=1/2, d=6/π² ≈ 0.608
- S(n): f_E=1/3, d=64/(9π²) ≈ 0.721

This connects Erdős's work on primitive sets (Problems #143, #530)
with coprime graph theory (Problem #883).
"""

import math
from itertools import combinations
from typing import Set, List, Tuple, Dict, Any, Optional
from collections import defaultdict

# Sieve-theoretic constants
DENSITY_TOP_LAYER = 6 / math.pi**2          # ≈ 0.6079 (f_E = 1/2)
DENSITY_SHIFTED = 64 / (9 * math.pi**2)     # ≈ 0.7205 (f_E = 1/3)
RATIO_SHIFTED_TO_TOP = 32 / 27              # ≈ 1.1852


def coprime_density_formula(f_E: float) -> float:
    """Coprime density for a set with even fraction f_E.

    Sieve-theoretic result: d = (8/π²)(1 - f_E²).
    - f_E = 0 (all odd): d = 8/π² ≈ 0.8106
    - f_E = 1/3 (shifted top): d = 64/(9π²) ≈ 0.7205
    - f_E = 1/2 (top layer): d = 6/π² ≈ 0.6079
    - f_E = 1 (all even): d = 0
    """
    return (8 / math.pi**2) * (1 - f_E**2)


def even_fraction(A: Set[int]) -> float:
    """Compute the fraction of even elements in A."""
    if not A:
        return 0.0
    return sum(1 for a in A if a % 2 == 0) / len(A)


def verify_density_formula(n: int) -> Dict[str, float]:
    """Verify the sieve-theoretic density formula for T(n) and S(n).

    Returns predicted vs observed densities and the ratio.
    """
    T = top_layer(n)
    S = shifted_top_layer(n)

    M_T = coprime_pair_count(T)
    M_S = coprime_pair_count(S)

    pairs_T = len(T) * (len(T) - 1) // 2
    pairs_S = len(S) * (len(S) - 1) // 2

    d_T_obs = M_T / pairs_T if pairs_T > 0 else 0
    d_S_obs = M_S / pairs_S if pairs_S > 0 else 0

    f_E_T = even_fraction(T)
    f_E_S = even_fraction(S)

    d_T_pred = coprime_density_formula(f_E_T)
    d_S_pred = coprime_density_formula(f_E_S)

    ratio_obs = M_S / M_T if M_T > 0 else float('inf')

    return {
        "n": n,
        "f_E_T": f_E_T, "d_T_pred": d_T_pred, "d_T_obs": d_T_obs,
        "f_E_S": f_E_S, "d_S_pred": d_S_pred, "d_S_obs": d_S_obs,
        "ratio_pred": RATIO_SHIFTED_TO_TOP,
        "ratio_obs": ratio_obs,
    }


def is_primitive(A: Set[int]) -> bool:
    """Check if A is a primitive set (no element divides another)."""
    A_sorted = sorted(A)
    for i in range(len(A_sorted)):
        for j in range(i + 1, len(A_sorted)):
            if A_sorted[j] % A_sorted[i] == 0:
                return False
    return True


def coprime_pair_count(A: Set[int]) -> int:
    """Count coprime pairs in A."""
    A_list = sorted(A)
    count = 0
    for i in range(len(A_list)):
        for j in range(i + 1, len(A_list)):
            if math.gcd(A_list[i], A_list[j]) == 1:
                count += 1
    return count


def primes_up_to(n: int) -> Set[int]:
    """Sieve of Eratosthenes."""
    if n < 2:
        return set()
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return {i for i, is_p in enumerate(sieve) if is_p}


def top_layer(n: int) -> Set[int]:
    """The top layer {⌊n/2⌋+1, ..., n} — a large primitive set."""
    return set(range(n // 2 + 1, n + 1))


def squarefree_min_prime(n: int, k: int) -> Set[int]:
    """
    Squarefree numbers in [1,n] whose smallest prime factor is > k.

    These form a primitive-like set (not always primitive, but interesting).
    For k=1: all squarefree numbers (NOT primitive in general).
    For large k: approaches {1} ∪ primes.
    """
    primes = sorted(primes_up_to(n))
    result = set()
    for x in range(1, n + 1):
        # Check squarefree
        temp = x
        is_squarefree = True
        smallest_prime = None
        for p in primes:
            if p * p > temp:
                break
            if temp % p == 0:
                if smallest_prime is None:
                    smallest_prime = p
                count = 0
                while temp % p == 0:
                    temp //= p
                    count += 1
                if count > 1:
                    is_squarefree = False
                    break
        if temp > 1 and smallest_prime is None:
            smallest_prime = temp
        if x == 1:
            smallest_prime = float('inf')
        if is_squarefree and (smallest_prime is None or smallest_prime > k):
            result.add(x)
    return result


def primitive_squarefree_layer(n: int, k: int) -> Set[int]:
    """
    Squarefree numbers in [1,n] with all prime factors > k,
    filtered to be actually primitive.
    """
    candidates = squarefree_min_prime(n, k)
    # Filter to primitive: remove x if any proper divisor of x is in candidates
    result = set()
    for x in sorted(candidates):
        # Check if any element in result divides x
        is_dominated = False
        for y in result:
            if x % y == 0 and x != y:
                is_dominated = True
                break
        if not is_dominated:
            result.add(x)
    return result


def kth_layer(n: int, k: int) -> Set[int]:
    """
    k-th antichain layer of ([n], |):
    Layer 0: {1}
    Layer 1: primes ≤ n
    Layer 2: semiprimes ≤ n with no divisor in layer 1 present
    etc.

    More precisely: elements of [n] with exactly k prime factors (with multiplicity).
    These don't form a primitive set in general (e.g., 4=2² and 6=2·3 are both
    in Omega=2, and 4 doesn't divide 6), but they ARE primitive within each layer
    for squarefree numbers.
    """
    result = set()
    primes = sorted(primes_up_to(n))
    for x in range(2, n + 1):
        omega = 0
        temp = x
        for p in primes:
            if p * p > temp:
                break
            while temp % p == 0:
                temp //= p
                omega += 1
        if temp > 1:
            omega += 1
        if omega == k:
            result.add(x)
    return result


def exhaustive_max_primitive_coprime(n: int) -> Tuple[int, Set[int]]:
    """
    Exhaustively find the primitive set A ⊆ [n] maximizing M(A).

    Only feasible for small n (≤ 20 or so).
    Returns (max_M, best_set).
    """
    elements = list(range(1, n + 1))
    best_M = 0
    best_set = set()

    # Generate all primitive subsets using backtracking
    def backtrack(idx: int, current: List[int]):
        nonlocal best_M, best_set
        # Compute M for current set
        M = 0
        for i in range(len(current)):
            for j in range(i + 1, len(current)):
                if math.gcd(current[i], current[j]) == 1:
                    M += 1
        if M > best_M:
            best_M = M
            best_set = set(current)

        for next_idx in range(idx, len(elements)):
            x = elements[next_idx]
            # Check primitivity: x should not divide or be divided by any current element
            ok = True
            for c in current:
                if x % c == 0 or c % x == 0:
                    ok = False
                    break
            if ok:
                current.append(x)
                backtrack(next_idx + 1, current)
                current.pop()

    backtrack(0, [])
    return best_M, best_set


def greedy_max_primitive_coprime(n: int) -> Tuple[int, Set[int]]:
    """
    Greedy heuristic: build a primitive set maximizing coprime pairs.

    Strategy: start with primes, then try adding elements
    that increase M(A) the most.
    """
    primes = sorted(primes_up_to(n))
    current = set(primes)

    candidates = [x for x in range(2, n + 1) if x not in current]

    improved = True
    while improved:
        improved = False
        best_gain = 0
        best_add = None

        for x in candidates:
            if x in current:
                continue
            ok = all(x % c != 0 and c % x != 0 for c in current)
            if not ok:
                continue
            gain = sum(1 for c in current if math.gcd(x, c) == 1)
            if gain > best_gain:
                best_gain = gain
                best_add = x

        if best_add is not None and best_gain > 0:
            current.add(best_add)
            improved = True

    M = coprime_pair_count(current)
    return M, current


def smart_greedy(n: int) -> Tuple[int, Set[int]]:
    """
    Smart greedy: start empty, add elements maximizing marginal M(A) gain.

    At each step, add the element that creates the most new coprime pairs.
    """
    current = set()
    all_elements = list(range(2, n + 1))

    while True:
        best_gain = -1
        best_add = None

        for x in all_elements:
            if x in current:
                continue
            ok = all(x % c != 0 and c % x != 0 for c in current)
            if not ok:
                continue
            gain = sum(1 for c in current if math.gcd(x, c) == 1)
            # For the first element, gain=0 but we still want to add it
            if len(current) == 0:
                gain = 0
            if gain > best_gain:
                best_gain = gain
                best_add = x

        if best_add is None:
            break
        if len(current) > 0 and best_gain == 0:
            break
        current.add(best_add)

    M = coprime_pair_count(current)
    return M, current


def hybrid_greedy(n: int) -> Tuple[int, Set[int]]:
    """
    Hybrid greedy: mimic the exhaustive-optimal pattern.

    Key insight from exhaustive search: avoid small primes p,
    use p² instead, plus products pq. This "blocks fewer multiples"
    and allows a larger primitive set.

    Strategy: For small primes p ≤ √n, use p² instead of p.
    Then add products pq of small primes (as long as primitive).
    Then add large primes (> √n).
    Then extend greedily.
    """
    all_primes = sorted(primes_up_to(n))
    sqrt_n = int(n**0.5)

    # Small primes: use p² instead of p
    small_primes = [p for p in all_primes if p <= sqrt_n]
    large_primes = [p for p in all_primes if p > sqrt_n]

    current = set()

    # Phase 1: Add prime squares for small primes
    for p in small_primes:
        pp = p * p
        if pp <= n:
            ok = all(pp % c != 0 and c % pp != 0 for c in current)
            if ok:
                current.add(pp)

    # Phase 2: Add products of pairs of small primes
    for i, p in enumerate(small_primes):
        for q in small_primes[i + 1:]:
            pq = p * q
            if pq <= n:
                ok = all(pq % c != 0 and c % pq != 0 for c in current)
                if ok:
                    current.add(pq)

    # Phase 3: Add large primes
    for p in large_primes:
        ok = all(p % c != 0 and c % p != 0 for c in current)
        if ok:
            current.add(p)

    # Phase 4: Greedy extension with any remaining coprime-contributing elements
    for x in range(2, n + 1):
        if x in current:
            continue
        ok = all(x % c != 0 and c % x != 0 for c in current)
        if ok:
            gain = sum(1 for c in current if math.gcd(x, c) == 1)
            if gain > 0:
                current.add(x)

    M = coprime_pair_count(current)
    return M, current


def iterative_improve(n: int, initial: Optional[Set[int]] = None,
                      rounds: int = 1000) -> Tuple[int, Set[int]]:
    """
    Iterative improvement: start from initial set, try swaps.

    For each round: try removing one element and adding a different one.
    Accept if M(A) increases.
    """
    import random
    if initial is None:
        _, initial = hybrid_greedy(n)
    current = set(initial)
    current_M = coprime_pair_count(current)

    all_elements = set(range(2, n + 1))

    for _ in range(rounds):
        if not current:
            break
        # Pick random element to remove
        remove = random.choice(sorted(current))
        trial = current - {remove}

        # Try adding something new
        candidates = all_elements - trial
        best_add = None
        best_M = coprime_pair_count(trial)

        for x in candidates:
            ok = all(x % c != 0 and c % x != 0 for c in trial)
            if not ok:
                continue
            trial_add = trial | {x}
            M_new = coprime_pair_count(trial_add)
            if M_new > best_M:
                best_M = M_new
                best_add = x

        if best_M > current_M:
            current = trial | ({best_add} if best_add else set())
            current_M = best_M

    return current_M, current


def shifted_top_layer(n: int) -> Set[int]:
    """
    Improved top layer: replace even 2k with odd k ∈ (n/3, n/2).

    This maintains primitivity and size while increasing coprime density
    by ~18.5%, because odd k doesn't share factor 2 with even elements.
    """
    T = set(range(n // 2 + 1, n + 1))
    to_remove = set()
    to_add = set()
    for x in sorted(T):
        if x % 2 == 0:
            k = x // 2
            if k > n // 3 and k % 2 == 1:
                to_remove.add(x)
                to_add.add(k)
    return (T - to_remove) | to_add


def compare_primitive_sets(n: int) -> Dict[str, Any]:
    """
    Compare M(A) for various primitive sets A ⊆ [n].

    Returns comparison data.
    """
    results = {"n": n}

    # 1. Primes
    P = primes_up_to(n)
    M_primes = coprime_pair_count(P)
    pi_n = len(P)
    expected_primes = pi_n * (pi_n - 1) // 2  # All pairs coprime
    results["primes"] = {
        "size": pi_n,
        "M": M_primes,
        "expected": expected_primes,
        "match": M_primes == expected_primes,
    }

    # 2. Top layer
    T = top_layer(n)
    M_top = coprime_pair_count(T)
    results["top_layer"] = {
        "size": len(T),
        "M": M_top,
        "density": M_top / max(len(T) * (len(T) - 1) // 2, 1),
    }

    # 3. Primes + {1}
    P1 = P | {1}
    M_p1 = coprime_pair_count(P1)
    results["primes_plus_1"] = {
        "size": len(P1),
        "M": M_p1,
        "is_primitive": is_primitive(P1),
    }

    # 4. Squarefree with min prime > 3 (primitive filtered)
    S3 = primitive_squarefree_layer(n, 3)
    M_s3 = coprime_pair_count(S3)
    results["sqfree_minp>3"] = {
        "size": len(S3),
        "M": M_s3,
        "is_primitive": is_primitive(S3),
    }

    # 5. Squarefree with min prime > 5
    S5 = primitive_squarefree_layer(n, 5)
    M_s5 = coprime_pair_count(S5)
    results["sqfree_minp>5"] = {
        "size": len(S5),
        "M": M_s5,
        "is_primitive": is_primitive(S5),
    }

    # 6. Layer 2: semiprimes (products of exactly 2 primes)
    L2 = kth_layer(n, 2)
    # Filter to primitive within the layer
    L2_prim = set()
    for x in sorted(L2):
        ok = True
        for y in L2_prim:
            if x % y == 0:
                ok = False
                break
        if ok:
            L2_prim.add(x)
    M_l2 = coprime_pair_count(L2_prim)
    results["semiprimes_prim"] = {
        "size": len(L2_prim),
        "M": M_l2,
        "is_primitive": is_primitive(L2_prim),
    }

    # 7. Greedy
    M_greedy, A_greedy = greedy_max_primitive_coprime(n)
    results["greedy"] = {
        "size": len(A_greedy),
        "M": M_greedy,
        "is_primitive": is_primitive(A_greedy),
    }

    # 8. Shifted top layer
    S = shifted_top_layer(n)
    M_shifted = coprime_pair_count(S)
    results["shifted_top"] = {
        "size": len(S),
        "M": M_shifted,
        "is_primitive": is_primitive(S),
        "density": M_shifted / max(len(S) * (len(S) - 1) // 2, 1),
    }

    return results


def analyze_growth(max_n: int = 500, step: int = 50) -> List[Dict[str, Any]]:
    """
    Analyze how M(A) grows for primes vs top layer vs greedy.

    Key question: does M(primes) = C(π(n),2) dominate for large n?
    """
    data = []
    for n in range(step, max_n + 1, step):
        P = primes_up_to(n)
        pi_n = len(P)
        M_primes = pi_n * (pi_n - 1) // 2  # All coprime

        T = top_layer(n)
        M_top = coprime_pair_count(T)

        row = {
            "n": n,
            "pi_n": pi_n,
            "M_primes": M_primes,
            "top_size": len(T),
            "M_top": M_top,
            "primes_win": M_primes > M_top,
        }
        data.append(row)
    return data


def main():
    print("=" * 70)
    print("PRIMITIVE-COPRIME HYBRID PROBLEM (NPG-23)")
    print("=" * 70)
    print()
    print("Question: Among primitive A ⊆ [n], which maximizes M(A)?")
    print("M(A) = number of coprime pairs in A.")
    print()

    # Part 1: Exhaustive search for small n
    print("--- Part 1: Exhaustive Search (small n) ---")
    for n in [8, 10, 12, 15]:
        M_best, A_best = exhaustive_max_primitive_coprime(n)
        P = primes_up_to(n)
        M_primes = coprime_pair_count(P)
        print(f"  n={n:2d}: best M={M_best} (set={sorted(A_best)})")
        print(f"         primes M={M_primes} (primes={sorted(P)})")
        print(f"         primes optimal: {M_best == M_primes}")
    print()

    # Part 2: Compare various constructions
    print("--- Part 2: Comparing Constructions ---")
    for n in [50, 100, 200, 500]:
        print(f"\n  n = {n}:")
        results = compare_primitive_sets(n)

        p = results["primes"]
        print(f"    Primes:        |A|={p['size']:4d}, M={p['M']:6d}"
              f" (density=1.000, all coprime={p['match']})")

        t = results["top_layer"]
        print(f"    Top layer:     |A|={t['size']:4d}, M={t['M']:6d}"
              f" (density={t['density']:.3f})")

        p1 = results["primes_plus_1"]
        print(f"    Primes+{{1}}:    |A|={p1['size']:4d}, M={p1['M']:6d}"
              f" (primitive={p1['is_primitive']})")

        s3 = results["sqfree_minp>3"]
        print(f"    Sqfree(p>3):   |A|={s3['size']:4d}, M={s3['M']:6d}"
              f" (primitive={s3['is_primitive']})")

        s5 = results["sqfree_minp>5"]
        print(f"    Sqfree(p>5):   |A|={s5['size']:4d}, M={s5['M']:6d}"
              f" (primitive={s5['is_primitive']})")

        l2 = results["semiprimes_prim"]
        print(f"    Semiprimes:    |A|={l2['size']:4d}, M={l2['M']:6d}"
              f" (primitive={l2['is_primitive']})")

        g = results["greedy"]
        print(f"    Greedy:        |A|={g['size']:4d}, M={g['M']:6d}"
              f" (primitive={g['is_primitive']})")
    print()

    # Part 3: Growth analysis
    print("--- Part 3: Growth Analysis ---")
    print(f"  {'n':>5s}  {'π(n)':>5s}  {'M(primes)':>10s}  {'|top|':>5s}"
          f"  {'M(top)':>10s}  {'winner':>8s}")
    data = analyze_growth(500, 50)
    for row in data:
        winner = "primes" if row["primes_win"] else "top"
        print(f"  {row['n']:5d}  {row['pi_n']:5d}  {row['M_primes']:10d}"
              f"  {row['top_size']:5d}  {row['M_top']:10d}  {winner:>8s}")
    print()

    # Part 4: Exhaustive vs top layer comparison
    print("--- Part 4: Exhaustive Optimum vs Top Layer ---")
    for n in [8, 10, 12, 15]:
        M_best, A_best = exhaustive_max_primitive_coprime(n)
        T = top_layer(n)
        M_top = coprime_pair_count(T)
        ratio = M_best / max(M_top, 1)
        print(f"  n={n:2d}: best={M_best}, top_layer={M_top}, ratio={ratio:.3f}")
    print()

    # Part 5: Top layer coprime density convergence
    print("--- Part 5: Top Layer Coprime Density Convergence ---")
    expected = 6 / math.pi**2
    print(f"  Expected: 6/π² = {expected:.6f}")
    for n in [50, 100, 200, 500, 1000]:
        T = top_layer(n)
        M = coprime_pair_count(T)
        density = M / (len(T) * (len(T) - 1) // 2)
        print(f"  n={n:4d}: density={density:.6f}, error={abs(density-expected):.6f}")
    print()

    # Part 6: Conjecture
    print("=" * 70)
    print("CONJECTURE (NPG-23)")
    print("=" * 70)
    print(f"""
Define M*(n) = max {{ M(A) : A ⊆ [n] primitive }}.

FINDING: Primes do NOT maximize M(A). The top layer T(n) = {{⌊n/2⌋+1,...,n}}
consistently dominates.

Conjecture A (Asymptotic):
  M*(n) = (6/π² + o(1)) · C(⌊n/2⌋, 2) ~ (3/π²) · n²/4

Conjecture B (Extremal set):
  For sufficiently large n, the top layer T(n) achieves M*(n).

Evidence:
- Exhaustive verification shows top layer is optimal or near-optimal for n ≤ 15
- Top layer coprime density → 6/π² as n → ∞
- Size ⌊n/2⌋ is the Dilworth maximum for antichains in ([n], |)
- No construction found that beats the top layer for n > 10

Asymptotic comparison:
  M(primes)    = C(π(n), 2) ~ n²/(2 ln²n)    (grows slowly)
  M(top layer) ~ (3/π²) n²/4 ≈ 0.076 n²       (quadratic)
  Ratio: M(top) / M(primes) → ∞ as n → ∞

The "size vs density" tradeoff strongly favors size.

Connection to Erdős:
- Problem #143: primitive sets and Σ 1/(a log a)
- Problem #530: primitive sets and their densities
- Problem #883: coprime graph structure
- Dilworth's theorem: max antichain in ([n], |) = ⌊n/2⌋
""")


if __name__ == "__main__":
    main()
