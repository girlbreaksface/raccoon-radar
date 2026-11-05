"""Restart recovery invariants and durable journal fault injection."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from execution_recovery import Journal, read_journal, replay, recover
from execution_recovery_checks import ACCOUNT, events, serialize, scenarios, evidence, validate_evidence, order, broker
from paper_account_reconciliation import digest


class RecoveryTests(unittest.TestCase):
    def test_fixed_scenarios(self):
        reports = scenarios()
        self.assertGreaterEqual(len(reports), 30)
        for report in reports.values():
            self.assertEqual(report['paper_execution'], 'HOLD')
            self.assertEqual(report['orders'], 'DISABLED')

    def test_repeated_replay_is_identical_and_does_not_mutate_input(self):
        raw, checkpoint = serialize(events())
        items = read_journal(raw, checkpoint, ACCOUNT)
        original = copy.deepcopy(items)
        self.assertEqual(replay(items), replay(items))
        self.assertEqual(items, original)

    def test_duplicate_cumulative_fill_does_not_double_count(self):
        items = events() + [dict(id='fill1', kind='observation', order=order('FILLED_PART', '1')),
                            dict(id='fill2', kind='observation', order=order('FILLED_PART', '1'))]
        self.assertEqual(replay(items)['net_quantities'], {'US.SPY': '1'})

    def test_no_fills_inferred_from_cancel_or_position(self):
        state = replay(events() + [dict(id='cancel', kind='cancel_intent', order_id='ORDER1')])
        self.assertEqual(state['net_quantities'], {})
        self.assertIn('CANCEL_UNCONFIRMED', state['reasons'])

    def test_exclusive_journal_and_fsync_failure_poison_writer(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'journal'
            journal = Journal(path, ACCOUNT)
            try:
                with self.assertRaises(FileExistsError): Journal(path, ACCOUNT)
                before = dict(journal.checkpoint)
                with patch('execution_recovery.os.fsync', side_effect=OSError('fictional disk failure')):
                    with self.assertRaises(OSError): journal.append(events()[0])
                self.assertEqual(journal.checkpoint, before)
                with self.assertRaises(ValueError): journal.append(events()[0])
            finally:
                journal.close()
            with self.assertRaises(ValueError): read_journal(path.read_bytes(), before, ACCOUNT)

    def test_checkpoint_scope_and_order_integrity(self):
        raw, checkpoint = serialize(events())
        for data, receipt, account in [(raw, checkpoint, 'f'*64),
                (raw, dict(checkpoint, head='f'*64), ACCOUNT),
                (b'\n'.join(reversed(raw.splitlines())) + b'\n', checkpoint, ACCOUNT)]:
            with self.assertRaises(ValueError): read_journal(data, receipt, account)

    def test_repaired_hash_cannot_hide_removed_scenario_or_gate(self):
        report = evidence()
        for change in ('scenario', 'gate'):
            forged = copy.deepcopy(report)
            if change == 'scenario': forged['scenarios'].pop('partial-fill')
            else: forged['paper_execution'] = 'GO'
            forged['evidence_hash'] = digest({k:v for k,v in forged.items() if k != 'evidence_hash'})
            with self.assertRaises(ValueError): validate_evidence(forged)

    def test_broker_evidence_tamper_and_wrong_account_hold(self):
        items = events() + [dict(id='cancelled', kind='observation', order=order('CANCELLED_ALL'))]
        raw, checkpoint = serialize(items)
        for change in ('hash', 'snapshot', 'account'):
            kwargs = broker([order('CANCELLED_ALL')])
            if change == 'hash': kwargs['reconciliation']['report_hash'] = '0'*64
            elif change == 'snapshot': kwargs['snapshots'][1]['orders'] = []
            else:
                r = kwargs['reconciliation']
                r['account_fingerprint'] = 'f'*64
                r['report_hash'] = digest({k:v for k,v in r.items() if k != 'report_hash'})
            self.assertEqual(recover(raw, checkpoint, ACCOUNT, **kwargs)['recovery'], 'HOLD')

    def test_invalid_semantic_events_rejected_even_with_valid_chain(self):
        mutations = [dict(id='unknown', kind='execute'),
            dict(id='badack', kind='ack', intent='MISSING', order_id='ORDER2'),
            dict(id='badfill', kind='observation', order=order('FILLED_ALL', '3')),
            dict(id='wrongqty', kind='observation', order=order(qty='3')),
            dict(id='badconnection', kind='connection', connected=1)]
        for event in mutations:
            raw, checkpoint = serialize(events() + [event])
            with self.assertRaises(ValueError): replay(read_journal(raw, checkpoint, ACCOUNT))
