#!/usr/bin/env python3
"""
Coprime Ramsey Numbers (NPG-26)

Define R_cop(k) = min n such that every 2-coloring of edges of the
coprime graph G([n]) contains a monochromatic complete subgraph K_k.

This connects Ramsey theory with number-theoretic graph structure.
"""

import math
from itertools import combinations, product
from typing import Set, List, Tuple, Optional


def coprime_edges(n: int) -> List[Tuple[int, int]]:
    """Return all coprime pairs (i,j) with 1 ≤ i < j ≤ n."""
    edges = []
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                edges.append((i, j))
    return edges


def is_clique_in_color(vertices: Set[int], color_map: dict, target_color: int) -> bool:
    """Check if vertices form a monochromatic clique of the given color."""
    vlist = sorted(vertices)
    for i in range(len(vlist)):
        for j in range(i + 1, len(vlist)):
            a, b = vlist[i], vlist[j]
            if math.gcd(a, b) != 1:
                return False  # Not an edge in coprime graph
            edge = (min(a, b), max(a, b))
            if color_map.get(edge) != target_color:
                return False
    return True


def has_monochromatic_clique(n: int, k: int, coloring: dict) -> Optional[Tuple[int, Set[int]]]:
    """
    Check if a 2-coloring of coprime edges of [n] has a monochromatic K_k.

    Returns (color, vertices) if found, None otherwise.
    """
    vertices = list(range(1, n + 1))

    # Find all k-subsets that are cliques in the coprime graph
    for subset in combinations(vertices, k):
        subset_set = set(subset)
        # Check if all pairs are coprime
        all_coprime = True
        for i in range(len(subset)):
            for j in range(i + 1, len(subset)):
                if math.gcd(subset[i], subset[j]) != 1:
                    all_coprime = False
                    break
            if not all_coprime:
                break

        if not all_coprime:
            continue

        # Check if all edges have the same color
        edge_colors = set()
        for i in range(len(subset)):
            for j in range(i + 1, len(subset)):
                edge = (subset[i], subset[j])
                edge_colors.add(coloring.get(edge, -1))

        if len(edge_colors) == 1:
            color = edge_colors.pop()
            return (color, subset_set)

    return None


def compute_coprime_ramsey(k: int, max_n: int = 100) -> int:
    """
    Compute R_cop(k) exactly by incremental extension.

    For each n, check if EVERY 2-coloring of coprime edges has monochromatic K_k.

    Algorithm: enumerate all avoiding colorings at a base n (where exhaustive
    enumeration of 2^edges is feasible), then extend incrementally to larger n.
    When adding vertex n+1, only the new edges (from n+1 to coprime predecessors)
    need to be colored, so we try all 2^(new_edges) extensions of each avoiding
    coloring and check for new monochromatic K_k cliques involving n+1.

    The set of avoiding colorings shrinks rapidly, making this exact and efficient.
    """
    # Phase 1: exhaustive enumeration while edge count is small
    base_n = None
    avoiding = None

    for n in range(k, max_n + 1):
        edges = coprime_edges(n)
        if not edges:
            continue

        if len(edges) <= 25:
            # Enumerate all 2^|edges| colorings
            new_avoiding = []
            for bits in range(2 ** len(edges)):
                coloring = {}
                for idx, e in enumerate(edges):
                    coloring[e] = (bits >> idx) & 1
                if has_monochromatic_clique(n, k, coloring) is None:
                    new_avoiding.append(coloring)

            if not new_avoiding:
                return n  # All colorings forced

            avoiding = new_avoiding
            base_n = n
        else:
            break  # Switch to incremental extension

    if avoiding is None or base_n is None:
        return -1

    # Phase 2: incremental extension from base_n + 1 onward
    for n in range(base_n + 1, max_n + 1):
        new_edges = [(min(i, n), max(i, n))
                     for i in range(1, n) if math.gcd(i, n) == 1]
        if not new_edges:
            continue

        next_avoiding = []
        for col in avoiding:
            for bits in range(2 ** len(new_edges)):
                new_col = dict(col)
                for idx, e in enumerate(new_edges):
                    new_col[e] = (bits >> idx) & 1
                if has_monochromatic_clique(n, k, new_col) is None:
                    next_avoiding.append(new_col)

        if not next_avoiding:
            return n

        avoiding = next_avoiding

    return -1  # Not found within max_n


def coprime_ramsey_lower_bound(k: int, max_n: int = 50) -> int:
    """
    Find lower bound: largest n where some 2-coloring avoids monochromatic K_k.

    Uses exact incremental extension — same algorithm as compute_coprime_ramsey.
    Returns max n such that an avoiding coloring exists at n, or k-1 if none found.
    """
    best_n = k - 1
    avoiding = None
    base_n = None

    for n in range(k, max_n + 1):
        edges = coprime_edges(n)
        if not edges:
            best_n = n
            continue

        if len(edges) <= 25:
            # Exhaustive
            new_avoiding = []
            for bits in range(2 ** len(edges)):
                coloring = {}
                for idx, e in enumerate(edges):
                    coloring[e] = (bits >> idx) & 1
                if has_monochromatic_clique(n, k, coloring) is None:
                    new_avoiding.append(coloring)
            if new_avoiding:
                best_n = n
                avoiding = new_avoiding
                base_n = n
            else:
                return best_n  # Forced at n, so n-1 was the last good
        else:
            break

    if avoiding is None or base_n is None:
        return best_n

    # Incremental extension
    for n in range(base_n + 1, max_n + 1):
        new_edges = [(min(i, n), max(i, n))
                     for i in range(1, n) if math.gcd(i, n) == 1]
        if not new_edges:
            best_n = n
            continue

        next_avoiding = []
        for col in avoiding:
            for bits in range(2 ** len(new_edges)):
                new_col = dict(col)
                for idx, e in enumerate(new_edges):
                    new_col[e] = (bits >> idx) & 1
                if has_monochromatic_clique(n, k, new_col) is None:
                    next_avoiding.append(new_col)

        if next_avoiding:
            best_n = n
            avoiding = next_avoiding
        else:
            return best_n

    return best_n


def coprime_clique_number(n: int) -> int:
    """Find the maximum clique size in the coprime graph G([n])."""
    # Maximum set of mutually coprime numbers in [n]
    # This includes 1 and all primes ≤ n
    # The clique number is 1 + π(n) where π(n) = number of primes ≤ n
    best = 0
    vertices = list(range(1, n + 1))

    for size in range(min(n, 15), 0, -1):
        for subset in combinations(vertices, size):
            all_coprime = True
            for i in range(len(subset)):
                for j in range(i + 1, len(subset)):
                    if math.gcd(subset[i], subset[j]) != 1:
                        all_coprime = False
                        break
                if not all_coprime:
                    break
            if all_coprime:
                return size

    return 1


def main():
    print("=" * 70)
    print("COPRIME RAMSEY NUMBERS (NPG-26)")
    print("=" * 70)
    print()
    print("R_cop(k) = min n such that every 2-coloring of edges")
    print("           of G([n]) has monochromatic K_k.")
    print()

    # Compute coprime clique numbers first
    print("--- Coprime Clique Numbers ---")
    for n in [5, 10, 15, 20, 25, 30]:
        if n <= 15:
            omega = coprime_clique_number(n)
            print(f"  omega(G([{n}])) = {omega}")
        else:
            # Approximate: 1 + primes ≤ n
            primes = [p for p in range(2, n + 1)
                      if all(p % d != 0 for d in range(2, int(p**0.5) + 1))]
            print(f"  omega(G([{n}])) >= {1 + len(primes)} (1 + pi({n}))")
    print()

    # Compute R_cop(3)
    print("--- Computing R_cop(3) ---")
    for n in range(3, 20):
        edges = coprime_edges(n)
        print(f"  n={n:2d}: {len(edges):3d} coprime edges", end="")

        if len(edges) <= 25:
            # Exhaustive check
            all_forced = True
            avoiding_count = 0
            for bits in range(2 ** len(edges)):
                coloring = {}
                for idx, e in enumerate(edges):
                    coloring[e] = (bits >> idx) & 1
                if has_monochromatic_clique(n, 3, coloring) is None:
                    all_forced = False
                    avoiding_count += 1

            if all_forced:
                print(f" -> ALL colorings have mono K_3. R_cop(3) = {n}")
                break
            else:
                print(f" -> {avoiding_count} colorings avoid mono K_3")
        else:
            print(f" -> (incremental extension from here)")
    print()

    # Summary
    print("--- Summary ---")
    print("  Classical R(3,3) = 6")
    r3 = compute_coprime_ramsey(3, max_n=20)
    print(f"  R_cop(3) = {r3}")
    print()

    # Compare
    print("--- Comparison ---")
    print("  R_cop(k) vs R(k,k):")
    print("  k=3: R_cop(3) = {}, R(3,3) = 6".format(r3))
    print()
    print("Note: R_cop(k) ≤ R(k,k) since the coprime graph is a subgraph")
    print("of K_n (not all pairs are coprime). But forcing a monochromatic")
    print("clique in a sparser graph may require larger n.")
    print()

    print("=" * 70)
    print("CONJECTURE (NPG-26)")
    print("=" * 70)
    print(f"""
For k ≥ 3, define R_cop(k) = min n such that every 2-coloring of
coprime edges in G([n]) contains a monochromatic K_k.

Computed: R_cop(3) = {r3}
Classical: R(3,3) = 6

Conjecture: R_cop(k) > R(k,k) for all k ≥ 3.

Rationale: The coprime graph G([n]) has density ~6/π² ≈ 0.608 < 1,
so it's a "sparse" version of K_n. Monochromatic cliques are harder
to force in sparser graphs.
""")


if __name__ == "__main__":
    main()
