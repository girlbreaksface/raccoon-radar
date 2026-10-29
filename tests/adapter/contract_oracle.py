"""SYNTHETIC TEST ORACLE ONLY. Not a supported adapter or provider implementation.

Exercises proposed dispositions; authority labels are fictional caller assertions.
No client, network, files, persistence, production import or ambient clock.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import struct


def instant(value):
    value=datetime.fromisoformat(value.replace("Z","+00:00"))
    if value.tzinfo is None: raise ValueError("Unknown timezone")
    return value.astimezone(timezone.utc)


def digest(value):
    def typed(v):
        if type(v) is float: return ["float64",struct.pack("!d",v).hex()]
        if isinstance(v,dict): return ["dict",[[k,typed(v[k])] for k in sorted(v)]]
        if isinstance(v,(list,tuple)): return [type(v).__name__,[typed(x) for x in v]]
        if v is None: return ["null"]
        if type(v) is bool: return ["bool",v]
        if type(v) is int: return ["int",str(v)]
        if type(v) is str: return ["str",v]
        raise ValueError("Unsupported synthetic evidence type")
    return hashlib.sha256(json.dumps(typed(value),sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def local_instant(raw,zone):
    """Strict test conversion: unapproved/ambiguous/nonexistent wall times block."""
    wall=datetime.fromisoformat(raw)
    if wall.tzinfo is not None: return wall.astimezone(timezone.utc)
    choices=[]
    for fold in (0,1):
        candidate=wall.replace(tzinfo=zone,fold=fold).astimezone(timezone.utc)
        if candidate.astimezone(zone).replace(tzinfo=None)==wall and candidate not in choices:
            choices.append(candidate)
    if len(choices)!=1: raise ValueError("Ambiguous or nonexistent wall time")
    return choices[0]


def supported_precision(available,cutoff):
    """Conservative legacy-second view; full instants remain separately preserved."""
    up=available.replace(microsecond=0)+(timedelta(seconds=1) if available.microsecond else timedelta())
    return up,cutoff.replace(microsecond=0)


def knowledge_upper_bound(receipt,metadata_receipt,end,uncertainty_ms):
    if type(uncertainty_ms) not in (int,float) or not math.isfinite(uncertainty_ms) or uncertainty_ms<0:
        raise ValueError("Proven finite nonnegative clock bound required")
    return max(receipt,metadata_receipt,end)+timedelta(milliseconds=uncertainty_ms)


def characterize(rows,context,*,cutoff,zone):
    """Proposed PR31 profile, final-only; not proof that a real source meets it."""
    raw=deepcopy(rows); ctx=deepcopy(context); now=instant(cutoff)
    reasons=[]; visible=[]; exclusions=[]
    report=dict(eligible=False,reasons=[],frame=None,frame_hash=None,bundle_hash=digest(raw),
                excluded=[],profile="SYNTHETIC_PR31_FINAL_ONLY")
    if ctx.get("synthetic") is not True: reasons.append("REAL_DATA_NOT_AUTHORIZED")
    if not ctx.get("source_evidence"): reasons.append("SOURCE_UNVERIFIED")
    scope=ctx.get("source_scope",{})
    if any(not isinstance(scope.get(k),str) or not scope[k] for k in
           ("endpoint","sdk","opend","interval","timezone","session_flags","adjustment","entitlement","units")):
        reasons.append("SOURCE_SCOPE_UNVERIFIED")
    if ctx.get("mapping_scope")!=scope: reasons.append("SOURCE_MAPPING_SCOPE_MISMATCH")
    if not ctx.get("mapping_evidence") or ctx.get("mapping") not in ("START","END"):
        reasons.append("MAPPING_UNVERIFIED")
    if not ctx.get("calendar_evidence"): reasons.append("CALENDAR_UNVERIFIED")
    if not ctx.get("capture_committed"): reasons.append("CAPTURE_NOT_COMMITTED")
    if ctx.get("capture_hash_valid") is not True: reasons.append("CUSTODY_HASH_MISMATCH")
    if ctx.get("pagination_complete") is not True: reasons.append("PARTIAL_SOURCE")
    if ctx.get("clock_trusted") is not True: reasons.append("CLOCK_UNTRUSTED")
    if ctx.get("holiday"):
        reasons.append("MARKET_CLOSED")
    for row in raw:
        if str(row.get("symbol","")).upper().removeprefix("US.")!=ctx.get("symbol"): continue
        known=row.get("available_at")
        if known is None or row.get("availability_basis") not in ("SYNTHETIC_CAPTURE","SYNTHETIC_PIT"):
            reasons.append("AVAILABILITY_UNKNOWN"); continue
        try: available=instant(known)
        except (ValueError,TypeError,AttributeError): reasons.append("AVAILABILITY_UNKNOWN"); continue
        if available>now:
            exclusions.append(row.get("revision_id")); continue  # Before payload/quality inspection.
        visible.append((row,available))
    report["excluded"]=exclusions
    frame=[]
    if not reasons:
        try:
            opening,closing=instant(ctx["open"]),instant(ctx["close"])
            watermark=instant(ctx["watermark"])
            if not opening<watermark<=closing or watermark>now: raise ValueError("Watermark")
            expected=[]; start=opening
            while start<watermark:
                expected.append(start); start+=timedelta(minutes=1)
            if start!=watermark: raise ValueError("Watermark precision")
            seen=set()
            for row,available in visible:
                stamp=local_instant(row["raw_stamp"],zone)
                start=stamp if ctx["mapping"]=="START" else stamp-timedelta(minutes=1)
                end=start+timedelta(minutes=1)
                if start<opening or end>closing: reasons.append("OUTSIDE_SESSION"); continue
                if start in seen: reasons.append("CONFLICTING_OR_DUPLICATE_REVISION")
                seen.add(start)
                if row.get("completed") is not True: reasons.append("COMPLETION_UNVERIFIED")
                if row.get("finality")!="FINAL": reasons.append("CONSUMER_FINALITY_BLOCKED")
                if available<end: reasons.append("AVAILABILITY_BEFORE_END")
                if row.get("units")!="USD_SHARES" or row.get("adjustment")!="SYNTHETIC_FIXED":
                    reasons.append("UNITS_ADJUSTMENT_UNVERIFIED")
                values=[row[k] for k in ("open","high","low","close","volume")]
                if any(type(v) not in (int,float) or not math.isfinite(v) for v in values):
                    reasons.append("INVALID_OHLCV"); continue
                o,h,l,c,v=values
                if min(o,h,l,c)<=0 or not l<=min(o,c)<=max(o,c)<=h or v<0:
                    reasons.append("INVALID_OHLCV"); continue
                frame.append(dict(symbol=ctx["symbol"],raw_stamp=row["raw_stamp"],
                    start=start.isoformat(),end=end.isoformat(),available_at=available.isoformat(),
                    revision_id=row["revision_id"],open=o,high=h,low=l,close=c,volume=v))
            if set(expected)!=seen: reasons.append("EXPECTED_GRID_GAP_OR_EXTRA")
            if not frame: reasons.append("NO_ROWS")
            if frame:
                latest_end=max(instant(r["end"]) for r in frame)
                latest_seen=max(instant(r["available_at"]) for r in frame)
                for name,age in (("max_event_age",(now-latest_end).total_seconds()),
                                 ("max_knowledge_age",(now-latest_seen).total_seconds())):
                    limit=ctx.get(name)
                    if type(limit) not in (int,float) or not math.isfinite(limit) or limit<=0:
                        reasons.append("FRESHNESS_POLICY_UNREVIEWED")
                    elif age>limit: reasons.append("STALE_"+name.upper())
                lag=ctx.get("max_delivery_lag")
                if type(lag) not in (int,float) or not math.isfinite(lag) or lag<=0:
                    reasons.append("FRESHNESS_POLICY_UNREVIEWED")
                elif any((instant(r["available_at"])-instant(r["end"])).total_seconds()>lag for r in frame):
                    reasons.append("LATE_DELIVERY")
        except (ValueError,KeyError,TypeError,OverflowError): reasons.append("CONTRACT_OR_TIMESTAMP_INVALID")
    report["reasons"]=sorted(set(reasons))
    if not reasons:
        frame.sort(key=lambda r:r["start"])
        report.update(eligible=True,frame=frame,frame_hash=digest(frame))
    return report
