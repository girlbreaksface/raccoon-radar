"""Raccoon Radar read-only local diagnostics. No network, brokerage or order calls.

Only reads SQLite databases using mode=ro; creates a diagnostic ZIP in chosen output
folder. Reports table counts and aggregate quality checks, not account information.
"""
import argparse, ast, csv, hashlib, importlib.util, io, json, os, sqlite3, sys, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DATABASES=('raccoon_discovery.sqlite3','raccoon_history.sqlite3','raccoon_swing.sqlite3','raccoon_fundamentals.sqlite3')
MODULES=('volume_discovery','price_action_engine','setup_detective','strategy_validation','validation_intelligence','performance_intelligence','research_journal','swing_watchlist','fundamental_intelligence')

def inspect_database(path):
    info={'file':path.name,'exists':path.is_file()}
    if not path.is_file():return info
    info['bytes']=path.stat().st_size
    # Explicit read-only URI: never initialize or migrate databases.
    uri=path.resolve().as_uri()+'?mode=ro'
    try:
        with sqlite3.connect(uri,uri=True,timeout=2) as db:
            info['integrity_check']=db.execute('PRAGMA integrity_check').fetchone()[0]
            tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            info['tables']={}
            for name in tables:
                quoted='"'+name.replace('"','""')+'"'
                info['tables'][name]={'rows':db.execute('SELECT COUNT(*) FROM '+quoted).fetchone()[0]}
            if 'discovery_snapshots' in tables:
                info['snapshots_by_session']=[{'session':s,'rows':n,'distinct_symbols':u} for s,n,u in db.execute('SELECT session,COUNT(*),COUNT(DISTINCT symbol) FROM discovery_snapshots GROUP BY session ORDER BY session DESC LIMIT 12')]
                info['snapshot_runs']=[{'scan_utc':s,'rows':n} for s,n in db.execute('SELECT scan_utc,COUNT(*) FROM discovery_snapshots GROUP BY scan_utc ORDER BY scan_utc DESC LIMIT 20')]
                info['snapshot_null_metrics']=dict(zip(('rvol50','avg_dollar_volume20','avg_dollar_volume50'),db.execute('SELECT SUM(rvol50 IS NULL),SUM(avg_dollar_volume20 IS NULL),SUM(avg_dollar_volume50 IS NULL) FROM discovery_snapshots').fetchone()))
                info['invalid_snapshot_values']=db.execute('SELECT COUNT(*) FROM discovery_snapshots WHERE volume<=0 OR close<=0 OR baseline_volume<=0 OR rvol<=0 OR avg_dollar_volume20<=0 OR (rvol50 IS NOT NULL AND rvol50<=0)').fetchone()[0]
            if 'discoveries' in tables:
                info['duplicate_discoveries']=db.execute('SELECT COUNT(*) FROM (SELECT symbol,session FROM discoveries GROUP BY symbol,session HAVING COUNT(*)>1)').fetchone()[0]
                info['discovery_session_counts']=[{'session':s,'rows':n} for s,n in db.execute('SELECT session,COUNT(*) FROM discoveries GROUP BY session ORDER BY session DESC LIMIT 12')]
    except Exception as exc:info['error']=type(exc).__name__+': '+str(exc)[:250]
    return info

def analyze(project):
    checks=[]
    def check(name,status,details):checks.append({'name':name,'status':status,'details':details})
    files={}
    for module in MODULES:
        path=project/(module+'.py'); files[module]={'present':path.is_file()}
        if path.is_file():
            try:
                ast.parse(path.read_text(encoding='utf-8-sig'))
                files[module]['syntax']='ok';files[module]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            except Exception as exc:files[module]['syntax']='error: '+str(exc)[:160]
    for p in sorted(project.glob('raccoon_dashboard*.py')):
        try:ast.parse(p.read_text(encoding='utf-8-sig'));status='ok'
        except Exception as exc:status='error: '+str(exc)[:160]
        files[p.name]={'present':True,'syntax':status,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    bad=[k for k,v in files.items() if v.get('syntax','ok')!='ok']
    check('Python syntax','fail' if bad else 'pass','Errors: '+', '.join(bad) if bad else 'All found project modules parse successfully')
    missing=[m for m in MODULES if not files[m]['present']]
    check('Supporting modules','warn' if missing else 'pass','Missing: '+', '.join(missing) if missing else 'All expected modules found')
    dbs=[inspect_database(project/n) for n in DATABASES]
    existing=[d for d in dbs if d['exists']]
    bad_dbs=[d['file'] for d in existing if d.get('integrity_check')!='ok']
    check('SQLite integrity','fail' if bad_dbs else ('pass' if existing else 'warn'),'Failed/unreadable: '+', '.join(bad_dbs) if bad_dbs else str(len(existing))+' database(s) checked')
    discovery=next(d for d in dbs if d['file']==DATABASES[0])
    if discovery['exists'] and not discovery.get('error'):
        has_snap='discovery_snapshots' in discovery.get('tables',{})
        check('Append-only discovery snapshots','pass' if has_snap else 'warn',str(discovery.get('tables',{}).get('discovery_snapshots',{}).get('rows',0))+' stored observations')
        check('Unique current discoveries','pass' if discovery.get('duplicate_discoveries',0)==0 else 'fail',str(discovery.get('duplicate_discoveries','unknown'))+' duplicate ticker/session keys')
        if has_snap:
            invalid=discovery.get('invalid_snapshot_values',0)
            check('Snapshot numeric sanity','pass' if invalid==0 else 'warn',str(invalid)+' invalid/nonpositive observations')
    else:check('Discovery database','warn','Missing or unreadable; no database created')
    result={'tool':'Raccoon Radar Diagnostics','version':'1.0','generated_utc':datetime.now(timezone.utc).isoformat(),'project_folder':str(project),'read_only':True,'no_network_or_orders':True,'checks':checks,'files':files,'databases':dbs,'limitations':['Static syntax checks do not verify runtime imports or trading accuracy.','No live OpenD connection, real-time quotes, or brokerage account is accessed.','No backtest, walk-forward performance or options execution is validated.','Report contains local project folder paths, filenames, database counts, and hashes; review before sharing.']}
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--output-dir',type=Path,default=None)
    args=parser.parse_args();project=args.project.resolve()
    if not project.is_dir():parser.error('Project folder does not exist')
    output=(args.output_dir or (project/'diagnostics_reports')).resolve();output.mkdir(parents=True,exist_ok=True)
    report=analyze(project)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    dest=output/('raccoon_diagnostics_'+stamp+'.zip')
    summary='\n'.join(f"{c['status'].upper()}: {c['name']} — {c['details']}" for c in report['checks'])
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('diagnostics.json',json.dumps(report,indent=2,ensure_ascii=False))
        z.writestr('SUMMARY.txt',summary+'\n\n'+ '\n'.join(report['limitations'])+'\n')
    print('Diagnostic ZIP: '+str(dest)+'\n'+summary)
    return 0 if not any(c['status']=='fail' for c in report['checks']) else 1
if __name__=='__main__':sys.exit(main())
