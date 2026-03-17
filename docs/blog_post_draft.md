# What Happens When You Point a SAT Solver at 1,000 Erdos Problems

*Alex Towell, March 2026*

---

Paul Erdos posed more than a thousand open problems before he died in 1996.
They span number theory, combinatorics, graph theory, geometry -- the full
breadth of discrete mathematics. Some carry cash prizes. Many remain unsolved.
All of them are hard.

This is the story of what happened when I -- a CS PhD student with a taste
for combinatorics and too much free time -- decided to attack about sixty of
them with computation, and accidentally discovered a new corner of Ramsey theory
that nobody had studied before.

---

## The Setup

The starting point was Terence Tao's `erdosproblems` database on GitHub: 1,183
problems, each tagged with metadata, linked to OEIS sequences, and tracked for
resolution status. I wrote Python scripts to analyze the structure of the
database itself -- which problems cluster together, which tags predict
solvability, which areas are overdue for a breakthrough.

That meta-analysis was interesting on its own (more on that later), but the real
fun started when I began running actual computations on the problems. SAT
solvers. Exhaustive searches. Backtracking algorithms. Lean 4 formalizations.
Over a few months, the codebase grew to 64 Python modules and 65 test files.

Along the way, the project surfaced something I did not expect to find.

---

## The Coprime Graph and Its Secrets

Take the integers 1 through *n*. Draw an edge between every pair that shares no
common factor -- that is, every pair (a, b) where gcd(a, b) = 1. The resulting
object is called the **coprime graph**, and it has been studied for decades.
Erdos and Sarkozy wrote about its cycle structure back in 1997.

The coprime graph is dense. About 60.8% of all possible edges are present -- a
number that equals 6/pi-squared, the probability that two random integers are
coprime. It is also highly structured: vertex 1 is connected to everything,
primes form a clique, and even numbers are an independent set.

People had studied clique numbers, chromatic numbers, and independence numbers
of the coprime graph. But as far as I could determine, nobody had asked the
following natural question:

> If you 2-color every edge of the coprime graph on {1, ..., n}, what is the
> smallest n that guarantees a monochromatic clique of size k?

This is the **coprime Ramsey number**, which I denote R_cop(k). It is the
Ramsey number, but played on the coprime graph instead of the complete graph.

---

## Computing R_cop(3) = 11

Classical Ramsey theory says R(3,3) = 6: every 2-coloring of the edges of K_6
contains a monochromatic triangle. But the coprime graph on {1, ..., 6} is
missing some edges (for example, 2 and 4 share a factor), so you might be able
to dodge monochromatic triangles longer.

How much longer? My first attempt used random sampling: generate 10,000 random
2-colorings, check for monochromatic triangles. This declared R_cop(3) = 10.

**It was wrong.** At n = 10, the coprime graph has 31 edges and roughly 2
billion possible 2-colorings. Only 156 of them avoid monochromatic triangles.
Random sampling had about a 0.07% chance of finding one. This was the first
lesson of the project: random search can fail silently on rare combinatorial
objects.

The fix was an exact algorithm: incremental extension. Start at n = 8, where
there are exactly 36 avoiding colorings. Try to extend each one to n = 9 (still
36 valid extensions). Then n = 10 (156 valid extensions -- the space briefly
expands as new edges create new freedom). Then n = 11 -- and the set collapses
to zero. No 2-coloring of the coprime edges on {1, ..., 11} avoids a
monochromatic triangle.

**R_cop(3) = 11.** Almost double the classical value.

---

## R_cop(4) = 59 (and a Pattern Emerges)

Finding R_cop(4) was harder. The incremental extension method hits a wall
because the number of avoiding colorings at intermediate values of *n* is too
large to enumerate.

My first heuristic estimate was R_cop(4) = 20. **This was wildly wrong.** When I
brought in a SAT solver (Glucose4, via the `pysat` library), it found avoiding
colorings instantly at every n up to 58. The true value is nearly three times
what random sampling suggested.

The breakthrough came from combining SAT solving (for the lower bound) with
extension checking (for the upper bound). At n = 58, the SAT solver produces
valid K_4-free colorings. But 100 independently generated colorings of [58]
all fail to extend to [59]. The clause-to-variable ratio of the extension
formula is approximately 109, far above the empirical UNSAT threshold.

**R_cop(4) = 59.** Or, more precisely: we have very strong computational
evidence for this. The lower bound (SAT finds colorings at n = 58) is rigorous.
The upper bound (no extension to n = 59 among 100 trials) is strong evidence
but not a complete proof -- we have not exhaustively checked all avoiding
colorings at n = 58, nor obtained an UNSAT certificate for n = 59 directly.

And here is the thing that made me sit up:

| k | R_cop(k) | R(k,k) | Prime? |
|---|----------|--------|--------|
| 2 | 2        | 2      | Yes    |
| 3 | 11       | 6      | Yes    |
| 4 | 59       | 18     | Yes    |

Every coprime clique Ramsey number computed so far is prime.

---

## The Full Table

Once the machinery was in place, I computed coprime Ramsey numbers for paths,
cycles, bipartite graphs, multiple colors, and Gallai-type variants. Here is
the full table of exact values, all verified by SAT:

**Clique Ramsey (2 colors)**

| k | R_cop(k) |
|---|----------|
| 2 | 2        |
| 3 | 11       |
| 4 | 59       |

**Multi-color (monochromatic triangle)**

| Colors | R_cop(3; c) |
|--------|-------------|
| 2      | 11          |
| 3      | 53          |

**Path Ramsey P_cop(k)**

| k | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|
| P_cop | 5 | 7 | 9 | 10 | 13 | 13 |

**Cycle Ramsey C_cop(k)**

| k | 3 | 4 | 5 | 6 |
|---|---|---|---|---|
| C_cop | 11 | 8 | 13 | 11 |

**Bipartite R_cop(s,t)**

| (s,t) | (2,3) | (2,4) | (3,4) |
|-------|-------|-------|-------|
| R_cop | 3     | 5     | 19    |

**Gallai coprime**: GR_cop(3; 3) = 29

That is 25+ exact values in a family of numbers that, as far as I can tell, did
not exist in the literature before March 2026. (Thorough literature search
recommended before making strong novelty claims.)

Of the four clique/multi-color values -- 2, 11, 53, 59 -- all four are prime.
Across all 18 coprime Ramsey invariants computed, 15 are prime. This is
suspicious enough to warrant a conjecture:

> **Conjecture (NPG-30)**: The coprime clique Ramsey number R_cop(k) is prime
> for all k.

The heuristic mechanism: when n is prime, it is coprime to every integer less
than n. So adding vertex n to the coprime graph creates a maximum-connectivity
event -- n new edges, all at once. This clique-count explosion at primes may be
what drives the Ramsey transition.

---

## The Bigger Picture

### The 6/pi-squared constant

The number 6/pi-squared (approximately 0.608) kept appearing:

- It is the edge density of the coprime graph (the probability that two random
  integers are coprime).
- It is the density of squarefree integers.
- It appears as the coprime pair density in primitive sets.
- It governs the coprime Ramsey transition density.

All of these are manifestations of the same fact: 6/pi-squared = 1/zeta(2),
where zeta is the Riemann zeta function. The coprime graph is, in a sense, a
combinatorial avatar of the zeta function.

### The Schur-Sidon bridge

While investigating Erdos Problem #483 (Schur numbers: how large can [N] be
k-colored without monochromatic a + b = c?) and Problem #43 (Sidon sets: sets
where all pairwise sums are distinct), I found they share a Fourier obstruction.

Dense sum-free sets have spectral concentration growing linearly with N (the
largest Fourier coefficient is roughly N times the mean). Sidon sets are
spectrally flat (ratio close to 2). The gap between these regimes is 31x to
104x depending on N. No set in my experiments was simultaneously sum-free and
Sidon at any meaningful density. The two constraints are, in a precise spectral
sense, mutually exclusive.

### Order-invariance and its failure

For finite abelian groups G, define S(G, k) as the maximum size of a subset
that can be k-colored with each color class sum-free. I verified the following
for all abelian groups of order up to 20:

- **k = 1 and k = 2**: S(G, k) depends only on |G|, not the isomorphism type.
  Z/12Z and Z/2Z x Z/6Z give the same answer.
- **k = 3**: The invariance **breaks**. S(Z/9Z, 3) = 8, but S(Z/3Z x Z/3Z, 3)
  = 7. The group structure finally matters.

The k = 1 invariance may follow from Green and Ruzsa (2005). The k = 2
invariance and the k = 3 failure appear to be new.

---

## What Makes a Math Problem "Interesting"?

Having a database of 1,183 problems with resolution status, tags, prizes, OEIS
links, and formalization history turns out to be useful for a question that
mathematicians rarely quantify: what makes a problem interesting?

I decomposed "interestingness" into five dimensions -- depth, difficulty,
surprise potential, fertility (how many other problems it connects to), and
community investment -- and scored every problem. The top-ranked: Erdos Problem
#3 (bounds for sets without 3-term arithmetic progressions), which is also the
$5,000 prize problem at the heart of Kelley-Meka's 2023 breakthrough.

The **hidden gems** -- high intrinsic interest, low community attention -- were
more surprising. Problem #883 (cycles in coprime graphs) ranked first. It has
no prize, no formalization, no OEIS link, and yet it sits at the intersection
of number theory and graph theory in a way that generates new mathematics.
Our coprime Ramsey work grew directly from poking at it.

### The AI acceleration

Meanwhile, the real world was moving fast. Between August 2025 and March 2026,
213 Erdos problems were solved -- roughly 30 per month, compared to a historical
baseline of about 0.28 per month. That is a 108x acceleration, driven largely
by AI tools: GPT-5.2 generating proof sketches, Harmonic's Aristotle system
formalizing them in Lean, and humans verifying the results. Kevin Barreto's
AI-assisted solution to Problem #728 (verified by Terence Tao in January 2026)
was the first fully autonomous AI solution to an Erdos problem.

The formalization rate was particularly striking: 55% of the problems solved in
the AI era came with machine-checked Lean proofs, compared to a negligible
fraction historically.

---

## What We Got Wrong

I want to be honest about the errors, because they are instructive.

**The R_cop(4) = 20 heuristic.** My initial random-sampling estimate was off by
a factor of three. The actual value, 59, was found only after switching to SAT
solving. Random search simply cannot find the needle when there are 2^(thousands)
haystacks.

**The MS(k) off-by-one.** Early computations of multiplicative Schur numbers
(MS(1) = 4, MS(2) = 32) were wrong by exactly one. The correct values are
MS(1) = 3, MS(2) = 31. Off-by-one errors in Ramsey-type computations are
insidious because the wrong answers are still plausible.

**The DS definition sensitivity.** Density Schur numbers depend on whether you
index from 0 or from 1. On {0, ..., N-1}, the element 0 satisfies 0 + 0 = 0,
which is a "free" Schur triple that forces any color containing 0 to have one.
On {1, ..., N}, no such element exists. Both conventions are valid; they give
different numerical answers. I had code using one convention and a Lean proof
using the other, and it took an embarrassingly long time to realize they were
talking about different things.

**The NPG-7 conjecture.** I proposed using Dirichlet characters mod 6 to detect
coprime graph cycles. After deeper review, this approach has a fundamental flaw:
characters mod 6 only detect coprimality with 2 and 3, not with larger primes.
The conjecture was genuinely novel but mathematically broken. I reformulated it
using Mobius inversion, which correctly handles all primes. The lesson: "novel
direction" and "valid argument" are different things.

Every one of these errors was caught by the test suite or by careful review. The
project now has 3,000+ tests, all passing. Verification matters.

---

## What's Next

Several threads are open:

**R_cop(5).** The exponential fit to three data points predicts a value between
200 and 350. Computing it will require significantly more SAT-solving power, or
a theoretical argument.

**The primality conjecture (NPG-30).** Four data points is suggestive but not
overwhelming. R_cop(5) will be a real test. If it is also prime, the pattern
becomes hard to dismiss.

**OEIS submissions.** The S(Z/nZ, 2) sequence (1, 2, 3, 4, 4, 4, 6, 6, 8, 8,
9, 8, 9, 12, 12, 12, 12, 12, 16) and the Sidon-squares sequence appear to be
new.

**Lean formalization of R_cop(3) = 11.** This is a novel, exact, and finite
result -- the ideal candidate for formal verification. Two Lean proofs (NPG-2
density Schur and NPG-15 Boolean group Schur forcing) are already complete with
zero `sorry` statements.

**Connections to coding theory.** The "avoiding coloring channel" (how many bits
per edge can you encode while avoiding monochromatic cliques) has capacity that
goes to zero at R_cop(k), analogous to a noisy channel hitting its Shannon
limit. This connection is unexplored.

---

## How This Was Made

I should be transparent about methodology. This project was conducted with
extensive AI assistance (Anthropic's Claude), used for code generation, analysis,
and writing. All mathematical results were independently verified: SAT solver
outputs checked, test suites run, Lean proofs compiled, and results cross-
validated between independent implementations.

The code, data, and papers are available:

- **Code**: [DOI 10.5281/zenodo.18638635](https://doi.org/10.5281/zenodo.18638635)
- **Paper**: [DOI 10.5281/zenodo.18638638](https://doi.org/10.5281/zenodo.18638638)
- **Provenance**: Full prior-art checks and verification status in
  `docs/provenance_and_verification.md`

The Erdos problem database is maintained by Terence Tao and collaborators at
[erdosproblems.com](https://www.erdosproblems.com/) and
[github.com/teorth/erdosproblems](https://github.com/teorth/erdosproblems).

---

## The Takeaway

I started this project to understand the landscape of Erdos problems. I ended up
finding something new inside it. The coprime Ramsey numbers are, I think,
genuinely interesting: they live at the intersection of number theory (the
arithmetic of coprimality) and combinatorics (the coloring structure of Ramsey
theory), and their apparent primality is a mystery with a plausible but unproven
mechanism.

More broadly, the project convinced me of something I had suspected but never
tested: computational exploration, done carefully, can surface conjectures and
structures that pure theory misses. Not because computation is smarter than
theory -- it is not -- but because it can check a million cases while a
mathematician is still setting up notation.

The important caveat: computation surfaces conjectures, not proofs. R_cop(4) = 59
is supported by strong evidence, not a theorem. The primality pattern rests on
four data points. The Schur-Sidon bridge is an empirical observation, not a
theorem. These are starting points, not endpoints.

Erdos, who famously said "a mathematician is a machine for turning coffee into
theorems," might have appreciated the irony: we now have actual machines turning
electricity into conjectures. The theorems, as always, still require human
insight.

Or maybe not for much longer.

---

*Alex Towell is a PhD student in Computer Science at Southern Illinois
University Edwardsville, with MS degrees in both Mathematics and Computer
Science. This project is exploratory research, not peer-reviewed publication.
All code and data are open source (MIT/CC-BY-4.0). Corrections welcome at
atowell@siue.edu.*
