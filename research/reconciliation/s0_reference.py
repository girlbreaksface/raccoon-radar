"""Bounded price-state reference for PR39 MS12-S0; exact rational comparisons.

Input is a prevalidated single-session FINAL prefix, not a public ingestion API.
No source, provider, pair, revision ingestion or outcome implementation is claimed.
Ordinals in this module are zero based. Thresholds are unchanged from PR39.
"""
from fractions import Fraction as F


def candidate(rows, i):
    t, box = rows[i-27:i-7], rows[i-7:i+1]
    tr = [max(r[1]-r[2], abs(r[1]-t[j-1][3]), abs(r[2]-t[j-1][3]))
          if j else r[1]-r[2] for j, r in enumerate(t)]
    s = sum(tr)/20
    d = t[-1][3]-t[0][3]
    v = sum(abs(b[3]-a[3]) for a,b in zip(t,t[1:]))
    sign = 1 if d > 0 else -1
    if not s > 0 or not v > 0 or abs(d) < 4*s or abs(d)/v < F(3,5):
        return None
    if sum(sign*(b[3]-a[3]) > 0 for a,b in zip(t,t[1:])) < 12:
        return None
    lo, hi = min(r[2] for r in box), max(r[1] for r in box)
    w = hi-lo
    if not s/2 <= w <= F(5,2)*s or abs(box[-1][3]-box[0][3]) > w/4:
        return None
    if any(not lo+w/10 <= r[3] <= hi-w/10 for r in box):
        return None
    for positions in ([j for j,r in enumerate(box) if r[2] <= lo+w/5],
                      [j for j,r in enumerate(box) if r[1] >= hi-w/5]):
        if not any(b-a >= 2 for a in positions for b in positions):
            return None
    return dict(lo=lo, hi=hi, s=s, d=sign, end=i)


def replay(values):
    rows = [tuple(F(str(x)) for x in r[:4]) for r in values]
    active = None
    floor = 0
    phase = 'INSUFFICIENT_EVIDENCE'
    events, trace = [], []
    last = 0
    streak = 0
    for i,r in enumerate(rows):
        if active is None:
            if i-floor+1 >= 28:
                active = candidate(rows,i)
                if active:
                    active.update(b=None, breakout=None, retest=None)
                    phase, last, streak = 'BOX', 0, 0
            trace.append(phase)
            continue
        a = active
        if phase == 'CONFIRMED':
            trace.append(phase)
            continue
        eps, tol = a['s']/10, F(3,20)*a['s']
        if a['b'] is None:
            side = 1 if r[3]-a['hi'] > eps else -1 if a['lo']-r[3] > eps else 0
            streak = streak+1 if side and side == last else int(bool(side))
            last = side
            if streak == 2:
                a.update(b=side, breakout=i)
                phase = 'BREAKOUT_PENDING'
            elif i >= a['end']+10:
                active, floor, phase = None, i+1, 'EXPIRED'
        else:
            b = a['b']
            boundary = a['hi'] if b == 1 else a['lo']
            z = b*(r[3]-boundary)
            if z < -tol:
                active, floor, phase = None, i+1, 'FAILED'
            elif a['retest'] is None:
                if i > a['breakout']+5:
                    active, floor, phase = None, i+1, 'RETEST_TIMEOUT'
                elif r[2] <= boundary+tol and r[1] >= boundary-tol and z >= 0:
                    a['retest'], phase = i, 'RETEST_PENDING'
                elif i == a['breakout']+5:
                    active, floor, phase = None, i+1, 'RETEST_TIMEOUT'
            elif i <= a['retest']+3 and z > eps:
                kind = 'POTENTIAL_REVERSAL_CONFIRMED' if b == -a['d'] else 'CONTINUATION_CONFIRMED'
                events.append((i, kind, b))
                phase = 'CONFIRMED'
            elif i >= a['retest']+3:
                active, floor, phase = None, i+1, 'HOLD_TIMEOUT'
        trace.append(phase)
    return dict(events=events, trace=trace)
