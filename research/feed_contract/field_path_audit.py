"""Offline field trajectories: expose excursions hidden by endpoint equality."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from revision_impact import analyze


def _state(row, field):
    return dict(present=field in row['source'], value=copy.deepcopy(row['source'].get(field)))


def _ref(row):
    return {k: row[k] for k in ('sequence', 'row_index')}


def audit(directory, *, before, after, decoder=None):
    """Audit a fixed baseline against every later observation, including reversions.

    First-seen-after-baseline groups have no baseline; their initial values are
    not revisions. References resolve into the embedded, sealed impact evidence.
    All comparisons use the inherited decoded-field presence/value semantics.
    """
    evidence = analyze(directory, before=before, after=after, decoder=decoder)
    baseline = {(g['symbol'], g['source_label']): g['last_observed']
                for g in evidence['before']['groups']}
    paths = []
    for group in evidence['after']['groups']:
        key = group['symbol'], group['source_label']
        initial = baseline.get(key)
        history = group['history']
        # Sequence/row position, rather than label time or value equality.
        later = [r for r in history if initial is None or
                 (r['sequence'], r['row_index']) > (initial['sequence'], initial['row_index'])]
        anchor = initial if initial is not None else history[0]
        rows = [anchor] + (later if initial is not None else later[1:])
        fields = sorted(set().union(*(r['source'] for r in rows)))
        field_paths = []
        for field in fields:
            start = _state(anchor, field)
            previous = anchor
            changes = []
            for row in rows[1:]:
                old, new = _state(previous, field), _state(row, field)
                if old != new:
                    changes.append(dict(previous=_ref(previous), observation=_ref(row),
                                        before=old, after=new, returns_to_anchor=new == start))
                previous = row
            end = _state(rows[-1], field)
            classification = ('UNCHANGED' if not changes else
                              'RETURNED_TO_ANCHOR' if end == start else 'NET_CHANGED')
            field_paths.append(dict(field=field, anchor=start, last_observed=end,
                                    classification=classification, change_count=len(changes),
                                    return_count=sum(c['returns_to_anchor'] for c in changes),
                                    changes=changes))
        paths.append(dict(symbol=key[0], source_label=key[1],
                          baseline_available=initial is not None, anchor=_ref(anchor),
                          last_observed=_ref(rows[-1]), observations_after_baseline=len(later),
                          fields=field_paths, status='PROVISIONAL', finality='UNKNOWN',
                          strategy_status='DATA_BLOCKED'))
    result = {k: copy.deepcopy(evidence[k]) for k in
              ('status', 'finality', 'strategy_status', 'boundary_semantics',
               'completeness', 'provider_accuracy', 'adjustment_factors', 'provenance')}
    result['provenance']['field_path_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result.update(schema=1, mode='OFFLINE_FIELD_PATH_AUDIT', paths=paths, evidence=evidence,
                  counts={name: sum(f['classification'] == name for p in paths for f in p['fields'])
                          for name in ('UNCHANGED', 'RETURNED_TO_ANCHOR', 'NET_CHANGED')})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--before-sequence', type=int, required=True)
    parser.add_argument('--after-sequence', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit(args.capture, before={'sequence': args.before_sequence},
                       after={'sequence': args.after_sequence})
        encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
        with args.output.open('x', encoding='utf-8') as handle:
            handle.write(encoded)
    except Exception as exc:
        print(f'DATA_BLOCKED: field path audit failed: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
