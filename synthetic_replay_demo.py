"""Prebuilt fictional UTC scenarios only. No input files, SDK, market feed or clock."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

from canonical_candles import (
    Source, Mapping, Calendar, Clock, Policy, TimeRules, Authority, Context,
    Observation, Page, Bundle, identity, subjects,
)
from synthetic_replay import Series, Step, ReplayInput

SCENARIOS = (
    ("conflict", "SPY bullish / QQQ bearish"),
    ("aligned", "Both bullish"),
    ("mixed", "No directional conjunction"),
    ("provisional", "QQQ provisional candle"),
    ("gap", "QQQ missing minute"),
    ("partial", "QQQ incomplete page"),
    ("unknown", "QQQ unknown availability"),
)
NOTICE = "Fictional 40-minute UTC session; not an exchange calendar or market history."


def _series(symbol, scenario):
    start = datetime(2026, 10, 23, 9, 30, tzinfo=timezone.utc)
    grid = tuple(((start + timedelta(minutes=i)).isoformat(),
                  (start + timedelta(minutes=i+1)).isoformat()) for i in range(40))
    scope = tuple(sorted(dict(
        provider="SYNTHETIC_OPEND", endpoint="SYNTHETIC_DEMO", sdk="SYNTHETIC_V1",
        opend="SYNTHETIC_V1", market="SYNTHETIC_US", interval="PT1M", timezone="UTC",
        tzdata="SYNTHETIC_FIXED", session="SYNTHETIC_RTH", adjustment="SYNTHETIC_FIXED",
        price_unit="USD", volume_unit="SHARES", entitlement="SYNTHETIC_ONLY",
    ).items()))
    source = Source(scope, "SYNTHETIC_BYTES", identity(("DEMO_SOURCE", symbol)))
    mapping = Mapping("START", identity(source), "ISO")
    calendar = Calendar("2026-10-23", grid[0][0], grid[-1][1], "UTC", "FICTIONAL_40_MINUTE_V1",
                        "2026-10-22T00:00:00Z", grid, False, "SYNTHETIC_CONTINUOUS")
    context = Context(source, mapping, calendar, Clock("SYNTHETIC_CLOCK", 0, "c"*64),
                      Policy(120, 120, 30, "FINAL_ONLY", "SYNTHETIC_CAPTURE"),
                      (TimeRules("UTC", "SYNTHETIC_FIXED", b""),), (),
                      identity(("DECLARED_DEMO_IMPLEMENTATION", 1)))
    context = replace(context, authorities=tuple(
        Authority(role, role+"-SYNTHETIC", "d"*64, subject, identity(source), True)
        for role, subject in subjects(context).items()))
    rows = []
    for i in range(40):
        stamp = grid[i][0]
        receipt = (start + timedelta(minutes=i+1, seconds=1)).isoformat()
        values = ((100, 101, 99, 100, 100) if scenario == "mixed" else
                  (200-i, 202-i, 199-i, 201-i, 100) if symbol == "QQQ" and scenario == "conflict"
                  else (100+i, 102+i, 99+i, 101+i, 100))
        snapshot = json.dumps(dict(symbol=symbol, raw_stamp=stamp, values=values),
                              sort_keys=True, separators=(",", ":")).encode()
        row = Observation(f"{symbol}-O-{i}", f"{symbol}-R-{i}", symbol, stamp, values,
                          receipt, "SYNTHETIC_CAPTURE", receipt, receipt, True, "FINAL",
                          "availability-SYNTHETIC", identity(source), symbol+"-P", str(i), snapshot)
        if symbol == "QQQ" and i == 34:
            if scenario == "provisional":
                row = replace(row, finality="PROVISIONAL")
            if scenario == "unknown":
                row = replace(row, available_at=None)
        if not (symbol == "QQQ" and scenario == "gap" and i == 10):
            rows.append(row)
    rows = tuple(rows)
    partial = symbol == "QQQ" and scenario == "partial"
    page = Page(symbol+"-P", symbol, symbol+"-Q", None, "MISSING" if partial else None,
                "OK", not partial, tuple(row.observation_id for row in rows))
    bundle = Bundle(symbol+"-SYNTHETIC-DEMO", rows, (page,), True, True, identity((rows, (page,))))
    return Series(symbol, bundle, context)


def make_demo(scenario="conflict"):
    if scenario not in {key for key, _ in SCENARIOS}:
        raise ValueError("Choose a predefined synthetic scenario")
    series = tuple(_series(symbol, scenario) for symbol in ("SPY", "QQQ"))
    steps = tuple(Step("2026-10-23", (
        datetime.fromisoformat(end) + timedelta(seconds=1)).isoformat(), end)
        for _, end in series[0].context.calendar.intervals)
    return ReplayInput(series, steps)
