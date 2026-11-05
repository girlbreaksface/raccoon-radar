"""Guarded deterministic indicator evidence; fictional candles only."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from generate_indicator_golden import golden
from offline_checks import OfflineGuard
from test_production_indicators import FIXTURE, IndicatorTests, bars, run


def evidence():
    raw = FIXTURE.read_bytes()
    if json.loads(raw) != golden():
        raise ValueError('Static golden fixture differs from independent rational oracle')
    return dict(schema=1, scope='SYNTHETIC_ONLY', profile='PROVISIONAL_RTH_1M_V1',
                calendar='PUBLISHED_NYSE_2026_ONLY_UNSCHEDULED_UNVERIFIED',
                fixture_sha256=hashlib.sha256(raw).hexdigest(),
                numerical={str(n): run(bars(count=n)) for n in (101, 120)},
                paper_execution='HOLD', recording='HOLD', live_execution='NO-GO',
                orders='DISABLED', merge='HOLD', deployment='HOLD', provider_verified=False)


def validate_evidence(report):
    if report != evidence():
        raise ValueError('Indicator evidence differs from fixed current-code fixtures')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp, OfflineGuard(temp):
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(IndicatorTests))
        if not result.wasSuccessful():
            return 1
        report = evidence()
        validate_evidence(report)
    with args.output.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('Independent rational fixtures and indicator regressions PASS; orders DISABLED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
