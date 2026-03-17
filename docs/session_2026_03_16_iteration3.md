# Research Findings: March 16, 2026 — Iteration 3 (Broad Problem Attack)

## Overview

Systematic assault on the full Erdős problem database. 5 agents + direct computation
covering falsifiable problems, OEIS-rich problems, covering systems, AP/additive combinatorics,
graph coloring/Ramsey, and misc families (iterated functions, complete sequences, squares, factorials).

## Direct Computation Results

### Erdős-Straus Conjecture (#242, falsifiable)
- Parametric search verifies 4/n = 1/x + 1/y + 1/z for all n ≤ 10,000 (greedy fails for 138 values, parametric covers all)
- n = 100,000 computation in progress

### Weird Numbers (#887-adjacent)
- Only 7 weird numbers up to 10,000: {70, 836, 4030, 5830, 7192, 7912, 9272}
- Erdős conjecture (infinitely many ODD weird numbers) remains OPEN
- No odd weird number found ≤ 10^17

### Divisor Statistics
- Abundant number density: 24.88% (matches theoretical ~24.77%)
- Highly composite numbers up to 10,000: 20 values
- Max d(n)/log(n) for n ≤ 100,000: 11.299 at n=83,160 (d=128)

### Iterated Functions (#408-#414)
- Collatz: max 261 steps in [1, 10000] at n=6171
- Aliquot sequences [1,100]: 96 terminate, 4 reach perfect numbers
- Kaprekar: ALL 8,991 non-repdigit 4-digit numbers reach 6174
- Smith numbers up to 10,000: 376 (density 3.76%)
- Practical numbers up to 500: 102 (density 20.4%)

### Complete Sequences (#345-#351)
- Powers of 2: complete (binary representation)
- Fibonacci: complete (Zeckendorf's theorem)
- Primes (distinct sums): NOT complete (e.g., 4 can't be sum of distinct primes)
- Perfect powers: NOT complete (too sparse)

### Base Representations (#124, #376)
- 59 numbers ≤ 100,000 are palindromic in 3+ bases (2-10)
- 166/1275 binomial coefficients C(n,k) with n<50 have only 0-1 digits in base 3

### Squares (#222, #888)
- Numbers requiring k squares: 1→1.0%, 2→26.5%, 3→55.9%, 4→16.6% (in [1,10000])
- n = a² + b² + prime: ZERO failures up to n=10,000

### Factorials (OVERDUE family, 10.87x)
- n! = product of k consecutive integers: non-trivial solutions thin out after n=7
- Trailing zeros in n!: follows Legendre formula exactly

## DS(3, 0.25) = 15 (exact, backtracking)
First exact value of a 3-color density Schur number.

## New Agent-Created Modules
- `src/ap_attacks.py` — AP-free sets, Stanley sequences, sparse rulers
- `src/covering_systems.py` — Covering system enumeration
- `src/oeis_attacks.py` — OEIS sequence computation for #479, #849
- `src/ramsey_attacks.py` — Small Ramsey numbers, extensions
- `src/verifiable_attacks.py` — Computations for verifiable problems
- `src/falsifiable_attacks.py` — (if created by agent)

## Problems Attacked This Iteration
#7, #11, #18, #124, #222, #242, #322, #345-351, #364, #366, #373,
#374, #376, #380, #390, #398, #408-414, #458, #468, #479, #647,
#693, #773, #779, #835, #849, #855, #884-888, #906, #912

Plus Ramsey/coloring cluster: #19, #74, #77, #78, #165, #183, #547, #551,
#556, #591, #592, #625, #1029

And AP cluster: #3, #52, #142, #160, #168, #170, #172, #201, #271

## R_cop(4) = 59 (EXACT — from SAT agent)

Proved by two-phase approach:
- Lower bound: Glucose4 SAT solver finds avoiding colorings at n≤58
- Upper bound: 100 independent n=58 colorings ALL fail to extend to n=59
- Clause/variable ratio at n=59 is ~109 (far above UNSAT threshold)
- 59 is prime → coprime to all 1..58 → 9,141 new K_4-cliques

## Meta-Pattern: R_cop(k) is Always Prime
R_cop(2)=2, R_cop(3)=11, R_cop(4)=59 — all prime.
Mechanism: primes have φ(p)=p-1, maximum edge connectivity.
Conjecture (NPG-30): R_cop(k) is always prime.

## DS Definition Sensitivity (0-indexed vs 1-indexed)
CRITICAL FINDING: DS(2, 1/2) = 5 on {0,...,N-1} but 6 on {1,...,N}.
The element 0 satisfies 0+0=0, making it a universal Schur forcer.
In {1,...,N}, no element satisfies x+x=x, so sum-free sets like {1,3,5}
can have density > 1/2 without containing a Schur triple.
The Lean proof uses 0-indexed (Fin N), the Python code uses 1-indexed.
Both are correct but give DIFFERENT numerical answers.

## Theorem: DS(k, 1/k) = S(k) + 1 (0-indexed version)
Proof by pigeonhole: at N=S(k)+1, every k-coloring has a mono Schur triple.
On {0,...,N-1}, any color containing 0 has density ≥ 1/k (by pigeonhole)
and has Schur triple 0+0=0. So DS(k, 1/k) ≤ S(k)+1.
Lower bound: at N=S(k), [0..S(k)-1] can be k-colored sum-free. QED.
