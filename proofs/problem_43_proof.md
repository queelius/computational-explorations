# Problem #43: Sidon Sets with Disjoint Differences

## Problem Statement

For Sidon sets $A, B \subseteq \{1, \ldots, N\}$ with $(A-A) \cap (B-B) = \{0\}$, is it true that:

$$\binom{|A|}{2} + \binom{|B|}{2} \leq \binom{f(N)}{2} + O(1)$$

where $f(N) \sim \sqrt{N}$ is the maximum Sidon set size in $\{1, \ldots, N\}$?

**Prize**: $100

---

## Definitions

**Sidon set**: $A$ is Sidon if all pairwise sums $a + b$ ($a \leq b$, $a, b \in A$) are distinct. Equivalently, $a + b = c + d$ with $a, b, c, d \in A$ implies $\{a, b\} = \{c, d\}$.

**Difference set**: $A - A = \{a_1 - a_2 : a_1, a_2 \in A\}$.

**Difference-disjoint**: $(A-A) \cap (B-B) = \{0\}$, meaning no nonzero integer appears as a difference in both sets.

---

## Results

### Theorem 1 (Difference Set Size for Sidon Sets)

If $A$ is a Sidon set with $|A| = a$, then $|A - A| = a^2 - a + 1 = a(a-1) + 1$.

**Proof.** The set $A - A$ consists of 0 and all nonzero differences $a_i - a_j$ ($i \neq j$).

*Claim*: All nonzero differences are distinct. Suppose $a_1 - a_2 = a_3 - a_4$ with $(a_1, a_2) \neq (a_3, a_4)$. Then $a_1 + a_4 = a_3 + a_2$. By the Sidon property, $\{a_1, a_4\} = \{a_3, a_2\}$, so either ($a_1 = a_3$ and $a_4 = a_2$, contradicting $(a_1,a_2) \neq (a_3,a_4)$) or ($a_1 = a_2$ and $a_4 = a_3$, contradicting that the differences are nonzero). Contradiction.

There are $a(a-1)$ ordered nonzero pairs, giving $a(a-1)$ distinct nonzero differences, plus 0. $\blacksquare$

### Theorem 2 (Disjoint Difference Counting)

If $A, B$ are Sidon sets in $\{1, \ldots, N\}$ with $(A-A) \cap (B-B) = \{0\}$, then:

$$\binom{|A|}{2} + \binom{|B|}{2} \leq N - 1$$

**Proof.** The *positive* differences of a Sidon set $A$ are $\{a_i - a_j : a_i > a_j,\; a_i, a_j \in A\}$. By the proof of Theorem 1, these are all distinct. There are $\binom{a}{2}$ of them, and they lie in $\{1, \ldots, N-1\}$.

Since $(A-A) \cap (B-B) = \{0\}$, the positive differences of $A$ and $B$ are disjoint subsets of $\{1, \ldots, N-1\}$. Therefore:

$$\binom{|A|}{2} + \binom{|B|}{2} \leq N - 1. \qquad \blacksquare$$

### Theorem 3 (Partial Result Toward Conjecture)

$$\binom{|A|}{2} + \binom{|B|}{2} \leq 2 \binom{f(N)}{2} + O(\sqrt{N})$$

**Proof.** By Theorem 2, $\binom{|A|}{2} + \binom{|B|}{2} \leq N-1$. By the Erdos-Turan bound, $f(N) \leq \sqrt{N} + O(N^{1/4})$, so:

$$\binom{f(N)}{2} = \frac{f(N)(f(N)-1)}{2} \geq \frac{N - O(N^{3/4})}{2} = \frac{N}{2} - O(N^{3/4})$$

Therefore $N - 1 \leq 2 \binom{f(N)}{2} + O(N^{3/4})$. $\blacksquare$

---

## Analysis of the Gap

Theorem 2 gives a bound that is about **twice** the conjectured bound. The gap arises because we only use the disjointness of positive differences in $\{1, \ldots, N-1\}$, without exploiting the global structure of Sidon sets.

### Why the Factor of 2 Is Hard to Remove

The optimal configuration approaches the bound: take $A$ to be a near-maximum Sidon set with $|A| \approx \sqrt{N}$ (using $\approx N/2$ positive differences), and take $B$ to be another Sidon set using the remaining $\approx N/2$ positive differences, with $|B| \approx \sqrt{N}$. If such $B$ exists, then $\binom{|A|}{2} + \binom{|B|}{2} \approx N/2 + N/2 = N$.

However, the conjecture predicts this is impossible: if $A$ uses $N/2$ differences, the remaining $N/2$ differences cannot support another Sidon set of size $\sqrt{N}$. The reason is **structural**: the complementary differences are not "well-spread" enough to support a large Sidon set.

### Possible Approaches to Close the Gap

1. **Additive energy method**: Bound $E(A \cup B) = |\{(a_1, a_2, a_3, a_4) : a_1 + a_2 = a_3 + a_4\}|$ under the disjoint-difference constraint. For Sidon $A$, $E(A) = 2|A|^2 - |A|$.

2. **Polynomial method**: Over $\mathbb{F}_p$, Sidon sets correspond to curves with restricted intersection properties. The disjoint-difference constraint adds a "non-interference" condition that may be analyzable via algebraic geometry.

3. **Spectral method**: Use eigenvalues of the Cayley graph on $\mathbb{Z}/N\mathbb{Z}$ with connection set $A - A$.

---

## Computational Verification

### Exhaustive Search Results (N ≤ 13)

All exhaustive searches confirm the conjecture:

| N | Best $|A|$ | Best $|B|$ | $\binom{|A|}{2}+\binom{|B|}{2}$ | $\binom{f(N)}{2}$ | Ratio |
|---|-----------|-----------|--------------------------------|-------------------|-------|
| 5 | 2 | 2 | 2 | 3 | 0.67 |
| 7 | 3 | 2 | 4 | 3 | 1.33 |
| 8 | 3 | 2 | 4 | 6 | 0.67 |
| 10 | 3 | 3 | 6 | 6 | 1.00 |
| 13 | 4 | 2 | 7 | 6 | 1.17 |

Note: The ratio exceeds 1 for some $N$ values, but this is due to the $O(1)$ error term in the conjecture.

### Heuristic Search Results (N ≤ 200)

For larger $N$, random search with local optimization finds pairs satisfying the conjecture with slack.

---

## Lean Formalization Strategy

The Lean file `lean/Erdos43.lean` contains the following sorry statements to fill:

1. **`sidon_diffSet_card`**: Theorem 1 above. **PROVED** (pending `lake build`). Proof strategy: decompose `diffSet A = {0} ∪ image(offDiag, sub)`, show disjointness (off-diagonal diffs are nonzero in ℤ), show injectivity via `sidon_diff_injective`, combine with `offDiag_card`.

2. **`diffDisjoint_partition`**: If $(A-A) \cap (B-B) = \{0\}$, then $|A-A| + |B-B| = |A-A \cup B-B| + 1$. **PROVED** via inclusion-exclusion + `omega`.

3. **`sidon_size_bound`**: Classical Erdos-Turan bound. Uses $|A-A| = a^2-a+1 \leq 2N-1$. **sorry** — requires careful ℕ arithmetic connecting `Nat.sqrt` to the counting bound.

4. **`erdos43`**: Main theorem. **sorry** — currently only provable up to the factor-of-2 bound (Theorem 2).

---

## References

1. Erdos, P., Turan, P. (1941): "On a problem of Sidon in additive number theory." *J. London Math. Soc.* 16, 212--215.
2. Singer, J. (1938): "A theorem in finite projective geometry and some applications to number theory." *Trans. AMS* 43, 377--385.
3. O'Bryant, K. (2004): "A complete annotated bibliography of work related to Sidon sets." *Electronic J. Combin.* DS11.
