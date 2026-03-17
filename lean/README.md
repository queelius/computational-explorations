# Lean 4 Formalizations

Lean 4 formalizations of results from the Erdos problems research project.

## File Status

| File | Status | Sorry | Axioms | Theorems | Notes |
|------|--------|-------|--------|----------|-------|
| NPG2_DensitySchur.lean | COMPLETE | 0 | 0 | 12 | DS(2, 1/2) = 5 fully proved |
| Erdos43.lean | PARTIAL | 6 | 0 | 10 | Main theorem proved; sorry in auxiliary lemmas |
| Erdos883.lean | PARTIAL | 7 | 1 | 17 | Main theorem depends on sorry |
| NPG15_SchurGroups.lean | COMPLETE | 0 | 0 | 10 | All theorems proved, including boolean_group_forces_schur |

NPG2_DensitySchur.lean and NPG15_SchurGroups.lean are complete formalizations.

### NPG2_DensitySchur.lean (COMPLETE)

Proves DS(2, 1/2) = 5, the first non-trivial density-relaxed Schur number.
Both lower bound (witness coloring of [4]) and upper bound (pigeonhole on [5])
are fully proved with 0 sorry and 0 axioms. Also proves S(2) = 4 (classical
Schur number) via native_decide.

### Erdos43.lean (PARTIAL)

Formalizes Erdos Problem #43 on Sidon sets with disjoint differences. The main
theorem `erdos43` (C(|A|,2) + C(|B|,2) <= N for difference-disjoint Sidon sets)
is fully proved. The 6 sorry are in auxiliary results: `sidon_size_bound`,
`diffSet_card_lower` (2 sorry), `sidon_energy`, and `sidon_iff_repr` (2 sorry).
None of these are in the dependency chain of the main theorem.

### Erdos883.lean (PARTIAL)

Formalizes Erdos Problem #883 on odd cycles in coprime graphs. The triangle-forcing
case analysis is largely complete, but the main theorem `erdos883` transitively
depends on sorry through `erdos883_triangle` (3 sorry in density argument branches)
and `erdos883_small` (1 sorry, computationally verified in Python). Additional
sorry in `extremalSet_card`, `extremalSet_approx`, and `density_coprime_exists`.
Contains 1 axiom (`bondys_theorem`) used only by a stub that concludes True.

### NPG15_SchurGroups.lean (COMPLETE)

Formalizes Schur numbers in abelian groups (NPG-15). Proves 10 theorems about
sum-free sets, boolean groups, and embedding preservation. The key theorem
`boolean_group_forces_schur` (Theorem B: Boolean Group Schur Forcing) is fully
proved with 0 sorry. The proof splits into two cases: (1) if any nonzero element
shares 0's color, `(a, a, 0)` is a monochromatic triple via the boolean identity
`a + a = 0`; (2) if all nonzero elements share the other color, extract two distinct
nonzero elements `a, b` from `|G| >= 4`, then `(a, b, a+b)` is monochromatic since
`a + b` is a third distinct nonzero element by boolean group properties.

## Build Instructions

Requires Lean 4 and an internet connection (for Mathlib download on first build).

```bash
cd lean/
lake build
```

The first build will download Mathlib, which may take significant time and disk space.
Subsequent builds will be incremental.

## Dependencies

- Lean 4 (v4.16.0, specified in lean-toolchain)
- Mathlib (v4.16.0, specified in lakefile.lean)
