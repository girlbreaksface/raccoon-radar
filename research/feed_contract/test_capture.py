"""Synthetic capture regression cases. Never imports an SDK or connects."""
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from capture import Journal, CaptureStopped, verify, digest, encode


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-capture-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / 'exclusive'
        self.clock = [1_000_000_000_000, 0]
        self.j = Journal(self.directory, {'mode': 'SYNTHETIC'},
                         clock=lambda: tuple(self.clock))
        self.addCleanup(self.j.close)

    def add(self, **kw):
        args = dict(symbol='US.SPY', source_stamps=('2026-10-30 10:00:00',),
                    payload=b'\x00SYNTHETIC\xff')
        args.update(kw)
        return self.j.append(**args)

    def test_resealed_invalid_receipt_chronology_blocks_empty_cutoff(self):
        self.add(); self.add(); self.j.finish('TIME_LIMIT')
        path = self.directory / 'receipts.jsonl'
        original = [json.loads(line) for line in path.read_bytes().splitlines()]
        seal = json.loads((self.directory / 'summary.json').read_bytes())
        cases = [(0, 'sequence', True), (0, 'received_wall_ns', True),
                 (0, 'received_mono_ns', -1),
                 (1, 'received_wall_ns', self.clock[0]-1),
                 (0, 'received_mono_ns', 1),
                 (1, 'journal_wall_ns', self.clock[0]-1),
                 (0, 'journal_wall_ns', self.clock[0]+250_000_001)]
        for index, field, value in cases:
            with self.subTest(field=field, value=value):
                rows = [dict(r) for r in original]
                rows[index][field] = value
                chain = seal['manifest_sha256']
                lines = []
                for row in rows:
                    row.pop('hash')
                    row['previous'] = chain
                    chain = digest(row)
                    lines.append(encode(dict(row, hash=chain)) + b'\n')
                raw = b''.join(lines)
                path.write_bytes(raw)
                (self.directory / 'summary.json').write_bytes(encode(
                    dict(seal, last_hash=chain, bytes=len(raw))))
                with self.assertRaises(ValueError):
                    verify(self.directory, sequence=0)

    def test_verifier_rejects_invalid_cutoffs_and_clock_origin(self):
        self.j.finish('TIME_LIMIT')
        for name in ('sequence', 'cutoff_ns'):
            for value in (-1, True, 1.5):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        verify(self.directory, **{name: value})
        manifest = self.directory / 'manifest.json'
        data = json.loads(manifest.read_bytes())
        data['start_mono_ns'] = True
        manifest.write_bytes(encode(data))
        seal = json.loads((self.directory / 'summary.json').read_bytes())
        seal.update(manifest_sha256=digest(data), last_hash=digest(data))
        (self.directory / 'summary.json').write_bytes(encode(seal))
        with self.assertRaisesRegex(ValueError, 'clock origin'):
            verify(self.directory)

    def test_exclusive_no_overwrite(self):
        with self.assertRaises(FileExistsError):
            Journal(self.directory, {}, clock=lambda: tuple(self.clock))

    def test_exact_raw_hash_chain_asof(self):
        self.add()
        self.clock[:] = [1_001_000_000_000, 1_000_000_000]
        self.add(symbol='US.QQQ')
        result = self.j.finish('TIME_LIMIT')
        self.assertEqual(result['records'], 2)
        records = verify(self.directory)
        self.assertEqual(base64.b64decode(records[0]['payload_b64']), b'\x00SYNTHETIC\xff')
        self.assertEqual(records[0]['finality'], 'UNKNOWN')
        self.assertEqual(records[0]['strategy_status'], 'DATA_BLOCKED')
        self.assertEqual(len(verify(self.directory, cutoff_ns=1_000_000_000_000,
                                    sequence=1)), 1)

    def test_tamper_truncate_missing_summary(self):
        self.add(); self.j.finish('TIME_LIMIT')
        path = self.directory / 'receipts.jsonl'
        original = path.read_bytes()
        for altered in (original.replace(b'US.SPY', b'US.QQQ'), b'', original[:-1]):
            path.write_bytes(altered)
            with self.assertRaises(ValueError): verify(self.directory)
        path.write_bytes(original)
        (self.directory / 'summary.json').unlink()
        with self.assertRaises((ValueError, FileNotFoundError)): verify(self.directory)

    def test_scope_and_payload_fail_closed(self):
        with self.assertRaises(CaptureStopped): self.add(symbol='US.AAPL')
        with self.assertRaises(CaptureStopped): self.add()

    def test_deadline_cannot_be_extended_by_activity(self):
        self.clock[:] = [1_300_000_000_000, 300_000_000_000]
        with self.assertRaisesRegex(CaptureStopped, 'TIME_LIMIT'): self.add()

    def test_backward_monotonic_and_wall_clock_divergence(self):
        self.clock[:] = [999_000_000_000, 1_000_000_000]
        with self.assertRaisesRegex(CaptureStopped, 'CLOCK'): self.add()

    def test_silence_each_symbol(self):
        self.add()
        self.clock[:] = [1_031_000_000_000, 31_000_000_000]
        with self.assertRaisesRegex(CaptureStopped, 'SILENCE'): self.j.check()

    def test_bad_stamp_retained_without_interpretation(self):
        self.add(source_stamps=('ambiguous source text',))
        self.j.finish('TIME_LIMIT')
        self.assertEqual(verify(self.directory)[0]['source_stamps'], ['ambiguous source text'])

    def test_record_and_byte_budget(self):
        self.j.max_records = 1
        self.add()
        with self.assertRaisesRegex(CaptureStopped, 'RECORD_LIMIT'): self.add()

    def test_byte_budget(self):
        self.j.max_bytes = 1
        with self.assertRaisesRegex(CaptureStopped, 'BYTE_LIMIT'): self.add()

    def test_monotonic_rollback(self):
        self.clock[1] = -1
        with self.assertRaisesRegex(CaptureStopped, 'CLOCK'): self.add()

    def test_oversized_payload_and_disk_failure(self):
        with self.assertRaisesRegex(CaptureStopped, 'PAYLOAD_LIMIT'):
            self.add(payload=b'x' * 65537)

    def test_fsync_failure_never_acknowledges_record(self):
        with patch('capture.os.fsync', side_effect=OSError('synthetic disk full')):
            with self.assertRaisesRegex(CaptureStopped, 'WRITE_FAILURE'): self.add()
        self.assertEqual(self.j.count, 0)

    def test_future_sequence_excluded(self):
        self.add(); self.add(symbol='US.QQQ'); self.j.finish('TIME_LIMIT')
        self.assertEqual(len(verify(self.directory, sequence=1)), 1)


if __name__ == '__main__': unittest.main()
