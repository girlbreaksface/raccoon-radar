"""PRIVATE synthetic PR31 kernel extraction. Only assess's required resolver is changed.
Reference SHA256 5e6e2b647ff6f763c356e34a1adde2b375470d2f00ff6811fc37e74d2b718a29.
Not a standalone data-validation/provider API. Public entry is pinned_timezone_bridge.
"""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, localcontext, Context, ROUND_HALF_EVEN
import hashlib
import json
import math
import re
import struct

AUTHORITIES = ('source_authority', 'mapping_authority', 'calendar_authority', 'availability_authority', 'completion_authority', 'finality_authority')
NOTICE = 'SYNTHETIC OFFLINE RESEARCH ONLY; no verified live bias, news or order execution'

def _time(value):
    t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError('Aware timestamp required')
    return t.astimezone(timezone.utc)

def _symbol(value):
    if not isinstance(value, str):
        return None
    value = value.strip().upper()
    if value.startswith('US.'):
        value = value[3:]
    return value if value in ('SPY', 'QQQ') else None

def _typed(value):
    """Reversible typed raw evidence, including float64 nonfinite bits; strict JSON."""
    if value is None:
        return ['null']
    if type(value) is bool:
        return ['bool', value]
    if type(value) is int:
        return ['int', str(value)]
    if type(value) is float:
        return ['float64', struct.pack('!d', value).hex()]
    if type(value) is str:
        return ['str', value]
    if type(value) in (tuple, list):
        return [type(value).__name__, [_typed(v) for v in value]]
    if type(value) is dict and all((type(k) is str for k in value)):
        return ['dict', [[k, _typed(value[k])] for k in sorted(value)]]
    raise ValueError('Evidence accepts explicit JSON-like Python values only')

def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')

def _hash(value):
    return hashlib.sha256(_json(value)).hexdigest()

def assess(symbol, rows, *, now, session, contract=None, policy=None, pagination_complete=False, provider_error=None, synthetic=False, zone_factory):
    if synthetic is not True:
        raise ValueError('Only explicit synthetic inputs authorized')
    if symbol not in ('SPY', 'QQQ'):
        raise ValueError('Exact symbol required')
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('Controlled aware clock required')
    datetime.strptime(session, '%Y-%m-%d')
    rows = tuple(rows)
    if len(rows) > 10000:
        raise ValueError('Synthetic snapshot exceeds10000 rows')
    selected = [r for r in rows if isinstance(r, dict) and _symbol(r.get('symbol')) == symbol]
    reasons = []
    if not selected:
        reasons.append('NO_ROWS')
    if pagination_complete is not True:
        reasons.append('PAGINATION_INCOMPLETE')
    if provider_error is not None:
        reasons.append('PROVIDER_ERROR')
    limit = policy.get('max_age_seconds') if isinstance(policy, dict) else None
    try:
        policy_ok = type(limit) in (int, float) and math.isfinite(limit) and (limit > 0)
    except OverflowError:
        policy_ok = False
    if not policy_ok:
        reasons.append('FRESHNESS_POLICY_UNREVIEWED')
    contract = contract if isinstance(contract, dict) else {}
    for key in AUTHORITIES:
        if not isinstance(contract.get(key), str) or not contract[key].strip():
            reasons.append(key.upper() + '_UNVERIFIED')
    source = contract.get('source_sha256')
    if not isinstance(source, str) or re.fullmatch('[a-f0-9]{64}', source) is None:
        reasons.append('SOURCE_HASH_UNVERIFIED')
    mapped = {}
    intervals = []
    try:
        zone = contract['exchange_timezone']
        zone = timezone.utc if zone == 'UTC' else zone_factory(zone)
        definitions = contract['intervals']
        if not isinstance(definitions, (list, tuple)) or not 1 <= len(definitions) <= 10000:
            raise ValueError('Expected interval grid required')
        for item in definitions:
            stamp = item['raw_stamp']
            if not isinstance(stamp, str) or not stamp or stamp in mapped:
                raise ValueError('Duplicate mapping')
            start, end, available = (_time(item[k]) for k in ('start', 'end', 'available_at'))
            if (end - start).total_seconds() != 60 or start.astimezone(zone).date().isoformat() != session:
                raise ValueError('Wrong session or interval length')
            if available < end:
                reasons.append('AVAILABILITY_BEFORE_INTERVAL_END')
            if end > now or available > now:
                reasons.append('FUTURE_INFORMATION')
            if item.get('completed') is not True:
                reasons.append('INCOMPLETE_CANDLE')
            if item.get('finality') != 'FINAL':
                reasons.append('FINALITY_UNVERIFIED')
            mapped[stamp] = (start, end, available)
            intervals.append((start, end))
        intervals.sort()
        if any((a[1] > b[0] for a, b in zip(intervals, intervals[1:]))):
            raise ValueError('Overlapping canonical intervals')
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
        reasons.append('INTERVAL_CALENDAR_CONTRACT_INVALID')
    seen = set()
    bars = []
    for row in selected:
        stamp = row.get('time')
        if not isinstance(stamp, str):
            reasons.append('INVALID_RAW_STAMP')
            continue
        if stamp in seen:
            reasons.append('DUPLICATE_RAW_STAMP')
        seen.add(stamp)
        if stamp not in mapped:
            reasons.append('UNMAPPED_RAW_STAMP')
        if row.get('source_sha256') != source:
            reasons.append('SOURCE_MISMATCH')
        try:
            values = [row[k] for k in ('open', 'high', 'low', 'close', 'volume')]
            if any((type(v) not in (int, float) or not math.isfinite(v) for v in values)):
                raise ValueError('Finite numeric OHLCV required')
            o, h, l, c, v = (Decimal(str(v)) for v in values)
            if min(o, h, l, c) <= 0 or not l <= min(o, c) <= max(o, c) <= h or v < 0:
                raise ValueError('Invalid OHLCV')
            if stamp in mapped:
                bars.append((mapped[stamp], o, h, l, c, v))
        except (KeyError, ValueError, TypeError, OverflowError):
            reasons.append('INVALID_OHLCV')
    if set(mapped) - seen:
        reasons.append('MISSING_EXPECTED_INTERVAL')
    if len(bars) < 35:
        reasons.append('INSUFFICIENT_REFERENCE_WARMUP')
    if bars and policy_ok:
        latest = max((b[0][1] for b in bars))
        if (now - latest).total_seconds() > limit:
            reasons.append('STALE')
    result = dict(schema=1, synthetic=True, symbol=symbol, session=session, notice=NOTICE, evaluated_at=now.astimezone(timezone.utc).isoformat(), eligible=False, bias=None, bias_status='UNVERIFIED' if selected else 'UNAVAILABLE', action='WAIT', news_status='UNAVAILABLE', sentiment_status='UNAVAILABLE', reasons=sorted(set(reasons)), observations=None, raw_sha256=_hash(_typed(selected)), contract_sha256=_hash(_typed(contract)), policy_sha256=_hash(_typed(policy)), contract_evidence=_typed(contract), policy_evidence=_typed(policy))
    if reasons:
        return result
    bars.sort(key=lambda b: b[0][0])
    with localcontext(Context(prec=50, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999, capitals=1)):
        e9 = e21 = bars[0][4]
        for b in bars[1:]:
            e9 = Decimal(2) / 10 * b[4] + Decimal(8) / 10 * e9
            e21 = Decimal(2) / 22 * b[4] + Decimal(20) / 22 * e21
        volume = sum((b[5] for b in bars))
        prior = sum((b[5] for b in bars[-21:-1])) / 20
        if volume <= 0 or prior <= 0:
            result['reasons'] = ['ZERO_VOLUME_DENOMINATOR']
            return result
        proxy = sum(((b[2] + b[3] + b[4]) / 3 * b[5] for b in bars)) / volume
        ratio = bars[-1][5] / prior
        close = bars[-1][4]
        bias = 'BULLISH' if close > e9 > e21 and close > proxy else 'BEARISH' if close < e9 < e21 and close < proxy else 'MIXED'
        result.update(eligible=bias != 'MIXED', bias=bias, bias_status='SYNTHETIC CONTRACT SATISFIED', observations=dict(ema9=str(e9), ema21=str(e21), relative_volume=str(ratio), hlc3_volume_weighted_proxy=str(proxy), canonical_bars=len(bars), interval_end=bars[-1][0][1].isoformat(), limitations=['NOT_TRADE_LEVEL_VWAP', 'UNVALIDATED_REFERENCE_HYPOTHESIS']))
        if bias == 'MIXED':
            result['reasons'] = ['NO_DIRECTIONAL_CONJUNCTION']
    return result
