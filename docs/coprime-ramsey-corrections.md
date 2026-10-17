# Coprime Ramsey corrections and archival errata

Correction date: **2026-10-17**. This notice accompanies the unchanged original
[manuscript source](../paper/coprime_ramsey_note.tex),
[PDF](../paper/coprime_ramsey_note.pdf), and
[Zenodo paper record](https://zenodo.org/records/19058647). The
[citation and reproducibility audit](coprime-ramsey-citation-audit.md) preserves
the historical evidence and exact verification scope. The later
[E-JC manuscript](../e-jc/coprime-ramsey-ejc.tex) incorporates the proof repairs.
For the subsequent software snapshot and corrected manuscript, see the
[release record](coprime-ramsey-release.md). The original paper archive remains
unchanged.

## Current conclusions

All parameters here color undirected **edges** of the coprime graph on `1..n`.
They differ from the vertex-coloring parameters of Du et al.

| Parameter | Value | Lower and upper evidence |
| --- | --- | --- |
| Two-color triangle | 11 | Full witness at 10; prime clique K_6 at 11 and R(3,3)=6 |
| Two-color K_4 | 59 | Full witness at 58; prime clique K_18 at 59 and R(4,4)=18 |
| Three-color triangle | 53 | Full witness at 52; prime clique K_17 at 53 and R(3,3,3)=17 |

The [dated audit witnesses](audits/coprime-ramsey-2026-10-17/) are new
constructions, independently checked for full edge coverage, palette, and every
relevant clique; they are not recovered historical SAT assignments. Direct SAT
upper-bound searches at 53 and 59 were not rerun in the audit. Their mathematical
upper bounds do not depend on those searches.

The historical 100 failed extensions from 58 to 59 are corroborating samples.
They do not exhaust the avoiding base colorings and cannot establish a universal
upper bound. High clause density likewise does not prove UNSAT.

The edge-clique identity and the Gallai triangle transfer are established in
[Du et al. v2, Theorem 4.4 and Proposition 4.6](https://arxiv.org/html/2605.26815v2).
Thus the value 29 for three-color Gallai triangles is also covered. Paths and
cycles have non-complete targets; the matching pullback lower bound need not
hold. The audit reproduced the shorter path and cycle thresholds, but path
parameters 7 and 8 (counting edges) each timed out after 60 seconds. Their
reported values 13 and 13 retain that qualification.

For R_cop(5), the supported interval is **181–197**, using
[Angeltveit–McKay's R(5,5) <= 46](https://arxiv.org/abs/2409.15709) and the
classical lower bound 43. The candidate primes are 181, 191, 193, 197, not every
integer in the interval. The older 181–211 interval used a stale upper bound;
attributing 48 to that paper was incorrect. See the
[reconciliation note](rcop5-reconciliation.md).

## Errata for the archived original paper

1. **Introduction, restriction argument:** an avoiding coloring of K_n
   restricts to an avoiding coloring of the coprime graph. An arbitrary
   extension in the reverse direction need not avoid monochromatic cliques.
   The valid restriction argument still gives R_cop(k) >= R(k,k).
2. **Proof of 59:** sampled extensions did not prove the upper bound. Replace
   that inference with the prime-clique argument above and retain the lower
   witness at 58.
3. **Variant table:** the classical counterparts of asymmetric (2,3), (2,4),
   and three-color Gallai triangles are respectively **3, 4, 11**, replacing
   6, 9, 17. The asymmetric targets are cliques, not complete bipartite graphs.
4. **Independence number:** for n >= 2 the value floor(n/2) remains correct,
   but the paired-bin pigeonhole proof fails for odd n. An independent set of
   size at least two excludes 1 and cannot contain consecutive integers. Such
   a subset of {2,...,n} has size at most ceil((n-1)/2)=floor(n/2); the evens
   attain the bound. For n=1 the independence number is 1.
5. **Primality conjecture:** this is now a consequence of the edge prime-index
   identity, not an open conjecture or a conclusion of a density heuristic.
6. **Code URL:** the archival `queelius/erdos-research` URL is obsolete. The
   maintained repository is
   [queelius/computational-explorations](https://github.com/queelius/computational-explorations).
   The cited paths and archival paper remain in place.

## Computational repairs

The follow-up repair distinguishes three extension-search outcomes:
`EXTENSIBLE` includes a full witness, `EXHAUSTED` certifies universal failure,
and `INCONCLUSIVE` records a seed limit with unexamined colorings remaining.
Use `check_extensions` for this structured result. The legacy
`check_extension_unsat` tuple remains available, but its Boolean is true only
after exhaustive failure; false does not imply SAT. An inconclusive search
cannot make `compute_rcop4_with_extension` report an exact threshold.

`validate_avoiding_coloring` now requires exactly the canonical coprime edges
and integer colors 0 or 1 before checking every forbidden clique. Counting
registers unconstrained edge variables and returns `ColoringCount` with an
explicit `exhausted` flag. The integer-returning `count_avoiding_colorings_sat`
and the density helper raise `IncompleteEnumerationError` if a cap prevents
an exact result. Seed and model caps do not impose solver time limits.

The solver dependency `python-sat` is now declared. Regression tests cover
failed samples on a satisfiable target, exhaustion exactly at the cap,
malformed witnesses, free edge variables, and incomplete density counts.
See the [repair validation record](coprime-ramsey-repair-validation.md) for the
bounded test command, coverage, environment, and remaining full-suite blocker.

## Other dated corrections and remaining gaps

The historical triangle value **9** in `docs/research_insights.md` and K_4
estimate **20** in `docs/novel_problems.md` were false. Those records now retain
the old claims with explicit correction notices giving 11 and 59. Random-search
failure had been mistaken for evidence strong enough to estimate a threshold.
Going forward, report failed search as failed search; exactness requires a
complete lower witness and a valid universal upper argument.

`lean/CoprimeRamsey.lean` does **not** certify these results. The audit found
nine `sorry` tactics, predicates that ignore the clique-size parameter,
missing undirected symmetry, a false admitted edge count (36 instead of 41 at
11), and a subset-existence statement presented as exhaustive counting. No
build was performed; completing the proof holes requires correcting the
statements first. See [Lean status](../lean/README.md).

The original coprime DOI archives only the PDF. The February
[code DOI](https://zenodo.org/records/18638635) predates the SAT modules and is
not an archive of the corrected repository. The [release record](coprime-ramsey-release.md)
describes the subsequent software-and-witness snapshot. Counting defects identified in the audit are
repaired as described above. Preserving solver certificates for all variant
computations, reproducing the two longer path searches, and completing the
Lean formalization remain outstanding.
