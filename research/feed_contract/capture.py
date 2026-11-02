"""Bounded raw evidence journal, deliberately unable to produce eligible bars.

Payloads are SDK protobuf serializations, not original network packet bytes.
No SDK, network, trading, database or detector imports. One owner thread required.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import time

SYMBOLS = ('US.SPY', 'US.QQQ')


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


class CaptureStopped(RuntimeError):
    pass


class Journal:
    """Exclusive session, bounded bytes/records/time, fsync before acknowledgement.

    Local wall-versus-monotonic checks detect divergence, not UTC accuracy.
    A clean seal verifies local integrity, never source truth or market completeness.
    """
    def __init__(self, directory, metadata, clock=None):
        self.clock = clock or (lambda: (time.time_ns(), time.monotonic_ns()))
        self.start_wall, self.start_mono = self.clock()
        self.previous_wall, self.previous_mono = self.start_wall, self.start_mono
        self.last_receipt_wall, self.last_receipt_mono = self.start_wall, self.start_mono
        self.last = {s: self.start_mono for s in SYMBOLS}
        self.count = self.size = 0
        self.max_records, self.max_bytes = 5000, 10 * 1024 * 1024
        self.closed = False
        self.stopped = None
        self.directory = Path(directory)
        self.directory.mkdir(parents=False, exist_ok=False)
        self.manifest = dict(schema=1, mode='RAW_ONLY', strategy_status='DATA_BLOCKED',
                             symbols=SYMBOLS, duration_ns=300_000_000_000,
                             silence_ns=30_000_000_000, max_records=self.max_records,
                             max_bytes=self.max_bytes, max_payload_bytes=65536,
                             start_wall_ns=self.start_wall, start_mono_ns=self.start_mono,
                             metadata=metadata)
        self.chain = digest(self.manifest)
        self._save('manifest.json', self.manifest)
        self.file = (self.directory / 'receipts.jsonl').open('xb')

    def _save(self, name, value):
        with (self.directory / name).open('xb') as handle:
            handle.write(encode(value) + b'\n')
            handle.flush()
            os.fsync(handle.fileno())

    def stop(self, reason):
        self.stopped = self.stopped or reason
        raise CaptureStopped(self.stopped)

    def check(self):
        if self.closed: raise CaptureStopped('CLOSED')
        if self.stopped: raise CaptureStopped(self.stopped)
        wall, mono = self.clock()
        if (mono < self.previous_mono or wall < self.previous_wall
                or abs((wall-self.start_wall)-(mono-self.start_mono)) > 250_000_000):
            self.stop('CLOCK_DIVERGENCE')
        self.previous_wall, self.previous_mono = wall, mono
        if mono-self.start_mono >= self.manifest['duration_ns']: self.stop('TIME_LIMIT')
        if any(mono-last > self.manifest['silence_ns'] for last in self.last.values()):
            self.stop('SYMBOL_SILENCE')
        return wall, mono

    def append(self, symbol, source_stamps, payload, *, received=None):
        wall, mono = self.check()
        if received is None: received = (wall, mono)
        rw, rm = received
        if (rm < self.last_receipt_mono or rw < self.last_receipt_wall or rm > mono or rw > wall
                or abs((rw-self.start_wall)-(rm-self.start_mono)) > 250_000_000):
            self.stop('RECEIPT_CLOCK')
        if symbol not in SYMBOLS: self.stop('SYMBOL_SCOPE')
        if not isinstance(payload, bytes) or not payload or len(payload) > 65536:
            self.stop('PAYLOAD_LIMIT')
        if (not isinstance(source_stamps, tuple) or not source_stamps
                or len(source_stamps) > 100
                or any(not isinstance(s, str) or len(s) > 128 for s in source_stamps)):
            self.stop('SCHEMA')
        if self.count >= self.max_records: self.stop('RECORD_LIMIT')
        record = dict(sequence=self.count+1, symbol=symbol, source_stamps=source_stamps,
                      received_wall_ns=rw, received_mono_ns=rm,
                      journal_wall_ns=wall, journal_mono_ns=mono,
                      finality='UNKNOWN', strategy_status='DATA_BLOCKED',
                      payload_kind='SDK_PROTOBUF_SERIALIZATION',
                      payload_b64=base64.b64encode(payload).decode('ascii'),
                      payload_sha256=hashlib.sha256(payload).hexdigest(), previous=self.chain)
        hashed = digest(record)
        line = encode(dict(record, hash=hashed)) + b'\n'
        if self.size+len(line) > self.max_bytes: self.stop('BYTE_LIMIT')
        try:
            if self.file.write(line) != len(line): raise OSError('short write')
            self.file.flush()
            os.fsync(self.file.fileno())
        except OSError:
            self.stop('WRITE_FAILURE')
        self.count += 1
        self.size += len(line)
        self.chain = hashed
        self.last[symbol] = rm
        self.last_receipt_wall, self.last_receipt_mono = rw, rm
        return self.count

    def finish(self, reason):
        summary = dict(schema=1, manifest_sha256=digest(self.manifest),
                       records=self.count, bytes=self.size, last_hash=self.chain,
                       stop_reason=self.stopped or reason,
                       strategy_status='DATA_BLOCKED', finality='UNKNOWN',
                       completeness='NOT_ESTABLISHED')
        self.close()
        self._save('summary.json', summary)
        return summary

    def close(self):
        if not self.closed:
            self.closed = True
            if hasattr(self, 'file'): self.file.close()


def verify(directory, *, cutoff_ns=None, sequence=None):
    """Validate entire sealed capture before returning a receipt-as-of prefix.

    This is a receipt view, not a point-in-time market state or durable-commit view.
    Hash chain detects accidental edits; no signature or adversarial authenticity.
    """
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_bytes())
    summary = json.loads((directory / 'summary.json').read_bytes())
    if (type(manifest.get('schema')) is not int or manifest['schema'] != 1
            or manifest.get('mode') != 'RAW_ONLY'
            or manifest.get('strategy_status') != 'DATA_BLOCKED'
            or manifest.get('symbols') != list(SYMBOLS)
            or type(summary.get('schema')) is not int or summary['schema'] != 1
            or summary.get('finality') != 'UNKNOWN'
            or summary.get('completeness') != 'NOT_ESTABLISHED'):
        raise ValueError('Unsupported seal safety metadata')
    for name, value in (('sequence', sequence), ('cutoff_ns', cutoff_ns)):
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError(f'{name} must be a nonnegative integer')
    start = (manifest.get('start_wall_ns'), manifest.get('start_mono_ns'))
    if any(type(v) is not int or v < 0 for v in start):
        raise ValueError('Invalid capture clock origin')
    previous_receipt = previous_journal = start
    chain = digest(manifest)
    records = []
    size = 0
    with (directory / 'receipts.jsonl').open('rb') as handle:
        for line in handle:
            size += len(line)
            if size > 10*1024*1024 or len(records) >= 5000 or not line.endswith(b'\n'):
                raise ValueError('Capture bounds or framing')
            r = json.loads(line)
            receipt = (r.get('received_wall_ns'), r.get('received_mono_ns'))
            journal = (r.get('journal_wall_ns'), r.get('journal_mono_ns'))
            if (type(r.get('sequence')) is not int
                    or any(type(v) is not int or v < 0 for v in receipt + journal)
                    or any(v < old for v, old in zip(receipt, previous_receipt))
                    or any(v < old for v, old in zip(journal, previous_journal))
                    or any(v > saved for v, saved in zip(receipt, journal))
                    or any(abs((pair[0]-start[0])-(pair[1]-start[1])) > 250_000_000
                           for pair in (receipt, journal))):
                raise ValueError('Invalid capture receipt chronology')
            previous_receipt, previous_journal = receipt, journal
            hashed = r.pop('hash')
            payload = base64.b64decode(r['payload_b64'], validate=True)
            if (r['previous'] != chain or digest(r) != hashed
                    or r['sequence'] != len(records)+1 or r['symbol'] not in SYMBOLS
                    or r['finality'] != 'UNKNOWN' or r['strategy_status'] != 'DATA_BLOCKED'
                    or not 0 < len(payload) <= 65536
                    or hashlib.sha256(payload).hexdigest() != r['payload_sha256']):
                raise ValueError('Capture integrity')
            chain = hashed
            records.append(dict(r, hash=hashed))
    if (summary['manifest_sha256'] != digest(manifest)
            or summary['records'] != len(records) or summary['bytes'] != size
            or summary['last_hash'] != chain or summary['strategy_status'] != 'DATA_BLOCKED'):
        raise ValueError('Seal mismatch')
    return tuple(r for r in records
                 if (cutoff_ns is None or r['received_wall_ns'] <= cutoff_ns)
                 and (sequence is None or r['sequence'] <= sequence))
