#!/usr/bin/env python3
"""
tda_problems.py -- Topological Data Analysis of the Erdos problem space.

Applies persistent homology and the Mapper algorithm to the corpus of 1,183
Erdos problems, treating each problem as a point in a feature space derived
from tags, OEIS links, prize values, resolution status, and formalization
state.

Topological features discovered:
  H0 (connected components) -- robust problem clusters that persist across
      many filtration scales, revealing deep structural families.
  H1 (1-cycles / loops) -- circular relationships between problem groups;
      families that reference each other in a ring.
  H2 (2-cycles / voids) -- holes in the problem landscape, signalling
      missing problem types that "should" exist given the surrounding
      structure.

Also implements a Mapper graph for low-dimensional visualization of the
high-dimensional problem space using configurable lens functions.

Implementation note: Since ripser/gudhi are not available in this
environment, we implement persistent homology from first principles using
Vietoris-Rips filtration with union-find (H0) and the standard boundary
matrix reduction algorithm (H1, H2).
"""

from __future__ import annotations

import re
import math
import yaml
import numpy as np
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from scipy.spatial.distance import pdist, squareform
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"

# ── Status categories ────────────────────────────────────────────────
_SOLVED_STATES = frozenset({
    "proved", "disproved", "solved",
    "proved (Lean)", "disproved (Lean)", "solved (Lean)",
})
_OPEN_STATES = frozenset({"open"})


# =====================================================================
# 0. Data helpers (consistent with other src/ modules)
# =====================================================================

def load_problems() -> List[Dict]:
    """Load the YAML problem corpus."""
    with open(DATA_PATH) as f:
        return yaml.safe_load(f)


def _status(p: Dict) -> str:
    return p.get("status", {}).get("state", "unknown")


def _tags(p: Dict) -> Set[str]:
    return set(p.get("tags", []))


def _number(p: Dict) -> int:
    n = p.get("number", 0)
    return int(n) if isinstance(n, (int, str)) and str(n).isdigit() else 0


def _prize(p: Dict) -> float:
    pz = p.get("prize", "no")
    if not pz or pz == "no":
        return 0.0
    nums = re.findall(r"[\d,]+", str(pz))
    if nums:
        val = float(nums[0].replace(",", ""))
        if "\u00a3" in str(pz):
            val *= 1.27
        return val
    return 0.0


def _oeis_valid(p: Dict) -> List[str]:
    """Return OEIS references, filtering out 'N/A' and 'possible'."""
    refs = p.get("oeis", [])
    if not isinstance(refs, list):
        return []
    return [r for r in refs if isinstance(r, str)
            and r.startswith("A") and r not in ("N/A", "possible")]


def _is_solved(p: Dict) -> bool:
    return _status(p) in _SOLVED_STATES


def _is_open(p: Dict) -> bool:
    return _status(p) in _OPEN_STATES


def _is_formalized(p: Dict) -> bool:
    return p.get("formalized", {}).get("state", "no") == "yes"


# =====================================================================
# 1. Point-cloud construction
# =====================================================================

def build_tag_vocabulary(problems: List[Dict]) -> List[str]:
    """Deterministic sorted tag list for reproducible feature ordering."""
    tags: Set[str] = set()
    for p in problems:
        tags |= _tags(p)
    return sorted(tags)


def problem_to_feature_vector(
    p: Dict,
    tag_vocab: List[str],
    tag_index: Dict[str, int],
) -> np.ndarray:
    """
    Map a single problem to R^d.

    Features (in order):
      - Binary indicator per tag (len = |tag_vocab|)
      - OEIS count (valid refs only)
      - log1p(prize)
      - is_solved (binary)
      - is_open (binary)
      - is_formalized (binary)
      - normalized problem number (ordinal position)
    """
    n_tags = len(tag_vocab)
    vec = np.zeros(n_tags + 6, dtype=np.float64)

    # Tag indicators
    for t in _tags(p):
        if t in tag_index:
            vec[tag_index[t]] = 1.0

    # Numerical features
    vec[n_tags] = len(_oeis_valid(p))
    vec[n_tags + 1] = math.log1p(_prize(p))
    vec[n_tags + 2] = float(_is_solved(p))
    vec[n_tags + 3] = float(_is_open(p))
    vec[n_tags + 4] = float(_is_formalized(p))
    vec[n_tags + 5] = _number(p) / 1200.0  # rough normalization

    return vec


def build_point_cloud(
    problems: List[Dict],
    standardize: bool = True,
) -> Tuple[np.ndarray, List[str], List[int]]:
    """
    Build the full point cloud X in R^d.

    Returns:
        X         -- (n, d) array of feature vectors
        tag_vocab -- ordered list of tags used as features
        numbers   -- problem numbers in the same row order as X
    """
    tag_vocab = build_tag_vocabulary(problems)
    tag_index = {t: i for i, t in enumerate(tag_vocab)}

    rows = []
    numbers = []
    for p in problems:
        rows.append(problem_to_feature_vector(p, tag_vocab, tag_index))
        numbers.append(_number(p))

    X = np.array(rows, dtype=np.float64)

    if standardize and X.shape[0] > 1:
        scaler = StandardScaler()
        X = scaler.fit_transform(X)

    return X, tag_vocab, numbers


# =====================================================================
# 2. Distance matrix
# =====================================================================

def compute_distance_matrix(X: np.ndarray) -> np.ndarray:
    """Euclidean distance matrix from point cloud."""
    return squareform(pdist(X, metric="euclidean"))


# =====================================================================
# 3. Persistent homology -- from-scratch implementation
# =====================================================================

class UnionFind:
    """Union-Find with path compression and union by rank."""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.n_components = n

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        # path compression
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> bool:
        """Merge components; return True if a merge happened."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        self.n_components -= 1
        return True


def _sorted_edges(D: np.ndarray) -> List[Tuple[float, int, int]]:
    """
    Return all edges (i < j) sorted by distance.

    For performance with large n we cap at n=1200 (the full corpus).
    """
    n = D.shape[0]
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            edges.append((D[i, j], i, j))
    edges.sort(key=lambda e: e[0])
    return edges


def compute_persistence_h0(
    D: np.ndarray,
) -> List[Tuple[float, float]]:
    """
    Compute H0 persistent homology (connected-component births/deaths).

    Every vertex is born at filtration value 0.  When an edge merges two
    components, the younger component dies at that edge's weight.  The
    oldest component (the one that never dies) gets death = inf.

    Returns list of (birth, death) pairs.
    """
    n = D.shape[0]
    if n == 0:
        return []

    uf = UnionFind(n)
    # Track birth time of each component (all born at 0)
    birth = {i: 0.0 for i in range(n)}
    intervals: List[Tuple[float, float]] = []

    edges = _sorted_edges(D)

    for weight, i, j in edges:
        ri, rj = uf.find(i), uf.find(j)
        if ri != rj:
            # The younger component dies; the elder absorbs it.
            # "younger" = higher birth (here all are 0, so pick the one
            # that becomes non-root).
            if uf.rank[ri] < uf.rank[rj]:
                ri, rj = rj, ri
            # rj gets absorbed into ri
            dying_birth = birth.pop(rj, 0.0)
            intervals.append((dying_birth, weight))
            uf.union(i, j)

    # The final surviving component: birth 0, death infinity
    for root_birth in birth.values():
        intervals.append((root_birth, float("inf")))

    return intervals


def _build_vr_simplices(
    D: np.ndarray,
    max_dim: int = 2,
    max_edge_length: float = float("inf"),
    max_simplices: int = 500_000,
) -> List[Tuple[float, Tuple[int, ...]]]:
    """
    Build Vietoris-Rips simplices up to dimension max_dim, sorted by
    filtration value.

    A k-simplex (v0, ..., vk) enters the filtration at the maximum
    pairwise distance among its vertices.

    Returns list of (filtration_value, simplex_tuple), sorted.
    """
    n = D.shape[0]
    simplices: List[Tuple[float, Tuple[int, ...]]] = []

    # 0-simplices (vertices): born at 0
    for i in range(n):
        simplices.append((0.0, (i,)))

    # 1-simplices (edges)
    edges_by_weight: List[Tuple[float, int, int]] = []
    for i in range(n):
        for j in range(i + 1, n):
            w = D[i, j]
            if w <= max_edge_length:
                edges_by_weight.append((w, i, j))
    edges_by_weight.sort()

    for w, i, j in edges_by_weight:
        simplices.append((w, (i, j)))

    if max_dim < 2 or len(simplices) > max_simplices:
        simplices.sort()
        return simplices[:max_simplices]

    # 2-simplices (triangles): check all triples that form cliques
    # For performance, build adjacency at each edge threshold
    adj: Dict[int, Set[int]] = defaultdict(set)

    # Sort edges and build triangles incrementally
    triangles: List[Tuple[float, Tuple[int, ...]]] = []
    for w, i, j in edges_by_weight:
        # Check for common neighbors already connected to both i and j
        common = adj[i] & adj[j]
        for k in common:
            filt_val = max(D[i, j], D[i, k], D[j, k])
            verts = tuple(sorted([i, j, k]))
            triangles.append((filt_val, verts))
        adj[i].add(j)
        adj[j].add(i)

    simplices.extend(triangles)
    simplices.sort(key=lambda s: (s[0], len(s[1])))

    if len(simplices) > max_simplices:
        simplices = simplices[:max_simplices]

    return simplices


def _boundary_matrix_mod2(
    simplices: List[Tuple[float, Tuple[int, ...]]],
) -> Tuple[Dict[int, Set[int]], Dict[Tuple[int, ...], int]]:
    """
    Build the boundary matrix over Z/2Z for the simplex list.

    Returns:
        columns -- dict mapping column index to set of row indices (sparse)
        simplex_to_idx -- maps simplex tuple to its index in the list
    """
    simplex_to_idx: Dict[Tuple[int, ...], int] = {}
    for idx, (_, sigma) in enumerate(simplices):
        simplex_to_idx[sigma] = idx

    columns: Dict[int, Set[int]] = {}
    for idx, (_, sigma) in enumerate(simplices):
        if len(sigma) <= 1:
            columns[idx] = set()  # 0-simplices have empty boundary
            continue
        # boundary of (v0, ..., vk) = sum of (v0,...,v_{i-1},v_{i+1},...,vk)
        boundary: Set[int] = set()
        for i in range(len(sigma)):
            face = sigma[:i] + sigma[i + 1:]
            if face in simplex_to_idx:
                row = simplex_to_idx[face]
                # Z/2 addition: XOR
                if row in boundary:
                    boundary.remove(row)
                else:
                    boundary.add(row)
        columns[idx] = boundary

    return columns, simplex_to_idx


def _reduce_boundary_matrix(
    columns: Dict[int, Set[int]],
    n_simplices: int,
) -> Tuple[Dict[int, Set[int]], Dict[int, int]]:
    """
    Standard persistence algorithm: column reduction over Z/2Z.

    Returns:
        reduced -- the reduced column dictionary
        low_to_col -- maps low(j) -> j for non-zero columns
    """
    reduced = {j: set(columns.get(j, set())) for j in range(n_simplices)}
    low_to_col: Dict[int, int] = {}

    for j in range(n_simplices):
        while reduced[j]:
            low_j = max(reduced[j])
            if low_j in low_to_col:
                # Add column low_to_col[low_j] to column j (mod 2)
                other = low_to_col[low_j]
                reduced[j] = reduced[j].symmetric_difference(reduced[other])
            else:
                low_to_col[low_j] = j
                break

    return reduced, low_to_col


def compute_persistence(
    D: np.ndarray,
    max_dim: int = 2,
    max_edge_pct: float = 0.3,
    max_simplices: int = 500_000,
) -> Dict[int, List[Tuple[float, float]]]:
    """
    Compute persistent homology H0, H1, (optionally H2) from a distance
    matrix using explicit Vietoris-Rips filtration and boundary matrix
    reduction.

    Parameters:
        D              -- square distance matrix
        max_dim        -- highest homology dimension to compute
        max_edge_pct   -- percentile of edge lengths to use as cutoff
                          (controls complex size)
        max_simplices  -- hard cap on simplex count for tractability

    Returns dict mapping dimension -> list of (birth, death) intervals.
    """
    n = D.shape[0]
    if n == 0:
        return {d: [] for d in range(max_dim + 1)}

    if n == 1:
        # Single point: one eternal connected component, nothing higher
        result = {d: [] for d in range(max_dim + 1)}
        result[0] = [(0.0, float("inf"))]
        return result

    # Determine edge cutoff from percentile of pairwise distances
    upper = D[np.triu_indices(n, k=1)]
    if len(upper) == 0:
        return {d: [] for d in range(max_dim + 1)}
    max_edge_length = float(np.percentile(upper, max_edge_pct * 100))

    simplices = _build_vr_simplices(
        D, max_dim=max_dim,
        max_edge_length=max_edge_length,
        max_simplices=max_simplices,
    )

    columns, simplex_to_idx = _boundary_matrix_mod2(simplices)
    reduced, low_to_col = _reduce_boundary_matrix(columns, len(simplices))

    # Extract persistence intervals
    intervals: Dict[int, List[Tuple[float, float]]] = defaultdict(list)
    paired_births: Set[int] = set()

    for low_idx, col_idx in low_to_col.items():
        birth_simplex = simplices[low_idx]
        death_simplex = simplices[col_idx]
        dim = len(birth_simplex[1]) - 1  # dimension of the birth simplex
        b = birth_simplex[0]
        d = death_simplex[0]
        if abs(d - b) > 1e-12:  # skip zero-length intervals
            intervals[dim].append((b, d))
        paired_births.add(low_idx)

    # Unpaired simplices contribute infinite intervals
    paired_deaths = set(low_to_col.values())
    for idx in range(len(simplices)):
        if idx not in paired_births and idx not in paired_deaths:
            dim = len(simplices[idx][1]) - 1
            filt = simplices[idx][0]
            intervals[dim].append((filt, float("inf")))

    # Ensure all requested dimensions are present
    result = {}
    for d in range(max_dim + 1):
        result[d] = sorted(intervals.get(d, []))

    return result


# =====================================================================
# 4. Persistence analysis and interpretation
# =====================================================================

def persistence_to_lifetimes(
    intervals: List[Tuple[float, float]],
) -> np.ndarray:
    """Convert (birth, death) pairs to finite lifetimes (death - birth)."""
    lifetimes = []
    for b, d in intervals:
        if math.isinf(d):
            continue
        lifetimes.append(d - b)
    return np.array(lifetimes, dtype=np.float64) if lifetimes else np.array([])


def find_significant_features(
    intervals: List[Tuple[float, float]],
    threshold_factor: float = 2.0,
) -> List[Tuple[float, float, float]]:
    """
    Identify topologically significant features: those with lifetime
    exceeding threshold_factor * median_lifetime.

    Returns list of (birth, death, lifetime) for significant features.
    """
    lifetimes = persistence_to_lifetimes(intervals)
    if len(lifetimes) == 0:
        return []

    median_lt = float(np.median(lifetimes))
    threshold = threshold_factor * median_lt if median_lt > 0 else 0.0

    significant = []
    for b, d in intervals:
        lt = d - b if not math.isinf(d) else float("inf")
        if lt > threshold:
            significant.append((b, d, lt))

    return sorted(significant, key=lambda x: -x[2])


def persistence_entropy(intervals: List[Tuple[float, float]]) -> float:
    """
    Persistence entropy: Shannon entropy of the normalized lifetime
    distribution.  Measures how uniformly topological features are spread
    across scales.  Low entropy = a few dominant features; high entropy =
    many features of similar prominence.
    """
    lifetimes = persistence_to_lifetimes(intervals)
    if len(lifetimes) == 0:
        return 0.0
    total = lifetimes.sum()
    if total <= 0:
        return 0.0
    probs = lifetimes / total
    # Clip to avoid log(0)
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))


def total_persistence(intervals: List[Tuple[float, float]], p: float = 1.0) -> float:
    """L^p total persistence (sum of lifetime^p for finite intervals)."""
    lifetimes = persistence_to_lifetimes(intervals)
    if len(lifetimes) == 0:
        return 0.0
    return float(np.sum(lifetimes ** p))


# =====================================================================
# 5. Betti curves
# =====================================================================

def betti_curve(
    intervals: List[Tuple[float, float]],
    n_steps: int = 100,
    t_range: Optional[Tuple[float, float]] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the Betti curve: number of active intervals at each filtration
    value t.

    Returns (t_values, betti_values).
    """
    if not intervals:
        t = np.linspace(0, 1, n_steps)
        return t, np.zeros(n_steps)

    finite_deaths = [d for _, d in intervals if not math.isinf(d)]
    all_births = [b for b, _ in intervals]

    if t_range is None:
        t_min = min(all_births) if all_births else 0.0
        t_max = max(finite_deaths) if finite_deaths else 1.0
        if t_max <= t_min:
            t_max = t_min + 1.0
    else:
        t_min, t_max = t_range

    t_vals = np.linspace(t_min, t_max, n_steps)
    betti = np.zeros(n_steps, dtype=int)

    for b, d in intervals:
        active = (t_vals >= b) & (t_vals < d)
        betti += active.astype(int)

    return t_vals, betti


# =====================================================================
# 6. Mapper algorithm
# =====================================================================

def mapper(
    X: np.ndarray,
    lens: np.ndarray,
    n_intervals: int = 10,
    overlap_frac: float = 0.3,
    cluster_eps: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Mapper algorithm for topological summarization.

    Parameters:
        X              -- (n, d) point cloud
        lens           -- (n,) lens function values
        n_intervals    -- number of cover intervals
        overlap_frac   -- fractional overlap between adjacent intervals
        cluster_eps    -- DBSCAN epsilon; if None, auto-calibrate

    Returns dict with:
        nodes          -- list of (node_id, member_indices)
        edges          -- list of (node_a, node_b) sharing members
        node_sizes     -- list of ints (members per node)
        n_components   -- connected components in the Mapper graph
    """
    n = X.shape[0]
    if n == 0:
        return {"nodes": [], "edges": [], "node_sizes": [], "n_components": 0}

    # Auto-calibrate DBSCAN eps from nearest-neighbor distances
    if cluster_eps is None:
        from scipy.spatial.distance import cdist
        # Sample for speed
        sample_size = min(n, 500)
        rng = np.random.RandomState(42)
        idx = rng.choice(n, sample_size, replace=False)
        sample_dists = cdist(X[idx], X[idx])
        np.fill_diagonal(sample_dists, np.inf)
        nn_dists = sample_dists.min(axis=1)
        cluster_eps = float(np.percentile(nn_dists, 75))
        if cluster_eps <= 0:
            cluster_eps = 1.0

    # Build cover of the lens range
    l_min, l_max = float(lens.min()), float(lens.max())
    if l_max <= l_min:
        l_max = l_min + 1.0

    step = (l_max - l_min) / n_intervals
    overlap = step * overlap_frac

    nodes: List[Tuple[int, List[int]]] = []
    node_id = 0

    point_to_nodes: Dict[int, List[int]] = defaultdict(list)

    for k in range(n_intervals):
        lo = l_min + k * step - overlap
        hi = l_min + (k + 1) * step + overlap
        members = np.where((lens >= lo) & (lens <= hi))[0]

        if len(members) == 0:
            continue

        # Cluster within each cover element
        if len(members) == 1:
            nodes.append((node_id, members.tolist()))
            point_to_nodes[members[0]].append(node_id)
            node_id += 1
            continue

        X_local = X[members]
        db = DBSCAN(eps=cluster_eps, min_samples=1).fit(X_local)
        labels = db.labels_

        for lab in set(labels):
            if lab == -1:
                continue
            cluster_members = members[labels == lab].tolist()
            nodes.append((node_id, cluster_members))
            for m in cluster_members:
                point_to_nodes[m].append(node_id)
            node_id += 1

    # Build edges: two nodes share an edge if they have common members
    edge_set: Set[Tuple[int, int]] = set()
    for point_nodes in point_to_nodes.values():
        for i in range(len(point_nodes)):
            for j in range(i + 1, len(point_nodes)):
                a, b = point_nodes[i], point_nodes[j]
                edge_set.add((min(a, b), max(a, b)))

    edges = sorted(edge_set)

    # Connected components via union-find
    uf = UnionFind(node_id)
    for a, b in edges:
        uf.union(a, b)
    n_comp = len(set(uf.find(i) for i in range(node_id))) if node_id > 0 else 0

    return {
        "nodes": nodes,
        "edges": edges,
        "node_sizes": [len(members) for _, members in nodes],
        "n_components": n_comp,
    }


# =====================================================================
# 7. Solved vs. open topological comparison
# =====================================================================

def split_by_status(
    problems: List[Dict],
    X: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, List[int], List[int]]:
    """
    Split point cloud into solved and open subsets.

    Returns (X_solved, X_open, indices_solved, indices_open).
    """
    solved_idx = [i for i, p in enumerate(problems) if _is_solved(p)]
    open_idx = [i for i, p in enumerate(problems) if _is_open(p)]
    X_solved = X[solved_idx] if solved_idx else np.empty((0, X.shape[1]))
    X_open = X[open_idx] if open_idx else np.empty((0, X.shape[1]))
    return X_solved, X_open, solved_idx, open_idx


def topological_signature(
    D: np.ndarray,
    max_dim: int = 1,
    max_edge_pct: float = 0.3,
) -> Dict[str, Any]:
    """
    Compute a topological signature (summary statistics) from a distance
    matrix.  Used to compare solved vs. open problems.
    """
    if D.shape[0] < 2:
        return {
            "n_points": D.shape[0],
            "h0_n_features": 0,
            "h0_entropy": 0.0,
            "h0_total_persistence": 0.0,
            "h1_n_features": 0,
            "h1_entropy": 0.0,
            "h1_total_persistence": 0.0,
        }

    intervals = compute_persistence(D, max_dim=max_dim, max_edge_pct=max_edge_pct)

    sig: Dict[str, Any] = {"n_points": D.shape[0]}
    for dim in range(max_dim + 1):
        prefix = f"h{dim}"
        iv = intervals[dim]
        finite = [(b, d) for b, d in iv if not math.isinf(d)]
        sig[f"{prefix}_n_features"] = len(finite)
        sig[f"{prefix}_entropy"] = persistence_entropy(iv)
        sig[f"{prefix}_total_persistence"] = total_persistence(iv)

    return sig


def compare_solved_vs_open(
    problems: List[Dict],
    X: np.ndarray,
    max_points: int = 150,
) -> Dict[str, Any]:
    """
    Compare topological signatures of the solved and open subspaces.

    Subsamples if necessary for tractability (default 150 per group to
    keep the simplex count manageable while still getting rich H1).
    """
    X_solved, X_open, _, _ = split_by_status(problems, X)

    rng = np.random.RandomState(42)

    def _subsample(arr: np.ndarray) -> np.ndarray:
        if arr.shape[0] > max_points:
            idx = rng.choice(arr.shape[0], max_points, replace=False)
            return arr[idx]
        return arr

    X_solved_sub = _subsample(X_solved)
    X_open_sub = _subsample(X_open)

    result: Dict[str, Any] = {}

    if X_solved_sub.shape[0] >= 2:
        D_solved = compute_distance_matrix(X_solved_sub)
        result["solved"] = topological_signature(D_solved, max_edge_pct=0.25)
    else:
        result["solved"] = topological_signature(np.zeros((0, 0)))

    if X_open_sub.shape[0] >= 2:
        D_open = compute_distance_matrix(X_open_sub)
        result["open"] = topological_signature(D_open, max_edge_pct=0.25)
    else:
        result["open"] = topological_signature(np.zeros((0, 0)))

    return result


# =====================================================================
# 8. Full analysis pipeline
# =====================================================================

def analyze_problem_topology(
    max_points: int = 400,
    max_dim: int = 2,
    max_edge_pct: float = 0.3,
) -> Dict[str, Any]:
    """
    Run the complete TDA pipeline on the Erdos problem corpus.

    Parameters:
        max_points   -- subsample to this many points for tractability
        max_dim      -- max homology dimension
        max_edge_pct -- percentile cutoff for edge lengths

    Returns a dict with all results.
    """
    problems = load_problems()

    X, tag_vocab, numbers = build_point_cloud(problems)

    # Subsample if needed
    rng = np.random.RandomState(42)
    if X.shape[0] > max_points:
        idx = rng.choice(X.shape[0], max_points, replace=False)
        X_sub = X[idx]
        numbers_sub = [numbers[i] for i in idx]
        problems_sub = [problems[i] for i in idx]
    else:
        X_sub = X
        numbers_sub = numbers
        problems_sub = problems

    D = compute_distance_matrix(X_sub)

    # Persistent homology
    intervals = compute_persistence(D, max_dim=max_dim, max_edge_pct=max_edge_pct)

    # Significant features per dimension
    significant: Dict[int, List[Tuple[float, float, float]]] = {}
    for dim in range(max_dim + 1):
        significant[dim] = find_significant_features(intervals[dim])

    # Persistence entropy
    entropies = {dim: persistence_entropy(intervals[dim])
                 for dim in range(max_dim + 1)}

    # Total persistence
    total_pers = {dim: total_persistence(intervals[dim])
                  for dim in range(max_dim + 1)}

    # Betti curves
    betti_curves = {}
    for dim in range(max_dim + 1):
        t_vals, betti_vals = betti_curve(intervals[dim])
        betti_curves[dim] = {"t": t_vals, "betti": betti_vals}

    # Mapper with PCA-1 lens (first principal component -- most natural
    # continuous lens for Mapper; captures the dominant axis of variation)
    from sklearn.decomposition import PCA
    pca = PCA(n_components=min(3, X_sub.shape[1]), random_state=42)
    X_pca = pca.fit_transform(X_sub)
    mapper_pca1 = mapper(X_sub, X_pca[:, 0], n_intervals=15, overlap_frac=0.4)

    # Mapper with problem-number lens (temporal / ordinal structure)
    num_lens = np.array([_number(p) / 1200.0 for p in problems_sub])
    mapper_number = mapper(X_sub, num_lens, n_intervals=15, overlap_frac=0.4)

    # Mapper with eccentricity lens (distance from the "center" of the
    # point cloud -- highlights outlier problems at the periphery)
    centroid = X_sub.mean(axis=0)
    eccentricity = np.linalg.norm(X_sub - centroid, axis=1)
    mapper_eccentric = mapper(X_sub, eccentricity, n_intervals=15,
                              overlap_frac=0.4)

    # Solved vs open comparison
    comparison = compare_solved_vs_open(problems, X)

    return {
        "n_problems": len(problems),
        "n_features": X.shape[1],
        "n_subsampled": X_sub.shape[0],
        "tag_vocab": tag_vocab,
        "intervals": intervals,
        "significant_features": significant,
        "entropies": entropies,
        "total_persistence": total_pers,
        "betti_curves": betti_curves,
        "mapper_pca1": mapper_pca1,
        "mapper_problem_number": mapper_number,
        "mapper_eccentricity": mapper_eccentric,
        "solved_vs_open": comparison,
    }


# =====================================================================
# 9. CLI entry point
# =====================================================================

def main() -> None:
    """Print a summary of the TDA analysis."""
    print("=" * 70)
    print("TOPOLOGICAL DATA ANALYSIS OF THE ERDOS PROBLEM SPACE")
    print("=" * 70)

    results = analyze_problem_topology(max_points=300, max_dim=2,
                                       max_edge_pct=0.25)

    print(f"\nPoint cloud: {results['n_problems']} problems in "
          f"R^{results['n_features']}")
    print(f"Subsampled to {results['n_subsampled']} points for filtration")

    for dim in range(3):
        iv = results["intervals"].get(dim, [])
        finite = [(b, d) for b, d in iv if not math.isinf(d)]
        inf_count = sum(1 for _, d in iv if math.isinf(d))
        sig = results["significant_features"].get(dim, [])
        ent = results["entropies"].get(dim, 0.0)
        tp = results["total_persistence"].get(dim, 0.0)

        print(f"\n--- H{dim} ---")
        print(f"  Intervals: {len(finite)} finite, {inf_count} infinite")
        print(f"  Significant features (>2x median): {len(sig)}")
        print(f"  Persistence entropy: {ent:.3f} bits")
        print(f"  Total persistence: {tp:.3f}")

        if sig:
            print(f"  Top features:")
            for b, d, lt in sig[:5]:
                d_str = f"{d:.3f}" if not math.isinf(d) else "inf"
                print(f"    [{b:.3f}, {d_str}) lifetime={lt:.3f}")

    # Mapper summaries
    for name, key in [("PCA-1", "mapper_pca1"),
                      ("problem_number", "mapper_problem_number"),
                      ("eccentricity", "mapper_eccentricity")]:
        m = results[key]
        print(f"\n--- Mapper (lens={name}) ---")
        print(f"  Nodes: {len(m['nodes'])}, Edges: {len(m['edges'])}")
        print(f"  Connected components: {m['n_components']}")
        if m["node_sizes"]:
            print(f"  Node sizes: min={min(m['node_sizes'])}, "
                  f"max={max(m['node_sizes'])}, "
                  f"mean={np.mean(m['node_sizes']):.1f}")

    # Solved vs open
    cmp = results["solved_vs_open"]
    print(f"\n--- Solved vs Open comparison ---")
    for label in ("solved", "open"):
        sig = cmp[label]
        print(f"  {label.upper()} ({sig['n_points']} pts): "
              f"H0 entropy={sig['h0_entropy']:.3f}, "
              f"H1 features={sig['h1_n_features']}")


if __name__ == "__main__":
    main()
