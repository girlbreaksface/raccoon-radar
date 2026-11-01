"""Offline contract tests; all times are synthetic UTC integer microseconds."""
from dataclasses import replace
import unittest
from adapter import Revision, Context, Health, select


def bar(**kw):
    return replace(Revision('a', 'US.SPY', 0, 60, b'SYNTHETIC',
                            ('100', '102', '99', '101', '10'),
                            61, 1, 62, 2, 62, 2, 'FINAL', True, None), **kw)


def context(**kw):
    return replace(Context('US.SPY', (0,), 60, 100, 20,
                           (('permission', 1, 1), ('mapping', 1, 1),
                            ('calendar', 1, 1), ('finality', 1, 1),
                            ('clock', 1, 1), ('source', 1, 1)),
                           (Health(1, 1, 'VALIDATED'),), 'SYNTHETIC'), **kw)


class ContractTests(unittest.TestCase):
    def test_valid_immutable_frame(self):
        r=bar(); result=select((r,), context())
        self.assertEqual(result.ids, ('a',)); self.assertEqual(result.status, 'MOCK_READY')
        self.assertEqual(r.raw, b'SYNTHETIC')
        with self.assertRaises(AttributeError): result.ids=()

    def test_missing_each_authority(self):
        for i in range(6):
            c=context(); self.assertEqual(select((bar(),), replace(c, authorities=c.authorities[:i]+c.authorities[i+1:])).status, 'DATA_BLOCKED')

    def test_future_authority(self):
        self.assertIn('AUTHORITY', select((bar(),), context(authorities=(('permission',101,1),))).reasons)

    def test_unknown_finality_never_inferred_from_time(self):
        for label in ('UNKNOWN','PROVISIONAL'):
            self.assertIn('FINALITY', select((bar(finality=label),), context()).reasons)

    def test_uncommitted_replacement_no_fallback(self):
        b=bar(id='b',parent='a',received=70,receipt_seq=3,committed=None)
        self.assertIn('VISIBILITY',select((bar(),b),context()).reasons)

    def test_ambiguous_health_blocks(self):
        history=(Health(80,10,'VALIDATED'),Health(80,10,'DISCONNECTED'))
        self.assertIn('HEALTH',select((bar(),),context(health=history)).reasons)

    def test_completion_separate(self):
        self.assertIn('FINALITY',select((bar(complete=False),),context()).reasons)

    def test_newer_provisional_blocks_old_final(self):
        b=bar(id='b', parent='a', received=70, receipt_seq=3, committed=71, commit_seq=4,
              authority_time=71, authority_seq=4, finality='PROVISIONAL')
        self.assertIn('FINALITY', select((bar(),b),context()).reasons)

    def test_cutoff_before_after_correction(self):
        a=bar(); b=bar(id='b',parent='a',received=110,receipt_seq=21,committed=111,commit_seq=22,authority_time=111,authority_seq=22)
        earlier=select((a,),context())
        self.assertEqual(select((a,b),context()), earlier)
        self.assertEqual(select((a,b),context(cutoff=120,sequence=25)).ids,('b',))
        self.assertEqual(earlier.ids,('a',))

    def test_receipt_boundary_inclusive(self):
        self.assertEqual(select((bar(received=100,committed=100,authority_time=100),),context()).ids,('a',))
        self.assertIn('COVERAGE',select((bar(received=101),),context()).reasons)

    def test_commit_and_authority_not_yet_visible_blocks(self):
        for kw in ({'committed':101},{'commit_seq':21},{'authority_time':101},{'authority_seq':21},{'committed':None}):
            self.assertIn('VISIBILITY',select((bar(**kw),),context()).reasons)

    def test_clock_rollback_sequence(self):
        self.assertIn('COVERAGE',select((bar(received=50,receipt_seq=21),),context()).reasons)

    def test_future_malformed_payload_excluded(self):
        self.assertEqual(select((bar(),bar(id='bad',received=101,values=('bad',)*5)),context()),select((bar(),),context()))

    def test_duplicate_identical_and_conflict(self):
        self.assertEqual(select((bar(),bar()),context()).ids,('a',))
        self.assertIn('IDENTITY_CONFLICT',select((bar(),bar(raw=b'different')),context()).reasons)

    def test_branch_and_orphan(self):
        for bars in ((bar(),bar(id='b',parent='a'),bar(id='c',parent='a')),(bar(parent='missing'),)):
            self.assertIn('REVISION_GRAPH',select(bars,context()).reasons)

    def test_cycle(self):
        self.assertIn('REVISION_GRAPH',select((bar(parent='b'),bar(id='b',parent='a')),context()).reasons)

    def test_parent_same_symbol_interval_required(self):
        self.assertIn('REVISION_GRAPH',select((bar(),bar(id='b',start=60,end=120,parent='a')),context(expected=(0,60),cutoff=200)).reasons)

    def test_reordered_input_deterministic(self):
        a=bar(); b=bar(id='b',parent='a',received=70,receipt_seq=3,committed=71,commit_seq=4,authority_time=71,authority_seq=4)
        self.assertEqual(select((a,b),context()),select((b,a),context()))

    def test_gap_tail_whole_symbol(self):
        for bars,c in (((bar(),),context(expected=(0,60),cutoff=200)), ((),context()), ((bar(symbol='US.QQQ'),),context())):
            self.assertIn('COVERAGE',select(bars,c).reasons)

    def test_numeric_quality(self):
        for values in (('NaN','102','99','101','10'),('0','102','99','101','10'),('100','98','99','101','10'),('100','102','99','101','-1')):
            self.assertIn('OHLCV',select((bar(values=values),),context()).reasons)

    def test_disconnect_reconnect_requires_validation(self):
        for state in ('DISCONNECTED','RECOVERING','OVERFLOW','ENTITLEMENT_LOST','SCHEMA_DRIFT'):
            self.assertIn('HEALTH',select((bar(),),context(health=(Health(1,1,'VALIDATED'),Health(80,10,state)))).reasons)
        history=(Health(1,1,'VALIDATED'),Health(80,10,'DISCONNECTED'),Health(90,15,'RECOVERING'),Health(95,18,'VALIDATED'))
        self.assertEqual(select((bar(),),context(health=history)).ids,('a',))

    def test_future_disconnect_does_not_rewrite(self):
        self.assertEqual(select((bar(),),context(health=(Health(1,1,'VALIDATED'),Health(101,21,'DISCONNECTED')))),select((bar(),),context()))

    def test_recovery_late_never_backdated(self):
        late=bar(received=110,receipt_seq=21,committed=111,commit_seq=22,authority_time=111,authority_seq=22)
        self.assertIn('COVERAGE',select((late,),context()).reasons)
        self.assertEqual(select((late,),context(cutoff=120,sequence=25)).ids,('a',))

    def test_real_mode_rejected_and_bad_context(self):
        for c in (context(mode='LIVE'),context(expected=()),context(expected=(0,0)),context(expected=(60,0))):
            self.assertEqual(select((bar(),),c).status,'DATA_BLOCKED')

if __name__=='__main__': unittest.main()
