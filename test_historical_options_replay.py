import copy
from datetime import datetime, timedelta, timezone
from decimal import localcontext
import tempfile
import unittest
from pathlib import Path
from historical_options_replay import VERSION, replay, signals, rank, export, encoded, cost_scenarios, evaluation_plan


def fixture():
    """Entirely fictional prices/quotes; not downloaded market data."""
    opening = datetime(2026,11,2,14,30,tzinfo=timezone.utc)
    def at(seconds):
        return (opening+timedelta(seconds=seconds)).isoformat()
    bars = []
    for i in range(21):
        close = 500-i
        bars.append(dict(end=at((i+1)*60),available=at((i+1)*60),
                         open=str(close+1),high=str(close+5),low=str(close-1),
                         close=str(close),volume='100',pv=str(close*100),
                         final=True,revision=0,generation=0))
    # low must be above next close for strict breakdown.
    for b in bars:
        b['low'] = str(int(b['close']))
    quotes = [dict(available=at(1261+i),observed=at(1261+i),bid=bid,
                   ask=ask,bid_size='10',ask_size='10',volume='100',open_interest='200')
              for i,(bid,ask) in enumerate([('.23','.24'),('.29','.30'),('.30','.31'),('.32','.33'),('.31','.32')])]
    c = dict(id='SYNTHETICSPYPUT',symbol='SPY',right='PUT',expiry='2026-11-02',
             strike='480',multiplier=100,available=at(0),quotes=quotes)
    session = dict(date='2026-11-02',open=at(0),cutoff=at(1265),close=at(23400),
                   bars={'SPY':bars},contracts=[c])
    return dict(schema=VERSION,quality='SYNTHETIC',provenance={'source':'FICTIONAL_TEST_ONLY'},sessions=[session])


class ReplayTests(unittest.TestCase):
    def test_same_entries_four_distinct_exits_and_costs(self):
        result = replay(fixture(),{'slippage_per_side':'0'})
        rows = result['trades']
        self.assertEqual(len(rows),4)
        self.assertEqual(len({r['signal_id'] for r in rows}),1)
        self.assertEqual([r['entry'] for r in rows],['0.24']*4)
        self.assertEqual([r['net'] for r in rows],['3.00','4.00','6.00','6.00'])
        self.assertTrue(all(r['reason']=='TARGET' for r in rows))

    def test_repeat_and_decimal_context_independent(self):
        expected = replay(fixture())
        with localcontext() as context:
            context.prec = 6
            self.assertEqual(replay(fixture()),expected)

    def test_gap_does_not_invent_exit(self):
        d = fixture()
        del d['sessions'][0]['contracts'][0]['quotes'][1:]
        rows = replay(d)['trades']
        self.assertTrue(all(r['status']=='UNRESOLVED' and 'net' not in r for r in rows))

    def test_invalid_path_blocks_even_if_next_quote_wins(self):
        d = fixture()
        d['sessions'][0]['contracts'][0]['quotes'][1]['bid_size']='0'
        self.assertTrue(all(r['reason']=='PATH_GAP_OR_INVALID_QUOTE' for r in replay(d)['trades']))

    def test_stop_gap_fill_uses_observed_bid(self):
        d = fixture()
        q = d['sessions'][0]['contracts'][0]['quotes'][1]
        q.update(bid='.10',ask='.11')
        rows = replay(d,{'slippage_per_side':'0'})['trades']
        self.assertEqual([r['net'] for r in rows],['-16.00']*4)
        self.assertTrue(all(r['reason']=='STOP' for r in rows))

    def test_cutoff_exact_quote_only(self):
        d = fixture()
        for q in d['sessions'][0]['contracts'][0]['quotes'][1:]:
            q.update(bid='.24',ask='.25')
        self.assertTrue(all(r['reason']=='CUTOFF' for r in replay(d)['trades']))
        d['sessions'][0]['contracts'][0]['quotes'].pop()
        self.assertTrue(all(r['status']=='UNRESOLVED' for r in replay(d)['trades']))

    def test_entry_fee_counts_against_budget(self):
        rows = replay(fixture(),{'budget':'24.5','slippage_per_side':'0'})['trades']
        self.assertTrue(all(r['reason']=='ENTRY_BUDGET' for r in rows))

    def test_future_quote_cannot_be_entry(self):
        d = fixture()
        d['sessions'][0]['contracts'][0]['quotes'][0]['observed']='2026-11-02T15:00:00+00:00'
        self.assertTrue(all(r['status']=='REJECTED' for r in replay(d)['trades']))

    def test_prefix_invariance(self):
        d = fixture()
        before = signals(d['sessions'][0])
        b = copy.deepcopy(d['sessions'][0]['bars']['SPY'][-1])
        b.update(end='2026-11-02T14:52:00+00:00',available='2026-11-02T14:52:00+00:00')
        d['sessions'][0]['bars']['SPY'].append(b)
        self.assertEqual(signals(d['sessions'][0])[:-1],before)

    def test_quality_fail_closed(self):
        for field,value in [('close','NaN'),('revision',1),('generation',1),('final',False),('end','2026-11-02T14:31:00')]:
            with self.subTest(field=field):
                d=fixture()
                d['sessions'][0]['bars']['SPY'][-1][field]=value
                with self.assertRaises((ValueError,TypeError)):
                    replay(d)
        d=fixture()
        d['sessions'][0]['bars']['SPY'].pop(3)
        with self.assertRaises(ValueError):
            replay(d)

    def test_scope_and_duplicate_quotes(self):
        d=fixture()
        d['sessions'][0]['contracts'][0]['expiry']='2026-11-03'
        self.assertTrue(all(r['status']=='REJECTED' for r in replay(d)['trades']))
        d=fixture()
        quotes=d['sessions'][0]['contracts'][0]['quotes']
        quotes.insert(1,copy.deepcopy(quotes[0]))
        with self.assertRaises(ValueError):
            replay(d)

    def test_export_identical_bytes_unique_files(self):
        result=replay(fixture())
        with tempfile.TemporaryDirectory() as directory:
            a,b=export(result,directory),export(result,directory)
            self.assertNotEqual(a,b)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            self.assertEqual(a.read_bytes(),encoded(result)+b'\n')

    def test_ranking_is_deterministic_and_causal(self):
        d=fixture()
        c=d['sessions'][0]['contracts'][0]
        other=copy.deepcopy(c)
        other['id']='BETTER'
        other['quotes'][0]['bid']='.239'
        d['sessions'][0]['contracts'].append(other)
        self.assertTrue(all(r['contract']=='BETTER' for r in replay(d)['trades']))
        other['quotes'][0]['available']='2026-11-02T14:51:02+00:00'
        other['quotes'][0]['observed']='2026-11-02T14:51:02+00:00'
        other['quotes'].pop(1)
        self.assertTrue(all(r['contract']=='SYNTHETICSPYPUT' for r in replay(d)['trades']))

    def test_frozen_split_is_chronological_and_discloses_inspection(self):
        dates=['2026-11-0'+str(i) for i in range(1,6)]
        plan=evaluation_plan(dates,[dates[-1]])
        self.assertEqual(plan['development'],dates[:3])
        self.assertTrue(plan['test_previously_inspected'])
        self.assertEqual(plan['walk_forward'][-1]['train'],dates[:-1])

    def test_scenarios_do_not_double_charge_spread(self):
        runs=cost_scenarios(fixture())
        self.assertEqual(runs['optimistic']['trades'][0]['net'],'3.00')
        self.assertEqual(runs['base']['trades'][0]['entry'],'0.245')
        self.assertEqual(runs['base']['trades'][0]['exit'],'0.295')
        self.assertEqual(runs['base']['trades'][0]['net'],'3.000')
        self.assertEqual(runs['stress']['trades'][0]['entry_cost'],'26.500')

    def test_metadata_must_be_known_at_signal(self):
        d=fixture()
        d['sessions'][0]['contracts'][0]['available']='2026-11-02T15:00:00+00:00'
        rows=replay(d)['trades']
        self.assertEqual(len(rows),4)
        self.assertTrue(all(r['status']=='REJECTED' for r in rows))

    def test_availability_order_blocks_future_feature_leak(self):
        d=fixture()
        d['sessions'][0]['bars']['SPY'][0]['available']='2026-11-02T15:00:00+00:00'
        with self.assertRaises(ValueError):
            replay(d)

    def test_shared_exposure_and_daily_limit(self):
        d=fixture()
        session=d['sessions'][0]
        session['cutoff']='2026-11-02T14:52:05+00:00'
        b=copy.deepcopy(session['bars']['SPY'][-1])
        b.update(end='2026-11-02T14:52:00+00:00',available='2026-11-02T14:52:00+00:00',
                 open='480',close='479',low='479',high='484',pv='47900')
        session['bars']['SPY'].append(b)
        quotes=session['contracts'][0]['quotes']
        q=copy.deepcopy(quotes[0])
        q.update(available='2026-11-02T14:52:01+00:00',observed='2026-11-02T14:52:01+00:00')
        quotes.append(q)
        rows=replay(d)['trades']
        self.assertEqual(len(rows),8)
        self.assertTrue(all(r['reason']=='SHARED_EXPOSURE_RESERVATION' for r in rows[4:]))
        rows=replay(d,{'daily_limit':1})['trades']
        self.assertTrue(all(r['reason']=='DAILY_LIMIT' for r in rows[4:]))

    def test_indicator_conventions_are_explicit(self):
        points=signals(fixture()['sessions'][0])
        self.assertFalse(any(r['eligible'] for r in points[:20]))
        self.assertTrue(points[-1]['eligible'])
        self.assertEqual(points[-1]['session_vwap'],'490')
        self.assertTrue(points[-1]['breakdown'] and points[-1]['rejection'])

    def test_no_fabricated_candle_fill_mode(self):
        d=fixture()
        d['quality']='CANDLES'
        with self.assertRaises(ValueError):
            replay(d)

    def test_quote_gap_over_limit_is_unresolved(self):
        d=fixture()
        q=d['sessions'][0]['contracts'][0]['quotes'][1]
        q.update(available='2026-11-02T14:51:08+00:00', observed='2026-11-02T14:51:08+00:00')
        d['sessions'][0]['contracts'][0]['quotes']=d['sessions'][0]['contracts'][0]['quotes'][:2]
        rows=replay(d)['trades']
        self.assertEqual(len(rows),4)
        self.assertTrue(all(r['reason']=='PATH_GAP_OR_INVALID_QUOTE' for r in rows))


if __name__=='__main__':
    unittest.main()
