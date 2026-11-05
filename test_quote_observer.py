"""Fictional callbacks; no SDK import, network, subscriptions or recording."""
import ast
import base64
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import unittest
from quote_observer import RevisionBook, interval, preflight, callback_handler, SUPPORT_VERSION
from production_indicators import session

NOW = datetime(2026, 11, 5, 15, 0, 0, 123456, timezone.utc)
ROW = dict(code='US.SPY', k_type='K_1M', time_key='2026-11-05 09:31:00',
           open='100', close='101', high='102', low='99', volume='12.345')


class ObserverTests(unittest.TestCase):
    def book(self, **kw):
        return RevisionBook(sdk_version=SUPPORT_VERSION, opend_version=SUPPORT_VERSION, **kw)

    def test_support_interval_boundaries_dst_and_early_close(self):
        for day in (date(2026,3,6), date(2026,3,9), date(2026,11,27)):
            opening, closing = session(day)
            label=(opening+timedelta(minutes=1)).astimezone(__import__('quote_observer').ET).strftime('%Y-%m-%d %H:%M:%S')
            self.assertEqual(interval(label)['start'], opening.isoformat())
            label=closing.astimezone(__import__('quote_observer').ET).strftime('%Y-%m-%d %H:%M:%S')
            self.assertEqual(interval(label)['end'], closing.isoformat())
        for label in ('2026-11-05 09:30:00','2026-11-27 13:01:00',
                      '2026-11-26 10:00:00','2026-11-05 10:00:00.123','2027-01-04 10:00:00'):
            with self.assertRaises(ValueError): interval(label)

    def test_preserve_raw_reordered_revisions_and_duplicate_arrivals(self):
        b=self.book()
        rows=[ROW,dict(ROW,time_key='2026-11-05 09:32:00'),dict(ROW,low='98'),dict(ROW,low='98')]
        records=[b.accept(r,bytes([i+1]),received_at=NOW,monotonic_ns=i) for i,r in enumerate(rows)]
        self.assertEqual([r['local_revision'] for r in records],[1,1,2,3])
        self.assertEqual([r['changed'] for r in records],[None,None,True,False])
        self.assertEqual(records[2]['previous_arrival'],1)
        self.assertEqual(records[0]['original'],ROW)
        self.assertEqual(base64.b64decode(records[0]['raw_sdk_protobuf_b64']),b'\x01')
        self.assertTrue(records[0]['received_at_utc'].endswith('.123456+00:00'))
        self.assertTrue(all(r['finality']=='UNKNOWN' and r['signal_status']=='BLOCKED' for r in records))
        records[0]['original']['volume']='tampered'
        self.assertEqual(b.summary()['changed_revisions'],1)

    def test_no_silent_coverage_merge_or_version_promotion(self):
        b=self.book()
        with self.assertRaises(ValueError):
            b.accept(ROW,b'raw',received_at=NOW,monotonic_ns=1,source_context='quote.historical')
        b=RevisionBook(sdk_version='10.12.7208',opend_version=SUPPORT_VERSION)
        r=b.accept(ROW,b'raw',received_at=NOW,monotonic_ns=1)
        self.assertIsNone(r['derived_interval'])
        self.assertEqual(r['reason'],'SDK_OPEND_VERSION_NOT_CONFIRMED')

    def test_capacity_scope_clock_and_invalid_values_fail_closed(self):
        b=self.book(capacity=1)
        b.accept(ROW,b'raw',received_at=NOW,monotonic_ns=2)
        with self.assertRaises(ValueError): b.accept(ROW,b'raw',received_at=NOW,monotonic_ns=3)
        for row,raw,receipt,ticks in ((dict(ROW,code='US.AAPL'),b'raw',NOW,1),
                (ROW,b'',NOW,1),(ROW,b'raw',NOW.replace(tzinfo=None),1),
                (dict(ROW,volume=float('nan')),b'raw',NOW,1)):
            with self.assertRaises(ValueError): self.book().accept(row,raw,received_at=receipt,monotonic_ns=ticks)
        b=self.book(); b.accept(ROW,b'raw',received_at=NOW,monotonic_ns=2)
        with self.assertRaises(ValueError): b.accept(ROW,b'raw',received_at=NOW,monotonic_ns=1)

    def test_read_only_allowlist_closure_redaction_and_delivery_not_inferred(self):
        calls=[]
        class Fake:
            def get_user_info(self): calls.append('user'); return 0,dict(us_qot_right='LV3',secret='PRIVATE')
            def get_global_state(self): calls.append('state'); return 0,dict(server_ver=SUPPORT_VERSION,qot_logined=1)
            def query_subscription(self, **kw):
                calls.append(('query',kw)); return 0,dict(sub_list={'K_1M':['US.SPY','US.QQQ','US.AAPL']})
            def close(self): calls.append('close')
        def factory(**kw):
            self.assertEqual(kw,dict(host='127.0.0.1',port=11111)); return Fake()
        r=preflight(factory,sdk_version=SUPPORT_VERSION)
        self.assertEqual(calls,['user','state',('query',dict(is_all_conn=True)),'close'])
        self.assertEqual(r['existing_k1m_symbols'],['US.SPY','US.QQQ'])
        self.assertEqual(r['callback_delivery'],'UNVERIFIED')
        self.assertNotIn('PRIVATE',str(r)); self.assertTrue(r['close_confirmed'])

    def test_query_error_is_redacted_and_context_closed(self):
        closed=[]
        class Fake:
            def get_user_info(self): raise ValueError('PRIVATE_ACCOUNT_DETAILS')
            def close(self): closed.append(True)
        r=preflight(lambda **kw:Fake(),sdk_version=SUPPORT_VERSION)
        self.assertNotIn('PRIVATE',str(r)); self.assertEqual(closed,[True])
        self.assertEqual(r['status'],'HOLD')

    def test_callback_adapter_keeps_serialized_bytes_and_filters_other_symbols(self):
        class Frame:
            def to_dict(self, mode):
                return [ROW,dict(ROW,code='US.AAPL')]
        class Base:
            def on_recv_rsp(self, rsp): return 0, Frame()
        class Payload:
            def SerializeToString(self): return b'fictional protobuf'
        b=self.book(); handler=callback_handler(Base,b)
        self.assertEqual(handler.on_recv_rsp(Payload()),(0,None))
        self.assertEqual(b.summary()['callback_rows'],1)
        self.assertEqual(b.summary()['symbols'],['US.SPY'])

    def test_callback_capacity_error_blocks_without_spilling_to_disk(self):
        class Frame:
            def to_dict(self, mode): return [ROW]
        class Base:
            def on_recv_rsp(self, rsp): return 0,Frame()
        class Payload:
            def SerializeToString(self): return b'fixture'
        b=self.book(capacity=1); handler=callback_handler(Base,b)
        self.assertEqual(handler.on_recv_rsp(Payload()),(0,None))
        self.assertEqual(handler.on_recv_rsp(Payload()),(-1,None))
        self.assertTrue(handler.failed)
        self.assertEqual(b.summary()['callback_rows'],1)

    def test_observation_duration_is_bounded_before_context_creation(self):
        for seconds in (-1,6,float('nan'),True):
            with self.assertRaises(ValueError):
                preflight(lambda **kw:self.fail('must not open'),sdk_version=SUPPORT_VERSION,seconds=seconds)

    def test_observer_imports_and_calls_have_no_mutation_paths(self):
        tree=ast.parse(Path(__file__).with_name('quote_observer.py').read_text())
        calls={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertTrue({'get_user_info','get_global_state','query_subscription','set_handler','close'} <= calls)
        self.assertFalse({'subscribe','unsubscribe','unlock_trade','place_order','modify_order','history_order_list_query'} & calls)
        imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        self.assertFalse(any('trade' in str(n) or 'execution' in str(n) for n in imports))


if __name__=='__main__': unittest.main()
