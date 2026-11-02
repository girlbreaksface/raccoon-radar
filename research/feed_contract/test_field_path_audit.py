"""Synthetic sealed evidence: endpoint equality must not hide field excursions."""
import json
import unittest
from unittest.mock import patch

import test_provisional_replay as fixtures
from field_path_audit import audit, main


class FieldPathTests(unittest.TestCase):
    setUp = fixtures.ReplayTests.setUp
    add = fixtures.ReplayTests.add

    def view(self, before=1, after=99, decoder=fixtures.synthetic_decode):
        return audit(self.directory, before={'sequence': before},
                     after={'sequence': after}, decoder=decoder)

    def field(self, result, name='openPrice', group=0):
        return next(f for f in result['paths'][group]['fields'] if f['field'] == name)

    def test_endpoint_equality_exposes_multiple_excursions_and_repeats(self):
        for price in (696.88, 696.9, 696.9, 696.88, 696.91, 696.88):
            self.add(price=price)
        self.j.finish('RUN_LIMIT')
        result = self.view()
        field = self.field(result)
        self.assertEqual(field['anchor'], field['last_observed'])
        self.assertEqual(field['classification'], 'RETURNED_TO_ANCHOR')
        self.assertEqual((field['change_count'], field['return_count']), (4, 2))
        self.assertEqual([c['observation']['sequence'] for c in field['changes']], [2, 4, 5, 6])
        self.assertEqual(field['changes'][1]['previous'], dict(sequence=3, row_index=0))
        self.assertEqual(result['counts']['RETURNED_TO_ANCHOR'], 2)
        self.assertEqual(result, self.view())
        # Every reference resolves to the exact embedded receipt/row evidence.
        rows = {(r['sequence'], r['row_index']): r for r in result['evidence']['after']['observations']}
        for change in field['changes']:
            for ref, state in (('previous', 'before'), ('observation', 'after')):
                row = rows[tuple(change[ref][k] for k in ('sequence', 'row_index'))]
                self.assertEqual(row['source']['openPrice'], change[state]['value'])
                self.assertTrue(row['receipt']['payload_b64'])

    def test_net_change_unchanged_and_unobserved_baseline_are_distinct(self):
        self.add(); self.add(price=696.9); self.add(label='earlier'); self.add(symbol='US.SPY')
        self.j.finish('RUN_LIMIT')
        result = self.view()
        self.assertEqual(self.field(result)['classification'], 'NET_CHANGED')
        self.assertEqual(self.field(result, 'closePrice')['classification'], 'UNCHANGED')
        self.assertEqual([(p['symbol'], p['source_label'], p['baseline_available']) for p in result['paths']],
                         [('US.QQQ', '2026-11-02 10:52:00', True),
                          ('US.QQQ', 'earlier', False), ('US.SPY', '2026-11-02 10:52:00', False)])
        self.assertEqual(self.field(result, group=1)['change_count'], 0)
        self.assertFalse(self.view(0)['paths'][0]['baseline_available'])
        for path in self.view(2, 2)['paths']:
            self.assertEqual(path['observations_after_baseline'], 0)
            self.assertTrue(all(f['classification'] == 'UNCHANGED' for f in path['fields']))
        self.assertEqual(self.view(0, 0)['paths'], [])

    def test_presence_null_removal_and_same_receipt_rows(self):
        self.add(labels=['same', 'same', 'same', 'same'])
        self.j.finish('RUN_LIMIT')
        def decode(payload):
            symbol, rows = fixtures.synthetic_decode(payload)
            rows[1]['optional'] = None
            rows[2]['optional'] = 0
            return symbol, rows
        result = self.view(0, decoder=decode)
        field = self.field(result, 'optional')
        self.assertEqual(field['classification'], 'RETURNED_TO_ANCHOR')
        self.assertEqual(field['change_count'], 3)
        self.assertEqual([c['observation']['row_index'] for c in field['changes']], [1, 2, 3])
        self.assertEqual(field['changes'][0]['before'], dict(present=False, value=None))
        self.assertEqual(field['changes'][0]['after'], dict(present=True, value=None))
        self.assertFalse(result['paths'][0]['baseline_available'])

    def test_baseline_excludes_earlier_excursions_and_detaches_evidence(self):
        self.add(); self.add(price=696.9); self.add(price=696.88); self.add()
        self.j.finish('RUN_LIMIT')
        result = self.view(3)
        self.assertEqual(self.field(result)['change_count'], 0)
        self.assertEqual(result['paths'][0]['anchor'], dict(sequence=3, row_index=0))
        self.field(result)['anchor']['value'] = 0
        self.assertEqual(result['evidence']['before']['groups'][0]['last_observed']['source']['openPrice'], 696.88)

    def test_cutoffs_safety_provenance_and_full_capture_failure(self):
        self.add(); self.add(price=696.9); self.j.finish('RUN_LIMIT')
        result = self.view()
        timed = audit(self.directory, before={'cutoff_ns': 1_000_000_000_000},
                      after={'sequence': 2}, decoder=fixtures.synthetic_decode)
        self.assertEqual(result['paths'], timed['paths'])
        for item in [result] + result['paths']:
            self.assertEqual((item['status'], item['finality'], item['strategy_status']),
                             ('PROVISIONAL', 'UNKNOWN', 'DATA_BLOCKED'))
        self.assertEqual(result['completeness'], 'NOT_ESTABLISHED')
        self.assertEqual(result['boundary_semantics'], 'UNKNOWN')
        self.assertEqual(len(result['provenance']['field_path_source_sha256']), 64)
        with self.assertRaises(ValueError): self.view(2, 1)
        calls = []
        def bad(payload):
            calls.append(1)
            if len(calls) == 2: raise ValueError('late decode failure')
            return fixtures.synthetic_decode(payload)
        with self.assertRaisesRegex(ValueError, 'late decode'):
            self.view(0, 0, decoder=bad)
        journal = self.directory / 'receipts.jsonl'
        journal.write_bytes(journal.read_bytes().replace(b'US.QQQ', b'US.SPY'))
        with self.assertRaises(ValueError): self.view(0, 0)

    def test_cli_exclusive_and_no_output_on_failure(self):
        self.add(); self.j.finish('RUN_LIMIT')
        output = self.directory.parent / 'audit.json'
        args = [str(self.directory), '--before-sequence', '0', '--after-sequence', '1', '--output', str(output)]
        with patch('provisional_replay.protobuf_decoder', return_value=(fixtures.synthetic_decode, {})):
            self.assertEqual(main(args), 0)
            original = output.read_bytes()
            self.assertEqual(json.loads(original)['mode'], 'OFFLINE_FIELD_PATH_AUDIT')
            self.assertEqual(main(args), 1)
            self.assertEqual(output.read_bytes(), original)
            missing = self.directory.parent / 'missing.json'
            with patch('field_path_audit.audit', side_effect=ValueError('blocked')):
                self.assertEqual(main(args[:-1] + [str(missing)]), 1)
            self.assertFalse(missing.exists())
