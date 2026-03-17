# Quantifying Mathematical Interestingness

## The Meta-Problem

What makes a mathematical problem 'interesting'? We decompose this into
five orthogonal dimensions: **depth**, **difficulty**, **surprise potential**,
**fertility**, and **community investment**. We score all 1,183 Erdos problems
and identify hidden gems -- problems with high intrinsic interest but low attention.

Total problems analyzed: 1183

## Top 20 Most Interesting Problems

| Rank | # | Score | Depth | Diff | Surprise | Fertility | Invest | Tags |
|------|---|-------|-------|------|----------|-----------|--------|------|
| 1 | 3 | 0.700 | 0.64 | 0.63 | 0.79 | 0.80 | 0.76 | additive combinatorics, arithmetic progressions, number theory |
| 2 | 30 | 0.629 | 0.64 | 0.60 | 0.47 | 0.68 | 0.74 | additive combinatorics, number theory, sidon sets |
| 3 | 142 | 0.602 | 0.31 | 0.65 | 0.31 | 0.80 | 0.76 | additive combinatorics, arithmetic progressions |
| 4 | 139 | 0.557 | 0.31 | 0.36 | 0.39 | 0.80 | 0.76 | additive combinatorics, arithmetic progressions |
| 5 | 43 | 0.551 | 0.64 | 0.54 | 0.47 | 0.68 | 0.41 | additive combinatorics, number theory, sidon sets |
| 6 | 39 | 0.540 | 0.42 | 0.58 | 0.47 | 0.40 | 0.67 | additive combinatorics, number theory, sidon sets |
| 7 | 41 | 0.540 | 0.42 | 0.58 | 0.47 | 0.40 | 0.67 | additive combinatorics, number theory, sidon sets |
| 8 | 1 | 0.527 | 0.36 | 0.57 | 0.45 | 0.38 | 0.67 | additive combinatorics, number theory |
| 9 | 219 | 0.517 | 0.61 | 0.21 | 0.96 | 0.54 | 0.61 | additive combinatorics, arithmetic progressions, number theory |
| 10 | 4 | 0.516 | 0.11 | 0.43 | 0.56 | 0.32 | 1.00 | number theory, primes |
| 11 | 564 | 0.515 | 0.42 | 0.56 | 0.55 | 0.24 | 0.67 | graph theory, hypergraphs, ramsey theory |
| 12 | 593 | 0.501 | 0.50 | 0.58 | 0.76 | 0.26 | 0.33 | chromatic number, graph theory, hypergraphs |
| 13 | 74 | 0.487 | 0.17 | 0.56 | 0.44 | 0.29 | 0.67 | chromatic number, cycles, graph theory |
| 14 | 77 | 0.485 | 0.53 | 0.54 | 0.41 | 0.39 | 0.38 | graph theory, ramsey theory |
| 15 | 28 | 0.483 | 0.08 | 0.57 | 0.40 | 0.34 | 0.67 | additive basis, number theory |
| 16 | 40 | 0.482 | 0.08 | 0.57 | 0.40 | 0.34 | 0.67 | additive basis, number theory |
| 17 | 592 | 0.482 | 0.33 | 0.61 | 0.27 | 0.22 | 0.67 | ramsey theory, set theory |
| 18 | 66 | 0.482 | 0.08 | 0.57 | 0.40 | 0.34 | 0.67 | additive basis, number theory |
| 19 | 89 | 0.478 | 0.17 | 0.58 | 0.29 | 0.26 | 0.67 | distances, geometry |
| 20 | 14 | 0.477 | 0.58 | 0.41 | 0.47 | 0.53 | 0.39 | additive combinatorics, number theory, sidon sets |

## Hidden Gems: High Intrinsic Interest, Low Attention

These problems score high on depth/surprise/fertility but have no prize,
no formalization, and few OEIS connections.

| Rank | # | Gem Score | Intrinsic | Investment | Status | Tags |
|------|---|-----------|-----------|------------|--------|------|
| 1 | 883 | 0.477 | 0.477 | 0.000 | open | graph theory, number theory |
| 2 | 337 | 0.474 | 0.474 | 0.000 | disproved (Lean) | additive basis, additive combinatorics, number theory |
| 3 | 704 | 0.467 | 0.467 | 0.000 | open | chromatic number, geometry, graph theory |
| 4 | 966 | 0.453 | 0.453 | 0.000 | proved (Lean) | additive combinatorics, number theory, ramsey theory |
| 5 | 483 | 0.449 | 0.449 | 0.000 | open | additive combinatorics, number theory, ramsey theory |
| 6 | 769 | 0.448 | 0.448 | 0.000 | open | geometry, number theory |
| 7 | 967 | 0.437 | 0.437 | 0.000 | disproved (Lean) | analysis, number theory |
| 8 | 772 | 0.435 | 0.435 | 0.000 | proved | additive combinatorics, number theory, sidon sets |
| 9 | 864 | 0.431 | 0.431 | 0.000 | open | additive combinatorics, number theory, sidon sets |
| 10 | 986 | 0.428 | 0.485 | 0.057 | open | graph theory, ramsey theory |
| 11 | 1030 | 0.428 | 0.485 | 0.057 | open | graph theory, ramsey theory |
| 12 | 484 | 0.428 | 0.428 | 0.000 | proved | additive combinatorics, number theory, ramsey theory |
| 13 | 863 | 0.424 | 0.424 | 0.000 | open | additive combinatorics, number theory, sidon sets |
| 14 | 1127 | 0.423 | 0.423 | 0.000 | independent | distances, geometry, set theory |
| 15 | 279 | 0.422 | 0.422 | 0.000 | open | covering systems, number theory, primes |

## Feature Importance (Learned Model)

- **is_formalized**: 0.1555
- **prize_log**: 0.0869
- **has_prize**: 0.0805
- **unsolved_despite_age**: 0.0293
- **formalization_momentum**: 0.0281
- **catalogue_position**: 0.0265
- **solve_rate_anomaly**: 0.0211
- **n_oeis**: 0.0200
- **cascade_potential**: 0.0117
- **cross_domain**: 0.0064

## Tag Interestingness Rankings

| Tag | N | Avg Score | Depth | Difficulty | Surprise | Fertility |
|-----|---|-----------|-------|------------|----------|-----------|
| base representations | 5 | 0.412 | 0.13 | 0.45 | 0.41 | 0.48 |
| sidon sets | 28 | 0.401 | 0.26 | 0.42 | 0.45 | 0.40 |
| arithmetic progressions | 24 | 0.393 | 0.16 | 0.36 | 0.45 | 0.54 |
| powers | 4 | 0.372 | 0.10 | 0.45 | 0.35 | 0.40 |
| additive combinatorics | 92 | 0.369 | 0.22 | 0.36 | 0.45 | 0.42 |
| powerful | 2 | 0.369 | 0.17 | 0.38 | 0.57 | 0.33 |
| iterated functions | 9 | 0.368 | 0.12 | 0.41 | 0.37 | 0.36 |
| primes | 55 | 0.368 | 0.14 | 0.39 | 0.44 | 0.34 |
| algebra | 1 | 0.365 | 0.00 | 0.61 | 0.33 | 0.15 |
| irrationality | 22 | 0.359 | 0.04 | 0.35 | 0.32 | 0.50 |
| squares | 4 | 0.356 | 0.20 | 0.37 | 0.54 | 0.27 |
| set theory | 35 | 0.356 | 0.32 | 0.43 | 0.44 | 0.23 |
| additive basis | 29 | 0.356 | 0.11 | 0.36 | 0.47 | 0.35 |
| binomial coefficients | 22 | 0.352 | 0.13 | 0.37 | 0.43 | 0.33 |
| ramsey theory | 110 | 0.351 | 0.36 | 0.37 | 0.46 | 0.26 |

## Dimension Correlations

- depth_vs_difficulty: r = 0.115
- depth_vs_surprise: r = 0.504
- depth_vs_fertility: r = 0.317
- depth_vs_investment: r = 0.066
- difficulty_vs_surprise: r = -0.269
- difficulty_vs_fertility: r = 0.112
- difficulty_vs_investment: r = 0.265
- surprise_vs_fertility: r = 0.230
- surprise_vs_investment: r = 0.015
- fertility_vs_investment: r = 0.239

## What Predicts Solvability?

- unsolved_despite_age: -0.493
- is_formalized: -0.258
- solve_rate_anomaly: +0.254
- oeis_investment: +0.133
- formalization_momentum: -0.062
- inv_tag_solve_rate: -0.039
- tag_entropy: -0.033
- n_oeis: -0.027

## What Predicts Cross-Field Connectivity?

- cross_domain: +1.000
- n_tags: +0.234
- tag_entropy: +0.196
- is_formalized: -0.144
- resolution_velocity: +0.127
- isolation_score: +0.113
- has_prize: +0.095
- formalization_momentum: -0.091

## What Predicts Theory Generation?

- is_formalized: +0.911
- formalization_momentum: +0.142
- catalogue_position: -0.093
- oeis_investment: +0.072
- has_prize: +0.067
- solve_rate_anomaly: +0.050
- prize_log: +0.045
- n_oeis: +0.042
