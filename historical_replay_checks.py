"""Deterministic offline replay rehearsal and informational paper-readiness audit.

No provider, account, order or execution interface. Fixture evidence never
releases an operational gate. A dataset's VERIFIED_QUOTES label is untrusted.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile

from historical_options_replay import digest, encoded, replay, ENGINE_VERSION
from offline_checks import OfflineGuard

PAPER_GATES = (
    ('repository-integration', 'Offline rehearsal only; Phase 25 equivalence and application integration unverified'),
    ('broker-reconciliation', 'No integrated broker lifecycle, restart or recovery evidence'),
    ('production-vwap-warmup', 'Research signal conventions do not verify production VWAP or warmup'),
    ('real-fees-slippage', 'Illustrative costs, not verified broker costs or fills'),
    ('historical-validation', 'No independently verified licensed dataset or empirical holdout results'),
    ('paper-authorization', 'Development permission does not authorize order submission'),
)


def check_result(result):
    """Recompute rather than trust a supplied summary or self-consistent hash."""
    expected = replay(result['dataset'], result['config'])
    if encoded(expected) != encoded(result):
        raise ValueError('Replay result differs from current-code recomputation')
    return result


def assess(results):
    if not results:
        raise ValueError('Missing replay evidence')
    counts = {'CLOSED': 0, 'UNRESOLVED': 0, 'REJECTED': 0}
    classifications = set()
    for result in results:
        check_result(result)
        classifications.add(result['quality'])
        if not result['trades']:
            raise ValueError('Empty trade audit cannot establish rehearsal coverage')
        for row in result['trades']:
            counts[row['status']] += 1
    return {
        'evidence_integrity': 'PASS',
        'dataset_classifications': sorted(classifications),
        'classification_authority': 'SUPPLIER_ASSERTION_NOT_PROVIDER_VERIFICATION',
        'variant_rows': counts,
        'quote_path_gate': 'BLOCKED_UNRESOLVED' if counts['UNRESOLVED'] else 'MODELED_PATHS_ONLY',
        'empirical_validation': 'NOT_ESTABLISHED',
        'paper_execution': 'HOLD', 'live_execution': 'NO-GO', 'orders': 'DISABLED',
        'merge': 'HOLD', 'deployment': 'HOLD',
        'gates': [{'id': key, 'status': 'HOLD', 'reason': reason} for key, reason in PAPER_GATES],
        'notification_policy': 'APPROVAL_REQUIRED_ONLY', 'approval_requested': False,
        'limitations': 'Variant rows share entries and are not independent trades or empirical samples',
    }


def scenarios():
    # Tooling deliberately reuses the explicitly fictional regression fixture.
    # Application code does not import tests or this module.
    from test_historical_options_replay import fixture
    cases = {}
    cases['target'] = (fixture(), {}, 'CLOSED', 'TARGET')
    stop = fixture()
    stop['sessions'][0]['contracts'][0]['quotes'][1].update(bid='.10', ask='.11')
    cases['stop-gap'] = (stop, {}, 'CLOSED', 'STOP')
    cutoff = fixture()
    for q in cutoff['sessions'][0]['contracts'][0]['quotes'][1:]:
        q.update(bid='.24', ask='.25')
    cases['cutoff'] = (cutoff, {}, 'CLOSED', 'CUTOFF')
    missing = copy.deepcopy(cutoff)
    missing['sessions'][0]['contracts'][0]['quotes'].pop()
    cases['missing-cutoff'] = (missing, {}, 'UNRESOLVED', 'MISSING_CUTOFF_QUOTE')
    invalid = fixture()
    invalid['sessions'][0]['contracts'][0]['quotes'][1]['bid_size'] = '0'
    cases['invalid-path'] = (invalid, {}, 'UNRESOLVED', 'PATH_GAP_OR_INVALID_QUOTE')
    for key, observed in [('regressed-observation', '2026-11-02T14:51:01.500000+00:00'),
                          ('duplicate-observation', '2026-11-02T14:51:02+00:00')]:
        data = fixture()
        quotes = data['sessions'][0]['contracts'][0]['quotes']
        quotes[1].update(bid='.24', ask='.25')
        quotes[2]['observed'] = observed
        cases[key] = (data, {}, 'UNRESOLVED', 'NONMONOTONIC_EXIT_OBSERVATION')
    stale = fixture()
    stale['sessions'][0]['contracts'][0]['quotes'][0]['observed'] = '2026-11-02T14:50:50+00:00'
    cases['stale-entry'] = (stale, {}, 'REJECTED', 'NO_ELIGIBLE_QUOTE')
    metadata = fixture()
    metadata['sessions'][0]['contracts'][0]['available'] = '2026-11-02T15:00:00+00:00'
    cases['late-metadata'] = (metadata, {}, 'REJECTED', 'NO_ELIGIBLE_QUOTE')
    cases['entry-budget'] = (fixture(), {'budget': '24.5', 'slippage_per_side': '0'},
                             'REJECTED', 'ENTRY_BUDGET')
    return cases


def evidence():
    runs = {}
    for name, (dataset, parameters, status, reason) in scenarios().items():
        result = replay(dataset, parameters)
        if encoded(result) != encoded(replay(dataset, parameters)):
            raise ValueError('Nondeterministic fixture replay: ' + name)
        rows = result['trades']
        if len(rows) != 4 or {r['variant'] for r in rows} != {'A', 'B', 'C', 'D'}:
            raise ValueError('Missing paired variants: ' + name)
        if any(r['status'] != status or r['reason'] != reason for r in rows):
            raise ValueError('Unexpected fixture outcome: ' + name)
        if status != 'REJECTED' and len({encoded(r['entry_quote']) for r in rows}) != 1:
            raise ValueError('Variants no longer share an entry: ' + name)
        runs[name] = result
    result = {'schema_version': 1, 'scope': 'SYNTHETIC_ONLY',
              'engine_version': ENGINE_VERSION, 'scenarios': runs,
              'assessment': assess(list(runs.values()))}
    result['evidence_hash'] = digest(result)
    return result


def validate_evidence(report):
    if type(report) is not dict:
        raise ValueError('Replay evidence object required')
    unsigned = {k: v for k, v in report.items() if k != 'evidence_hash'}
    if report.get('evidence_hash') != digest(unsigned):
        raise ValueError('Replay evidence hash mismatch')
    # Bind coverage, expected outcomes, assessment and current code, not just bytes.
    if encoded(report) != encoded(evidence()):
        raise ValueError('Replay evidence differs from fixed current-code rehearsal')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='historical-rehearsal-') as temp:
        with OfflineGuard(temp):
            report = evidence()
            validate_evidence(report)
    raw = encoded(report) + b'\n'
    with args.output.open('xb') as handle:
        handle.write(raw)
    print(json.dumps({'scenarios': len(report['scenarios']),
                      'paper_execution': 'HOLD', 'orders': 'DISABLED',
                      'artifact_sha256': hashlib.sha256(raw).hexdigest()}, sort_keys=True))


if __name__ == '__main__':
    main()
