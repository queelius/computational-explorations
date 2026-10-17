# Coprime Ramsey Citation and Reproducibility Audit

Audit date: **2026-10-17**. Local revision: `f5f43ddf6df291742c029fd073f6e99034a5fb85`.

The headline values **11, 59, and 53 remain supported**, but the repository does not consistently distinguish complete proofs, sampled evidence, and unfinished formalization. The principal risks are an unsound interpretation of sampled extension checks, incomplete witness validation, stale public documentation, and a Lean file containing false admitted statements. These are evidence and maintenance defects; this audit found no counterexample to the three headline values.

This report covers the coprime results cited by Du, Xi, Deng, and Ma, their historical provenance, and bounded computational checks. Existing research code, papers, and summaries were left unchanged. New audit artifacts are in [audits/coprime-ramsey-2026-10-17](audits/coprime-ramsey-2026-10-17/); the new witnesses are explicitly dated audit evidence, not reconstructed historical SAT outputs.

## Citation and historical provenance

Du et al., *Prime Certificates for Exact Vertex-Coprime Ramsey Numbers*, arXiv:2605.26815v2, directly cite this GitHub repository as reference 22 and Alexander Towell's blog post as reference 21. Section 8 and Table 12 discuss the reported variants. Theorem 4.4 gives the mixed **edge-coloring** identity

\[
R^{\mathrm{edge}}_{\mathrm{cop}}(k_1,\ldots,k_c)
=p_{R(k_1,\ldots,k_c)-1}.
\]

The paper's vertex-coloring formula concerns a different parameter. Proposition 4.6 covers complete-pattern transfers, including Gallai triangles; Corollary 4.7 gives gcd scaling. [Citing paper, version 2](https://arxiv.org/html/2605.26815v2)

| State | Evidence and interpretation |
| --- | --- |
| Initial repository | [`448b341d326a87787b95851aee6e88f27d1dd474`](https://github.com/queelius/computational-explorations/commit/448b341d326a87787b95851aee6e88f27d1dd474), 2026-03-17 01:27:36 UTC. Contains the coprime modules and original paper. |
| Reconstructed citation-era default branch | [`eb15dc09dce0ba0394eabba04633e87e5f8724d5`](https://github.com/queelius/computational-explorations/commit/eb15dc09dce0ba0394eabba04633e87e5f8724d5), 2026-03-17 02:04:50 UTC. Latest surviving default-branch commit before the May paper. This is an inference: the citation specifies neither a SHA nor an access date, and commit dates do not establish push dates. |
| Public default branch at audit | [`4bef9df23fba3801b069dccdce32027d9c7e5865`](https://github.com/queelius/computational-explorations/commit/4bef9df23fba3801b069dccdce32027d9c7e5865), 2026-06-06. GitHub MCP reported no tags or releases. `CITATION.cff` first appears here, after the citation. |
| Local corrections absent from public main | `9939a1f…`: primality/prediction reconciliation; `45a4cb6…`: edge/vertex distinction; `dfc09dd…`: repaired proof of 59. All precede the audited local HEAD but follow public main. |
| Original DOI artifact | [Zenodo 19058647](https://zenodo.org/records/19058647), concept DOI 19058646, published March 17. Its sole file is a 238,813-byte PDF, MD5 `ce0330361a5eac353798068306ceff64`, identical to the initial and current local `paper/coprime_ramsey_note.pdf`. It archives neither code nor certificates. |

The archived original paper acknowledges that checking 100 seeds did not prove the upper bound for 59. The later E-JC manuscript repairs that proof, but neither the original DOI artifact nor public main incorporates the repair. The principal coprime Python modules are unchanged across these historical states.

The February [Zenodo code archive 18638635](https://zenodo.org/records/18638635) is an earlier code state: it lacks the SAT/variants modules and contains the old random-search heuristic. It must not be presented as an archive of the corrected March repository. Separately, `docs/doi_candidates.md:7` misidentifies the concept DOI for [record 18638638](https://zenodo.org/records/18638638); that record reports **18638632**.

## Definitions and claim ledger

All claims below color **undirected coprime edges** on the integers `1..n`. A path parameter `k` counts **edges**, hence `k+1` vertices; a cycle parameter counts both edges and vertices. The function called `compute_bipartite_coprime_ramsey` computes asymmetric **clique** demands, not a complete-bipartite target.

Source abbreviations:

- **S**: [src/coprime_ramsey_sat.py](../src/coprime_ramsey_sat.py), especially `encode_rcop_sat`, `compute_rcop_sat`, and `check_extension_unsat`.
- **V**: [src/coprime_ramsey_variants.py](../src/coprime_ramsey_variants.py), with corresponding `tests/test_coprime_ramsey_variants.py` classes.
- **N**: [src/nt_graph_ramsey.py](../src/nt_graph_ramsey.py), `gcd_graph` and `compute_rgcd`.
- **E**: [e-jc/coprime-ramsey-ejc.tex](../e-jc/coprime-ramsey-ejc.tex), the later local manuscript.
- **P**: [paper/coprime_ramsey_note.tex](../paper/coprime_ramsey_note.tex), source of the original archived manuscript.

| Claim | Repository evidence | Fresh audit result and remaining gap |
| --- | --- | --- |
| Two-color triangle threshold **11** | S; `TestRCopExact`; E `thm:rcop3`, lines 151–181 | SAT threshold test passed. New full coloring at 10 independently checked. Upper bound follows from the prime clique of size 6 and `R(3,3)=6`. |
| Two-color `K4` threshold **59** | S; E `prop:cone`, lines 119–134, and `thm:rcop4`, lines 190–213; P lines 145–168 | New full coloring at 58 checked against all 49,815 coprime `K4`s. E's prime-clique upper bound uses `R(4,4)=18`. Historical sampled extensions alone are incomplete. Direct SAT at 59 was not rerun. |
| Three-color triangle threshold **53** | V `compute_multicolor_coprime_ramsey`; E `thm:rcop33`, lines 227–241 | New full coloring at 52 checked against all 6,684 coprime triangles. Upper bound uses the prime clique of size 17 and `R(3,3,3)=17`. Existing tests only check this three-color search through 12; the claimed full original SAT transition was not rerun. |
| Asymmetric `(2,3)` **3** | V `compute_bipartite_coprime_ramsey`; `TestBipartiteCoprimeRamsey` | Exact threshold test passed. |
| Asymmetric `(2,4)` **5** | Same | Exact threshold test passed. |
| Asymmetric `(3,4)` **19** | Same; E table `tab:variants` | Exact threshold test passed. |
| Three-color Gallai triangle **29** | V `compute_gallai_coprime_ramsey`; `TestGallaiCoprimeRamsey` | Exact threshold and below-threshold tests passed. No historical assignment/proof certificate located. E's exclusion of Gallai from the transfer needs correction. |
| gcd-`d` triangle threshold **11d** | N lines 297–340; `tests/test_nt_graph_ramsey.py::TestRGCD` | Tests passed, including `d=1,2,3,6`. General proof rescales multiples of `d` to the coprime graph; other vertices are isolated. |
| Path with 3 edges: **5** | V `compute_path_coprime_ramsey`; `TestPathCoprimeRamsey::test_pcop3` | Exact threshold test passed. |
| Path with 4 edges: **7** | Same, `test_pcop4` | Exact threshold test passed. |
| Path with 5 edges: **9** | Same, `test_pcop5` | Exact threshold test passed. |
| Path with 6 edges: **10** | Same, `test_pcop6` | Exact threshold test passed. |
| Path with 7 edges: **13** | V module table; E `tab:variants` | No exact-value regression test. Audit rerun timed out after 60 seconds; the reported value was not independently reproduced. |
| Path with 8 edges: **13** | Same | No exact-value regression test. Audit rerun timed out after 60 seconds; the reported value was not independently reproduced. |
| Cycle of length 3: **11** | V `compute_cycle_coprime_ramsey`; `TestCycleCoprimeRamsey` | Exact threshold test passed. |
| Cycle of length 4: **8** | Same | Exact threshold test passed. |
| Cycle of length 5: **13** | Same | Exact threshold test passed. |
| Cycle of length 6: **11** | Same | Exact threshold test passed. |
| Avoiding two-color triangle counts at 8, 9, 10, 11 | V `count_avoiding_colorings_sat`; P/E extension proof | Fresh complete SAT enumeration returned **36, 36, 156, 0**. These are labeled colorings, without quotienting color swaps. A separate unconstrained-variable counting defect is described below. |

Passing SAT searches establish these computations conditional on their encodings and solver correctness. The variant functions discard models and return an integer; they do not preserve independently checkable UNSAT certificates. Before this audit, the inspected coprime artifacts contained no saved SAT assignments, exhaustive coloring lists, DRAT/LRAT files, or per-instance certificate manifests.

## Reproduced correctness and coverage gaps

### P0 Sample exhaustion is confused with a proof

`S:414–445` returns `(True, checked)` both when all base colorings are exhausted and when an arbitrary seed limit is reached. `compute_rcop4_with_extension`, lines 529–540, promotes that result to an exact threshold.

Concrete counterexample in the installed solver version:

```python
check_extension_unsat(6, 7, 3, num_seeds=1)  # (True, 1)
solver, _, _ = encode_rcop_sat(7, 3)
solver.solve()                             # True: a valid target coloring exists
solver.delete()
```

The sampled seed really fails to extend; the invalid inference concerns all seeds. Future repair should distinguish an extensible witness, proven exhaustion, and a sampling/resource limit using structured status. Tests must cover the sampled-failure/target-SAT case. The repaired theorem for 59 survives this defect because its upper bound has an independent mathematical proof.

### P1 Witness validation does not enforce its input contract

`S:448–464` accepts an empty coloring and also accepts a valid coloring after replacing colors `0,1` with `2,3`. Missing edges receive `-1` and evade the monochromatic check; palette membership is never checked. Tests validate well-formed solver outputs but omit these malformed inputs. A future validator must check the exact required edge set, canonical undirected keys, and the permitted palette before checking forbidden subgraphs.

### P1 Counting omits unconstrained variables and hides truncation

`V:444–480` returns **1** for `count_avoiding_colorings_sat(2,3)`, although the single edge has **2** valid colorings. Variables appear only through clique clauses, so the empty formula does not enumerate the unconstrained edge. The cap also returns an integer without an exhaustion indicator. Future tests should cover free variables and distinguish exact counts from capped lower bounds. This does not invalidate the separately reproduced counts at 8–11.

### P1 Lean does not certify these results

[lean/CoprimeRamsey.lean](../lean/CoprimeRamsey.lean) contains nine `sorry` tactics, including a false admitted equality: lines 116–118 assert **36** edges at 11; independent enumeration gives **41**. Its generic `RcopUpper`/`RcopLower` definitions ignore `k` and always ask about triangles; `EdgeColoring'` has no undirected symmetry condition. The purported exact-count lemma at lines 224–227 only asserts existence of a subset of size 36, not that it contains all avoiding colorings. Apparent proved wrappers depend on admitted results.

The file's header counts, an explicit witness comment, and several graph counts are also inconsistent. Correct the definitions before filling proof holes. Lean 4.16.0 is installed, but this checkout lacks the Mathlib build/dependency directory; no dependency download or Lean build was performed. Only `Erdos43` is the default Lake target, so ordinary `lake build` would not validate this file anyway.

### Dependency and semantic test gaps

[pyproject.toml](../pyproject.toml) declares NumPy, PyYAML, and NetworkX, but not the `python-sat` package required by S/V/N. A clean installation of declared test extras is therefore insufficient for the audited tests. No lock or pinned solver environment accompanies the historical claims.

The focused suite passed **81 tests**, with **3 expensive `TestRCop4` tests deliberately deselected**, in **20.57 seconds**. Coverage was **81%** for S, **95%** for V, and **31%** for N; the N figure reflects that only its gcd-related tests were selected. These are selected-run figures, not repository-wide coverage. S's uncovered `compute_rcop4_with_extension` branch includes the problematic exactness promotion. V's high coverage does not cover the missing palette/free-variable contracts, the full three-color 53 transition, or the two longer path thresholds.

## Required documentation corrections

| Priority | Locations | Required correction |
| --- | --- | --- |
| P0 | `README.md:10,49`; `discoveries/coprime-ramsey/README.md:71`; `docs/novel_problems.md:770–776`; `docs/session_2026_03_16_iteration3.md:71–77` | Attribute the upper bound for 59 to the complete prime-clique argument. Label sampled extensions as corroboration; preserve dated historical context. |
| P1 | P lines 87–90, 232–236, 288–298, 300–310, 357 | Correct the reversed restriction/extension argument, classical counterpart values `(3,4,11)`, independence proof for odd `n` (already repaired in E lines 391–403), superseded primality conjecture, and old `erdos-research` URL in a new version. Keep the archived version intact and link a correction notice. |
| P1 | E abstract lines 59–61, introduction 92–94, remark 286–292 | Gallai triangles fall within the complete-pattern transfer. Paths and cycles remain outside its exact lower-bound mechanism. |
| P1 | `docs/rcop5-reconciliation.md:38–56,82,95,113`; discovery README lines 61–63 | Replace the purported current/cited `181–211` window with the supported `181–197` window; retain the old window only as dated history. Describe possible prime values, not every integer in the interval as prime. |
| P1 | `docs/research_insights.md:186`; `docs/novel_problems.md:644,661` | Annotate obsolete values 9 for the triangle threshold and 20 for the `K4` threshold. |
| P1 | `lean/CoprimeRamsey.lean`; `lean/README.md`; research summaries | State incomplete formalization and semantic defects explicitly; no claim of Lean verification for the coprime results. |
| P2 | Discovery README lines 39,54–55; `tests/test_coprime_ramsey_variants.py:263–266,335–342` | Rename the asymmetric-clique heading, align values with prime indices, and correct misleading classical-value comments. |
| P2 | `CITATION.cff`; `docs/doi_candidates.md:7` | Add software snapshot/version metadata when an archive exists; distinguish paper and software DOIs; correct the unrelated concept DOI. Use canonical author metadata consistently. |

The `181–197` window is the one reported in the citing paper's Table 3. Its upper endpoint follows from Angeltveit and McKay's published bound `R(5,5) <= 46`, already available in 2024; attributing 48 to that work is incorrect. [Primary bound](https://arxiv.org/abs/2409.15709), [citing paper](https://arxiv.org/html/2605.26815v2)

## Reproducing the audit

The [environment record](audits/coprime-ramsey-2026-10-17/environment.json) lists the interpreter and installed versions. Run the following from the repository root in that environment, without Python's `-O` option:

```bash
python docs/audits/coprime-ramsey-2026-10-17/independent_checks.py

COVERAGE_FILE=/tmp/coprime-ramsey-audit.coverage timeout 240s python -m pytest \
  tests/test_coprime_ramsey_sat.py tests/test_coprime_ramsey_variants.py \
  tests/test_nt_graph_ramsey.py::TestRGCD -k 'not TestRCop4' --timeout=20 \
  --cov=coprime_ramsey_sat --cov=coprime_ramsey_variants --cov=nt_graph_ramsey \
  --cov-report=term-missing \
  --cov-report=json:docs/audits/coprime-ramsey-2026-10-17/coverage.json \
  --junitxml=docs/audits/coprime-ramsey-2026-10-17/pytest.xml --durations=10 -q
```

The first command regenerates three full lower-bound witnesses and checks every relevant clique using a separate combination-based verifier. Its constructions use a five-cycle, quadratic residues modulo 17, and multiplicative difference classes in the field with 16 elements, pulled back through prime-divisor labels. Saved JSON files were additionally checked independently for edge completeness, palette validity, and forbidden cliques.

| Artifact | Purpose |
| --- | --- |
| [independent-checks.json](audits/coprime-ramsey-2026-10-17/independent-checks.json) | Diagnostic outputs and independent enumeration totals. |
| [witness at 10](audits/coprime-ramsey-2026-10-17/witness-n10-k3-c2.json) | 31 edges; 42 triangles checked. |
| [witness at 58](audits/coprime-ramsey-2026-10-17/witness-n58-k4-c2.json) | 1,027 edges; 49,815 four-cliques checked. |
| [witness at 52](audits/coprime-ramsey-2026-10-17/witness-n52-k3-c3.json) | 829 edges; 6,684 triangles checked. |
| [pytest.txt](audits/coprime-ramsey-2026-10-17/pytest.txt), [pytest.xml](audits/coprime-ramsey-2026-10-17/pytest.xml), [coverage.json](audits/coprime-ramsey-2026-10-17/coverage.json) | Selected unit/integration results and missing-line coverage. |
| [extra-paths.json](audits/coprime-ramsey-2026-10-17/extra-paths.json) | Exact commands, 60-second budgets, and outcomes for path parameters 7 and 8. |
| [manifest.json](audits/coprime-ramsey-2026-10-17/manifest.json) | SHA-256 hashes of audited source files and delivered audit artifacts. |

No full-repository test run, direct SAT upper-bound rerun for 53/59, or formal Lean verification is claimed. The two largest path checks have separate bounded outcomes rather than being counted among passing tests.

## Recommended next work

1. Repair proof-status handling, witness validation, and counting semantics, with regression tests for the concrete cases above. Add the missing solver dependency and a small, explicitly bounded verification command.
2. Reconcile the current summaries and manuscript with the repaired proof and cited literature. Add dated correction notes to historical material; preserve cited paths and Git history.
3. Prepare a versioned release containing source, dependency versions, claim definitions, witnesses, and verification commands. Review exactly which local commits should become public before pushing; do not push the entire local branch merely to publish this audit.
4. Reassess research priorities after that baseline is reliable. Separate consequences of the clique transfer from target families still requiring computation, and close the longer-path reproducibility gap before extending their table.
