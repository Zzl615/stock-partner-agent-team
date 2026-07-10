import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.smoke_test_westock import CheckResult, main, run_check


class RunCheckTests(unittest.TestCase):
    @patch("scripts.smoke_test_westock.subprocess.run")
    def test_returns_successful_result_and_invokes_node_with_expected_options(
        self, mock_run
    ):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="quote output", stderr=""
        )

        result = run_check(
            "行情", Path("/tmp/westock-data.js"), ["quote", "sh600519"], "node"
        )

        self.assertTrue(result.ok)
        self.assertEqual("quote output", result.stdout)
        mock_run.assert_called_once_with(
            ["node", "/tmp/westock-data.js", "quote", "sh600519"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )

    @patch("scripts.smoke_test_westock.subprocess.run")
    def test_returns_failed_result_for_nonzero_exit_code(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=2, stdout="", stderr="request rejected"
        )

        result = run_check("行情", Path("/tmp/westock-data.js"), ["quote"], "node")

        self.assertFalse(result.ok)
        self.assertEqual(2, result.returncode)
        self.assertEqual("request rejected", result.stderr)

    @patch("scripts.smoke_test_westock.subprocess.run")
    def test_business_failure_marker_is_not_success_even_with_zero_exit_code(
        self, mock_run
    ):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="执行失败 [SKILL_006]: fetch failed", stderr=""
        )

        result = run_check("行情", Path("/tmp/westock-data.js"), ["quote"], "node")

        self.assertFalse(result.ok)
        self.assertEqual(0, result.returncode)

    @patch("scripts.smoke_test_westock.time.perf_counter", side_effect=[10.0, 10.25])
    @patch("scripts.smoke_test_westock.subprocess.run", side_effect=FileNotFoundError("node"))
    def test_returns_failed_result_when_node_executable_is_missing(
        self, mock_run, mock_perf_counter
    ):
        result = run_check("行情", Path("/tmp/westock-data.js"), ["quote"], "node")

        self.assertFalse(result.ok)
        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual("node", result.stderr)
        self.assertEqual(0.25, result.elapsed_seconds)

    @patch("scripts.smoke_test_westock.subprocess.run", side_effect=PermissionError("denied"))
    def test_returns_failed_result_when_node_is_not_executable(self, mock_run):
        result = run_check("行情", Path("/tmp/westock-data.js"), ["quote"], "node")

        self.assertFalse(result.ok)
        self.assertEqual(1, result.returncode)
        self.assertEqual("denied", result.stderr)


class MainTests(unittest.TestCase):
    @patch("scripts.smoke_test_westock.run_check")
    def test_returns_zero_when_all_checks_have_no_business_failure(self, mock_run_check):
        mock_run_check.side_effect = [
            CheckResult("行情", ["node", "data.js"], 0, "quote output", "", 0.1),
            CheckResult("选股", ["node", "tool.js"], 0, "strategy output", "", 0.2),
        ]

        self.assertEqual(0, main())

    @patch("scripts.smoke_test_westock.run_check")
    def test_returns_one_when_any_check_fails(self, mock_run_check):
        mock_run_check.side_effect = [
            CheckResult("行情", ["node", "data.js"], 0, "", "", 0.1),
            CheckResult("选股", ["node", "tool.js"], 1, "", "failed", 0.2),
        ]

        self.assertEqual(1, main())
        self.assertEqual(2, mock_run_check.call_count)

    @patch("scripts.smoke_test_westock.time.perf_counter", side_effect=[10.0, 10.25])
    @patch(
        "scripts.smoke_test_westock.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["node", "/tmp/westock-data.js"], 30),
    )
    def test_returns_failed_result_when_node_check_times_out(
        self, mock_run, mock_perf_counter
    ):
        result = run_check("行情", Path("/tmp/westock-data.js"), ["quote"], "node")

        self.assertFalse(result.ok)
        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual(
            "Command '['node', '/tmp/westock-data.js']' timed out after 30 seconds",
            result.stderr,
        )
        self.assertEqual(0.25, result.elapsed_seconds)
