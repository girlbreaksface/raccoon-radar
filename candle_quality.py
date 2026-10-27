"""Pure, non-mutating candle diagnostics against caller-declared raw stamp bounds.

No database, file, provider, calendar lookup, timestamp shifting or candle repair.
"""
import math
from collections import Counter, defaultdict
from collections.abc import Mapping
from datetime import datetime, timedelta


def audit_candles(rows, *, expected_start, expected_end):
    """Audit naive raw minute stamps; inclusive bounds are explicit hypotheses.

    Coverage counts only valid OHLCV minutes. Duplicates/order/outside rows remain
    separate quality issues even when the declared coverage is present.
    """
    start = datetime.strptime(expected_start, "%H:%M").time()
    end = datetime.strptime(expected_end, "%H:%M").time()
    if start > end:
        raise ValueError("Expected bounds must be within one session, start <= end")
    groups = defaultdict(list)
    invalid = []
    row_count = 0
    for index, row in enumerate(rows):
        row_count += 1
        if not isinstance(row, Mapping):
            invalid.append({"index": index, "reason": "invalid_row"})
            continue
        symbol = str(row.get("symbol") or "").strip().upper()
        if symbol.startswith("US."):
            symbol = symbol[3:]
        if not symbol:
            invalid.append({"index": index, "reason": "invalid_symbol"})
            continue
        try:
            stamp = datetime.strptime(str(row.get("time") or row.get("bar_time_et")),
                                      "%Y-%m-%d %H:%M:%S")
            if stamp.second != 0:
                raise ValueError("Not a minute boundary")
        except (TypeError, ValueError):
            invalid.append({"index": index, "reason": "invalid_timestamp"})
            continue
        reason = None
        try:
            o, h, low, c, volume = (float(row[k]) for k in
                                    ("open", "high", "low", "close", "volume"))
            if not all(math.isfinite(v) for v in (o, h, low, c, volume)):
                reason = "nonfinite_ohlcv"
            elif min(o, h, low, c) <= 0:
                reason = "nonpositive_price"
            elif volume < 0:
                reason = "negative_volume"
            elif not low <= min(o, c) <= max(o, c) <= h:
                reason = "ohlc_bounds"
        except (KeyError, TypeError, ValueError, OverflowError):
            reason = "invalid_ohlcv"
        if reason:
            invalid.append({"index": index, "reason": reason})
        groups[(symbol, stamp.date())].append((stamp, reason is None))

    sessions = []
    for (symbol, day), entries in sorted(groups.items()):
        first = datetime.combine(day, start)
        last = datetime.combine(day, end)
        expected = {first + timedelta(minutes=i)
                    for i in range(int((last - first).total_seconds() / 60) + 1)}
        counts = Counter(stamp for stamp, _ in entries)
        valid = {stamp for stamp, ok in entries if ok and stamp in expected}
        missing = sorted(expected - valid)
        duplicates = [{"timestamp": stamp.strftime("%Y-%m-%d %H:%M:%S"),
                       "count": count} for stamp, count in sorted(counts.items())
                      if count > 1]
        outside = sum(stamp not in expected for stamp, _ in entries)
        disorder = sum(b[0] < a[0] for a, b in zip(entries, entries[1:]))
        invalid_count = sum(not ok for _, ok in entries)
        sessions.append({
            "symbol": symbol, "session": day.isoformat(),
            "row_count": len(entries), "valid_unique_minutes": len(valid),
            "expected_minutes": len(expected),
            "missing_minutes": [stamp.strftime("%H:%M") for stamp in missing],
            "duplicates": duplicates, "invalid_ohlcv_rows": invalid_count,
            "outside_expected_count": outside, "out_of_order_count": disorder,
            "coverage_complete": not missing,
            "quality_ok": not (missing or duplicates or outside or disorder or invalid_count),
        })
    return {
        "schema_version": 1, "row_count": row_count,
        "expected_start": expected_start, "expected_end": expected_end,
        "timestamp_semantics": "UNVERIFIED", "invalid_rows": invalid,
        "sessions": sessions,
        "limitations": [
            "Bounds are caller-declared raw-stamp hypotheses, not an exchange calendar.",
            "No provider semantics, completed-bar status or trading edge is verified.",
            "Unparseable symbol/timestamp rows cannot be assigned to a session.",
            "No empty sessions are inferred; absent symbol-days require an external schedule.",
        ],
    }
