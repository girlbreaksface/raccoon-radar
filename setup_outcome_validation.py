"""Read-only study of ORIGINAL setup_detective.detect() events. No order or broker API."""
import argparse,csv,datetime,hashlib,json,sqlite3,statistics,sys,zipfile
from collections import defaultdict
from pathlib import Path
from setup_detective import detect,summary
HORIZONS=(1,3,5,15,30,60)

def validate(project):
    path=project/'raccoon_history.sqlite3'
    report={'version':'1.5.6','read_only':True,'source':str(path.name),'horizons_minutes':HORIZONS,
      'limitations':['Candle-close directional returns, not executable trade P/L or options returns.',
       'Signal is known only after the event candle completes; next-bar executable fills are NOT modeled.',
       'Overlapping events and horizons are not independent observations.',
       'In-sample exploratory results only; no held-out or forward validation.',
       'SPY/QQQ bias tile formulas are NOT independently validated by this study.',
       'Original setup labels are unchanged; these outcomes use original Setup Detective.']}
    if not path.is_file():raise FileNotFoundError(f'Historical database not found: {path}')
    con=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    try:
        con.row_factory=sqlite3.Row
        cols={x['name'] for x in con.execute('PRAGMA table_info(candles)')}
        needed={'symbol','time','open','high','low','close','volume'}
        if not needed<=cols:raise ValueError(f'History candle columns missing: {sorted(needed-cols)}')
        rows=[dict(x) for x in con.execute('SELECT symbol,time,open,high,low,close,volume FROM candles ORDER BY symbol,time')]
    finally:con.close()
    report['source_rows']=len(rows)
    original=detect(rows)
    report['original_event_count']=len(original)
    report['original_summary']=summary(original)
    closes={};dup=0
    for r in rows:
        try:
            t=datetime.datetime.strptime(str(r['time']),'%Y-%m-%d %H:%M:%S')
            key=(str(r['symbol']),t)
            if key in closes:dup+=1
            closes[key]=float(r['close'])
        except (ValueError,TypeError):pass
    report['duplicate_input_keys']=dup
    enriched=[]
    for e in original:
        row=dict(e);t=datetime.datetime.strptime(e['time'],'%Y-%m-%d %H:%M:%S')
        close=float(e['entry_close']);direction=1 if e['direction']=='UP' else -1
        for n in HORIZONS:
            future=t+datetime.timedelta(minutes=n)
            c=closes.get((e['symbol'],future)) if future.date()==t.date() else None
            row[f'{n}m_%']=round(100*direction*(c/close-1),4) if c is not None and close>0 else None
        enriched.append(row)
    discrepancies=[]
    for old,new in zip(original,enriched):
        for n in (1,3,5):
            a=old[f'{n}m_%'];b=new[f'{n}m_%']
            if a!=b:
                discrepancies.append({'time':old['time'],'symbol':old['symbol'],'setup':old['setup'],'horizon':n,'original':a,'recomputed':b})
    report['original_horizon_discrepancies']=discrepancies[:30]
    report['original_horizon_discrepancy_count']=len(discrepancies)
    grouped=defaultdict(list)
    for e in enriched:
        t=datetime.datetime.strptime(e['time'],'%Y-%m-%d %H:%M:%S')
        window='09:30–10:30' if datetime.time(9,30)<=t.time()<datetime.time(10,30) else 'other'
        grouped[(e['symbol'],e['setup'],window)].append(e)
    result=[]
    for (symbol,setup,window),group in sorted(grouped.items()):
        item={'symbol':symbol,'setup':setup,'window':window,'events':len(group),'sessions':len({e['time'][:10] for e in group})}
        for n in HORIZONS:
            values=[e[f'{n}m_%'] for e in group if e[f'{n}m_%'] is not None]
            item[f'{n}m_n']=len(values)
            item[f'{n}m_hit_rate_pct']=round(100*sum(x>0 for x in values)/len(values),2) if values else None
            item[f'{n}m_mean_pct']=round(statistics.mean(values),5) if values else None
            item[f'{n}m_median_pct']=round(statistics.median(values),5) if values else None
        result.append(item)
    report['grouped_results']=result
    report['missing_outcome_counts']={str(n):sum(e[f'{n}m_%'] is None for e in enriched) for n in HORIZONS}
    report['status']='pass' if not discrepancies and not dup else 'review'
    return report,enriched

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parent);a=parser.parse_args()
    project=a.project.resolve()
    try:report,events=validate(project)
    except Exception as exc:
        print(f'FAILED: {type(exc).__name__}: {exc}',file=sys.stderr);return 1
    out=project/'diagnostics_reports';out.mkdir(exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    path=out/f'raccoon_setup_outcomes_{stamp}.zip'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('setup_outcomes.json',json.dumps(report,indent=2))
        if events:
            from io import StringIO
            stream=StringIO();writer=csv.DictWriter(stream,fieldnames=list(events[0]));writer.writeheader();writer.writerows(events)
            z.writestr('events.csv',stream.getvalue())
        z.writestr('README.txt','Exploratory candle-close event study. NOT a backtest of executable trades, option P/L, or bias tile accuracy.\n')
    print('Report ZIP:',path)
    print('Original events:',report['original_event_count'],'| groups:',len(report['grouped_results']))
    print('Original 1/3/5-minute recomputation differences:',report['original_horizon_discrepancy_count'])
    print('Status:',report['status'])
    return 0 if report['status']=='pass' else 2
if __name__=='__main__':sys.exit(main())
