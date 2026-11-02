"""Deterministic offline as-of snapshots and observation revision impact."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from provisional_replay import replay


def _select(full, cutoff):
    if not isinstance(cutoff, dict) or not cutoff or set(cutoff) - {'sequence', 'cutoff_ns'}:
        raise ValueError('Explicit sequence/cutoff_ns required')
    for value in cutoff.values():
        if type(value) is not int or value < 0:
            raise ValueError('Cutoffs must be nonnegative integers')
    return [r for r in full['revisions']
            if r['sequence'] <= cutoff.get('sequence', float('inf'))
            and r['received_wall_ns'] <= cutoff.get('cutoff_ns', float('inf'))]


def _snapshot(rows, cutoff):
    groups = {}
    for row in rows:
        groups.setdefault((row['symbol'], row['source_label']), []).append(row)
    return dict(as_of=copy.deepcopy(cutoff), observations=copy.deepcopy(rows),
                status='PROVISIONAL', finality='UNKNOWN', strategy_status='DATA_BLOCKED',
                groups=[dict(symbol=s, source_label=l, status='PROVISIONAL',
                             finality='UNKNOWN', strategy_status='DATA_BLOCKED', history=copy.deepcopy(h),
                             last_observed=copy.deepcopy(h[-1]))
                        for (s, l), h in groups.items()])


def analyze(directory, *, before, after, decoder=None):
    """Verify/decode once in full, then compare nested inclusive receipt prefixes.

    Field changes include presence changes; repeats compare all decoded fields.
    Deltas are observation differences, never returns or provider corrections.
    """
    full = replay(directory, decoder=decoder)
    left, right = _select(full, before), _select(full, after)
    if len(left) > len(right) or left != right[:len(left)]:
        raise ValueError('Before must select a prefix of after')
    latest = {(r['symbol'], r['source_label']): r for r in left}
    impacts = []
    for row in right[len(left):]:
        key = row['symbol'], row['source_label']
        previous = latest.get(key)
        changes = []
        if previous is not None:
            old, new = previous['source'], row['source']
            for field in sorted(set(old) | set(new)):
                if (field in old) != (field in new) or old.get(field) != new.get(field):
                    changes.append(dict(field=field, before_present=field in old,
                                        after_present=field in new,
                                        before=copy.deepcopy(old.get(field)),
                                        after=copy.deepcopy(new.get(field))))
        impacts.append(dict(symbol=key[0], source_label=key[1],
                            previous=copy.deepcopy(previous), observation=copy.deepcopy(row),
                            kind='FIRST_OBSERVATION' if previous is None else
                            ('REVISION' if changes else 'EXACT_REPEAT'), changes=changes,
                            status='PROVISIONAL', finality='UNKNOWN', strategy_status='DATA_BLOCKED'))
        latest[key] = row
    result = {k: copy.deepcopy(full[k]) for k in
              ('status', 'finality', 'strategy_status', 'boundary_semantics',
               'completeness', 'provider_accuracy', 'adjustment_factors', 'provenance')}
    result.update(schema=1, mode='OFFLINE_ASOF_REVISION_IMPACT',
                  before=_snapshot(left, before), after=_snapshot(right, after), impacts=impacts)
    result['provenance']['analysis_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--before-sequence', type=int, required=True)
    parser.add_argument('--after-sequence', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = analyze(args.capture, before={'sequence': args.before_sequence},
                         after={'sequence': args.after_sequence})
        encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
        with args.output.open('x', encoding='utf-8') as handle:
            handle.write(encoded)
    except Exception as exc:
        print(f'DATA_BLOCKED: analysis failed: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
