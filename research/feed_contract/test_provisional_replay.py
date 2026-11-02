"""Synthetic receipt fixtures; no SDK, provider, databases or network required."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from capture import Journal
from provisional_replay import replay, main


def synthetic_decode(payload):
    value = json.loads(payload)
    return value['symbol'], value['rows']


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-replay-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / 'capture'
        self.clock = [1_000_000_000_000, 0]
        self.j = Journal(self.directory, {'fixture': 'SYNTHETIC'},
                         clock=lambda: tuple(self.clock))
        self.addCleanup(self.j.close)

    def add(self, symbol='US.QQQ', label='2026-11-02 10:52:00', price=696.88,
            labels=None):
        rows = [dict(time=l, openPrice=price, lowPrice=price,
                     highPrice=697.0, closePrice=697.0, volume=1, turnover=697.0)
                for l in (labels or [label])]
        self.j.append(symbol, tuple(r['time'] for r in rows),
                      json.dumps(dict(symbol=symbol, rows=rows)).encode())
        self.clock[0] += 1
        self.clock[1] += 1

    def view(self, **kwargs):
        return replay(self.directory, decoder=synthetic_decode, **kwargs)

    def test_revisions_repeats_and_last_observed(self):
        self.add(); self.add(price=696.9054); self.add(price=696.9054)
        self.j.finish('RUN_LIMIT')
        result = self.view()
        group = result['groups'][0]
        self.assertEqual([r['source']['openPrice'] for r in group['history']],
                         [696.88, 696.9054, 696.9054])
        self.assertEqual(group['last_observed']['sequence'], 3)
        self.assertEqual(len(result['receipts']), 3)
        self.assertTrue(all(r['receipt']['payload_b64'] for r in result['revisions']))
        group['last_observed']['source']['openPrice'] = 0
        self.assertEqual(group['history'][-1]['source']['openPrice'], 696.9054)

    def test_receipt_order_not_label_or_symbol_sort(self):
        self.add(label='later'); self.add(symbol='US.SPY', label='earlier')
        self.add(label='earlier'); self.add(label='later', price=695)
        self.j.finish('RUN_LIMIT')
        result = self.view()
        self.assertEqual([r['sequence'] for r in result['revisions']], [1, 2, 3, 4])
        self.assertEqual([(g['symbol'], g['source_label']) for g in result['groups']],
                         [('US.QQQ', 'later'), ('US.SPY', 'earlier'), ('US.QQQ', 'earlier')])
        self.assertEqual(result['groups'][0]['last_observed']['sequence'], 4)

    def test_inclusive_asof_and_intersection(self):
        self.add(); self.add(price=696.9054); self.add(label='next')
        self.j.finish('RUN_LIMIT')
        self.assertEqual(self.view(sequence=0)['groups'], [])
        for kwargs, expected in [({'sequence': 1}, [1]),
                                 ({'cutoff_ns': 1_000_000_000_001}, [1, 2]),
                                 ({'sequence': 2, 'cutoff_ns': 1_000_000_000_000}, [1]),
                                 ({'sequence': 999}, [1, 2, 3])]:
            self.assertEqual([r['sequence'] for r in self.view(**kwargs)['revisions']], expected)
        for value in (-1, True, 1.2):
            with self.assertRaises(ValueError): self.view(sequence=value)

    def test_integrity_failure_after_cutoff_returns_nothing(self):
        self.add(); self.add(); self.j.finish('RUN_LIMIT')
        p = self.directory / 'receipts.jsonl'
        lines = p.read_bytes().splitlines(keepends=True)
        lines[1] = lines[1].replace(b'US.QQQ', b'US.SPY')
        p.write_bytes(b''.join(lines))
        with self.assertRaises(ValueError): self.view(sequence=1)

    def test_decode_failure_after_cutoff_also_blocks(self):
        self.add(); self.add(); self.j.finish('RUN_LIMIT')
        calls = []
        def decode(payload):
            calls.append(1)
            if len(calls) == 2: raise ValueError('bad later payload')
            return synthetic_decode(payload)
        with self.assertRaisesRegex(ValueError, 'bad later'):
            replay(self.directory, sequence=1, decoder=decode)

    def test_boundary_ambiguity_and_never_promote(self):
        self.add(label='2026-11-02 10:52:00')
        self.add(label='2026-11-02 10:53:00')
        self.j.finish('RUN_LIMIT')
        for seq in (1, 2, 999999):
            view = self.view(sequence=seq)
            self.assertEqual(view['boundary_semantics'], 'UNKNOWN')
            for item in [view] + view['groups'] + view['revisions']:
                self.assertEqual((item['status'], item['finality'], item['strategy_status']),
                                 ('PROVISIONAL', 'UNKNOWN', 'DATA_BLOCKED'))
            self.assertEqual(view['groups'][0]['source_label'], '2026-11-02 10:52:00')
            self.assertEqual(view['groups'][0]['last_observed']['source']['time'],
                             '2026-11-02 10:52:00')

    def test_multirow_ties_preserve_wire_order(self):
        self.add(labels=['same', 'same']); self.j.finish('RUN_LIMIT')
        self.assertEqual([r['row_index'] for r in self.view()['revisions']], [0, 1])
        self.assertEqual(self.view()['groups'][0]['last_observed']['row_index'], 1)

    def test_mismatch_blocks(self):
        self.add(); self.j.finish('RUN_LIMIT')
        def bad(payload):
            _, rows = synthetic_decode(payload)
            return 'US.SPY', rows
        with self.assertRaises(ValueError): replay(self.directory, decoder=bad)

    def test_output_exclusive_and_failure_no_export(self):
        self.add(); self.j.finish('RUN_LIMIT')
        out = Path(self.temp.name) / 'view.json'
        with patch('provisional_replay.protobuf_decoder', return_value=(synthetic_decode, {})):
            self.assertEqual(main([str(self.directory), '--output', str(out)]), 0)
            raw = out.read_bytes()
            self.assertEqual(main([str(self.directory), '--output', str(out)]), 1)
            self.assertEqual(out.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
