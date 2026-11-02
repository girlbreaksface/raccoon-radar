"""Synthetic sealed-journal revision impact regressions."""
import test_provisional_replay as fixtures
from revision_impact import analyze


class ImpactTests(fixtures.ReplayTests):
    def impact(self, before=1, after=99):
        return analyze(self.directory, before={'sequence': before},
                       after={'sequence': after}, decoder=fixtures.synthetic_decode)

    def test_impact_transitions(self):
        self.add(); self.add(price=696.9054); self.add(price=696.9054)
        self.add(label='earlier'); self.add(price=696.88)
        self.j.finish('RUN_LIMIT')
        result = self.impact()
        self.assertEqual(result, self.impact())
        self.assertEqual([r['kind'] for r in result['impacts']],
                         ['REVISION', 'EXACT_REPEAT', 'FIRST_OBSERVATION', 'REVISION'])
        self.assertEqual([c['field'] for c in result['impacts'][0]['changes']], ['lowPrice', 'openPrice'])
        self.assertEqual(len(result['after']['observations']), 5)
        self.assertEqual(len(result['after']['groups'][0]['history']), 4)
        result['after']['groups'][0]['history'][0]['source']['openPrice'] = 0
        self.assertEqual(result['before']['observations'][0]['source']['openPrice'], 696.88)

    def test_impact_cutoffs(self):
        self.add(labels=['same', 'same']); self.add(price=696.9054)
        self.j.finish('RUN_LIMIT')
        result = self.impact(0, 1)
        self.assertEqual([r['kind'] for r in result['impacts']], ['FIRST_OBSERVATION', 'EXACT_REPEAT'])
        self.assertEqual(result['after']['groups'][0]['last_observed']['row_index'], 1)
        self.assertEqual(self.impact(1, 1)['impacts'], [])
        timed = analyze(self.directory, before={'sequence': 0},
                        after={'cutoff_ns': 1_000_000_000_000, 'sequence': 2}, decoder=fixtures.synthetic_decode)
        self.assertEqual(timed['after']['observations'], result['after']['observations'])
        for cutoff in ({}, {'sequence': True}, {'sequence': -1}, {'bad': 1}, {'cutoff_ns': 1.2}):
            with self.assertRaises(ValueError):
                analyze(self.directory, before=cutoff, after={'sequence': 2}, decoder=fixtures.synthetic_decode)
        with self.assertRaises(ValueError): self.impact(2, 1)

    def test_impact_presence_and_fail_closed(self):
        self.add(); self.add(); self.j.finish('RUN_LIMIT')
        calls = []
        def decode(payload):
            symbol, rows = fixtures.synthetic_decode(payload)
            if not calls: rows[0]['optional'] = None
            calls.append(1)
            return symbol, rows
        result = analyze(self.directory, before={'sequence': 1}, after={'sequence': 2}, decoder=decode)
        self.assertEqual(result['impacts'][0]['changes'], [dict(field='optional', before_present=True,
                         after_present=False, before=None, after=None)])
        def fail(payload):
            raise ValueError('decode blocked')
        with self.assertRaises(ValueError):
            analyze(self.directory, before={'sequence': 0}, after={'sequence': 0}, decoder=fail)
        journal = self.directory / 'receipts.jsonl'
        journal.write_bytes(journal.read_bytes().replace(b'US.QQQ', b'US.SPY'))
        with self.assertRaises(ValueError): self.impact(0, 0)

    def test_impact_cli_exclusive_and_no_partial_export(self):
        from unittest.mock import patch
        from revision_impact import main
        self.add(); self.j.finish('RUN_LIMIT')
        output = self.directory.parent / 'impact.json'
        args = [str(self.directory), '--before-sequence', '0', '--after-sequence', '1', '--output', str(output)]
        with patch('provisional_replay.protobuf_decoder', return_value=(fixtures.synthetic_decode, {})):
            self.assertEqual(main(args), 0)
            original = output.read_bytes()
            self.assertEqual(main(args), 1)
            self.assertEqual(output.read_bytes(), original)
            missing = self.directory.parent / 'missing.json'
            with patch('revision_impact.analyze', side_effect=ValueError('blocked')):
                self.assertEqual(main(args[:-1] + [str(missing)]), 1)
                self.assertFalse(missing.exists())

    def test_impact_safety_flags(self):
        self.add(); self.add(label='later'); self.j.finish('RUN_LIMIT')
        result = self.impact()
        for item in [result, result['before'], result['after']] + result['impacts'] + result['after']['groups'] + result['after']['observations']:
            self.assertEqual((item['status'], item['finality'], item['strategy_status']),
                             ('PROVISIONAL', 'UNKNOWN', 'DATA_BLOCKED'))
        self.assertEqual(result['boundary_semantics'], 'UNKNOWN')
        self.assertEqual(result['completeness'], 'NOT_ESTABLISHED')
