"""Current-behavior characterization, NOT approved strategy/provider semantics.

Only hash-pinned function ASTs execute; the scanner module/main/provider imports never do.
All quotes are injected DataFrames and every CSV write uses a disposable temp directory.
"""
import ast
from contextlib import redirect_stdout
import copy
import csv
from datetime import datetime, time, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import socket
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import pandas as pd


FIXTURE = Path(__file__).with_name("fixtures") / "raccoon_radar_v3.py.txt"
SOURCE_SHA256 = "28bcd08df43b93f4f19818975d470cdc592c72a49d29fb71027d74e04d69eb0d"
_ROOTS = set()


def audit(event, args):
    if event.startswith(("socket.", "subprocess.", "sqlite3.")):
        raise PermissionError("Pinned scanner tests forbid network/processes/SQLite")
    if event == "open" and isinstance(args[0], (str, bytes, Path)):
        mode, flags = args[1], args[2]
        write = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool(flags & 0x3)
        if write:
            path = Path(args[0]).resolve()
            if not any(path.is_relative_to(root) for root in _ROOTS):
                raise PermissionError("Synthetic writes require a registered disposable directory")


def setUpModule():
    tempfile.gettempdir()  # Resolve tempfile's system probe before restricting writes.
    sys.addaudithook(audit)


def function(name, **values):
    data = FIXTURE.read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise AssertionError("Characterized source bytes changed")
    tree = ast.parse(data.decode("utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = dict(pd=pd, clock_time=time, RET_OK=0,
                     KLType=types.SimpleNamespace(K_1M="SYNTHETIC_1M"),
                     ENTRY_START=time(9,40), ENTRY_END=time(11,30))
    namespace.update(values)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(FIXTURE), "exec"), namespace)
    return namespace[name]


def fields():
    tree = ast.parse(FIXTURE.read_text(encoding="utf-8"))
    return ast.literal_eval(next(n.value for n in tree.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "FIELDS" for t in n.targets)))


def candles(count=35, start="2026-10-23 09:30:00"):
    start = datetime.fromisoformat(start)
    return [dict(time_key=(start+timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S"),
                 open=100+i*.1, high=100.2+i*.1, low=99.9+i*.1,
                 close=100.1+i*.1, volume=100) for i in range(count)]


class PinnedAnalysisTests(unittest.TestCase):
    def analyze(self, rows=None, now="2026-10-23T10:05:00-04:00", ret=0):
        rows = candles() if rows is None else rows
        provider = Mock()
        provider.request_history_kline.return_value = (ret, pd.DataFrame(rows), "UNCONSUMED_PAGE")
        output = function("analyze")(provider, "US.SPY", datetime.fromisoformat(now))
        return output, provider

    def test_exact_source_identity_and_no_provider_module_import(self):
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(), SOURCE_SHA256)
        self.assertEqual(len(FIXTURE.read_bytes()),6222)
        self.assertNotIn("moomoo",sys.modules)

    def test_current_pagination_key_is_ignored(self):
        output, provider = self.analyze()
        provider.request_history_kline.assert_called_once_with("US.SPY",start="2026-10-23",
            end="2026-10-23",ktype="SYNTHETIC_1M",max_count=1000)
        self.assertEqual(output["action"],"WAIT")

    def test_fresh_and_stale_both_keep_directional_bias_stale_patterns_cleared(self):
        rows = candles()
        rows[-1]["volume"] = 200
        rows[-1]["close"] += .2
        rows[-1]["high"] += .2
        fresh,_ = self.analyze(rows)
        stale,_ = self.analyze(rows,now="2026-10-23T11:00:00-04:00")
        self.assertTrue(fresh["fresh"])
        self.assertFalse(stale["fresh"])
        self.assertEqual(fresh["bias"],"BULLISH")
        self.assertEqual(stale["bias"],"BULLISH")
        self.assertNotEqual(fresh["pattern"],"None")
        self.assertEqual(stale["pattern"],"None")

    def test_exact_180_second_age_boundary_is_current_policy_not_verified_authority(self):
        at,_ = self.analyze(now="2026-10-23T10:07:00-04:00")
        after,_ = self.analyze(now="2026-10-23T10:07:01-04:00")
        self.assertTrue(at["fresh"])
        self.assertFalse(after["fresh"])

    def test_current_and_future_minute_removed_without_raw_stamp_shift(self):
        rows = candles(37)
        before = copy.deepcopy(rows)
        output,_ = self.analyze(rows,now="2026-10-23T10:05:59-04:00")
        self.assertEqual(output["bar_time_et"],"2026-10-23 10:04:00")
        self.assertEqual(rows,before)

    def test_1600_excluded_and_1559_retained(self):
        rows = candles(36,start="2026-10-23 15:25:00")
        output,_ = self.analyze(rows,now="2026-10-23T17:00:00-04:00")
        self.assertEqual(output["bar_time_et"],"2026-10-23 15:59:00")

    def test_missing_minute_is_not_rejected_when_row_count_sufficient(self):
        rows = candles(36)
        del rows[10]
        output,_ = self.analyze(rows,now="2026-10-23T10:06:00-04:00")
        self.assertEqual(output["bar_time_et"],"2026-10-23 10:05:00")

    def test_duplicates_not_deduplicated_change_ema(self):
        rows = candles()
        original,_ = self.analyze(rows)
        duplicate,_ = self.analyze(rows+[copy.deepcopy(rows[-1])])
        self.assertNotEqual(original["ema9"],duplicate["ema9"])
        self.assertEqual(original["bar_time_et"],duplicate["bar_time_et"])

    def test_wrong_session_can_survive_request_date_filter_and_emit_stale_bias(self):
        output,_ = self.analyze(candles(start="2026-10-22 09:30:00"))
        self.assertEqual(output["bar_time_et"],"2026-10-22 10:04:00")
        self.assertFalse(output["fresh"])
        self.assertEqual(output["bias"],"BULLISH")

    def test_inconsistent_ohlc_not_rejected(self):
        rows = candles()
        rows[-1]["low"] = rows[-1]["high"]+50
        output,_ = self.analyze(rows)
        self.assertEqual(output["bar_time_et"],rows[-1]["time_key"])

    def test_infinite_close_can_escape_to_output_and_strict_json_rejects(self):
        rows = candles()
        rows[-1]["close"] = float("inf")
        output,_ = self.analyze(rows)
        self.assertTrue(math.isinf(output["close"]))
        with self.assertRaises(ValueError):
            json.dumps(output,allow_nan=False)

    def test_zero_volume_anywhere_rejects_whole_snapshot(self):
        rows = candles()
        rows[0]["volume"] = 0
        with self.assertRaisesRegex(ValueError,"insufficient"):
            self.analyze(rows)

    def test_fewer_than_35_or_provider_failure_rejected(self):
        with self.assertRaisesRegex(ValueError,"insufficient"):
            self.analyze(candles(34))
        with self.assertRaisesRegex(ValueError,"history unavailable"):
            self.analyze(ret=1)

    def test_reverse_order_sorted_and_original_dataframe_unchanged(self):
        data = pd.DataFrame(list(reversed(candles())))
        before = data.copy(deep=True)
        provider = Mock()
        provider.request_history_kline.return_value = (0,data,None)
        output = function("analyze")(provider,"US.SPY",datetime.fromisoformat("2026-10-23T10:05:00-04:00"))
        pd.testing.assert_frame_equal(data,before)
        self.assertEqual(output["bar_time_et"],"2026-10-23 10:04:00")

    def test_ema_relative_volume_and_hlc3_proxy_follow_documented_formulas(self):
        rows = candles()
        rows[-1]["volume"] = 250
        output,_ = self.analyze(rows)
        e9=e21=rows[0]["close"]
        for row in rows[1:]:
            e9=(2/10)*row["close"]+(1-2/10)*e9
            e21=(2/22)*row["close"]+(1-2/22)*e21
        proxy=sum(((r["high"]+r["low"]+r["close"])/3)*r["volume"] for r in rows)/sum(r["volume"] for r in rows)
        self.assertEqual(output["ema9"],round(e9,4))
        self.assertEqual(output["ema21"],round(e21,4))
        self.assertEqual(output["vwap"],round(proxy,4))
        self.assertEqual(output["volume_ratio"],2.5)

    def test_mixed_bias_is_possible_and_action_always_wait(self):
        rows = candles()
        for row in rows:
            row.update(open=100,high=101,low=99,close=100)
        output,_ = self.analyze(rows)
        self.assertEqual(output["bias"],"MIXED")
        self.assertEqual(output["action"],"WAIT")

    def test_one_symbol_failure_still_logs_the_other_and_closes_fake_context(self):
        class Clock:
            @staticmethod
            def now(tz):
                return datetime.fromisoformat("2026-10-23T10:05:00-04:00")
        provider = Mock()
        provider.request_history_kline.side_effect = [(0,pd.DataFrame(candles()),None),
                                                       (1,"SYNTHETIC QQQ FAILURE",None)]
        append = Mock(return_value=1)
        scan = function("scan", datetime=Clock, ET=timezone.utc,
            OpenQuoteContext=Mock(return_value=provider), SYMBOLS=("US.SPY","US.QQQ"),
            analyze=function("analyze"),append_new_rows=append,LOG_FILE="SYNTHETIC_NO_FILE")
        with redirect_stdout(io.StringIO()) as capture:
            scan()
        self.assertEqual([r["symbol"] for r in append.call_args.args[0]],["US.SPY"])
        self.assertIn("US.QQQ: unavailable",capture.getvalue())
        provider.close.assert_called_once_with()


class PinnedCsvTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-pinned-scanner-")
        self.root = Path(self.temp.name)
        _ROOTS.add(self.root.resolve())
        self.log = self.root/"synthetic.csv"
        self.append = function("append_new_rows", csv=csv, LOG_FILE=self.log, FIELDS=fields())
        self.row = {key:"SYNTHETIC" for key in fields()}
        self.row.update(symbol="US.SPY",bar_time_et="2026-10-23 10:04:00",close=100)

    def tearDown(self):
        self.temp.cleanup()

    def test_first_write_header_and_same_bar_revision_suppressed(self):
        self.assertEqual(self.append([self.row]),1)
        before = self.log.read_bytes()
        revised = {**self.row,"close":999,"fresh":False}
        self.assertEqual(self.append([revised]),0)
        self.assertEqual(self.log.read_bytes(),before)

    def test_duplicate_within_one_batch_not_deduplicated(self):
        self.assertEqual(self.append([self.row,self.row]),2)
        with self.log.open(newline="") as handle:
            self.assertEqual(len(list(csv.DictReader(handle))),2)

    def test_empty_scan_does_not_create_file(self):
        self.assertEqual(self.append([]),0)
        self.assertFalse(self.log.exists())

    def test_network_and_sqlite_write_guards_are_active(self):
        with self.assertRaises(PermissionError):
            socket.socket()
        import sqlite3
        with self.assertRaises(PermissionError):
            sqlite3.connect(":memory:")


if __name__ == "__main__":
    unittest.main()
