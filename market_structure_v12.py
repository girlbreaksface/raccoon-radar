"""Pure synthetic v1.2 structure hypotheses; no EMA imports, I/O, orders or outcomes."""
from dataclasses import dataclass, replace
from decimal import (Decimal, Context as DecimalContext, localcontext, ROUND_HALF_EVEN,
                     InvalidOperation, DivisionByZero, Overflow)
import re

from canonical_candles import (
    FrozenRecord, Bundle, Context, Request, Report, canonicalize, identity, _time,
)

VERSION = "synthetic-market-structure-v12-hypothesis-1"
TERMINAL = ("FAILED_REVERSAL", "INVALIDATED_SETUP", "TREND_CONTINUATION")


@dataclass(frozen=True, slots=True)
class Config(FrozenRecord):
    trend_bars: int = 8
    consolidation_bars: int = 5
    min_move: str = "0.015"
    min_efficiency: str = "0.70"
    min_directional: str = "0.75"
    min_structure: str = "0.60"
    max_contraction: str = "0.55"
    max_width: str = "0.015"
    min_overlap: str = "0.75"
    max_drift: str = "0.50"
    min_touches: int = 2
    touch_fraction: str = "0.20"
    breakout_fraction: str = "0.10"
    retest_fraction: str = "0.20"
    confirmation_closes: int = 2
    max_retest_bars: int = 4
    max_range_bars: int = 20


@dataclass(frozen=True, slots=True)
class Setup(FrozenRecord):
    setup_id: str
    prior_trend: str
    support: str
    resistance: str
    formed_index: int
    formed_at: str
    measurements: tuple
    breakout_index: int | None = None
    retested: bool = False
    consecutive: int = 0


@dataclass(frozen=True, slots=True)
class Machine(FrozenRecord):
    classification: str = "INSUFFICIENT_EVIDENCE"
    stage: str = "AWAITING_STRUCTURE"
    prior_trend: str | None = None
    setup: Setup | None = None
    measurements: tuple = ()
    reasons: tuple = ("INSUFFICIENT_STRUCTURE_WARMUP",)
    scan_floor: int = 0


@dataclass(frozen=True, slots=True)
class Event(FrozenRecord):
    kind: str
    reason: str
    observed_at: str
    trigger_interval_end: str
    setup_id: str
    event_id: str


@dataclass(frozen=True, slots=True)
class Decision(FrozenRecord):
    symbol: str
    at: str
    data_status: str
    classification: str
    stage: str
    prior_trend: str | None
    potential_direction: str | None
    direction: str | None
    support: str | None
    resistance: str | None
    setup_id: str | None
    measurements: tuple
    reasons: tuple
    frame_hash: str | None
    config_hash: str
    event_ids: tuple
    decision_hash: str
    action: str = "WAIT"
    version: str = VERSION


@dataclass(frozen=True, slots=True)
class Tracker(FrozenRecord):
    symbol: str
    session: str
    context_hash: str
    config_hash: str
    evaluated_at: str
    candles: tuple
    machine: Machine
    events: tuple
    history: tuple
    seal: str
    version: str = VERSION


@dataclass(frozen=True, slots=True)
class Assessment(FrozenRecord):
    decision: Decision
    tracker: Tracker
    canonical_report: Report
    audit_hash: str


@dataclass(frozen=True, slots=True)
class Pair(FrozenRecord):
    at: str
    state: str
    directions: tuple
    classifications: tuple
    decision_hashes: tuple
    pair_hash: str


def _validate_config(config):
    if type(config) is not Config:
        raise TypeError("Typed immutable Config required")
    limits = dict(trend_bars=(3,100), consolidation_bars=(3,100),
                  min_touches=(1,config.consolidation_bars), confirmation_closes=(2,10),
                  max_retest_bars=(1,100), max_range_bars=(config.consolidation_bars,500))
    for name,(low,high) in limits.items():
        value=getattr(config,name)
        if type(value) is not int or not low<=value<=high:
            raise ValueError("Invalid integer parameter: "+name)
    if config.confirmation_closes>config.max_retest_bars+1:
        raise ValueError("Confirmation count cannot fit within the retest deadline")
    parsed={}
    positive=("min_move","max_contraction","max_width")
    for name in ("min_move","min_efficiency","min_directional","min_structure","max_contraction",
                 "max_width","min_overlap","max_drift","touch_fraction","breakout_fraction","retest_fraction"):
        raw=getattr(config,name)
        if type(raw) is not str:
            raise TypeError("Decimal-string threshold required: "+name)
        if re.fullmatch(r"[0-9]{1,3}(?:[.][0-9]{1,12})?",raw) is None:
            raise ValueError("Invalid decimal threshold: "+name)
        value=Decimal(raw)
        ceiling=Decimal("0.5") if name in ("touch_fraction","breakout_fraction","retest_fraction") else Decimal(1)
        if not 0<=value<=ceiling or (name in positive and value==0):
            raise ValueError("Threshold out of bounds: "+name)
        parsed[name]=value
    return parsed


def _opposite(direction):
    return "BEARISH" if direction=="BULLISH" else "BULLISH"


def _candidate(candles, index, config, params):
    total=config.trend_bars+config.consolidation_bars
    window=candles[index-total+1:index+1]
    values=[tuple(Decimal(str(v)) for v in bar.values) for bar in window]
    trend=values[:config.trend_bars]
    region=values[config.trend_bars:]
    closes=[v[3] for v in trend]
    net=closes[-1]-closes[0]
    direction="BULLISH" if net>0 else "BEARISH" if net<0 else None
    sign=1 if net>0 else -1
    path=sum((abs(b-a) for a,b in zip(closes,closes[1:])),Decimal(0))
    efficiency=abs(net)/path if path else Decimal(0)
    directional=Decimal(sum(sign*(b-a)>0 for a,b in zip(closes,closes[1:])))/(len(trend)-1)
    structure=Decimal(sum(sign*(b[1]-a[1])>0 and sign*(b[2]-a[2])>0
                          for a,b in zip(trend,trend[1:])))/(len(trend)-1)
    move=abs(net)/closes[0]
    tr=[]
    for i,v in enumerate(values):
        tr.append(v[1]-v[2] if i==0 else max(v[1]-v[2],abs(v[1]-values[i-1][3]),abs(v[2]-values[i-1][3])))
    trend_tr=sum(tr[:config.trend_bars])/config.trend_bars
    range_tr=sum(tr[config.trend_bars:])/config.consolidation_bars
    lower=min(v[2] for v in region)
    upper=max(v[1] for v in region)
    width=upper-lower
    contraction=range_tr/trend_tr if trend_tr else None
    width_ratio=width/((upper+lower)/2)
    overlap=Decimal(sum(max(a[2],b[2])<=min(a[1],b[1]) for a,b in zip(region,region[1:])))/(len(region)-1)
    drift=abs(region[-1][3]-region[0][3])/width if width else None
    touch=params["touch_fraction"]*width
    support_touches=sum(v[2]<=lower+touch for v in region)
    resistance_touches=sum(v[1]>=upper-touch for v in region)
    stats=(("trend_move",str(move)),("trend_efficiency",str(efficiency)),
           ("directional_fraction",str(directional)),("structure_fraction",str(structure)),
           ("trend_mean_true_range",str(trend_tr)),("range_mean_true_range",str(range_tr)),
           ("contraction_ratio",str(contraction) if contraction is not None else None),("width_fraction",str(width_ratio)),
           ("overlap_fraction",str(overlap)),("range_drift_fraction",str(drift) if drift is not None else None),
           ("support_touches",str(support_touches)),("resistance_touches",str(resistance_touches)))
    reasons=[]
    strong=direction is not None and move>=params["min_move"] and efficiency>=params["min_efficiency"] and directional>=params["min_directional"] and structure>=params["min_structure"]
    if not strong:
        reasons.append("NO_ESTABLISHED_TREND")
    if width<=0:
        reasons.append("ZERO_WIDTH_RANGE")
    if contraction is None:
        reasons.append("VOLATILITY_REFERENCE_UNAVAILABLE")
    elif contraction>params["max_contraction"]:
        reasons.append("VOLATILITY_NOT_CONTRACTED")
    if width_ratio>params["max_width"]:
        reasons.append("RANGE_TOO_WIDE")
    if overlap<params["min_overlap"]:
        reasons.append("PRICE_STRUCTURE_NOT_OVERLAPPING")
    if drift is not None and drift>params["max_drift"]:
        reasons.append("RANGE_DRIFT_EXCEEDED")
    if min(support_touches,resistance_touches)<config.min_touches:
        reasons.append("BOUNDARY_TOUCHES_INSUFFICIENT")
    return direction if strong else None, lower, upper, stats, tuple(reasons)


def _process(machine, candles, index, config, params, context_hash, cutoff):
    bar=candles[index]
    new_event=None
    def event(kind, reason, setup):
        return Event(kind,reason,cutoff,bar.end,setup.setup_id,
                     identity((VERSION,kind,reason,cutoff,bar.end,setup.setup_id)))
    def terminal(kind, reason):
        result=replace(machine,classification=kind,stage="TERMINAL",reasons=(reason,),scan_floor=index+1)
        return result,event(kind,reason,machine.setup)
    if machine.classification=="TREND_CONTINUATION" and machine.setup is not None:
        # The recorded breakout remains in history, but its current direction cannot
        # survive a close back beyond the broken boundary's wrong-side tolerance.
        prior=machine.setup
        lower,upper=Decimal(prior.support),Decimal(prior.resistance)
        sign=1 if prior.prior_trend=="BULLISH" else -1
        boundary=upper if sign==1 else lower
        if sign*(Decimal(str(bar.values[3]))-boundary)<-params["retest_fraction"]*(upper-lower):
            return terminal("INVALIDATED_SETUP","CONTINUATION_INVALIDATED")
    if machine.setup is None or machine.classification in TERMINAL:
        total=config.trend_bars+config.consolidation_bars
        if index+1-machine.scan_floor<total:
            if machine.classification in TERMINAL:
                return replace(machine,reasons=tuple(dict.fromkeys(machine.reasons+("AWAITING_NEW_STRUCTURE",)))),None
            return replace(machine,reasons=("INSUFFICIENT_STRUCTURE_WARMUP",)),None
        direction,lower,upper,stats,reasons=_candidate(candles,index,config,params)
        if reasons:
            if machine.classification in TERMINAL:
                return machine,None
            return replace(machine,prior_trend=direction,measurements=stats,reasons=reasons),None
        setup=Setup(identity((VERSION,identity(config),context_hash,candles[index-total+1:index+1])),
                    direction,str(lower),str(upper),index,cutoff,stats)
        result=Machine("REVERSAL_WATCH","CONSOLIDATING",direction,setup,stats,
                       ("RANGE_FORMED_NO_BREAKOUT",),machine.scan_floor)
        return result,event("REVERSAL_WATCH","QUALIFIED_CONSOLIDATION",setup)
    setup=machine.setup
    lower,upper=Decimal(setup.support),Decimal(setup.resistance)
    width=upper-lower
    buffer=params["breakout_fraction"]*width
    tolerance=params["retest_fraction"]*width
    close,high,low=(Decimal(str(v)) for v in (bar.values[3],bar.values[1],bar.values[2]))
    opposite=_opposite(setup.prior_trend)
    sign=1 if opposite=="BULLISH" else -1
    boundary=upper if sign==1 else lower
    if machine.classification=="CONFIRMED_STRUCTURAL_REVERSAL":
        if sign*(close-boundary)<-tolerance:
            return terminal("INVALIDATED_SETUP","CONFIRMED_REVERSAL_INVALIDATED")
        return machine,None
    if high>upper+buffer and low<lower-buffer:
        return terminal("INVALIDATED_SETUP","AMBIGUOUS_TWO_SIDED_EXCURSION")
    if setup.breakout_index is None:
        if config.consolidation_bars+index-setup.formed_index>config.max_range_bars:
            return terminal("INVALIDATED_SETUP","CONSOLIDATION_EXPIRED")
        up,down=close>upper+buffer,close<lower-buffer
        direction="BULLISH" if up else "BEARISH" if down else None
        if direction==setup.prior_trend:
            return terminal("TREND_CONTINUATION","ESTABLISHED_TREND_CLOSE_BREAKOUT")
        if direction==opposite:
            setup=replace(setup,breakout_index=index,consecutive=1)
            result=replace(machine,stage="AWAITING_RETEST",setup=setup,reasons=("OPPOSITE_CLOSE_BREAKOUT",))
            return result,event("REVERSAL_WATCH","OPPOSITE_CLOSE_BREAKOUT",setup)
        reason="WICK_ONLY_NO_CLOSE_BREAKOUT" if high>upper+buffer or low<lower-buffer else "RANGE_FORMED_NO_BREAKOUT"
        return replace(machine,reasons=(reason,)),None
    if index-setup.breakout_index>config.max_retest_bars:
        return terminal("FAILED_REVERSAL","RETEST_TIMEOUT")
    touched=low<=boundary+tolerance and high>=boundary-tolerance
    if sign*(close-boundary)<=0:
        reason="FAILED_RETEST" if touched and sign*(close-boundary)<-tolerance else "BREAKOUT_REENTERED_RANGE"
        return terminal("FAILED_REVERSAL",reason)
    outside=sign*(close-boundary)>buffer
    setup=replace(setup,retested=setup.retested or (touched and outside),
                  consecutive=setup.consecutive+1 if outside else 0)
    if setup.retested and setup.consecutive>=config.confirmation_closes:
        result=replace(machine,classification="CONFIRMED_STRUCTURAL_REVERSAL",stage="CONFIRMED",
                       setup=setup,reasons=("RETEST_AND_HOLD_CONFIRMED",))
        return result,event("CONFIRMED_STRUCTURAL_REVERSAL","RETEST_AND_HOLD_CONFIRMED",setup)
    return replace(machine,setup=setup,reasons=("AWAITING_RETEST_AND_HOLD",)),new_event


def _tracker_seal(tracker):
    return identity(replace(tracker,seal=""))


def _decision_seal(decision):
    return identity(replace(decision,decision_hash=""))


def assess(bundle, context, request, *, config=Config(), previous=None, synthetic=False):
    if synthetic is not True:
        raise ValueError("Explicit synthetic-only research required")
    if type(bundle) is not Bundle or type(context) is not Context or type(request) is not Request:
        raise TypeError("Typed immutable canonical inputs required")
    if bundle.synthetic is not True:
        raise ValueError("Real records are not authorized")
    if request.symbol not in ("SPY","QQQ"):
        raise ValueError("Exact SPY/QQQ request required")
    params=_validate_config(config)
    context_hash,config_hash=identity(context),identity(config)
    cutoff=_time(request.cutoff)
    if previous is not None:
        if (type(previous) is not Tracker or previous.version!=VERSION or previous.seal!=_tracker_seal(previous) or
            previous.context_hash!=context_hash or previous.config_hash!=config_hash or
            previous.symbol!=request.symbol or previous.session!=request.session_date):
            raise ValueError("Tracker seal/context/config/symbol/session mismatch; start a separate run")
        if cutoff<=_time(previous.evaluated_at) or len(previous.history)>=512:
            raise ValueError("Increasing cutoff and bounded 512-step run required")
    report=canonicalize(bundle,context,request)
    candles=previous.candles if previous is not None else ()
    machine=previous.machine if previous is not None else Machine()
    events=previous.events if previous is not None else ()
    history=previous.history if previous is not None else ()
    blocked=not report.eligible
    reasons=report.reasons+(("ENGINE_READY_REQUEST_REQUIRED",) if request.mode!="ENGINE_READY" else ())
    if report.eligible:
        current=report.frame.candles
        if len(current)>1000:
            blocked=True
            reasons=("STRUCTURE_FRAME_BUDGET_EXCEEDED",)
        elif current[:len(candles)]!=candles:
            blocked=True
            reasons=("PREFIX_REVISION_CHANGED",)
        else:
            with localcontext(DecimalContext(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999,
                    capitals=1,clamp=0,flags=[],traps=[InvalidOperation,DivisionByZero,Overflow])):
                for index in range(len(candles),len(current)):
                    machine,new_event=_process(machine,current,index,config,params,context_hash,request.cutoff)
                    if new_event is not None:
                        events=events+(new_event,)
            candles=current
            reasons=machine.reasons
    setup=machine.setup if not blocked else None
    classification=machine.classification if not blocked else "INSUFFICIENT_EVIDENCE"
    direction=None
    potential=None
    if not blocked and setup is not None:
        if classification=="CONFIRMED_STRUCTURAL_REVERSAL":
            direction=_opposite(setup.prior_trend)
        elif classification=="TREND_CONTINUATION":
            direction=setup.prior_trend
        elif classification=="REVERSAL_WATCH":
            potential=_opposite(setup.prior_trend)
    event_ids=tuple(e.event_id for e in events if e.observed_at==request.cutoff)
    decision=Decision(request.symbol,request.cutoff,"BLOCKED" if blocked else report.status,classification,
        "DATA_BLOCKED" if blocked else machine.stage,machine.prior_trend if not blocked else None,
        potential,direction,setup.support if setup else None,setup.resistance if setup else None,
        setup.setup_id if setup else None,machine.measurements if not blocked else (),tuple(reasons),
        report.frame.frame_hash if not blocked and report.frame else None,config_hash,event_ids,"")
    decision=replace(decision,decision_hash=_decision_seal(decision))
    tracker=Tracker(request.symbol,request.session_date,context_hash,config_hash,request.cutoff,candles,
                    machine,events,history+(decision,),"")
    tracker=replace(tracker,seal=_tracker_seal(tracker))
    return Assessment(decision,tracker,report,identity((VERSION,bundle,context,request,config,
                      previous.seal if previous else None,decision,tracker.seal)))


def compare(spy, qqq):
    if (type(spy) is not Decision or type(qqq) is not Decision or spy.version!=VERSION or qqq.version!=VERSION or
        spy.symbol!="SPY" or qqq.symbol!="QQQ" or
        spy.at!=qqq.at or spy.config_hash!=qqq.config_hash or
        spy.decision_hash!=_decision_seal(spy) or qqq.decision_hash!=_decision_seal(qqq)):
        raise ValueError("Aligned sealed independent SPY/QQQ decisions required")
    if "BLOCKED" in (spy.data_status,qqq.data_status):
        state="PEER_DATA_UNAVAILABLE"
    elif "INSUFFICIENT_EVIDENCE" in (spy.classification,qqq.classification):
        state="PEER_INSUFFICIENT_EVIDENCE"
    else:
        left,right=spy.direction,qqq.direction
        state=("NO_CONFIRMED_DIRECTION" if left is None and right is None else
               "SINGLE_DIRECTION" if left is None or right is None else
               "AGREEMENT_"+left if left==right else "CONFLICT")
    values=(spy.at,state,(spy.direction,qqq.direction),(spy.classification,qqq.classification),
            (spy.decision_hash,qqq.decision_hash))
    return Pair(*values,identity((VERSION,values)))
