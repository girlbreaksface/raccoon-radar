"""Fictional cents/contracts only, disposable explicit SQLite paths."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from durable_daily_risk import Ledger, RiskBlocked, replay

ACCOUNT = 'a'*64
LIMITS = dict(trades=3, loss_cents=5000, exposure_cents=50000, mark_age_seconds=30)
NOW = '2026-11-05T15:00:00+00:00'


def event(key, kind, **kw):
    return dict(id=key, kind=kind, at=NOW, **kw)


ORIGIN = event('origin','origin', inventory='DECLARED_FLAT')
BUY = event('r1','reserve',intent='entry',contract='FICTIONAL_SPY_CALL',qty=2,cap_cents=22000)
FILL = event('f1','fill',intent='entry',side='BUY',qty=1,price_cents=10000,fee_cents=65)
MARK = event('m1','mark',contract='FICTIONAL_SPY_CALL',bid_cents=9000)


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'synthetic.sqlite3'
        self.ledger = Ledger(self.path, ACCOUNT, LIMITS, create=True)
        self.addCleanup(lambda: self.ledger.close())
        self.ledger.append(ORIGIN,now=NOW)

    def append(self,*rows):
        for row in rows: result,_ = self.ledger.append(row,now=NOW)
        return result

    def test_independent_integer_accounting_and_restart(self):
        self.append(BUY,FILL,MARK)
        state = self.ledger.state(NOW)
        self.assertEqual((state['trades'],state['realized_cents'],state['unrealized_cents'],state['exposure_cents']), (1,'-65','-1000','21935'))
        # Independent arithmetic: 22000 reservation - 10065 spent + 10000 inventory.
        receipt = dict(self.ledger.receipt)
        other = Ledger(self.path,ACCOUNT,LIMITS,checkpoint=receipt)
        try: self.assertEqual(other.state(NOW),state)
        finally: other.close()
        before = dict(self.ledger.receipt)
        self.append(FILL)
        self.assertEqual(self.ledger.receipt,before)
        with self.assertRaises(RiskBlocked): self.append(dict(FILL,price_cents=10001))

    def test_partial_exit_fees_and_no_double_count(self):
        self.append(BUY,FILL,dict(FILL,id='f2',price_cents=11000),event('done','terminal',intent='entry'),MARK)
        sell = event('rs','reserve',intent='exit',contract='FICTIONAL_SPY_CALL',qty=1,cap_cents=1)
        self.append(sell,event('fs','fill',intent='exit',side='SELL',qty=1,price_cents=12000,fee_cents=65),dict(MARK,id='m2'))
        state=self.ledger.state(NOW)
        self.assertEqual(state['realized_cents'],'1305')  # 12000 - average 10500 - 3*65
        self.assertEqual(state['unrealized_cents'],'-1500')
        self.assertEqual(state['trades'],1)

    def test_missing_stale_marks_and_day_roll(self):
        self.assertIn('MISSING_OR_STALE_MARK',self.append(BUY,FILL)['reasons'])
        self.append(MARK)
        self.assertIn('MISSING_OR_STALE_MARK',self.ledger.state('2026-11-05T15:00:31+00:00')['reasons'])
        reasons=self.ledger.state('2026-11-06T15:00:00+00:00')['reasons']
        self.assertIn('OVERNIGHT_BASELINE_UNVERIFIED',reasons)
        self.assertIn('OVERNIGHT_PENDING',reasons)

    def test_loss_limit_exposure_and_pending_trade_capacity(self):
        self.append(BUY,FILL,dict(MARK,bid_cents=4000))
        self.assertIn('LOSS_LIMIT',self.ledger.state(NOW)['reasons'])
        with self.assertRaises(RiskBlocked): self.append(dict(BUY,id='r2',intent='new'))
        with self.assertRaises(RiskBlocked):
            replay([ORIGIN,dict(BUY,qty=True)],NOW,LIMITS)

    def test_scope_checkpoint_and_rollback_detection(self):
        for account, limits, receipt in [('b'*64,LIMITS,self.ledger.receipt),(ACCOUNT,dict(LIMITS,trades=4),self.ledger.receipt),(ACCOUNT,LIMITS,dict(count=0,head='0'*64))]:
            with self.assertRaises(RiskBlocked): Ledger(self.path,account,limits,checkpoint=receipt)
        self.ledger.db.execute("UPDATE events SET body='{}'")
        with self.assertRaises((RiskBlocked,KeyError)): self.ledger.state(NOW)

    def test_second_writer_cannot_use_stale_receipt(self):
        other=Ledger(self.path,ACCOUNT,LIMITS,checkpoint=self.ledger.receipt)
        try:
            self.append(BUY)
            with self.assertRaises(RiskBlocked): other.append(BUY,now=NOW)
        finally: other.close()

    def test_atomic_failure_does_not_change_receipt(self):
        before=dict(self.ledger.receipt)
        with self.assertRaises(RiskBlocked): self.append(FILL)
        self.assertEqual(before,self.ledger.receipt)
        self.assertEqual(self.ledger.state(NOW)['trades'],0)
        self.append(BUY,FILL)
        with self.assertRaises(RiskBlocked): self.append(dict(FILL,id='overfill',qty=2))

    def test_committed_reply_lost_blocks_old_checkpoint(self):
        before=dict(self.ledger.receipt)
        self.append(BUY)
        with self.assertRaises(RiskBlocked): Ledger(self.path,ACCOUNT,LIMITS,checkpoint=before)

    def test_unknown_short_future_and_conflicting_events(self):
        for bad in [dict(ORIGIN,id='bad',kind='mystery'),dict(BUY,at='2026-11-06T00:00:00+00:00'),dict(BUY,cap_cents=50001)]:
            with self.assertRaises(RiskBlocked): self.append(bad)
        self.append(BUY)
        with self.assertRaises(RiskBlocked): self.append(dict(FILL,side='SELL'))


if __name__ == '__main__': unittest.main()
