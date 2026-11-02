"""Run the independent red-distance audit in its own import namespace."""

from pathlib import Path
import subprocess
import sys


def test_periodic_red_distance_audit():
    packet = Path(__file__).resolve().parents[1] / "docs/audits/erdos188-red-gap-2026-10-18"
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-m", "unittest", "discover",
         "-s", str(packet), "-p", "test_audit.py", "-v"],
        capture_output=True, text=True, timeout=90, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
