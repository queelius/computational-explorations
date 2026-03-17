# Schur Number Extensions

## 1. S(G,k) Order-Invariance

For finite abelian groups G, the maximum size of a k-colorable sum-free subset S(G,k):

- **k = 1, 2**: S(G,k) depends ONLY on |G|, not isomorphism type. Verified all abelian groups through order 20.
- **k = 3**: Order-invariance FAILS. First failure at order 9: S(Z/9Z, 3) = 8 ≠ S(Z/3Z × Z/3Z, 3) = 7.

### S(Z/nZ, 2) Sequence (n=2..20)
1, 2, 3, 4, 4, 4, 6, 6, 8, 8, 9, 8, 9, 12, 12, 12, 12, 12, 16

### S(Z/nZ, 3) Sequence (n=2..15)
1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 13

Note: S(Z/nZ, 3) = n-1 for n = 2..14 (all nonzero elements 3-colorable sum-free).

### Prior Art
- Green & Ruzsa (2005): S(G,1) for general abelian groups — our k=1 invariance may follow.
- S(G,2) invariance and k=3 failure appear novel.

## 2. Density Schur Numbers DS(k, α)

**CAVEAT**: Definition-sensitive. On {0,...,N-1}, element 0 satisfies 0+0=0 (free Schur triple). On {1,...,N}, no such element exists. Values differ between the two domains.

### DS(2, α) Phase Transitions (1-indexed)
| α range | DS(2,α) |
|---------|---------|
| α ≤ 0.59 | 5 |
| 0.60 ≤ α ≤ 0.66 | 6 |
| α ≥ 0.67 | > 12 |

DS(3, 0.25) = 15 (first exact DS(3,α) value, via backtracking).

## 3. Multiplicative Schur Numbers

MS(k) = max N such that [2..N] can be k-colored avoiding monochromatic {a, b, ab}.

| k | MS(k) |
|---|-------|
| 1 | **3** |
| 2 | **31** |

**CORRECTED**: Earlier computation reported 4 and 32 (off-by-one). Independently verified.

Related work: Mattos, Mergoni Cecchelli, Parczyk, "On Product Schur Triples" (SIAM J. Discrete Math, 2024).

## 4. Rado Numbers

2-color Rado numbers for linear equations:

| Equation | R(eq; 2) |
|----------|----------|
| a + b = c (Schur) | 5 |
| a + b = 2c (AP) | 9 |
| a + b + c = d | 11 |
| a + 2b = 3c | 13 |

## Source Code
- `src/schur_groups.py`, `src/schur_extremal.py`, `src/rado_extensions.py`
