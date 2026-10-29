"""Reproducible invented paths for v1.2; UTC is fictional, not an exchange calendar."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

from canonical_candles import (
    Source, Mapping, Calendar, Clock, Policy, TimeRules, Context, Authority,
    Observation, Page, Bundle, Request, identity, subjects,
)

SCENARIOS = (
    "bullish_reversal", "bearish_reversal", "bullish_continuation", "bearish_continuation",
    "bullish_false_breakout", "bearish_false_breakout", "bullish_failed_retest", "bearish_failed_retest",
    "bullish_invalidated", "bearish_invalidated", "prolonged", "retest_timeout", "wick_only",
    "two_sided", "weak_trend", "no_contraction", "gap", "provisional", "partial", "unknown",
    "duplicate", "incomplete", "invalid", "not_ready",
)


def reseal(bundle, rows=None, pages=None):
    rows = bundle.observations if rows is None else tuple(rows)
    pages = (replace(bundle.pages[0], observation_ids=tuple(o.observation_id for o in rows)),) if pages is None else tuple(pages)
    return replace(bundle, observations=rows, pages=pages, capture_hash=identity((rows, pages)))


def scenario(name="bullish_reversal", symbol="SPY"):
    if name not in SCENARIOS or symbol not in ("SPY", "QQQ"):
        raise ValueError("Predefined synthetic scenario and exact symbol required")
    # Base is an eight-bar downtrend followed by five overlapping, contracted bars.
    trend = [(10000-i*100, 10080-i*100, 9920-i*100, 10000-i*100, 100) for i in range(8)]
    flat = (9300, 9340, 9260, 9300, 100)
    values = trend + [flat]*5
    breakout = (9370, 9400, 9360, 9380, 100)
    retest = (9370, 9410, 9330, 9390, 100)
    if name.endswith("continuation"):
        values += [(9230, 9240, 9200, 9220, 100)]
    elif name.endswith("false_breakout"):
        values += [breakout, (9300, 9320, 9280, 9300, 100)]
    elif name.endswith("failed_retest"):
        values += [breakout, (9320, 9350, 9290, 9310, 100)]
    elif name.endswith("invalidated"):
        values += [breakout, retest, (9300, 9320, 9280, 9300, 100)]
    elif name == "prolonged":
        values += [flat]*16
    elif name == "retest_timeout":
        values += [breakout]*6
    elif name == "wick_only":
        values += [(9300, 9360, 9280, 9300, 100)]
    elif name == "two_sided":
        values += [(9300, 9360, 9240, 9300, 100)]
    elif name == "weak_trend":
        values[:8] = [(10000-i, 10080-i, 9920-i, 10000-i, 100) for i in range(8)]
        values[8:] = [(9993, 10033, 9953, 9993, 100)]*5
    elif name == "no_contraction":
        values[8:] = [(9300, 9500, 9100, 9300, 100)]*5
    elif name == "not_ready":
        values = values[:5]
    else:
        values += [breakout, retest]
    # Exact integer affine reflection mirrors highs/lows and all reversal mechanics.
    mirror = name.startswith("bearish_") and not name.endswith("continuation")
    mirror = mirror or name == "bullish_continuation"
    if mirror:
        values = [(20000-o, 20000-l, 20000-h, 20000-c, v) for o,h,l,c,v in values]
    opening = datetime(2026, 10, 23, 9, 30, tzinfo=timezone.utc)
    grid = tuple(((opening+timedelta(minutes=i)).isoformat(),
                  (opening+timedelta(minutes=i+1)).isoformat()) for i in range(len(values)))
    scope = tuple(sorted(dict(provider="SYNTHETIC_OPEND", endpoint="SYNTHETIC_STRUCTURE",
        sdk="SYNTHETIC_V1", opend="SYNTHETIC_V1", market="SYNTHETIC_US", interval="PT1M",
        timezone="UTC", tzdata="SYNTHETIC_FIXED", session="SYNTHETIC_RTH", adjustment="SYNTHETIC_FIXED",
        price_unit="USD", volume_unit="SHARES", entitlement="SYNTHETIC_ONLY").items()))
    source = Source(scope, "SYNTHETIC_BYTES", identity(("STRUCTURE_FIXTURE", symbol)))
    context = Context(source, Mapping("START", identity(source), "ISO"),
        Calendar("2026-10-23", grid[0][0], grid[-1][1], "UTC", "FICTIONAL_STRUCTURE_V1",
                 "2026-10-22T00:00:00Z", grid, False, "SYNTHETIC_CONTINUOUS"),
        Clock("SYNTHETIC_CLOCK", 0, "c"*64), Policy(120,120,30,"FINAL_ONLY","SYNTHETIC_CAPTURE"),
        (TimeRules("UTC","SYNTHETIC_FIXED",b""),), (), identity("DECLARED_STRUCTURE_FIXTURE_V1"))
    context = replace(context, authorities=tuple(
        Authority(role, role+"-SYNTHETIC", "d"*64, subject, identity(source), True)
        for role,subject in subjects(context).items()))
    rows=[]
    for i, row_values in enumerate(values):
        received=(datetime.fromisoformat(grid[i][1])+timedelta(seconds=1)).isoformat()
        snapshot=json.dumps(dict(symbol=symbol, time=grid[i][0], values=row_values),
                            sort_keys=True,separators=(",",":")).encode()
        rows.append(Observation(f"{symbol}-O{i}",f"{symbol}-R{i}",symbol,grid[i][0],tuple(row_values),
            received,"SYNTHETIC_CAPTURE",received,received,True,"FINAL","availability-SYNTHETIC",
            identity(source),symbol+"-P",str(i),snapshot))
    if name=="gap":
        rows.pop(4)
    if name in ("provisional","unknown","incomplete","invalid"):
        changes={"provisional":dict(finality="PROVISIONAL"),"unknown":dict(available_at=None),
                 "incomplete":dict(completed=False),"invalid":dict(values=(0,1,-1,0,100))}
        rows[-1]=replace(rows[-1],**changes[name])
    if name=="duplicate":
        rows.append(replace(rows[-1],observation_id="DUP",revision_id="DUP",row_id="DUP"))
    rows=tuple(rows)
    page=Page(symbol+"-P",symbol,symbol+"-Q",None,"MISSING" if name=="partial" else None,
              "OK",name!="partial",tuple(row.observation_id for row in rows))
    bundle=Bundle(symbol+"-STRUCTURE-SYNTHETIC",rows,(page,),True,True,identity((rows,(page,))))
    requests=tuple(Request(symbol,"2026-10-23",
        (datetime.fromisoformat(end)+timedelta(seconds=1)).isoformat(),end,"ENGINE_READY") for _,end in grid)
    return bundle,context,requests


def run(name="bullish_reversal", symbol="SPY"):
    from market_structure_v12 import assess
    bundle,context,requests=scenario(name,symbol)
    previous=None
    result=None
    for request in requests:
        result=assess(bundle,context,request,previous=previous,synthetic=True)
        previous=result.tracker
    return result


def main(argv=None):
    import argparse
    from dataclasses import asdict
    from market_structure_v12 import compare
    parser=argparse.ArgumentParser(description="Synthetic-only v1.2 structure research, no market history")
    parser.add_argument("--scenario",choices=SCENARIOS,default="bullish_reversal")
    parser.add_argument("--peer",choices=SCENARIOS,default="bearish_reversal")
    args=parser.parse_args(argv)
    left,right=run(args.scenario,"SPY"),run(args.peer,"QQQ")
    # Different scenario lengths have different final cutoffs, so do not invent alignment.
    pair=asdict(compare(left.decision,right.decision)) if left.decision.at==right.decision.at else "UNALIGNED_CUTOFFS"
    print(json.dumps(dict(notice="SYNTHETIC ONLY; no market history, orders or P/L",
                         spy=asdict(left.decision),qqq=asdict(right.decision),pair=pair),sort_keys=True,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
