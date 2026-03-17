# Attack Surface Analysis

Concrete mathematical attack strategies for open Erdős problems.

## 1. Most Effective Technique Combinations

| Technique | Solve Rate | Solved/Total | Examples |
|-----------|-----------|-------------|----------|
| intersecting family + number theory | 100.0% | 3/3 | #56, #534, #844 |
| diophantine approximation + number theory | 80.0% | 4/5 | #496, #999, #1000 |
| number theory + ramsey theory | 78.6% | 11/14 | #45, #46, #54 |
| graph theory + planar graphs | 66.7% | 2/3 | #1018, #1019 |
| combinatorics + hypergraphs | 60.0% | 3/5 | #207, #747, #780 |
| chromatic number + hypergraphs | 60.0% | 3/5 | #780, #832, #833 |
| additive combinatorics + ramsey theory | 57.1% | 4/7 | #484, #645, #721 |
| covering systems + number theory | 53.3% | 8/15 | #2, #8, #27 |
| number theory + unit fractions | 50.0% | 24/48 | #45, #46, #47 |
| chromatic number + cycles | 50.0% | 4/8 | #57, #58, #63 |
| analysis + probability | 50.0% | 3/6 | #523, #525, #527 |
| factorials + number theory | 47.6% | 10/21 | #391, #392, #399 |
| additive combinatorics + number theory | 45.9% | 17/37 | #37, #53, #219 |
| analysis + polynomials | 44.4% | 8/18 | #115, #116, #228 |
| divisors + number theory | 43.3% | 13/30 | #26, #144, #381 |

### Single Tag Effectiveness (top 15)

- **intersecting family**: 80.0% (5 problems)
- **diophantine approximation**: 71.4% (7 problems)
- **combinatorics**: 56.8% (44 problems)
- **analysis**: 52.8% (72 problems)
- **unit fractions**: 50.0% (48 problems)
- **discrepancy**: 50.0% (16 problems)
- **factorials**: 47.6% (21 problems)
- **covering systems**: 47.4% (19 problems)
- **polynomials**: 44.4% (18 problems)
- **hypergraphs**: 44.4% (27 problems)
- **probability**: 44.4% (9 problems)
- **graph theory**: 44.1% (270 problems)
- **additive combinatorics**: 43.3% (90 problems)
- **divisors**: 43.3% (30 problems)
- **convex**: 41.7% (12 problems)

## 2. Prerequisite Chains (OEIS-linked)

- **#12**: depends on [#8, #26, #27] via N/A
- **#15**: depends on [#8, #26, #27] via N/A
- **#25**: depends on [#8, #26, #27] via N/A
- **#28** ($500): depends on [#8, #26, #27] via N/A
- **#32**: depends on [#8, #26, #27] via N/A
- **#33**: depends on [#8, #26, #27] via N/A
- **#38**: depends on [#8, #26, #27] via N/A
- **#39** ($500): depends on [#8, #26, #27] via N/A
- **#40** ($500): depends on [#8, #26, #27] via N/A
- **#41** ($500): depends on [#8, #26, #27] via N/A

## 3. Near-Miss Problems

### Falsifiable (31 problems)
- #11: additive basis, number theory
- #23: graph theory
- #64 $1000: cycles, graph theory
- #85: graph theory
- #97 $100: convex, distances, geometry
- #106: geometry
- #107 $500: convex, geometry — 'Happy Ending' problem
- #128 $250: graph theory

### Verifiable (7 problems)
- #7: covering systems, number theory
- #307: number theory, unit fractions
- #364: number theory
- #366: number theory
- #647 $32: number theory
- #672: number theory
- #835: graph theory, hypergraphs

### Decidable (8 problems)
- #19 $500: chromatic number, graph theory
- #506: geometry
- #547: graph theory, ramsey theory
- #551: graph theory, ramsey theory
- #556: graph theory, ramsey theory
- #580: graph theory
- #742: graph theory
- #848: number theory

Lean-verified techniques cover: number theory, unit fractions, additive combinatorics, additive basis, analysis, ramsey theory, geometry, factorials

## 4. Prize Portfolio (Optimal Research Investment)

Total available prize money: **$37935**
Total expected value: **$12742**

| Problem | Prize | P(solve) | Similar Solved | Expected Value |
|---------|-------|----------|---------------|----------------|
| #142 | $10000 | 35.2% | 42 | $3439 |
| #3 | $5000 | 34.3% | 215 | $1708 |
| #710 | $2000 | 32.5% | 190 | $647 |
| #20 (sunflower conjecture) | $1000 | 43.4% | 25 | $417 |
| #625 | $1000 | 36.1% | 120 | $358 |
| #687 | $1000 | 32.5% | 190 | $324 |
| #711 | $1000 | 32.5% | 190 | $324 |
| #30 | $1000 | 32.2% | 214 | $321 |
| #592 | $1000 | 31.1% | 43 | $304 |
| #161 | $500 | 39.3% | 72 | $194 |
| #564 | $500 | 36.3% | 141 | $180 |
| #138 | $500 | 36.7% | 39 | $179 |
| #74 | $500 | 35.9% | 120 | $178 |
| #500 | $500 | 35.3% | 124 | $175 |
| #712 | $500 | 35.3% | 124 | $175 |

## 5. Breakthrough Cascade Simulations

What happens if we solve these problems?

### #592 ($1000)
- Tags: ramsey theory, set theory
- OEIS connections: 589
- Problems potentially unlocked: **275**
- Unlocked: #12, #15, #25, #28, #32
- Biggest tag boost: set theory +0.042

### #625 ($1000)
- Tags: chromatic number, graph theory
- OEIS connections: 589
- Problems potentially unlocked: **275**
- Unlocked: #12, #15, #25, #28, #32
- Biggest tag boost: chromatic number +0.018

### #711 ($1000)
- Tags: number theory
- OEIS connections: 301
- Problems potentially unlocked: **196**
- Unlocked: #14, #36, #43, #60, #81
- Biggest tag boost: number theory +0.002

### #30 ($1000)
- Tags: additive combinatorics, number theory, sidon sets
- OEIS connections: 5
- Problems potentially unlocked: **4**
- Unlocked: #14, #43, #155, #530
- Biggest tag boost: sidon sets +0.036

### #142 ($10000)
- Tags: additive combinatorics, arithmetic progressions
- OEIS connections: 4
- Problems potentially unlocked: **2**
- Unlocked: #3, #201
- Biggest tag boost: arithmetic progressions +0.042

### #3 ($5000)
- Tags: additive combinatorics, arithmetic progressions, number theory
- OEIS connections: 4
- Problems potentially unlocked: **2**
- Unlocked: #142, #201
- Biggest tag boost: arithmetic progressions +0.042

### #687 ($1000)
- Tags: number theory
- OEIS connections: 1
- Problems potentially unlocked: **1**
- Unlocked: #854
- Biggest tag boost: number theory +0.002

### #710 ($2000)
- Tags: number theory
- OEIS connections: 0
- Problems potentially unlocked: **0**
- Biggest tag boost: number theory +0.002

## 6. Detailed Attack Plans

### #883
- **Risk**: low (vulnerability=0.710)
- **Tags**: graph theory, number theory
- **Formalized**: no
- **OEIS sequences**: 1

  **Approach angles:**
  - graph theory: moderate (44.1% success)
  - number theory: moderate (35.1% success)

  **Study these solved problems:**
  - #13 (proved, overlap=50%, shared: number theory)
  - #22 (proved, overlap=50%, shared: graph theory)
  - #24 (proved, overlap=50%, shared: graph theory)
  - #34 (disproved, overlap=50%, shared: number theory)
  - #48 (proved, overlap=50%, shared: number theory)

### #108
- **Risk**: low (vulnerability=0.689)
- **Tags**: chromatic number, cycles, graph theory
- **Formalized**: yes
- **OEIS sequences**: 1

  **Approach angles:**
  - graph theory: moderate (44.1% success)
  - cycles: moderate (40.9% success)
  - chromatic number: moderate (40.4% success)

  **Study these solved problems:**
  - #57 (proved, overlap=100%, shared: chromatic number, cycles, graph theory)
  - #58 (proved, overlap=100%, shared: chromatic number, cycles, graph theory)
  - #63 (proved, overlap=100%, shared: chromatic number, cycles, graph theory)
  - #921 (proved, overlap=100%, shared: chromatic number, cycles, graph theory)
  - #71 (proved, overlap=67%, shared: cycles, graph theory)

### #626
- **Risk**: low (vulnerability=0.689)
- **Tags**: chromatic number, cycles, graph theory
- **Formalized**: no
- **OEIS sequences**: 1

  **Approach angles:**
  - graph theory: moderate (44.1% success)
  - cycles: moderate (40.9% success)
  - chromatic number: moderate (40.4% success)

  **Study these solved problems:**
  - #57 (proved, overlap=100%, shared: chromatic number, cycles, graph theory)
  - #58 (proved, overlap=100%, shared: chromatic number, cycles, graph theory)
  - #63 (proved, overlap=100%, shared: chromatic number, cycles, graph theory)
  - #921 (proved, overlap=100%, shared: chromatic number, cycles, graph theory)
  - #71 (proved, overlap=67%, shared: cycles, graph theory)

### #531
- **Risk**: low (vulnerability=0.677)
- **Tags**: number theory, ramsey theory
- **Formalized**: no
- **OEIS sequences**: 1

  **Approach angles:**
  - ramsey theory: moderate (39.2% success)
  - number theory: moderate (35.1% success)

  **Study these solved problems:**
  - #54 (solved, overlap=100%, shared: number theory, ramsey theory)
  - #55 (solved, overlap=100%, shared: number theory, ramsey theory)
  - #439 (proved, overlap=100%, shared: number theory, ramsey theory)
  - #532 (proved, overlap=100%, shared: number theory, ramsey theory)
  - #894 (proved, overlap=100%, shared: number theory, ramsey theory)

### #948
- **Risk**: low (vulnerability=0.677)
- **Tags**: number theory, ramsey theory
- **Formalized**: no
- **OEIS sequences**: 1

  **Approach angles:**
  - ramsey theory: moderate (39.2% success)
  - number theory: moderate (35.1% success)

  **Study these solved problems:**
  - #54 (solved, overlap=100%, shared: number theory, ramsey theory)
  - #55 (solved, overlap=100%, shared: number theory, ramsey theory)
  - #439 (proved, overlap=100%, shared: number theory, ramsey theory)
  - #532 (proved, overlap=100%, shared: number theory, ramsey theory)
  - #894 (proved, overlap=100%, shared: number theory, ramsey theory)

### #80
- **Risk**: low (vulnerability=0.672)
- **Tags**: graph theory, ramsey theory
- **Formalized**: no
- **OEIS sequences**: 1

  **Approach angles:**
  - graph theory: moderate (44.1% success)
  - ramsey theory: moderate (39.2% success)

  **Study these solved problems:**
  - #76 (proved, overlap=100%, shared: graph theory, ramsey theory)
  - #79 (proved, overlap=100%, shared: graph theory, ramsey theory)
  - #88 (proved, overlap=100%, shared: graph theory, ramsey theory)
  - #163 (proved, overlap=100%, shared: graph theory, ramsey theory)
  - #166 (proved, overlap=100%, shared: graph theory, ramsey theory)

### #87
- **Risk**: low (vulnerability=0.672)
- **Tags**: graph theory, ramsey theory
- **Formalized**: no
- **OEIS sequences**: 2

  **Approach angles:**
  - graph theory: moderate (44.1% success)
  - ramsey theory: moderate (39.2% success)

  **Study these solved problems:**
  - #76 (proved, overlap=100%, shared: graph theory, ramsey theory)
  - #79 (proved, overlap=100%, shared: graph theory, ramsey theory)
  - #88 (proved, overlap=100%, shared: graph theory, ramsey theory)
  - #163 (proved, overlap=100%, shared: graph theory, ramsey theory)
  - #166 (proved, overlap=100%, shared: graph theory, ramsey theory)

### #112
- **Risk**: low (vulnerability=0.672)
- **Tags**: graph theory, ramsey theory
- **Formalized**: no
- **OEIS sequences**: 1

  **Approach angles:**
  - graph theory: moderate (44.1% success)
  - ramsey theory: moderate (39.2% success)

  **Study these solved problems:**
  - #76 (proved, overlap=100%, shared: graph theory, ramsey theory)
  - #79 (proved, overlap=100%, shared: graph theory, ramsey theory)
  - #88 (proved, overlap=100%, shared: graph theory, ramsey theory)
  - #163 (proved, overlap=100%, shared: graph theory, ramsey theory)
  - #166 (proved, overlap=100%, shared: graph theory, ramsey theory)
