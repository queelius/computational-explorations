# Temporal Evolution Analysis

How the character of Erdős problems changes across
problem number space (proxy for chronological ordering).

## 1. Problem Epochs

| Epoch | Solve Rate | Open Rate | Formalized | Prize $ | Tags/Prob | Dominant Tag |
|-------|-----------|-----------|-----------|---------|----------|--------------|
| 1-100 | 41.0% | 52.0% | 38.0% | $28842 | 2.0 | number theory |
| 101-200 | 35.0% | 60.0% | 29.0% | $17550 | 1.6 | graph theory |
| 201-300 | 52.0% | 46.0% | 41.0% | $700 | 1.6 | number theory |
| 301-400 | 33.0% | 62.0% | 48.0% | $0 | 1.7 | number theory |
| 401-500 | 48.0% | 49.0% | 31.0% | $625 | 1.5 | number theory |
| 501-600 | 33.0% | 59.0% | 20.0% | $2950 | 1.8 | graph theory |
| 601-700 | 32.0% | 63.0% | 15.0% | $3632 | 1.6 | number theory |
| 701-800 | 49.0% | 45.0% | 11.0% | $5450 | 1.6 | graph theory |
| 801-900 | 34.0% | 63.0% | 22.0% | $25 | 1.6 | number theory |
| 901-1000 | 39.0% | 59.0% | 26.0% | $0 | 1.4 | number theory |
| 1001-1100 | 39.0% | 57.0% | 30.0% | $110 | 1.4 | graph theory |
| 1101-1135 | 31.4% | 60.0% | 17.1% | $663 | 1.5 | analysis |

## 2. Tag Lifecycle Phases

### Declining Tags (peak in early problems)
- **additive basis**: peaked at #51 (27 problems)
- **intersecting family**: peaked at #51 (5 problems)
- **distances**: peaked at #101 (53 problems)
- **cycles**: peaked at #101 (22 problems)
- **geometry**: peaked at #101 (108 problems)

### Established Tags (persistent)
- **number theory**: 542 problems, solve rate 35.1%
- **graph theory**: 270 problems, solve rate 44.1%
- **ramsey theory**: 102 problems, solve rate 39.2%
- **analysis**: 72 problems, solve rate 52.8%
- **chromatic number**: 57 problems, solve rate 40.4%
- **combinatorics**: 44 problems, solve rate 56.8%
- **divisors**: 30 problems, solve rate 43.3%
- **hypergraphs**: 27 problems, solve rate 44.4%
- **set theory**: 24 problems, solve rate 25.0%
- **binomial coefficients**: 22 problems, solve rate 27.3%

## 3. Difficulty Gradient

- Trend: **stable** (slope=-0.000049)
- Difficulty cliff at problem #1051 (drop=0.180)
- Easiest region: around #226
- Hardest region: around #576

## 4. Status Landscape

### Golden Zones (>50% resolved)
- Around #251: 52.0% resolved

### Disproof Hotspots
- Around #801: 15.0% disproved
- Around #251: 13.0% disproved
- Around #201: 12.0% disproved

## 5. Tag Succession Patterns

### Strongest Successors (tag A → tag B)

- factorials → **number theory** (p=0.571, n=20)
- divisors → **number theory** (p=0.551, n=27)
- primitive sets → **number theory** (p=0.500, n=6)
- unit fractions → **number theory** (p=0.495, n=46)
- primes → **number theory** (p=0.483, n=42)
- additive basis → **number theory** (p=0.481, n=26)
- complete sequences → **number theory** (p=0.467, n=7)
- binomial coefficients → **number theory** (p=0.463, n=19)
- cycles → **graph theory** (p=0.462, n=18)
- turan number → **graph theory** (p=0.444, n=16)

### Most Clustered Tags (self-reinforcing)
- **number theory**: self-probability 0.525
- **irrationality**: self-probability 0.517
- **graph theory**: self-probability 0.464
- **analysis**: self-probability 0.457
- **unit fractions**: self-probability 0.441
- **diophantine approximation**: self-probability 0.417
- **complete sequences**: self-probability 0.400
- **geometry**: self-probability 0.389

## 6. Complexity Drift

- Tag complexity trend: stable or decreasing
- Most complex region: around #51
- Least complex region: around #1051

## 7. Named Problems

- Named: 61 problems, solve rate 29.5%
- Unnamed: 1074 problems, solve rate 39.9%
- Named formalization: 36.1% vs unnamed 27.5%

### Famous Problems

| # | Name | Status | Tags | Prize |
|---|------|--------|------|-------|
| #17 | cluster primes | open | number theory, primes | - |
| #18 | practical numbers | open | divisors, factorials | - |
| #20 | sunflower conjecture | open | combinatorics | $1000 |
| #36 | minimum overlap problem | open | additive combinatorics, number theory | - |
| #52 | sum-product problem | open | additive combinatorics, number theory | $250 |
| #67 | Erdős discrepancy problem | proved | discrepancy | $500 |
| #89 | Erdős distance problem | open | distances, geometry | $500 |
| #90 | unit distance problem | open | distances, geometry | $500 |
| #107 | 'Happy Ending' problem | falsifiable | convex, geometry | $500 |
| #109 | Erdős sumset conjecture | proved | additive combinatorics | - |
| #120 | Erdős similarity problem | open | combinatorics | $100 |
| #139 | Szemerédi's theorem | proved | additive combinatorics, arithmetic progressions | $1000 |
| #163 | Burr-Erdős conjecture | proved | graph theory, ramsey theory | - |
| #170 | sparse ruler problem | open | additive combinatorics | - |
| #171 | density Hales-Jewett | proved | additive combinatorics, combinatorics | - |
| #219 | Green-Tao theorem | proved | additive combinatorics, arithmetic progressions | - |
| #242 | Erdős-Straus conjecture | falsifiable | number theory, unit fractions | - |
| #271 | Stanley sequences | open | additive combinatorics, arithmetic progressions | - |
| #274 | Herzog-Schönheim conjecture | open | covering systems, group theory | - |
| #359 | segmented numbers | open | number theory | - |
