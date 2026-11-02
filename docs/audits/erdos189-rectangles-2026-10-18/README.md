# Independent audit of Crocker's two-color unit-area rectangle certificate

Alexander Richard Towell, with substantial OpenAI Codex assistance.
Examined 2026-10-18. Original construction and certificate: **Carson Crocker**,
[Zenodo 23178517](https://doi.org/10.5281/zenodo.23178517), CC BY 4.0.

**Finding:** a fresh integer-arithmetic check reconstructs exactly **676**
unit-area rectangles on the supplied **180** points, matches all **1,353** CNF
clauses, and checks every step of the saved refutation. This independently
corroborates Crocker's statement that every two-coloring of the real plane
contains a monochromatic rectangle of area one. It is a verification result,
not a new rectangle theorem, a new witness, or a claim of human peer review.

The geometric check uses equal diagonals with a common midpoint. Crocker's
supplied Python checker instead enumerates perpendicular side pairs in three
ways. This implementation neither imports nor executes his checker. The
source was read before implementation, so this is not a blind replication.
His existing DRAT, LRAT, reported cake_lpr check, and compiler-assumed Lean
formalization are credited; we do not replace or re-audit their trust models.

## Reproduce

Python 3.10 or later, standard library only. From this directory:

```sh
python reproduce.py
```

This runs the failure controls, downloads the 48.7 MB pinned source archive,
checks its SHA-256, extracts only the point list, CNF and LRAT proof into a
temporary directory, runs the saved reviewer's checks, and runs the complete
audit. No downloaded program is
executed. A previously downloaded archive can be supplied with
`python reproduce.py --archive /path/to/FINAL_189_release_189_lb.zip`.

Expected: tests pass, then `Geometry PASS: 180 points, 676 rectangles, 1353
clauses`, and a JSON result with `status: PASS`, `additions: 317041`,
`deletion_records: 159589`, `propagation_hints: 7567456` and
`final_clause_id: 382906`. Observed proof runtimes on the audit machine ranged
from 13 to 58 seconds, plus download and tests. This is an observation, not a benchmark
against the source tools. The full input has 476,630 proof records.

For already unpacked data, `python audit.py /path/to/cert` performs the same
mathematical checks and prints the input digests, but does not pin the source
archive. Use `reproduce.py` to verify this exact deposit. Run tests alone with
`python -m unittest -v test_audit`.

## Geometric bridge

Put

\[
s=192^{-1/4}>0,\qquad
L(x,y)=s(x+y/2,\sqrt3\,y/2).
\]

The source points are exactly the images under \(L\) of the integer pairs in
`cert180.pts`. We check that the IDs are \(1,\ldots,180\) and the points are
distinct. For an integer vector \(d=(d_x,d_y)\),

\[
\lVert Ld\rVert^2=s^2q(d),\qquad
q(d)=d_x^2+d_xd_y+d_y^2,\qquad
\det L=s^2\sqrt3/2=1/16.
\]

Take two distinct unordered pairs \(\{a,b\}\) and \(\{c,d\}\) of points.
Their diagonals have a common midpoint exactly when \(a+b=c+d\), using
integer coordinates. Let \(v=b-a\) and \(w=d-c\). The equal-length condition
is exactly \(q(v)=q(w)\). Relative to their common center, the physical
endpoints are \(-Lv/2,Lv/2,-Lw/2,Lw/2\). The adjacent side vectors in the
order \(a,c,b,d\) are, up to sign,

\[
(Lv-Lw)/2\quad\hbox{and}\quad(Lv+Lw)/2.
\]

Their dot product is
\((\lVert Lv\rVert^2-\lVert Lw\rVert^2)/4=0\). They therefore form a
rectangle when nondegenerate. Its area is

\[
\frac{|\det(Lv,Lw)|}{2}
=\frac{|\det(v,w)|}{32}.
\]

Thus a diagonal determinant of absolute value **32** both excludes degeneracy
and gives area exactly one. Conversely, the opposite pairs of every rectangle
have the same midpoint and equal lengths, and its determinant satisfies this
condition if its area is one. Enumerating all point pairs and all pair-pairs
within these exact buckets is therefore complete. Checking four distinct
point IDs is an additional explicit guard.

All these decisions use Python integers. There is no floating-point tolerance,
angle approximation, sampling of orientations, or finite discretization of
the ambient plane.

## Color encoding and passage to the plane

Associate variable \(i\) to the truth value “point \(i\) has the same color
as point 1.” The unit clause \((1)\) is valid for every two-coloring after
this relabeling. For a rectangle with vertex IDs \(a,b,c,d\), the clauses

\[
(a\lor b\lor c\lor d),\qquad
(\neg a\lor\neg b\lor\neg c\lor\neg d)
\]

together say that its four vertices are not all one color. We compare the
**multiset** of every supplied clause with the color unit and these two
clauses for every geometrically enumerated rectangle. Clause order and
literal order are irrelevant; extra, missing or duplicated clauses fail.

If a two-coloring of the whole plane avoided monochromatic unit-area
rectangles, its restriction to these 180 points, relabeled as above, would
satisfy this exact CNF. A sound finite refutation contradicts that. This is
why a finite witness establishes the plane statement; it does not rely on
exhaustively sampling plane colorings, regularity, or measurability.

## Refutation checker and its soundness invariant

`audit.py` supports the **positive-hint / RUP subset of LRAT** used by every
addition in this input. Negative hints requiring RAT are rejected; this is
not advertised as a general-purpose LRAT implementation. Input variable
bounds, clause terminators, clause counts and proof identifiers are checked.
Tautologies and repeated variables are rejected as an unsupported, unnecessary
extension of this small checker.

The live clause database initially contains the CNF. To accept a new clause
\(C\), temporarily set all its literals false. Each listed positive hint
must name a live clause that is either unit under the current partial
assignment, forcing its one unassigned literal, or entirely false, establishing
contradiction. The final hint must produce contradiction; no trailing hints
are ignored. A satisfied or nonunit hinted clause fails the strict checker.

Consequently the live clauses imply \(C\): any model of them that falsified
\(C\) would have to obey every forced literal and then falsify an already
required clause. Inductively, every model of the original CNF satisfies every
derived live clause. Deleting clauses only weakens this database, preserving
that invariant. Addition IDs cannot be reused; hints cannot name deleted or
unknown clauses. The proof must end with an accepted empty clause and no
subsequent material. The original CNF therefore has no model.

The complete replay accepted 317,041 additions, including that final empty
clause, and 159,589 deletion records deleting 318,358 clauses. It checked
7,567,456 individual propagation hints; the maximum live database had 11,040
clauses. Counts describe the completed exact computation, not a search.

## Controls and limits

Tests cover an actual unit-area rectangle, translations and central
reflections, an area-preserving shear that destroys right angles, a unit-area
nonrectangular rhombus, a rectangle of the wrong area, malformed point and
CNF inputs, missing/extra clauses, a satisfiable formula, false unit derivation,
invalid/deleted hint IDs, unsupported RAT, ignored proof tails and truncation.
The reproduction also checks mutations of the actual supplied finite data.

One separately tasked AI reviewer found no soundness blocker. Its preserved
`reviewer_checks.py` cross-checks the geometry by adjacent sides on both the
deposited points and a complete 11-by-11 lattice (676 and 194 rectangles),
and checks 5,868 small candidate/hint traces against all satisfying Boolean
assignments. All 504 accepted candidate additions were entailed. This domain
has two variables and at most three initial clauses; it is not an exhaustive
check of arbitrary proof histories. Ten further boundary controls pass.
See `review.md` for the exact read set and limits. The initial review read
the core checker and its then-14 tests; it did not review the later download
wrapper or this README. The expanded regression suite is checked separately.

This packet is a written reduction plus exact computation checked by ordinary
Python execution. It is **not a kernel-checked formal proof**. The remaining
trust includes the written argument, checker implementation, Python runtime,
and hardware; failure controls and a separate AI review do not remove it.
No human peer review is asserted. The supplied Lean proof is outside this
audit, as are point minimality, the stronger listed side-length restriction,
the best possible number of colors, and the source's upper bound.

Scaling gives a monochromatic rectangle for each prescribed positive area,
but the color can depend on that area. We do **not** prove that one fixed
color has rectangles of every area, nor claim to settle the original
finite-color Erdős Problem 189. The source itself distinguishes these claims.

## Provenance and licensing

The exact archive and file pins are recorded in `source.json`; `result.json`
records the completed full run. The source is licensed CC BY 4.0 according to
both its Zenodo metadata and README. Its point set, formula and refutation
remain Crocker's work. The new checker and tests are MIT-licensed (see
`LICENSE`); this audit's prose is CC BY 4.0. Code, derivation, tests and prose
were produced with substantial OpenAI Codex assistance for Alexander Richard
Towell. There is no claim that an AI review is independent human peer review.
