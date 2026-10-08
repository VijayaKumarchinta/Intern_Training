import logging
import unittest
from unittest.mock import MagicMock, patch

from machine_insert import store_errors


class StoreErrorsTests(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        self.connection_patch = patch(
            "machine_insert.get_connection",
            return_value=self.connection,
        )
        self.connection_patch.start()
        self.addCleanup(self.connection_patch.stop)

    def test_new_error_is_inserted_and_duplicate_is_ignored(self):
        row_counts = iter((1, 0))

        def execute(query, parameters):
            self.assertIn("INSERT INTO", query)
            self.assertEqual(parameters[0], "M102")
            self.cursor.rowcount = next(row_counts)

        self.cursor.execute.side_effect = execute
        error = {
            "machine_id": "M102",
            "timestamp": "2026-10-08T10:16:55+00:00",
            "unix_timestamp": 1791454615,
            "error_message": "Motor overheating",
        }

        with self.assertLogs("machine_insert", level=logging.INFO) as log:
            store_errors([error, error])

        self.assertIn("Stored 1 error(s); ignored 1 duplicate(s)", log.output[0])
        self.assertEqual(self.cursor.execute.call_count, 2)
        query = self.cursor.execute.call_args.args[0]
        self.assertIn("ON CONFLICT ON CONSTRAINT unique_machine_error", query)
        self.connection.commit.assert_called_once()
        self.connection.rollback.assert_not_called()
        self.connection.close.assert_called_once()

    def test_database_failure_rolls_back_and_is_raised(self):
        self.cursor.execute.side_effect = RuntimeError("database unavailable")

        with self.assertLogs("machine_insert", level=logging.ERROR):
            with self.assertRaisesRegex(RuntimeError, "database unavailable"):
                store_errors(
                    [
                        {
                            "machine_id": "M102",
                            "timestamp": "2026-10-08T10:16:55+00:00",
                            "unix_timestamp": 1791454615,
                            "error_message": "Motor overheating",
                        }
                    ]
                )

        self.connection.commit.assert_not_called()
        self.connection.rollback.assert_called_once()
        self.connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
