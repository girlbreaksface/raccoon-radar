"""Invented JSON stress fixtures; no option prices, packets, or execution model."""
import json
from contextlib import closing
from pathlib import Path
import tempfile
import unittest

from capture import Journal
from provisional_replay import replay
from test_provider_informed import decode


SESSIONS = ('2024-01-19', '2024-03-08', '2024-03-11',
            '2024-03-15', '2024-06-03', '2024-07-03')


class ZeroDollarTests(unittest.TestCase):
    def fixture(self, date, symbol, *, append_revision=True):
        temp = tempfile.TemporaryDirectory(prefix='synthetic-zero-dollar-')
        self.addCleanup(temp.cleanup)
        directory = Path(temp.name) / 'journal'
        clock = [1_000_000_000_000, 0]
        with closing(Journal(directory, {
            'fixture': 'SYNTHETIC_JSON_NOT_PROVIDER_PROTOBUF',
            'study_session': date, 'real_market_evidence': False,
        }, clock=lambda: tuple(clock))) as journal:
            rows = [dict(time=date + ' 10:00:00', openPrice=100,
                         highPrice=102, lowPrice=99, closePrice=101,
                         volume=10, turnover=1010,
                         fixture_quotes=None, fixture_chain=None,
                         fixture_feed='INVENTED_A', fixture_endpoint='fake-push'),
                    dict(time=date + ' 10:02:00', openPrice=100,
                         highPrice=102, lowPrice=99, closePrice=101,
                         volume=10, turnover=1010,
                         fixture_disruption='INVENTED_GAP_NOT_ACTUAL_HALT')]
            if append_revision:
                rows.append(dict(rows[0], closePrice=102,
                                 fixture_feed='INVENTED_B',
                                 fixture_endpoint='fake-history'))
            for row in rows:
                payload = json.dumps({'symbol': symbol, 'rows': [row]},
                                     sort_keys=True).encode()
                journal.append(symbol, (row['time'],), payload)
                clock[0] += 1_000_000_000
                clock[1] += 1_000_000_000
            journal.finish('SYNTHETIC_FIXTURE_COMPLETE')
        return directory, rows

    def cases(self):
        for date in SESSIONS:
            for symbol in ('US.SPY', 'US.QQQ'):
                yield date, symbol

    def test_missing_quotes_and_chain_stay_missing_in_all_twelve_cases(self):
        for date, symbol in self.cases():
            with self.subTest(date=date, symbol=symbol):
                directory, _ = self.fixture(date, symbol)
                view = replay(directory, decoder=decode)
                for row in (view['revisions'][0], view['revisions'][2]):
                    self.assertIsNone(row['source']['fixture_quotes'])
                    self.assertIsNone(row['source']['fixture_chain'])
                    self.assertNotIn('bid', row['source'])
                    self.assertNotIn('ask', row['source'])
                self.assertEqual(view['strategy_status'], 'DATA_BLOCKED')

    def test_gap_never_generates_a_bar_or_a_halt_claim(self):
        for date, symbol in self.cases():
            directory, rows = self.fixture(date, symbol)
            view = replay(directory, decoder=decode)
            self.assertEqual([g['source_label'] for g in view['groups']],
                             [rows[0]['time'], rows[1]['time']])
            self.assertEqual(view['revisions'][1]['source']['fixture_disruption'],
                             'INVENTED_GAP_NOT_ACTUAL_HALT')
            self.assertEqual(view['completeness'], 'NOT_ESTABLISHED')

    def test_delayed_revision_respects_receipt_boundary_not_old_event_label(self):
        directory, _ = self.fixture('2024-06-03', 'US.SPY')
        before = replay(directory, decoder=decode, cutoff_ns=1_001_999_999_999)
        after = replay(directory, decoder=decode, cutoff_ns=1_002_000_000_000)
        self.assertEqual(before['groups'][0]['last_observed']['source']['closePrice'], 101)
        self.assertEqual(after['groups'][0]['last_observed']['source']['closePrice'], 102)
        self.assertEqual(len(before['revisions']), 2)
        self.assertEqual(len(after['revisions']), 3)

    def test_appending_future_revision_preserves_selected_observations(self):
        first, _ = self.fixture('2024-03-11', 'US.QQQ', append_revision=False)
        extended, _ = self.fixture('2024-03-11', 'US.QQQ')
        a = replay(first, decoder=decode, sequence=2)
        b = replay(extended, decoder=decode, sequence=2)
        # Archive manifests/hashes are deliberately excluded: whole-seal validation
        # is not online causal processing. Compare the selected source observations.
        projection = lambda v: [(r['sequence'], r['source_label'], r['source'])
                                for r in v['revisions']]
        self.assertEqual(projection(a), projection(b))

    def test_raw_labels_never_gain_verified_mapping_across_dst_or_early_close(self):
        for date, symbol in self.cases():
            directory, rows = self.fixture(date, symbol)
            view = replay(directory, decoder=decode)
            self.assertEqual(view['boundary_semantics'], 'UNKNOWN')
            self.assertEqual([r['source_label'] for r in view['revisions']],
                             [r['time'] for r in rows])
            for row in view['revisions']:
                self.assertNotIn('interval_start', row)
                self.assertNotIn('interval_end', row)
                self.assertEqual(row['finality'], 'UNKNOWN')

    def test_conflicting_feed_provenance_is_retained_without_qualification(self):
        directory, rows = self.fixture('2024-03-15', 'US.SPY')
        view = replay(directory, decoder=decode)
        self.assertEqual([r['source'] for r in view['revisions']], rows)
        self.assertEqual(view['status'], 'PROVISIONAL')
        self.assertEqual(view['provider_accuracy'], 'NOT_ESTABLISHED')
        self.assertEqual(view['strategy_status'], 'DATA_BLOCKED')


if __name__ == '__main__':
    unittest.main()
