"""Chronological event-study contracts; all data are explicitly synthetic."""
import copy
import unittest
from datetime import datetime, timedelta

from direction_validation import replay_session, study
from test_direction_engine import candles, EVIDENCE


def session(day="2026-10-23", symbol="SPY", count=32):
    rows = candles(count=count,day=day,symbol=symbol)
    rows[24]["volume"] = 200
    return dict(symbol=symbol,session_open_et=day+" 09:30:00",
                session_close_et=day+" 16:00:00",interval_evidence=EVIDENCE,rows=rows)


class DirectionValidationTests(unittest.TestCase):
    def test_outcome_uses_next_open_and_full_horizon_not_event_close(self):
        source = session()
        source["rows"][25]["open"] = 124.5
        source["rows"][25]["low"] = 124.25
        result = replay_session(**source,horizon_minutes=3)
        event = next(e for e in result["events"] if e["known_at_et"].endswith("09:55:00"))
        self.assertEqual(event["entry_assumed_at_et"],"2026-10-23 09:55:00")
        self.assertEqual(event["exit_interval_end_et"],"2026-10-23 09:58:00")
        self.assertAlmostEqual(event["directional_etf_move_pct"],(127/124.5-1)*100)

    def test_missing_or_invalid_forward_minutes_never_bridged(self):
        for mode in ("missing","invalid","duplicate"):
            with self.subTest(mode=mode):
                source = session()
                if mode == "missing": source["rows"].pop(26)
                elif mode == "invalid": source["rows"][26]["low"] = 200
                else: source["rows"].insert(27,copy.deepcopy(source["rows"][26]))
                result = replay_session(**source)
                event = next(e for e in result["events"] if e["known_at_et"].endswith("09:55:00"))
                self.assertIsNone(event["directional_etf_move_pct"])
                self.assertIsNotNone(event["outcome_missing_reason"])

    def test_future_mutation_cannot_change_past_classifications(self):
        source = session()
        first = replay_session(**source)
        changed = copy.deepcopy(source)
        for row in changed["rows"][26:]:
            row.update(open=500,high=501,low=499,close=500,volume=5000)
        second = replay_session(**changed)
        before = lambda r: [s for s in r["snapshots"] if s["as_of_et"] <= "2026-10-23 09:55:00"]
        self.assertEqual(before(first),before(second))

    def test_no_overnight_or_silently_skipped_entry(self):
        source = session(count=25)
        event = replay_session(**source)["events"][0]
        self.assertIsNone(event["directional_etf_move_pct"])
        self.assertEqual(event["outcome_missing_reason"],"MISSING_ENTRY_BAR")
        source = session()
        source["rows"].pop(25)
        event = replay_session(**source)["events"][0]
        self.assertEqual(event["outcome_missing_reason"],"MISSING_ENTRY_BAR")

    def test_delayed_information_never_uses_an_earlier_open(self):
        source = session()
        source["rows"][24]["available_at_et"] = "2026-10-23 09:55:30"
        result = replay_session(**source)
        event = next(e for e in result["events"] if e["known_at_et"].endswith("09:55:30"))
        self.assertEqual(event["entry_assumed_at_et"],"2026-10-23 09:56:00")

    def test_chronological_dates_shared_across_spy_qqq_and_embargo_excluded(self):
        sessions = [session("2026-10-21"),session("2026-10-21","QQQ"),
                    session("2026-10-22"),session("2026-10-23"),session("2026-10-23","QQQ")]
        result = study(sessions,train_through="2026-10-21",test_start="2026-10-23",
                       test_end="2026-10-23",freeze_id="synthetic-freeze",code_revision="synthetic-revision")
        self.assertEqual(result["manifest"]["train_dates"],["2026-10-21"])
        self.assertEqual(result["manifest"]["test_dates"],["2026-10-23"])
        self.assertEqual(result["manifest"]["excluded_dates"],["2026-10-22"])
        self.assertTrue(all(e["session"]=="2026-10-21" for e in result["train"]["events"]))
        self.assertTrue(all(e["session"]=="2026-10-23" for e in result["test"]["events"]))
        self.assertEqual(result["manifest"]["prior_inspection"],"UNKNOWN")
        self.assertEqual(result["manifest"]["evaluation_status"],"RETROSPECTIVE_CHRONOLOGICAL")

    def test_manifest_determinism_input_preservation_and_missing_counts(self):
        sessions = [session("2026-10-21"),session("2026-10-23",count=25)]
        before = copy.deepcopy(sessions)
        args = dict(train_through="2026-10-21",test_start="2026-10-23",test_end="2026-10-23",
                    freeze_id="synthetic",code_revision="synthetic")
        first, second = study(sessions,**args), study(sessions,**args)
        self.assertEqual(first,second)
        self.assertEqual(sessions,before)
        self.assertEqual(len(first["manifest"]["dataset_sha256"]),64)
        self.assertEqual(first["test"]["missing_outcomes"],1)
        self.assertEqual(first["test"]["valid_outcomes"],0)

    def test_invalid_splits_duplicate_sessions_and_unfrozen_config_are_rejected(self):
        sessions = [session("2026-10-21"),session("2026-10-23")]
        args = dict(train_through="2026-10-21",test_start="2026-10-23",test_end="2026-10-23",
                    freeze_id="synthetic",code_revision="synthetic")
        for changes in ({"test_start":"2026-10-21"},{"freeze_id":""},{"horizon_minutes":0}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                study(sessions,**{**args,**changes})
        with self.assertRaises(ValueError):
            study(sessions+[copy.deepcopy(sessions[0])],**args)
        with self.assertRaises(ValueError):
            study([session("2026-10-23")],**args)

    def test_train_labels_must_be_available_before_training_cutoff(self):
        train, test = session("2026-10-21"), session("2026-10-23")
        train["rows"][26]["available_at_et"] = "2026-10-23 09:30:00"
        result = study([train,test],train_through="2026-10-21",test_start="2026-10-23",
            test_end="2026-10-23",freeze_id="synthetic",code_revision="synthetic")
        event = next(e for e in result["train"]["events"] if e["known_at_et"].endswith("09:55:00"))
        self.assertIsNone(event["directional_etf_move_pct"])
        self.assertEqual(event["outcome_missing_reason"],"INVALID_OR_UNAVAILABLE_OUTCOME_BAR")

    def test_replay_never_evaluates_information_after_its_cutoff(self):
        result = replay_session(**session(),outcome_as_of_et="2026-10-23 09:56:00")
        self.assertTrue(all(s["as_of_et"] <= "2026-10-23 09:56:00" for s in result["snapshots"]))

    def test_empty_sessions_alias_duplicates_and_false_freeze_metadata_rejected(self):
        args = dict(train_through="2026-10-21",test_start="2026-10-23",test_end="2026-10-23",
                    freeze_id="synthetic",code_revision="synthetic")
        first, second = session("2026-10-21"), session("2026-10-23")
        alias = copy.deepcopy(first)
        alias["symbol"] = "US.SPY"
        with self.assertRaises(ValueError):
            study([first,second,alias],**args)
        first["rows"] = []
        with self.assertRaises(ValueError):
            study([first,second],**args)
        with self.assertRaises(ValueError):
            study([session("2026-10-21"),second],**{**args,"freeze_id":True})

    def test_greedy_entry_cooldown_does_not_depend_on_outcome_value(self):
        source = session(count=35)
        for row in source["rows"][21:]: row["volume"] = 1000
        result = replay_session(**source,horizon_minutes=3)
        times = [datetime.fromisoformat(e["entry_assumed_at_et"]) for e in result["events"]]
        self.assertTrue(all(b-a>=timedelta(minutes=3) for a,b in zip(times,times[1:])))
        self.assertGreaterEqual(len(times),2)


if __name__ == "__main__":
    unittest.main()
