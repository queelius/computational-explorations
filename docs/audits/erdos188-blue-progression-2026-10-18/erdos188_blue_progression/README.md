# External integer audit of Crocker's blue-progression condition

Alexander Richard Towell, with substantial OpenAI Codex assistance.
Source construction and previous verification: **Carson Crocker**,
[v5 deposit, October 15, 2026](https://doi.org/10.5281/zenodo.23405962).
The construction follows the Currier–Mody–Xie–Zhang cell framework, with
variable cell sizes suggested by Gabriel Currier. This is an external audit
of an existing claim, not a new coloring, new Ramsey number, blind replication,
formal proof, or human peer review.

## Precise scope

Let `P1=(15.620641,0)`, `P2=(7.980039,13.537743)` and
`Gamma=Z P1+Z P2`. The ninety exact rational centers `c_i` and apothems `h_i`
are those in `cfg_k60.json`, SHA256
`b15251de28f6f552f4364d2170a58e923b730590d8797dfe5d09e007d2f87b2e`.
For `k=0,...,11`, put
`n_k=(cos((2k+1)pi/24),sin((2k+1)pi/24))` and
`C(h)={q: |n_k dot q| <= h for every k}`. The red set is the union of the
closed polygons `c_i+g+C(h_i)` over all cells and all `g in Gamma`; blue is
its complement.

**Claim B:** for every `x in R^2` and every unit vector `u`, some integer
`j in {0,...,59}` has `x+j*u` red. Equivalently there is no all-blue
sixty-term unit-spaced straight progression. The independent full-run result
is recorded in `full/result.json`; a pilot alone does not establish this claim.

Together with the separately audited Claim A (no red unit pair), this
corroborates the **source's upper bound `K_* <= 60`**, within the written-proof
and exact-computation trust model. It says nothing about the source's lower
bound `7 <= K_*`, optimality among colorings, or human acceptance of either
submission. The [Claim A packet](https://github.com/queelius/computational-explorations/pull/8)
remains independently reviewable and is not modified here.

## Written reduction to checked inequalities

1. **Inscribed disks.** Every `n_k` is a unit vector. Cauchy–Schwarz gives
   `|n_k dot q| <= ||q||`, so the closed disk `D(0,h)` is contained in `C(h)`.
   Therefore it suffices to cover starting points by translated, shrunken
   copies of these disks. We do not approximate the polygon from outside.

2. **All starting positions.** Write `L=P1.x >0`, `H=P2.y >0`. Given any point,
   subtract an integer multiple of `P2` to put its y-coordinate in `[0,H)`,
   then an integer multiple of `P1` to put its x-coordinate in `[0,L)`.
   Consequently `F=[0,L) x [0,H)` is a fundamental representative rectangle,
   despite the shear `P2.x`. Red is Gamma-periodic. Covering
   `G=[0,63/4] x [0,55/4]`, which contains `F`, suffices. Grid dimensions are
   calculated by exact rational ceilings, not hardcoded in the acceptor.

3. **All directions.** Put `u(theta)=(cos(theta),sin(theta))`. For an interval
   `[a,b]` with midpoint parameter `t in [a,b]`, let
   `delta=max(b-t,t-a)`. The derivative has norm one, hence
   `||u(theta)-u(t)|| <= |theta-t| <= delta`. For any `0<=j<60`,
   the disk with center `z=c_i+g-j*u(t)` and radius `r=h_i-j*delta`, if positive,
   is contained in `D(c_i+g-j*u(theta),h_i)` for every angle in the interval.
   Thus a square contained in this disk has `x+j*u(theta)` red throughout it.
   We cover `[0,H_theta]`, where `H_theta` is the exact binary float named
   `3.1416`, namely `7074254294673575/2251799813685248`. This is slightly
   below the decimal rational `31416/10000`. Angles `[0,pi]` suffice because a progression in the
   opposite direction is the same point set with starting point `x+59u` and
   reversed order. A separate exact check verifies adjacent endpoints and
   `H_theta > pi`; no floating comparison with pi is trusted.

4. **Independent trigonometric enclosures.** At each exact binary-float
   midpoint, `audit.py` evaluates the degree 32 Taylor polynomial of sine and
   cosine with Python integers and `Fraction`. Lagrange's theorem bounds each
   error by `|t|^33/33!`, since every real derivative of sine/cosine has absolute
   value at most one. This is valid on the checked domain `0<=t<=4`; no
   assumption of decreasing alternating terms is needed. Floor and ceiling
   round the resulting rational endpoints outward to units of `2^-40`.
   An independent exact Machin identity
   `pi=16 atan(1/5)-4 atan(1/239)`, with ten alternating terms and the next-term
   error, supplies a rational upper bound for pi. The implementation checks
   that the actual last endpoint exceeds that upper bound.

5. **Rounding direction.** Lattice vectors and cell centers are independently
   rounded outward in the same units. Multiplication by a negative lattice
   coefficient reverses interval endpoints. For `j>=0`, a center interval
   `[c_lo,c_hi]` and direction interval `[u_lo,u_hi]` give
   `[c_lo-j*u_hi,c_hi-j*u_lo]`. The accepted radius is the integer
   `R=floor(2^40*h_i)-j*ceil(2^40*delta)`, so `R/2^40 <= h_i-j*delta`.
   The verifier requires `R>0`; squaring a negative radius cannot certify a
   square. Python arbitrary-precision integers avoid machine overflow.

6. **Every point of a square.** A dyadic square is represented exactly by
   integer coordinates `[X,X+w] x [Y,Y+w]`. If the disk-center enclosure is
   `[A,B] x [C,D]`, define
   `dx=max(|X-B|,|X+w-A|)` and `dy=max(|Y-D|,|Y+w-C|)`.
   For every point in the closed square and every possible actual center,
   its squared distance is at most `(dx^2+dy^2)/2^80`.
   The strict integer test `R^2-dx^2-dy^2 >0` puts the whole closed square
   inside the open disk, so sector/grid boundaries are included. This differs
   from the source's center-distance-plus-half-diagonal Arb test and needs
   no square root.

7. **Complete finite coverage.** For each angle interval the trusted walker
   starts at every square of the `63 x 55` root grid, each of side `1/4`.
   A split is replaced by its four closed dyadic children. Every leaf must
   have an accepted witness. Missing or extra nodes, negative/invalid disk
   indices, noninteger witnesses, out-of-range cell or progression indices,
   and splits beyond the depth bound are rejected. Hence induction on the
   finite trees proves coverage of `G`. Every accepted angle record is
   collected from an actual call to this verifier. The driver requires all
   initial tasks to finish and the final exact angle intervals to tile from
   zero to an endpoint above pi. A missing angular region or a pilot cannot
   produce a full-cover result.

These seven steps connect the finite integer inequalities to the quantified
Claim B. They use standard real geometry, Taylor's theorem and Machin's
identity as written mathematics. They are not a kernel-checked formal proof.

## What is independent, and what is reused

The deposit already includes: an interval strip verifier, an Arb disk verifier,
and a separate integer polygon verifier with an additional rational replay.
Its V3 report records 9,287,913 polygon witnesses. We credit those checks and do
not present their absence as motivation. We read the source before writing
this audit.

We reuse the **unmodified `stage1` floating/Numba search** from verifier2 solely
to propose a tree and disk indices. Its success flags, counts, radii, trig
values and Arb acceptance code are not accepted as mathematical evidence.
`audit.py` independently reconstructs the square tiling, the exact data,
Taylor bounds, radius shrinkage, and integer corner inequalities. The driver
binds the configuration and generator to complete SHA256 pins and fixes
`j<60`. Arbitrary lattice coefficients are allowed: each proposed translate
is valid on its own; an exhaustive lattice search is not needed for a cover.

The external acceptor combines different arithmetic and a different geometric
containment test, and checks the full cover rather than sampling a success log.
It is not independent of the source construction, disk-cover reduction, or
witness-search strategy. Python/interpreter/hardware correctness and the
accuracy of this written-to-code translation remain trust assumptions.

## Reproduce

From this research workspace:

```sh
python -m pip install -r docs/audits/erdos188-blue-progression-2026-10-18/erdos188_blue_progression/requirements.txt
PYTHONPATH=docs/audits/erdos188-blue-progression-2026-10-18 python -m unittest erdos188_blue_progression.test_audit
PYTHONPATH=docs/audits/erdos188-blue-progression-2026-10-18 python -m erdos188_blue_progression.run --workers 8 --output /tmp/erdos188-blue-replay
```

The first command is only for the untrusted search dependencies. The trusted
arithmetic and unit tests use the standard library. `--pilot 80` (written as
`--pilot 80`) selects eighty initial intervals and explicitly returns
`PILOT_ONLY`; it is not a proof of complete coverage. For a full run, expect
`FULL_COVER_VERIFIED` and `direction_tiling_checked: true`; the checked counts,
margin and measured runtime are in `full/result.json`. Each output includes
input/checker hashes, parameters, environment versions and a digest of all
per-interval records. Witness hashes identify the regenerated trees; the
summary/log are evidence receipts, not a replacement for regenerating and
checking the witnesses.

The source generator uses a Numba cache. Use an ordinary module import as the
driver does, rather than dynamic import names; an earlier exploratory dynamic
import produced an unusable cache entry. This was an environment issue, not a
failed mathematical inequality. No Arb or python-flint dependency is needed
for the full verification.

## Attribution and publication status

The unmodified source generator, its notes and the configuration are retained
under the deposit's CC BY4.0 attribution; see `vendor/README.md` and
`source-pins.json`. Our checker, proof text, tests and review distinguish
original work from these inherited artifacts. AI assistance was substantial
throughout implementation, derivation, testing and drafting. A separate AI
review is recorded in `review.md`; it is not human peer review. Submission and
acceptance, when applicable, are recorded separately in `submission.json`.

Public packaging note: reproduction paths above are adapted to this repository.
The reviewed README hash in review.md refers to the preserved research-workspace
version; the mathematical text and audit.py/run.py are unchanged.
