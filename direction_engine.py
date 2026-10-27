"""Deterministic, read-only directional RESEARCH hypotheses for SPY/QQQ.

Canonical completed intervals must be supplied explicitly. Raw provider stamps
are never interpreted, shifted or saved here. No trading or confidence scores.
"""
import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

VERSION = "direction-hypothesis-v1"


@dataclass(frozen=True)
class Config:
    ema_fast: int = 9
    ema_slow: int = 21
    volume_lookback: int = 20
    volume_multiplier: float = 1.2
    opening_minutes: int = 15
    max_age_minutes: int = 2

    def validate(self):
        integers = (self.ema_fast, self.ema_slow, self.volume_lookback,
                    self.opening_minutes, self.max_age_minutes)
        if (any(type(v) is not int for v in integers) or
                (self.ema_fast,self.ema_slow) != (9,21) or
                self.volume_lookback < 1 or self.opening_minutes < 1 or
                self.max_age_minutes < 0 or
                type(self.volume_multiplier) not in (int,float) or
                not math.isfinite(self.volume_multiplier) or self.volume_multiplier <= 0):
            raise ValueError("Invalid research hypothesis configuration")


def _stamp(value):
    return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")


def _symbol(value):
    value = str(value or "").strip().upper()
    return value[3:] if value.startswith("US.") else value


def _ema(values, period):
    """SMA seed, then alpha=2/(period+1); no across-session carry."""
    out = [None] * len(values)
    if len(values) >= period:
        out[period - 1] = sum(values[:period]) / period
        alpha = 2 / (period + 1)
        for i in range(period, len(values)):
            out[i] = alpha * values[i] + (1 - alpha) * out[i - 1]
    return out


def evaluate(rows, *, symbol, session_open_et, session_close_et, as_of_et,
             interval_evidence=None, config=Config()):
    """Evaluate only completed, available intervals as of a caller-supplied time.

    Evidence status VERIFIED is a caller assertion, not verified by this module;
    SYNTHETIC is allowed for fixtures and is retained in every output. Missing
    evidence fails closed. All timestamps are explicit naive ET wall timestamps.
    """
    config.validate()
    symbol = _symbol(symbol)
    supplied = interval_evidence if isinstance(interval_evidence, Mapping) else {}
    evidence = {key:supplied.get(key) if isinstance(supplied.get(key),str) else None
                for key in ("status","reference")}
    result = dict(schema_version=1, engine_version=VERSION, symbol=symbol,
        signal="NO TRADE", timestamp=None, interval_end_et=None, as_of_et=as_of_et,
        interval_evidence=evidence, config=asdict(config), data_hash=None,
        data_quality={"status":"INVALID", "eligible_bars":0, "issues":[]},
        observations={"indicator_status":"NOT_EVALUATED"}, reasons=[],
        limitations=["Hypothesis only; no validated trading edge or executable P/L.",
                     "HLC3 volume-weighted candle proxy is NOT trade-level VWAP.",
                     "Interval/session evidence is caller supplied; provider semantics are not inferred."])

    def stop(reasons, status):
        result["reasons"] = list(dict.fromkeys(reasons))
        result["data_quality"]["issues"] = result["reasons"][:]
        result["data_quality"]["status"] = status
        return result

    try:
        opening, closing, as_of = map(_stamp, (session_open_et,session_close_et,as_of_et))
        if (symbol not in ("SPY","QQQ") or opening >= closing or
                opening.date() != closing.date() or opening.second or closing.second):
            raise ValueError("Invalid symbol/session")
    except (ValueError, TypeError):
        return stop(["INVALID_CONTEXT"], "INVALID")

    issues = []
    if evidence.get("status") not in ("VERIFIED","SYNTHETIC") or not evidence.get("reference"):
        issues.append("UNVERIFIED_INTERVAL_MAPPING")
    bars = []
    for row in rows:
        if not isinstance(row, Mapping):
            issues.append("INVALID_ROW")
            continue
        try:
            available = _stamp(row["available_at_et"])
        except (KeyError, TypeError, ValueError):
            issues.append("INVALID_AVAILABILITY")
            continue
        if available > as_of:
            continue  # Future data, including its prices, must not affect this result.
        try:
            start, end = _stamp(row["interval_start_et"]), _stamp(row["interval_end_et"])
            raw = row["raw_timestamp"]
            if not isinstance(raw,str) or not raw.strip():
                issues.append("INVALID_RAW_TIMESTAMP")
                continue
            result["timestamp"], result["interval_end_et"] = raw, row["interval_end_et"]
            if _symbol(row["symbol"]) != symbol:
                issues.append("WRONG_SYMBOL")
            if start < opening or end > closing:
                issues.append("OUTSIDE_SESSION")
            if end - start != timedelta(minutes=1) or start.second or end.second or available < end:
                issues.append("INVALID_INTERVAL")
            if row.get("complete") is not True:
                issues.append("INCOMPLETE_CANDLE")
            o,h,low,c,volume = (float(row[k]) for k in ("open","high","low","close","volume"))
            if (not all(math.isfinite(v) for v in (o,h,low,c,volume)) or
                    min(o,h,low,c) <= 0 or volume < 0 or
                    not low <= min(o,c) <= max(o,c) <= h):
                issues.append("INVALID_OHLCV")
                continue
            bars.append(dict(start=start,end=end,available=available,raw=raw,
                             open=o,high=h,low=low,close=c,volume=volume))
        except (KeyError, ValueError, TypeError, OverflowError):
            issues.append("INVALID_ROW")
    result["data_quality"]["eligible_bars"] = len(bars)
    if not bars:
        return stop(issues + ["NO_COMPLETED_DATA"], "MISSING" if not issues else "INVALID")

    counts = Counter(b["start"] for b in bars)
    if any(n > 1 for n in counts.values()):
        issues.append("DUPLICATE_INTERVAL")
    if any(a["start"] > b["start"] for a,b in zip(bars,bars[1:])):
        issues.append("OUT_OF_ORDER")
    latest = max(b["end"] for b in bars)
    expected = {opening + timedelta(minutes=i)
                for i in range(max(0,int((min(latest,closing)-opening).total_seconds()/60)))}
    missing = sorted(expected - set(counts))
    result["data_quality"]["missing_interval_starts"] = [t.strftime("%Y-%m-%d %H:%M:%S") for t in missing]
    if missing:
        issues.append("MISSING_MINUTES")
    if issues:
        return stop(issues, "UNVERIFIED" if issues == ["UNVERIFIED_INTERVAL_MAPPING"] else "INVALID")
    bars = list(bars)
    last = bars[-1]
    result["timestamp"], result["interval_end_et"] = last["raw"], last["end"].strftime("%Y-%m-%d %H:%M:%S")
    visible = [{**{k:v for k,v in b.items() if k not in ("start","end","available")},
                "start":b["start"].isoformat(),"end":b["end"].isoformat(),
                "available":b["available"].isoformat()} for b in bars]
    result["data_hash"] = hashlib.sha256(json.dumps(visible,sort_keys=True,
        separators=(",",":"),allow_nan=False).encode()).hexdigest()
    result["data_quality"]["evidence_status"] = evidence.get("status")
    if (as_of-last["end"]).total_seconds() > config.max_age_minutes * 60:
        return stop(["STALE_DATA"], "STALE")
    result["data_quality"]["status"] = "READY"
    obs = result["observations"]
    obs.update(indicator_status="WARMUP",bars=len(bars),last_close=last["close"],last_volume=last["volume"],
               vwap_basis="HLC3_VOLUME_WEIGHTED_CANDLE_PROXY")
    minimum = max(config.ema_slow+1,config.volume_lookback+1,config.opening_minutes+1,6)
    if len(bars) < minimum:
        return stop(["INSUFFICIENT_WARMUP"], "READY")
    closes = [b["close"] for b in bars]
    fast, slow = _ema(closes,config.ema_fast), _ema(closes,config.ema_slow)
    baseline = sum(b["volume"] for b in bars[-config.volume_lookback-1:-1])/config.volume_lookback
    total_volume = sum(b["volume"] for b in bars)
    proxy = sum((b["high"]+b["low"]+b["close"])/3*b["volume"] for b in bars)/total_volume if total_volume else None
    derived = (fast[-1],fast[-2],slow[-1],baseline,total_volume,
               config.volume_multiplier*baseline)
    if any(not math.isfinite(value) for value in derived) or (proxy is not None and not math.isfinite(proxy)):
        return stop(["NUMERIC_OVERFLOW"], "INVALID")
    opening_bars = bars[:config.opening_minutes]
    or_high, or_low = max(b["high"] for b in opening_bars), min(b["low"] for b in opening_bars)
    prior5 = bars[-6:-1]
    five_high, five_low = max(b["high"] for b in prior5), min(b["low"] for b in prior5)
    volume_confirmed = baseline > 0 and last["volume"] >= config.volume_multiplier*baseline
    bull = last["close"] > fast[-1] > slow[-1] and fast[-1] > fast[-2]
    bear = last["close"] < fast[-1] < slow[-1] and fast[-1] < fast[-2]
    above, below = last["close"] > or_high, last["close"] < or_low
    breakout, breakdown = last["close"] > five_high, last["close"] < five_low
    rejection = last["high"] >= fast[-2] and last["open"] <= fast[-2] and last["close"] < fast[-2] and last["close"] < last["open"]
    support = last["low"] <= fast[-2] and last["open"] >= fast[-2] and last["close"] > fast[-2] and last["close"] > last["open"]
    obs.update(indicator_status="EVALUATED",ema9=fast[-1],ema21=slow[-1],ema_fast_period=config.ema_fast,
        ema_slow_period=config.ema_slow,prior_fast_ema=fast[-2],
        vwap_candle_proxy=proxy,above_vwap_proxy=proxy is not None and last["close"]>proxy,
        below_vwap_proxy=proxy is not None and last["close"]<proxy,volume_baseline=baseline,
        volume_ratio=last["volume"]/baseline if baseline else None,
        volume_confirmed=volume_confirmed,opening_range_high=or_high,opening_range_low=or_low,
        above_opening_range=above,below_opening_range=below,
        prior_five_high=five_high,prior_five_low=five_low,
        five_bar_break_above=breakout,five_bar_break_below=breakdown,
        ema9_rejection=rejection,ema9_support=support,
        bullish_trend=bull,bearish_trend=bear)
    reasons = []
    if not baseline:
        reasons.append("ZERO_VOLUME_BASELINE")
    if proxy is None:
        reasons.append("VWAP_PROXY_UNAVAILABLE")
    if not volume_confirmed:
        reasons.append("VOLUME_NOT_CONFIRMED")
    if not bull and not bear:
        reasons.append("NO_ALIGNED_TREND")
    if not above and not below:
        reasons.append("INSIDE_OPENING_RANGE")
    if not (breakout or breakdown or support or rejection):
        reasons.append("NO_PRICE_ACTION_PATTERN")
    if proxy is not None and ((bull and last["close"]<=proxy) or (bear and last["close"]>=proxy)):
        reasons.append("VWAP_PROXY_NOT_ALIGNED")
    if (bull and not above) or (bear and not below):
        reasons.append("OPENING_RANGE_NOT_ALIGNED")
    if (bull and not (breakout or support)) or (bear and not (breakdown or rejection)):
        reasons.append("DIRECTIONAL_PATTERN_NOT_CONFIRMED")
    bullish = bull and volume_confirmed and above and proxy is not None and last["close"] > proxy and (breakout or support)
    bearish = bear and volume_confirmed and below and proxy is not None and last["close"] < proxy and (breakdown or rejection)
    if bullish != bearish:
        result["signal"] = "BULLISH CANDIDATE" if bullish else "BEARISH CANDIDATE"
        return result
    if not reasons:
        reasons.append("CONDITIONS_NOT_ALIGNED")
    result["reasons"] = reasons
    return result
