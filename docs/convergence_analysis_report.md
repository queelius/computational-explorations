# Convergence Analysis: Cross-Module Signal Agreement

Synthesizing 6 independent analytical modules
to identify highest-confidence research targets among 636 open problems.

## 1. Module Independence

Average pairwise correlation: **0.326**

| Module A | Module B | Correlation |
|----------|----------|-------------|
| tractability | tag_solvability | +0.896 |
| opportunity | vulnerability | +0.752 |
| tractability | frontier | +0.733 |
| frontier | tag_solvability | +0.656 |
| opportunity | tractability | +0.623 |
| opportunity | keystone_impact | -0.596 |
| opportunity | tag_solvability | +0.465 |
| frontier | vulnerability | +0.453 |
| opportunity | frontier | +0.450 |
| tractability | vulnerability | +0.434 |

## 2. Consensus Top 20 (Borda Count Aggregation)

| Rank | Problem | Consensus | Agreement | Modules | Tags | Prize |
|------|---------|-----------|-----------|---------|------|-------|
| 1 | #1021 | 0.904 | 0.93 | 5 | graph theory | - |
| 2 | #1111 | 0.894 | 0.91 | 5 | graph theory | - |
| 3 | #911 | 0.894 | 0.91 | 5 | graph theory, ramsey theory | - |
| 4 | #802 | 0.893 | 0.94 | 5 | graph theory | - |
| 5 | #1035 | 0.893 | 0.91 | 5 | graph theory | - |
| 6 | #778 | 0.891 | 0.94 | 5 | graph theory | - |
| 7 | #1033 | 0.891 | 0.91 | 5 | graph theory | - |
| 8 | #626 | 0.890 | 0.91 | 5 | chromatic number, cycles, graph theory | - |
| 9 | #619 | 0.888 | 0.94 | 5 | graph theory | - |
| 10 | #1017 | 0.888 | 0.91 | 5 | graph theory | - |
| 11 | #1029 | 0.888 | 0.92 | 5 | graph theory, ramsey theory | $100 |
| 12 | #1014 | 0.887 | 0.91 | 5 | graph theory | - |
| 13 | #616 | 0.886 | 0.94 | 5 | graph theory | - |
| 14 | #919 | 0.886 | 0.93 | 5 | chromatic number, graph theory | - |
| 15 | #667 | 0.886 | 0.91 | 5 | graph theory, ramsey theory | - |
| 16 | #638 | 0.885 | 0.91 | 5 | graph theory, ramsey theory | - |
| 17 | #1011 | 0.885 | 0.91 | 5 | graph theory | - |
| 18 | #1105 | 0.884 | 0.92 | 5 | graph theory, ramsey theory | - |
| 19 | #612 | 0.884 | 0.94 | 5 | graph theory | - |
| 20 | #917 | 0.884 | 0.93 | 5 | chromatic number, graph theory | - |

## 3. High-Confidence Targets (Multi-Module Agreement)

**221 problems** pass the high-confidence filter
(agreement ≥ 0.7, consensus ≥ 0.6, ≥ 4 modules).

| Problem | Consensus | Agreement | Tags | Prize |
|---------|-----------|-----------|------|-------|
| #1021 | 0.904 | 0.93 | graph theory | - |
| #1111 | 0.894 | 0.91 | graph theory | - |
| #911 | 0.894 | 0.91 | graph theory, ramsey theory | - |
| #802 | 0.893 | 0.94 | graph theory | - |
| #1035 | 0.893 | 0.91 | graph theory | - |
| #778 | 0.891 | 0.94 | graph theory | - |
| #1033 | 0.891 | 0.91 | graph theory | - |
| #626 | 0.890 | 0.91 | chromatic number, cycles, graph theory | - |
| #619 | 0.888 | 0.94 | graph theory | - |
| #1017 | 0.888 | 0.91 | graph theory | - |
| #1029 | 0.888 | 0.92 | graph theory, ramsey theory | $100 |
| #1014 | 0.887 | 0.91 | graph theory | - |
| #616 | 0.886 | 0.94 | graph theory | - |
| #919 | 0.886 | 0.93 | chromatic number, graph theory | - |
| #667 | 0.886 | 0.91 | graph theory, ramsey theory | - |

## 4. Module Disagreements (Analytical Blindspots)

Problems where modules strongly disagree reveal what different
analytical lenses see differently.

### #20 (spread=0.98)
- Tags: combinatorics
- **High**: tractability, tag_solvability
- **Low**: vulnerability
- Scores: frontier=0.73, keystone_impact=0.24, opportunity=0.15, tag_solvability=0.98, tractability=0.93, vulnerability=0.00

### #725 (spread=0.98)
- Tags: combinatorics
- **High**: tractability, tag_solvability
- **Low**: vulnerability
- Scores: frontier=0.74, keystone_impact=0.61, opportunity=0.14, tag_solvability=0.99, tractability=0.95, vulnerability=0.02

### #724 (spread=0.98)
- Tags: combinatorics
- **High**: tractability, tag_solvability
- **Low**: vulnerability
- Scores: frontier=0.74, keystone_impact=0.60, opportunity=0.14, tag_solvability=0.99, tractability=0.95, vulnerability=0.01

### #687 (spread=0.94)
- Tags: number theory
- **High**: keystone_impact
- **Low**: vulnerability
- Scores: frontier=0.40, keystone_impact=0.99, opportunity=0.21, tag_solvability=0.39, tractability=0.31, vulnerability=0.05

### #457 (spread=0.93)
- Tags: number theory
- **High**: keystone_impact
- **Low**: opportunity
- Scores: frontier=0.37, keystone_impact=0.98, opportunity=0.05, tag_solvability=0.36, tractability=0.26, vulnerability=0.25

### #416 (spread=0.92)
- Tags: number theory
- **High**: keystone_impact
- **Low**: opportunity
- Scores: frontier=0.35, keystone_impact=0.97, opportunity=0.05, tag_solvability=0.33, tractability=0.26, vulnerability=0.24

### #202 (spread=0.91)
- Tags: covering systems
- **High**: tag_solvability
- **Low**: opportunity, frontier, vulnerability
- Scores: frontier=0.08, keystone_impact=0.34, opportunity=0.10, tag_solvability=0.93, tractability=0.73, vulnerability=0.02

### #145 (spread=0.91)
- Tags: number theory
- **High**: keystone_impact
- **Low**: opportunity
- Scores: frontier=0.30, keystone_impact=0.96, opportunity=0.05, tag_solvability=0.29, tractability=0.22, vulnerability=0.21

### #51 (spread=0.88)
- Tags: number theory
- **High**: keystone_impact
- **Low**: opportunity
- Scores: frontier=0.29, keystone_impact=0.95, opportunity=0.07, tag_solvability=0.28, tractability=0.17, vulnerability=0.21

### #14 (spread=0.88)
- Tags: additive combinatorics, number theory, sidon sets
- **High**: vulnerability
- **Low**: keystone_impact
- Scores: frontier=0.65, keystone_impact=0.04, opportunity=0.73, tag_solvability=0.25, tractability=0.15, vulnerability=0.92

## 5. Research Strategy Matrix

### Do First (High Tractability + High Impact)
**13 problems** — Quick wins with big payoff

| Problem | Tractability | Impact | Tags | Prize |
|---------|-------------|--------|------|-------|
| #1029 | 0.87 | 0.65 | graph theory, ramsey theory | $100 |
| #625 | 0.82 | 0.70 | chromatic number, graph theory | $1000 |
| #74 | 0.84 | 0.67 | chromatic number, cycles, graph theory | $500 |
| #161 | 0.82 | 0.66 | combinatorics, discrepancy, ramsey theory | $500 |
| #564 | 0.78 | 0.66 | graph theory, hypergraphs, ramsey theory | $500 |
| #713 | 0.71 | 0.68 | graph theory, turan number | $500 |
| #712 | 0.73 | 0.65 | graph theory, hypergraphs, turan number | $500 |
| #146 | 0.70 | 0.68 | graph theory, turan number | $500 |
| #671 | 0.78 | 0.59 | analysis | $250 |
| #1111 | 0.87 | 0.50 | graph theory | - |

### Easy Wins (High Tractability + Low Impact)
**213 problems** — Low-hanging fruit

| Problem | Tractability | Impact | Tags | Prize |
|---------|-------------|--------|------|-------|
| #1021 | 0.88 | 0.50 | graph theory | - |
| #1035 | 0.87 | 0.50 | graph theory | - |
| #802 | 0.87 | 0.49 | graph theory | - |
| #1033 | 0.86 | 0.50 | graph theory | - |
| #911 | 0.88 | 0.48 | graph theory, ramsey theory | - |
| #778 | 0.87 | 0.49 | graph theory | - |
| #1017 | 0.86 | 0.50 | graph theory | - |
| #619 | 0.87 | 0.49 | graph theory | - |
| #1014 | 0.86 | 0.50 | graph theory | - |
| #616 | 0.86 | 0.49 | graph theory | - |

### Moonshots (Low Tractability + High Impact)
**26 problems** — Hard but transformative

| Problem | Tractability | Impact | Tags | Prize |
|---------|-------------|--------|------|-------|
| #601 | 0.58 | 0.67 | graph theory, set theory | $500 |
| #595 | 0.59 | 0.64 | graph theory, set theory | $250 |
| #165 | 0.54 | 0.67 | graph theory, ramsey theory | $250 |
| #77 | 0.54 | 0.67 | graph theory, ramsey theory | $250 |
| #66 | 0.59 | 0.59 | additive basis, number theory | $500 |
| #78 | 0.54 | 0.63 | graph theory, ramsey theory | $100 |
| #142 | 0.41 | 0.76 | additive combinatorics, arithmetic progressions | $10000 |
| #183 | 0.50 | 0.67 | graph theory, ramsey theory | $250 |
| #1013 | 0.56 | 0.60 | graph theory | - |
| #86 | 0.54 | 0.57 | graph theory | $100 |

### Deprioritize (Low Tractability + Low Impact)
**384 problems** — 
