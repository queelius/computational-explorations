# R_cop(5): reconciliation with the prime-index map

**Corrected 2026-10-17:** the previous 181–211 window used a stale upper bound and misattributed it to Angeltveit–McKay. The supported window below is 181–197; the earlier interval is retained here only as correction history. See [consolidated corrections](coprime-ramsey-corrections.md).

This note reconciles the repository's earlier numerical estimates for the coprime
clique Ramsey number R_cop(5) with the prime-index theorem of Du, Xi, Deng & Ma
(2026, [arXiv:2605.26815](https://arxiv.org/abs/2605.26815), Theorem 4.4).

> **Edge vs vertex (read first).** Du et al. prove TWO distinct identities.
> For the *vertex*-coprime Ramsey number (color the integers [n]) they get
> R_cop = p_{sum_i (k_i - 1)} (Theorem 3.2, elementary pigeonhole). For the
> *edge*-coprime variant (color the EDGES of the coprime graph) they get
> R_cop^edge = p_{R(k_1,...,k_c) - 1} with R the classical Ramsey number
> (Theorem 4.4). This repository's R_cop is the EDGE variant, so the relevant
> theorem is 4.4 and every formula below is the edge-variant identity.
> Du et al. cite our edge values R_cop^edge(3;2)=11, (4;2)=59, (3;3)=53.
> Throughout this note, "R_cop" = the edge-coprime Ramsey number.

## The prime-map forces the answer

Du et al. prove the exact identity

> R_cop(k) = p_{R(k,k)-1}

where p_m is the m-th prime and R(k,k) is the classical diagonal Ramsey number.
This is not a fit to data; it is a theorem that determines R_cop(k) from R(k,k).
The map reproduces every value we computed (verified in Python with
sympy.prime / sympy.primepi):

| k | R(k,k) | index R(k,k)-1 | R_cop(k) = p_{R(k,k)-1} |
|---|--------|----------------|--------------------------|
| 2 | 2  | 1  | p_1  = 2  |
| 3 | 6  | 5  | p_5  = 11 |
| 4 | 18 | 17 | p_17 = 59 |

For k = 5, the map gives R_cop(5) = p_{R(5,5)-1} with no remaining freedom.

## What the prime-map says about R_cop(5)

The classical diagonal Ramsey number R(5,5) is not known exactly. The bounds reported in Du et al. v2, Table 3, are

> 43 <= R(5,5) <= 46

(lower bound 43 from Exoo 1989; upper bound 46 from [Angeltveit & McKay, arXiv:2409.15709](https://arxiv.org/abs/2409.15709), first posted in 2024). These agree with [Du et al. v2, Table 3](https://arxiv.org/html/2605.26815v2). Substituting into the prime-map:

| R(5,5) | index R(5,5)-1 | R_cop(5) = p_{R(5,5)-1} |
|--------|----------------|--------------------------|
| 43 (lower) | 42 | p_42 = 181 |
| 46 (upper) | 45 | p_45 = 197 |

So the prime-map pins R_cop(5) to the interval

> R_cop(5) in [p_42, p_45] = [181, 197].

The possible prime values in this interval are 181, 191, 193, and 197; the
intervening composite integers are excluded by the identity. R_cop(5) becomes known exactly precisely
when R(5,5) does; the residual uncertainty in R_cop(5) is exactly the residual
uncertainty in R(5,5).

## The older fit of R_cop(5) = 157 is falsified

Before the prime-map was available, this repository fit the prime-index sequence
(1, 5, 17) for k = 2, 3, 4 with the quadratic

> pi(R_cop(k)) = 4k^2 - 16k + 17

(see `src/universal_patterns.py`, lines ~414-418). This quadratic matches the
three known indices exactly and extrapolates to index 37 at k = 5, predicting

> R_cop(5) = p_37 = 157.

The same value appears as `PRED_QUADRATIC = 157` in `src/rcop5_estimation.py`.

The structural argument falsifies this prediction; the computational evidence gives a weaker, consistent bound:

1. **Structural (the prime-map).** 157 = p_37, and pi(157) = 37, so R_cop(5) = 157
   would require R(5,5) - 1 = 37, i.e. R(5,5) = 38. But R(5,5) >= 43 is an
   established lower bound. The prime-map therefore excludes 157 outright: the
   smallest value it permits is p_42 = 181 > 157. The quadratic index fit was a
   coincidence of three points, not the governing law; the governing law is
   index = R(k,k) - 1, and 4k^2 - 16k + 17 simply does not equal R(k,k) - 1 at
   k = 5 (it gives 37 where the truth is in [42, 45]).

2. **Computational (the SAT push).** The incremental CaDiCaL search in
   `src/rcop5_push.py` proved R_cop(5) > 138 (every n in [5, 138] admits an
   avoiding 2-coloring; n = 139 was left unsolved after 60+ minutes). This already
   ruled out the much older quadratic-*value* model (~31) and the density-adjusted
   prediction (~74). Note the precise logic: the bound R_cop(5) > 138 does not by
   itself exclude 157 (since 157 > 138). What the SAT push does is confirm that the
   true value lies well above the small-index predictions and is fully consistent
   with the prime-map floor of p_42 = 181 (since 181 > 138). The exclusion of 157
   specifically comes from the prime-map plus R(5,5) >= 43 in point 1.

The SAT evidence pushed the lower bound past the smaller estimates. The
prime-map fixes the target interval [181, 197], above the falsified 157.

## Files that stated R_cop(5) = 157

The value 157 = p_37 is correct *arithmetic* (it genuinely is the 37th prime), so
the prime-index facts in the code remain true and the tests asserting
`prime(37) == 157` stay valid. What changed is the *interpretation*: 157 was a
prediction for R_cop(5), and that prediction is wrong. The following locations have
been annotated to mark the 157 prediction as superseded by the prime-map:

- `src/rcop5_estimation.py` (module docstring; `PRED_QUADRATIC` constant)
- `src/universal_patterns.py` (quadratic-fit block, ~line 414-418)
- `discoveries/coprime-ramsey/README.md` (growth/prediction note)

## Summary

- Prime-map (Du et al. Thm 4.4): R_cop(5) = p_{R(5,5)-1}.
- With 43 <= R(5,5) <= 46: R_cop(5) in [p_42, p_45] = [181, 197].
- SAT push (`src/rcop5_push.py`): R_cop(5) > 138, consistent with the floor 181.
- Older fit R_cop(5) = p_37 = 157: falsified, because 157 would need R(5,5) = 38 < 43.
- R_cop(5) will be known exactly when R(5,5) is.
