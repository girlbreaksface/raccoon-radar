"""Issue #46 scenarios: invented JSON envelopes, never provider packet evidence.

The injected decoder exercises sealed receipt replay without SDK/schema loading.
Support's reported end label is NOT promoted to a verified interval mapping.
"""
import base64
import copy
import json
from pathlib import Path
import tempfile
import unittest

from capture import Journal, verify
from provisional_replay import replay
from receipt_quality import report
from revision_impact import analyze


def decode(payload):
    envelope = json.loads(payload)
    return envelope['symbol'], envelope['rows']


class ProviderInformedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-provider-informed-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = [1_000_000_000_000, 0]
        self.payloads = []
        self.directory = self.root / 'receipts'
        self.journal = Journal(self.directory, {
            'fixture': 'SYNTHETIC_JSON_NOT_PROVIDER_PROTOBUF',
            'source': 'issue-46-scenarios', 'provider_semantics_verified': False,
        }, clock=lambda: tuple(self.clock))
        self.addCleanup(self.journal.close)

    def add(self, label='2026-11-02 10:52:00', symbol='US.SPY',
            elapsed=0, **fields):
        self.clock[0] += elapsed
        self.clock[1] += elapsed
        row = dict(time=label, openPrice=100, highPrice=102, lowPrice=99,
                   closePrice=101, volume=10, turnover=1010)
        row.update(fields)
        payload = json.dumps({'symbol': symbol, 'rows': [row]},
                             sort_keys=True, allow_nan=False).encode()
        self.payloads.append(payload)
        self.journal.append(symbol, (label,), payload)

    def finish(self):
        self.journal.finish('SYNTHETIC_FIXTURE_COMPLETE')

    def view(self, **cutoffs):
        return replay(self.directory, decoder=decode, **cutoffs)

    def assert_blocked(self, view):
        for item in [view] + view['groups'] + view['revisions']:
            self.assertEqual((item['status'], item['finality'], item['strategy_status']),
                             ('PROVISIONAL', 'UNKNOWN', 'DATA_BLOCKED'))
        self.assertEqual(view['completeness'], 'NOT_ESTABLISHED')

    def test_reported_end_labels_stay_raw_at_open_close_and_early_close(self):
        labels = ('2026-11-02 09:31:00', '2026-11-02 16:00:00',
                  '2026-11-27 13:00:00')
        for symbol in ('US.SPY', 'US.QQQ'):
            for label in labels:
                self.add(label=label, symbol=symbol)
        self.finish()
        view = self.view()
        self.assertEqual([r['source_label'] for r in view['revisions']], list(labels)*2)
        self.assertEqual([r['source']['time'] for r in view['revisions']], list(labels)*2)
        self.assertEqual(view['boundary_semantics'], 'UNKNOWN')
        for row in view['revisions']:
            self.assertNotIn('interval_start', row)
            self.assertNotIn('interval_end', row)
        self.assert_blocked(view)

    def test_dst_adjacent_labels_are_not_silently_normalized(self):
        labels = ['2026-10-30 09:31:00', '2026-11-02 09:31:00',
                  '2026-11-01 01:30:00']
        for label in labels:
            self.add(label=label)
        self.finish()
        self.assertEqual([g['source_label'] for g in self.view()['groups']], labels)
        self.assert_blocked(self.view())

    def test_older_label_can_arrive_after_newer_and_revise_all_values(self):
        for symbol in ('US.SPY', 'US.QQQ'):
            self.add(symbol=symbol)
            self.add(label='2026-11-02 10:53:00', symbol=symbol)
            self.add(symbol=symbol, openPrice=101, highPrice=104, lowPrice=98,
                     closePrice=103, volume=7, turnover=721)
        self.finish()
        view = self.view()
        self.assertEqual([r['sequence'] for r in view['revisions']], list(range(1, 7)))
        for group in view['groups']:
            if group['source_label'].endswith('10:52:00'):
                self.assertEqual(len(group['history']), 2)
                self.assertEqual(group['last_observed']['source']['volume'], 7)
        impact = analyze(self.directory, before={'sequence': 0},
                         after={'sequence': 6}, decoder=decode)
        revisions = [r for r in impact['impacts'] if r['kind'] == 'REVISION']
        self.assertEqual(len(revisions), 2)
        for r in revisions:
            self.assertEqual({c['field'] for c in r['changes']},
                             {'openPrice', 'highPrice', 'lowPrice', 'closePrice',
                              'volume', 'turnover'})
        self.assert_blocked(view)

    def test_late_stale_values_are_last_observed_not_authoritative_truth(self):
        self.add(closePrice=101)
        self.add(closePrice=102, elapsed=1)
        self.add(closePrice=101, elapsed=1)
        self.finish()
        group = self.view()['groups'][0]
        self.assertEqual([r['source']['closePrice'] for r in group['history']], [101, 102, 101])
        self.assertEqual(group['last_observed']['sequence'], 3)
        self.assertEqual(group['last_observed']['source']['closePrice'], 101)
        self.assert_blocked(self.view())

    def test_receipt_cutoff_does_not_backdate_late_revision(self):
        self.add()
        self.add(label='2026-11-02 10:53:00', elapsed=1_000_000_000)
        self.add(closePrice=102, elapsed=2_000_000_000)
        self.finish()
        before = self.view(cutoff_ns=1_002_999_999_999)
        saved = copy.deepcopy(before)
        after = self.view(cutoff_ns=1_003_000_000_000)
        self.assertEqual(before['groups'][0]['last_observed']['source']['closePrice'], 101)
        self.assertEqual(after['groups'][0]['last_observed']['source']['closePrice'], 102)
        self.assertEqual(before, saved)
        self.assertEqual(before, self.view(cutoff_ns=1_002_999_999_999))
        self.assertEqual(self.view(sequence=2, cutoff_ns=1_003_000_000_000)['revisions'],
                         before['revisions'])

    def test_one_second_after_next_label_never_establishes_finality(self):
        self.add()
        self.add(label='2026-11-02 10:53:00', elapsed=1_000_000_000)
        self.add(label='2026-11-02 10:53:00', elapsed=1_000_000_000)
        self.add(closePrice=102, elapsed=1_000_000_000)
        self.finish()
        for cutoff in (1_002_000_000_000, 1_003_000_000_000, 10**30):
            self.assert_blocked(self.view(cutoff_ns=cutoff))

    def test_repeated_identical_observations_and_clean_seal_are_not_finality(self):
        for _ in range(3):
            self.add(elapsed=1_000_000_000)
        self.finish()
        self.assertEqual(len(verify(self.directory)), 3)
        quality = report(self.directory, decoder=decode)
        self.assertEqual(quality['groups'][0]['identical_transitions'], 2)
        self.assertEqual(quality['finality'], 'UNKNOWN')
        self.assertEqual(quality['completeness'], 'NOT_ESTABLISHED')
        self.assert_blocked(self.view(cutoff_ns=10**30))

    def test_payload_and_receipt_bytes_survive_views_unchanged(self):
        self.add(); self.add(closePrice=102, elapsed=1)
        self.finish()
        files = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        view = self.view()
        self.assertEqual([base64.b64decode(r['payload_b64']) for r in view['receipts']],
                         self.payloads)
        view['revisions'][0]['source']['time'] = 'caller mutation'
        self.assertEqual({p.name: p.read_bytes() for p in self.directory.iterdir()}, files)
        self.assertEqual(self.view()['revisions'][0]['source_label'], '2026-11-02 10:52:00')

    def test_feed_scope_and_adjustment_provenance_are_preserved_not_equated(self):
        # Test-only decoded metadata: not claimed to be actual protobuf fields.
        live = dict(fixture_feed='NASDAQ_ONLY', fixture_endpoint='Qot_UpdateKL',
                    fixture_rehab_type=1, fixture_anchor='2026-11-02')
        history = dict(fixture_feed='CONSOLIDATED', fixture_endpoint='history',
                       fixture_rehab_type=1, fixture_anchor='2026-11-03')
        self.add(**live)
        self.add(**history, closePrice=102, elapsed=1)
        self.finish()
        result = analyze(self.directory, before={'sequence': 1},
                         after={'sequence': 2}, decoder=decode)
        change = result['impacts'][0]
        self.assertEqual(change['kind'], 'REVISION')  # observation delta only
        self.assertEqual(change['previous']['source']['fixture_feed'], 'NASDAQ_ONLY')
        self.assertEqual(change['observation']['source']['fixture_feed'], 'CONSOLIDATED')
        self.assertEqual({c['field'] for c in change['changes']},
                         {'closePrice', 'fixture_feed', 'fixture_endpoint', 'fixture_anchor'})
        self.assertEqual(result['adjustment_factors'], 'UNKNOWN')
        self.assertEqual(result['provider_accuracy'], 'NOT_ESTABLISHED')
        self.assertEqual(result['strategy_status'], 'DATA_BLOCKED')

    def test_matching_rehab_enum_does_not_verify_factors_or_feed_equivalence(self):
        for anchor in ('2026-11-02', '2026-11-03'):
            self.add(fixture_rehab_type=1, fixture_anchor=anchor)
        self.finish()
        view = self.view()
        self.assertEqual([r['source']['fixture_anchor'] for r in view['revisions']],
                         ['2026-11-02', '2026-11-03'])
        self.assertEqual(view['adjustment_factors'], 'UNKNOWN')
        self.assertEqual(view['provider_accuracy'], 'NOT_ESTABLISHED')
        self.assert_blocked(view)

    def test_report_and_replay_are_deterministic_strict_json(self):
        self.add(); self.add(closePrice=102, elapsed=1)
        self.finish()
        for operation in (self.view, lambda: report(self.directory, decoder=decode)):
            first = operation()
            self.assertEqual(first, operation())
            self.assertEqual(json.loads(json.dumps(first, allow_nan=False)), first)


if __name__ == '__main__':
    unittest.main()
