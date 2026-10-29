"""Read-only evidence gates. No default freshness policy or provider semantics.

An explicit evidence parameter is a caller-supplied trust contract, not an automatic
source-verification mechanism. The dashboard supplies none and cannot mark bias verified.
Pagination/quality helpers are offline-ready but deliberately not wired into fetch workers.
"""
from copy import deepcopy
from datetime import datetime, timezone
import math
import re


def symbol_name(value):
    if not isinstance(value, str):
        return None
    value = value.strip().upper()
    if value.startswith("US."):
        value = value[3:]
    return value if value in ("SPY", "QQQ") else None


def aware_time(value):
    if not isinstance(value, str):
        raise ValueError("Explicit aware ISO timestamp required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp offset required; no assumed ET mapping")
    return parsed.astimezone(timezone.utc)


def evaluate_signals(rows, *, now, max_age_seconds=None, evidence=None):
    """Assess each symbol, using explicit event/availability times and reviewed policy.

    Source hashes/authority and verified availability must be supplied by a trusted
    caller and bound to each row. No mtime/fetch-time fallback, no market-session claim.
    Any malformed matching row blocks that symbol rather than falling back silently.
    """
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Controlled aware evaluation clock required")
    rows = tuple(rows)
    try:
        policy_ok = (type(max_age_seconds) in (int, float) and
                     math.isfinite(max_age_seconds) and max_age_seconds > 0)
    except OverflowError:
        policy_ok = False
    evidence_ok = (isinstance(evidence, dict) and
        isinstance(evidence.get("source_sha256"), str) and
        re.fullmatch(r"[a-f0-9]{64}", evidence["source_sha256"]) is not None and
        isinstance(evidence.get("authority"), str) and bool(evidence["authority"].strip()) and
        evidence.get("availability_verified") is True)
    result = {}
    for symbol in ("SPY", "QQQ"):
        matching = [r for r in rows if isinstance(r, dict) and symbol_name(r.get("symbol")) == symbol]
        reasons, parsed = [], []
        if not matching:
            reasons.append("NO_ROWS")
        if not policy_ok:
            reasons.append("FRESHNESS_POLICY_UNREVIEWED")
        if not evidence_ok:
            reasons.append("SOURCE_AVAILABILITY_UNVERIFIED")
        for row in matching:
            if not isinstance(row.get("bias"), str) or row["bias"] not in ("BULLISH", "BEARISH", "NO TRADE"):
                reasons.append("INVALID_BIAS")
                continue
            try:
                event = aware_time(row.get("event_at"))
                available = aware_time(row.get("available_at"))
            except (TypeError, ValueError, OverflowError):
                reasons.append("TIMESTAMP_UNVERIFIED")
                continue
            if available < event:
                reasons.append("AVAILABILITY_BEFORE_EVENT")
            if available > now or event > now:
                reasons.append("FUTURE_INFORMATION")
            if evidence_ok and row.get("source_sha256") != evidence["source_sha256"]:
                reasons.append("SOURCE_MISMATCH")
            parsed.append((event, available, row["bias"]))
        latest = max((p[0] for p in parsed), default=None)
        candidates = [p for p in parsed if p[0] == latest]
        if len({p[2] for p in candidates}) > 1:
            reasons.append("CONFLICTING_LATEST_BIAS")
        bias = candidates[0][2] if candidates else None
        if latest is not None and policy_ok and (now-latest).total_seconds() > max_age_seconds:
            reasons.append("STALE_EVENT")
        if bias == "NO TRADE":
            reasons.append("NO_TRADE")
        eligible = bool(candidates) and not reasons
        invalid = any(r in reasons for r in ("NO_ROWS", "INVALID_BIAS"))
        result[symbol] = dict(eligible=eligible, bias=bias if eligible else None,
            display=bias if eligible or reasons == ["NO_TRADE"] else (
                "UNAVAILABLE" if invalid else "UNVERIFIED"),
            event_at=latest.isoformat() if latest else None, reasons=sorted(set(reasons)))
    return result


def collect_pages(request, symbol, request_kwargs, *, max_pages=20):
    """Preserve raw pages; no eligible/completed-bar claim from pagination success.

    Injected request returns (status, table-or-list, continuation-key), status0=success.
    This helper never imports/opens a provider, writes a file or retries on failure.
    """
    if type(max_pages) is not int or not 1 <= max_pages <= 1000:
        raise ValueError("Explicit bounded page limit required")
    if "page_req_key" in request_kwargs:
        raise ValueError("Pagination starts at the first page")
    rows, reasons, seen, page = [], [], set(), None
    for count in range(1, max_pages+1):
        kwargs = deepcopy(request_kwargs)
        if page is not None:
            kwargs["page_req_key"] = page
        try:
            status, data, page = request(symbol, **kwargs)
            if status != 0:
                reasons.append("PROVIDER_PAGE_ERROR")
                break
            values = (r for _, r in data.iterrows()) if hasattr(data, "iterrows") else iter(data)
            page_rows = [deepcopy(dict(row)) for row in values]
            rows.extend(page_rows)
        except Exception as exc:
            reasons.append("PAGE_EXCEPTION:" + type(exc).__name__)
            break
        if page is None or page == "":
            return dict(rows=rows, pagination_complete=True, pages=count, reasons=[])
        key = repr(page)
        if key in seen:
            reasons.append("REPEATED_PAGE_KEY")
            break
        seen.add(key)
    else:
        reasons.append("PAGE_LIMIT")
    return dict(rows=rows, pagination_complete=False, pages=count, reasons=reasons)


def assess_candles(rows, *, symbol, session, pagination_complete=False):
    """Raw-stamp diagnostics only: gaps do NOT establish missing canonical intervals.

    No assumed session calendar, timestamp mapping, finality, completion or availability.
    Therefore eligibility always fails closed even when numeric/page checks pass.
    """
    if symbol not in ("SPY", "QQQ"):
        raise ValueError("Exact supported symbol required")
    datetime.strptime(session, "%Y-%m-%d")
    stamps, invalid, counts, reasons = [], [], {}, []
    if pagination_complete is not True:
        reasons.append("PAGINATION_INCOMPLETE")
    for index, row in enumerate(rows):
        try:
            if symbol_name(row.get("symbol")) != symbol:
                continue
            stamp = row.get("time_key", row.get("time"))
            parsed = datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S")
            if parsed.date().isoformat() != session:
                raise ValueError("Wrong session")
            values = [float(row[k]) for k in ("open", "high", "low", "close", "volume")]
            o, h, l, c, v = values
            if (not all(math.isfinite(x) for x in values) or min(o,h,l,c) <= 0 or
                    not l <= min(o,c) <= max(o,c) <= h or v < 0):
                raise ValueError("Invalid OHLCV")
            stamps.append(stamp)
            counts[stamp] = counts.get(stamp, 0)+1
        except (AttributeError, TypeError, ValueError, KeyError, OverflowError):
            invalid.append(index)
    unique = sorted(counts)
    gaps = [[a,b] for a,b in zip(unique, unique[1:]) if
            (datetime.fromisoformat(b)-datetime.fromisoformat(a)).total_seconds() > 60]
    duplicates = [s for s in unique if counts[s] > 1]
    if not stamps:
        reasons.append("NO_VALID_ROWS")
    if invalid:
        reasons.append("INVALID_OHLCV_OR_TIMESTAMP")
    if duplicates:
        reasons.append("DUPLICATE_STAMPS")
    if gaps:
        reasons.append("RAW_STAMP_GAPS")
    reasons.append("INTERVAL_COMPLETION_AVAILABILITY_UNVERIFIED")
    return dict(eligible=False, raw_stamps=stamps, duplicates=duplicates,
                raw_stamp_gaps=gaps, invalid_rows=invalid, reasons=reasons)
