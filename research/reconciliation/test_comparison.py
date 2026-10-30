"""Predeclared development conformance expectations, not a held-out study."""
from dataclasses import replace
from datetime import datetime, timedelta
from hashlib import sha1
from pathlib import Path
import json
import random
import unittest

from compare import (HERE, paths, transform, evaluate, bundle_for, replay,
                     assess, canonicalize, reseal)


class ComparisonTests(unittest.TestCase):
    def test_s0_epsilon_strict_boundary_and_later_hold(self):
        from fractions import Fraction as F
        base=paths()['reversal'][:28]
        for delta,confirmed in [(F(-1,1000000),False),(F(0),False),(F(1,1000000),True)]:
            close=F(8170)+delta
            breakout=(close,close+1,close-1,close,100)
            rows=base+[breakout,breakout,(8150,8160,8140,8150,100),breakout]
            result=replay(rows)
            self.assertEqual(bool(result['events']),confirmed)
            if confirmed:
                self.assertEqual(result['events'][0][0],31)

    def test_s0_failure_precedes_touch_and_adverse_wicks_allowed(self):
        rows=paths()['reversal']
        good=rows[:30]+[(8200,8210,7900,8200,100),rows[-1]]
        self.assertEqual(replay(good)['events'],[(31,'POTENTIAL_REVERSAL_CONFIRMED',1)])
        bad=rows[:30]+[(8110,8160,7900,8110,100),rows[-1]]
        self.assertEqual(replay(bad)['events'],[])
        self.assertEqual(replay(bad)['trace'][30],'FAILED')

    def test_future_extreme_and_correction_do_not_change_earlier_s0_trace(self):
        rows=paths()['reversal']
        old=replay(rows)
        longer=replay(rows+[(100000,100001,99999,100000,100)])
        self.assertEqual(old['trace'],longer['trace'][:len(rows)])
        self.assertEqual(old['events'],longer['events'])

    def test_vendor_exact_git_blobs(self):
        for name,expected in json.loads((HERE/'vendor/PIN.json').read_text()).items():
            blob=(HERE/'vendor'/name).read_bytes()
            self.assertEqual(sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest(),expected)

    def test_frozen_expected_s0_events_and_deadlines(self):
        expected={'reversal':(31,'POTENTIAL_REVERSAL_CONFIRMED',1),
                  'continuation':(31,'CONTINUATION_CONFIRMED',-1),
                  'late_retest':(35,'POTENTIAL_REVERSAL_CONFIRMED',1)}
        phases={'no_retest':'RETEST_TIMEOUT','failed_retest':'FAILED',
                'hold_timeout':'HOLD_TIMEOUT','exact_epsilon':'EXPIRED','box_expiry':'EXPIRED',
                'one_close':'BOX','wick_only':'BOX','flat':'INSUFFICIENT_EVIDENCE'}
        for name,rows in paths().items():
            with self.subTest(name=name):
                result=replay(rows)
                self.assertEqual(result['events'],[expected[name]] if name in expected else [])
                if name in phases:
                    self.assertEqual(result['trace'][-1],phases[name])
                if name!='flat':
                    self.assertEqual(result['trace'][27],'BOX')

    def test_pr40_expected_differences_without_threshold_changes(self):
        expected={'reversal':'CONFIRMED_STRUCTURAL_REVERSAL','continuation':'TREND_CONTINUATION',
                  'exact_epsilon':'CONFIRMED_STRUCTURAL_REVERSAL','hold_timeout':'CONFIRMED_STRUCTURAL_REVERSAL',
                  'late_retest':'FAILED_REVERSAL','no_retest':'FAILED_REVERSAL'}
        for name,want in expected.items():
            self.assertEqual(evaluate(paths()[name])['p40']['classification'],want)

    def test_exact_event_times_differ(self):
        for name,ordinal in [('reversal',30),('continuation',28)]:
            b,c,requests=bundle_for(paths()[name])
            result=assess(b,c,requests[-1],synthetic=True)
            kind='CONFIRMED_STRUCTURAL_REVERSAL' if name=='reversal' else 'TREND_CONTINUATION'
            self.assertEqual([e.trigger_interval_end for e in result.tracker.events if e.kind==kind],
                             [requests[ordinal].watermark])

    def test_s0_affine_symmetry_all_cases(self):
        for name,rows in paths().items():
            base=replay(rows)
            for reflected in (False,True):
                for scale,shift in [(1,0),(3,0),(1,1000000),(7,12345)]:
                    changed=transform(rows,reflect=1000000 if reflected else None,scale=scale,shift=shift)
                    actual=replay(changed)
                    self.assertEqual(actual['trace'],base['trace'],(name,reflected,scale,shift))
                    want=[(i,k,-b if reflected else b) for i,k,b in base['events']]
                    self.assertEqual(actual['events'],want)

    def test_pr40_scaling_and_counterexamples(self):
        for name,rows in paths().items():
            base=evaluate(rows)['p40']
            self.assertEqual(evaluate(transform(rows,scale=3))['p40'],base)
        rows=paths()['reversal']
        for changed in (transform(rows,shift=1000000),transform(rows,reflect=1000000)):
            self.assertEqual(evaluate(changed)['p40']['classification'],'INSUFFICIENT_EVIDENCE')
        self.assertEqual(evaluate(transform(rows,reflect=20000))['p40']['classification'],
                         'CONFIRMED_STRUCTURAL_REVERSAL')

    def test_s0_seeded_perturbed_price_paths_affine(self):
        rng=random.Random(12003940)
        for _ in range(60):
            rows=[(r[0],r[1],r[2],r[3]+rng.randint(-10,10),r[4]) for r in paths()['reversal']]
            base=replay(rows)
            other=replay(transform(rows,reflect=1000000,scale=3,shift=17))
            self.assertEqual(base['trace'],other['trace'])
            self.assertEqual([(i,k,-b) for i,k,b in base['events']],other['events'])

    def test_prefix_no_backdating_and_batch_matches_incremental(self):
        rows=paths()['reversal']
        b,c,requests=bundle_for(rows)
        prior=None
        for i,request in enumerate(requests):
            gate=canonicalize(b,c,request)
            self.assertTrue(gate.eligible,gate.reasons)
            visible=[r.values for r in gate.frame.candles]
            self.assertEqual(replay(visible),replay(rows[:i+1]))
            # Removing unavailable future observations preserves visible decisions.
            prefix=reseal(b,b.observations[:i+1])
            batch=assess(b,c,request,synthetic=True)
            truncated=assess(prefix,c,request,synthetic=True)
            self.assertEqual(batch.decision,truncated.decision)
            stepped=assess(b,c,request,previous=prior,synthetic=True)
            prior=stepped.tracker
            self.assertEqual(batch.decision.classification,stepped.decision.classification)
            if i<31:
                self.assertEqual(replay(visible)['events'],[])
        self.assertTrue(all(e.observed_at==requests[-1].cutoff for e in batch.tracker.events))

    def test_future_bad_revision_excluded_from_both_visible_results(self):
        b,c,requests=bundle_for(paths()['reversal'])
        original=assess(b,c,requests[-1],synthetic=True)
        row=replace(b.observations[0],observation_id='FUTURE',revision_id='FUTURE',row_id='FUTURE',
                    raw_stamp='BAD',values=(float('inf'),None,True,0,100),
                    available_at='2026-10-24T00:00:00Z',received_at='2026-10-24T00:00:00Z',
                    completion_received_at='2026-10-24T00:00:00Z')
        changed=reseal(b,b.observations+(row,))
        result=assess(changed,c,requests[-1],synthetic=True)
        self.assertEqual(original.decision,result.decision)
        a=canonicalize(b,c,requests[-1]); z=canonicalize(changed,c,requests[-1])
        self.assertEqual(replay([r.values for r in a.frame.candles]),replay([r.values for r in z.frame.candles]))

    def test_final_only_gate_blocks_faults_for_both_inputs(self):
        b,c,requests=bundle_for(paths()['reversal'])
        bad_cases=[replace(b.observations[-1],finality='PROVISIONAL'),
                   replace(b.observations[-1],completed=False),
                   replace(b.observations[-1],available_at=None),
                   replace(b.observations[-1],values=(0,1,-1,0,100))]
        for row in bad_cases:
            changed=reseal(b,b.observations[:-1]+(row,))
            report=canonicalize(changed,c,requests[-1])
            self.assertFalse(report.eligible)
            self.assertIsNone(report.frame)
            self.assertEqual(assess(changed,c,requests[-1],synthetic=True).decision.classification,'INSUFFICIENT_EVIDENCE')
        for rows in (b.observations[:4]+b.observations[5:], b.observations+(replace(b.observations[-1],observation_id='DUP'),)):
            self.assertFalse(canonicalize(reseal(b,rows),c,requests[-1]).eligible)

    def test_delayed_final_is_unavailable_until_receipt(self):
        b,c,requests=bundle_for(paths()['reversal'])
        receipt=(datetime.fromisoformat(requests[-1].cutoff)+timedelta(microseconds=1)).isoformat()
        late=replace(b.observations[-1],available_at=receipt,received_at=receipt,completion_received_at=receipt)
        b=reseal(b,b.observations[:-1]+(late,))
        self.assertFalse(canonicalize(b,c,requests[-1]).eligible)
        later=replace(requests[-1],cutoff=receipt)
        self.assertTrue(canonicalize(b,c,later).eligible)

    def test_corrected_replay_preserves_old_result(self):
        b,c,requests=bundle_for(paths()['reversal'])
        original=assess(b,c,requests[-1],synthetic=True)
        rows=list(b.observations)
        for i in range(20):
            rows[i]=replace(rows[i],revision_id='CORRECTED'+str(i),values=(8100,8200,8000,8100,100))
        corrected=reseal(b,rows)
        newer=assess(corrected,c,requests[-1],synthetic=True)
        self.assertEqual(newer.decision.classification,'INSUFFICIENT_EVIDENCE')
        self.assertEqual(original.decision.classification,'CONFIRMED_STRUCTURAL_REVERSAL')
        self.assertNotEqual(original.audit_hash,newer.audit_hash)
        blocked=assess(corrected,c,replace(requests[-1],cutoff=(datetime.fromisoformat(requests[-1].cutoff)+timedelta(seconds=1)).isoformat()),
                       previous=original.tracker,synthetic=True)
        self.assertIn('PREFIX_REVISION_CHANGED',blocked.decision.reasons)
        self.assertEqual(blocked.tracker.history[:-1],original.tracker.history)
        self.assertEqual(replay([r.values for r in newer.canonical_report.frame.candles])['events'],[])


if __name__=='__main__':
    unittest.main()
