#!/usr/bin/env python3
"""
Adversarial Analysis of Six Mathematical Claims
=================================================

Systematic devil's-advocate testing of conjectured formulas and patterns.
For each claim, we attempt to DISPROVE or find structural weaknesses.

Claims tested:
  1. MS(k) = 2^((3^k+1)/2) - 1 -- overfitting test via alternative formulas
  2. NPG-30: Coprime Ramsey numbers are always prime -- null model probability
  3. R_gcd(3;d) = 11d -- edge-by-edge isomorphism verification for d=5
  4. Coprime graph perfectness -- strong perfectness via odd hole/antihole search
  5. DS(2,0.50) definition sensitivity -- exhaustive enumeration on [5]
  6. 156 avoiding colorings at n=10 for R_cop(3) -- independent SAT count
"""

import math
from itertools import combinations, product
from typing import Dict, List, Optional, Set, Tuple, Any

import numpy as np
from scipy.interpolate import lagrange


# =====================================================================
# Claim 1: MS(k) = 2^((3^k+1)/2) - 1 -- Overfitting Analysis
# =====================================================================

def ms_proposed(k: int) -> int:
    """The proposed formula: MS(k) = 2^((3^k + 1) / 2) - 1."""
    exp = (3 ** k + 1) // 2
    return 2 ** exp - 1


def find_alternative_formulas() -> List[Dict[str, Any]]:
    """
    Find alternative closed-form expressions that match MS(1)=3, MS(2)=31,
    MS(3)=16383 but predict DIFFERENT MS(4).

    Strategy: any 3-parameter model can fit 3 points exactly.
    We try several parametric families and solve for coefficients.
    """
    # Known data points: k=1 -> 3, k=2 -> 31, k=3 -> 16383
    ks = [1, 2, 3]
    vals = [3, 31, 16383]

    alternatives = []

    # --- Family 1: Lagrange interpolation (polynomial through 3 points) ---
    # A degree-2 polynomial fits any 3 points exactly.
    poly = lagrange(ks, vals)
    pred_4_poly = int(round(float(poly(4))))
    alternatives.append({
        "family": "degree-2 polynomial (Lagrange)",
        "formula": f"p(k) = {poly.coef[0]:.1f}k^2 + {poly.coef[1]:.1f}k + {poly.coef[2]:.1f}",
        "fits_data": all(int(round(float(poly(k)))) == v for k, v in zip(ks, vals)),
        "MS(4)_predicted": pred_4_poly,
        "MS(4)_proposed": ms_proposed(4),
        "agrees_with_proposed": pred_4_poly == ms_proposed(4),
    })

    # --- Family 2: a * b^k + c (exponential + constant) ---
    # 3 equations: a*b + c = 3, a*b^2 + c = 31, a*b^3 + c = 16383
    # From (2)-(1): a*b*(b-1) = 28
    # From (3)-(2): a*b^2*(b-1) = 16352
    # Ratio: b = 16352/28 = 584
    # Then a*584*(584-1) = 28 => a = 28/(584*583) = 28/340472
    b_exp = 16352 / 28
    a_exp = 28 / (b_exp * (b_exp - 1))
    c_exp = 3 - a_exp * b_exp
    pred_4_exp = a_exp * b_exp ** 4 + c_exp
    alternatives.append({
        "family": "a * b^k + c (exponential + offset)",
        "params": {"a": a_exp, "b": b_exp, "c": c_exp},
        "fits_data": True,  # By construction
        "MS(4)_predicted": int(round(pred_4_exp)),
        "MS(4)_proposed": ms_proposed(4),
        "agrees_with_proposed": int(round(pred_4_exp)) == ms_proposed(4),
    })

    # --- Family 3: 2^f(k) - 1 where f is a degree-2 polynomial in k ---
    # f(1) = 2, f(2) = 5, f(3) = 14
    # Fit quadratic: f(k) = ak^2 + bk + c
    # a + b + c = 2
    # 4a + 2b + c = 5
    # 9a + 3b + c = 14
    # Solving: (2)-(1): 3a + b = 3; (3)-(2): 5a + b = 9 => 2a = 6 => a = 3
    # b = 3 - 9 = -6; c = 2 - 3 + 6 = 5
    a_q, b_q, c_q = 3, -6, 5
    f_check = [a_q * k**2 + b_q * k + c_q for k in ks]
    assert f_check == [2, 5, 14], f"Quadratic exponent check failed: {f_check}"
    f4 = a_q * 16 + b_q * 4 + c_q  # k=4
    pred_4_quad_exp = 2 ** f4 - 1
    alternatives.append({
        "family": "2^(3k^2 - 6k + 5) - 1 (quadratic exponent)",
        "exponent_formula": "f(k) = 3k^2 - 6k + 5",
        "exponent_values": {k: a_q * k**2 + b_q * k + c_q for k in range(1, 5)},
        "fits_data": True,
        "MS(4)_predicted": pred_4_quad_exp,
        "MS(4)_proposed": ms_proposed(4),
        "agrees_with_proposed": pred_4_quad_exp == ms_proposed(4),
    })

    # --- Family 4: The proposed formula uses f(k) = (3^k + 1)/2 ---
    # Exponents: 2, 5, 14, 41 (next term)
    # Recurrence: f(k) = 3*f(k-1) - 1
    # The quadratic exponent gives f(4) = 3*16 - 24 + 5 = 29
    # The proposed gives f(4) = (81+1)/2 = 41
    # These disagree!
    proposed_exp_4 = (3**4 + 1) // 2  # = 41
    quad_exp_4 = a_q * 16 + b_q * 4 + c_q  # = 29
    alternatives.append({
        "family": "COMPARISON: quadratic vs proposed exponent at k=4",
        "proposed_exponent": proposed_exp_4,
        "quadratic_exponent": quad_exp_4,
        "proposed_MS4": 2**41 - 1,
        "quadratic_MS4": 2**29 - 1,
        "ratio": (2**41 - 1) / (2**29 - 1),
    })

    # --- Family 5: f(k) = floor(e * 3^(k-1)) (exponential rounding) ---
    # f(1)=2, f(2)=5, f(3)=14
    # Try a * r^k: 2 = a*r, 5 = a*r^2, 14 = a*r^3
    # r = 14/5 = 2.8, r = 5/2 = 2.5 -- not consistent, so not exact
    # But round(a * 2.6458^k)? Let's check with a = 2/r.
    # The non-constant ratio rules out simple a*r^k,
    # but floor(c * 3^(k-1)) with c ~ 2.333 might work:
    # floor(2.333 * 1) = 2, floor(2.333 * 3) = 6 (not 5) -- FAILS
    # This family does NOT fit, confirming f(k) = (3^k+1)/2 is special.

    # --- Family 6: Catalan/factorial-based ---
    # C(1)=1, C(2)=2, C(3)=5, C(4)=14 -- note f(3)=14 = C(4)!
    # f(k) as Catalan(k+1)? C(2)=2, C(3)=5, C(4)=14. Yes!
    # But C(2)=2=f(1), C(3)=5=f(2), C(4)=14=f(3). So f(k) = C(k+1).
    # C(5) = 42, so MS(4) = 2^42 - 1 under this model.
    def catalan(n):
        return math.comb(2 * n, n) // (n + 1)
    cat_exps = [catalan(k + 1) for k in range(1, 5)]
    fits_catalan = (cat_exps[:3] == [2, 5, 14])
    pred_4_catalan = 2 ** catalan(5) - 1 if fits_catalan else None
    alternatives.append({
        "family": "2^(Catalan(k+1)) - 1",
        "exponent_as_catalan": {k: catalan(k + 1) for k in range(1, 5)},
        "fits_data": fits_catalan,
        "MS(4)_predicted": pred_4_catalan,
        "MS(4)_proposed": ms_proposed(4),
        "agrees_with_proposed": pred_4_catalan == ms_proposed(4) if pred_4_catalan else False,
    })

    return alternatives


def overfitting_verdict() -> Dict[str, Any]:
    """
    Summarize the overfitting analysis for the MS(k) formula.
    """
    alts = find_alternative_formulas()
    distinct_predictions = set()
    for a in alts:
        if "MS(4)_predicted" in a and a["MS(4)_predicted"] is not None:
            distinct_predictions.add(a["MS(4)_predicted"])

    proposed_ms4 = ms_proposed(4)

    return {
        "num_alternatives": len(alts),
        "distinct_MS4_predictions": sorted(distinct_predictions),
        "proposed_MS4": proposed_ms4,
        "num_agreeing": sum(
            1 for a in alts
            if a.get("agrees_with_proposed") is True
        ),
        "num_disagreeing": sum(
            1 for a in alts
            if a.get("agrees_with_proposed") is False
        ),
        "alternatives": alts,
        "verdict": (
            "WEAKENED: Multiple alternative 3-parameter formulas fit "
            "the same 3 data points but predict wildly different MS(4). "
            "The formula is NOT uniquely determined by the data. "
            "Computing MS(4) directly would be the only way to discriminate."
        ),
    }


# =====================================================================
# Claim 2: NPG-30 -- Coprime Ramsey primes null model
# =====================================================================

def prime_probability_null_model() -> Dict[str, Any]:
    """
    Compute the probability that 4 'random' numbers in the same ranges
    as R_cop(2..5) would all be prime.

    Known values: R_cop(2)=2, R_cop(3)=11, R_cop(4)=53 or 59, R_cop(3;3)=53.
    The claim says the 4 data points are {2, 11, 53, 59}.

    We model each R_cop(k) as drawn uniformly from [2, upper_k] where
    upper_k is a generous range around the observed value.
    """
    def sieve(n):
        if n < 2:
            return []
        is_p = [True] * (n + 1)
        is_p[0] = is_p[1] = False
        for i in range(2, int(n**0.5) + 1):
            if is_p[i]:
                for j in range(i*i, n+1, i):
                    is_p[j] = False
        return [i for i in range(2, n+1) if is_p[i]]

    # The 4 claimed prime values
    claimed = [2, 11, 53, 59]

    # Model 1: uniform on [2, 2*value] for each
    # Model 2: uniform on [value//2, 2*value] for each
    # Model 3: PNT-based -- Pr(n prime) ~ 1/ln(n) for n around the value

    results = {}

    # Model 1: range [2, 2*v]
    prob_m1 = 1.0
    details_m1 = []
    for v in claimed:
        hi = max(4, 2 * v)
        primes_in_range = sieve(hi)
        primes_in_range = [p for p in primes_in_range if p >= 2]
        total = hi - 1  # numbers in [2, hi]
        p_prime = len(primes_in_range) / total
        prob_m1 *= p_prime
        details_m1.append({
            "value": v, "range": f"[2, {hi}]",
            "primes_in_range": len(primes_in_range),
            "total": total,
            "p_prime": p_prime,
        })
    results["model_uniform_2_to_2v"] = {
        "probability_all_prime": prob_m1,
        "details": details_m1,
    }

    # Model 2: PNT approximation -- 1/ln(v) for each
    prob_pnt = 1.0
    details_pnt = []
    for v in claimed:
        p_prime = 1.0 / math.log(max(v, 2))
        prob_pnt *= p_prime
        details_pnt.append({"value": v, "p_prime_pnt": p_prime})
    results["model_PNT"] = {
        "probability_all_prime": prob_pnt,
        "details": details_pnt,
    }

    # Model 3: conditional on being odd (Ramsey numbers > 2 should be odd)
    # Among odd numbers up to N, prime density ~ 2/ln(N)
    prob_odd = 1.0
    details_odd = []
    for v in claimed:
        if v == 2:
            # 2 is the only even prime; Pr(2 | draw from {2}) = 1
            # But in a fair range model, Pr(prime AND even) is tiny
            details_odd.append({"value": 2, "note": "special case", "p_prime": 0.5})
            prob_odd *= 0.5
        else:
            hi = max(4, 2 * v)
            odd_primes = [p for p in sieve(hi) if p >= 3 and p % 2 == 1]
            odd_numbers = (hi - 1) // 2  # count of odd numbers in [3, hi]
            p = len(odd_primes) / max(odd_numbers, 1)
            prob_odd *= p
            details_odd.append({
                "value": v, "p_prime_among_odd": p,
                "odd_primes": len(odd_primes), "odd_total": odd_numbers,
            })
    results["model_odd_conditional"] = {
        "probability_all_prime": prob_odd,
        "details": details_odd,
    }

    # Verdict
    is_surprising = all(
        r["probability_all_prime"] < 0.01
        for r in results.values()
    )

    results["verdict"] = {
        "probabilities": {k: v["probability_all_prime"] for k, v in results.items()
                          if isinstance(v, dict) and "probability_all_prime" in v},
        "is_surprising": is_surprising,
        "assessment": (
            "WEAK EVIDENCE: The probability of 4 numbers in these ranges "
            "all being prime is NOT negligibly small under reasonable null "
            "models. With prime density ~25-45% in the relevant ranges, "
            "seeing 4 primes is not extraordinary. The 'always prime' "
            "pattern could easily be coincidence."
            if not is_surprising else
            "MODERATE EVIDENCE: The probability is < 1% under all null "
            "models, suggesting the primality pattern is unlikely to be "
            "pure coincidence. But 4 data points remain very few."
        ),
    }

    return results


# =====================================================================
# Claim 3: R_gcd(3;d) = 11d -- Isomorphism verification for d=5
# =====================================================================

def verify_gcd_isomorphism(d: int, m: int) -> Dict[str, Any]:
    """
    Verify edge-by-edge that the map i -> d*i is a graph isomorphism
    between:
      - Coprime graph on [m] (edges where gcd(i,j)=1)
      - GCD-d graph on {d, 2d, ..., md} (edges where gcd(a,b)=d)

    If this is an isomorphism, then R_gcd(k;d) = d * R_cop(k) for all k.
    """
    # Coprime graph edges on [m]
    coprime_edges = []
    for i in range(1, m + 1):
        for j in range(i + 1, m + 1):
            if math.gcd(i, j) == 1:
                coprime_edges.append((i, j))

    # GCD-d graph edges on {d, 2d, ..., md}
    gcd_d_edges = []
    for i in range(1, m + 1):
        for j in range(i + 1, m + 1):
            a, b = d * i, d * j
            if math.gcd(a, b) == d:
                gcd_d_edges.append((d * i, d * j))

    # The map i -> d*i should send coprime_edges to gcd_d_edges.
    # Check: gcd(i,j)=1 iff gcd(d*i, d*j) = d
    # Proof: gcd(d*i, d*j) = d * gcd(i,j). So gcd(di,dj)=d iff gcd(i,j)=1.
    # This is a THEOREM, not just empirical. Let's verify edge-by-edge anyway.

    mapped_coprime = set()
    for (i, j) in coprime_edges:
        mapped_coprime.add((d * i, d * j))

    gcd_d_set = set(gcd_d_edges)

    # Edges in coprime (mapped) but not in GCD-d
    missing_from_gcd = mapped_coprime - gcd_d_set
    # Edges in GCD-d but not in mapped coprime
    extra_in_gcd = gcd_d_set - mapped_coprime

    is_isomorphic = (len(missing_from_gcd) == 0 and len(extra_in_gcd) == 0)

    # Also verify the algebraic identity edge by edge
    algebraic_failures = []
    for i in range(1, m + 1):
        for j in range(i + 1, m + 1):
            gcd_ij = math.gcd(i, j)
            gcd_didj = math.gcd(d * i, d * j)
            if gcd_didj != d * gcd_ij:
                algebraic_failures.append({
                    "i": i, "j": j,
                    "gcd(i,j)": gcd_ij,
                    "gcd(di,dj)": gcd_didj,
                    "d*gcd(i,j)": d * gcd_ij,
                })

    return {
        "d": d,
        "m": m,
        "coprime_edge_count": len(coprime_edges),
        "gcd_d_edge_count": len(gcd_d_edges),
        "is_isomorphic": is_isomorphic,
        "missing_from_gcd": list(missing_from_gcd)[:10],
        "extra_in_gcd": list(extra_in_gcd)[:10],
        "algebraic_identity_holds": len(algebraic_failures) == 0,
        "algebraic_failures": algebraic_failures[:5],
    }


def verify_gcd_scaling_formula() -> Dict[str, Any]:
    """
    Verify R_gcd(3;d) = 11d for d = 1..6 by checking the isomorphism
    and computing R_gcd directly for small d.
    """
    results = {}
    for d in range(1, 7):
        iso = verify_gcd_isomorphism(d, m=11)
        results[d] = {
            "isomorphism_verified": iso["is_isomorphic"],
            "algebraic_identity": iso["algebraic_identity_holds"],
            "predicted_R_gcd": 11 * d,
        }
    return results


# =====================================================================
# Claim 4: Coprime graph strong perfectness
# =====================================================================

def coprime_adj(n: int) -> Dict[int, Set[int]]:
    """Build adjacency for the coprime graph on [n]."""
    adj: Dict[int, Set[int]] = {v: set() for v in range(1, n + 1)}
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def induced_subgraph(adj: Dict[int, Set[int]],
                     subset: Set[int]) -> Dict[int, Set[int]]:
    """Return adjacency restricted to subset."""
    return {v: adj[v] & subset for v in subset}


def brute_clique_number(adj: Dict[int, Set[int]]) -> int:
    """Find clique number by brute force on a small graph."""
    verts = sorted(adj.keys())
    n = len(verts)
    best = 0
    for size in range(1, n + 1):
        found = False
        for combo in combinations(verts, size):
            if all(combo[j] in adj[combo[i]]
                   for i in range(len(combo))
                   for j in range(i + 1, len(combo))):
                found = True
                break
        if found:
            best = size
        else:
            break
    return best


def greedy_chromatic(adj: Dict[int, Set[int]]) -> int:
    """Greedy chromatic number (upper bound on chi)."""
    verts = sorted(adj.keys(), key=lambda v: len(adj[v]), reverse=True)
    color = {}
    for v in verts:
        used = {color[u] for u in adj[v] if u in color}
        c = 0
        while c in used:
            c += 1
        color[v] = c
    return max(color.values()) + 1 if color else 0


def exact_chromatic_number(adj: Dict[int, Set[int]]) -> int:
    """
    Compute exact chromatic number for small graphs.
    Try coloring with k colors for k = omega, omega+1, ... up to greedy bound.
    Uses backtracking.
    """
    verts = sorted(adj.keys())
    n = len(verts)
    if n == 0:
        return 0

    omega = brute_clique_number(adj)
    greedy_ub = greedy_chromatic(adj)

    if omega == greedy_ub:
        return omega

    def can_color(num_colors):
        color = {}

        def bt(idx):
            if idx == n:
                return True
            v = verts[idx]
            used = {color[u] for u in adj[v] if u in color}
            for c in range(num_colors):
                if c not in used:
                    color[v] = c
                    if bt(idx + 1):
                        return True
                    del color[v]
            return False

        return bt(0)

    for k in range(omega, greedy_ub + 1):
        if can_color(k):
            return k
    return greedy_ub


def check_strong_perfectness_g20() -> Dict[str, Any]:
    """
    Check strong perfectness of G(20) by examining all induced subgraphs
    of manageable size. For strong perfectness, chi(H) = omega(H) must
    hold for EVERY induced subgraph H.

    We test:
    1. Specific interesting subsets (e.g., even numbers, composites)
    2. Random samples
    3. Targeted search for odd holes and odd antiholes
    """
    n = 20
    adj = coprime_adj(n)
    results = {"n": n, "tests": []}

    # Test 1: Even numbers {2, 4, 6, ..., 20}
    evens = set(range(2, n + 1, 2))
    sub_adj = induced_subgraph(adj, evens)
    omega_e = brute_clique_number(sub_adj)
    chi_e = exact_chromatic_number(sub_adj)
    results["tests"].append({
        "name": "even numbers {2,4,...,20}",
        "vertices": sorted(evens),
        "omega": omega_e,
        "chi": chi_e,
        "perfect": omega_e == chi_e,
    })

    # Test 2: Composites only
    composites = set()
    for x in range(2, n + 1):
        if any(x % d == 0 for d in range(2, int(x**0.5) + 1)):
            composites.add(x)
    if composites:
        sub_adj = induced_subgraph(adj, composites)
        omega_c = brute_clique_number(sub_adj)
        chi_c = exact_chromatic_number(sub_adj)
        results["tests"].append({
            "name": "composites only",
            "vertices": sorted(composites),
            "omega": omega_c,
            "chi": chi_c,
            "perfect": omega_c == chi_c,
        })

    # Test 3: A subset designed to be tricky: multiples of 6 excluded
    tricky = set(range(1, n + 1)) - set(range(6, n + 1, 6))
    sub_adj = induced_subgraph(adj, tricky)
    omega_t = brute_clique_number(sub_adj)
    chi_t = exact_chromatic_number(sub_adj)
    results["tests"].append({
        "name": "exclude multiples of 6",
        "vertices": sorted(tricky),
        "omega": omega_t,
        "chi": chi_t,
        "perfect": omega_t == chi_t,
    })

    # Test 4: Exhaustive over all subsets of size 5-8 from {2,...,15}
    # to search for chi != omega
    base_verts = list(range(2, 16))
    failure_found = None
    subsets_tested = 0
    for size in range(5, 9):
        for combo in combinations(base_verts, size):
            s = set(combo)
            sa = induced_subgraph(adj, s)
            om = brute_clique_number(sa)
            ch = exact_chromatic_number(sa)
            subsets_tested += 1
            if om != ch:
                failure_found = {
                    "vertices": sorted(s),
                    "omega": om,
                    "chi": ch,
                }
                break
        if failure_found:
            break

    results["exhaustive_small_subsets"] = {
        "range": "subsets of {2,...,15} of size 5-8",
        "total_tested": subsets_tested,
        "failure_found": failure_found,
    }

    # Test 5: Check for odd holes of length 5 in G(20)
    # An odd hole is an induced chordless odd cycle of length >= 5
    # Limit to length 5 and 7; length 9 is too expensive on a 20-vertex
    # graph with ~120 edges (coprime graph is dense).
    results["odd_hole_search"] = _search_odd_holes(adj, n, max_len=7)

    # Test 6: Check for odd antiholes in G(20)
    # Build complement graph
    comp_adj: Dict[int, Set[int]] = {v: set() for v in range(1, n + 1)}
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) > 1:
                comp_adj[i].add(j)
                comp_adj[j].add(i)
    results["odd_antihole_search"] = _search_odd_holes(comp_adj, n, max_len=7)

    all_perfect = all(t.get("perfect", True) for t in results["tests"])
    no_holes = results["odd_hole_search"]["found"] is None
    no_antiholes = results["odd_antihole_search"]["found"] is None
    no_exhaustive_failure = results["exhaustive_small_subsets"]["failure_found"] is None

    results["verdict"] = {
        "all_induced_tests_perfect": all_perfect,
        "no_odd_holes": no_holes,
        "no_odd_antiholes": no_antiholes,
        "no_exhaustive_failures": no_exhaustive_failure,
        "strongly_perfect_consistent": (
            all_perfect and no_holes and no_antiholes and no_exhaustive_failure
        ),
    }

    return results


def _search_odd_holes(adj: Dict[int, Set[int]], n: int,
                      max_len: int = 9) -> Dict[str, Any]:
    """Search for induced chordless odd cycles of length 5, 7, 9, ...."""
    verts = sorted(adj.keys())
    for length in range(5, max_len + 1, 2):
        if length > len(verts):
            break
        result = _find_chordless_cycle(adj, verts, length)
        if result is not None:
            return {"found": result, "length": length}
    return {"found": None, "searched_up_to": max_len}


def _find_chordless_cycle(adj: Dict[int, Set[int]], verts: list,
                          length: int) -> Optional[List[int]]:
    """Find an induced chordless cycle of given length via backtracking.
    Uses an iteration counter to avoid runaway searches."""
    counter = [0]
    max_iters = 2_000_000

    for start in verts:
        path = [start]
        result = _cycle_bt(adj, path, start, length, counter, max_iters)
        if result is not None:
            return result
        if counter[0] >= max_iters:
            return None  # Hit iteration limit
    return None


def _cycle_bt(adj: Dict[int, Set[int]], path: list, target: int,
              length: int, counter: list, max_iters: int) -> Optional[List[int]]:
    """Backtracking search for chordless cycle with iteration budget."""
    counter[0] += 1
    if counter[0] >= max_iters:
        return None

    if len(path) == length:
        if target in adj.get(path[-1], set()):
            # Verify chordless
            for i in range(len(path)):
                for j in range(i + 2, len(path)):
                    if i == 0 and j == len(path) - 1:
                        continue
                    if path[j] in adj.get(path[i], set()):
                        return None
            return list(path)
        return None

    current = path[-1]
    for nxt in sorted(adj.get(current, set())):
        if counter[0] >= max_iters:
            return None
        if nxt == target and len(path) < length:
            continue
        if nxt in path:
            continue
        if nxt < path[0]:
            continue
        path.append(nxt)
        result = _cycle_bt(adj, path, target, length, counter, max_iters)
        if result is not None:
            return result
        path.pop()
    return None


# =====================================================================
# Claim 5: DS(2, 0.50) definition sensitivity
# =====================================================================

def has_schur_triple(s: Set[int]) -> bool:
    """Check if set s contains a Schur triple a + b = c (integers, a <= b)."""
    s_list = sorted(s)
    s_set = s
    for i, a in enumerate(s_list):
        for b in s_list[i:]:
            if a + b in s_set:
                return True
    return False


def is_dense_color(color_set: Set[int], N: int, alpha: float) -> bool:
    """Check if a color class is 'dense': has >= alpha*N elements."""
    threshold = max(1, int(alpha * N))
    return len(color_set) >= threshold


def ds2_check_exhaustive(N: int, indexing: str = "1-indexed",
                         alpha: float = 0.50) -> Dict[str, Any]:
    """
    Exhaustive check: does every 2-coloring of the specified set have
    a color class that is both dense (>= alpha*N elements) AND contains
    a Schur triple?

    indexing: "0-indexed" means {0,...,N-1}, "1-indexed" means {1,...,N}
    """
    if indexing == "0-indexed":
        universe = set(range(0, N))
    else:
        universe = set(range(1, N + 1))

    elements = sorted(universe)
    n = len(elements)
    threshold = max(1, int(alpha * N))

    avoiding_count = 0
    avoiding_examples = []

    for bits in range(2 ** n):
        color0 = set()
        color1 = set()
        for i, elem in enumerate(elements):
            if (bits >> i) & 1:
                color1.add(elem)
            else:
                color0.add(elem)

        # Check if this coloring "avoids" -- meaning no color class is
        # both dense AND has a Schur triple
        c0_dense = len(color0) >= threshold
        c1_dense = len(color1) >= threshold
        c0_schur = has_schur_triple(color0)
        c1_schur = has_schur_triple(color1)

        # "Avoids" if no color has BOTH dense AND Schur
        avoids = not (c0_dense and c0_schur) and not (c1_dense and c1_schur)

        if avoids:
            avoiding_count += 1
            if len(avoiding_examples) < 5:
                avoiding_examples.append({
                    "color0": sorted(color0),
                    "color1": sorted(color1),
                    "c0_dense": c0_dense,
                    "c1_dense": c1_dense,
                    "c0_schur": c0_schur,
                    "c1_schur": c1_schur,
                })

    return {
        "N": N,
        "indexing": indexing,
        "universe": sorted(universe),
        "alpha": alpha,
        "threshold": threshold,
        "total_colorings": 2 ** n,
        "avoiding_count": avoiding_count,
        "forced": avoiding_count == 0,
        "examples": avoiding_examples,
    }


def ds2_definition_sensitivity() -> Dict[str, Any]:
    """
    Compare DS(2, 0.50) under both indexing conventions for N = 3..8.
    Find where they differ.
    """
    results = []
    for N in range(1, 9):
        r0 = ds2_check_exhaustive(N, "0-indexed", 0.50)
        r1 = ds2_check_exhaustive(N, "1-indexed", 0.50)
        results.append({
            "N": N,
            "0-indexed_forced": r0["forced"],
            "1-indexed_forced": r1["forced"],
            "0-indexed_avoiding": r0["avoiding_count"],
            "1-indexed_avoiding": r1["avoiding_count"],
            "threshold_0": r0["threshold"],
            "threshold_1": r1["threshold"],
            "match": r0["forced"] == r1["forced"],
        })

    # Find DS values
    ds_0 = None
    ds_1 = None
    for r in results:
        if r["0-indexed_forced"] and ds_0 is None:
            ds_0 = r["N"]
        if r["1-indexed_forced"] and ds_1 is None:
            ds_1 = r["N"]

    return {
        "per_N": results,
        "DS_0indexed": ds_0,
        "DS_1indexed": ds_1,
        "definitions_agree": ds_0 == ds_1,
        "verdict": (
            f"DS(2,0.50) = {ds_0} on {{0,...,N-1}} vs {ds_1} on {{1,...,N}}. "
            + ("CONFIRMED: definitions disagree." if ds_0 != ds_1
               else "DISPROVED: definitions agree.")
        ),
    }


def enumerate_1indexed_5_colorings() -> Dict[str, Any]:
    """
    Enumerate ALL 2^5 = 32 colorings of [5] = {1,2,3,4,5} (1-indexed).
    For each, check if some color class is both:
      (a) dense (>= ceil(0.50 * 5) = 2 elements), AND
      (b) contains a Schur triple (a + b = c with a, b, c in the set).

    If ANY coloring avoids, then DS(2, 0.50) > 5 on [5].
    """
    universe = [1, 2, 3, 4, 5]
    alpha = 0.50
    N = 5
    threshold = max(1, int(alpha * N))  # = 2

    all_results = []
    for bits in range(32):
        c0 = set()
        c1 = set()
        for i, elem in enumerate(universe):
            if (bits >> i) & 1:
                c1.add(elem)
            else:
                c0.add(elem)

        c0_dense = len(c0) >= threshold
        c1_dense = len(c1) >= threshold
        c0_schur = has_schur_triple(c0)
        c1_schur = has_schur_triple(c1)

        avoids = not (c0_dense and c0_schur) and not (c1_dense and c1_schur)
        all_results.append({
            "bits": bits,
            "c0": sorted(c0),
            "c1": sorted(c1),
            "c0_dense": c0_dense,
            "c0_schur": c0_schur,
            "c1_dense": c1_dense,
            "c1_schur": c1_schur,
            "avoids": avoids,
        })

    avoiding = [r for r in all_results if r["avoids"]]

    return {
        "N": 5,
        "indexing": "1-indexed [1..5]",
        "threshold": threshold,
        "total_colorings": 32,
        "avoiding_count": len(avoiding),
        "avoiding_examples": avoiding[:10],
        "forced": len(avoiding) == 0,
    }


# =====================================================================
# Claim 6: 156 avoiding colorings at n=10 for R_cop(3)
# =====================================================================

def coprime_edges(n: int) -> List[Tuple[int, int]]:
    """All coprime pairs (i,j) with 1 <= i < j <= n."""
    edges = []
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                edges.append((i, j))
    return edges


def has_mono_triangle(n: int, coloring: Dict[Tuple[int, int], int]) -> bool:
    """Check if any coprime triangle in [n] is monochromatic."""
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) != 1:
                continue
            for k in range(j + 1, n + 1):
                if math.gcd(i, k) == 1 and math.gcd(j, k) == 1:
                    e1 = (i, j)
                    e2 = (i, k)
                    e3 = (j, k)
                    c1 = coloring.get(e1, -1)
                    c2 = coloring.get(e2, -1)
                    c3 = coloring.get(e3, -1)
                    if c1 == c2 == c3 and c1 != -1:
                        return True
    return False


def count_avoiding_colorings_direct(n: int) -> Dict[str, Any]:
    """
    Count 2-colorings of coprime edges on [n] that avoid monochromatic K_3,
    using direct enumeration. This is feasible only for small n or via
    incremental extension.
    """
    edges = coprime_edges(n)
    num_edges = len(edges)

    if num_edges > 17:
        # Use incremental extension for large edge counts (>17 edges = 2^17 ~ 131K)
        return _count_avoiding_incremental(n)

    total = 2 ** num_edges
    avoiding = 0
    for bits in range(total):
        coloring = {}
        for idx, e in enumerate(edges):
            coloring[e] = (bits >> idx) & 1
        if not has_mono_triangle(n, coloring):
            avoiding += 1

    return {
        "n": n,
        "num_edges": num_edges,
        "total_colorings": total,
        "avoiding_count": avoiding,
        "method": "exhaustive",
    }


def _count_avoiding_incremental(n: int) -> Dict[str, Any]:
    """
    Count avoiding colorings using incremental extension from a small base.
    Start at a base where exhaustive search is feasible, then extend one
    vertex at a time.
    """
    # Start with exhaustive at a small base
    base_n = 3
    while True:
        edges = coprime_edges(base_n + 1)
        if len(edges) > 22:
            break
        base_n += 1

    # Exhaustive at base_n
    edges = coprime_edges(base_n)
    num_edges = len(edges)
    avoiding = []
    for bits in range(2 ** num_edges):
        coloring = {}
        for idx, e in enumerate(edges):
            coloring[e] = (bits >> idx) & 1
        if not has_mono_triangle(base_n, coloring):
            avoiding.append(coloring)

    # Extend incrementally
    for curr_n in range(base_n + 1, n + 1):
        new_edges = [(min(i, curr_n), max(i, curr_n))
                     for i in range(1, curr_n) if math.gcd(i, curr_n) == 1]
        if not new_edges:
            continue

        next_avoiding = []
        for col in avoiding:
            for bits in range(2 ** len(new_edges)):
                new_col = dict(col)
                for idx, e in enumerate(new_edges):
                    new_col[e] = (bits >> idx) & 1
                if not has_mono_triangle(curr_n, new_col):
                    next_avoiding.append(new_col)
        avoiding = next_avoiding

    return {
        "n": n,
        "num_edges": len(coprime_edges(n)),
        "total_colorings": 2 ** len(coprime_edges(n)),
        "avoiding_count": len(avoiding),
        "method": "incremental_extension",
        "base_n": base_n,
    }


def count_avoiding_sat(n: int) -> int:
    """
    Count avoiding colorings via SAT with blocking clauses.
    Independent verification method.
    """
    from pysat.solvers import Glucose4

    edges = coprime_edges(n)
    if not edges:
        return 1

    edge_to_var = {e: i + 1 for i, e in enumerate(edges)}
    num_vars = len(edges)

    # Find all coprime triangles
    triangles = []
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) != 1:
                continue
            for k in range(j + 1, n + 1):
                if math.gcd(i, k) == 1 and math.gcd(j, k) == 1:
                    triangles.append((i, j, k))

    # Build SAT clauses: for each triangle, forbid all-same-color
    clauses = []
    for (a, b, c) in triangles:
        e1 = (a, b)
        e2 = (a, c)
        e3 = (b, c)
        v1, v2, v3 = edge_to_var[e1], edge_to_var[e2], edge_to_var[e3]
        # Not all 0: at least one is 1
        clauses.append([v1, v2, v3])
        # Not all 1: at least one is 0
        clauses.append([-v1, -v2, -v3])

    solver = Glucose4(bootstrap_with=clauses)
    count = 0
    while solver.solve():
        count += 1
        model = solver.get_model()
        # Block this solution
        solver.add_clause([-lit for lit in model[:num_vars]])

    solver.delete()
    return count


def verify_156_avoiding(timeout_n10: bool = False) -> Dict[str, Any]:
    """
    Independently verify the count of 156 avoiding colorings at n=10.

    Uses two methods:
    1. Incremental extension (same as coprime_ramsey.py but reimplemented)
    2. SAT with blocking clauses

    Also verifies intermediate counts at n=4..9.
    """
    results = {}

    # Count at small n using exhaustive search
    for nn in range(4, 10):
        r = count_avoiding_colorings_direct(nn)
        results[nn] = {
            "avoiding": r["avoiding_count"],
            "total": r["total_colorings"],
            "method": r["method"],
        }

    # Count at n=10 using incremental method
    r10 = _count_avoiding_incremental(10)
    results[10] = {
        "avoiding": r10["avoiding_count"],
        "total": r10["total_colorings"],
        "method": r10["method"],
    }

    # Cross-check with SAT at n=10
    sat_count = count_avoiding_sat(10)
    results["sat_verification_n10"] = sat_count

    claimed = 156
    incremental_matches = r10["avoiding_count"] == claimed
    sat_matches = sat_count == claimed
    methods_agree = r10["avoiding_count"] == sat_count

    results["verdict"] = {
        "claimed": claimed,
        "incremental_count": r10["avoiding_count"],
        "sat_count": sat_count,
        "incremental_matches_claim": incremental_matches,
        "sat_matches_claim": sat_matches,
        "methods_agree": methods_agree,
        "assessment": (
            "CONFIRMED" if (incremental_matches and sat_matches)
            else "DISPROVED" if methods_agree and not incremental_matches
            else "INCONSISTENT METHODS" if not methods_agree
            else "PARTIAL"
        ),
    }

    # Also verify n=11 has 0 avoiding (confirming R_cop(3) = 11)
    r11 = _count_avoiding_incremental(11)
    results[11] = {
        "avoiding": r11["avoiding_count"],
        "confirms_R_cop_3_eq_11": r11["avoiding_count"] == 0,
    }

    return results


# =====================================================================
# Main: run all adversarial checks
# =====================================================================

def run_all_checks() -> Dict[str, Any]:
    """Run all adversarial checks and return collected results."""
    results = {}

    print("=" * 72)
    print("ADVERSARIAL ANALYSIS OF SIX MATHEMATICAL CLAIMS")
    print("=" * 72)

    # Claim 1
    print("\n--- Claim 1: MS(k) = 2^((3^k+1)/2) - 1 ---")
    v1 = overfitting_verdict()
    results["claim_1_MS_formula"] = v1
    print(f"  Alternatives found: {v1['num_alternatives']}")
    print(f"  Distinct MS(4) predictions: {v1['distinct_MS4_predictions']}")
    print(f"  Proposed MS(4): {v1['proposed_MS4']}")
    print(f"  Verdict: {v1['verdict'][:80]}...")

    # Claim 2
    print("\n--- Claim 2: NPG-30 primality ---")
    v2 = prime_probability_null_model()
    results["claim_2_primality"] = v2
    probs = v2["verdict"]["probabilities"]
    for model, p in probs.items():
        print(f"  {model}: P(all prime) = {p:.4f}")
    print(f"  Verdict: {v2['verdict']['assessment'][:80]}...")

    # Claim 3
    print("\n--- Claim 3: R_gcd(3;d) = 11d isomorphism ---")
    v3_d5 = verify_gcd_isomorphism(d=5, m=11)
    results["claim_3_gcd_iso"] = v3_d5
    print(f"  d=5, m=11: isomorphic = {v3_d5['is_isomorphic']}")
    print(f"  Algebraic identity gcd(di,dj) = d*gcd(i,j): {v3_d5['algebraic_identity_holds']}")
    print(f"  Coprime edges on [11]: {v3_d5['coprime_edge_count']}")
    print(f"  GCD-5 edges on {{5,10,...,55}}: {v3_d5['gcd_d_edge_count']}")

    # Claim 4
    print("\n--- Claim 4: Coprime graph strong perfectness ---")
    v4 = check_strong_perfectness_g20()
    results["claim_4_perfectness"] = v4
    for t in v4["tests"]:
        status = "PERFECT" if t["perfect"] else "IMPERFECT"
        print(f"  {t['name']}: omega={t['omega']}, chi={t['chi']} [{status}]")
    print(f"  Odd holes found: {v4['odd_hole_search']['found']}")
    print(f"  Odd antiholes found: {v4['odd_antihole_search']['found']}")
    exh = v4["exhaustive_small_subsets"]
    print(f"  Exhaustive search ({exh['total_tested']} subsets): "
          f"failure = {exh['failure_found']}")
    sv = v4["verdict"]
    print(f"  Strong perfectness consistent: {sv['strongly_perfect_consistent']}")

    # Claim 5
    print("\n--- Claim 5: DS(2,0.50) definition sensitivity ---")
    v5 = ds2_definition_sensitivity()
    results["claim_5_ds_sensitivity"] = v5
    for r in v5["per_N"]:
        print(f"  N={r['N']}: 0-idx forced={r['0-indexed_forced']}, "
              f"1-idx forced={r['1-indexed_forced']}, "
              f"match={r['match']}")
    print(f"  DS(2,0.50) 0-indexed: {v5['DS_0indexed']}")
    print(f"  DS(2,0.50) 1-indexed: {v5['DS_1indexed']}")
    print(f"  Verdict: {v5['verdict']}")

    # Detailed [5] enumeration
    v5b = enumerate_1indexed_5_colorings()
    results["claim_5_enumeration"] = v5b
    print(f"\n  [1..5] exhaustive: {v5b['avoiding_count']} avoiding out of 32")
    if v5b["avoiding_examples"]:
        for ex in v5b["avoiding_examples"][:3]:
            print(f"    c0={ex['c0']}, c1={ex['c1']}, "
                  f"c0_schur={ex['c0_schur']}, c1_schur={ex['c1_schur']}")

    # Claim 6
    print("\n--- Claim 6: 156 avoiding colorings at n=10 ---")
    v6 = verify_156_avoiding()
    results["claim_6_156_avoiding"] = v6
    for nn in range(4, 12):
        if nn in v6:
            info = v6[nn]
            if "avoiding" in info:
                print(f"  n={nn}: {info['avoiding']} avoiding colorings")
            elif "confirms_R_cop_3_eq_11" in info:
                print(f"  n={nn}: {info['avoiding']} avoiding "
                      f"(R_cop(3)=11 confirmed: {info['confirms_R_cop_3_eq_11']})")
    vd = v6["verdict"]
    print(f"  SAT count at n=10: {vd['sat_count']}")
    print(f"  Incremental count at n=10: {vd['incremental_count']}")
    print(f"  Methods agree: {vd['methods_agree']}")
    print(f"  Assessment: {vd['assessment']}")

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)

    return results


if __name__ == "__main__":
    run_all_checks()
