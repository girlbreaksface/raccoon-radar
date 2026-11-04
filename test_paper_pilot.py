"""Fake broker lifecycle tests; no SDK import or network."""
import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from paper_pilot import execute_pilot


class Frame(list):
    def to_dict(self, orient): return list(self)


class PilotTests(unittest.TestCase):
    def broker(self, environment='SIMULATE', rejected=False, filled=True):
        sdk = NS(RET_OK=0, TrdEnv=NS(SIMULATE='SIMULATE'),
            SimAccType=NS(STOCK_AND_OPTION='STOCK_AND_OPTION'),
            TrdAccStatus=NS(ACTIVE='ACTIVE'), TrdMarket=NS(US='US'),
            TrdSide=NS(BUY='BUY', SELL='SELL'), OrderType=NS(NORMAL='LIMIT'),
            TimeInForce=NS(DAY='DAY'), OrderStatus=NS(FILLED_ALL='FILLED_ALL'),
            ModifyOrderOp=NS(CANCEL='CANCEL'))
        class Broker:
            def __init__(self): self.calls=[]; self.qty=0; self.count=0
            def get_acc_list(self):
                return 0, Frame([dict(acc_id=123, trd_env=environment,
                    sim_acc_type='STOCK_AND_OPTION', acc_status='ACTIVE',trdmarket_auth=['US'])])
            def check(self, kwargs):
                assert kwargs['trd_env']=='SIMULATE' and kwargs['acc_id']==123
            def position_list_query(self, **kwargs):
                self.check(kwargs)
                return 0, Frame([dict(qty=self.qty,can_sell_qty=self.qty)] if self.qty else [])
            def order_list_query(self, **kwargs):
                self.check(kwargs)
                if 'order_id' not in kwargs:return 0, Frame()
                return 0, Frame([dict(order_status='FILLED_ALL' if filled else 'SUBMITTED',
                    dealt_qty=1 if filled else 0,dealt_avg_price='.19')])
            def place_order(self, **kwargs):
                self.check(kwargs); self.calls.append(kwargs); self.count+=1
                if rejected:return -1, 'synthetic rejection'
                if filled:self.qty += 1 if kwargs['trd_side']=='BUY' else -1
                return 0, Frame([dict(order_id=str(self.count))])
            def modify_order(self,*args,**kwargs):self.check(kwargs);return 0,Frame()
        return sdk,Broker()

    def invoke(self, sdk, broker, path, **kwargs):
        fingerprint=hashlib.sha256(b'raccoon-paper-account:123').hexdigest()
        return execute_pilot(sdk,broker,path,verified_quote=lambda:True,
            pause=lambda seconds:None,reviewed=True,expected_fingerprint=fingerprint,
            kill_switch=kwargs.pop('kill_switch', lambda:False),**kwargs)

    def test_round_trip_and_exclusive_journal(self):
        sdk,b=self.broker()
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'pilot.jsonl'
            self.assertEqual(self.invoke(sdk,b,path),'ROUND_TRIP_COMPLETE')
            self.assertEqual([c['trd_side'] for c in b.calls],['BUY','SELL'])
            self.assertEqual([c['price'] for c in b.calls],[.20,.01])
            self.assertEqual(b.qty,0)
            with self.assertRaises(FileExistsError): self.invoke(sdk,b,path)
            self.assertEqual(len(b.calls),2)
            self.assertIn('ROUND_TRIP_COMPLETE',path.read_text())

    def test_live_account_never_submits(self):
        sdk,b=self.broker(environment='REAL')
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):self.invoke(sdk,b,Path(root)/'pilot')
        self.assertEqual(b.calls,[])

    def test_uncertain_submission_never_retries(self):
        sdk,b=self.broker(rejected=True)
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'pilot'
            with self.assertRaises(RuntimeError):self.invoke(sdk,b,path)
            self.assertEqual(len(b.calls),1)
            self.assertIn('HALTED_RECONCILE_REQUIRED',path.read_text())

    def test_unfilled_entry_does_not_sell_short(self):
        sdk,b=self.broker(filled=False)
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(self.invoke(sdk,b,Path(root)/'pilot'),'RECONCILE_REQUIRED')
        self.assertEqual([c['trd_side'] for c in b.calls],['BUY'])

    def test_unreviewed_or_stale_never_submits(self):
        sdk,b=self.broker()
        for reviewed,fresh in ((False,True),(True,False)):
            with self.assertRaises(ValueError):
                execute_pilot(sdk,b,'unused',reviewed=reviewed,
                    verified_quote=lambda:fresh,pause=lambda n:None,expected_fingerprint='a'*64,
                    kill_switch=lambda:False)
        self.assertEqual(b.calls,[])

    def test_order_polling_respects_broker_rate_limit(self):
        sdk,b=self.broker()
        pauses=[]
        fingerprint=hashlib.sha256(b'raccoon-paper-account:123').hexdigest()
        with tempfile.TemporaryDirectory() as root:
            execute_pilot(sdk,b,Path(root)/'pilot',verified_quote=lambda:True,
                pause=pauses.append,reviewed=True,expected_fingerprint=fingerprint,kill_switch=lambda:False)
        self.assertEqual(pauses,[4,4])

    def test_missing_unknown_active_or_failed_kill_switch_never_submits(self):
        for switch in (None, lambda:True, lambda:None, lambda:0,
                       lambda: (_ for _ in ()).throw(OSError('unavailable'))):
            sdk,b=self.broker()
            with tempfile.TemporaryDirectory() as root:
                with self.assertRaises(ValueError):
                    self.invoke(sdk,b,Path(root)/'pilot',kill_switch=switch)
            self.assertEqual(b.calls,[])

    def test_kill_switch_change_before_entry_is_journaled(self):
        sdk,b=self.broker()
        values=iter((False,True))
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'pilot'
            with self.assertRaises(RuntimeError):
                self.invoke(sdk,b,path,kill_switch=lambda:next(values))
            self.assertIn('ENTRY_KILLED',path.read_text())
        self.assertEqual(b.calls,[])

    def test_kill_after_fill_allows_verified_risk_reducing_exit(self):
        sdk,b=self.broker()
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(self.invoke(sdk,b,Path(root)/'pilot',
                kill_switch=lambda:bool(b.calls)), 'ROUND_TRIP_COMPLETE')
        self.assertEqual([c['trd_side'] for c in b.calls],['BUY','SELL'])

    def test_changed_account_type_market_or_duplicate_identity_blocks_entry(self):
        for mutation in ('type','market','duplicate'):
            sdk,b=self.broker()
            original=b.get_acc_list
            calls=[]
            def changed():
                ret,rows=original()
                calls.append(True)
                if len(calls)>1:
                    if mutation=='type':rows[0]['sim_acc_type']='OTHER'
                    if mutation=='market':rows[0]['trdmarket_auth']=[]
                    if mutation=='duplicate':rows.append(dict(rows[0]))
                return ret,rows
            b.get_acc_list=changed
            with tempfile.TemporaryDirectory() as root:
                with self.assertRaises(RuntimeError):
                    self.invoke(sdk,b,Path(root)/'pilot')
            self.assertEqual(b.calls,[])
