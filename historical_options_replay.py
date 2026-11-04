"""Offline paired 0DTE research replay. No broker, recording or order APIs.

Input is an explicit normalized JSON dataset; normalization/provider verification
is outside this module. All prices are decimal strings, times offset-aware.
"""
import argparse
from datetime import datetime, timedelta
from decimal import Decimal, localcontext
import hashlib
import json
import platform
from pathlib import Path
import uuid
from zoneinfo import ZoneInfo

VERSION = 'historical-options-replay-v1'
ENGINE_VERSION = 'historical-options-replay-v1.1'
VARIANTS = (('A', '0.20', '0.15'), ('B', '0.25', '0.15'),
            ('C', '0.30', '0.15'), ('D', '0.30', '0.20'))
NY = ZoneInfo('America/New_York')
DEFAULTS = dict(fee_per_side='1', slippage_per_side='0.005', budget='30',
                max_spread='0.03', max_quote_age_seconds=5,
                max_gap_seconds=5, max_signal_age_seconds=5, daily_limit=3)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def number(value):
    if not isinstance(value, str) or len(value) > 30:
        raise ValueError('Decimal strings required')
    try:
        n = Decimal(value)
    except Exception as exc:
        raise ValueError('Invalid decimal string') from exc
    if not n.is_finite() or n < 0 or n > 1000000000 or n.as_tuple().exponent < -8:
        raise ValueError('Invalid nonnegative decimal')
    return n


def stamp(value):
    t = datetime.fromisoformat(value)
    if t.utcoffset() is None:
        raise ValueError('Offset-aware timestamps required')
    return t


def chronological(rows, field):
    times = [stamp(r[field]) for r in rows]
    if any(a >= b for a, b in zip(times, times[1:])):
        raise ValueError('Duplicate or nonchronological timestamps')


def signals(session):
    """Research PUT rule, session-reset first-close EMA seeds, 21-bar warmup.

    Session VWAP uses supplied cumulative trade price*volume (pv), never OHLC4.
    Five-bar breakdown: close below previous five lows. Rejection: high touches
    current EMA9 and close is below it. All predicates must hold on same bar.
    """
    opening, cutoff = stamp(session['open']), stamp(session['cutoff'])
    closing = stamp(session['close'])
    if not opening < cutoff < closing:
        raise ValueError('Explicit calendar open < cutoff < close required')
    if any(t.astimezone(NY).date().isoformat() != session['date']
           for t in (opening, cutoff, closing)):
        raise ValueError('Session date mismatch')
    decisions = []
    for symbol, bars in sorted(session['bars'].items()):
        if symbol not in ('SPY', 'QQQ'):
            raise ValueError('Only SPY/QQQ supported')
        chronological(bars, 'end')
        chronological(bars, 'available')
        ema9 = ema21 = None
        volume = pv = Decimal(0)
        expected = opening + timedelta(minutes=1)
        for i, b in enumerate(bars):
            end, known = stamp(b['end']), stamp(b['available'])
            if end != expected or known < end or end > closing:
                raise ValueError('Incomplete one-minute session prefix or noncausal availability')
            expected += timedelta(minutes=1)
            if b['final'] is not True or b['revision'] != 0 or b['generation'] != 0:
                raise ValueError('Revisions/reconnects require a verified as-of adapter')
            o, h, l, c, v, p = [number(b[k]) for k in ('open','high','low','close','volume','pv')]
            if not 0 < l <= min(o,c) <= max(o,c) <= h or v <= 0 or not l*v <= p <= h*v:
                raise ValueError('Invalid OHLCV or trade notional')
            ema9 = c if ema9 is None else ema9 + (c-ema9)/5
            ema21 = c if ema21 is None else ema21 + (c-ema21)/11
            volume += v
            pv += p
            vwap = pv/volume
            breakdown = i >= 5 and c < min(number(x['low']) for x in bars[i-5:i])
            rejection = h >= ema9 and c < ema9
            eligible = i >= 20 and c < ema9 < ema21 and c < vwap and breakdown and rejection
            row = dict(symbol=symbol, at=b['available'], bar_end=b['end'],
                       ema9=str(ema9), ema21=str(ema21), session_vwap=str(vwap),
                       breakdown=breakdown, rejection=rejection,
                       eligible=eligible and known < cutoff,
                       reason='SIGNAL' if eligible and known < cutoff else 'RULE_OR_WARMUP_OR_CUTOFF')
            row['signal_id'] = digest([VERSION, session['date'], symbol, b, row])
            decisions.append(row)
    return sorted(decisions, key=lambda r: (stamp(r['at']), r['symbol']))


def quote_ok(q, config):
    bid, ask = number(q['bid']), number(q['ask'])
    age = (stamp(q['available'])-stamp(q['observed'])).total_seconds()
    return (0 < bid <= ask and ask-bid <= number(config['max_spread'])
            and number(q['bid_size']) >= 1 and number(q['ask_size']) >= 1
            and 0 <= age <= config['max_quote_age_seconds'])


def rank(candidates, underlying):
    """Transparent lexicographic research ranking, no fitted weights.

    Tightest relative spread, largest minimum displayed size, nearest strike,
    then contract ID. Only already eligible, point-in-time quotes may be passed.
    """
    return sorted(candidates, key=lambda pair: (
        (number(pair[1]['ask'])-number(pair[1]['bid']))/number(pair[1]['ask']),
        -min(number(pair[1]['bid_size']), number(pair[1]['ask_size'])),
        abs(number(pair[0]['strike'])-underlying), pair[0]['id']))


def score(rows):
    completed = [r for r in rows if r['status'] == 'CLOSED']
    values = [Decimal(r['net']) for r in completed]
    wins, losses = [v for v in values if v > 0], [v for v in values if v < 0]
    equity = peak = drawdown = Decimal(0)
    streak = longest = 0
    for v in values:
        equity += v
        peak = max(peak, equity)
        drawdown = max(drawdown, peak-equity)
        streak = streak+1 if v < 0 else 0
        longest = max(longest, streak)
    avgwin = sum(wins)/len(wins) if wins else None
    avgloss = -sum(losses)/len(losses) if losses else None
    return dict(completed=len(values), unresolved=sum(r['status']=='UNRESOLVED' for r in rows),
                rejected=sum(r['status']=='REJECTED' for r in rows),
                win_rate=str(Decimal(len(wins))/len(values)) if values else None,
                average_net=str(sum(values)/len(values)) if values else None,
                profit_factor=str(sum(wins)/-sum(losses)) if losses else None,
                break_even_win_rate=str(avgloss/(avgwin+avgloss)) if avgwin and avgloss else None,
                max_realized_drawdown=str(drawdown), longest_loss_streak=longest,
                mean_holding_seconds=str(sum(Decimal(r['holding_seconds']) for r in completed)/len(completed)) if completed else None,
                exits={k:sum(r.get('reason')==k for r in completed) for k in ('TARGET','STOP','CUTOFF')})


def replay(data, parameters=None):
    with localcontext() as ctx:
        ctx.prec = 50
        return _replay(data, parameters)


def _replay(data, parameters):
    config = dict(DEFAULTS)
    if parameters:
        if set(parameters)-set(config):
            raise ValueError('Unknown parameter')
        config.update(parameters)
    for key in ('fee_per_side','slippage_per_side','budget','max_spread'):
        number(config[key])
    for key in ('max_quote_age_seconds','max_gap_seconds','max_signal_age_seconds','daily_limit'):
        if type(config[key]) is not int or not 0 < config[key] <= 86400:
            raise ValueError('Positive bounded integer policy required')
    if data['schema'] != VERSION or data['quality'] not in ('SYNTHETIC','VERIFIED_QUOTES'):
        raise ValueError('Explicit quote provenance classification required; candles cannot model fills')
    if not data['provenance']:
        raise ValueError('Provenance required')
    sessions = data['sessions']
    if not sessions:
        raise ValueError('At least one session required')
    dates = [s['date'] for s in sessions]
    if dates != sorted(set(dates)):
        raise ValueError('Unique chronological sessions required')
    audits, decisions = [], []
    for session in sessions:
        cutoff = stamp(session['cutoff'])
        contracts = session['contracts']
        if len({c['id'] for c in contracts}) != len(contracts):
            raise ValueError('Duplicate contract')
        for c in contracts:
            number(c['strike'])
            stamp(c['available'])
            chronological(c['quotes'], 'available')
            for q in c['quotes']:
                # Validate every row, even unused quotes. Never reorder tied paths.
                stamp(q['observed'])
                for k in ('bid','ask','bid_size','ask_size','volume','open_interest'):
                    number(q[k])
                if not stamp(session['open']) <= stamp(q['available']) < stamp(session['close']):
                    raise ValueError('Quote outside session')
        selected = 0
        reserved = set()
        steps = signals(session)
        decisions.extend(steps)
        for s in steps:
            if not s['eligible']:
                continue
            at = stamp(s['at'])
            candidates = []
            rejected = []
            for c in contracts:
                if stamp(c['available']) > at or c['symbol'] != s['symbol'] or c['right'] != 'PUT' or c['expiry'] != session['date'] or c['multiplier'] != 100:
                    rejected.append([c['id'], 'CONTRACT_SCOPE'])
                    continue
                # One first observation per candidate; never search forward for a better fill.
                q = next((q for q in c['quotes'] if stamp(q['available']) > at), None)
                if (q is None or stamp(q['available']) >= cutoff or
                    (stamp(q['available'])-stamp(s['bar_end'])).total_seconds() > config['max_signal_age_seconds'] or
                    stamp(q['observed']) <= at or not quote_ok(q, config)):
                    rejected.append([c['id'], 'QUOTE_UNAVAILABLE_OR_INVALID'])
                    continue
                if (number(q['ask'])+number(config['slippage_per_side']))*100+number(config['fee_per_side']) > number(config['budget']):
                    rejected.append([c['id'], 'ENTRY_BUDGET'])
                    continue
                candidates.append((c,q))
            # Freeze first opportunity time across all candidates; later arrivals cannot win ranking.
            if candidates:
                first = min(stamp(q['available']) for _,q in candidates)
                candidates = [(c,q) for c,q in candidates if stamp(q['available']) == first]
            underlying = number(next(b['close'] for b in session['bars'][s['symbol']] if b['end']==s['bar_end']))
            candidates = rank(candidates, underlying)
            choice = candidates[0] if candidates else None
            fee, slip = number(config['fee_per_side']), number(config['slippage_per_side'])
            reason = ('DAILY_LIMIT' if selected >= config['daily_limit'] else
                      'SHARED_EXPOSURE_RESERVATION' if s['symbol'] in reserved else
                      ('ENTRY_BUDGET' if any(r[1]=='ENTRY_BUDGET' for r in rejected) else 'NO_ELIGIBLE_QUOTE') if choice is None else None)
            if choice:
                c,q = choice
                entry = number(q['ask'])+slip
                if entry*100+fee > number(config['budget']):
                    reason = reason or 'ENTRY_BUDGET'
            common = dict(signal_id=s['signal_id'], session=session['date'], symbol=s['symbol'],
                          candidate_rejections=rejected, ranking=[c['id'] for c,_ in candidates])
            if reason:
                for variant,_,_ in VARIANTS:
                    audits.append(dict(common, variant=variant, status='REJECTED', reason=reason))
                continue
            selected += 1
            reserved.add(s['symbol'])  # shared through cutoff, independent of variant exits
            start = stamp(q['available'])
            for variant,target,stop in VARIANTS:
                row = dict(common, variant=variant, contract=c['id'], entry_quote=q,
                           entry=str(entry), entry_cost=str(entry*100+fee),
                           status='UNRESOLVED', reason='MISSING_CUTOFF_QUOTE')
                previous = start
                previous_observed = stamp(q['observed'])
                for exitq in c['quotes']:
                    time = stamp(exitq['available'])
                    if time <= start:
                        continue
                    if (time-previous).total_seconds() > config['max_gap_seconds'] or not quote_ok(exitq,config):
                        row['reason'] = 'PATH_GAP_OR_INVALID_QUOTE'
                        break
                    if stamp(exitq['observed']) <= start:
                        row['reason'] = 'NONCAUSAL_EXIT_QUOTE'
                        break
                    if stamp(exitq['observed']) <= previous_observed:
                        row['reason'] = 'NONMONOTONIC_EXIT_OBSERVATION'
                        break
                    previous_observed = stamp(exitq['observed'])
                    previous = time
                    # Cutoff requires an exact observation; never a stale carry-forward or later fill.
                    if time > cutoff:
                        break
                    bid = number(exitq['bid'])
                    trigger = ('CUTOFF' if time == cutoff else
                               'STOP' if bid <= entry*(1-Decimal(stop)) else
                               'TARGET' if bid >= entry*(1+Decimal(target)) else None)
                    if trigger:
                        fill = max(Decimal(0), bid-slip)
                        gross = (fill-entry)*100
                        row.update(status='CLOSED', reason=trigger, exit_quote=exitq,
                                   exit=str(fill), gross=str(gross), fees=str(2*fee),
                                   net=str(gross-2*fee), return_on_cost=str((gross-2*fee)/(entry*100+fee)),
                                   holding_seconds=str((time-start).total_seconds()))
                        break
                audits.append(row)
    summaries = {}
    for variant,_,_ in VARIANTS:
        rows = sorted([r for r in audits if r['variant']==variant],
                      key=lambda r: (stamp(r['exit_quote']['available']) if 'exit_quote' in r else datetime.max.replace(tzinfo=NY),r['signal_id']))
        summaries[variant] = dict(overall=score(rows), by_symbol={symbol:score([r for r in rows if r['symbol']==symbol]) for symbol in ('SPY','QQQ')})
    for row in audits:
        row['trade_id'] = digest([VERSION, row['signal_id'], row['variant'], config])
    result = dict(version=VERSION, engine_version=ENGINE_VERSION,
                  quality=data['quality'], provenance=data['provenance'],
                  dataset=json.loads(encoded(data)), software={'python':platform.python_version()},
                  input_hash=digest(data), config=config, config_hash=digest(config),
                  code_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  decisions=decisions, trades=audits, summaries=summaries,
                  limitations=['Sampled quotes do not establish intervening extrema or executable fills',
                               'Shared per-symbol reservation through cutoff; paired opportunity research',
                               'Unresolved outcomes excluded from completed-trade metrics; no profitability inference'],
                  recording='HOLD', paper_execution='HOLD', live='NO-GO', orders='DISABLED')
    result['run_hash'] = digest(result)
    return result



def cost_scenarios(data):
    """Illustrative $2 fees and $0/$1/$3 extra round-trip slippage, one contract."""
    return {name: replay(data, {'fee_per_side':'1', 'slippage_per_side':slip})
            for name,slip in (('optimistic','0'),('base','0.005'),('stress','0.015'))}


def evaluation_plan(session_dates, inspected_dates=()):
    """Freeze before use. Labels never certify an untouched holdout."""
    dates = list(session_dates)
    if dates != sorted(set(dates)) or len(dates) < 5:
        raise ValueError('At least five unique chronological sessions required')
    a,b = len(dates)*3//5,len(dates)*4//5
    plan = dict(development=dates[:a], validation=dates[a:b], test=dates[b:],
                inspected_dates=sorted(set(inspected_dates)),
                test_previously_inspected=bool(set(dates[b:]) & set(inspected_dates)),
                walk_forward=[dict(train=dates[:i],evaluate=[dates[i]]) for i in range(a,len(dates))],
                warning='Freeze this plan and all hypotheses before evaluation; chronological does not mean untouched')
    plan['plan_hash'] = digest(plan)
    return plan


def export(result, directory):
    """Deterministic bytes with exclusive, collision-resistant output names."""
    path = Path(directory)/('replay-'+result['run_hash'][:12]+'-'+uuid.uuid4().hex+'.json')
    with path.open('xb') as handle:
        handle.write(encoded(result)+b'\n')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset')
    parser.add_argument('output_directory')
    parser.add_argument('--parameters', help='JSON policy overrides')
    args = parser.parse_args()
    dataset = json.loads(Path(args.dataset).read_text(encoding='utf-8'))
    print(export(replay(dataset, json.loads(args.parameters) if args.parameters else None), args.output_directory))
