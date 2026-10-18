"""Routine and integration checks for the external Claim B audit packet."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

PACKET_PARENT = Path(__file__).resolve().parents[1] / 'docs' / 'audits' / 'erdos188-blue-progression-2026-10-18'
sys.path.insert(0, str(PACKET_PARENT))
from erdos188_blue_progression.test_audit import AuditTests
from erdos188_blue_progression import reviewer_checks


def test_separate_arithmetic_oracles():
    assert reviewer_checks.trig_controls() == 138
    assert reviewer_checks.pi_control()['production_enclosure_confirmed']
    assert reviewer_checks.corner_controls() == {'cases': 108, 'accepted': 63, 'rejected': 45}
    assert len(reviewer_checks.failure_controls()) == 24


def require_generator_dependencies():
    pytest.importorskip('numpy')
    pytest.importorskip('numba')


def test_real_witness_rejections(capsys):
    require_generator_dependencies()
    from erdos188_blue_progression import real_controls
    real_controls.main()
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'PASS'
    assert result['reject_count'] == 44
    assert result['receipt_intervals'] == 40198


def test_driver_pilot_cannot_claim_full_cover(tmp_path):
    require_generator_dependencies()
    import os
    env = os.environ.copy()
    env['PYTHONPATH'] = str(PACKET_PARENT)
    completed = subprocess.run([sys.executable, '-m', 'erdos188_blue_progression.run', '--pilot', '4', '--workers', '1', '--output', str(tmp_path)], env=env, capture_output=True, text=True, timeout=90)
    assert completed.returncode == 0, completed.stderr
    result = json.loads((tmp_path/'result.json').read_text())
    assert result['status'] == 'PILOT_ONLY'
    assert result['direction_tiling_checked'] is False
    assert result['initial_intervals'] == 4
