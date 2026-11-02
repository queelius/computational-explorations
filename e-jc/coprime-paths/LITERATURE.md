# Literature and contribution boundary

Checked October 18, 2026. This is a bounded comparison for manuscript
preparation, not a systematic novelty review or a claim of priority.

## What the manuscript can claim

The manuscript presents a proof of `P_cop(9) = 17`: positive finite host
certificates force a connected 48-edge `P_10`-free color graph, and a
written classification excludes its required deletion resilience. The
classification is proved in the manuscript rather than attributed to an
unlocated equality theorem. Whether that classification or its application
has appeared elsewhere remains open to a broader literature review.

The values `P_cop(7) = P_cop(8) = 13` were reported publicly before this
work. Their contribution here is reproducibility through independently
validated certificates. Linear growth follows from standard methods;
neither priority nor optimality of `197*pi^2/595` is asserted.

## Closest sources inspected

| Source | Material checked | Consequence for this manuscript |
| --- | --- | --- |
| [Du, Xi, Deng, Ma, v2](https://arxiv.org/html/2605.26815v2) | Proposition 4.6, Table 12, Open Problem 9.2, references | Earlier path values are already attributed to this repository. The complete-target transfer does not establish matching lower bounds for paths. This supports a path-focused follow-up, not a new clique-threshold paper. |
| [Füredi, Kostochka, Verstraëte (2016)](https://arxiv.org/pdf/1507.05338v2) | Theorems 1.4 and 1.6; Lemmas 4.8 and 4.9 | Supplies strict stability, path bounds, and the dense bipartite contraction machinery. These are proof inputs, not contributions of this manuscript. |
| [Füredi, Kostochka, Luo, Verstraëte (2018), published text](https://users.renyi.hu/~furedi/PUBS3/furedi_238_kostochka_ruthluo_verstraete_Erdos-Gallai-stability_II.pdf) | Theorem 2.3; Theorem 4.2; Lemma 4.6; publication metadata | Extends the needed stability argument to orders 11 and 12. The published theorem numbering used in the draft matches the inspected text. DOI: `10.1016/j.disc.2017.12.018`. |
| [Ma and Ning, preprint v2](https://arxiv.org/pdf/1708.00704v2) / [Combinatorica (2020)](https://doi.org/10.1007/s00493-019-3843-4) | Statements in Sections 1.1-1.6, especially Theorems 1.7 and 1.9 | Their minimum-degree refinement also has a strict threshold. See the boundary calculation below; it does not by itself settle the equality case used here. |
| [Ali and Staton (1996)](https://www.combinatorics.org/ojs/index.php/eljc/article/download/v3i1r20/pdf/) | Original Theorem 3 | Gives the minimum-degree-four dichotomy when longest path order is nine and order is at least ten. Every invocation in the draft has order at least eleven. |
| [Balister, Győri, Lehel, Schelp (2008)](https://www.memphis.edu/msci/people/pbalistr/nopk.pdf) | Theorem 1.3 | Gives the bound 42 for a connected 13-vertex graph without a ten-vertex path. The source uses target `P_(k+1)`, so substitute `k=9`. |
| [Erdős and Gallai (1959)](https://web.vu.lt/mif/s.jukna/tropical/Erdos-Gallai-1959.pdf) | Theorem 2.6 | Standard path extremal bound underlying the asymptotic argument. |

## The equality boundary

The universal augmentation of the 17-vertex, 48-edge graph has order
18 and size 65. The FKV/FKVL stability threshold contains

```text
h(18,11,4) = binom(7,2) + 4*(18-7) = 65.
```

For circumference 10, Ma-Ning's notation satisfies
`W_(n,a,10) = H(n,11,a)` and `f(18,4,10) = 65`.
Their Theorems 1.7 and 1.9 require size strictly larger than a maximum
containing this term. This numerical observation rules out applying those
statements directly at equality. It does **not** rule out a deduction from
other results or a previously published equality analysis. The draft
therefore retains the full proof and avoids “first” or “previously unknown.”

## Adjacent work and limits of the search

[Christoph, Müyesser, and Wigderson (2026)](https://arxiv.org/html/2607.02483v1)
give approximate hyperstability for sufficiently large parameters. The
introduction and main statements inspected distinguish that setting from
exact finite stability. No exact 17-vertex conclusion was identified in
those inspected statements; the entire paper was not checked for every
possible implication.

[Liu and Kang (2024)](https://arxiv.org/abs/2312.00620) concern graphs
forbidding both a long path and an additional graph, including connected
extremal results at sufficiently large order. Only the abstract and
publication metadata were checked here; it is not a proof dependency.

The earlier repository comparison also inspected the accessible
[Banerjee preprint](https://arxiv.org/html/2506.10583v1) on structural and
spectral properties of coprime graphs. The final journal text was not
available in that comparison. General web searches for coprime path
Ramsey thresholds and 17-vertex `P_10`-free equality cases are not evidence
that no other literature exists.

Before making a priority claim, extend the search through cited and citing
papers, check relevant final versions, and have a graph theorist assess
whether the equality classification is already a known special case.
The present manuscript remains a working draft pending that judgment and
the author's proof review.
