"""Pure SYNTHETIC-ONLY canonicalizer. No SDK, capture, storage, ambient clock or orders.

Authorities are caller-supplied fictional evidence bindings, not authentication or proof
of real provider semantics. All real-data use and real adapter integration remain blocked.
"""
from dataclasses import dataclass,fields
from datetime import datetime,timedelta,timezone
from hashlib import sha256
from io import BytesIO
import json
import math
import re
import struct
from zoneinfo import ZoneInfo


def _deep(value):
    if type(value) in (str,int,float,bool,bytes,type(None)): return
    if type(value) is tuple:
        for item in value: _deep(item)
        return
    if isinstance(value,FrozenRecord):
        for f in fields(value): _deep(getattr(value,f.name))
        return
    raise TypeError("Only recursively immutable records, tuples and scalar values accepted")


class FrozenRecord:
    __slots__=()
    def __post_init__(self): _deep(self)


@dataclass(frozen=True,slots=True)
class Source(FrozenRecord):
    scope:tuple
    fidelity:str
    artifact_hash:str

@dataclass(frozen=True,slots=True)
class Mapping(FrozenRecord):
    label:str
    scope_hash:str
    raw_format:str

@dataclass(frozen=True,slots=True)
class Calendar(FrozenRecord):
    session_date:str
    open_at:str|None
    close_at:str|None
    timezone:str
    version:str
    known_at:str|None
    intervals:tuple
    closed:bool
    halt_policy:str

@dataclass(frozen=True,slots=True)
class Clock(FrozenRecord):
    name:str
    uncertainty_seconds:float|None
    record_hash:str

@dataclass(frozen=True,slots=True)
class Policy(FrozenRecord):
    event_age:float|None
    knowledge_age:float|None
    delivery_lag:float|None
    finality_profile:str
    availability_model:str|None

@dataclass(frozen=True,slots=True)
class TimeRules(FrozenRecord):
    name:str
    version:str
    data:bytes

@dataclass(frozen=True,slots=True)
class Authority(FrozenRecord):
    role:str
    reference:str
    evidence_hash:str
    subject_hash:str
    scope_hash:str
    synthetic:bool

@dataclass(frozen=True,slots=True)
class Context(FrozenRecord):
    source:Source
    mapping:Mapping
    calendar:Calendar
    clock:Clock
    policy:Policy
    time_rules:tuple
    authorities:tuple
    implementation_hash:str

@dataclass(frozen=True,slots=True)
class Request(FrozenRecord):
    symbol:str
    session_date:str
    cutoff:str
    watermark:str
    mode:str

@dataclass(frozen=True,slots=True)
class Observation(FrozenRecord):
    observation_id:str
    revision_id:str
    symbol:str
    raw_stamp:str
    values:tuple
    available_at:str|None
    availability_basis:str
    received_at:str|None
    completion_received_at:str|None
    completed:bool|None
    finality:str
    availability_reference:str
    scope_hash:str
    page_id:str
    row_id:str
    snapshot:bytes

@dataclass(frozen=True,slots=True)
class Page(FrozenRecord):
    page_id:str
    symbol:str
    request_id:str
    request_cursor:str|None
    next_cursor:str|None
    status:str
    terminal:bool
    observation_ids:tuple

@dataclass(frozen=True,slots=True)
class Bundle(FrozenRecord):
    bundle_id:str
    observations:tuple
    pages:tuple
    committed:bool
    synthetic:bool
    capture_hash:str

@dataclass(frozen=True,slots=True)
class Candle(FrozenRecord):
    observation_id:str
    revision_id:str
    raw_stamp:str
    values:tuple
    start:str
    end:str
    available_at:str
    raw_record_hash:str

@dataclass(frozen=True,slots=True)
class Frame(FrozenRecord):
    candles:tuple
    context:Context
    request:Request
    frame_hash:str

@dataclass(frozen=True,slots=True)
class Report(FrozenRecord):
    eligible:bool
    status:str
    reasons:tuple
    exclusions:tuple
    frame:Frame|None
    bundle_hash:str
    context_hash:str
    request_hash:str
    run_hash:str


def _encode(value):
    if isinstance(value,FrozenRecord):
        return [type(value).__name__,[[f.name,_encode(getattr(value,f.name))] for f in fields(value)]]
    if type(value) is tuple: return ["tuple",[_encode(v) for v in value]]
    if type(value) is float: return ["float64",struct.pack("!d",value).hex()]
    if type(value) is bytes: return ["bytes",value.hex()]
    if value is None: return ["null"]
    if type(value) is bool: return ["bool",value]
    if type(value) is int: return ["int",str(value)]
    if type(value) is str: return ["str",value]
    raise TypeError("Unsupported immutable identity value")


def identity(value):
    return sha256(json.dumps(_encode(value),separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def subjects(context):
    """Exact content subjects for caller-supplied synthetic authority bindings."""
    source=identity(context.source)
    return dict(source=source,mapping=identity(context.mapping),calendar=identity(context.calendar),
        time_rules=identity(context.time_rules),clock=identity(context.clock),policy=identity(context.policy),
        completion=source,finality=source,
        availability=identity((context.source,context.policy.availability_model)))


def _hash(value): return type(value) is str and re.fullmatch(r"[a-f0-9]{64}",value) is not None
def _text(value): return type(value) is str and bool(value.strip())


def _time(value):
    if not _iso(value): raise ValueError("Time format/precision unknown")
    parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None: raise ValueError("Aware instant required")
    return parsed.astimezone(timezone.utc)


def _iso(value):
    return type(value) is str and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})?",value) is not None


def _number(value,zero=False):
    try: return type(value) in (int,float) and math.isfinite(value) and (value>=0 if zero else value>0)
    except OverflowError: return False


def _clock_delta(seconds):
    # Ceiling the exact supplied native-number bound avoids timedelta's nearest rounding.
    numerator,denominator=seconds.as_integer_ratio() if type(seconds) is float else (seconds,1)
    micros=(numerator*1000000+denominator-1)//denominator
    return timedelta(microseconds=micros)


def _symbol(value):
    if type(value) is not str: return None
    value=value.strip().upper()
    if value.startswith("US."): value=value[3:]
    return value if value in ("SPY","QQQ") else None


def _zone(name,context):
    rules=[r for r in context.time_rules if type(r) is TimeRules and r.name==name]
    if len(rules)!=1 or not _text(rules[0].version): raise ValueError("Timezone rule identity missing")
    rule=rules[0]
    if rule.version!=dict(context.source.scope).get("tzdata"): raise ValueError("Timezone version mismatch")
    if name=="UTC" and rule.data==b"": return timezone.utc
    if not 1<=len(rule.data)<=1048576: raise ValueError("Pinned in-memory TZif required")
    return ZoneInfo.from_file(BytesIO(rule.data),key=name)


def _raw_time(raw,mapping,zone):
    if not _iso(raw) or mapping.raw_format!="ISO": raise ValueError("Raw timestamp format/precision unapproved")
    parsed=datetime.fromisoformat(raw)
    if parsed.tzinfo is not None:
        instant=parsed.astimezone(timezone.utc)
        if parsed.utcoffset()!=instant.astimezone(zone).utcoffset():
            raise ValueError("Explicit offset contradicts scoped timezone")
        return instant
    choices=[]
    for fold in (0,1):
        instant=parsed.replace(tzinfo=zone,fold=fold).astimezone(timezone.utc)
        if instant.astimezone(zone).replace(tzinfo=None)==parsed and instant not in choices:
            choices.append(instant)
    if len(choices)!=1: raise ValueError("Ambiguous/nonexistent wall time")
    return choices[0]


def canonicalize(bundle,context,request):
    """Return immutable SYNTHETIC report; never fetch, persist, infer or run a consumer."""
    if type(bundle) is not Bundle or type(context) is not Context or type(request) is not Request:
        raise TypeError("Typed immutable inputs required")
    if (type(context.source) is not Source or type(context.mapping) is not Mapping or
        type(context.calendar) is not Calendar or type(context.clock) is not Clock or type(context.policy) is not Policy):
        raise TypeError("Typed immutable context required")
    if len(bundle.observations)>10000 or len(bundle.pages)>1000 or len(context.calendar.intervals)>10000:
        raise ValueError("Bounded synthetic input budget exceeded")
    reasons=[]; exclusions=[]; candles=[]
    bundle_hash=identity(bundle); context_hash=identity(context); request_hash=identity(request)
    def finish():
        eligible=not reasons and request.mode=="ENGINE_READY"
        frame=None
        if eligible:
            ordered=tuple(sorted(candles,key=lambda row:row.start))
            frame=Frame(ordered,context,request,identity((ordered,context_hash,request_hash)))
        status="SYNTHETIC_ENGINE_READY" if eligible else ("RAW_AUDIT" if request.mode=="RAW_AUDIT" else "BLOCKED")
        return Report(eligible,status,tuple(sorted(set(reasons))),tuple(exclusions),frame,
            bundle_hash,context_hash,request_hash,identity(("synthetic-canonical-v1",bundle_hash,context_hash,request_hash)))
    if bundle.synthetic is not True: reasons.append("REAL_DATA_NOT_AUTHORIZED")
    if not _text(bundle.bundle_id): reasons.append("CAPTURE_IDENTITY_INVALID")
    if any(type(rule) is not TimeRules for rule in context.time_rules):
        reasons.append("CONTEXT_SCHEMA_INVALID")
    if bundle.committed is not True: reasons.append("CAPTURE_NOT_COMMITTED")
    if bundle.capture_hash!=identity((bundle.observations,bundle.pages)): reasons.append("CAPTURE_HASH_MISMATCH")
    if request.symbol not in ("SPY","QQQ") or request.mode not in ("RAW_AUDIT","ENGINE_READY"):
        reasons.append("REQUEST_INVALID")
    try:
        cutoff,watermark=_time(request.cutoff),_time(request.watermark)
        if watermark>cutoff: raise ValueError()
    except (ValueError,TypeError,OverflowError): reasons.append("REQUEST_TIME_INVALID"); return finish()
    scope={}
    try:
        if any(type(pair) is not tuple or len(pair)!=2 for pair in context.source.scope): raise ValueError()
        scope=dict(context.source.scope)
        required=("provider","endpoint","sdk","opend","market","interval","timezone","tzdata",
                  "session","adjustment","price_unit","volume_unit","entitlement")
        if len(scope)!=len(context.source.scope) or any(not _text(scope.get(k)) for k in required): raise ValueError()
        if not scope["provider"].startswith("SYNTHETIC_"): reasons.append("REAL_DATA_NOT_AUTHORIZED")
        if scope["interval"]!="PT1M" or scope["price_unit"]!="USD" or scope["volume_unit"]!="SHARES":
            reasons.append("UNSUPPORTED_UNITS_OR_INTERVAL")
        if context.source.fidelity not in ("SDK_ROW_SNAPSHOT","SYNTHETIC_BYTES") or not _hash(context.source.artifact_hash):
            reasons.append("SOURCE_FIDELITY_UNVERIFIED")
    except (ValueError,TypeError): reasons.append("SOURCE_SCOPE_INVALID")
    source_hash=identity(context.source)
    if context.mapping.scope_hash!=source_hash or context.mapping.label not in ("START","END"):
        reasons.append("MAPPING_UNVERIFIED")
    expected_subjects=subjects(context); approvals={}
    for authority in context.authorities:
        if type(authority) is not Authority: reasons.append("AUTHORITY_INVALID"); continue
        if (authority.role in approvals or authority.role not in expected_subjects or authority.synthetic is not True or
            not _text(authority.reference) or not _hash(authority.evidence_hash) or authority.scope_hash!=source_hash or
            authority.subject_hash!=expected_subjects.get(authority.role)):
            reasons.append("AUTHORITY_BINDING_INVALID")
        approvals[authority.role]=authority
    if set(approvals)!=set(expected_subjects): reasons.append("AUTHORITY_MISSING")
    if not _hash(context.implementation_hash): reasons.append("IMPLEMENTATION_IDENTITY_MISSING")
    policy=context.policy
    if any(not _number(v) for v in (policy.event_age,policy.knowledge_age,policy.delivery_lag)):
        reasons.append("FRESHNESS_POLICY_UNREVIEWED")
    if policy.finality_profile!="FINAL_ONLY": reasons.append("CONSUMER_PROFILE_UNSUPPORTED")
    if policy.availability_model not in ("SYNTHETIC_CAPTURE","SYNTHETIC_PIT"):
        reasons.append("AVAILABILITY_MODEL_UNREVIEWED")
    if not _number(context.clock.uncertainty_seconds,zero=True) or not _text(context.clock.name) or not _hash(context.clock.record_hash):
        reasons.append("CLOCK_UNTRUSTED")
    if reasons: return finish()
    expected=set()
    try:
        raw_zone=_zone(scope["timezone"],context); calendar_zone=_zone(context.calendar.timezone,context)
        calendar=context.calendar
        if calendar.session_date!=request.session_date or not _text(calendar.version) or _time(calendar.known_at)>cutoff:
            raise ValueError("Session/calendar knowledge mismatch")
        if calendar.closed is True:
            if calendar.intervals or calendar.open_at is not None or calendar.close_at is not None: raise ValueError()
            reasons.append("MARKET_CLOSED"); return finish()
        if calendar.closed is not False or calendar.halt_policy!="SYNTHETIC_CONTINUOUS": raise ValueError("Unreviewed halt policy")
        opening,closing=_time(calendar.open_at),_time(calendar.close_at)
        if not opening<watermark<=closing or opening.astimezone(calendar_zone).date().isoformat()!=request.session_date:
            raise ValueError("Session/watermark invalid")
        grid=tuple((_time(a),_time(b)) for a,b in calendar.intervals)
        if not grid or grid[0][0]!=opening or grid[-1][1]!=closing: raise ValueError("Incomplete calendar grid")
        for i,(start,end) in enumerate(grid):
            if ((end-start).total_seconds()!=60 or start.second or start.microsecond or
                end.second or end.microsecond or (i and grid[i-1][1]!=start)):
                raise ValueError("Invalid minute grid")
            if end<=watermark: expected.add((start,end))
        if not expected or max(end for _,end in expected)!=watermark: raise ValueError("Unapproved watermark")
    except (ValueError,KeyError,TypeError,OverflowError,IndexError):
        reasons.append("CALENDAR_OR_TIME_RULES_INVALID"); return finish()
    observations=[]; pages=[]
    if any(type(row) is not Observation for row in bundle.observations) or any(type(p) is not Page for p in bundle.pages):
        reasons.append("CAPTURE_SCHEMA_INVALID"); return finish()
    observations=[row for row in bundle.observations if _symbol(row.symbol)==request.symbol]
    pages=[p for p in bundle.pages if p.symbol==request.symbol]
    observation_ids=[row.observation_id for row in observations]
    page_refs=[]; seen_keys=set(); seen_pages=set(); next_key=None
    if len(set(observation_ids))!=len(observation_ids) or any(not _text(v) for v in observation_ids):
        reasons.append("OBSERVATION_IDENTITY_INVALID")
    for i,page in enumerate(pages):
        if (not _text(page.page_id) or page.page_id in seen_pages or page.status!="OK" or
            not _text(page.request_id) or page.request_id!=pages[0].request_id or page.request_cursor!=next_key or
            any(type(k) not in (str,type(None)) for k in (page.request_cursor,page.next_cursor)) or
            (i<len(pages)-1 and (page.terminal is not False or page.next_cursor is None)) or
            (i==len(pages)-1 and (page.terminal is not True or page.next_cursor is not None))):
            reasons.append("PARTIAL_SOURCE")
        if page.next_cursor is not None:
            if page.next_cursor in seen_keys: reasons.append("REPEATED_PAGE_CURSOR")
            seen_keys.add(page.next_cursor)
        seen_pages.add(page.page_id); next_key=page.next_cursor
        page_refs.extend(page.observation_ids)
    if (not pages or any(not _text(ref) for ref in page_refs) or
        set(page_refs)!=set(observation_ids) or len(set(page_refs))!=len(page_refs)):
        reasons.append("PAGE_ROW_MANIFEST_MISMATCH")
    for row in observations:
        if (not _text(row.revision_id) or not _text(row.row_id) or type(row.snapshot) is not bytes or not row.snapshot or
            row.scope_hash!=source_hash or row.page_id not in seen_pages): reasons.append("ROW_LINEAGE_INVALID")
    if len({(row.page_id,row.row_id) for row in observations})!=len(observations):
        reasons.append("ROW_LINEAGE_INVALID")
    if reasons: return finish()
    seen_intervals=set(); knowledge=[]; ends=[]; lags=[]
    for row in observations:
        try:
            if row.availability_basis!=policy.availability_model or row.availability_reference!=approvals["availability"].reference:
                raise ValueError("Unreviewed availability")
            available=_time(row.available_at); receipt=_time(row.received_at); completion_receipt=_time(row.completion_received_at)
            if policy.availability_model=="SYNTHETIC_CAPTURE" and available<max(receipt,completion_receipt)+_clock_delta(context.clock.uncertainty_seconds):
                reasons.append("INVALID_KNOWLEDGE_BOUND"); continue
        except (ValueError,TypeError,OverflowError): reasons.append("AVAILABILITY_UNKNOWN"); continue
        if available>cutoff:
            exclusions.append((row.observation_id,"POST_CUTOFF")); continue  # Before unavailable payload inspection.
        try:
            stamp=_raw_time(row.raw_stamp,context.mapping,raw_zone)
            start=stamp if context.mapping.label=="START" else stamp-timedelta(minutes=1)
            end=start+timedelta(minutes=1)
            if (start,end) not in expected: reasons.append("OUTSIDE_EXPECTED_INTERVALS"); continue
            if (start,end) in seen_intervals: reasons.append("DUPLICATE_OR_CONFLICTING_INTERVAL")
            seen_intervals.add((start,end))
            if end>cutoff: reasons.append("INCOMPLETE_INTERVAL")
            if row.completed is not True: reasons.append("COMPLETION_UNVERIFIED")
            if row.finality!="FINAL": reasons.append("FINALITY_UNVERIFIED")
            if available<end: reasons.append("INVALID_KNOWLEDGE_BOUND")
            if len(row.values)!=5 or any(type(v) not in (int,float) or not math.isfinite(v) for v in row.values):
                reasons.append("INVALID_OHLCV"); continue
            o,h,l,c,v=row.values
            if min(o,h,l,c)<=0 or not l<=min(o,c)<=max(o,c)<=h or v<0:
                reasons.append("INVALID_OHLCV"); continue
            candles.append(Candle(row.observation_id,row.revision_id,row.raw_stamp,row.values,
                start.isoformat(),end.isoformat(),available.isoformat(),identity(row)))
            knowledge.append(available); ends.append(end); lags.append((available-end).total_seconds())
        except (ValueError,TypeError,OverflowError): reasons.append("INVALID_RAW_TIMESTAMP_OR_VALUE")
    if seen_intervals!=expected: reasons.append("EXPECTED_GRID_GAP")
    if not candles: reasons.append("NO_ELIGIBLE_OBSERVATIONS")
    if candles:
        if (cutoff-max(ends)).total_seconds()>policy.event_age: reasons.append("STALE_EVENT")
        if (cutoff-max(knowledge)).total_seconds()>policy.knowledge_age: reasons.append("STALE_KNOWLEDGE")
        if max(lags)>policy.delivery_lag: reasons.append("DELIVERY_LAG_EXCEEDED")
    return finish()


def to_pr31_arguments(report):
    """Explicit isolated synthetic view; does not import or invoke PR31."""
    if type(report) is not Report or not report.eligible or report.frame is None:
        raise ValueError("Only a sealed eligible synthetic frame may materialize")
    frame=report.frame; context=frame.context; request=frame.request
    if context.calendar.timezone!="UTC":
        raise ValueError("PR31 host-timezone bridge unreviewed; only synthetic UTC profile supported")
    if (report.context_hash!=identity(context) or report.request_hash!=identity(request) or
        frame.frame_hash!=identity((frame.candles,report.context_hash,report.request_hash))):
        raise ValueError("Frame/context binding mismatch")
    roles={a.role:a.reference for a in context.authorities}
    contract={name+"_authority":roles[name] for name in
              ("source","mapping","calendar","availability","completion","finality")}
    contract.update(source_sha256=context.source.artifact_hash,exchange_timezone=context.calendar.timezone,
                    intervals=[dict(raw_stamp=row.raw_stamp,start=row.start,end=row.end,available_at=row.available_at,
                                    completed=True,finality="FINAL") for row in frame.candles])
    rows=[dict(symbol=request.symbol,time=row.raw_stamp,source_sha256=context.source.artifact_hash,
               **dict(zip(("open","high","low","close","volume"),row.values))) for row in frame.candles]
    return dict(symbol=request.symbol,rows=rows,now=_time(request.cutoff),session=request.session_date,
                contract=contract,policy=dict(max_age_seconds=context.policy.event_age),
                pagination_complete=True,provider_error=None,synthetic=True)
