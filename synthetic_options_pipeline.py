"""Pure fictional signal -> contract -> option-fill pipeline. No I/O or orders."""
from dataclasses import dataclass
from datetime import datetime
from paper_signal_engine import run
from synthetic_contract_selector import select_contract
from synthetic_options_adapter import FixtureObservation, run_fixture_adapter
from synthetic_options_execution import Config

@dataclass(frozen=True, slots=True)
class SelectionInput:
    signal_id: str
    candidates: tuple
    observations: tuple

@dataclass(frozen=True, slots=True)
class PipelineResult:
    decisions: tuple
    execution: object
    mode: str = "SYNTHETIC_ONLY"
    orders: str = "DISABLED"

def execute_fixture_pipeline(replay_input, selections, config=Config(), *,
                             synthetic=False):
    """Select from cutoff-known fictional chains, then simulate later quotes.

    Missing/rejected selection yields no fill. No chain-to-real-contract mapping.
    Candidate timestamps must not postdate signal cutoff; exit observations must
    refer to the selected contract and remain subject to simulator validation.
    """
    if synthetic is not True or type(selections) is not tuple or type(config) is not Config:
        raise ValueError("Explicit fictional immutable pipeline inputs required")
    if len(selections) > 10000:
        raise ValueError("Too many selection inputs")
    signals = run(replay_input, synthetic=True)
    events = {e.event_id: e for e in signals.signals}
    seen, decisions, observations = set(), [], []
    for item in selections:
        if type(item) is not SelectionInput or item.signal_id not in events or item.signal_id in seen:
            raise ValueError("Unique known signal selections required")
        if type(item.candidates) is not tuple or type(item.observations) is not tuple:
            raise ValueError("Immutable candidate and observation tuples required")
        seen.add(item.signal_id)
        event = events[item.signal_id]
        cutoff = datetime.fromisoformat(event.cutoff)
        decision = select_contract(event.symbol, event.direction,
                                   cutoff.date().isoformat(), event.cutoff,
                                   item.candidates)
        decisions.append((item.signal_id, decision))
        if decision.selected is None:
            if item.observations:
                raise ValueError("Cannot supply fills without an eligible selection")
            continue
        expected_right = "CALL" if event.direction == "BULLISH" else "PUT"
        for obs in item.observations:
            if type(obs) is not FixtureObservation or obs.synthetic is not True:
                raise ValueError("Typed fictional observations required")
            if obs.signal_id != item.signal_id or obs.contract != decision.selected or obs.right != expected_right:
                raise ValueError("Observation must match selected signal/contract/right")
            observations.append(obs)
    # The execution engine validates time ordering, freshness, session bounds,
    # entry premium after slippage, limits, and all exit quote conditions.
    observations.sort(key=lambda obs: (datetime.fromisoformat(obs.available_at), obs.signal_id))
    result = run_fixture_adapter(replay_input, tuple(observations), config, synthetic=True)
    return PipelineResult(tuple(decisions), result)
