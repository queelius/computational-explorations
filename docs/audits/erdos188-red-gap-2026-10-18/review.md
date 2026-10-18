# Scoped independent AI review

Reviewer: a separately tasked OpenAI Codex agent, 2026-10-18.
Work attributed to Alexander Richard Towell, with substantial OpenAI Codex
assistance. This is **AI review, not human peer review or a formal proof**.

## Finding

No blocking mathematical or implementation defect was found in the reviewed
claim: for the pinned 90-cell configuration, the infinite union of the stated
closed polygons, and even the larger rational closed disks used by the audit,
has no pair at a distance in `[999/1000,1001/1000]`.

The written reduction covers all integer lattice translates and all polygon
boundaries. A separate arithmetic implementation corroborates the conclusion
using a different finite translation range and different algebraic test for the
secant bound. This corroborates Claim A only; it does not verify Claim B,
the complete upper bound 60, the lower bound, or optimality.

## Exact scope read and tested

The reviewer read `PLAN.md`, the mathematical argument in `README.md`,
`audit.py`, all 20 tests in `test_audit.py`, `cfg_k60.json`, and
`source-pins.json`. The relevant source-note definitions and Lemma 8 /
Proposition 9 were read from text extracted from the pinned PDF. The six
locally available source members listed in `source-pins.json` were checked
against their recorded byte counts and SHA-256 digests; all agreed. The full
source ZIP and its other claims were not checked.

Hashes of the reviewed files are:

| File | SHA-256 |
|---|---|
| `audit.py` | `a0fa94170dd4075b0dcaf105e759f2b872f83ff47cf1394f311c9ce00f66df1c` |
| `test_audit.py` | `aeb7d67963a2642e764bfea4b059b756f6aa282cd7d725f948f38525a806123f` |
| `cfg_k60.json` | `b15251de28f6f552f4364d2170a58e923b730590d8797dfe5d09e007d2f87b2e` |
| `README.md` | `08526247d1487d28079e146abedba51bcdb60cafefbbfca3fc01cf396ca097d4` |
| `PLAN.md` | `c964566f52b803ba146904d9161fd8fb7a9e2561be0871238a43f70a6326b351` |
| `source-pins.json` | `b0ef5393b0c1478c9f5308dab2704e8a7db4511b6c80d1bd08abae7e7c45d0e3` |

Later packaging or publication metadata changes are outside these hashes. No
download code is part of this review. The independent checker did not import
`audit.py` or any program from the source deposit. The reviewer had read the
production argument before writing the check, so this is not a blind audit.

## Mathematical checks

The source's halfplanes define a closed regular 24-gon with apothem `h`, hence
circumradius `h sec(pi/24)`. The production radical identity and lower bounds
give the stated strict upper radius factor. Exact floor reduction changes only
which representative is used for each lattice orbit. It makes each coordinate
of the difference of two normalized lattice coordinates lie in `(-1,1)`.
Consequently a translate coefficient of absolute value at least 2 forces an
inverse-lattice coordinate of the center difference to have absolute value
strictly above 1. The verified row-norm bound and Cauchy--Schwarz then force the
center distance strictly above `upper + 2 max_radius`. This is sufficient for
all omitted translates to be far.

The remaining tests use the correct near inequality with its positive-sign
guard before squaring, and the correct far inequality. Same-cell distances
are covered separately. Their strict inequalities exclude the endpoints of
the closed prohibited interval even though cell and disk boundaries are
included. Overlap between disks creates no hidden disjointness assumption.

The pinned CLI validates the exact source digest before parsing. Coordinate
and radius values are parsed as exact rational strings; no floating-point
calculation participates in acceptance. Rejecting a sufficient disk test is
not generally a geometric counterexample. The test which moves an actual
source center exactly one unit from another is a genuine counterexample for
that modified configuration because both centers are red.

## Separate infinite-to-finite reduction and arithmetic

`reviewer_checks.py` keeps the original, unnormalized centers and uses the
source's upper-triangular basis `P1=(L,0), P2=(A,H)` with positive `L,H`.
For each ordered pair let `dx,dy` be its center difference and
`D = upper + r_i + r_j`. A center difference which is not already far must
satisfy both coordinate bounds

```
|dy + b H| <= D,
|dx + b A + a L| <= D.
```

Thus its integer translation coefficients must satisfy

```
ceil((-D-dy)/H) <= b <= floor((D-dy)/H),
ceil((-D-dx-bA)/L) <= a <= floor((D-dx-bA)/L).
```

Every omitted translate has a coordinate of absolute value strictly above
`D`, hence Euclidean center distance above `D` and all point distances above
the prohibited interval. The remaining pairs are tested by squared
inequalities. This gives a separate proof of exhaustive translation coverage,
without a lattice inverse, recentering, a fixed nine-image window, or the
production classifier. The pair-specific window method is not claimed to be
novel; the source also has a checker using pair-specific windows.

All positions, radii, and interval endpoints scale to integers with common
scale `10^9`. Candidate enumeration and pair inequalities then use integer
arithmetic only. The check found **662 candidate ordered pairs**, with **408
near** and **254 far**. All translates omitted by the coordinate bounds are
far by the argument above; same-cell pairs are checked separately.
The minima over the checked candidates are exactly

```
near squared margin = 137427179858569/40000000000000000
far squared margin  = 71532731492067/7812500000000000
same-cell margin    = 3303/62500000
```

These agree with the production certificate. They are not asserted here to
be global optimal margins over every omitted translate or the polygon set.

The radius factor is also checked differently. For `c=100863/100000`, set
`t=2/c^2-1` and `s=4t^2-2`. Exact arithmetic verifies `t>0`, `s>0`, and
`s^2<3`. Therefore

```
t^2 < (2+sqrt(3))/4 = cos(pi/12)^2,
1/c^2 < (1+cos(pi/12))/2 = cos(pi/24)^2.
```

The positive branches give `c > sec(pi/24)`. This uses no copied radical
approximations from the production checker. Reducing `c` to `100862/100000`
is rejected by this test.

## Reproduction and failure controls

From this directory, on Python 3.10.20:

```sh
python reviewer_checks.py
python -O reviewer_checks.py
python -m unittest discover -s . -p test_audit.py -v
```

Both independent runs returned `status: PASS`, `cells: 90`,
`pair_specific_candidates: 662`, `near: 408`, and `far: 254`.
The production suite passed all **20 tests**, including the 806 direct
rational-distance classifier cases and optimized CLI checks.

The independent checker also passed 12 control groups: 387 signed integer
ceiling cases; rejection of an insufficient secant factor and duplicate JSON
keys; two safe separated/overlapping fixtures; rejection of unit pairs inside
a period and across a period boundary; rejection at both closed gap endpoints
and at the same-cell diameter endpoint; rejection of the actual-source center
mutation; and invariance after all 90 centers were independently shifted by
large positive or negative lattice vectors. The latter check still finds
exactly 408 near pairs without normalizing the centers.

## Limits

Both implementations depend on Python, its exact integer arithmetic and
rational parsing, and the same pinned configuration. Their logical
independence does not remove those shared trusted dependencies. The Euclidean
and trigonometric implications are written arguments, not kernel-checked
formal proofs. The finite computations establish the stated fixed-data disk
criterion together with those arguments; they do not certify arbitrary
colorings or the unreviewed blue-progression claim. No claim of human review,
global novelty, or an improved Ramsey bound is made.
