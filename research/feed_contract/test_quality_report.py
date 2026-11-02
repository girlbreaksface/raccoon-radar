"""Synthetic offline quality and independent replay review regressions."""
import json
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

import test_provisional_replay as fixtures
from receipt_quality import report, main


class QualityTests(unittest.TestCase):
    setUp = fixtures.ReplayTests.setUp
    add = fixtures.ReplayTests.add
    view = fixtures.ReplayTests.view
    def quality(self, **kwargs):
        from test_provisional_replay import synthetic_decode
        return report(self.directory, decoder=synthetic_decode, **kwargs)

    def test_changes_repeats_and_coverage(self):
        self.add(); self.add(price=696.9054); self.add(price=696.9054)
        self.j.finish('RUN_LIMIT')
        q = self.quality()
        g = q['groups'][0]
        self.assertEqual((g['observations'], g['changed_transitions'], g['identical_transitions']), (3, 1, 1))
        self.assertEqual(g['changed_fields'], {'lowPrice': 1, 'openPrice': 1})
        self.assertEqual(q['symbols'][0]['max_interreceipt_mono_ns'], 1)
        self.assertEqual(q['symbols'][0]['observation_span_mono_ns'], 2)
        self.assertEqual(q['completeness'], 'NOT_ESTABLISHED')
        self.assertEqual(self.quality(sequence=0)['symbols'], [])
        self.assertEqual(self.quality(sequence=1)['groups'][0]['changed_transitions'], 0)

    def test_tied_receipt_cutoff_includes_all_rows(self):
        self.add(labels=['same', 'same'])
        self.clock[0] -= 1; self.clock[1] -= 1
        self.add(label='older'); self.j.finish('RUN_LIMIT')
        self.assertEqual(len(self.view(cutoff_ns=self.clock[0]-1)['revisions']), 3)
        self.assertEqual(len(self.view(sequence=1)['revisions']), 2)

    def test_summary_safety_metadata_rejected_even_empty_cutoff(self):
        self.add(); self.j.finish('RUN_LIMIT')
        p = self.directory / 'summary.json'
        original = json.loads(p.read_bytes())
        for field, value in [('finality', 'FINAL'), ('completeness', 'COMPLETE'), ('schema', 2)]:
            with self.subTest(field=field):
                p.write_text(json.dumps(dict(original, **{field: value})))
                with self.assertRaises(ValueError): self.quality(sequence=0)
        p.write_text(json.dumps(original))

    def test_manifest_safety_metadata_rejected(self):
        from capture import digest
        self.j.finish('RUN_LIMIT')
        p = self.directory / 'manifest.json'
        manifest = json.loads(p.read_bytes())
        manifest['strategy_status'] = 'ELIGIBLE'
        p.write_text(json.dumps(manifest))
        s = self.directory / 'summary.json'
        summary = json.loads(s.read_bytes())
        summary.update(manifest_sha256=digest(manifest), last_hash=digest(manifest))
        s.write_text(json.dumps(summary))
        with self.assertRaises(ValueError): self.quality(sequence=0)

    def test_production_import_isolation(self):
        root = Path(__file__).resolve().parents[2]
        for p in root.glob('*.py'):
            if p.name.startswith('test_'): continue
            tree = ast.parse(p.read_text(encoding='utf-8-sig'))
            for node in ast.walk(tree):
                names = ([node.module or ''] if isinstance(node, ast.ImportFrom)
                         else [a.name for a in node.names] if isinstance(node, ast.Import) else [])
                self.assertFalse(any('provisional_replay' in n or 'receipt_quality' in n for n in names), str(p))

    def test_quality_cli_failure_no_export_and_exclusive(self):
        from test_provisional_replay import synthetic_decode
        self.add(); self.j.finish('RUN_LIMIT')
        out = self.directory.parent / 'quality.json'
        with patch('provisional_replay.protobuf_decoder', return_value=(synthetic_decode, {})):
            self.assertEqual(main([str(self.directory), '--output', str(out)]), 0)
            raw = out.read_bytes()
            self.assertEqual(main([str(self.directory), '--output', str(out)]), 1)
            self.assertEqual(out.read_bytes(), raw)
            out.unlink()
            (self.directory / 'summary.json').unlink()
            self.assertEqual(main([str(self.directory), '--output', str(out)]), 1)
            self.assertFalse(out.exists())

