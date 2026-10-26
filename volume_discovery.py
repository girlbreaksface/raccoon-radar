"""Read-only daily unusual-volume discovery. Data sourced from local Moomoo OpenD.
No orders, no claims about options liquidity or future price direction.
"""
import sqlite3, math
from pathlib import Path
from datetime import datetime, timezone
from contextlib import closing

DB_PATH=Path(__file__).resolve().parent/'raccoon_discovery.sqlite3'
# Initial curated *underlying* universe; NOT a verified options-liquidity whitelist.
UNIVERSE=('SPY','QQQ','IWM','DIA','AAPL','MSFT','NVDA','AMZN','META','GOOGL','TSLA','AMD','AVGO','NFLX','PLTR','MU','INTC','COIN','MSTR','HOOD','SOFI','UBER','BAC','JPM','GS','XLF','XLE','XLK','SMH','TLT','GLD','SLV','XBI','TQQQ','SQQQ','DIS','WMT','COST','CRM','ORCL')

def initialize(path=DB_PATH):
    """Additive migration: preserve all existing discoveries and their IDs."""
    with closing(sqlite3.connect(path)) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS discoveries (id INTEGER PRIMARY KEY, scan_utc TEXT NOT NULL, symbol TEXT NOT NULL, session TEXT NOT NULL, close REAL NOT NULL, volume REAL NOT NULL, baseline_volume REAL NOT NULL, rvol REAL NOT NULL, change_pct REAL, range_pct REAL, notes TEXT NOT NULL, UNIQUE(symbol,session))""")
        existing={r[1] for r in db.execute('PRAGMA table_info(discoveries)')}
        for col in ('rvol50','avg_dollar_volume20','avg_dollar_volume50','baseline_volume50'):
            if col not in existing: db.execute(f'ALTER TABLE discoveries ADD COLUMN {col} REAL')
        db.execute("""CREATE TABLE IF NOT EXISTS discovery_snapshots (
            id INTEGER PRIMARY KEY, scan_utc TEXT NOT NULL, symbol TEXT NOT NULL,
            session TEXT NOT NULL, close REAL NOT NULL, volume REAL NOT NULL,
            baseline_volume REAL NOT NULL, rvol REAL NOT NULL,
            rvol50 REAL, avg_dollar_volume20 REAL, avg_dollar_volume50 REAL,
            change_pct REAL, range_pct REAL, notes TEXT NOT NULL)""")
        db.commit()

def evaluate(symbol,bars,min_baseline=20):
    """Compare last completed bar with strictly preceding observed sessions."""
    clean={}
    raw_dates=[]
    for b in bars:
        try:
            day=str(b['time_key'])[:10]
            raw_dates.append(day)
            if datetime.strptime(day,'%Y-%m-%d').date().isoformat()!=day: continue
            volume=float(b['volume']);close=float(b['close']);op=float(b['open']);hi=float(b['high']);lo=float(b['low'])
            if not all(math.isfinite(x) for x in (volume,close,op,hi,lo)): continue
            if volume<=0 or min(close,op,hi,lo)<=0 or lo>min(op,close) or hi<max(op,close): continue
            clean[day]={'date':day,'volume':volume,'close':close,'open':op,'high':hi,'low':lo}
        except (KeyError,TypeError,ValueError,OverflowError):continue
    # Fail closed rather than silently treating an older candle as latest.
    if raw_dates and max(raw_dates) not in clean: return None
    ordered=sorted(clean.values(),key=lambda b:b['date'])
    if len(ordered)<min_baseline+1:return None
    latest=ordered[-1];history=ordered[:-1]
    b20=history[-min_baseline:];mean20=sum(b['volume'] for b in b20)/len(b20)
    if mean20<=0:return None
    b50=history[-50:] if len(history)>=50 else None
    mean50=sum(b['volume'] for b in b50)/50 if b50 else None
    avg_dollar20=sum(b['volume']*b['close'] for b in b20)/len(b20)
    avg_dollar50=sum(b['volume']*b['close'] for b in b50)/50 if b50 else None
    prev=history[-1]['close']
    return {'symbol':symbol,'session':latest['date'],'close':latest['close'],'volume':latest['volume'],
      'baseline_volume':mean20,'rvol':latest['volume']/mean20,
      'baseline_volume50':mean50,'rvol50':latest['volume']/mean50 if mean50 else None,
      'avg_dollar_volume20':avg_dollar20,'avg_dollar_volume50':avg_dollar50,
      'change_pct':(latest['close']/prev-1)*100,
      'range_pct':(latest['high']-latest['low'])/latest['close']*100,
      'notes':'Completed daily candle; 20 prior observed sessions. 50-session metrics require 50 prior sessions. Dollar volume approximated by daily close × shares. Underlying only; options liquidity unverified.'}

def save_results(rows,path=DB_PATH):
    initialize(path);stamp=datetime.now(timezone.utc).isoformat(timespec='microseconds')
    with closing(sqlite3.connect(path)) as db:
        with db:
            for r in rows:
                keys=('symbol','session','close','volume','baseline_volume','rvol','change_pct','range_pct','notes','rvol50','avg_dollar_volume20','avg_dollar_volume50','baseline_volume50')
                vals=[r.get(k) for k in keys]
                db.execute("""INSERT INTO discoveries (scan_utc,symbol,session,close,volume,baseline_volume,rvol,change_pct,range_pct,notes,rvol50,avg_dollar_volume20,avg_dollar_volume50,baseline_volume50)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(symbol,session) DO UPDATE SET scan_utc=excluded.scan_utc,close=excluded.close,volume=excluded.volume,baseline_volume=excluded.baseline_volume,rvol=excluded.rvol,change_pct=excluded.change_pct,range_pct=excluded.range_pct,notes=excluded.notes,rvol50=excluded.rvol50,avg_dollar_volume20=excluded.avg_dollar_volume20,avg_dollar_volume50=excluded.avg_dollar_volume50,baseline_volume50=excluded.baseline_volume50""",[stamp]+vals)
                db.execute("""INSERT INTO discovery_snapshots(scan_utc,symbol,session,close,volume,baseline_volume,rvol,rvol50,avg_dollar_volume20,avg_dollar_volume50,change_pct,range_pct,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    [stamp]+[r.get(k) for k in ('symbol','session','close','volume','baseline_volume','rvol','rvol50','avg_dollar_volume20','avg_dollar_volume50','change_pct','range_pct','notes')])

def list_results(path=DB_PATH,limit=200):
    initialize(path)
    with closing(sqlite3.connect(path)) as db:
        db.row_factory=sqlite3.Row
        return [dict(x) for x in db.execute('SELECT * FROM discoveries ORDER BY session DESC,rvol DESC LIMIT ?', (limit,))]

def list_snapshots(path=DB_PATH,limit=1000):
    initialize(path)
    with closing(sqlite3.connect(path)) as db:
        db.row_factory=sqlite3.Row
        return [dict(x) for x in db.execute('SELECT * FROM discovery_snapshots ORDER BY id DESC LIMIT ?', (limit,))]

def scan_moomoo(tickers=UNIVERSE,progress=None):
    from moomoo import OpenQuoteContext,RET_OK,KLType
    from datetime import datetime,timedelta
    from zoneinfo import ZoneInfo
    now=datetime.now(ZoneInfo('America/New_York'))
    # Use only prior calendar day as latest when current session may be incomplete.
    end=(now.date() if (now.weekday()<5 and (now.hour>16 or (now.hour==16 and now.minute>=15))) else now.date()-timedelta(days=1))
    start=end-timedelta(days=115)
    ctx=None;results=[];errors=[]
    try:
        ctx=OpenQuoteContext(host='127.0.0.1',port=11111)
        for idx,ticker in enumerate(tickers,1):
            try:
                ret,data,_=ctx.request_history_kline('US.'+ticker,start=start.isoformat(),end=end.isoformat(),ktype=KLType.K_DAY,max_count=150)
                if ret!=RET_OK or not hasattr(data,'iterrows'):raise RuntimeError(str(data)[:120])
                rows=[r.to_dict() for _,r in data.iterrows() if str(r.get('time_key',''))[:10]<=end.isoformat()]
                found=evaluate(ticker,rows)
                if found and found['session']<=end.isoformat():results.append(found)
                else:errors.append(ticker+': insufficient completed daily bars')
            except Exception as exc:errors.append(ticker+': '+str(exc)[:110])
            if progress:progress(idx,len(tickers),ticker)
    finally:
        if ctx is not None:ctx.close()
    results.sort(key=lambda r:r['rvol'],reverse=True)
    return results,errors
