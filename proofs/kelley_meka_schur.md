# Kelley-Meka Extension to Schur Numbers

## Overview

This document outlines how the Kelley-Meka (2023) Fourier-analytic technique for 3-term arithmetic progressions could be adapted to attack Schur numbers (Problem #483).

## Background

### Kelley-Meka Result (2023)

**Theorem (Kelley-Meka)**: If A ⊆ [N] contains no non-trivial 3-term AP, then:
```
|A| ≤ N / exp(c(log N)^{1/9})
```

**Key technique**: Fourier analysis on ℤ/Nℤ with:
1. Density increment argument
2. Almost-periodicity via Bohr sets
3. Character sum bounds

### Schur Numbers

**Definition**: S(k) = largest n such that [n] can be k-colored without monochromatic Schur triple (a + b = c).

**Known bounds**: 3.28^k ≤ S(k) + 1 ≤ (e - 1/24)k!

**Problem #483**: Is S(k) + 1 < c^k for some constant c?

---

## Structural Comparison

### 3-AP vs Schur Triple

| Aspect | 3-AP (a, a+d, a+2d) | Schur (a + b = c) |
|--------|---------------------|-------------------|
| Equation | x + z = 2y | x + y = z |
| Variables | 3 (with constraint) | 3 (free) |
| Symmetry | Symmetric in x, z | Asymmetric |
| Density | In single set A | In single color class |
| Fourier character | e(2πi·r(x+z-2y)/N) | e(2πi·r(x+y-z)/N) |

**Key observation**: Both are *linear* constraints on 3 variables!

### Fourier Representation

For A ⊆ ℤ/Nℤ, define indicator:
```
1_A(x) = (1/N) Σ_{r ∈ ℤ/Nℤ} Â(r) e(rx/N)
```

**3-AP count**:
```
Λ_3(A) = Σ_{x,y,z} 1_A(x) 1_A(y) 1_A(z) 1_{x+z=2y}
       = (1/N) Σ_r |Â(r)|² Â(-2r)
```

**Schur triple count**:
```
T(A) = Σ_{x,y,z} 1_A(x) 1_A(y) 1_A(z) 1_{x+y=z}
     = (1/N) Σ_r |Â(r)|² Â(-r)
```

---

## Adaptation Strategy

### Step 1: Fourier Setup for k-Colorings

For a k-coloring χ: [N] → [k], define color indicators:
```
f_i(x) = 1_{χ(x) = i}
```

Properties:
- Σ_i f_i(x) = 1 for all x
- f_i(x) ∈ {0, 1}

**Schur triple in color i**:
```
T_i = Σ_{x+y=z} f_i(x) f_i(y) f_i(z)
```

**Goal**: Show that for N ≥ f(k), some T_i > 0.

### Step 2: Density Increment for Colorings

**Key insight from K-M**: If A has no 3-APs and is "Fourier-uniform", then |A| is small.

**Adaptation**: If color i has no Schur triples and is "Fourier-uniform", then |color i| is small.

**Density increment lemma** (to prove):
If T_i = 0 and color i has density δ = |color i|/N, then either:
1. δ is small (bounded by Fourier uniformity), or
2. Color i has large Fourier coefficient, enabling restriction to Bohr set

### Step 3: Bohr Set Machinery

**Definition**: Bohr set B(S, ε) = {x : |e(rx/N) - 1| < ε for all r ∈ S}

**K-M key lemma**: For set A with large Fourier coefficient, A ∩ B(S, ε) has:
- Increased density (density increment)
- Preserved AP-freeness (if A was AP-free)

**Adaptation for Schur**:
- If color i has large Fourier coefficient at r, restrict to Bohr set
- Need: Schur-freeness preserved under Bohr set restriction

**Potential issue**: Schur structure may not behave as nicely under restriction as AP structure.

### Step 4: Iterated Density Increment

**K-M iteration**: Repeat density increment until density exceeds threshold, forcing structure.

**For Schur**:
1. Start with k-coloring of [N]
2. If no Schur triple, all colors are sum-free
3. Sum-free sets have density ≤ 1/2 in ℤ/Nℤ (odd numbers show this is tight)
4. Apply density increment to largest color
5. Repeat on restricted domain

**Expected outcome**: After O(log log N) iterations, density exceeds 1/2, contradiction.

---

## Technical Challenges

### Challenge 1: Schur vs AP Symmetry

3-APs have the symmetric property: if (a, b, c) is a 3-AP, so is (c, b, a).

Schur triples are asymmetric: a + b = c doesn't imply b + a = c (well, it does, but c + a ≠ b in general).

**Impact**: Fourier analysis for Schur may have different cancellation properties.

### Challenge 2: Density Threshold

For 3-AP-free sets: density → 0 as N → ∞ (Roth/K-M).

For sum-free sets: density can be 1/2 (odd numbers in ℤ/Nℤ).

**Implication**: Direct analogy fails. Need to exploit coloring structure, not just density.

### Challenge 3: Multicolor Complexity

K-M works on a single set A.

Schur involves k colors simultaneously, with constraint that ALL must avoid triples.

**Approach**: Analyze colors one-by-one, use that density sum equals 1.

---

## Proposed Attack Plan

### Phase 1: Single Color Analysis

**Theorem to prove**: If C ⊆ ℤ/Nℤ is sum-free with |C| > N/3, then C has special structure (large Fourier coefficient or contained in short interval).

**Technique**: Adapt K-M Fourier analysis for sumsets.

### Phase 2: Multicolor Bootstrap

**Lemma**: For k-coloring of [N] with no monochromatic Schur triple:
- Each color has size ≤ N/2 (sum-free bound)
- At least one color has size ≥ N/k
- If k ≥ 3, the largest color has size in [N/k, N/2]

**Strategy**: Show that "medium-density" sum-free sets are highly structured, enabling iterated restriction.

### Phase 3: Iteration Bound

**Goal**: Prove that after O(k) iterations of density increment:
- Either a Schur triple is found, or
- All colors have size < c for absolute constant c

**Outcome**: S(k) + 1 < exp(O(k)) · k, giving S(k) < c^k.

---

## Concrete First Steps

### Step A: Verify Fourier Formula

Compute T(A) = Σ_{x+y=z} 1_A(x) 1_A(y) 1_A(z) in terms of Fourier coefficients.

```python
import numpy as np

def schur_count_fourier(A, N):
    """Count Schur triples in A ⊆ ℤ/Nℤ using Fourier."""
    # Indicator function
    f = np.zeros(N)
    for a in A:
        f[a % N] = 1

    # Fourier transform
    f_hat = np.fft.fft(f)

    # Schur count: (1/N) Σ_r |f_hat(r)|² f_hat(-r)
    # Actually: T = (1/N) Σ_r f_hat(r) f_hat(r) f_hat(-r)*
    #         where constraint is x + y = z mod N

    T = 0
    for r in range(N):
        T += f_hat[r] * f_hat[r] * np.conj(f_hat[r])
    T = T / N

    return np.real(T)

# Test on sum-free set
N = 100
A_odd = [i for i in range(1, N, 2)]  # Odd numbers
print(f"Schur count for odds: {schur_count_fourier(A_odd, N)}")
```

### Step B: Density Increment Simulation

```python
def has_schur_triple(A, N):
    """Check if A contains a Schur triple modulo N."""
    A_set = set(a % N for a in A)
    for a in A_set:
        for b in A_set:
            if (a + b) % N in A_set:
                return True, (a, b, (a+b) % N)
    return False, None

def largest_fourier_coeff(A, N):
    """Find largest non-zero Fourier coefficient."""
    f = np.zeros(N)
    for a in A:
        f[a % N] = 1
    f_hat = np.fft.fft(f)

    # Find max |f_hat(r)| for r ≠ 0
    magnitudes = np.abs(f_hat)
    magnitudes[0] = 0  # Exclude DC component
    r_max = np.argmax(magnitudes)
    return r_max, magnitudes[r_max]

# Test
A = [1, 2, 4, 8, 16, 32, 64]  # Powers of 2 (should be sum-free-ish)
print(f"Has Schur: {has_schur_triple(A, 100)}")
print(f"Largest Fourier: {largest_fourier_coeff(A, 100)}")
```

### Step C: Bohr Set Restriction

```python
def bohr_set(S, epsilon, N):
    """Return Bohr set B(S, ε) in ℤ/Nℤ."""
    B = []
    for x in range(N):
        in_bohr = True
        for r in S:
            phase = np.exp(2j * np.pi * r * x / N)
            if np.abs(phase - 1) >= epsilon:
                in_bohr = False
                break
        if in_bohr:
            B.append(x)
    return B

# Test
S = [1]  # Frequency 1
eps = 0.5
B = bohr_set(S, eps, 100)
print(f"Bohr set B({S}, {eps}): size {len(B)}")
```

---

## Expected Outcome

If this adaptation succeeds, we would prove:

**Theorem**: S(k) + 1 ≤ exp(c · k^{1-ε}) for some ε > 0.

This would be a significant improvement over the current upper bound of (e - 1/24)k! and would resolve Problem #483 affirmatively (that S(k) < c^k for some c).

---

## References

1. Kelley-Meka (2023): "Strong bounds for 3-progressions" arXiv:2302.07211
2. Bloom-Sisask (2023): Improvements to Kelley-Meka, arXiv:2309.02353
3. Schur (1916): Original result on partition regularity
4. Abbott-Wang: Current best lower bounds for Schur numbers
5. Tao-Vu: "Additive Combinatorics" - general reference

---

## Status

**This is a research outline, not a complete proof.**

Key lemmas marked with "to prove" require significant technical work.

The approach is promising because:
1. Both problems involve linear constraints on 3 variables
2. Fourier techniques have revolutionized AP bounds
3. No one has systematically applied K-M machinery to Schur

The main obstacle is that sum-free sets can have constant density (unlike AP-free sets), so the density increment must exploit multicolor structure.
