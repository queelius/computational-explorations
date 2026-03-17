#!/usr/bin/env python3
"""
Geometry Attacks: Computational experiments on open Erdos geometry problems.

Targets:
  #89  ($500)  Distinct distances - min distinct distances among n planar points
  #99  ($100)  Unit distance problem - max unit-distance edges on n points
  #93/#95      Erdos-Szekeres convex position (proved, but verify small cases)
  #604 ($500)  Diameter graphs - max edges with all pairwise distances <= 1
  #90  ($500)  Repeated distances - max multiplicity of any one distance

All computations focus on EXACT values for small n, filling gaps in the literature.
Strategy: use algebraic constructions seeded from known optimal families, then
verify via exact arithmetic where possible.
"""

import math
import numpy as np
from itertools import combinations, product
from typing import List, Tuple, Optional, Set, Dict
from collections import Counter
from scipy.spatial.distance import pdist


# ---------------------------------------------------------------------------
# Utility: distance counting with controlled tolerance
# ---------------------------------------------------------------------------

def _squared_distances(points: np.ndarray) -> np.ndarray:
    """Compute all pairwise squared distances (avoids sqrt for exact comparison)."""
    n = len(points)
    sq_dists = []
    for i in range(n):
        for j in range(i + 1, n):
            diff = points[i] - points[j]
            sq_dists.append(diff[0]**2 + diff[1]**2)
    return np.array(sq_dists)


def distinct_distance_count(points: np.ndarray, tol: float = 1e-9) -> int:
    """Count distinct pairwise distances (up to floating-point tolerance).

    Uses squared distances and relative tolerance for robust comparison.
    """
    if len(points) < 2:
        return 0
    sq_dists = sorted(_squared_distances(points))
    # Count distinct values with tolerance
    distinct = 1
    for i in range(1, len(sq_dists)):
        if sq_dists[i] - sq_dists[i - 1] > tol * max(1.0, sq_dists[i]):
            distinct += 1
    return distinct


def unit_distance_count(points: np.ndarray, tol: float = 1e-7) -> int:
    """Count pairs of points at distance exactly 1 (within tolerance)."""
    count = 0
    n = len(points)
    for i in range(n):
        for j in range(i + 1, n):
            diff = points[i] - points[j]
            dsq = diff[0]**2 + diff[1]**2
            if abs(dsq - 1.0) < tol:
                count += 1
    return count


def max_distance_multiplicity(points: np.ndarray, tol: float = 1e-9) -> Tuple[int, float]:
    """Find the maximum number of times any single distance occurs.

    Returns (max_count, the_squared_distance).
    """
    if len(points) < 2:
        return 0, 0.0
    sq_dists = sorted(_squared_distances(points))
    # Group by tolerance
    groups = []
    current_val = sq_dists[0]
    current_count = 1
    for i in range(1, len(sq_dists)):
        if sq_dists[i] - current_val < tol * max(1.0, current_val):
            current_count += 1
        else:
            groups.append((current_count, current_val))
            current_val = sq_dists[i]
            current_count = 1
    groups.append((current_count, current_val))
    groups.sort(reverse=True)
    return groups[0][0], groups[0][1]


# ---------------------------------------------------------------------------
# 1. DISTINCT DISTANCES (#89, $500)
#
# g(n) = min number of distinct distances among n points in the plane.
# Erdos (1946) conjectured g(n) = Omega(n / sqrt(log n)).
# Guth-Katz (2015): proved g(n) = Omega(n / log n).
#
# Strategy: construct known-optimal configurations exactly.
# The optimal configurations for small n are known:
#   n=3: equilateral triangle (1 distance)
#   n=4: two nested equilateral triangles or rhombus (2 distances)
#   n=5: regular pentagon (2 distances)
#   n=6: regular hexagon (3 distances)
#   n=7: regular hexagon + center (3 distances: side, short diag, long diag=2*side)
#   n >= 8: subsets of the triangular lattice
# ---------------------------------------------------------------------------

def _regular_polygon(n: int) -> np.ndarray:
    """Vertices of a regular n-gon inscribed in the unit circle."""
    angles = np.array([2 * math.pi * k / n for k in range(n)])
    return np.column_stack([np.cos(angles), np.sin(angles)])


def _triangular_lattice_points(n: int) -> np.ndarray:
    """Generate n points from the triangular lattice, closest to origin.

    Basis: e1 = (1, 0), e2 = (1/2, sqrt(3)/2).
    """
    e1 = np.array([1.0, 0.0])
    e2 = np.array([0.5, math.sqrt(3) / 2])
    radius = int(math.ceil(math.sqrt(n))) + 3
    pts = []
    for i in range(-radius, radius + 1):
        for j in range(-radius, radius + 1):
            pts.append(i * e1 + j * e2)
    pts = np.array(pts)
    dists = np.linalg.norm(pts, axis=1)
    return pts[np.argsort(dists)[:n]]


def _square_lattice_points(n: int) -> np.ndarray:
    """Generate n points from the integer lattice, closest to origin."""
    radius = int(math.ceil(math.sqrt(n))) + 2
    pts = []
    for i in range(-radius, radius + 1):
        for j in range(-radius, radius + 1):
            pts.append(np.array([float(i), float(j)]))
    pts = np.array(pts)
    dists = np.linalg.norm(pts, axis=1)
    return pts[np.argsort(dists)[:n]]


def _known_optimal_distinct_distances(n: int) -> np.ndarray:
    """Return known-optimal or near-optimal configurations for g(n).

    The regular n-gon achieves floor(n/2) distinct distances, which is
    optimal for small n.  For each k = 1, ..., floor(n/2), the chord
    length 2*sin(k*pi/n) appears n times (or n/2 times for the diameter
    when n is even and k = n/2).
    """
    return _regular_polygon(n)


def _try_all_triangular_subsets(n: int, pool_size: int = 0) -> Tuple[int, np.ndarray]:
    """For n >= 8, try subsets of the triangular lattice to minimize g(n).

    For tractable sizes, we enumerate subsets of a larger pool.
    For larger n, use the closest-to-origin subset and local search.
    """
    if pool_size == 0:
        # Larger pool gives more combinatorial freedom
        pool_size = min(n + 12, 35)

    pool = _triangular_lattice_points(pool_size)
    total = len(pool)

    best_count = float('inf')
    best_config = None

    # If small enough, enumerate
    if math.comb(total, n) <= 200000:
        for subset in combinations(range(total), n):
            pts = pool[list(subset)]
            c = distinct_distance_count(pts)
            if c < best_count:
                best_count = c
                best_config = pts.copy()
    else:
        # Start with closest-to-origin, then local search
        rng = np.random.RandomState(42)
        indices = list(range(n))  # already sorted by distance from origin

        for trial in range(300):
            if trial == 0:
                current_indices = list(range(n))
            else:
                current_indices = sorted(rng.choice(total, n, replace=False))

            pts = pool[current_indices]
            current_count = distinct_distance_count(pts)

            # Local search: swap points
            for _ in range(100):
                improved = False
                idx_set = set(current_indices)
                avail = [i for i in range(total) if i not in idx_set]
                for pos in range(n):
                    old = current_indices[pos]
                    for new_idx in rng.choice(avail, min(len(avail), 15), replace=False):
                        current_indices[pos] = new_idx
                        pts = pool[current_indices]
                        c = distinct_distance_count(pts)
                        if c < current_count:
                            current_count = c
                            idx_set.discard(old)
                            idx_set.add(new_idx)
                            avail = [i for i in range(total) if i not in idx_set]
                            improved = True
                            break
                        current_indices[pos] = old
                if not improved:
                    break

            pts = pool[current_indices]
            c = distinct_distance_count(pts)
            if c < best_count:
                best_count = c
                best_config = pts.copy()

    return best_count, best_config


def compute_min_distinct_distances(n_range: Tuple[int, int] = (3, 13)) -> Dict[int, Tuple[int, np.ndarray]]:
    """Compute g(n) = min distinct distances for n in range.

    Returns dict: n -> (min_count, optimal_config).

    Strategy: try the regular n-gon (gives floor(n/2)), then also search
    the triangular lattice for potentially better configs at larger n.
    """
    results = {}
    for n in range(n_range[0], n_range[1] + 1):
        # Regular n-gon: always gives floor(n/2)
        polygon_config = _regular_polygon(n)
        polygon_count = distinct_distance_count(polygon_config)

        best_count = polygon_count
        best_config = polygon_config

        # For n >= 8, also try triangular lattice subsets
        if n >= 8:
            lattice_count, lattice_config = _try_all_triangular_subsets(n)
            if lattice_count < best_count:
                best_count = lattice_count
                best_config = lattice_config

        results[n] = (best_count, best_config)
    return results


# Known exact values from the literature (Erdos-Fishburn 1996, Altman 1972):
# g(n) = min number of distinct distances among n points in the plane.
# The regular n-gon achieves floor(n/2), which is optimal for n <= 13.
# For large n, the triangular lattice gives g(n) ~ sqrt(n / (2*sqrt(3))) (Erdos 1946).
KNOWN_DISTINCT_DISTANCES = {
    3: 1,   # equilateral triangle (regular 3-gon)
    4: 2,   # square (regular 4-gon)
    5: 2,   # regular pentagon
    6: 3,   # regular hexagon
    7: 3,   # regular 7-gon
    8: 4,   # regular 8-gon
    9: 4,   # regular 9-gon
    10: 5,  # regular 10-gon
    11: 5,  # regular 11-gon
    12: 6,  # regular 12-gon
    13: 6,  # regular 13-gon
}


# ---------------------------------------------------------------------------
# 2. UNIT DISTANCE PROBLEM (#99, $100)
#
# u(n) = max number of unit distances among n points in R^2.
# Known: u(n) = Theta(n^{1+c/log log n}).
# The exact values for small n are known (OEIS A186705).
#
# Strategy: build optimal configurations algebraically.  The key building
# blocks are equilateral triangles and rhombi of side 1.
# ---------------------------------------------------------------------------

def _build_unit_distance_graph(n: int) -> np.ndarray:
    """Construct a point set with many unit distances.

    Uses chains of equilateral triangles and known optimal substructures.
    Each new point is placed at unit distance from as many existing points
    as possible (intersection of unit circles).
    """
    if n <= 1:
        return np.array([[0.0, 0.0]])[:n]
    if n == 2:
        return np.array([[0.0, 0.0], [1.0, 0.0]])
    if n == 3:
        # Equilateral triangle: 3 unit distances
        return np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [0.5, math.sqrt(3) / 2],
        ])

    # For n >= 4: start with equilateral triangle, greedily add points
    # at unit circle intersections to maximize unit edges
    pts = [
        np.array([0.0, 0.0]),
        np.array([1.0, 0.0]),
        np.array([0.5, math.sqrt(3) / 2]),
    ]

    def _unit_circle_intersections(p1, p2):
        """Find intersections of unit circles centered at p1 and p2."""
        d = np.linalg.norm(p2 - p1)
        if d > 2.0 + 1e-10 or d < 1e-10:
            return []
        a = d / 2
        if a > 1.0:
            return []
        h = math.sqrt(max(1.0 - a**2, 0.0))
        mid = (p1 + p2) / 2
        direction = (p2 - p1) / d
        perp = np.array([-direction[1], direction[0]])
        return [mid + h * perp, mid - h * perp]

    while len(pts) < n:
        best_point = None
        best_edges = 0

        # Try all intersections of unit circles from existing pairs
        candidates = set()
        for i, j in combinations(range(len(pts)), 2):
            for q in _unit_circle_intersections(pts[i], pts[j]):
                # Round to avoid duplicates in the candidate set
                key = (round(q[0], 8), round(q[1], 8))
                candidates.add(key)

        for key in candidates:
            q = np.array([key[0], key[1]])
            # Check it's not a duplicate of existing point
            is_dup = False
            for p in pts:
                if np.linalg.norm(q - p) < 1e-7:
                    is_dup = True
                    break
            if is_dup:
                continue

            # Count unit distances to existing points
            edges = sum(1 for p in pts if abs(np.linalg.norm(q - p) - 1.0) < 1e-7)
            if edges > best_edges:
                best_edges = edges
                best_point = q.copy()

        if best_point is not None:
            pts.append(best_point)
        else:
            # Fallback: place on unit circle from last point
            angle = np.random.RandomState(len(pts)).uniform(0, 2 * math.pi)
            pts.append(pts[-1] + np.array([math.cos(angle), math.sin(angle)]))

    return np.array(pts[:n])


def _has_duplicate_points(pts: np.ndarray, min_sep: float = 1e-4) -> bool:
    """Check if any two points are closer than min_sep."""
    n = len(pts)
    for i in range(n):
        for j in range(i + 1, n):
            if np.linalg.norm(pts[i] - pts[j]) < min_sep:
                return True
    return False


def _optimize_unit_distances(n: int, trials: int = 200,
                             iterations: int = 600) -> Tuple[int, np.ndarray]:
    """Optimize unit distance count via simulated annealing with circle-snap moves.

    Each move either:
    (a) snaps a point to the intersection of two unit circles (algebraic move), or
    (b) small random perturbation.

    IMPORTANT: rejects configurations with duplicate/near-duplicate points.
    """
    best_count = 0
    best_config = None
    rng = np.random.RandomState(42)

    # Build seed configurations
    seed_greedy = _build_unit_distance_graph(n)
    seed_chain = np.array([[float(i), 0.0] for i in range(n)])  # chain

    # Triangular lattice also gives many unit distances (side = 1)
    tri = _triangular_lattice_points(max(n + 5, 15))

    seeds = [seed_greedy, seed_chain]

    for trial in range(trials):
        if trial < len(seeds):
            pts = seeds[trial].copy()
        elif trial % 5 == 0:
            # Subset of triangular lattice
            indices = rng.choice(len(tri), min(n, len(tri)), replace=False)
            pts = tri[indices].copy()
        elif trial % 5 == 1:
            pts = _build_unit_distance_graph(n) + rng.randn(n, 2) * 0.05
        elif trial % 5 == 2:
            # Two concentric circles
            pts = []
            for i in range(n):
                r = 0.5 if i < n // 2 else 1.0
                angle = rng.uniform(0, 2 * math.pi)
                pts.append([r * math.cos(angle), r * math.sin(angle)])
            pts = np.array(pts)
        else:
            pts = rng.randn(n, 2) * 0.5

        if _has_duplicate_points(pts):
            continue

        current_count = unit_distance_count(pts)

        # SA with circle-snap moves
        temp = 0.5
        for it in range(iterations):
            temp *= 0.996
            idx = rng.randint(n)
            old_pos = pts[idx].copy()

            if rng.random() < 0.5 and n > 2:
                # Circle-snap: place idx at intersection of two unit circles
                others = [k for k in range(n) if k != idx]
                i, j = rng.choice(others, 2, replace=False)
                d = np.linalg.norm(pts[i] - pts[j])
                if 1e-6 < d < 2.0 - 1e-6:
                    a = d / 2
                    h = math.sqrt(max(1.0 - a**2, 0.0))
                    mid = (pts[i] + pts[j]) / 2
                    direction = (pts[j] - pts[i]) / d
                    perp = np.array([-direction[1], direction[0]])
                    if rng.random() < 0.5:
                        pts[idx] = mid + h * perp
                    else:
                        pts[idx] = mid - h * perp
                else:
                    pts[idx] += rng.randn(2) * max(temp, 0.002)
            else:
                pts[idx] += rng.randn(2) * max(temp, 0.002)

            # Reject if duplicate created
            if _has_duplicate_points(pts):
                pts[idx] = old_pos
                continue

            new_count = unit_distance_count(pts)
            if new_count > current_count:
                current_count = new_count
            elif new_count == current_count and rng.random() < 0.5:
                current_count = new_count
            elif rng.random() < math.exp(-max(current_count - new_count, 0) / max(temp, 0.001)):
                current_count = new_count
            else:
                pts[idx] = old_pos

        if not _has_duplicate_points(pts):
            count = unit_distance_count(pts)
            if count > best_count:
                best_count = count
                best_config = pts.copy()

    return best_count, best_config


def compute_max_unit_distances(n_range: Tuple[int, int] = (2, 14),
                               trials: int = 200) -> Dict[int, int]:
    """Compute u(n) = max unit distances for n in range.

    Known exact values (OEIS A186705):
      u(2)=1, u(3)=3, u(4)=5, u(5)=7, u(6)=9,
      u(7)=12, u(8)=14, u(9)=18, u(10)=20, u(11)=23,
      u(12)=27, u(13)=30, u(14)=33
    """
    results = {}
    for n in range(n_range[0], n_range[1] + 1):
        # For small n, the greedy builder is already optimal; use it directly
        greedy = _build_unit_distance_graph(n)
        greedy_count = unit_distance_count(greedy)

        # Also run SA for potentially better results
        sa_count, sa_config = _optimize_unit_distances(n, trials=trials)

        results[n] = max(greedy_count, sa_count)
    return results


# Known exact values (OEIS A186705)
KNOWN_UNIT_DISTANCES = {
    2: 1,
    3: 3,
    4: 5,
    5: 7,
    6: 9,
    7: 12,
    8: 14,
    9: 18,
    10: 20,
    11: 23,
    12: 27,
    13: 30,
    14: 33,
}


# ---------------------------------------------------------------------------
# 3. ERDOS-SZEKERES CONVEX POSITION
#
# f(k) = min n such that any n points in general position contain k in
# convex position.  The Erdos-Szekeres theorem gives upper bound
# f(k) <= C(2k-4, k-2) + 1.  Exact values: f(3)=3 trivially (but the
# "canonical" Happy Ending convention gives f(3)=5 counting non-general too),
# f(4)=5, f(5)=9, f(6)=17 (Szekeres-Peters 2006).
# ---------------------------------------------------------------------------

def points_in_general_position(points: np.ndarray, tol: float = 1e-10) -> bool:
    """Check no three points are collinear."""
    n = len(points)
    for i, j, k in combinations(range(n), 3):
        v1 = points[j] - points[i]
        v2 = points[k] - points[i]
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        if abs(cross) < tol:
            return False
    return True


def max_convex_subset_size(points: np.ndarray) -> int:
    """Find the maximum number of points in convex position.

    A set is in convex position if all points are vertices of its convex hull.
    Brute force for small n.
    """
    from scipy.spatial import ConvexHull
    n = len(points)
    if n <= 3:
        return n

    for size in range(n, 2, -1):
        for subset in combinations(range(n), size):
            sub_pts = points[list(subset)]
            try:
                hull = ConvexHull(sub_pts)
                if len(hull.vertices) == size:
                    return size
            except Exception:
                continue
    return min(n, 3)


def erdos_szekeres_bound(k: int) -> int:
    """Erdos-Szekeres upper bound: f(k) <= C(2k-4, k-2) + 1."""
    if k <= 2:
        return k
    return math.comb(2 * k - 4, k - 2) + 1


def verify_erdos_szekeres(k: int, num_trials: int = 500) -> Dict:
    """Verify Erdos-Szekeres experimentally for small k.

    Generate random point sets and check the minimum n for which
    ALL sets contain k points in convex position.
    """
    rng = np.random.RandomState(42)
    f_k = KNOWN_ES_VALUES.get(k, erdos_szekeres_bound(k))

    results = {
        'k': k,
        'known_f_k': f_k,
        'ES_bound': erdos_szekeres_bound(k),
        'trials': num_trials,
        'fraction_containing_k_convex': {},
    }

    if f_k > 25:
        results['note'] = f'f({k})={f_k} too large for brute force'
        return results

    for n in range(k, min(f_k + 2, 18)):
        success = 0
        for _ in range(num_trials):
            pts = rng.randn(n, 2)
            if max_convex_subset_size(pts) >= k:
                success += 1
        results['fraction_containing_k_convex'][n] = success / num_trials

    return results


# Known exact values for Erdos-Szekeres f(k):
KNOWN_ES_VALUES = {
    3: 3,    # any 3 non-collinear points are in convex position
    4: 5,    # f(4) = 5 (the Happy Ending theorem)
    5: 9,    # f(5) = 9
    6: 17,   # f(6) = 17 (Szekeres-Peters 2006, computer-assisted proof)
}


# ---------------------------------------------------------------------------
# 4. DIAMETER GRAPHS (#604, $500)
#
# Given n points with diameter 1, what is the max number of diametral pairs
# (pairs at distance exactly 1)?
#
# Hopf-Pannwitz (1934): at most n such pairs in R^2.
# This is tight: Reuleaux polygons achieve d(n) = n for all n >= 3.
#
# A Reuleaux polygon of order k (k odd >= 3) is a curve of constant width
# formed from k circular arcs.  By placing points at vertices and on arcs
# opposite a vertex, each such point is at distance 1 from the opposite vertex.
# ---------------------------------------------------------------------------

def diameter_edge_count(points: np.ndarray, tol: float = 1e-8) -> int:
    """Count pairs at distance equal to the diameter."""
    if len(points) < 2:
        return 0
    sq_dists = _squared_distances(points)
    diam_sq = np.max(sq_dists)
    return int(np.sum(np.abs(sq_dists - diam_sq) < tol * max(1.0, diam_sq)))


def all_pairwise_le_1(points: np.ndarray, tol: float = 1e-9) -> bool:
    """Check all pairwise distances are at most 1."""
    sq_dists = _squared_distances(points)
    return np.all(sq_dists <= 1.0 + tol)


def _reuleaux_triangle_config(n: int) -> np.ndarray:
    """Construct n points achieving d(n)=n diametral pairs.

    Place points on the boundary of a Reuleaux triangle (width 1).
    The Reuleaux triangle has 3 vertices A, B, C forming an equilateral
    triangle of side 1.  Arc BC is centered at A (radius 1), etc.

    Each point on arc BC is at distance 1 from A.  By distributing extra
    points on different arcs, each is at distance 1 from the opposite vertex.
    """
    s3 = math.sqrt(3)
    # Equilateral triangle vertices, side length 1
    A = np.array([0.0, 0.0])
    B = np.array([1.0, 0.0])
    C = np.array([0.5, s3 / 2])
    vertices = [A, B, C]

    if n <= 3:
        return np.array(vertices[:n])

    pts = list(vertices)
    remaining = n - 3

    # Arc opposite to each vertex:
    # Arc BC centered at A, arc CA centered at B, arc AB centered at C
    arcs = [
        (A, B, C),  # center=A, from B to C
        (B, C, A),  # center=B, from C to A
        (C, A, B),  # center=C, from A to B
    ]

    # Distribute remaining points across arcs
    per_arc = remaining // 3
    extra = remaining % 3

    for arc_idx, (center, start, end) in enumerate(arcs):
        count = per_arc + (1 if arc_idx < extra else 0)
        if count == 0:
            continue

        # Parametrize arc from start to end, centered at center, radius 1
        angle_start = math.atan2(start[1] - center[1], start[0] - center[0])
        angle_end = math.atan2(end[1] - center[1], end[0] - center[0])

        # The arc goes from start to end (the shorter arc, ~60 degrees)
        # For equilateral triangle, the angle is pi/3
        if angle_end < angle_start:
            angle_end += 2 * math.pi

        # Check: both angles should span about pi/3
        diff = angle_end - angle_start
        if diff > math.pi:
            # Go the other way
            angle_end -= 2 * math.pi
            if angle_end > angle_start:
                angle_start, angle_end = angle_end, angle_start

        for i in range(count):
            t = (i + 1) / (count + 1)
            angle = angle_start + t * (angle_end - angle_start)
            pt = center + np.array([math.cos(angle), math.sin(angle)])
            pts.append(pt)

    return np.array(pts[:n])


def compute_max_diameter_edges(n_range: Tuple[int, int] = (3, 12)) -> Dict[int, Tuple[int, np.ndarray]]:
    """Compute d(n) = max diametral pairs for n points with diameter 1.

    Hopf-Pannwitz: d(n) = n for all n >= 3 in R^2.
    """
    results = {}
    for n in range(n_range[0], n_range[1] + 1):
        config = _reuleaux_triangle_config(n)
        # Verify diameter = 1
        sq_dists = _squared_distances(config)
        diam = math.sqrt(np.max(sq_dists))
        if diam > 1e-10:
            config = config / diam  # normalize to diameter 1
        count = diameter_edge_count(config)
        results[n] = (count, config)
    return results


# Known: d(n) = n for n >= 3 in R^2 (Hopf-Pannwitz)
KNOWN_DIAMETER_EDGES = {n: n for n in range(3, 16)}


# ---------------------------------------------------------------------------
# 5. REPEATED DISTANCES (#90, $500)
#
# t(n) = max multiplicity of any single distance among n points in R^2.
# Erdos conjectured t(n) = O(n^{1+epsilon}) for every epsilon > 0.
# Known: t(n) = O(n^{4/3}) by Szemeredi-Trotter.
# Construction: t(n) >= n^{1+c/log log n} using lattice points.
#
# We compute exact values for small n on the integer lattice Z^2,
# then also search over R^2 using algebraic constructions.
# ---------------------------------------------------------------------------

def _lattice_repeated_distances(n: int, grid_size: int = 0) -> Tuple[int, np.ndarray]:
    """Find n points on Z^2 maximizing the multiplicity of any single distance.

    For small n, exhaustive search over subsets of the grid.
    For larger n, local search.
    """
    if grid_size == 0:
        grid_size = max(int(math.ceil(math.sqrt(n))) + 2, 5)

    grid_pts = []
    for i in range(grid_size):
        for j in range(grid_size):
            grid_pts.append(np.array([float(i), float(j)]))
    grid_pts = np.array(grid_pts)
    total = len(grid_pts)

    best_mult = 0
    best_config = None

    if math.comb(total, n) <= 500000 and n <= 9:
        # Exhaustive
        for subset in combinations(range(total), n):
            pts = grid_pts[list(subset)]
            mult, _ = max_distance_multiplicity(pts)
            if mult > best_mult:
                best_mult = mult
                best_config = pts.copy()
    else:
        rng = np.random.RandomState(42)
        for trial in range(500):
            if trial == 0:
                center = np.array([grid_size / 2.0, grid_size / 2.0])
                d = np.linalg.norm(grid_pts - center, axis=1)
                indices = list(np.argsort(d)[:n])
            else:
                indices = sorted(rng.choice(total, n, replace=False))

            # Local search
            for _ in range(300):
                pts = grid_pts[indices]
                current_mult, _ = max_distance_multiplicity(pts)
                improved = False
                idx_set = set(indices)
                avail = [i for i in range(total) if i not in idx_set]
                if not avail:
                    break
                for pos in range(n):
                    old = indices[pos]
                    sample_size = min(len(avail), 20)
                    for new_idx in rng.choice(avail, sample_size, replace=False):
                        indices[pos] = new_idx
                        pts = grid_pts[indices]
                        m, _ = max_distance_multiplicity(pts)
                        if m > current_mult:
                            current_mult = m
                            idx_set.discard(old)
                            idx_set.add(new_idx)
                            avail = [i for i in range(total) if i not in idx_set]
                            improved = True
                            break
                        indices[pos] = old
                if not improved:
                    break

            pts = grid_pts[indices]
            m, _ = max_distance_multiplicity(pts)
            if m > best_mult:
                best_mult = m
                best_config = pts.copy()

    return best_mult, best_config


def _repeated_distances_continuous(n: int, trials: int = 200) -> Tuple[int, np.ndarray]:
    """Find n points in R^2 maximizing repeated distance multiplicity.

    Key construction: n points on a circle all have many equal distances.
    Regular n-gon on a circle has floor(n/2) distinct distances, each occurring
    at least n times in the best case. More precisely, for regular n-gon:
    distance d_k appears n times for k = 1, ..., floor(n/2)-1 if n is even,
    and n times for k = 1, ..., (n-1)/2 if n is odd.
    """
    best_mult = 0
    best_config = None
    rng = np.random.RandomState(42)

    # Seed 1: Regular n-gon (each distance appears n times if n odd,
    # except the diameter which appears n/2 times if n even)
    reg = _regular_polygon(n)
    m, _ = max_distance_multiplicity(reg)
    if m > best_mult:
        best_mult = m
        best_config = reg.copy()

    # Seed 2: Two concentric regular polygons
    for k in range(2, n - 1):
        inner = _regular_polygon(k)
        outer = _regular_polygon(n - k) * 2.0
        pts = np.vstack([inner, outer])
        m, _ = max_distance_multiplicity(pts)
        if m > best_mult:
            best_mult = m
            best_config = pts.copy()

    # Seed 3: Points on a circle, choosing specific angles
    for trial in range(trials):
        angles = rng.uniform(0, 2 * math.pi, n)
        angles.sort()
        r = rng.uniform(0.5, 2.0)
        pts = r * np.column_stack([np.cos(angles), np.sin(angles)])
        m, _ = max_distance_multiplicity(pts)
        if m > best_mult:
            best_mult = m
            best_config = pts.copy()

    return best_mult, best_config


def compute_max_repeated_distances(n_range: Tuple[int, int] = (3, 12),
                                   grid_size: int = 0) -> Dict[int, Dict]:
    """Compute max distance multiplicity for n in range.

    Reports both lattice (Z^2) and continuous (R^2) results.
    """
    results = {}
    for n in range(n_range[0], n_range[1] + 1):
        lattice_mult, lattice_config = _lattice_repeated_distances(n, grid_size=grid_size)
        cont_mult, cont_config = _repeated_distances_continuous(n, trials=100)
        results[n] = {
            'lattice_multiplicity': lattice_mult,
            'continuous_multiplicity': cont_mult,
            'best_multiplicity': max(lattice_mult, cont_mult),
        }
    return results


# ---------------------------------------------------------------------------
# Summary and main
# ---------------------------------------------------------------------------

def summarize_all(quick: bool = True) -> Dict:
    """Run all computations and return summary.

    Args:
        quick: If True, reduce n ranges for fast execution.
    """
    n_max_dd = 10 if quick else 12
    n_max_ud = 9 if quick else 14
    n_max_diam = 10 if quick else 12
    n_max_rep = 8 if quick else 12
    ud_trials = 100 if quick else 200

    summary = {}

    # 1. Distinct distances
    dd = compute_min_distinct_distances((3, n_max_dd))
    summary['distinct_distances'] = {
        'computed': {n: c for n, (c, _) in dd.items()},
        'known': {k: v for k, v in KNOWN_DISTINCT_DISTANCES.items() if k <= n_max_dd},
        'problem': '#89',
        'prize': '$500',
    }

    # 2. Unit distances
    ud = compute_max_unit_distances((2, n_max_ud), trials=ud_trials)
    summary['unit_distances'] = {
        'computed': ud,
        'known': {k: v for k, v in KNOWN_UNIT_DISTANCES.items() if k <= n_max_ud},
        'problem': '#99',
        'prize': '$100',
    }

    # 3. Erdos-Szekeres
    es = {k: erdos_szekeres_bound(k) for k in range(3, 8)}
    summary['erdos_szekeres'] = {
        'bounds': es,
        'known': KNOWN_ES_VALUES,
        'problem': '#93-#95',
    }

    # 4. Diameter graphs
    diam = compute_max_diameter_edges((3, n_max_diam))
    summary['diameter_graphs'] = {
        'computed': {n: c for n, (c, _) in diam.items()},
        'known': {k: v for k, v in KNOWN_DIAMETER_EDGES.items() if k <= n_max_diam},
        'problem': '#604',
        'prize': '$500',
    }

    # 5. Repeated distances
    rep = compute_max_repeated_distances((3, n_max_rep))
    summary['repeated_distances'] = {
        'computed': {n: v['best_multiplicity'] for n, v in rep.items()},
        'lattice': {n: v['lattice_multiplicity'] for n, v in rep.items()},
        'continuous': {n: v['continuous_multiplicity'] for n, v in rep.items()},
        'problem': '#90',
        'prize': '$500',
    }

    return summary


if __name__ == '__main__':
    print("=" * 70)
    print("ERDOS GEOMETRY PROBLEMS: COMPUTATIONAL ATTACKS")
    print("=" * 70)

    results = summarize_all(quick=True)

    print("\n1. DISTINCT DISTANCES (#89, $500)")
    print("   g(n) = min distinct distances among n planar points")
    print(f"   {'n':>3s}  {'computed':>9s}  {'known':>6s}  {'match':>6s}")
    dd = results['distinct_distances']
    for n in sorted(dd['computed'].keys()):
        c = dd['computed'][n]
        k = dd['known'].get(n, '?')
        match_str = 'OK' if c == k else f'({c} vs {k})'
        print(f"   {n:>3d}  {c:>9d}  {str(k):>6s}  {match_str:>6s}")

    print("\n2. UNIT DISTANCES (#99, $100)")
    print("   u(n) = max unit-distance pairs among n planar points")
    print(f"   {'n':>3s}  {'computed':>9s}  {'known':>6s}  {'match':>6s}")
    ud = results['unit_distances']
    for n in sorted(ud['computed'].keys()):
        c = ud['computed'][n]
        k = ud['known'].get(n, '?')
        match_str = 'OK' if c == k else f'({c} vs {k})'
        print(f"   {n:>3d}  {c:>9d}  {str(k):>6s}  {match_str:>6s}")

    print("\n3. ERDOS-SZEKERES CONVEX POSITION")
    es = results['erdos_szekeres']
    for k in sorted(es['known'].keys()):
        bound = es['bounds'][k]
        known = es['known'][k]
        print(f"   f({k}) = {known}  (ES upper bound: {bound})")

    print("\n4. DIAMETER GRAPHS (#604, $500)")
    print("   d(n) = max diametral pairs among n points with diam 1")
    print(f"   {'n':>3s}  {'computed':>9s}  {'known':>6s}")
    diam = results['diameter_graphs']
    for n in sorted(diam['computed'].keys()):
        c = diam['computed'][n]
        k = diam['known'].get(n, '?')
        print(f"   {n:>3d}  {c:>9d}  {str(k):>6s}")

    print("\n5. REPEATED DISTANCES (#90, $500)")
    print("   t(n) = max multiplicity of any distance among n points")
    rep = results['repeated_distances']
    print(f"   {'n':>3s}  {'best':>6s}  {'lattice':>8s}  {'contin':>7s}")
    for n in sorted(rep['computed'].keys()):
        b = rep['computed'][n]
        la = rep['lattice'][n]
        co = rep['continuous'][n]
        print(f"   {n:>3d}  {b:>6d}  {la:>8d}  {co:>7d}")

    print("\n" + "=" * 70)
