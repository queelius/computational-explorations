"""Exercise witness validation and the dependency-free CLI boundary."""

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pytest

from verify_coprime_witnesses import Witness, verify_witness


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "src" / "verify_coprime_witnesses.py"


@pytest.fixture
def triangle():
    return {
        "n": 3,
        "forbidden_clique_size": 3,
        "colors": 2,
        "coloring": [[1, 2, 0], [1, 3, 0], [2, 3, 1]],
    }


def run_checker(*paths, optimized=False):
    # -I -S proves verification works without the repository's SAT/NumPy stack.
    flags = ["-I", "-S"] + (["-O"] if optimized else [])
    return subprocess.run(
        [sys.executable, *flags, str(CHECKER), *map(str, paths)],
        capture_output=True, text=True, timeout=30,
    )


def write_record(tmp_path, record):
    path = tmp_path / "witness.json"
    path.write_text(json.dumps(record))
    return path


@pytest.mark.parametrize("optimized", [False, True])
def test_valid_witness_is_recomputed_without_dependencies(tmp_path, triangle, optimized):
    triangle.update(valid=False, edges=999, cliques_checked=999)
    path = write_record(tmp_path, triangle)
    original = path.read_bytes()
    result = run_checker(path, optimized=optimized)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["valid"] is True
    checked = report["results"][0]
    assert (checked["n"], checked["edges"], checked["cliques_checked"]) == (3, 3, 1)
    assert path.read_bytes() == original


@pytest.mark.parametrize("field,value", [
    ("n", 0), ("n", -1), ("n", True), ("n", 3.0), ("n", "3"),
    ("forbidden_clique_size", 1), ("forbidden_clique_size", False),
    ("forbidden_clique_size", 3.0),
    ("colors", 0), ("colors", -1), ("colors", True), ("colors", 2.0),
    ("coloring", None), ("coloring", {}), ("coloring", "1,2,0"),
])
def test_rejects_invalid_metadata(triangle, field, value):
    triangle[field] = value
    with pytest.raises(ValueError):
        verify_witness(Witness.from_record(triangle))


@pytest.mark.parametrize("field", ["n", "forbidden_clique_size", "colors", "coloring"])
def test_rejects_missing_required_fields(triangle, field):
    del triangle[field]
    with pytest.raises(ValueError):
        Witness.from_record(triangle)


@pytest.mark.parametrize("row", [
    [1, 2], [1, 2, 0, 0], None, "120",
    [True, 2, 0], [1.0, 2, 0], [1, 2, False], [1, 2, 0.0],
    [1, 2, -1], [1, 2, 2], [2, 1, 0], [1, 1, 0], [1, 4, 0],
])
def test_rejects_malformed_or_noncanonical_edges(triangle, row):
    triangle["coloring"][0] = row
    with pytest.raises(ValueError):
        verify_witness(Witness.from_record(triangle))


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "noncoprime"])
def test_requires_exactly_one_color_per_coprime_edge(mutation):
    record = {
        "n": 4, "forbidden_clique_size": 3, "colors": 2,
        "coloring": [[1, 2, 0], [1, 3, 1], [1, 4, 0], [2, 3, 0], [3, 4, 0]],
    }
    if mutation == "missing":
        record["coloring"].pop()
    elif mutation == "duplicate":
        record["coloring"].append([1, 2, 0])
    else:
        record["coloring"].append([2, 4, 1])
    with pytest.raises(ValueError):
        verify_witness(Witness.from_record(record))


@pytest.mark.parametrize("optimized", [False, True])
def test_rejects_monochromatic_clique_even_when_record_claims_valid(tmp_path, triangle, optimized):
    triangle["coloring"] = [[1, 2, 1], [1, 3, 1], [2, 3, 1]]
    triangle["valid"] = True
    result = run_checker(write_record(tmp_path, triangle), optimized=optimized)
    assert result.returncode == 1
    assert json.loads(result.stdout)["results"][0]["valid"] is False


def test_single_vertex_has_no_edges_or_cliques():
    record = {"n": 1, "forbidden_clique_size": 2, "colors": 1, "coloring": []}
    result = verify_witness(Witness.from_record(record))
    assert (result.edges, result.cliques_checked) == (0, 0)


@pytest.mark.parametrize("field,value", [
    ("n", 0), ("n", True), ("forbidden_clique_size", 1), ("colors", 0),
    ("colors", 2.0), ("coloring", ((1, 2, False),)),
    ("coloring", ((1, 2),)), ("coloring", [[1, 2, 0]]),
])
def test_direct_construction_cannot_bypass_validation(triangle, field, value):
    witness = Witness.from_record(triangle)
    with pytest.raises(ValueError):
        replace(witness, **{field: value})


def test_rejects_a_monochromatic_clique_in_the_last_color(triangle):
    triangle["colors"] = 3
    triangle["coloring"] = [[1, 2, 2], [1, 3, 2], [2, 3, 2]]
    with pytest.raises(ValueError, match="Monochromatic"):
        verify_witness(Witness.from_record(triangle))


@pytest.mark.parametrize("content", ["{", "[]", "null"])
def test_reports_invalid_json_documents(tmp_path, content):
    path = tmp_path / "bad.json"
    path.write_text(content)
    result = run_checker(path)
    assert result.returncode == 1
    assert json.loads(result.stdout)["valid"] is False


def test_batch_reports_valid_and_missing_files_without_hiding_failure(tmp_path, triangle):
    valid = write_record(tmp_path, triangle)
    result = run_checker(tmp_path / "missing.json", valid)
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["valid"] is False
    assert [item["valid"] for item in report["results"]] == [False, True]


def test_saved_release_witnesses_have_expected_complete_checks():
    paths = sorted((ROOT / "docs/audits/coprime-ramsey-release-2026-10-17").glob("witness-*.json"))
    assert len(paths) == 3
    results = [verify_witness(Witness.from_record(json.loads(path.read_text()))) for path in paths]
    counts = sorted((item.n, item.edges, item.cliques_checked) for item in results)
    assert counts == [(10, 31, 42), (52, 829, 6684), (58, 1027, 49815)]
