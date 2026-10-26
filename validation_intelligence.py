"""Descriptive rolling chronological research. ETF movement only, no order simulation."""
from collections import defaultdict
from datetime import datetime, time

def _selected(events,start='09:40',end='11:30',horizon='3m_%'):
    lo=time.fromisoformat(start);hi=time.fromisoformat(end)
    return [e for e in events if lo <= datetime.strptime(e['time'],'%Y-%m-%d %H:%M:%S').time() < hi and e.get(horizon) not in (None,'')]

def daily_outcomes(events):
    groups=defaultdict(list)
    for e in _selected(events):
        groups[(e['time'][:10],e['symbol'],e['setup'])].append(float(e['3m_%']))
    result=[]
    for (day,sym,setup),values in sorted(groups.items()):
        result.append({'day':day,'symbol':sym,'setup':setup,'n':len(values),
                       'favorable_%':round(100*sum(x>0 for x in values)/len(values),1),
                       'avg_move_%':round(sum(values)/len(values),4),
                       'min_move_%':round(min(values),4),'max_move_%':round(max(values),4)})
    return result

def rolling_holdout(events,min_train_days=10,test_days=5):
    """Expanding training periods followed by non-overlapping 5-session evaluation blocks.
    All setups evaluated, not selected based on results. Outcomes not independent.
    """
    selected=_selected(events)
    dates=sorted({e['time'][:10] for e in selected})
    if len(dates)<min_train_days+test_days:return [],f'Need at least {min_train_days+test_days} observed sessions; found {len(dates)}.'
    bykey=defaultdict(lambda:defaultdict(list))
    for e in selected:bykey[(e['symbol'],e['setup'])][e['time'][:10]].append(float(e['3m_%']))
    rows=[]
    for start in range(min_train_days,len(dates),test_days):
        evaluation=dates[start:start+test_days]
        if len(evaluation)<test_days:break # no incomplete last fold
        train=dates[:start]
        for (sym,setup),dayvals in sorted(bykey.items()):
            a=[v for day in train for v in dayvals.get(day,())]
            b=[v for day in evaluation for v in dayvals.get(day,())]
            rows.append({'fold':len({r['fold'] for r in rows})+1 if not rows or rows[-1]['test_first']!=evaluation[0] else rows[-1]['fold'],
                'symbol':sym,'setup':setup,'train_days':len(train),'train_n':len(a),
                'train_avg_%':round(sum(a)/len(a),4) if a else '',
                'test_first':evaluation[0],'test_last':evaluation[-1],
                'test_n':len(b),'test_avg_%':round(sum(b)/len(b),4) if b else '',
                'test_favorable_%':round(100*sum(v>0 for v in b)/len(b),1) if b else '',
                'warning':'SMALL SAMPLE' if len(b)<30 else 'EXPLORATORY'})
    return rows,f'{len(dates)} observed sessions; expanding train >= {min_train_days} sessions, nonoverlapping {test_days}-session evaluation blocks. Previously inspected history is NOT untouched out-of-sample data.'
