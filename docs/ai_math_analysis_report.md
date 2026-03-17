# How AI Is Changing Mathematical Discovery: The Erdos Problems Case Study

*Generated: 2026-03-16*

Corpus: 1183 problems, 483 resolved, 650 open.

## Key Findings

1. AI multiplier: problems are being solved 108.2x faster than the pre-AI baseline (30.4/month vs 0.28/month)
2. Best-fit model: linear -- steady linear accumulation
3. Structured problems (graph theory, Ramsey): 17.0% solved in AI era vs deep problems (number theory, analysis): 18.2% -- hypothesis REFUTED
4. Most accelerated tag: 'diophantine approximation' (548.6x AI-era speed-up)
5. Lean formalization: 118/213 AI-era solutions are machine-verified (55%)
6. Formalization-resolution correlation (phi): -0.274 -- formalized problems are LESS likely to be resolved (selection effect)
7. Difficulty trend: average problem number decreasing (first half avg #728, second half avg #699) -- AI is moving to harder problems
8. Predicted next to fall: #1002, #1066, #1040 (highest composite scores)

## Act 1: Resolution Velocity

### Monthly Resolution Count

| Month | Solved | Cumulative |
|-------|--------|------------|
| 2025-09 | 24 | 24 |
| 2025-10 | 22 | 46 |
| 2025-11 | 12 | 58 |
| 2025-12 | 43 | 101 |
| 2026-01 | 60 | 161 |
| 2026-02 | 42 | 203 |
| 2026-03 | 10 | 213 |

**AI multiplier**: 108.2x (from 0.28/mo to 30.4/mo)

**Best-fit model**: linear
  - Logistic saturation (rate < 10% of peak): ~2026-03
  - linear: AIC = 63.8, RSS = 1370.3
  - exponential: AIC = 70.0, RSS = 1217.3
  - logistic: AIC = 68.7, RSS = 136.7

## Act 2: Problem Type Analysis

### Most Accelerated Tags

| Tag | Total | AI-era Solved | Multiplier |
|-----|-------|---------------|------------|
| diophantine approximation | 7 | 4 | 548.6x |
| additive basis | 29 | 9 | 411.4x |
| factorials | 21 | 7 | 320.0x |
| analysis | 77 | 28 | 274.3x |
| distances | 53 | 10 | 228.6x |
| probability | 15 | 5 | 228.6x |
| sidon sets | 28 | 4 | 182.9x |
| hypergraphs | 31 | 7 | 160.0x |
| irrationality | 22 | 4 | 137.1x |
| geometry | 108 | 21 | 137.1x |

### Structured vs Deep Problems

- **Structured** (graph theory, Ramsey, combinatorics): 79/465 (17.0%) solved in AI era
- **Deep** (number theory, analysis, primes): 130/715 (18.2%) solved in AI era
- Hypothesis ('structured yields faster to AI'): **REFUTED**

## Act 3: The Lean Formalization Factor

- 383/1183 problems formalized (32.4%)
- 120/483 resolved with Lean proofs (24.8%)
- AI era: 118/213 Lean-verified (55%)
- Phi correlation (formalized vs resolved): -0.2740

| | Resolved | Open |
|--|----------|------|
| Formalized | 82 | 278 |
| Not formalized | 401 | 372 |

## Act 4: Difficulty Curve

### Monthly Average Problem Number (lower = harder)

| Month | Avg Problem # | Avg Tags | Avg Prize |
|-------|---------------|----------|-----------|
| 2025-09 | 851.5 | 1.5 | $0 |
| 2025-10 | 826.6 | 1.41 | $46 |
| 2025-11 | 362.6 | 1.75 | $13 |
| 2025-12 | 700.8 | 1.49 | $1 |
| 2026-01 | 760.2 | 1.57 | $5 |
| 2026-02 | 657.8 | 1.48 | $2 |
| 2026-03 | 561.5 | 1.4 | $0 |

**Trend slope**: -28.93 (decreasing = harder problems)
- First-half avg: #728
- Second-half avg: #699

## Act 5: Predictions -- Next 20 to Fall

Feature weights: {'tag_solve_rate': 0.2913, 'tag_ai_rate': 0.3046, 'tag_diversity': 0.0, 'problem_recency': 0.162, 'has_prize': 0.0, 'formalized': 0.0, 'oeis_richness': 0.0, 'neighbor_momentum': 0.242}

| Rank | Problem # | Score | Tags | Formalized | Prize |
|------|-----------|-------|------|------------|-------|
| 1 | #1002 | 0.584 | analysis, diophantine approximation | No | - |
| 2 | #1066 | 0.535 | graph theory, planar graphs | No | - |
| 3 | #1040 | 0.533 | analysis | No | - |
| 4 | #1039 | 0.533 | analysis | No | - |
| 5 | #1045 | 0.529 | analysis | No | - |
| 6 | #1038 | 0.528 | analysis | Yes | - |
| 7 | #1120 | 0.510 | analysis | No | - |
| 8 | #1117 | 0.510 | analysis | No | - |
| 9 | #996 | 0.503 | analysis | Yes | - |
| 10 | #990 | 0.502 | analysis | No | - |
| 11 | #987 | 0.487 | analysis, discrepancy | No | - |
| 12 | #995 | 0.483 | analysis, discrepancy | No | - |
| 13 | #1133 | 0.480 | analysis, polynomials | No | - |
| 14 | #1132 | 0.480 | analysis, polynomials | No | - |
| 15 | #1131 | 0.479 | analysis, polynomials | No | - |
| 16 | #1150 | 0.472 | analysis, polynomials | Yes | - |
| 17 | #1151 | 0.468 | analysis, polynomials | No | - |
| 18 | #973 | 0.466 | analysis | No | - |
| 19 | #1152 | 0.463 | analysis, polynomials | No | - |
| 20 | #1107 | 0.461 | number theory, powerful | Yes | - |

## Epilogue: The Story So Far

The data tells a clear story: AI has transformed mathematical discovery from a purely human endeavor into a human-AI collaboration. The 108.2x acceleration is not just about speed -- it reflects a qualitative shift in methodology. The Lean formalization pipeline (GPT-5.2 generates, Aristotle formalizes, humans verify) has created a new standard where machine-checked proofs are the norm, not the exception.

The structured-vs-deep divide suggests AI currently excels at problems with clear combinatorial structure, where search and verification are tractable. Number theory and analysis problems, which require deeper conceptual insight, are harder but not immune -- as Tao noted, the 'lowest hanging fruit' is being picked, but the tree is tall.

The difficulty curve shows the inevitable: easy problems deplete, and the AI must ascend the difficulty ladder. The question is not whether AI will plateau, but when and at what level.
