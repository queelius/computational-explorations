"""Boundary searches distinguish witnesses, UNSAT, and resource limits."""
import pytest
import json
import gzip
import hashlib
from pathlib import Path
import subprocess
import sys

from coprime_path_certificates import PathProblem, validate_formula, validate_witness
from coprime_path_search import SearchStatus, solve_path_problem


@pytest.mark.parametrize('n,k,expected', [
    (1,1,SearchStatus.SAT), (2,1,SearchStatus.UNSAT),
    (2,2,SearchStatus.SAT), (3,2,SearchStatus.UNSAT),
    (4,3,SearchStatus.SAT), (5,3,SearchStatus.UNSAT),
    (6,4,SearchStatus.SAT), (7,4,SearchStatus.UNSAT),
])
def test_search_matches_known_small_boundaries(n,k,expected):
    problem=PathProblem(n,k)
    result=solve_path_problem(problem,seconds=10)
    assert result.status is expected
    validate_formula(problem,result.clauses)
    if expected is SearchStatus.SAT:
        validate_witness(problem,result.coloring)
        assert result.proof is None
    else:
        assert result.coloring is None
        assert result.proof and '0' in result.proof


def test_zero_time_budget_is_inconclusive():
    result=solve_path_problem(PathProblem(5,3),seconds=0)
    assert result.status is SearchStatus.INCONCLUSIVE
    assert result.coloring is None and result.proof is None


def test_round_limit_is_not_unsat():
    problem=PathProblem(5,3)
    result=solve_path_problem(problem,seconds=10,max_rounds=1)
    assert result.status is SearchStatus.INCONCLUSIVE
    assert result.rounds==1
    validate_formula(problem,result.clauses)


def test_live_deadline_returns_inconclusive():
    result=solve_path_problem(PathProblem(13,8),seconds=0.02)
    assert result.status is SearchStatus.INCONCLUSIVE
    assert result.coloring is None and result.proof is None


@pytest.mark.parametrize('seconds', [-1,float('nan'),float('inf'),True,'10'])
def test_rejects_invalid_time_budget(seconds):
    with pytest.raises(ValueError):
        solve_path_problem(PathProblem(3,2),seconds=seconds)


@pytest.mark.parametrize('limit', [-1,True,1.5])
def test_rejects_invalid_round_budget(limit):
    with pytest.raises(ValueError):
        solve_path_problem(PathProblem(3,2),max_rounds=limit)


def test_cli_limit_produces_explicit_inconclusive_artifact(tmp_path):
    script=Path(__file__).resolve().parents[1]/'src/coprime_path_search.py'
    output=tmp_path/'search'
    run=subprocess.run([sys.executable,str(script),'5','3','--seconds','0','--output',str(output)],capture_output=True,text=True)
    assert run.returncode==1
    report=json.loads((output/'search.json').read_text())
    assert report['solver_status']=='inconclusive'
    assert not (output/'proof.drat.gz').exists()


def test_cli_refuses_to_overwrite_existing_artifacts(tmp_path):
    script=Path(__file__).resolve().parents[1]/'src/coprime_path_search.py'
    sentinel=tmp_path/'search.json';sentinel.write_text('original')
    run=subprocess.run([sys.executable,str(script),'3','2','--output',str(tmp_path)],capture_output=True,text=True)
    assert run.returncode!=0
    assert sentinel.read_text()=='original'


@pytest.mark.parametrize('n,k,status', [(3,3,'sat'),(2,1,'unsat')])
def test_cli_writes_recheckable_artifacts(tmp_path,n,k,status):
    script=Path(__file__).resolve().parents[1]/'src/coprime_path_search.py'
    output=tmp_path/'evidence'
    run=subprocess.run([sys.executable,str(script),str(n),str(k),'--output',str(output)],capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    report=json.loads((output/'search.json').read_text())
    assert report['solver_status']==status
    for name,checksum in report['files_sha256'].items():
        assert hashlib.sha256((output/name).read_bytes()).hexdigest()==checksum
    if status=='sat':
        witness=json.loads((output/'witness.json').read_text())
        validate_witness(PathProblem(n,k),witness['coloring'])
    else:
        formula=json.loads(gzip.decompress((output/'formula.json.gz').read_bytes()))
        validate_formula(PathProblem(n,k),formula['clauses'])
        assert '0' in gzip.decompress((output/'proof.drat.gz').read_bytes()).decode().splitlines()
