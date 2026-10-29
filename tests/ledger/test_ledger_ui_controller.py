"""H-014 deterministic controller tests; real API, synthetic temporary stores only."""
import copy
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from uuid import uuid4

import test_manual_ledger as backend_tests
from ledger_ui_controller import LedgerController, WorkQueue, example_form
from manual_ledger import Ledger, LedgerError

def setUpModule():
    backend_tests.setUpModule()

def form(**values):
    return {**example_form(), "reason":"synthetic UI test", **values}

class LedgerControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        backend_tests._TEMPORARY_ROOTS.add(self.root.resolve())
        self.ui=LedgerController()
    def tearDown(self):
        self.temp.cleanup()
    def create(self):
        self.ui.create_store(self.root/"journal")
    def test_startup_has_no_store_or_automatic_open(self):
        self.assertIsNone(self.ui.repository)
        self.assertIsNone(self.ui.snapshot)
        self.assertEqual(list(self.root.iterdir()),[])
    def test_manual_buy_partial_exit_and_fee_pnl_come_from_repository(self):
        self.create()
        self.ui.submit_form(form(quantity="3",premium="1.00",fees="0.01"))
        position=self.ui.snapshot["positions"][0]["position_id"]
        data=self.ui.select_position(position)
        data.update(reason="synthetic partial exit",side="SELL_TO_CLOSE",quantity="1",
                    premium="1.20",fees="0.01",effective_at="2026-10-23T11:00:00-04:00")
        self.ui.submit_form(data)
        self.assertEqual(self.ui.snapshot,self.ui.repository.report())
        self.assertEqual(self.ui.snapshot["positions"][0]["remaining"],2)
        self.assertEqual(self.ui.snapshot["positions"][0]["realized_usd"],"19.99000000")
    def test_historical_view_blocks_writes_but_exports_exact_view(self):
        self.create()
        self.ui.submit_form(form())
        self.ui.set_sequence(0)
        with self.assertRaises(LedgerError): self.ui.submit_form(form())
        with self.assertRaises(LedgerError): self.ui.backup(self.root/"blocked-backup")
        out=self.root/"historical-export"
        self.ui.export(out)
        self.assertTrue((out/"manifest.json").exists())
        import json
        self.assertEqual(json.loads((out/"report.json").read_text())["snapshot_sequence"],0)
        self.assertFalse((self.root/"blocked-backup").exists())
    def test_correction_preserves_original_and_historical_snapshots(self):
        self.create(); self.ui.submit_form(form(premium="1.00"))
        original=copy.deepcopy(self.ui.snapshot)
        revision=original["revisions"][0]["revision_id"]
        data=self.ui.load_correction(revision)
        data.update(premium="1.05",reason="synthetic correction")
        self.ui.submit_form(data)
        self.assertEqual(len(self.ui.snapshot["revisions"]),2)
        self.ui.set_sequence(1)
        self.assertEqual(self.ui.snapshot,original)
        with self.assertRaises(LedgerError): self.ui.load_correction(revision)
        self.ui.set_sequence(None)
        with self.assertRaises(LedgerError): self.ui.load_correction(revision)
    def test_existing_contract_identity_cannot_be_changed_from_form(self):
        self.create(); self.ui.submit_form(form())
        position=self.ui.snapshot["positions"][0]["position_id"]
        data=self.ui.select_position(position)
        data.update(strike="999",reason="invalid identity edit")
        with self.assertRaises(LedgerError): self.ui.submit_form(data)
        self.assertEqual(self.ui.repository.report()["snapshot_sequence"],1)
    def test_integer_fields_reject_fractional_malformed_or_empty(self):
        self.create()
        for changes in (dict(quantity="1.5"),dict(quantity="1.0"),dict(tie="-1"),
                        dict(reason=""),dict(quantity="NaN")):
            with self.subTest(changes=changes),self.assertRaises(LedgerError):
                self.ui.submit_form(form(**changes))
        self.assertEqual(self.ui.repository.report()["snapshot_sequence"],0)
    def test_unknown_tick_is_explicit_not_verified(self):
        self.create(); self.ui.submit_form(form(tick=""))
        saved=self.ui.snapshot["active_fills"][0]
        self.assertEqual(saved["tick_authority"],"UNKNOWN")
        self.assertIsNone(saved["tick_units"])
    def test_lost_ack_retry_reuses_same_request_and_does_not_duplicate(self):
        self.create()
        original=self.ui.repository.apply
        observed=[]
        def apply(command,fills):
            observed.append((command,copy.deepcopy(fills)))
            receipt=original(command,fills)
            if len(observed)==1: raise OSError("synthetic lost acknowledgement")
            return receipt
        with patch.object(self.ui.repository,"apply",side_effect=apply):
            with self.assertRaises(OSError): self.ui.submit_form(form())
            pending=copy.deepcopy(self.ui.pending)
            with self.assertRaises(LedgerError): self.ui.submit_form(form())
            self.ui.retry_pending()
        self.assertEqual(observed[0],observed[1])
        self.assertEqual(observed[0][0],pending["command_id"])
        self.assertIsNone(self.ui.pending)
        self.assertEqual(len(self.ui.snapshot["commands"]),1)
    def test_reload_reconciles_committed_receipt_after_lost_ack(self):
        self.create(); original=self.ui.repository.apply
        def lost(command,fills):
            original(command,fills); raise OSError("synthetic ack loss")
        with patch.object(self.ui.repository,"apply",side_effect=lost):
            with self.assertRaises(OSError): self.ui.submit_form(form())
        self.ui.reload()
        self.assertIsNone(self.ui.pending)
        self.assertEqual(len(self.ui.snapshot["commands"]),1)
    def test_permanent_rejection_retained_until_explicit_abandon(self):
        self.create()
        with self.assertRaises(LedgerError):
            self.ui.submit_form(form(side="SELL_TO_CLOSE"))
        self.assertIsNotNone(self.ui.pending)
        with self.assertRaises(LedgerError): self.ui.abandon_pending(confirmed=False)
        self.ui.abandon_pending(confirmed=True)
        self.assertIsNone(self.ui.pending)
        self.assertEqual(self.ui.snapshot["snapshot_sequence"],0)
    def test_failed_open_clears_active_store_and_never_creates_path(self):
        self.create()
        missing=self.root/"missing"
        with self.assertRaises(LedgerError): self.ui.open_store(missing)
        self.assertIsNone(self.ui.repository)
        self.assertIsNone(self.ui.snapshot)
        self.assertFalse(missing.exists())
    def test_pending_request_prevents_store_switch_or_recovery(self):
        self.create()
        with self.assertRaises(LedgerError): self.ui.submit_form(form(side="SELL_TO_CLOSE"))
        with self.assertRaises(LedgerError): self.ui.create_store(self.root/"another")
        with self.assertRaises(LedgerError):
            self.ui.recover_store(self.root/"missing",confirmed=True)
        self.assertFalse((self.root/"another").exists())
    def test_void_is_auditable_and_cancellation_has_no_effect(self):
        self.create(); self.ui.submit_form(form())
        revision=self.ui.snapshot["revisions"][0]["revision_id"]
        old=copy.deepcopy(self.ui.snapshot)
        with self.assertRaises(LedgerError):
            self.ui.void_revision(revision,"synthetic void",confirmed=False)
        self.assertEqual(self.ui.repository.report(),old)
        self.ui.void_revision(revision,"synthetic void",confirmed=True)
        self.assertEqual(self.ui.snapshot["positions"][0]["status"],"VOIDED")
        self.assertEqual(len(self.ui.snapshot["revisions"]),2)
    def test_backup_is_new_nonoverwriting_and_reports_actual_cutoff(self):
        self.create(); self.ui.submit_form(form())
        result=self.ui.backup(self.root/"backup")
        self.assertEqual(result["sequence"],1)
        with self.assertRaises((LedgerError,FileExistsError)):
            self.ui.backup(self.root/"backup")
    def test_recovery_requires_confirmation_and_delegates_no_fallback(self):
        with patch.object(Ledger,"recover") as recover:
            with self.assertRaises(LedgerError):
                self.ui.recover_store(self.root/"missing",confirmed=False)
        recover.assert_not_called()

class WorkQueueTests(unittest.TestCase):
    def test_worker_delivers_data_and_close_waits_for_completion(self):
        queue=WorkQueue()
        release=threading.Event()
        queue.start(lambda:(release.wait(timeout=3),"synthetic")[1])
        self.assertTrue(queue.busy)
        self.assertFalse(queue.close())
        release.set()
        event=queue.take(timeout=3)
        self.assertTrue(event["ok"])
        self.assertEqual(event["result"],"synthetic")
        self.assertFalse(queue.busy)
        self.assertTrue(queue.close())
    def test_error_message_is_captured_before_deferred_ui_delivery(self):
        queue=WorkQueue()
        def fail(): raise LedgerError("synthetic visible failure")
        queue.start(fail)
        event=queue.take(timeout=3)
        self.assertFalse(event["ok"])
        self.assertIn("synthetic visible failure",event["error"])
        self.assertTrue(queue.close())

if __name__=="__main__":
    unittest.main()
