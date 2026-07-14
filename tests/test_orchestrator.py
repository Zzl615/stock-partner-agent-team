import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import orchestrator


class OrchestratorTests(unittest.TestCase):
    def test_render_html_report_returns_none_when_renderer_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "orchestrator.subprocess.run",
                return_value=subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="render failed"),
            ):
                result = orchestrator.render_html_report(
                    body_html="<section></section>",
                    html_fpath=os.path.join(tmpdir, "report.html"),
                    title="测试报告",
                    date_str="2026-07-09",
                )

        self.assertIsNone(result)

    def test_run_team_roundtable_does_not_report_failed_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("orchestrator.run_sub_agent", return_value=("valuation-analyst", "sub report")),
                patch("orchestrator.run_roundtable_lead", return_value=("lead report", "<section></section>")),
                patch("orchestrator.render_html_report", return_value=None),
            ):
                result = orchestrator.run_team_roundtable(
                    user_query="分析中远海能 600026",
                    active_agents=["valuation-analyst"],
                    output_dir=tmpdir,
                )

        self.assertIsNone(result["html_report"])


if __name__ == "__main__":
    unittest.main()
