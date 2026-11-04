import unittest
from historical_options_replay import digest, encoded, replay
from historical_replay_checks import assess, evidence, validate_evidence
from test_historical_options_replay import fixture


class ReadinessTests(unittest.TestCase):
    def test_rehearsal_determinism_and_blocked_paths_remain_visible(self):
        report = evidence()
        self.assertEqual(encoded(report), encoded(evidence()))
        validate_evidence(report)
        self.assertEqual(len(report['scenarios']), 10)
        assessment = report['assessment']
        self.assertEqual(assessment['variant_rows'], {'CLOSED': 12, 'UNRESOLVED': 16, 'REJECTED': 12})
        self.assertEqual(assessment['quote_path_gate'], 'BLOCKED_UNRESOLVED')
        self.assertEqual(assessment['paper_execution'], 'HOLD')
        self.assertEqual(assessment['orders'], 'DISABLED')

    def test_hash_repair_cannot_hide_forged_profit(self):
        result = replay(fixture())
        result['trades'][0]['net'] = '999'
        result['run_hash'] = digest({k: v for k, v in result.items() if k != 'run_hash'})
        with self.assertRaises(ValueError):
            assess([result])

    def test_verified_label_cannot_release_any_paper_gate(self):
        data = fixture()
        data['quality'] = 'VERIFIED_QUOTES'
        assessment = assess([replay(data)])
        self.assertEqual(assessment['evidence_integrity'], 'PASS')
        self.assertEqual(assessment['empirical_validation'], 'NOT_ESTABLISHED')
        self.assertEqual(assessment['paper_execution'], 'HOLD')
        self.assertEqual(assessment['live_execution'], 'NO-GO')
        self.assertTrue(all(g['status'] == 'HOLD' for g in assessment['gates']))

    def test_missing_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            assess([])
        for invalid in (None, [], 'PASS'):
            with self.assertRaises(ValueError):
                validate_evidence(invalid)

    def test_missing_scenario_cannot_be_hidden_by_rehashing(self):
        report = evidence()
        del report['scenarios']['invalid-path']
        report['evidence_hash'] = digest({k: v for k, v in report.items() if k != 'evidence_hash'})
        with self.assertRaises(ValueError):
            validate_evidence(report)

    def test_forged_readiness_is_rejected(self):
        report = evidence()
        report['assessment']['paper_execution'] = 'GO'
        with self.assertRaises(ValueError):
            validate_evidence(report)
        report['evidence_hash'] = digest({k: v for k, v in report.items() if k != 'evidence_hash'})
        with self.assertRaises(ValueError):
            validate_evidence(report)
