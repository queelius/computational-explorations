# Red-pair audit: proposition and stopping rule

Alexander Richard Towell, with substantial OpenAI Codex assistance.
Started 2026-10-18 08:30:45 UTC; setup ends 08:40:45, verification begins
09:00:45, hard stop 09:15:45. One visit; no automatic next cycle.
Archive base: `13cd72bbb9b0ca24f4593132ad4f7fe40b45906d`.

## Precise hypothesis

For the 90 rational centers, positive apothems and period vectors in Carson
Crocker's `release_188_v5/upper_bound/cfg_k60.json`, let RED be the union of
all the closed regular 24-gons specified in section 4 of his v5 note, over
every integer combination of the two period vectors. Hypothesis: no two
points of RED have distance in the **closed** interval `[999/1000,1001/1000]`.
This implies Claim A, exclusion of red unit pairs. It does not establish
Claim B (blue 60-term progressions), the full upper bound, or the lower bound.

## Dependencies and independent coverage

Source DOI: https://doi.org/10.5281/zenodo.23405962 (v5, CC BY 4.0).
Configuration SHA-256:
`b15251de28f6f552f4364d2170a58e923b730590d8797dfe5d09e007d2f87b2e`.
The configuration digest agrees with the release README. The complete ZIP
is not required for this audit: selected members are fetched by HTTP ranges,
read with Python's ZIP parser (including CRC checks), and pinned individually.
Full-deposit verification is not claimed.

The source's Lemma 8 and Proposition 9 already supply the near/far argument,
including a complete finite translation window. This is **not** a repair of
a missing proof. Its `claimA_nf.py`, `indep_nearfar.py`, and
`extra_checks/blind_verifier_V3/claimA_v3.py` have been read and are credited;
this is not blind replication. They use respectively an Arb/rational radius
and global window, Machin/Taylor radius bounds and pair-specific windows,
and polygon interval geometry with a fixed window.

Our proposed additional evidence is a separately derived inverse-lattice
reduction to nine translates after exact recentering, an elementary algebraic
radius enclosure (no numerical trigonometry), and a certified uniform distance
gap. The gap is a modest quantitative strengthening of Claim A, not a new
coloring, improved Ramsey bound, or global novelty claim.

## Method and success criterion

1. Bound sec(pi/24) by `100863/100000`, using
   `cos(pi/24)^2 = (4 + sqrt(6) + sqrt(2))/8` and integer-square comparisons.
2. Put `r_i = h_i * 100863/100000`; closed polygons lie in these closed disks.
3. Recenter each point using the exact inverse lattice matrix and floor its
   two lattice coordinates into `[0,1)`. For each inverse row u, verify
   `T^2 * ||u||^2 < 1`, where `T = 1001/1000 + 2 max(r_i)`.
   A translate with either coefficient outside `{-1,0,1}` then has center
   distance greater than T, by Cauchy--Schwarz; its cells are automatically far.
4. Check all ordered pairs in the nine remaining translates. Require each
   same-cell diameter below 999/1000, and each distinct pair either
   `d + r_i + r_j < 999/1000` or `d - r_i - r_j > 1001/1000` using squared
   rational inequalities, with the positive-sign guard before squaring.
5. Test strict boundary equality, same-cell diameter, malformed inputs,
   recentering invariance, altered lattice and actual-data counterexamples.
   Obtain one separate review of the geometry, arithmetic, and assumptions.

Success means a written all-translates argument plus complete exact arithmetic
and failure controls. A rejecting check is not a counterexample unless explicit
red points witnessing the prohibited distance are supplied. If the gap fails,
one pivot to the original unit-distance claim is allowed and will be recorded.
If no distinct result or viable setup exists by the setup deadline, stop with
the concrete source findings. Do not run the blue-progression or lower-bound
certificates. No source program is executed or imported by our checker.

## Publication

No competing 188 audit is present in plasma-ai/erdos issue 62 at selection.
Computational Explorations has only our distinct 189 audit PR7 and a coprime
path PR6 open. One focused evidence packet there is the prospective canonical
destination; no accepted problem status or verification tier will be changed.
Publish only if the scoped proof, full checks and review are complete.
