"""Pure synthetic stream compatibility gate; no wire parsing or candle eligibility.

Identity strings are caller declarations, never authenticated provider evidence.
This module is intentionally disconnected from the existing receipt observer.
"""
from dataclasses import dataclass, fields
from unicodedata import category


@dataclass(frozen=True)
class Identity:
    mode: str
    provider: str
    endpoint: str
    schema_version: str
    coverage: str
    session: str
    interval: str
    adjustment: str
    adjustment_anchor: str
    adjustment_version: str


@dataclass(frozen=True)
class Observation:
    identity: Identity
    symbol: str
    source_label: str
    sequence: int
    raw: bytes


@dataclass(frozen=True)
class Result:
    compatibility: str
    observations: tuple[Observation, ...]
    reasons: tuple[str, ...]
    status: str = 'DATA_BLOCKED'
    finality: str = 'UNKNOWN'
    completeness: str = 'NOT_ESTABLISHED'


def _known(value):
    return (type(value) is str and 0 < len(value) <= 256
            and value == value.strip()
            and value.upper() not in {'UNKNOWN', 'UNVERIFIED', 'NOT_ESTABLISHED'}
            and not any(category(char) == 'Cc' for char in value))


def _identity(value):
    return (type(value) is Identity and value.mode == 'SYNTHETIC'
            and all(_known(getattr(value, f.name)) for f in fields(Identity)))


def isolate(observations, expected, *, synthetic=False):
    """Accept an entire bounded tuple only if every declared stream matches.

    Never choose a winning feed or filter out conflicting evidence. Blocked output
    is empty; caller retains the original immutable observations. Preserve order,
    repeats, raw bytes and labels. No revision selection, time conversion, clock
    validation, OHLCV validation, persistence or FINAL promotion is performed.
    """
    reasons = set()
    if synthetic is not True:
        reasons.add('SYNTHETIC_OPT_IN_REQUIRED')
    valid_expected = _identity(expected)
    if not valid_expected:
        reasons.add('IDENTITY_UNESTABLISHED')
    if type(observations) is not tuple or not 0 < len(observations) <= 5000:
        reasons.add('BATCH_INVALID')
    else:
        for row in observations:
            if type(row) is not Observation:
                reasons.add('OBSERVATION_INVALID')
                continue
            if not _identity(row.identity):
                reasons.add('IDENTITY_UNESTABLISHED')
            elif valid_expected and row.identity != expected:
                reasons.add('INCOMPATIBLE_STREAM')
            if (row.symbol not in ('US.SPY', 'US.QQQ') or type(row.symbol) is not str
                    or not _known(row.source_label) or len(row.source_label) > 128
                    or type(row.sequence) is not int or row.sequence <= 0
                    or type(row.raw) is not bytes or not 0 < len(row.raw) <= 65536):
                reasons.add('OBSERVATION_INVALID')
    if reasons:
        return Result('BLOCKED', (), tuple(sorted(reasons)))
    return Result('COMPATIBLE', observations, ())
