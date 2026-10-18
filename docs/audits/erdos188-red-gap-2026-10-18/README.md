# An independent red-distance gap certificate for Crocker's coloring

Alexander Richard Towell, with substantial OpenAI Codex assistance.
Source construction: Carson Crocker, [Erdős Problem #188, v5](https://doi.org/10.5281/zenodo.23405962),
sections 4 and 5 and Appendix A, CC BY 4.0.

## Statement and significance

For the **specified** periodic union of 90 closed regular 24-gons in Crocker's
`cfg_k60.json`, no two red points have distance in the closed interval

\[
 [999/1000,1001/1000].
\]

In particular, this independently corroborates the exclusion of red unit
pairs (Claim A). The calculation checks a slightly larger red set: the union
of closed disks with radii `h_i * 100863/100000` at the same periodic centers.
It includes every polygon boundary and every integer lattice translate.

This is a written proof with exact finite Python arithmetic, **not** a kernel
formalization or human peer review. It does not verify Claim B (absence of blue
60-term progressions), the complete bound `K_* <= 60`, the claimed lower bound,
the 59-term witness, or optimality. No new coloring or improved Ramsey bound
is claimed. The numerical interval is a convenient certified gap, not asserted
to be the largest possible gap.

The original note already contains the near/far proof and a complete
translation-window reduction. This audit is not a missing-proof repair. Its
additional evidence is an inverse-lattice nine-image reduction after exact
recentering, an algebraic rather than trigonometric radius enclosure, an
explicit distance gap, and adversarial controls. The source and its three
checkers were read before implementation; this is not blind replication.

## Reproduce

Python 3.10 or later; standard library only. From this directory:

```sh
python audit.py
python -m unittest discover -s . -p 'test_audit.py' -v
python reviewer_checks.py
```

The first command checks the vendored configuration's exact SHA-256 and emits
a fresh certificate with `status: PASS`, **90 cells, 72,810 ordered pairs,
408 near and 72,402 far**. It does not trust the saved `certificate.json`.
The 20-test suite includes prohibited endpoint equalities, missing-period
counterexamples, a nearly singular lattice, malformed data, oversized cells,
and two actual-source centers changed to be exactly one unit apart.

The 4,823-byte source configuration is reproduced unchanged under CC BY 4.0.
Its digest agrees with the release README:
`b15251de28f6f552f4364d2170a58e923b730590d8797dfe5d09e007d2f87b2e`.
[source-pins.json](source-pins.json) pins the note and source programs inspected.
Only selected ZIP members were needed; the full release ZIP and its unrelated
certificates were not verified. No source program is imported or executed.

## Written proof of the infinite-to-finite implication

Write `B = [P1 P2]` for the matrix whose columns are the two rational period
vectors in the configuration, and `Gamma = B Z^2`. For the source apothems
`h_i > 0`, let `C(h_i)` be the closed regular 24-gon defined by the source's
twelve pairs of supporting halfplanes. Its circumradius is
`h_i sec(pi/24)`, so it lies in the closed disk of that radius about zero.
This elementary polygon fact is independent of the near/far computation.

**1. Algebraic radius enclosure.** Put

\[
 c=100863/100000,\quad a=1414213/10^6,\quad b=2449489/10^6.
\]

Exact square comparisons give `0 < a`, `a^2 < 2`, `0 < b`, `b^2 < 6`, and
`c^2 (4+a+b)/8 > 1`. The half-angle identity

\[
 \cos^2(\pi/24)=(4+\sqrt6+\sqrt2)/8
\]

and positivity of the cosine imply `c > sec(pi/24)`. Thus each closed polygon
is contained in the closed disk of rational radius `r_i = c h_i`. These
inequalities are checked on every run. No floating-point, library value of
pi, or numerical trigonometric calculation is used in acceptance.

**2. Exact recentering.** Let `u_1,u_2` be the rows of `B^{-1}`. For each
center `c_i`, set `z_i = floor(B^{-1} c_i)` coordinatewise and
`c'_i = c_i - B z_i`. Then `f_i = B^{-1} c'_i` has both coordinates in
`[0,1)`. Replacing a center by an integer lattice translate does not change
its full orbit, so the infinite union is unchanged. Negative and exact
integer coordinates use mathematical floor, not truncation.

**3. Nine images are complete.** Set `ell = 999/1000`, `u = 1001/1000`,
`r_max = max_i r_i` and `T = u + 2 r_max`. The checker verifies, exactly,

\[
 T^2\|u_j\|^2<1 \qquad (j=1,2).
\]

By periodicity any pair of cells can be written with centers
`c'_i + B k` and `c'_j`, where `k` is an arbitrary integer pair. Their center
difference `v` satisfies `B^{-1}v = k + f_i - f_j`. If some `|k_j| >= 2`,
then `|(B^{-1}v)_j| > 1`, since `(f_i-f_j)_j` belongs to `(-1,1)`.
Cauchy--Schwarz gives `1 < |u_j dot v| <= ||u_j|| ||v||`; the verified row
bound consequently implies `||v|| > T`. For any points in these two closed
disks, the reverse triangle inequality gives

\[
 \|p-q\|\ge\|v\|-r_i-r_j>T-2r_{max}=u.
\]

Thus **every omitted translate is far**. Only `k in {-1,0,1}^2` needs a
finite check. No bounded sample is being substituted for all translates.

**4. The finite inequalities.** Each same-cell diameter satisfies
`2 r_i < ell`. For each of the nine images and each ordered cell pair except
`i=j,k=0`, form the exact rational number `q = ||v||^2` and `s = r_i+r_j`.
Require one of

\[
 \ell-s>0\ \text{and}\ q<(\ell-s)^2,
 \qquad\text{or}\qquad q>(u+s)^2.
\]

The first, with its essential positive-sign guard, implies `||v||+s < ell`;
all point distances between the disks are then strictly below `ell`.
The second implies `||v||-s > u`; all are strictly above `u`. There are
`9*90^2-90 = 72,810` such ordered triples, and all satisfy one of these
strict alternatives. The complete finite certificate therefore proves the
stated exclusion for the infinite union. Overlapping disks are allowed:
disjointness and a unique cell assignment are not assumed.

Closed polygons and disks cause no endpoint exception, since the triangle
inequalities are non-strict while every checked separation from the prohibited
distance interval is strict. The half-open fundamental parallelogram is only
a device for choosing representatives; it does not discard cell boundaries.

## Scope, provenance and review

Crocker supplied the construction, the near/far mechanism (Lemma 8), the
original proof of Claim A (Proposition 9), and multiple prior checks.
`claimA_nf.py` uses an Arb-certified rational radius and a global window;
`indep_nearfar.py` uses Machin/Taylor bounds and pair-specific windows;
`extra_checks/blind_verifier_V3/claimA_v3.py` uses polygon interval geometry.
We do not claim priority for the near/far argument or for independent checking
as a method. Crocker credits Currier, Mody, Xie and Zhang's periodic-cell
framework and Gabriel Currier's suggestion of variable cell sizes; that
construction attribution is retained.

The certificate depends on elementary Euclidean geometry, exact integer and
Fraction arithmetic, the Python implementation/runtime, and faithful parsing
of the pinned input. The written proof is not machine formalized. A checker
failure means the sufficient criterion was not established; only an explicit
pair of red points can supply a geometric counterexample. A gap established
for these fixed data says nothing about arbitrary periodic colorings.

One separately tasked AI review found no blocking defect; its scope and exact
reviewed hashes are in [review.md](review.md). Its independent checker uses
scaled integers and pair-specific translation bounds, checks 662 candidate
pairs (408 near, 254 far), and proves every omitted translate far by a separate
coordinate argument. It agrees on the exact finite squared margins and passes
12 control groups. Both implementations share Python and the pinned data;
AI review is not human peer review. The public submission and verification
receipt are recorded separately from the mathematical status. New code is MIT;
prose and the attributed configuration are CC BY 4.0. See [LICENSE.md](LICENSE.md).
