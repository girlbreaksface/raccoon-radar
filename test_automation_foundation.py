"""Control-plane regressions; fictional results never unlock operational gates."""
import subprocess
import sys
import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import automation_foundation
from automation_foundation import COMMANDS, infrastructure_retry, readiness


class FoundationTests(unittest.TestCase):
    def test_successful_child_cannot_hide_a_forged_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'evidence'
            def run(command, **kwargs):
                if '--output' in command:
                    Path(command[-1]).write_text('{"paper_execution":"GO"}')
                return subprocess.CompletedProcess(command, 0)
            with patch.object(sys, 'argv', ['foundation', '--output', str(output)]), \
                    patch.object(automation_foundation.subprocess, 'run', side_effect=run):
                self.assertEqual(automation_foundation.main(), 1)
            report = json.loads((output / 'readiness.json').read_text())
            self.assertEqual(report['repository_verification']['historical-replay']['status'], 'ERROR')
            self.assertEqual(report['repository_verification']['paper-reconciliation']['status'], 'ERROR')
            self.assertEqual(report['repository_verification']['execution-recovery']['status'], 'ERROR')
            self.assertEqual(report['paper_execution'], 'HOLD')

    def test_timeout_preserves_diagnostics_and_runs_remaining_suites(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'evidence'
            outcomes = [subprocess.TimeoutExpired('fixture', 600)] + [
                subprocess.CompletedProcess([], 0) for _ in range(len(COMMANDS) - 1)]
            with patch.object(sys, 'argv', ['foundation', '--output', str(output)]), \
                    patch.object(automation_foundation.subprocess, 'run', side_effect=outcomes) as run:
                self.assertEqual(automation_foundation.main(), 1)
                self.assertEqual(run.call_count, len(COMMANDS))
            report = json.loads((output / 'readiness.json').read_text())
            self.assertEqual(report['repository_verification']['root']['status'], 'ERROR')
            self.assertEqual(report['repository_verification']['historical-replay']['status'], 'ERROR')
            self.assertEqual(report['synthetic_regression'], 'FAIL')
            for result in report['repository_verification'].values():
                self.assertTrue((output / result['log']).exists())
                self.assertEqual(len(result['log_sha256']), 64)
            with patch.object(sys, 'argv', ['foundation', '--output', str(output)]), \
                    patch.object(automation_foundation.subprocess, 'run') as run:
                with self.assertRaises(FileExistsError):
                    automation_foundation.main()
                run.assert_not_called()

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
        return [sys.executable, '-m', 'pip', 'download', '--retries', '0', '--timeout', '30', '--no-deps',
                '--dest', 'work/ci-dependencies', 'tzdata==2026.5']
