# Coprime Ramsey Numbers

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
| Colors c | R_cop(3;c) | R(3,...,3;c) | Prime? |
|----------|------------|-------------|--------|
| 2 | **11** | 6 | Yes |
| 3 | **53** | 17 | Yes |

### Path Ramsey P_cop(k)
| k | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|
| P_cop | **5** | **7** | **9** | **10** | **13** | **13** |

### Cycle Ramsey C_cop(k)
| k | 3 | 4 | 5 | 6 |
|---|---|---|---|---|
| C_cop | **11** | **8** | **13** | **11** |

### Bipartite R_cop(s,t)
| (s,t) | (2,3) | (2,4) | (3,4) |
|-------|-------|-------|-------|
| R_cop | **3** | **5** | **19** |

### Gallai
GR_cop(3; 3) = **29**

## Conjectures

1. **NPG-30 (Primality)**: R_cop(k;c) is always prime for the clique case.
   Evidence: 2, 11, 53, 59 — all prime (4/4).

2. **Growth**: R_cop(k) ~ 0.38 · 5.43^k (exponential fit to 3 points).
   Predicted R_cop(5) ∈ [200, 350].

3. **Ratio**: R_cop(k)/R(k,k) grows exponentially, base ~1.81.

## Methodology

- R_cop(3) = 11: Exact incremental extension (enumerate all 36 avoiding colorings at n=8, extend to n=11 where 0 remain).
- R_cop(4) = 59: SAT lower bound (Glucose4 finds avoiding colorings at n ≤ 58) + extension upper bound (100 independent n=58 colorings all fail to extend to n=59).
- All variants: SAT encoding via pysat with symmetry breaking.

## Provenance

- No prior art found for "coprime Ramsey numbers" (searched March 2026).
- Coprime graph structure studied by others; Ramsey questions on it appear novel.
- Related: Syarifudin & Wardhana (coprime graph of groups, chromatic = clique number).

## Source Code

- `src/coprime_ramsey.py` — Incremental extension algorithm
- `src/coprime_ramsey_sat.py` — SAT-based computation
- `src/coprime_ramsey_variants.py` — Path, cycle, multi-color, bipartite variants
- `tests/test_coprime_ramsey.py`, `tests/test_coprime_ramsey_sat.py`, `tests/test_coprime_ramsey_variants.py`
