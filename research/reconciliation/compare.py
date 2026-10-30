"""Matched synthetic experiment; vendored PR40 is an unchanged comparator."""
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from hashlib import sha256
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'vendor'))
from canonical_candles import canonicalize, identity
from market_structure_v12 import assess
from market_structure_v12_scenarios import scenario, reseal
from s0_reference import replay


def transform(rows, scale=1, shift=0, reflect=None):
    if reflect is not None:
        rows = [(reflect-o,reflect-l,reflect-h,reflect-c,v) for o,h,l,c,v in rows]
    return [tuple(scale*x+shift for x in r[:4])+(r[4],) for r in rows]


def paths():
    trend = [(10000-i*100,10100-i*100,9900-i*100,10000-i*100,100) for i in range(20)]
    box = [(8100,8150,8050,8100,100)]*8
    up = (8200,8210,8190,8200,100)
    touch = (8200,8210,8140,8200,100)
    down = (8000,8010,7990,8000,100)
    dtouch = (8000,8060,7990,8000,100)
    base = trend+box
    return dict(
        reversal=base+[up,up,touch,up],
        continuation=base+[down,down,dtouch,down],
        one_close=base+[up,box[0]],
        wick_only=base+[(8100,8200,8050,8100,100)]*4,
        failed_retest=base+[up,up,(8100,8160,8090,8100,100)],
        no_retest=base+[up]*8,
        exact_epsilon=base+[(8170,8180,8160,8170,100)]*10,
        hold_timeout=base+[up,up,touch]+[(8150,8160,8140,8150,100)]*3,
        late_retest=base+[up]*6+[touch,up],
        box_expiry=base+[box[0]]*10,
        flat=[box[0]]*32,
    )


def bundle_for(values, symbol='SPY'):
    bundle, context, requests = scenario(symbol=symbol)
    start = datetime.fromisoformat(bundle.observations[0].raw_stamp)
    grid = tuple(((start+timedelta(minutes=i)).isoformat(),(start+timedelta(minutes=i+1)).isoformat()) for i in range(len(values)))
    # Rebuild the fictional calendar and rebind its synthetic authority subjects.
    from canonical_candles import subjects
    calendar = context.calendar
    # Field names are pinned to PR40's canonical contract, never introspected market metadata.
    calendar = replace(calendar, intervals=grid, close_at=grid[-1][1])
    context = replace(context,calendar=calendar)
    context = replace(context,authorities=tuple(replace(a,subject_hash=subjects(context)[a.role]) for a in context.authorities))
    template = bundle.observations[0]
    rows=[]
    for i,r in enumerate(values):
        received=(datetime.fromisoformat(grid[i][1])+timedelta(seconds=1)).isoformat()
        rows.append(replace(template,observation_id=f'{symbol}-M{i}',revision_id=f'{symbol}-MR{i}',row_id=str(i),
            raw_stamp=grid[i][0],values=tuple(r),available_at=received,received_at=received,
            completion_received_at=received,snapshot=json.dumps(r).encode()))
    bundle=reseal(bundle,rows)
    requests=tuple(replace(requests[0],cutoff=(datetime.fromisoformat(end)+timedelta(seconds=1)).isoformat(),watermark=end) for _,end in grid)
    return bundle,context,requests


def evaluate(values):
    bundle,context,requests=bundle_for(values)
    result=assess(bundle,context,requests[-1],synthetic=True)
    gate=canonicalize(bundle,context,requests[-1])
    assert gate.eligible, gate.reasons
    return dict(s0=replay(values),p40=dict(classification=result.decision.classification,
        direction=result.decision.direction,events=[(e.trigger_interval_end,e.kind) for e in result.tracker.events],
        reasons=result.decision.reasons))


def evidence():
    cases={}
    for name,rows in paths().items():
        for direction,r in [('downtrend',rows),('uptrend',transform(rows,reflect=20000))]:
            for variant,changed in [('base',r),('scale3',transform(r,scale=3)),
                                    ('translate1m',transform(r,shift=1000000)),
                                    ('reflect1m',transform(r,reflect=1000000))]:
                cases[f'{name}/{direction}/{variant}']=evaluate(changed)
    return dict(notice='Invented paths; conformance only, no market accuracy or performance claims.',
        sources={'PR39':'8d45bb39b298a8c7d9e01b17b12bc7b324c45e19','PR40':'6f282a88c41d345e744089b6dd880e93dd53a4af'},
        code_sha256={p.relative_to(HERE).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.rglob('*.py'))},cases=cases)


if __name__ == '__main__':
    print(json.dumps(evidence(),sort_keys=True,indent=2,allow_nan=False))
