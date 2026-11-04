"""Offline rehearsal evidence and isolation regression checks."""
import socket
import unittest
from unittest.mock import patch

from paper_only_validation import validate


class PaperValidationTests(unittest.TestCase):
    def test_rehearsal_controls_and_outcomes(self):
        with patch.object(socket, 'create_connection', side_effect=AssertionError('network attempted')) as connect:
            report = validate()
        connect.assert_not_called()
        self.assertEqual(report['integration'], 'HOLD')
        self.assertEqual(report['live_trading'], 'NO-GO')
        self.assertEqual(report['external_paper_orders'], 'REVIEW_REQUIRED')
        self.assertEqual(len(report['scenarios']), 8)
        for case in report['scenarios'].values():
            self.assertEqual(case['result']['orders'], 'DISABLED')
        self.assertTrue(report['scenarios']['open_position']['result']['open_positions'])
        self.assertIn('synthetic_options_adapter.py', report['source_sha256'])

    def test_guard_blocks_actual_network_before_connect(self):
        import tempfile
        from offline_checks import OfflineGuard
        with tempfile.TemporaryDirectory() as root:
            with OfflineGuard(root):
                with self.assertRaises(PermissionError):
                    socket.create_connection(('127.0.0.1', 11111), timeout=.1)
