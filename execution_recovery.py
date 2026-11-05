"""Offline, fail-closed execution journal recovery. Contains no broker actions.

A checkpoint is an independently retained (count, head) receipt, not a signature.
Never repair, truncate, resume submission, or infer fills from positions.
"""
import hashlib
import json
import os
from pathlib import Path
from paper_account_reconciliation import (
    VERSION as RECONCILIATION_VERSION, PENDING, TERMINAL, normalize,
    quantity, decimal_text, digest, encoded, security,
)

VERSION = 'offline-execution-recovery-v1'
ROOT = '0' * 64


class RecoveryBlocked(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise RecoveryBlocked(reason)


def fingerprint(value):
    require(type(value) is str and len(value) == 64
            and all(c in '0123456789abcdef' for c in value), 'INVALID_ACCOUNT')
    return value


def identifier(value):
    require(type(value) is str and 0 < len(value) <= 100
            and value.isascii() and value.isalnum(), 'INVALID_ID')
    return value


def read_journal(raw, checkpoint, account):
    fingerprint(account)
    require(type(raw) is bytes and len(raw) <= 8 * 1024 * 1024, 'JOURNAL_LIMIT')
    require(type(checkpoint) is dict and set(checkpoint) == {'count', 'head'}
            and type(checkpoint['count']) is int and 0 <= checkpoint['count'] <= 10000,
            'INVALID_CHECKPOINT')
    fingerprint(checkpoint['head'])
    require(not raw or raw.endswith(b'\n'), 'TORN_JOURNAL')
    lines = raw.splitlines()
    require(len(lines) == checkpoint['count'], 'CHECKPOINT_COUNT_MISMATCH')
    parent, events = ROOT, []
    for sequence, line in enumerate(lines, 1):
        row = json.loads(line)
        require(type(row) is dict and set(row) == {
            'schema', 'account', 'sequence', 'parent', 'event', 'hash'}, 'INVALID_ENVELOPE')
        body = {k: v for k, v in row.items() if k != 'hash'}
        require(encoded(row) == line and row['hash'] == digest(body), 'JOURNAL_HASH_MISMATCH')
        require(row['schema'] == VERSION and row['account'] == account
                and type(row['sequence']) is int and row['sequence'] == sequence
                and row['parent'] == parent, 'JOURNAL_SCOPE_OR_CHAIN')
        parent = row['hash']
        events.append(row['event'])
    require(parent == checkpoint['head'], 'CHECKPOINT_HEAD_MISMATCH')
    return events


class Journal:
    """Single exclusive writer. After any write failure abandon; never reuse it.

    New journals only. A crash before a receipt is retained requires investigation.
    File fsync is used; directory durability and external custody are not certified.
    """
    def __init__(self, path, account):
        self.account = fingerprint(account)
        self.path = Path(path)
        self.handle = self.path.open('xb')
        self.checkpoint = dict(count=0, head=ROOT)
        self.failed = False

    def append(self, event):
        require(not self.failed and not self.handle.closed, 'WRITER_UNAVAILABLE')
        body = dict(schema=VERSION, account=self.account,
                    sequence=self.checkpoint['count'] + 1,
                    parent=self.checkpoint['head'], event=event)
        row = dict(body, hash=digest(body))
        try:
            self.handle.write(encoded(row) + b'\n')
            self.handle.flush()
            os.fsync(self.handle.fileno())
        except BaseException:
            self.failed = True
            raise
        self.checkpoint = dict(count=body['sequence'], head=row['hash'])
        return dict(self.checkpoint)

    def close(self):
        self.handle.close()


def replay(events):
    require(events and events[0] == dict(id='origin', kind='origin', inventory='DECLARED_FLAT'),
            'FLAT_ORIGIN_REQUIRED')
    intents, orders, seen = {}, {}, {}
    connected = False  # A restart never assumes an existing broker connection.
    for event in events:
        require(type(event) is dict and 'id' in event and 'kind' in event, 'INVALID_EVENT')
        key = identifier(event['id'])
        if key in seen:
            require(seen[key] == event, 'CONFLICTING_EVENT_ID')
            continue
        seen[key] = event
        kind = event['kind']
        if kind == 'origin':
            require(event == events[0] and not intents and not orders and len(seen) == 1, 'INVALID_ORIGIN')
        elif kind == 'connection':
            require(set(event) == {'id', 'kind', 'connected'}
                    and type(event['connected']) is bool, 'INVALID_CONNECTION')
            connected = event['connected']
        elif kind == 'intent':
            require(set(event) == {'id', 'kind', 'intent', 'code', 'side', 'qty'}, 'INVALID_INTENT')
            intent = identifier(event['intent'])
            require(intent not in intents and event['side'] in ('BUY', 'SELL')
                    and quantity(event['qty']) > 0, 'INVALID_INTENT')
            security(event['code'])
            intents[intent] = dict(event, order_id=None)
        elif kind == 'ack':
            require(set(event) == {'id', 'kind', 'intent', 'order_id'}, 'INVALID_ACK')
            intent, order_id = identifier(event['intent']), identifier(event['order_id'])
            require(intent in intents and intents[intent]['order_id'] is None
                    and order_id not in orders, 'AMBIGUOUS_ACK')
            item = intents[intent]
            item['order_id'] = order_id
            orders[order_id] = dict(order_id=order_id, code=item['code'], qty=decimal_text(quantity(item['qty'])),
                dealt_qty='0', trd_side=item['side'], order_status='SUBMITTED', cancel_pending=False)
        elif kind == 'cancel_intent':
            require(set(event) == {'id', 'kind', 'order_id'} and event['order_id'] in orders,
                    'INVALID_CANCEL_INTENT')
            item = orders[event['order_id']]
            require(item['order_status'] in PENDING, 'CANCEL_AFTER_TERMINAL')
            item['cancel_pending'] = True
        elif kind == 'observation':
            require(set(event) == {'id', 'kind', 'order'}, 'INVALID_OBSERVATION')
            row = normalize([], [event['order']])['orders'][0]
            require(row['order_id'] in orders, 'UNTRACKED_OBSERVATION')
            prior = orders[row['order_id']]
            require(all(row[k] == prior[k] for k in ('code', 'qty', 'trd_side')), 'ORDER_IDENTITY_CHANGED')
            require(quantity(row['dealt_qty']) >= quantity(prior['dealt_qty']), 'FILL_REGRESSION')
            require(prior['order_status'] not in TERMINAL or all(row[k] == prior[k] for k in row),
                    'TERMINAL_STATE_CHANGED')
            require(not (prior['order_status'] == 'FILLED_PART' and row['order_status'] in
                         {'WAITING_SUBMIT', 'SUBMITTING', 'SUBMITTED'}), 'STATUS_REGRESSION')
            orders[row['order_id']] = dict(row, cancel_pending=(prior['cancel_pending']
                                                              and row['order_status'] in PENDING))
        else:
            raise RecoveryBlocked('UNKNOWN_EVENT_KIND')
    net = {}
    for row in orders.values():
        net[row['code']] = net.get(row['code'], quantity('0')) + (
            quantity(row['dealt_qty']) * (1 if row['trd_side'] == 'BUY' else -1))
    reasons = []
    if not connected: reasons.append('DISCONNECTED_OR_UNCONFIRMED')
    if any(i['order_id'] is None for i in intents.values()): reasons.append('UNACKNOWLEDGED_INTENT')
    if any(o['order_status'] in PENDING for o in orders.values()): reasons.append('PENDING_ORDER')
    if any(o['cancel_pending'] for o in orders.values()): reasons.append('CANCEL_UNCONFIRMED')
    if any(o['order_status'] == 'FAILED' for o in orders.values()): reasons.append('REJECTED_ORDER')
    if any(q != 0 for q in net.values()): reasons.append('NONFLAT_LOCAL_FILLS')
    return dict(orders=sorted(orders.values(), key=lambda o: o['order_id']),
                net_quantities={k: decimal_text(v) for k, v in sorted(net.items()) if v}, reasons=reasons)


def recover(raw, checkpoint, account, *, reconciliation=None, snapshots=None):
    """Integrate journal replay with #71 evidence and its two explicit snapshots.

    Caller supplies retained evidence only. No SDK import, provider connection,
    inferred trade price, P/L, retry, resubmit, cancel or local ledger correction.
    Journal position accounting assumes a declared flat starting inventory.
    """
    report = dict(schema=VERSION, scope='OFFLINE_ONLY', recovery='HOLD', reasons=[],
        recording='HOLD', paper_execution='HOLD', live_execution='NO-GO', orders='DISABLED',
        merge='HOLD', deployment='HOLD', journal_sha256=hashlib.sha256(raw).hexdigest(),
        checkpoint=checkpoint, local=None)
    try:
        state = replay(read_journal(raw, checkpoint, account))
        report['local'] = state
        report['reasons'].extend(state['reasons'])
        require(reconciliation is not None and snapshots is not None, 'BROKER_EVIDENCE_REQUIRED')
        r = reconciliation
        require(type(r) is dict and r.get('report_hash') == digest({k: v for k, v in r.items()
                if k != 'report_hash'}), 'RECONCILIATION_HASH_MISMATCH')
        report['reconciliation_hash'] = r['report_hash']
        require(r.get('schema') == RECONCILIATION_VERSION and r.get('account_fingerprint') == account
                and r.get('close_confirmed') is True and r.get('orders') == 'DISABLED'
                and r.get('paper_execution') == 'HOLD', 'RECONCILIATION_SCOPE')
        require(type(snapshots) is list and len(snapshots) == 2
                and len(r.get('observations', [])) == 2, 'TWO_SNAPSHOTS_REQUIRED')
        normalized = [normalize(s['positions'], s['orders']) for s in snapshots]
        require(all(digest(s) == o['snapshot_hash'] for s, o in zip(normalized, r['observations'])),
                'SNAPSHOT_HASH_MISMATCH')
        require(normalized[0] == normalized[1], 'SNAPSHOT_CHANGED')
        local_orders = [{k: v for k, v in row.items() if k != 'cancel_pending'} for row in state['orders']]
        require(normalized[1]['orders'] == local_orders, 'BROKER_LOCAL_ORDER_MISMATCH')
        actual_net = {row['code']: row['qty'] for row in normalized[1]['positions']}
        require(actual_net == state['net_quantities'], 'BROKER_LOCAL_POSITION_MISMATCH')
        # Preserve the existing reconciler's stricter pending/frozen/rejected gates.
        report['reasons'].extend(r['reasons'])
        require(r.get('reconciliation') == 'MATCHED_BASELINE', 'BROKER_RECONCILIATION_HOLD')
        if not report['reasons']:
            report['recovery'] = 'CONSISTENT_OFFLINE'
    except RecoveryBlocked as exc:
        report['reasons'].append(str(exc))
    except (ValueError, KeyError, TypeError, IndexError, UnicodeError):
        # Keep errors bounded and identifiers private; no provider exception strings.
        report['reasons'].append('INVALID_OR_AMBIGUOUS_EVIDENCE')
    report['reasons'] = sorted(set(report['reasons']))
    report['report_hash'] = digest(report)
    return report
