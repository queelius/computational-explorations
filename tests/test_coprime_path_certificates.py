"""Independent checks must reject bad evidence, including a wrong SAT encoding."""
from itertools import combinations, permutations, product
import math
import json
from pathlib import Path
import subprocess
import sys

import pytest

from coprime_path_certificates import PathProblem, validate_witness, validate_formula


@pytest.mark.parametrize('n,k', [(True,2),(3,False),(0,2),(3,0),(3.0,2),(3,2.5)])
def test_problem_rejects_invalid_integer_parameters(n,k):
    with pytest.raises(ValueError):
        PathProblem(n,k)


def test_simple_paths_do_not_reuse_vertices():
    problem=PathProblem(3,3)
    result=validate_witness(problem, [[1,2,0],[1,3,0],[2,3,0]])
    assert result == (2,0)  # The zero color has longest path two.


@pytest.mark.parametrize('coloring', [[],[[1,2,0]],[[1,2,0],[1,3,0],[1,3,1]],
    None, 'invalid', [[1,2]], [[1,2,'0']],
    [[2,1,0],[1,3,1],[2,3,0]],[[1,2,2],[1,3,1],[2,3,0]],
    [[1,2,True],[1,3,1],[2,3,0]],[[1,2,0.0],[1,3,1],[2,3,0]],
    [[1,2,0],[1,3,1],[2,3,0],[2,4,1]]])
def test_rejects_incomplete_noncanonical_or_invalid_colorings(coloring):
    with pytest.raises(ValueError):
        validate_witness(PathProblem(3,2),coloring)


def test_independent_witness_check_matches_permutation_oracle():
    n=5
    edges=[e for e in combinations(range(1,n+1),2) if math.gcd(*e)==1]
    for colors in product((0,1),repeat=len(edges)):
        assignment=dict(zip(edges,colors))
        maxima=[]
        for color in (0,1):
            longest=0
            for length in range(1,n):
                if any(all(assignment.get(tuple(sorted(pair)))==color
                           for pair in zip(path,path[1:]))
                       for path in permutations(range(1,n+1),length+1)):
                    longest=length
            maxima.append(longest)
        rows=[[a,b,c] for (a,b),c in zip(edges,colors)]
        assert validate_witness(PathProblem(n,n),rows)==tuple(maxima)
        if max(maxima)>=3:
            with pytest.raises(ValueError,match='monochromatic'):
                validate_witness(PathProblem(n,3),rows)
        else:
            assert validate_witness(PathProblem(n,3),rows)==tuple(maxima)


def test_formula_accepts_only_valid_path_exclusions_and_tautologies():
    # n=4 canonical edges: 12,13,14,23,34. Edges 12,23,34 form a path.
    problem=PathProblem(4,3)
    assert validate_formula(problem, [[1,4,5],[-1,-4,-5],[5,-5]]) == 2


@pytest.mark.parametrize('clauses', [ [[]], [[1]], [[1,1,4]], [[1,-4,5]],
    [[1,2,3]], [[1,2,4]], [[1,4,6]], [[True,4,5]], [[1.0,4,5]],
    [[0,4,5]], [[6,-6]], [[1,-1,2]], [[1,4]], [[1,2,3,4]] ])
def test_formula_rejects_nonpath_and_malformed_constraints(clauses):
    with pytest.raises(ValueError):
        validate_formula(PathProblem(4,3),clauses)


def test_formula_rejects_disconnected_cycle_and_edge():
    problem=PathProblem(5,4)
    positions={e:i+1 for i,e in enumerate(problem.edges)}
    clause=[positions[e] for e in ((1,2),(1,3),(2,3),(4,5))]
    with pytest.raises(ValueError):
        validate_formula(problem,[clause])


def test_cli_validates_witness_without_site_packages(tmp_path):
    path=tmp_path/'witness.json'
    path.write_text(json.dumps({'n':3,'path_edges':3,'coloring':[[1,2,0],[1,3,0],[2,3,0]]}))
    script=Path(__file__).resolve().parents[1]/'src/coprime_path_certificates.py'
    run=subprocess.run([sys.executable,'-I','-S','-O',str(script),'witness',str(path)],capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    assert json.loads(run.stdout)['longest_paths']==[2,0]


def test_cli_emits_checked_dimacs(tmp_path):
    path=tmp_path/'formula.json'
    path.write_text(json.dumps({'n':4,'path_edges':3,'clauses':[[1,4,5],[-1,-4,-5]]}))
    target=tmp_path/'formula.cnf'
    script=Path(__file__).resolve().parents[1]/'src/coprime_path_certificates.py'
    run=subprocess.run([sys.executable,str(script),'formula',str(path),'--dimacs-out',str(target)],capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    assert target.read_text()=='p cnf 5 2\n1 4 5 0\n-1 -4 -5 0\n'
    assert json.loads(run.stdout)['path_clauses']==2


@pytest.mark.parametrize('record', [[],{}, {'n':3,'path_edges':2,'coloring':[]},
    {'n':3,'path_edges':2,'coloring':[[1,2,0],[1,3,0],[2,3,0]]}])
def test_cli_rejects_invalid_witnesses(tmp_path,record):
    path=tmp_path/'bad.json';path.write_text(json.dumps(record))
    script=Path(__file__).resolve().parents[1]/'src/coprime_path_certificates.py'
    run=subprocess.run([sys.executable,str(script),'witness',str(path)],capture_output=True,text=True)
    assert run.returncode!=0


def test_bad_formula_does_not_create_dimacs(tmp_path):
    path=tmp_path/'bad.json';path.write_text(json.dumps({'n':4,'path_edges':3,'clauses':[[1]]}))
    target=tmp_path/'bad.cnf'
    script=Path(__file__).resolve().parents[1]/'src/coprime_path_certificates.py'
    run=subprocess.run([sys.executable,str(script),'formula',str(path),'--dimacs-out',str(target)],capture_output=True,text=True)
    assert run.returncode!=0 and not target.exists()
