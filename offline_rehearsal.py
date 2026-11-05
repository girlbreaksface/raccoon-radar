"""Fictional end-to-end exercise; no SDK, network or execution adapter."""
import argparse
from datetime import date, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import tempfile
from durable_daily_risk import Ledger, digest
from production_indicators import Candle, evaluate, causal_quote, session
from paper_account_reconciliation import normalize, compare

LIMITS=dict(trades=3,loss_cents=2000,exposure_cents=6000,mark_age_seconds=30)


def candles(symbol):
    rows=[]
    for day,count in ((date(2026,11,4),390),(date(2026,11,5),15)):
        start=session(day)[0]
        for i in range(count):
            n=len(rows); close=Decimal(100)+Decimal(n)/100
            rows.append(Candle(symbol,start+timedelta(minutes=i),start+timedelta(minutes=i+1),
                start+timedelta(minutes=i+1,seconds=2),n+1,str(close-Decimal('.01')),
                str(close+Decimal('.02')),str(close-Decimal('.02')),str(close),'100',
                'FINAL','VERIFIED_START_END'))
    return rows


def rehearsal(scenario='baseline'):
    if scenario not in ('baseline','gap','stale','mismatch'): raise ValueError('Unknown scenario')
    report=dict(schema='fictional-e2e-v1',scenario=scenario,scope='FICTIONAL_ONLY',stages=[],
                paper_execution='HOLD',recording='HOLD',live_execution='NO-GO',orders='DISABLED',merge='HOLD',deployment='HOLD')
    with tempfile.TemporaryDirectory(prefix='fictional-e2e-') as tmp:
        path=Path(tmp)/'synthetic.sqlite3'
        ledger=Ledger(path,'f'*64,LIMITS,create=True)
        try:
            base=candles('SPY')[-1].available_at
            def append(key,kind,at,**kw):
                return ledger.append(dict(id=key,kind=kind,at=at.isoformat(),**kw),now=at.isoformat())
            append('origin','origin',base,inventory='DECLARED_FLAT')
            simulated=[]
            for symbol in ('SPY','QQQ'):
                rows=candles(symbol)
                if scenario=='gap': rows.pop(200)
                decision=evaluate(rows,symbol=symbol,evaluated_at=base,evaluation_sequence=406,required_through=rows[-1].end)
                stage=dict(symbol=symbol,indicator=decision,input_hash=digest([str(r) for r in rows]))
                report['stages'].append(stage)
                if decision['status']!='READY_OFFLINE': stage['outcome']='SIGNAL_BLOCKED'; continue
                # Explicit fictional conjunction, separate from provider/production wiring.
                bullish=Decimal(rows[-1].close)>Decimal(decision['vwap']) and Decimal(decision['ema9'])>Decimal(decision['ema21'])
                stage['signal']='BULLISH' if bullish else 'BEARISH'
                contract='US.'+symbol+'FICTIONAL'+('CALL' if bullish else 'PUT')
                quote_at=base+timedelta(seconds=1)
                quote_event=base-timedelta(seconds=1) if scenario=='stale' else quote_at
                stage['contract']=dict(code=contract,fictional=True,multiplier=100,bid='.19',ask='.20',
                                       event_at=quote_event.isoformat(),received_at=quote_at.isoformat())
                if not causal_quote(decision,symbol=symbol,event_at=quote_event,received_at=quote_at,sequence=407):
                    stage['outcome']='QUOTE_BLOCKED'; continue
                # Two contracts processed at equal times, retaining ledger chronology.
                at=base+timedelta(seconds=1)
                entry=symbol+'entry'
                state,_=append(symbol+'reserve','reserve',at,intent=entry,contract=contract,qty=1,cap_cents=2065)
                stage['risk_reservation']=state
                append(symbol+'buy','fill',at,intent=entry,side='BUY',qty=1,price_cents=2000,fee_cents=65)
                append(symbol+'entrydone','terminal',at,intent=entry)
                append(symbol+'mark','mark',at,contract=contract,bid_cents=1900)
                receipt=dict(ledger.receipt)
                ledger.close()
                ledger=Ledger(path,'f'*64,LIMITS,checkpoint=receipt)
                stage['restart_receipt']=receipt
                exit_intent=symbol+'exit'
                append(symbol+'exitreserve','reserve',at,intent=exit_intent,contract=contract,qty=1,cap_cents=1)
                append(symbol+'sell','fill',at,intent=exit_intent,side='SELL',qty=1,price_cents=2400,fee_cents=65)
                append(symbol+'exitdone','terminal',at,intent=exit_intent)
                for side in ('BUY','SELL'):
                    simulated.append(dict(order_id=symbol+side,code=contract,qty='1',dealt_qty='1',trd_side=side,order_status='FILLED_ALL'))
                stage['outcome']='SIMULATED_ROUND_TRIP'
            # Independent fictional broker view; never inferred from persisted positions.
            observed=normalize([],simulated)
            expected=normalize([],simulated)
            if scenario=='mismatch': observed['orders']=observed['orders'][:-1]
            report['reconciliation']=dict(reasons=compare(observed,expected),observed_hash=digest(observed),expected_hash=digest(expected))
            report['risk']=ledger.state((base+timedelta(seconds=1)).isoformat())
            report['checkpoint']=dict(ledger.receipt)
        finally: ledger.close()
    report['status']='PASS' if (all(s['outcome']=='SIMULATED_ROUND_TRIP' for s in report['stages'])
                    and not report['reconciliation']['reasons'] and report['risk']['realized_cents']=='540'
                    and report['risk']['positions']=={}) else 'BLOCKED'
    report['report_hash']=digest(report)
    return report


def evidence():
    reports={s:rehearsal(s) for s in ('baseline','gap','stale','mismatch')}
    if reports['baseline']['status']!='PASS' or any(reports[s]['status']!='BLOCKED' for s in ('gap','stale','mismatch')):
        raise ValueError('Unexpected rehearsal outcomes')
    return dict(schema='offline-rehearsal-evidence-v1',reports=reports,report_hash=digest(reports))


def validate_evidence(value):
    if value != evidence(): raise ValueError('Evidence differs from independent rerun')


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); result=evidence(); validate_evidence(result)
    with args.output.open('x',encoding='utf-8') as f: json.dump(result,f,sort_keys=True,indent=2)
    print('PASS: fictional baseline, gap, stale/causal quote and reconciliation mismatch')


if __name__=='__main__': main()
