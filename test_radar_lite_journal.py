"""Paper journal persistence tests using disposable synthetic runs."""
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from raccoon_radar_lite import JournaledReplay
from radar_lite_journal import JournalError, PaperJournal


class JournalTests(unittest.TestCase):
    def setUp(self):
        folder = self.enterContext(TemporaryDirectory())
        self.path = Path(folder) / "synthetic-paper.sqlite3"
        self.journal = PaperJournal(self.path)

    def resume(self, *, new=False):
        return JournaledReplay(PaperJournal(self.path), "conflict", 34, new=new)

    def enter_trade(self, session):
        run = session.run
        contract = run.candidates(run.point.cells[0])[0].contract
        session.record("ENTER", contract)
        return contract

    def test_restart_restores_position_cursor_and_limit(self):
        start = self.resume()
        contract = self.enter_trade(start)
        resumed = self.resume()
        self.assertEqual(resumed.run.open.contract, contract)
        self.assertEqual(resumed.run.index, 34)
        resumed.record("ENTER", contract)
        self.assertEqual(resumed.sequence, 1)
        resumed.record("STEP")
        for _ in range(2):
            self.enter_trade(resumed)
            resumed.record("STEP")
        final = self.resume()
        self.assertEqual(final.run.index, 37)
        self.assertEqual(final.run.entries, 3)
        self.assertIsNone(final.run.open)
        self.assertFalse(final.run.can_enter)
        self.assertEqual(len(self.journal.history()), 6)
        self.assertIn("TARGET", final.run.events[1])
        self.assertIn("STOP", final.run.events[3])

    def test_save_failure_does_not_publish_state(self):
        session = self.resume()
        with patch.object(session.journal, "append", side_effect=sqlite3.OperationalError("disk full")):
            with self.assertRaises(sqlite3.OperationalError):
                self.enter_trade(session)
        self.assertEqual(session.sequence, 0)
        self.assertEqual(session.run.entries, 0)
        self.assertEqual(self.journal.history(), ())

    def test_stale_windows_cannot_duplicate_or_write_to_archived_run(self):
        first, stale = self.resume(), self.resume()
        self.enter_trade(first)
        with self.assertRaises(JournalError):
            self.enter_trade(stale)
        self.assertIsNone(stale.run.open)
        new = self.resume(new=True)
        self.assertEqual(new.run.entries, 0)
        self.assertNotEqual(new.replay_id, first.replay_id)
        with self.assertRaises(JournalError):
            first.record("STEP")
        self.assertEqual(self.journal.history()[0][0], first.replay_id)

    def test_unreplayable_log_is_rejected(self):
        session = self.resume()
        self.journal.append(session.replay_id, 1, "ENTER", -1, "invalid")
        with self.assertRaises(JournalError):
            self.resume()
