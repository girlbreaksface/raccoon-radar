"""Synthetic-only journal acceptance. All stores are explicit temporary directories."""
import copy
import csv
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4
from manual_ledger import Ledger, LedgerError, RecoveryRequired

def uid():
    return str(uuid4())

def contract(**kw):
    data = dict(symbol="SYNTHETIC_SPY_CALL", underlying="SPY", expiration="2026-12-18",
                strike="500", right="CALL", multiplier=100, currency="USD", deliverable="STANDARD_100")
    return {**data, **kw}

def fill(position=None, **kw):
    data = dict(fill_id=uid(), revision_id=uid(), expected_revision=None,
                position_id=position or uid(), contract=contract(), side="BUY_TO_OPEN",
                quantity=3, premium="1.00", fees="0.01",
                effective_at="2026-10-23T10:00:00-04:00",
                timezone="America/New_York", tie=0, reason="synthetic fixture",
                tick="0.01", tick_authority="USER_ASSERTED", synthetic=True)
    return {**data, **kw}

def files(path):
    return {str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob("*") if p.is_file()}

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = self.root/"journal"
        self.ledger = Ledger.create(self.path, synthetic=True)
    def tearDown(self):
        self.temp.cleanup()
    def write(self, *items, command=None, fault=None):
        return self.ledger.apply(command or uid(), list(items), _fault=fault)
    def three_fills(self):
        entry = fill()
        first = fill(entry["position_id"], side="SELL_TO_CLOSE", quantity=1, premium="1.20",
                     effective_at="2026-10-23T11:00:00-04:00")
        second = fill(entry["position_id"], side="SELL_TO_CLOSE", quantity=2, premium="0.90",
                      effective_at="2026-10-24T11:00:00-04:00")
        self.write(entry, first, second)
        return entry, first, second

    def test_partial_fee_conservation_and_exact_realized_totals(self):
        self.three_fills()
        report = self.ledger.report()
        self.assertEqual([a["net_usd"] for a in report["allocations"]], ["19.99000000","-20.02000000"])
        self.assertEqual(sum(a["entry_fee_cents"] for a in report["allocations"]), 1)
        self.assertEqual(sum(a["exit_fee_cents"] for a in report["allocations"]), 2)
        self.assertEqual(report["positions"][0]["realized_usd"], "-0.03000000")
        self.assertEqual(report["positions"][0]["status"], "CLOSED")

    def test_fee_remainder_stays_with_open_lot(self):
        entry = fill()
        self.write(entry, fill(entry["position_id"], side="SELL_TO_CLOSE", quantity=1,
                              premium="1.20", effective_at="2026-10-23T11:00:00-04:00"))
        p = self.ledger.report()["positions"][0]
        self.assertEqual(p["unrecognized_entry_fee_cents"], 1)
        self.assertEqual(p["status"], "PARTIALLY_CLOSED")
        self.assertEqual(p["remaining"], 2)

    def test_multiple_fifo_lots_and_exit_fee_allocation(self):
        entry = fill(quantity=1, fees="0")
        another = fill(entry["position_id"], quantity=2, premium="2",fees="0.02",
                       effective_at="2026-10-23T10:01:00-04:00")
        exit_ = fill(entry["position_id"], side="SELL_TO_CLOSE", premium="3",fees="0.01",
                     effective_at="2026-10-23T11:00:00-04:00")
        self.write(entry, another, exit_)
        a = self.ledger.report()["allocations"]
        self.assertEqual([i["entry_fill_id"] for i in a],[entry["fill_id"],another["fill_id"]])
        self.assertEqual(sum(i["exit_fee_cents"] for i in a),1)
        self.assertEqual(sum(i["entry_fee_cents"] for i in a),2)

    def test_correction_batch_and_original_snapshot_reproducible(self):
        entry, first, second = self.three_fills()
        before = self.ledger.report()
        replacement = {**entry,"revision_id":uid(),"expected_revision":entry["revision_id"],
                       "premium":"1.05","reason":"synthetic correction"}
        receipt = self.write(replacement)
        after = self.ledger.report()
        self.assertEqual(after["positions"][0]["realized_usd"], "-15.03000000")
        self.assertEqual(self.ledger.report(sequence=1),before)
        self.assertEqual(receipt["sequence"],2)
        self.assertEqual(len(after["revisions"]),4)

    def test_stale_write_and_invalid_dependent_correction_rollback(self):
        entry, _, _ = self.three_fills()
        before = self.ledger.report()
        with self.assertRaises(LedgerError):
            self.write({**entry,"revision_id":uid(),"expected_revision":entry["revision_id"],"quantity":1})
        self.assertEqual(self.ledger.report(),before)
        with self.assertRaises(LedgerError):
            self.write({**entry,"revision_id":uid(),"premium":"2"})
        self.assertEqual(self.ledger.report(),before)

    def test_atomic_void_batch_can_remove_dependent_trade_without_erasing_history(self):
        items = self.three_fills()
        voids=[dict(fill_id=i["fill_id"],revision_id=uid(),expected_revision=i["revision_id"],
                    void=True,reason="synthetic void",synthetic=True) for i in items]
        self.write(*voids)
        report=self.ledger.report()
        self.assertEqual(report["allocations"],[])
        self.assertEqual(report["positions"][0]["status"],"VOIDED")
        self.assertEqual(len(report["revisions"]),6)
        self.assertEqual(len(self.ledger.report(sequence=1)["allocations"]),2)

    def test_idempotency_and_lost_ack_retry_commit_once(self):
        entry=fill(); command=uid()
        def fault(stage):
            if stage=="after_commit": raise OSError("lost acknowledgement")
        with self.assertRaises(OSError):
            self.write(entry,command=command,fault=fault)
        one=self.write(entry,command=command)
        self.assertEqual(one["sequence"],1)
        self.assertEqual(self.ledger.report()["snapshot_sequence"],1)
        with self.assertRaises(LedgerError):
            self.write({**entry,"fees":"1"},command=command)

    def test_failure_at_insert_and_before_commit_is_atomic(self):
        for target in ("after_command","after_revision","before_commit"):
            with self.subTest(target=target):
                before=self.ledger.report()
                def fault(stage):
                    if stage==target: raise OSError("synthetic disk failure")
                with self.assertRaises(OSError): self.write(fill(),fault=fault)
                self.assertEqual(self.ledger.report(),before)

    def test_unknown_cutoff_and_bool_rejected_no_half_batch_visibility(self):
        self.three_fills()
        for bad in (True,-1,2,1.5,"1"):
            with self.subTest(bad=bad),self.assertRaises(LedgerError):
                self.ledger.report(sequence=bad)
        self.assertEqual(self.ledger.report(sequence=0)["active_fills"],[])

    def test_invalid_inputs_and_unsupported_terms_never_commit(self):
        invalid=[dict(quantity=1.5),dict(quantity=True),dict(quantity=0),dict(premium="NaN"),
                 dict(premium="1e3"),dict(premium="-1"),dict(fees="0.001"),dict(fees="-1"),
                 dict(synthetic=False),dict(contract=contract(underlying="IWM")),
                 dict(contract=contract(multiplier=10)),dict(contract=contract(right="BAD")),
                 dict(contract=contract(symbol="SPY_REAL")),dict(tick_authority="VERIFIED"),
                 dict(premium="0"),dict(timezone="No/SuchZone")]
        for changes in invalid:
            with self.subTest(changes=changes),self.assertRaises(LedgerError):
                self.write(fill(**changes))
        self.assertEqual(self.ledger.report()["snapshot_sequence"],0)

    def test_no_oversell_negative_prefix_equal_time_ambiguity_or_reopen(self):
        entry=fill(quantity=1); self.write(entry)
        for exit_ in [fill(entry["position_id"],side="SELL_TO_CLOSE",quantity=2),
                      fill(entry["position_id"],side="SELL_TO_CLOSE",quantity=1,
                           effective_at="2026-10-23T09:59:00-04:00")]:
            with self.assertRaises(LedgerError): self.write(exit_)
        exit_=fill(entry["position_id"],side="SELL_TO_CLOSE",quantity=1,
                   effective_at="2026-10-23T11:00:00-04:00")
        self.write(exit_)
        with self.assertRaises(LedgerError):
            self.write(fill(entry["position_id"],effective_at="2026-10-23T12:00:00-04:00"))
        other=fill()
        with self.assertRaises(LedgerError):
            self.write(other,fill(other["position_id"]))

    def test_zero_close_is_explicit_no_automatic_expiry(self):
        entry=fill(); self.write(entry)
        with self.assertRaises(LedgerError):
            self.write(fill(entry["position_id"],side="SELL_TO_CLOSE",premium="0",
                            effective_at="2026-10-23T12:00:00-04:00"))
        self.write(fill(entry["position_id"],side="MANUAL_ZERO_CLOSE",premium="0",
                        effective_at="2026-10-23T12:00:00-04:00"))
        self.assertEqual(self.ledger.report()["positions"][0]["status"],"CLOSED")

    def test_tick_warning_preserves_fill_price_and_inputs(self):
        item=fill(premium="1.03",tick="0.05")
        before=copy.deepcopy(item); self.write(item)
        saved=self.ledger.report()["active_fills"][0]
        self.assertEqual(saved["premium_units"],103000000)
        self.assertIn("OFF_REFERENCE_TICK",saved["warnings"])
        self.assertEqual(item,before)

    def test_dst_offsets_and_iso_year_reporting(self):
        for stamp in ("2026-03-08T02:30:00-05:00","2026-11-01T01:30:00-03:00"):
            with self.assertRaises(LedgerError): self.write(fill(effective_at=stamp))
        early=fill(effective_at="2026-11-01T01:30:00-04:00")
        later=fill(effective_at="2026-11-01T01:30:00-05:00")
        self.write(early,later)
        folds=[i["fold"] for i in self.ledger.report()["active_fills"]]
        self.assertEqual(folds,[0,1])
        entry=fill(effective_at="2020-12-31T10:00:00-05:00")
        exit_=fill(entry["position_id"],side="SELL_TO_CLOSE",premium="1.20",
                   effective_at="2021-01-01T10:00:00-05:00")
        self.write(entry,exit_)
        self.assertIn("2020-W53",self.ledger.report()["summaries"]["weekly"])
        self.assertIn("2021-01",self.ledger.report()["summaries"]["monthly"])

    def test_large_products_do_not_overflow_sqlite_integer_or_use_float(self):
        entry=fill(quantity=100000,premium="1000000",fees="0")
        self.write(entry,fill(entry["position_id"],quantity=100000,premium="0",
                   fees="0",side="MANUAL_ZERO_CLOSE",effective_at="2026-10-23T12:00:00-04:00"))
        self.assertEqual(self.ledger.report()["positions"][0]["realized_usd"],
                         "-10000000000000.00000000")

    def test_reload_readonly_and_no_open_creation(self):
        self.three_fills(); before=self.ledger.report()
        self.assertEqual(Ledger.open(self.path).report(),before)
        read=Ledger.open(self.path,readonly=True)
        with self.assertRaises(LedgerError): read.apply(uid(),[fill()])
        missing=self.root/"missing"
        with self.assertRaises(LedgerError): Ledger.open(missing)
        self.assertFalse(missing.exists())

    def test_create_collision_and_foreign_path_do_not_change_bytes(self):
        before=files(self.path)
        with self.assertRaises((LedgerError,FileExistsError)): Ledger.create(self.path,synthetic=True)
        self.assertEqual(files(self.path),before)
        foreign=self.root/"raccoon_history.sqlite3"
        with sqlite3.connect(foreign) as db: db.execute("CREATE TABLE precious(value)")
        old=foreign.read_bytes()
        with self.assertRaises(LedgerError): Ledger.open(foreign)
        self.assertEqual(foreign.read_bytes(),old)
        other=self.root/"foreign"; other.mkdir()
        (other/"ledger.sqlite3").write_bytes(old)
        with self.assertRaises(LedgerError): Ledger.open(other)
        self.assertEqual((other/"ledger.sqlite3").read_bytes(),old)

    def test_identity_replacement_hardlinks_and_schema_changes_blocked(self):
        db=self.path/"ledger.sqlite3"
        original=db.read_bytes()
        replacement=self.path/"other"
        replacement.write_bytes(original)
        os.replace(replacement,db)
        with self.assertRaises(LedgerError): Ledger.open(self.path)
        self.assertEqual(db.read_bytes(),original)

    def test_symlink_and_hardlink_paths_fail_closed(self):
        alias=self.root/"alias"
        try: alias.symlink_to(self.path,target_is_directory=True)
        except OSError: pass  # Platform privilege may forbid creation; hard-link case still tested.
        else:
            with self.assertRaises(LedgerError): Ledger.open(alias)
        os.link(self.path/"ledger.sqlite3",self.root/"hardlink.sqlite3")
        before=files(self.path)
        with self.assertRaises(LedgerError): Ledger.open(self.path)
        self.assertEqual(files(self.path),before)

    def test_immutable_sql_rows_and_corruption_are_not_reinitialized(self):
        self.write(fill())
        with sqlite3.connect(self.path/"ledger.sqlite3") as db:
            with self.assertRaises(sqlite3.DatabaseError):
                db.execute("DELETE FROM commands")
        damaged=self.path/"ledger.sqlite3"
        # Same inode, synthetic only: invalid header must fail without replacing it.
        with damaged.open("r+b") as output: output.write(b"BAD HEADER")
        before=files(self.path)
        with self.assertRaises(LedgerError): Ledger.open(self.path)
        self.assertEqual(files(self.path),before)

    def test_export_snapshot_consistency_formula_safety_and_no_overwrite(self):
        self.three_fills()
        out=self.root/"export"
        self.ledger.export(out,sequence=1)
        manifest=json.loads((out/"manifest.json").read_text())
        self.assertTrue(manifest["complete"])
        self.assertEqual(json.loads((out/"report.json").read_text()),self.ledger.report(sequence=1))
        for name,hash_ in manifest["sha256"].items():
            self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(),hash_)
        before=files(out)
        with self.assertRaises((LedgerError,FileExistsError)): self.ledger.export(out)
        self.assertEqual(files(out),before)
        self.write(fill(reason="  =HYPERLINK(synthetic)"))
        self.ledger.export(self.root/"sanitized")
        with (self.root/"sanitized"/"revisions.csv").open(newline="") as stream:
            rows=list(csv.DictReader(stream))
        self.assertTrue(rows[-1]["reason"].startswith("'"))
        self.assertEqual(self.ledger.report()["active_fills"][-1]["reason"],"  =HYPERLINK(synthetic)")

    def test_incomplete_export_never_has_completion_manifest(self):
        def fault(stage):
            if stage=="before_export_complete": raise OSError("synthetic write failed")
        out=self.root/"partial-export"
        with self.assertRaises(OSError): self.ledger.export(out,_fault=fault)
        self.assertFalse((out/"manifest.json").exists())

    def test_backup_restore_new_path_and_tamper_detection(self):
        self.three_fills()
        backup=self.root/"backup"
        self.ledger.backup(backup)
        self.assertEqual(Ledger.open(backup,readonly=True).report(),self.ledger.report())
        with self.assertRaises(LedgerError): Ledger.open(backup)
        restored=Ledger.restore(backup,self.root/"restored",synthetic=True)
        self.assertEqual(restored.report(),self.ledger.report())
        before=files(backup)
        with self.assertRaises((LedgerError,FileExistsError)):
            Ledger.restore(backup,self.path,synthetic=True)
        self.assertEqual(files(backup),before)
        with (backup/"ledger.sqlite3").open("ab") as output: output.write(b"x")
        with self.assertRaises(LedgerError): Ledger.restore(backup,self.root/"nope",synthetic=True)

    def test_unknown_schema_version_does_not_migrate(self):
        with sqlite3.connect(self.path/"ledger.sqlite3") as db: db.execute("PRAGMA user_version=99")
        before=files(self.path)
        with self.assertRaises(LedgerError): Ledger.open(self.path)
        self.assertEqual(files(self.path),before)

    def test_busy_writer_is_bounded_and_rollback_preserves_state(self):
        db=sqlite3.connect(self.path/"ledger.sqlite3")
        db.execute("BEGIN IMMEDIATE")
        try:
            with self.assertRaises(LedgerError): self.write(fill())
        finally:
            db.rollback(); db.close()
        self.assertEqual(self.ledger.report()["snapshot_sequence"],0)

    def test_process_interrupt_before_and_after_commit(self):
        # Controlled child only, temp synthetic store; no default path or providers.
        for stage in ("before_commit","after_commit"):
            with self.subTest(stage=stage):
                path=self.root/stage
                Ledger.create(path,synthetic=True)
                item=fill(); command=uid()
                request=self.root/(stage+".json")
                request.write_text(json.dumps(dict(command=command,fills=[item])))
                program=("import json,os,sys; from manual_ledger import Ledger; "
                         "p=json.load(open(sys.argv[2])); "
                         "Ledger.open(sys.argv[1]).apply(p['command'],p['fills'],"
                         "_fault=lambda s: os._exit(91) if s==sys.argv[3] else None)")
                run=subprocess.run([sys.executable,"-B","-c",program,str(path),str(request),stage],
                                   cwd=Path(__file__).resolve().parents[2],capture_output=True,timeout=20)
                self.assertEqual(run.returncode,91,run.stderr.decode())
                if stage=="before_commit":
                    old=files(path)
                    with self.assertRaises(RecoveryRequired): Ledger.open(path)
                    self.assertEqual(files(path),old)
                    Ledger.recover(path,confirm_exclusive=True)
                ledger=Ledger.open(path)
                ledger.apply(command,[item])
                self.assertEqual(ledger.report()["snapshot_sequence"],1)
                self.assertEqual(len(ledger.report()["active_fills"]),1)

if __name__=="__main__":
    unittest.main()
