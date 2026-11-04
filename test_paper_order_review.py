"""Fictional pilot risk policy regressions; never contacts a broker."""
from dataclasses import replace
import unittest
from paper_order_review import Proposal, review


class RiskReviewTests(unittest.TestCase):
    def fixture(self):
        return Proposal('a'*64, 'SIMULATE', 'SPY', 'US.SPY261106C100000', 'CALL',
            1, '.29', '1', 5, True, True, True, 0, '0', '0', False)

    def test_all_in_boundary_still_requires_review(self):
        r = review(self.fixture())
        self.assertEqual(r['status'], 'READY_FOR_REVIEW')
        self.assertEqual(r['all_in_entry'], '30.00')
        self.assertEqual(r['orders'], 'DISABLED')
        self.assertEqual(r['external_paper_orders'], 'REVIEW_REQUIRED')
        self.assertEqual(r, review(self.fixture()))

    def test_each_control_blocks(self):
        for changes, reason in (
            ({'environment':'REAL'}, 'PAPER_ENV_REQUIRED'),
            ({'account_fingerprint':''}, 'ACCOUNT_IDENTITY_REQUIRED'),
            ({'underlying':'AAPL'}, 'UNDERLYING_NOT_ALLOWED'),
            ({'contract':'US.QQQFICTIONAL'}, 'CONTRACT_NOT_VERIFIED'),
            ({'quantity':2}, 'ONE_CONTRACT_ONLY'),
            ({'right':'SHORT'}, 'LONG_OPTION_REQUIRED'),
            ({'limit_price':'.30'}, 'ALL_IN_ENTRY_LIMIT'),
            ({'quote_age_seconds':6}, 'STALE_QUOTE'),
            ({'session_verified':False}, 'SESSION_UNVERIFIED'),
            ({'account_verified':False}, 'ACCOUNT_UNVERIFIED'),
            ({'reconciled':False}, 'RECONCILIATION_REQUIRED'),
            ({'entries_today':3}, 'DAILY_ENTRY_LIMIT'),
            ({'open_premium':'30.01'}, 'PORTFOLIO_PREMIUM_LIMIT'),
            ({'realized_net':'-30'}, 'DAILY_LOSS_STOP'),
            ({'kill_switch':True}, 'KILL_SWITCH')):
            with self.subTest(changes=changes):
                r = review(replace(self.fixture(), **changes))
                self.assertIn(reason, r['reasons'])
                self.assertEqual(r['status'], 'BLOCKED')

    def test_malformed_state_aborts(self):
        for changes in ({'limit_price':'NaN'}, {'estimated_round_trip_fees':'-1'},
                        {'quantity':True}, {'reconciled':1}, {'open_premium':'Infinity'}):
            with self.assertRaises(ValueError): review(replace(self.fixture(), **changes))
