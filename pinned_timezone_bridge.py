"""Pure SYNTHETIC-ONLY bridge with pinned in-memory UTC/New York timezone rules.

No provider, host ZoneInfo fallback, files, capture, database, GUI or order API. PR33's
original non-UTC materialization block remains intact. Public entry consumes Report only.
"""
from dataclasses import dataclass
from datetime import datetime,timezone
import math

import _pr31_pinned_kernel as kernel
from canonical_candles import FrozenRecord,Context,Report,canonicalize,identity,_zone

REFERENCE_SHA256="5e6e2b647ff6f763c356e34a1adde2b375470d2f00ff6811fc37e74d2b718a29"
BRIDGE_VERSION="synthetic-pinned-tz-bridge-v1"
SUPPORTED_ZONES=("UTC","America/New_York")


@dataclass(frozen=True,slots=True)
class FrozenMap(FrozenRecord):
    items:tuple

@dataclass(frozen=True,slots=True)
class FrozenList(FrozenRecord):
    items:tuple

@dataclass(frozen=True,slots=True)
class BridgeReport(FrozenRecord):
    canonical_report:Report
    eligible:bool
    status:str
    reasons:tuple
    consumer:FrozenMap|None
    consumer_hash:str|None
    bridge_hash:str
    action:str="WAIT"


def _freeze(value):
    if type(value) is dict:
        if any(type(k) is not str for k in value): raise ValueError("Consumer keys must be strings")
        return FrozenMap(tuple((k,_freeze(value[k])) for k in sorted(value)))
    if type(value) in (list,tuple): return FrozenList(tuple(_freeze(v) for v in value))
    if type(value) is float:
        if not math.isfinite(value): raise ValueError("Nonfinite consumer output")
        return value
    if type(value) in (str,int,bool,type(None)): return value
    raise ValueError("Unsupported consumer output type")


def _thaw(value):
    if type(value) is FrozenMap: return {k:_thaw(v) for k,v in value.items}
    if type(value) is FrozenList: return [_thaw(v) for v in value.items]
    return value


def consumer_dict(result):
    """New mutable DISPLAY copy only; preserve BridgeReport for authoritative lineage."""
    if type(result) is not BridgeReport or result.consumer is None:
        raise ValueError("No consumer result available")
    return _thaw(result.consumer)


@dataclass(frozen=True,slots=True)
class _PinnedZones(FrozenRecord):
    context:Context

    def __call__(self,name):
        if type(name) is not str or name not in SUPPORTED_ZONES or name!=self.context.calendar.timezone:
            raise ValueError("Unsupported/unbound consumer timezone")
        return _zone(name,self.context)  # Validates name/version; reads immutable BytesIO only.


def _arguments(report):
    """Private translation of an ALREADY revalidated canonical report, not a public gate."""
    frame=report.frame; context=frame.context; request=frame.request
    roles={a.role:a.reference for a in context.authorities}
    contract={role+"_authority":roles[role] for role in
              ("source","mapping","calendar","availability","completion","finality")}
    contract.update(source_sha256=context.source.artifact_hash,exchange_timezone=context.calendar.timezone,
        intervals=[dict(raw_stamp=row.raw_stamp,start=row.start,end=row.end,available_at=row.available_at,
                        completed=True,finality="FINAL") for row in frame.candles])
    rows=[dict(symbol=request.symbol,time=row.raw_stamp,source_sha256=context.source.artifact_hash,
               **dict(zip(("open","high","low","close","volume"),row.values))) for row in frame.candles]
    return dict(symbol=request.symbol,rows=rows,now=datetime.fromisoformat(request.cutoff.replace("Z","+00:00")).astimezone(timezone.utc),
        session=request.session_date,contract=contract,policy=dict(max_age_seconds=context.policy.event_age),
        pagination_complete=True,provider_error=None,synthetic=True)


def evaluate(report):
    """Recompute the full canonical seal before numeric work; all results remain WAIT."""
    if type(report) is not Report: raise TypeError("Immutable canonical Report required")
    def result(reasons,consumer=None,eligible=False):
        frozen=None if consumer is None else _freeze(consumer)
        reasons=tuple(sorted(set(reasons)))
        status="SYNTHETIC_CANDIDATE" if eligible else "NO_TRADE"
        digest=identity((BRIDGE_VERSION,REFERENCE_SHA256,report,status,reasons,frozen))
        return BridgeReport(report,eligible,status,reasons,frozen,
                            identity(frozen) if frozen is not None else None,digest)
    if not report.eligible or report.frame is None:
        return result(report.reasons or ("CANONICAL_REPORT_NOT_ELIGIBLE",))
    frame=report.frame
    try:
        checked=canonicalize(report.bundle,frame.context,frame.request)
        if not checked.eligible or identity(checked)!=identity(report):
            return result(("CANONICAL_REPORT_SEAL_MISMATCH",))
    except (ValueError,TypeError,OverflowError):
        return result(("CANONICAL_REVALIDATION_FAILED",))
    if frame.context.calendar.timezone not in SUPPORTED_ZONES:
        return result(("UNSUPPORTED_CONSUMER_TIMEZONE",))
    zones=_PinnedZones(frame.context)
    try:
        output=kernel.assess(**_arguments(checked),zone_factory=zones)
    except (ValueError,TypeError,OverflowError):
        return result(("PINNED_CONSUMER_CONVERSION_BLOCKED",))
    if (type(output) is not dict or output.get("synthetic") is not True or output.get("action")!="WAIT" or
        type(output.get("eligible")) is not bool):
        return result(("INVALID_CONSUMER_OUTPUT",))
    codes=output.get("reasons")
    if (type(codes) not in (list,tuple) or any(type(code) is not str or not code for code in codes) or
        (output["eligible"] and (codes or output.get("bias") not in ("BULLISH","BEARISH")))):
        return result(("INVALID_CONSUMER_OUTPUT",))
    try:
        _freeze(output)
    except (ValueError,TypeError,OverflowError):
        return result(("INVALID_CONSUMER_OUTPUT",))
    eligible=output["eligible"] and output.get("bias") in ("BULLISH","BEARISH")
    reasons=() if eligible else tuple(output.get("reasons") or ("NO_DIRECTIONAL_CANDIDATE",))
    return result(reasons,output,eligible)
