"""H-006 synthetic-only characterization; deliberate failures are NOT MERGE READY.

No provider, file/database adapter, historical replay or execution code.
Extreme values are valid under the engine's numeric schema, not market realism.
"""
import copy
import json
import math
import unittest
from datetime import datetime, timedelta

from direction_engine import evaluate

SOURCE_COMMIT = "6e7d1a8804b14aba9d08302bc5db48f31b0706ae"


def synthetic_rows(extreme=False):
    """25 complete minutes; first 24 volumes 1e-200, last 1e200 if extreme."""
    start = datetime(2026, 10, 23, 9, 30)
    rows = []
    for i in range(25):
        first = start + timedelta(minutes=i)
        end = first + timedelta(minutes=1)
        price = 0.01 + i * 0.0001
        volume = (1e200 if i == 24 else 1e-200) if extreme else (200.0 if i == 24 else 100.0)
        rows.append(dict(symbol="SPY", raw_timestamp=first.strftime("%Y-%m-%d %H:%M:%S"),
            interval_start_et=first.strftime("%Y-%m-%d %H:%M:%S"),
            interval_end_et=end.strftime("%Y-%m-%d %H:%M:%S"),
            available_at_et=end.strftime("%Y-%m-%d %H:%M:%S"), complete=True,
            open=price, high=price + 0.000025, low=price - 0.000025,
            close=price, volume=volume))
    return rows


def snapshot(rows):
    return evaluate(rows, symbol="SPY",
        session_open_et="2026-10-23 09:30:00",
        session_close_et="2026-10-23 16:00:00",
        as_of_et="2026-10-23 09:55:00",
        interval_evidence={"status":"SYNTHETIC", "reference":"H-006-explicit-intervals-only"})


def nonfinite_paths(value, path="$"):
    if isinstance(value, float) and not math.isfinite(value):
        return [path]
    if isinstance(value, dict):
        return [p for key, item in value.items() for p in nonfinite_paths(item, path+"."+str(key))]
    if isinstance(value, (list, tuple)):
        return [p for i, item in enumerate(value) for p in nonfinite_paths(item, path+"["+str(i)+"]")]
    return []


class ExtremeNumericOutputTests(unittest.TestCase):
    def checked_result(self, extreme):
        rows = synthetic_rows(extreme)
        for row in rows:
            for key in ("open","high","low","close","volume"):
                self.assertTrue(math.isfinite(row[key]), (key, row[key]))
            self.assertGreater(row["low"], 0)
            self.assertLessEqual(row["low"], min(row["open"], row["close"]))
            self.assertGreaterEqual(row["high"], max(row["open"], row["close"]))
            self.assertGreater(row["volume"], 0)
        before = copy.deepcopy(rows)
        result = snapshot(rows)
        self.assertEqual(rows, before, "Evaluation must not mutate synthetic input")
        self.assertEqual(result["data_quality"]["status"], "READY")
        self.assertEqual(result["data_quality"]["eligible_bars"], 25)
        self.assertEqual(result["observations"]["indicator_status"], "EVALUATED")
        return result

    def test_benign_control_is_finite_and_strict_json_serializable(self):
        result = self.checked_result(False)
        self.assertEqual(result["observations"]["volume_ratio"], 2.0)
        self.assertEqual(nonfinite_paths(result), [])
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)

    def test_extreme_valid_inputs_emit_only_finite_observation_numbers(self):
        result = self.checked_result(True)
        bad = nonfinite_paths(result["observations"], "$.observations")
        self.assertEqual(bad, [],
            "Finite coherent inputs emitted nonfinite observation(s): "+repr(bad)+
            "; volume_ratio="+repr(result["observations"]["volume_ratio"]))

    def test_extreme_valid_result_remains_strict_json_serializable(self):
        result = self.checked_result(True)
        try:
            encoded = json.dumps(result, allow_nan=False)
        except ValueError as error:
            self.fail("Strict JSON rejected the valid-input result: "+str(error)+
                "; nonfinite paths="+repr(nonfinite_paths(result)))
        self.assertEqual(json.loads(encoded), result)

    def test_existing_invalid_and_incomplete_inputs_still_fail_closed(self):
        for fields, reason in (({"complete":False}, "INCOMPLETE_CANDLE"),
                               ({"volume":float("inf")}, "INVALID_OHLCV"),
                               ({"low":1.0}, "INVALID_OHLCV")):
            with self.subTest(fields=fields):
                rows = synthetic_rows(True)
                rows[-1].update(fields)
                before = copy.deepcopy(rows)
                result = snapshot(rows)
                self.assertEqual(rows, before)
                self.assertEqual(result["signal"], "NO TRADE")
                self.assertIn(reason, result["reasons"])


if __name__ == "__main__":
    unittest.main()
