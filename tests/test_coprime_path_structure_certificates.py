"""Small exhaustive and adversarial checks of positive structural evidence."""
from copy import deepcopy
import gzip
from itertools import combinations, permutations
import json
from math import gcd
from pathlib import Path
import subprocess
import sys

import pytest

from coprime_path_structure_certificates import (
    has_edge_transversal, validate_cut_paths, validate_fault_paths,
    validate_cut_extensions,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'src/coprime_path_structure_certificates.py'
AUDIT = ROOT / 'docs/audits/coprime-path-nine-2026-10-18'


def small_cuts():
    records = []
    for size in (1, 2):
        for side in combinations(range(1, 5), size):
            path = next(p for p in permutations(range(1, 5), 3)
                        if all(gcd(a, b) == 1 and ((a in side) != (b in side))
                               for a, b in zip(p, p[1:])))
            records.append({'side': list(side), 'path': list(path)})
    return {'n': 4, 'target_edges': 2, 'minimum_side': 1,
            'status': 'complete', 'records': records}


def small_faults():
    return {'n': 4, 'target_edges': 1, 'deleted_vertices': 1,
            'deleted_edges': 1, 'status': 'complete',
            'classes': [[1, 3], [2, 4]], 'records': [
                {'deleted': [1], 'paths': [[2, 3], [3, 4]]},
                {'deleted': [2], 'paths': [[1, 3], [1, 4], [3, 4]]},
            ]}


def small_extensions():
    records = []
    for vertex in range(1, 5):
        side = [vertex]
        for edge in combinations([v for v in range(1, 5) if v != vertex], 2):
            if gcd(*edge) != 1:
                continue
            def valid(path):
                used = {tuple(sorted(pair)) for pair in zip(path, path[1:])}
                return edge in used and all(gcd(a, b) == 1 and (
                    (a, b) == edge or ((a in side) != (b in side))) for a, b in used)
            path = next(p for p in permutations(range(1, 5), 3) if valid(p))
            records.append({'side': side, 'edge': list(edge), 'path': list(path)})
    return {'n': 4, 'target_edges': 2, 'side_size': 1, 'minimum_side_edges': 0,
            'status': 'complete', 'records': records}


CASES = [(small_cuts, validate_cut_paths), (small_faults, validate_fault_paths),
         (small_extensions, validate_cut_extensions)]


def test_small_certificates_have_complete_derived_case_counts():
    assert validate_cut_paths(small_cuts())['validated_cuts'] == 10
    faults = validate_fault_paths(small_faults())
    assert (faults['validated_orbits'], faults['covered_deletions']) == (2, 4)
    assert faults['validated_paths'] == 5
    extensions = validate_cut_extensions(small_extensions())
    assert (extensions['qualified_cuts'], extensions['validated_pairs']) == (4, 10)


@pytest.mark.parametrize('factory,validate', CASES)
@pytest.mark.parametrize('damage', ['missing', 'duplicate', 'incomplete', 'boolean_n',
                                    'zero_length', 'oversized_length'])
def test_rejects_incomplete_cases_and_invalid_task_parameters(factory, validate, damage):
    data = factory()
    if damage == 'missing':
        data['records'].pop()
    elif damage == 'duplicate':
        data['records'].append(deepcopy(data['records'][0]))
    elif damage == 'incomplete':
        data['status'] = 'inconclusive'
    elif damage == 'boolean_n':
        data['n'] = True
    elif damage == 'zero_length':
        data['target_edges'] = 0
    else:
        data['target_edges'] = data['n']
    with pytest.raises(ValueError):
        validate(data)


@pytest.mark.parametrize('path', [[1, 1, 2], [1, 2, 8], [True, 2, 3],
                                 [1, 2], [1, 2, 4], '1,2,3'])
def test_rejects_invalid_or_noncoprime_paths(path):
    data = small_cuts()
    data['records'][0]['path'] = path
    with pytest.raises(ValueError):
        validate_cut_paths(data)


def test_cuts_reject_non_crossing_path_and_noncanonical_side():
    data = small_cuts()
    data['records'][0]['path'] = [1, 2, 3]  # The last edge misses side {1}.
    with pytest.raises(ValueError, match='cross'):
        validate_cut_paths(data)
    data = small_cuts()
    data['records'][-1]['side'].reverse()
    with pytest.raises(ValueError):
        validate_cut_paths(data)


@pytest.mark.parametrize('classes', [[[1, 2], [3, 4]], [[1, 3], [2]],
                                    [[1, 3], [2, 4], []], [[1, 3], [2, True]],
                                    [[1, 3], [2, 2, 4]], 'bad'])
def test_faults_require_a_partition_into_verified_symmetries(classes):
    data = small_faults()
    data['classes'] = classes
    with pytest.raises(ValueError):
        validate_fault_paths(data)


def test_faults_reject_hit_family_and_path_meeting_deleted_vertex():
    data = small_faults()
    data['records'][0]['paths'].pop()
    with pytest.raises(ValueError, match='transversal'):
        validate_fault_paths(data)
    data = small_faults()
    data['records'][0]['paths'][0] = [1, 2]
    with pytest.raises(ValueError):
        validate_fault_paths(data)


@pytest.mark.parametrize('factory,validate,field,value', [
    (small_cuts, validate_cut_paths, 'minimum_side', 0),
    (small_cuts, validate_cut_paths, 'minimum_side', 3),
    (small_faults, validate_fault_paths, 'deleted_vertices', 4),
    (small_faults, validate_fault_paths, 'deleted_edges', -1),
    (small_extensions, validate_cut_extensions, 'side_size', 0),
    (small_extensions, validate_cut_extensions, 'minimum_side_edges', True),
])
def test_rejects_invalid_case_parameters(factory, validate, field, value):
    data = factory()
    data[field] = value
    with pytest.raises(ValueError):
        validate(data)


def test_extensions_reject_wrong_internal_edge_and_unused_distinguished_edge():
    data = small_extensions()
    data['records'][0]['edge'] = [1, 2]  # Meets its side {1}.
    with pytest.raises(ValueError):
        validate_cut_extensions(data)
    data = small_extensions()
    data['records'][0]['path'] = [2, 1, 4]  # Valid crossing path, missing edge 23.
    with pytest.raises(ValueError, match='distinguished'):
        validate_cut_extensions(data)


def test_rejects_nonrecord_sequence():
    data = small_cuts()
    data['records'] = ['a purported record']
    with pytest.raises(ValueError, match='records'):
        validate_cut_paths(data)


def test_faults_reject_empty_family():
    data = small_faults()
    data['records'][0]['paths'] = []
    with pytest.raises(ValueError, match='family'):
        validate_fault_paths(data)


def test_extensions_reject_a_second_internal_edge():
    data = small_extensions()
    data['records'][0]['path'] = [2, 3, 4]  # 23 is distinguished; 34 is also internal.
    with pytest.raises(ValueError, match='neither crossing nor distinguished'):
        validate_cut_extensions(data)


def test_transversal_check_matches_exhaustive_enumeration():
    universe = [(1, 2), (1, 3), (2, 3)]
    subsets = [frozenset(s) for size in range(4) for s in combinations(universe, size)]
    for mask in range(1 << len(subsets)):
        family = [s for i, s in enumerate(subsets) if mask >> i & 1]
        for budget in range(4):
            expected = any(all(set(choice) & path for path in family)
                           for size in range(budget + 1)
                           for choice in combinations(universe, size))
            assert has_edge_transversal(family, budget) is expected


@pytest.mark.parametrize('mode,factory', [('cuts', small_cuts), ('faults', small_faults),
                                         ('extensions', small_extensions)])
def test_isolated_optimized_cli_checks_plain_and_compressed_json(tmp_path, mode, factory):
    path = tmp_path / (mode + ('.json.gz' if mode == 'faults' else '.json'))
    raw = json.dumps(factory()).encode()
    path.write_bytes(gzip.compress(raw) if path.suffix == '.gz' else raw)
    run = subprocess.run([sys.executable, '-I', '-S', '-O', str(SCRIPT), mode, str(path)],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)['n'] == 4


@pytest.mark.parametrize('record', [None, [], {}, {'n': 4}, small_cuts() | {'records': []}])
def test_cli_reports_invalid_evidence_as_json(tmp_path, record):
    path = tmp_path / 'invalid.json'
    path.write_text(json.dumps(record))
    run = subprocess.run([sys.executable, '-I', '-S', '-O', str(SCRIPT), 'cuts', str(path)],
                         capture_output=True, text=True)
    assert run.returncode == 1
    assert 'error' in json.loads(run.stderr)


@pytest.mark.parametrize('filename,validate,key,count', [
    ('cuts.json.gz', validate_cut_paths, 'validated_cuts', 62322),
    ('fault-families.json.gz', validate_fault_paths, 'validated_orbits', 262),
    ('extensions.json.gz', validate_cut_extensions, 'validated_pairs', 63859),
])
def test_archived_positive_certificates(filename, validate, key, count):
    with gzip.open(AUDIT / filename, 'rt') as source:
        data = json.load(source)
    assert (data['n'], data['target_edges']) == (17, 9)
    assert validate(data)[key] == count
