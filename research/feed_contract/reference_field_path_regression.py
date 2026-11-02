"""Local-only pinned reference audit; emits counts, never raw receipts."""
import argparse
import hashlib
from pathlib import Path
import sys
import tempfile

from reference_impact_regression import EXPECTED, check
from offline_checks import OfflineGuard
from field_path_audit import audit


def check_paths(capture):
    check(capture)
    with tempfile.TemporaryDirectory(prefix='reference-path-') as temp, OfflineGuard(temp):
        kwargs = dict(before={'sequence': 386}, after={'sequence': 388})
        result = audit(capture, **kwargs)
        if result != audit(capture, **kwargs):
            raise ValueError('Nondeterministic field audit')
        group = next(p for p in result['paths'] if p['symbol'] == 'US.QQQ'
                     and p['source_label'] == '2026-11-02 10:52:00')
        for field in ('openPrice', 'lowPrice'):
            path = next(f for f in group['fields'] if f['field'] == field)
            if (path['classification'] != 'NET_CHANGED' or path['change_count'] != 1
                    or path['anchor'] != dict(present=True, value=696.88)
                    or path['last_observed'] != dict(present=True, value=696.9054)
                    or path['changes'][0]['observation'] != dict(sequence=388, row_index=0)):
                raise ValueError('Reference field path differs')
        full = audit(capture, before={'sequence': 0}, after={'sequence': 1143})
        if len(full['paths']) != 6 or len(full['evidence']['after']['observations']) != 1143:
            raise ValueError('Reference history loss')
        rows = {(r['sequence'], r['row_index']): r for r in full['evidence']['after']['observations']}
        for group in full['paths']:
            for field in group['fields']:
                for change in field['changes']:
                    for ref, state in (('previous', 'before'), ('observation', 'after')):
                        row = rows[tuple(change[ref][k] for k in ('sequence', 'row_index'))]
                        source = row['source']
                        if change[state] != dict(present=field['field'] in source,
                                                 value=source.get(field['field'])):
                            raise ValueError('Unresolvable field evidence')
        if full['completeness'] != 'NOT_ESTABLISHED' or full['strategy_status'] != 'DATA_BLOCKED':
            raise ValueError('Safety promotion')
        if any(n == 'moomoo' or n.startswith('moomoo.') for n in sys.modules):
            raise ValueError('SDK imported')
    if {n: hashlib.sha256((capture / n).read_bytes()).hexdigest() for n in EXPECTED} != EXPECTED:
        raise ValueError('Evidence changed')
    print('PASS: field path reference, deterministic 386/388 comparison, 1143 observations, six groups, all change references resolved, unchanged evidence')
    print('Full-capture field classifications (first observation anchors):', full['counts'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    check_paths(parser.parse_args().capture)
