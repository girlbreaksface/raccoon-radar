"""Deterministic SYNTHETIC-ONLY PR31-profile observation replay; no I/O or outcomes."""
from dataclasses import dataclass
from canonical_candles import (
    FrozenRecord, Bundle, Context, Request, canonicalize, identity, _time,
)
from pinned_timezone_bridge import BridgeReport, evaluate, consumer_dict

VERSION = "synthetic-observation-replay-v1"
PROFILE = "PR31_FIRST_CLOSE_EMA_35_FINAL_ONLY"


@dataclass(frozen=True, slots=True)
class Series(FrozenRecord):
    symbol: str
    bundle: Bundle
    context: Context


@dataclass(frozen=True, slots=True)
class Step(FrozenRecord):
    session_date: str
    cutoff: str
    watermark: str


@dataclass(frozen=True, slots=True)
class ReplayInput(FrozenRecord):
    series: tuple
    steps: tuple


@dataclass(frozen=True, slots=True)
class Cell(FrozenRecord):
    symbol: str
    state: str
    bias: str | None
    data_quality: str
    reasons: tuple
    evidence: BridgeReport
    action: str = "WAIT"


@dataclass(frozen=True, slots=True)
class Point(FrozenRecord):
    step: Step
    cells: tuple
    pair: str
    decision_hash: str


@dataclass(frozen=True, slots=True)
class ReplayResult(FrozenRecord):
    profile: str
    version: str
    input_hash: str
    points: tuple
    run_hash: str


def _validate(data, synthetic):
    if synthetic is not True:
        raise ValueError("Only explicitly synthetic replay is authorized")
    if type(data) is not ReplayInput:
        raise TypeError("Immutable ReplayInput required")
    if (len(data.series) != 2 or any(type(s) is not Series for s in data.series)
            or {s.symbol for s in data.series} != {"SPY", "QQQ"}):
        raise ValueError("One exact SPY and QQQ series required")
    for source in data.series:
        if type(source.bundle) is not Bundle or type(source.context) is not Context:
            raise TypeError("Typed immutable bundle/context required")
        if source.bundle.synthetic is not True:
            raise ValueError("Real observations are not authorized")
    if not 1 <= len(data.steps) <= 120:
        raise ValueError("Explicit grid of 1..120 steps required")
    previous = watermark = None
    for step in data.steps:
        if type(step) is not Step:
            raise TypeError("Typed immutable Step required")
        try:
            cutoff, end = _time(step.cutoff), _time(step.watermark)
            if (end > cutoff or (previous is not None and cutoff <= previous)
                    or (watermark is not None and end < watermark)):
                raise ValueError("Unordered grid")
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValueError("Strict chronological aware microsecond grid required") from exc
        previous, watermark = cutoff, end


def _cell(source, step):
    request = Request(source.symbol, step.session_date, step.cutoff, step.watermark, "ENGINE_READY")
    report = canonicalize(source.bundle, source.context, request)
    result = evaluate(report)
    bias = None
    if not report.eligible:
        state = "DATA_BLOCKED"
    elif result.eligible:
        state = "CANDIDATE"
        bias = consumer_dict(result)["bias"]
    elif "NO_DIRECTIONAL_CONJUNCTION" in result.reasons:
        state = "NO_CANDIDATE"
    else:
        state = "PROFILE_BLOCKED"
    return Cell(source.symbol, state, bias, report.status, result.reasons, result)


def _pair(cells):
    if any(c.state == "DATA_BLOCKED" for c in cells):
        return "PEER_DATA_UNAVAILABLE"
    if any(c.state == "PROFILE_BLOCKED" for c in cells):
        return "PEER_PROFILE_UNAVAILABLE"
    left, right = (c.bias for c in cells)
    if left is None and right is None:
        return "BOTH_NO_TRADE"
    if left is None or right is None:
        return "SINGLE_CANDIDATE"
    return "AGREEMENT_" + left if left == right else "CONFLICT"


def replay(data, *, synthetic=False):
    """Re-evaluate each explicit cutoff; no trade events, cooldown, labels or persistence.

    input/run hashes include all supplied evidence. decision_hash intentionally includes
    only visible frame/consumer state, not unavailable future payloads. Hashes are
    identity checks, not authenticated source or historical-availability evidence.
    """
    _validate(data, synthetic)
    input_hash = identity((VERSION, PROFILE, data))
    points = []
    ordered = tuple(sorted(data.series, key=lambda s: ("SPY", "QQQ").index(s.symbol)))
    for step in data.steps:
        cells = tuple(_cell(source, step) for source in ordered)
        pair = _pair(cells)
        visible = tuple((c.symbol, c.state, c.bias, c.data_quality, c.reasons,
                         c.evidence.canonical_report.frame.frame_hash
                         if c.evidence.canonical_report.frame is not None else None,
                         c.evidence.consumer_hash) for c in cells)
        points.append(Point(step, cells, pair, identity((VERSION, PROFILE, step, visible, pair))))
    points = tuple(points)
    return ReplayResult(PROFILE, VERSION, input_hash, points,
                        identity((VERSION, PROFILE, input_hash, points)))
