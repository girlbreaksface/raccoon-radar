"""Synthetic fixtures for the isolated observation recorder."""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from radar_live_panel import FeedRecovery
from radar_observations import ObservationStore, observation_report


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(self.enterContext(TemporaryDirectory())) / "synthetic-fixture.sqlite3"
        self.store = ObservationStore(self.path)
        self.now = datetime(2026, 11, 16, 15, tzinfo=timezone.utc)

    def snapshot(self):
        return {"authenticated": True, "provenance": {"source": "MOOMOO_OPEND", "sdk": "fixture"},
                "session": "REGULAR", "symbols": {
                    code: {"metrics": {"bars": 1}, "action": "WAIT",
                           "reason": "Unverified timestamp; Stale quote",
                           "raw_candles": [{"code": code, "time_key": "2026-11-16 09:31:00",
                                            "close": 101.01}]}
                    for code in ("US.SPY", "US.QQQ")}}

    def test_restart_round_trip_and_duplicate_batches(self):
        expected = self.snapshot()
        self.store.append(expected, self.now)
        self.store.append(expected, self.now)
        restored = list(ObservationStore(self.path).playback("2026-11-16"))
        self.assertEqual(restored, list(self.store.playback("2026-11-16")))
        self.assertEqual(len(restored), 2)
        for code, row in restored[0]["symbols"].items():
            self.assertEqual(row["raw_candles"], expected["symbols"][code]["raw_candles"])
            self.assertEqual(row["batch_sha256"], restored[1]["symbols"][code]["batch_sha256"])
        report = observation_report(self.store.playback("2026-11-16", include_candles=False))
        self.assertEqual(report["polls"], 2)
        self.assertEqual(report["wait_reasons"]["Unverified timestamp"], 4)
        self.assertEqual(report["decisions"]["US.QQQ WAIT"], 2)

    def test_lane_isolation_and_foreign_database(self):
        fixture = self.snapshot()
        with self.assertRaises(ValueError):
            self.store.append(dict(fixture, synthetic=True), self.now)
        with self.assertRaises(ValueError):
            self.store.append(dict(fixture, authenticated=False), self.now)
        self.assertFalse(self.path.exists())
        db = sqlite3.connect(self.path)
        try:
            db.execute("CREATE TABLE paper (trade TEXT)")
            db.commit()
        finally:
            db.close()
        with self.assertRaises(ValueError):
            self.store.append(fixture, self.now)

    def test_poll_tampering_rejected(self):
        self.store.append(self.snapshot(), self.now)
        db = sqlite3.connect(self.path)
        try:
            db.execute("UPDATE radar_observed_polls_v1 SET payload = '{}'")
            db.commit()
        finally:
            db.close()
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            list(self.store.playback("2026-11-16"))

    def test_recovery_requires_second_complete_poll(self):
        recovery = FeedRecovery()
        failure = {"status": "Connection closed", "symbols": {}}
        self.assertEqual(recovery.apply(failure), 5000)
        self.assertEqual(recovery.apply(dict(failure)), 10000)
        confirmation = self.snapshot()
        confirmation["symbols"]["US.SPY"]["action"] = "CALL"
        self.assertEqual(recovery.apply(confirmation), 5000)
        self.assertEqual(confirmation["symbols"]["US.SPY"]["action"], "WAIT")
        self.assertIn("confirming", confirmation["symbols"]["US.SPY"]["reason"])
        self.assertEqual(recovery.apply(self.snapshot()), 20000)
        self.assertEqual(recovery.state, "OBSERVING")
