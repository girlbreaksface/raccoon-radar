"""Offline evidence orchestration; never a broker or release authorization."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
COMMANDS = {
    'root': ['offline_checks.py'],
    'feed': ['research/feed_contract/run_checks.py'],
    'reconciliation': ['research/reconciliation/run_checks.py'],
    'deterministic-evidence': ['research/reconciliation/verify_evidence.py'],
    'historical-replay': ['historical_replay_checks.py'],
    'paper-reconciliation': ['paper_reconciliation_checks.py'],
    'execution-recovery': ['execution_recovery_checks.py'],
    'production-indicators': ['production_indicator_checks.py'],
}
GATES = (
    ('provider-provenance', 'Authenticated provider timestamps, finality and availability lineage absent'),
    ('data-rights', 'Current entitlement and retention approval unverified'),
    ('session-calendar', 'Authoritative exchange calendar, clock and session mapping unverified'),
    ('historical-options', 'Licensed historical bid/ask and point-in-time universe unverified'),
    ('execution-reconciliation', 'Integrated broker lifecycle, reconciliation and risk recovery unverified'),
    ('empirical-validation', 'Frozen holdout/walk-forward executable-return evidence absent'),
)


def readiness(results):
    """A passing synthetic suite cannot release any operational gate."""
    complete = set(results) == set(COMMANDS)
    passed = complete and all(r['status'] == 'PASS' for r in results.values())
    return {
        'schema_version': 1,
        'synthetic_regression': 'PASS' if passed else 'FAIL',
        'recording': 'HOLD', 'paper_execution': 'HOLD', 'live_execution': 'NO-GO',
        'orders': 'DISABLED', 'merge': 'HOLD', 'deployment': 'HOLD',
        'gates': [{'id': key, 'status': 'HOLD', 'reason': reason} for key, reason in GATES],
        'reported_research': {'assertions': '224/224', 'stress_cycles': '1500/1500',
                              'verification': 'USER_REPORTED_NOT_REPO_CI'},
        'repository_verification': results,
        'notification_policy': 'APPROVAL_REQUIRED_ONLY',
        'approval_requested': False,
        'limitations': 'Synthetic fixtures only; no provider, GUI, broker, profitability or release certification',
    }


def infrastructure_retry(command, run=subprocess.run, sleep=time.sleep):
    """Retry only a fixed tzdata download, once, on explicit transport failures."""
    allowed = [sys.executable, '-m', 'pip', 'download', '--retries', '0', '--timeout', '30', '--no-deps',
               '--dest', 'work/ci-dependencies', 'tzdata==2026.5']
    if command != allowed:
        raise ValueError('Only the fixed dependency download may be retried')
    transient = ('Temporary failure in name resolution', 'Read timed out',
                 'Connection reset by peer', 'Connection aborted')
    for attempt in range(2):
        result = run(command, cwd=ROOT, capture_output=True, text=True, timeout=180)
        print(result.stdout, end='')
        print(result.stderr, end='', file=sys.stderr)
        if result.returncode == 0 or not any(s in result.stderr for s in transient) or attempt == 1:
            return result.returncode
        sleep(3)
    raise AssertionError('unreachable')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--download-ci-dependency', action='store_true')
    args = parser.parse_args()
    if args.download_ci_dependency:
        return infrastructure_retry([sys.executable, '-m', 'pip', 'download', '--retries', '0', '--timeout', '30', '--no-deps',
                                     '--dest', 'work/ci-dependencies', 'tzdata==2026.5'])
    if args.output is None:
        parser.error('--output is required for regression runs')
    # Exclusive directory: earlier evidence must never be overwritten.
    args.output.mkdir(parents=True, exist_ok=False)
    results = {}
    for name, script in COMMANDS.items():
        log = args.output / (name + '.txt')
        artifact = args.output / (name + '.json') if name in ('historical-replay', 'paper-reconciliation', 'execution-recovery', 'production-indicators') else None
        command = [sys.executable, '-B', *script]
        if artifact is not None:
            command.extend(['--output', str(artifact.resolve())])
        with log.open('x', encoding='utf-8') as stream:
            try:
                result = subprocess.run(command, cwd=ROOT,
                                        stdout=stream, stderr=subprocess.STDOUT, timeout=600)
                results[name] = {'status': 'PASS' if result.returncode == 0 else 'FAIL',
                                 'exit_code': result.returncode}
                if result.returncode == 0 and artifact is not None:
                    if name == 'historical-replay':
                        from historical_replay_checks import validate_evidence
                    elif name == 'execution-recovery':
                        from execution_recovery_checks import validate_evidence
                    elif name == 'production-indicators':
                        from production_indicator_checks import validate_evidence
                    else:
                        from paper_reconciliation_checks import validate_evidence
                    raw = artifact.read_bytes()
                    validate_evidence(json.loads(raw))
                    results[name].update(artifact=artifact.name,
                                         artifact_sha256=hashlib.sha256(raw).hexdigest())
            except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                stream.write('\nCheck failure: ' + str(exc))
                results[name] = {'status': 'ERROR', 'reason': type(exc).__name__}
        results[name]['log'] = log.name
        results[name]['log_sha256'] = hashlib.sha256(log.read_bytes()).hexdigest()
    report = readiness(results)
    report['environment'] = {'python': platform.python_version(), 'os': platform.system(),
                             'ci': os.environ.get('GITHUB_ACTIONS') == 'true',
                             'commit': os.environ.get('GITHUB_SHA'),
                             'head_commit': os.environ.get('PR_HEAD_SHA'),
                             'run_id': os.environ.get('GITHUB_RUN_ID')}
    report['source_sha256'] = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(ROOT.rglob('*.py')) if '.git' not in p.parts and 'work' not in p.relative_to(ROOT).parts
    }
    (args.output / 'readiness.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('synthetic_regression', 'paper_execution', 'live_execution')}))
    return 0 if report['synthetic_regression'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
