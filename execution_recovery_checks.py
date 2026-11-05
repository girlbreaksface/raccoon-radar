"""Deterministic fictional restart/crash fixtures; no provider SDK."""
import argparse
import copy
from pathlib import Path
import tempfile
from execution_recovery import VERSION, Journal, recover
from paper_account_reconciliation import digest, encoded, reconcile, VERSION as RV
from offline_checks import OfflineGuard

ACCOUNT = __import__('hashlib').sha256(b'raccoon-paper-account:123456').hexdigest()


def order(status='SUBMITTED', filled='0', **changes):
    return dict(dict(order_id='ORDER1', code='US.SPY', qty='2', dealt_qty=filled,
                     trd_side='BUY', order_status=status), **changes)


def events():
    return [dict(id='origin', kind='origin', inventory='DECLARED_FLAT'),
            dict(id='connect', kind='connection', connected=True),
            dict(id='intent1', kind='intent', intent='INTENT1', code='US.SPY', side='BUY', qty='2'),
            dict(id='ack1', kind='ack', intent='INTENT1', order_id='ORDER1')]


def serialize(items):
    with tempfile.TemporaryDirectory() as temp:
        journal = Journal(Path(temp) / 'journal.jsonl', ACCOUNT)
        try:
            for event in items:
                checkpoint = journal.append(event)
            checkpoint = dict(journal.checkpoint)
        finally:
            journal.close()
        return (Path(temp) / 'journal.jsonl').read_bytes(), checkpoint


def broker(orders, positions=None, **kwargs):
    from test_paper_account_reconciliation import fake_sdk
    snapshot = dict(orders=orders, positions=[] if positions is None else positions)
    sdk, calls = fake_sdk(**snapshot, **kwargs)
    baseline = dict(schema=RV, **snapshot)
    report = reconcile(sdk, baseline, expected_fingerprint=ACCOUNT, clock=lambda: 0)
    return dict(reconciliation=report, snapshots=[copy.deepcopy(snapshot), copy.deepcopy(snapshot)])


def scenarios():
    base = events()
    observe = lambda name, row: dict(id=name, kind='observation', order=row)
    cancelled = order('CANCELLED_ALL')
    complete = base + [observe('cancelled', cancelled)]
    partial = base + [observe('partial', order('FILLED_PART', '1'))]
    cases = {}
    def add(name, items, evidence, expected='HOLD', alter=None):
        raw, checkpoint = serialize(items)
        if alter: raw, checkpoint = alter(raw, checkpoint)
        result = recover(raw, checkpoint, ACCOUNT, **evidence)
        if result['recovery'] != expected or result['orders'] != 'DISABLED':
            raise ValueError('Unexpected recovery fixture: ' + name)
        cases[name] = result
    add('cancelled-unfilled', complete, broker([cancelled]), 'CONSISTENT_OFFLINE')
    add('partial-fill', partial, broker([order('FILLED_PART', '1')], [dict(
        code='US.SPY', qty='1', can_sell_qty='1', position_side='LONG')]))
    add('reject', base + [observe('reject', order('FAILED'))], broker([order('FAILED')]))
    add('cancel-request-not-fill', partial + [dict(id='cancel', kind='cancel_intent', order_id='ORDER1')],
        broker([order('FILLED_PART', '1')]))
    add('cancel-fill-race', partial + [dict(id='cancel', kind='cancel_intent', order_id='ORDER1'),
        observe('latefill', order('FILLED_ALL', '2'))], broker([order('FILLED_ALL', '2')]))
    add('cancelled-partial', partial + [observe('cancelled', order('CANCELLED_PART', '1'))],
        broker([order('CANCELLED_PART', '1')]))
    add('disconnect', complete + [dict(id='lost', kind='connection', connected=False)], broker([cancelled]))
    add('reconnect-without-evidence', complete + [dict(id='lost', kind='connection', connected=False),
        dict(id='back', kind='connection', connected=True)], {})
    add('reconnect-reconciled', complete + [dict(id='lost', kind='connection', connected=False),
        dict(id='back', kind='connection', connected=True)], broker([cancelled]), 'CONSISTENT_OFFLINE')
    add('unknown-status', base + [observe('unknown', order('UNKNOWN'))], broker([cancelled]))
    add('idempotent-event', complete + [complete[-1]], broker([cancelled]), 'CONSISTENT_OFFLINE')
    add('conflicting-event-id', complete + [dict(complete[-1], order=order('FILLED_ALL', '2'))], broker([cancelled]))
    add('fill-regression', partial + [observe('older', order())], broker([cancelled]))
    add('terminal-regression', complete + [observe('late', order('FILLED_ALL', '2'))], broker([cancelled]))
    add('order-discrepancy', complete, broker([order('FILLED_ALL', '2')]))
    add('position-discrepancy', complete, broker([cancelled], [dict(
        code='US.SPY', qty='1', can_sell_qty='1', position_side='LONG')]))
    add('missing-order', complete, broker([]))
    add('untracked-order', complete, broker([cancelled, order(order_id='OTHER')]))
    add('account-changed', complete, broker([cancelled], changed_accounts=[]))
    add('close-failure', complete, broker([cancelled], close_fails=True))
    add('tampered-journal', complete, broker([cancelled]), alter=lambda r,c: (r.replace(b'US.SPY', b'US.QQQ'), c))
    add('torn-write', complete, broker([cancelled]), alter=lambda r,c: (r[:-5], c))
    add('truncated-valid-prefix', complete, broker([cancelled]), alter=lambda r,c: (r[:r.rfind(b'\n',0,-1)+1], c))
    add('lost-checkpoint-receipt', complete, broker([cancelled]), alter=lambda r,c: (r, dict(count=c['count']-1, head=c['head'])))
    # Every durable event boundary is replayed independently after a simulated restart.
    for boundary in range(len(complete)+1):
        add('crash-boundary-' + str(boundary), complete[:boundary], broker([cancelled]),
            'CONSISTENT_OFFLINE' if boundary == len(complete) else 'HOLD')
    # A flat round trip uses only cumulative broker fill observations, never positions.
    roundtrip = base + [observe('entryfill', order('FILLED_ALL', '2')),
        dict(id='exitintent', kind='intent', intent='EXIT', code='US.SPY', side='SELL', qty='2'),
        dict(id='exitack', kind='ack', intent='EXIT', order_id='EXITORDER'),
        observe('exitfill', order('FILLED_ALL', '2', order_id='EXITORDER', trd_side='SELL'))]
    add('flat-roundtrip', roundtrip, broker([order('FILLED_ALL', '2'),
        order('FILLED_ALL', '2', order_id='EXITORDER', trd_side='SELL')]), 'CONSISTENT_OFFLINE')
    return cases


def evidence():
    report = dict(schema=VERSION, scope='SYNTHETIC_ONLY', scenarios=scenarios(),
        orders='DISABLED', paper_execution='HOLD', live_execution='NO-GO', broker_verified=False)
    report['evidence_hash'] = digest(report)
    return report


def validate_evidence(report):
    if encoded(report) != encoded(evidence()):
        raise ValueError('Recovery evidence differs from fixed current-code fixtures')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp, OfflineGuard(temp):
        report = evidence()
        validate_evidence(report)
    with args.output.open('xb') as handle:
        handle.write(encoded(report) + b'\n')
    print(str(len(report['scenarios'])) + ' offline recovery scenarios PASS; paper HOLD; orders DISABLED')


if __name__ == '__main__':
    main()
