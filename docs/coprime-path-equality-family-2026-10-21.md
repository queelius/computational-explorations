# A published stability corollary for the ten-vertex path

**Updated:** October 21, 2026, after the targeted overlap review.
**Status:** written corollary of published mathematics; human verification
pending. The bound, equality uniqueness, and order range below are not
claimed as new. Prepared for Alexander Richard Towell with substantial
OpenAI Codex assistance.

The earlier version extended our manuscript's proof to `n >= 13` and left
uniqueness novelty unresolved. A further proof check extended it to 12.
The subsequent literature check found that the entire statement follows
directly from Ma–Yuan's equality refinement, stated as Theorem 3 in
[Yuan, *Circumference, minimum degree and clique number*, E-JC 31(4)
(2024), #P4.64, page 2](https://www.combinatorics.org/ojs/index.php/eljc/article/download/v31i4p64/pdf/).
The [earlier deduction remains in Git](https://github.com/queelius/computational-explorations/blob/161d39034acacdaa1dc04dfc28b4977ed693d74e/docs/coprime-path-equality-family-2026-10-21.md).

## Statement

Let `J` be a connected simple graph on `n >= 12` vertices with no path on
ten vertices. Write `tau(J)` for its minimum vertex-cover size. If
`tau(J) >= 5`, then

\[
e(J)\leq3n-3,
\]

with equality if and only if

\[
J\cong K_3\vee\bigl(K_3\cup\overline K_{n-6}\bigr).
\]

Paths here count vertices. The symbol `vee` means joining every vertex
of one graph to every vertex of the other.

## Short proof and walkthrough

**1. Turn paths into cycles.** Add a universal vertex `u`, obtaining
`Q = J + u` of order `N = n + 1 >= 13`. Removing `u` leaves connected `J`;
removing any other vertex leaves a graph connected through `u`. Thus `Q`
is 2-connected. A cycle of at least eleven vertices through `u` would give
a ten-vertex path after deleting `u`; one avoiding `u` already contains
such a path. Hence `Q` has circumference less than eleven.

**2. Apply the published equality refinement.** Write

\[
h(N,k,a)=\binom{k-a}{2}+a(N-k+a).
\]

Here `H(N,k,a)` consists of a joining clique of size `a`, a clique of
size `k-2a`, and `N-k+a` independent vertices; the latter two parts have
no edges between them. For `k=11`, the three relevant sizes are

\[
h(N,11,2)=2N+18,\quad h(N,11,3)=3N+4,\quad
h(N,11,4)=4N-7.
\]

Suppose `e(J) >= 3n-3`. Then `e(Q) >= 4N-7`. For `N >= 13`, both of
the first two displayed sizes are strictly smaller. Theorem 3, specialized
to `k=11` and `ell=5`, leaves the following possibilities:

| Published alternative | Consequence here |
| --- | --- |
| `Q` is a subgraph of `H(N,11,2)` | Impossible: too few edges. |
| `Q = H(N,11,3)` | Impossible: too few edges. |
| `Q` is a subgraph of `H(N,11,5)` | Gives a four-vertex cover of `J`, as below. |
| `Q = H(N,11,4)` | Gives the asserted equality graph. |

The exceptional case for cycle threshold seven is irrelevant. The strict
edge inequality in this published refinement is what lets us handle
equality; the older FKV/FKVL statements alone stopped at that boundary.

**3. Remove the universal vertex.** The container `H(N,11,5)` is
`K_5` joined to an independent set. Its outside vertices have degree at
most five, whereas `u` has degree `N-1 >= 12`. Thus `u` lies in the
five-vertex part. The other four vertices cover `J`, contrary to
`tau(J) >= 5`.

Only `Q = H(N,11,4)` remains. Its universal vertices are exactly its
four-vertex joining clique. Deleting `u` gives
`K_3 ∨ (K_3 ∪ I_(n-6))` and exactly `3n-3` edges. In particular, more
than `3n-3` edges is impossible under the cover assumption.

**4. Check the converse.** Write the graph's parts as a joining triangle
`A`, another triangle `C`, and independent set `B` of size `n-6`. It has
`3 + 3 + 9 + 3(n-6) = 3n-3` edges. Its largest independent set is
`B` plus one vertex of `C`, of size `n-5`, so its cover number is five.
After deleting the at most three `A` vertices from a path, at most four
blocks remain. If any block meets `C`, all such blocks together use at
most three vertices; all other blocks are singletons in `B`. There are
therefore at most nine path vertices. Without `C`, there are at most
seven. This proves `P_10`-freeness and completes the corollary.

## Why the starting order is sharp

At order eleven, take `K_8` and attach three leaves to the same core
vertex. The graph has 31 edges and cover number seven, contradicting
the proposed upper bound `3*11-3 = 30`. Every path uses at most one leaf,
unless it is the three-vertex leaf–center–leaf path, so its longest path
has nine vertices.

Delete a core edge whose endpoints differ from the attachment center.
The resulting graph has 30 edges, independence number five, and cover
number six. It is still `P_10`-free and is not the equality graph above.
This also disproves equality uniqueness at order eleven. These examples
explain the sharp range of the corollary; they are not priority claims.

The following Python 3.10+ check exhausts subsets of these small graphs.
Endpoint dynamic programming checks path orders, and a separate subset
enumeration checks independence. The added-edge control must contain a
ten-vertex path. This finite check supplements the preceding arguments.

```python
from itertools import combinations

def check(n, edges):
    adjacency = [0] * n
    for a, b in edges:
        adjacency[a] |= 1 << b
        adjacency[b] |= 1 << a
    endpoints = [0] * (1 << n)
    for v in range(n):
        endpoints[1 << v] = 1 << v
    for mask in range(1, 1 << n):
        for v in range(n):
            if mask & (1 << v) and (
                endpoints[mask ^ (1 << v)] & adjacency[v]
            ):
                endpoints[mask] |= 1 << v
    longest = max(m.bit_count() for m in range(1 << n) if endpoints[m])
    alpha = max(
        m.bit_count() for m in range(1 << n)
        if all(not (adjacency[v] & m) for v in range(n) if m & (1 << v))
    )
    return len(edges), longest, n - alpha

edges = set(combinations(range(8), 2)) | {(0, v) for v in range(8, 11)}
assert check(11, edges) == (31, 9, 7)
edges.remove((1, 2))
assert check(11, edges) == (30, 9, 6)
assert check(11, edges | {(1, 8)})[1] >= 10
print("Both order-eleven counterexamples and the added-edge control passed.")
```

## Attribution and review scope

Yuan explicitly credits Theorem 3 to Jie Ma and Long-Tu Yuan,
[*A Stability Result of the Pósa Lemma*, SIAM Journal on Discrete
Mathematics 38(2) (2024), 1757–1783](https://doi.org/10.1137/20M1382143).
We inspected the accessible published statement in Yuan's paper and the
SIAM bibliographic record; the original SIAM full text was access restricted.
That article is distinct from Ma–Yuan's 2020 clique-stability preprint
previously checked in this project.

Two AI reviewers and the coordinating review checked the relevant
deductions; these are not human or formal verification. This short route
replaces the long equality argument as the recommended review path. The
author-edited manuscript and October 20 DOI packet remain historical
versions without this new attribution. The [contribution assessment](coprime-paths-contribution-assessment-2026-10-21.md)
records the resulting change in publication recommendation.
