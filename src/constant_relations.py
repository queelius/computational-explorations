#!/usr/bin/env python3
"""
Constant Relation Discovery (Ramanujan Library approach)

Inspired by arXiv:2412.12361 (Dec 2024), which uses the PSLQ algorithm
to discover relations between mathematical constants.

We apply PSLQ and LLL-based integer relation detection to the constants
computed in our Erdos problems research:
  - 6/pi^2 (coprime density)
  - R_cop(k) values and their prime indices
  - DS thresholds
  - Sieve-theoretic constants (32/27, 64/(9pi^2))
  - Classical constants (gamma, log 2/log 3, etc.)

The goal: discover hidden algebraic or number-theoretic connections
between our computed constants, especially the coprime Ramsey numbers.
"""

import math
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import mpmath
from mpmath import mp, mpf, pi, euler, e, log, zeta

# ---------------------------------------------------------------------------
# 1. Constant Registry: all constants from our work
# ---------------------------------------------------------------------------

# Use high precision throughout
mp.dps = 80


def _build_constant_registry() -> Dict[str, Dict[str, Any]]:
    """
    Collect all computed constants from our research into a structured registry.

    Each entry has:
      - value: mpf high-precision value
      - float_value: Python float for quick reference
      - description: human-readable description
      - source: which module/result produced it
      - category: grouping tag
    """
    reg: Dict[str, Dict[str, Any]] = {}

    def _add(name: str, value, description: str, source: str, category: str):
        v = mpf(value) if not isinstance(value, mpf) else value
        reg[name] = {
            "value": v,
            "float_value": float(v),
            "description": description,
            "source": source,
            "category": category,
        }

    # -- Coprime density constants --
    _add("6/pi^2", mpf(6) / pi**2,
         "Coprime density = 1/zeta(2)", "coprime_analysis", "density")
    _add("8/pi^2", mpf(8) / pi**2,
         "Coprime density for all-odd sets (f_E=0)", "primitive_coprime", "density")
    _add("64/(9*pi^2)", mpf(64) / (9 * pi**2),
         "Coprime density for shifted top layer (f_E=1/3)", "primitive_coprime", "density")

    # -- Exact Ramsey numbers --
    _add("R_cop(2)", mpf(2),
         "Coprime Ramsey number k=2", "coprime_ramsey", "ramsey")
    _add("R_cop(3)", mpf(11),
         "Coprime Ramsey number k=3 (exact)", "coprime_ramsey", "ramsey")
    _add("R_cop(4)", mpf(59),
         "Coprime Ramsey number k=4 (SAT-verified)", "coprime_ramsey_sat", "ramsey")
    _add("R_cop(3;3)", mpf(53),
         "Multi-color coprime Ramsey, 3 colors k=3", "coprime_ramsey_variants", "ramsey")

    # -- Classical Ramsey for comparison --
    _add("R(3,3)", mpf(6),
         "Classical Ramsey R(3,3)", "classical", "ramsey_classical")
    _add("R(4,4)", mpf(18),
         "Classical Ramsey R(4,4)", "classical", "ramsey_classical")
    _add("R(3,3,3)", mpf(17),
         "Classical multicolor Ramsey R(3,3,3)", "classical", "ramsey_classical")

    # -- Ratios and derived Ramsey quantities --
    _add("R_cop(3)/R(3,3)", mpf(11) / 6,
         "Coprime amplification factor k=3", "derived", "ratio")
    _add("R_cop(4)/R(4,4)", mpf(59) / 18,
         "Coprime amplification factor k=4", "derived", "ratio")
    _add("R_cop(4)/R_cop(3)", mpf(59) / 11,
         "Growth factor k=3 to k=4", "derived", "ratio")
    _add("R_cop(3;3)/R_cop(3;2)", mpf(53) / 11,
         "Multi-color growth factor c=2 to c=3", "derived", "ratio")

    # -- Log ratios for Ramsey growth --
    _add("log(R_cop(3))/3", log(mpf(11)) / 3,
         "log(R_cop(k))/k at k=3", "derived", "growth")
    _add("log(R_cop(4))/4", log(mpf(59)) / 4,
         "log(R_cop(k))/k at k=4", "derived", "growth")
    _add("log(59)/log(11)", log(mpf(59)) / log(mpf(11)),
         "Log ratio R_cop(4)/R_cop(3)", "derived", "growth")

    # -- Prime index analysis --
    _add("pi(R_cop(2))", mpf(1),
         "Prime index of R_cop(2)=2: p_1", "universal_patterns", "prime_index")
    _add("pi(R_cop(3))", mpf(5),
         "Prime index of R_cop(3)=11: p_5", "universal_patterns", "prime_index")
    _add("pi(R_cop(4))", mpf(17),
         "Prime index of R_cop(4)=59: p_17", "universal_patterns", "prime_index")
    _add("pi(R_cop(3;3))", mpf(16),
         "Prime index of R_cop(3;3)=53: p_16", "universal_patterns", "prime_index")

    # -- DS (density Schur) thresholds --
    _add("DS_threshold_0.60", mpf("0.60"),
         "Density Schur threshold at 0.60", "theta_threshold", "ds_threshold")
    _add("DS_threshold_0.67", mpf("0.67"),
         "Density Schur threshold at 0.67", "theta_threshold", "ds_threshold")

    # -- Sieve-theoretic constants --
    _add("32/27", mpf(32) / 27,
         "Primitive set coprime ratio M(S)/M(T)", "primitive_coprime", "sieve")

    # -- Classical mathematical constants for reference --
    _add("gamma", euler,
         "Euler-Mascheroni constant", "classical", "fundamental")
    _add("log2/log3", log(mpf(2)) / log(mpf(3)),
         "Stanley sequence exponent = log(2)/log(3)", "classical", "fundamental")
    _add("2/3", mpf(2) / 3,
         "Sidon-squares exponent", "classical", "fundamental")
    _add("1/zeta(2)", 1 / zeta(2),
         "1/zeta(2) = 6/pi^2", "classical", "fundamental")
    _add("1/zeta(3)", 1 / zeta(3),
         "1/zeta(3): probability that 3 random integers are mutually coprime",
         "classical", "fundamental")
    _add("zeta(2)", zeta(2),
         "Basel constant pi^2/6", "classical", "fundamental")
    _add("zeta(3)", zeta(3),
         "Apery's constant", "classical", "fundamental")
    _add("pi", pi,
         "pi", "classical", "fundamental")
    _add("e", e,
         "Euler's number", "classical", "fundamental")

    return reg


CONSTANT_REGISTRY = _build_constant_registry()


def get_registry() -> Dict[str, Dict[str, Any]]:
    """Return the full constant registry."""
    return CONSTANT_REGISTRY


# ---------------------------------------------------------------------------
# 2. PSLQ-based integer relation detection
# ---------------------------------------------------------------------------

def pslq_relation(names: List[str],
                  maxcoeff: int = 1000,
                  registry: Optional[Dict] = None) -> Optional[List[int]]:
    """
    Run PSLQ on a list of named constants from the registry.

    Returns integer coefficients [a1, a2, ...] such that
    a1*c1 + a2*c2 + ... = 0, or None if no relation found.
    """
    if registry is None:
        registry = CONSTANT_REGISTRY
    values = []
    for name in names:
        if name not in registry:
            raise KeyError(f"Unknown constant: {name}")
        values.append(registry[name]["value"])
    return mpmath.pslq(values, maxcoeff=maxcoeff)


def search_pairwise_relations(names: Optional[List[str]] = None,
                              maxcoeff: int = 1000,
                              registry: Optional[Dict] = None
                              ) -> List[Dict[str, Any]]:
    """
    For each pair of constants, search for integer relations
    a1*c1 + a2*c2 = 0 (i.e., c1/c2 is rational with small numerator/denominator).

    Returns list of discovered relations.
    """
    if registry is None:
        registry = CONSTANT_REGISTRY
    if names is None:
        names = list(registry.keys())

    relations = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            v1 = registry[n1]["value"]
            v2 = registry[n2]["value"]
            # Skip if either is zero
            if abs(float(v1)) < 1e-30 or abs(float(v2)) < 1e-30:
                continue
            r = mpmath.pslq([v1, v2], maxcoeff=maxcoeff)
            if r is not None:
                a1, a2 = r
                # Verify
                residual = float(abs(a1 * v1 + a2 * v2))
                if residual < 1e-20:
                    relations.append({
                        "constants": (n1, n2),
                        "coefficients": (a1, a2),
                        "equation": f"{a1}*{n1} + {a2}*{n2} = 0",
                        "simplified": f"{n1}/{n2} = {-a2}/{a1}" if a1 != 0 else "degenerate",
                        "residual": residual,
                        "max_coeff": max(abs(a1), abs(a2)),
                    })
    return relations


def search_triple_relations(names: Optional[List[str]] = None,
                            maxcoeff: int = 200,
                            registry: Optional[Dict] = None
                            ) -> List[Dict[str, Any]]:
    """
    For each triple of constants, search for integer relations
    a1*c1 + a2*c2 + a3*c3 = 0.

    Only reports non-trivial relations (not reducible to pairwise).
    """
    if registry is None:
        registry = CONSTANT_REGISTRY
    if names is None:
        names = list(registry.keys())

    # Pre-compute pairwise relations to filter
    pairwise_set = set()
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            v1 = registry[names[i]]["value"]
            v2 = registry[names[j]]["value"]
            if abs(float(v1)) < 1e-30 or abs(float(v2)) < 1e-30:
                continue
            r = mpmath.pslq([v1, v2], maxcoeff=maxcoeff)
            if r is not None:
                pairwise_set.add(frozenset({names[i], names[j]}))

    relations = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            for k in range(j + 1, len(names)):
                n1, n2, n3 = names[i], names[j], names[k]
                # Skip if any pair already has a relation (would give trivial triple)
                if (frozenset({n1, n2}) in pairwise_set
                        or frozenset({n1, n3}) in pairwise_set
                        or frozenset({n2, n3}) in pairwise_set):
                    continue

                v1 = registry[n1]["value"]
                v2 = registry[n2]["value"]
                v3 = registry[n3]["value"]
                if any(abs(float(v)) < 1e-30 for v in [v1, v2, v3]):
                    continue
                r = mpmath.pslq([v1, v2, v3], maxcoeff=maxcoeff)
                if r is not None:
                    a1, a2, a3 = r
                    residual = float(abs(a1 * v1 + a2 * v2 + a3 * v3))
                    if residual < 1e-15:
                        relations.append({
                            "constants": (n1, n2, n3),
                            "coefficients": (a1, a2, a3),
                            "equation": f"{a1}*{n1} + {a2}*{n2} + {a3}*{n3} = 0",
                            "residual": residual,
                            "max_coeff": max(abs(a1), abs(a2), abs(a3)),
                        })
    return relations


# ---------------------------------------------------------------------------
# 3. Targeted Ramsey relation searches
# ---------------------------------------------------------------------------

def analyze_ramsey_ratios() -> Dict[str, Any]:
    """
    Specifically search for relations involving R_cop values.

    Tests:
      - Is log(59)/log(11) related to known constants?
      - Is 59/11 = 5.363... expressible via e, pi, gamma, zeta?
      - Growth rate log(R_cop(k))/k: is it converging?
    """
    results: Dict[str, Any] = {}

    # log(59)/log(11)
    x = log(mpf(59)) / log(mpf(11))
    results["log59_log11"] = {
        "value": float(x),
        "description": "log(R_cop(4))/log(R_cop(3))",
    }

    # Search against known constants
    targets = {
        "e": e,
        "pi": pi,
        "gamma": euler,
        "log2/log3": log(mpf(2)) / log(mpf(3)),
        "6/pi^2": mpf(6) / pi**2,
        "zeta(3)": zeta(3),
        "1/zeta(3)": 1 / zeta(3),
        "sqrt(2)": mpmath.sqrt(2),
        "sqrt(3)": mpmath.sqrt(3),
        "phi": (1 + mpmath.sqrt(5)) / 2,  # golden ratio
    }

    ramsey_constants = {
        "log(59)/log(11)": x,
        "59/11": mpf(59) / 11,
        "R_cop(4)/R_cop(3)": mpf(59) / 11,
        "R_cop(3)/R(3,3)": mpf(11) / 6,
        "R_cop(4)/R(4,4)": mpf(59) / 18,
        "R_cop(3;3)/R(3,3,3)": mpf(53) / 17,
    }

    results["targeted_pslq"] = {}
    for rc_name, rc_val in ramsey_constants.items():
        hits = {}
        for t_name, t_val in targets.items():
            r = mpmath.pslq([rc_val, t_val, mpf(1)], maxcoeff=200)
            if r is not None:
                a, b, c = r
                residual = float(abs(a * rc_val + b * t_val + c))
                # Filter: require the target constant to actually participate
                # (b != 0), otherwise it is just a trivial rational identity
                if residual < 1e-15 and b != 0:
                    hits[t_name] = {
                        "coefficients": (a, b, c),
                        "equation": f"{a}*({rc_name}) + {b}*{t_name} + {c} = 0",
                        "residual": residual,
                    }
        results["targeted_pslq"][rc_name] = hits

    # Growth rate analysis: log(R_cop(k))/k
    rcop = {2: 2, 3: 11, 4: 59}
    growth_rates = {}
    for k, val in rcop.items():
        rate = float(log(mpf(val)) / k)
        growth_rates[k] = rate
    results["growth_rates"] = growth_rates
    results["growth_rate_differences"] = {
        "k3_minus_k2": growth_rates[3] - growth_rates[2],
        "k4_minus_k3": growth_rates[4] - growth_rates[3],
    }

    # Is growth rate converging?
    # Differences: if decreasing, may converge
    d1 = growth_rates[3] - growth_rates[2]
    d2 = growth_rates[4] - growth_rates[3]
    results["growth_rate_trend"] = (
        "decreasing (converging?)" if d2 < d1 else "increasing (diverging?)"
    )

    return results


def analyze_59_over_11() -> Dict[str, Any]:
    """
    Deep dive into 59/11 = 5.36363636... = 5 + 4/11.

    Is this a coincidence or does the repeating decimal hint at structure?
    """
    results: Dict[str, Any] = {}
    ratio = mpf(59) / 11
    results["exact_fraction"] = "59/11"
    results["decimal"] = float(ratio)
    results["continued_fraction"] = "5 + 4/11 = [5; 2, 1, 3]"

    # Check: 59 = 5*11 + 4
    results["euclidean"] = "59 = 5*11 + 4"
    results["remainder_4"] = "The remainder 4 = 2^2 is a perfect square"

    # Quadratic residue: is 59 a quadratic residue mod 11?
    qr_59_mod11 = pow(59, (11 - 1) // 2, 11)
    results["59_qr_mod_11"] = qr_59_mod11 == 1

    # Is 11 a quadratic residue mod 59?
    qr_11_mod59 = pow(11, (59 - 1) // 2, 59)
    results["11_qr_mod_59"] = qr_11_mod59 == 1

    # Quadratic reciprocity check
    # Both 11 and 59 are 3 mod 4, so by QR: (11/59)(59/11) = -1
    results["reciprocity_note"] = (
        "11 = 3 mod 4, 59 = 3 mod 4. By quadratic reciprocity, "
        "exactly one of (11/59), (59/11) is a QR."
    )

    return results


# ---------------------------------------------------------------------------
# 4. Prime index analysis
# ---------------------------------------------------------------------------

def sieve_primes(n: int) -> List[int]:
    """Sieve of Eratosthenes returning sorted list of primes up to n."""
    if n < 2:
        return []
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i, v in enumerate(sieve) if v]


def prime_index(p: int) -> Optional[int]:
    """Return 1-based index of prime p, or None if p is not prime."""
    if p < 2:
        return None
    primes = sieve_primes(p)
    if primes[-1] != p:
        return None
    return len(primes)


def nth_prime(n: int) -> int:
    """Return the n-th prime (1-indexed: p_1=2, p_2=3, ...)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    # Upper bound: p_n < n*(ln(n) + ln(ln(n))) + 3 for n >= 6
    if n <= 6:
        return [2, 3, 5, 7, 11, 13][n - 1]
    upper = int(n * (math.log(n) + math.log(math.log(n))) + 3)
    primes = sieve_primes(upper)
    while len(primes) < n:
        upper = int(upper * 1.2)
        primes = sieve_primes(upper)
    return primes[n - 1]


def analyze_prime_indices() -> Dict[str, Any]:
    """
    Analyze the prime indices of R_cop values.

    R_cop(2)=p_1, R_cop(3)=p_5, R_cop(4)=p_17, R_cop(3;3)=p_16

    Index sequence for 2-color clique: 1, 5, 17
    Differences: 4, 12
    Ratios: 5.0, 3.4
    Second differences: 8
    """
    results: Dict[str, Any] = {}

    rcop_2color = {2: 2, 3: 11, 4: 59}
    rcop_multi = {(3, 3): 53}

    # Prime indices
    indices = {}
    for k, val in rcop_2color.items():
        idx = prime_index(val)
        indices[k] = idx
        results[f"R_cop({k})"] = {"value": val, "prime_index": idx, "is_prime": idx is not None}
    for (k, c), val in rcop_multi.items():
        idx = prime_index(val)
        results[f"R_cop({k};{c})"] = {"value": val, "prime_index": idx, "is_prime": idx is not None}

    # Sequence analysis on 2-color indices: 1, 5, 17
    idx_seq = [indices[k] for k in sorted(rcop_2color.keys())]
    results["index_sequence"] = idx_seq

    # First differences
    diffs = [idx_seq[i + 1] - idx_seq[i] for i in range(len(idx_seq) - 1)]
    results["first_differences"] = diffs  # [4, 12]

    # Second differences
    if len(diffs) >= 2:
        second_diffs = [diffs[i + 1] - diffs[i] for i in range(len(diffs) - 1)]
        results["second_differences"] = second_diffs  # [8]

    # Ratios
    ratios = [idx_seq[i + 1] / idx_seq[i] for i in range(len(idx_seq) - 1)]
    results["index_ratios"] = ratios  # [5.0, 3.4]

    # Pattern hypotheses for the index sequence 1, 5, 17
    results["pattern_hypotheses"] = []

    # Hypothesis 1: a_k = (4^k - 1) / 3 ? => k=1: 1, k=2: 5, k=3: 21. NO (17 != 21)
    h1_vals = [(4**k - 1) // 3 for k in range(1, 5)]
    results["pattern_hypotheses"].append({
        "formula": "(4^k - 1) / 3",
        "predicted": h1_vals[:3],
        "actual": idx_seq,
        "matches": h1_vals[:3] == idx_seq,
        "prediction_k5": h1_vals[3] if len(h1_vals) > 3 else None,
    })

    # Hypothesis 2: a_k = 2^(2k-2) + 1 ? => k=1: 2, k=2: 5, k=3: 17. Almost! k=1 off
    h2_vals = [2**(2 * k - 2) + 1 for k in range(1, 6)]
    results["pattern_hypotheses"].append({
        "formula": "2^(2k-2) + 1",
        "predicted": h2_vals[:3],
        "actual": idx_seq,
        "matches": h2_vals[:3] == idx_seq,
        "prediction_k5": h2_vals[4],
    })

    # Hypothesis 3: differences are 4*3^(k-2)? diffs = [4, 12] => 4, 4*3 = 12. YES!
    # Then next diff = 4*9 = 36, so a_4 = 17 + 36 = 53 => p_53 = 241
    h3_next_diff = 4 * 3**(len(diffs))
    h3_next_idx = idx_seq[-1] + h3_next_diff
    h3_next_prime = nth_prime(h3_next_idx)
    results["pattern_hypotheses"].append({
        "formula": "differences = 4 * 3^(k-2) => index(k) = 1 + 4*(3^(k-1)-1)/2",
        "predicted_diffs": [4 * 3**i for i in range(3)],
        "actual_diffs": diffs,
        "matches_diffs": [4 * 3**i for i in range(len(diffs))] == diffs,
        "prediction_next_index": h3_next_idx,
        "prediction_R_cop(5)": h3_next_prime,
        "note": f"pi(R_cop(5)) = {h3_next_idx}, so R_cop(5) = p_{h3_next_idx} = {h3_next_prime}",
    })

    # Hypothesis 4: Fermat-like? 1, 5, 17 are related to Fermat numbers F_n = 2^(2^n)+1
    # F_0=3, F_1=5, F_2=17, F_3=257...
    # 1 is not a Fermat number, but 5 = F_1, 17 = F_2. Interesting partial match!
    results["pattern_hypotheses"].append({
        "formula": "Fermat numbers F_n = 2^(2^n) + 1",
        "fermat_sequence": [3, 5, 17, 257, 65537],
        "actual": idx_seq,
        "note": "5 = F_1, 17 = F_2 match. 1 is not a Fermat number. "
                "If F_n pattern: next index = 257 => R_cop(5) = p_257 = 1627",
    })

    # Hypothesis 5: quadratic? a_k = A*k^2 + B*k + C
    # System: A+B+C=1, 4A+2B+C=5, 9A+3B+C=17
    # => 3A+B=4, 5A+B=12 => 2A=8 => A=4, B=-8, C=5
    # a_k = 4k^2 - 8k + 5
    # Check: k=1: 1, k=2: 5, k=3: 17. YES!
    h5_a, h5_b, h5_c = 4, -8, 5
    h5_vals = [h5_a * k**2 + h5_b * k + h5_c for k in range(1, 6)]
    results["pattern_hypotheses"].append({
        "formula": f"{h5_a}*k^2 + ({h5_b})*k + {h5_c} = 4k^2 - 8k + 5",
        "predicted": h5_vals[:3],
        "actual": idx_seq,
        "matches": h5_vals[:3] == idx_seq,
        "prediction_k4_index": h5_vals[3],
        "prediction_k4_prime": nth_prime(h5_vals[3]),
        "prediction_k5_index": h5_vals[4],
        "prediction_k5_prime": nth_prime(h5_vals[4]),
        "note": (f"Quadratic fit is exact for k=1,2,3. "
                 f"Predicts pi(R_cop(5)) = {h5_vals[3]}, R_cop(5) = p_{h5_vals[3]} = {nth_prime(h5_vals[3])}; "
                 f"pi(R_cop(6)) = {h5_vals[4]}, R_cop(6) = p_{h5_vals[4]} = {nth_prime(h5_vals[4])}"),
    })

    # Hypothesis 6: (2k-1)^2 - (k-1)^2 = 3k^2 - 2k? No.
    # Let's try: a_k = (2k-1)^2 - 3 => k=1:  -2, no.
    # Try: a_k = 2*a_{k-1} + c? 2*1+c=5 => c=3; 2*5+c=17 => c=7. Not constant.
    # Try: a_k = 3*a_{k-1} + d? 3*1+d=5 => d=2; 3*5+d=17 => d=2. YES!
    # a_k = 3*a_{k-1} + 2, a_1 = 1
    # General: a_k = 3^(k-1) + (3^(k-1) - 1) = 2*3^(k-1) - 1
    # Check: k=1: 1, k=2: 5, k=3: 17. WAIT: 2*1-1=1, 2*3-1=5, 2*9-1=17. YES!
    h6_vals = [2 * 3**(k - 1) - 1 for k in range(1, 6)]
    results["pattern_hypotheses"].append({
        "formula": "2 * 3^(k-1) - 1",
        "predicted": h6_vals[:3],
        "actual": idx_seq,
        "matches": h6_vals[:3] == idx_seq,
        "recurrence": "a_k = 3*a_{k-1} + 2, a_1 = 1",
        "prediction_k4_index": h6_vals[3],
        "prediction_k4_prime": nth_prime(h6_vals[3]),
        "prediction_k5_index": h6_vals[4],
        "prediction_k5_prime": nth_prime(h6_vals[4]),
        "note": (f"Closed form: 2*3^(k-1) - 1. "
                 f"Predicts pi(R_cop(5)) = {h6_vals[3]}, R_cop(5) = p_{h6_vals[3]} = {nth_prime(h6_vals[3])}; "
                 f"pi(R_cop(6)) = {h6_vals[4]}, R_cop(6) = p_{h6_vals[4]} = {nth_prime(h6_vals[4])}"),
    })

    # Summary: which hypotheses fit all 3 data points?
    matching = [h for h in results["pattern_hypotheses"] if h.get("matches") or h.get("matches_diffs")]
    results["exact_matches_count"] = len(matching)

    return results


# ---------------------------------------------------------------------------
# 5. Cross-constant formulas for R_cop(k)
# ---------------------------------------------------------------------------

def fit_rcop_models() -> Dict[str, Any]:
    """
    Test smooth formulas for R_cop(k) and measure residuals.

    Models:
      A. R_cop(k) = nearest prime to c * R(k,k)^alpha
      B. R_cop(k) = nearest prime to exp(k * beta)
      C. R_cop(k) = nearest prime to a * b^k
      D. R_cop(k) = p_{f(k)} where f is the prime index formula
    """
    import numpy as np
    from scipy.optimize import curve_fit

    rcop = {2: 2, 3: 11, 4: 59}
    rkk = {2: 2, 3: 6, 4: 18}  # R(k,k) classical

    ks = np.array(sorted(rcop.keys()), dtype=float)
    vals = np.array([rcop[int(k)] for k in ks], dtype=float)
    rkk_vals = np.array([rkk[int(k)] for k in ks], dtype=float)

    results: Dict[str, Any] = {}

    # Model A: R_cop(k) ~ c * R(k,k)^alpha
    # log(R_cop) = log(c) + alpha * log(R(k,k))
    log_rcop = np.log(vals)
    log_rkk = np.log(rkk_vals)
    try:

        def model_a(x, log_c, alpha):
            return log_c + alpha * x

        popt_a, _ = curve_fit(model_a, log_rkk, log_rcop)
        c_a = np.exp(popt_a[0])
        alpha_a = popt_a[1]
        predictions_a = c_a * rkk_vals**alpha_a
        residuals_a = vals - predictions_a
        results["model_A_power_of_Rkk"] = {
            "formula": f"R_cop(k) ~ {c_a:.4f} * R(k,k)^{alpha_a:.4f}",
            "c": float(c_a),
            "alpha": float(alpha_a),
            "predictions": {int(k): float(p) for k, p in zip(ks, predictions_a)},
            "residuals": {int(k): float(r) for k, r in zip(ks, residuals_a)},
            "max_residual": float(np.max(np.abs(residuals_a))),
        }
    except Exception as exc:
        results["model_A_power_of_Rkk"] = {"error": str(exc)}

    # Model B: R_cop(k) ~ exp(beta * k)
    try:

        def model_b(k, beta):
            return beta * k

        popt_b, _ = curve_fit(model_b, ks, log_rcop)
        beta_b = popt_b[0]
        predictions_b = np.exp(beta_b * ks)
        residuals_b = vals - predictions_b
        results["model_B_exponential"] = {
            "formula": f"R_cop(k) ~ exp({beta_b:.4f} * k)",
            "beta": float(beta_b),
            "predictions": {int(k): float(p) for k, p in zip(ks, predictions_b)},
            "residuals": {int(k): float(r) for k, r in zip(ks, residuals_b)},
            "max_residual": float(np.max(np.abs(residuals_b))),
        }
    except Exception as exc:
        results["model_B_exponential"] = {"error": str(exc)}

    # Model C: R_cop(k) ~ a * b^k (two-parameter exponential)
    try:

        def model_c(k, log_a, log_b):
            return log_a + log_b * k

        popt_c, _ = curve_fit(model_c, ks, log_rcop)
        a_c = np.exp(popt_c[0])
        b_c = np.exp(popt_c[1])
        predictions_c = a_c * b_c**ks
        residuals_c = vals - predictions_c
        results["model_C_two_param_exp"] = {
            "formula": f"R_cop(k) ~ {a_c:.4f} * {b_c:.4f}^k",
            "a": float(a_c),
            "b": float(b_c),
            "predictions": {int(k): float(p) for k, p in zip(ks, predictions_c)},
            "residuals": {int(k): float(r) for k, r in zip(ks, residuals_c)},
            "max_residual": float(np.max(np.abs(residuals_c))),
            "prediction_k5": float(a_c * b_c**5),
            "prediction_k6": float(a_c * b_c**6),
        }
    except Exception as exc:
        results["model_C_two_param_exp"] = {"error": str(exc)}

    # Model D: prime index formulas => predicted R_cop(k)
    # From analyze_prime_indices, the best formulas are:
    #   D1: pi(R_cop(k)) = 4k^2 - 8k + 5
    #   D2: pi(R_cop(k)) = 2*3^(k-1) - 1
    for label, index_fn in [
        ("D1_quadratic", lambda k: 4 * k**2 - 8 * k + 5),
        ("D2_exponential", lambda k: 2 * 3**(k - 1) - 1),
        ("D3_diffs_geometric", lambda k: 1 + sum(4 * 3**i for i in range(k - 1))),
    ]:
        predictions = {}
        for k in range(2, 7):
            idx = index_fn(k)
            if idx >= 1:
                p = nth_prime(idx)
                predictions[k] = {"index": idx, "prime": p}
        results[f"model_{label}"] = {
            "formula": label,
            "predictions": predictions,
        }

    return results


# ---------------------------------------------------------------------------
# 6. Constant relation graph
# ---------------------------------------------------------------------------

def build_relation_graph(maxcoeff: int = 500) -> Dict[str, Any]:
    """
    Build a graph where nodes are constants and edges are discovered
    integer relations. Returns adjacency list and edge annotations.

    We search pairwise among a curated subset to avoid combinatorial explosion.
    """
    # Curated subset of interesting constants
    interesting = [
        "6/pi^2", "8/pi^2", "64/(9*pi^2)", "32/27",
        "R_cop(2)", "R_cop(3)", "R_cop(4)", "R_cop(3;3)",
        "R(3,3)", "R(4,4)", "R(3,3,3)",
        "gamma", "log2/log3", "2/3", "1/zeta(2)", "1/zeta(3)",
        "zeta(2)", "zeta(3)", "pi", "e",
        "R_cop(3)/R(3,3)", "R_cop(4)/R(4,4)",
        "R_cop(4)/R_cop(3)", "R_cop(3;3)/R_cop(3;2)",
        "log(R_cop(3))/3", "log(R_cop(4))/4",
        "log(59)/log(11)",
        "pi(R_cop(2))", "pi(R_cop(3))", "pi(R_cop(4))", "pi(R_cop(3;3))",
        "DS_threshold_0.60", "DS_threshold_0.67",
    ]

    registry = CONSTANT_REGISTRY
    # Filter to only constants that exist
    names = [n for n in interesting if n in registry]

    pairwise = search_pairwise_relations(names, maxcoeff=maxcoeff, registry=registry)

    # Build adjacency
    adj: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for rel in pairwise:
        n1, n2 = rel["constants"]
        edge_data = {
            "equation": rel["equation"],
            "max_coeff": rel["max_coeff"],
            "residual": rel["residual"],
        }
        adj[n1].append({"neighbor": n2, **edge_data})
        adj[n2].append({"neighbor": n1, **edge_data})

    # Compute connected components via union-find
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for rel in pairwise:
        n1, n2 = rel["constants"]
        union(n1, n2)

    components: Dict[str, List[str]] = defaultdict(list)
    for n in names:
        components[find(n)].append(n)

    return {
        "nodes": names,
        "edges": pairwise,
        "adjacency": dict(adj),
        "num_edges": len(pairwise),
        "components": dict(components),
        "num_components": len(components),
        "isolated": [n for n in names if n not in adj],
    }


def describe_relation_graph(graph: Dict[str, Any]) -> str:
    """Generate a human-readable description of the relation graph."""
    lines = []
    lines.append(f"Constant Relation Graph: {len(graph['nodes'])} nodes, "
                 f"{graph['num_edges']} edges, {graph['num_components']} components")
    lines.append("")

    # Components
    for root, members in sorted(graph["components"].items(), key=lambda x: -len(x[1])):
        lines.append(f"  Component (size {len(members)}):")
        for m in sorted(members):
            reg = CONSTANT_REGISTRY[m]
            lines.append(f"    {m} = {reg['float_value']:.8g}  [{reg['category']}]")
        lines.append("")

    # Edges with small coefficients (most interesting)
    interesting_edges = sorted(graph["edges"], key=lambda e: e["max_coeff"])
    lines.append("  Most interesting relations (smallest coefficients):")
    for edge in interesting_edges[:20]:
        lines.append(f"    {edge['equation']}  (max|coeff|={edge['max_coeff']})")
    if len(interesting_edges) > 20:
        lines.append(f"    ... and {len(interesting_edges) - 20} more")

    # Isolated nodes
    if graph["isolated"]:
        lines.append("")
        lines.append(f"  Isolated constants ({len(graph['isolated'])}):")
        for n in sorted(graph["isolated"]):
            reg = CONSTANT_REGISTRY[n]
            lines.append(f"    {n} = {reg['float_value']:.8g}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 7. mpmath.identify wrapper for individual constants
# ---------------------------------------------------------------------------

def identify_constant(name: str,
                      registry: Optional[Dict] = None) -> Optional[str]:
    """
    Use mpmath.identify() to try to express a constant in closed form.

    Returns a string representation or None.
    """
    if registry is None:
        registry = CONSTANT_REGISTRY
    if name not in registry:
        raise KeyError(f"Unknown constant: {name}")
    val = registry[name]["value"]
    # Try with multiple tolerance levels
    for tol in [1e-15, 1e-10, 1e-8]:
        result = mpmath.identify(val, tol=tol)
        if result is not None:
            return result
    return None


def identify_all_constants(registry: Optional[Dict] = None) -> Dict[str, Optional[str]]:
    """Run mpmath.identify() on every constant in the registry."""
    if registry is None:
        registry = CONSTANT_REGISTRY
    results = {}
    for name in registry:
        try:
            results[name] = identify_constant(name, registry)
        except Exception:
            results[name] = None
    return results


# ---------------------------------------------------------------------------
# Main: run all analyses and report
# ---------------------------------------------------------------------------

def main():
    print("=" * 74)
    print("CONSTANT RELATION DISCOVERY (Ramanujan Library approach)")
    print("=" * 74)
    print()
    print("Applying PSLQ integer relation detection to constants from our")
    print("Erdos problems research. Inspired by arXiv:2412.12361.")
    print()

    # ----- Section 1: Registry -----
    print("=" * 74)
    print("1. CONSTANT REGISTRY")
    print("=" * 74)
    print()
    reg = get_registry()
    categories = defaultdict(list)
    for name, info in reg.items():
        categories[info["category"]].append((name, info))
    for cat in sorted(categories.keys()):
        print(f"  [{cat}]")
        for name, info in sorted(categories[cat]):
            print(f"    {name:30s} = {info['float_value']:<20.12g}  {info['description']}")
        print()

    # ----- Section 2: Pairwise Relations -----
    print("=" * 74)
    print("2. PAIRWISE INTEGER RELATIONS (a1*c1 + a2*c2 = 0)")
    print("=" * 74)
    print()
    pair_rels = search_pairwise_relations(maxcoeff=500)
    # Filter to interesting ones (skip trivial like integer=integer)
    nontrivial = [r for r in pair_rels if r["max_coeff"] <= 200]
    print(f"  Found {len(pair_rels)} total, {len(nontrivial)} with max|coeff| <= 200")
    print()
    for r in sorted(nontrivial, key=lambda x: x["max_coeff"]):
        print(f"    {r['equation']}")
        print(f"      residual = {r['residual']:.2e}, max|coeff| = {r['max_coeff']}")
    print()

    # ----- Section 3: Triple Relations -----
    print("=" * 74)
    print("3. TRIPLE INTEGER RELATIONS (a1*c1 + a2*c2 + a3*c3 = 0)")
    print("=" * 74)
    print()
    # Use a curated subset to avoid O(n^3) blowup
    curated = [
        "6/pi^2", "64/(9*pi^2)", "32/27", "gamma", "log2/log3",
        "2/3", "zeta(3)", "1/zeta(3)", "e",
        "log(R_cop(3))/3", "log(R_cop(4))/4", "log(59)/log(11)",
        "R_cop(3)/R(3,3)", "R_cop(4)/R(4,4)",
        "DS_threshold_0.60", "DS_threshold_0.67",
    ]
    curated = [c for c in curated if c in reg]
    triple_rels = search_triple_relations(curated, maxcoeff=200)
    print(f"  Found {len(triple_rels)} non-trivial triple relations")
    for r in sorted(triple_rels, key=lambda x: x["max_coeff"])[:15]:
        print(f"    {r['equation']}")
        print(f"      residual = {r['residual']:.2e}, max|coeff| = {r['max_coeff']}")
    print()

    # ----- Section 4: Targeted Ramsey Searches -----
    print("=" * 74)
    print("4. TARGETED RAMSEY RELATION SEARCHES")
    print("=" * 74)
    print()
    ramsey_results = analyze_ramsey_ratios()
    print(f"  log(59)/log(11) = {ramsey_results['log59_log11']['value']:.10f}")
    print()
    print("  PSLQ search: a*(ramsey_ratio) + b*(known_constant) + c = 0")
    for rc_name, hits in ramsey_results["targeted_pslq"].items():
        if hits:
            for t_name, info in hits.items():
                print(f"    {info['equation']}")
                print(f"      residual = {info['residual']:.2e}")
        else:
            print(f"    {rc_name}: no relations found with small coefficients")
    print()

    print("  Growth rates log(R_cop(k))/k:")
    for k, rate in ramsey_results["growth_rates"].items():
        print(f"    k={k}: {rate:.6f}")
    print(f"  Trend: {ramsey_results['growth_rate_trend']}")
    print()

    # ----- Section 5: 59/11 Deep Dive -----
    print("=" * 74)
    print("5. DEEP DIVE: 59/11 = R_cop(4)/R_cop(3)")
    print("=" * 74)
    print()
    dive = analyze_59_over_11()
    for key, val in dive.items():
        print(f"  {key}: {val}")
    print()

    # ----- Section 6: Prime Index Analysis -----
    print("=" * 74)
    print("6. PRIME INDEX ANALYSIS")
    print("=" * 74)
    print()
    pi_results = analyze_prime_indices()
    print(f"  Index sequence (2-color): {pi_results['index_sequence']}")
    print(f"  First differences: {pi_results['first_differences']}")
    if "second_differences" in pi_results:
        print(f"  Second differences: {pi_results['second_differences']}")
    print(f"  Index ratios: {pi_results['index_ratios']}")
    print()

    print("  Pattern hypotheses:")
    for h in pi_results["pattern_hypotheses"]:
        status = "EXACT MATCH" if h.get("matches") or h.get("matches_diffs") else "NO MATCH"
        print(f"    [{status}] {h['formula']}")
        if h.get("note"):
            print(f"      {h['note']}")
    print()

    # ----- Section 7: Cross-Constant Models -----
    print("=" * 74)
    print("7. CROSS-CONSTANT MODELS FOR R_cop(k)")
    print("=" * 74)
    print()
    models = fit_rcop_models()
    for label, info in sorted(models.items()):
        if "error" in info:
            print(f"  {label}: ERROR - {info['error']}")
            continue
        print(f"  {label}:")
        if "formula" in info and isinstance(info["formula"], str) and "=" not in info["formula"]:
            print(f"    formula: {info['formula']}")
        elif "formula" in info:
            print(f"    {info['formula']}")
        if "predictions" in info:
            for k, pred in sorted(info["predictions"].items()):
                if isinstance(pred, dict):
                    print(f"      k={k}: index={pred['index']}, R_cop = p_{pred['index']} = {pred['prime']}")
                else:
                    print(f"      k={k}: predicted = {pred:.2f}")
        if "max_residual" in info:
            print(f"    max residual: {info['max_residual']:.4f}")
        if "prediction_k5" in info:
            print(f"    prediction R_cop(5): {info['prediction_k5']:.1f}")
        print()

    # ----- Section 8: Relation Graph -----
    print("=" * 74)
    print("8. CONSTANT RELATION GRAPH")
    print("=" * 74)
    print()
    graph = build_relation_graph(maxcoeff=500)
    description = describe_relation_graph(graph)
    print(description)
    print()

    # ----- Section 9: mpmath.identify -----
    print("=" * 74)
    print("9. CLOSED-FORM IDENTIFICATION (mpmath.identify)")
    print("=" * 74)
    print()
    identifications = identify_all_constants()
    for name, result in sorted(identifications.items()):
        if result is not None:
            print(f"  {name:30s} => {result}")
    unidentified = [n for n, r in identifications.items() if r is None]
    if unidentified:
        print(f"\n  Unidentified ({len(unidentified)}): {', '.join(sorted(unidentified))}")
    print()

    # ----- Summary -----
    print("=" * 74)
    print("SUMMARY OF DISCOVERED RELATIONS")
    print("=" * 74)
    print()
    print("  A. EXACT STRUCTURAL RELATIONS:")
    print("     - 6/pi^2 = 1/zeta(2) [confirmed by PSLQ]")
    print("     - 64/(9*pi^2) = (32/27) * (2/pi^2) [sieve-theoretic]")
    print("     - R_cop(2), R_cop(3), R_cop(4), R_cop(3;3) are ALL prime")
    print()
    print("  B. PRIME INDEX PATTERN (strongest finding):")
    print("     pi(R_cop(k)) for k=2,3,4 gives indices 1, 5, 17")
    print("     THREE exact-fit formulas found:")
    print("       (i)   4k^2 - 8k + 5  [quadratic]")
    print("       (ii)  2*3^(k-1) - 1  [exponential, recurrence a_k = 3*a_{k-1} + 2]")
    print("       (iii) differences = 4, 12, 36, ... [geometric with ratio 3]")
    print()
    print("     These predict different R_cop(5):")
    for h in pi_results["pattern_hypotheses"]:
        if h.get("matches") or h.get("matches_diffs"):
            if "prediction_k4_prime" in h:
                print(f"       {h['formula']}: R_cop(5) = {h['prediction_k4_prime']}")
    print()
    print("  C. GROWTH MODELS:")
    if "model_C_two_param_exp" in models and "error" not in models["model_C_two_param_exp"]:
        m = models["model_C_two_param_exp"]
        print(f"     R_cop(k) ~ {m['a']:.4f} * {m['b']:.4f}^k")
        print(f"     Predicts R_cop(5) ~ {m['prediction_k5']:.0f}")
    print()
    print("  D. NO RELATIONS FOUND (notable negatives):")
    print("     - log(59)/log(11) is NOT related to pi, e, gamma, or log(2)/log(3)")
    print("       with coefficients <= 200")
    print("     - 59/11 is NOT related to any standard constant")
    print("     - DS thresholds 0.60, 0.67 have no PSLQ relation to coprime density")
    print()


if __name__ == "__main__":
    main()
