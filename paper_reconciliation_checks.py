"""Fake-only read-only paper reconciliation CI evidence. Never imports a broker SDK."""
import argparse
from pathlib import Path
import tempfile
from offline_checks import OfflineGuard
from paper_account_reconciliation import VERSION, digest, encoded, reconcile


def evidence():
    from test_paper_account_reconciliation import fake_sdk, account, position, order
    terminal = order(qty='1', dealt_qty='1', order_status='FILLED_ALL')
    expected_terminal = dict(schema=VERSION, positions=[], orders=[terminal])
    cases = {
        'flat': ({}, None, 'MATCHED_BASELINE', None),
        'mixed-live-paper': ({'accounts': [account(acc_id=777, trd_env='REAL'), account()]},
                             None, 'MATCHED_BASELINE', None),
        'expected-terminal-order': ({'orders': [terminal]}, expected_terminal, 'MATCHED_BASELINE', None),
        'nonflat': ({'positions': [position()]}, None, 'HOLD', 'NONFLAT_POSITION'),
        'pending': ({'orders': [order()]}, None, 'HOLD', 'PENDING_ORDER'),
        'partial-fill': ({'orders': [order(order_status='FILLED_PART', dealt_qty='1')],
                          'positions': [position()]}, None, 'HOLD', 'PENDING_ORDER'),
        'cancelled-partial': ({'orders': [order(order_status='CANCELLED_PART', dealt_qty='1')],
                              'positions': [position()]}, None, 'HOLD', 'NONFLAT_POSITION'),
        'unknown-status': ({'orders': [order(order_status='CANCELLING_ALL')]}, None, 'HOLD', 'UNKNOWN_ORDER_STATUS'),
        'query-failure': ({'fail': 'orders'}, None, 'HOLD', 'QUERY_FAILED'),
        'sdk-exception': ({'fail': 'positions'}, None, 'HOLD', 'QUERY_OR_SCHEMA_ERROR'),
        'duplicate-account': ({'accounts': [account(), account(trd_env='REAL')]}, None, 'HOLD', 'DUPLICATE_ACCOUNT_ID'),
        'account-changed': ({'changed_accounts': [account(trd_env='REAL')]}, None, 'HOLD', 'ACCOUNT_CHANGED'),
        'state-changed': ({'second_positions': [position()]}, None, 'HOLD', 'SNAPSHOT_CHANGED'),
        'malformed-quantity': ({'positions': [position(qty='NaN')]}, None, 'HOLD', 'INVALID_QUANTITY'),
        'close-failure': ({'close_fails': True}, None, 'HOLD', 'CLOSE_FAILED'),
        'missing-expected-order': ({}, expected_terminal, 'HOLD', 'MISSING_EXPECTED_ORDER'),
    }
    reports = {}
    for name, (kwargs, expected, status, reason) in cases.items():
        sdk, calls = fake_sdk(**kwargs)
        result = reconcile(sdk, expected, clock=lambda: 0)
        if result['reconciliation'] != status or (reason is not None and reason not in result['reasons']):
            raise ValueError('Unexpected reconciliation fixture outcome: ' + name)
        if result['orders'] != 'DISABLED' or result['paper_execution'] != 'HOLD':
            raise ValueError('Operational gate changed: ' + name)
        for method, args in calls:
            if method not in {'connect_localhost', 'get_acc_list', 'position_list_query', 'order_list_query', 'close'}:
                raise ValueError('Unexpected SDK call: ' + name)
            if method in {'position_list_query', 'order_list_query'} and args != dict(
                    trd_env='SIMULATE', acc_id=123456, refresh_cache=True):
                raise ValueError('Account isolation changed: ' + name)
        reports[name] = result
    report = dict(schema=VERSION, scope='SYNTHETIC_ONLY', broker_verified=False,
                  scenarios=reports, orders='DISABLED', paper_execution='HOLD', live_execution='NO-GO',
                  limitations='Fake SDK evidence only; no real account, ledger or execution certification')
    report['evidence_hash'] = digest(report)
    return report


def validate_evidence(report):
    if type(report) is not dict or report.get('evidence_hash') != digest(
            {k: v for k, v in report.items() if k != 'evidence_hash'}):
        raise ValueError('Paper reconciliation evidence hash mismatch')
    if encoded(report) != encoded(evidence()):
        raise ValueError('Paper reconciliation evidence differs from fixed current-code fixtures')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='paper-reconciliation-') as temp:
        with OfflineGuard(temp):
            report = evidence()
            validate_evidence(report)
    with args.output.open('xb') as handle:
        handle.write(encoded(report) + b'\n')
    print('16 fake-only reconciliation scenarios PASS; paper HOLD; orders DISABLED')


if __name__ == '__main__':
    main()
