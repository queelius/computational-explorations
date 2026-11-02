"""Failure controls for the independent rectangle and hinted-RUP audit."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from audit import (
    AuditError, Formula, check_encoding, diagonal_rectangles,
    parse_dimacs, read_points, verify_lrat,
)


class GeometryTests(unittest.TestCase):
    def setUp(self):
        # Perpendicular sides (2,0), (-4,8) have lattice determinant 16.
        self.points = {1: (0, 0), 2: (2, 0), 3: (-4, 8), 4: (-2, 8)}
        self.cnf = Formula(4, ((1,), (1, 2, 3, 4), (-1, -2, -3, -4)))

    def test_unit_area_rectangle(self):
        self.assertEqual(diagonal_rectangles(self.points), {(1, 2, 3, 4)})
        self.assertEqual(check_encoding(self.points, self.cnf), 1)

    def test_area_preserving_shear_is_not_rectangle(self):
        sheared = {i: (x + y, y) for i, (x, y) in self.points.items()}
        self.assertEqual(diagonal_rectangles(sheared), set())
        with self.assertRaises(AuditError):
            check_encoding(sheared, self.cnf)

    def test_same_area_rhombus_is_not_rectangle(self):
        rhombus = {1: (0, 0), 2: (4, 0), 3: (0, 4), 4: (4, 4)}
        self.assertEqual(diagonal_rectangles(rhombus), set())

    def test_rectangle_with_wrong_area(self):
        scaled = {i: (2*x, 2*y) for i, (x, y) in self.points.items()}
        self.assertEqual(diagonal_rectangles(scaled), set())

    def test_translation_and_central_reflection(self):
        moved = {i: (19-x, -37-y) for i, (x, y) in self.points.items()}
        self.assertEqual(diagonal_rectangles(moved), {(1, 2, 3, 4)})

    def test_missing_or_extra_clause_rejected(self):
        for clauses in (self.cnf.clauses[:-1], self.cnf.clauses + ((2,),)):
            with self.assertRaises(AuditError):
                check_encoding(self.points, Formula(4, clauses))

    def test_clause_order_is_irrelevant(self):
        reordered = Formula(4, ((-4, -2, -1, -3), (3, 4, 1, 2), (1,)))
        self.assertEqual(check_encoding(self.points, reordered), 1)

    def test_point_parser_rejects_duplicates_and_gaps(self):
        for text in ('1 0 0\n1 1 0\n', '1 0 0\n3 1 0\n',
                     '1 0 0\n2 0 0\n', '1 0 0 4\n', ''):
            with self.assertRaises(AuditError):
                read_points(io.StringIO(text))

    def test_point_comments_and_variable_count(self):
        self.assertEqual(read_points(io.StringIO('# coordinates\n\n1 0 0\n')), {1: (0, 0)})
        with self.assertRaises(AuditError):
            check_encoding(self.points, Formula(5, self.cnf.clauses))


class DimacsTests(unittest.TestCase):
    def test_multiline_and_multiclause(self):
        formula = parse_dimacs(io.StringIO('c comment\np cnf 2 2\n1\n-2 0 2 0\n'))
        self.assertEqual(formula, Formula(2, ((1, -2), (2,))))

    def test_malformed_input(self):
        for text in ('p cnf 1 1\n1', 'p cnf 1 1\n2 0', 'p cnf 1 2\n1 0',
                     '1 0', 'p cnf 1 1\np cnf 1 1\n1 0',
                     'p cnf 1 1\n1 1 0', 'p cnf 1 1\n1 -1 0',
                     'p cnf 0 1\n0', 'p cnf 1 -1\n', 'p cnf x 1\n1 0'):
            with self.subTest(text=text), self.assertRaises(AuditError):
                parse_dimacs(io.StringIO(text))


class LratTests(unittest.TestCase):
    def setUp(self):
        self.formula = Formula(2, ((1, 2), (-1, 2), (1, -2), (-1, -2)))
        self.proof = '5 2 0 1 2 0\n5 d 1 2 0\n6 0 5 3 4 0\n'

    def test_complete_refutation_with_deletion(self):
        stats = verify_lrat(self.formula, io.StringIO(self.proof))
        self.assertEqual(stats['additions'], 2)
        self.assertEqual(stats['deletion_records'], 1)
        self.assertEqual(stats['deleted_clauses'], 2)

    def test_satisfiable_formula_has_no_empty_derivation(self):
        with self.assertRaises(AuditError):
            verify_lrat(Formula(1, ((1,),)), io.StringIO('2 0 1 0\n'))

    def test_false_unit_derivation(self):
        with self.assertRaises(AuditError):
            verify_lrat(Formula(2, ((1, 2),)), io.StringIO('2 1 0 1 0\n'))

    def test_bad_proofs(self):
        for proof in (
            self.proof.replace('1 2 0', '1 99 0', 1),  # unknown clause
            self.proof.replace('6 0 5 3 4 0', '6 0 5 1 4 0'),  # deleted clause
            self.proof.replace('5 2 0', '5 3 0'),  # variable out of range
            self.proof.replace('5 2 0', '3 2 0'),  # reused initial ID
            self.proof.replace('1 2 0', '-1 2 0', 1),  # unsupported RAT
            self.proof.replace('6 0 5 3 4 0', '6 0 3 4 0'),  # non-unit hint
            self.proof.replace('6 0 5 3 4 0', '6 0 5 3 4 1 0'),  # ignored tail
            self.proof.splitlines()[0] + '\n',  # truncated, no empty clause
            self.proof + '7 1 0 6 0\n',  # material after empty clause
            '5 0 0\n',  # no contradiction established
            '5 2 0 1 2\n',  # missing terminator
        ):
            with self.subTest(proof=proof), self.assertRaises(AuditError):
                verify_lrat(self.formula, io.StringIO(proof))

    def test_deletion_and_record_boundaries(self):
        for proof in ('0 d 1 0\n', '5\n', '5 d 1\n', '5 d 0 1 0\n',
                      '5 d 99 0\n', '5 d 1 1 0\n',
                      '5 2 2 0 1 2 0\n', '5 2 -2 0 1 2 0\n'):
            with self.subTest(proof=proof), self.assertRaises(AuditError):
                verify_lrat(self.formula, io.StringIO(proof))

    def test_satisfied_hint_is_rejected(self):
        with self.assertRaises(AuditError):
            verify_lrat(Formula(1, ((1,), (-1,))), io.StringIO('3 1 0 2 1 0\n'))

    def test_original_empty_clause_and_trailing_blank_lines(self):
        stats = verify_lrat(Formula(1, ((),)), io.StringIO('\n2 0 1 0\n\n'))
        self.assertEqual(stats['additions'], 1)


class ProvenanceTests(unittest.TestCase):
    def test_source_receipt_matches_fetcher(self):
        from reproduce import ARCHIVE_SHA256, ARCHIVE_URL
        source = json.loads(Path(__file__).with_name('source.json').read_text())
        self.assertEqual(source['archive']['sha256'], ARCHIVE_SHA256)
        self.assertEqual(source['archive']['url'], ARCHIVE_URL)

    def test_changed_archive_rejected_before_extraction(self):
        from reproduce import extract_pinned
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            archive = directory/'wrong.zip'
            corrupt = b'not the pinned archive'
            archive.write_bytes(corrupt)
            with self.assertRaises(AuditError) as caught:
                extract_pinned(archive, directory)
            self.assertIn(f'{len(corrupt)} bytes', str(caught.exception))
            self.assertIn('expected', str(caught.exception))
            self.assertIn('got', str(caught.exception))
            self.assertEqual(list(directory.iterdir()), [archive])

    def test_cli_missing_certificate_is_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).with_name('audit.py')), temp],
                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn('AUDIT FAIL:', result.stderr)


if __name__ == '__main__':
    unittest.main()
