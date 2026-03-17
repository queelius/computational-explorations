# KLL Techniques for Problem #143

## Overview

This document analyzes recent techniques from Koukoulopoulos, Lamzouri, and Lichtman that could apply to Problem #143 (primitive sets in the reals).

## Problem #143 Recap

**Statement**: Let A ⊂ (1,∞) be countably infinite satisfying |kx - y| ≥ 1 for all distinct x,y ∈ A and integers k ≥ 1.

**Question**: Does this imply Σ_{x∈A} 1/(x log x) < ∞ or Σ_{x<n, x∈A} 1/x = o(log n)?

**Status**: PARTIALLY RESOLVED. Part 2 ($\sum 1/x = o(\log n)$) proved by KLL 2025. Part 1 ($\sum 1/(x \log x) < \infty$) remains open. See `proofs/problem_143_resolution.md` for the full verdict.

---

## Key Papers

### 1. KLL 2025: Integer Dilation Approximation (arXiv:2502.09539)

**Main result**: For any countable A ⊂ ℝ≥1 with lim sup (1/log x) Σ_{α∈A∩[1,x]} 1/α > 0, there exist infinitely many pairs with |nα - β| < ε.

**Key technique**: GCD graphs (from Duffin-Schaeffer proof).

**Relevance to #143**:
- The condition |kx - y| ≥ 1 is the NEGATION of |kx - y| < 1.
- KLL shows that sufficient density forces close pairs.
- For #143: if A is too dense, it violates the spacing condition.
- This gives an UPPER BOUND on primitive set density.

### 2. Lichtman 2022: Erdős Primitive Set Conjecture (arXiv:2202.02384)

**Main result**: For integer primitive sets A, sup f(A) = f(primes) where f(A) = Σ 1/(a log a).

**Relevance to #143**:
- Establishes optimal bound for INTEGER primitive sets.
- Primes achieve the supremum.
- Need to extend to REAL primitive sets.

---

## Technique Transfer Analysis

### GCD Graph Machinery

**Definition**: GCD graph G_q has vertices [q] with edges between coprime pairs.

**Properties**:
- Edge density ≈ 6/π² ≈ 0.608 (by Möbius)
- Contains many triangles (by Mantel, as we proved)
- Encodes coprimality structure

**Application to #143**:
- Define "multiplicative graph" on A: connect x, y if |kx - y| < 1 for some k.
- Primitive condition says this graph is EMPTY.
- KLL machinery bounds density of independent sets in such graphs.

### Density Bounds via Fourier/Diophantine

**KLL approach**:
1. Assume A has positive logarithmic density.
2. Use Fourier analysis on multiplicative characters.
3. Show existence of close pairs contradicting primitivity.

**For #143**:
1. Assume Σ 1/x diverges (high density).
2. Apply KLL machinery to show |kx - y| < 1 for some pair.
3. Contradiction proves Σ 1/x = o(log n).

---

## Proposed Attack on #143

### Phase 1: Translate KLL to Real Setting

**KLL Theorem (restated)**: If A ⊂ ℝ≥1 has positive upper logarithmic density:
```
lim sup_{X→∞} (1/log X) Σ_{x∈A, x≤X} 1/x > 0
```
then for all ε > 0, there exist x ≠ y in A with |kx - y| < ε for some k ≥ 1.

**Contrapositive**: If |kx - y| ≥ 1 for all x ≠ y and k ≥ 1, then:
```
lim sup_{X→∞} (1/log X) Σ_{x∈A, x≤X} 1/x = 0
```

This means Σ_{x≤X} 1/x = o(log X), which is exactly what #143 asks!

### Phase 2: Verify KLL Applies -- VERIFIED

All three potential gaps have been checked against the paper:

| Concern | Resolution |
|---------|------------|
| KLL may require integers | **NO**: Theorem stated for $\mathcal{A} \subset \mathbb{R}_{\geq 1}$ |
| GCD graph may not extend to reals | **OK**: Paper uses general "dilation graph" framework |
| $\varepsilon = 1$ may need special handling | **NO**: "For every $\varepsilon > 0$" covers all cases; Section 2.1 explicitly reduces to $\varepsilon = 1$ |

**Conclusion**: The contrapositive of KLL Theorem 1 directly resolves Part 2 of #143.

### Phase 3: Gap Analysis -- COMPLETED

**No gaps for Part 2.** The logical chain is complete:

1. #143 hypothesis ($|kx - y| \geq 1$) $\Rightarrow$ $\mathcal{A}$ is discrete (points separated by $\geq 1$)
2. #143 hypothesis $\Rightarrow$ contrapositive hypothesis of KLL Theorem 1 with $\varepsilon = 1$
3. Contrapositive conclusion: $\limsup (1/\log x) \sum 1/\alpha = 0$
4. By definition: $\sum_{x \leq n} 1/x = o(\log n)$ $\qquad \blacksquare$

**Remaining gap for Part 1**: $\sum 1/(x \log x) < \infty$ is strictly stronger than $o(\log n)$. KLL does not address this. See `proofs/problem_143_resolution.md` for details.

---

## Connection to Our Other Work

### NPG-7-R (Coprime Graphs)

KLL's GCD graph is closely related to our coprime graph G(A).

**Insight**: The techniques for bounding |A| when G(A) is bipartite may transfer to bounding |A| when the "dilation graph" has no edges.

### NPG-23 (Primitive-Coprime Hybrid)

The primitive set constraint (no divisibility) is related to coprimality.

**Observation**: If A is primitive AND has high coprime pair count, what can we say?
- KLL-style bounds on primitive density
- Möbius-based bounds on coprime structure
- Combined: tighter bounds on both?

---

## Summary

### Key Finding -- CONFIRMED

The KLL 2025 paper resolves Part 2 of #143 via contrapositive:

**KLL Theorem 1**: Positive logarithmic density + discrete $\Rightarrow$ close dilation pairs exist (for every $\varepsilon > 0$).
**Contrapositive**: No close pairs $\Rightarrow$ zero logarithmic density.
**Applied to #143**: $|kx - y| \geq 1$ $\Rightarrow$ $\sum 1/x = o(\log n)$. **PROVED.**

### Action Items -- STATUS

1. ~~Obtain and read full KLL paper~~ **DONE** (arXiv HTML version analyzed)
2. ~~Verify the theorem applies to real A~~ **VERIFIED**: $\mathcal{A} \subset \mathbb{R}_{\geq 1}$
3. ~~Check if ε = 1 threshold is covered~~ **VERIFIED**: universal over $\varepsilon > 0$
4. ~~If yes, #143 Part 2 is resolved by citing KLL~~ **YES**: Part 2 resolved
5. Part 1 ($\sum 1/(x \log x) < \infty$) **REMAINS OPEN**

### Confidence Level

**Certain** for Part 2: The contrapositive argument is a direct logical consequence with no gaps.
**Open** for Part 1: Would require a quantitative refinement of the KLL density bound.

### Full Analysis

See `proofs/problem_143_resolution.md` for the complete resolution document with verification checklist.

---

## References

1. Koukoulopoulos-Lamzouri-Lichtman (2025): "Erdős's integer dilation approximation problem and GCD graphs" [arXiv:2502.09539](https://arxiv.org/abs/2502.09539)

2. Lichtman (2022): "A proof of the Erdős primitive set conjecture" [arXiv:2202.02384](https://arxiv.org/abs/2202.02384)

3. Koukoulopoulos-Maynard: Duffin-Schaeffer conjecture (GCD graph origin)
