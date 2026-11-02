"""Offline receipt replay. No market-time interpretation or eligible candle output."""
import argparse
import ast
import base64
import copy
import hashlib
from importlib.metadata import distribution, version
import json
import math
from pathlib import Path
import sys

from capture import verify


def protobuf_decoder():
    """Read descriptor literals only; never import/execute the moomoo package.

    The installed, reviewed SDK supplies schemas, not a quote context. Private
    descriptor pool avoids global SDK registrations. No installation/download.
    """
    from google.protobuf import descriptor_pool, message_factory
    if version('moomoo-api') != '10.11.7108':
        raise ValueError('Unreviewed schema version')
    package = distribution('moomoo-api')
    pool = descriptor_pool.DescriptorPool()
    hashes = {}
    for name in ('Common', 'Qot_Common', 'Qot_UpdateKL'):
        path = Path(package.locate_file(f'moomoo/common/pb/{name}_pb2.py'))
        raw = path.read_bytes()
        tree = ast.parse(raw)
        literals = [node.value.args[0] for node in tree.body
                    if isinstance(node, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'DESCRIPTOR'
                            for t in node.targets)
                    and isinstance(node.value, ast.Call)]
        if len(literals) != 1:
            raise ValueError('Unexpected protobuf schema layout')
        pool.AddSerializedFile(ast.literal_eval(literals[0]))
        hashes[name] = hashlib.sha256(raw).hexdigest()
    response = message_factory.GetMessageClass(
        pool.FindMessageTypeByName('Qot_UpdateKL.Response'))

    def decode(payload):
        message = response()
        message.ParseFromString(payload)
        if not message.IsInitialized() or message.retType != 0 or not message.HasField('s2c'):
            raise ValueError('Invalid Qot_UpdateKL response')
        s = message.s2c
        if s.security.market != 11 or s.klType != 1 or s.rehabType != 1:
            raise ValueError('Unsupported market/interval/adjustment flag')
        rows = []
        for k in s.klList:
            # ListFields retains field presence, names and exact decoded values.
            row = {field.name: value for field, value in k.ListFields()}
            required = ('time', 'openPrice', 'highPrice', 'lowPrice',
                        'closePrice', 'volume', 'turnover')
            if any(key not in row for key in required):
                raise ValueError('Missing candle fields')
            prices = [row[key] for key in required[1:5]]
            if (not all(math.isfinite(v) and v > 0 for v in prices)
                    or not math.isfinite(k.turnover) or k.turnover < 0
                    or k.volume < 0 or k.isBlank
                    or not k.lowPrice <= min(k.openPrice, k.closePrice)
                    <= max(k.openPrice, k.closePrice) <= k.highPrice):
                raise ValueError('Invalid candle values')
            rows.append(row)
        if not 0 < len(rows) <= 100:
            raise ValueError('Unexpected row count')
        return 'US.' + s.security.code, rows

    return decode, dict(sdk='10.11.7108', schema_source_sha256=hashes)


def replay(directory, *, sequence=None, cutoff_ns=None, decoder=None):
    """Verify the entire seal, decode all receipts, then select inclusive cutoffs.

    Last means receipt sequence/row position, never greatest source timestamp.
    Both cutoffs intersect. History includes repeats and all rows in wire order.
    Raw journal records remain attached, including payloads and integrity hashes.
    Returns detached data so a caller cannot alter another replay's history.
    """
    for name, value in (('sequence', sequence), ('cutoff_ns', cutoff_ns)):
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError(f'{name} must be a nonnegative integer')
    records = verify(directory)
    identity = {'decoder': 'injected'}
    if decoder is None:
        decoder, identity = protobuf_decoder()
    revisions = []
    previous_wall = previous_mono = -1
    for record in records:
        wall, mono = record['received_wall_ns'], record['received_mono_ns']
        if (type(wall) is not int or type(mono) is not int
                or wall < previous_wall or mono < previous_mono):
            raise ValueError('Invalid receipt ordering')
        previous_wall, previous_mono = wall, mono
        if record['payload_kind'] != 'SDK_PROTOBUF_SERIALIZATION':
            raise ValueError('Unsupported payload kind')
        symbol, rows = decoder(base64.b64decode(record['payload_b64'], validate=True))
        if (symbol != record['symbol'] or not rows
                or [row['time'] for row in rows] != record['source_stamps']):
            raise ValueError('Decoded symbol/source label mismatch')
        for index, row in enumerate(rows):
            if not isinstance(row['time'], str) or not row['time']:
                raise ValueError('Invalid source label')
            revisions.append(dict(symbol=symbol, source_label=row['time'],
                                  sequence=record['sequence'], row_index=index,
                                  received_wall_ns=wall, received_mono_ns=mono,
                                  source=copy.deepcopy(row), receipt=copy.deepcopy(record),
                                  status='PROVISIONAL', finality='UNKNOWN',
                                  strategy_status='DATA_BLOCKED'))
    selected = [r for r in revisions
                if (sequence is None or r['sequence'] <= sequence)
                and (cutoff_ns is None or r['received_wall_ns'] <= cutoff_ns)]
    groups = {}
    for revision in selected:
        key = revision['symbol'], revision['source_label']
        groups.setdefault(key, []).append(revision)
    return dict(schema=1, mode='OFFLINE_RECEIPT_REPLAY', status='PROVISIONAL',
                finality='UNKNOWN', strategy_status='DATA_BLOCKED',
                boundary_semantics='UNKNOWN', completeness='NOT_ESTABLISHED',
                provider_accuracy='NOT_ESTABLISHED', adjustment_factors='UNKNOWN',
                as_of=dict(sequence=sequence, received_wall_ns=cutoff_ns),
                provenance=dict(decoder=identity, verified_receipts=len(records),
                                replay_source_sha256=hashlib.sha256(
                                    Path(__file__).read_bytes()).hexdigest(),
                                verifier_source_sha256=hashlib.sha256(
                                    Path(__file__).with_name('capture.py').read_bytes()).hexdigest(),
                                verified_last_hash=records[-1]['hash'] if records else None,
                                manifest_sha256=hashlib.sha256(
                                    (Path(directory) / 'manifest.json').read_bytes()).hexdigest()),
                receipts=[copy.deepcopy(r) for r in records
                          if (sequence is None or r['sequence'] <= sequence)
                          and (cutoff_ns is None or r['received_wall_ns'] <= cutoff_ns)],
                revisions=selected,
                groups=[dict(symbol=s, source_label=label, history=history,
                             last_observed=copy.deepcopy(history[-1]),
                             status='PROVISIONAL', finality='UNKNOWN',
                             strategy_status='DATA_BLOCKED')
                        for (s, label), history in groups.items()])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--sequence', type=int)
    parser.add_argument('--cutoff-ns', type=int, help='Inclusive receipt wall nanoseconds')
    parser.add_argument('--output', type=Path, help='New exclusive JSON file; otherwise stdout')
    args = parser.parse_args(argv)
    try:
        result = replay(args.capture, sequence=args.sequence, cutoff_ns=args.cutoff_ns)
        encoded = json.dumps(result, indent=2, allow_nan=False) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(encoded)
        else:
            print(encoded, end='')
    except Exception as exc:
        # CLI boundary: protobuf/dependency failures must also report blocked,
        # without emitting a partial view. Interrupts still propagate.
        print(f'DATA_BLOCKED: replay failed: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
