"""Independently verify saved coprime edge colorings using only the standard library.

This checks lower-bound witnesses, not upper bounds or solver certificates.
All coprime edges and forbidden cliques are recomputed from the record's
parameters; previously saved ``valid`` flags and counts are never trusted.
"""

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from itertools import combinations
import json
from math import gcd
from pathlib import Path


@dataclass(frozen=True)
class Witness:
    n: int
    forbidden_clique_size: int
    colors: int
    coloring: tuple[tuple[int, int, int], ...]

    def __post_init__(self) -> None:
        for name, minimum in (("n", 1), ("forbidden_clique_size", 2), ("colors", 1)):
            value = getattr(self, name)
            if type(value) is not int or value < minimum:
                raise ValueError(f"{name} must be an integer at least {minimum}")
        if not isinstance(self.coloring, tuple):
            raise ValueError("coloring must be an immutable tuple of edge rows")
        for index, row in enumerate(self.coloring):
            if (not isinstance(row, tuple) or len(row) != 3
                    or any(type(value) is not int for value in row)):
                raise ValueError(f"coloring row {index} must contain three integers")

    @classmethod
    def from_record(cls, record: object) -> "Witness":
        """Decode the archived JSON format without coercing numeric values."""
        if not isinstance(record, Mapping):
            raise ValueError("Witness must be a JSON object")
        rows = record.get("coloring")
        if not isinstance(rows, list):
            raise ValueError("coloring must be a list of [a, b, color] rows")
        coloring = []
        for index, row in enumerate(rows):
            if not isinstance(row, list):
                raise ValueError(f"coloring row {index} must be a list")
            coloring.append(tuple(row))
        return cls(
            n=record.get("n"), forbidden_clique_size=record.get("forbidden_clique_size"),
            colors=record.get("colors"), coloring=tuple(coloring),
        )


@dataclass(frozen=True)
class VerificationResult:
    n: int
    forbidden_clique_size: int
    colors: int
    edges: int
    cliques_checked: int


def verify_witness(witness: Witness) -> VerificationResult:
    """Reject any malformed coloring or monochromatic forbidden clique.

    The exhaustive enumeration is intended for small archived witnesses;
    its cost grows with the number of vertex subsets of the requested size.
    """
    vertices = range(1, witness.n + 1)
    expected_edges = {edge for edge in combinations(vertices, 2) if gcd(*edge) == 1}
    edge_colors = {}
    for a, b, color in witness.coloring:
        edge = (a, b)
        if edge not in expected_edges:
            raise ValueError(f"Unexpected or noncanonical coprime edge {edge}")
        if edge in edge_colors:
            raise ValueError(f"Duplicate edge {edge}")
        if not 0 <= color < witness.colors:
            raise ValueError(f"Color {color} for edge {edge} is outside the palette")
        edge_colors[edge] = color
    missing = expected_edges - edge_colors.keys()
    if missing:
        raise ValueError(f"Missing {len(missing)} coprime edges")

    checked = 0
    for clique in combinations(vertices, witness.forbidden_clique_size):
        edges = tuple(combinations(clique, 2))
        if all(edge in expected_edges for edge in edges):
            checked += 1
            if len({edge_colors[edge] for edge in edges}) == 1:
                raise ValueError(f"Monochromatic forbidden clique {clique}")
    return VerificationResult(
        witness.n, witness.forbidden_clique_size, witness.colors,
        len(expected_edges), checked,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("witnesses", type=Path, nargs="+", help="saved witness JSON files")
    args = parser.parse_args(argv)
    results = []
    for path in args.witnesses:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            verified = verify_witness(Witness.from_record(record))
        except (OSError, ValueError) as error:
            results.append({"path": str(path), "valid": False, "error": str(error)})
        else:
            results.append({"path": str(path), "valid": True, **asdict(verified)})
    valid = all(result["valid"] for result in results)
    print(json.dumps({"valid": valid, "results": results}, indent=2))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
