import unittest
from unittest.mock import patch

import tools


class ToolsTests(unittest.TestCase):
    def test_normalizes_a_share_fund_command_to_asfund(self):
        self.assertEqual(tools.normalize_westock_data_command("fund sh600026 --days 7"), "asfund sh600026 --days 7")
        self.assertEqual(tools.normalize_westock_data_command("fund 600026"), "asfund sh600026")
        self.assertEqual(tools.normalize_westock_data_command("fund 300750"), "asfund sz300750")

    def test_normalizes_loose_kline_arguments(self):
        self.assertEqual(
            tools.normalize_westock_data_command("kline sh600150 day 1200 qfq"),
            "kline sh600150 --period day --limit 1200 --fq qfq",
        )

    def test_query_westock_data_logs_normalized_command(self):
        with patch("tools.execute_node_script", return_value="ok") as execute:
            result = tools.query_westock_data("fund 600026")

        self.assertEqual(result, "ok")
        execute.assert_called_once_with(tools.config.WESTOCK_DATA_SCRIPT, "asfund sh600026", tool_name="westock-data")


if __name__ == "__main__":
    unittest.main()
