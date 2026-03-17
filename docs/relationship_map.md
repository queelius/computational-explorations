# Erdős Problems: Relationship Map

## Overview

This document maps relationships between Erdős problems across mathematical domains, identifying:
- Gateway problems (highest connectivity)
- Cross-category connections
- Problem clusters and implications
- Opportunities for technique transfer

**Data Source**: erdosproblems.com (1,135 problems as of January 2026)

---

## Problem Distribution Summary

| Status | Count | Percentage |
|--------|-------|------------|
| Open | 636 | 56.0% |
| Proved | 257 | 22.6% |
| Disproved | 86 | 7.6% |
| Solved | 57 | 5.0% |
| Proved (Lean) | 24 | 2.1% |
| Other | 75 | 6.6% |

**Formalized**: 317/1135 (28%)

---

## Major Tag Pairs (Co-occurrence)

The strongest connections between mathematical areas:

| Tag Pair | Count | Notes |
|----------|-------|-------|
| Graph Theory + Ramsey Theory | 68 | Natural pairing in extremal combinatorics |
| Chromatic Number + Graph Theory | 54 | Coloring problems |
| Distances + Geometry | 52 | Point configuration problems |
| Number Theory + Unit Fractions | 48 | Egyptian fraction problems |
| Number Theory + Primes | 45 | Prime distribution |
| Additive Combinatorics + Number Theory | 37 | Structure in integers |
| Additive Combinatorics + Arithmetic Progressions | 16 | Szemerédi-type problems |
| Number Theory + Ramsey Theory | 14 | Cross-domain bridge |
| Geometry + Ramsey Theory | 6 | Geometric Ramsey |

---

## Gateway Problems (Highest Connectivity)

These problems connect to the most other problems through shared topics:

### #883 - Coprime Graphs (OPEN)
**Degree**: 810 (highest connectivity)
**Tags**: Number Theory, Graph Theory
**Statement**: For A ⊆ {1,...,n}, let G(A) be the graph with edges between coprime integers. If |A| > ⌊n/2⌋ + ⌊n/3⌋ - ⌊n/6⌋, does G(A) contain all odd cycles of length ≤ n/3 + 1?
**Why Gateway**: Bridges number theory (coprimality) with graph theory (cycle structure). Partial results exist but core conjecture open.

### #483 - Schur Numbers (OPEN)
**Degree**: 680
**Tags**: Number Theory, Additive Combinatorics, Ramsey Theory
**Statement**: Is f(k) < c^k where f(k) is the minimal N such that any k-coloring of {1,...,N} contains a monochromatic solution to a+b=c?
**Known**: 3.28^k ≤ f(k) ≤ (e-1/24)k!
**Why Gateway**: Fundamental Ramsey-type problem connecting coloring to additive structure.

### #769 - Number Theory + Geometry (OPEN)
**Degree**: 648
**Tags**: Number Theory, Geometry
**Why Gateway**: Rare direct bridge between number-theoretic and geometric problems.

### #45, #46 - Unit Fractions + Ramsey (PROVED)
**Degree**: 629
**Tags**: Number Theory, Unit Fractions, Ramsey Theory
**Why Gateway**: Connects Egyptian fraction problems to Ramsey coloring.

---

## The Arithmetic Progression Hub

Central to many relationships is the cluster around arithmetic progressions:

```
                    [Szemerédi's Theorem]
                           ↓
    [Problem #142] ←→ [Problem #3] ←→ [Problem #139, #140]
    ($10,000)          ($5,000)
         ↓                  ↓
   Asymptotic r_k(N)    Divergent sum → APs
         ↓                  ↓
    [Kelley-Meka]     [Green-Tao for primes]
         ↓                  ↓
   [Problem #483] ←→ [Ramsey-type extensions]
   (Schur numbers)
```

### Key Problems in This Cluster:

**Problem #3** ($5,000): If Σ(1/a_n) diverges, does {a_n} contain arbitrarily long APs?
- Most famous Erdős conjecture
- Called "completely hopeless" by Erdős himself
- Green-Tao (2004) proved it for primes

**Problem #142** ($10,000): Prove an asymptotic formula for r_k(N)
- Even harder than #3
- Recent progress: Kelley-Meka for k=3, Leng-Sah-Sawhney for k≥5

**Related solved problems**: #139, #140 contain weaker versions that have been resolved.

---

## Cross-Category Problems (156 total)

Problems spanning multiple major mathematical areas offer unique insight opportunities:

### Number Theory × Graph Theory
- **#883**: Coprime graphs (flagship)
- **#970, #971**: Divisibility graphs
- Structure of integers creates graph structure

### Number Theory × Additive Combinatorics (37 problems)
- Largest overlap between major categories
- Problems #1, #3, #14, #30, #36, etc.
- Sidon sets (28 problems) serve as bridge

### Graph Theory × Ramsey Theory (68 problems)
- Natural pairing: Ramsey theory originates in graph theory
- But 34 Ramsey problems are NOT about graphs (set theory, geometry)

### Geometry × Ramsey Theory (6 problems)
- Rare but valuable connections
- Geometric Ramsey: point configurations with forbidden patterns

---

## Technique Transfer Opportunities

### From Additive Combinatorics → Graph Theory
The polynomial method and Fourier analysis that revolutionized bounds on r_k(N) may apply to:
- Chromatic number problems (#74, #625)
- Cycle problems in dense graphs (#883)

### From Ramsey Theory → Number Theory
The stepping-up lemma and density increment arguments could help:
- Covering systems (#279)
- Sidon set constructions (#30, #39, #41, #43)

### From Geometry → Combinatorics
Algebraic geometry techniques (Guth-Katz) that solved distinct distances may help:
- Unit fraction problems (#47 cluster)
- Convex position problems (#96)

---

## Open Prize Problems - Relationship Analysis

| Problem | Prize | Tags | Related Problems |
|---------|-------|------|-----------------|
| #142 | $10,000 | Additive Combinatorics, APs | #3, #139, #140 |
| #3 | $5,000 | Number Theory, Add. Comb., APs | #142, #139, #140 |
| #30 | $1,000 | Number Theory, Sidon Sets | #39, #41, #43 |
| #592 | $1,000 | Set Theory, Ramsey | Related to #591 |
| #625 | $1,000 | Graph Theory, Chromatic | #74 |
| #687 | $1,000 | Number Theory | Isolated |
| #1 | $500 | Number Theory, Add. Comb. | #3 cluster |
| #39 | $500 | Sidon Sets, Add. Comb. | #30, #41, #43 |

---

## Formalization Frontiers

### High-Value Unformalized Open Problems

These problems are open, unformalized, and highly connected:

1. **#593** (4 tags): Set theory, Graph theory, Hypergraphs, Chromatic number - $500 prize
2. **#18** (3 tags): Number theory, Divisors, Factorials
3. **#43** (3 tags): Number theory, Sidon sets, Additive combinatorics - $100 prize
4. **#70** (3 tags): Graph theory, Ramsey theory, Set theory
5. **#96** (3 tags): Geometry, Distances, Convex

### Problems Recently Formalized and Solved

- #124 (Nov 2025): Solved by Aristotle AI after formalization
- #728 (Oct 2025): Number theory, factorial divisibility
- #1026 (Dec 2025): Monotone subsequences, connected to Erdős-Szekeres

---

## Proposed Novel Problems (Gap Identification)

Based on relationship analysis, these areas seem underexplored:

### NP1: Generalized Coprime Graph Problems
Problem #883 connects number theory and graph theory through coprimality. Natural extensions:
- What about k-coprime graphs (gcd = k)?
- Weighted versions based on φ(gcd(a,b))?

### NP2: Arithmetic Progression Coloring Interaction
Combine AP problems with chromatic number:
- Given k colors, what's the maximum density of integers colorable so no color class has a 3-AP?

### NP3: Sidon Sets in Geometric Settings
Sidon sets (no repeated pairwise sums) transfer to geometry:
- What's the maximum size of a planar point set where no two distances appear more than once?

### NP4: Unit Fraction Ramsey
Unit fraction problems (#47 cluster) + Ramsey coloring:
- If we k-color unit fractions, must some color class sum to 1?

---

## Next Steps

1. **Deep dive on AP cluster**: Problems #3, #142, #139, #140 deserve full analysis
2. **Formalize gateway problems**: #883, #769 could benefit from Lean formalization
3. **Cross-technique experiments**: Apply Kelley-Meka methods to #883
4. **Community consultation**: Post gap problems to erdosproblems.com forum
