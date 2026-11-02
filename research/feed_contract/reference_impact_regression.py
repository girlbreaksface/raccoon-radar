"""Local-only reference regression. Takes private capture path; never uploads it."""
import argparse
import hashlib
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from offline_checks import OfflineGuard
from provisional_replay import replay
from revision_impact import analyze

EXPECTED = {
    'manifest.json': '931377b114bca98c372fa848a1175f6a51dce85befc50d8be0823f2f986c5d2f',
    'receipts.jsonl': '42fa2dd2324b67a043f3ff26a75a5e52d43ccf7a842ee254db2e78c4c09fc19f',
    'summary.json': '667ddd5e0ff6c0fc0521803c709ce9b3d314856c3dc4b9dde06858943471404f',
}


def check(capture):
    def hashes():
        return {n: hashlib.sha256((capture / n).read_bytes()).hexdigest() for n in EXPECTED}
    if hashes() != EXPECTED:
        raise ValueError('Not the verified reference capture')
    with tempfile.TemporaryDirectory(prefix='reference-impact-') as temp, OfflineGuard(temp):
        full = replay(capture)
        result = analyze(capture, before={'sequence': 386}, after={'sequence': 388})
        if result != analyze(capture, before={'sequence': 386}, after={'sequence': 388}):
            raise ValueError('Nondeterministic result')
        if len(full['receipts']) != 1143 or len(full['groups']) != 6 or len(full['revisions']) != 1143:
            raise ValueError('Reference counts differ')
        def q(snapshot):
            return next(g['last_observed']['source'] for g in snapshot['groups']
                        if g['symbol'] == 'US.QQQ' and g['source_label'] == '2026-11-02 10:52:00')
        for snapshot, price in ((result['before'], 696.88), (result['after'], 696.9054)):
            if q(snapshot)['openPrice'] != price or q(snapshot)['lowPrice'] != price:
                raise ValueError('QQQ revision differs')
        revision = next(i for i in result['impacts'] if i['symbol'] == 'US.QQQ'
                        and i['observation']['sequence'] == 388)
        changes = {c['field']: c for c in revision['changes']}
        if revision['kind'] != 'REVISION' or any(
                changes[f]['before'] != 696.88 or changes[f]['after'] != 696.9054
                for f in ('openPrice', 'lowPrice')):
            raise ValueError('QQQ impact differs')
        wall = next(r['received_wall_ns'] for r in full['receipts'] if r['sequence'] == 386)
        timed = analyze(capture, before={'cutoff_ns': wall}, after={'sequence': 388})
        if timed['before']['observations'] != result['before']['observations']:
            raise ValueError('Receipt cutoff differs')
        all_rows = analyze(capture, before={'sequence': 0}, after={'sequence': 1143})
        if all_rows['after']['observations'] != full['revisions']:
            raise ValueError('History loss')
        for item in [result, result['before'], result['after']] + result['impacts'] + full['revisions']:
            if (item['status'], item['finality'], item['strategy_status']) != ('PROVISIONAL', 'UNKNOWN', 'DATA_BLOCKED'):
                raise ValueError('Safety status differs')
        if any(n == 'moomoo' or n.startswith('moomoo.') for n in sys.modules):
            raise ValueError('SDK package executed')
    if hashes() != EXPECTED:
        raise ValueError('Evidence changed')
    print('PASS: 1143 receipts/rows, six groups; 386/388 QQQ open/low revision; receipt cutoff; deterministic history; unchanged hashes; SDK not imported')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    check(args.capture)
