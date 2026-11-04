"""Only fake SDKs; unexpected methods fail immediately, including mutations."""
import copy
from contextlib import redirect_stdout
from decimal import localcontext
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import paper_account_reconciliation
from paper_account_reconciliation import reconcile, normalize, VERSION


def account(**changes):
    return dict(dict(acc_id=123456, trd_env='SIMULATE', sim_acc_type='STOCK_AND_OPTION',
                     acc_status='ACTIVE', trdmarket_auth=['US']), **changes)


def position(**changes):
    return dict(dict(code='US.SPY', qty='1', can_sell_qty='1', position_side='LONG'), **changes)


def order(**changes):
    return dict(dict(order_id='SYNTHETICORDER', code='US.SPY', qty='2', dealt_qty='0',
                     trd_side='BUY', order_status='SUBMITTED'), **changes)


def fake_sdk(*, accounts=None, positions=None, orders=None, fail=None,
             changed_accounts=None, second_positions=None, close_fails=False):
    calls = []
    positions = [] if positions is None else positions
    orders = [] if orders is None else orders
    accounts = [account()] if accounts is None else accounts
    class Frame:
        def __init__(self, rows): self.rows = copy.deepcopy(rows)
        def __len__(self): return len(self.rows)
        def to_dict(self, orient):
            if orient != 'records': raise AssertionError('Unexpected frame access')
            return self.rows
    class Context:
        account_queries = 0
        position_queries = 0
        def get_acc_list(self):
            calls.append(('get_acc_list', {}))
            self.account_queries += 1
            if fail == 'accounts': return -1, 'PRIVATE_PROVIDER_DETAIL'
            rows = changed_accounts if changed_accounts is not None and self.account_queries > 1 else accounts
            return 0, Frame(rows)
        def position_list_query(self, **kwargs):
            calls.append(('position_list_query', kwargs))
            self.position_queries += 1
            if fail == 'positions': raise RuntimeError('PRIVATE_PROVIDER_DETAIL')
            rows = second_positions if second_positions is not None and self.position_queries > 1 else positions
            return 0, Frame(rows)
        def order_list_query(self, **kwargs):
            calls.append(('order_list_query', kwargs))
            if fail == 'orders': return -1, 'PRIVATE_PROVIDER_DETAIL'
            return 0, Frame(orders)
        def close(self):
            calls.append(('close', {}))
            if close_fails: raise RuntimeError('PRIVATE_PROVIDER_DETAIL')
        def __getattr__(self, name):
            raise AssertionError('Unexpected SDK method: ' + name)
    def factory(**kwargs):
        calls.append(('connect_localhost', kwargs))
        if fail == 'connect': raise RuntimeError('PRIVATE_PROVIDER_DETAIL')
        return Context()
    sdk = NS(OpenSecTradeContext=factory, RET_OK=0, TrdMarket=NS(US='US'),
             TrdEnv=NS(SIMULATE='SIMULATE'), SecurityFirm=NS(FUTUINC='FUTUINC'),
             SimAccType=NS(STOCK_AND_OPTION='STOCK_AND_OPTION'), TrdAccStatus=NS(ACTIVE='ACTIVE'))
    return sdk, calls


class ReconciliationTests(unittest.TestCase):
    def test_cli_startup_failure_preserves_sanitized_hold_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.json'
            with patch.object(sys, 'argv', ['reconcile', '--read-only', '--output', str(output)]), \
                    patch('importlib.metadata.version', return_value='unsupported'), redirect_stdout(io.StringIO()):
                self.assertEqual(paper_account_reconciliation.main(), 1)
            result = json.loads(output.read_text())
            self.assertEqual(result['orders'], 'DISABLED')
            self.assertEqual(result['reconciliation'], 'HOLD')
            self.assertEqual(result['source'], 'SDK_NOT_VERIFIED')
            self.assertIn('observed_at_utc', result)

    def test_cli_refuses_overwrite_before_import_or_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.json'
            output.write_text('original')
            with patch.object(sys, 'argv', ['reconcile', '--read-only', '--output', str(output)]), \
                    patch('importlib.metadata.version') as version:
                with self.assertRaises(FileExistsError):
                    paper_account_reconciliation.main()
                version.assert_not_called()
            self.assertEqual(output.read_text(), 'original')

    def run_fake(self, **kwargs):
        sdk, calls = fake_sdk(**kwargs)
        return reconcile(sdk, clock=lambda: 0), calls

    def test_flat_baseline_matches_with_exact_read_only_surface(self):
        result, calls = self.run_fake()
        self.assertEqual(result['reconciliation'], 'MATCHED_BASELINE')
        self.assertEqual(result['orders'], 'DISABLED')
        self.assertEqual(result['paper_execution'], 'HOLD')
        self.assertTrue(result['close_confirmed'])
        self.assertEqual(calls[0], ('connect_localhost', dict(filter_trdmarket='US',
                            host='127.0.0.1', port=11111, security_firm='FUTUINC')))
        self.assertEqual([name for name, _ in calls], ['connect_localhost', 'get_acc_list'] +
                         ['get_acc_list', 'position_list_query', 'get_acc_list',
                          'order_list_query', 'get_acc_list'] * 2 + ['close'])
        for name, kwargs in calls:
            if name in ('position_list_query', 'order_list_query'):
                self.assertEqual(kwargs, dict(trd_env='SIMULATE', acc_id=123456, refresh_cache=True))

    def test_mixed_live_and_paper_account_queries_only_paper(self):
        result, calls = self.run_fake(accounts=[account(acc_id=888, trd_env='REAL'), account()])
        self.assertEqual(result['reconciliation'], 'MATCHED_BASELINE')
        self.assertTrue(all(kw['acc_id'] == 123456 for name, kw in calls if 'acc_id' in kw))

    def test_account_scope_rejected_before_state_queries(self):
        changes = [{'trd_env': 'REAL'}, {'acc_status': 'DISABLED'}, {'sim_acc_type': 'STOCK'},
                   {'trdmarket_auth': ['HK']}, {'trdmarket_auth': 'US'}, {'acc_id': True}]
        for change in changes:
            with self.subTest(change=change):
                result, calls = self.run_fake(accounts=[account(**change)])
                self.assertEqual(result['reconciliation'], 'HOLD')
                self.assertFalse(any(name.endswith('_list_query') for name, _ in calls))
                self.assertEqual(calls[-1][0], 'close')

    def test_ambiguous_and_conflicting_duplicate_accounts_block(self):
        for rows in ([account(), account(acc_id=9)], [account(), account(trd_env='REAL')]):
            result, calls = self.run_fake(accounts=rows)
            self.assertEqual(result['reconciliation'], 'HOLD')
            self.assertFalse(any(name.endswith('_list_query') for name, _ in calls))

    def test_reclassification_stops_before_state_read(self):
        result, calls = self.run_fake(changed_accounts=[account(trd_env='REAL')])
        self.assertEqual(result['reasons'], ['ACCOUNT_CHANGED'])
        self.assertFalse(any(name.endswith('_list_query') for name, _ in calls))

    def test_explicit_account_mismatch_blocks(self):
        sdk, calls = fake_sdk()
        result = reconcile(sdk, expected_fingerprint='0' * 64, clock=lambda: 0)
        self.assertEqual(result['reasons'], ['ACCOUNT_FINGERPRINT_MISMATCH'])
        self.assertFalse(any(name.endswith('_list_query') for name, _ in calls))
        sdk, calls = fake_sdk()
        baseline = dict(schema=VERSION, positions=[], orders=[], account_fingerprint='0' * 64)
        self.assertEqual(reconcile(sdk, baseline, clock=lambda: 0)['reasons'], ['ACCOUNT_FINGERPRINT_MISMATCH'])
        self.assertFalse(any(name.endswith('_list_query') for name, _ in calls))

    def test_query_and_close_failures_are_redacted_without_retry(self):
        for stage in ('connect', 'accounts', 'positions', 'orders'):
            result, calls = self.run_fake(fail=stage)
            self.assertEqual(result['reconciliation'], 'HOLD')
            self.assertNotIn('PRIVATE_PROVIDER_DETAIL', json.dumps(result))
            names = [name for name, _ in calls]
            if stage != 'connect': self.assertEqual(names[-1], 'close')
            if stage == 'orders': self.assertEqual(names.count('order_list_query'), 1)
        result, _ = self.run_fake(close_fails=True)
        self.assertIn('CLOSE_FAILED', result['reasons'])
        self.assertEqual(result['reconciliation'], 'HOLD')

    def test_state_drift_is_not_a_matched_baseline(self):
        result, _ = self.run_fake(second_positions=[position()])
        self.assertIn('SNAPSHOT_CHANGED', result['reasons'])
        self.assertIn('POSITION_MISMATCH', result['reasons'])

    def test_pending_and_partial_orders_stay_hold(self):
        for row in (order(), order(order_status='FILLED_PART', dealt_qty='1'),
                    order(order_status='CANCELLED_PART', dealt_qty='1')):
            result, _ = self.run_fake(positions=[position()], orders=[row])
            self.assertEqual(result['reconciliation'], 'HOLD')
            self.assertIn('UNTRACKED_ORDER', result['reasons'])
            self.assertIn('NONFLAT_POSITION', result['reasons'])
        result, _ = self.run_fake(orders=[order(order_status='CANCELLING_ALL')])
        self.assertEqual(result['reasons'], ['UNKNOWN_ORDER_STATUS'])

    def test_expected_orders_must_exist_with_exact_status_and_fill(self):
        row = order(order_status='FILLED_ALL', dealt_qty='2')
        sdk, _ = fake_sdk(orders=[row])
        expected = dict(schema=VERSION, positions=[], orders=[row])
        self.assertEqual(reconcile(sdk, expected, clock=lambda: 0)['reconciliation'], 'MATCHED_BASELINE')
        sdk, _ = fake_sdk()
        self.assertIn('MISSING_EXPECTED_ORDER', reconcile(sdk, expected, clock=lambda: 0)['reasons'])
        sdk, _ = fake_sdk(orders=[order()])
        self.assertIn('ORDER_MISMATCH', reconcile(sdk, expected, clock=lambda: 0)['reasons'])

    def test_invalid_duplicate_and_wrong_scope_rows_fail_closed(self):
        position_cases = [[position(qty='NaN')], [position(qty=True)],
                          [position(can_sell_qty='2')], [position(position_side='SHORT')],
                          [position(), position()], [position(acc_id=999)],
                          [position(trd_env='REAL')], [dict(code='US.SPY')], [{}] * 10001]
        order_cases = [[order(), order()], [order(dealt_qty='3')],
                       [order(order_status='FILLED_ALL')], [order(order_status='NEW_UNKNOWN')]]
        for rows in position_cases:
            result, _ = self.run_fake(positions=rows)
            self.assertEqual(result['reconciliation'], 'HOLD')
        for rows in order_cases:
            result, _ = self.run_fake(orders=rows)
            self.assertEqual(result['reconciliation'], 'HOLD')

    def test_clock_budget_and_bad_expectations_block(self):
        sdk, calls = fake_sdk()
        values = iter([0, 31])
        result = reconcile(sdk, clock=lambda: next(values))
        self.assertEqual(result['reasons'], ['QUERY_WINDOW_EXCEEDED'])
        self.assertEqual(calls[-1][0], 'close')
        sdk, calls = fake_sdk()
        result = reconcile(sdk, expected={'schema': 'unknown'}, clock=lambda: 0)
        self.assertEqual(result['reasons'], ['INVALID_EXPECTATIONS'])
        self.assertEqual(calls, [])

    def test_report_redacts_raw_ids_rows_and_errors(self):
        result, _ = self.run_fake(orders=[order(order_id='SECRETORDER')])
        raw = json.dumps(result)
        for value in ('123456', 'SECRETORDER', 'US.SPY', 'PRIVATE_PROVIDER_DETAIL'):
            self.assertNotIn(value, raw)

    def test_quantity_normalization_does_not_depend_on_decimal_context(self):
        data = [position(qty='12345678.12345678', can_sell_qty='12345678.12345678')]
        expected = normalize(data, [])
        with localcontext() as context:
            context.prec = 4
            self.assertEqual(normalize(data, []), expected)
