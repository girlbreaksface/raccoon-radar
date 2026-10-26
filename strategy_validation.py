"""Read-only historical research store and chronological validation. No trading APIs."""
import csv
import sqlite3
from collections import defaultdict
from datetime import datetime, time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / 'raccoon_history.sqlite3'

def store_candles(rows, path=DB_PATH):
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS candles (symbol TEXT NOT NULL, time TEXT NOT NULL, open REAL, high REAL, low REAL, close REAL, volume REAL, PRIMARY KEY(symbol,time))')
        count = 0
        for r in rows:
            try:
                symbol=str(r['symbol']); stamp=str(r['time'])
                datetime.strptime(stamp,'%Y-%m-%d %H:%M:%S')
                values=[float(r[k]) for k in ('open','high','low','close','volume')]
                if not (values[2] <= min(values[0],values[3]) <= max(values[0],values[3]) <= values[1] and values[4]>=0): continue
                db.execute('INSERT INTO candles VALUES (?,?,?,?,?,?,?) ON CONFLICT(symbol,time) DO UPDATE SET open=excluded.open,high=excluded.high,low=excluded.low,close=excluded.close,volume=excluded.volume', (symbol,stamp,*values))
                count+=1
            except (ValueError,KeyError,TypeError): continue
    return count

def load_candles(path=DB_PATH):
    if not Path(path).exists(): return []
    with sqlite3.connect(path) as db:
        return [dict(zip(('symbol','time','open','high','low','close','volume'),r)) for r in db.execute('SELECT symbol,time,open,high,low,close,volume FROM candles ORDER BY time,symbol')]

def strict_spacing(events, minutes=5):
    """One observation per symbol in each cooldown; SPY/QQQ may still correlate."""
    from datetime import timedelta
    last={}; out=[]
    for e in sorted(events,key=lambda e:(e['time'],e['symbol'],e['setup'])):
        t=datetime.strptime(e['time'],'%Y-%m-%d %H:%M:%S'); sym=e['symbol']
        if sym in last and t-last[sym]<timedelta(minutes=minutes): continue
        out.append(e);last[sym]=t
    return out

def validate(events, start='09:40', end='11:30', holdout_days=2, horizon='3m_%'):
    """Chronological train/test separation. Every setup reported, not cherry-picked.
    Outcomes are ETF directional movements, not options returns.
    """
    start_t=time.fromisoformat(start);end_t=time.fromisoformat(end)
    if start_t>=end_t: raise ValueError('Start must be before end')
    filtered=[e for e in events if start_t<=datetime.strptime(e['time'],'%Y-%m-%d %H:%M:%S').time()<end_t]
    days=sorted({e['time'][:10] for e in filtered})
    if len(days)<holdout_days+2: return [],f'Insufficient days: {len(days)} with observations in window; need at least {holdout_days+2}.'
    test_days=set(days[-holdout_days:]); grouped=defaultdict(lambda: {'train':[],'test':[],'train_days':set(),'test_days':set()})
    for e in filtered:
        val=e.get(horizon)
        if val is None or val=='':continue
        group=grouped[(e['symbol'],e['setup'])]; bucket='test' if e['time'][:10] in test_days else 'train'
        group[bucket].append(float(val));group[bucket+'_days'].add(e['time'][:10])
    out=[]
    for (symbol,setup),group in sorted(grouped.items()):
        a,b=group['train'],group['test']
        out.append({'symbol':symbol,'setup':setup,'train_n':len(a),'train_days':len(group['train_days']),
            'train_win_%':round(100*sum(v>0 for v in a)/len(a),1) if a else '—',
            'train_avg_%':round(sum(a)/len(a),4) if a else '—',
            'test_n':len(b),'test_days':len(group['test_days']),
            'test_win_%':round(100*sum(v>0 for v in b)/len(b),1) if b else '—',
            'test_avg_%':round(sum(b)/len(b),4) if b else '—',
            'warning':'VERY LIMITED' if len(a)<30 or len(b)<30 or len(group['test_days'])<2 else 'EXPLORATORY'})
    return out,f'Train: {days[0]} to {days[-holdout_days-1]}; untouched holdout: {days[-holdout_days]} to {days[-1]}. {len(days)} observed sessions. All setups shown; not a trading backtest.'

def weekdays(events, horizon='3m_%'):
    groups=defaultdict(list); sessions=defaultdict(set)
    for e in events:
        v=e.get(horizon)
        if v is None or v=='': continue
        day=e['time'][:10];key=(e['symbol'],e['setup'],datetime.strptime(day,'%Y-%m-%d').strftime('%A'))
        groups[key].append(float(v));sessions[key].add(day)
    out=[]
    for key,vals in sorted(groups.items()):
        out.append({'symbol':key[0],'setup':key[1],'weekday':key[2],'events':len(vals),'sessions':len(sessions[key]),
                    'win_%':round(100*sum(v>0 for v in vals)/len(vals),1),'avg_%':round(sum(vals)/len(vals),4),
                    'warning':'TOO FEW DAYS' if len(sessions[key])<8 else 'EXPLORATORY'})
    return out
