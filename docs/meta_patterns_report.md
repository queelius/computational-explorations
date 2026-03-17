# Meta-Patterns in Erdős Problems

Higher-order patterns discovered by analyzing patterns of patterns.

## 1. Resolution Waves

- Problems with resolution dates: 343
- Year range: 2025–2026
- Mean solutions per year: 171.5
- Peak year: 2025 (341 solutions)

### Tag-Specific Resolution Peaks

| Tag | Total Solved | Peak Year | Peak Count | Span |
|-----|-------------|-----------|------------|------|
| number theory | 134 | 2025 | 133 | 1y |
| graph theory | 101 | 2025 | 101 | 0y |
| ramsey theory | 33 | 2025 | 32 | 1y |
| additive combinatorics | 31 | 2025 | 31 | 0y |
| analysis | 31 | 2025 | 31 | 0y |
| geometry | 27 | 2025 | 27 | 0y |
| chromatic number | 21 | 2025 | 21 | 0y |
| combinatorics | 17 | 2025 | 17 | 0y |
| unit fractions | 16 | 2025 | 16 | 0y |
| divisors | 11 | 2025 | 11 | 0y |

## 2. Tag Co-Evolution

Analyzed 48 tag pairs (≥3 occurrences)

### Easiest Tag Pairs (highest solve rate)

| Tags | Solve Rate | Solved/Total |
|------|-----------|-------------|
| number theory + ramsey theory | 66.7% | 6/9 |
| diophantine approximation + number theory | 66.7% | 2/3 |
| chromatic number + hypergraphs | 60.0% | 3/5 |
| covering systems + number theory | 57.1% | 8/14 |
| chromatic number + cycles | 57.1% | 4/7 |
| convex + geometry | 55.6% | 5/9 |
| convex + distances | 50.0% | 3/6 |
| combinatorics + hypergraphs | 50.0% | 2/4 |

### Hardest Tag Pairs (lowest solve rate)

| Tags | Solve Rate | Solved/Total |
|------|-----------|-------------|
| chromatic number + set theory | 0.0% | 0/3 |
| base representations + number theory | 0.0% | 0/5 |
| number theory + powers | 0.0% | 0/4 |
| iterated functions + number theory | 0.0% | 0/7 |
| combinatorics + set theory | 0.0% | 0/3 |
| binomial coefficients + primes | 0.0% | 0/3 |
| chromatic number + geometry | 0.0% | 0/3 |
| additive combinatorics + sidon sets | 7.1% | 1/14 |

### Synergistic Tag Pairs (actual >> expected)

| Tags | Actual Rate | Expected | Synergy |
|------|-----------|----------|---------|
| number theory + ramsey theory | 66.7% | 28.5% | +0.382 |
| chromatic number + hypergraphs | 60.0% | 35.1% | +0.249 |
| convex + geometry | 55.6% | 33.3% | +0.223 |
| covering systems + number theory | 57.1% | 36.0% | +0.211 |
| convex + distances | 50.0% | 30.3% | +0.197 |
| chromatic number + cycles | 57.1% | 38.9% | +0.182 |
| number theory + unit fractions | 43.2% | 29.0% | +0.142 |
| analysis + probability | 50.0% | 38.2% | +0.118 |

## 3. Difficulty Structure

### Tag Count vs Solve Rate

| Tags | Solve Rate |
|------|-----------|
| 1 | 31.3% |
| 2 | 29.9% |
| 3 | 24.4% |
| 4 | 50.0% |

### Problem Age vs Solve Rate

| Quartile | Solve Rate | Total | Solved |
|----------|-----------|-------|--------|
| Q1 (earliest) | 34.9% | 284 | 99 |
| Q2 | 29.2% | 284 | 83 |
| Q3 | 31.0% | 284 | 88 |
| Q4 (latest) | 25.8% | 283 | 73 |

### Formalization Paradox

- **Not formalized**: 30.2% solved (343/1135)

## 4. Network Structure

- Nodes: 321
- Edges: 23105
- Triangles: 1249142
- Star nodes (degree ≥ 10): 10
- Bridge edges: 6
- Components: 7
- Largest component: 309

Degree distribution: max=187, median=183, mean=144.0

### Hub Nodes

- **#41**: degree 187
- **#44**: degree 187
- **#42**: degree 187
- **#39**: degree 187
- **#563**: degree 185

## 5. Problem DNA Profiles

### Solved vs Open Averages

| Feature | Solved | Open |
|---------|--------|------|
| Avg tags | 1.59 | 1.64 |
| Avg OEIS | 1.09 | 1.19 |
| Avg prize (log) | 0.47 | 0.53 |
| Formalized % | 0.0% | 0.0% |

### Tags Most Enriched in Solved Problems

- **intersecting family**: 3.7× enriched (solved: 0.6%, open: 0.2%)
- **diophantine approximation**: 2.8× enriched (solved: 0.9%, open: 0.3%)
- **convex**: 2.3× enriched (solved: 1.5%, open: 0.6%)
- **analysis**: 1.9× enriched (solved: 9.0%, open: 4.9%)
- **covering systems**: 1.9× enriched (solved: 2.6%, open: 1.4%)
- **planar graphs**: 1.9× enriched (solved: 0.3%, open: 0.2%)
- **powerful**: 1.9× enriched (solved: 0.3%, open: 0.2%)

### Tags Most Enriched in Open Problems

- **base representations**: 0.00× (solved: 0.0%, open: 0.8%)
- **iterated functions**: 0.00× (solved: 0.0%, open: 1.3%)
- **powers**: 0.00× (solved: 0.0%, open: 0.6%)
- **sidon sets**: 0.27× (solved: 0.9%, open: 3.3%)
- **primitive sets**: 0.37× (solved: 0.3%, open: 0.8%)
- **primes**: 0.46× (solved: 2.6%, open: 5.7%)
- **binomial coefficients**: 0.49× (solved: 1.2%, open: 2.4%)
- **distances**: 0.52× (solved: 2.9%, open: 5.7%)

## 6. Anomalies

### Should Be Solved (high vulnerability, still open)

- **#883** (v=0.710): graph theory, number theory
- **#108** (v=0.689): chromatic number, cycles, graph theory
- **#626** (v=0.689): chromatic number, cycles, graph theory
- **#531** (v=0.677): number theory, ramsey theory
- **#948** (v=0.677): number theory, ramsey theory

### Surprisingly Solved (low-solvability tags)

- **#154**: avg tag rate = 10.7%
- **#157**: avg tag rate = 10.7%
- **#164**: avg tag rate = 19.5%
- **#4**: avg tag rate = 21.5%
- **#6**: avg tag rate = 21.5%

### Prize Orphans (has prize, no technique match)

- **#20** ($1000): combinatorics
- **#92** ($500): distances, geometry
- **#604** ($500): distances, geometry
- **#89** ($500): distances, geometry
- **#90** ($500): distances, geometry
