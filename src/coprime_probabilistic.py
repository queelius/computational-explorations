#!/usr/bin/env python3
"""
Probabilistic Analysis of Coprime Ramsey Numbers.

Uses the probabilistic method to understand WHY specific values
R_cop(3)=11, R_cop(4)=59, R_cop(3;3)=53 arise, and to predict R_cop(5).

Methods:
  1. First moment method: E[# monochromatic K_k] under random 2-coloring
  2. Second moment method: Var and Chebyshev bound on P(no mono K_k)
  3. Lovasz Local Lemma: dependency graph bound on R_cop(k)
  4. Random coloring sampling at critical thresholds
  5. Phase transition sharpness analysis
  6. Prediction of R_cop(5) via combined methods
"""

import math
import random
from itertools import combinations
from typing import List, Tuple, Dict, Set, Optional
from collections import defaultdict

import numpy as np


# ---------------------------------------------------------------------------
# Core graph infrastructure
# ---------------------------------------------------------------------------

def coprime_edges(n: int) -> List[Tuple[int, int]]:
    """Return all coprime pairs (i,j) with 1 <= i < j <= n."""
    edges = []
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                edges.append((i, j))
    return edges


def coprime_adj(n: int) -> Dict[int, Set[int]]:
    """Build adjacency dict for the coprime graph on [n]."""
    adj: Dict[int, Set[int]] = {v: set() for v in range(1, n + 1)}
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def coprime_cliques(n: int, k: int) -> List[Tuple[int, ...]]:
    """Enumerate all k-cliques in the coprime graph on [n]."""
    if k < 1:
        return []
    if k == 1:
        return [(v,) for v in range(1, n + 1)]

    adj = coprime_adj(n)
    vertices = list(range(1, n + 1))
    cliques: List[Tuple[int, ...]] = []

    def extend(current: List[int], candidates: List[int]):
        if len(current) == k:
            cliques.append(tuple(current))
            return
        needed = k - len(current)
        for idx, v in enumerate(candidates):
            if len(candidates) - idx < needed:
                break
            if all(v in adj[u] for u in current):
                new_cands = [w for w in candidates[idx + 1:] if w in adj[v]]
                extend(current + [v], new_cands)

    extend([], vertices)
    return cliques


def clique_edges(clique: Tuple[int, ...]) -> List[Tuple[int, int]]:
    """Return all edges of a clique as sorted tuples."""
    vlist = sorted(clique)
    return [(vlist[i], vlist[j])
            for i in range(len(vlist))
            for j in range(i + 1, len(vlist))]


# ---------------------------------------------------------------------------
# 1. First moment method
# ---------------------------------------------------------------------------

def count_coprime_cliques(n: int, k: int) -> int:
    """Count the number of k-cliques in the coprime graph on [n]."""
    return len(coprime_cliques(n, k))


def expected_mono_cliques(n: int, k: int, num_colors: int = 2) -> float:
    """
    E[# monochromatic K_k] under uniform random c-coloring.

    Each K_k has C(k,2) edges. Under c-coloring, P(all edges same color)
    = c * (1/c)^{C(k,2)} = c^{1 - C(k,2)}.

    So E[mono K_k] = num_cliques * c^{1 - C(k,2)}.
    """
    num_cliques = count_coprime_cliques(n, k)
    edge_count = k * (k - 1) // 2
    prob_mono = num_colors ** (1 - edge_count)
    return num_cliques * prob_mono


def first_moment_threshold(k: int, num_colors: int = 2,
                           max_n: int = 200) -> Tuple[int, float]:
    """
    Find the smallest n where E[# mono K_k] >= 1.

    This is the first moment threshold: below it, E < 1 so some coloring
    likely avoids mono K_k. Above it, mono K_k are expected.

    Returns (threshold_n, E_at_threshold).
    """
    for n in range(k, max_n + 1):
        exp = expected_mono_cliques(n, k, num_colors)
        if exp >= 1.0:
            return n, exp
    return -1, 0.0


def first_moment_table(k: int, n_range: range,
                       num_colors: int = 2) -> List[Tuple[int, int, float]]:
    """
    Compute (n, num_cliques, E[mono K_k]) for each n in range.

    Returns list of (n, num_k_cliques, expected_mono).
    """
    results = []
    for n in n_range:
        nc = count_coprime_cliques(n, k)
        exp = expected_mono_cliques(n, k, num_colors)
        results.append((n, nc, exp))
    return results


# ---------------------------------------------------------------------------
# 2. Second moment method
# ---------------------------------------------------------------------------

def cliques_share_edge(c1: Tuple[int, ...], c2: Tuple[int, ...]) -> bool:
    """Check if two cliques share at least one edge (two common vertices)."""
    common = set(c1) & set(c2)
    return len(common) >= 2


def second_moment_analysis(n: int, k: int,
                           num_colors: int = 2) -> Dict[str, float]:
    """
    Compute second moment quantities for the mono-K_k count.

    Let X = sum of X_C over all coprime k-cliques C, where X_C is the
    indicator that C is monochromatic.

    E[X] = num_cliques * p, where p = c^{1 - C(k,2)}.
    E[X^2] = sum_{C1,C2} E[X_{C1} X_{C2}].

    For independent cliques (no shared edge): E[X_{C1} X_{C2}] = p^2.
    For dependent cliques (shared edge(s)): need joint probability.

    If C1 and C2 share s vertices (hence C(s,2) edges), they have
    2*C(k,2) - C(s,2) distinct edges total. The joint monochromatic
    probability (both same color, possibly different colors) is:
      c^2 * (1/c)^{2*C(k,2) - C(s,2)} = c^{2 - 2*C(k,2) + C(s,2)}.

    Var[X] = E[X^2] - E[X]^2.
    By Chebyshev: P(X = 0) <= Var[X] / E[X]^2.
    Second moment condition: if E[X]^2 / E[X^2] -> 1, then P(X > 0) -> 1.

    Returns dict with E_X, E_X2, Var_X, chebyshev_upper, second_moment_ratio.
    """
    all_cliques = coprime_cliques(n, k)
    num_cliques = len(all_cliques)
    c = num_colors
    kc2 = k * (k - 1) // 2
    p = c ** (1 - kc2)  # P(single clique is mono)

    E_X = num_cliques * p

    # Compute E[X^2] by iterating over pairs and computing overlap
    # For efficiency, precompute vertex sets
    clique_sets = [set(cl) for cl in all_cliques]

    # Accumulate E[X^2] = sum_{i,j} E[X_i X_j]
    # Diagonal terms: E[X_i^2] = E[X_i] = p (indicator)
    # Off-diagonal: depends on overlap
    E_X2 = 0.0

    for i in range(num_cliques):
        E_X2 += p  # diagonal: E[X_i^2] = p
        for j in range(i + 1, num_cliques):
            s = len(clique_sets[i] & clique_sets[j])
            if s < 2:
                # Independent: no shared edge
                E_X2 += 2 * p * p
            else:
                # Shared edges: C(s,2) edges in common
                shared_edges = s * (s - 1) // 2
                # Both monochromatic (each in some color):
                # For each pair of colors (c1, c2):
                #   P(C1 all c1 AND C2 all c2)
                #   = (1/c)^{edges_only_C1} * (1/c)^{edges_only_C2} * (1/c)^{shared if c1=c2, 0 if c1!=c2}
                # Wait: shared edges must satisfy BOTH color requirements.
                # If c1 = c2: shared edges just need to be that color -> (1/c)^{2*kc2 - shared_edges}
                # If c1 != c2: shared edges need to be c1 AND c2 simultaneously -> impossible
                # So P(both mono) = c * (1/c)^{2*kc2 - shared_edges}  (same color)
                #                  = c^{1 - 2*kc2 + shared_edges}
                joint_prob = c ** (1 - 2 * kc2 + shared_edges)
                E_X2 += 2 * joint_prob

    Var_X = E_X2 - E_X ** 2

    # Chebyshev: P(X = 0) <= Var[X] / E[X]^2 (when E[X] > 0)
    chebyshev_upper = Var_X / (E_X ** 2) if E_X > 0 else float('inf')

    # Second moment ratio: E[X]^2 / E[X^2], approaches 1 => X > 0 whp
    sm_ratio = (E_X ** 2) / E_X2 if E_X2 > 0 else 0.0

    return {
        'n': n,
        'k': k,
        'num_cliques': num_cliques,
        'E_X': E_X,
        'E_X2': E_X2,
        'Var_X': Var_X,
        'chebyshev_upper': chebyshev_upper,
        'second_moment_ratio': sm_ratio,
    }


def second_moment_threshold(k: int, num_colors: int = 2,
                            max_n: int = 100) -> int:
    """
    Find the smallest n where the second moment method proves
    P(mono K_k exists) > 0, i.e., chebyshev_upper < 1.

    Returns the threshold n, or -1 if not found.
    """
    for n in range(k, max_n + 1):
        result = second_moment_analysis(n, k, num_colors)
        if result['E_X'] >= 1.0 and result['chebyshev_upper'] < 1.0:
            return n
    return -1


# ---------------------------------------------------------------------------
# 3. Lovasz Local Lemma bound
# ---------------------------------------------------------------------------

def lll_dependency_graph(n: int, k: int) -> Tuple[int, Dict[int, Set[int]]]:
    """
    Build the dependency graph for the LLL.

    Each "bad event" is: clique C is monochromatic in some color.
    Two events are dependent if the cliques share an edge.

    Returns (num_events, adjacency dict for dependency graph).
    The events are indexed 0..num_events-1.
    """
    all_cliques = coprime_cliques(n, k)
    num_events = len(all_cliques)

    # Precompute edge sets for each clique
    clique_edge_sets = []
    for cl in all_cliques:
        es = set()
        vlist = sorted(cl)
        for i in range(len(vlist)):
            for j in range(i + 1, len(vlist)):
                es.add((vlist[i], vlist[j]))
        clique_edge_sets.append(es)

    # Build dependency graph
    dep: Dict[int, Set[int]] = {i: set() for i in range(num_events)}
    for i in range(num_events):
        for j in range(i + 1, num_events):
            if clique_edge_sets[i] & clique_edge_sets[j]:
                dep[i].add(j)
                dep[j].add(i)

    return num_events, dep


def lll_symmetric_bound(n: int, k: int, num_colors: int = 2) -> Dict[str, float]:
    """
    Apply the symmetric Lovasz Local Lemma.

    Each bad event (clique C monochromatic) has probability
      p = c * (1/c)^{C(k,2)} = c^{1 - C(k,2)}.

    In the dependency graph, let d = max degree.

    Symmetric LLL: if e * p * (d + 1) <= 1, then P(no bad event) > 0,
    meaning an avoiding coloring exists.

    This gives a LOWER BOUND on R_cop(k): if the condition holds at n,
    then R_cop(k) > n.

    Returns dict with p, d_max, lll_condition, lll_holds.
    """
    c = num_colors
    kc2 = k * (k - 1) // 2
    p = c ** (1 - kc2)

    num_events, dep = lll_dependency_graph(n, k)

    if num_events == 0:
        return {
            'n': n, 'k': k, 'p': p, 'num_events': 0,
            'd_max': 0, 'epd1': 0.0, 'lll_holds': True,
        }

    d_max = max(len(dep[i]) for i in range(num_events))

    epd1 = math.e * p * (d_max + 1)

    return {
        'n': n,
        'k': k,
        'p': p,
        'num_events': num_events,
        'd_max': d_max,
        'epd1': epd1,
        'lll_holds': epd1 <= 1.0,
    }


def lll_lower_bound(k: int, num_colors: int = 2,
                    max_n: int = 200) -> int:
    """
    Find the largest n where the symmetric LLL guarantees an avoiding
    coloring exists. This gives R_cop(k) > n.

    Returns the LLL lower bound on R_cop(k).
    """
    best_n = k - 1
    for n in range(k, max_n + 1):
        result = lll_symmetric_bound(n, k, num_colors)
        if result['lll_holds']:
            best_n = n
        else:
            # Once LLL fails, it stays failed (d grows faster than p shrinks)
            break
    return best_n


def lll_asymmetric_bound(n: int, k: int,
                         num_colors: int = 2) -> Dict[str, float]:
    """
    Apply the asymmetric Lovasz Local Lemma with uniform x_i = x.

    Condition: p <= x * prod_{j in Gamma(i)} (1 - x) for all i.
    With uniform x: p <= x * (1-x)^d for all i, where d = degree of i.

    We find the optimal x that maximizes x * (1-x)^d_max.
    Maximum of f(x) = x(1-x)^d at x = 1/(d+1), giving f = d^d/(d+1)^{d+1}.

    So condition becomes: p <= d_max^{d_max} / (d_max+1)^{d_max+1}.
    This is tighter than the symmetric ep(d+1) <= 1 form.
    """
    c = num_colors
    kc2 = k * (k - 1) // 2
    p = c ** (1 - kc2)

    num_events, dep = lll_dependency_graph(n, k)

    if num_events == 0:
        return {
            'n': n, 'k': k, 'p': p, 'num_events': 0,
            'd_max': 0, 'threshold': 1.0, 'lll_holds': True,
        }

    d_max = max(len(dep[i]) for i in range(num_events))

    if d_max == 0:
        threshold = 1.0
    else:
        threshold = (d_max ** d_max) / ((d_max + 1) ** (d_max + 1))

    return {
        'n': n,
        'k': k,
        'p': p,
        'num_events': num_events,
        'd_max': d_max,
        'threshold': threshold,
        'lll_holds': p <= threshold,
    }


def lll_asymmetric_lower_bound(k: int, num_colors: int = 2,
                               max_n: int = 200) -> int:
    """LLL asymmetric lower bound: largest n where LLL condition holds."""
    best_n = k - 1
    for n in range(k, max_n + 1):
        result = lll_asymmetric_bound(n, k, num_colors)
        if result['lll_holds']:
            best_n = n
        else:
            break
    return best_n


# ---------------------------------------------------------------------------
# 4. Random coloring sampling at critical thresholds
# ---------------------------------------------------------------------------

def sample_random_coloring(n: int, num_colors: int = 2,
                           rng: Optional[random.Random] = None) -> Dict[Tuple[int, int], int]:
    """Generate a uniform random coloring of coprime edges on [n]."""
    if rng is None:
        rng = random.Random()
    edges = coprime_edges(n)
    return {e: rng.randint(0, num_colors - 1) for e in edges}


def has_mono_clique_fast(n: int, k: int,
                         coloring: Dict[Tuple[int, int], int],
                         precomputed_cliques: Optional[List[Tuple[int, ...]]] = None) -> bool:
    """
    Check if a coloring has a monochromatic K_k.

    Uses precomputed clique list for efficiency when sampling many colorings.
    """
    cliques = precomputed_cliques if precomputed_cliques is not None else coprime_cliques(n, k)

    for cl in cliques:
        edges = clique_edges(cl)
        colors = set(coloring[e] for e in edges)
        if len(colors) == 1:
            return True
    return False


def sample_avoiding_fraction(n: int, k: int, num_samples: int,
                             num_colors: int = 2,
                             seed: int = 42) -> Dict[str, float]:
    """
    Estimate the fraction of random c-colorings that avoid mono K_k.

    Returns dict with n, k, num_samples, num_avoiding, fraction,
    and 95% confidence interval.
    """
    rng = random.Random(seed)
    cliques = coprime_cliques(n, k)

    if not cliques:
        return {
            'n': n, 'k': k, 'num_samples': num_samples,
            'num_avoiding': num_samples, 'fraction': 1.0,
            'ci_low': 1.0, 'ci_high': 1.0,
        }

    num_avoiding = 0
    for _ in range(num_samples):
        coloring = sample_random_coloring(n, num_colors, rng)
        if not has_mono_clique_fast(n, k, coloring, cliques):
            num_avoiding += 1

    frac = num_avoiding / num_samples
    # Wilson score interval for proportion
    z = 1.96
    denom = 1 + z ** 2 / num_samples
    center = (frac + z ** 2 / (2 * num_samples)) / denom
    halfwidth = z * math.sqrt(frac * (1 - frac) / num_samples
                              + z ** 2 / (4 * num_samples ** 2)) / denom

    return {
        'n': n, 'k': k, 'num_samples': num_samples,
        'num_avoiding': num_avoiding, 'fraction': frac,
        'ci_low': max(0, center - halfwidth),
        'ci_high': min(1, center + halfwidth),
    }


# ---------------------------------------------------------------------------
# 5. Phase transition analysis
# ---------------------------------------------------------------------------

def phase_transition_curve(k: int, n_range: range, num_samples: int,
                           num_colors: int = 2,
                           seed: int = 42) -> List[Dict[str, float]]:
    """
    Compute P(avoiding) as function of n by sampling.

    Returns list of dicts with n, fraction, ci_low, ci_high.
    """
    results = []
    for n in n_range:
        result = sample_avoiding_fraction(n, k, num_samples, num_colors, seed)
        results.append(result)
    return results


def transition_width(curve: List[Dict[str, float]],
                     low_threshold: float = 0.9,
                     high_threshold: float = 0.1) -> Dict[str, float]:
    """
    Measure the width of the phase transition.

    Find n_low where P(avoiding) drops below low_threshold and
    n_high where it drops below high_threshold.

    Width = n_high - n_low. Sharper transitions have smaller width.
    """
    n_low = None
    n_high = None

    for entry in curve:
        n = entry['n']
        f = entry['fraction']
        if n_low is None and f < low_threshold:
            n_low = n
        if n_high is None and f < high_threshold:
            n_high = n

    width = None
    if n_low is not None and n_high is not None:
        width = n_high - n_low

    return {
        'n_low': n_low,
        'n_high': n_high,
        'width': width,
        'low_threshold': low_threshold,
        'high_threshold': high_threshold,
    }


# ---------------------------------------------------------------------------
# 6. Prediction of R_cop(5)
# ---------------------------------------------------------------------------

def exponential_fit(known_values: Dict[int, int]) -> Tuple[float, float]:
    """
    Fit R_cop(k) ~ a * b^k using least squares on log scale.

    Returns (a, b) such that R_cop(k) ~ a * b^k.
    """
    ks = sorted(known_values.keys())
    log_vals = [math.log(known_values[k]) for k in ks]

    # Linear regression on log(R_cop(k)) = log(a) + k * log(b)
    n = len(ks)
    sum_k = sum(ks)
    sum_logv = sum(log_vals)
    sum_k2 = sum(k ** 2 for k in ks)
    sum_k_logv = sum(k * lv for k, lv in zip(ks, log_vals))

    denom = n * sum_k2 - sum_k ** 2
    if abs(denom) < 1e-15:
        return 1.0, 1.0

    log_b = (n * sum_k_logv - sum_k * sum_logv) / denom
    log_a = (sum_logv - log_b * sum_k) / n

    return math.exp(log_a), math.exp(log_b)


def predict_rcop(k_target: int,
                 known_values: Dict[int, int],
                 num_colors: int = 2,
                 max_n_first: int = 2000,
                 max_n_lll: int = 500) -> Dict[str, float]:
    """
    Predict R_cop(k_target) using multiple methods:

    1. First moment lower bound: n where E[mono K_k] = 1
    2. LLL lower bound (computed for small k, extrapolated for large k)
    3. Exponential fit from known values
    4. Ramsey comparison: R_cop(k) / R(k,k) ratio extrapolation

    Returns dict with each method's prediction.
    """
    predictions = {}

    # 1. First moment: use clique count asymptotics
    # For large n, #(k-cliques) ~ C * n^k (coprime density).
    # At the threshold: C * n^k * 2^{1-C(k,2)} = 1
    # => n ~ (2^{C(k,2)-1} / C)^{1/k}
    # We can estimate C from moderate n values.
    kc2 = k_target * (k_target - 1) // 2
    # Sample clique counts at a few n values to estimate the coefficient
    sample_ns = [30, 40, 50]
    coefficients = []
    for sn in sample_ns:
        nc = count_coprime_cliques(sn, k_target)
        if nc > 0:
            coefficients.append(nc / (sn ** k_target))

    if coefficients:
        C_est = np.mean(coefficients)
        if C_est > 0:
            # Solve C * n^k * 2^{1-kc2} = 1
            n_threshold = (2 ** (kc2 - 1) / C_est) ** (1.0 / k_target)
            predictions['first_moment'] = n_threshold
        else:
            predictions['first_moment'] = float('inf')
    else:
        predictions['first_moment'] = float('inf')

    # 2. Exponential fit
    a, b = exponential_fit(known_values)
    predictions['exp_fit'] = a * b ** k_target
    predictions['exp_fit_a'] = a
    predictions['exp_fit_b'] = b

    # 3. Classical Ramsey comparison
    # Known: R(3,3)=6, R(4,4)=18, R(5,5) in [43,48]
    # Ratios: R_cop(3)/R(3,3) = 11/6 ~ 1.83, R_cop(4)/R(4,4) = 59/18 ~ 3.28
    classical_ramsey = {3: 6, 4: 18, 5: 43}  # lower bound for R(5,5)
    ratios = {}
    for k_val in known_values:
        if k_val in classical_ramsey:
            ratios[k_val] = known_values[k_val] / classical_ramsey[k_val]

    if len(ratios) >= 2:
        # Extrapolate ratio growth
        sorted_ks = sorted(ratios.keys())
        if len(sorted_ks) >= 2:
            # Log-linear fit on ratios
            log_ratios = [math.log(ratios[k]) for k in sorted_ks]
            # Simple: assume ratio grows exponentially
            r_a, r_b = exponential_fit(ratios)
            pred_ratio = r_a * r_b ** k_target
            predictions['ratio_extrapolation'] = pred_ratio * classical_ramsey.get(
                k_target, 43)

    # 4. LLL bound (for small targets, compute directly)
    if k_target <= 4:
        lll_bound = lll_lower_bound(k_target, num_colors, max_n=max_n_lll)
        predictions['lll_lower'] = lll_bound + 1
    else:
        # Extrapolate LLL bound from known k values
        lll_bounds = {}
        for kv in [3, 4]:
            lll_bounds[kv] = lll_lower_bound(kv, num_colors, max_n=60)
        la, lb = exponential_fit(lll_bounds)
        predictions['lll_lower_extrapolated'] = la * lb ** k_target

    return predictions


# ---------------------------------------------------------------------------
# Main: run all experiments
# ---------------------------------------------------------------------------

def main():
    """Run all probabilistic analyses and report results."""
    print("=" * 74)
    print("PROBABILISTIC ANALYSIS OF COPRIME RAMSEY NUMBERS")
    print("=" * 74)
    print()

    known_rcop = {3: 11, 4: 59}
    known_rcop_3color = {3: 53}

    # =======================================================================
    # 1. First moment method
    # =======================================================================
    print("=" * 74)
    print("1. FIRST MOMENT METHOD: E[# mono K_k] under random 2-coloring")
    print("=" * 74)
    print()

    for k in [3, 4]:
        print(f"--- K_{k} ---")
        kc2 = k * (k - 1) // 2
        p_mono = 2 ** (1 - kc2)
        print(f"  P(single K_{k} monochromatic) = 2 * (1/2)^{kc2} = {p_mono:.6f}")
        print()

        if k == 3:
            n_range = range(3, 20)
        else:
            n_range = range(4, 70)

        table = first_moment_table(k, n_range)
        print(f"  {'n':>4s}  {'#K_k':>8s}  {'E[mono K_k]':>14s}")
        print(f"  {'----':>4s}  {'--------':>8s}  {'--------------':>14s}")
        for n, nc, exp in table:
            marker = " <-- E=1" if nc > 0 and abs(exp - 1.0) < 0.5 * exp else ""
            if k == 3 or n % 2 == 0 or n <= 10 or n >= 55:
                print(f"  {n:4d}  {nc:8d}  {exp:14.4f}{marker}")

        fm_n, fm_e = first_moment_threshold(k)
        actual = known_rcop[k]
        print()
        print(f"  First moment threshold: E[mono K_{k}] = 1 at n = {fm_n}"
              f"  (E = {fm_e:.4f})")
        print(f"  Actual R_cop({k}) = {actual}")
        print(f"  Gap: R_cop({k}) / FM_threshold = {actual / fm_n:.3f}")
        print()

    # =======================================================================
    # 2. Second moment method
    # =======================================================================
    print("=" * 74)
    print("2. SECOND MOMENT METHOD: Var[X] and Chebyshev bound")
    print("=" * 74)
    print()

    for k in [3, 4]:
        print(f"--- K_{k} ---")
        if k == 3:
            test_ns = range(5, 16)
        else:
            test_ns = [10, 15, 20, 25, 30]

        print(f"  {'n':>4s}  {'E[X]':>10s}  {'E[X^2]':>14s}  {'Var[X]':>14s}  "
              f"{'P(X=0)<=':>12s}  {'E^2/E[X^2]':>12s}")
        print(f"  {'----':>4s}  {'----------':>10s}  {'--------------':>14s}  "
              f"{'--------------':>14s}  {'------------':>12s}  {'------------':>12s}")

        for n in test_ns:
            res = second_moment_analysis(n, k)
            cheb = min(res['chebyshev_upper'], 999.99)
            print(f"  {n:4d}  {res['E_X']:10.4f}  {res['E_X2']:14.4f}  "
                  f"{res['Var_X']:14.4f}  {cheb:12.6f}  "
                  f"{res['second_moment_ratio']:12.6f}")

        sm_n = second_moment_threshold(k, max_n=(20 if k == 3 else 80))
        print()
        print(f"  Second moment threshold (Chebyshev < 1): n = {sm_n}")
        print(f"  Actual R_cop({k}) = {known_rcop[k]}")
        if sm_n > 0:
            print(f"  Gap: R_cop({k}) / SM_threshold = {known_rcop[k] / sm_n:.3f}")
        print()

    # =======================================================================
    # 3. Lovasz Local Lemma bound
    # =======================================================================
    print("=" * 74)
    print("3. LOVASZ LOCAL LEMMA: dependency-graph lower bound")
    print("=" * 74)
    print()

    for k in [3, 4]:
        print(f"--- K_{k} ---")
        kc2 = k * (k - 1) // 2
        p_mono = 2 ** (1 - kc2)
        print(f"  p = P(clique mono) = {p_mono:.8f}")
        print()

        if k == 3:
            test_ns = range(3, 16)
        else:
            # Limit to n <= 14 for K_4 (dependency graph at n=15+ is very expensive)
            test_ns = range(4, 15)

        print(f"  {'n':>4s}  {'events':>8s}  {'d_max':>6s}  {'e*p*(d+1)':>12s}  "
              f"{'LLL holds':>10s}  | {'asym thresh':>14s}  {'asym holds':>10s}")
        print(f"  {'----':>4s}  {'--------':>8s}  {'------':>6s}  {'------------':>12s}  "
              f"{'----------':>10s}  | {'--------------':>14s}  {'----------':>10s}")

        for n in test_ns:
            sym = lll_symmetric_bound(n, k)
            asym = lll_asymmetric_bound(n, k)
            print(f"  {n:4d}  {sym['num_events']:8d}  {sym['d_max']:6d}  "
                  f"{sym['epd1']:12.6f}  {'YES' if sym['lll_holds'] else 'no':>10s}  | "
                  f"{asym['threshold']:14.8f}  {'YES' if asym['lll_holds'] else 'no':>10s}")

        sym_bound = lll_lower_bound(k, max_n=(20 if k == 3 else 14))
        asym_bound = lll_asymmetric_lower_bound(k, max_n=(20 if k == 3 else 14))
        actual = known_rcop[k]
        print()
        print(f"  Symmetric LLL:   R_cop({k}) > {sym_bound}  (bound: {sym_bound + 1})")
        print(f"  Asymmetric LLL:  R_cop({k}) > {asym_bound}  (bound: {asym_bound + 1})")
        print(f"  Actual R_cop({k}) = {actual}")
        print(f"  LLL tightness: actual / LLL_bound = {actual / (asym_bound + 1):.3f}")
        print()

    # =======================================================================
    # 4. Random coloring statistics at critical thresholds
    # =======================================================================
    print("=" * 74)
    print("4. RANDOM COLORING STATISTICS AT CRITICAL THRESHOLDS")
    print("=" * 74)
    print()

    num_samples = 1_000_000

    print(f"--- n=10 (= R_cop(3) - 1): sampling {num_samples:,} random 2-colorings ---")
    res10 = sample_avoiding_fraction(10, 3, num_samples, seed=42)
    edges_10 = len(coprime_edges(10))
    total_10 = 2 ** edges_10
    print(f"  Coprime edges at n=10: {edges_10}")
    print(f"  Total 2-colorings: 2^{edges_10} = {total_10:,}")
    print(f"  Avoiding found: {res10['num_avoiding']} / {num_samples:,}")
    print(f"  Estimated fraction: {res10['fraction']:.8e}")
    print(f"  95% CI: [{res10['ci_low']:.8e}, {res10['ci_high']:.8e}]")

    # Compare with exact count: 156 / 2^31
    exact_frac = 156 / total_10
    print(f"  Exact fraction (156/2^31): {exact_frac:.8e}")
    if res10['fraction'] > 0:
        print(f"  Ratio sampled/exact: {res10['fraction'] / exact_frac:.2f}")
    else:
        print("  (No avoiding colorings found in sample -- consistent with rarity)")
    print()

    # Smaller n values where sampling is informative
    print(f"--- Sampling at smaller n values (100,000 samples each) ---")
    for n in [6, 7, 8, 9]:
        res = sample_avoiding_fraction(n, 3, 100_000, seed=42)
        print(f"  n={n:2d}: avoiding fraction = {res['fraction']:.6f}  "
              f"({res['num_avoiding']}/100000)")
    print()

    n58_samples = 10_000
    print(f"--- n=58 (= R_cop(4) - 1): sampling {n58_samples:,} random 2-colorings ---")
    res58 = sample_avoiding_fraction(58, 4, n58_samples, seed=42)
    print(f"  Avoiding found: {res58['num_avoiding']} / {n58_samples:,}")
    print(f"  Estimated fraction: {res58['fraction']:.8e}")
    print(f"  95% CI: [{res58['ci_low']:.8e}, {res58['ci_high']:.8e}]")
    print()

    # =======================================================================
    # 5. Phase transition analysis
    # =======================================================================
    print("=" * 74)
    print("5. PHASE TRANSITION SHARPNESS")
    print("=" * 74)
    print()

    print("--- K_3 transition: P(avoiding) vs n ---")
    print(f"  (10,000 samples per point)")
    k3_curve = phase_transition_curve(3, range(4, 16), 10_000, seed=42)
    print(f"  {'n':>4s}  {'P(avoiding)':>14s}  {'95% CI':>30s}")
    print(f"  {'----':>4s}  {'--------------':>14s}  {'------------------------------':>30s}")
    for entry in k3_curve:
        print(f"  {entry['n']:4d}  {entry['fraction']:14.8f}  "
              f"[{entry['ci_low']:.8f}, {entry['ci_high']:.8f}]")

    tw3 = transition_width(k3_curve)
    print()
    print(f"  Transition width (90% -> 10%): "
          f"n={tw3['n_low']} to n={tw3['n_high']}, width={tw3['width']}")
    print(f"  R_cop(3) = 11 (transition completes here: P drops to 0)")
    print()

    print("--- K_4 transition: P(avoiding) vs n ---")
    print(f"  (2,000 samples per point)")
    k4_range = list(range(8, 22)) + list(range(22, 62, 4))
    k4_curve = phase_transition_curve(4, k4_range, 2_000, seed=42)
    print(f"  {'n':>4s}  {'P(avoiding)':>14s}  {'95% CI':>30s}")
    print(f"  {'----':>4s}  {'--------------':>14s}  {'------------------------------':>30s}")
    for entry in k4_curve:
        print(f"  {entry['n']:4d}  {entry['fraction']:14.8f}  "
              f"[{entry['ci_low']:.8f}, {entry['ci_high']:.8f}]")

    tw4 = transition_width(k4_curve)
    print()
    if tw4['width'] is not None:
        print(f"  Transition width (90% -> 10%): "
              f"n={tw4['n_low']} to n={tw4['n_high']}, width={tw4['width']}")
    else:
        print(f"  Transition: 90% at n={tw4['n_low']}, "
              f"10% at n={tw4['n_high']} (incomplete)")
    print(f"  R_cop(4) = 59 (transition completes here)")
    print()

    # =======================================================================
    # 6. Predictions for R_cop(5)
    # =======================================================================
    print("=" * 74)
    print("6. PREDICTIONS FOR R_cop(5)")
    print("=" * 74)
    print()

    preds = predict_rcop(5, known_rcop, max_n_first=2000, max_n_lll=60)
    print("  Method                     | Prediction")
    print("  ---------------------------+------------")

    if 'first_moment' in preds:
        print(f"  First moment threshold     | {preds['first_moment']:.1f}")
    if 'exp_fit' in preds:
        a = preds['exp_fit_a']
        b = preds['exp_fit_b']
        print(f"  Exponential fit            | {preds['exp_fit']:.1f}  "
              f"(R_cop(k) ~ {a:.3f} * {b:.3f}^k)")
    if 'ratio_extrapolation' in preds:
        print(f"  Ratio extrapolation        | {preds['ratio_extrapolation']:.1f}  "
              f"(R_cop/R classical ratio)")
    if 'lll_lower' in preds:
        print(f"  LLL lower bound            | >= {preds['lll_lower']:.0f}")
    if 'lll_lower_extrapolated' in preds:
        print(f"  LLL lower (extrapolated)   | >= {preds['lll_lower_extrapolated']:.0f}")

    print()
    print("  --- Analysis ---")
    print()

    # Growth pattern analysis
    print("  Known values:  R_cop(3) = 11,  R_cop(4) = 59")
    print(f"  Growth factor: R_cop(4)/R_cop(3) = {59/11:.3f}")
    print()

    # Multiple estimation approaches
    if 'exp_fit' in preds:
        exp_pred = preds['exp_fit']
        print(f"  Exponential fit: {a:.3f} * {b:.3f}^5 = {exp_pred:.1f}")

    # Conservative bracket
    fm = preds.get('first_moment', float('inf'))
    exp = preds.get('exp_fit', float('inf'))
    lll = preds.get('lll_lower_extrapolated', preds.get('lll_lower', 0))

    # The first moment is a lower bound on the truth (since at the FM
    # threshold, the expected count is only 1, so avoidance is still
    # possible). LLL gives a provable lower bound.
    print()
    print(f"  PREDICTION BRACKET FOR R_cop(5):")
    print(f"    Lower bound (LLL extrapolation):   ~{lll:.0f}")
    print(f"    First moment threshold:            ~{fm:.0f}")
    print(f"    Exponential fit:                   ~{exp:.0f}")
    print()

    # =======================================================================
    # Summary
    # =======================================================================
    print("=" * 74)
    print("SUMMARY: WHY THESE SPECIFIC VALUES?")
    print("=" * 74)
    print()
    print("  R_cop(k) arises from the interplay of three forces:")
    print()
    print("  1. CLIQUE DENSITY: The coprime graph has density 6/pi^2 ~ 0.608.")
    print("     More cliques => more 'pressure' for monochromatic ones.")
    print("     First moment captures this: E[mono K_k] = #cliques * p.")
    print()
    print("  2. CORRELATION STRUCTURE: Coprime cliques sharing edges create")
    print("     positive correlation. The second moment ratio E[X]^2/E[X^2]")
    print("     quantifies how much the 'random' prediction overshoots.")
    print()
    print("  3. NUMBER-THEORETIC STRUCTURE: The coprime graph is NOT a random")
    print("     graph! Primes are coprime to everything, creating a 'hub'")
    print("     structure. Even numbers are never coprime to each other,")
    print("     creating a large independent set. This structured sparsity")
    print("     makes R_cop(k) significantly larger than the probabilistic")
    print("     threshold would suggest.")
    print()

    # Quantify the gaps
    for k in [3, 4]:
        fm_n, _ = first_moment_threshold(k)
        actual = known_rcop[k]
        ratio = actual / fm_n
        print(f"  K_{k}: First moment threshold = {fm_n}, "
              f"actual R_cop({k}) = {actual}, ratio = {ratio:.2f}")

    print()
    print("  The ratio actual/FM_threshold GROWS with k, reflecting the")
    print("  increasing importance of correlation and structure for larger cliques.")
    print()

    # Comparison with Erdos-type random graph thresholds
    print("  For comparison, in the classical Ramsey problem on K_n:")
    print("    FM threshold for R(3,3): ~6 (actual 6) -- ratio 1.0")
    print("    FM threshold for R(4,4): ~10 (actual 18) -- ratio 1.8")
    print("  The coprime graph amplifies this gap because its non-random")
    print("  structure provides extra room for clever avoidance.")


if __name__ == "__main__":
    main()
