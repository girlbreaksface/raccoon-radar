"""Offline long-option accounting. No broker imports or execution authorization.

Explicit new stores only. SQLite FULL transactions survive process restart;
external checkpoints detect rollback. Disk/controller power-loss is unqualified.
Money is integer cents per contract (premium * multiplier already applied).
"""
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


class RiskBlocked(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise RiskBlocked(reason)


def encoded(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(x):
    return hashlib.sha256(encoded(x).encode()).hexdigest()


def integer(x, minimum=0):
    require(type(x) is int and minimum <= x <= 10**12, 'INVALID_INTEGER')
    return x


def timestamp(x):
    require(type(x) is str, 'INVALID_TIME')
    t = datetime.fromisoformat(x)
    require(t.tzinfo is not None and t.utcoffset() is not None, 'NAIVE_TIME')
    return t


def replay(events, now, limits):
    """Recompute, never trust stored counters. One flat-origin account per store.

    Trade count = distinct entry intents with a fill, including partial entries.
    Fees are expensed immediately; average entry cost uses exact rational cents.
    Overnight holdings/pending intents block until a future baseline protocol.
    """
    from fractions import Fraction
    t = timestamp(now)
    day = t.astimezone(ZoneInfo('America/New_York')).date()
    require(set(limits) == {'trades', 'loss_cents', 'exposure_cents', 'mark_age_seconds'}, 'LIMIT_SCHEMA')
    for value in limits.values(): integer(value, 1)
    require(events and events[0]['kind'] == 'origin', 'ORIGIN_REQUIRED')
    pending, positions, marks, entries, intents = {}, {}, {}, set(), set()
    realized = Fraction(0)
    last = None
    reasons = []
    overnight_ambiguity = False
    for e in events:
        require(type(e) is dict and {'id', 'kind', 'at'} <= set(e), 'EVENT_SCHEMA')
        et = timestamp(e['at'])
        require((last is None or et >= last) and et <= t, 'EVENT_CHRONOLOGY')
        last = et
        today = et.astimezone(ZoneInfo('America/New_York')).date() == day
        if today and (any(p['qty'] and p['day'] != day for p in positions.values())
                      or any(timestamp(p['at']).astimezone(ZoneInfo('America/New_York')).date() != day for p in pending.values())):
            overnight_ambiguity = True
        kind = e['kind']
        if kind == 'origin':
            require(e == events[0] and set(e) == {'id', 'kind', 'at', 'inventory'}
                    and e['inventory'] == 'DECLARED_FLAT', 'INVALID_ORIGIN')
        elif kind == 'reserve':
            require(set(e) == {'id', 'kind', 'at', 'intent', 'contract', 'qty', 'cap_cents'}, 'RESERVE_SCHEMA')
            require(type(e['intent']) is str and e['intent'] and e['intent'] not in intents, 'INTENT_REUSE')
            intents.add(e['intent'])
            require(type(e['contract']) is str and e['contract'], 'CONTRACT_REQUIRED')
            integer(e['qty'], 1); integer(e['cap_cents'], 1)
            pending[e['intent']] = dict(e, remaining=e['qty'], used=0)
        elif kind == 'fill':
            require(set(e) == {'id', 'kind', 'at', 'intent', 'side', 'qty', 'price_cents', 'fee_cents'}, 'FILL_SCHEMA')
            require(e['intent'] in pending and e['side'] in ('BUY', 'SELL'), 'UNRESERVED_FILL')
            p = pending[e['intent']]
            q = integer(e['qty'], 1); price = integer(e['price_cents'], 1); fee = integer(e['fee_cents'])
            require(q <= p['remaining'], 'OVERFILL')
            p['remaining'] -= q
            contract = p['contract']
            pos = positions.setdefault(contract, {'qty': 0, 'cost': Fraction(0), 'day': et.astimezone(ZoneInfo('America/New_York')).date()})
            if e['side'] == 'BUY':
                p['used'] += q * price + fee
                require(p['used'] <= p['cap_cents'], 'RESERVATION_EXCEEDED')
                pos['qty'] += q; pos['cost'] += q * price
                if today: entries.add(e['intent'])
            else:
                require(q <= pos['qty'], 'SHORT_OR_UNKNOWN_INVENTORY')
                cost = pos['cost'] * q / pos['qty']
                if today: realized += q * price - cost
                pos['qty'] -= q; pos['cost'] -= cost
            if today: realized -= fee
            if not today and pos['qty']: pos['day'] = et.astimezone(ZoneInfo('America/New_York')).date()
            marks.pop(contract, None)
        elif kind == 'terminal':
            require(set(e) == {'id', 'kind', 'at', 'intent'} and e['intent'] in pending, 'UNKNOWN_TERMINAL')
            del pending[e['intent']]
        elif kind == 'mark':
            require(set(e) == {'id', 'kind', 'at', 'contract', 'bid_cents'}, 'MARK_SCHEMA')
            integer(e['bid_cents'])
            marks[e['contract']] = (e['bid_cents'], et)
        else:
            raise RiskBlocked('UNKNOWN_EVENT')
    unrealized = Fraction(0)
    if overnight_ambiguity: reasons.append('OVERNIGHT_BASELINE_UNVERIFIED')
    exposure = sum(p['cap_cents'] - p['used'] for p in pending.values())
    for c, p in positions.items():
        if not p['qty']: continue
        exposure += p['cost']
        if p['day'] != day: reasons.append('OVERNIGHT_BASELINE_UNVERIFIED')
        if c not in marks or (t-marks[c][1]).total_seconds() > limits['mark_age_seconds']:
            reasons.append('MISSING_OR_STALE_MARK')
        else: unrealized += p['qty'] * marks[c][0] - p['cost']
    if any(timestamp(p['at']).astimezone(ZoneInfo('America/New_York')).date() != day for p in pending.values()):
        reasons.append('OVERNIGHT_PENDING')
    # Reserve trade capacity for every pending entry conservatively, including exits.
    if len(entries) + sum(k not in entries for k in pending) >= limits['trades']: reasons.append('TRADE_LIMIT')
    if realized + min(Fraction(0), unrealized) <= -limits['loss_cents']: reasons.append('LOSS_LIMIT')
    if exposure >= limits['exposure_cents']: reasons.append('EXPOSURE_LIMIT')
    return dict(trades=len(entries), realized_cents=str(realized), unrealized_cents=str(unrealized),
                exposure_cents=str(exposure), positions={c:p['qty'] for c,p in positions.items() if p['qty']},
                reasons=sorted(set(reasons)), eligible_offline=not reasons, orders='DISABLED', paper_execution='HOLD')


class Ledger:
    """Caller must retain receipt independently and supply it on every reopen.

    Receipt mismatch blocks even after a committed write whose reply was lost.
    Single transaction serializes writers and validates state before commit.
    """
    def __init__(self, path, account, limits, *, create=False, checkpoint=None):
        self.path = Path(path)
        require(type(account) is str and len(account) == 64 and all(c in '0123456789abcdef' for c in account), 'ACCOUNT_FINGERPRINT')
        self.account, self.limits = account, dict(limits)
        if create:
            with self.path.open('xb'): pass
        require(self.path.is_file(), 'STORE_MISSING')
        self.db = sqlite3.connect(str(self.path.resolve()), isolation_level=None)
        try:
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.execute('PRAGMA busy_timeout=1000')
            if create:
                self.db.execute('CREATE TABLE metadata (body TEXT NOT NULL)')
                self.db.execute('INSERT INTO metadata VALUES (?)', (encoded({'version':1,'account':account,'limits':limits}),))
                self.db.execute('CREATE TABLE events (seq INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, body TEXT NOT NULL, hash TEXT NOT NULL)')
            require(self.db.execute('PRAGMA integrity_check').fetchall() == [('ok',)], 'STORE_INTEGRITY')
            require(self.db.execute('SELECT body FROM metadata').fetchall() == [(encoded({'version':1,'account':account,'limits':limits}),)], 'STORE_SCOPE')
            self.events, self.receipt = self._read()
            require(create or checkpoint == self.receipt, 'CHECKPOINT_MISMATCH')
        except BaseException:
            self.db.close(); raise

    def _read(self):
        events, head = [], '0'*64
        for n, (seq, key, body, h) in enumerate(self.db.execute('SELECT seq,id,body,hash FROM events ORDER BY seq'), 1):
            e = json.loads(body)
            require(seq == n and key == e['id'] and body == encoded(e), 'STORE_SEQUENCE')
            head = digest({'parent':head,'event':e,'account':self.account,'limits':self.limits})
            require(head == h, 'STORE_HASH')
            events.append(e)
        return events, {'count':len(events),'head':head}

    def append(self, event, *, now):
        require(type(event.get('id')) is str and 0 < len(event['id']) <= 128, 'EVENT_ID')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            events, receipt = self._read()
            require(receipt == self.receipt, 'CONCURRENT_OR_UNRECEIPTED_WRITE')
            old = next((e for e in events if e['id'] == event['id']), None)
            if old is not None:
                require(old == event, 'CONFLICTING_ID')
                state = replay(events, now, self.limits)
            else:
                state = replay(events + [event], now, self.limits)
                if event['kind'] == 'reserve':
                    prior = replay(events, now, self.limits)
                    require(prior['eligible_offline'], 'PRIOR_RISK_BLOCKED')
                    require(not set(state['reasons']) - {'TRADE_LIMIT','EXPOSURE_LIMIT'}, 'RISK_BLOCKED')
                    require(int(state['exposure_cents']) <= self.limits['exposure_cents'], 'EXPOSURE_EXCEEDED')
                    require(state['trades'] + sum(e['kind']=='reserve' for e in events+[event]) <= 10000, 'EVENT_BOUND')
                head = digest({'parent':receipt['head'],'event':event,'account':self.account,'limits':self.limits})
                self.db.execute('INSERT INTO events VALUES (?,?,?,?)', (receipt['count']+1,event['id'],encoded(event),head))
                receipt = {'count':receipt['count']+1,'head':head}
            self.db.execute('COMMIT')
            self.events, self.receipt = events + ([] if old is not None else [event]), receipt
            return state, dict(receipt)
        except BaseException:
            if self.db.in_transaction: self.db.execute('ROLLBACK')
            raise

    def state(self, now):
        events, receipt = self._read()
        require(receipt == self.receipt, 'CHECKPOINT_CHANGED')
        return replay(events, now, self.limits)

    def close(self):
        self.db.close()
