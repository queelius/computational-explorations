# Independently checked blue-progression cover for Erdős188

Alexander Richard Towell, with substantial OpenAI Codex assistance.

The new integer acceptor corroborates **Claim B** of [Carson Crocker’s v5
construction](https://doi.org/10.5281/zenodo.23405962): every 60-term unit-spaced
straight progression contains a red point, at every starting position and
direction. It checked **147,421,290 closed squares in 40,198 angular intervals**,
including exact spatial/directional coverage. Full execution took 165.23 seconds
with eight workers. The source already has several checkers; this is external
corroboration using a different disk-containment test and arithmetic.

Together with the separate [Claim A audit](https://github.com/queelius/computational-explorations/pull/8),
this corroborates the source upper bound `K_* <=60`. It is not a new coloring
or bound, an audit of the lower bound, a formal proof, or human peer review.

- [Precise proposition and written proof](erdos188_blue_progression/README.md)
- [Independent integer acceptor](erdos188_blue_progression/audit.py) and [driver](erdos188_blue_progression/run.py)
- [Full execution receipt](erdos188_blue_progression/full/result.json), [compressed interval records](erdos188_blue_progression/full/intervals.jsonl.gz), and [source pins](erdos188_blue_progression/source-pins.json)
- [Separate AI review](erdos188_blue_progression/review.md), [independent oracle results](erdos188_blue_progression/reviewer-result.json), and [44 rejecting controls](erdos188_blue_progression/real-controls.json)
- [License and attribution](erdos188_blue_progression/LICENSE.md)

## Reproduce from the repository root

```sh
python -m pip install -r docs/audits/erdos188-blue-progression-2026-10-18/erdos188_blue_progression/requirements.txt
PYTHONPATH=docs/audits/erdos188-blue-progression-2026-10-18 python -m erdos188_blue_progression.run --workers 8 --output /tmp/erdos188-blue-replay
python -m pytest -q tests/test_erdos188_blue_audit.py
```

Expected full result: `FULL_COVER_VERIFIED`, 147,421,290 leaves, 40,198 intervals,
and `direction_tiling_checked: true`. `--pilot 80` is explicitly partial and
cannot establish the theorem. Exact counts are supplied for the pinned search
and environment; any changed witness search still has to pass every inequality
and the full coverage checks.

The source floating/Numba search only proposes witnesses. The new acceptor
uses Python integers/Fractions, independently bounded Taylor polynomials and
strict square-corner distance inequalities. No Arb acceptance result is used.
The compressed log is a receipt, not all witnesses; full verification requires
regenerating and checking the witnesses with the command above. Tests require
only the standard library and pytest except the two generator integration tests,
which explicitly skip when NumPy/Numba are unavailable.

The contribution credits Crocker’s construction and prior checkers, the
Currier–Mody–Xie–Zhang framework, and Gabriel Currier’s variable-cell suggestion.
The exact input and unmodified generator retain the deposit’s CC BY4.0 terms.
Substantial OpenAI Codex assistance includes implementation, drafting and one
separate AI review; no human peer review is represented.
