"""H-009 TEST ONLY. Synthetic consumer contracts; expected failures are evidence."""
import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from test_extreme_numeric_output import synthetic_rows, snapshot, nonfinite_paths

ENGINE_HEAD = "48e184c67168724b1449ac8c36d209d4a2d72892"
REPLAY_HEAD = "328135f2695543cde96bb434aaa07201c51c0582"
REPLAY_BLOB = "4eeaa8c1fdb595134096fa5ac13f52f8ecf82392"
ENGINE_BLOB = "8a4d091a24e2ea6f80e4d24b14dcebd400cf3586"
ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "tests" / "fixtures" / "h009" / "direction_validation.py"
SPEC = importlib.util.spec_from_file_location("h009_pinned_replay", FIXTURE)
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)


def session(extreme=True, day="2026-10-23"):
    rows = synthetic_rows(extreme)
    for row in rows:
        for key in ("raw_timestamp", "interval_start_et", "interval_end_et", "available_at_et"):
            row[key] = day + row[key][10:]
    return dict(rows=rows, symbol="SPY", session_open_et=day+" 09:30:00",
                session_close_et=day+" 16:00:00",
                interval_evidence={"status":"SYNTHETIC", "reference":"H009-no-provider-evidence"})


def assert_json(test, result):
    test.assertEqual(nonfinite_paths(result), [])
    test.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)


class H009ConsumerIntegrationTests(unittest.TestCase):
    def test_pinned_source_artifacts_are_unchanged(self):
        for path, expected in ((FIXTURE, REPLAY_BLOB), (ROOT/"direction_engine.py", ENGINE_BLOB)):
            raw = path.read_bytes().replace(b"\r\n", b"\n")
            actual = hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
            self.assertEqual(actual, expected, str(path))

    def test_real_overflow_replay_retains_rejection_and_creates_no_events(self):
        source = session()
        before = copy.deepcopy(source)
        result = replay.replay_session(**source)
        self.assertEqual(source, before)
        self.assertEqual(result["events"], [])
        last = result["snapshots"][-1]
        self.assertEqual(last["signal"], "NO TRADE")
        self.assertEqual(last["reasons"], ["VOLUME_RATIO_OVERFLOW"])
        self.assertIsNone(last["observations"]["volume_ratio"])
        self.assertEqual(last["data_quality"]["status"], "READY")
        self.assertTrue(last["observations"]["volume_confirmed"])
        assert_json(self, result)

    def test_real_synthetic_study_retains_reason_counts_and_zero_outcomes(self):
        sources = [session(day="2026-10-21"), session()]
        before = copy.deepcopy(sources)
        args = dict(train_through="2026-10-21", test_start="2026-10-23",
                    test_end="2026-10-23", freeze_id="H009-SYNTHETIC-NOT-RESEARCH-FREEZE",
                    code_revision=ENGINE_HEAD+"+"+REPLAY_HEAD)
        result = replay.study(sources, **args)
        self.assertEqual(result, replay.study(sources, **args))
        self.assertEqual(sources, before)
        for bucket in ("train", "test"):
            self.assertEqual(result[bucket]["events"], [])
            self.assertEqual(result[bucket]["valid_outcomes"], 0)
            self.assertEqual(result[bucket]["missing_outcomes"], 0)
            self.assertEqual(result[bucket]["no_trade_reasons"]["VOLUME_RATIO_OVERFLOW"], 1)
        assert_json(self, result)

    def two_decision_session(self):
        # Fake evaluator isolates routing/cooldown from feature dynamics.
        # Canonical timing and all prices remain synthetic.
        source = session(False)
        last = copy.deepcopy(source["rows"][-1])
        for key in ("raw_timestamp", "interval_start_et"):
            last[key] = "2026-10-23 09:55:00"
        for key in ("interval_end_et", "available_at_et"):
            last[key] = "2026-10-23 09:56:00"
        source["rows"] = [source["rows"][-1], last]
        return source

    def test_overflow_rejection_does_not_consume_next_candidate_cooldown(self):
        source = self.two_decision_session()
        rejected = snapshot(synthetic_rows(True))
        candidate = snapshot(synthetic_rows(False))
        self.assertEqual(candidate["signal"], "BULLISH CANDIDATE")
        before = copy.deepcopy(source)
        with patch.object(replay, "evaluate", side_effect=[rejected, candidate]):
            result = replay.replay_session(**source, horizon_minutes=3)
        control = copy.deepcopy(rejected)
        control["reasons"] = ["CONDITIONS_NOT_ALIGNED"]
        with patch.object(replay, "evaluate", side_effect=[control, candidate]):
            comparison = replay.replay_session(**source, horizon_minutes=3)
        self.assertEqual(source, before)
        self.assertEqual(result["events"], comparison["events"])
        self.assertEqual(len(result["events"]), 1)
        self.assertEqual(result["events"][0]["known_at_et"], "2026-10-23 09:56:00")
        self.assertEqual(result["events"][0]["signal"], "BULLISH CANDIDATE")
        # No forward price is fabricated: the valid candidate has a missing label.
        self.assertIsNone(result["events"][0]["directional_etf_move_pct"])
        assert_json(self, result)

    def test_unknown_signal_is_rejected_not_routed_as_bearish(self):
        source = self.two_decision_session()
        invalid = snapshot(synthetic_rows(False))
        invalid["signal"] = "UNKNOWN_H009_SYNTHETIC"
        with patch.object(replay, "evaluate", return_value=invalid):
            result = replay.replay_session(**source)
        self.assertEqual(result["events"], [],
                         "Unknown signal must not be admitted as a candidate or bearish event")

    def test_missing_signal_fails_closed_without_exception_or_event(self):
        source = self.two_decision_session()
        invalid = snapshot(synthetic_rows(False))
        del invalid["signal"]
        with patch.object(replay, "evaluate", return_value=invalid):
            try:
                result = replay.replay_session(**source)
            except (KeyError, TypeError, ValueError) as error:
                self.fail("Missing signal must fail closed explicitly, not crash: "+repr(error))
        self.assertEqual(result["events"], [])

    def test_both_known_candidate_enums_are_preserved_by_consumer(self):
        source = self.two_decision_session()
        for signal in ("BULLISH CANDIDATE", "BEARISH CANDIDATE"):
            with self.subTest(signal=signal):
                candidate = snapshot(synthetic_rows(False))
                candidate["signal"] = signal
                with patch.object(replay, "evaluate", return_value=candidate):
                    result = replay.replay_session(**source)
                self.assertEqual(len(result["events"]), 1)
                self.assertEqual(result["events"][0]["signal"], signal)
                assert_json(self, result)


if __name__ == "__main__":
    unittest.main()
