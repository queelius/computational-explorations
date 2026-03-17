# Deep Analysis of Erdos Problems Database


*Generated: 2026-02-13 00:06 | 1135 problems analyzed*


## Executive Summary

The Erdos Problems database contains **1135 problems**: 636 open (56%), 281 proved (25%), 107 disproved (9%), 58 solved (5%), and 53 in other states.

### Key Findings

1. **OEIS Family Structure**: 38 OEIS sequences are shared across problems, forming 28 connected families. The largest super-family (10 problems: #77, #78, #87, #165, #166, #544, #545, #553, #986, #1030) is formed by the merger of the A059442 cluster (7 problems) and the A000791 cluster (5 problems), which overlap at #986 and #1030. This bridge connects two distinct sets of Ramsey-theoretic problems. The Sidon set family (6 problems via A143824/A227590/A003022) and the arithmetic progression family (5 problems via A003002-A003005) are also prominent. Notably, 5 of 6 Sidon family problems remain open.

2. **Solvability Varies Dramatically by Area**: The highest prove rates belong to 'polynomials' (39%), 'factorials' (38%), and 'unit fractions' (38%). The highest disprove rates belong to 'covering systems' (32%), 'turan number' (19%), and 'divisors' (17%). Sidon sets (75% open) and primes (73% open) are the most stubbornly unsolved areas.

3. **Low-Hanging Fruit Identified**: A gradient-boosted classifier trained on tag presence, OEIS count, prize, and formalization status achieves 58% accuracy distinguishing open/proved/disproved. The strongest predictive features are formalization status, OEIS count, and prize amount. Top candidates for future proofs include #626 (graph theory, chromatic number, cycles; P(proved)=0.73), #992 (discrepancy; 0.66), and #404 (factorials; 0.66). Top counterexample candidates include #838 (geometry, convex; P(disproved)=0.44) and #146 (turan number; 0.43).

4. **Temporal Patterns**: 121 problems were resolved after the initial database load (2025-08-31). December 2025 saw the largest post-load burst (48 resolutions), followed by September (27) and October (26). Graph theory and analysis dominate recent resolutions. A cluster of diophantine approximation problems (#998, #999, #1000, #1001) was resolved together in early September 2025, suggesting coordinated breakthroughs in that area.

5. **Five Natural Mathematical Communities**: Greedy modularity optimization on the tag co-occurrence network (modularity = 0.536) reveals: (a) Number theory mega-cluster (21 tags, 637 problems) including primes, additive combinatorics, Sidon sets, divisors; (b) Graph theory cluster (9 tags, 351 problems) including Ramsey theory, chromatic number, cycles; (c) Analysis cluster (6 tags, 93 problems) with polynomials, probability, discrepancy; (d) Geometry cluster (3 tags, 109 problems) with distances and convexity; (e) A singleton algebra tag.

6. **Isolation Analysis**: Problem #1123 (algebra, 'not provable') is the single most isolated problem in the database (score 0.95) -- it shares no tags with any other problem. After that, #910 (topology) and #909 (analysis + topology) are the most isolated. Tags massively over-represented among isolated problems include group theory (22.7x), powers (22.7x), planar graphs (22.7x), and topology (22.7x), suggesting these are areas where the database's tag vocabulary may be too coarse to capture true relationships. The most connected problems are #986 and #1030, each linked to 9 other problems via shared OEIS sequences.


## 1. OEIS Cluster Analysis

**38 OEIS sequences** are shared by more than one problem.

These form **28 problem families** (connected components via shared sequences).

### Key Named Families

#### Arithmetic Progression Family (A003002-A003005)

Expected problems: ['3', '139', '140', '142', '201']
Actual problems found: ['3', '139', '140', '142', '201']

Status breakdown: {'proved': 2, 'open': 3}
Common tags (all members share): ['additive combinatorics', 'arithmetic progressions']
Union of tags: ['additive combinatorics', 'arithmetic progressions', 'number theory']

#### Sidon Set Family (A143824, A227590, A003022)

Expected problems: ['14', '30', '43', '155', '530', '861']
Actual problems found: ['14', '30', '43', '155', '530', '861']

Status breakdown: {'open': 5, 'solved': 1}
Common tags (all members share): ['sidon sets']
Union of tags: ['additive combinatorics', 'number theory', 'sidon sets']

#### A059442 Family

Expected problems: ['77', '78', '87', '166', '545', '986', '1030']
Actual problems found: ['77', '78', '87', '166', '545', '986', '1030']

Status breakdown: {'open': 6, 'proved': 1}
Common tags (all members share): ['graph theory', 'ramsey theory']
Union of tags: ['graph theory', 'ramsey theory']

#### A000791 Family

Expected problems: ['165', '544', '553', '986', '1030']
Actual problems found: ['165', '544', '553', '986', '1030']

Status breakdown: {'open': 4, 'proved': 1}
Common tags (all members share): ['graph theory', 'ramsey theory']
Union of tags: ['graph theory', 'ramsey theory']

### All Families (sorted by size)

| Family | Size | Members | Connecting Sequences | Open | Proved |
|--------|------|---------|---------------------|------|--------|
| 77-family | 10 | 77, 78, 87, 165, 166, 544, 545, 553, 986, 1030 | A000791, A059442 | 8 | 2 |
| 14-family | 6 | 14, 30, 43, 155, 530, 861 | A003022, A143824, A227590 | 5 | 0 |
| 3-family | 5 | 3, 139, 140, 142, 201 | A003002, A003003, A003004, A003005 | 3 | 2 |
| 5-family | 3 | 5, 852, 853 | A001223 | 3 | 0 |
| 121-family | 3 | 121, 786, 969 | A013928, A143301 | 2 | 0 |
| 148-family | 3 | 148, 243, 315 | A000058, A076393 | 2 | 1 |
| 364-family | 3 | 364, 365, 366 | A060355 | 1 | 0 |
| 368-family | 3 | 368, 683, 928 | A006530, A074399 | 3 | 0 |
| 51-family | 2 | 51, 821 | A014197 | 2 | 0 |
| 85-family | 2 | 85, 552 | A006672 | 1 | 0 |
| 89-family | 2 | 89, 91 | A186704 | 2 | 0 |
| 101-family | 2 | 101, 669 | A006065 | 2 | 0 |
| 138-family | 2 | 138, 169 | A005346 | 2 | 0 |
| 145-family | 2 | 145, 208 | A005117 | 2 | 0 |
| 200-family | 2 | 200, 219 | A005115 | 1 | 1 |
| 251-family | 2 | 251, 980 | A098990 | 1 | 1 |
| 321-family | 2 | 321, 327 | A384927 | 2 | 0 |
| 367-family | 2 | 367, 935 | A057521 | 2 | 0 |
| 398-family | 2 | 398, 936 | A146968 | 1 | 0 |
| 410-family | 2 | 410, 412 | A007497 | 2 | 0 |
| 416-family | 2 | 416, 417 | A264810 | 2 | 0 |
| 457-family | 2 | 457, 663 | A391668 | 2 | 0 |
| 468-family | 2 | 468, 1054 | A167485 | 2 | 0 |
| 470-family | 2 | 470, 825 | A006037 | 2 | 0 |
| 687-family | 2 | 687, 854 | A048670 | 2 | 0 |
| 770-family | 2 | 770, 820 | A263647 | 2 | 0 |
| 941-family | 2 | 941, 1107 | A056828 | 1 | 1 |
| 1103-family | 2 | 1103, 1109 | A392164 | 2 | 0 |

### Potential Missing Connections

Problems in OEIS families that share many tags with each other but are NOT linked by OEIS:

- Problems #77 and #165: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #77 and #544: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #77 and #553: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #78 and #165: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #78 and #544: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #78 and #553: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #87 and #165: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #87 and #544: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #87 and #553: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #165 and #166: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #165 and #545: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #166 and #544: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #166 and #553: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #544 and #545: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)
- Problems #545 and #553: share tags ['graph theory', 'ramsey theory'] but no direct OEIS link (connected only indirectly)


## 2. Solve-Rate Meta-Analysis

### Per-Tag Statistics

| Tag | Count | Open% | Proved% | Disproved% | Solved% | Avg Tags | Formalized% | Avg OEIS |
|-----|-------|-------|---------|------------|---------|----------|-------------|----------|
| number theory | 542 | 62% | 23% | 8% | 4% | 1.6 | 41% | 0.6 |
| graph theory | 270 | 47% | 26% | 12% | 6% | 1.8 | 6% | 0.1 |
| geometry | 108 | 59% | 20% | 7% | 6% | 1.7 | 19% | 0.2 |
| ramsey theory | 102 | 56% | 27% | 8% | 4% | 2.1 | 14% | 0.2 |
| additive combinatorics | 90 | 56% | 29% | 12% | 2% | 1.9 | 36% | 0.6 |
| analysis | 72 | 43% | 36% | 12% | 4% | 1.5 | 21% | 0.0 |
| chromatic number | 57 | 51% | 26% | 11% | 4% | 2.3 | 14% | 0.0 |
| distances | 53 | 68% | 17% | 4% | 4% | 2.2 | 23% | 0.2 |
| primes | 49 | 73% | 16% | 2% | 2% | 2.2 | 57% | 0.8 |
| unit fractions | 48 | 44% | 38% | 8% | 4% | 2.0 | 40% | 0.5 |
| combinatorics | 44 | 41% | 36% | 5% | 16% | 1.5 | 9% | 0.2 |
| divisors | 30 | 57% | 23% | 17% | 3% | 2.0 | 33% | 0.6 |
| sidon sets | 28 | 75% | 11% | 7% | 7% | 2.3 | 50% | 0.8 |
| additive basis | 27 | 59% | 22% | 15% | 0% | 2.2 | 44% | 0.2 |
| hypergraphs | 27 | 48% | 19% | 15% | 11% | 2.4 | 7% | 0.0 |
| arithmetic progressions | 24 | 62% | 21% | 12% | 4% | 2.0 | 38% | 1.0 |
| set theory | 24 | 62% | 12% | 12% | 0% | 2.3 | 25% | 0.0 |
| cycles | 22 | 50% | 36% | 5% | 0% | 2.4 | 14% | 0.0 |
| irrationality | 22 | 68% | 18% | 9% | 5% | 1.3 | 68% | 0.5 |
| binomial coefficients | 22 | 68% | 23% | 5% | 0% | 2.2 | 59% | 0.8 |
| factorials | 21 | 48% | 38% | 5% | 5% | 2.0 | 38% | 0.7 |
| turan number | 21 | 67% | 5% | 19% | 10% | 2.1 | 0% | 0.1 |
| covering systems | 19 | 47% | 16% | 32% | 0% | 1.9 | 21% | 0.2 |
| polynomials | 18 | 56% | 39% | 6% | 0% | 2.3 | 17% | 0.0 |
| discrepancy | 16 | 50% | 25% | 6% | 19% | 1.8 | 6% | 0.1 |
| convex | 12 | 33% | 25% | 17% | 0% | 2.7 | 25% | 0.3 |
| iterated functions | 9 | 89% | 11% | 0% | 0% | 2.0 | 78% | 1.0 |
| probability | 9 | 56% | 33% | 0% | 11% | 2.6 | 22% | 0.0 |
| complete sequences | 8 | 75% | 25% | 0% | 0% | 2.0 | 62% | 0.1 |
| primitive sets | 7 | 71% | 14% | 0% | 14% | 1.9 | 29% | 0.1 |
| diophantine approximation | 7 | 29% | 57% | 0% | 14% | 2.0 | 14% | 0.0 |
| intersecting family | 5 | 20% | 40% | 20% | 20% | 2.0 | 20% | 0.4 |
| base representations | 5 | 100% | 0% | 0% | 0% | 2.4 | 100% | 0.6 |
| powers | 4 | 100% | 0% | 0% | 0% | 2.0 | 50% | 0.5 |
| squares | 4 | 75% | 0% | 25% | 0% | 2.2 | 25% | 3.0 |
| group theory | 4 | 75% | 25% | 0% | 0% | 1.5 | 25% | 0.0 |
| planar graphs | 3 | 33% | 33% | 0% | 33% | 2.0 | 0% | 0.0 |
| topology | 2 | 0% | 50% | 50% | 0% | 1.5 | 0% | 0.0 |
| powerful | 2 | 50% | 0% | 50% | 0% | 2.0 | 50% | 1.5 |
| algebra | 1 | 0% | 0% | 0% | 0% | 1.0 | 0% | 0.0 |

### Tags Predicting Solvability (highest prove rate, n >= 5)

- **diophantine approximation**: 57% proved (7 problems)
- **intersecting family**: 40% proved (5 problems)
- **polynomials**: 39% proved (18 problems)
- **factorials**: 38% proved (21 problems)
- **unit fractions**: 38% proved (48 problems)
- **combinatorics**: 36% proved (44 problems)
- **cycles**: 36% proved (22 problems)
- **analysis**: 36% proved (72 problems)
- **probability**: 33% proved (9 problems)
- **additive combinatorics**: 29% proved (90 problems)

### Tags Predicting Falsifiability (highest disprove rate, n >= 5)

- **covering systems**: 32% disproved (19 problems)
- **intersecting family**: 20% disproved (5 problems)
- **turan number**: 19% disproved (21 problems)
- **convex**: 17% disproved (12 problems)
- **divisors**: 17% disproved (30 problems)
- **additive basis**: 15% disproved (27 problems)
- **hypergraphs**: 15% disproved (27 problems)
- **analysis**: 12% disproved (72 problems)
- **arithmetic progressions**: 12% disproved (24 problems)
- **set theory**: 12% disproved (24 problems)

### Hardest Tags (highest open rate, n >= 10)

- **sidon sets**: 75% still open (28 problems)
- **primes**: 73% still open (49 problems)
- **binomial coefficients**: 68% still open (22 problems)
- **irrationality**: 68% still open (22 problems)
- **distances**: 68% still open (53 problems)
- **turan number**: 67% still open (21 problems)
- **arithmetic progressions**: 62% still open (24 problems)
- **set theory**: 62% still open (24 problems)
- **number theory**: 62% still open (542 problems)
- **additive basis**: 59% still open (27 problems)

### Most Formalized Tags (n >= 10)

- **irrationality**: 68% formalized (22 problems)
- **binomial coefficients**: 59% formalized (22 problems)
- **primes**: 57% formalized (49 problems)
- **sidon sets**: 50% formalized (28 problems)
- **additive basis**: 44% formalized (27 problems)
- **number theory**: 41% formalized (542 problems)
- **unit fractions**: 40% formalized (48 problems)
- **factorials**: 38% formalized (21 problems)
- **arithmetic progressions**: 38% formalized (24 problems)
- **additive combinatorics**: 36% formalized (90 problems)

### Complexity Proxy: Average Number of Tags

(Higher tag count = problem touches more areas = potentially harder)

- **convex**: avg 2.67 tags per problem
- **hypergraphs**: avg 2.41 tags per problem
- **cycles**: avg 2.36 tags per problem
- **set theory**: avg 2.33 tags per problem
- **chromatic number**: avg 2.30 tags per problem
- **sidon sets**: avg 2.29 tags per problem
- **polynomials**: avg 2.28 tags per problem
- **primes**: avg 2.24 tags per problem
- **binomial coefficients**: avg 2.23 tags per problem
- **additive basis**: avg 2.19 tags per problem


## 3. Problem Difficulty Classifier

### Cross-Validated Classification Report (5-fold)

Predicting: open / proved / disproved from problem features

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| disproved | 0.06 | 0.02 | 0.03 | 107 |
| open | 0.68 | 0.76 | 0.72 | 636 |
| proved | 0.39 | 0.38 | 0.38 | 281 |
| **accuracy** | | | 0.58 | 1024 |

### Top Feature Importances

- **formalized**: 0.1977
- **n_oeis**: 0.1446
- **prize_usd**: 0.1203
- **n_tags**: 0.0651
- **tag:irrationality**: 0.0332
- **tag:number theory**: 0.0285
- **tag:primes**: 0.0274
- **tag:discrepancy**: 0.0252
- **tag:additive combinatorics**: 0.0229
- **tag:distances**: 0.0223
- **tag:graph theory**: 0.0219
- **tag:unit fractions**: 0.0217
- **tag:convex**: 0.0203
- **tag:turan number**: 0.0196
- **tag:combinatorics**: 0.0189

### Top 20 Low-Hanging Fruit (open problems most resembling proved)

| Problem | P(proved) | P(disproved) | Prize | Tags | OEIS |
|---------|-----------|--------------|-------|------|------|
| #626 | 0.73 | 0.01 | no | graph theory, chromatic number, cycles |  |
| #992 | 0.66 | 0.03 | no | discrepancy |  |
| #404 | 0.66 | 0.06 | no | number theory, factorials |  |
| #400 | 0.66 | 0.06 | no | number theory, factorials |  |
| #282 | 0.62 | 0.08 | no | number theory, unit fractions |  |
| #293 | 0.62 | 0.08 | no | number theory, unit fractions |  |
| #311 | 0.62 | 0.08 | no | number theory, unit fractions |  |
| #318 | 0.62 | 0.08 | no | number theory, unit fractions |  |
| #1029 | 0.60 | 0.03 | $100 | graph theory, ramsey theory |  |
| #531 | 0.56 | 0.07 | no | number theory, ramsey theory |  |
| #948 | 0.56 | 0.07 | no | number theory, ramsey theory |  |
| #1002 | 0.53 | 0.03 | no | analysis, diophantine approximation |  |
| #521 | 0.49 | 0.01 | no | analysis, polynomials, probability |  |
| #524 | 0.49 | 0.01 | no | analysis, probability, polynomials |  |
| #1066 | 0.49 | 0.03 | no | graph theory, planar graphs |  |
| #148 | 0.47 | 0.02 | no | number theory, unit fractions | A076393, A006585 |
| #1044 | 0.46 | 0.17 | no | analysis |  |
| #990 | 0.46 | 0.17 | no | analysis |  |
| #973 | 0.46 | 0.17 | no | analysis |  |
| #1117 | 0.46 | 0.17 | no | analysis |  |

### Top 20 Counterexample Candidates (open problems most resembling disproved)

| Problem | P(disproved) | P(proved) | Prize | Tags | OEIS |
|---------|--------------|-----------|-------|------|------|
| #838 | 0.44 | 0.13 | no | geometry, convex |  |
| #146 | 0.43 | 0.02 | $500 | graph theory, turan number |  |
| #713 | 0.43 | 0.02 | $500 | graph theory, turan number |  |
| #61 | 0.40 | 0.12 | no | graph theory |  |
| #281 | 0.37 | 0.27 | no | number theory, covering systems |  |
| #278 | 0.37 | 0.27 | no | number theory, covering systems |  |
| #195 | 0.34 | 0.10 | no | arithmetic progressions |  |
| #197 | 0.34 | 0.10 | no | arithmetic progressions |  |
| #1100 | 0.30 | 0.14 | no | number theory, divisors | A325864 |
| #995 | 0.26 | 0.09 | no | analysis, discrepancy |  |
| #987 | 0.26 | 0.09 | no | analysis, discrepancy |  |
| #885 | 0.26 | 0.09 | no | number theory, divisors |  |
| #859 | 0.26 | 0.09 | no | number theory, divisors |  |
| #365 | 0.24 | 0.02 | no | number theory | A060355, A060859, A175155 |
| #886 | 0.23 | 0.33 | no | number theory, divisors |  |
| #884 | 0.23 | 0.33 | no | number theory, divisors |  |
| #887 | 0.23 | 0.33 | no | number theory, divisors |  |
| #450 | 0.23 | 0.33 | no | number theory, divisors |  |
| #693 | 0.23 | 0.33 | no | number theory, divisors |  |
| #696 | 0.23 | 0.33 | no | number theory, divisors |  |


## 4. Temporal Pattern Analysis

Total resolved problems with dates: 446

### Monthly Resolution Activity

| Month | Proved | Disproved | Solved | Total |
|-------|--------|-----------|--------|-------|
| 2025-08 | 216 | 72 | 37 | 325 |
| 2025-09 | 13 | 8 | 6 | 27 |
| 2025-10 | 17 | 5 | 4 | 26 |
| 2025-11 | 7 | 4 | 0 | 11 |
| 2025-12 | 25 | 13 | 10 | 48 |
| 2026-01 | 3 | 5 | 1 | 9 |

Average resolutions per month: 74.3

**Solution waves** (>1.5x average):

- 2025-08: 325 resolutions

### Tags Predicting Recent Solutions

Median resolution date: 2025-08-31

Tags with highest fraction of *recent* resolutions (n >= 3):

- **ramsey theory**: 100% recent (40/40)
- **primes**: 100% recent (10/10)
- **sidon sets**: 100% recent (7/7)
- **number theory**: 100% recent (190/190)
- **intersecting family**: 100% recent (4/4)
- **factorials**: 100% recent (10/10)
- **diophantine approximation**: 100% recent (5/5)
- **graph theory**: 100% recent (119/119)
- **additive basis**: 100% recent (10/10)
- **polynomials**: 100% recent (8/8)
- **arithmetic progressions**: 100% recent (9/9)
- **combinatorics**: 100% recent (25/25)
- **covering systems**: 100% recent (9/9)
- **distances**: 100% recent (13/13)
- **set theory**: 100% recent (6/6)

### Status Update Timeline

Problems resolved after initial load (2025-08-31): 121

| Date | Problem | Category | Tags |
|------|---------|----------|------|
| 2025-09-02 | #259 | proved | irrationality |
| 2025-09-02 | #867 | disproved | additive combinatorics |
| 2025-09-07 | #957 | proved | geometry, distances |
| 2025-09-07 | #994 | disproved | analysis, discrepancy |
| 2025-09-07 | #998 | proved | analysis, diophantine approximation |
| 2025-09-07 | #999 | proved | number theory, diophantine approximation |
| 2025-09-07 | #1001 | solved | number theory, diophantine approximation |
| 2025-09-08 | #527 | proved | analysis, probability |
| 2025-09-09 | #1006 | disproved | graph theory, cycles |
| 2025-09-09 | #1007 | solved | graph theory |
| 2025-09-10 | #1008 | proved | graph theory |
| 2025-09-10 | #1010 | proved | graph theory |
| 2025-09-10 | #1015 | solved | graph theory, ramsey theory |
| 2025-09-12 | #1024 | solved | graph theory, hypergraphs |
| 2025-09-12 | #1025 | solved | combinatorics |
| 2025-09-12 | #1028 | solved | graph theory, discrepancy |
| 2025-09-13 | #1031 | proved | graph theory |
| 2025-09-13 | #1036 | proved | graph theory |
| 2025-09-15 | #511 | disproved | analysis |
| 2025-09-15 | #1042 | proved | analysis |
| 2025-09-15 | #1046 | disproved | analysis |
| 2025-09-15 | #1047 | disproved | analysis |
| 2025-09-15 | #1048 | disproved | analysis |
| 2025-09-22 | #1037 | disproved | graph theory |
| 2025-09-28 | #1050 | proved | irrationality |
| 2025-09-28 | #1058 | proved | number theory |
| 2025-09-29 | #565 | proved | graph theory, ramsey theory |
| 2025-10-01 | #435 | proved | number theory |
| 2025-10-01 | #737 | proved | graph theory, chromatic number |
| 2025-10-01 | #974 | proved | analysis |
| 2025-10-01 | #1027 | proved | combinatorics |
| 2025-10-01 | #1067 | disproved | graph theory, set theory |
| 2025-10-05 | #1069 | solved | geometry |
| 2025-10-06 | #1078 | proved | graph theory |
| 2025-10-12 | #339 | proved | number theory, additive basis |
| 2025-10-14 | #223 | solved | geometry, distances |
| 2025-10-14 | #494 | proved | analysis, additive combinatorics |
| 2025-10-14 | #621 | proved | graph theory |
| 2025-10-14 | #822 | proved | number theory |
| 2025-10-14 | #903 | proved | combinatorics |
| 2025-10-14 | #1079 | solved | graph theory, turan number |
| 2025-10-14 | #1081 | disproved | number theory, powerful |
| 2025-10-18 | #1098 | proved | group theory |
| 2025-10-19 | #515 | proved | analysis |
| 2025-10-19 | #775 | disproved | graph theory, hypergraphs |
| 2025-10-19 | #1090 | proved | geometry, ramsey theory |
| 2025-10-19 | #1099 | proved | number theory, divisors |
| 2025-10-21 | #707 | disproved | additive combinatorics, sidon sets |
| 2025-10-25 | #608 | disproved | graph theory |
| 2025-10-31 | #433 | proved | number theory |
| 2025-10-31 | #434 | proved | number theory |
| 2025-10-31 | #1009 | proved | graph theory |
| 2025-10-31 | #1012 | solved | graph theory |
| 2025-11-04 | #613 | disproved | graph theory |
| 2025-11-21 | #1019 | proved | graph theory, planar graphs |
| 2025-11-22 | #105 | disproved | geometry |
| 2025-11-23 | #198 | disproved | additive combinatorics, sidon sets, arithmetic progressions |
| 2025-11-23 | #418 | proved | number theory |
| 2025-11-23 | #645 | proved | number theory, additive combinatorics, ramsey theory |
| 2025-11-24 | #31 | proved | number theory, additive basis |
| 2025-11-24 | #370 | proved | number theory |
| 2025-11-25 | #350 | proved | number theory, additive combinatorics |
| 2025-11-26 | #56 | disproved | number theory, intersecting family |
| 2025-11-29 | #499 | proved | combinatorics |
| 2025-12-01 | #481 | proved | number theory |
| 2025-12-02 | #69 | proved | number theory, irrationality |
| 2025-12-02 | #248 | proved | number theory |
| 2025-12-02 | #1102 | solved | number theory |
| 2025-12-04 | #1034 | disproved | graph theory |
| 2025-12-05 | #94 | proved | geometry, convex, distances |
| 2025-12-05 | #1000 | proved | number theory, diophantine approximation |
| 2025-12-08 | #674 | proved | number theory |
| 2025-12-08 | #1026 | solved | combinatorics |
| 2025-12-10 | #337 | disproved | number theory, additive combinatorics, additive basis |
| 2025-12-12 | #1018 | solved | graph theory, planar graphs |
| 2025-12-12 | #1023 | solved | combinatorics |
| 2025-12-12 | #1064 | proved | number theory |
| 2025-12-12 | #1076 | proved | hypergraphs |
| 2025-12-19 | #189 | disproved | geometry, ramsey theory |
| 2025-12-19 | #967 | disproved | number theory, analysis |
| 2025-12-20 | #697 | proved | number theory, divisors |
| 2025-12-20 | #784 | solved | number theory |
| 2025-12-21 | #303 | proved | number theory, unit fractions |
| 2025-12-25 | #333 | disproved | number theory, additive basis |
| 2025-12-26 | #981 | proved | number theory |
| 2025-12-27 | #440 | solved | number theory |
| 2025-12-27 | #493 | proved | number theory |
| 2025-12-27 | #897 | disproved | number theory |
| 2025-12-27 | #958 | disproved | distances, geometry |
| 2025-12-28 | #26 | disproved | number theory, divisors |
| 2025-12-28 | #229 | proved | analysis, iterated functions |
| 2025-12-28 | #246 | proved | number theory |
| 2025-12-28 | #516 | proved | analysis |
| 2025-12-28 | #862 | solved | number theory, sidon sets |
| 2025-12-28 | #1043 | disproved | analysis |
| 2025-12-28 | #1080 | disproved | graph theory |
| 2025-12-29 | #46 | proved | number theory, unit fractions, ramsey theory |
| 2025-12-29 | #226 | proved | analysis |
| 2025-12-29 | #298 | proved | number theory, unit fractions |
| 2025-12-29 | #299 | disproved | number theory, unit fractions |
| 2025-12-29 | #1077 | disproved | graph theory |
| 2025-12-29 | #1114 | proved | analysis, polynomials |
| 2025-12-29 | #1115 | solved | analysis |
| 2025-12-29 | #1116 | solved | analysis |
| 2025-12-29 | #1118 | solved | analysis |
| 2025-12-30 | #541 | proved | number theory |
| 2025-12-30 | #1121 | proved | geometry |
| 2025-12-30 | #1124 | proved | geometry |
| 2025-12-30 | #1125 | proved | analysis |
| 2025-12-30 | #1126 | proved | analysis |
| 2025-12-30 | #1128 | disproved | set theory, ramsey theory, hypergraphs |
| 2025-12-31 | #476 | proved | number theory, additive combinatorics |
| 2026-01-01 | #834 | solved | graph theory, hypergraphs |
| 2026-01-01 | #965 | disproved | ramsey theory |
| 2026-01-07 | #678 | proved | number theory |
| 2026-01-08 | #845 | disproved | number theory |
| 2026-01-10 | #205 | disproved | number theory |
| 2026-01-10 | #397 | disproved | number theory, binomial coefficients |
| 2026-01-10 | #729 | proved | number theory, factorials |
| 2026-01-11 | #401 | proved | number theory, factorials |
| 2026-01-11 | #1134 | disproved | number theory |


## 5. Tag Network Communities

Bipartite graph: 1175 nodes, 1838 edges

Tag co-occurrence graph: 40 tags, 93 edges

Detected **5 communities**:

### Community 1: additive basis, additive combinatorics, arithmetic progressions, base representations, binomial coefficients, complete sequences, covering systems, divisors, factorials, group theory, intersecting family, irrationality, iterated functions, number theory, powerful, powers, primes, primitive sets, sidon sets, squares, unit fractions
- Problems: 637 (394 open, 243 resolved)
- Strongest co-occurrences: number theory+unit fractions (48), number theory+primes (45), number theory+additive combinatorics (37), number theory+divisors (30), number theory+additive basis (27)

### Community 2: chromatic number, combinatorics, cycles, graph theory, hypergraphs, planar graphs, ramsey theory, set theory, turan number
- Problems: 351 (163 open, 188 resolved)
- Strongest co-occurrences: graph theory+ramsey theory (68), graph theory+chromatic number (54), graph theory+cycles (22), graph theory+turan number (21), graph theory+hypergraphs (19)

### Community 3: analysis, diophantine approximation, discrepancy, polynomials, probability, topology
- Problems: 93 (39 open, 54 resolved)
- Strongest co-occurrences: polynomials+analysis (18), analysis+probability (6), polynomials+probability (5), discrepancy+analysis (4), analysis+diophantine approximation (2)

### Community 4: convex, distances, geometry
- Problems: 109 (65 open, 44 resolved)
- Strongest co-occurrences: geometry+distances (52), geometry+convex (12), distances+convex (8)

### Community 5: algebra
- Problems: 1 (0 open, 1 resolved)

### Problem-Problem Network (projected via shared tags)

Problem co-tag graph: 1135 nodes, 199831 edges
Connected components: 2
Largest component: 1134 problems
Isolated problems (no shared tags with any other): 1

Tag network modularity: **0.536**


## 6. Isolation Score

Isolation score range: [0.055, 0.950]
Mean: 0.244, Median: 0.247, Std: 0.051

### Top 30 Most Isolated Problems

| Problem | Isolation | Jaccard Dist | Tag Rarity | OEIS Links | Tags | State |
|---------|-----------|--------------|------------|------------|------|-------|
| #1123 | 0.950 | 1.000 | 1.0000 | 0 | algebra | not provable |
| #910 | 0.600 | 0.500 | 0.5000 | 0 | topology | disproved |
| #909 | 0.510 | 0.500 | 0.2569 | 0 | analysis, topology | proved |
| #143 | 0.493 | 0.500 | 0.1429 | 0 | primitive sets | open |
| #274 | 0.479 | 0.500 | 0.1513 | 0 | covering systems, group theory | open |
| #543 | 0.471 | 0.500 | 0.1259 | 0 | group theory, number theory | open |
| #623 | 0.463 | 0.500 | 0.0417 | 0 | set theory | open |
| #132 | 0.456 | 0.500 | 0.0189 | 0 | distances | open |
| #520 | 0.450 | 0.500 | 0.0565 | 0 | number theory, probability | open |
| #1028 | 0.443 | 0.500 | 0.0331 | 0 | discrepancy, graph theory | solved |
| #192 | 0.443 | 0.500 | 0.0322 | 0 | arithmetic progressions, combinatorics | solved |
| #1119 | 0.442 | 0.500 | 0.0278 | 0 | analysis, set theory | independent |
| #498 | 0.439 | 0.500 | 0.0183 | 0 | analysis, combinatorics | proved |
| #171 | 0.438 | 0.500 | 0.0169 | 0 | additive combinatorics, combinatorics | proved |
| #733 | 0.438 | 0.500 | 0.0160 | 0 | combinatorics, geometry | proved |
| #777 | 0.437 | 0.500 | 0.0132 | 0 | combinatorics, graph theory | solved |
| #494 | 0.437 | 0.500 | 0.0125 | 0 | additive combinatorics, analysis | proved |
| #967 | 0.436 | 0.500 | 0.0079 | 0 | analysis, number theory | disproved (Lean) |
| #769 | 0.435 | 0.500 | 0.0056 | 0 | geometry, number theory | open |
| #883 | 0.434 | 0.500 | 0.0028 | 0 | graph theory, number theory | open |
| #773 | 0.387 | 0.333 | 0.0959 | 0 | number theory, sidon sets, squares | open |
| #527 | 0.385 | 0.333 | 0.0625 | 0 | analysis, probability | proved |
| #177 | 0.382 | 0.333 | 0.0521 | 0 | arithmetic progressions, discrepancy | open |
| #203 | 0.378 | 0.333 | 0.0365 | 0 | covering systems, primes | open |
| #191 | 0.372 | 0.333 | 0.0163 | 0 | combinatorics, ramsey theory | proved |
| #176 | 0.370 | 0.333 | 0.0384 | 0 | additive combinatorics, arithmetic progressions, discrepancy | open |
| #997 | 0.368 | 0.333 | 0.0323 | 0 | analysis, discrepancy, primes | open |
| #1128 | 0.367 | 0.333 | 0.0295 | 0 | hypergraphs, ramsey theory, set theory | disproved |
| #198 | 0.367 | 0.333 | 0.0295 | 0 | additive combinatorics, arithmetic progressions, sidon sets | disproved (Lean) |
| #18 | 0.367 | 0.333 | 0.0276 | 0 | divisors, factorials, number theory | open |

### What Makes Problems Isolated?

Tags over-represented in the 50 most isolated problems:

- **analysis**: 7 observed vs 3.2 expected (ratio 2.2x)
- **combinatorics**: 7 observed vs 1.9 expected (ratio 3.6x)
- **arithmetic progressions**: 6 observed vs 1.1 expected (ratio 5.7x)
- **additive combinatorics**: 6 observed vs 4.0 expected (ratio 1.5x)
- **set theory**: 5 observed vs 1.1 expected (ratio 4.7x)
- **primes**: 5 observed vs 2.2 expected (ratio 2.3x)
- **group theory**: 4 observed vs 0.2 expected (ratio 22.7x)
- **discrepancy**: 4 observed vs 0.7 expected (ratio 5.7x)
- **powers**: 4 observed vs 0.2 expected (ratio 22.7x)
- **covering systems**: 3 observed vs 0.8 expected (ratio 3.6x)
- **sidon sets**: 3 observed vs 1.2 expected (ratio 2.4x)
- **hypergraphs**: 3 observed vs 1.2 expected (ratio 2.5x)
- **planar graphs**: 3 observed vs 0.1 expected (ratio 22.7x)
- **topology**: 2 observed vs 0.1 expected (ratio 22.7x)
- **probability**: 2 observed vs 0.4 expected (ratio 5.0x)
- **squares**: 2 observed vs 0.2 expected (ratio 11.3x)
- **algebra**: 1 observed vs 0.0 expected (ratio 22.7x)
- **primitive sets**: 1 observed vs 0.3 expected (ratio 3.2x)
- **powerful**: 1 observed vs 0.1 expected (ratio 11.3x)

### Top 20 Most Connected Problems (lowest isolation)

| Problem | Isolation | Jaccard Dist | OEIS Links | Tags | State |
|---------|-----------|--------------|------------|------|-------|
| #139 | 0.081 | 0.000 | 4 | additive combinatorics, arithmetic progressions | proved |
| #140 | 0.081 | 0.000 | 4 | additive combinatorics, arithmetic progressions | proved |
| #142 | 0.081 | 0.000 | 4 | additive combinatorics, arithmetic progressions | open |
| #201 | 0.081 | 0.000 | 4 | additive combinatorics, arithmetic progressions | open |
| #165 | 0.075 | 0.000 | 4 | graph theory, ramsey theory | open |
| #544 | 0.075 | 0.000 | 4 | graph theory, ramsey theory | open |
| #553 | 0.075 | 0.000 | 4 | graph theory, ramsey theory | proved |
| #155 | 0.074 | 0.000 | 5 | additive combinatorics, sidon sets | open |
| #530 | 0.072 | 0.000 | 5 | number theory, sidon sets | open |
| #861 | 0.072 | 0.000 | 5 | number theory, sidon sets | solved |
| #77 | 0.064 | 0.000 | 6 | graph theory, ramsey theory | open |
| #78 | 0.064 | 0.000 | 6 | graph theory, ramsey theory | open |
| #87 | 0.064 | 0.000 | 6 | graph theory, ramsey theory | open |
| #166 | 0.064 | 0.000 | 6 | graph theory, ramsey theory | proved |
| #545 | 0.064 | 0.000 | 6 | graph theory, ramsey theory | open |
| #14 | 0.063 | 0.000 | 5 | additive combinatorics, number theory, sidon sets | open |
| #30 | 0.063 | 0.000 | 5 | additive combinatorics, number theory, sidon sets | open |
| #43 | 0.063 | 0.000 | 5 | additive combinatorics, number theory, sidon sets | open |
| #986 | 0.055 | 0.000 | 9 | graph theory, ramsey theory | open |
| #1030 | 0.055 | 0.000 | 9 | graph theory, ramsey theory | open |
