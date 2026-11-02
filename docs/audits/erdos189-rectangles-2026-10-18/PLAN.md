# Independent finite audit: Crocker's two-color rectangle witness

Alexander Richard Towell, with substantial OpenAI Codex assistance.
Recorded 2026-10-18, before implementation. Selection completed at 07:49 UTC.
Visit began 07:39:12 UTC; verification reservation 08:09:12 UTC; hard stop
08:24:12 UTC. Archive base: `c8324835b958f4ea887090dc98142bb66e042b59`.

## Precise proposition and value

Check the finite implication supporting Carson Crocker's claim: every map
from the real plane to two colors has a monochromatic rectangle of area one.
The input points are `s(x + y/2, sqrt(3)y/2)`, where
`s = 192^(-1/4) > 0`, and `(x,y)` are the 180 distinct integer pairs in
`cert/cert180.pts`. Check that the supplied CNF consists exactly of a color
symmetry unit and both nonmonochromatic clauses for every area-one rectangle
in this set, and independently verify its saved refutation.

This is an external corroboration, not a new theorem or a claim that the
author lacks verification. His exact checker uses three enumerations of
perpendicular sides. This audit instead groups pairs by equal midpoint and
equal diagonal length, then checks area using the diagonal determinant.
His deposit also reports DRAT, LRAT, cake_lpr and a Lean proof with compiler
trust. We will execute our own small positive-hint LRAT/RUP checker, without
using those programs or trusting their saved outputs. We will not recheck
the Lean proof or claim kernel verification.

## Pins and assumptions

- Source: <https://doi.org/10.5281/zenodo.23178517>, Carson Crocker, CC BY 4.0.
- Archive: `FINAL_189_release_189_lb.zip`, 48,708,459 bytes.
- SHA256: `7b5dbdf14a96a29f6c4cb7b3176002d185776a85fd51747da6f693259b582e18`.
- Zenodo MD5: `bdf689e72eab72cb15f79ae006b111a9` (matched on download).
- Plasma source/overlap pin: `abe008481755ef6186c9ab93789b04702b8ff243`.
- Coordination: <https://github.com/plasma-ai/erdos/issues/62#issuecomment-6247282596>.

Assumptions for the mathematical bridge are ordinary Euclidean geometry,
the two-color restriction, and exact execution of the checker and its input
parser. Python execution and AI review are not formal proof or human peer
review. No measurability assumption is needed. This does not settle the
original Problem 189 or show that a single color realizes every area. We
will not assess the 21-color upper bound or point minimality.

## Method, success and stopping rule

1. Prove that distinct equal-length diagonals with a common midpoint yield
   a rectangle, and derive the exact normalization: unit area is equivalent
   to absolute determinant 32 for the two integer diagonal vectors.
2. Enumerate all unordered point pairs, group by their exact summed endpoint
   coordinates and squared length `dx^2 + dx*dy + dy^2`, and compare the
   resulting area-one quadruples to every CNF clause pair.
3. Stream every LRAT record; check every addition by its positive propagation
   hints, honor deletions, reject unsupported RAT steps, and require a derived
   empty clause. Initial inspection found 317,041 additions, 159,589 deletion
   records, no negative-hint lines, and one final empty clause.
4. Exercise geometric and proof failure controls, including a same-area
   nonrectangle, wrong area, altered/missing clauses, invalid hints and a
   satisfiable formula. Have at most one scoped independent reviewer assess
   the geometry-to-CNF-to-plane implication and hidden assumptions.

Success is fresh exact geometric agreement and a complete checked finite
refutation, with reproducible source pins and controls. A defect will be
reported only at its actual scope. Stop if the available proof language or
runtime is unsuitable; preserve completed coverage and the exact missing
step. Do not chase a smaller witness, a new color bound, or another cycle.
If external publication setup exceeds the remaining budget, retain the
packet locally and report the scoped result on the coordination thread.
