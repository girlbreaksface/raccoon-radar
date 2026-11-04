"""Pure proposed paper-order risk review. No broker, files, clock or submission.

Limits here are a proposed pilot policy, not modifications to the simulator.
Caller-supplied state requires broker reconciliation before any future use.
"""
from dataclasses import dataclass, asdict
from decimal import Decimal, localcontext, Context
import re
import hashlib
import json


@dataclass(frozen=True)
class Proposal:
    account_fingerprint: str
    environment: str
    underlying: str
    contract: str
    right: str
    quantity: int
    limit_price: str
    estimated_round_trip_fees: str
    quote_age_seconds: int
    session_verified: bool
    account_verified: bool
    reconciled: bool
    entries_today: int
    open_premium: str
    realized_net: str
    kill_switch: bool


def review(proposal):
    if type(proposal) is not Proposal:
        raise ValueError('Typed immutable proposal required')
    p = proposal
    for value in (p.session_verified, p.account_verified, p.reconciled, p.kill_switch):
        if type(value) is not bool:
            raise ValueError('Explicit boolean control required')
    for value in (p.quantity, p.quote_age_seconds, p.entries_today):
        if type(value) is not int or value < 0:
            raise ValueError('Nonnegative integer required')
    def number(raw):
        if type(raw) is not str or len(raw) > 24:
            raise ValueError('Bounded decimal strings required')
        try: value = Decimal(raw)
        except Exception as exc: raise ValueError('Invalid decimal') from exc
        if not value.is_finite() or abs(value) > 1000000 or value.as_tuple().exponent < -8:
            raise ValueError('Invalid bounded decimal')
        return value
    price, fees, exposure, pnl = map(number, (p.limit_price,
        p.estimated_round_trip_fees, p.open_premium, p.realized_net))
    if min(price, fees, exposure) < 0:
        raise ValueError('Negative price, fee or exposure')
    with localcontext(Context(prec=50)):
        cost = price * 100 * p.quantity + fees
        total_exposure = exposure + cost
    reasons = []
    conditions = (
        (p.environment != 'SIMULATE', 'PAPER_ENV_REQUIRED'),
        (type(p.account_fingerprint) is not str or len(p.account_fingerprint) != 64
         or any(c not in '0123456789abcdef' for c in p.account_fingerprint), 'ACCOUNT_IDENTITY_REQUIRED'),
        (p.underlying not in ('SPY', 'QQQ'), 'UNDERLYING_NOT_ALLOWED'),
        (type(p.contract) is not str or type(p.underlying) is not str
         or re.fullmatch(r'US\.' + re.escape(p.underlying) + r'\d{6}'
             + ('C' if p.right == 'CALL' else 'P') + r'\d+', p.contract) is None,
             'CONTRACT_NOT_VERIFIED'),
        (p.right not in ('CALL', 'PUT'), 'LONG_OPTION_REQUIRED'),
        (p.quantity != 1, 'ONE_CONTRACT_ONLY'),
        (price <= 0 or cost > 30, 'ALL_IN_ENTRY_LIMIT'),
        (p.quote_age_seconds > 5, 'STALE_QUOTE'),
        (not p.session_verified, 'SESSION_UNVERIFIED'),
        (not p.account_verified, 'ACCOUNT_UNVERIFIED'),
        (not p.reconciled, 'RECONCILIATION_REQUIRED'),
        (p.entries_today >= 3, 'DAILY_ENTRY_LIMIT'),
        (total_exposure > 60, 'PORTFOLIO_PREMIUM_LIMIT'),
        (pnl <= -30, 'DAILY_LOSS_STOP'),
        (p.kill_switch, 'KILL_SWITCH'),
    )
    reasons.extend(reason for blocked, reason in conditions if blocked)
    digest = hashlib.sha256(json.dumps(asdict(p), sort_keys=True).encode()).hexdigest()
    return dict(proposal_hash=digest, status='BLOCKED' if reasons else 'READY_FOR_REVIEW',
        reasons=reasons, all_in_entry=str(cost), order_type='LIMIT', side='BUY',
        time_in_force='DAY', orders='DISABLED', integration='HOLD', live_trading='NO-GO',
        external_paper_orders='REVIEW_REQUIRED')
