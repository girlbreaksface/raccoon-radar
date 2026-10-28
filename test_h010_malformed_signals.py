"""H-010 synthetic malformed-signal repair contracts; no market or IO adapters."""
import copy
import json
import unittest
from unittest.mock import patch

import direction_validation as replay
from test_extreme_numeric_output import synthetic_rows, snapshot, nonfinite_paths
import test_h009_consumer_integration as h009

MISSING = object()
BAD = (MISSING, None, "", "UNKNOWN", "BULLISH", "BEARISH", " bullish candidate ",
       0, True, [], {}, float("inf"), float("nan"))


def source():
    return h009.H009ConsumerIntegrationTests().two_decision_session()


def fake(signal):
    value = snapshot(synthetic_rows(False))
    value["reasons"] = ["SYNTHETIC_ORIGINAL_REASON"]
    if signal is MISSING:
        del value["signal"]
    else:
        value["signal"] = signal
    return value


class H010MalformedSignalTests(unittest.TestCase):
    def test_all_malformed_signals_are_explicit_json_safe_rejections(self):
        for signal in BAD:
            with self.subTest(signal=repr(signal)):
                result_from_engine = fake(signal)
                original = copy.deepcopy(result_from_engine)
                rows = source()
                original_rows = copy.deepcopy(rows)
                with patch.object(replay, "evaluate", return_value=result_from_engine):
                    result = replay.replay_session(**rows)
                self.assertEqual(result["events"], [])
                for item in result["snapshots"]:
                    self.assertEqual(item["signal"], "NO TRADE")
                    self.assertEqual(item["reasons"],
                                     ["SYNTHETIC_ORIGINAL_REASON", "INVALID_SIGNAL"])
                    self.assertEqual(item["data_quality"], original["data_quality"])
                self.assertEqual(result_from_engine, original)
                self.assertEqual(rows, original_rows)
                self.assertEqual(nonfinite_paths(result), [])
                json.dumps(result, allow_nan=False)

    def test_rejected_signal_never_consumes_cooldown_for_either_direction(self):
        rows = source()
        for bad in BAD:
            for direction in ("BULLISH CANDIDATE", "BEARISH CANDIDATE"):
                with self.subTest(bad=repr(bad), direction=direction):
                    rejected = fake(bad)
                    valid = snapshot(synthetic_rows(False))
                    valid["signal"] = direction
                    with patch.object(replay, "evaluate", side_effect=[rejected, valid]):
                        result = replay.replay_session(**rows)
                    control = snapshot(synthetic_rows(True))  # valid NO TRADE
                    with patch.object(replay, "evaluate", side_effect=[control, valid]):
                        comparison = replay.replay_session(**rows)
                    self.assertEqual(result["events"], comparison["events"])
                    self.assertEqual(len(result["events"]), 1)
                    self.assertEqual(result["events"][0]["known_at_et"],
                                     "2026-10-23 09:56:00")

    def test_valid_no_trade_snapshot_is_not_reclassified_or_mutated(self):
        value = snapshot(synthetic_rows(True))
        before = copy.deepcopy(value)
        with patch.object(replay, "evaluate", return_value=value):
            result = replay.replay_session(**source())
        self.assertEqual(result["snapshots"], [before, before])
        self.assertEqual(result["events"], [])
        self.assertEqual(value, before)
        self.assertNotIn("INVALID_SIGNAL", value["reasons"])

    def test_replay_and_study_aggregate_invalid_signal_without_crashing(self):
        sessions = []
        for day in ("2026-10-21", "2026-10-23"):
            item = source()
            item["session_open_et"] = day+" 09:30:00"
            item["session_close_et"] = day+" 16:00:00"
            for row in item["rows"]:
                for key in ("raw_timestamp", "interval_start_et", "interval_end_et", "available_at_et"):
                    row[key] = day+row[key][10:]
            sessions.append(item)
        before = copy.deepcopy(sessions)
        args = dict(train_through="2026-10-21", test_start="2026-10-23",
                    test_end="2026-10-23", freeze_id="H010-SYNTHETIC",
                    code_revision="H010-test-assembly")
        for bad in BAD:
            with self.subTest(bad=repr(bad)), patch.object(replay, "evaluate", return_value=fake(bad)):
                result = replay.study(sessions, **args)
                for bucket in ("train", "test"):
                    self.assertEqual(result[bucket]["events"], [])
                    self.assertEqual(result[bucket]["decision_counts"], {"NO TRADE":2})
                    self.assertEqual(result[bucket]["no_trade_reasons"]["INVALID_SIGNAL"], 2)
                self.assertEqual(nonfinite_paths(result), [])
                json.dumps(result, allow_nan=False)
        self.assertEqual(sessions, before)


if __name__ == "__main__":
    unittest.main()
