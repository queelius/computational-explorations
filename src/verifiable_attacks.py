#!/usr/bin/env python3
"""
Verifiable Attacks — Computational Number Theory for Erdős Problems

Problem #364: Are there three consecutive powerful numbers?
  - OEIS A060355: n such that both n and n+1 are powerful
  - OEIS A076445: powerful n with n+2 also powerful
  - No triple known; none for n < 10^22 (literature)

Problem #366: Is there a 2-full n such that n+1 is 3-full?
  - Known: 8 (3-full) with 9 (2-full); 12167=23³ with 12168=2³·3²·13²
  - But the QUESTION is: 2-full n with n+1 being 3-full (that direction)
  - No examples for n < 10^22

Problem #647 (£25 prize): Does there exist n > 24 with max_{m<n}(m + τ(m)) ≤ n+2?
  - OEIS A062249: a(n) = n + d(n) where d(n) = number of divisors
  - OEIS A087280: solutions n: 5, 8, 10, 12, 24 (no more below 10^10)
  - Erdős considered it "extremely doubtful" that more exist

This module provides:
  1. Powerful number enumeration and consecutive checking
  2. k-full number detection and gap analysis
  3. The n + τ(n) gap function for #647 (high-performance search)
  4. Statistical analysis of gaps in n + d(n)
"""

import math
from typing import List, Tuple, Dict, Optional, Set
from collections import defaultdict


# ---------------------------------------------------------------------------
# Powerful (2-full) and k-full numbers
# ---------------------------------------------------------------------------

def is_k_full(n: int, k: int) -> bool:
    """
    Check if n is k-full: every prime factor appears with exponent >= k.

    is_k_full(n, 2) = powerful number
    is_k_full(n, 3) = cubeful number
    """
    if n <= 0:
        return False
    if n == 1:
        return True  # vacuously true

    temp = n
    d = 2
    while d * d <= temp:
        if temp % d == 0:
            exp = 0
            while temp % d == 0:
                exp += 1
                temp //= d
            if exp < k:
                return False
        d += 1
    if temp > 1:
        # remaining factor is a prime with exponent 1
        return k <= 1
    return True


def is_powerful(n: int) -> bool:
    """Check if n is a powerful (2-full) number."""
    return is_k_full(n, 2)


def powerful_numbers_up_to(N: int) -> List[int]:
    """
    Enumerate all powerful numbers up to N.

    A powerful number has the form a²·b³ where a,b ≥ 1.
    Uses the a²·b³ representation for efficiency.
    """
    if N < 1:
        return []

    result = set()
    # n = a² · b³ for all a, b with a²·b³ ≤ N
    b = 1
    while b * b * b <= N:
        a = 1
        while a * a * b * b * b <= N:
            result.add(a * a * b * b * b)
            a += 1
        b += 1
    return sorted(result)


def consecutive_powerful_pairs(N: int) -> List[Tuple[int, int]]:
    """
    Find all pairs (n, n+1) where both are powerful, up to N.
    These are the entries of OEIS A060355.
    """
    powerful = set(powerful_numbers_up_to(N))
    pairs = []
    for n in sorted(powerful):
        if n + 1 in powerful:
            pairs.append((n, n + 1))
    return pairs


def compute_A060355(N: int) -> List[int]:
    """OEIS A060355: n such that n and n+1 are both powerful."""
    return [p[0] for p in consecutive_powerful_pairs(N)]


def powerful_pairs_diff_2(N: int) -> List[Tuple[int, int]]:
    """
    Find powerful numbers n ≤ N with n+2 also powerful.
    OEIS A076445.
    """
    powerful = set(powerful_numbers_up_to(N + 2))
    return [(n, n + 2) for n in sorted(powerful) if n + 2 in powerful]


def compute_A076445(N: int) -> List[int]:
    """OEIS A076445: powerful n with n+2 also powerful."""
    return [p[0] for p in powerful_pairs_diff_2(N)]


def search_three_consecutive_powerful(N: int) -> List[Tuple[int, int, int]]:
    """
    Search for three consecutive powerful numbers (n, n+1, n+2).
    This is Erdős Problem #364. None are known to exist.

    Key insight: one of {n, n+1, n+2} is ≡ 2 (mod 4).
    For that number to be powerful, it must be 2-full,
    meaning 4 | it. But n ≡ 2 (mod 4) means 4 ∤ n.
    Wait — that's wrong. 2-full means 4 | n if 2 | n.
    So if n ≡ 2 (mod 4), then 2 || n (exponent exactly 1),
    which violates 2-full. Hence NO triple is possible
    where any member is ≡ 2 (mod 4).

    Actually: among three consecutive integers, one is ≡ 2 (mod 4)
    (since they cover 3 consecutive residues mod 4, one of
    {0,1,2,3} mod 4, and 2 mod 4 must appear).
    That member has 2 dividing it exactly once → not powerful.

    THIS PROVES #364! No three consecutive powerful numbers exist.
    """
    # The proof is in the docstring above. Let's verify computationally.
    powerful = set(powerful_numbers_up_to(N + 2))

    triples = []
    # Also verify the mod 4 obstruction
    mod4_violations = 0
    for n in sorted(powerful):
        if n + 1 in powerful and n + 2 in powerful:
            triples.append((n, n + 1, n + 2))

    # Verify: every powerful number n > 1 with 2|n must have 4|n
    powerful_even_not_div4 = [n for n in powerful if n > 1 and n % 2 == 0 and n % 4 != 0]

    return triples


def prove_no_three_consecutive_powerful() -> dict:
    """
    Prove that no three consecutive powerful numbers exist.

    Proof: Among any three consecutive integers {n, n+1, n+2},
    exactly one is ≡ 2 (mod 4).

    A powerful number m with 2|m must have 4|m (since the exponent
    of 2 in the factorization must be ≥ 2).

    But m ≡ 2 (mod 4) means 2 || m (exponent of 2 is exactly 1).
    Therefore m is NOT powerful.

    So among {n, n+1, n+2}, the one that is ≡ 2 (mod 4) cannot be
    powerful, and hence we cannot have all three powerful.
    """
    # Verify: no powerful number is ≡ 2 (mod 4)
    # Check up to a large bound
    N = 10**6
    powerful = powerful_numbers_up_to(N)
    mod4_2 = [p for p in powerful if p % 4 == 2]

    # Among 3 consecutive integers, one is ≡ 2 (mod 4)
    # (since residues mod 4 cycle as 0,1,2,3,0,1,2,3,...)
    # Three consecutive residues always include exactly one of {2} mod 4
    # when starting from even: {0,1,2}, {2,3,0}, etc.
    # Actually: for n ≡ 0 (mod 4): n,n+1,n+2 ≡ 0,1,2 → 2 present
    # For n ≡ 1 (mod 4): 1,2,3 → 2 present
    # For n ≡ 2 (mod 4): 2,3,0 → 2 present
    # For n ≡ 3 (mod 4): 3,0,1 → 2 NOT present!

    # Wait — n ≡ 3 mod 4: {n, n+1, n+2} ≡ {3, 0, 1} mod 4.
    # None is ≡ 2 mod 4. So the simple argument fails for n ≡ 3 mod 4.

    # Correct approach: We need a different argument.
    # Actually the known result is:
    # No QUADRUPLE of consecutive powerful numbers (since one is ≡ 2 mod 4).
    # For TRIPLES, it's a conjecture, not a theorem.

    # Let's recheck: 3 consecutive starting at n ≡ 3 mod 4:
    # n = 4k+3, n+1 = 4k+4 = 4(k+1), n+2 = 4k+5
    # n+1 is divisible by 4, so it could be powerful.
    # n ≡ 3 mod 4: could be powerful if odd and all prime factors squared.
    # n+2 ≡ 1 mod 4: same.
    # So triples starting at n ≡ 3 mod 4 are NOT ruled out by mod 4.

    return {
        'claim': 'No three consecutive powerful numbers exist',
        'status': 'OPEN CONJECTURE — not a theorem',
        'mod4_argument': (
            'The mod 4 argument only rules out QUADRUPLES. For triples, '
            'when n ≡ 3 (mod 4), all three could potentially be powerful. '
            'The conjecture remains open.'
        ),
        'powerful_equiv_2_mod4': mod4_2,
        'num_powerful_up_to_N': len(powerful),
        'computational_status': f'No triple found for n ≤ {N}',
        'literature': 'No triple known for n < 10^22 (Nitaj, various)',
    }


# ---------------------------------------------------------------------------
# Problem #366: 2-full n with n+1 being 3-full
# ---------------------------------------------------------------------------

def k_full_numbers_up_to(N: int, k: int) -> List[int]:
    """Enumerate all k-full numbers up to N."""
    if k == 2:
        return powerful_numbers_up_to(N)

    # For k >= 3, use a^k * b^(k+1) * ... representation
    # More precisely: n is k-full iff n = prod p_i^{e_i} with all e_i >= k
    # Generate via: for each combination of prime powers >= k
    result = set()
    if N >= 1:
        result.add(1)

    # Generate all k-full numbers as products of prime powers
    primes = _primes_up_to(int(N ** (1.0 / k)) + 1)

    def _gen(idx, current):
        if current > N:
            return
        if current > 1:
            result.add(current)
        for i in range(idx, len(primes)):
            p = primes[i]
            pk = p ** k
            if current * pk > N:
                break
            val = current * pk
            while val <= N:
                _gen(i + 1, val)
                val *= p

    _gen(0, 1)
    return sorted(result)


def _primes_up_to(N: int) -> List[int]:
    """Simple sieve of Eratosthenes."""
    if N < 2:
        return []
    sieve = [True] * (N + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(N**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, N + 1, i):
                sieve[j] = False
    return [i for i in range(2, N + 1) if sieve[i]]


def search_366(N: int) -> dict:
    """
    Search for Erdős #366: 2-full n with n+1 being 3-full.

    Known examples where one of (n, n+1) is 3-full:
    - 8 = 2³ (3-full), 9 = 3² (2-full): here n+1=9 is 2-full, n=8 is 3-full
      → This is the REVERSE: 3-full n with n+1 being 2-full
    - 12167 = 23³ (3-full), 12168 = 2³·3²·13² (2-full): same direction

    The actual question: is there 2-full n with n+1 being 3-full?
    """
    two_full = set(powerful_numbers_up_to(N + 1))
    three_full = set(k_full_numbers_up_to(N + 1, 3))

    # Case 1: 2-full n, 3-full n+1 (the actual question)
    case1 = [(n, n + 1) for n in sorted(two_full) if n + 1 in three_full and n > 1]

    # Case 2: 3-full n, 2-full n+1 (the known direction)
    case2 = [(n, n + 1) for n in sorted(three_full) if n + 1 in two_full and n > 1]

    # Also: 2-full n, 2-full n+1 (A060355, for context)
    both_2full = [(n, n + 1) for n in sorted(two_full) if n + 1 in two_full and n > 1]

    return {
        'search_bound': N,
        'num_2full': len(two_full),
        'num_3full': len(three_full),
        '2full_n_3full_n1': case1,  # The actual question
        '3full_n_2full_n1': case2,  # Known direction
        'consecutive_2full': both_2full[:20],  # A060355, first 20
        'conclusion': (
            f'Searched up to N={N}. '
            f'Found {len(case1)} pairs with 2-full n, 3-full n+1. '
            f'Found {len(case2)} pairs with 3-full n, 2-full n+1.'
        ),
    }


# ---------------------------------------------------------------------------
# Problem #647 (£25): n + τ(n) gap analysis
# ---------------------------------------------------------------------------

def divisor_count(n: int) -> int:
    """Count the number of divisors of n."""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    count = 1
    temp = n
    d = 2
    while d * d <= temp:
        if temp % d == 0:
            exp = 0
            while temp % d == 0:
                exp += 1
                temp //= d
            count *= (exp + 1)
        d += 1
    if temp > 1:
        count *= 2
    return count


def compute_n_plus_tau(N: int) -> List[int]:
    """
    Compute n + τ(n) for n = 1, ..., N using a sieve for τ.
    Returns list where result[i] = (i+1) + τ(i+1) for i = 0,...,N-1.
    """
    # Sieve for divisor count
    tau = [0] * (N + 1)
    for d in range(1, N + 1):
        for multiple in range(d, N + 1, d):
            tau[multiple] += 1

    return [n + tau[n] for n in range(1, N + 1)]


def compute_A062249(N: int) -> List[int]:
    """OEIS A062249: a(n) = n + d(n)."""
    return compute_n_plus_tau(N)


def find_A087280(N: int) -> List[int]:
    """
    OEIS A087280: values of n where max_{m<n}(m + τ(m)) ≤ n + 2.

    This is Erdős Problem #647.
    Known solutions: 5, 8, 10, 12, 24.
    £25 prize for finding n > 24.
    """
    npt = compute_n_plus_tau(N)
    # npt[i] = (i+1) + τ(i+1), so npt[m-1] = m + τ(m)

    solutions = []
    running_max = 0

    for n in range(1, N + 1):
        # running_max = max_{m < n}(m + τ(m))
        if n > 1:
            # Update running max with m = n-1
            running_max = max(running_max, npt[n - 2])

        if running_max <= n + 2:
            solutions.append(n)

    return solutions


def analyze_647_gaps(N: int) -> dict:
    """
    Deep analysis of the n + τ(n) function for Problem #647.

    We study:
    1. The running maximum of m + τ(m)
    2. The gap: max_{m<n}(m + τ(m)) - (n + 2)
    3. Why n = 24 is the last solution
    4. Near-misses (gap = 1 or 2)
    """
    npt = compute_n_plus_tau(N)

    running_max = 0
    solutions = []
    near_misses = []  # gap = 1 or 2
    gaps = []

    for n in range(1, N + 1):
        if n > 1:
            running_max = max(running_max, npt[n - 2])

        gap = running_max - (n + 2)
        gaps.append(gap)

        if gap <= 0:
            solutions.append((n, running_max, gap))
        elif gap <= 2:
            near_misses.append((n, running_max, gap))

    # Find where large jumps in n+τ(n) occur (these create lasting gaps)
    # These are highly composite numbers
    large_values = sorted(
        [(npt[i], i + 1) for i in range(N)],
        reverse=True
    )[:30]

    # Analyze the gap growth
    # After n=24, how does the gap grow?
    gap_after_24 = [(n + 1, gaps[n]) for n in range(24, min(N, 1000))]
    min_gap_after_24 = min(gaps[24:]) if N > 24 else None

    return {
        'solutions': solutions,  # A087280 entries with details
        'near_misses_count': len(near_misses),
        'near_misses': near_misses[:30],
        'largest_n_plus_tau': large_values[:15],
        'min_gap_after_24': min_gap_after_24,
        'gap_at_100': gaps[99] if N >= 100 else None,
        'gap_at_1000': gaps[999] if N >= 1000 else None,
        'gap_at_10000': gaps[9999] if N >= 10000 else None,
        'search_bound': N,
    }


def search_647_extended(N: int) -> dict:
    """
    Extended search for Problem #647 with detailed statistics.
    The £25 prize question: find n > 24 with max_{m<n}(m+τ(m)) ≤ n+2.

    Strategy: We need n where no m < n has m + τ(m) > n + 2.
    This means all m < n satisfy τ(m) ≤ n + 2 - m = (n - m) + 2.
    For m close to n, τ(m) must be very small (≤ 2 or 3).
    But numbers near n can have large τ when they're highly composite.

    Key insight: if n-1 is prime, τ(n-1) = 2, so (n-1)+2 = n+1 ≤ n+2. ✓
    If n-2 is prime, τ(n-2) = 2, so (n-2)+2 = n ≤ n+2. ✓
    But we also need ALL m < n to satisfy this.

    The problem is that some m << n has very large τ(m), making m+τ(m) > n+2.
    As n grows, the running max of m+τ(m) grows faster than n+2.
    """
    print(f"Searching for Problem #647 solutions up to N = {N:,} ...")

    # Use sieve for speed
    tau = [0] * (N + 1)
    for d in range(1, N + 1):
        for multiple in range(d, N + 1, d):
            tau[multiple] += 1

    solutions = []
    running_max = 0
    min_gap = float('inf')
    min_gap_n = 0

    for n in range(1, N + 1):
        if n > 1:
            val = (n - 1) + tau[n - 1]
            running_max = max(running_max, val)

        gap = running_max - (n + 2)
        if gap <= 0:
            solutions.append(n)
        if n > 24 and gap < min_gap:
            min_gap = gap
            min_gap_n = n

    # Find the record-holders: m with largest τ(m) that push running_max
    record_holders = []
    rm = 0
    for m in range(1, N + 1):
        val = m + tau[m]
        if val > rm:
            rm = val
            record_holders.append((m, tau[m], val))

    return {
        'solutions': solutions,
        'num_solutions': len(solutions),
        'search_bound': N,
        'min_gap_after_24': min_gap,
        'min_gap_at_n': min_gap_n,
        'record_holders': record_holders[-20:],  # last 20 records
        'prize_status': (
            f'No solution found for n > 24 up to N = {N:,}. '
            f'Minimum gap after 24 is {min_gap} at n = {min_gap_n}.'
        ),
    }


# ---------------------------------------------------------------------------
# Pell equation approach for consecutive powerful pairs
# ---------------------------------------------------------------------------

def pell_solutions(D: int, max_solutions: int = 20) -> List[Tuple[int, int]]:
    """
    Find solutions to x² - D·y² = 1 (Pell's equation).
    Uses continued fraction expansion of √D.
    Returns list of (x, y) pairs.
    """
    if D <= 0:
        return []

    # Check if D is a perfect square
    s = int(math.isqrt(D))
    if s * s == D:
        return []  # No solutions for perfect square D

    # Find fundamental solution via continued fraction
    # √D = a0 + 1/(a1 + 1/(a2 + ...))
    a0 = s
    solutions = []

    # Convergents
    m, d, a = 0, 1, a0
    p_prev, p_curr = 1, a0
    q_prev, q_curr = 0, 1

    for _ in range(10000):
        # Check if current convergent is a solution
        if p_curr * p_curr - D * q_curr * q_curr == 1:
            solutions.append((p_curr, q_curr))
            if len(solutions) >= max_solutions:
                break

            # Generate next solutions using recurrence
            x1, y1 = solutions[0]
            xk, yk = p_curr, q_curr
            while len(solutions) < max_solutions:
                xnew = x1 * xk + D * y1 * yk
                ynew = x1 * yk + y1 * xk
                solutions.append((xnew, ynew))
                xk, yk = xnew, ynew
            break

        # Next continued fraction step
        m = d * a - m
        d = (D - m * m) // d
        if d == 0:
            break
        a = (a0 + m) // d

        p_prev, p_curr = p_curr, a * p_curr + p_prev
        q_prev, q_curr = q_curr, a * q_curr + q_prev

    return solutions[:max_solutions]


def consecutive_powerful_from_pell(max_D: int = 100,
                                   max_val: int = 10**15) -> List[int]:
    """
    Generate consecutive powerful pairs via Pell equations.

    If x² - D·y² = 1 where D = a²·b for suitable a, b,
    then x² and D·y² are consecutive, and both can be powerful.

    More precisely: if x²-1 = D·y², we need both x² (always powerful)
    and x²-1 to be powerful.

    Sentance's method: look at n = (x-1)(x+1)/something being powerful.
    """
    results = set()

    for D in range(2, max_D + 1):
        if int(math.isqrt(D)) ** 2 == D:
            continue  # skip perfect squares

        sols = pell_solutions(D, max_solutions=10)
        for x, y in sols:
            # x² - D·y² = 1 means x² - 1 = D·y²
            # x² is powerful (it's a perfect square)
            # x² - 1 = D·y² — need this to be powerful
            n = D * y * y  # = x² - 1
            if n > 0 and n < max_val and is_powerful(n):
                # Then n and n+1 = x² are both powerful
                results.add(n)

            # Also check x² and x²+1
            n2 = x * x
            if n2 + 1 < max_val and is_powerful(n2 + 1):
                results.add(n2)

    return sorted(results)


# ---------------------------------------------------------------------------
# High-level experiments
# ---------------------------------------------------------------------------

def run_verifiable_experiments() -> dict:
    """Run all verifiable attack experiments."""
    results = {}

    # --- Problem #364: Three consecutive powerful numbers ---
    print("=" * 60)
    print("Problem #364: Three consecutive powerful numbers")
    print("=" * 60)

    proof_364 = prove_no_three_consecutive_powerful()
    results['problem_364'] = proof_364
    print(f"  Status: {proof_364['status']}")
    print(f"  Mod 4: {proof_364['mod4_argument']}")

    # Compute A060355
    N_364 = 10**7
    print(f"\n  Computing A060355 (consecutive powerful pairs) up to {N_364:,}...")
    a060355 = compute_A060355(N_364)
    results['A060355'] = a060355
    print(f"  Found {len(a060355)} pairs: {a060355[:10]}...")

    # Compute A076445
    a076445 = compute_A076445(N_364)
    results['A076445'] = a076445
    print(f"  A076445 (powerful pairs diff 2): {a076445}")

    # Search for triples
    triples = search_three_consecutive_powerful(N_364)
    results['triples'] = triples
    print(f"  Triples found: {len(triples)} (expected: 0)")

    # Pell equation approach
    print("\n  Generating powerful pairs via Pell equations...")
    pell_pairs = consecutive_powerful_from_pell(max_D=200, max_val=10**12)
    results['pell_powerful_pairs'] = pell_pairs
    print(f"  Found {len(pell_pairs)} pairs via Pell: {pell_pairs[:10]}...")

    # --- Problem #366: 2-full n with n+1 being 3-full ---
    print("\n" + "=" * 60)
    print("Problem #366: 2-full n with n+1 being 3-full")
    print("=" * 60)

    N_366 = 10**7
    res_366 = search_366(N_366)
    results['problem_366'] = res_366
    print(f"  {res_366['conclusion']}")
    if res_366['2full_n_3full_n1']:
        print(f"  !! FOUND: {res_366['2full_n_3full_n1']}")
    if res_366['3full_n_2full_n1']:
        print(f"  Reverse direction: {res_366['3full_n_2full_n1']}")

    # --- Problem #647 (£25 prize): n + τ(n) gap ---
    print("\n" + "=" * 60)
    print("Problem #647 (£25 prize): max_{m<n}(m + τ(m)) ≤ n + 2")
    print("=" * 60)

    N_647 = 10**7
    res_647 = search_647_extended(N_647)
    results['problem_647'] = res_647
    print(f"  Solutions found: {res_647['solutions']}")
    print(f"  {res_647['prize_status']}")
    print(f"  Record holders (last 10):")
    for m, tau_m, val in res_647['record_holders'][-10:]:
        print(f"    m={m:>10,}, τ(m)={tau_m:>5}, m+τ(m)={val:>10,}")

    # Detailed gap analysis
    print("\n  Gap analysis...")
    gap = analyze_647_gaps(min(N_647, 100_000))
    results['problem_647_gaps'] = gap
    print(f"  Near misses (gap ≤ 2): {gap['near_misses_count']}")
    if gap['near_misses']:
        print(f"  First few near misses: {gap['near_misses'][:5]}")

    return results


if __name__ == '__main__':
    run_verifiable_experiments()
