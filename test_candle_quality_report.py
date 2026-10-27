"""Standalone CSV diagnostic tests use synthetic temporary files only."""
import csv
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from candle_quality_report import main


FIELDS = ("symbol", "time", "open", "high", "low", "close", "volume")


def rows():
    return [dict(symbol="SPY", time=f"2026-10-23 09:{minute:02d}:00",
                 open=100, high=101, low=99, close=100, volume=10)
            for minute in range(30, 35)]


class CandleQualityReportTests(unittest.TestCase):
    def write_csv(self, path, records):
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(records)

    def run_report(self, source, output=None):
        args = ["--input", str(source), "--expected-start", "09:30",
                "--expected-end", "09:34"]
        if output is not None:
            args += ["--output", str(output)]
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_complete_csv_is_read_only_hashed_and_explicitly_unverified(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.csv"
            self.write_csv(path, rows())
            original = path.read_bytes()
            with patch("sqlite3.connect") as connect:
                code, stdout, stderr = self.run_report(path)
            connect.assert_not_called()
            self.assertEqual(code, 0)
            self.assertEqual(stderr, "")
            report = json.loads(stdout)
            self.assertEqual(report["status"], "COVERAGE_MATCH")
            self.assertEqual(report["audit"]["timestamp_semantics"], "UNVERIFIED")
            self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(path.read_bytes(), original)

    def test_gaps_duplicates_and_invalid_ohlcv_produce_review_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.csv"
            original_rows = rows()
            self.write_csv(path, [original_rows[0], original_rows[0],
                                 dict(original_rows[2], low=105), original_rows[4]])
            code, stdout, _ = self.run_report(path)
            report = json.loads(stdout)
            self.assertEqual(code, 2)
            self.assertEqual(report["status"], "REVIEW")
            self.assertEqual(len(report["audit"]["invalid_rows"]), 1)
            session = report["audit"]["sessions"][0]
            self.assertEqual(session["missing_minutes"], ["09:31", "09:32", "09:33"])
            self.assertEqual(session["duplicates"][0]["count"], 2)

    def test_output_is_exclusive_and_cannot_overwrite_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "synthetic.csv"
            target = Path(folder) / "report.json"
            self.write_csv(source, rows())
            original = source.read_bytes()
            target.write_text("existing evidence", encoding="utf-8")
            for destination in (target, source):
                with self.subTest(destination=destination):
                    code, _, stderr = self.run_report(source, destination)
                    self.assertEqual(code, 1)
                    self.assertIn("Report failed", stderr)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(target.read_text(encoding="utf-8"), "existing evidence")
            fresh = Path(folder) / "new-report.json"
            self.assertEqual(self.run_report(source, fresh)[0], 0)
            self.assertEqual(json.loads(fresh.read_text(encoding="utf-8"))["status"],
                             "COVERAGE_MATCH")

    def test_bad_schema_and_non_csv_input_fail_without_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ("synthetic.csv", "synthetic.sqlite3"):
                source = root / name
                source.write_text("symbol,close\nSPY,100\n", encoding="utf-8")
                target = root / "never-created.json"
                code, _, _ = self.run_report(source, target)
                self.assertEqual(code, 1)
                self.assertFalse(target.exists())

    def test_header_only_csv_is_no_data_not_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "synthetic-empty.csv"
            self.write_csv(source, [])
            code, stdout, _ = self.run_report(source)
            self.assertEqual(code, 2)
            report = json.loads(stdout)
            self.assertEqual(report["status"], "NO_DATA")
            self.assertEqual(report["audit"]["sessions"], [])


if __name__ == "__main__":
    unittest.main()
