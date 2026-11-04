"""Print one predefined fictional simulator scenario. No external data paths."""
import argparse
from dataclasses import asdict, replace
import json

from paper_execution import Config, Quote, simulate
from synthetic_replay_demo import make_demo


def demo(scenario='closed'):
    if scenario not in ('closed', 'open', 'expired'):
        raise ValueError('Predefined synthetic scenario required')
    data = make_demo('conflict')
    if scenario != 'expired':
        data = replace(data, steps=(data.steps[34],))
    quotes = (
        Quote('2026-10-23', '2026-10-23T10:05:02Z', 'QQQ', '100', '101'),
        Quote('2026-10-23', '2026-10-23T10:05:02Z', 'SPY', '99', '100'),
        Quote('2026-10-23', '2026-10-23T10:06:02Z', 'QQQ', '89', '90'),
        Quote('2026-10-23', '2026-10-23T10:06:02Z', 'SPY', '110', '111'),
    )
    if scenario == 'open':
        quotes = quotes[:2]
    if scenario == 'expired':
        quotes = ()
    result = simulate(data, quotes, Config(fee_per_fill='1'), synthetic=True)
    return dict(notice='FICTIONAL SHARES ONLY. No real fills or performance evidence.',
                scenario=scenario, simulation=asdict(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=('closed', 'open', 'expired'), default='closed')
    print(json.dumps(demo(parser.parse_args().scenario), sort_keys=True, indent=2))
