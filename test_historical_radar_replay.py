"""Synthetic fixtures for the Phase 3 import and replay."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from historical_radar_replay import replay


def stamp(dt):
    return dt.isoformat().replace("+00:00", "Z")


def fixture():
    opening = datetime(2026, 10, 26, 13, 30, tzinfo=timezone.utc)
    coverage = ("common_cash_calendar", "dated_futures", "consolidated_equity",
                "consolidated_options", "point_in_time_greeks", "asof_option_volume",
                "published_open_interest", "point_in_time_definition")
    sources = {
        name: dict(provider="fixture", dataset=name, coverage=name, clock="synthetic",
                   artifact="generated", rights_reference="synthetic")
        for name in coverage
    }

    def evidence(source, when, lag=0, **extra):
        return dict(source=source, observed=stamp(when),
                    available=stamp(when + timedelta(seconds=lag)), **extra)

    bundle = dict(version=1, kind="synthetic", sources=sources, sessions=[],
                  bars=[], quotes=[], calendar=evidence(coverage[0], opening - timedelta(days=1)))
    for day in (0, 1, 2, 3, 4, 7):
        start = opening + timedelta(days=day, hours=int(day == 7))
        bundle["sessions"].append(dict(id=str(day), opening=stamp(start), **{"from": stamp(start)},
                                       closing=stamp(start + timedelta(hours=6, minutes=30)),
                                       until=stamp(start + timedelta(minutes=27)),
                                       root="ES", contract="ESZ6"))
        for minute in range(1, 28):
            end = start + timedelta(minutes=minute)
            for symbol, instrument, price, move, feed in (
                ("ES", "ESZ6", 5000, 15, coverage[1]),
                ("SPY", "SPY", 500, 1.5, coverage[2]),
            ):
                close = price + (move if day == 7 and minute >= 21 else 0)
                volume = (300 if day == 7 else 200) if minute == 21 else 100
                bundle["bars"].append(evidence(
                    feed, end, 1, session=str(day), symbol=symbol, instrument=instrument,
                    close=close, low=close - .25, high=close + .25, volume=volume,
                    complete=True, delayed=False,
                ))
        if day == 7:
            for minute, bid in ((21, ".18"), (26, ".31")):
                when = start + timedelta(minutes=minute, seconds=4)
                for contract, ask in (("fixture-A", ".32" if minute == 26 else ".20"),
                                      ("fixture-B", ".36" if minute == 26 else ".30")):
                    bundle["quotes"].append(evidence(
                        coverage[3], when, 1, session=str(day), symbol="SPY", contract=contract,
                        bid=bid if contract == "fixture-A" or minute == 26 else ".25",
                        ask=ask, bid_size=2, ask_size=3, delayed=False,
                        greeks=evidence(coverage[4], when, value=dict(
                            delta=.3, gamma=.04, theta_per_day=-.10, vega_per_point=.03)),
                        volume=evidence(coverage[5], when, value=100),
                        open_interest=evidence(coverage[6], start, value=200),
                        definition=evidence(coverage[7], start, value=dict(
                            right="CALL", expires=stamp(start + timedelta(hours=6)),
                            multiplier=100, standard_deliverable=True)),
                    ))
    return bundle


class HistoricalReplayTests(unittest.TestCase):
    def test_paired_replay_and_hypothetical_costs(self):
        bundle = fixture()
        report = replay(bundle)
        rolling = report["metrics"]["rolling_20_minute"]
        self.assertEqual((rolling["signals"], rolling["hypothetical_entries"],
                          rolling["priced_exit"]), (1, 1, 1))
        self.assertEqual(rolling["modeled_net_pnl"], Decimal("9.44500"))
        self.assertEqual(rolling["contract:PREMIUM_LIMIT"], 1)
        self.assertEqual(report["signal_agreement"]["rolling_20_minute"], 1)
        self.assertEqual(report["metrics"]["prior_session_same_minute"]["signals"], 0)
        for name in ("bars", "quotes", "sessions"):
            bundle[name].reverse()
        self.assertEqual(report, replay(bundle))

    def test_a_gap_and_unavailable_quotes_do_not_create_an_entry(self):
        bundle = fixture()
        bundle["bars"].pop(-15)
        self.assertEqual(replay(bundle)["metrics"]["rolling_20_minute"]["signals"], 0)
        bundle = fixture()
        for quote in bundle["quotes"][:2]:
            quote["available"] = quote["available"].replace(":05Z", ":06Z")
        self.assertEqual(replay(bundle)["metrics"]["rolling_20_minute"]["hypothetical_entries"], 0)

    def test_missing_and_stale_exit_are_unpriced(self):
        bundle = fixture()
        del bundle["quotes"][2:]
        result = replay(bundle)["metrics"]["rolling_20_minute"]
        self.assertEqual((result["missing_exit"], result["priced_exit"]), (1, 0))

    def test_rejects_duplicates_and_future_greeks(self):
        bundle = fixture()
        bundle["bars"].append(deepcopy(bundle["bars"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate bar"):
            replay(bundle)
        bundle = fixture()
        quote = bundle["quotes"][0]
        quote["greeks"]["available"] = bundle["quotes"][-1]["available"]
        with self.assertRaisesRegex(ValueError, "contemporaneous"):
            replay(bundle)

    def test_contract_roll_does_not_borrow_volume_history(self):
        bundle = fixture()
        bundle["sessions"][-1]["contract"] = "ESH7"
        for bar in bundle["bars"]:
            if bar["session"] == "7" and bar["symbol"] == "ES":
                bar["instrument"] = "ESH7"
        counts = replay(bundle)["metrics"]["prior_session_same_minute"]
        self.assertEqual(counts["signal:TIME_OF_DAY_HISTORY_UNAVAILABLE"], 36)
