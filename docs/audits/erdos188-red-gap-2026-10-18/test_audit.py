"""Behavioral and adversarial tests for the scoped red-pair certificate."""

import copy
import json
from fractions import Fraction as F
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import audit


def fixture(centres=None):
    return {
        "P1": ["10", "0"], "P2": ["0", "10"], "k": 24,
        "centres": centres or [["0", "0"], ["3", "0"]],
        "h": ["1/10", "1/10"],
    }


class ExactGeometryTests(unittest.TestCase):
    def test_small_safe_periodic_disks(self):
        # Catches omitted pairs, or classifying separated disks as near.
        result = audit.certify(audit.parse_config(fixture()))
        self.assertEqual(result["ordered_pairs"], 34)
        self.assertEqual(result["near_pairs"], 0)
        self.assertEqual(result["far_pairs"], 34)

    def test_overlapping_disks_are_allowed(self):
        result = audit.certify(audit.parse_config(fixture([["0", "0"], ["1/10", "0"]])))
        self.assertEqual(result["near_pairs"], 2)

    def test_unit_pair_across_period_boundary_rejected(self):
        with self.assertRaises(audit.AuditError):
            audit.certify(audit.parse_config(fixture([["0", "0"], ["9", "0"]])))

    def test_unit_pair_inside_period_rejected(self):
        with self.assertRaises(audit.AuditError):
            audit.certify(audit.parse_config(fixture([["0", "0"], ["1", "0"]])))

    def test_closed_distance_interval_endpoints_rejected(self):
        for q in (F(4, 25), F(289, 100)):
            # radius sum .1, excluded interval [.5,1.6]: d=.4 or d=1.7.
            with self.subTest(q=q), self.assertRaises(audit.AuditError):
                audit.classify(q, F(1, 10), F(1, 2), F(8, 5))

    def test_near_squared_inequality_requires_positive_room(self):
        with self.assertRaises(audit.AuditError):
            audit.classify(F(0), F(2), F(1), F(1))

    def test_same_cell_diameter_rejected(self):
        d = fixture(); d["h"][0] = "1/2"
        with self.assertRaises(audit.AuditError):
            audit.certify(audit.parse_config(d))

    def test_short_period_rejected_by_completeness_guard(self):
        d = fixture(); d["P1"] = ["1", "0"]
        with self.assertRaisesRegex(audit.AuditError, "window"):
            audit.certify(audit.parse_config(d))

    def test_long_but_nearly_parallel_periods_rejected(self):
        d = fixture(); d["P2"] = ["10", "1/10"]
        with self.assertRaisesRegex(audit.AuditError, "window"):
            audit.certify(audit.parse_config(d))

    def test_exact_recentering_handles_negative_and_integer_coordinates(self):
        d = fixture([["-20", "10"], ["-7", "-30"]])
        result = audit.certify(audit.parse_config(d))
        self.assertEqual(result["near_pairs"], 0)
        self.assertEqual(result["far_pairs"], 34)
        self.assertEqual(result["normalized_centres"], [["0", "0"], ["3", "0"]])

    def test_basis_orientation_does_not_change_conclusion(self):
        d = fixture(); d["P1"], d["P2"] = d["P2"], d["P1"]
        result = audit.certify(audit.parse_config(d))
        self.assertEqual(result["far_pairs"], 34)

    def test_algebraic_radius_bound_and_invalid_bound_control(self):
        self.assertEqual(audit.radius_factor(), F(100863, 100000))
        with self.assertRaises(audit.AuditError):
            audit.radius_factor(F(100862, 100000))

    def test_squared_classifier_agrees_with_direct_rational_distances(self):
        # Direct d comparisons independently exercise the sign guard and both
        # strict endpoints; no numerical square root or production helper oracle.
        for di in range(31):
            for si in range(13):
                for gap in (F(0), F(1, 1000)):
                    d, s = F(di, 10), F(si, 10)
                    lower, upper = 1 - gap, 1 + gap
                    if d + s < lower:
                        self.assertEqual(audit.classify(d*d, s, lower, upper)[0], audit.PairKind.NEAR)
                    elif d - s > upper:
                        self.assertEqual(audit.classify(d*d, s, lower, upper)[0], audit.PairKind.FAR)
                    else:
                        with self.assertRaises(audit.AuditError):
                            audit.classify(d*d, s, lower, upper)


class InputTests(unittest.TestCase):
    def test_malformed_configurations_rejected(self):
        base = fixture()
        variants = []
        for key, value in [
            ("k", 12), ("k", 24.0), ("h", ["1/10"]),
            ("h", ["-1/10", "1/10"]), ("h", ["0", "1/10"]),
            ("h", [0.1, "1/10"]), ("P1", ["0", "0"]),
            ("h", ["1/0", "1/10"]), ("h", ["NaN", "1/10"]),
            ("P1", ["10"]), ("centres", []),
            ("centres", [["0", "0", "0"], ["1", "1"]]),
        ]:
            d = copy.deepcopy(base); d[key] = value; variants.append(d)
        d = copy.deepcopy(base); del d["P1"]; variants.append(d)
        d = copy.deepcopy(base); d["unexpected"] = 1; variants.append(d)
        for d in variants:
            with self.subTest(d=d), self.assertRaises(audit.AuditError):
                audit.parse_config(d)

    def test_invalid_gap_rejected(self):
        cfg = audit.parse_config(fixture())
        for gap in (F(-1, 10), F(1), F(2)):
            with self.subTest(gap=gap), self.assertRaises(audit.AuditError):
                audit.certify(cfg, gap)


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = Path(__file__).with_name("cfg_k60.json").read_bytes()
        cls.data = json.loads(cls.raw)

    def test_complete_source_certificate(self):
        result = audit.certify(audit.parse_config(self.data))
        self.assertEqual(result["cells"], 90)
        self.assertEqual(result["ordered_pairs"], 72810)
        self.assertEqual(result["near_pairs"], 408)
        self.assertEqual(result["far_pairs"], 72402)
        self.assertEqual(result["excluded_distance_interval"], ["999/1000", "1001/1000"])

    def test_actual_data_unit_pair_mutation_rejected(self):
        d = copy.deepcopy(self.data)
        x, y = map(F, d["centres"][0])
        d["centres"][1] = [str(x + 1), str(y)]
        # These two centers themselves are red, exactly one unit apart.
        with self.assertRaises(audit.AuditError):
            audit.certify(audit.parse_config(d))

    def test_source_digest_guard_rejects_changed_bytes(self):
        audit.check_source_digest(self.raw)
        with self.assertRaises(audit.AuditError):
            audit.check_source_digest(self.raw + b" ")

    def test_separate_large_lattice_shifts_preserve_the_source_certificate(self):
        # Same infinite coloring, different representatives including negatives.
        d = copy.deepcopy(self.data)
        p, q = [tuple(map(F, d[key])) for key in ("P1", "P2")]
        for i, centre in enumerate(d["centres"]):
            x, y = map(F, centre)
            a, b = 31 * i - 1500, 71 - 7 * i
            d["centres"][i] = [str(x+a*p[0]+b*q[0]), str(y+a*p[1]+b*q[1])]
        original = audit.certify(audit.parse_config(self.data))
        shifted = audit.certify(audit.parse_config(d))
        self.assertEqual(shifted, original)

    def test_cli_rejects_corrupt_input_and_works_with_optimization(self):
        script = str(Path(__file__).with_name("audit.py"))
        good = subprocess.run([sys.executable, "-I", "-S", "-O", script],
                              text=True, capture_output=True, check=False)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)["ordered_pairs"], 72810)
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "bad.json"
            bad.write_bytes(self.raw + b" ")
            result = subprocess.run([sys.executable, "-I", "-S", "-O", script, str(bad)],
                                    text=True, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NOT ESTABLISHED", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
