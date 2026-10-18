# Structural bounds for coprime path Ramsey numbers

**October 18, 2026 — Alexander Richard Towell; investigation assisted by Codex.**

Let G_n have vertices {1,…,n}, joining distinct integers exactly when their
gcd is 1. Let P_cop(k) be the least n such that every two-coloring of its
**edges** contains a monochromatic simple path of **k edges**, hence k+1
distinct vertices. This note proves

\[
2\le\liminf_{k\to\infty}\frac{P_{\rm cop}(k)}k
\le\limsup_{k\to\infty}\frac{P_{\rm cop}(k)}k
\le\frac{197\pi^2}{595}=3.267751373\ldots.
\]

In particular, **P_cop(k) = Θ(k)**. The argument combines standard extremal
and arithmetic methods; priority is unestablished. It neither determines an
exact infinite family nor replaces the [independently checked certificate
for P_cop(7) = P_cop(8) = 13](audits/coprime-paths-2026-10-18/README.md).

## Lower bound from two vertex covers

The 2m odd vertices form a vertex cover of G_(4m): two even vertices cannot
be coprime. Split the odd vertices into sets A and B of size m. Give color 0
to every edge meeting A and color 1 to the remaining edges. A covers the
first color, and B covers the second. A simple path in a graph with a
vertex cover of size m has at most m cover vertices and m+1 other vertices,
so it has at most 2m edges. Therefore

\[
P_{\rm cop}(2m+1)\ge4m+1.
\]

Monotonicity in the target length gives the finite bound
P_cop(k) ≥ 4⌊(k−1)/2⌋+1 for k ≥ 3, and the asymptotic lower constant 2.
This construction was already recorded in the October 18 certificate audit.

## A finite upper bound from edge density

The Erdős–Gallai path theorem bounds a graph with v vertices and no k-edge
path by (k−1)v/2 edges. Apply it separately to the two color classes of any
subgraph H of G_n. Consequently,

\[
 e(H)>(k-1)v(H)\quad\Longrightarrow\quad P_{\rm cop}(k)\le n. \tag{1}
\]

The inequality is **strict**. This is a sufficient condition, not a
characterization. The graph-theoretic input is [Erdős and Gallai (1959),
Theorem 2.6, printed page 347](https://web.vu.lt/mif/s.jukna/tropical/Erdos-Gallai-1959.pdf).

Adding vertex j to G_(j−1) adds φ(j) edges, so
E_n = e(G_n) = Σ_(j=2)^n φ(j). The first n with E_n > (k−1)n is an exact,
integer-computable upper bound. To obtain its growth, count ordered coprime
pairs by Möbius inversion:

\[
2E_n+1=\sum_{r=1}^n\mu(r)\lfloor n/r\rfloor^2
=\frac{6}{\pi^2}n^2+O(n\log n).
\]

The added 1 is the diagonal pair (1,1). Replacing floors costs O(n log n);
the tail of Σ μ(r)/r² costs O(n), using the absolutely convergent Euler
product 1/ζ(2) = 6/π². Thus E_n = 3n²/π²+O(n log n). For every ε > 0,
choosing n = ⌈(π²/3+ε)k⌉ satisfies (1) for sufficiently large k. This already
proves limsup P_cop(k)/k ≤ π²/3 ≈ 3.289868 and linear growth.

## Improving the upper constant by deleting vertices

Set D_n = {a ≤ n : 30 divides a, or 42 divides a, or 70 divides a}, and
H_n = G_n − D_n. All deleted vertices are even, so D_n is independent.
The least common multiple of any two of 30, 42, 70 is 210. Inclusion-exclusion
therefore gives

\[
 |D_n|=\lfloor n/30\rfloor+\lfloor n/42\rfloor+\lfloor n/70\rfloor
       -2\lfloor n/210\rfloor
       =\frac{13}{210}n+O(1). \tag{2}
\]

For fixed squarefree d ≥ 2 define
C_d(n) = #{(a,b) ∈ [n]² : d divides a and gcd(a,b)=1}. Möbius inversion gives

\[
 C_d(n)=\sum_{r=1}^n\mu(r)
       \left\lfloor\frac{n}{\operatorname{lcm}(d,r)}\right\rfloor
       \left\lfloor\frac nr\right\rfloor
 =\frac{6n^2}{\pi^2\prod_{p\mid d}(p+1)}+O_d(n\log n). \tag{3}
\]

For completeness, removing the floors and extending the sum to infinity
has the same error estimates as above, since lcm(d,r) ≥ r. Its coefficient is

\[
 \sum_{r\ge1}\frac{\mu(r)}{\operatorname{lcm}(d,r)r}
 =\frac1d\prod_{p\mid d}(1-1/p)\prod_{p\nmid d}(1-1/p^2)
 =\frac{6}{\pi^2\prod_{p\mid d}(p+1)}.
\]

Because D_n is independent, the number of edges lost is counted exactly
once by ordered pairs with the first endpoint in D_n. Using (3), it equals

\[
\begin{aligned}
 C_{30}+C_{42}+C_{70}-2C_{210}
 &=\frac6{\pi^2}\left(\frac1{72}+\frac1{96}+\frac1{144}
                    -\frac2{576}\right)n^2+O(n\log n)\\
 &=\frac1{6\pi^2}n^2+O(n\log n).
\end{aligned}
\]

Hence v(H_n) = (197/210)n+O(1), e(H_n) = 17n²/(6π²)+O(n log n), and

\[
 \frac{e(H_n)}{v(H_n)}=\frac{595}{197\pi^2}n+O(\log n).
\]

For every ε > 0, take n = ⌈(197π²/595+ε)k⌉ and apply (1) for sufficiently
large k. This proves the stated improved limsup bound. The constant is not
asserted optimal, and the asymptotic expression alone is not a bound for
an arbitrary finite k.

## Reproduce finite bounds

The [standard-library calculator](../src/coprime_path_bounds.py) counts
retained vertices and edges exactly, then applies (1). It uses a
smallest-prime-factor sieve and squarefree-divisor inclusion-exclusion:
when retaining a vertex a, its number of earlier retained neighbors is
Σ_(d|a) μ(d) M_d, where M_d counts earlier retained multiples of d. Counts are
updated after adding its edges, so loops are excluded. No SAT solver or
floating-point arithmetic is used.

```sh
python3 -I -S -O src/coprime_path_bounds.py \
  3 4 5 6 7 8 9 10 20 50 100 1000 --max-n 3400
python -m pytest -q tests/test_coprime_path_bounds.py \
  --cov=coprime_path_bounds --cov-report=term-missing
```

The [saved JSON](audits/coprime-path-structure-2026-10-18/finite-bounds.json)
includes the retained vertex and edge counts for each sufficient upper bound.
Both columns are upper bounds; take the smaller one. The lower column uses
only the cover argument, even where stronger exact values are known.

| Target k (edges) | Cover lower bound | Whole-graph upper | Deleted-host upper |
| --- | --- | --- | --- |
| 7 | 13 | 19 | 19 |
| 8 | 13 | 23 | 23 |
| 9 | 17 | 26 | 26 |
| 10 | 17 | 29 | 29 |
| 20 | 37 | 61 | 61 |
| 50 | 97 | 161 | 161 |
| 100 | 197 | 325 | 323 |
| 1000 | 1997 | 3287 | 3265 |

`--exclude-multiples` accepts other positive integer divisors for finite
experiments. Overlaps are handled automatically. The proof of the displayed
asymptotic constant concerns specifically 30, 42, 70. JSON `null` means no
sufficient bound was found up to `--max-n`; it says nothing about the actual
threshold. Density can decrease as n grows, so the calculator scans every n
and retains the first successful certificate.

The 43 added tests compare counts with direct gcd enumeration, check
non-strict equality is rejected (k=4, n=9), exercise empty/overlapping
deletions and invalid inputs, and independently validate small cover
colorings using the existing subset-DP checker. CLI integration tests run
under isolated optimized Python. Measured statement coverage of the new
calculation logic is 100%; repository configuration excludes `main` bodies.
These finite checks support the implementation, not the infinite proof by
themselves. Existing path tests remain separate from this calculator.

## What this does not explain at n = 13

For every graph on at most 13 vertices, e/v ≤ (v−1)/2 ≤ 6. Therefore (1)
cannot certify a seven- or eight-edge path, even after selecting an induced
subgraph of G_13. That sufficient condition is intrinsically too weak for
the exact boundary.

A second obstruction rules out several coarse structural explanations.
G_13 has 13 vertices, 57 edges, minimum degree 5, and four universal vertices.
The graph J = K_6 ∨ I_7 (join a six-vertex clique to seven independent
vertices) also has 13 vertices and 57 edges, but minimum degree 6 and six
universal vertices. Split its clique into two triples and apply the same
cover coloring as above. Each color has a three-vertex cover, so neither
contains a seven-edge path. Thus order and size, even together with lower
bounds of 5 on minimum degree and 4 on universal-vertex count, do not suffice.

The detailed host matters: G_13 is K_7 ∨ I_6 with the six edges
{3,9}, {3,6}, {3,12}, {9,6}, {9,12}, {5,10} removed. The odd labels form the
seven-vertex side. Its universal clique is {1,7,11,13}. An arbitrary edge
coloring can break every symmetry of this host; assigning identical colors
to edges between twin classes would need a proof, not an assumption.

## The next family and limits of the current construction

The values at k=3,5,7 suggest testing P_cop(2m+1) = 4m+1. The cover argument
proves its lower side for every m. It is optimal within that particular
avoidance mechanism: α(G_n) = ⌊n/2⌋ for n ≥ 2. Evens attain the bound;
for even n, disjoint consecutive pairs bound an independent set by n/2.
For odd n, a set containing the universal vertex 1 has size at most 1;
otherwise use pairs (2,3), (4,5), …, (n−1,n). Each pair is an edge.
Thus the minimum vertex-cover size is ⌈n/2⌉. At n=4m+1, two color covers
of size at most m would cover G_n with at most 2m vertices, a contradiction.

This does **not** prove the proposed equality: graphs without long paths
need not have small vertex covers. A counterexample must use another
avoidance mechanism. [Two bounded searches](audits/coprime-path-structure-2026-10-18/searches.json)
at (n,k)=(17,9) and (17,10) each exhausted a 120-second budget and were
inconclusive. They establish neither upper bounds nor counterexamples. Their
partial formulas are diagnostic scratch, not archived proof certificates.

## Literature and publication scope

[Du, Xi, Deng and Ma, v2](https://arxiv.org/html/2605.26815v2), Table 12,
already attributes the small path values to this repository. Proposition
4.6 provides a prime-clique upper transfer for general edge targets;
Open Problem 9.2 discusses non-complete targets. The checked sections and
full-text search did not locate the linear argument given here. This is a
bounded observation, not a claim of priority.

[Banerjee's primary preprint](https://arxiv.org/html/2506.10583v1) concerns
structural and spectral properties of the same host. Its accessible version
did not supply an edge-color path Ramsey bound; the final journal text
was not accessible for comparison. [Erdős and Sárközy (1997)](https://www.combinatorics.org/ojs/index.php/eljc/article/download/v4i2r8/pdf)
study long cycles in uncolored induced coprime graphs, a different condition.
The bounded search also checked adjacent tripartite-subgraph and bipartite
path-Ramsey literature at abstract level. It does not exclude unindexed or
unexamined prior work.

Treat Θ(k) as a standard-method corollary and the deletion constant as a
proved refinement whose priority remains unestablished. A concise exact
upper proof at 13, an exact infinite family, or substantially sharper
asymptotics would be a stronger next contribution. This note is an ordinary
repository update, not a journal submission or a new archival release.
