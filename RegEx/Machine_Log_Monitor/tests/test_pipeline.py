import csv
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import jobs
import report
from config import DB_SCHEMA
from log_parser import parse_machine_log
from log_reader import MachineLogReader


class MachineLogPipelineTests(unittest.TestCase):
    def test_reader_returns_line_numbers_and_end_of_file_status(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "machine.log"
            log_path.write_text("first\nsecond\n", encoding="utf-8")
            reader = MachineLogReader(log_path)
            try:
                self.assertEqual(reader.read_next_line(), (1, "first", False))
                self.assertEqual(reader.read_next_line(), (2, "second", True))
                self.assertIsNone(reader.read_next_line())
            finally:
                reader.close()

    def test_parser_extracts_error_fields_and_rejects_invalid_date(self):
        parsed = parse_machine_log(
            "2026-10-08 10:16:55 | ERROR | Machine M102 | Motor overheating"
        )

        self.assertEqual(parsed["machine_id"], "M102")
        self.assertEqual(parsed["error_message"], "Motor overheating")
        self.assertEqual(parsed["level"], "ERROR")
        self.assertIsNotNone(parsed["timestamp"].tzinfo)
        self.assertIsNone(
            parse_machine_log(
                "2026-13-08 10:16:55 | ERROR | Machine M102 | Invalid date"
            )
        )

    def test_job_retries_failed_line_and_stores_critical_events(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "machine.log"
            log_path.write_text(
                "2026-10-08 10:16:55 | CRITICAL | Machine M102 | Shutdown\n",
                encoding="utf-8",
            )
            reader = MachineLogReader(log_path)
            self.addCleanup(reader.close)

            with (
                patch.object(jobs, "reader", reader),
                patch.object(
                    jobs,
                    "store_errors",
                    side_effect=[RuntimeError("database unavailable"), None],
                ) as store_errors,
                patch.object(jobs, "generate_report") as generate_report,
            ):
                with self.assertRaisesRegex(RuntimeError, "database unavailable"):
                    jobs.monitor_machine_logs()

                self.assertEqual(reader.line_number, 0)
                self.assertFalse(jobs.monitor_machine_logs())

            self.assertEqual(store_errors.call_count, 2)
            self.assertEqual(store_errors.call_args.args[0][0]["level"], "CRITICAL")
            generate_report.assert_called_once()

    def test_report_accepts_string_path_and_writes_csv(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ("M102", "2026-10-08 10:16:55+00:00", "Motor overheating")
        ]

        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "nested" / "errors.csv"
            with (
                patch.object(report, "get_connection", return_value=connection),
                patch.object(report, "REPORT_FILE", str(report_path)),
                self.assertLogs("report", level=logging.INFO) as log,
            ):
                report.generate_report()

            with report_path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.reader(file))

        self.assertEqual(
            rows,
            [
                ["Machine ID", "Timestamp", "Error Message"],
                ["M102", "2026-10-08 10:16:55+00:00", "Motor overheating"],
            ],
        )
        self.assertIn(
            f"FROM {DB_SCHEMA}.machine_errors", cursor.execute.call_args.args[0]
        )
        self.assertIn("Records=1", log.output[0])
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
