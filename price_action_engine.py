"""Read-only OHLCV price-action research. No broker or order APIs."""
import csv
from pathlib import Path

def analyze(rows):
    """Return candle-based hypotheses; all thresholds are exploratory, not validated."""
    out=[]; prior=[]
    for row in rows:
        try:
            symbol=str(row.get('symbol','')).strip()
            stamp=str(row.get('time') or row.get('bar_time_et') or '')
            o,h,l,c,v=[float(row[k]) for k in ('open','high','low','close','volume')]
            if not symbol or not (l <= min(o,c) <= max(o,c) <= h) or v < 0: continue
        except (ValueError,TypeError,KeyError): continue
        p=[x for x in prior if x['symbol']==symbol][-12:]
        ranges=[x['high']-x['low'] for x in p]
        avg_range=sum(ranges)/len(ranges) if ranges else 0
        avg_vol=sum(x['volume'] for x in p)/len(p) if p else 0
        rng=h-l; body=abs(c-o)
        burst=len(p)>=5 and avg_range>0 and body>=1.7*avg_range and v>=1.3*avg_vol
        tight=len(p)>=5 and avg_range>0 and rng<=0.65*avg_range
        last5=p[-5:]
        top=max((x['high'] for x in last5),default=h)
        bottom=min((x['low'] for x in last5),default=l)
        breakout_up=len(last5)==5 and c>top and o<=top
        breakout_down=len(last5)==5 and c<bottom and o>=bottom
        failed_up=len(last5)==5 and h>top and c<top and o<=top
        failed_down=len(last5)==5 and l<bottom and c>bottom and o>=bottom
        tags=[]
        if burst: tags.append('UP BURST' if c>o else 'DOWN BURST')
        if tight: tags.append('TIGHT CANDLE')
        if breakout_up: tags.append('BREAK ABOVE 5-BAR HIGH')
        if breakout_down: tags.append('BREAK BELOW 5-BAR LOW')
        if failed_up: tags.append('UP BREAK REJECTED')
        if failed_down: tags.append('DOWN BREAK REJECTED')
        # Candle-only balance proxy, not actual auction acceptance or order flow.
        if len(p)>=5 and avg_range>0:
            window=p[-4:]+[{'high':h,'low':l}]
            span=max(x['high'] for x in window)-min(x['low'] for x in window)
            state='BALANCE PROXY' if span<=2.0*avg_range else 'EXPANSION PROXY'
        else: state='INSUFFICIENT HISTORY'
        out.append({'time':stamp,'symbol':symbol,'close':f'{c:.3f}',
                    'auction_proxy':state,'setup':', '.join(tags) if tags else '—',
                    'range_ratio':f'{rng/avg_range:.2f}' if avg_range else '—',
                    'volume_ratio':f'{v/avg_vol:.2f}' if avg_vol else '—'})
        prior.append({'symbol':symbol,'high':h,'low':l,'close':c,'volume':v})
    return out

def load_ohlcv(path):
    with open(path,newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not {'symbol','open','high','low','close','volume'}.issubset(reader.fieldnames):
            raise ValueError('Need symbol, open, high, low, close, volume columns. Existing v3 signal log has no OHLC candles.')
        return analyze(list(reader))
