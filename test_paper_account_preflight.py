"""Fakes prove account filtering and read-only call surface."""
import unittest
from types import SimpleNamespace as NS
from paper_account_preflight import inspect_accounts


class PreflightTests(unittest.TestCase):
    def sdk(self, rows, code=0, fail=False):
        calls = []
        class Context:
            def get_acc_list(self):
                calls.append('get_acc_list')
                if fail:
                    raise RuntimeError('synthetic failure')
                return code, NS(to_dict=lambda orient: rows)
            def position_list_query(self, **kwargs):
                calls.append(('positions', kwargs))
                return 0, []
            def order_list_query(self, **kwargs):
                calls.append(('orders', kwargs))
                return 0, []
            def close(self): calls.append('close')
        def factory(**kwargs):
            calls.append(kwargs)
            return Context()
        sdk = NS(OpenSecTradeContext=factory, RET_OK=0,
            TrdMarket=NS(US='US'), SecurityFirm=NS(FUTUINC='FUTUINC'),
            TrdEnv=NS(SIMULATE='SIMULATE'),
            SimAccType=NS(STOCK_AND_OPTION='STOCK_AND_OPTION'),
            TrdAccStatus=NS(ACTIVE='ACTIVE'))
        return sdk, calls

    def row(self, **changes):
        return dict(acc_id=123456, trd_env='SIMULATE',
                    sim_acc_type='STOCK_AND_OPTION', acc_status='ACTIVE',
                    trdmarket_auth=['US'], **changes)

    def test_paper_selected_and_redacted(self):
        row = self.row()
        live = dict(row, trd_env='REAL')
        sdk, calls = self.sdk([live, row])
        result = inspect_accounts(sdk)
        self.assertEqual(result['status'], 'PAPER_ACCOUNT_FOUND')
        self.assertNotIn('123456', str(result))
        self.assertEqual(calls, [dict(filter_trdmarket='US', host='127.0.0.1',
            port=11111, security_firm='FUTUINC'), 'get_acc_list',
            ('positions', dict(trd_env='SIMULATE', acc_id=123456, refresh_cache=True)),
            ('orders', dict(trd_env='SIMULATE', acc_id=123456, refresh_cache=True)), 'close'])
        self.assertEqual(result['paper_state']['position_list_query']['row_count'], 0)

    def test_missing_disabled_wrong_market_and_live_rejected(self):
        for change in ({'trd_env':'REAL'}, {'acc_status':'DISABLED'},
                       {'trdmarket_auth':['HK']}, {'sim_acc_type':'STOCK'},
                       {'acc_id':True}, {'acc_id':0}):
            sdk, _ = self.sdk([dict(self.row(), **change)])
            self.assertEqual(inspect_accounts(sdk)['status'], 'NO_ELIGIBLE_PAPER_ACCOUNT')

    def test_ambiguity_and_provider_failure(self):
        sdk, _ = self.sdk([self.row(), dict(self.row(), acc_id=789)])
        self.assertEqual(inspect_accounts(sdk)['status'], 'AMBIGUOUS_PAPER_ACCOUNTS')
        sdk, calls = self.sdk([], code=-1)
        self.assertEqual(inspect_accounts(sdk)['status'], 'ACCOUNT_QUERY_FAILED')
        self.assertEqual(calls[-1], 'close')

    def test_exception_still_closes(self):
        sdk, calls = self.sdk([], fail=True)
        with self.assertRaises(RuntimeError): inspect_accounts(sdk)
        self.assertEqual(calls[-1], 'close')
