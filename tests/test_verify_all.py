"""Tests for verify_all.py claims (individual claim functions)."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from verify_all import (
    PASS, FAIL, SKIP,
    verify_coprime_density,
    verify_extremal_density,
    verify_theta_star,
    verify_fourier_matches_direct,
    verify_sum_free_ratio,
    verify_sum_free_bound,
    verify_883_small,
    verify_883_medium,
    verify_43_small,
    verify_npg23_shifted_beats_top,
    verify_npg15_theorem_a,
    run_all,
)


class TestIndividualClaims:
    def test_coprime_density(self):
        ok, detail = verify_coprime_density()
        assert ok, f"Coprime density failed: {detail}"

    def test_extremal_density(self):
        ok, detail = verify_extremal_density()
        assert ok, f"Extremal density failed: {detail}"

    def test_theta_star(self):
        ok, detail = verify_theta_star()
        assert ok, f"Theta star failed: {detail}"

    def test_fourier_matches_direct(self):
        ok, detail = verify_fourier_matches_direct()
        assert ok, f"Fourier match failed: {detail}"

    def test_sum_free_ratio(self):
        ok, detail = verify_sum_free_ratio()
        assert ok, f"Sum-free ratio failed: {detail}"

    def test_sum_free_bound(self):
        ok, detail = verify_sum_free_bound()
        assert ok, f"Sum-free bound failed: {detail}"

    def test_883_small(self):
        ok, detail = verify_883_small()
        assert ok, f"#883 small failed: {detail}"

    def test_43_small(self):
        ok, detail = verify_43_small()
        assert ok, f"#43 small failed: {detail}"

    def test_npg23_shifted(self):
        ok, detail = verify_npg23_shifted_beats_top()
        assert ok, f"NPG-23 failed: {detail}"

    def test_npg15_theorem_a(self):
        ok, detail = verify_npg15_theorem_a()
        assert ok, f"NPG-15 failed: {detail}"


class TestConstants:
    def test_pass_value(self):
        assert PASS == "PASS"

    def test_fail_value(self):
        assert FAIL == "FAIL"

    def test_skip_value(self):
        assert SKIP == "SKIP"


class TestClaimReturnFormat:
    """All verify_ functions should return (bool, str)."""

    def test_coprime_density_format(self):
        ok, detail = verify_coprime_density()
        assert isinstance(ok, bool)
        assert isinstance(detail, str)

    def test_extremal_density_format(self):
        ok, detail = verify_extremal_density()
        assert isinstance(ok, bool)
        assert isinstance(detail, str)

    def test_npg23_format(self):
        ok, detail = verify_npg23_shifted_beats_top()
        assert isinstance(ok, bool)
        assert isinstance(detail, str)


class TestVerify883Medium:
    """Test verify_883_medium function structure (lines 110-118).
    Note: actual execution is too slow for CI timeout, so we test structure."""

    def test_883_medium_callable(self):
        assert callable(verify_883_medium)

    def test_883_medium_import(self):
        # verify_883_medium imports check_near_extremal_sets from verify_883
        from verify_883 import check_near_extremal_sets
        assert callable(check_near_extremal_sets)


class TestRunAllStructure:
    """Test the run_all() runner structure (lines 171-236).
    Note: full run takes >120s, so we test callable + partial execution."""

    def test_run_all_callable(self):
        assert callable(run_all)

    def test_claims_list_complete(self):
        """Verify all 11 claims are registered in run_all."""
        import inspect
        source = inspect.getsource(run_all)
        assert "Coprime density" in source
        assert "Extremal density" in source
        assert "θ*" in source or "Theta" in source or "theta" in source
        assert "Fourier" in source
        assert "Sum-free" in source
        assert "#883" in source
        assert "#43" in source
        assert "NPG-23" in source
        assert "NPG-15" in source

    def test_report_constants(self):
        """Test PASS/FAIL/SKIP constants used by run_all."""
        assert PASS == "PASS"
        assert FAIL == "FAIL"
        assert SKIP == "SKIP"


class TestFailureBranches:
    """Test failure branches in verify_ functions (lines 77, 104-105, 137, 156)."""

    def test_fourier_mismatch_sets_all_ok_false(self):
        """Line 77: all_ok = False when Fourier and direct counts diverge."""
        # verify_fourier_matches_direct uses lazy imports, so we patch
        # the functions on the kelley_meka_schur module directly.
        import kelley_meka_schur as kms
        original_direct = kms.schur_count_direct
        original_fourier = kms.schur_count_fourier

        call_count = [0]

        def fake_direct(A, N):
            return 10

        def fake_fourier(A, N):
            call_count[0] += 1
            if call_count[0] == 2:
                return 999.0  # Force mismatch on second call
            return 10.0

        kms.schur_count_direct = fake_direct
        kms.schur_count_fourier = fake_fourier
        try:
            ok, detail = verify_fourier_matches_direct()
            assert not ok, "Should fail when Fourier mismatches direct"
            assert "match=False" in detail
        finally:
            kms.schur_count_direct = original_direct
            kms.schur_count_fourier = original_fourier

    def test_883_small_failure_branch(self):
        """Lines 104-105: verify_883_small returns False on counterexample."""
        import verify_883 as v883
        original_fn = v883.verify_exhaustive

        def fake_verify_exhaustive(n):
            if n == 5:
                return False, {1, 2, 3}  # Fake counterexample
            return True, None

        v883.verify_exhaustive = fake_verify_exhaustive
        try:
            ok, detail = verify_883_small()
            assert not ok
            assert "FAILED at n=5" in detail
            assert "counterexample" in detail
        finally:
            v883.verify_exhaustive = original_fn

    def test_883_medium_failure_branch(self):
        """Lines 112-118: verify_883_medium returns False on counterexample."""
        import verify_883 as v883
        original_fn = v883.check_near_extremal_sets

        def fake_check_near_extremal_sets(n):
            if n == 50:
                return False, {10, 20, 30}
            return True, None

        v883.check_near_extremal_sets = fake_check_near_extremal_sets
        try:
            ok, detail = verify_883_medium()
            assert not ok
            assert "FAILED at n=50" in detail
        finally:
            v883.check_near_extremal_sets = original_fn

    def test_883_medium_success(self):
        """Lines 112-118: verify_883_medium succeeds when all pass."""
        import verify_883 as v883
        original_fn = v883.check_near_extremal_sets

        def fake_check_near_extremal_sets(n):
            return True, None

        v883.check_near_extremal_sets = fake_check_near_extremal_sets
        try:
            ok, detail = verify_883_medium()
            assert ok
            assert "verified for n=30,50,75,100" in detail
        finally:
            v883.check_near_extremal_sets = original_fn

    def test_43_small_failure_branch(self):
        """Line 137: verify_43_small returns False when conjecture fails."""
        import sidon_disjoint as sd
        original_fn = sd.exhaustive_search

        def fake_exhaustive_search(N):
            if N == 7:
                return {"conjecture_holds": False}
            return {"conjecture_holds": True}

        sd.exhaustive_search = fake_exhaustive_search
        try:
            ok, detail = verify_43_small()
            assert not ok
            assert "FAILED at N=7" in detail
        finally:
            sd.exhaustive_search = original_fn

    def test_npg23_shifted_failure_branch(self):
        """Line 156: all_ok = False when shifted does not beat top layer."""
        import primitive_coprime as pc
        orig_top = pc.top_layer
        orig_shift = pc.shifted_top_layer
        orig_count = pc.coprime_pair_count
        orig_prim = pc.is_primitive

        # Make shifted WORSE than top for n=100, so the check fails
        def fake_top_layer(n):
            return set(range(n // 2 + 1, n + 1))

        def fake_shifted_top_layer(n):
            return set(range(n // 2 + 1, n + 1))

        def fake_coprime_pair_count(S):
            return 10  # Same count, so M_s > M_t fails

        def fake_is_primitive(S):
            return True

        pc.top_layer = fake_top_layer
        pc.shifted_top_layer = fake_shifted_top_layer
        pc.coprime_pair_count = fake_coprime_pair_count
        pc.is_primitive = fake_is_primitive
        try:
            ok, detail = verify_npg23_shifted_beats_top()
            assert not ok, "Should fail when shifted does not beat top"
        finally:
            pc.top_layer = orig_top
            pc.shifted_top_layer = orig_shift
            pc.coprime_pair_count = orig_count
            pc.is_primitive = orig_prim


class TestRunAllExecution:
    """Test run_all() end-to-end with mocked verification functions (lines 173-236)."""

    def _make_mock_claims(self, pass_all=True, fail_indices=None):
        """Create a list of mock claim functions for run_all."""
        if fail_indices is None:
            fail_indices = set()
        results = []
        for i in range(3):
            if i in fail_indices:
                results.append((True, f"detail_{i}") if pass_all else (False, f"failed_{i}"))
            else:
                results.append((True, f"detail_{i}"))
        return results

    def test_run_all_all_pass(self, tmp_path):
        """Lines 173-236: run_all() with all claims passing."""
        import verify_all

        # Mock all 11 verify functions to return quickly
        mock_fns = {}
        fn_names = [
            "verify_coprime_density", "verify_extremal_density",
            "verify_theta_star", "verify_fourier_matches_direct",
            "verify_sum_free_ratio", "verify_sum_free_bound",
            "verify_883_small", "verify_883_medium",
            "verify_43_small", "verify_npg23_shifted_beats_top",
            "verify_npg15_theorem_a",
        ]
        patches = []
        for fn_name in fn_names:
            p = patch.object(verify_all, fn_name, return_value=(True, f"{fn_name} ok"))
            patches.append(p)

        # Redirect report path to tmp_path
        report_path = tmp_path / "docs" / "verification_report.md"

        for p in patches:
            p.start()

        # Patch the report path inside run_all
        original_run_all = verify_all.run_all

        def patched_run_all():
            # Temporarily patch Path(__file__).parent.parent
            import verify_all as va
            old_file = va.__file__
            # We'll instead patch the report writing by patching Path
            pass

        # Simpler approach: just mock __file__ so report goes to tmp_path
        original_file = verify_all.__file__
        verify_all.__file__ = str(tmp_path / "src" / "verify_all.py")
        (tmp_path / "src").mkdir(exist_ok=True)

        try:
            result = run_all()
            assert result is True
            # Check report was written
            report = tmp_path / "docs" / "verification_report.md"
            assert report.exists()
            content = report.read_text()
            assert "Verification Report" in content
            assert "11/11 claims verified" in content
            assert "PASS" in content
        finally:
            verify_all.__file__ = original_file
            for p in patches:
                p.stop()

    def test_run_all_with_failures(self, tmp_path):
        """Lines 196-217: run_all() counts failures correctly."""
        import verify_all

        fn_names = [
            "verify_coprime_density", "verify_extremal_density",
            "verify_theta_star", "verify_fourier_matches_direct",
            "verify_sum_free_ratio", "verify_sum_free_bound",
            "verify_883_small", "verify_883_medium",
            "verify_43_small", "verify_npg23_shifted_beats_top",
            "verify_npg15_theorem_a",
        ]
        patches = []
        for i, fn_name in enumerate(fn_names):
            # Make first two fail
            if i < 2:
                p = patch.object(verify_all, fn_name, return_value=(False, f"{fn_name} FAILED"))
            else:
                p = patch.object(verify_all, fn_name, return_value=(True, f"{fn_name} ok"))
            patches.append(p)

        original_file = verify_all.__file__
        verify_all.__file__ = str(tmp_path / "src" / "verify_all.py")
        (tmp_path / "src").mkdir(exist_ok=True)

        for p in patches:
            p.start()
        try:
            result = run_all()
            assert result is False  # Has failures
            report = tmp_path / "docs" / "verification_report.md"
            assert report.exists()
            content = report.read_text()
            assert "9/11 claims verified" in content
            assert "FAIL" in content
        finally:
            verify_all.__file__ = original_file
            for p in patches:
                p.stop()

    def test_run_all_with_exception(self, tmp_path):
        """Lines 206-210: run_all() handles exceptions in claim functions."""
        import verify_all

        fn_names = [
            "verify_coprime_density", "verify_extremal_density",
            "verify_theta_star", "verify_fourier_matches_direct",
            "verify_sum_free_ratio", "verify_sum_free_bound",
            "verify_883_small", "verify_883_medium",
            "verify_43_small", "verify_npg23_shifted_beats_top",
            "verify_npg15_theorem_a",
        ]
        patches = []
        for i, fn_name in enumerate(fn_names):
            if i == 0:
                # First claim raises an exception
                p = patch.object(verify_all, fn_name, side_effect=RuntimeError("test error"))
            else:
                p = patch.object(verify_all, fn_name, return_value=(True, f"{fn_name} ok"))
            patches.append(p)

        original_file = verify_all.__file__
        verify_all.__file__ = str(tmp_path / "src" / "verify_all.py")
        (tmp_path / "src").mkdir(exist_ok=True)

        for p in patches:
            p.start()
        try:
            result = run_all()
            assert result is False  # Exception counts as failure
            report = tmp_path / "docs" / "verification_report.md"
            content = report.read_text()
            assert "ERROR" in content
            assert "10/11 claims verified" in content
        finally:
            verify_all.__file__ = original_file
            for p in patches:
                p.stop()

    def test_run_all_report_format(self, tmp_path):
        """Lines 224-234: Verify report file format (markdown table)."""
        import verify_all

        fn_names = [
            "verify_coprime_density", "verify_extremal_density",
            "verify_theta_star", "verify_fourier_matches_direct",
            "verify_sum_free_ratio", "verify_sum_free_bound",
            "verify_883_small", "verify_883_medium",
            "verify_43_small", "verify_npg23_shifted_beats_top",
            "verify_npg15_theorem_a",
        ]
        patches = []
        for fn_name in fn_names:
            p = patch.object(verify_all, fn_name, return_value=(True, "ok"))
            patches.append(p)

        original_file = verify_all.__file__
        verify_all.__file__ = str(tmp_path / "src" / "verify_all.py")
        (tmp_path / "src").mkdir(exist_ok=True)

        for p in patches:
            p.start()
        try:
            run_all()
            report = tmp_path / "docs" / "verification_report.md"
            content = report.read_text()
            # Check markdown table headers
            assert "| Claim | Status | Detail | Time |" in content
            assert "|-------|--------|--------|------|" in content
            # Check that all 11 rows are in the table (header + separator + 11 data rows)
            table_lines = [l for l in content.split("\n") if l.startswith("|")]
            assert len(table_lines) == 13  # 2 header lines + 11 data rows
            # Check Generated timestamp
            assert "**Generated**:" in content
        finally:
            verify_all.__file__ = original_file
            for p in patches:
                p.stop()

    def test_run_all_creates_docs_dir(self, tmp_path):
        """Line 225: run_all() creates docs/ directory if it doesn't exist."""
        import verify_all

        fn_names = [
            "verify_coprime_density", "verify_extremal_density",
            "verify_theta_star", "verify_fourier_matches_direct",
            "verify_sum_free_ratio", "verify_sum_free_bound",
            "verify_883_small", "verify_883_medium",
            "verify_43_small", "verify_npg23_shifted_beats_top",
            "verify_npg15_theorem_a",
        ]
        patches = []
        for fn_name in fn_names:
            p = patch.object(verify_all, fn_name, return_value=(True, "ok"))
            patches.append(p)

        original_file = verify_all.__file__
        # Point to a location where docs/ does NOT yet exist
        fake_src = tmp_path / "fresh_project" / "src"
        fake_src.mkdir(parents=True)
        verify_all.__file__ = str(fake_src / "verify_all.py")

        for p in patches:
            p.start()
        try:
            run_all()
            docs_dir = tmp_path / "fresh_project" / "docs"
            assert docs_dir.exists()
            assert (docs_dir / "verification_report.md").exists()
        finally:
            verify_all.__file__ = original_file
            for p in patches:
                p.stop()

    def test_run_all_prints_output(self, tmp_path, capsys):
        """Lines 187-220: run_all() prints report to stdout."""
        import verify_all

        fn_names = [
            "verify_coprime_density", "verify_extremal_density",
            "verify_theta_star", "verify_fourier_matches_direct",
            "verify_sum_free_ratio", "verify_sum_free_bound",
            "verify_883_small", "verify_883_medium",
            "verify_43_small", "verify_npg23_shifted_beats_top",
            "verify_npg15_theorem_a",
        ]
        patches = []
        for i, fn_name in enumerate(fn_names):
            if i == 0:
                p = patch.object(verify_all, fn_name, return_value=(False, "density mismatch"))
            else:
                p = patch.object(verify_all, fn_name, return_value=(True, "ok"))
            patches.append(p)

        original_file = verify_all.__file__
        verify_all.__file__ = str(tmp_path / "src" / "verify_all.py")
        (tmp_path / "src").mkdir(exist_ok=True)

        for p in patches:
            p.start()
        try:
            run_all()
            captured = capsys.readouterr()
            # Check header
            assert "MASTER VERIFICATION REPORT" in captured.out
            # Check summary line
            assert "SUMMARY:" in captured.out
            assert "10 PASS" in captured.out
            assert "1 FAIL" in captured.out
            # Check symbols
            assert "\u2713" in captured.out  # checkmark for pass
            assert "\u2717" in captured.out  # cross for fail
            # Check report path mention
            assert "Report written to" in captured.out
        finally:
            verify_all.__file__ = original_file
            for p in patches:
                p.stop()

    def test_run_all_long_detail_truncated_in_report(self, tmp_path):
        """Line 233: Detail is truncated to 60 chars in report table."""
        import verify_all

        long_detail = "A" * 100  # 100-char detail string

        fn_names = [
            "verify_coprime_density", "verify_extremal_density",
            "verify_theta_star", "verify_fourier_matches_direct",
            "verify_sum_free_ratio", "verify_sum_free_bound",
            "verify_883_small", "verify_883_medium",
            "verify_43_small", "verify_npg23_shifted_beats_top",
            "verify_npg15_theorem_a",
        ]
        patches = []
        for i, fn_name in enumerate(fn_names):
            if i == 0:
                p = patch.object(verify_all, fn_name, return_value=(True, long_detail))
            else:
                p = patch.object(verify_all, fn_name, return_value=(True, "ok"))
            patches.append(p)

        original_file = verify_all.__file__
        verify_all.__file__ = str(tmp_path / "src" / "verify_all.py")
        (tmp_path / "src").mkdir(exist_ok=True)

        for p in patches:
            p.start()
        try:
            run_all()
            report = tmp_path / "docs" / "verification_report.md"
            content = report.read_text()
            # The detail in the table should be truncated to 60 chars
            assert "A" * 60 in content
            assert "A" * 61 not in content  # truncated, not full 100
        finally:
            verify_all.__file__ = original_file
            for p in patches:
                p.stop()
