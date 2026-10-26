"""Historical price-action event study. Candle closes only; not option P/L."""
from collections import defaultdict
from datetime import datetime, timedelta

HORIZONS=(1,3,5)

def _time(row):
    return datetime.strptime(str(row.get('time') or row.get('bar_time_et')), '%Y-%m-%d %H:%M:%S')

def detect(rows):
    """Return event records using only current and earlier completed bars.
    Future outcomes are attached separately; missing minutes are never bridged.
    """
    groups=defaultdict(list)
    for r in rows:
        try:
            t=_time(r); o,h,l,c,v=(float(r[k]) for k in ('open','high','low','close','volume'))
            sym=str(r['symbol']).strip()
            if not sym or not l<=min(o,c)<=max(o,c)<=h or v<0: continue
            groups[(sym,t.date())].append(dict(time=t,symbol=sym,open=o,high=h,low=l,close=c,volume=v))
        except (ValueError,TypeError,KeyError): continue
    events=[]
    for (sym,day),bars in groups.items():
        bars.sort(key=lambda x:x['time'])
        # Deduplicate timestamps, preserving the last received bar.
        unique={b['time']:b for b in bars}; bars=[unique[t] for t in sorted(unique)]
        by_time={b['time']:b for b in bars}
        for i,b in enumerate(bars):
            prior=bars[max(0,i-12):i]
            if len(prior)<5 or any(prior[j+1]['time']-prior[j]['time']!=timedelta(minutes=1) for j in range(len(prior)-1)) or b['time']-prior[-1]['time']!=timedelta(minutes=1): continue
            last5=prior[-5:]; high=max(p['high'] for p in last5); low=min(p['low'] for p in last5)
            avg_range=sum(p['high']-p['low'] for p in prior)/len(prior)
            avg_vol=sum(p['volume'] for p in prior)/len(prior)
            if avg_range<=0 or avg_vol<=0: continue
            body=abs(b['close']-b['open']); rng=b['high']-b['low']
            tags=[]
            if body>=1.7*avg_range and b['volume']>=1.3*avg_vol:
                tags.append(('UP MOMENTUM BURST' if b['close']>b['open'] else 'DOWN MOMENTUM BURST',1 if b['close']>b['open'] else -1))
            if b['high']>high and b['close']<high and b['open']<=high: tags.append(('UP BREAK REJECTED',-1))
            if b['low']<low and b['close']>low and b['open']>=low: tags.append(('DOWN BREAK REJECTED',1))
            if b['close']>high and b['open']<=high: tags.append(('BREAKOUT UP',1))
            if b['close']<low and b['open']>=low: tags.append(('BREAKOUT DOWN',-1))
            # A deliberately strict, preliminary multi-candle pattern:
            # burst 2-4 bars ago, intervening pullback/tight pause, current close
            # above/below prior close. It is a research label, not a trade trigger.
            for k in (2,3,4):
                if i<k: continue
                impulse=bars[i-k]
                if b['time']-impulse['time']!=timedelta(minutes=k): continue
                ir=impulse['high']-impulse['low']
                pause=bars[i-k+1:i]
                if ir<=0 or not pause: continue
                if impulse['close']>impulse['open'] and impulse['close']-impulse['open']>=1.7*avg_range and all(p['low']>=impulse['open'] for p in pause) and max(p['high']-p['low'] for p in pause)<=0.9*ir and b['close']>prior[-1]['close'] and b['close']>b['open']:
                    tags.append(('BULL PAUSE CONTINUATION',1)); break
                if impulse['close']<impulse['open'] and impulse['open']-impulse['close']>=1.7*avg_range and all(p['high']<=impulse['open'] for p in pause) and max(p['high']-p['low'] for p in pause)<=0.9*ir and b['close']<prior[-1]['close'] and b['close']<b['open']:
                    tags.append(('BEAR PAUSE CONTINUATION',-1)); break
            for label,direction in tags:
                event={'time':b['time'].strftime('%Y-%m-%d %H:%M:%S'),'symbol':sym,'setup':label,'direction':'UP' if direction>0 else 'DOWN','entry_close':f"{b['close']:.3f}"}
                for n in HORIZONS:
                    future=by_time.get(b['time']+timedelta(minutes=n))
                    event[f'{n}m_%']=round(direction*(future['close']/b['close']-1)*100,4) if future else None
                events.append(event)
    return sorted(events,key=lambda x:(x['time'],x['symbol'],x['setup']))

def summary(events):
    grouped=defaultdict(list)
    for e in events: grouped[(e['symbol'],e['setup'])].append(e)
    result=[]
    for (sym,setup),group in sorted(grouped.items()):
        row={'symbol':sym,'setup':setup,'events':len(group)}
        for n in HORIZONS:
            values=[e[f'{n}m_%'] for e in group if e[f'{n}m_%'] is not None]
            row[f'{n}m_n']=len(values)
            row[f'{n}m_winrate']=round(100*sum(v>0 for v in values)/len(values),1) if values else None
            row[f'{n}m_avg']=round(sum(values)/len(values),4) if values else None
        result.append(row)
    return result
