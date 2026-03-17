# Erdos Problems: Relationship Discovery Report

**Generated**: 2026-02-12
**Database**: 1135 problems from erdosproblems.com

---

## 1. Hidden Connections via OEIS Sequences

Problem pairs sharing OEIS sequences but having **no shared tags** represent
non-obvious mathematical bridges. The OEIS sequence links them through a
common integer sequence, yet their mathematical domains appear disjoint.

**Found 14 hidden bridges** (0 with zero tag overlap, 14 with low overlap).

| Problem A | Tags A | Problem B | Tags B | Shared OEIS | Shared Tags | Jaccard | Investigation |
|-----------|--------|-----------|--------|-------------|-------------|---------|---------------|
| #683 (open) | binomial coefficients, number theory, primes | #928 (open) | number theory | A006530 | number theory | 0.333 | Prime-counting and binomial structures share extremal sequence |
| #368 (open) | number theory | #683 (open) | binomial coefficients, number theory, primes | A074399 | number theory | 0.333 | Prime-counting and binomial structures share extremal sequence |
| #155 (open) | additive combinatorics, sidon sets | #530 (open) | number theory, sidon sets | A143824 | sidon sets | 0.333 | Sidon set structure bridges additive and number-theoretic properties |
| #155 (open) | additive combinatorics, sidon sets | #861 (solved) | number theory, sidon sets | A143824 | sidon sets | 0.333 | Sidon set structure bridges additive and number-theoretic properties |
| #243 (open) | number theory | #315 (proved) | number theory, unit fractions | A000058 | number theory | 0.5 | Egyptian fraction structure parallels via shared counting sequence |
| #200 (open) | arithmetic progressions, primes | #219 (proved) | additive combinatorics, arithmetic progressions, number theory | A005115 | arithmetic progressions, primes | 0.5 | Distinct topics (additive combinatorics, number theory) linked by shared sequence A005115 |
| #138 (open) | additive combinatorics | #169 (open) | additive combinatorics, arithmetic progressions | A005346 | additive combinatorics | 0.5 | Distinct topics (arithmetic progressions) linked by shared sequence A005346 |
| #470 (open) | divisors, number theory | #825 (open) | number theory | A006037 | number theory | 0.5 | Divisor structure creates counting parallel with different area |
| #85 (falsifiable) | graph theory | #552 (open) | graph theory, ramsey theory | A006672 | graph theory | 0.5 | Distinct topics (ramsey theory) linked by shared sequence A006672 |
| #121 (disproved) | number theory, squares | #969 (open) | number theory | A013928 | number theory | 0.5 | Perfect square constraints create unexpected counting parallels |
| #941 (proved) | number theory | #1107 (open) | number theory, powerful | A056828 | number theory | 0.5 | Distinct topics (powerful) linked by shared sequence A056828 |
| #251 (open) | irrationality, number theory | #980 (proved) | number theory | A098990 | number theory | 0.5 | Distinct topics (irrationality) linked by shared sequence A098990 |
| #121 (disproved) | number theory, squares | #786 (open) | number theory | A143301 | number theory | 0.5 | Perfect square constraints create unexpected counting parallels |
| #398 (falsifiable) | factorials, number theory | #936 (open) | number theory | A146968 | number theory | 0.5 | Distinct topics (factorials) linked by shared sequence A146968 |

### Key Insight

These bridges suggest that the OEIS sequences encode deeper structural
parallels between problems with little mathematical domain overlap.
Each bridge is a candidate for a new theorem connecting the two areas.

---

## 2. Tag Gap Analysis

### Major Tag Pair Intersection Counts

| Tag Pair | Intersection Size | Category 1 Size | Category 2 Size | Bridging Sub-topics |
|----------|-------------------|-----------------|-----------------|---------------------|
| graph theory x ramsey theory | 68 | 270 | 102 | set theory, hypergraphs |
| number theory x additive combinatorics | 37 | 542 | 90 | sidon sets, ramsey theory, arithmetic progressions |
| number theory x ramsey theory | 14 | 542 | 102 | additive combinatorics, unit fractions |
| ramsey theory x additive combinatorics | 7 | 102 | 90 | number theory |
| geometry x ramsey theory | 6 | 108 | 102 | (none) |
| ramsey theory x combinatorics | 3 | 102 | 44 | discrepancy |
| graph theory x additive combinatorics | 2 | 270 | 90 | (none) |
| number theory x graph theory | 1 | 542 | 270 | (none) |
| number theory x geometry | 1 | 542 | 108 | (none) |
| number theory x analysis | 1 | 542 | 72 | (none) |
| graph theory x geometry | 1 | 270 | 108 | chromatic number |
| graph theory x combinatorics | 1 | 270 | 44 | (none) |
| geometry x combinatorics | 1 | 108 | 44 | (none) |
| additive combinatorics x analysis | 1 | 90 | 72 | (none) |
| additive combinatorics x combinatorics | 1 | 90 | 44 | (none) |
| analysis x combinatorics | 1 | 72 | 44 | (none) |
| number theory x combinatorics | 0 | 542 | 44 | (none) |
| graph theory x analysis | 0 | 270 | 72 | (none) |
| geometry x additive combinatorics | 0 | 108 | 90 | (none) |
| geometry x analysis | 0 | 108 | 72 | (none) |
| ramsey theory x analysis | 0 | 102 | 72 | (none) |

### Rare Intersections (5 or fewer problems)

These sparse intersections are where novel problems are most likely to live.

#### number theory x combinatorics (0 problems)
- **No existing problems** -- entirely unexplored territory
- Missing bridge sub-topics: additive combinatorics, analysis, arithmetic progressions, geometry, graph theory

#### graph theory x analysis (0 problems)
- **No existing problems** -- entirely unexplored territory
- Missing bridge sub-topics: additive combinatorics, combinatorics, discrepancy, number theory, set theory

#### geometry x additive combinatorics (0 problems)
- **No existing problems** -- entirely unexplored territory
- Missing bridge sub-topics: combinatorics, graph theory, number theory, ramsey theory, sidon sets

#### geometry x analysis (0 problems)
- **No existing problems** -- entirely unexplored territory
- Missing bridge sub-topics: combinatorics, number theory, probability, set theory

#### ramsey theory x analysis (0 problems)
- **No existing problems** -- entirely unexplored territory
- Missing bridge sub-topics: additive combinatorics, combinatorics, discrepancy, number theory, set theory

#### number theory x graph theory (1 problems)
- Existing problems: #883
- Missing bridge sub-topics: additive combinatorics, geometry, ramsey theory

#### number theory x geometry (1 problems)
- Existing problems: #769
- Missing bridge sub-topics: graph theory, probability, ramsey theory, sidon sets

#### number theory x analysis (1 problems)
- Existing problems: #967
- Missing bridge sub-topics: additive combinatorics, diophantine approximation, iterated functions, primes, probability

#### graph theory x geometry (1 problems)
- Existing problems: #704
- Missing bridge sub-topics: combinatorics, number theory, ramsey theory, set theory

#### graph theory x combinatorics (1 problems)
- Existing problems: #777
- Missing bridge sub-topics: additive combinatorics, chromatic number, discrepancy, geometry, hypergraphs

#### geometry x combinatorics (1 problems)
- Existing problems: #733
- Missing bridge sub-topics: chromatic number, graph theory, ramsey theory, set theory

#### additive combinatorics x analysis (1 problems)
- Existing problems: #494
- Missing bridge sub-topics: combinatorics, discrepancy, number theory, primes

#### additive combinatorics x combinatorics (1 problems)
- Existing problems: #171
- Missing bridge sub-topics: analysis, arithmetic progressions, discrepancy, graph theory, ramsey theory

#### analysis x combinatorics (1 problems)
- Existing problems: #498
- Missing bridge sub-topics: additive combinatorics, discrepancy, set theory

#### graph theory x additive combinatorics (2 problems)
- Existing problems: #808, #895
- Missing bridge sub-topics: combinatorics, discrepancy, number theory, ramsey theory

#### ramsey theory x combinatorics (3 problems)
- Existing problems: #161, #162, #191
- Missing bridge sub-topics: additive combinatorics, geometry, graph theory, hypergraphs, set theory

### Missing Bridge Analysis

For each tag pair, 'missing bridges' are sub-topics that appear independently
in both areas but never at their intersection. These represent unexplored
connections.

- **additive combinatorics x analysis**: Missing bridges = combinatorics, discrepancy, number theory, primes
- **additive combinatorics x combinatorics**: Missing bridges = analysis, arithmetic progressions, discrepancy, graph theory, ramsey theory
- **analysis x combinatorics**: Missing bridges = additive combinatorics, discrepancy, set theory
- **geometry x additive combinatorics**: Missing bridges = combinatorics, graph theory, number theory, ramsey theory, sidon sets
- **geometry x analysis**: Missing bridges = combinatorics, number theory, probability, set theory
- **geometry x combinatorics**: Missing bridges = chromatic number, graph theory, ramsey theory, set theory
- **geometry x ramsey theory**: Missing bridges = combinatorics, graph theory, number theory, set theory
- **graph theory x additive combinatorics**: Missing bridges = combinatorics, discrepancy, number theory, ramsey theory
- **graph theory x analysis**: Missing bridges = additive combinatorics, combinatorics, discrepancy, number theory, set theory
- **graph theory x combinatorics**: Missing bridges = additive combinatorics, chromatic number, discrepancy, geometry, hypergraphs, ramsey theory, set theory
- **graph theory x geometry**: Missing bridges = combinatorics, number theory, ramsey theory, set theory
- **graph theory x ramsey theory**: Missing bridges = additive combinatorics, combinatorics, discrepancy, geometry, number theory
- **number theory x additive combinatorics**: Missing bridges = analysis, graph theory
- **number theory x analysis**: Missing bridges = additive combinatorics, diophantine approximation, iterated functions, primes, probability
- **number theory x combinatorics**: Missing bridges = additive combinatorics, analysis, arithmetic progressions, geometry, graph theory, intersecting family, ramsey theory
- **number theory x geometry**: Missing bridges = graph theory, probability, ramsey theory, sidon sets
- **number theory x graph theory**: Missing bridges = additive combinatorics, geometry, ramsey theory
- **number theory x ramsey theory**: Missing bridges = geometry, graph theory
- **ramsey theory x additive combinatorics**: Missing bridges = combinatorics, discrepancy, graph theory
- **ramsey theory x analysis**: Missing bridges = additive combinatorics, combinatorics, discrepancy, number theory, set theory
- **ramsey theory x combinatorics**: Missing bridges = additive combinatorics, geometry, graph theory, hypergraphs, set theory

---

## 3. Technique Transfer Map

Solved problems whose techniques could transfer to open problems in
different mathematical areas.

### Technique Transfer Counts

| Technique | Transfer Candidates |
|-----------|---------------------|
| ramsey theory | 1439 |
| additive combinatorics | 1060 |
| chromatic number | 163 |
| analysis | 99 |
| hypergraphs | 96 |
| sidon sets | 80 |
| arithmetic progressions | 36 |
| covering systems | 32 |
| discrepancy | 22 |
| probability | 10 |
| intersecting family | 3 |

### Top Area-to-Area Transfers

| From Areas | To Areas | Count | Example (Solved -> Open) |
|-----------|----------|-------|--------------------------|
| number theory |  | 624 | #219 -> #141 |
| number theory | graph theory | 473 | #45 -> #80 |
|  | number theory | 427 | #198 -> #14 |
| graph theory |  | 141 | #76 -> #172 |
| set theory | graph theory | 137 | #1128 -> #562 |
| graph theory | graph theory, set theory | 137 | #832 -> #593 |
| graph theory | geometry | 132 | #57 -> #1091 |
| graph theory | number theory | 106 | #76 -> #483 |
| combinatorics | graph theory | 100 | #780 -> #836 |
| geometry | graph theory | 86 | #189 -> #80 |
| combinatorics |  | 84 | #171 -> #141 |
| graph theory | set theory | 66 | #76 -> #598 |
| graph theory | combinatorics | 60 | #76 -> #162 |
|  | graph theory | 54 | #965 -> #80 |
| number theory | geometry | 47 | #45 -> #173 |

### High-Value Technique Transfers (Open Problems with Prizes)

| Solved | Open | Prize | Shared Techniques | From Area | To Area |
|--------|------|-------|-------------------|-----------|---------|
| #198 (disproved (Lean)) | #43 | $100 | additive combinatorics, sidon sets |  | number theory |
| #707 (disproved (Lean)) | #43 | $100 | additive combinatorics, sidon sets |  | number theory |
| #772 (proved) | #241 | $100 | additive combinatorics, sidon sets | number theory |  |
| #198 (disproved (Lean)) | #39 | $500 | additive combinatorics, sidon sets |  | number theory |
| #198 (disproved (Lean)) | #41 | $500 | additive combinatorics, sidon sets |  | number theory |
| #707 (disproved (Lean)) | #39 | $500 | additive combinatorics, sidon sets |  | number theory |
| #707 (disproved (Lean)) | #41 | $500 | additive combinatorics, sidon sets |  | number theory |
| #780 (proved) | #593 | $500 | chromatic number, hypergraphs | combinatorics | graph theory, set theory |
| #832 (disproved) | #593 | $500 | chromatic number, hypergraphs | graph theory | graph theory, set theory |
| #833 (proved) | #593 | $500 | chromatic number, hypergraphs | graph theory | graph theory, set theory |
| #1128 (disproved) | #564 | $500 | hypergraphs, ramsey theory | set theory | graph theory |
| #198 (disproved (Lean)) | #30 | $1000 | additive combinatorics, sidon sets |  | number theory |
| #707 (disproved (Lean)) | #30 | $1000 | additive combinatorics, sidon sets |  | number theory |
| #139 (proved) | #3 | $5000 | additive combinatorics, arithmetic progressions |  | number theory |
| #140 (proved) | #3 | $5000 | additive combinatorics, arithmetic progressions |  | number theory |
| #179 (proved) | #3 | $5000 | additive combinatorics, arithmetic progressions |  | number theory |
| #198 (disproved (Lean)) | #3 | $5000 | additive combinatorics, arithmetic progressions |  | number theory |
| #984 (proved) | #3 | $5000 | additive combinatorics, arithmetic progressions |  | number theory |
| #219 (proved) | #142 | $10000 | additive combinatorics, arithmetic progressions | number theory |  |
| #37 (disproved) | #241 | $100 | additive combinatorics | number theory |  |

---

## 4. Structural Isomorphism (Same Tags, Different Status)

Problem pairs with **identical tag sets** where one is solved and one is open.
The solution technique may directly adapt.

**Found 58 tag patterns with both solved and open problems.**

### Most Specific Isomorphisms (3+ tags)

| Tag Pattern | # Tags | Solved Problems | Open Problems |
|-------------|--------|-----------------|---------------|
| additive combinatorics, number theory, ramsey theory | 3 | #484, #645, #721, #966 | #483 |
| chromatic number, graph theory, hypergraphs | 3 | #832, #833 | #836 |
| graph theory, hypergraphs, turan number | 3 | #794 | #500, #712 |
| chromatic number, cycles, graph theory | 3 | #57, #58, #63, #921 | #108, #626, #74 |
| additive basis, number theory, primes | 3 | #16 | #10, #358, #9 |
| analysis, polynomials, probability | 3 | #523, #525 | #521, #522, #524 |
| convex, distances, geometry | 3 | #93, #94, #95 | #660, #956, #96, #97, #982 |
| additive combinatorics, number theory, sidon sets | 3 | #772 | #14, #30, #340, #39, #41 |

### All Isomorphisms with Prizes

| Tags | Solved | Open | Prize | Solved OEIS | Open OEIS |
|------|--------|------|-------|-------------|-----------|
| additive combinatorics, arithmetic progressions | #139 | #142 | $10000 | A003002, A003003, A003004, A003005 | A003002, A003003, A003004, A003005 |
| additive combinatorics, arithmetic progressions | #140 | #142 | $10000 | A003002 | A003002, A003003, A003004, A003005 |
| additive combinatorics, arithmetic progressions | #179 | #142 | $10000 | - | A003002, A003003, A003004, A003005 |
| additive combinatorics, arithmetic progressions | #984 | #142 | $10000 | - | A003002, A003003, A003004, A003005 |
| additive combinatorics, number theory, sidon sets | #772 | #30 | $1000 | - | A143824, A227590, A003022 |
| chromatic number, graph theory | #630 | #625 | $1000 | - | - |
| chromatic number, graph theory | #631 | #625 | $1000 | - | - |
| chromatic number, graph theory | #632 | #625 | $1000 | - | - |
| chromatic number, graph theory | #737 | #625 | $1000 | - | - |
| chromatic number, graph theory | #744 | #625 | $1000 | - | - |
| chromatic number, graph theory | #751 | #625 | $1000 | - | - |
| chromatic number, graph theory | #753 | #625 | $1000 | - | - |
| chromatic number, graph theory | #758 | #625 | $1000 | - | - |
| chromatic number, graph theory | #759 | #625 | $1000 | - | - |
| chromatic number, graph theory | #760 | #625 | $1000 | - | - |
| chromatic number, graph theory | #762 | #625 | $1000 | - | - |
| chromatic number, graph theory | #797 | #625 | $1000 | - | - |
| chromatic number, graph theory | #799 | #625 | $1000 | - | - |
| chromatic number, graph theory | #842 | #625 | $1000 | - | - |
| chromatic number, graph theory | #922 | #625 | $1000 | - | - |


---

## 5. Novel Problem Generation

Based on gap analysis and technique transfer, here are 5 new problems
at unexplored intersections.

### NRD-1: Sidon Sets in Point Configurations

**Intersection**: geometry x additive combinatorics (existing: 0 problems)

**Question**: Let P be a set of n points in the plane. Define D(P) = {|p-q| : p,q in P, p != q} as the multiset of pairwise distances. Call P a 'distance-Sidon set' if all distances in D(P) are distinct (i.e., D(P) is a Sidon set under the distance metric). What is the maximum n such that a distance-Sidon set of n points exists in [0,N]^2? How does this relate to the Erdos distinct distances problem?

**Why novel**: The gap analysis shows only few problems at the geometry x additive combinatorics intersection. Distance-Sidon sets combine Sidon structure (additive combinatorics) with point configurations (geometry). The Guth-Katz distinct distances result gives an upper bound on distance repetitions, but the Sidon constraint is strictly stronger.

**Suggested approach**: Use polynomial partitioning (Guth-Katz) combined with the B_2 set upper bound sqrt(N) for Sidon sets. The geometric constraint adds dimension, potentially allowing larger Sidon-like sets than in the integer case.

**Related problems**: #30 (Sidon), #89 (distinct distances), #91 (distances)

---

### NRD-2: Spectral Gap of Coprime Graphs and Analytic Number Theory

**Intersection**: analysis x graph theory (existing: 0 problems)

**Question**: Let G(n) be the coprime graph on {1,...,n}. Let lambda_1 >= lambda_2 >= ... >= lambda_n be the eigenvalues of its adjacency matrix. Define the spectral gap delta(n) = lambda_1 - lambda_2. Conjecture: delta(n) ~ c * n / log(n) for some constant c related to 6/pi^2. Does the spectral gap of coprime graphs encode prime distribution information?

**Why novel**: The gap analysis shows only few problems bridging analysis and graph theory. Spectral graph theory on coprime graphs connects analytic number theory (eigenvalue distributions, random matrix theory) with extremal graph theory (expansion, mixing). No Erdos problem studies spectral properties of arithmetic graphs.

**Suggested approach**: Compute spectral gaps for small coprime graphs computationally. Compare with 6/pi^2 * n (edge density times n). Use the Ramanujan sum representation of coprimality to express the adjacency matrix in terms of Dirichlet characters.

**Related problems**: #883 (coprime graphs), #75 (chromatic), #4 (prime gaps)

---

### NRD-3: Discrepancy Bounds for Ramsey Colorings

**Intersection**: ramsey theory x analysis (existing: 0 problems)

**Question**: For a 2-coloring chi: [N] -> {-1,+1}, define the discrepancy along arithmetic progressions D(chi) = max_{a,d,k} |sum_{i=0}^{k-1} chi(a+id)|. The Ramsey coloring problem asks for monochromatic APs. What is the minimum D(chi) over colorings that avoid monochromatic k-APs? Specifically, for k=3 and N < W(3,2)=9, what is the minimum 3-AP discrepancy of a coloring of [8] with no monochromatic 3-AP?

**Why novel**: The gap analysis shows only few problems at analysis x ramsey theory. Discrepancy theory (analysis) and Ramsey theory study complementary aspects of colorings. This problem asks: when Ramsey-type monochromatic structure is forbidden, what analytic imbalance must remain? This connects to the Roth/Kelley-Meka Fourier approach where discrepancy (large Fourier coefficients) drives density increment.

**Suggested approach**: Compute minimum discrepancy for small cases. Connect to Fourier analysis: a coloring with small discrepancy on all APs has small Fourier coefficients, which by Kelley-Meka implies density conditions. Seek a phase transition.

**Related problems**: #3 (AP conjecture), #142 (AP density), #483 (Schur)

---

### NRD-4: Turan Numbers for Geometric Hypergraphs

**Intersection**: combinatorics x geometry (existing: 0 problems)

**Question**: Given n points in general position in the plane, define a '3-uniform distance hypergraph' H where {p,q,r} is an edge if the triangle pqr has perimeter exactly some target value t. What is the maximum number of edges in H? More precisely, define ex_geo(n, K_4^3) as the maximum number of hyperedges in a geometric 3-uniform hypergraph on n points in general position that contains no complete 3-uniform 4-graph (every 4-point subset has a non-edge triple).

**Why novel**: Turan numbers are well-studied in abstract combinatorics (21 problems with 'turan number' tag). Geometric hypergraphs add distance constraints from geometry. This intersection (0 problems) is underexplored. The problem imports Turan theory into geometric settings where algebraic geometry tools apply.

**Suggested approach**: Use the Kővári-Sós-Turán bound combined with incidence geometry. The algebraic degree of the perimeter constraint limits hyperedge density. Compare with abstract Turan numbers for 3-uniform hypergraphs.

**Related problems**: #96 (convex position), #89 (distances), #564 (hypergraph Ramsey)

---

### NRD-5: Covering Systems as Intersecting Families

**Intersection**: number theory x combinatorics (existing: 0 problems)

**Question**: A covering system is a finite collection of arithmetic progressions a_i (mod n_i) that covers all integers. View each progression as a subset of Z/LCM(n_i)Z. When is a covering system also an intersecting family (every two progressions share an element in Z/LCM(n_i)Z)? Define I(N) = max number of residue classes a_i (mod n_i) with n_i <= N that form both a covering system and an intersecting family. What is the growth rate of I(N)?

**Why novel**: Covering systems (19 problems) and intersecting families (5 problems) have never been combined. The former is number theory, the latter extremal combinatorics (Erdos-Ko-Rado). This asks when the number-theoretic covering property coexists with the combinatorial intersection property. The gap analysis shows few problems at this intersection.

**Suggested approach**: For small moduli, enumerate all covering systems and test intersection. Use the Erdos-Ko-Rado sunflower lemma to bound I(N). The Chinese Remainder Theorem provides structure for when progressions intersect.

**Related problems**: #2 (covering systems), #7 (covering systems), #279 (covering), #593 (intersecting family)

---

## 6. Problem 'Genome' and Nearest-Neighbor Analysis

Each problem is encoded as a 44-dimensional feature vector:
- Binary tag presence (one-hot for all 40 tags)
- OEIS sequence count
- Log-scaled prize value
- Status encoding (open/solved binary)

Cosine distance is used to find nearest neighbors. **Surprising neighbors**
are pairs that are close in genome space but have low tag overlap (Jaccard < 0.5),
indicating shared structural properties (OEIS, prize, status) across different areas.

### Top 30 Surprising Near-Neighbors

| Problem A | Problem B | Cosine Dist | Shared Tags | Unique to A | Unique to B | Surprise Score |
|-----------|-----------|-------------|-------------|-------------|-------------|----------------|
| #168 (open) | #479 (open) | 0.0429 | (none) | additive combinatorics | number theory | 0.9571 |
| #168 (open) | #849 (open) | 0.0521 | (none) | additive combinatorics | binomial coefficients, number theory | 0.9479 |
| #201 (open) | #479 (open) | 0.0684 | (none) | additive combinatorics, arithmetic progressions | number theory | 0.9316 |
| #82 (open) | #479 (open) | 0.0712 | (none) | graph theory | number theory | 0.9288 |
| #669 (open) | #479 (open) | 0.0712 | (none) | geometry | number theory | 0.9288 |
| #82 (open) | #168 (open) | 0.0761 | (none) | graph theory | additive combinatorics | 0.9239 |
| #82 (open) | #374 (open) | 0.0761 | (none) | graph theory | number theory | 0.9239 |
| #82 (open) | #380 (open) | 0.0761 | (none) | graph theory | number theory | 0.9239 |
| #669 (open) | #374 (open) | 0.0761 | (none) | geometry | number theory | 0.9239 |
| #669 (open) | #168 (open) | 0.0761 | (none) | geometry | additive combinatorics | 0.9239 |
| #669 (open) | #380 (open) | 0.0761 | (none) | geometry | number theory | 0.9239 |
| #82 (open) | #849 (open) | 0.0801 | (none) | graph theory | binomial coefficients, number theory | 0.9199 |
| #139 (proved) | #121 (disproved) | 0.0853 | (none) | additive combinatorics, arithmetic progressions | number theory, squares | 0.9147 |
| #142 (open) | #479 (open) | 0.0885 | (none) | additive combinatorics, arithmetic progressions | number theory | 0.9115 |
| #1026 (solved (Lean)) | #34 (disproved) | 0.1384 | (none) | combinatorics | number theory | 0.8616 |
| #1026 (solved (Lean)) | #121 (disproved) | 0.1537 | (none) | combinatorics | number theory, squares | 0.8463 |
| #67 (proved) | #139 (proved) | 0.1545 | (none) | discrepancy | additive combinatorics, arithmetic progressions | 0.8455 |
| #83 (proved) | #139 (proved) | 0.1545 | (none) | combinatorics | additive combinatorics, arithmetic progressions | 0.8455 |
| #67 (proved) | #83 (proved) | 0.1566 | (none) | discrepancy | combinatorics | 0.8434 |
| #67 (proved) | #34 (disproved) | 0.1648 | (none) | discrepancy | number theory | 0.8352 |
| #67 (proved) | #121 (disproved) | 0.1797 | (none) | discrepancy | number theory, squares | 0.8203 |
| #67 (proved) | #861 (solved) | 0.183 | (none) | discrepancy | number theory, sidon sets | 0.817 |
| #202 (open) | #1074 (open) | 0.2929 | (none) | covering systems | number theory | 0.7071 |
| #202 (open) | #51 (open) | 0.2929 | (none) | covering systems | number theory | 0.7071 |
| #202 (open) | #935 (open) | 0.2929 | (none) | covering systems | number theory | 0.7071 |
| #202 (open) | #528 (open) | 0.2929 | (none) | covering systems | geometry | 0.7071 |
| #219 (proved) | #34 (disproved) | 0.1136 | number theory | additive combinatorics, arithmetic progressions | - | 0.6648 |
| #219 (proved) | #1064 (proved) | 0.1271 | number theory | additive combinatorics, arithmetic progressions | - | 0.6547 |
| #242 (falsifiable) | #849 (open) | 0.0229 | number theory | unit fractions | binomial coefficients | 0.6517 |
| #121 (disproved) | #849 (open) | 0.0316 | number theory | squares | binomial coefficients | 0.6459 |

### Interpretation of Surprising Neighbors

The highest-surprise pairs represent problems from different mathematical areas
that share structural 'DNA': similar OEIS profiles, similar prize levels, or
similar status. These are candidates for cross-pollination of ideas.

**Most frequent area pairs in surprising neighbors:**

- (shared) <-> number theory: 11 surprising pairs
- (shared) <-> (shared): 5 surprising pairs
- graph theory <-> number theory: 4 surprising pairs
- geometry <-> number theory: 3 surprising pairs
- (shared) <-> geometry: 2 surprising pairs
- combinatorics <-> number theory: 2 surprising pairs
- (shared) <-> combinatorics: 2 surprising pairs
- (shared) <-> graph theory: 1 surprising pairs

---

## Summary of Key Discoveries

### 1. Hidden OEIS Bridges
- Found **14** problem pairs sharing OEIS sequences with low tag overlap (0 zero-overlap, 14 low-overlap)
- Most notable: #683 <-> #928 via A006530 (Jaccard=0.333)

### 2. Tag Gaps
- **5** major tag pairs have ZERO intersection problems
  - Empty: number theory x combinatorics, graph theory x analysis, geometry x additive combinatorics, geometry x analysis, ramsey theory x analysis
- **11** major tag pairs have 1-3 problems (sparse)
  - Sparse: number theory x graph theory, number theory x geometry, number theory x analysis, graph theory x geometry, graph theory x additive combinatorics, graph theory x combinatorics, geometry x combinatorics, ramsey theory x combinatorics, additive combinatorics x analysis, additive combinatorics x combinatorics, analysis x combinatorics

### 3. Technique Transfer
- **2988** potential technique transfers identified
- **512** target open problems with prizes
- Most transferable technique: **ramsey theory** (1439 candidates)

### 4. Structural Isomorphisms
- **58** tag patterns have both solved and open problems
- **8** of these have 3+ tags (highly specific)

### 5. Novel Problems
- Generated **5** novel problems at underexplored intersections
  - **NRD-1**: Sidon Sets in Point Configurations (geometry x additive combinatorics)
  - **NRD-2**: Spectral Gap of Coprime Graphs and Analytic Number Theory (analysis x graph theory)
  - **NRD-3**: Discrepancy Bounds for Ramsey Colorings (ramsey theory x analysis)
  - **NRD-4**: Turan Numbers for Geometric Hypergraphs (combinatorics x geometry)
  - **NRD-5**: Covering Systems as Intersecting Families (number theory x combinatorics)

### 6. Surprising Genome Neighbors
- Found **30** surprising near-neighbor pairs
- These are problems with similar structural profiles but different mathematical content
