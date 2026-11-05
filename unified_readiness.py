"""Hash-bound offline readiness record. PASS never releases operational gates."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from durable_daily_risk import digest
from offline_rehearsal import evidence, validate_evidence

ROOT=Path(__file__).resolve().parent
GATES={
    'provider-finality':'Support confirms no authoritative finality; end-label mapping clarified for 10.11.7108, current build applicability and correction revocation unverified',
    'calendar-clock':'Unscheduled closures, beyond-2026 calendar and clock provenance unverified',
    'broker-history':'Paper historical fills unavailable; actual terminal orders lack local baseline',
    'risk-production':'Offline ledger only; overnight baseline, receipt custody, reduce-only exits and hardware durability unqualified',
    'data-rights':'Historical quote license, retention and use rights not acquired/verified',
    'empirical-edge':'No licensed quote holdout evaluated; no empirical edge claimed',
    'paper-authorization':'Offline development approval does not authorize paper orders',
    'merge-deployment':'Separate approval required',
}


def file_hash(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sources():
    return {p.relative_to(ROOT).as_posix():file_hash(p) for p in sorted(ROOT.rglob('*.py'))
            if '.git' not in p.parts and 'work' not in p.relative_to(ROOT).parts}


def foundation_check(directory):
    """Verify evidence bytes and exact current source inventory, never trust PASS alone."""
    from automation_foundation import COMMANDS, ARTIFACT_SUITES
    directory=Path(directory).resolve()
    report=json.loads((directory/'readiness.json').read_text())
    if report['source_sha256'] != sources(): raise ValueError('Source inventory mismatch')
    rows=report['repository_verification']
    if set(rows)!=set(COMMANDS): raise ValueError('Suite inventory mismatch')
    for key,row in rows.items():
        if row.get('status')!='PASS' or row.get('exit_code')!=0: raise ValueError('Suite failed: '+key)
        required = {'log': key + '.txt'}
        if key in ARTIFACT_SUITES: required['artifact'] = key + '.json'
        for kind, expected in required.items():
            if row.get(kind) != expected or not isinstance(row.get(kind+'_sha256'), str):
                raise ValueError('Missing or invalid evidence reference: '+key+'/'+kind)
            path=directory/row[kind]
            if path.resolve().parent != directory: raise ValueError('Invalid evidence path')
            if file_hash(path)!=row[kind+'_sha256']: raise ValueError('Evidence hash mismatch')
    return dict(status='PASS',readiness_sha256=file_hash(directory/'readiness.json'),environment=report['environment'],suites=rows)


def certify(*, foundation=None, broker_paths=(), rehearsal_evidence=None):
    r=evidence() if rehearsal_evidence is None else rehearsal_evidence
    validate_evidence(r)
    report=dict(schema='unified-offline-readiness-v1',as_of_utc=datetime.now(timezone.utc).isoformat(),
        certification_scope='OFFLINE_SOFTWARE_ONLY',synthetic_rehearsal='PASS',rehearsal_hash=digest(r),
        source_sha256=sources(),gates=[dict(id=k,status='HOLD',reason=v) for k,v in GATES.items()],
        paper_execution='HOLD',recording='HOLD',live_execution='NO-GO',orders='DISABLED',merge='HOLD',deployment='HOLD',
        foundation=dict(status='NOT_SUPPLIED'),broker_observations=[],limitations=[
            'Hashes are integrity checks, not signatures or proof of authentic market/broker data',
            'Fictional fills and returns are software fixtures, not empirical results'])
    if foundation is not None: report['foundation']=foundation_check(foundation)
    for path in broker_paths:
        item=json.loads(Path(path).read_text())
        if item.get('report_hash')!=digest({k:v for k,v in item.items() if k!='report_hash'}):
            raise ValueError('Broker report hash mismatch')
        if item.get('orders')!='DISABLED' or item.get('paper_execution')!='HOLD': raise ValueError('Broker scope mismatch')
        report['broker_observations'].append(dict(file_sha256=file_hash(path),report_hash=item['report_hash'],
            schema=item['schema'],observed_at_utc=item.get('observed_at_utc'),reasons=item.get('reasons',[]),
            reconciliation=item.get('reconciliation'),history_orders=item.get('history_orders'),history_fills=item.get('history_fills')))
    report['status']='HOLD'
    report['report_hash']=digest(report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--foundation',type=Path); p.add_argument('--broker',action='append',type=Path,default=[])
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); report=certify(foundation=args.foundation,broker_paths=args.broker)
    with args.output.open('x',encoding='utf-8') as f: json.dump(report,f,sort_keys=True,indent=2)
    print(json.dumps({k:report[k] for k in ('status','synthetic_rehearsal','orders','report_hash')}))


if __name__=='__main__': main()
