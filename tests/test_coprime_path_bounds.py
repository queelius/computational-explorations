"""Independent checks for finite sufficient path bounds, not exact thresholds."""

import importlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys

import pytest


def bounds_module():
    assert importlib.util.find_spec("coprime_path_bounds") is not None, (
        "the finite structural bound calculator is missing"
    )
    return importlib.import_module("coprime_path_bounds")


def brute_counts(n, excluded):
    vertices = [a for a in range(1, n + 1) if all(a % d for d in excluded)]
    edges = sum(math.gcd(a, b) == 1 for a, b in itertools.combinations(vertices, 2))
    return len(vertices), edges


@pytest.mark.parametrize("excluded", [(), (2,), (3, 5), (6, 10, 15), (30, 42, 70), (2, 4, 2), (1,)])
def test_counts_match_gcd_enumeration_with_overlapping_deletions(excluded):
    module = bounds_module()
    counts = list(module.induced_counts(85, excluded))
    assert [c.n for c in counts] == list(range(1, 86))
    for c in counts:
        assert (c.vertices, c.edges) == brute_counts(c.n, excluded)


def test_empty_range_and_vertex_one():
    module = bounds_module()
    assert list(module.induced_counts(0)) == []
    assert list(module.induced_counts(1)) == [module.GraphCounts(1, 1, 0)]
    assert list(module.induced_counts(1, (1,))) == [module.GraphCounts(1, 0, 0)]


@pytest.mark.parametrize("excluded", [(), (2,), (3, 5), (30, 42, 70), (1,)])
def test_first_bound_matches_independent_graph_enumeration(excluded):
    module = bounds_module()
    results = module.density_bounds([8, 3, 4, 8, 6, 10], 50, excluded)
    assert [r.path_edges for r in results] == [3, 4, 6, 8, 10]
    for result in results:
        expected = None
        for n in range(1, 51):
            v, e = brute_counts(n, excluded)
            if e > (result.path_edges - 1) * v:
                expected = (n, v, e)
                break
        actual = result.upper_bound
        assert (None if actual is None else (actual.n, actual.vertices, actual.edges)) == expected


def test_equality_is_not_a_sufficient_bound_and_budget_is_explicit():
    module = bounds_module()
    assert module.density_bounds([4], 9)[0].upper_bound is None
    assert module.density_bounds([4], 10)[0].upper_bound == module.GraphCounts(10, 10, 31)
    assert module.density_bounds([3], 0)[0].upper_bound is None
    assert module.density_bounds([], 100) == ()


@pytest.mark.parametrize("k,lower", [(3, 5), (4, 5), (5, 9), (6, 9), (7, 13), (8, 13), (9, 17), (10, 17)])
def test_cover_lower_bound_has_correct_edge_convention(k, lower):
    assert bounds_module().density_bounds([k], 0)[0].lower_bound == lower


@pytest.mark.parametrize("m", [1, 2, 3])
def test_cover_construction_avoids_target_path_by_independent_dp(m):
    from coprime_path_certificates import PathProblem, validate_witness

    n, k = 4 * m, 2 * m + 1
    a_cover = set(range(1, 2 * m, 2))
    colors = [[a, b, int(a not in a_cover and b not in a_cover)]
              for a in range(1, n + 1) for b in range(a + 1, n + 1)
              if math.gcd(a, b) == 1]
    result = validate_witness(PathProblem(n, k), colors)
    assert max(result) <= 2 * m
    assert bounds_module().density_bounds([k], 0)[0].lower_bound == n + 1


@pytest.mark.parametrize("limit", [-1, 2.5, True, "10"])
def test_invalid_range_rejected(limit):
    module = bounds_module()
    with pytest.raises(ValueError):
        list(module.induced_counts(limit))
    with pytest.raises(ValueError):
        module.density_bounds([3], limit)


@pytest.mark.parametrize("divisor", [0, -2, 2.5, True, "2"])
def test_invalid_exclusion_rejected(divisor):
    with pytest.raises(ValueError):
        list(bounds_module().induced_counts(10, [divisor]))


@pytest.mark.parametrize("k", [0, 1, 2, -3, 3.5, True, "3"])
def test_invalid_path_length_rejected(k):
    with pytest.raises(ValueError):
        bounds_module().density_bounds([k], 10)


def test_cli_json_under_isolated_optimized_python():
    module = bounds_module()
    script = Path(module.__file__)
    process = subprocess.run(
        [sys.executable, "-I", "-S", "-O", str(script), "4", "100", "--max-n", "10"],
        capture_output=True, text=True, check=True,
    )
    report = json.loads(process.stdout)
    assert report["max_n"] == 10
    assert report["excluded_multiples"] == [30, 42, 70]
    row, exhausted = report["bounds"]
    assert row["lower_bound"] == 5
    assert row["whole_graph_upper"] == {"n": 10, "vertices": 10, "edges": 31}
    assert exhausted["whole_graph_upper"] is None
    assert exhausted["induced_upper"] is None


def test_cli_exclusions_and_invalid_input():
    script = Path(bounds_module().__file__)
    process = subprocess.run(
        [sys.executable, str(script), "3", "--max-n", "20", "--exclude-multiples", "1"],
        capture_output=True, text=True, check=True,
    )
    row = json.loads(process.stdout)["bounds"][0]
    assert row["whole_graph_upper"]["n"] == 7
    assert row["induced_upper"] is None
    invalid = subprocess.run([sys.executable, str(script), "2"], capture_output=True, text=True)
    assert invalid.returncode == 2
    assert invalid.stdout == ""
