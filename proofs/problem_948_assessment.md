# Erdős Problem #948: FS-Set Colour Avoidance Under Growth Constraints

## Problem Statement

In any $k$-colouring of $\mathbb{N}$, does there exist a sequence $a_1 < a_2 < \cdots$
with $a_n < f(n)$ for infinitely many $n$, whose FS-set (all finite subset sums)
misses at least one colour?

Here $f$ is a prescribed growth bound.

## Context and Related Problems

| Problem | Status | Relationship |
|---------|--------|-------------|
| #532 (Hindman) | Solved (1974) | No growth constraint → monochromatic FS-set exists |
| #54 | Solved (CFP 2021) | Ramsey-complete sequences |
| #55 | Solved (CFP 2021) | r-complete sequences |
| #439 | Solved (Khalfalah-Szemerédi) | $x + y = \text{square}$ partition regularity |
| #894 | Solved (Katznelson) | Lacunary sequences and chromatic number |

### Hierarchy of FS-set results

1. **Hindman (1974)**: No growth constraint → monochromatic FS-set guaranteed.
2. **Galvin**: Growth constraint → monochromatic FS-set NOT guaranteed.
3. **#948**: Growth constraint → can FS-set at least MISS one colour?

#948 asks for a weaker conclusion than Hindman but under stronger hypotheses (growth constraints).

## Computational Experiments (`src/ip_ramsey.py`)

### Experiment 1: Galvin FS-Set Coverage

Under Galvin colouring ($\chi(n) = v_2(n) \bmod k$), FS-sets of bounded-growth sequences hit ALL $k$ colours:

| Growth Rate | Seq Length | FS Size | Colours Hit | Missed |
|-------------|-----------|---------|-------------|--------|
| Polynomial ($n^2$) | 14 | 946 | 3/3 | 0 |
| Linear (odd numbers) | 20 | 327 | 3/3 | 0 |
| Lacunary ($\times 1.5$) | 13 | 424 | 3/3 | 0 |

**Interpretation**: Galvin colouring is a strong candidate counterexample to #948. Even with growth constraints, FS-sets are rich enough to cover all colours. The 2-adic structure spreads valuations across all finite subset sums.

### Experiment 2: Greedy Minimization

Greedy colouring (minimize FS coverage at each step) achieves:
- $k=2$: best sequence hits only 1/2 colours
- $k=3$: best sequence hits only 1/3 colours

**Caveat**: Only arithmetic-like subsequences were tested. The greedy colouring may fail against more exotic sequence families.

### Experiment 3: Colouring Scheme Comparison ($k=3$, $N=200$)

| Scheme | % All-Hit | Details |
|--------|-----------|---------|
| Galvin ($v_2 \bmod 3$) | 100.0% | 116/116 sequences |
| 3-adic ($v_3 \bmod 3$) | 99.1% | 115/116 sequences |
| Golden rotation | 100.0% | 116/116 sequences |
| Random (seed 42) | 100.0% | 116/116 sequences |

**Interpretation**: All natural colourings have FS-sets that hit all colours. The 3-adic scheme shows a tiny gap (1 miss in 116 trials), suggesting $p$-adic with $p=k$ is slightly more effective at preventing coverage — but still far from a counterexample.

### Experiment 4: Growth Rate Phase Transition ($k=2$, $N=500$)

| Growth $\alpha$ | % All-Hit | Trials |
|-----------------|-----------|--------|
| 1.0 | 100% | 20/20 |
| 1.2 | 100% | 20/20 |
| 1.4 | 100% | 20/20 |
| 1.6 | 100% | 20/20 |
| 1.8 | 100% | 20/20 |
| **2.0** | **68%** | 13/19 |
| 2.2 | 100% | 13/13 |
| 2.4 | 90% | 9/10 |
| 2.6 | 100% | 7/7 |
| 2.8 | 100% | 6/6 |
| 3.0 | 100% | 4/4 |

**Initial finding** (N=500, 20 trials): Apparent phase transition at α≈2 with 68% coverage. However, deep analysis (below) reveals this was a finite-size artifact.

### Experiment 5: Deep Phase Transition (N=2000, 80 trials/α, 21 α-steps)

**Galvin, k=2:**

| α range | Coverage | Avg seq length | Avg FS size |
|---------|----------|---------------|-------------|
| 1.50-1.95 | **100%** | 34-59 | 18K-45K |
| 2.00-2.10 | **100%** | 22-30 | 16K-24K |
| 2.15 | 98.8% | 19 | 12K |
| 2.25-2.50 | 94-100% | 12-16 | 5K-9K |

Critical exponent: $\alpha_{95} = 2.45$. No α reaches 50% coverage.

**3-adic (p=k=2), k=2:** (most effective at preventing coverage)

| α range | Coverage | Note |
|---------|----------|------|
| 1.50-1.95 | 100% | Same as Galvin |
| 2.00 | 98.8% | First drop |
| 2.15 | **93.8%** | Earlier than Galvin |
| 2.50 | **91.3%** | Minimum |

Critical exponent: $\alpha_{95} = 2.15$ — earlier than Galvin's 2.45.

**Galvin, k=3:** (the most informative experiment)

| α range | Coverage | Significance |
|---------|----------|-------------|
| 1.50-2.00 | 100% | Perfect coverage |
| 2.05 | 98.8% | First crack |
| 2.15 | 95.0% | Borderline |
| **2.25** | **84.1%** | **Minimum** |
| 2.30-2.50 | 86-89% | Plateau |

Critical exponent: $\alpha_{95} = 2.2$. Coverage stabilizes around 85-89% for α > 2.25.

**Key revision**: The earlier "68% at α=2.0" was a **small-N artifact** (N=500 with only 19 trials). With N=2000 and 80 trials, Galvin k=2 stays at 100% through α=2.1. The actual critical exponent is scheme-dependent:

| Scheme | k | $\alpha_{95}$ | Min coverage | At α= |
|--------|---|--------------|-------------|-------|
| Galvin | 2 | 2.45 | 94.0% | 2.45 |
| 3-adic | 2 | 2.15 | 91.3% | 2.50 |
| Rotation | 2 | >2.5 | 95.7% | 2.50 |
| Random | 2 | >2.5 | 97.8% | 2.50 |
| **Galvin** | **3** | **2.20** | **84.1%** | **2.25** |

### Interpretation

The coverage decline is driven by **two confounded effects**:
1. **Shorter sequences** at higher α (59 → 12 elements), giving smaller FS-sets
2. **Genuine structural difficulty** of hitting all valuation classes with sparse sums

The fact that coverage **stabilizes around 85-90%** rather than decaying to 0 suggests that even short sequences with large elements generate FS-sets rich enough to usually hit all colours. The 15% miss rate for k=3 at α=2.25 reflects sequences that happen to avoid one valuation class.

## Theoretical Analysis

### Why Galvin Is Hard to Beat

For the Galvin colouring $\chi(n) = v_2(n) \bmod k$:
- $\text{FS}(\{2^0, 2^1, \ldots, 2^{k-1}\}) = \{1, 2, \ldots, 2^k - 1\}$ hits all $k$ colours.
- Even growth-constrained sequences with polynomial growth can reconstruct enough powers-of-2 structure in their FS-set.
- The FS operation creates MANY new elements: $|\text{FS}(A)| \leq 2^{|A|} - 1$, and for Sidon-like sequences it achieves this bound.

### Why 3-adic (p=k) Is Slightly Better

When $p = k$, the $p$-adic valuation partitions numbers more "evenly" across colour classes for numbers near $p^j$. The 3-adic colouring with $k=2$ achieves $\alpha_{95} = 2.15$ vs Galvin's $\alpha_{95} = 2.45$ — the matching of prime base to colour count creates a more efficient barrier.

### The Greedy Gap

The greedy experiment's success (hitting only 1 colour) may be an artifact of the limited sequence search. In theory, for ANY colouring of $\{1, \ldots, N\}$, by the pigeonhole principle, there exist long monochromatic arithmetic progressions — and their FS-sets could hit additional colours.

### Revised Conjecture

Based on the deep analysis, we **revise our conjecture**:

**Conjecture (Positive for #948)**: For any $k$-colouring of $\mathbb{N}$ and any growth bound $f(n) \geq n^{1+\varepsilon}$ ($\varepsilon > 0$), there exists a sequence $a_1 < a_2 < \cdots$ with $a_n < f(n)$ infinitely often, whose FS-set hits all $k$ colours.

This would mean **#948 has a positive answer** — you CANNOT force the FS-set to miss a colour under any superlinear growth bound.

**Rationale**: The coverage stabilization at 85-90% for finite N suggests that the misses are finite-size effects. As N → ∞, sequences become longer and FS-sets become richer, driving coverage toward 100%.

**Confidence**: Low-medium. The asymptotic extrapolation from finite experiments is speculative. The stabilization could also reflect a genuine 10-15% fraction of "bad" starting configurations that persist at all scales.

## Assessment for Our Project

### Tractability: MEDIUM

- Strong technique match (additive combinatorics, Fourier analysis, Ramsey theory)
- 5 solved analogues provide proof templates
- But: no clear path to full resolution. The phase transition at $\alpha = 2$ is interesting but not yet exploitable.

### Prize: None listed

- Unlike #625 ($1000), #948 has no prize. Value is purely intellectual and cascading.

### Competition: LOW

- No recent (2024-2025) preprints directly addressing #948.
- The problem sits in a well-studied area but this specific question seems untouched.

### Recommendation: EXPLORE FURTHER

1. **Deepen the phase transition analysis**: Run larger experiments at $\alpha = 2.0 \pm 0.1$ with N up to 5000.
2. **Test structured colourings**: Try colourings designed to make FS-sets hit all colours (worst case for the positive answer).
3. **Fourier analysis**: Apply Kelley-Meka style Fourier bounds to FS-set colour distribution.
4. **Partial result target**: Prove the Galvin obstruction for $f(n) = n^{1+\epsilon}$ (subquadratic growth).

## Connections

- **#532** (Hindman): Direct parent problem. Hindman → #948 is the weakening step.
- **#483** (Schur/Fourier): Same Fourier techniques apply to FS-set colour distribution.
- **NPG-23** (Primitive-Coprime): FS-sets of coprime-dense sequences may have special structure.
- **Kelley-Meka**: The density increment strategy could bound colour coverage of structured FS-sets.
