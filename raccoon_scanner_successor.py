"""Synthetic-only offline research successor. No SDK, CLI feed, GUI or order APIs.

Explicit caller evidence is a trust contract, not provider verification. Missing authority
blocks eligibility. No default freshness policy, timestamp/calendar/finality assumptions.
"""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
from uuid import uuid4
from zoneinfo import ZoneInfo

AUTHORITIES=("source_authority","mapping_authority","calendar_authority",
             "availability_authority","completion_authority","finality_authority")
NOTICE="SYNTHETIC OFFLINE RESEARCH ONLY; no verified live bias, news or order execution"


def _time(value):
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None or t.utcoffset() is None: raise ValueError("Aware timestamp required")
    return t.astimezone(timezone.utc)


def _symbol(value):
    if not isinstance(value,str): return None
    value=value.strip().upper()
    if value.startswith("US."): value=value[3:]
    return value if value in ("SPY","QQQ") else None


def _typed(value):
    """Reversible typed raw evidence, including float64 nonfinite bits; strict JSON."""
    if value is None: return ["null"]
    if type(value) is bool: return ["bool",value]
    if type(value) is int: return ["int",str(value)]
    if type(value) is float: return ["float64",struct.pack("!d",value).hex()]
    if type(value) is str: return ["str",value]
    if type(value) in (tuple,list): return [type(value).__name__,[_typed(v) for v in value]]
    if type(value) is dict and all(type(k) is str for k in value):
        return ["dict",[[k,_typed(value[k])] for k in sorted(value)]]
    raise ValueError("Evidence accepts explicit JSON-like Python values only")


def _json(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")


def _hash(value): return hashlib.sha256(_json(value)).hexdigest()


def assess(symbol,rows,*,now,session,contract=None,policy=None,pagination_complete=False,
           provider_error=None,synthetic=False):
    if synthetic is not True: raise ValueError("Only explicit synthetic inputs authorized")
    if symbol not in ("SPY","QQQ"): raise ValueError("Exact symbol required")
    if not isinstance(now,datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Controlled aware clock required")
    datetime.strptime(session,"%Y-%m-%d")
    rows=tuple(rows)
    if len(rows)>10000: raise ValueError("Synthetic snapshot exceeds10000 rows")
    selected=[r for r in rows if isinstance(r,dict) and _symbol(r.get("symbol"))==symbol]
    reasons=[]
    if not selected: reasons.append("NO_ROWS")
    if pagination_complete is not True: reasons.append("PAGINATION_INCOMPLETE")
    if provider_error is not None: reasons.append("PROVIDER_ERROR")
    limit=policy.get("max_age_seconds") if isinstance(policy,dict) else None
    try: policy_ok=type(limit) in (int,float) and math.isfinite(limit) and limit>0
    except OverflowError: policy_ok=False
    if not policy_ok: reasons.append("FRESHNESS_POLICY_UNREVIEWED")
    contract=contract if isinstance(contract,dict) else {}
    for key in AUTHORITIES:
        if not isinstance(contract.get(key),str) or not contract[key].strip():
            reasons.append(key.upper()+"_UNVERIFIED")
    source=contract.get("source_sha256")
    if not isinstance(source,str) or re.fullmatch(r"[a-f0-9]{64}",source) is None:
        reasons.append("SOURCE_HASH_UNVERIFIED")
    mapped={}; intervals=[]
    try:
        zone=contract["exchange_timezone"]
        zone=timezone.utc if zone=="UTC" else ZoneInfo(zone)
        definitions=contract["intervals"]
        if not isinstance(definitions,(list,tuple)) or not 1<=len(definitions)<=10000:
            raise ValueError("Expected interval grid required")
        for item in definitions:
            stamp=item["raw_stamp"]
            if not isinstance(stamp,str) or not stamp or stamp in mapped: raise ValueError("Duplicate mapping")
            start,end,available=(_time(item[k]) for k in ("start","end","available_at"))
            if (end-start).total_seconds()!=60 or start.astimezone(zone).date().isoformat()!=session:
                raise ValueError("Wrong session or interval length")
            if available<end: reasons.append("AVAILABILITY_BEFORE_INTERVAL_END")
            if end>now or available>now: reasons.append("FUTURE_INFORMATION")
            if item.get("completed") is not True: reasons.append("INCOMPLETE_CANDLE")
            if item.get("finality")!="FINAL": reasons.append("FINALITY_UNVERIFIED")
            mapped[stamp]=(start,end,available)
            intervals.append((start,end))
        intervals.sort()
        if any(a[1]>b[0] for a,b in zip(intervals,intervals[1:])):
            raise ValueError("Overlapping canonical intervals")
    except (ValueError,KeyError,TypeError,AttributeError,OverflowError):
        reasons.append("INTERVAL_CALENDAR_CONTRACT_INVALID")
    seen=set(); bars=[]
    for row in selected:
        stamp=row.get("time")
        if not isinstance(stamp,str): reasons.append("INVALID_RAW_STAMP"); continue
        if stamp in seen: reasons.append("DUPLICATE_RAW_STAMP")
        seen.add(stamp)
        if stamp not in mapped: reasons.append("UNMAPPED_RAW_STAMP")
        if row.get("source_sha256")!=source: reasons.append("SOURCE_MISMATCH")
        try:
            values=[row[k] for k in ("open","high","low","close","volume")]
            if any(type(v) not in (int,float) or not math.isfinite(v) for v in values):
                raise ValueError("Finite numeric OHLCV required")
            o,h,l,c,v=(Decimal(str(v)) for v in values)
            if min(o,h,l,c)<=0 or not l<=min(o,c)<=max(o,c)<=h or v<0:
                raise ValueError("Invalid OHLCV")
            if stamp in mapped: bars.append((mapped[stamp],o,h,l,c,v))
        except (KeyError,ValueError,TypeError,OverflowError): reasons.append("INVALID_OHLCV")
    if set(mapped)-seen: reasons.append("MISSING_EXPECTED_INTERVAL")
    if len(bars)<35: reasons.append("INSUFFICIENT_REFERENCE_WARMUP")
    if bars and policy_ok:
        latest=max(b[0][1] for b in bars)
        if (now-latest).total_seconds()>limit: reasons.append("STALE")
    result=dict(schema=1,synthetic=True,symbol=symbol,session=session,notice=NOTICE,
        evaluated_at=now.astimezone(timezone.utc).isoformat(),eligible=False,bias=None,
        bias_status="UNVERIFIED" if selected else "UNAVAILABLE",action="WAIT",
        reasons=sorted(set(reasons)),observations=None,raw_sha256=_hash(_typed(selected)),
        contract_sha256=_hash(_typed(contract)),policy_sha256=_hash(_typed(policy)),
        contract_evidence=_typed(contract),policy_evidence=_typed(policy))
    if reasons: return result
    bars.sort(key=lambda b:b[0][0])
    with localcontext() as ctx:
        ctx.prec=50
        e9=e21=bars[0][4]
        for b in bars[1:]:
            e9=(Decimal(2)/10)*b[4]+(Decimal(8)/10)*e9
            e21=(Decimal(2)/22)*b[4]+(Decimal(20)/22)*e21
        volume=sum(b[5] for b in bars)
        prior=sum(b[5] for b in bars[-21:-1])/20
        if volume<=0 or prior<=0:
            result["reasons"]=["ZERO_VOLUME_DENOMINATOR"]; return result
        proxy=sum(((b[2]+b[3]+b[4])/3)*b[5] for b in bars)/volume
        ratio=bars[-1][5]/prior
        close=bars[-1][4]
        bias="BULLISH" if close>e9>e21 and close>proxy else (
            "BEARISH" if close<e9<e21 and close<proxy else "MIXED")
        result.update(eligible=bias!="MIXED",bias=bias,bias_status="SYNTHETIC CONTRACT SATISFIED",
            observations=dict(ema9=str(e9),ema21=str(e21),relative_volume=str(ratio),
                hlc3_volume_weighted_proxy=str(proxy),canonical_bars=len(bars),
                interval_end=bars[-1][0][1].isoformat(),
                limitations=["NOT_TRADE_LEVEL_VWAP","UNVALIDATED_REFERENCE_HYPOTHESIS"]))
        if bias=="MIXED": result["reasons"]=["NO_DIRECTIONAL_CONJUNCTION"]
    return result


def collect_pages(request,symbol,kwargs,*,max_pages=20,max_rows=10000):
    if symbol not in ("SPY","QQQ"): raise ValueError("Exact symbol required")
    if type(max_pages) is not int or not 1<=max_pages<=1000: raise ValueError("Bounded page limit required")
    if type(max_rows) is not int or not 1<=max_rows<=100000: raise ValueError("Bounded row limit required")
    if "page_req_key" in kwargs: raise ValueError("Start at first page")
    rows=[]; seen=set(); key=None; reasons=[]
    for page in range(1,max_pages+1):
        args=deepcopy(kwargs)
        if key is not None: args["page_req_key"]=key
        try:
            status,data,key=request(symbol,**args)
            if status!=0: reasons.append("PROVIDER_PAGE_ERROR"); break
            if type(data) not in (list,tuple) or any(type(r) is not dict for r in data):
                reasons.append("MALFORMED_PAGE"); break
            if len(rows)+len(data)>max_rows: reasons.append("ROW_LIMIT"); break
            rows.extend(deepcopy(data))
        except Exception as exc:
            reasons.append("PAGE_EXCEPTION:"+type(exc).__name__); break
        if key is None or key=="": return dict(rows=rows,complete=True,pages=page,reasons=[])
        if type(key) not in (str,bytes) or repr(key) in seen:
            reasons.append("REPEATED_OR_INVALID_PAGE_KEY"); break
        seen.add(repr(key))
    else: reasons.append("PAGE_LIMIT")
    return dict(rows=rows,complete=False,pages=page,reasons=reasons)


def _store(path):
    path=Path(path)
    if not path.is_absolute() or path.resolve()!=path or not path.is_dir():
        raise ValueError("Explicit existing non-symlink store required")
    marker=path/"synthetic-store.json"
    if marker.is_symlink() or not marker.is_file() or marker.stat().st_nlink!=1:
        raise ValueError("Synthetic store identity missing")
    identity=json.loads(marker.read_text(encoding="utf-8"))
    if identity!={"schema":1,"kind":"SYNTHETIC_SCANNER_SUCCESSOR"}:
        raise ValueError("Unrecognized synthetic store")
    return path


def create_store(path,*,synthetic=False):
    if synthetic is not True: raise ValueError("Synthetic store only")
    path=Path(path)
    if not path.is_absolute() or path.resolve()!=path: raise ValueError("Explicit absolute path required")
    path.mkdir(exist_ok=False)
    with (path/"synthetic-store.json").open("xb") as f:
        f.write(_json(dict(schema=1,kind="SYNTHETIC_SCANNER_SUCCESSOR")))
    return path


@contextmanager
def _lock(path):
    lock=path/".writer-lock"
    with lock.open("xb") as f: f.write(b"EXCLUSIVE SYNTHETIC OPERATION")
    try: yield
    finally: lock.unlink()


def _records(path):
    records=[]
    for entry in path.iterdir():
        if entry.name in ("synthetic-store.json",".writer-lock"): continue
        if (entry.is_symlink() or not entry.is_file() or entry.stat().st_nlink!=1 or
            re.fullmatch(r"[0-9a-f-]{36}\.json",entry.name) is None):
            raise ValueError("Unexpected evidence file")
        record=json.loads(entry.read_text(encoding="utf-8"))
        if set(record)!={"payload","sha256"} or _hash(record["payload"])!=record["sha256"]:
            raise ValueError("Evidence hash mismatch")
        payload=record["payload"]
        if payload.get("record_id")+".json"!=entry.name or payload.get("synthetic") is not True:
            raise ValueError("Evidence identity mismatch")
        if _hash(payload["raw_evidence"])!=payload["raw_sha256"]:
            raise ValueError("Raw evidence hash mismatch")
        records.append(payload)
    records.sort(key=lambda r:r["sequence"])
    previous={}; superseded=set()
    for n,record in enumerate(records,1):
        if record["sequence"]!=n: raise ValueError("Evidence sequence gap")
        parent=record["supersedes"]
        if parent is not None:
            if parent not in previous or parent in superseded or previous[parent]["observation"].get("symbol")!=record["observation"].get("symbol"):
                raise ValueError("Invalid revision chain")
            superseded.add(parent)
        previous[record["record_id"]]=record
    return records


def read_records(path):
    path=_store(path)
    with _lock(path): return _records(path)


def record_observation(path,observation,*,raw_rows,recorded_at,supersedes=None):
    path=_store(path)
    if observation.get("synthetic") is not True: raise ValueError("Synthetic observation only")
    stamp=_time(recorded_at)
    raw=_typed(raw_rows)
    if "raw_sha256" in observation and observation["raw_sha256"]!=_hash(raw):
        raise ValueError("Observation does not match provided raw evidence")
    _json(observation)  # Reject nonfinite or unsupported summary values before writing.
    with _lock(path):
        records=_records(path)
        if supersedes is not None:
            parent=next((r for r in records if r["record_id"]==supersedes),None)
            if (parent is None or any(r["supersedes"]==supersedes for r in records) or
                    parent["observation"].get("symbol")!=observation.get("symbol")):
                raise ValueError("Revision requires an existing current record of same symbol")
        payload=dict(record_id=str(uuid4()),sequence=len(records)+1,synthetic=True,schema=1,
            supersedes=supersedes,recorded_at_utc=stamp.isoformat(),recorded_at_input=recorded_at,
            observation=deepcopy(observation),raw_evidence=raw,raw_sha256=_hash(raw),
            code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        with (path/(payload["record_id"]+".json")).open("xb") as f:
            f.write(_json(dict(payload=payload,sha256=_hash(payload))))
            f.flush(); os.fsync(f.fileno())
        return payload
