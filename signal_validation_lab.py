"""Read-only historical candle quality audit. No network, trading or database writes."""
import argparse, collections, datetime, json, sqlite3, sys, zipfile
from pathlib import Path
from zoneinfo import ZoneInfo
ET=ZoneInfo("America/New_York")
def quote(name): return '"'+name.replace('"','""')+'"'
def audit(project):
    path=project/'raccoon_history.sqlite3'
    report={"version":"1.5.5","read_only":True,"source":path.name,"checks":[],"limitations":[
        "Candle quality is not signal predictive validation.",
        "No independent SPY/QQQ bias recalculation: original calculation modules and signal definitions must be reviewed first.",
        "No options spread, fill, slippage, or profitability estimates.",
        "This audit does not access live quotes or Moomoo."]}
    def check(name,status,detail): report['checks'].append(dict(name=name,status=status,detail=detail))
    if not path.exists():
        check("Historical database","warn","Not found");return report
    try:
        con=sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True)
        con.row_factory=sqlite3.Row
        with con:
            cols=[r['name'] for r in con.execute('PRAGMA table_info(candles)')]
            report['candle_columns']=cols
            check('Candle table','pass' if cols else 'fail',f'Columns: {cols}')
            if not cols:return report
            report['total_candles']=con.execute('SELECT COUNT(*) FROM candles').fetchone()[0]
            # Detect actual schema; do not pretend to know timestamps/units.
            symbol=next((c for c in ('symbol','ticker') if c in cols),None)
            time=next((c for c in ('bar_time_et','timestamp_et','time_et','timestamp','datetime','bar_time','time') if c in cols),None)
            if not symbol or not time:
                check('Chronology audit','warn','Unknown symbol or timestamp columns; no chronological claims made')
                return report
            grouped=collections.defaultdict(list)
            sql=f'SELECT {quote(symbol)} AS sym, {quote(time)} AS ts FROM candles'
            for row in con.execute(sql):
                grouped[str(row['sym'])].append(str(row['ts']))
            report['symbols']={k:len(v) for k,v in sorted(grouped.items())}
            duplicates=sum(len(v)-len(set(v)) for v in grouped.values())
            check('Duplicate symbol/timestamp pairs','pass' if not duplicates else 'warn',f'{duplicates} duplicates')
            parsed=collections.defaultdict(list);invalid=0
            for sym,vals in grouped.items():
                for raw in vals:
                    try:
                        t=datetime.datetime.fromisoformat(raw.replace('Z','+00:00'))
                        if t.tzinfo:t=t.astimezone(ET).replace(tzinfo=None)
                        parsed[sym].append(t)
                    except (ValueError,OverflowError):invalid+=1
            check('Timestamp parsing','pass' if not invalid else 'warn',f'{invalid} unparseable timestamps')
            report['date_counts']={}
            gaps=0;outside=0
            for sym,ts in parsed.items():
                ts.sort()
                byday=collections.defaultdict(list)
                for t in ts:
                    byday[t.date().isoformat()].append(t)
                    if not (datetime.time(9,30)<=t.time()<=datetime.time(16,0)):outside+=1
                report['date_counts'][sym]={day:len(items) for day,items in sorted(byday.items())}
                for day,items in byday.items():
                    for a,b in zip(items,items[1:]):
                        if (b-a).total_seconds()>300:gaps+=1
            check('Regular-session timestamps','pass' if not outside else 'warn',f'{outside} outside 09:30–16:00 ET (requires confirmation timestamps are ET)')
            check('Intraday 5-minute gaps','pass' if not gaps else 'warn',f'{gaps} gaps >5 minutes within symbol/session; verify data cadence')
            report['gaps_over_5m']=gaps
            check('Historical coverage','pass' if report['total_candles'] else 'warn',f"{report['total_candles']} candles, {len(grouped)} symbols")
    except Exception as exc:
        check('Read-only audit','fail',f'{type(exc).__name__}: {str(exc)[:220]}')
    finally:
        if 'con' in locals():con.close()
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--project',type=Path,default=Path(__file__).resolve().parent)
    args=p.parse_args()
    project=args.project.resolve()
    result=audit(project)
    out=project/'diagnostics_reports';out.mkdir(exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    dest=out/f'raccoon_signal_audit_{stamp}.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('signal_audit.json',json.dumps(result,indent=2))
        z.writestr('SUMMARY.txt','\n'.join(f"{c['status'].upper()}: {c['name']} — {c['detail']}" for c in result['checks'])+'\n')
    print(f'Signal audit ZIP: {dest}')
    for c in result['checks']:print(f"{c['status'].upper()}: {c['name']} — {c['detail']}")
    return int(any(c['status']=='fail' for c in result['checks']))
if __name__=='__main__':sys.exit(main())
