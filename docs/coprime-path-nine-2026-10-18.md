# Structural constraints at the proposed nine-edge-path boundary

**October 18, 2026 — Alexander Richard Towell; investigation assisted by Codex.**

Let G_n join distinct integers in {1,…,n} when their gcd is 1, and let
P_cop(k) be the least n forcing a monochromatic simple **k-edge** path in
every two-coloring of its edges. A k-edge path has k+1 distinct vertices.

**Conditional theorem.** If a coloring of G_17 avoids a monochromatic
nine-edge path, then both color graphs are connected and span all 17 vertices,
their edge counts are 47 and 48, and deleting any four vertices leaves at
least five edges of each color.

This is a necessary condition, not a contradiction. **P_cop(9) = 17 remains
unresolved.** The [previous bounds](coprime-path-structure-2026-10-18.md)
still give 17 ≤ P_cop(9) ≤ 26. The lower bound comes from splitting the eight
odd vertices of G_16 into two four-vertex color covers. No new exact value,
infinite family, or priority claim is asserted here.

## Three finite lemmas with positive certificates

The [audit archive](audits/coprime-path-nine-2026-10-18/README.md) contains
explicit paths establishing these statements:

1. **Balanced cuts.** Every cut of G_17 with both sides of size at least five
   contains a nine-edge path using only crossing edges. There are 62,322
   smaller sides of sizes 5–8; complements cover sizes 9–12.
2. **Deletion resilience.** After any four vertices and any further set of
   at most four edges are removed, a nine-edge path remains. Certificates
   cover all 2,380 vertex deletions through 262 verified symmetry orbits,
   using 30,671 paths in total.
3. **Cut extensions.** Let A be a four-vertex set inducing at least five
   host edges, and B its complement. For every host edge e inside B, the
   graph consisting of all A–B edges plus e contains a nine-edge path.
   The archive supplies all 63,859 witnesses for the 1,253 qualifying sets A.

The independent [standard-library checker](../src/coprime_path_structure_certificates.py)
reconstructs every required case and checks path lengths, distinct vertices,
gcd adjacency, and cut/deletion restrictions. Saved completion flags and
counts alone cannot establish a lemma.

For deletion resilience, each recorded family has no edge transversal of
size at most four: no four edges meet all its paths. The checker exhaustively
branches on every edge of an uncovered path, memoizing repeated states.
Thus some recorded path survives every allowed edge deletion. It also
checks every transposition within each supplied vertex class against host
adjacency. These transpositions generate the within-class permutations;
deletion sets with the same class counts are therefore equivalent. Every
deletion signature must occur exactly once. This reuses **host** symmetries
without assuming that a coloring respects them.

## Published inputs and path-length conventions

For a connected s-vertex graph with no **10-vertex** path, the specialization
of [Balister, Győri, Lehel and Schelp, Theorem 1.3, page 2](https://www.memphis.edu/msci/people/pbalistr/nopk.pdf)
at s=13 gives

\[
e\le\max\{\tbinom82+5,\;\tbinom52+4\cdot8\}=42.
\]

That paper writes the forbidden path as P_(k+1), so its parameter here is k=9.

For s ≥ 14, [Füredi, Kostochka and Verstraëte, Theorem 1.6, page 3](https://arxiv.org/pdf/1507.05338)
with t=5 and k=10 gives e ≤ 3s−3 unless the graph is contained in H_(s,10,4).
Their k counts vertices. Their definition of H_(s,k,a) has parts A,B,C of
sizes a,s−k+a,k−2a, all A–B edges, and a clique on A∪C. Its edge count is
h(s,k,a) = binom(k−a,2)+a(s−k+a). Accordingly,

\[
h(s+1,11,4)-s=21+4(s-6)-s=3s-3.
\]

In the exceptional graph, deleting A leaves just the possible edge on the
two vertices of C. The exception is therefore **four vertices plus one
residual edge**; a four-vertex-cover condition alone would not exclude it.

## Deriving the conditional theorem

Consider either color. If all its components had size at most 12, some union
of components would have size 5–12: use such a component directly, or
accumulate components of size at most four until the union first reaches
five (and hence has size at most eight). All host edges across that cut have
the other color, contradicting the balanced-cut lemma. Each color therefore
has a component C of size s ≥ 13.

If s ≥ 14 and C lay in the stability exception, delete its four distinguished
vertices. At most one edge of C and binom(17−s,2) ≤ 3 edges in the remaining
components survive in this color. Deletion resilience then supplies a
nine-edge path of the other color. The exception is impossible.

Adding the maximum possible edges outside C gives the following bounds on
the **entire** color graph:

| Giant component size s | 13 | 14 | 15 | 16 | 17 |
| --- | --- | --- | --- | --- | --- |
| Edge bound | 48 | 42 | 43 | 45 | 48 |

For s=13 use 42+binom(4,2); otherwise use 3s−3+binom(17−s,2).
Since G_17 has 95 edges, the colors have 47 and 48 edges. Their giant
components consequently have sizes 13 or 17.

Suppose one giant has vertex set B of size 13, with complement A. At least
47−42=5 edges of its color lie inside A, so A qualifies for cut extensions.
All crossing edges have the other color. The extension lemma forces every
host edge inside B to have the giant's color: an edge of the other color
would complete a forbidden path. But deletion resilience, with zero edge
faults, gives a nine-edge path in G_17[B]. This excludes size 13, proving
that both colors are connected on all 17 vertices.

Finally, if deleting four vertices left at most four edges of one color,
delete those edges as well. Resilience supplies a nine-edge path of the
other color. Each color must therefore retain at least five edges after
every four-vertex deletion.

## Search outcome and remaining gap

The [search diagnostics](audits/coprime-path-nine-2026-10-18/searches.json)
record a separate bounded experiment. Closing deletion-path clauses under
2,304 checked host automorphisms produced 1,423,104 path clauses. This
subset was satisfiable, but independent subset-DP checking rejected its
candidate as an avoiding coloring. A 120-second lazy refinement added
975,168 valid path clauses over 284 rounds and ended **inconclusive**.
Neither outcome certifies an upper bound or a counterexample; partial SAT
formulas remain diagnostic scratch rather than archived proof evidence.

The next mathematical question is whether complementary connected
P_10-free subgraphs of G_17 with 47 and 48 edges can satisfy the deletion
condition. The stability inequality reaches its boundary at 48; it does
not classify that boundary. Further work should address this remaining
case explicitly. The positive finite lemmas above remain useful regardless
of the answer.
