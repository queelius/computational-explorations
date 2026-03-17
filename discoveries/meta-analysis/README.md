# Meta-Analysis of Mathematical Problem Solving

## The Erdős Problem Acceleration

213 problems solved between Aug 2025 and March 2026 (from 1,183 total).
Monthly rate: ~30/month. 118 Lean-formalized. AI tools (GPT-5.2, Aristotle) involved in multiple solutions.

## What Makes Problems Solvable?

| Feature | Solved (mean) | Open (mean) | Signal |
|---------|--------------|-------------|--------|
| Graph theory tag | 0.257 | 0.198 | Solved+ |
| Number theory tag | 0.418 | 0.522 | Open+ (harder) |
| OEIS connections | 0.224 | 0.471 | Open+ (studied but resistant) |
| Analysis tag | 0.087 | 0.049 | Solved+ |

## Resolution Cascade Timing

All active tag families show bursty resolution patterns (coefficient of variation > 1.0).
Most overdue families: factorials (10.87x), primes (5.00x), chromatic number (4.60x).

## Coprime Ramsey Primality (NPG-30)

All 4 known coprime clique Ramsey values are prime: {2, 11, 53, 59}.
15 of 18 computed coprime Ramsey invariants (including paths, cycles, bipartite) are prime.

Mechanism: primes p have φ(p) = p-1, creating maximum connectivity when added as a new vertex.

## The 6/π² Ubiquity

The constant 6/π² = 1/ζ(2) ≈ 0.6079 appears as:
- Coprime edge density
- Squarefree integer density
- Coprime Ramsey transition density (~0.62 at thresholds)
- Primitive set coprime density (top layer)

## Cross-Domain Connections

- **Survival analysis**: Problem resolution modeled as censored survival data (Kaplan-Meier, Cox hazards)
- **Information theory**: Channel capacity of avoiding colorings approaches 0 at R_cop(k)
- **Computational complexity**: SAT phase transition at coprime Ramsey thresholds
- **ML prediction**: Feature importance for problem solvability
