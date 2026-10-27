"""Availability/revision leakage probes for independent technical review."""
import copy
import unittest
from direction_validation import replay_session, study
from test_direction_validation import session


class DirectionAvailabilityReviewTests(unittest.TestCase):
    def test_revision_after_replay_cutoff_changes_neither_features_nor_labels(self):
        source = session()
        baseline = replay_session(**source)
        changed = copy.deepcopy(source)
        revision = dict(changed["rows"][26],available_at_et="2026-10-26 09:30:00",
                        open=126,high=130,low=125,close=129)
        changed["rows"].append(revision)
        before = copy.deepcopy(changed)
        self.assertEqual(replay_session(**changed),baseline)
        self.assertEqual(changed,before)

    def test_future_unavailable_interval_metadata_is_not_parsed(self):
        source = session()
        baseline = replay_session(**source)
        source["rows"].append(dict(source["rows"][0],
            available_at_et="2026-10-26 09:30:00",interval_start_et="unavailable-invalid"))
        self.assertEqual(replay_session(**source),baseline)

    def test_train_outcomes_ignore_revisions_first_available_during_holdout(self):
        train, test = session("2026-10-21"), session("2026-10-23")
        args = dict(train_through="2026-10-21",test_start="2026-10-23",
                    test_end="2026-10-23",freeze_id="synthetic-review",code_revision="synthetic")
        baseline = study([train,test],**args)
        train["rows"].append(dict(train["rows"][26],
            available_at_et="2026-10-23 09:30:00",open=126,high=130,low=125,close=129))
        revised = study([train,test],**args)
        self.assertEqual(revised["train"],baseline["train"])
        self.assertNotEqual(revised["manifest"]["dataset_sha256"],
                            baseline["manifest"]["dataset_sha256"])

    def test_test_price_changes_cannot_change_train_result(self):
        train, test = session("2026-10-21"), session("2026-10-23")
        args = dict(train_through="2026-10-21",test_start="2026-10-23",
                    test_end="2026-10-23",freeze_id="synthetic-review",code_revision="synthetic")
        baseline = study([train,test],**args)
        for row in test["rows"]:
            row.update(open=500,high=501,low=499,close=500,volume=999)
        self.assertEqual(study([train,test],**args)["train"],baseline["train"])

    def test_inspection_declarations_never_upgrade_to_untouched_holdout(self):
        args = dict(train_through="2026-10-21",test_start="2026-10-23",
                    test_end="2026-10-23",freeze_id="synthetic-review",code_revision="synthetic")
        for status in ("UNKNOWN","PREVIOUSLY_VIEWED","DECLARED_NOT_VIEWED"):
            with self.subTest(status=status):
                result = study([session("2026-10-21"),session("2026-10-23")],
                               prior_inspection=status,**args)
                self.assertEqual(result["manifest"]["evaluation_status"],
                                 "RETROSPECTIVE_CHRONOLOGICAL")
                self.assertEqual(result["manifest"]["prior_inspection"],status)


if __name__ == "__main__":
    unittest.main()
