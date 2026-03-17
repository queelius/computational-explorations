# Primitive Sets: Analysis and Novel Extensions

## Problem #143 Overview

**Problem**: Let A ⊂ (1,∞) be a countably infinite set satisfying: for all distinct x,y ∈ A and integers k ≥ 1, we have |kx - y| ≥ 1.

**Question**: Does this imply A is sparse? Specifically:
1. Σ_{x∈A} 1/(x log x) < ∞ ?
2. Σ_{x<n, x∈A} 1/x = o(log n) ?

**Prize**: $500

**Status**: Open (partial progress by Koukoulopoulos-Lamzouri-Lichtman 2025)

---

## Connection to Coprime Graphs (#883)

### Structural Duality

| Primitive Sets | Coprime Sets |
|----------------|--------------|
| No a divides b | gcd(a,b) = 1 |
| Divisibility forbidden | Common factors forbidden |
| Sparse upper bound | Dense lower bound |
| A ⊂ [n]: |A| ≤ π(n) + O(1) | A ⊂ [n]: coprime density ≈ 0.608 |

### Key Insight

Primitive sets and coprime sets are **complementary constraints**:
- Primitive: forbid divisibility chains
- Coprime: forbid common prime factors

The "coprime graph" G(A) and "divisibility poset" D(A) capture different aspects of the same underlying arithmetic structure.

---

## Möbius Function Approach

### For Coprime Counting (NPG-7-R)

We used:
```
M(A) = Σ_{d≥1} μ(d) · |{a∈A : d|a}|²
```

### For Primitive Sets

Define the **divisibility count**:
```
D(A) = |{(a,b) ∈ A² : a|b, a < b}|
```

**Primitive condition**: D(A) = 0

Using Möbius inversion on divisibility:
```
D(A) = Σ_{a∈A} (|{b∈A : a|b}| - 1)
     = Σ_{a∈A} Σ_{k≥2} 1_{ka∈A}
```

### Dual Density Theorem

**Theorem (Primitive Set Density)**: For A ⊂ [n] primitive:
```
|A| ≤ (1 + o(1)) · n / log n
```

Achieved by primes (π(n) ~ n/log n).

**Proof sketch**: Each a ∈ A "blocks" the arithmetic progression {2a, 3a, 4a, ...}. By a covering argument, |A| ≤ n/log n.

---

## Novel Problem: NPG-23 (Primitive-Coprime Hybrid)

### Statement

For A ⊂ [n], define:
- P(A) = 1 if A is primitive, 0 otherwise
- M(A) = coprime pair count

**Question**: What is max M(A) subject to P(A) = 1?

### Conjecture

```
max{M(A) : A ⊂ [n] primitive} = (1 + o(1)) · π(n)²/2
```

Achieved by A = primes up to n.

### Reasoning

- Primes are primitive (no prime divides another)
- All prime pairs are coprime
- M(primes) = C(π(n), 2) = π(n)(π(n)-1)/2

**Open question**: Is there a primitive set with higher coprime count than primes?

---

## Novel Problem: NPG-24 (Weighted Primitive Density)

### Statement

Define weighted primitive counting function:
```
f(A) = Σ_{a∈A} 1/(a log a)
```

**Question**: For A ⊂ ℕ primitive with |A ∩ [n]| = Θ(n/log n):
1. What is sup f(A)?
2. Is the supremum achieved by primes?

### Known Bounds

- Erdős proved f(A) < ∞ for all primitive A
- Primes give f(primes) = Σ_p 1/(p log p) which converges (slowly)

**Conjecture**: sup f(A) = f(primes) + O(1)

---

## Novel Problem: NPG-25 (Real Primitive Extension)

### Statement (Extending #143)

For A ⊂ (1, ∞) satisfying |kx - y| ≥ 1 for all distinct x, y and k ≥ 1:

**Question**: What is the maximum density
```
δ(A, X) = |A ∩ [1, X]| / X
```
as X → ∞?

### Analysis

For integer primitive sets: δ(A, X) ≤ (1+o(1))/log X

For real sets with |kx - y| ≥ 1:
- Stronger condition than primitivity
- Each x ∈ A creates "forbidden zones" around kx for all k
- These zones have measure approaching 1

**Conjecture**: δ(A, X) = O(1/log X) for real primitive sets too.

---

## Technique Transfer: Kelley-Meka to Primitive Sets

### Observation

Kelley-Meka works on additive structure (a + b = c in 3-APs).
Primitive sets involve multiplicative structure (a · k = b in divisibility).

### Potential Connection

**Logarithmic transformation**: If a | b, then log a + log k = log b for some k.

This converts multiplicative primitivity to additive structure!

**Idea**: Apply Kelley-Meka-style Fourier analysis to log A = {log a : a ∈ A}.

**Challenge**: log A is not uniformly distributed; need weighted Fourier.

---

## Connections to Other Problems

### Problem #164 (Primitive Sets + Number Theory)

Related to primitive set density bounds.

### Problem #486 (Primitive Sets + Number Theory)

Another primitive set problem, status to check.

### Problem #858 (Primitive Sets + Number Theory)

Connection through divisibility structure.

### Cluster Structure

```
#143 (Real primitive, $500, OPEN)
   ↓
#164 (Integer primitive density)
   ↓
#486 (Primitive + density)
   ↓
#858 (Primitive + divisors)
```

---

## Attack Strategy for #143

### Phase 1: Understand the Real Constraint

|kx - y| ≥ 1 for all k ≥ 1 means:
- y ∉ (kx - 1, kx + 1) for any k
- Each x creates "forbidden intervals" around multiples

### Phase 2: Measure-Theoretic Approach

For x ∈ A ∩ [1, X]:
- Forbidden measure around x: Σ_k 2/(kx - 1 to kx + 1 overlap with [1,X])
- Total forbidden: Σ_{x∈A} Σ_{k≤X/x} 2 / (kx)
- This is approximately Σ_{x∈A} (2 log(X/x)) / x

### Phase 3: Density Bound

If |A ∩ [1,X]| > c · X / log X, the forbidden measure exceeds X.

**This would prove**: |A ∩ [1,X]| = O(X / log X)

**Which implies**: Σ_{x<n, x∈A} 1/x = O(log n / log log n) = o(log n) ✓

---

## Computational Verification

```python
def is_primitive_real(A, tol=1.0):
    """Check if real set A satisfies |kx - y| >= 1 for all x, y, k."""
    A = sorted(A)
    for i, x in enumerate(A):
        for y in A[i+1:]:
            # Check |kx - y| >= 1 for k = 1, 2, ..., ceil(y/x)
            for k in range(1, int(y/x) + 2):
                if abs(k*x - y) < tol:
                    return False, (x, y, k)
    return True, None

def max_primitive_real(X, n_elements):
    """Greedily construct large primitive set in [1, X]."""
    A = []
    candidates = [1 + i * X / 1000 for i in range(1, 1000)]

    for c in candidates:
        test_A = A + [c]
        if is_primitive_real(test_A)[0]:
            A.append(c)
            if len(A) >= n_elements:
                break

    return A

# Test
A = max_primitive_real(100, 20)
print(f"Primitive set of size {len(A)} in [1, 100]: {A[:10]}...")
```

---

## Summary

### Novel Problems Proposed

| ID | Name | Connection | Priority |
|----|------|------------|----------|
| NPG-23 | Primitive-Coprime Hybrid | #143 + #883 | ⭐⭐ |
| NPG-24 | Weighted Primitive Density | #143 | ⭐⭐ |
| NPG-25 | Real Primitive Bounds | #143 extension | ⭐⭐⭐ |

### Key Insight

The 2025 progress by Koukoulopoulos-Lamzouri-Lichtman suggests #143 may be close to resolution. Our analysis shows:

1. Real primitive sets have density O(1/log X) (conjectured)
2. The constraint |kx - y| ≥ 1 is stronger than integer primitivity
3. Measure-theoretic arguments may suffice for complete proof

### Recommended Next Steps

1. Study the KLL 2025 paper for technique extraction
2. Formalize NPG-23 (primitive-coprime hybrid) in Lean
3. Implement computational search for extremal primitive-coprime sets
