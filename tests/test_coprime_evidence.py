"""Regression checks for proof completeness and full coloring witnesses."""

from types import SimpleNamespace

import pytest

import coprime_ramsey_sat as sat
import coprime_ramsey_variants as variants
from coprime_ramsey_variants import count_avoiding_colorings_sat


def test_failed_sample_does_not_prove_target_unsat():
    # The first seed fails, but another coloring of G(7) avoids triangles.
    with sat.encode_rcop_sat(7, 3)[0] as solver:
        assert solver.solve()
    proved, checked = sat.check_extension_unsat(6, 7, 3, num_seeds=1)
    assert not proved
    assert checked == 1


def test_seed_limit_is_not_exhaustion_even_when_threshold_is_true():
    # There are 78 base colorings after fixing the color of edge (1, 2).
    proved, checked = sat.check_extension_unsat(10, 11, 3, num_seeds=20)
    assert not proved
    assert checked == 20


def test_empty_sample_cannot_produce_an_exact_threshold(monkeypatch):
    # A controlled clock enters phase two after a real small SAT solve.
    ticks = iter((0.0, 6.0))
    monkeypatch.setattr(sat, "time", SimpleNamespace(time=lambda: next(ticks)))
    assert sat.compute_rcop4_with_extension(
        max_n=5, num_seeds=0, verbose=False
    ) == -1


def test_cli_reports_an_undetermined_threshold(monkeypatch, capsys):
    monkeypatch.setattr(sat, "compute_rcop_sat", lambda *args, **kwargs: -1)
    monkeypatch.setattr(sat, "compute_rcop4_with_extension",
                        lambda *args, **kwargs: -1)
    sat.main()
    output = capsys.readouterr().out
    for k in (2, 3, 4):
        assert f"R_cop({k}) = -1" not in output
        assert f"R_cop({k}): undetermined" in output


def test_variants_cli_does_not_publish_unknown_values_as_thresholds(monkeypatch, capsys):
    for name in ("compute_path_coprime_ramsey", "compute_cycle_coprime_ramsey",
                 "compute_multicolor_coprime_ramsey", "compute_bipartite_coprime_ramsey",
                 "compute_gallai_coprime_ramsey"):
        monkeypatch.setattr(variants, name, lambda *args, **kwargs: -1)
    variants.main()
    output = capsys.readouterr().out
    assert "-1" not in output
    assert "undetermined" in output
    assert "BIPARTITE COPRIME RAMSEY" not in output


@pytest.mark.parametrize("coloring", [
    {},
    {(1, 2): 0, (1, 3): 1},
    {(1, 2): 2, (1, 3): 2, (2, 3): 3},
    {(1, 2): 0.0, (1, 3): 0, (2, 3): 1},
    {(1, 2): False, (1, 3): 0, (2, 3): 1},
    {(2, 1): 0, (1, 3): 0, (2, 3): 1},
    {(1, 2): 0, (1, 3): 0, (2, 3): 1, (3, 4): 0},
    {(1, 2): 0, (1, 3): 0, (2, 3): 1, (1, 1): 0},
])
def test_validator_rejects_malformed_colorings(coloring):
    assert not sat.validate_avoiding_coloring(3, 3, coloring)


def test_validator_requires_edges_outside_any_forbidden_clique():
    assert not sat.validate_avoiding_coloring(2, 3, {})
    assert sat.validate_avoiding_coloring(2, 3, {(1, 2): 0})


def test_validator_rejects_non_coprime_extra_edge():
    coloring = {(1, 2): 0, (1, 3): 0, (1, 4): 0,
                (2, 3): 1, (3, 4): 1, (2, 4): 1}
    assert not sat.validate_avoiding_coloring(4, 3, coloring)


def test_counter_enumerates_free_edge_variables():
    assert count_avoiding_colorings_sat(2, 3) == 2
    # G(3) is K3 with no K4: all eight edge colorings are allowed.
    assert count_avoiding_colorings_sat(3, 4) == 8


def test_counter_does_not_report_a_cap_as_an_exact_count():
    with pytest.raises(RuntimeError):
        count_avoiding_colorings_sat(3, 3, max_count=1)


@pytest.mark.parametrize("budget", [78, 100])
def test_extension_exhaustion_including_exactly_at_budget(budget):
    result = sat.check_extensions(10, 11, 3, num_seeds=budget)
    assert result.status is sat.ExtensionStatus.EXHAUSTED
    assert result.seeds_checked == 78
    assert result.coloring is None


def test_extensible_result_contains_a_complete_witness():
    result = sat.check_extensions(3, 4, 3, num_seeds=20)
    assert result.status is sat.ExtensionStatus.EXTENSIBLE
    assert set(result.coloring) == {(1, 2), (1, 3), (1, 4), (2, 3), (3, 4)}
    assert sat.validate_avoiding_coloring(4, 3, result.coloring)


def test_extension_without_any_base_clique_includes_free_edges():
    result = sat.check_extensions(2, 3, 4, num_seeds=1)
    assert result.status is sat.ExtensionStatus.EXTENSIBLE
    assert set(result.coloring) == {(1, 2), (1, 3), (2, 3)}


def test_no_base_colorings_certifies_unsat_without_any_seed():
    result = sat.check_extensions(2, 3, 2, num_seeds=0)
    assert result.status is sat.ExtensionStatus.EXHAUSTED
    assert result.seeds_checked == 0


@pytest.mark.parametrize("arguments", [(1, 2, 3, 1), (3, 5, 3, 1),
                                      (3, 4, 1, 1), (3, 4, 3, -1)])
def test_invalid_extension_parameters_are_rejected(arguments):
    with pytest.raises(ValueError):
        sat.check_extensions(*arguments)


@pytest.mark.parametrize("n,k,budget,want,exhausted", [
    (2, 3, 0, 0, False),
    (2, 3, 1, 1, False),
    (2, 3, 2, 2, True),
    (2, 3, 3, 2, True),
    (3, 3, 6, 6, True),
    (1, 3, 0, 0, False),
    (1, 3, 1, 1, True),
    (2, 2, 0, 0, True),
])
def test_count_status_separates_exhaustion_from_capped_lower_bound(
        n, k, budget, want, exhausted):
    result = variants.count_avoiding_colorings(n, k, budget)
    assert result.count == want
    assert result.exhausted is exhausted


def test_density_does_not_treat_truncation_as_an_exact_fraction():
    with pytest.raises(variants.IncompleteEnumerationError) as error:
        variants.density_avoiding_colorings(3, 3, max_count=1)
    assert error.value.result.count == 1
    assert not error.value.result.exhausted


@pytest.mark.parametrize("n,k,cap", [(2, 3, -1), (2, 3, 1.5),
                                   (2, 3, True), (-1, 3, 5), (3, 1, 5)])
def test_invalid_count_parameters_are_rejected(n, k, cap):
    with pytest.raises(ValueError):
        variants.count_avoiding_colorings(n, k, cap)
