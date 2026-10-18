# Coprime Ramsey Numbers

**Reconciled 2026-10-17.** See the [corrections and archival errata](../../docs/coprime-ramsey-corrections.md) and [reproducibility audit](../../docs/coprime-ramsey-citation-audit.md). These are edge-coloring parameters; Lean certification is incomplete.

## Definition

For the **coprime graph** G(n) on {1,...,n} (edges between coprime pairs), define:

**R_cop(k)** = min n such that every 2-coloring of coprime edges contains a monochromatic complete subgraph K_k.

## Exact Values

### Clique Ramsey (2 colors)
| k | R_cop(k) | R(k,k) | Ratio | Prime? |
|---|----------|--------|-------|--------|
| 2 | 2 | 2 | 1.00 | Yes |
| 3 | **11** | 6 | 1.83 | Yes |
| 4 | **59** | 18 | 3.28 | Yes |

### Multi-Color (monochromatic K_3)
| Colors c | R_cop(3;c) | R(3,...,3;c) | index R-1 | p_{R-1} | Prime? |
|----------|------------|--------------|-----------|---------|--------|
| 2 | **11** | 6  | 5  | p_5  = 11 | Yes |
| 3 | **53** | 17 | 16 | p_16 = 53 | Yes |

The c=3 row is a second instance, off the two-color diagonal, of the prime-index
map R_cop = p_{R-1} (Du et al. 2026, Thm 4.4): with the multicolor Ramsey number
R(3,3,3) = 17, the map gives p_16 = 53, matching the SAT-computed value exactly.
(Verified in Python: sympy.prime(16) = 53, sympy.primepi(53) = 16.)

### Path Ramsey P_cop(k)

Here k counts edges (a simple path has k+1 distinct vertices). The October 17
audit reproduced k=3..6. The [October 18 path certificate](../../docs/audits/coprime-paths-2026-10-18/README.md)
independently verifies k=7,8: a complete avoiding coloring at 12 and a
semantically checked CNF with a DRAT-trim-verified UNSAT proof at 13 establish
both values. This closes the earlier audit's 60-second timeout gap.

| k | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|
| P_cop | **5** | **7** | **9** | **10** | **13** | **13** |

The [structural follow-up](../../docs/coprime-path-structure-2026-10-18.md)
proves P_cop(k) = Θ(k), with asymptotic lower constant 2 and upper constant
197π²/595 ≈ 3.267751. This is an elementary density argument, with no priority
claim. It supplies finite sufficient bounds and explains why that method
cannot recover the exact threshold 13; the next exact family remains unresolved.

The [nine-edge-path investigation](../../docs/coprime-path-nine-2026-10-18.md)
narrows any hypothetical avoiding coloring at 17: both colors must be
connected and spanning, with 47 and 48 edges, and each retains at least five
edges after every four-vertex deletion. The supporting finite certificates
are independently checked. This does not establish P_cop(9)=17; the current
bounds remain 17 ≤ P_cop(9) ≤ 26.

### Cycle Ramsey C_cop(k)
| k | 3 | 4 | 5 | 6 |
|---|---|---|---|---|
| C_cop | **11** | **8** | **13** | **11** |

### Asymmetric clique Ramsey R_cop(s,t)

Targets are a color-0 K_s or color-1 K_t, not a complete bipartite graph. The legacy source function is named `compute_bipartite_coprime_ramsey`.

| (s,t) | (2,3) | (2,4) | (3,4) |
|-------|-------|-------|-------|
| R_cop | **3** | **5** | **19** |

### Gallai
GR_cop(3; 3) = **29**. This is the complete-pattern transfer of the classical Gallai triangle threshold 11: p_10 = 29 (Du et al., Proposition 4.6).

## Conjectures and resolved items

1. **NPG-30 (Primality), EXPLAINED, not a conjecture.** Du, Xi, Deng & Ma (2026,
   arXiv:2605.26815, Thm 4.4) prove R_cop(k) = p_{R(k,k)-1}, the (R(k,k)-1)-th
   prime. (Thm 4.4 is the EDGE-coprime variant = our R_cop; distinct from their
   vertex Thm 3.2, which gives p_{sum(k_i-1)}.) Primality is then automatic (R_cop is a prime by construction), so the
   "always prime" observation is a corollary of the prime-map. The four values
   {2, 11, 53, 59} are exactly p_1, p_5, p_16, p_17, respectively (53 is the multicolor
   R_cop(3;3) via R(3,3,3)=17). For the two-color diagonal, identifying which
   primes occur remains tied to the unknown R(k,k) values for k >= 5.
   Every prime occurs in the unrestricted mixed family: R(2,t)=t gives
   R_cop(2,t)=p_(t-1).
   See [R_cop(5) reconciliation](../../docs/rcop5-reconciliation.md) and [novel problems](../../docs/novel_problems.md).

2. **Growth (historical fit)**: R_cop(k) ~ 0.38 * 5.43^k (exponential fit to 3
   points), which predicted R_cop(5) in [200, 350]. The prime-map now supersedes
   any fit: R_cop(5) = p_{R(5,5)-1} in [p_42, p_45] = [181, 197] from
   43 <= R(5,5) <= 46 ([Angeltveit–McKay](https://arxiv.org/abs/2409.15709); [Du et al. v2, Table 3](https://arxiv.org/html/2605.26815v2)). The earlier [181, 211] window was stale. (The competing quadratic-index fit of R_cop(5) =
   p_37 = 157 is FALSIFIED; it would require R(5,5) = 38 < 43.)

3. **Ratio**: R_cop(k)/R(k,k) grows; the prime-map makes this precise, since
   R_cop(k)/R(k,k) = p_{R(k,k)-1}/R(k,k) ~ ln(R(k,k)) by the prime number theorem.

## Methodology

- R_cop(3) = 11: Exact incremental extension (enumerate all 36 avoiding colorings at n=8, extend to n=11 where 0 remain).
- R_cop(4) = 59: a full avoiding witness at 58 supplies the lower bound. At 59, the set consisting of 1 and the 17 primes at most 59 forms K_18; R(4,4)=18 supplies the upper bound. The historical 100 failed seeded extensions are corroboration, not a proof of universal nonextendibility.
- R_cop(3;3) = 53: a full witness at 52 and the K_17 prime clique at 53, using R(3,3,3)=17.
- The [audit witnesses](../../docs/audits/coprime-ramsey-2026-10-17/) at 10, 58, and 52 were independently checked for all required edges, palette, and forbidden cliques.
- Variants use pysat encodings. The [path audit](../../docs/audits/coprime-paths-2026-10-18/README.md) preserves a complete witness and an independently checked UNSAT certificate for k=7,8; certificate preservation for the other variants remains incomplete.

## Provenance

- No prior art found for "coprime Ramsey numbers" (searched March 2026).
- Coprime graph structure studied by others; Ramsey questions on it appear novel.
- Related: Syarifudin & Wardhana (coprime graph of groups, chromatic = clique number).

## Source Code

- `src/coprime_ramsey.py` — Incremental extension algorithm
- `src/coprime_ramsey_sat.py` — SAT-based computation
- `src/coprime_ramsey_variants.py` — Path, cycle, multi-color, asymmetric-clique variants
- `src/coprime_path_search.py`, `src/coprime_path_certificates.py` — Bounded path search and independent evidence validation
- `tests/test_coprime_ramsey.py`, `tests/test_coprime_ramsey_sat.py`, `tests/test_coprime_ramsey_variants.py`
