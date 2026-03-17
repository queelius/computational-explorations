# Difficulty Decomposition Analysis

Decomposing the multi-dimensional Erdős problem space into
independent difficulty dimensions via PCA.

## 1. Principal Components (Variance Explained)

| PC | Name | Variance | Cumulative |
|-----|------|----------|------------|
| PC1 | Tag Solvability Gradient | 8.6% | 8.6% |
| PC2 | Multi-Tag Complexity | 5.7% | 14.3% |
| PC3 | Geometry-Age-Solvability | 4.9% | 19.3% |
| PC4 | Geometry vs Graph Theory | 3.9% | 23.2% |
| PC5 | Late-Era Analytical | 3.8% | 27.0% |
| PC6 | OEIS Connectivity | 3.4% | 30.4% |
| PC7 | PC7: additive combinatorics / sidon sets | 3.0% | 33.3% |
| PC8 | Problem Isolation | 2.9% | 36.2% |
| PC9 | PC9: set theory / cycles | 2.5% | 38.8% |
| PC10 | PC10: base representations / binomial coefficients | 2.4% | 41.1% |

## 2. Factor Loadings (Top 3 Components)

### PC1: Tag Solvability Gradient (8.6%)

**Positive loadings** (high score = more of this):
- avg_tag_solve_rate: +0.424
- min_tag_solve_rate: +0.406
- max_tag_solve_rate: +0.349
- tag:graph theory: +0.207
- oeis_solved_bridges: +0.206

**Negative loadings** (high score = less of this):
- tag:number theory: -0.275
- isolation_proxy: -0.199
- formalized: -0.186
- tag:primes: -0.162
- oeis_count: -0.113

### PC2: Multi-Tag Complexity (5.7%)

**Positive loadings** (high score = more of this):
- problem_number_norm: +0.224
- number_quartile: +0.212
- tag:number theory: +0.191
- min_tag_solve_rate: +0.149
- isolation_proxy: +0.144

**Negative loadings** (high score = less of this):
- tag_count: -0.500
- tag_diversity: -0.482
- tag:ramsey theory: -0.211
- tag:graph theory: -0.198
- tag:chromatic number: -0.176

### PC3: Geometry-Age-Solvability (4.9%)

**Positive loadings** (high score = more of this):
- max_tag_solve_rate: +0.304
- isolation_proxy: +0.256
- avg_tag_solve_rate: +0.234
- tag:number theory: +0.203
- tag:unit fractions: +0.196

**Negative loadings** (high score = less of this):
- tag:geometry: -0.331
- tag:distances: -0.290
- problem_number_norm: -0.272
- oeis_solved_bridges: -0.271
- number_quartile: -0.263

## 3. Dimension-Solvability Correlation

| PC | Correlation | Solved Mean | Open Mean | Separation |
|----|-------------|------------|-----------|-----------|
| PC1 (Tag Solvability Gradient) | +0.225 | +0.59 | -0.38 | 0.472 |
| PC7 (PC7: additive combinatorics / sidon sets) | +0.077 | +0.12 | -0.08 | 0.159 |
| PC8 (Problem Isolation) | -0.070 | -0.11 | +0.07 | 0.144 |
| PC3 (Geometry-Age-Solvability) | +0.060 | +0.12 | -0.08 | 0.122 |
| PC4 (Geometry vs Graph Theory) | +0.054 | +0.10 | -0.06 | 0.110 |
| PC9 (PC9: set theory / cycles) | +0.047 | +0.07 | -0.04 | 0.096 |
| PC5 (Late-Era Analytical) | -0.043 | -0.08 | +0.05 | 0.088 |
| PC10 (PC10: base representations / binomial coefficients) | -0.038 | -0.05 | +0.03 | 0.077 |
| PC6 (OEIS Connectivity) | -0.023 | -0.04 | +0.02 | 0.047 |
| PC2 (Multi-Tag Complexity) | -0.016 | -0.03 | +0.02 | 0.033 |

## 4. Difficulty Clusters

Silhouette score: 0.347

| Cluster | Size | Solve Rate | Top Tags | Avg Prize |
|---------|------|-----------|----------|-----------|
| 2 | 60 | 26.7% | geometry, distances, convex | $62 |
| 3 | 155 | 27.7% | number theory, primes, divisors | $1 |
| 0 | 422 | 37.2% | number theory, graph theory, geometry | $16 |
| 1 | 198 | 38.9% | graph theory, ramsey theory, chromatic number | $50 |
| 5 | 191 | 46.6% | number theory, additive combinatorics, unit fractions | $204 |
| 4 | 109 | 58.7% | analysis, combinatorics, polynomials | $11 |

## 5. Tag Difficulty Profiles

| Tag | Dominant PC | Strength | Solve Rate | Count |
|-----|-----------|----------|-----------|-------|
| base representations | PC1 (Tag Solvability Gradient) | 6.016 | 0.0% | 5 |
| probability | PC5 (Late-Era Analytical) | 5.372 | 44.4% | 9 |
| intersecting family | PC3 (Geometry-Age-Solvability) | 5.035 | 80.0% | 5 |
| powers | PC1 (Tag Solvability Gradient) | 4.969 | 0.0% | 4 |
| polynomials | PC5 (Late-Era Analytical) | 4.856 | 44.4% | 18 |
| convex | PC4 (Geometry vs Graph Theory) | 4.832 | 41.7% | 12 |
| planar graphs | PC1 (Tag Solvability Gradient) | 4.794 | 66.7% | 3 |
| squares | PC1 (Tag Solvability Gradient) | 3.988 | 25.0% | 4 |
| diophantine approximation | PC1 (Tag Solvability Gradient) | 3.742 | 71.4% | 7 |
| iterated functions | PC1 (Tag Solvability Gradient) | 3.608 | 11.1% | 9 |
| analysis | PC1 (Tag Solvability Gradient) | 3.494 | 52.8% | 72 |
| combinatorics | PC1 (Tag Solvability Gradient) | 3.474 | 56.8% | 44 |
| primes | PC1 (Tag Solvability Gradient) | 3.417 | 20.4% | 49 |
| distances | PC3 (Geometry-Age-Solvability) | 3.367 | 24.5% | 53 |
| binomial coefficients | PC1 (Tag Solvability Gradient) | 3.061 | 27.3% | 22 |
| cycles | PC2 (Multi-Tag Complexity) | 2.903 | 40.9% | 22 |
| set theory | PC2 (Multi-Tag Complexity) | 2.737 | 25.0% | 24 |
| discrepancy | PC1 (Tag Solvability Gradient) | 2.678 | 50.0% | 16 |
| geometry | PC3 (Geometry-Age-Solvability) | 2.625 | 34.3% | 108 |
| complete sequences | PC1 (Tag Solvability Gradient) | 2.554 | 25.0% | 8 |

## 6. Hardest Open Problems (by Difficulty Score)

| Problem | Score | Tags | Prize |
|---------|-------|------|-------|
| #376 | 4.575 | base representations, binomial coefficients, number theory | - |
| #730 | 4.535 | base representations, binomial coefficients, number theory | - |
| #125 | 4.037 | base representations, number theory | - |
| #322 | 3.469 | number theory, powers | - |
| #124 | 3.390 | base representations, number theory | - |
| #406 | 3.354 | base representations, number theory | - |
| #409 | 3.078 | iterated functions, number theory | - |
| #413 | 2.957 | iterated functions, number theory | - |
| #325 | 2.932 | number theory, powers | - |
| #324 | 2.931 | number theory, powers | - |
| #412 | 2.911 | iterated functions, number theory | - |
| #849 | 2.901 | binomial coefficients, number theory | - |
| #408 | 2.728 | iterated functions, number theory | - |
| #218 | 2.717 | number theory, primes | - |
| #323 | 2.702 | number theory, powers | - |

## 7. Easiest Open Problems (Low-Hanging Fruit)

| Problem | Score | Tags | Prize |
|---------|-------|------|-------|
| #1044 | -2.091 | analysis | - |
| #1117 | -2.096 | analysis | - |
| #1120 | -2.096 | analysis | - |
| #987 | -2.204 | analysis, discrepancy | - |
| #995 | -2.205 | analysis, discrepancy | - |
| #624 | -2.301 | combinatorics | - |
| #120 | -2.416 | combinatorics | $100 |
| #644 | -2.532 | combinatorics | - |
| #665 | -2.534 | combinatorics | - |
| #734 | -2.538 | combinatorics | - |
| #776 | -2.541 | combinatorics | - |
| #857 | -2.563 | combinatorics | - |
| #1066 | -2.607 | graph theory, planar graphs | - |
| #1002 | -3.452 | analysis, diophantine approximation | - |
| #701 | -4.324 | combinatorics, intersecting family | - |

## 8. Difficulty Outliers

### PC1: Tag Solvability Gradient

**Extreme high:**
- #910 (z=5.79, disproved): topology
- #909 (z=4.46, proved): analysis, topology
- #701 (z=3.09, open): combinatorics, intersecting family
- #1002 (z=2.77, open): analysis, diophantine approximation
- #998 (z=2.77, proved): analysis, diophantine approximation

**Extreme low:**
- #376 (z=-3.22, open): base representations, binomial coefficients, number theory
- #730 (z=-3.06, open): base representations, binomial coefficients, number theory
- #125 (z=-3.02, open): base representations, number theory
- #1123 (z=-2.80, not provable): algebra
- #322 (z=-2.69, open): number theory, powers

### PC2: Multi-Tag Complexity

**Extreme high:**
- #1106 (z=1.85, open): number theory
- #1074 (z=1.84, open): number theory
- #1065 (z=1.84, open): number theory
- #1064 (z=1.84, proved): number theory
- #1073 (z=1.80, open): number theory

**Extreme low:**
- #593 (z=-3.45, open): chromatic number, graph theory, hypergraphs
- #95 (z=-3.09, proved): convex, distances, geometry
- #97 (z=-2.93, falsifiable): convex, distances, geometry
- #74 (z=-2.78, open): chromatic number, cycles, graph theory
- #93 (z=-2.74, proved): convex, distances, geometry

### PC3: Geometry-Age-Solvability

**Extreme high:**
- #21 (z=3.73, proved): combinatorics, intersecting family
- #534 (z=3.58, solved): intersecting family, number theory
- #910 (z=3.49, disproved): topology
- #56 (z=3.21, disproved (Lean)): intersecting family, number theory
- #909 (z=3.13, proved): analysis, topology

**Extreme low:**
- #1123 (z=-4.73, not provable): algebra
- #1127 (z=-3.00, independent): distances, geometry, set theory
- #956 (z=-2.98, open): convex, distances, geometry
- #1089 (z=-2.73, open): distances, geometry
- #1087 (z=-2.73, open): distances, geometry
