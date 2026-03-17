# Cross-Domain Connections

Connections discovered between our number-theoretic work and other fields.

## Schur-Sidon Fourier Bridge (Math: Additive Combinatorics)

The same Fourier rigidity constrains both Schur numbers (#483) and Sidon sets (#43):
- Sum-free sets: spectral concentration grows linearly (flatness ratio ~N)
- Sidon sets: spectrally flat (ratio ~2)
- Gap: 31-104x across tested N values
- Largest simultaneously sum-free AND Sidon set has density → 0

## Coprime Graph as Statistical Mechanics (Physics)

The coprime Ramsey problem maps to an antiferromagnetic spin model:
- Each edge has spin ±1 (color)
- Forbidden monochromatic cliques = antiferromagnetic constraint
- Phase transition at R_cop(k) corresponds to a "critical temperature"

## SAT Phase Transition (CS Theory)

Coprime Ramsey SAT instances exhibit:
- Clause/variable ratio ~109 at R_cop(4)=59 (far above random 3-SAT threshold ~4.27)
- Easy-SAT below threshold, hard-UNSAT at threshold
- The structural (non-random) nature makes LLL bounds very loose

## Survival Analysis of Problem Resolution (Statistics)

Treating problem resolution as censored survival data:
- Competing risks: proved vs disproved
- Cox proportional hazards: which features predict faster resolution?
- AI changepoint detection in the hazard function

## Number-Theoretic Graph Taxonomy (Combinatorics × Number Theory)

Multiple number-theoretic graphs studied:
- Coprime graph: R_cop(3)=11, R_cop(4)=59 (this work)
- Divisibility graph: sparser, different Ramsey behavior
- GCD-d graph: Ramsey numbers depend on d
- Multiplicative Ramsey: MS(1)=3, MS(2)=31

## Information-Theoretic Channel Capacity

The "avoiding coloring channel" has capacity:
- log₂(156) / 31 ≈ 0.24 bits/edge at n=10 (R_cop(3)-1)
- Capacity → 0 at R_cop(k), consistent with Shannon's noisy channel theorem
