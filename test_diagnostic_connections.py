"""Disposable-store regression tests for read-only diagnostic handle lifetime."""
import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import ExitStack, closing
from pathlib import Path
from unittest.mock import patch

from raccoon_diagnostics import inspect_database


class DiagnosticConnectionTests(unittest.TestCase):
    def inspect_fixture(self, schema, expect_error):
        with tempfile.TemporaryDirectory() as folder, ExitStack() as cleanup:
            path = Path(folder) / "synthetic.sqlite3"
            with closing(sqlite3.connect(path)) as db:
                db.execute(schema)
                db.commit()
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            connect = sqlite3.connect
            connections = []
            requests = []

            def tracked_connect(database, **kwargs):
                requests.append((database, kwargs))
                connection = connect(database, **kwargs)
                connections.append(connection)  # Prevent GC from concealing leaks.
                cleanup.callback(connection.close)
                return connection

            with patch("raccoon_diagnostics.sqlite3.connect",
                       side_effect=tracked_connect):
                report = inspect_database(path)
            self.assertEqual(len(connections), 1)
            self.assertTrue(requests[0][0].endswith("?mode=ro"))
            self.assertTrue(requests[0][1]["uri"])
            self.assertEqual("error" in report, expect_error)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
            with self.assertRaises(sqlite3.ProgrammingError):
                connections[0].execute("SELECT 1")
            return report

    def test_success_closes_read_only_handle_and_preserves_file(self):
        report = self.inspect_fixture("CREATE TABLE synthetic (value TEXT)", False)
        self.assertEqual(report["integrity_check"], "ok")
        self.assertEqual(report["tables"]["synthetic"]["rows"], 0)

    def test_schema_error_also_closes_handle_and_preserves_file(self):
        report = self.inspect_fixture(
            "CREATE TABLE discovery_snapshots (id INTEGER)", True)
        self.assertIn("OperationalError", report["error"])

    def test_missing_database_is_not_created_or_connected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic-missing.sqlite3"
            with patch("raccoon_diagnostics.sqlite3.connect") as connect:
                self.assertFalse(inspect_database(path)["exists"])
            connect.assert_not_called()
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
