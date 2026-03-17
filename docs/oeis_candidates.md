# OEIS Sequence Candidates

Sequences computed in this project that may be new to OEIS.

## 1. S(Z/nZ, 2): Maximum 2-colorable sum-free subset of Z/nZ

**Offset**: 2
**Sequence** (n=2..20): 1, 2, 3, 4, 4, 4, 6, 6, 8, 8, 9, 8, 9, 12, 12, 12, 12, 12, 16

**Definition**: a(n) = maximum size of a subset A of Z/nZ such that A can be
partitioned into two sum-free sets. Equivalently, a(n) = max |A₁ ∪ A₂| where
A₁, A₂ are disjoint subsets of Z/nZ with no a+b≡c (mod n) within either set.

**Properties**:
- a(n) ≥ S(Z/nZ, 1) (one color always works)
- a(n) ≤ n (trivially)
- ORDER-INVARIANT: for all abelian groups G with |G|=n, S(G,2) = a(n) (verified through n=20)

**Related**: Maximum sum-free subset of Z/nZ (k=1 case) may already be in OEIS.

## 2. S(Z/nZ, 3): Maximum 3-colorable sum-free subset of Z/nZ

**Offset**: 2
**Sequence** (n=2..15): 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 13

**Definition**: a(n) = maximum size of a subset A of Z/nZ such that A can be
partitioned into three sum-free sets.

**Property**: a(n) = n-1 for n = 2..14 (all nonzero elements 3-colorable sum-free).
First exception at n=15 where a(15) = 13 = n-2.

**NOTE**: S(G,3) is NOT order-invariant. S(Z/9Z, 3) = 8 ≠ S(Z/3Z×Z/3Z, 3) = 7.

## 3. a(n) = max Sidon subset of {1², 2², ..., n²}

**Offset**: 1
**Sequence** (n=1..50): 1, 2, 3, 4, 5, 6, 6, 7, 8, 9, 9, 9, 10, 10, 11, 12, 12, 13, 13, 13, 14, 14, 14, 15, 16, 16, 17, 17, 17, 17, 17, 18, 18, 19, 19, 19, 20, 20, 21, 21, 21, 21, 21, 21, 22, 22, 22, 22, 23, 24

**Definition**: a(n) = maximum cardinality of a subset S of {1², 4, 9, ..., n²}
such that all pairwise sums s_i + s_j (i < j) are distinct.

**Growth rate**: a(n) ~ 1.81 * n^{0.658} ≈ n^{2/3}.

**Note**: OEIS A390813 (submitted 2025) may cover a related formulation. Check before submitting.

## 4. DS(2, alpha): Density-relaxed Schur numbers

**Not a sequence per se, but a function**:
- DS(2, alpha) = 5 for 0 < alpha ≤ 0.59
- DS(2, alpha) = 6 for 0.60 ≤ alpha ≤ 0.66
- DS(2, alpha) = ∞ for alpha ≥ 0.67 (no finite N forces)

DS(2, 1/2) = 5 is proved in Lean (NPG2_DensitySchur.lean).
