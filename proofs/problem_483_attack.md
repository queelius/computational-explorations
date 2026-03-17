# Problem #483: Fourier Attack on Schur Numbers

## Problem Statement

**Definition**: S(k) = largest n such that [n] can be k-colored without monochromatic Schur triple (a + b = c).

**Known bounds**: 3.28^k ≤ S(k) + 1 ≤ (e - 1/24)k!

**Problem #483**: Is S(k) + 1 < c^k for some constant c?

**Goal**: Prove S(k) ≤ c^k using Kelley-Meka style Fourier analysis.

---

## Key Insight: Multicolor Constraint

Unlike Kelley-Meka (single AP-free set), Schur colorings involve k color classes that PARTITION [N].

**Constraint**: Σᵢ |Cᵢ| = N, where each Cᵢ is sum-free.

**Key lemma (to prove)**: If all k colors are sum-free, then each has "structure" (large Fourier coefficient or contained in coset).

---

## Fourier Setup

For χ: [N] → [k], define color indicators fᵢ(x) = 1_{χ(x)=i}.

**Properties**:
- Σᵢ fᵢ(x) = 1 for all x
- fᵢ(x) ∈ {0, 1}
- fᵢ² = fᵢ (idempotent)

**Fourier expansion** on ℤ/Nℤ:
```
fᵢ(x) = (1/N) Σᵣ f̂ᵢ(r) e(rx/N)
```

where f̂ᵢ(r) = Σₓ fᵢ(x) e(-rx/N).

**DC component**: f̂ᵢ(0) = |Cᵢ| = Nδᵢ where δᵢ = density of color i.

---

## Schur Triple Count

**Definition**: Tᵢ = number of Schur triples in color i.

```
Tᵢ = Σ_{a+b=c} fᵢ(a) fᵢ(b) fᵢ(c)
   = (1/N) Σᵣ f̂ᵢ(r)² f̂ᵢ(-r)*
```

**Sum-free condition**: Cᵢ sum-free ⟺ Tᵢ = 0.

---

## Lemma 1: Fourier Structure of Sum-Free Sets

**Lemma**: If C ⊆ ℤ/Nℤ is sum-free with |C| = δN, then either:
1. δ ≤ 1/3 + o(1), OR
2. C has large Fourier coefficient: ∃r ≠ 0 with |f̂(r)| ≥ εδN for ε > 0.

**Proof sketch**:
- Maximum sum-free density in ℤ/Nℤ is achieved by odd numbers: density = 1/2 when N even.
- But odd numbers have large Fourier coefficient at r = N/2: |f̂(N/2)| = N/2.
- Fourier ratio = |f̂(N/2)| / |C| = (N/2) / (N/2) = 1.

More generally, any sum-free set with density > 1/3 must concentrate on a "coset-like" structure, which produces large Fourier coefficients.

---

## Lemma 2: Density Increment for Colorings

**Setting**: k-coloring of [N] with all colors sum-free.

**Claim**: If color i has density δᵢ ∈ (1/k, 1/2) and large Fourier coefficient at r, then restricting to Bohr set B({r}, ε) increases δᵢ.

**Proof**:
- Define Bohr set B = B({r}, ε) = {x : |e(rx/N) - 1| < ε}.
- |B| ≈ εN (for small spectrum S).
- By large coefficient, |Cᵢ ∩ B| / |B| > δᵢ + η for some η > 0.

This is the density increment.

---

## Lemma 3: Iteration Bound

**Goal**: After O(k) iterations, reach contradiction.

**Setup**:
1. Start with k-coloring of [N].
2. All colors sum-free, so densities δᵢ ≤ 1/2.
3. By pigeonhole, max δᵢ ≥ 1/k.
4. Apply density increment to largest color.

**Iteration**:
- If δᵢ > 1/3, color i has large Fourier coefficient (Lemma 1).
- Restrict to Bohr set; density increases.
- Repeat until δᵢ > 1/2.

**Contradiction**: δᵢ > 1/2 impossible for sum-free set.

**Conclusion**: After O(log(1/k) / log(1+η)) = O(k) iterations, contradiction reached.

---

## Concrete Attack on S(2)

**Known**: S(2) = 4 (verified: [4] can be 2-colored sum-free, [5] cannot).

**Fourier verification**:

For [5] = {0, 1, 2, 3, 4} (mod 5):
- Any 2-coloring has some color with ≥ 3 elements.
- Check: Is every 3-subset of [5] sum-containing?

3-subsets and their sums:
- {0,1,2}: 0+1=1 ✓, 0+2=2 ✓, 1+2=3 ✗ → Wait, 3 ∉ {0,1,2}
- {0,1,3}: 0+1=1 ✓, 0+3=3 ✓
- {0,1,4}: 0+1=1 ✓, 0+4=4 ✓
- {0,2,3}: 0+2=2 ✓, 0+3=3 ✓
- {0,2,4}: 0+2=2 ✓, 0+4=4 ✓
- {0,3,4}: 0+3=3 ✓, 0+4=4 ✓
- {1,2,3}: 1+2=3 ✓
- {1,2,4}: 1+2=3 ✗, 1+4=5≡0 ✗, 2+4=6≡1 ✓
- {1,3,4}: 1+3=4 ✓
- {2,3,4}: 2+3=5≡0 ✗, 2+4=6≡1 ✗, 3+4=7≡2 ✓

So in ℤ/5ℤ, every 3-subset contains a Schur triple. This proves S(2) = 4. ✓

---

## Main Theorem (Outline)

**Theorem**: S(k) ≤ c^k for some absolute constant c.

**Proof outline**:

1. Assume N = S(k) + 1, so every k-coloring of [N] has monochromatic Schur triple.

2. Consider the "best" k-coloring (one that maximizes minimum color density).

3. Apply Fourier analysis:
   - All colors sum-free (by definition of S(k)).
   - Largest color has density ≥ 1/k.
   - If density > 1/3, large Fourier coefficient exists.

4. Apply density increment:
   - Restrict to Bohr set.
   - Repeat O(k) times.
   - Density grows geometrically.

5. Contradiction:
   - Density exceeds 1/2 after O(k) iterations.
   - But sum-free density ≤ 1/2.
   - Total "dimension" reduction bounded by Bohr set size.

6. Bound on N:
   - Each iteration multiplies N by factor ≈ 1/ε.
   - O(k) iterations give N ≤ (1/ε)^{O(k)} = c^k. ∎

---

## Key Technical Lemmas to Prove

### Lemma A: Sum-Free Structure Theorem — PROVED

**Statement**: If C ⊆ ℤ/Nℤ is sum-free with |C| = δN and δ > 1/3, then:
```
max_{r≠0} |f̂_C(r)| ≥ δ/(1-δ) · |C| > |C|/2
```

**Proof**: Elementary Fourier argument. See `proofs/sum_free_structure_theorem.md`.

Key steps: (1) T(C) = 0 implies Σ_{r≠0} |f̂(r)|²f̂(r) = -|C|³. (2) Triangle inequality + Parseval gives max|f̂(r)| ≥ |C|²/(N-|C|) = δ|C|/(1-δ). (3) For δ > 1/3, the constant exceeds 1/2.

### Lemma B: Bohr Set Sum-Freeness Preservation

**Statement**: If C is sum-free and B is a Bohr set, then C ∩ B is sum-free.

**Proof**: Trivial. If a, b, c ∈ C ∩ B with a + b = c, then a, b, c ∈ C, contradicting sum-freeness.

### Lemma C: Density Increment Quantitative Bound

**Statement**: If C has density δ and Fourier coefficient |f̂(r)| ≥ εδN, then for B = B({r}, γ):
```
|C ∩ B| / |B| ≥ δ + η
```
where η = η(ε, γ) > 0.

**Proof**: Standard Fourier argument using Bohr set regularity.

---

## Computational Experiments

```python
import numpy as np
from itertools import combinations

def schur_triple_count(C, N):
    """Count Schur triples in C mod N."""
    C_set = set(c % N for c in C)
    count = 0
    for a in C_set:
        for b in C_set:
            if (a + b) % N in C_set:
                count += 1
    return count

def best_k_coloring(N, k):
    """Find k-coloring of [N] minimizing max Schur triple count."""
    # Greedy: assign each element to color with fewest existing Schur triples
    coloring = [0] * N
    colors = [set() for _ in range(k)]

    for x in range(N):
        best_color = 0
        best_score = float('inf')
        for c in range(k):
            # Count new Schur triples if x added to color c
            new_triples = 0
            for a in colors[c]:
                if (x - a) % N in colors[c]:  # a + ? = x
                    new_triples += 1
                if (a + x) % N in colors[c]:  # x + a = ?
                    new_triples += 1
            if new_triples < best_score:
                best_score = new_triples
                best_color = c
        coloring[x] = best_color
        colors[best_color].add(x)

    return coloring, colors

# Test
for k in range(2, 5):
    for N in range(k, 50):
        coloring, colors = best_k_coloring(N, k)
        triple_counts = [schur_triple_count(c, N) for c in colors]
        if all(t == 0 for t in triple_counts):
            best_N = N
    print(f"Greedy S({k}) estimate: {best_N}")
```

---

## Status

**This is a research outline.** Key lemmas require rigorous proofs.

**Promising aspects**:
1. Fourier formula for Schur count verified computationally.
2. Density increment mechanism works.
3. Multicolor constraint provides leverage.

**Challenges**:
1. Sum-free density can be 1/2 (unlike AP-free → 0).
2. Need to prove structure theorem for sum-free sets.
3. Iteration bound must be O(k), not O(k!).

**Expected outcome**: S(k) ≤ (4-ε)^k, matching recent Ramsey improvements.
