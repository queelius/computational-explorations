# Problem #143: Resolution Status

## Problem Statement

Let $\mathcal{A} \subset (1, \infty)$ be countably infinite such that for all distinct $x, y \in \mathcal{A}$ and all integers $k \geq 1$:

$$|kx - y| \geq 1.$$

Does this imply:
1. $\sum_{x \in \mathcal{A}} \frac{1}{x \log x} < \infty$? **(OPEN)**
2. $\sum_{\substack{x < n \\ x \in \mathcal{A}}} \frac{1}{x} = o(\log n)$? **(RESOLVED)**

**Prize**: $500 (Erdos, 1997)

---

## Verdict

**PARTIALLY RESOLVED.** The second conclusion is fully proved by Koukoulopoulos, Lamzouri, and Lichtman (2025). The first (stronger) conclusion remains open.

---

## Resolution of Part 2: $\sum 1/x = o(\log n)$

### Theorem (KLL 2025, arXiv:2502.09539)

> **Theorem 1.** Let $\mathcal{A} \subset \mathbb{R}_{\geq 1}$ be discrete. Suppose
> $$\limsup_{x \to \infty} \frac{1}{\log x} \sum_{\alpha \in \mathcal{A} \cap [1,x]} \frac{1}{\alpha} > 0.$$
> Then, for every $\varepsilon > 0$, there exist distinct $\alpha, \beta \in \mathcal{A}$ and a positive integer $n$ such that $|n\alpha - \beta| < \varepsilon$.

A subsequent **Remark** in the paper notes that this trivially yields *infinitely many* such pairs for every $\varepsilon > 0$, by iteratively removing found pairs and reapplying the theorem.

### Contrapositive Argument

The contrapositive of KLL Theorem 1 states:

> If $\mathcal{A} \subset \mathbb{R}_{\geq 1}$ is discrete and there exists $\varepsilon > 0$ such that $|n\alpha - \beta| \geq \varepsilon$ for all distinct $\alpha, \beta \in \mathcal{A}$ and all positive integers $n$, then
> $$\limsup_{x \to \infty} \frac{1}{\log x} \sum_{\alpha \in \mathcal{A} \cap [1,x]} \frac{1}{\alpha} = 0.$$

### Application to Problem #143

**Step 1.** Assume the hypothesis of Problem #143: $\mathcal{A} \subset (1, \infty)$ with $|kx - y| \geq 1$ for all distinct $x, y \in \mathcal{A}$ and all $k \geq 1$.

**Step 2.** Check discreteness: Taking $k = 1$ gives $|x - y| \geq 1$ for all distinct $x, y$. Points are separated by at least 1, so $\mathcal{A}$ is discrete (no accumulation points).

**Step 3.** The hypothesis gives $|n\alpha - \beta| \geq 1$ for all distinct $\alpha, \beta$ and all $n \geq 1$. This is the contrapositive hypothesis with $\varepsilon = 1$.

**Step 4.** The KLL theorem states "for every $\varepsilon > 0$", which is universal over all positive $\varepsilon$. In particular, $\varepsilon = 1$ is covered. (In fact, Section 2.1 of the paper explicitly reduces to the $\varepsilon = 1$ case by rescaling.)

**Step 5.** By the contrapositive:
$$\limsup_{x \to \infty} \frac{1}{\log x} \sum_{\alpha \in \mathcal{A} \cap [1,x]} \frac{1}{\alpha} = 0.$$

**Step 6.** By definition of $\limsup = 0$:
$$\sum_{\substack{x \in \mathcal{A} \\ x \leq n}} \frac{1}{x} = o(\log n). \qquad \blacksquare$$

### Verification Checklist

| Question | Answer | Evidence |
|----------|--------|----------|
| Does KLL apply to real $\mathcal{A}$? | **YES** | Theorem stated for $\mathcal{A} \subset \mathbb{R}_{\geq 1}$ |
| Does $\varepsilon = 1$ work? | **YES** | "For every $\varepsilon > 0$" is universal; Section 2.1 reduces to $\varepsilon = 1$ |
| Is $\mathcal{A}$ discrete under #143? | **YES** | $|x - y| \geq 1$ for distinct elements |
| Does $\limsup = 0$ mean $o(\log n)$? | **YES** | $f(n)/g(n) \to 0$ iff $f = o(g)$ |
| Any logical gap? | **NONE** | Chain is: #143 hypothesis $\Rightarrow$ contrapositive hypothesis $\Rightarrow$ conclusion |

---

## Part 1 Remains Open: $\sum 1/(x \log x) < \infty$

### Why KLL Does Not Resolve Part 1

Part 1 asks whether $\sum_{x \in \mathcal{A}} \frac{1}{x \log x} < \infty$. This is **strictly stronger** than Part 2:

By partial summation, if $\sum 1/(x \log x) < \infty$, then $\sum_{x \leq n} 1/x = o(\log n)$. But the converse fails: there exist sequences with $\sum_{x \leq n} 1/x = o(\log n)$ but $\sum 1/(x \log x) = \infty$.

KLL's theorem addresses condition (1.3) in their paper (the logarithmic density condition) but explicitly does NOT address condition (1.2) (the $\sum 1/(x \log x)$ divergence condition). The authors write that condition (1.2) "might indeed be possible" but leave it unresolved.

### What Would Be Needed

To resolve Part 1, one would need to show: under the #143 hypothesis, not just $\limsup (1/\log x) \sum 1/\alpha = 0$, but the stronger quantitative bound $\sum 1/(\alpha \log \alpha) < \infty$.

This requires a more refined density estimate. KLL shows zero logarithmic density; Part 1 needs something like:
$$\sum_{\alpha \in \mathcal{A} \cap [x, 2x]} \frac{1}{\alpha} = O(1/\log x)$$
or equivalently $|\mathcal{A} \cap [x, 2x]| = O(x / \log x)$.

### Connection to Erdos Primitive Set Conjecture

For **integer** primitive sets, Lichtman (2022, arXiv:2202.02384) proved $\sum 1/(a \log a) \leq \sum 1/(p \log p)$ where $p$ ranges over primes. This resolves Part 1 for integer sets. The gap is extending this to real sets satisfying the dilation condition.

---

## erdosproblems.com Status

The website lists Problem #143 as **OPEN** (as of the last update), but acknowledges the KLL result on the second part:

> "Koukoulopoulos, Lamzouri, and Lichtman proved that we must have $\sum_{\substack{x < n \\ x \in A}} \frac{1}{x} = o(\log n)$."

The problem remains listed as open, presumably because the stronger Part 1 is unresolved.

---

## Summary

| Part | Statement | Status | Resolved By |
|------|-----------|--------|-------------|
| 2 | $\sum_{x \leq n} 1/x = o(\log n)$ | **RESOLVED** | KLL 2025 (contrapositive of Theorem 1) |
| 1 | $\sum 1/(x \log x) < \infty$ | **OPEN** | — |

**The $500 prize**: Since Part 1 remains open, and Erdos's phrasing uses "or" between the two conditions, the prize status depends on whether resolving Part 2 alone qualifies. The erdosproblems.com listing still shows the problem as open with the prize available.

---

## References

1. D. Koukoulopoulos, Y. Lamzouri, J.D. Lichtman, "Erdos's integer dilation approximation problem and GCD graphs," arXiv:2502.09539 (2025). [link](https://arxiv.org/abs/2502.09539)

2. J.D. Lichtman, "A proof of the Erdos primitive set conjecture," arXiv:2202.02384 (2022). [link](https://arxiv.org/abs/2202.02384)

3. D. Koukoulopoulos, J. Maynard, "On the Duffin-Schaeffer conjecture," Annals of Mathematics 192 (2020), 251--307.

4. Erdos, "Some of my favourite problems which recently have been solved," Proc. Int. Conf. Number Theory (1997), 59--79.
