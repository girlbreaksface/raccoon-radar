"""Read-only, candle-derived market structure. No orders, no fabricated macro data."""
from collections import defaultdict
from datetime import datetime,time,timedelta
import math

def calculate(rows):
    groups=defaultdict(list)
    for row in rows:
        try:
            sym=str(row['symbol']).upper().strip()
            if sym.startswith('US.'): sym=sym[3:]
            if sym not in ('SPY','QQQ'):continue
            stamp=datetime.strptime(str(row.get('time') or row.get('bar_time_et')),'%Y-%m-%d %H:%M:%S')
            o,h,l,c,v=(float(row[k]) for k in ('open','high','low','close','volume'))
            if not all(math.isfinite(x) for x in (o,h,l,c,v)) or not (l<=min(o,c)<=max(o,c)<=h) or v<0:continue
            if not (time(9,30)<=stamp.time()<=time(16,0)):continue
            groups[(sym,stamp.date())].append((stamp,o,h,l,c,v))
        except (ValueError,TypeError,KeyError):continue
    out={}
    for sym in ('SPY','QQQ'):
        days=sorted(day for symbol,day in groups if symbol==sym)
        if not days:
            out[sym]={'status':'NO DATA'};continue
        day=days[-1];bars=sorted(groups[(sym,day)],key=lambda r:r[0]);unique={b[0]:b for b in bars};bars=[unique[t] for t in sorted(unique)]
        prev=sorted(groups[(sym,days[-2])]) if len(days)>1 else []
        result={'status':'OK','session':day.isoformat(),'last_candle_et':bars[-1][0].strftime('%H:%M'),'bars':len(bars),'first_candle_et':bars[0][0].strftime('%H:%M'),'last_price':bars[-1][4],
                'session_high':max(b[2] for b in bars),'session_low':min(b[3] for b in bars)}
        if prev:
            result['prior_high']=max(b[2] for b in prev);result['prior_low']=min(b[3] for b in prev);result['prior_close']=prev[-1][4]
        else:result['prior_high']=result['prior_low']=result['prior_close']=None
        # Timestamp convention is not assumed. 09:31..09:59 means 09:30
        # is absent, not a complete 30-minute opening range.
        for mins in (5,15,30):
            start=datetime.combine(day,time(9,30))
            expected={start+timedelta(minutes=i) for i in range(mins)}
            window=[b for b in bars if b[0] in expected]
            present={b[0] for b in window}
            missing=sorted(expected-present)
            result[f'or{mins}']={'high':max(b[2] for b in window),'low':min(b[3] for b in window)} if not missing else None
            result[f'or{mins}_missing']=[t.strftime('%H:%M') for t in missing]
        # Evidence-backed candidate only: retain raw provider stamps; derive interval
        # start in memory and NEVER modify raw history or label ranges verified.
        # A complete prior regular session with 390 unique 1m bars at 09:31..16:00
        # supports, but does not independently prove, close-time labeling.
        full_end_labeled = (len(bars)==390 and
            bars[0][0].time()==time(9,31) and bars[-1][0].time()==time(16,0) and
            all(bars[i][0]-bars[i-1][0]==timedelta(minutes=1) for i in range(1,len(bars))))
        result['end_labeled_full_session_evidence']=full_end_labeled
        result['candidate_interval_start_first']=(bars[0][0]-timedelta(minutes=1)).strftime('%H:%M:%S')
        for mins in (5,15,30):
            start=datetime.combine(day,time(9,30))
            candidate=[b for b in bars if start <= b[0]-timedelta(minutes=1) < start+timedelta(minutes=mins)]
            expected={start+timedelta(minutes=i) for i in range(mins)}
            actual={b[0]-timedelta(minutes=1) for b in candidate}
            result[f'candidate_or{mins}']=({'high':max(b[2] for b in candidate), 'low':min(b[3] for b in candidate)}
                if actual==expected and len(candidate)==mins else None)
        result['timestamp_convention']='Provider raw stamps retained. End-of-minute labeling is STRONGLY SUGGESTED by 390-bar session; not independently verified.' 
        result['first_five_timestamps']=[b[0].strftime('%H:%M:%S') for b in bars[:5]]
        result['last_five_timestamps']=[b[0].strftime('%H:%M:%S') for b in bars[-5:]]
        # Diagnostic only: shifted window is deliberately NOT presented as an opening range.
        start=datetime.combine(day,time(9,31))
        for mins in (5,15,30):
            shifted=[b for b in bars if start<=b[0]<start+timedelta(minutes=mins)]
            result[f'shifted_{mins}_count']=len(shifted)
        result['session_complete_390']=full_end_labeled
        # OHLC4 proxy is NOT trade-by-trade VWAP; label explicitly.
        denominator=sum(b[5] for b in bars)
        result['ohlc4_volume_weighted_proxy']=sum(((b[1]+b[2]+b[3]+b[4])/4)*b[5] for b in bars)/denominator if denominator>0 else None
        out[sym]=result
    return out

def format_report(results):
    def price(x):return f'{x:.2f}' if x is not None else 'UNAVAILABLE'
    lines=['RACCOON RADAR — MARKET STRUCTURE DESK','CANDLE-BASED RESEARCH • NOT A LIVE SIGNAL • NO ORDER ROUTING','']
    for sym,r in results.items():
        lines.append(f'=== {sym} ===')
        if r['status']!='OK':lines.extend(['No loaded historical candles.','']);continue
        lines.append(f"SESSION {r['session']} | FIRST {r['first_candle_et']} ET | LAST {r['last_candle_et']} ET | {r['bars']} candles")
        lines.append(f"Last close: {price(r['last_price'])} | Session high/low: {price(r['session_high'])} / {price(r['session_low'])}")
        lines.append(f"Previous session high/low/close: {price(r['prior_high'])} / {price(r['prior_low'])} / {price(r['prior_close'])}")
        for n in (5,15,30):
            w=r[f'or{n}'];lines.append(f"Opening range {n}m: {price(w['high'])} / {price(w['low'])}" if w else f"Opening range {n}m: INCOMPLETE (missing {', '.join(r[f'or{n}_missing'][:8])}{' ...' if len(r[f'or{n}_missing'])>8 else ''})")
        lines.append(r['timestamp_convention'])
        lines.append('Normalized interval-start candidate: first '+r['candidate_interval_start_first']+' ET (raw timestamp minus 1 minute; NOT saved)')
        for n in (5,15,30):
            w=r[f'candidate_or{n}']
            lines.append(f"PROVISIONAL end-labeled {n}m range: {price(w['high'])} / {price(w['low'])} — NOT VERIFIED FOR TRADING" if w else f'PROVISIONAL end-labeled {n}m range: INCOMPLETE')
        lines.append('First five raw timestamps: '+', '.join(r['first_five_timestamps']))
        lines.append('Last five raw timestamps: '+', '.join(r['last_five_timestamps']))
        lines.append('Provider 09:31-based candidate windows: '+', '.join(f"{n}m={r[f'shifted_{n}_count']}/{n} bars" for n in (5,15,30))+' — DIAGNOSTIC ONLY; NOT VALIDATED OPENING RANGES')
        lines.append('390-bar end-labeled candidate coverage: '+('COMPLETE (hypothesis)' if r['session_complete_390'] else 'INCOMPLETE / NOT A FULL SESSION'))
        proxy=r['ohlc4_volume_weighted_proxy']
        lines.append(f'OHLC4 volume-weighted candle proxy (NOT true VWAP): {price(proxy)}')
        if r['or15']:
            h=r['or15']['high'];l=r['or15']['low'];p=r['last_price']
            stance='ABOVE 15m RANGE' if p>h else 'BELOW 15m RANGE' if p<l else 'INSIDE 15m RANGE'
            lines.append(f'15m range location: {stance} (descriptive, not call/put recommendation)')
        lines.append('')
    lines+=['NEWS SENTIMENT: UNAVAILABLE — no sourced news feed connected',
            'ECONOMIC CALENDAR: UNAVAILABLE — no verified calendar connected',
            'VIX / TREASURY YIELDS / DOLLAR: UNAVAILABLE — no feed connected',
            'SECTOR BREADTH / OPTIONS FLOW: UNAVAILABLE — no feed connected',
            '', 'CAUTION: Loaded history can be stale. Check session/date and compare against live chart.',
            'Official opening ranges remain unverified; provisional ranges are research-only. No options fills or trading edge inferred.']
    return '\n'.join(lines)
