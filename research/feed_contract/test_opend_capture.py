"""Fake SDK lifecycle and supervisor tests; no installed provider required."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch
import opend_capture as live
from capture import verify


class FakeTable:
    empty = False
    def __init__(self, symbol): self.symbol = symbol
    def __getitem__(self, key):
        if key == 'code':
            return types.SimpleNamespace(unique=lambda: [self.symbol])
        return {'k_type': ['K_1M'], 'time_key': ['2026-10-30 10:00:00']}[key]


class FakePB:
    def __init__(self, symbol): self.table = FakeTable(symbol)
    def ByteSize(self): return 16
    def SerializeToString(self): return b'SYNTHETIC_PROTOBUF'


class LifecycleTests(unittest.TestCase):
    def run_fake(self, accepted=True, overflow=False, disconnect=False, initial_failure=False):
        calls = []
        self.calls = calls
        class Context:
            def __init__(self, **kw):
                calls.append(('connect', kw)); self.handlers = []
                if initial_failure:
                    self._auto_reconnect = True
                    self._wait_reconnect(0)
                    self._wait_reconnect(6)
            def _wait_reconnect(self, delay=6): calls.append(('scheduled', delay))
            def on_connect(self, *a): pass
            def on_disconnect(self, *a): calls.append(('disconnect',))
            def set_sync_query_connect_timeout(self, n): calls.append(('timeout', n))
            def set_handler(self, h): self.handlers.append(h)
            def subscribe(self, symbols, intervals, **kw):
                calls.append(('subscribe', symbols, intervals, kw))
                if disconnect:
                    self.on_disconnect(1, None, 'SYNTHETIC')
                    self._reconnect_flag = self._auto_reconnect
                    calls.append(('reconnect', self._reconnect_flag))
                if accepted:
                    for i in range(129 if overflow else 2):
                        self.handlers[0].on_recv_rsp(FakePB(('US.SPY', 'US.QQQ')[i % 2]))
                return (0 if accepted else -1), None
            def close(self): calls.append(('close',))
        class Candles:
            def on_recv_rsp(self, pb): return 0, pb.table
        modules = {
            'moomoo': types.ModuleType('moomoo'),
            'moomoo.quote': types.ModuleType('moomoo.quote'),
            'moomoo.common': types.ModuleType('moomoo.common'),
            'moomoo.quote.open_quote_context': types.SimpleNamespace(OpenQuoteContext=Context),
            'moomoo.quote.quote_response_handler': types.SimpleNamespace(
                CurKlineHandlerBase=Candles, SysNotifyHandlerBase=object),
            'moomoo.common.constant': types.SimpleNamespace(RET_OK=0, RET_ERROR=-1,
                SubType=types.SimpleNamespace(K_1M='K_1M'), Session=types.SimpleNamespace(RTH='RTH'))}
        with tempfile.TemporaryDirectory(prefix='synthetic-sdk-') as temp:
            path = Path(temp) / 'capture'
            with patch.dict(sys.modules, modules), patch.object(live, 'version', return_value='10.11.7108'), \
                 patch.object(live, 'local_identity', return_value={'environment': 'SYNTHETIC'}), \
                 patch.object(live, 'regular_hours', return_value=True), \
                 patch.object(live.socket, 'create_connection', return_value=MagicMock()), \
                 patch.object(live.time, 'monotonic', side_effect=[0, 0, 1, 121]):
                live.worker(path)
            return calls, json.loads((path/'summary.json').read_text()), verify(path)

    def test_one_subscription_scope_no_cached_push_close_and_raw(self):
        calls, summary, records = self.run_fake()
        sub = [c for c in calls if c[0] == 'subscribe']
        self.assertEqual(len(sub), 1)
        self.assertEqual(sub[0][1:3], (['US.SPY', 'US.QQQ'], ['K_1M']))
        self.assertEqual(sub[0][3], dict(is_first_push=False, subscribe_push=True,
                                      extended_time=False, session='RTH'))
        self.assertEqual(calls[-1], ('close',))
        self.assertEqual(len(records), 2)
        self.assertEqual(summary['strategy_status'], 'DATA_BLOCKED')

    def test_subscription_rejection_seals_empty_evidence_and_closes(self):
        calls, summary, records = self.run_fake(accepted=False)
        self.assertEqual(summary['stop_reason'], 'SUBSCRIPTION_REJECTED')
        self.assertEqual(records, ())
        self.assertEqual(calls[-1], ('close',))

    def test_queue_overflow_stops_instead_of_dropping_and_continuing(self):
        _, summary, records = self.run_fake(overflow=True)
        self.assertEqual(summary['stop_reason'], 'QUEUE_OVERFLOW')
        self.assertEqual(records, ())

    def test_disconnect_disables_reconnect_and_stops(self):
        calls, summary, records = self.run_fake(disconnect=True)
        self.assertIn(('reconnect', False), calls)
        self.assertEqual(summary['stop_reason'], 'DISCONNECTED')
        self.assertEqual(records, ())

    def test_unreviewed_sdk_never_connects(self):
        with patch.object(live, 'version', return_value='UNKNOWN'), \
             patch.object(live.socket, 'create_connection') as connect:
            with self.assertRaises(RuntimeError): live.worker(Path('unused'))
        connect.assert_not_called()

    def test_initial_connection_failure_never_schedules_retry(self):
        calls, summary, records = self.run_fake(initial_failure=True)
        self.assertEqual([c for c in calls if c[0] == 'scheduled'], [('scheduled', 0)])
        self.assertFalse(any(c[0] == 'subscribe' for c in calls))
        self.assertEqual(summary['stop_reason'], 'INITIAL_CONNECT_FAILED')
        self.assertEqual(records, ())
        self.assertEqual(calls[-1], ('close',))

    def test_supervisor_kills_hung_worker(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'synthetic'
            fake = MagicMock()
            fake.wait.side_effect = [live.subprocess.TimeoutExpired('synthetic', 300), -9]
            with patch.object(live.subprocess, 'Popen', return_value=fake):
                self.assertEqual(live.supervise(path), 1)
            fake.kill.assert_called_once()
            result = json.loads((Path(temp)/'synthetic.supervisor.json').read_text())
            self.assertTrue(result['timed_out'])

    def test_cleanup_runs_when_seal_write_fails(self):
        with patch.object(live.Journal, 'finish', side_effect=OSError('synthetic disk failure')):
            with self.assertRaises(OSError): self.run_fake()
        self.assertEqual(self.calls[-1], ('close',))

    def test_existing_capture_directory_blocks_child(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(live.subprocess, 'Popen') as child:
                with self.assertRaises(FileExistsError): live.supervise(Path(temp))
            child.assert_not_called()

    def test_time_of_day_scope_handles_dst_and_weekend(self):
        self.assertTrue(live.regular_hours(datetime(2026, 10, 30, 14, tzinfo=timezone.utc)))
        self.assertFalse(live.regular_hours(datetime(2026, 10, 31, 14, tzinfo=timezone.utc)))
        self.assertFalse(live.regular_hours(datetime(2026, 10, 30, 20, tzinfo=timezone.utc)))


if __name__ == '__main__': unittest.main()
