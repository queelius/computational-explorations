# Coprime path certificates — October 18, 2026

**Result: P_cop(7) = P_cop(8) = 13.** These previously reported values now have
archived, independently checked boundary evidence. The October 17 audit's
60-second timeouts remain recorded in that historical report.

## Definitions and boundary argument

G_n has vertices 1 through n and an undirected edge {a,b} exactly when
gcd(a,b)=1. Every edge receives color 0 or 1. P_cop(k) is the least n for which
every such coloring contains a monochromatic **simple path of k edges**
(k+1 distinct vertices).

| Boundary | Evidence | Independent result |
| --- | --- | --- |
| n=12, k=7 | Complete coloring of all 45 edges | Longest path has 6 edges in each color |
| n=13, k=8 | 57-variable CNF and compressed DRAT proof | All clauses valid; proof VERIFIED |

The first coloring also avoids eight-edge paths. The second result forces an
eight-edge path, which contains a seven-edge path. Restriction to G_13 and
restriction of the lower coloring to smaller vertex sets give both exact
thresholds; intermediate searches are unnecessary.

## Lower witness and an elementary construction

[The full coloring](lower-n12-k7/witness.json) has vertex covers
**{1,3,11}** for color 0 and **{5,7,9}** for color 1. Check that every edge of
each color meets its cover. A simple path in a graph with a three-vertex cover
uses at most three cover vertices and four other vertices, hence at most six
edges. Independently, the standard-library checker enumerates reachable path
endpoints for every vertex subset and finds longest lengths (6,6).

More generally, the 2m odd vertices of G_(4m) form a vertex cover because two
even vertices are never coprime. Split the odd vertices into two sets A and B
of size m. Color every edge meeting A with 0 and every remaining edge with 1.
The second color has cover B. Each monochromatic path has at most 2m edges,
so **P_cop(2m+1) >= 4m+1** for positive integers m. This explains the lower
bound at m=3; no novelty claim is made for this elementary construction.

## Upper certificate and trust boundary

The search asks Glucose4 for a coloring, finds forbidden simple paths by DFS,
and adds the two uniform-sign exclusion clauses for each found path. It stops
at a valid candidate, UNSAT, or an explicit resource limit. No symmetry-breaking
or other auxiliary constraints are used.

The archived formula has **71,832 path clauses** and one harmless two-literal
tautology registering all 57 edge variables. Variables index lexicographically
ordered coprime pairs starting at one. The independent checker verifies that
each non-tautological clause has uniform sign and exactly eight distinct
edges forming one connected simple path. It does not trust saved validity
flags, the search's DFS, or the solver's verdict.

Every path-avoiding coloring satisfies these constraints. Therefore an UNSAT
proof for this subset of path exclusions suffices, even without enumerating
all paths. DRAT-trim independently checked the archived proof against the
validated DIMACS formula: **VERIFIED**, 57,506 core clauses, 391,234 core lemmas,
4,858,014 resolution steps, and no RAT lemmas in the core.

This is a computational certificate, not a Lean proof. Its trust boundary
includes the small Python semantics checker, DRAT-trim, and their execution
environments. A successful SAT search alone, a valid formula alone, or a
timeout establishes no upper bound.

## Reproduce the checks

Run from the repository root with Python 3.10 or newer, a C compiler, Make,
Git, gzip, and GNU timeout. Choose a new output directory:

```sh
mkdir path-check
python3 -I -S -O src/coprime_path_certificates.py witness \
  docs/audits/coprime-paths-2026-10-18/lower-n12-k7/witness.json
python3 -I -S -O src/coprime_path_certificates.py formula \
  docs/audits/coprime-paths-2026-10-18/upper-n13-k8/formula.json.gz \
  --dimacs-out path-check/upper.cnf
git clone https://github.com/marijnheule/drat-trim.git path-check/drat-trim
git -C path-check/drat-trim checkout 2e3b2dc0ecf938addbd779d42877b6ed69d9a985
make -C path-check/drat-trim drat-trim
gzip -dc docs/audits/coprime-paths-2026-10-18/upper-n13-k8/proof.drat.gz \
  > path-check/upper.drat
timeout 600 path-check/drat-trim/drat-trim \
  path-check/upper.cnf path-check/upper.drat -t 590
```

Require the witness and formula checks to exit zero, and the final check to
exit zero and report `s VERIFIED`. The formula checker deliberately reports
`unsat_checked: false`; the proof checker supplies that separate result.
Existing DIMACS outputs are never overwritten. The witness DP is exponential
in n and is intended for small instances.

To regenerate evidence, first install the constrained test environment from
[Running verification](../../verification.md), then use fresh output paths:

```sh
timeout 610 python src/coprime_path_search.py 12 7 --seconds 600 --output new-lower
timeout 610 python src/coprime_path_search.py 13 8 --seconds 600 --output new-upper
```

Always independently check regenerated artifacts. The search reports
`sat`, `unsat`, or `inconclusive`; only the first two exit zero, and neither
solver status substitutes for evidence checking. Limits cover solving and
path separation; serialization is outside the internal timer. The archived
searches took approximately 0.54 and 63.51 seconds; independent proof checking
took 121.66 seconds on this machine. Runtime varies with hardware.

## Artifacts and validation

- `lower-n12-k7/`: complete witness and search metadata.
- `upper-n13-k8/`: compressed formula, compressed proof, and search metadata.
- `lower-check.json`, `formula-check.json`, `proof-check.txt`: independent results.
- `manifest.json`: file hashes, environment, source identity, limits, and commands.
- `tests.txt`, `coverage.json`: local regression results and measured coverage.

The new tests exercise malformed evidence, complete edge coverage, simple
paths versus walks, disconnected clauses, small exact boundaries, resource
limits, and CLI artifacts. The witness DP is compared with permutation
enumeration for all 512 colorings of G_5. CI checks the saved boundary evidence
separately from the focused Python 3.10/3.13 and broader routine test jobs.
See [Running verification](../../verification.md) for coverage exclusions and
the 14 deliberately excluded long research tests.

## Citation and publication implications

[Du, Xi, Deng and Ma, v2, Table 12](https://arxiv.org/html/2605.26815v2)
already lists these path values and attributes them to Towell's variant
computations. Their Proposition 4.6 does not supply an exact pullback identity
for non-complete targets such as paths; Open Problem 9.2 identifies such
edge-pattern thresholds as a research direction.

This follow-up closes a reproducibility gap and supplies reusable evidence
tools. It does not establish that the numerical values are new, replace the
cited archives, or constitute a journal submission. A stronger next research
contribution would explain upper bounds structurally or establish a family of
path thresholds. The limited literature check here is not a systematic
novelty review. Other variant certificates and the Lean formalization remain
separate work.
