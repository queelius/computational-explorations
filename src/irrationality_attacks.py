#!/usr/bin/env python3
"""
Irrationality & Polynomial Attacks — Computational Number Theory

Target problems from the Erdos database:
  Irrationality (14 open): #68, #247, #249, #251, #252, #257, #258, #260,
                            #263, #264, #265, #267, #269, #1049
  Polynomials   (11 open): #114, #119, #521, #522, #524, #1131, #1132,
                            #1133, #1150, #1151, #1152

Techniques:
  1. Liouville-Roth irrationality measures via rational approximation search
  2. Lacunary series irrationality (PSLQ for algebraic relations)
  3. Littlewood polynomials (real root counts, root density near unit circle)
  4. Continued fraction analysis (bounded partial quotients, pattern detection)
  5. Erdos-Borwein constant E = sum 1/(2^n - 1) algebraic relation search
"""

import math
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import mpmath
from mpmath import mp, mpf, pi, euler, e, log, zeta, floor

# ---------------------------------------------------------------------------
# 0. Precision settings and helpers
# ---------------------------------------------------------------------------

# Module-level precision — callers may raise for individual computations
_DEFAULT_DPS = 100


def _with_dps(dps: int):
    """Context manager for temporary precision."""
    return mpmath.workdps(dps)


def _cf_expand(alpha, num_terms: int, dps: int) -> List[int]:
    """
    Compute the simple continued fraction expansion [a0; a1, a2, ...]
    of alpha using the standard floor-reciprocal algorithm.

    To get `num_terms` reliable terms, we need roughly `num_terms / 3`
    decimal digits of precision (for typical constants).  This function
    sets the internal working precision to max(dps, num_terms) to
    ensure the output is trustworthy.

    `alpha` may be an mpf or a callable that returns an mpf (computed
    fresh at the current mp.dps).  Callables are preferred for getting
    many CF terms, since a pre-computed mpf at lower precision limits
    the reliable term count.
    """
    # We need at least num_terms/3 digits, but also at least the
    # caller's stated dps.  Using max(dps, num_terms) is safe.
    internal_dps = max(dps, num_terms) + 20
    with _with_dps(internal_dps):
        if callable(alpha):
            x = alpha()
        else:
            x = +mpf(alpha)
        terms = []
        for _ in range(num_terms):
            a = int(floor(x))
            terms.append(a)
            frac = x - a
            if frac < mpf(10) ** (-(internal_dps - 10)):
                break
            x = mpf(1) / frac
    return terms


# ---------------------------------------------------------------------------
# 1. Liouville-Roth irrationality measures
# ---------------------------------------------------------------------------
# For an irrational alpha, the irrationality measure mu(alpha) is the
# infimum of mu such that |alpha - p/q| > 1/q^mu for all but finitely
# many p/q.  By Roth's theorem, mu(alpha) = 2 for all algebraic irrationals.
# We estimate mu computationally by finding best rational approximations
# from continued fractions and measuring the empirical exponent.

def irrationality_measure_from_cf(alpha, num_terms: int = 500,
                                  dps: int = _DEFAULT_DPS) -> Dict[str, Any]:
    """
    Estimate the irrationality measure of alpha using its continued
    fraction convergents.

    `alpha` may be an mpf value or a callable returning mpf (preferred
    for high term counts, since the callable is re-evaluated at the
    needed internal precision).

    For each convergent p_k/q_k, compute
        mu_k = -log|alpha - p_k/q_k| / log(q_k)
    and return:
      - 'measures': list of (q_k, mu_k) pairs
      - 'best_mu': the maximum mu_k observed
      - 'running_sup': supremum of mu_k as function of k
      - 'num_terms': how many CF terms were computed
    """
    cf = _cf_expand(alpha, num_terms, dps)

    # For the convergent error computation, get alpha at high precision
    eval_dps = max(dps, num_terms) + 50
    with _with_dps(eval_dps):
        if callable(alpha):
            alpha_hp = alpha()
        else:
            alpha_hp = +mpf(alpha)

        # Reconstruct convergents
        p_prev, p_curr = mpf(1), mpf(cf[0])
        q_prev, q_curr = mpf(0), mpf(1)
        measures = []
        best_mu = mpf(0)
        running_sup = []

        for k in range(1, len(cf)):
            a_k = cf[k]
            p_next = a_k * p_curr + p_prev
            q_next = a_k * q_curr + q_prev

            if q_next > 1:
                err = abs(alpha_hp - p_next / q_next)
                if err > 0:
                    mu_k = -mpmath.log(err) / mpmath.log(q_next)
                    measures.append((int(q_next), float(mu_k)))
                    if mu_k > best_mu:
                        best_mu = mu_k
            running_sup.append(float(best_mu))

            p_prev, p_curr = p_curr, p_next
            q_prev, q_curr = q_curr, q_next

    return {
        "measures": measures,
        "best_mu": float(best_mu),
        "running_sup": running_sup,
        "num_terms": len(cf),
    }


def compute_irrationality_measures(num_terms: int = 500,
                                   dps: int = _DEFAULT_DPS
                                   ) -> Dict[str, Dict[str, Any]]:
    """
    Compute irrationality measure estimates for classical constants.

    Returns dict keyed by constant name, each entry from
    irrationality_measure_from_cf.

    Known theoretical values:
      mu(e) = 2 (proved by Davis 1978)
      mu(pi) = 2 (implied by Roth since pi is transcendental — but
                   currently best unconditional bound is mu(pi) <= 7.103...)
      mu(ln 2) <= 3.57... (Rukhadze 1987, improved by Marcovecchio 2009)
      mu(zeta(3)) = 2 (Rhin-Viola, conditional; unconditional <= 5.513...)
    """
    # Use callables so that each constant is recomputed at whatever
    # internal precision _cf_expand and the convergent evaluator need.
    constants = {
        "e": lambda: +e,
        "pi": lambda: +pi,
        "ln2": lambda: log(2),
        "zeta3": lambda: zeta(3),
        "sqrt2": lambda: mpmath.sqrt(2),
        "golden_ratio": lambda: (1 + mpmath.sqrt(5)) / 2,
        "euler_gamma": lambda: +euler,
    }

    results = {}
    for name, fn in constants.items():
        results[name] = irrationality_measure_from_cf(fn, num_terms, dps)

    return results


# ---------------------------------------------------------------------------
# 2. Lacunary series irrationality via PSLQ
# ---------------------------------------------------------------------------
# Lacunary (gap) series converge very rapidly, making them natural
# candidates for irrationality proofs.  We compute partial sums to
# high precision and search for polynomial relations using PSLQ.

def lacunary_sum_2exp(num_terms: int = 40, dps: int = _DEFAULT_DPS) -> mpf:
    """Compute sum_{n=0}^{N} 1/2^{2^n} (Kempner-like series)."""
    with _with_dps(dps + 20):
        s = mpf(0)
        for n in range(num_terms):
            exponent = mpf(2) ** n
            if exponent > dps * 4:
                break
            s += mpf(1) / (mpf(2) ** exponent)
        return +s  # normalize precision


def lacunary_sum_nn(num_terms: int = 100, dps: int = _DEFAULT_DPS) -> mpf:
    """Compute sum_{n=1}^{N} 1/n^n (Sophomore's dream related)."""
    with _with_dps(dps + 20):
        s = mpf(0)
        for n in range(1, num_terms + 1):
            term = mpf(1) / mpf(n) ** n
            s += term
            if term < mpf(10) ** (-(dps + 10)):
                break
        return +s


def lacunary_sum_fibonacci_recip(num_terms: int = 100,
                                 dps: int = _DEFAULT_DPS) -> mpf:
    """
    Compute sum_{n=1}^{N} 1/F_n where F_n is the n-th Fibonacci number
    (F_1 = F_2 = 1, F_3 = 2, ...).

    This is the reciprocal Fibonacci constant psi ~ 3.35988...
    Proved irrational by Andre-Jeannin (1989), building on Erdos-Graham.
    """
    with _with_dps(dps + 20):
        # Build Fibonacci sequence F_1, F_2, ..., F_N
        fibs = [mpf(1), mpf(1)]
        for _ in range(num_terms - 2):
            fibs.append(fibs[-1] + fibs[-2])
        s = sum(mpf(1) / f for f in fibs[:num_terms])
        return +s


def pslq_algebraic_search(alpha, max_degree: int = 6,
                          dps: int = _DEFAULT_DPS
                          ) -> Optional[Dict[str, Any]]:
    """
    Search for a polynomial relation P(alpha) = 0 with integer
    coefficients, using PSLQ on the vector [1, alpha, alpha^2, ...].

    `alpha` may be an mpf or a callable returning mpf (preferred for
    full precision at the working dps).

    Returns dict with 'degree', 'coefficients', 'residual' if found,
    else None.
    """
    with _with_dps(dps):
        if callable(alpha):
            alpha_hp = alpha()
        else:
            alpha_hp = +mpf(alpha)
        for deg in range(1, max_degree + 1):
            powers = [alpha_hp ** k for k in range(deg + 1)]
            rel = mpmath.pslq(powers, maxcoeff=10 ** 6)
            if rel is not None:
                # A relation [c0, c1, ..., cd] means
                # c0 + c1*alpha + ... + cd*alpha^d = 0.
                # The actual degree is the highest k with c_k != 0.
                max_nonzero = max(
                    (k for k, c in enumerate(rel) if c != 0),
                    default=0,
                )
                if max_nonzero == 0:
                    continue  # trivial: c0 = 0

                residual = sum(c * alpha_hp ** k
                               for k, c in enumerate(rel))
                return {
                    "degree": max_nonzero,
                    "coefficients": list(rel[:max_nonzero + 1]),
                    "residual": float(abs(residual)),
                }
    return None


def pslq_constant_relation(alpha, basis_constants: List,
                           basis_names: List[str],
                           maxcoeff: int = 10000,
                           dps: int = _DEFAULT_DPS
                           ) -> Optional[Dict[str, Any]]:
    """
    Search for an integer relation between alpha and a set of basis
    constants: a_0 * alpha + a_1 * c_1 + ... + a_n * c_n = 0.

    Uses PSLQ on [alpha, c_1, ..., c_n].
    `alpha` and elements of `basis_constants` may be mpf values or
    callables returning mpf.
    """
    def _resolve(v):
        return v() if callable(v) else +mpf(v)

    with _with_dps(dps):
        vec = [_resolve(alpha)] + [_resolve(c) for c in basis_constants]
        rel = mpmath.pslq(vec, maxcoeff=maxcoeff)
        if rel is not None:
            residual = sum(r * v for r, v in zip(rel, vec))
            names = ["alpha"] + list(basis_names)
            return {
                "relation": {n: c for n, c in zip(names, rel) if c != 0},
                "coefficients": list(rel),
                "names": names,
                "residual": float(abs(residual)),
            }
    return None


def analyze_lacunary_series(dps: int = _DEFAULT_DPS) -> Dict[str, Dict]:
    """
    Compute lacunary series to high precision and search for algebraic
    relations (via PSLQ) and relations with standard constants.
    """
    # Callables for basis constants — resolved inside PSLQ at working dps
    basis_constants = [
        lambda: mpf(1), lambda: +pi, lambda: pi ** 2,
        lambda: log(2), lambda: +e, lambda: zeta(3), lambda: +euler,
    ]
    basis_names = ["1", "pi", "pi^2", "ln2", "e", "zeta3", "gamma"]

    series = {
        "kempner_2exp": lacunary_sum_2exp(dps=dps),
        "sophomores_dream": lacunary_sum_nn(dps=dps),
        "fibonacci_reciprocal": lacunary_sum_fibonacci_recip(dps=dps),
    }

    results = {}
    for name, value in series.items():
        algebraic = pslq_algebraic_search(value, max_degree=6, dps=dps)
        constant_rel = pslq_constant_relation(
            value, basis_constants, basis_names, dps=dps
        )
        results[name] = {
            "value": float(value),
            "algebraic_relation": algebraic,
            "constant_relation": constant_rel,
        }

    return results


# ---------------------------------------------------------------------------
# 3. Littlewood polynomials — root structure
# ---------------------------------------------------------------------------
# A Littlewood polynomial has all coefficients in {-1, +1}.
# More generally, we also study {-1, 0, 1} (flat) polynomials.
# Erdos asked about the maximum number of real roots, root distribution
# near the unit circle, etc.

def _eval_poly_real_roots_sturm(coeffs: List[int]) -> int:
    """
    Count real roots of a polynomial with integer coefficients using
    mpmath's polyroots.

    Parameters
    ----------
    coeffs : list of int
        Coefficients [a_0, a_1, ..., a_n] so p(x) = a_0 + a_1*x + ... + a_n*x^n.

    Returns
    -------
    int : number of real roots (counting multiplicity)
    """
    # mpmath.polyroots expects highest degree first
    n = len(coeffs) - 1
    if n <= 0:
        return 0
    mp_coeffs = [mpf(c) for c in reversed(coeffs)]
    with _with_dps(30):
        try:
            roots = mpmath.polyroots(mp_coeffs, maxsteps=200, extraprec=30)
        except mpmath.libmp.libhyper.NoConvergence:
            return -1  # signal failure
    real_count = 0
    for r in roots:
        if abs(mpmath.im(r)) < 1e-10:
            real_count += 1
    return real_count


def littlewood_max_real_roots(degree: int,
                              exhaustive_limit: int = 14
                              ) -> Dict[str, Any]:
    """
    For a given degree, find the maximum number of real roots among
    all Littlewood polynomials (coefficients in {-1, +1}).

    For degree <= exhaustive_limit, enumerate all 2^(degree+1) polynomials.
    For larger degrees, sample randomly.

    Returns dict with 'degree', 'max_real_roots', 'best_poly', 'num_searched'.
    """
    n = degree
    max_real = 0
    best_poly = None
    count = 0

    if n <= exhaustive_limit:
        # Enumerate all: coefficients are +/-1, leading coeff always +1 by symmetry
        for bits in range(2 ** n):
            coeffs = [1]  # a_0 = 1 (or any fixed; by symmetry)
            for i in range(n):
                coeffs.append(1 if (bits >> i) & 1 else -1)
            nreal = _eval_poly_real_roots_sturm(coeffs)
            count += 1
            if nreal > max_real:
                max_real = nreal
                best_poly = list(coeffs)
    else:
        # Random sampling: try a large number of random polynomials
        import random
        rng = random.Random(42 + degree)
        num_samples = min(50000, 2 ** n)
        for _ in range(num_samples):
            coeffs = [rng.choice([-1, 1]) for _ in range(n + 1)]
            nreal = _eval_poly_real_roots_sturm(coeffs)
            count += 1
            if nreal > max_real:
                max_real = nreal
                best_poly = list(coeffs)

    return {
        "degree": n,
        "max_real_roots": max_real,
        "best_poly": best_poly,
        "num_searched": count,
    }


def littlewood_root_density_near_unit_circle(degree: int,
                                             epsilon: float = 0.1,
                                             num_samples: int = 200
                                             ) -> Dict[str, Any]:
    """
    Estimate the fraction of roots of random Littlewood polynomials of
    given degree that lie within distance epsilon of the unit circle.

    Returns dict with statistics.
    """
    import random
    rng = random.Random(123 + degree)

    near_circle_counts = []
    total_root_counts = []

    for _ in range(num_samples):
        coeffs = [rng.choice([-1, 1]) for _ in range(degree + 1)]
        mp_coeffs = [mpf(c) for c in reversed(coeffs)]
        with _with_dps(30):
            try:
                roots = mpmath.polyroots(mp_coeffs, maxsteps=200,
                                         extraprec=30)
            except mpmath.libmp.libhyper.NoConvergence:
                continue

        near = sum(1 for r in roots if abs(abs(r) - 1) < epsilon)
        near_circle_counts.append(near)
        total_root_counts.append(len(roots))

    if not near_circle_counts:
        return {"degree": degree, "epsilon": epsilon, "error": "no convergence"}

    import numpy as np
    ncc = np.array(near_circle_counts, dtype=float)
    trc = np.array(total_root_counts, dtype=float)
    fractions = ncc / np.maximum(trc, 1)

    return {
        "degree": degree,
        "epsilon": epsilon,
        "num_samples": len(near_circle_counts),
        "mean_near_fraction": float(np.mean(fractions)),
        "std_near_fraction": float(np.std(fractions)),
        "mean_near_count": float(np.mean(ncc)),
        "mean_total_roots": float(np.mean(trc)),
    }


def littlewood_real_root_table(min_degree: int = 5,
                               max_degree: int = 16
                               ) -> List[Dict[str, Any]]:
    """
    Build a table of max real roots for Littlewood polynomials,
    degree by degree.

    Known: for degree n, the max number of real roots is O(sqrt(n))
    (Bloch-Polya), with improvements by Kac, Littlewood-Offord.
    """
    table = []
    for d in range(min_degree, max_degree + 1):
        row = littlewood_max_real_roots(d)
        table.append(row)
    return table


def flat_poly_max_real_roots(degree: int,
                             exhaustive_limit: int = 10
                             ) -> Dict[str, Any]:
    """
    Like littlewood_max_real_roots but for flat polynomials with
    coefficients in {-1, 0, 1}.  There are 3^{n+1} such polynomials,
    so exhaustive search is only feasible for small degrees.
    """
    n = degree
    max_real = 0
    best_poly = None
    count = 0

    coeff_map = {0: -1, 1: 0, 2: 1}

    if n <= exhaustive_limit:
        total = 3 ** (n + 1)
        for code in range(total):
            coeffs = []
            c = code
            for _ in range(n + 1):
                coeffs.append(coeff_map[c % 3])
                c //= 3
            # Skip if leading coefficient is 0 (reduces degree)
            if coeffs[-1] == 0:
                continue
            nreal = _eval_poly_real_roots_sturm(coeffs)
            count += 1
            if nreal > max_real:
                max_real = nreal
                best_poly = list(coeffs)
    else:
        import random
        rng = random.Random(99 + degree)
        num_samples = min(50000, 3 ** (n + 1))
        for _ in range(num_samples):
            coeffs = [rng.choice([-1, 0, 1]) for _ in range(n)]
            coeffs.append(rng.choice([-1, 1]))  # leading coeff nonzero
            nreal = _eval_poly_real_roots_sturm(coeffs)
            count += 1
            if nreal > max_real:
                max_real = nreal
                best_poly = list(coeffs)

    return {
        "degree": n,
        "max_real_roots": max_real,
        "best_poly": best_poly,
        "num_searched": count,
    }


# ---------------------------------------------------------------------------
# 4. Continued fraction analysis
# ---------------------------------------------------------------------------
# For constants appearing in our work, compute CF expansions to many
# terms and look for patterns.

def continued_fraction_expansion(alpha, num_terms: int = 1000,
                                 dps: int = _DEFAULT_DPS
                                 ) -> List[int]:
    """
    Compute the continued fraction expansion of alpha to num_terms terms.

    `alpha` may be an mpf value or a callable returning mpf.
    """
    return _cf_expand(alpha, num_terms, dps)


def cf_statistics(cf_terms: List[int]) -> Dict[str, Any]:
    """
    Compute statistics of a continued fraction expansion:
      - max partial quotient
      - mean, median partial quotient
      - frequency distribution of partial quotients
      - Khinchin-Levy statistics
      - bounded partial quotient test (is max bounded?)
      - geometric mean of partial quotients (cf. Khinchin's constant)
    """
    if len(cf_terms) <= 1:
        return {"error": "too few terms"}

    # Skip a_0 (integer part) for statistics on partial quotients
    pq = cf_terms[1:] if len(cf_terms) > 1 else cf_terms
    if not pq:
        return {"error": "no partial quotients"}

    import numpy as np
    # Cap huge partial quotients (from precision exhaustion) to avoid
    # float64 overflow in numpy.
    _CAP = 10 ** 15
    capped = [min(a, _CAP) for a in pq]
    arr = np.array(capped, dtype=float)

    freq = Counter(pq)
    top_10 = freq.most_common(10)

    # Geometric mean -> compare to Khinchin's constant K0 ~ 2.6854520010...
    log_sum = sum(math.log(a) for a in capped if a > 0)
    geo_mean = math.exp(log_sum / len(pq)) if pq else 0

    # Levy's constant: lim (q_n)^{1/n} = e^{pi^2/(12 ln 2)} ~ 3.2758...
    # We can estimate this from the partial quotients
    # log(q_n) ~ sum log(a_k) + n*C where C comes from the CF structure

    return {
        "num_terms": len(pq),
        "max_pq": int(np.max(arr)),
        "mean_pq": float(np.mean(arr)),
        "median_pq": float(np.median(arr)),
        "std_pq": float(np.std(arr)),
        "geometric_mean": geo_mean,
        "khinchin_constant": 2.6854520010653064,  # theoretical value
        "geo_mean_ratio_to_khinchin": geo_mean / 2.6854520010653064,
        "top_10_frequencies": top_10,
        "is_bounded_quotients": int(np.max(arr)) < 100,
    }


def cf_pattern_search(cf_terms: List[int],
                      max_period: int = 50) -> Dict[str, Any]:
    """
    Search for periodicity or quasi-periodicity in partial quotients.

    Returns detected patterns:
      - exact_period: if [a_{n+1}, ...] is eventually periodic
      - approximate_period: best autocorrelation period
      - anomalous_quotients: unusually large partial quotients
    """
    if len(cf_terms) <= 2:
        return {"error": "too few terms"}

    pq = cf_terms[1:]  # skip integer part

    # Search for exact periodicity (quadratic irrationals have periodic CFs)
    exact_period = None
    for period in range(1, min(max_period, len(pq) // 3) + 1):
        # Check if pq[start:] is periodic with this period
        # Try different starting offsets
        for start in range(min(period, len(pq) // 3)):
            is_periodic = True
            checks = 0
            for i in range(start, len(pq) - period):
                if pq[i] != pq[i + period]:
                    is_periodic = False
                    break
                checks += 1
            if is_periodic and checks >= 2 * period:
                exact_period = {
                    "period": period,
                    "start": start,
                    "repeating_block": pq[start:start + period],
                }
                break
        if exact_period:
            break

    # Autocorrelation for approximate periodicity
    import numpy as np
    _CAP = 10 ** 15
    capped = [min(a, _CAP) for a in pq]
    arr = np.array(capped, dtype=float)
    arr_centered = arr - np.mean(arr)
    var = np.var(arr)
    if var > 0 and len(arr) > 2 * max_period:
        autocorr = []
        for lag in range(1, max_period + 1):
            c = np.mean(arr_centered[:-lag] * arr_centered[lag:]) / var
            autocorr.append((lag, float(c)))
        best_lag = max(autocorr, key=lambda x: x[1])
    else:
        autocorr = []
        best_lag = (0, 0.0)

    # Find anomalously large partial quotients
    if len(pq) > 10:
        mean_pq = float(np.mean(arr))
        std_pq = float(np.std(arr))
        threshold = mean_pq + 5 * std_pq if std_pq > 0 else mean_pq * 10
        anomalous = [(i, pq[i]) for i in range(len(pq))
                     if pq[i] > threshold]
    else:
        anomalous = []

    return {
        "exact_period": exact_period,
        "best_autocorrelation_lag": best_lag,
        "autocorrelation_top5": sorted(autocorr, key=lambda x: -x[1])[:5]
        if autocorr else [],
        "anomalous_quotients": anomalous[:20],
    }


def analyze_research_constants_cf(num_terms: int = 1000,
                                  dps: int = _DEFAULT_DPS
                                  ) -> Dict[str, Dict[str, Any]]:
    """
    Compute and analyze continued fraction expansions for constants
    appearing in our Erdos problems research.
    """
    constants = {
        "6/pi^2": lambda: mpf(6) / pi ** 2,
        "log2/log3": lambda: log(2) / log(3),
        "euler_gamma": lambda: +euler,
        "ln2": lambda: log(2),
        "zeta3": lambda: zeta(3),
        "pi": lambda: +pi,
        "e": lambda: +e,
        "sqrt2": lambda: mpmath.sqrt(2),
        "golden_ratio": lambda: (1 + mpmath.sqrt(5)) / 2,
    }

    results = {}
    for name, fn in constants.items():
        cf = continued_fraction_expansion(fn, num_terms, dps)
        stats = cf_statistics(cf)
        patterns = cf_pattern_search(cf)
        results[name] = {
            "cf_first_30": cf[:30],
            "statistics": stats,
            "patterns": patterns,
        }

    return results


# ---------------------------------------------------------------------------
# 5. Erdos-Borwein constant
# ---------------------------------------------------------------------------
# E = sum_{n=1}^{infty} 1/(2^n - 1) = sum_{n=1}^{infty} d(n)/2^n
# where d(n) is the number of divisors of n.
# Proved irrational by Erdos (1948).  Whether it's transcendental is open.
# We search for deeper algebraic or constant-relation structure.

def erdos_borwein_constant(num_terms: int = 200,
                           dps: int = _DEFAULT_DPS) -> mpf:
    """
    Compute E = sum_{n=1}^{N} 1/(2^n - 1) to high precision.

    The series converges geometrically, so 200 terms at 100 digits
    gives far more precision than needed.
    """
    with _with_dps(dps + 20):
        s = mpf(0)
        for n in range(1, num_terms + 1):
            term = mpf(1) / (mpf(2) ** n - 1)
            s += term
            if term < mpf(10) ** (-(dps + 10)):
                break
        return +s


def erdos_borwein_divisor_representation(num_terms: int = 200,
                                         dps: int = _DEFAULT_DPS) -> mpf:
    """
    Compute E via the divisor sum representation:
    E = sum_{n=1}^{infty} d(n) / 2^n

    This is an equivalent form useful for cross-validation.
    """
    with _with_dps(dps + 20):
        s = mpf(0)
        for n in range(1, num_terms + 1):
            d_n = sum(1 for k in range(1, n + 1) if n % k == 0)
            s += mpf(d_n) / mpf(2) ** n
        return +s


def analyze_erdos_borwein(dps: int = _DEFAULT_DPS) -> Dict[str, Any]:
    """
    Comprehensive analysis of the Erdos-Borwein constant:
    - High-precision computation (two independent methods)
    - Algebraic relation search (PSLQ)
    - Continued fraction analysis
    - Relations with standard constants
    """
    E_direct = erdos_borwein_constant(dps=dps)
    E_divisor = erdos_borwein_divisor_representation(
        num_terms=min(200, dps + 50), dps=dps
    )

    # Cross-validation
    agreement = float(abs(E_direct - E_divisor))

    # Algebraic relation search
    algebraic = pslq_algebraic_search(E_direct, max_degree=6, dps=dps)

    # Relations with standard constants (callables for precision)
    basis = [
        lambda: mpf(1), lambda: +pi, lambda: pi ** 2, lambda: log(2),
        lambda: +e, lambda: zeta(2), lambda: zeta(3), lambda: +euler,
    ]
    basis_names = ["1", "pi", "pi^2", "ln2", "e", "zeta2", "zeta3",
                   "gamma"]
    constant_rel = pslq_constant_relation(
        E_direct, basis, basis_names, dps=dps
    )

    # CF analysis
    cf = continued_fraction_expansion(E_direct, num_terms=500, dps=dps)
    cf_stats = cf_statistics(cf)

    return {
        "value": float(E_direct),
        "value_str": mpmath.nstr(E_direct, 50),
        "cross_validation_error": agreement,
        "algebraic_relation": algebraic,
        "constant_relation": constant_rel,
        "cf_first_30": cf[:30],
        "cf_statistics": cf_stats,
    }


# ---------------------------------------------------------------------------
# 6. Aggregate driver
# ---------------------------------------------------------------------------

def run_all_attacks(dps: int = 50, cf_terms: int = 500,
                    max_littlewood_degree: int = 12
                    ) -> Dict[str, Any]:
    """
    Run all irrationality and polynomial attacks.  Lower defaults for
    CI-friendly performance; raise dps and degree for deeper exploration.
    """
    results = {}

    # 1. Irrationality measures
    results["irrationality_measures"] = compute_irrationality_measures(
        num_terms=cf_terms, dps=dps
    )

    # 2. Lacunary series
    results["lacunary_series"] = analyze_lacunary_series(dps=dps)

    # 3. Littlewood polynomials
    results["littlewood_table"] = littlewood_real_root_table(
        min_degree=5, max_degree=max_littlewood_degree
    )

    # 4. CF analysis
    results["cf_analysis"] = analyze_research_constants_cf(
        num_terms=cf_terms, dps=dps
    )

    # 5. Erdos-Borwein
    results["erdos_borwein"] = analyze_erdos_borwein(dps=dps)

    return results


# ---------------------------------------------------------------------------
# 7. Summary printer
# ---------------------------------------------------------------------------

def print_summary(results: Dict[str, Any]) -> None:
    """Print a human-readable summary of all attacks."""

    print("=" * 72)
    print("IRRATIONALITY & POLYNOMIAL ATTACKS — SUMMARY")
    print("=" * 72)

    # Irrationality measures
    if "irrationality_measures" in results:
        print("\n--- 1. Irrationality Measures (Liouville-Roth) ---")
        for name, data in results["irrationality_measures"].items():
            mu = data["best_mu"]
            nt = data["num_terms"]
            print(f"  {name:20s}: best mu = {mu:.4f}  ({nt} CF terms)")

    # Lacunary series
    if "lacunary_series" in results:
        print("\n--- 2. Lacunary Series ---")
        for name, data in results["lacunary_series"].items():
            val = data["value"]
            alg = data["algebraic_relation"]
            crel = data["constant_relation"]
            print(f"  {name:25s}: value = {val:.12f}")
            if alg:
                print(f"    Algebraic relation found: deg {alg['degree']}, "
                      f"coeffs = {alg['coefficients']}")
            else:
                print("    No algebraic relation found (degree <= 6)")
            if crel:
                print(f"    Constant relation: {crel['relation']}")
            else:
                print("    No relation with standard constants found")

    # Littlewood
    if "littlewood_table" in results:
        print("\n--- 3. Littlewood Polynomials: Max Real Roots ---")
        print(f"  {'deg':>4s}  {'max_real':>8s}  {'searched':>10s}")
        for row in results["littlewood_table"]:
            print(f"  {row['degree']:4d}  {row['max_real_roots']:8d}  "
                  f"{row['num_searched']:10d}")

    # CF analysis
    if "cf_analysis" in results:
        print("\n--- 4. Continued Fraction Analysis ---")
        for name, data in results["cf_analysis"].items():
            stats = data["statistics"]
            pats = data["patterns"]
            gm = stats.get("geometric_mean", 0)
            mx = stats.get("max_pq", 0)
            ep = pats.get("exact_period")
            print(f"  {name:20s}: geo_mean={gm:.4f}, max_pq={mx}, "
                  f"periodic={'YES (period ' + str(ep['period']) + ')' if ep else 'no'}")

    # Erdos-Borwein
    if "erdos_borwein" in results:
        print("\n--- 5. Erdos-Borwein Constant ---")
        eb = results["erdos_borwein"]
        print(f"  E = {eb['value']:.15f}")
        print(f"  Cross-validation error: {eb['cross_validation_error']:.2e}")
        if eb["algebraic_relation"]:
            print(f"  Algebraic relation: {eb['algebraic_relation']}")
        else:
            print("  No algebraic relation found (degree <= 6)")
        if eb["constant_relation"]:
            print(f"  Constant relation: {eb['constant_relation']['relation']}")
        else:
            print("  No relation with standard constants found")

    print("\n" + "=" * 72)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = run_all_attacks(dps=50, cf_terms=300, max_littlewood_degree=12)
    print_summary(results)
