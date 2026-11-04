"""Fail-closed fixture-only adapter for synthetic options execution.

This is NOT a live market adapter. No broker, network, disk or order API.
"""
from dataclasses import dataclass
from synthetic_options_execution import Config, Quote, simulate

@dataclass(frozen=True, slots=True)
class FixtureObservation:
    signal_id: str
    contract: str
    right: str
    available_at: str
    observed_at: str
    bid: str
    ask: str
    synthetic: bool = True

def run_fixture_adapter(replay_input, observations, config=Config(), *, synthetic=False):
    """Convert explicitly fictional immutable observations to simulator quotes.

    Structural ambiguity fails before simulation. Price/freshness blocking
    remains the responsibility of the underlying simulator and its ledger.
    """
    if synthetic is not True or type(observations) is not tuple or type(config) is not Config:
        raise ValueError("Explicit synthetic fixture mode, tuple and Config required")
    if len(observations) > 10000:
        raise ValueError("Fixture limit exceeded")
    quotes = []
    for obs in observations:
        if type(obs) is not FixtureObservation or obs.synthetic is not True:
            raise ValueError("Only typed synthetic fixture observations accepted")
        quotes.append(Quote(obs.signal_id, obs.contract, obs.right,
                            obs.available_at, obs.observed_at, obs.bid, obs.ask,
                            synthetic=True))
    return simulate(replay_input, tuple(quotes), config, synthetic=True)
