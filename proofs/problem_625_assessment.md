# Erdős Problem #625: Chromatic vs Cochromatic Number

## Problem Statement

For a random graph $G \sim G(n, 1/2)$, does $\chi(G) - \zeta(G) \to \infty$ a.s.?

- **$100 prize** for YES (gap diverges)
- **$1000 prize** for NO (gap bounded)

Here $\zeta(G)$ is the **cochromatic number**: minimum colors where each color class is a clique OR independent set.

## Status: Effectively Resolved (positive answer)

### 2024 Breakthroughs

Three papers in August-September 2024 essentially resolve this:

1. **Steiner (arXiv:2408.02400)**: Shows $\chi(G_n) - \zeta(G_n) \geq n^{1/2-\varepsilon}$ with positive probability for infinitely many $n$.

2. **Heckel (arXiv:2408.13839)**: Proves the gap is not whp bounded by $n^{1/2-o(1)}$.

3. **Heckel (arXiv:2409.17614)**: For ~95% of $n$, $\chi(G) - \zeta(G) \geq n^{1-\varepsilon}$ whp. **Conjectures**: gap $= \Theta(n/(\log n)^3)$ whp.

### Remaining Gap

- The result holds for ~95% of $n$, not all $n$. The missing values occur near independence number transitions.
- The conjectured tight bound $\Theta(n/(\log n)^3)$ is not yet proved.
- An active collaboration (Heckel/Hunter/Steiner/Christoph) is working on full resolution via a two-graph coupling approach.

## Assessment for Our Project

**Prize reality**: The achievable prize is $100 (positive answer), not $1000. Our opportunity scoring was inflated by the $1000 figure.

**Competition**: World-class combinatorialists are actively working on the final 5%. Independent resolution by our project is unrealistic.

**Recommendation**: PASS. Monitor for full resolution. The cascade potential (275 unlocked problems) will activate when Heckel et al. publish the complete result.

## Connections

- Feeds into the chromatic cluster: #593, #74, #630, #631, etc.
- Related to NP-2 (chromatic Sidon hybrid) in our novel problems
- #593 (hypergraph chromatic, $500) is a better independent target in this cluster
