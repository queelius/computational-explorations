# Repository Guidelines

## Project Structure & Module Organization

- `src/`: standalone Python modules for number theory, combinatorics, SAT searches, and problem analysis.
- `tests/`: pytest suites; `conftest.py` adds `src/` to the import path and provides shared fixtures.
- `lean/`: Lean 4 formalizations with pinned Mathlib dependencies.
- `proofs/`, `docs/`, and `discoveries/`: proof arguments, research reports, and topic-specific results and computational artifacts.
- `paper/`, `e-jc/`, and `jis/`: LaTeX manuscripts and journal submission packages.
- `data/erdosproblems/`: ignored external database checkout; data-dependent tests expect `data/problems.yaml` within it.

## Build, Test, and Development Commands

Use Python 3.10 or newer. Core dependencies and test extras are declared in `pyproject.toml`; some experiments additionally require SciPy, scikit-learn, SymPy, or python-sat.

Run Python commands from the repository root:

- `python -m pytest`: run the full suite, including computationally expensive tests.
- `python -m pytest -m "not slow"`: exclude tests explicitly marked slow.
- `python -m pytest tests/test_kelley_meka_schur.py -q`: run a focused module suite.
- `python -m pytest --cov=src --cov-report=term-missing`: inspect coverage and missing lines.
- `python src/verify_all.py`: execute research-claim checks and generate a verification report; potentially lengthy.
- `cd lean && lake build NPG2_DensitySchur`: build a specific formalization; select the relevant target from `lakefile.lean`.

## Coding Style & Naming Conventions

Follow existing Python style: four-space indentation, `snake_case` modules/functions, `PascalCase` classes, and descriptive mathematical docstrings. Add type annotations to new interfaces. Prefer structured data and derived behavior over parallel lookup tables or regex parsing of structured formats. No formatter or linter is configured.

## Testing Guidelines

Name suites `tests/test_<module>.py` and functions `test_<behavior>`. Add unit and integration coverage for new functionality, including small exhaustive cases and independent cross-checks. Mark expensive tests `@pytest.mark.slow`; the configured timeout is 120 seconds per test. Review missing coverage; no numerical minimum is configured.

## Commit & Pull Request Guidelines

History uses concise, descriptive subjects, often prefixed by topic, such as `Schur:` or `README:`. Keep commits focused. PRs should explain the change, link relevant problems/issues, report validation commands and outcomes, and update affected research records.

## Research Integrity

Follow `CLAUDE.md`: preserve cited paths and the repository remote. Support exact computational values with witnesses and upper-bound verification. Claim Lean verification only after the relevant file builds without `sorry`. Distinguish conjectures, empirical evidence, and proofs.
