"""Control-plane regressions; fictional results never unlock operational gates."""
import subprocess
import sys
import unittest
from automation_foundation import COMMANDS, infrastructure_retry, readiness


class FoundationTests(unittest.TestCase):
    def test_passing_synthetic_checks_cannot_release_operations(self):
        report = readiness({name: {'status': 'PASS'} for name in COMMANDS})
        self.assertEqual(report['synthetic_regression'], 'PASS')
        self.assertEqual(report['paper_execution'], 'HOLD')
        self.assertEqual(report['live_execution'], 'NO-GO')
        self.assertEqual(report['orders'], 'DISABLED')
        self.assertEqual(len(report['gates']), 6)
        self.assertTrue(all(g['status'] == 'HOLD' for g in report['gates']))
        self.assertFalse(report['approval_requested'])

    def test_missing_failed_and_unknown_checks_fail_closed(self):
        for status in ('FAIL', 'ERROR', 'SKIP', None):
            results = {name: {'status': 'PASS'} for name in COMMANDS}
            results['root']['status'] = status
            self.assertEqual(readiness(results)['synthetic_regression'], 'FAIL')
        self.assertEqual(readiness({})['synthetic_regression'], 'FAIL')

    def test_transient_download_retried_once(self):
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 1, '', 'Read timed out')
        self.assertEqual(infrastructure_retry(self.command(), run, lambda _: None), 1)
        self.assertEqual(len(calls), 2)

    def test_no_retry_for_dependency_or_safety_failure(self):
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 1, '', 'No matching distribution found')
        self.assertEqual(infrastructure_retry(self.command(), run), 1)
        self.assertEqual(len(calls), 1)
        with self.assertRaises(ValueError):
            infrastructure_retry([sys.executable, 'offline_checks.py'], run)
        self.assertEqual(len(calls), 1)

    @staticmethod
    def command():
        return [sys.executable, '-m', 'pip', 'download', '--no-deps',
                '--dest', 'work/ci-dependencies', 'tzdata==2026.5']
