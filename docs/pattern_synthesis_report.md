# Pattern Synthesis: Meta-Patterns Across Analyses

Analyzing 1135 problems across 9 signal dimensions.
Discovered **8 problem archetypes**.

## 1. Problem Archetypes

| ID | Size | Solve Rate | Open | Prize | Top Tags | Representative |
|----|------|------------|------|-------|----------|----------------|
| 7 | 303 | 100% | 0 | $38 | graph theory, number theory, analysis | #622 |
| 0 | 197 | 9% | 164 | $50 | graph theory, number theory, ramsey theory | #579 |
| 6 | 165 | 28% | 110 | - | number theory, primes, unit fractions | #478 |
| 4 | 132 | 0% | 119 | $150 | number theory, graph theory, geometry | #742 |
| 5 | 125 | 19% | 97 | $10 | number theory, additive combinatorics, unit fractions | #508 |
| 1 | 111 | 19% | 86 | $67 | number theory | #695 |
| 2 | 93 | 34% | 54 | $60232 | number theory, graph theory, ramsey theory | #165 |
| 3 | 9 | 22% | 6 | - | number theory, additive combinatorics, squares | #242 |

### Centroid Profiles

**Archetype 7** (303 problems, 100% solved)
  is_solved            +1.000 ████████████████████
  problem_age          +0.444 ████████
  tag_solve_rate       +0.423 ████████
  tag_popularity       +0.409 ████████
  tag_diversity        +0.370 ███████
  formalized           +0.020 
  oeis_exclusivity     +0.003 
  prize_signal         +0.002 
  oeis_richness        +0.001 

**Archetype 0** (197 problems, 9% solved)
  tag_diversity        +0.548 ██████████
  problem_age          +0.473 █████████
  tag_solve_rate       +0.393 ███████
  tag_popularity       +0.296 █████
  is_solved            +0.091 █
  oeis_richness        +0.005 
  prize_signal         +0.002 
  formalized           +0.000 
  oeis_exclusivity     -0.000 

**Archetype 6** (165 problems, 28% solved)
  oeis_exclusivity     +0.994 ███████████████████
  problem_age          +0.579 ███████████
  tag_popularity       +0.523 ██████████
  tag_diversity        +0.450 █████████
  formalized           +0.358 ███████
  tag_solve_rate       +0.355 ███████
  is_solved            +0.279 █████
  oeis_richness        +0.164 ███
  prize_signal         +0.000 

**Archetype 4** (132 problems, 0% solved)
  tag_popularity       +0.580 ███████████
  tag_solve_rate       +0.402 ████████
  problem_age          +0.386 ███████
  tag_diversity        +0.250 ████
  prize_signal         +0.009 
  is_solved            +0.000 
  formalized           +0.000 
  oeis_richness        -0.000 
  oeis_exclusivity     -0.000 

**Archetype 5** (125 problems, 19% solved)
  formalized           +1.000 ███████████████████
  problem_age          +0.590 ███████████
  tag_diversity        +0.460 █████████
  tag_solve_rate       +0.372 ███████
  tag_popularity       +0.338 ██████
  is_solved            +0.192 ███
  prize_signal         +0.002 
  oeis_richness        +0.001 
  oeis_exclusivity     +0.000 

## 2. Open Problems Most Similar to Solved Ones

| Problem | Distance | Nearest Solved | Shared Tags | Prize |
|---------|----------|----------------|-------------|-------|
| #32 | 2.05 | #31 | additive basis, number theory | - |
| #68 | 2.05 | #69 | irrationality, number theory | - |
| #80 | 2.05 | #79 | graph theory, ramsey theory | - |
| #114 | 2.05 | #115 | analysis, polynomials | - |
| #146 | 2.05 | #147 | graph theory, turan number | $500 |
| #149 | 2.05 | #150 | graph theory | - |
| #151 | 2.05 | #150 | graph theory | - |
| #165 | 2.05 | #166 | graph theory, ramsey theory | $250 |
| #188 | 2.05 | #189 | geometry, ramsey theory | - |
| #195 | 2.05 | #194 | arithmetic progressions | - |
| #249 | 2.05 | #250 | irrationality, number theory | - |
| #251 | 2.05 | #250 | irrationality, number theory | - |
| #263 | 2.05 | #262 | irrationality | - |
| #267 | 2.05 | #266 | irrationality | - |
| #278 | 2.05 | #277 | covering systems, number theory | - |

## 3. Analytical Blindspots (Undervalued Problems)

**27 problems** have high importance indicators but
score low on tractability dimensions.

| Problem | Importance | Tractability | Gap | Tags | Prize |
|---------|------------|-------------|-----|------|-------|
| #687 | 0.67 | 0.30 | 0.37 | number theory | $1000 |
| #710 | 0.65 | 0.30 | 0.35 | number theory | $2000 |
| #479 | 0.62 | 0.30 | 0.32 | number theory | - |
| #1135 | 0.60 | 0.30 | 0.30 | number theory | $500 |
| #711 | 0.58 | 0.30 | 0.28 | number theory | $1000 |
| #825 | 0.53 | 0.30 | 0.23 | number theory | $25 |
| #50 | 0.53 | 0.30 | 0.23 | number theory | $250 |
| #123 | 0.53 | 0.30 | 0.23 | number theory | $250 |
| #126 | 0.53 | 0.30 | 0.23 | number theory | $250 |
| #708 | 0.50 | 0.30 | 0.20 | number theory | $100 |
| #374 | 0.50 | 0.30 | 0.20 | number theory | - |
| #380 | 0.50 | 0.30 | 0.20 | number theory | - |
| #1052 | 0.46 | 0.30 | 0.16 | number theory | $10 |
| #365 | 0.46 | 0.30 | 0.16 | number theory | - |
| #985 | 0.46 | 0.30 | 0.16 | number theory | - |

## 4. Tag-Archetype Mapping

Tags concentrated in a single archetype:

| Tag | Primary Archetype | Concentration | Count |
|-----|-------------------|---------------|-------|
| iterated functions | 6 | 78% | 9 |
| squares | 6 | 75% | 4 |
| diophantine approximation | 7 | 71% | 7 |
| planar graphs | 7 | 67% | 3 |
| complete sequences | 5 | 62% | 8 |
| base representations | 6 | 60% | 5 |
| cycles | 0 | 59% | 22 |
| polynomials | 0 | 56% | 18 |
| probability | 0 | 56% | 9 |
| primes | 6 | 55% | 49 |
| chromatic number | 0 | 53% | 57 |
| hypergraphs | 0 | 52% | 27 |
| group theory | 0 | 50% | 4 |
| powers | 5 | 50% | 4 |
| factorials | 6 | 48% | 21 |

## 5. Prize Efficiency by Archetype

| Archetype | Size | Rate | Open | Prize | Efficiency | Tags |
|-----------|------|------|------|-------|------------|------|
| 2 | 93 | 34% | 54 | $60232 | 987.4 | number theory, graph theory, ramsey theory |
| 4 | 132 | 0% | 119 | $150 | 1.1 | number theory, graph theory, geometry |
| 1 | 111 | 19% | 86 | $67 | 0.7 | number theory |
| 0 | 197 | 9% | 164 | $50 | 0.3 | graph theory, number theory, ramsey theory |
| 5 | 125 | 19% | 97 | $10 | 0.1 | number theory, additive combinatorics, unit fractions |
| 7 | 303 | 100% | 0 | $38 | 0.0 | graph theory, number theory, analysis |
| 6 | 165 | 28% | 110 | - | 0.0 | number theory, primes, unit fractions |
| 3 | 9 | 22% | 6 | - | 0.0 | number theory, additive combinatorics, squares |
