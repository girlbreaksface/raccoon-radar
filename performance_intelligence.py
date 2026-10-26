"""Exploratory summaries of completed-candle events. Not a trade backtest."""
from collections import defaultdict
from datetime import datetime, timedelta
from setup_detective import summary

def nonoverlap(events, minutes=5):
    """Greedy chronological cooldown per (symbol, setup), including across sessions.
    Distinct setups can still overlap, as can SPY and QQQ events.
    """
    last={}; result=[]
    for e in sorted(events,key=lambda x:(x['time'],x['symbol'],x['setup'])):
        key=(e['symbol'],e['setup']); t=datetime.strptime(e['time'],'%Y-%m-%d %H:%M:%S')
        if key in last and t-last[key]<timedelta(minutes=minutes): continue
        result.append(e); last[key]=t
    return result

def sample_label(n):
    return 'VERY LOW' if n<10 else ('LOW' if n<30 else ('MODERATE' if n<100 else 'LARGER'))

def daily_breakdown(events):
    groups=defaultdict(list)
    for e in events: groups[e['time'][:10]].append(e)
    rows=[]
    for day,group in sorted(groups.items()):
        for item in summary(group):
            row={'day':day,**item,'sample':sample_label(item['events'])}
            rows.append({k:('—' if v is None else v) for k,v in row.items()})
    return rows

def consistency(events):
    groups=defaultdict(list)
    for e in events: groups[(e['symbol'],e['setup'])].append(e)
    rows=[]
    for (sym,setup),group in sorted(groups.items()):
        daily=defaultdict(list)
        for e in group:
            if e.get('3m_%') is not None: daily[e['time'][:10]].append(e['3m_%'])
        means=[sum(v)/len(v) for v in daily.values()]
        valid=[e['3m_%'] for e in group if e.get('3m_%') is not None]
        warning='FEW SESSIONS' if len(daily)<5 else ('SMALL SAMPLE' if len(valid)<30 else 'EXPLORATORY')
        rows.append({'symbol':sym,'setup':setup,'events':len(group),
            'sessions':len(set(e['time'][:10] for e in group)),
            'positive_days_3m':sum(m>0 for m in means),
            'days_with_3m':len(means),
            '3m_daily_avg':round(sum(means)/len(means),4) if means else '—',
            '3m_winrate':round(100*sum(v>0 for v in valid)/len(valid),1) if valid else '—',
            'sample':sample_label(len(valid)),'warning':warning})
    return rows
