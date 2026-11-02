"""Strictly offline observations of provisional candle receipt evidence."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from provisional_replay import replay


def report(directory, *, sequence=None, cutoff_ns=None, decoder=None):
    """Verify/decode entire sealed journal before summarizing selected evidence.

    Receipt gaps are monotonic-clock deltas, never inferred missing candles.
    Repeated observations include all rows; changes compare decoded field presence
    and values, not protobuf byte identity. Raw evidence stays in the journal.
    """
    view = replay(directory, sequence=sequence, cutoff_ns=cutoff_ns, decoder=decoder)
    safety = dict(status='PROVISIONAL', finality='UNKNOWN', strategy_status='DATA_BLOCKED')
    groups = []
    for g in view['groups']:
        history = g['history']
        fields = Counter()
        changed = 0
        for previous, current in zip(history, history[1:]):
            a, b = previous['source'], current['source']
            keys = [k for k in sorted(a.keys() | b.keys())
                    if (k in a) != (k in b) or a.get(k) != b.get(k)]
            fields.update(keys)
            changed += bool(keys)
        groups.append(dict(symbol=g['symbol'], source_label=g['source_label'],
                           observations=len(history), changed_transitions=changed,
                           identical_transitions=len(history)-1-changed,
                           changed_fields=dict(fields),
                           first_sequence=history[0]['sequence'],
                           last_sequence=history[-1]['sequence'], **safety))
    symbols = []
    for symbol in dict.fromkeys(r['symbol'] for r in view['receipts']):
        receipts = [r for r in view['receipts'] if r['symbol'] == symbol]
        gaps = [dict(from_sequence=a['sequence'], to_sequence=b['sequence'],
                     elapsed_mono_ns=b['received_mono_ns']-a['received_mono_ns'])
                for a, b in zip(receipts, receipts[1:])]
        symbols.append(dict(symbol=symbol, receipts=len(receipts),
                            unique_observed_labels=sum(g['symbol'] == symbol for g in groups),
                            first_received_wall_ns=receipts[0]['received_wall_ns'],
                            last_received_wall_ns=receipts[-1]['received_wall_ns'],
                            observation_span_mono_ns=receipts[-1]['received_mono_ns']-receipts[0]['received_mono_ns'],
                            interreceipt_gaps=gaps,
                            max_interreceipt_mono_ns=max((g['elapsed_mono_ns'] for g in gaps), default=None),
                            **safety))
    return dict(schema=1, mode='OFFLINE_CANDLE_QUALITY', **safety,
                completeness='NOT_ESTABLISHED', boundary_semantics='UNKNOWN',
                provider_accuracy='NOT_ESTABLISHED', adjustment_factors='UNKNOWN',
                as_of=view['as_of'], provenance=dict(view['provenance'],
                    quality_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                selected_receipts=len(view['receipts']), selected_rows=len(view['revisions']),
                groups=groups, symbols=symbols,
                limitations='Observed receipts only. No expected cadence, missing-minute inference, '
                'session coverage ratio, finality, completeness or strategy eligibility established.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--sequence', type=int)
    parser.add_argument('--cutoff-ns', type=int)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        result = report(args.capture, sequence=args.sequence, cutoff_ns=args.cutoff_ns)
        encoded = json.dumps(result, indent=2, allow_nan=False) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(encoded)
        else:
            print(encoded, end='')
    except Exception as exc:
        print(f'DATA_BLOCKED: quality report failed: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
