"""Shared fixtures for Erdős problems test suite."""
import sys
from pathlib import Path

import pytest

# Add src/ to path so we can import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def small_primes():
    """First 10 primes."""
    return {2, 3, 5, 7, 11, 13, 17, 19, 23, 29}


@pytest.fixture
def extremal_set_30():
    """Extremal set A* for n=30: multiples of 2 or 3."""
    return {i for i in range(1, 31) if i % 2 == 0 or i % 3 == 0}


@pytest.fixture
def problems_yaml_path():
    """Path to the problems YAML data file."""
    return Path(__file__).parent.parent / "data" / "erdosproblems" / "data" / "problems.yaml"
