# A parameterized equality deduction for the ten-vertex path

**Date:** October 21, 2026. **Status:** provisional written deduction,
AI-reviewed; human verification and novelty assessment pending.
Prepared with substantial OpenAI Codex assistance for Alexander Richard
Towell. This note is separate from his unchanged manuscript revision.

## Statement and attribution

Let `J` be a connected simple graph on `n >= 13` vertices with no path on
ten vertices. Write `tau(J)` for the minimum vertex-cover size. Then

\[
\tau(J)\geq5\quad\Longrightarrow\quad e(J)\leq3n-3.
\]

The candidate equality conclusion is

\[
e(J)=3n-3,\quad\tau(J)\geq5
\quad\Longleftrightarrow\quad
J\cong K_3\vee\bigl(K_3\cup\overline K_{n-6}\bigr).
\]

The connectedness and forbidden-path assumptions remain in force on both
sides. Equivalently, every connected `P_10`-free graph at this density has
a cover of size at most four or is the displayed graph.

The upper bound and sharpness construction follow from published stability
theory. Only uniqueness at equality is a possible contribution here; it
has not been established as novel. The proof below explains precisely how
Section 3 of the [existing manuscript](../e-jc/coprime-paths/coprime-paths.tex)
extends beyond order 17. It uses that section's lemmas and case analysis;
it is not an independent self-contained replacement for them.

## Upper bound from published stability

Put `Q = J + u`, adding a universal vertex. It is 2-connected and has no
cycle of length at least eleven. If `e(J) > 3n - 3`, then

\[
e(Q)>4n-3=h(n+1,11,4)>h(n+1,11,3)=3n+7.
\]

[FKVL, Theorem 2.3](https://users.renyi.hu/~furedi/PUBS3/furedi_238_kostochka_ruthluo_verstraete_Erdos-Gallai-stability_II.pdf),
specialized to odd cycle threshold eleven, places `Q` in
`H(n+1,11,5)` or `H(n+1,11,2)`. The latter has only `2n+20` edges,
fewer than `4n-3` for `n >= 13`. The former is `K_5 ∨ I_(n-4)`;
its five-vertex part must contain the universal vertex `u`. Removing `u`
therefore supplies a four-vertex cover of `J`, a contradiction.

The same construction notation in
[FKV](https://arxiv.org/pdf/1507.05338v2) identifies the equality example:
delete a universal vertex from `H(n+1,11,4)` to obtain
`H(n,9,3) = K_3 ∨ (K_3 ∪ I_(n-6))`. Neither this construction nor the
preceding density deduction should be presented as a new discovery.

## Extending the equality proof

Assume equality and no four-vertex cover. Use the manuscript's family
`F_0` consisting of `K_(5,6)` with at most two edges deleted. Its
Lemma `lem:F0` implies that `Q` contains no member of this family.

Initially every edge of `J` lies in at least two triangles. Otherwise
contract such an edge in `Q`: the result is still a universal augmentation
of a connected graph, is 2-connected, has circumference less than eleven,
and has at least `4n-6` edges on `n` vertices. For `n >= 13`,

\[
4n-6>\max\{4n-7,\ 3n+4,\ 2n+18\}.
\]

The manuscript's stability, dense-subgraph, and contraction-lifting inputs
then force `F_0` in `Q`, a contradiction. Thus minimum degree is at least
three. This replaces its initial numerical calculation at orders 18 and
17; the general inequalities are essential at the smaller starting orders.

The remaining deletion invariant already uses a variable order `m`:
connected, `P_10`-free, `e=3m-3`, minimum degree at least two, and no `F_0`
in the augmentation. For every `m >= 13`, the same inequalities exclude
low-triangle edges. At `m = 11,12`, the manuscript's leaf-count argument
excludes the remaining `H(m,11,2)` container. These small intermediate
orders must still be treated even though the initial order is at least 13.

The minimum-degree-four alternative is excluded exactly as in Section 3.2:
the longest-path bound and Ali–Staton force a sparse windmill or a complete
cross part giving `F_0`. Hence a degree-three vertex exists; its neighbors
form a triangle. Deleting it preserves the invariant. After **`n-10`
deletions**, rather than seven, the same ten-vertex, 27-edge core remains.

Section 3.3's closure analysis is independent of the initial order. It
gives precisely the three possibilities

\[
K_2\vee(K_5\cup I_3),\qquad
K_3\vee(K_3\cup I_4),\qquad
L_{10}\subseteq K_4\vee I_6.
\]

Section 3.4's reconstruction is inductive and likewise has no upper bound
on the number of additions. The first core cannot survive even one
addition. The second forces every added vertex to attach exactly to the
joining triangle, producing `K_3 ∨ (K_3 ∪ I_(n-6))`. In the third, the Hall
argument forces every addition to have its earlier neighborhood inside
the same four-vertex set, which then covers the final graph. This
contradicts the assumed cover number. Since `n >= 13`, there is at least
one addition, as required to reject the first core.

## Checking the equality example

Write its parts as triangles `A,C` and independent set `B`, of sizes
`3,3,n-6`, with all edges from `A` to `B ∪ C`. Its size is
`3 + 3 + 9 + 3(n-6) = 3n-3`. An independent set has maximum size
`|B|+1 = n-5`, so its vertex-cover number is five.

Deleting the at most three `A` vertices from any path leaves at most four
blocks. Each block lies entirely in `B` or entirely in `C`, and a `B`
block is a singleton. If `r >= 1` blocks meet `C`, together they use at
most three vertices, so the path has at most
`3 + 3 + (4-r) <= 9` vertices. With no `C` block, it has at most seven.
Thus the graph has no `P_10`.

This completes the parameterized deduction, conditional on the cited
inputs and the manuscript's detailed core and reconstruction arguments.
Its [contribution assessment](coprime-paths-contribution-assessment-2026-10-21.md)
explains why this does not yet establish journal readiness.
