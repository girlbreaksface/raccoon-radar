"""Deterministic, offline replay of normalized historical market data."""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from math import isfinite
import json
from pathlib import Path
import re

from futures_spike_radar import (
    Bar, MINUTE, Option, PAIRS, Session, compare_volume_baselines, record_paper_entry,
)

SECOND = timedelta(seconds=1)
HORIZON = timedelta(minutes=5)
SLIP = Decimal(".005")
FEE = Decimal(".65")


def timestamp(value):
    # datetime cannot represent exchange nanoseconds. Exporters must round
    # availability up, and conservatively resolve event ties before export.
    if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z", value):
        raise ValueError(f"Expected a UTC timestamp at microsecond precision: {value}")
    return datetime.fromisoformat(value[:-1]).replace(tzinfo=timezone.utc)


def evidence(provenance, row, coverage):
    source = provenance[row["source"]]
    if source["coverage"] != coverage:
        raise ValueError(f"Expected {coverage} coverage for {row['source']}")
    observed = timestamp(row["observed"])
    available = timestamp(row["available"])
    if available < observed:
        raise ValueError("Availability precedes observation")
    return observed, available


def normalize(bundle):
    """Validate an explicit UTC cash calendar and normalize immutable rows."""
    provenance = bundle["sources"]
    synthetic = bundle["kind"] == "synthetic"
    if bundle["kind"] not in ("synthetic", "historical") or bundle["version"] != 1:
        raise ValueError("Unsupported bundle kind or version")
    for source in provenance.values():
        for key in ("provider", "dataset", "coverage", "artifact", "rights_reference"):
            if not isinstance(source[key], str) or not source[key].strip():
                raise ValueError(f"Missing provenance field: {key}")
        allowed = {"synthetic"} if synthetic else {"recorded", "capture_proxy"}
        if source["clock"] not in allowed:
            raise ValueError("Unsupported availability clock")

    evidence(provenance, bundle["calendar"], "common_cash_calendar")
    calendar_available = timestamp(bundle["calendar"]["available"])
    sessions = {}
    bars = {}
    windows = {}
    closes = {}
    previous_close = dict.fromkeys(PAIRS, calendar_available)
    for row in sorted(bundle["sessions"], key=lambda r: (r["opening"], r["root"])):
        session = Session(timestamp(row["opening"]), timestamp(row["closing"]))
        root = row["root"]
        if root not in PAIRS:
            raise ValueError("Unsupported futures root")
        if closes.setdefault(session.opening, session.closing) != session.closing:
            raise ValueError("Both roots must share the same cash session")
        if (previous_close[root] > session.opening or session.closing <= session.opening
                or any(t.second or t.microsecond for t in (session.opening, session.closing))
                or (session.opening, root) in windows):
            raise ValueError("Invalid or overlapping cash sessions")
        if not re.fullmatch(
                row["root"] + r"[FGHJKMNQUVXZ]\d{1,4}", row["contract"]):
            raise ValueError("Expected a dated outright ES/NQ contract")
        start, end = timestamp(row["from"]), timestamp(row["until"])
        if (not session.opening <= start < end <= session.closing
                or any(t.second or t.microsecond for t in (start, end))):
            raise ValueError("Invalid minute coverage window")
        windows[session.opening, root] = (session, root, row["contract"], start, end)
        sessions[row["id"]] = windows[session.opening, root]
        if len(sessions) != len(windows):
            raise ValueError("Duplicate session ID")
        previous_close[root] = session.closing

    ordered_calendar = sorted(closes.items())
    if any(close > next_open for (_, close), (next_open, _) in
           zip(ordered_calendar, ordered_calendar[1:])):
        raise ValueError("Overlapping common cash sessions")

    for row in bundle["bars"]:
        session, root, contract, start, end = sessions[row["session"]]
        symbol = row["symbol"]
        if symbol not in (root, PAIRS[root]):
            raise ValueError("Unexpected bar symbol")
        observed, available = evidence(
            provenance, row, "dated_futures" if symbol == root else "consolidated_equity",
        )
        if (not start < observed <= end or (observed - start) % MINUTE
                or row["instrument"] != (contract if symbol == root else symbol)):
            raise ValueError("Invalid bar interval end or instrument")
        key = row["session"], symbol, observed
        if key in bars:
            raise ValueError("Duplicate bar or unsupported revision")
        if any(type(row[name]) not in (int, float) for name in ("high", "low", "close")):
            raise ValueError("Bar prices must be numeric")
        if type(row["complete"]) is not bool or type(row["delayed"]) is not bool:
            raise ValueError("Bar quality fields must be boolean")
        bars[key] = Bar(symbol, row["instrument"], observed, available, row["high"],
                        row["low"], row["close"], row["volume"],
                        row["complete"], row["delayed"])

    quotes = defaultdict(dict)
    for row in bundle["quotes"]:
        session, root, _, start, end = sessions[row["session"]]
        observed, available = evidence(provenance, row, "consolidated_options")
        if not start <= observed < end or row["symbol"] != PAIRS[root]:
            raise ValueError("Quote outside declared session coverage")
        key = observed, available
        series = quotes[row["session"], row["contract"]]
        if key in series:
            raise ValueError("Ambiguous quote timestamps")
        if type(row["delayed"]) is not bool:
            raise ValueError("Quote delay field must be boolean")
        fields = {}
        for name, coverage in (("greeks", "point_in_time_greeks"),
                               ("volume", "asof_option_volume"),
                               ("open_interest", "published_open_interest"),
                               ("definition", "point_in_time_definition")):
            field = row[name]
            event, published = evidence(provenance, field, coverage)
            if event > observed:
                raise ValueError(f"{name} observation follows quote")
            if name == "greeks" and (observed - event > 5 * SECOND
                                     or published > timestamp(row["available"])):
                raise ValueError("Greeks must be contemporaneous and available with quote")
            if published > timestamp(row["available"]):
                raise ValueError(f"{name} was unavailable when the quote became available")
            fields[name] = field["value"]
        definition = fields["definition"]
        if definition["standard_deliverable"] is not True:
            raise ValueError("Only standard option deliverables are supported")
        greeks = fields["greeks"]
        if any(type(greeks[name]) not in (int, float) for name in
               ("delta", "gamma", "theta_per_day", "vega_per_point")):
            raise ValueError("Greeks must be numeric")
        series[key] = Option(
            row["symbol"], row["contract"], definition["right"],
            timestamp(definition["expires"]), observed, available,
            Decimal(row["bid"]), Decimal(row["ask"]), row["bid_size"], row["ask_size"],
            fields["volume"], fields["open_interest"], greeks["delta"], greeks["gamma"],
            greeks["theta_per_day"], greeks["vega_per_point"],
            definition["multiplier"], row["delayed"],
        )
    return sessions, bars, quotes


def snapshot(quotes, session_id, when):
    result = []
    for (key, _), series in sorted(quotes.items()):
        if key != session_id:
            continue
        visible = [q for q in series.values() if q.received <= when]
        if visible:
            result.append(max(visible, key=lambda q: (q.observed, q.received)))
    return result


def exit_pnl(candidate, quote, when):
    """Hypothetical liquidation at a displayed, fresh bid for one contract."""
    if (quote is None or quote.delayed or when - quote.observed > 5 * SECOND
            or quote.expires <= when or quote.multiplier != 100
            or type(quote.bid_size) is not int or quote.bid_size < 1
            or not quote.bid.is_finite() or not quote.ask.is_finite()
            or not 0 < quote.bid <= quote.ask <= 1000000):
        return None
    return quote.bid * (1 - SLIP) * 100 - candidate.entry_premium - 2 * FEE


def replay(bundle):
    sessions, bars, quotes = normalize(bundle)
    history = defaultdict(list)
    ledger = defaultdict(tuple)
    pending = defaultdict(dict)
    metrics = {mode: Counter(decisions=0, signals=0, hypothetical_entries=0,
                             priced_exit=0, missing_exit=0, modeled_net_pnl=Decimal(0))
               for mode in ("rolling_20_minute", "prior_session_same_minute")}
    agreement = Counter()
    decisions = []
    schedule = []
    for key, (session, root, contract, start, end) in sessions.items():
        for offset in range(1, (end - start) // MINUTE + 1):
            minute = start + offset * MINUTE
            bar = bars.get((key, root, minute))
            if (bar and bar.complete and not bar.delayed and bar.received - bar.end <= 5 * SECOND
                    and all(isfinite(v) for v in (bar.low, bar.close, bar.high))
                    and 0 < bar.low <= bar.close <= bar.high):
                history[root, contract, minute - session.opening].append((session, bar))
            if offset >= 21 and minute + 5 * SECOND < end:
                schedule.append((minute, root, key))
    for minute, root, key in sorted(schedule):
        session, _, contract, _, _ = sessions[key]
        etf = PAIRS[root]
        now = minute + 5 * SECOND
        chain = snapshot(quotes, key, now)
        by_contract = {q.contract: q for q in chain}
        windows = [
            [bars[k] for offset in range(20, -1, -1)
             if (k := (key, symbol, minute - offset * MINUTE)) in bars]
            for symbol in (root, etf)
        ]
        offset = minute - session.opening
        prior = [(s, b) for s, b in history[root, contract, offset]
                 if timedelta(0) < session.opening - s.opening <= timedelta(days=30)]
        spikes = compare_volume_baselines(root, *windows, session, now, prior)
        agreement["|".join(mode for mode, spike in spikes.items() if spike.direction) or "neither"] += 1
        for mode, spike in spikes.items():
            counts = metrics[mode]
            counts["decisions"] += 1
            counts["signals"] += bool(spike.direction)
            counts.update("signal:" + flag for flag in spike.flags)
            outcomes = []
            for index, (due, candidate) in tuple(pending[mode].items()):
                if due != now or ledger[mode][index].symbol != etf:
                    continue
                pnl = exit_pnl(candidate, by_contract.get(candidate.contract), now)
                outcomes.append({"contract": candidate.contract, "modeled_pnl": pnl})
                counts["missing_exit" if pnl is None else "priced_exit"] += 1
                if pnl is not None:
                    counts["modeled_net_pnl"] += pnl
                    entries = list(ledger[mode])
                    entries[index] = replace(entries[index], closed_at=now)
                    ledger[mode] = tuple(entries)
                del pending[mode][index]
            entries, ranking = record_paper_entry(
                replace(spike, at=minute), chain, now, ledger[mode],
            )
            counts.update("ranking:" + flag for flag in ranking.flags if spike.direction)
            counts.update("contract:" + reason for _, reason in ranking.rejected)
            if ranking.candidates:
                counts["hypothetical_entries"] += 1
                pending[mode][len(entries) - 1] = (now + HORIZON, ranking.candidates[0])
                ledger[mode] = entries
            decisions.append({"session": key, "at": now, "bar_end": minute, "baseline": mode,
                              "spike": asdict(spike), "ranking": asdict(ranking),
                              "hypothetical_exits": outcomes})
    for mode, remaining in pending.items():
        metrics[mode]["missing_exit"] += len(remaining)
    return {"kind": bundle["kind"], "execution": "hypothetical",
            "sources": bundle["sources"], "signal_agreement": agreement,
            "metrics": dict(metrics), "decisions": decisions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    raw = args.bundle.read_bytes()
    report = replay(json.loads(raw))
    report["input_sha256"] = sha256(raw).hexdigest()
    print(json.dumps(report, default=str, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
