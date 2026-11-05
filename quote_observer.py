"""SPY/QQQ quote-only metadata preflight and volatile revision observation.

No subscription mutation, recording, historical request or execution imports.
Provider bars never become FINAL merely because time has elapsed.
"""
import base64
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from threading import Lock
from zoneinfo import ZoneInfo

from production_indicators import session

SYMBOLS = ('US.SPY', 'US.QQQ')
SUPPORT_VERSION = '10.11.7108'
SUPPORT_EMAIL_SHA256 = '0a0876d3bfcf934b79c9128c032cf4b043fd8e13715cdf1f6a7b882d47a40a22'
ET = ZoneInfo('America/New_York')


def utc(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('AWARE_RECEIPT_REQUIRED')
    return value.astimezone(timezone.utc)


def interval(label):
    """Version-scoped reversible derivation; never changes the original label."""
    end = datetime.fromisoformat(label)
    if end.tzinfo is not None or end.second or end.microsecond:
        raise ValueError('EXCHANGE_LOCAL_MINUTE_LABEL_REQUIRED')
    end = end.replace(tzinfo=ET)
    start = end - timedelta(minutes=1)
    bounds = session(start.date())
    if not bounds or not bounds[0] <= utc(start) < utc(end) <= bounds[1]:
        raise ValueError('RTH_CALENDAR_BOUNDARY')
    return {'start': utc(start).isoformat(), 'end': utc(end).isoformat(),
            'inclusivity': '[start,end)', 'mapping': 'SUPPORT_CONFIRMED_10.11.7108'}


class RevisionBook:
    """Bounded volatile arrival ledger. Discarded on exit while recording is HOLD.

    Local revision numbers describe arrival order, never provider version/order.
    Preserve serialized SDK payload and original row values separately. Nothing
    promotes these observations into the FINAL-only production indicator path.
    """
    def __init__(self, *, sdk_version, opend_version, capacity=1000):
        if type(capacity) is not int or not 1 <= capacity <= 10000:
            raise ValueError('BOUNDED_CAPACITY_REQUIRED')
        self.sdk_version, self.opend_version = sdk_version, opend_version
        self.capacity = capacity
        self._records, self._last, self._lock = [], {}, Lock()

    def accept(self, row, raw_payload, *, received_at, monotonic_ns,
               source_context='quote.live.K_1M'):
        if source_context != 'quote.live.K_1M':
            raise ValueError('COVERAGE_CONTEXT_MIXING_FORBIDDEN')
        if (type(row) is not dict or row.get('code') not in SYMBOLS or
                row.get('k_type') != 'K_1M' or type(raw_payload) is not bytes or
                not raw_payload or type(monotonic_ns) is not int or monotonic_ns < 0):
            raise ValueError('CALLBACK_SCOPE')
        receipt = utc(received_at)
        original = json.loads(json.dumps(row, allow_nan=False))
        key = (original['code'], original['time_key'])
        derived, reason = None, 'SDK_OPEND_VERSION_NOT_CONFIRMED'
        if self.sdk_version == self.opend_version == SUPPORT_VERSION:
            try:
                derived = interval(original['time_key'])
                reason = 'AUTHORITATIVE_FINALITY_UNAVAILABLE'
            except (ValueError, TypeError):
                reason = 'INTERVAL_OR_CALENDAR_UNVERIFIED'
        with self._lock:
            if len(self._records) >= self.capacity:
                raise ValueError('VOLATILE_CAPACITY_STOP')
            if self._records and monotonic_ns < self._records[-1]['monotonic_ns']:
                raise ValueError('RECEIPT_CLOCK_ORDER')
            prior = self._last.get(key)
            value_hash = hashlib.sha256(json.dumps(original, sort_keys=True,
                separators=(',', ':'), allow_nan=False).encode()).hexdigest()
            record = dict(arrival_sequence=len(self._records)+1,
                local_revision=1 if prior is None else prior['local_revision']+1,
                changed=None if prior is None else prior['row_sha256'] != value_hash,
                previous_arrival=None if prior is None else prior['arrival_sequence'],
                received_at_utc=receipt.isoformat(), monotonic_ns=monotonic_ns,
                original=original, raw_sdk_protobuf_b64=base64.b64encode(raw_payload).decode(),
                payload_sha256=hashlib.sha256(raw_payload).hexdigest(), row_sha256=value_hash,
                source_context=source_context, coverage='NASDAQ_ONLY_SUPPORT_REPORTED',
                coverage_in_payload=False, sdk_version=self.sdk_version,
                opend_version=self.opend_version, support_email_sha256=SUPPORT_EMAIL_SHA256,
                derived_interval=derived, finality='UNKNOWN', signal_status='BLOCKED',
                reason=reason, recording='HOLD', orders='DISABLED')
            self._records.append(record)
            self._last[key] = record
            return copy.deepcopy(record)

    def summary(self):
        with self._lock:
            return dict(callback_rows=len(self._records),
                revisions=sum(r['previous_arrival'] is not None for r in self._records),
                changed_revisions=sum(r['changed'] is True for r in self._records),
                symbols=sorted({r['original']['code'] for r in self._records}),
                raw_recording='HOLD', finality='UNKNOWN', signals='BLOCKED', orders='DISABLED')


def callback_handler(base, book):
    """SDK callback adapter. Retains raw bytes only in bounded process memory."""
    import time
    class Handler(base):
        def on_recv_rsp(self, rsp_pb):
            receipt, ticks = datetime.now(timezone.utc), time.monotonic_ns()
            try:
                raw = rsp_pb.SerializeToString()
                ret, frame = super().on_recv_rsp(rsp_pb)
                if ret != 0: return -1, None
                for row in frame.to_dict('records'):
                    if row.get('code') not in SYMBOLS or row.get('k_type') != 'K_1M':
                        continue
                    book.accept(row, raw, received_at=receipt, monotonic_ns=ticks)
                return 0, None
            except Exception:
                self.failed = True
                return -1, None
    return Handler()


def preflight(factory, *, sdk_version, handler_base=None, seconds=0, wait=None):
    """Read only metadata. Factory must create only a localhost quote context.

    Do not return full user info, account identifiers or provider errors.
    Subscription inventory is observation, not subscription/delivery success.
    """
    if type(seconds) not in (int, float) or not 0 <= seconds <= 5:
        raise ValueError('BOUNDED_OBSERVATION_REQUIRED')
    result = dict(schema='quote-observer-preflight-v1',
        observed_at_utc=datetime.now(timezone.utc).isoformat(), sdk_version=sdk_version,
        support_version=SUPPORT_VERSION, support_email_sha256=SUPPORT_EMAIL_SHA256,
        recording='HOLD', paper_execution='HOLD', live_execution='NO-GO',
        orders='DISABLED', status='HOLD', query_trace=[], close_confirmed=False,
        callback_delivery='UNVERIFIED', subscription_success='NOT_TESTED_NO_MUTATION', reasons=[])
    ctx = None
    try:
        ctx = factory(host='127.0.0.1', port=11111)
        result['query_trace'].append('get_user_info')
        ret, info = ctx.get_user_info()
        if ret != 0 or type(info) is not dict or 'us_qot_right' not in info:
            raise ValueError('ENTITLEMENT_QUERY_UNVERIFIED')
        right = info['us_qot_right']
        if type(right) not in (str, int): raise ValueError('ENTITLEMENT_SCHEMA')
        result['us_qot_right'] = str(right)
        result['lv3_level_observed'] = str(right) == 'LV3'
        result['query_trace'].append('get_global_state')
        ret, state = ctx.get_global_state()
        if ret != 0 or type(state) is not dict: raise ValueError('GLOBAL_STATE_UNVERIFIED')
        result['opend_version'] = str(state.get('server_ver', 'UNKNOWN'))
        result['quote_logged_in'] = str(state.get('qot_logined', 'UNKNOWN'))
        if sdk_version != SUPPORT_VERSION or result['opend_version'] != SUPPORT_VERSION:
            result['reasons'].append('VERSION_APPLICABILITY_UNVERIFIED')
        result['query_trace'].append('query_subscription')
        ret, subs = ctx.query_subscription(is_all_conn=True)
        if ret != 0 or type(subs) is not dict: raise ValueError('SUBSCRIPTION_INVENTORY_UNVERIFIED')
        codes = subs.get('sub_list', {}).get('K_1M', [])
        result['existing_k1m_symbols'] = [s for s in SYMBOLS if s in codes]
        if handler_base is not None:
            import time
            book = RevisionBook(sdk_version=sdk_version, opend_version=result['opend_version'])
            handler = callback_handler(handler_base, book)
            if ctx.set_handler(handler) != 0: raise ValueError('HANDLER_REGISTRATION_FAILED')
            (time.sleep if wait is None else wait)(seconds)
            result['volatile_observation'] = book.summary()
            if getattr(handler, 'failed', False): result['reasons'].append('CALLBACK_PARSE_OR_CAPACITY_FAILURE')
            if result['volatile_observation']['symbols'] == list(SYMBOLS):
                result['callback_delivery'] = 'OBSERVED_BOTH_SYMBOLS_NOT_LATENCY_CERTIFIED'
        result['reasons'].extend(['PROMOTION_EXPIRY_UNKNOWN', 'AUTHORITATIVE_FINALITY_UNAVAILABLE'])
        if result['callback_delivery'] == 'UNVERIFIED':
            result['reasons'].append('CALLBACK_DELIVERY_UNVERIFIED')
    except Exception as exc:
        result['reasons'].append('READ_ONLY_QUERY_FAILED')
    finally:
        if ctx is not None:
            try:
                ctx.close()
                result['close_confirmed'] = True
            except Exception:
                result['reasons'].append('CLOSE_UNCONFIRMED')
    return result


def local_preflight():
    # No project execution modules, wildcard SDK import or trade context symbols.
    from importlib.metadata import version
    from moomoo.quote.open_quote_context import OpenQuoteContext
    from moomoo.quote.quote_response_handler import CurKlineHandlerBase
    return preflight(OpenQuoteContext, sdk_version=version('moomoo-api'),
                     handler_base=CurKlineHandlerBase, seconds=5)


if __name__ == '__main__':
    print(json.dumps(local_preflight(), sort_keys=True, indent=2))
