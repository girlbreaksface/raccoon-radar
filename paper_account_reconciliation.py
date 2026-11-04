"""Bounded read-only SIMULATE reconciliation. No execution or recovery actions."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import time

VERSION = 'paper-account-reconciliation-v1'
TERMINAL = {'FILLED_ALL', 'CANCELLED_ALL', 'CANCELLED_PART', 'FAILED', 'DISABLED', 'DELETED'}
PENDING = {'WAITING_SUBMIT', 'SUBMITTING', 'SUBMITTED', 'FILLED_PART'}
EMPTY_BASELINE = {'schema': VERSION, 'positions': [], 'orders': []}


class Blocked(ValueError):
    pass


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def quantity(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise Blocked('INVALID_QUANTITY')
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise Blocked('INVALID_QUANTITY') from None
    if not result.is_finite() or not 0 <= result <= 10**12 or result.as_tuple().exponent < -8:
        raise Blocked('INVALID_QUANTITY')
    return result


def security(value):
    if type(value) is not str or re.fullmatch(r'US\.[A-Z0-9.]{1,64}', value) is None:
        raise Blocked('UNSUPPORTED_SECURITY')
    return value


def decimal_text(value):
    if value == 0:
        return '0'
    text = format(value, 'f')
    return text.rstrip('0').rstrip('.') if '.' in text else text


def normalize(positions, orders, account=None):
    """Validate only required fields; never log provider messages or raw rows."""
    result = {'positions': [], 'orders': []}
    for kind, rows in (('positions', positions), ('orders', orders)):
        if type(rows) is not list or len(rows) > 10000 or any(type(r) is not dict for r in rows):
            raise Blocked('INVALID_ROWS')
        seen = set()
        for row in rows:
            if ('trd_env' in row and row['trd_env'] != 'SIMULATE') or (
                    'acc_id' in row and (type(row['acc_id']) is not int or row['acc_id'] != account)):
                raise Blocked('ROW_ACCOUNT_SCOPE_MISMATCH')
            code = security(row['code'])
            qty = quantity(row['qty'])
            if kind == 'positions':
                available = quantity(row['can_sell_qty'])
                if available > qty:
                    raise Blocked('INVALID_SELLABLE_QUANTITY')
                if row['position_side'] != 'LONG':
                    raise Blocked('UNSUPPORTED_POSITION_SIDE')
                key = code
                item = dict(code=code, qty=decimal_text(qty),
                            can_sell_qty=decimal_text(available), position_side='LONG')
            else:
                key = row['order_id']
                if type(key) is not str or not key or len(key) > 100 or not key.isascii() or not key.isalnum():
                    raise Blocked('INVALID_ORDER_ID')
                status = row['order_status']
                if status not in TERMINAL | PENDING:
                    raise Blocked('UNKNOWN_ORDER_STATUS')
                filled = quantity(row['dealt_qty'])
                if qty <= 0 or filled > qty or row['trd_side'] not in ('BUY', 'SELL'):
                    raise Blocked('INVALID_ORDER_QUANTITY_OR_SIDE')
                if ((status == 'FILLED_ALL' and filled != qty)
                    or (status in {'CANCELLED_ALL', 'FAILED', 'DISABLED', 'DELETED',
                                   'WAITING_SUBMIT', 'SUBMITTING', 'SUBMITTED'} and filled != 0)
                    or (status in {'FILLED_PART', 'CANCELLED_PART'} and not 0 < filled < qty)):
                    raise Blocked('ORDER_STATUS_QUANTITY_CONTRADICTION')
                item = dict(order_id=key, code=code, qty=decimal_text(qty),
                            dealt_qty=decimal_text(filled), trd_side=row['trd_side'], order_status=status)
            if key in seen:
                raise Blocked('DUPLICATE_' + kind.upper())
            seen.add(key)
            if kind != 'positions' or qty != 0:
                result[kind].append(item)
    result['positions'].sort(key=lambda r: r['code'])
    result['orders'].sort(key=lambda r: r['order_id'])
    return result


def compare(snapshot, expected):
    reasons = []
    if snapshot['positions'] != expected['positions']:
        reasons.append('POSITION_MISMATCH')
    actual = {r['order_id']: r for r in snapshot['orders']}
    wanted = {r['order_id']: r for r in expected['orders']}
    if actual.keys() - wanted.keys():
        reasons.append('UNTRACKED_ORDER')
    if wanted.keys() - actual.keys():
        reasons.append('MISSING_EXPECTED_ORDER')
    if any(actual[key] != wanted[key] for key in actual.keys() & wanted.keys()):
        reasons.append('ORDER_MISMATCH')
    if snapshot['positions']:
        reasons.append('NONFLAT_POSITION')
    if any(quantity(r['can_sell_qty']) < quantity(r['qty']) for r in snapshot['positions']):
        reasons.append('FROZEN_QUANTITY')
    if any(r['order_status'] in PENDING for r in snapshot['orders']):
        reasons.append('PENDING_ORDER')
    if any(r['order_status'] == 'FAILED' for r in snapshot['orders']):
        reasons.append('FAILED_ORDER')
    return reasons


def reconcile(sdk, expected=None, *, expected_fingerprint=None, clock=time.monotonic):
    """Two refresh reads with account revalidation; no retries or mutation methods.

    A matching empty baseline is not a verified local ledger or atomic broker
    snapshot. Unknown state remains HOLD. Raw frames and error strings stay local.
    """
    report = dict(schema=VERSION, scope='READ_ONLY_DRY_RUN', reconciliation='HOLD',
                  reasons=[], observations=[], query_trace=[], orders='DISABLED',
                  paper_execution='HOLD', live_execution='NO-GO', merge='HOLD', deployment='HOLD',
                  expectation_kind='DECLARED_EMPTY_BASELINE' if expected is None else 'EXPLICIT_CALLER_BASELINE',
                  account_fingerprint=None, close_confirmed=False,
                  code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  limitations=['Non-atomic reads, not a restart-safe execution gateway',
                               'Open orders plus recently closed orders only; no complete historical fill ledger',
                               'No market data, risk, fee, profitability or submission authorization verification'])
    context = None
    started = clock()
    def bounded():
        elapsed = clock() - started
        if not 0 <= elapsed <= 30:
            raise Blocked('QUERY_WINDOW_EXCEEDED')
    def query(method, **kwargs):
        bounded()
        report['query_trace'].append(method)
        ret, data = getattr(context, method)(**kwargs)
        bounded()
        if type(ret) is not int or ret != sdk.RET_OK:
            raise Blocked('QUERY_FAILED')
        if len(data) > 10000:
            raise Blocked('ROW_LIMIT_EXCEEDED')
        rows = data.to_dict('records')
        if type(rows) is not list or any(type(r) is not dict for r in rows):
            raise Blocked('INVALID_ROWS')
        return rows
    def eligible(row):
        return (type(row.get('acc_id')) is int and row['acc_id'] > 0
                and row.get('trd_env') == sdk.TrdEnv.SIMULATE
                and row.get('sim_acc_type') == sdk.SimAccType.STOCK_AND_OPTION
                and row.get('acc_status') == sdk.TrdAccStatus.ACTIVE
                and type(row.get('trdmarket_auth')) is list
                and sdk.TrdMarket.US in row['trdmarket_auth'])
    def revalidate(account):
        rows = [r for r in query('get_acc_list') if r.get('acc_id') == account]
        if len(rows) != 1 or not eligible(rows[0]):
            raise Blocked('ACCOUNT_CHANGED')
    try:
        baseline = EMPTY_BASELINE if expected is None else expected
        if type(baseline) is not dict or baseline.get('schema') != VERSION:
            raise Blocked('INVALID_EXPECTATIONS')
        wanted = normalize(baseline['positions'], baseline['orders'])
        report['expectation_hash'] = digest(wanted)
        report['expectation_source_hash'] = digest(baseline)
        baseline_fingerprint = baseline.get('account_fingerprint')
        if baseline_fingerprint is not None:
            if expected_fingerprint is not None and baseline_fingerprint != expected_fingerprint:
                raise Blocked('ACCOUNT_FINGERPRINT_MISMATCH')
            expected_fingerprint = baseline_fingerprint
        if expected_fingerprint is not None and (
                type(expected_fingerprint) is not str or re.fullmatch('[0-9a-f]{64}', expected_fingerprint) is None):
            raise Blocked('INVALID_EXPECTED_ACCOUNT')
        report['query_trace'].append('connect_localhost')
        context = sdk.OpenSecTradeContext(filter_trdmarket=sdk.TrdMarket.US,
                    host='127.0.0.1', port=11111, security_firm=sdk.SecurityFirm.FUTUINC)
        bounded()
        accounts = query('get_acc_list')
        eligible_rows = [r for r in accounts if eligible(r)]
        if len(eligible_rows) != 1:
            raise Blocked('ACCOUNT_NOT_UNIQUE')
        account = eligible_rows[0]['acc_id']
        # Also reject a duplicate ID whose conflicting row was filtered out.
        if len([r for r in accounts if r.get('acc_id') == account]) != 1:
            raise Blocked('DUPLICATE_ACCOUNT_ID')
        fingerprint = hashlib.sha256(('raccoon-paper-account:' + str(account)).encode()).hexdigest()
        if expected_fingerprint is not None and fingerprint != expected_fingerprint:
            raise Blocked('ACCOUNT_FINGERPRINT_MISMATCH')
        report['account_fingerprint'] = fingerprint
        snapshots = []
        for _ in range(2):
            revalidate(account)
            positions = query('position_list_query', trd_env=sdk.TrdEnv.SIMULATE,
                              acc_id=account, refresh_cache=True)
            revalidate(account)
            orders = query('order_list_query', trd_env=sdk.TrdEnv.SIMULATE,
                           acc_id=account, refresh_cache=True)
            revalidate(account)
            snapshot = normalize(positions, orders, account)
            snapshots.append(snapshot)
            report['observations'].append(dict(snapshot_hash=digest(snapshot),
                nonzero_positions=len(snapshot['positions']), order_rows=len(snapshot['orders']),
                pending_orders=sum(r['order_status'] in PENDING for r in snapshot['orders'])))
        if snapshots[0] != snapshots[1]:
            report['reasons'].append('SNAPSHOT_CHANGED')
        report['reasons'].extend(compare(snapshots[-1], wanted))
    except Blocked as exc:
        report['reasons'].append(str(exc))
    except Exception:
        # Malformed frames, SDK exceptions and private error details never leak.
        report['reasons'].append('QUERY_OR_SCHEMA_ERROR')
    finally:
        if context is not None:
            report['query_trace'].append('close')
            try:
                context.close()
                report['close_confirmed'] = True
            except Exception:
                report['reasons'].append('CLOSE_FAILED')
    if not report['reasons']:
        report['reconciliation'] = 'MATCHED_BASELINE'
    report['report_hash'] = digest(report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--read-only', action='store_true', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expectations', type=Path)
    args = parser.parse_args()
    # Reserve before importing/connecting; never overwrite previous evidence.
    with args.output.open('xb') as handle:
        try:
            expected = json.loads(args.expectations.read_text()) if args.expectations else None
            from importlib.metadata import version
            sdk_version = version('moomoo-api')
            if sdk_version != '10.12.7208':
                raise Blocked('UNREVIEWED_SDK_VERSION')
            import moomoo
            report = reconcile(moomoo, expected)
            report.update(source='LOCAL_SDK_READ_ONLY', sdk_version=sdk_version)
        except Exception:
            report = dict(schema=VERSION, source='SDK_NOT_VERIFIED', reconciliation='HOLD',
                          reasons=['INPUT_OR_SDK_STARTUP_FAILED'], orders='DISABLED',
                          paper_execution='HOLD', live_execution='NO-GO', close_confirmed=False)
        report['observed_at_utc'] = datetime.now(timezone.utc).isoformat()
        report.setdefault('code_sha256', hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        report['report_hash'] = digest({k: v for k, v in report.items() if k != 'report_hash'})
        handle.write(encoded(report) + b'\n')
    print(json.dumps({k: report[k] for k in ('reconciliation', 'reasons', 'orders', 'paper_execution')}))
    return 0 if report['reconciliation'] == 'MATCHED_BASELINE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
