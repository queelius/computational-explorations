# Problem Similarity Analysis

Multi-dimensional similarity computation revealing hidden
relationships, natural clusters, and technique transfer candidates.

## 1. Hidden Twins (high structural similarity, different tags)

| Problem A | Problem B | Cosine | Tag Overlap | Surprise | Tags A | Tags B |
|-----------|-----------|--------|-------------|----------|--------|--------|
| #12 | #61 | 0.802 | 0.000 | 0.802 | number theory | graph theory |
| #12 | #152 | 0.802 | 0.000 | 0.802 | number theory | sidon sets |
| #12 | #153 | 0.802 | 0.000 | 0.802 | number theory | sidon sets |
| #12 | #158 | 0.802 | 0.000 | 0.802 | number theory | sidon sets |
| #12 | #196 | 0.802 | 0.000 | 0.802 | number theory | arithmetic progressions |
| #12 | #257 | 0.802 | 0.000 | 0.802 | number theory | irrationality |
| #12 | #258 | 0.802 | 0.000 | 0.802 | number theory | irrationality |
| #12 | #264 | 0.802 | 0.000 | 0.802 | number theory | irrationality |
| #12 | #267 | 0.802 | 0.000 | 0.802 | number theory | irrationality |
| #12 | #269 | 0.802 | 0.000 | 0.802 | number theory | irrationality |
| #12 | #352 | 0.802 | 0.000 | 0.802 | number theory | geometry |
| #12 | #509 | 0.802 | 0.000 | 0.802 | number theory | analysis |
| #12 | #510 | 0.802 | 0.000 | 0.802 | number theory | analysis |
| #12 | #513 | 0.802 | 0.000 | 0.802 | number theory | analysis |
| #12 | #517 | 0.802 | 0.000 | 0.802 | number theory | analysis |

## 2. Natural Problem Families (k-means clustering)

### Family 0 (921 problems)
- Solve rate: 38.3%
- Tags: number theory (31%), graph theory (14%), geometry (6%)
- Examples: #1, #2, #3, #4, #6, #8
- Total prizes: $53614

### Family 4 (53 problems)
- Solve rate: 100.0%
- Tags: number theory (29%), graph theory (17%), combinatorics (8%)
- Examples: #54, #55, #136, #186, #192, #223
- Total prizes: $350

### Family 5 (50 problems)
- Solve rate: 0.0%
- Tags: graph theory (24%), number theory (23%), geometry (9%)
- Examples: #7, #11, #19, #23, #85, #97
- Total prizes: $1582

### Family 3 (44 problems)
- Solve rate: 31.8%
- Tags: number theory (48%), divisors (33%), sidon sets (7%)
- Examples: #5, #14, #18, #26, #30, #43
- Total prizes: $1350

### Family 1 (27 problems)
- Solve rate: 44.4%
- Tags: hypergraphs (42%), graph theory (29%), combinatorics (8%)
- Examples: #207, #500, #562, #563, #564, #593
- Total prizes: $2050

### Family 7 (22 problems)
- Solve rate: 40.9%
- Tags: cycles (42%), graph theory (42%), chromatic number (15%)
- Examples: #57, #58, #60, #63, #64, #65
- Total prizes: $1600

### Family 2 (9 problems)
- Solve rate: 11.1%
- Tags: iterated functions (50%), number theory (39%), analysis (11%)
- Examples: #229, #408, #409, #410, #411, #412

### Family 6 (9 problems)
- Solve rate: 44.4%
- Tags: probability (39%), analysis (26%), polynomials (22%)
- Examples: #520, #521, #522, #523, #524, #525

## 3. Most Isolated Problems (unique structure)

| Problem | Isolation | Max Sim | Tags | Status |
|---------|-----------|---------|------|--------|
| #67 | 0.382 | 0.618 | discrepancy | proved |
| #710 | 0.328 | 0.672 | number theory | open |
| #121 | 0.327 | 0.673 | number theory, squares | disproved |
| #1123 | 0.325 | 0.675 | algebra | not provable |
| #2 | 0.317 | 0.683 | covering systems, number theory | disproved |
| #241 | 0.313 | 0.687 | additive combinatorics, sidon sets | open |
| #56 | 0.262 | 0.738 | intersecting family, number theory | disproved (Lean) |
| #107 | 0.259 | 0.741 | convex, geometry | falsifiable |
| #474 | 0.259 | 0.741 | ramsey theory, set theory | not provable |
| #1128 | 0.259 | 0.741 | hypergraphs, ramsey theory | disproved |
| #94 | 0.253 | 0.747 | convex, distances | proved |
| #140 | 0.251 | 0.749 | additive combinatorics, arithmetic progressions | proved |
| #20 | 0.247 | 0.753 | combinatorics | open |
| #105 | 0.247 | 0.753 | geometry | disproved (Lean) |
| #120 | 0.247 | 0.753 | combinatorics | open |

## 4. Best Transfer Candidates (solved → open)

| Solved | Open | Similarity | Open Prize | Solved Tags | Open Tags |
|--------|------|-----------|-----------|-------------|-----------|
| #523 | #521 | 0.843 | - | analysis, polynomials | analysis, polynomials |
| #523 | #524 | 0.843 | - | analysis, polynomials | analysis, polynomials |
| #921 | #626 | 0.843 | - | chromatic number, cycles | chromatic number, cycles |
| #26 | #859 | 0.838 | - | divisors, number theory | divisors, number theory |
| #26 | #885 | 0.838 | - | divisors, number theory | divisors, number theory |
| #189 | #188 | 0.838 | - | geometry, ramsey theory | geometry, ramsey theory |
| #189 | #508 | 0.838 | - | geometry, ramsey theory | geometry, ramsey theory |
| #229 | #906 | 0.838 | - | analysis, iterated functions | analysis, iterated functions |
| #285 | #295 | 0.838 | - | number theory, unit fractions | number theory, unit fractions |
| #285 | #304 | 0.838 | - | number theory, unit fractions | number theory, unit fractions |
| #285 | #319 | 0.838 | - | number theory, unit fractions | number theory, unit fractions |
| #298 | #288 | 0.838 | - | number theory, unit fractions | number theory, unit fractions |
| #298 | #289 | 0.838 | - | number theory, unit fractions | number theory, unit fractions |
| #298 | #306 | 0.838 | - | number theory, unit fractions | number theory, unit fractions |
| #298 | #312 | 0.838 | - | number theory, unit fractions | number theory, unit fractions |

## 5. Structural Isomorphism Classes

- **28 problems** (number theory): #122, #254, #261, #341, #369, #388, #420, #432, #445, #460 +18 more
  Solve rate: 0.0% (0 solved, 28 open)
- **28 problems** (number theory): #131, #342, #367, #368, #374, #380, #382, #385, #394, #417 +18 more
  Solve rate: 0.0% (0 solved, 28 open)
- **28 problems** (number theory): #334, #415, #430, #436, #452, #456, #472, #535, #539, #650 +18 more
  Solve rate: 0.0% (0 solved, 28 open)
- **27 problems** (number theory): #145, #208, #243, #359, #371, #389, #416, #422, #424, #457 +17 more
  Solve rate: 0.0% (0 solved, 27 open)
- **22 problems** (number theory): #12, #25, #38, #137, #332, #354, #383, #421, #455, #477 +12 more
  Solve rate: 0.0% (0 solved, 22 open)
- **20 problems** (graph theory): #73, #134, #577, #578, #618, #621, #715, #717, #718, #745 +10 more
  Solve rate: 100.0% (20 solved, 0 open)
- **17 problems** (number theory): #235, #239, #246, #443, #464, #465, #466, #481, #487, #490 +7 more
  Solve rate: 100.0% (17 solved, 0 open)
- **17 problems** (number theory): #329, #357, #361, #536, #677, #694, #889, #936, #938, #939 +7 more
  Solve rate: 0.0% (0 solved, 17 open)
- **15 problems** (graph theory): #81, #151, #600, #610, #614, #620, #805, #813, #934, #1011 +5 more
  Solve rate: 0.0% (0 solved, 15 open)
- **14 problems** (ramsey theory, graph theory): #112, #129, #159, #181, #554, #555, #558, #560, #609, #809 +4 more
  Solve rate: 0.0% (0 solved, 14 open)

## 6. Tag Embedding (SVD on co-occurrence)

### Closest Tag Pairs (mathematical neighbors)
- powers ↔ squares: distance 0.246
- complete sequences ↔ irrationality: distance 0.951
- base representations ↔ primitive sets: distance 0.954
- group theory ↔ powerful: distance 0.962
- algebra ↔ topology: distance 0.973
- algebra ↔ group theory: distance 1.03
- base representations ↔ powers: distance 1.112
- base representations ↔ squares: distance 1.126
- group theory ↔ topology: distance 1.418
- irrationality ↔ primitive sets: distance 1.423

### Most Distant Tag Pairs
- graph theory ↔ number theory: distance 617.383
- geometry ↔ number theory: distance 562.07
- chromatic number ↔ number theory: distance 555.983
- distances ↔ number theory: distance 555.068
- analysis ↔ number theory: distance 554.158

First 3 components explain 55.1% of variance.
