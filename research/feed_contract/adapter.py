"""Fake-only eligibility model. No transport, SDK, persistence or detector integration.

Typed, trusted SYNTHETIC envelopes only. Authority flags model evidence; they
never verify actual provider claims. UTC times use synthetic integer microseconds.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class Revision:
    id: str
    symbol: str
    start: int
    end: int
    raw: bytes
    values: tuple[str, str, str, str, str]  # O H L C V
    received: int
    receipt_seq: int
    committed: int | None
    commit_seq: int
    authority_time: int
    authority_seq: int
    finality: str
    complete: bool
    parent: str | None


@dataclass(frozen=True)
class Health:
    at: int
    sequence: int
    state: str


@dataclass(frozen=True)
class Context:
    symbol: str
    expected: tuple[int, ...]  # externally evidenced complete grid, including tail
    duration: int
    cutoff: int
    sequence: int
    authorities: tuple[tuple[str, int, int], ...]
    health: tuple[Health, ...]
    mode: str


@dataclass(frozen=True)
class Frame:
    status: str
    ids: tuple[str, ...]
    reasons: tuple[str, ...]


def select(receipts: tuple[Revision, ...], c: Context) -> Frame:
    """Select a unique supersession leaf per expected interval as known at cutoff.

    Receipt visibility precedes eligibility: an uncommitted or provisional visible
    replacement blocks instead of resurrecting an older FINAL. Input order is not
    revision order. Caller supplies immutable typed fixture evidence, not wire rows.
    """
    reasons=set()
    if (c.mode != 'SYNTHETIC' or c.symbol not in ('US.SPY','US.QQQ')
            or not c.expected or c.duration <= 0
            or tuple(sorted(set(c.expected))) != c.expected
            or any(b-a != c.duration for a,b in zip(c.expected,c.expected[1:]))
            or c.expected[-1]+c.duration > c.cutoff):
        return Frame('DATA_BLOCKED',(),('CONTEXT',))
    visible=lambda t,s: t <= c.cutoff and s <= c.sequence
    needed={'permission','mapping','calendar','finality','clock','source'}
    if {name for name,t,s in c.authorities if visible(t,s)} != needed:
        reasons.add('AUTHORITY')
    states=[h for h in c.health if visible(h.at,h.sequence)]
    # Health sequence is authoritative; ties with different evidence are ambiguous.
    if not states:
        reasons.add('HEALTH')
    else:
        last=max(h.sequence for h in states)
        latest={h for h in states if h.sequence==last}
        if len(latest)!=1 or next(iter(latest)).state!='VALIDATED': reasons.add('HEALTH')
    known={}
    for r in receipts:
        if r.symbol != c.symbol or not visible(r.received,r.receipt_seq): continue
        if r.id in known and known[r.id]!=r: reasons.add('IDENTITY_CONFLICT')
        known[r.id]=r
    # Validate the whole visible symbol graph, including off-grid links. No sorting
    # by arrival and no fallback behind a missing/ambiguous successor.
    roots={}
    for r in known.values():
        seen=set(); node=r
        while True:
            if node.id in seen:
                reasons.add('REVISION_GRAPH'); break
            seen.add(node.id)
            if node.parent is None:
                roots[r.id]=node.id; break
            parent=known.get(node.parent)
            if parent is None or (parent.start,parent.end)!=(r.start,r.end):
                reasons.add('REVISION_GRAPH'); break
            if parent.receipt_seq > node.receipt_seq or parent.received > node.received:
                reasons.add('REVISION_GRAPH'); break
            node=parent
    selected=[]
    for start in c.expected:
        versions=[r for r in known.values() if r.start==start]
        if not versions:
            reasons.add('COVERAGE'); continue
        parents={r.parent for r in versions}
        leaves=[r for r in versions if r.id not in parents]
        if len(leaves)!=1 or len({roots.get(r.id) for r in versions})!=1:
            reasons.add('REVISION_GRAPH'); continue
        r=leaves[0]
        if r.end!=start+c.duration: reasons.add('INTERVAL')
        if (r.committed is None or not visible(r.committed,r.commit_seq)
                or not visible(r.authority_time,r.authority_seq)
                or r.committed < r.received or r.commit_seq < r.receipt_seq):
            reasons.add('VISIBILITY')
        if r.finality!='FINAL' or not r.complete: reasons.add('FINALITY')
        try:
            o,h,l,close,v=map(Decimal,r.values)
            if (not all(x.is_finite() for x in (o,h,l,close,v))
                    or min(o,h,l,close)<=0 or v<0
                    or not l<=min(o,close)<=max(o,close)<=h):
                reasons.add('OHLCV')
        except (InvalidOperation,ValueError,TypeError): reasons.add('OHLCV')
        selected.append(r.id)
    return Frame('DATA_BLOCKED' if reasons else 'MOCK_READY',
                 () if reasons else tuple(selected),tuple(sorted(reasons)))
