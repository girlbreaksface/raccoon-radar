"""Opt-in raw-only quote capture for pinned Moomoo 10.11.7108.

One localhost connection and one subscription; no history, account queries,
trade context, credentials, detector or dashboard imports. No automatic retries.
Run under --supervise for a hard process lifetime bound, including SDK calls.
"""
import argparse
from datetime import datetime, time as daytime
import hashlib
from importlib.metadata import distribution, version
import json
import os
from pathlib import Path
import queue
import socket
import subprocess
import sys
import threading
import time
from zoneinfo import ZoneInfo

from capture import Journal, CaptureStopped, SYMBOLS, verify


def local_identity():
    """Pin this reviewed Windows installation without reading login/config data."""
    binary = Path(os.environ['APPDATA']) / 'moomoo_OpenD' / 'moomoo_OpenD.exe'
    binary_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
    if binary_hash != '3c2c5065c8f18dece54dc2c208317721a0c16821cfcd8fa21e45255faa38d738':
        raise RuntimeError('Unreviewed OpenD binary; connection blocked')
    package = distribution('moomoo-api')
    sources = ('moomoo/common/open_context_base.py',
               'moomoo/quote/open_quote_context.py',
               'moomoo/quote/quote_response_handler.py')
    return dict(opend_binary_sha256=binary_hash,
                sdk_source_sha256={p: hashlib.sha256(Path(package.locate_file(p)).read_bytes()).hexdigest()
                                   for p in sources})


def regular_hours(now):
    eastern = now.astimezone(ZoneInfo('America/New_York'))
    # Time-of-day restriction only. Exchange holiday/halt authority remains UNKNOWN.
    return eastern.weekday() < 5 and daytime(9, 30) <= eastern.time() < daytime(16)


def worker(directory):
    if version('moomoo-api') != '10.11.7108':
        raise RuntimeError('Unreviewed SDK version; connection blocked')
    if not regular_hours(datetime.now().astimezone()):
        raise RuntimeError('Outside regular-hours time window; connection blocked')
    identity = local_identity()
    # Load native SDK dependencies before opening even the reachability socket.
    from moomoo.quote.open_quote_context import OpenQuoteContext
    from moomoo.quote.quote_response_handler import CurKlineHandlerBase, SysNotifyHandlerBase
    from moomoo.common.constant import RET_OK, RET_ERROR, SubType, Session
    # No provider request: a single TCP reachability probe before SDK construction.
    with socket.create_connection(('127.0.0.1', 11111), timeout=2):
        pass

    pending = queue.Queue(maxsize=128)
    fault = threading.Event()
    fault_reason = ['PROVIDER_EVENT']

    def fail(reason):
        fault_reason[0] = reason
        fault.set()

    class Quotes(OpenQuoteContext):
        def _wait_reconnect(self, wait_reconnect_interval=6):
            # The pinned SDK also retries initial failures before on_connect.
            # Permit its constructor's first scheduling call only.
            if getattr(self, '_capture_connect_scheduled', False):
                self._auto_reconnect = False
                fail('INITIAL_CONNECT_FAILED')
                return
            self._capture_connect_scheduled = True
            return super()._wait_reconnect(wait_reconnect_interval)

        def on_connect(self, conn_id, info):
            self._auto_reconnect = False  # pinned SDK implementation reviewed
            return super().on_connect(conn_id, info)

        def on_disconnect(self, conn_id, reason, msg):
            self._auto_reconnect = False
            fail('DISCONNECTED')
            return super().on_disconnect(conn_id, reason, msg)

    class Candles(CurKlineHandlerBase):
        def on_recv_rsp(self, pb):
            received = (time.time_ns(), time.monotonic_ns())
            if fault.is_set(): return RET_ERROR, 'capture stopped'
            try:
                if pb.ByteSize() > 65536: raise ValueError('payload limit')
                raw = pb.SerializeToString()
                ret, table = super().on_recv_rsp(pb)
                if ret != RET_OK or table.empty: raise ValueError('response/schema')
                symbols = tuple(table['code'].unique())
                if len(symbols) != 1 or symbols[0] not in SYMBOLS:
                    raise ValueError('symbol scope')
                if set(table['k_type']) != {SubType.K_1M}: raise ValueError('interval')
                pending.put_nowait((symbols[0], tuple(table['time_key']), raw, received))
                return RET_OK, None
            except queue.Full:
                fail('QUEUE_OVERFLOW')
            except Exception:
                fail('CALLBACK_SCHEMA_OR_SCOPE')
            return RET_ERROR, 'capture stopped'

    class Notifications(SysNotifyHandlerBase):
        def on_recv_rsp(self, pb):
            # Fail on all system notifications; do not retain broad account fields.
            fail('SYSTEM_NOTIFICATION')
            return RET_OK, None

    journal = Journal(directory, dict(
        mode='LIVE_RAW', provider='moomoo', sdk_version='10.11.7108',
        endpoint='127.0.0.1:11111', interval='K_1M', session='RTH',
        user_attestation='API_ACCESS_AND_LOCAL_RETENTION_PERMITTED',
        subscription='ONE_REQUEST_NO_CACHED_FIRST_PUSH',
        source_time_mapping='UNKNOWN', calendar_authority='UNKNOWN',
        utc_clock_accuracy='UNKNOWN', entitlement_independently_verified=False,
        adjustment='OBSERVE_PROTOBUF_REHABTYPE_ONLY_NOT_CERTIFIED',
        identity=identity,
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        journal_code_sha256=hashlib.sha256(Path(__file__).with_name('capture.py').read_bytes()).hexdigest()))
    context = None
    reason = 'RUN_LIMIT'
    subscription_accepted = False
    try:
        context = Quotes(host='127.0.0.1', port=11111, is_async_connect=True)
        context.set_sync_query_connect_timeout(5)
        context.set_handler(Candles())
        context.set_handler(Notifications())
        if fault.is_set(): raise CaptureStopped(fault_reason[0])
        ret, _ = context.subscribe(list(SYMBOLS), [SubType.K_1M],
                                   is_first_push=False, subscribe_push=True,
                                   extended_time=False, session=Session.RTH)
        if fault.is_set(): raise CaptureStopped(fault_reason[0])
        if ret != RET_OK: raise CaptureStopped('SUBSCRIPTION_REJECTED')
        subscription_accepted = True
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if fault.is_set(): raise CaptureStopped(fault_reason[0])
            if not regular_hours(datetime.now().astimezone()):
                raise CaptureStopped('SESSION_TIME_END')
            journal.check()
            try: symbol, stamps, raw, received = pending.get(timeout=0.1)
            except queue.Empty: continue
            journal.append(symbol, stamps, raw, received=received)
    except CaptureStopped as exc:
        reason = str(exc)
    except Exception:
        reason = 'SDK_OR_CAPTURE_FAILURE'  # no broad provider/account payload in report
    finally:
        fault.set()
        # Seal evidence before potentially blocking SDK cleanup. The supervisor
        # marks timeout separately; a journal seal alone never means clean teardown.
        try:
            summary = journal.finish(reason)
        finally:
            journal.close()
            if context is not None: context.close()
    verify(directory)
    return dict(summary, subscription_accepted=subscription_accepted)


def supervise(directory):
    """Hard 300-second worker limit. Raw files stay local and are never uploaded."""
    directory = Path(directory).resolve()
    if directory.exists(): raise FileExistsError(directory)
    if not directory.parent.is_dir(): raise FileNotFoundError(directory.parent)
    log = directory.parent / (directory.name + '.worker.log')
    result = directory.parent / (directory.name + '.supervisor.json')
    # Reserve both evidence names before starting any child/network operation.
    with result.open('x', encoding='utf-8') as report, log.open('xb') as output:
        process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()),
                                    '--worker', str(directory)],
                                   stdout=output, stderr=subprocess.STDOUT)
        timed_out = False
        try: code = process.wait(timeout=300)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            code = process.wait(timeout=10)
        report.write(json.dumps(dict(returncode=code, timed_out=timed_out,
                                     strategy_status='DATA_BLOCKED',
                                     capture_directory=str(directory)), sort_keys=True))
        report.flush()
        os.fsync(report.fileno())
    return 1 if timed_out or code else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--supervise', type=Path)
    mode.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.supervise: raise SystemExit(supervise(args.supervise))
    outcome = worker(args.worker)
    print(json.dumps(outcome, sort_keys=True))
    raise SystemExit(0 if outcome['stop_reason'] == 'RUN_LIMIT' else 2)
