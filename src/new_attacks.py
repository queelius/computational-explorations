#!/usr/bin/env python3
"""
New Problem Attacks — Computational Experiments on Open Erdős Problems

Focuses on problems where our existing techniques (coprime graphs, Fourier,
Möbius, Sidon sets, extremal density) can make concrete progress.
"""

import math
from itertools import combinations, product
from collections import defaultdict, Counter
from functools import lru_cache
from typing import Set, List, Tuple, Dict, Optional


# =============================================================================
# Problem #30: Maximum Sidon set in [N] — f(N) ~ √N + ?
# Prize: $1000 | Tags: sidon sets, additive combinatorics
# Question: Is f(N) ≤ √N + O(N^{1/4})? What is the exact second-order term?
# =============================================================================

def is_sidon(A: Set[int]) -> bool:
    """Check if A is a Sidon set (all pairwise sums distinct)."""
    sums = set()
    A_list = sorted(A)
    for i in range(len(A_list)):
        for j in range(i, len(A_list)):
            s = A_list[i] + A_list[j]
            if s in sums:
                return False
            sums.add(s)
    return True


def max_sidon_in_range(N: int) -> Tuple[int, Set[int]]:
    """Find maximum Sidon set in [1, N] by greedy + backtracking."""
    best = set()

    def backtrack(current: Set[int], sums: Set[int], start: int):
        nonlocal best
        if len(current) > len(best):
            best = current.copy()
        for x in range(start, N + 1):
            # Check if x can be added without repeating a sum
            new_sums = set()
            conflict = False
            for a in current:
                s = a + x
                if s in sums or s in new_sums:
                    conflict = True
                    break
                new_sums.add(s)
            double = 2 * x
            if not conflict and double not in sums and double not in new_sums:
                new_sums.add(double)
                current.add(x)
                backtrack(current, sums | new_sums, x + 1)
                current.remove(x)

    backtrack(set(), set(), 1)
    return len(best), best


def sidon_second_order(max_N: int = 200) -> List[Dict]:
    """Compute f(N) - √N for various N to study the second-order term."""
    results = []
    for N in range(10, max_N + 1, 10):
        size, _ = max_sidon_in_range(N)
        sqrt_N = math.sqrt(N)
        gap = size - sqrt_N
        results.append({
            "N": N, "f_N": size, "sqrt_N": round(sqrt_N, 3),
            "gap": round(gap, 3), "N_quarter": round(N**0.25, 3)
        })
    return results


# =============================================================================
# Problem #74: Chromatic number of cycle-containing graphs
# Prize: $500 | Tags: graph theory, chromatic number, cycles
# Can we relate coprime graph chromatic number to cycle structure?
# =============================================================================

def coprime_chromatic_number(n: int) -> int:
    """Compute (or bound) the chromatic number of the coprime graph G(n).
    Use greedy coloring as upper bound."""
    # Build adjacency
    adj = defaultdict(set)
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                adj[i].add(j)
                adj[j].add(i)

    # Greedy coloring (largest-first ordering)
    vertices = sorted(range(1, n + 1), key=lambda v: -len(adj[v]))
    color = {}
    for v in vertices:
        used = {color[u] for u in adj[v] if u in color}
        c = 0
        while c in used:
            c += 1
        color[v] = c

    return max(color.values()) + 1 if color else 0


def coprime_clique_number(n: int) -> int:
    """Find the clique number (max clique) of coprime graph G(n).
    1 is coprime to everything, and primes are pairwise coprime."""
    # {1} + all primes ≤ n form a clique
    primes = []
    for p in range(2, n + 1):
        if all(p % i != 0 for i in range(2, int(math.sqrt(p)) + 1)):
            primes.append(p)
    return len(primes) + 1  # +1 for element 1


def analyze_coprime_chromatic(max_n: int = 50) -> List[Dict]:
    """Analyze chromatic number vs clique number of coprime graphs."""
    results = []
    for n in range(5, max_n + 1, 5):
        chi = coprime_chromatic_number(n)
        omega = coprime_clique_number(n)
        results.append({
            "n": n, "chi": chi, "omega": omega,
            "gap": chi - omega, "ratio": round(chi / omega, 3) if omega > 0 else 0
        })
    return results


# =============================================================================
# Problem #142: Szemerédi regularity for APs (the $10,000 problem)
# Prize: $10,000 | Tags: additive combinatorics, arithmetic progressions
# r_k(N) bounds — compute AP-free set sizes for small k
# =============================================================================

def is_ap_free(A: Set[int], k: int) -> bool:
    """Check if A contains no k-term arithmetic progression."""
    A_sorted = sorted(A)
    A_set = set(A)
    for i, a in enumerate(A_sorted):
        for j in range(i + 1, len(A_sorted)):
            d = A_sorted[j] - a
            if d == 0:
                continue
            # Check if a, a+d, a+2d, ..., a+(k-1)d are all in A
            is_ap = True
            for m in range(2, k):
                if a + m * d not in A_set:
                    is_ap = False
                    break
            if is_ap:
                return False
    return True


def max_ap_free_size(N: int, k: int) -> Tuple[int, Set[int]]:
    """Find maximum size of k-AP-free set in [N] by greedy."""
    best = set()
    current = set()

    for x in range(1, N + 1):
        # Try to add x
        test = current | {x}
        if is_ap_free(test, k):
            current.add(x)

    return len(current), current


def compute_rk_values(max_N: int = 50, k: int = 3) -> List[Dict]:
    """Compute r_k(N) = max AP-free set size in [N]."""
    results = []
    for N in range(k, max_N + 1):
        size, A = max_ap_free_size(N, k)
        density = size / N
        results.append({
            "N": N, "r_k": size, "density": round(density, 4),
            "k": k, "example": sorted(A) if N <= 20 else "..."
        })
    return results


# =============================================================================
# Problem #340: Sidon sets with prescribed differences
# Tags: number theory, additive combinatorics, sidon sets
# OEIS: A080200, A005282
# =============================================================================

def greedy_b2_sequence(N: int) -> Set[int]:
    """Construct B2 (Sidon) sequence greedily up to N. OEIS A005282."""
    A = set()
    sums = set()
    for x in range(1, N + 1):
        new_sums = set()
        conflict = False
        for a in A:
            s = a + x
            if s in sums:
                conflict = True
                break
            new_sums.add(s)
        if not conflict:
            double = 2 * x
            if double not in sums:
                new_sums.add(double)
                A.add(x)
                sums |= new_sums
    return A


def sidon_difference_spectrum(A: Set[int]) -> Dict[int, int]:
    """Compute the difference spectrum of a Sidon set: histogram of |a-b|."""
    diffs = Counter()
    A_list = sorted(A)
    for i in range(len(A_list)):
        for j in range(i + 1, len(A_list)):
            diffs[A_list[j] - A_list[i]] += 1
    return dict(diffs)


# =============================================================================
# Problem #168: Complete sequences / additive bases
# Tags: additive combinatorics
# OEIS: A004059, A057561, A094708, A386439
# Is there a set that is an additive basis of order 2 with density → 0?
# =============================================================================

def is_additive_basis_order_h(A: Set[int], N: int, h: int) -> bool:
    """Check if A is an additive basis of order h for [1, N].
    i.e., every n in [1, N] can be written as sum of ≤ h elements of A."""
    representable = {0}
    for _ in range(h):
        new_rep = set()
        for r in representable:
            for a in A:
                if r + a <= N:
                    new_rep.add(r + a)
        representable |= new_rep
    return all(n in representable for n in range(1, N + 1))


def thin_basis_search(N: int, h: int = 2) -> Dict:
    """Search for thin additive bases of order h for [1, N].
    Goal: minimize |A| such that A is a basis of order h."""
    # Greedy: add elements that represent the most new numbers
    A = set()
    represented = {0}

    for x in range(1, N + 1):
        # Check what adding x would represent
        new_reps = set()
        for r in represented:
            if r + x <= N:
                new_reps.add(r + x)
        # Also sums of form a + x for a in A
        for a in A:
            for r in represented:
                if r + a + x <= N:
                    new_reps.add(r + a + x)

        if x not in represented or len(new_reps - represented) > 0:
            A.add(x)
            # Update represented: all h-fold sums from A
            represented = {0}
            for _ in range(h):
                new_rep = set()
                for r in represented:
                    for a in A:
                        if r + a <= N:
                            new_rep.add(r + a)
                represented |= new_rep

        if all(n in represented for n in range(1, x + 1)):
            pass  # Good, keep going

    return {
        "N": N, "h": h, "basis_size": len(A),
        "density": round(len(A) / N, 4),
        "basis": sorted(A) if N <= 100 else sorted(A)[:20],
        "is_basis": is_additive_basis_order_h(A, N, h)
    }


# =============================================================================
# Problem #483: Schur numbers — exponential upper bound
# Tags: number theory, additive combinatorics, ramsey theory
# We already have partial results. Let's push further.
# =============================================================================

def schur_coloring_count(N: int, k: int) -> int:
    """Count the number of valid k-colorings of [N] avoiding mono Schur triples.
    Only feasible for very small N and k."""
    if N > 15 or k > 3:
        return -1  # Too large

    count = 0
    for coloring in product(range(k), repeat=N):
        valid = True
        colors = [set() for _ in range(k)]
        for i, c in enumerate(coloring):
            colors[c].add(i + 1)

        for color_class in colors:
            for a in color_class:
                for b in color_class:
                    if a + b in color_class:
                        valid = False
                        break
                if not valid:
                    break
            if not valid:
                break

        if valid:
            count += 1

    return count


def schur_entropy(N: int, k: int = 2) -> Dict:
    """Compute the 'entropy' of Schur-free colorings:
    How many valid colorings exist? This measures the 'freedom' in coloring."""
    count = schur_coloring_count(N, k)
    total = k ** N
    if count > 0:
        entropy = math.log2(count) / N
    else:
        entropy = 0
    return {
        "N": N, "k": k, "valid_colorings": count,
        "total_colorings": total,
        "fraction": round(count / total, 6) if total > 0 else 0,
        "entropy_per_element": round(entropy, 4)
    }


# =============================================================================
# NEW PATTERN: "Resolution Difficulty Score"
# Meta-analysis: What makes some problems harder than others?
# =============================================================================

def compute_resolution_scores() -> Dict:
    """Compute a 'difficulty score' for each problem based on observable features."""
    import yaml
    data = yaml.safe_load(open('data/erdosproblems/data/problems.yaml'))

    # Features that predict difficulty
    tag_solve_rate = {}
    tag_counts = Counter()
    tag_solved = Counter()

    for p in data:
        status = p.get('status', {}).get('state', 'unknown')
        tags = p.get('tags', [])
        is_resolved = status in ('proved', 'disproved', 'solved',
                                  'proved (Lean)', 'disproved (Lean)', 'solved (Lean)')
        for t in tags:
            tag_counts[t] += 1
            if is_resolved:
                tag_solved[t] += 1

    for t in tag_counts:
        tag_solve_rate[t] = tag_solved[t] / tag_counts[t] if tag_counts[t] > 0 else 0

    # Score each open problem
    scored = []
    for p in data:
        if p.get('status', {}).get('state') != 'open':
            continue

        tags = p.get('tags', [])

        # Features
        n_tags = len(tags)
        avg_solve_rate = sum(tag_solve_rate.get(t, 0) for t in tags) / n_tags if n_tags > 0 else 0
        has_prize = p.get('prize', 'no') != 'no'
        is_formalized = p.get('formalized', {}).get('state') == 'yes'
        has_oeis = any(o not in ('N/A', 'possible') for o in p.get('oeis', []))

        # Difficulty score: lower = more likely solvable
        # High tag solve rate → easier
        # Formalized → cleaner statement → easier
        # OEIS → concrete sequence → easier
        # Prize → famous → harder (usually)
        score = (1 - avg_solve_rate) + (0.2 if has_prize else 0) - (0.1 if is_formalized else 0) - (0.1 if has_oeis else 0) + (0.05 * n_tags)

        scored.append({
            "number": p['number'],
            "score": round(score, 3),
            "tags": tags,
            "prize": p.get('prize', 'no'),
            "avg_tag_solve_rate": round(avg_solve_rate, 3),
            "formalized": is_formalized,
            "has_oeis": has_oeis
        })

    scored.sort(key=lambda x: x['score'])

    return {
        "tag_solve_rates": {t: round(r, 3) for t, r in sorted(tag_solve_rate.items(), key=lambda x: -x[1])},
        "easiest_open": scored[:20],
        "hardest_open": scored[-20:],
        "total_open": len(scored)
    }


# =============================================================================
# NEW PATTERN: "Proof Technique Fingerprint"
# Which combinations of tags predict which proof methods?
# =============================================================================

def technique_fingerprints() -> Dict:
    """Analyze which tag combinations correlate with specific outcomes."""
    import yaml
    data = yaml.safe_load(open('data/erdosproblems/data/problems.yaml'))

    # Group by status
    by_status = defaultdict(list)
    for p in data:
        status = p.get('status', {}).get('state', 'unknown')
        by_status[status].append(p)

    # For proved problems: what tag combinations appear?
    proved_tag_combos = Counter()
    disproved_tag_combos = Counter()
    open_tag_combos = Counter()

    for p in by_status['proved'] + by_status['proved (Lean)'] + by_status['solved'] + by_status['solved (Lean)']:
        tags = tuple(sorted(p.get('tags', [])))
        if tags:
            proved_tag_combos[tags] += 1

    for p in by_status['disproved'] + by_status['disproved (Lean)']:
        tags = tuple(sorted(p.get('tags', [])))
        if tags:
            disproved_tag_combos[tags] += 1

    for p in by_status['open']:
        tags = tuple(sorted(p.get('tags', [])))
        if tags:
            open_tag_combos[tags] += 1

    # Find tag combos that appear in both proved and open (technique transfer candidates)
    transfer = []
    for combo, open_count in open_tag_combos.most_common(100):
        proved_count = proved_tag_combos.get(combo, 0)
        if proved_count > 0:
            transfer.append({
                "tags": list(combo),
                "proved_count": proved_count,
                "open_count": open_count,
                "solve_rate": round(proved_count / (proved_count + open_count), 3)
            })

    transfer.sort(key=lambda x: -x['solve_rate'])

    # Find "proof deserts": tag combos with ONLY open problems
    deserts = []
    for combo, count in open_tag_combos.most_common(50):
        if combo not in proved_tag_combos and combo not in disproved_tag_combos:
            deserts.append({"tags": list(combo), "open_count": count})

    return {
        "technique_transfer": transfer[:20],
        "proof_deserts": deserts[:15],
        "proved_combos": proved_tag_combos.most_common(10),
        "disproved_combos": disproved_tag_combos.most_common(10)
    }


# =============================================================================
# NEW: Coprime Graph Spectrum Analysis
# Eigenvalues of coprime adjacency matrix → structural insights
# =============================================================================

def coprime_spectrum(n: int) -> Dict:
    """Compute eigenvalue spectrum of coprime graph adjacency matrix."""
    import numpy as np

    # Build adjacency matrix
    A = np.zeros((n, n))
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                A[i-1][j-1] = 1
                A[j-1][i-1] = 1

    eigenvalues = sorted(np.linalg.eigvalsh(A), reverse=True)

    return {
        "n": n,
        "lambda_1": round(eigenvalues[0], 4),
        "lambda_2": round(eigenvalues[1], 4),
        "lambda_min": round(eigenvalues[-1], 4),
        "spectral_gap": round(eigenvalues[0] - eigenvalues[1], 4),
        "negative_count": sum(1 for e in eigenvalues if e < -0.01),
        "trace": round(sum(eigenvalues), 4),  # Should be 0 for simple graph
        "energy": round(sum(abs(e) for e in eigenvalues), 4),
    }


# =============================================================================
# Main runner
# =============================================================================

def main():
    import json

    print("=" * 70)
    print("NEW ATTACKS ON ERDŐS PROBLEMS — COMPUTATIONAL EXPERIMENTS")
    print("=" * 70)

    results = {}

    # 1. Sidon second-order term (#30)
    print("\n--- Problem #30: Sidon second-order term ---")
    sidon_data = sidon_second_order(100)
    for d in sidon_data:
        print(f"  N={d['N']:3d}: f(N)={d['f_N']:2d}, √N={d['sqrt_N']:.1f}, gap={d['gap']:.3f}, N^{1/4}={d['N_quarter']:.3f}")
    results["sidon_second_order"] = sidon_data

    # 2. Coprime chromatic analysis (#74)
    print("\n--- Problem #74: Coprime chromatic numbers ---")
    chromatic = analyze_coprime_chromatic(40)
    for d in chromatic:
        print(f"  n={d['n']:2d}: χ={d['chi']}, ω={d['omega']}, gap={d['gap']}, ratio={d['ratio']}")
    results["coprime_chromatic"] = chromatic

    # 3. AP-free sets (#142)
    print("\n--- Problem #142: r_3(N) values ---")
    ap_free = compute_rk_values(40, k=3)
    for d in ap_free:
        if d['N'] % 5 == 0 or d['N'] <= 10:
            print(f"  N={d['N']:2d}: r_3(N)={d['r_k']:2d}, density={d['density']:.4f}")
    results["ap_free_3"] = ap_free

    # 4. Coprime graph spectrum
    print("\n--- Coprime Graph Spectral Analysis ---")
    for n in [10, 20, 30, 40, 50]:
        spec = coprime_spectrum(n)
        print(f"  n={n:2d}: λ₁={spec['lambda_1']:.2f}, λ₂={spec['lambda_2']:.2f}, "
              f"gap={spec['spectral_gap']:.2f}, neg={spec['negative_count']}, energy={spec['energy']:.1f}")
        results[f"spectrum_{n}"] = spec

    # 5. Schur entropy (#483)
    print("\n--- Problem #483: Schur coloring entropy ---")
    for N in range(1, 10):
        ent = schur_entropy(N, 2)
        print(f"  N={N}: valid={ent['valid_colorings']}/{ent['total_colorings']}, "
              f"fraction={ent['fraction']:.4f}, entropy/elem={ent['entropy_per_element']:.4f}")
    results["schur_entropy"] = [schur_entropy(N, 2) for N in range(1, 10)]

    # 6. Greedy B2 sequence (#340)
    print("\n--- Problem #340: Greedy B2 (Sidon) sequence ---")
    for N in [50, 100, 200, 500]:
        b2 = greedy_b2_sequence(N)
        print(f"  N={N}: |A|={len(b2)}, density={len(b2)/N:.4f}, first 10: {sorted(b2)[:10]}")

    # 7. Resolution difficulty scores
    print("\n--- Meta-Pattern: Resolution Difficulty Scores ---")
    scores = compute_resolution_scores()
    print("Tag solve rates (top 10 easiest topics):")
    for tag, rate in list(scores['tag_solve_rates'].items())[:10]:
        print(f"  {tag}: {rate:.1%}")
    print("Tag solve rates (bottom 10 hardest topics):")
    for tag, rate in list(scores['tag_solve_rates'].items())[-10:]:
        print(f"  {tag}: {rate:.1%}")
    print(f"\n20 Easiest open problems (lowest difficulty score):")
    for p in scores['easiest_open']:
        print(f"  #{p['number']}: score={p['score']:.3f}, tags={p['tags']}, "
              f"solve_rate={p['avg_tag_solve_rate']:.1%}")
    results["difficulty_scores"] = scores

    # 8. Technique fingerprints
    print("\n--- Meta-Pattern: Technique Fingerprints ---")
    fingerprints = technique_fingerprints()
    print("Best technique transfer candidates:")
    for tf in fingerprints['technique_transfer'][:10]:
        print(f"  {tf['tags']}: {tf['proved_count']} proved, {tf['open_count']} open, "
              f"solve_rate={tf['solve_rate']:.1%}")
    print("\nProof deserts (tag combos with ONLY open problems):")
    for d in fingerprints['proof_deserts'][:10]:
        print(f"  {d['tags']}: {d['open_count']} open, 0 proved")
    results["technique_fingerprints"] = fingerprints

    # 9. Thin additive basis (#168)
    print("\n--- Problem #168: Thin additive bases ---")
    for N in [20, 50, 100]:
        basis = thin_basis_search(N, h=2)
        print(f"  N={N}: basis_size={basis['basis_size']}, density={basis['density']:.4f}, "
              f"valid={basis['is_basis']}")

    print("\n" + "=" * 70)
    print("EXPERIMENTS COMPLETE")
    print("=" * 70)

    return results


if __name__ == "__main__":
    main()
