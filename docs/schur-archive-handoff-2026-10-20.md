# Schur extensions: existing archive and preserved evidence

The June 10, 2026 manuscript **Sum-Free Partitions in Finite Abelian Groups
and Multiplicative Schur Numbers**, version 2, is already archived at
[10.5281/zenodo.20634736](https://doi.org/10.5281/zenodo.20634736).
Its author, listed historically as Alex Towell, is Alexander Richard Towell
([ORCID](https://orcid.org/0000-0001-6443-9897)).
This handoff indexes that existing contribution; it does not create a new
publication date or claim new discoveries.

## Results and corrections recorded in version 2

For a finite abelian group \(G\), \(S(G,k)\) is the largest size of a subset
partitionable into \(k\) sum-free sets. The equation \(x+y=z\) includes
\(x=y\), and zero cannot belong to a sum-free set.

- The manuscript proves \(S(G,2)=2S(G,1)\) exactly when \(|G|\) is odd.
  Andrei Zabolotskii's observation prompted the result; the one-color
  formula is credited to Green and Ruzsa.
- At order 49, it gives \(S(\mathbb Z/49\mathbb Z,2)=32\) and
  \(S((\mathbb Z/7\mathbb Z)^2,2)=28\). Earlier observations through order
  20 must not be read as a general order-invariance theorem.
- It proves the upper bound \(MS(k)\le 2^{S(k)+1}-1\), where \(S(k)\) is
  the classical Schur number, and reports equality for \(k\le3\):
  \(MS(1)=3\), \(MS(2)=31\), and \(MS(3)=16383\).
- It reports a larger finite-group computational grid and related OEIS
  sequences. This indexing pass does not independently replay that grid
  or verify the sequences' current editorial status.

## What was checked during consolidation

All three public manuscript files (LaTeX, PDF, and bibliography) were
downloaded and matched byte for byte against the preserved author files.
The central record retains their hashes and the original archive date.

The historical
[`MS(3)` witness](../discoveries/schur-extensions/grid/ms3_witness_16383.txt)
was also restored to a tracked path without changing its bytes.
Two independent enumeration orders checked all **64,449** unordered product
triples on the **16,382** integers \(2,\ldots,16383\), finding no
monochromatic triple. A corrupted-color control was rejected.
The [verification receipt](audits/schur-archive-2026-10-20/verification.json)
contains the complete runnable command, output, witness hash, and scope.

The archived written upper bound restricts a coloring at \(2^{14}\) to
\(2^1,\ldots,2^{14}\); the classical fact \(S(3)=13\) forces a monochromatic
exponent sum, hence a product triple. This is a replay and explanation of
the earlier contribution, not a new theorem.

## Continue and cite

The central record is
[`computational-explorations-schur-extensions`](https://github.com/queelius/research-records/tree/main/records/computational-explorations-schur-extensions).
Cite the exact version DOI above for the manuscript and the pinned Git
commit in that record for the newly restored witness.

The June archive contains manuscript files, not the complete computational
data and software. Remaining historical grid scripts, results, and journal
revisions are preserved on `preserve/unpublished-2026-10-20`; review and
integrate them selectively before claiming a complete software reproduction.
A substantive future archival update should use the existing Zenodo version
family `10.5281/zenodo.19058652`.

The historical manuscript discloses Claude (Anthropic) assistance.
OpenAI Codex assisted this consolidation, file-identity check, witness
replay, and indexing. No new human peer review, formal verification,
comprehensive novelty assessment, or journal acceptance is asserted.
