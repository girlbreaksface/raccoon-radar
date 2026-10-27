"""Reproducible chronological DIRECTION event study, not executable P/L.

Features are evaluated as-of first. Future labels are attached separately using
a declared next-eligible-minute OPEN and fully observed same-session horizon.
"""
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timedelta
from statistics import mean

from direction_engine import Config, VERSION, evaluate


def _stamp(value):
    return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")


def _ceil_minute(value):
    floor = value.replace(second=0,microsecond=0)
    return floor if value == floor else floor+timedelta(minutes=1)


def _outcome_valid(row, symbol, start, cutoff):
    try:
        end, available = _stamp(row["interval_end_et"]), _stamp(row["available_at_et"])
        values = [float(row[k]) for k in ("open","high","low","close","volume")]
        o,h,low,c,volume = values
        return (str(row["symbol"]).strip().upper().removeprefix("US.") == symbol and
                row.get("complete") is True and _stamp(row["interval_start_et"]) == start and
                end-start == timedelta(minutes=1) and available >= end and available <= cutoff and
                all(math.isfinite(v) for v in values) and min(o,h,low,c)>0 and volume>=0 and
                low<=min(o,c)<=max(o,c)<=h)
    except (KeyError,TypeError,ValueError,OverflowError):
        return False


def replay_session(rows, *, symbol, session_open_et, session_close_et, interval_evidence,
                   config=Config(), horizon_minutes=3, outcome_as_of_et=None):
    """Snapshots never see later prices. Labels are hypothetical ETF movements."""
    config.validate()
    if type(horizon_minutes) is not int or horizon_minutes < 1:
        raise ValueError("horizon_minutes must be a positive integer")
    rows = list(rows)
    symbol = str(symbol).strip().upper().removeprefix("US.")
    close = _stamp(session_close_et)
    cutoff = _stamp(outcome_as_of_et) if outcome_as_of_et else close
    known_times = sorted({_stamp(row["available_at_et"]) for row in rows
                          if _stamp(row["available_at_et"]) <= cutoff})
    by_start = defaultdict(list)
    for row in rows:
        by_start[_stamp(row["interval_start_et"])].append(row)
    snapshots, events = [], []
    next_entry_allowed = None
    for known in known_times:
        snapshot = evaluate(rows,symbol=symbol,session_open_et=session_open_et,
            session_close_et=session_close_et,as_of_et=known.strftime("%Y-%m-%d %H:%M:%S"),
            interval_evidence=interval_evidence,config=config)
        snapshots.append(snapshot)
        if snapshot["signal"] == "NO TRADE":
            continue
        entry = _ceil_minute(known)
        if next_entry_allowed is not None and entry < next_entry_allowed:
            continue
        next_entry_allowed = entry+timedelta(minutes=horizon_minutes)
        exit_end = entry+timedelta(minutes=horizon_minutes)
        missing = None
        window = []
        if exit_end > close:
            missing = "HORIZON_OUTSIDE_SESSION"
        else:
            for offset in range(horizon_minutes):
                start = entry+timedelta(minutes=offset)
                matches = by_start.get(start,[])
                if not matches:
                    missing = "MISSING_ENTRY_BAR" if offset == 0 else "MISSING_OUTCOME_BAR"
                    break
                if len(matches) != 1:
                    missing = "DUPLICATE_OUTCOME_BAR"
                    break
                if not _outcome_valid(matches[0],symbol,start,cutoff):
                    missing = "INVALID_OR_UNAVAILABLE_OUTCOME_BAR"
                    break
                window.append(matches[0])
        value = None
        if not missing:
            direction = 1 if snapshot["signal"] == "BULLISH CANDIDATE" else -1
            value = direction*(float(window[-1]["close"])/float(window[0]["open"])-1)*100
            if not math.isfinite(value):
                missing, value = "OUTCOME_NUMERIC_OVERFLOW", None
        events.append(dict(
            symbol=symbol,session=session_open_et[:10],signal=snapshot["signal"],
            known_at_et=known.strftime("%Y-%m-%d %H:%M:%S"),
            raw_timestamp=snapshot["timestamp"],feature_hash=snapshot["data_hash"],
            observations=snapshot["observations"],data_quality=snapshot["data_quality"],
            entry_assumed_at_et=entry.strftime("%Y-%m-%d %H:%M:%S"),
            exit_interval_end_et=exit_end.strftime("%Y-%m-%d %H:%M:%S"),
            entry_open=float(window[0]["open"]) if window else None,
            exit_close=float(window[-1]["close"]) if not missing else None,
            directional_etf_move_pct=value,outcome_missing_reason=missing))
    return dict(snapshots=snapshots,events=events)


def study(sessions, *, train_through, test_start, test_end, freeze_id, code_revision,
          config=Config(), horizon_minutes=3, prior_inspection="UNKNOWN"):
    """Fixed date split; no tuning, ranking or outcome-based setup selection."""
    config.validate()
    train_day, first_test, last_test = (datetime.strptime(v,"%Y-%m-%d").date()
                                      for v in (train_through,test_start,test_end))
    if (not train_day < first_test <= last_test or
            any(not isinstance(v,str) or not v.strip() for v in (freeze_id,code_revision)) or
            prior_inspection not in ("UNKNOWN","PREVIOUSLY_VIEWED","DECLARED_NOT_VIEWED")):
        raise ValueError("Disjoint chronological dates and freeze/code references are required")
    if type(horizon_minutes) is not int or horizon_minutes < 1:
        raise ValueError("Invalid outcome horizon")
    sessions = list(sessions)
    dates, keys = set(), set()
    for session in sessions:
        if not session["rows"]:
            raise ValueError("Empty sessions cannot establish observed train/test coverage")
        day = _stamp(session["session_open_et"]).date()
        key = (str(session["symbol"]).strip().upper().removeprefix("US."),day)
        if key in keys:
            raise ValueError("Duplicate symbol/session")
        keys.add(key)
        dates.add(day)
    train_dates = sorted(d for d in dates if d <= train_day)
    test_dates = sorted(d for d in dates if first_test <= d <= last_test)
    if not train_dates or not test_dates:
        raise ValueError("Both train and test need observed sessions")
    encoded = json.dumps(sorted(sessions,key=lambda s:(s["session_open_et"],s["symbol"])),
                         sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    result = {"manifest":{
        "engine_version":VERSION,"config":asdict(config),"horizon_minutes":horizon_minutes,
        "freeze_id":freeze_id,"code_revision":code_revision,
        "dataset_sha256":hashlib.sha256(encoded).hexdigest(),
        "train_dates":[d.isoformat() for d in train_dates],
        "test_dates":[d.isoformat() for d in test_dates],
        "excluded_dates":[d.isoformat() for d in sorted(dates-set(train_dates)-set(test_dates))],
        "prior_inspection":prior_inspection,
        "evaluation_status":"RETROSPECTIVE_CHRONOLOGICAL",
        "train_outcome_cutoff_et":train_through+" 23:59:59",
        "test_outcome_cutoff_et":test_end+" 23:59:59",
        "selection":"Fixed hypotheses; greedy non-overlapping planned entry windows per symbol/session",
        "entry_assumption":"Next minute boundary at/after availability; open-price proxy, not modeled fills",
    },"limitations":[
        "No real dataset or evidence of predictive edge is supplied by this code.",
        "ETF directional movement only; not executed P/L, options returns or VWAP fills.",
        "No costs/slippage/spread; correlation and repeated testing remain risks.",
        "Freeze/code/inspection references are caller assertions, not authenticated.",
        "Previously inspected history is not untouched out-of-sample data.",
    ]}
    for bucket in ("train","test"):
        result[bucket] = {"events":[],"decision_counts":Counter(),"no_trade_reasons":Counter()}
    for session in sorted(sessions,key=lambda s:(s["session_open_et"],s["symbol"])):
        day = _stamp(session["session_open_et"]).date()
        bucket = "train" if day in train_dates else "test" if day in test_dates else None
        if bucket is None:
            continue
        replay = replay_session(**session,config=config,horizon_minutes=horizon_minutes,
                                outcome_as_of_et=(train_through if bucket=="train" else test_end)+" 23:59:59")
        target = result[bucket]
        target["events"].extend(replay["events"])
        for snapshot in replay["snapshots"]:
            target["decision_counts"][snapshot["signal"]] += 1
            target["no_trade_reasons"].update(snapshot["reasons"])
    for bucket in ("train","test"):
        target = result[bucket]
        values = [event["directional_etf_move_pct"] for event in target["events"]
                  if event["directional_etf_move_pct"] is not None]
        target["decision_counts"] = dict(sorted(target["decision_counts"].items()))
        target["no_trade_reasons"] = dict(sorted(target["no_trade_reasons"].items()))
        target.update(valid_outcomes=len(values),missing_outcomes=len(target["events"])-len(values),
                      mean_directional_etf_move_pct=mean(values) if values else None,
                      events_count=len(target["events"]))
    return result
