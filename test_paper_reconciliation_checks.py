import unittest
from paper_account_reconciliation import digest, encoded
from paper_reconciliation_checks import evidence, validate_evidence


class EvidenceTests(unittest.TestCase):
    def test_fixed_evidence_reproduces_and_never_enables_orders(self):
        report = evidence()
        self.assertEqual(encoded(report), encoded(evidence()))
        validate_evidence(report)
        self.assertEqual(len(report['scenarios']), 16)
        self.assertFalse(report['broker_verified'])
        self.assertEqual(report['scope'], 'SYNTHETIC_ONLY')
        for item in report['scenarios'].values():
            self.assertEqual(item['orders'], 'DISABLED')
            self.assertEqual(item['paper_execution'], 'HOLD')

    def test_rehash_cannot_hide_removed_case_or_changed_readiness(self):
        for change in ('case', 'readiness'):
            report = evidence()
            if change == 'case':
                del report['scenarios']['partial-fill']
            else:
                report['paper_execution'] = 'GO'
            report['evidence_hash'] = digest({k: v for k, v in report.items() if k != 'evidence_hash'})
            with self.assertRaises(ValueError):
                validate_evidence(report)

    def test_invalid_evidence_objects_fail_closed(self):
        for invalid in (None, [], {'evidence_hash': 'invalid'}):
            with self.assertRaises(ValueError):
                validate_evidence(invalid)
