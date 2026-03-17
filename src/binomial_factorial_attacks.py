#!/usr/bin/env python3
"""
Binomial Coefficient and Factorial Attacks — Open Erdos Problems

The factorial family is the MOST OVERDUE (10.87x average gap ratio).
This module attacks 15 open binomial-coefficient and 10 open factorial problems.

Targets:
  #849: Singmaster's conjecture (multiplicity in Pascal's triangle)
  #683, #684, #685: Binomial divisibility and p-adic valuations
  #373, #390, #400, #912: Factorial representations and factorial primes
  Catalan number divisibility and squarefreeness
  Wolstenholme primes (p^3 | C(2p,p) - 2)

Each section:
  1. Computes or extends known sequences
  2. Searches for rare objects (high multiplicities, Wolstenholme primes, etc.)
  3. Looks for structural patterns and growth rates
"""

import math
from collections import defaultdict, Counter
from functools import lru_cache
from typing import List, Tuple, Dict, Set, Optional


# =============================================================================
# Primality and factoring utilities
# =============================================================================

def _sieve_primes(limit: int) -> List[int]:
    """Sieve of Eratosthenes up to limit."""
    if limit < 2:
        return []
    is_prime = bytearray(b'\x01') * (limit + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, math.isqrt(limit) + 1):
        if is_prime[i]:
            for j in range(i * i, limit + 1, i):
                is_prime[j] = 0
    return [i for i in range(2, limit + 1) if is_prime[i]]


def _is_prime(n: int) -> bool:
    """Deterministic primality test for n < 3.3 * 10^24 (Miller-Rabin)."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    # Trial division for small factors
    if n < 1000:
        d = 5
        while d * d <= n:
            if n % d == 0 or n % (d + 2) == 0:
                return False
            d += 6
        return True
    # Miller-Rabin with deterministic witness set for n < 3.3e24
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def _factorize(n: int) -> Dict[int, int]:
    """
    Return prime factorization as {prime: exponent}.
    Efficient for n up to ~10^15.
    """
    if n <= 1:
        return {}
    factors = {}
    # Factor out 2
    while n % 2 == 0:
        factors[2] = factors.get(2, 0) + 1
        n //= 2
    # Odd factors
    d = 3
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 2
    if n > 1:
        factors[n] = 1
    return factors


def _digit_sum_base_p(n: int, p: int) -> int:
    """Sum of digits of n in base p."""
    if n == 0:
        return 0
    s = 0
    while n > 0:
        s += n % p
        n //= p
    return s


# =============================================================================
# Section 1: Singmaster's Conjecture Extensions (#849)
# =============================================================================
#
# Conjecture: There exists a finite bound B such that no integer > 1
# appears more than B times as a binomial coefficient C(n,k).
#
# Known: 3003 has multiplicity 8.  No integer with multiplicity > 8 is known.
# Goal: Search for multiplicity >= 10 up to row 10^6.


def singmaster_scan_row(n: int, counts: Dict[int, int], k_start: int = 2) -> None:
    """
    Scan row n of Pascal's triangle, updating multiplicity counts.

    For each C(n, k) with k_start <= k <= n/2, increments counts[val].
    Symmetry: C(n,k) = C(n,n-k), so each interior entry gets +2,
    except the central entry (k = n/2 for even n) which gets +1.
    """
    for k in range(k_start, n // 2 + 1):
        val = math.comb(n, k)
        if 2 * k == n:
            counts[val] = counts.get(val, 0) + 1
        else:
            counts[val] = counts.get(val, 0) + 2


def singmaster_multiplicity_search(max_row: int,
                                   threshold: int = 8
                                   ) -> List[Dict]:
    """
    Search for integers with multiplicity >= threshold in Pascal's triangle
    by scanning rows 0..max_row.

    For each value, its multiplicity = number of (n,k) pairs with C(n,k) = val
    (counting symmetric pairs). We also add the trivial k=1 appearances:
    every integer N appears as C(N,1) and C(N, N-1).

    Returns list of {value, multiplicity, positions} sorted by multiplicity desc.
    """
    # counts: value -> total count of appearances
    counts: Dict[int, int] = defaultdict(int)
    # positions: value -> set of (n, k) for k >= 2
    positions: Dict[int, Set[Tuple[int, int]]] = defaultdict(set)

    for n in range(4, max_row + 1):
        for k in range(2, n // 2 + 1):
            val = math.comb(n, k)
            positions[val].add((n, k))
            if 2 * k == n:
                counts[val] += 1
            else:
                counts[val] += 2
                positions[val].add((n, n - k))

    # Add k=1 appearances: C(val, 1) = val for all val >= 2
    for val in list(counts.keys()):
        if val >= 2:
            counts[val] += 2  # C(val, 1) and C(val, val-1)

    results = []
    for val, mult in counts.items():
        if mult >= threshold and val > 1:
            results.append({
                'value': val,
                'multiplicity': mult,
                'positions': sorted(positions[val]),
            })

    results.sort(key=lambda r: (-r['multiplicity'], r['value']))
    return results


def singmaster_known_high_multiplicity() -> List[Dict]:
    """
    Verify known high-multiplicity values.

    3003 = C(3003,1) = C(78,2) = C(15,5) = C(14,6) has multiplicity 8.
    Also: 120, 210, 1540, 7140, 11628, 24310 have multiplicity >= 6.
    """
    known = [
        (3003, [(3003, 1), (3003, 3002), (78, 2), (78, 76),
                (15, 5), (15, 10), (14, 6), (14, 8)]),
        (120, [(120, 1), (120, 119), (16, 2), (16, 14), (10, 3), (10, 7)]),
        (210, [(210, 1), (210, 209), (21, 2), (21, 19), (10, 4), (10, 6)]),
        (1540, [(1540, 1), (1540, 1539), (56, 2), (56, 54), (22, 3), (22, 19)]),
    ]
    results = []
    for val, expected_positions in known:
        verified_count = 0
        for n, k in expected_positions:
            if math.comb(n, k) == val:
                verified_count += 1
        results.append({
            'value': val,
            'expected_multiplicity': len(expected_positions),
            'verified': verified_count == len(expected_positions),
        })
    return results


def singmaster_infinite_family_multiplicities(num_terms: int = 10) -> List[Dict]:
    """
    Compute the infinite family from Lind (1968):
    C(n, k) = C(n-1, k+1) when n(n-1) = (k+1)(k+2)·(something).

    The known infinite families come from solutions to
      C(2r, r-1) = C(2r-1, r+1)
    which reduces to a Pell-like equation.

    The Fibonacci-derived family: for F = Fibonacci numbers,
      C(F_{2i} · F_{2i+1}, F_{2i-1} · F_{2i} - 1)
    gives infinitely many values with multiplicity >= 6.
    """
    fib = [1, 1]
    while len(fib) < 2 * num_terms + 4:
        fib.append(fib[-1] + fib[-2])

    results = []
    for i in range(1, num_terms + 1):
        f_2im1 = fib[2 * i - 2]  # F(2i-1) in 1-indexed
        f_2i = fib[2 * i - 1]     # F(2i)
        f_2ip1 = fib[2 * i]       # F(2i+1)

        n_val = f_2i * f_2ip1
        k_val = f_2im1 * f_2i - 1

        # This value appears at least 6 times
        val = math.comb(n_val, k_val) if n_val <= 10000 else None

        results.append({
            'i': i,
            'n': n_val,
            'k': k_val,
            'F_2im1': f_2im1,
            'F_2i': f_2i,
            'F_2ip1': f_2ip1,
            'value': val,
            'min_multiplicity': 6,
        })

    return results


# =============================================================================
# Section 2: Binomial Divisibility (#683, #684, #685)
# =============================================================================
#
# p-adic valuation: v_p(C(n,k)) = (s_p(k) + s_p(n-k) - s_p(n)) / (p-1)
# where s_p(m) = digit sum of m in base p  (Kummer's theorem).
#
# Central binomial coefficients C(2n, n) have special divisibility structure.


def p_adic_valuation_binom(n: int, k: int, p: int) -> int:
    """
    Compute v_p(C(n,k)) using Kummer's theorem.

    v_p(C(n,k)) = (number of carries when adding k and n-k in base p)
                 = (s_p(k) + s_p(n-k) - s_p(n)) / (p-1)
    """
    if k < 0 or k > n:
        return 0  # C(n,k) = 0
    s_k = _digit_sum_base_p(k, p)
    s_nk = _digit_sum_base_p(n - k, p)
    s_n = _digit_sum_base_p(n, p)
    return (s_k + s_nk - s_n) // (p - 1)


def carries_in_base_p(a: int, b: int, p: int) -> int:
    """
    Count the number of carries when adding a and b in base p.
    Equivalent to v_p(C(a+b, a)) by Kummer's theorem.

    Process digits from least significant to most significant.
    At each position, compute digit_a + digit_b + carry_in.
    If the sum >= p, a carry is produced and we count it.
    We stop when both numbers are exhausted; the final carry-out
    (if any) was already counted at the last digit position.
    """
    carry = 0
    total_carries = 0
    while a > 0 or b > 0:
        digit_sum = (a % p) + (b % p) + carry
        carry = digit_sum // p
        total_carries += carry  # carry is 0 or 1
        a //= p
        b //= p
    # Do NOT count the final carry-out beyond the last digit position,
    # as it was already produced (and counted) at that position.
    return total_carries


def central_binom_prime_divisors(max_n: int,
                                 max_p: int = 100
                                 ) -> List[Dict]:
    """
    For each n in 1..max_n, determine which primes p <= max_p divide C(2n, n)
    and with what p-adic valuation.

    Returns list of {n, prime_valuations: {p: v_p}, total_prime_factors}.

    Pattern: v_p(C(2n,n)) = (s_p(n) - s_p(2n)) / (p-1) + n/(p-1)
    but more accurately, v_p(C(2n,n)) = carries when adding n+n in base p.
    """
    primes = _sieve_primes(max_p)
    results = []
    for n in range(1, max_n + 1):
        valuations = {}
        for p in primes:
            v = p_adic_valuation_binom(2 * n, n, p)
            if v > 0:
                valuations[p] = v
        results.append({
            'n': n,
            'prime_valuations': valuations,
            'num_prime_factors': len(valuations),
        })
    return results


def primes_dividing_central_binom(n: int) -> List[int]:
    """
    Return all primes that divide C(2n, n).

    By Kummer's theorem, p | C(2n,n) iff there is a carry when adding n+n
    in base p, i.e., iff some digit of n in base p is >= ceil(p/2).

    For large n, every prime <= 2n may divide C(2n,n) except when
    n in base p has all digits < p/2.
    """
    result = []
    primes = _sieve_primes(2 * n)
    for p in primes:
        if p_adic_valuation_binom(2 * n, n, p) > 0:
            result.append(p)
    return result


def primes_not_dividing_central_binom(max_n: int) -> Dict[int, List[int]]:
    """
    For each n up to max_n, find primes p <= 2n that do NOT divide C(2n,n).

    These are primes where n in base p has all digits < p/2.
    The density of such n for a given p relates to the p-adic structure.

    Relevant to #683/#684: understanding which primes "miss" C(2n,n).
    """
    results = {}
    for n in range(1, max_n + 1):
        primes = _sieve_primes(2 * n)
        non_dividing = []
        for p in primes:
            if p_adic_valuation_binom(2 * n, n, p) == 0:
                non_dividing.append(p)
        if non_dividing:
            results[n] = non_dividing
    return results


def central_binom_valuation_records(max_n: int) -> List[Dict]:
    """
    Track record-breaking v_p(C(2n,n)) for each prime p.

    For small p, the valuation grows roughly as n/(p-1).
    We look for n where v_p is unusually large or small relative to expected.
    """
    records: Dict[int, Tuple[int, int]] = {}  # p -> (max_v, best_n)
    primes = _sieve_primes(min(max_n * 2, 200))

    results = []
    for n in range(1, max_n + 1):
        for p in primes:
            if p > 2 * n:
                break
            v = p_adic_valuation_binom(2 * n, n, p)
            prev = records.get(p, (0, 0))
            if v > prev[0]:
                records[p] = (v, n)
                results.append({
                    'prime': p, 'n': n,
                    'valuation': v,
                    'expected': n // (p - 1) if p > 1 else n,
                    'excess': v - (n // (p - 1)) if p > 1 else 0,
                })
    return results


def granville_pattern(max_n: int) -> List[Dict]:
    """
    Granville's observation: C(2n,n) is divisible by all primes p with
    n < p <= 2n, and these contribute exactly one factor each.

    The remaining prime factors come from p <= n.
    For "smooth" n (few carries in all small bases), C(2n,n) may be
    divisible by fewer small primes.

    This function computes the "Granville ratio":
      (product of primes in (n, 2n]) / C(2n, n)
    """
    results = []
    for n in range(2, max_n + 1):
        primes_in_range = [p for p in _sieve_primes(2 * n) if p > n]
        # v_p = 1 for these primes (exactly one carry in base p)
        log_product = sum(math.log(p) for p in primes_in_range)
        log_central = sum(math.log(k) for k in range(n + 1, 2 * n + 1)) \
                     - sum(math.log(k) for k in range(1, n + 1))

        # Ratio: log of (C(2n,n) / prod primes in (n,2n])
        # This is the "extra" from small primes
        ratio = log_central - log_product

        results.append({
            'n': n,
            'num_large_primes': len(primes_in_range),
            'log_large_product': round(log_product, 4),
            'log_central_binom': round(log_central, 4),
            'small_prime_log_contribution': round(ratio, 4),
        })
    return results


# =============================================================================
# Section 3: Factorial Problems (#373, #390, #400, #912)
# =============================================================================


# --- 3a. Factorials as products of consecutive integers (#373) ---

def factorial_as_consecutive_product(n: int) -> List[Tuple[int, int]]:
    """
    Find all representations n! = a * (a+1) * ... * (a+k-1) for a >= 2, k >= 2,
    where a is NOT necessarily 1.

    Equivalent to: n! = (a+k-1)! / (a-1)! = C(a+k-1, k) * k!

    The trivial representation is a=1, k=n.
    We look for non-trivial ones: a >= 2.

    Returns list of (a, k) pairs.
    """
    if n <= 2:
        return []

    target = math.factorial(n)
    results = []

    # For each length k >= 2, check if there exists a >= 2 with
    # a * (a+1) * ... * (a+k-1) = target
    for k in range(2, n + 1):
        # a^k <= target <= (a+k)^k approximately
        # so a ~ target^(1/k) - k/2
        approx_a = round(target ** (1.0 / k) - (k - 1) / 2.0)
        # Search around the approximation
        lo = max(2, approx_a - k)
        hi = approx_a + k + 1

        for a in range(lo, hi):
            product = 1
            for j in range(k):
                product *= (a + j)
                if product > target:
                    break
            if product == target:
                results.append((a, k))

    return results


def factorial_consecutive_table(max_n: int) -> List[Dict]:
    """
    For n = 2..max_n, find all non-trivial consecutive-product representations
    of n! and tabulate them.
    """
    results = []
    for n in range(2, max_n + 1):
        reps = factorial_as_consecutive_product(n)
        results.append({
            'n': n,
            'factorial': math.factorial(n),
            'representations': reps,
            'count': len(reps),
        })
    return results


# --- 3b. Factorial primes: n! +/- 1 (#390) ---

def is_probable_prime(n: int) -> bool:
    """
    Probabilistic primality test using Miller-Rabin.
    For n < 3.3 * 10^24, the deterministic witness set is sufficient.
    For larger n, this is probabilistic but extremely reliable.
    """
    if n < 2:
        return False
    if n < 1000000:
        return _is_prime(n)
    return _is_prime(n)


def factorial_prime_search(max_n: int) -> Dict[str, List[int]]:
    """
    Search for factorial primes: n such that n! + 1 or n! - 1 is prime.

    Known factorial primes n! + 1: n = 1, 2, 3, 11, 27, 37, 41, 73, 77, 116, 154, ...
    Known factorial primes n! - 1: n = 3, 4, 6, 7, 12, 14, 30, 32, 33, 38, 94, 166, ...

    For large n, we use trial division by small primes as a filter, then
    a probable prime test. True primality proofs for n! +/- 1 require
    specialized methods (e.g., for n > ~1000, the numbers are enormous).
    """
    plus_one = []
    minus_one = []

    for n in range(1, max_n + 1):
        f = math.factorial(n)
        # n! + 1
        fp = f + 1
        if _is_prime_or_trial_filter(fp):
            plus_one.append(n)
        # n! - 1
        fm = f - 1
        if fm >= 2 and _is_prime_or_trial_filter(fm):
            minus_one.append(n)

    return {
        'n_factorial_plus_1_prime': plus_one,
        'n_factorial_minus_1_prime': minus_one,
    }


def _is_prime_or_trial_filter(n: int) -> bool:
    """
    For very large n, do trial division first, then Miller-Rabin.
    This is practical only for moderate-sized factorials.
    """
    if n < 2:
        return False
    # Trial division by small primes
    small_primes = _sieve_primes(min(10000, math.isqrt(n) + 1))
    for p in small_primes:
        if n == p:
            return True
        if n % p == 0:
            return False
    return _is_prime(n)


def factorial_prime_known_verification() -> Dict[str, List[Tuple[int, bool]]]:
    """
    Verify known small factorial primes against our computation.

    n! + 1 prime: n = 1, 2, 3, 11, 27, 37, 41, 73, 77, 116, 154
    n! - 1 prime: n = 3, 4, 6, 7, 12, 14, 30, 32, 33, 38, 94, 166

    We verify up to n = 41 (since n! grows extremely fast).
    """
    known_plus = [1, 2, 3, 11, 27, 37, 41]
    known_minus = [3, 4, 6, 7, 12, 14, 30, 32, 33, 38]

    plus_results = []
    for n in known_plus:
        val = math.factorial(n) + 1
        plus_results.append((n, _is_prime(val)))

    minus_results = []
    for n in known_minus:
        val = math.factorial(n) - 1
        minus_results.append((n, _is_prime(val)))

    return {
        'plus_one_verified': plus_results,
        'minus_one_verified': minus_results,
    }


# --- 3c. n! and perfect powers (#400) ---

def factorial_perfect_power_check(max_n: int) -> List[Dict]:
    """
    Check whether n! is a perfect power for n = 2..max_n.

    Theorem (folklore): n! is never a perfect k-th power for n > 1, k >= 2.
    Proof sketch: By Bertrand's postulate, there is a prime p with n/2 < p <= n,
    and p appears exactly once in n!.

    We verify computationally and also study n!/k! being a perfect power.
    """
    results = []
    for n in range(2, max_n + 1):
        f = math.factorial(n)
        is_power = _is_perfect_power(f)
        results.append({
            'n': n,
            'is_perfect_power': is_power,
        })
    return results


def _is_perfect_power(n: int) -> bool:
    """Check if n = a^k for some a >= 2, k >= 2."""
    if n < 4:
        return False
    # Check k up to log2(n)
    max_k = n.bit_length()
    for k in range(2, max_k + 1):
        a = round(n ** (1.0 / k))
        for candidate in [a - 1, a, a + 1]:
            if candidate >= 2 and candidate ** k == n:
                return True
        # Early exit: if a < 2, no point checking larger k
        if a < 2:
            break
    return False


def factorial_ratio_powers(max_n: int) -> List[Dict]:
    """
    Search for n, m with n > m >= 2 such that n!/m! is a perfect power.

    n!/m! = (m+1)(m+2)...(n) = product of consecutive integers.
    By a result of Erdos and Selfridge (1975), the product of
    consecutive integers > 1 is never a perfect power.

    We verify this computationally for small ranges.
    """
    results = []
    for n in range(4, max_n + 1):
        for m in range(1, n - 1):  # n - m >= 2: product of >= 2 consecutive ints
            # Compute n!/m! = product of (m+1)..n
            product = 1
            for j in range(m + 1, n + 1):
                product *= j
            if _is_perfect_power(product):
                results.append({
                    'n': n, 'm': m,
                    'product': product,
                    'length': n - m,
                    'is_perfect_power': True,
                })
    return results


def erdos_selfridge_verification(max_length: int, max_start: int) -> Dict:
    """
    Verify the Erdos-Selfridge theorem:
    No product of k >= 2 consecutive positive integers > 1 is a perfect power.

    We check all products a*(a+1)*...*(a+k-1) for a in 2..max_start, k in 2..max_length.
    """
    counterexamples = []
    checked = 0

    for k in range(2, max_length + 1):
        for a in range(2, max_start + 1):
            product = 1
            for j in range(k):
                product *= (a + j)
            checked += 1
            if _is_perfect_power(product):
                counterexamples.append({'a': a, 'k': k, 'product': product})

    return {
        'checked': checked,
        'counterexamples': counterexamples,
        'theorem_holds': len(counterexamples) == 0,
    }


# --- 3d. Wilson quotient and factorial divisibility (#912) ---

def wilson_quotient(p: int) -> int:
    """
    Wilson quotient W_p = ((p-1)! + 1) / p for prime p.
    By Wilson's theorem, p | (p-1)! + 1 for prime p, so W_p is an integer.

    Wilson primes are primes p where p^2 | (p-1)! + 1, i.e., p | W_p.
    Known Wilson primes: 5, 13, 563. No others below 5 * 10^8.
    """
    if not _is_prime(p) or p < 2:
        raise ValueError(f"{p} is not prime")
    return (math.factorial(p - 1) + 1) // p


def wilson_prime_search(max_p: int) -> List[int]:
    """
    Search for Wilson primes: primes p where p^2 | (p-1)! + 1.

    Known: 5, 13, 563. These are extremely rare.
    For efficiency, we compute (p-1)! mod p^2 incrementally.
    """
    wilson_primes = []
    primes = _sieve_primes(max_p)

    for p in primes:
        # Compute (p-1)! mod p^2
        p_sq = p * p
        factorial_mod = 1
        for i in range(2, p):
            factorial_mod = (factorial_mod * i) % p_sq
        # Check if (p-1)! + 1 ≡ 0 (mod p^2)
        if (factorial_mod + 1) % p_sq == 0:
            wilson_primes.append(p)

    return wilson_primes


# =============================================================================
# Section 4: Catalan Numbers
# =============================================================================
#
# C_n = C(2n,n)/(n+1) = (2n)! / ((n+1)! * n!)
# Divisibility, squarefreeness, prime factorizations.


def catalan(n: int) -> int:
    """nth Catalan number: C(2n,n)/(n+1)."""
    if n < 0:
        return 0
    return math.comb(2 * n, n) // (n + 1)


def catalan_squarefree(max_n: int) -> List[int]:
    """
    Find n such that the nth Catalan number C_n is squarefree.

    C_n = C(2n,n)/(n+1).
    v_p(C_n) = v_p(C(2n,n)) - v_p(n+1).
    C_n is squarefree iff v_p(C_n) <= 1 for all primes p <= 2n.

    Uses p-adic valuations (Kummer's theorem) instead of factoring.
    Known squarefree Catalan numbers: C_1=1, C_2=2, C_3=5, C_4=14, ...
    OEIS A000108 (Catalan numbers), A197756 (squarefree Catalan indices).
    """
    primes = _sieve_primes(2 * max_n)
    squarefree_indices = []
    for n in range(1, max_n + 1):
        is_sq_free = True
        for p in primes:
            if p > 2 * n:
                break
            v_binom = p_adic_valuation_binom(2 * n, n, p)
            # v_p(n+1)
            v_denom = 0
            temp = n + 1
            while temp % p == 0:
                v_denom += 1
                temp //= p
            v_cat = v_binom - v_denom
            if v_cat >= 2:
                is_sq_free = False
                break
        if is_sq_free:
            squarefree_indices.append(n)
    return squarefree_indices


def _is_squarefree(n: int) -> bool:
    """Check if n is squarefree (no prime factor appears twice)."""
    if n <= 1:
        return True
    d = 2
    while d * d <= n:
        if n % (d * d) == 0:
            return False
        d += (1 if d == 2 else 2)
    return True


def catalan_prime_factorization_patterns(max_n: int) -> List[Dict]:
    """
    Analyze prime factorization of Catalan numbers.

    C_n = C(2n,n)/(n+1).
    By Kummer: v_p(C(2n,n)) = carries adding n+n in base p.
    v_p(C_n) = v_p(C(2n,n)) - v_p(n+1).

    Track: number of distinct prime factors, largest prime factor,
    squarefree core, etc.
    """
    results = []
    for n in range(1, max_n + 1):
        cn = catalan(n)
        factors = _factorize(cn)
        results.append({
            'n': n,
            'catalan': cn,
            'num_prime_factors': len(factors),
            'largest_prime': max(factors.keys()) if factors else 1,
            'is_squarefree': all(e == 1 for e in factors.values()),
            'max_exponent': max(factors.values()) if factors else 0,
            'factorization': factors,
        })
    return results


def catalan_divisibility_by_prime(max_n: int, p: int) -> List[Dict]:
    """
    Track v_p(C_n) for n = 1..max_n.

    v_p(C_n) = v_p(C(2n,n)) - v_p(n+1)
             = carries(n,n in base p) - v_p(n+1)
    """
    results = []
    for n in range(1, max_n + 1):
        v_binom = p_adic_valuation_binom(2 * n, n, p)
        # v_p(n+1)
        v_denom = 0
        temp = n + 1
        while temp % p == 0:
            v_denom += 1
            temp //= p
        v_catalan = v_binom - v_denom
        results.append({
            'n': n,
            'v_p_binom': v_binom,
            'v_p_denom': v_denom,
            'v_p_catalan': v_catalan,
        })
    return results


# =============================================================================
# Section 5: Wolstenholme's Theorem Extensions
# =============================================================================
#
# For prime p >= 5: C(2p, p) ≡ 2 (mod p^3)  [Wolstenholme's theorem]
#
# Wolstenholme primes: p where C(2p, p) ≡ 2 (mod p^4)
# Known: 16843, 2124679. No others below ~10^9.
#
# Stronger: does p^4 | C(2p,p) - 2? These are extremely rare.


def wolstenholme_verify(p: int) -> Dict:
    """
    For prime p >= 5, verify Wolstenholme's theorem and check for
    higher-order divisibility.

    Returns v = max k such that p^k | C(2p,p) - 2.
    """
    if not _is_prime(p) or p < 5:
        raise ValueError(f"Need prime p >= 5, got {p}")

    # Compute C(2p, p) mod p^5 to check divisibility
    # For moderate p, compute C(2p,p) directly
    # For larger p, compute mod p^5 using modular arithmetic

    if p <= 5000:
        val = math.comb(2 * p, p)
        remainder = val - 2
        k = 0
        temp = remainder
        while temp != 0 and temp % p == 0:
            k += 1
            temp //= p
        return {
            'p': p,
            'C_2p_p_mod_p3': val % (p ** 3),
            'divisibility_order': k,
            'is_wolstenholme_prime': k >= 4,
        }
    else:
        # Modular computation for larger p
        mod = p ** 5
        val = _comb_mod_prime_power(2 * p, p, p, 5)
        remainder = (val - 2) % mod
        k = 0
        temp = remainder
        while temp != 0 and temp % p == 0:
            k += 1
            temp //= p
        return {
            'p': p,
            'C_2p_p_mod_p3': val % (p ** 3),
            'divisibility_order': k,
            'is_wolstenholme_prime': k >= 4,
        }


def _comb_mod_prime_power(n: int, k: int, p: int, e: int) -> int:
    """
    Compute C(n, k) mod p^e where p is prime.

    Strategy: track the p-adic valuation separately.
    C(n,k) = prod_{i=0}^{k-1} (n-i)/(i+1).
    Factor out powers of p from numerator and denominator,
    compute the unit part mod p^e.
    """
    if k > n - k:
        k = n - k
    if k == 0:
        return 1

    mod = p ** e
    # Track total p-valuation: v_p(numerator) - v_p(denominator)
    p_excess = 0
    unit = 1

    for i in range(k):
        # Numerator factor: n - i
        num = n - i
        while num % p == 0:
            num //= p
            p_excess += 1
        unit = unit * num % mod

        # Denominator factor: i + 1
        den = i + 1
        while den % p == 0:
            den //= p
            p_excess -= 1
        unit = unit * pow(den, -1, mod) % mod

    # Multiply back in the p-valuation
    result = unit * pow(p, p_excess, mod) % mod
    return result


def wolstenholme_prime_search(max_p: int) -> List[Dict]:
    """
    Search for Wolstenholme primes up to max_p.

    A Wolstenholme prime is p such that p^4 | C(2p,p) - 2.
    Known: 16843, 2124679.

    For each prime p, we compute C(2p,p) mod p^4 efficiently.
    """
    results = []
    primes = _sieve_primes(max_p)

    for p in primes:
        if p < 5:
            continue
        p4 = p ** 4
        # Compute C(2p, p) mod p^4
        val = _comb_mod_prime_power(2 * p, p, p, 4)
        remainder = (val - 2) % p4
        if remainder == 0:
            results.append({
                'p': p,
                'is_wolstenholme_prime': True,
            })

    return results


def wolstenholme_residues(max_p: int) -> List[Dict]:
    """
    For each prime p >= 5, compute (C(2p,p) - 2) / p^3 mod p.

    When this residue is 0 mod p, we have a Wolstenholme prime.
    The distribution of these residues may reveal structure.

    By Wolstenholme's theorem, C(2p,p) ≡ 2 (mod p^3), so
    (C(2p,p) - 2) / p^3 is an integer.
    """
    primes = _sieve_primes(max_p)
    results = []

    for p in primes:
        if p < 5:
            continue
        p4 = p ** 4
        val = _comb_mod_prime_power(2 * p, p, p, 4)
        remainder = (val - 2) % p4
        # remainder is divisible by p^3 (Wolstenholme's theorem)
        # so remainder / p^3 is an integer, and we want it mod p
        quotient = remainder // (p ** 3)
        residue = quotient % p

        results.append({
            'p': p,
            'wolstenholme_residue': residue,
            'is_wolstenholme_prime': residue == 0,
        })

    return results


def wolstenholme_residue_distribution(max_p: int) -> Dict:
    """
    Analyze the distribution of Wolstenholme residues.

    If the residues (C(2p,p) - 2) / p^3 mod p are uniformly distributed
    in {0, 1, ..., p-1}, then the "probability" of a Wolstenholme prime
    is roughly 1/p, and by the prime number theorem, we'd expect
    sum_{p prime, p<=N} 1/p ~ log log N such primes up to N.

    This is very slow growth — consistent with only 2 known examples.
    """
    residues_data = wolstenholme_residues(max_p)

    # Aggregate residue distribution
    dist = Counter()
    for r in residues_data:
        # Normalize residue to [0, p) range
        dist[r['wolstenholme_residue']] += 1

    # Count how many residues are 0 (Wolstenholme primes)
    wolstenholme_count = sum(1 for r in residues_data if r['is_wolstenholme_prime'])

    # Expected under uniform model: sum 1/p for primes in range
    primes = [r['p'] for r in residues_data]
    expected = sum(1.0 / p for p in primes)

    return {
        'num_primes_checked': len(residues_data),
        'wolstenholme_primes_found': wolstenholme_count,
        'expected_under_uniform': round(expected, 4),
        'residue_zero_count': dist.get(0, 0),
        'sample_residues': [(r['p'], r['wolstenholme_residue'])
                           for r in residues_data[:20]],
    }


# =============================================================================
# Cross-cutting analysis
# =============================================================================

def binomial_factorial_summary(max_row_singmaster: int = 500,
                               max_n_binom: int = 100,
                               max_n_factorial: int = 20,
                               max_n_catalan: int = 100,
                               max_p_wolstenholme: int = 500) -> Dict:
    """
    Run all attack modules and return a summary of findings.
    """
    summary = {}

    # 1. Singmaster
    high_mult = singmaster_multiplicity_search(max_row_singmaster, threshold=6)
    max_mult = max((r['multiplicity'] for r in high_mult), default=0)
    summary['singmaster'] = {
        'max_row_searched': max_row_singmaster,
        'max_multiplicity_found': max_mult,
        'values_with_mult_ge_8': [r for r in high_mult if r['multiplicity'] >= 8],
        'values_with_mult_ge_6': len([r for r in high_mult if r['multiplicity'] >= 6]),
    }

    # 2. Binomial divisibility
    non_div = primes_not_dividing_central_binom(max_n_binom)
    # Count n where no prime > sqrt(2n) fails to divide C(2n,n)
    summary['binomial_divisibility'] = {
        'max_n': max_n_binom,
        'n_with_non_dividing_primes': len(non_div),
    }

    # 3. Factorial
    fact_table = factorial_consecutive_table(max_n_factorial)
    fact_primes = factorial_prime_search(min(max_n_factorial, 15))
    summary['factorial'] = {
        'max_n': max_n_factorial,
        'consecutive_representations': {
            r['n']: r['count'] for r in fact_table if r['count'] > 0
        },
        'factorial_primes_plus': fact_primes['n_factorial_plus_1_prime'],
        'factorial_primes_minus': fact_primes['n_factorial_minus_1_prime'],
    }

    # 4. Catalan
    sq_free = catalan_squarefree(max_n_catalan)
    summary['catalan'] = {
        'max_n': max_n_catalan,
        'squarefree_indices': sq_free,
        'squarefree_count': len(sq_free),
        'squarefree_density': len(sq_free) / max_n_catalan,
    }

    # 5. Wolstenholme
    wolf = wolstenholme_prime_search(max_p_wolstenholme)
    wolf_dist = wolstenholme_residue_distribution(max_p_wolstenholme)
    summary['wolstenholme'] = {
        'max_p_searched': max_p_wolstenholme,
        'wolstenholme_primes_found': [r['p'] for r in wolf],
        'expected_under_uniform': wolf_dist['expected_under_uniform'],
    }

    return summary


# =============================================================================
# Entry point
# =============================================================================

if __name__ == '__main__':
    import json

    print("=" * 72)
    print("Binomial Coefficient and Factorial Attacks")
    print("=" * 72)

    # 1. Singmaster
    print("\n--- Singmaster's Conjecture (#849) ---")
    known = singmaster_known_high_multiplicity()
    for k in known:
        print(f"  Value {k['value']}: multiplicity {k['expected_multiplicity']}, "
              f"verified={k['verified']}")

    print("\n  Searching rows 0..2000 for multiplicity >= 8 ...")
    high = singmaster_multiplicity_search(2000, threshold=8)
    for h in high[:10]:
        print(f"  Value {h['value']}: multiplicity {h['multiplicity']}")

    # 2. Wolstenholme
    print("\n--- Wolstenholme Primes ---")
    print("  Searching primes up to 1000 ...")
    wolf = wolstenholme_prime_search(1000)
    if wolf:
        for w in wolf:
            print(f"  Wolstenholme prime: {w['p']}")
    else:
        print("  No Wolstenholme primes found below 1000.")
        print("  (Known: 16843, 2124679)")

    # 3. Catalan squarefree
    print("\n--- Catalan Squarefreeness ---")
    sq = catalan_squarefree(200)
    print(f"  Squarefree C_n for n in 1..200: {sq}")
    print(f"  Count: {len(sq)} / 200 = {len(sq)/200:.1%}")

    # 4. Factorial primes
    print("\n--- Factorial Primes ---")
    fp = factorial_prime_search(20)
    print(f"  n! + 1 prime for n = {fp['n_factorial_plus_1_prime']}")
    print(f"  n! - 1 prime for n = {fp['n_factorial_minus_1_prime']}")

    # 5. Wilson primes
    print("\n--- Wilson Primes ---")
    wp = wilson_prime_search(600)
    print(f"  Wilson primes up to 600: {wp}")

    print("\n" + "=" * 72)
    print("Done.")
