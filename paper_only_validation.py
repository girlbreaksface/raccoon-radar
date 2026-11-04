"""Fixed fictional rehearsal; stdout evidence only, never a broker interface.

Run: python -B paper_only_validation.py > NEW_REPORT.json
Use exclusive file creation when preserving evidence programmatically.
"""
import hashlib
import json
import platform
import tempfile
from dataclasses import asdict, replace
from pathlib import Path

from offline_checks import OfflineGuard


def validate():
    # Guard before importing the replay/adapter dependency graph.
    with tempfile.TemporaryDirectory(prefix='raccoon-paper-') as root:
        with OfflineGuard(root):
            from canonical_candles import identity
            from paper_signal_engine import run
            from synthetic_options_adapter import FixtureObservation, run_fixture_adapter
            from synthetic_options_execution import VERSION
            from synthetic_replay_demo import make_demo

            demo = make_demo('conflict')
            data = replace(demo, steps=(demo.steps[34],))
            event = run(data, synthetic=True).signals[0]
            right = 'CALL' if event.direction == 'BULLISH' else 'PUT'

            def quote(second=2, bid='.19', ask='.20', **changes):
                at = f'2026-10-23T10:05:{second:02d}+00:00'
                return replace(FixtureObservation(event.event_id, 'FICTIONAL1', right,
                               at, at, bid, ask), **changes)

            scenarios = {
                'target': ((quote(), quote(3, '.24', '.25')), 'SELL_TARGET'),
                'stop_gap': ((quote(), quote(3, '.10', '.20')), 'SELL_STOP'),
                'premium_limit': ((quote(ask='.31'),), 'REJECT_PREMIUM_LIMIT'),
                'stale': ((quote(observed_at='2026-10-23T10:04:00+00:00'),), 'QUOTE_BLOCKED'),
                'future_quote': ((quote(observed_at='2026-10-23T10:05:03+00:00'),), 'QUOTE_BLOCKED'),
                'invalid_price': ((quote(bid='NaN'),), 'QUOTE_BLOCKED'),
                'missing_quote': ((), 'UNFILLED'),
                'open_position': ((quote(),), 'BUY'),
            }
            results = {}
            for name, (observations, expected) in scenarios.items():
                result = run_fixture_adapter(data, observations, synthetic=True)
                if result != run_fixture_adapter(data, observations, synthetic=True):
                    raise RuntimeError('Nondeterministic replay')
                if expected not in [row[1] for row in result.ledger]:
                    raise RuntimeError(f'Missing expected outcome: {name}')
                parent = result.signal_run_hash
                for row in result.ledger:
                    if row[-2] != parent or row[-1] != identity((VERSION, row[:-1])):
                        raise RuntimeError('Broken ledger chain')
                    parent = row[-1]
                if (result.mode, result.trading, result.orders) != ('SYNTHETIC_ONLY', 'NO-GO', 'DISABLED'):
                    raise RuntimeError('Unsafe result controls')
                results[name] = {'expected': expected, 'result': asdict(result)}
            sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted(Path(__file__).parent.glob('*.py'))}
            return {
                'schema': 'raccoon-paper-rehearsal-v1',
                'integration': 'HOLD', 'live_trading': 'NO-GO',
                'external_paper_orders': 'REVIEW_REQUIRED', 'orders': 'DISABLED',
                'python': platform.python_version(), 'platform': platform.system(),
                'source_sha256': sources, 'scenarios': results,
                'limitations': 'Fictional UTC fixtures only. No broker, market, fill, calendar or profitability validation. Open positions are not forcibly liquidated.',
            }


if __name__ == '__main__':
    print(json.dumps(validate(), sort_keys=True, indent=2))
