"""Explicit read-only SIMULATE order-history probe; never queries REAL fills."""
import argparse
from datetime import datetime, timezone, date
import hashlib
import json
from pathlib import Path
from paper_account_reconciliation import digest


def probe(sdk, expected_fingerprint, start, end):
    if not (date.fromisoformat(start) <= date.fromisoformat(end)):
        raise ValueError('Invalid date range')
    report=dict(schema='broker-history-provenance-v1', history='HOLD', orders='DISABLED',
                paper_execution='HOLD', recording='HOLD', live_execution='NO-GO', merge='HOLD', deployment='HOLD',
                start=start,end=end,query_trace=[],reasons=['PAPER_HISTORICAL_FILLS_UNSUPPORTED'],
                history_fills='UNAVAILABLE_DOCUMENTED', account_fingerprint=None)
    ctx=None
    try:
        ctx=sdk.OpenSecTradeContext(filter_trdmarket=sdk.TrdMarket.US,host='127.0.0.1',port=11111,security_firm=sdk.SecurityFirm.FUTUINC)
        report['query_trace'].append('get_acc_list')
        ret,frame=ctx.get_acc_list()
        if ret != sdk.RET_OK: raise ValueError('Accounts unavailable')
        rows=frame.to_dict('records')
        rows_account=rows
        eligible=[r for r in rows if r.get('trd_env')==sdk.TrdEnv.SIMULATE
                  and r.get('sim_acc_type')==sdk.SimAccType.STOCK_AND_OPTION
                  and r.get('acc_status')==sdk.TrdAccStatus.ACTIVE
                  and sdk.TrdMarket.US in r.get('trdmarket_auth',[])]
        if len(eligible)!=1: raise ValueError('Ambiguous account')
        acc=eligible[0]['acc_id']
        fingerprint=hashlib.sha256(('raccoon-paper-account:'+str(acc)).encode()).hexdigest()
        if fingerprint != expected_fingerprint: raise ValueError('Account mismatch')
        report['account_fingerprint']=fingerprint
        report['query_trace'].append('history_order_list_query_SIMULATE')
        ret,frame=ctx.history_order_list_query(start=start+' 00:00:00',end=end+' 23:59:59',
                    trd_env=sdk.TrdEnv.SIMULATE,acc_id=acc,order_market=sdk.TrdMarket.US)
        if ret != sdk.RET_OK:
            report['history_orders']='UNAVAILABLE_QUERY_FAILED'
        else:
            rows=frame.to_dict('records')
            if len(rows)>10000: raise ValueError('Unbounded history')
            # No account identifiers, prices or provider error strings retained.
            normalized=[{k:str(r.get(k,'')) for k in ('order_id','code','trd_side','qty','dealt_qty','order_status','create_time','updated_time')} for r in rows]
            normalized.sort(key=lambda r:r['order_id'])
            report.update(history_orders='OBSERVED_NOT_COMPLETE',row_count=len(rows),normalized_hash=digest(normalized))
        report['query_trace'].append('get_acc_list')
        ret,frame=ctx.get_acc_list()
        if ret != sdk.RET_OK or frame.to_dict('records') != rows_account:
            raise ValueError('Account changed')
    except Exception:
        report['reasons'].append('QUERY_OR_SCOPE_UNVERIFIED')
    finally:
        report['close_confirmed']=False
        if ctx is not None:
            try: ctx.close(); report['close_confirmed']=True
            except Exception: report['reasons'].append('CLOSE_FAILED')
    report['observed_at_utc']=datetime.now(timezone.utc).isoformat()
    report['report_hash']=digest(report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--start',required=True); p.add_argument('--end',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    baseline=json.loads(args.baseline.read_text())
    if baseline['report_hash'] != digest({k:v for k,v in baseline.items() if k!='report_hash'}):
        raise ValueError('Baseline hash mismatch')
    from importlib.metadata import version
    if version('moomoo-api')!='10.12.7208': raise ValueError('Unreviewed SDK')
    with args.output.open('x',encoding='utf-8') as f:
        import moomoo
        report=probe(moomoo,baseline['account_fingerprint'],args.start,args.end)
        report['sdk_version']=version('moomoo-api')
        report['code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        report['report_hash']=digest({k:v for k,v in report.items() if k!='report_hash'})
        json.dump(report,f,sort_keys=True,indent=2)
    print(json.dumps(report,sort_keys=True))


if __name__=='__main__': main()
