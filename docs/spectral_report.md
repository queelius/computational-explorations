# Spectral Analysis of the Erdős Problem Network

Graph-theoretic deep analysis using spectral methods.

## 1. Laplacian Spectrum

- **Algebraic connectivity (λ₂)**: 0.0
- **Spectral gap (λ₂/λ_max)**: 0.0
- **Max eigenvalue**: 641.0
- **Zero eigenvalues (components)**: 38

First 10 eigenvalues: 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000

## 2. Spectral Bisection

- Side A: 162 problems
- Side B: 238 problems
- Cut weight: 28360.0 / 73340.0 (38.7%)

### Side A Profile
  - number theory: 85
  - graph theory: 33
  - geometry: 21
  - ramsey theory: 20
  - additive combinatorics: 16

### Side B Profile
  - number theory: 123
  - graph theory: 51
  - ramsey theory: 26
  - geometry: 22
  - primes: 18

## 3. Bridge Problems (Cross-Community Connectors)

Problems that connect otherwise-disconnected research areas.

| Rank | Problem | Bridge Score | Fiedler | Degree | Cross% | Tags |
|------|---------|-------------|---------|--------|--------|------|
| 1 | #70 | 645.2 | -0.0 | 633 | 25% | graph theory, ramsey theory |
| 2 | #596 | 645.2 | -0.0 | 633 | 25% | graph theory, ramsey theory |
| 3 | #597 | 645.2 | 0.0 | 633 | 24% | graph theory, ramsey theory |
| 4 | #563 | 644.25 | -0.0 | 627 | 25% | graph theory, hypergraphs |
| 5 | #80 | 642.0 | 0.0 | 613 | 24% | graph theory, ramsey theory |
| 6 | #550 | 642.0 | -0.0 | 613 | 25% | graph theory, ramsey theory |
| 7 | #557 | 642.0 | -0.0 | 613 | 25% | graph theory, ramsey theory |
| 8 | #561 | 642.0 | -0.0 | 613 | 25% | graph theory, ramsey theory |
| 9 | #566 | 642.0 | -0.0 | 613 | 25% | graph theory, ramsey theory |
| 10 | #567 | 642.0 | -0.0 | 613 | 25% | graph theory, ramsey theory |
| 11 | #568 | 642.0 | -0.0 | 613 | 25% | graph theory, ramsey theory |
| 12 | #569 | 642.0 | -0.0 | 613 | 25% | graph theory, ramsey theory |
| 13 | #638 | 642.0 | -0.0 | 613 | 25% | graph theory, ramsey theory |
| 14 | #667 | 642.0 | -0.0 | 613 | 25% | graph theory, ramsey theory |
| 15 | #685 | 642.0 | -0.0 | 613 | 24% | binomial coefficients, number theory |

## 4. PageRank Influence

- PageRank-degree correlation: 0.894
- Gini coefficient: 0.2097
  (0 = uniform influence, 1 = concentrated in few problems)

| Rank | Problem | PageRank | Degree | Tags | Prize |
|------|---------|----------|--------|------|-------|
| 1 | #683 | 0.003873 | 400 | binomial coefficients, number theory | - |
| 2 | #201 | 0.003728 | 375 | additive combinatorics, arithmetic progressions | - |
| 3 | #43 | 0.003723 | 412 | additive combinatorics, number theory | $100 |
| 4 | #685 | 0.003660 | 613 | binomial coefficients, number theory | - |
| 5 | #404 | 0.003575 | 561 | factorials, number theory | - |
| 6 | #39 | 0.003560 | 604 | additive combinatorics, number theory | $500 |
| 7 | #41 | 0.003560 | 604 | additive combinatorics, number theory | $500 |
| 8 | #42 | 0.003560 | 604 | additive combinatorics, number theory | - |
| 9 | #44 | 0.003560 | 604 | additive combinatorics, number theory | - |
| 10 | #14 | 0.003547 | 400 | additive combinatorics, number theory | - |
| 11 | #563 | 0.003516 | 627 | graph theory, hypergraphs | - |
| 12 | #684 | 0.003514 | 397 | binomial coefficients, number theory | - |
| 13 | #70 | 0.003496 | 633 | graph theory, ramsey theory | - |
| 14 | #596 | 0.003496 | 633 | graph theory, ramsey theory | - |
| 15 | #597 | 0.003496 | 633 | graph theory, ramsey theory | - |

## 5. Spectral Communities

- Communities found: 5
- Modularity: 0.0309

### Eigenvalue Gaps (community count signal)

Large gaps indicate natural community boundaries:
  λ1→λ2: gap = 0.000
  λ2→λ3: gap = 0.000
  λ3→λ4: gap = 0.000
  λ4→λ5: gap = 0.000
  λ5→λ6: gap = 0.000
  λ6→λ7: gap = 0.000
  λ7→λ8: gap = 0.000
  λ8→λ9: gap = 0.000
  λ9→λ10: gap = 0.000
  λ10→λ11: gap = 0.000

### Community 2 (96 problems)
- Density: 0.510
- Total prize: $7000
- Dominant tags: number theory(44), graph theory(22), ramsey theory(13)
- Examples: #9, #12, #18, #20, #30

### Community 1 (83 problems)
- Density: 0.258
- Total prize: $4300
- Dominant tags: number theory(49), graph theory(14), geometry(9)
- Examples: #1, #5, #36, #38, #51

### Community 4 (79 problems)
- Density: 0.406
- Total prize: $2100
- Dominant tags: number theory(43), graph theory(20), ramsey theory(12)
- Examples: #10, #15, #33, #40, #42

### Community 0 (72 problems)
- Density: 0.385
- Total prize: $5200
- Dominant tags: number theory(41), graph theory(11), geometry(9)
- Examples: #14, #17, #25, #28, #32

### Community 3 (70 problems)
- Density: 0.200
- Total prize: $18200
- Dominant tags: number theory(31), graph theory(17), geometry(10)
- Examples: #3, #50, #75, #77, #86
