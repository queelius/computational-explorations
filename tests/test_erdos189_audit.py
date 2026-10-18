"""Run the portable certificate audit's fast controls in isolation.

The full certificate replay is the documented reproduce.py command; this
routine suite does not require the 48.7 MB external archive or network access.
"""
from pathlib import Path
import subprocess
import sys


def test_rectangle_certificate_controls() -> None:
    packet = (Path(__file__).resolve().parents[1] / 'docs' / 'audits'
              / 'erdos189-rectangles-2026-10-18')
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(packet), '-v'],
                   check=True, timeout=30)
