"""Synthetic, network-free futures radar regression tests."""
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from futures_spike_radar import (
    Bar, Option, PaperEntry, Session, compare_volume_baselines, detect, rank,
    record_paper_entry,
)


class RadarTests(unittest.TestCase):
    def setUp(self):
        opening = datetime(2026, 10, 23, 13, 30, tzinfo=timezone.utc)
        self.session = Session(opening, opening + timedelta(hours=6, minutes=30))
        self.end = opening + timedelta(minutes=21)
        self.now = self.end + timedelta(seconds=2)

    def bars(self, symbol, price, move):
        bars = []
        for index in range(21):
            end = self.end - timedelta(minutes=20 - index)
            close = price + (move if index == 20 else 0)
            bars.append(Bar(symbol, symbol + "1", end, end + timedelta(seconds=1),
                            close + .25, close - .25, close, 300 if index == 20 else 100))
        return bars

    def signal(self, root="ES", symbol="SPY", direction=1):
        return detect(root, self.bars(root, 5000, 15 * direction),
                      self.bars(symbol, 500, 1.5 * direction), self.session, self.now)

    def quote(self, **changes):
        q = Option("SPY", "FIXTURE1", "CALL", self.session.closing, self.now, self.now,
                   Decimal(".18"), Decimal(".20"), 2, 3, 100, 200, .3, .04, -.10, .03)
        return replace(q, **changes)

    def test_aligned_es_and_nq_and_prior_only_baseline(self):
        for root, symbol, direction in (("ES", "SPY", 1), ("NQ", "QQQ", -1)):
            s = self.signal(root, symbol, direction)
            self.assertEqual((s.etf, s.direction, s.volume_ratio), (symbol, direction, 3))
            self.assertEqual(s.broken_level, 5000 + direction * .25)
            self.assertEqual(s.source_lag_seconds, 1)
            self.assertGreater(s.estimated_move, 0)
        s = self.signal("NQ", "QQQ", -1)
        put = self.quote(symbol="QQQ", right="PUT", delta=-.3)
        self.assertEqual(len(rank(s, [put], self.now).candidates), 1)

    def test_etf_confirmation_and_range_break(self):
        futures = self.bars("ES", 5000, 15)
        etf = self.bars("SPY", 500, -1.5)
        futures[0] = replace(futures[0], high=5020)
        s = detect("ES", futures, etf, self.session, self.now)
        self.assertEqual(s.direction, 0)
        self.assertIn("ETF_UNCONFIRMED", s.flags)
        self.assertIn("NO_RANGE_BREAK", s.flags)

    def prior_volume(self, volumes):
        event = self.bars("ES", 5000, 15)[-1]
        history = []
        for days_ago, volume in enumerate(volumes, 1):
            # Simulate a one-hour UTC shift in the prior cash open.
            shift = timedelta(days=days_ago, hours=1)
            prior = Session(self.session.opening - shift, self.session.closing - shift)
            history.append((prior, replace(
                event, end=event.end - shift, received=event.received - shift, volume=volume,
            )))
        return history

    def compare(self, history, event_volume=300):
        futures = self.bars("ES", 5000, 15)
        futures[-1] = replace(futures[-1], volume=event_volume)
        return compare_volume_baselines(
            "ES", futures, self.bars("SPY", 500, 1.5), self.session, self.now, history,
        )

    def test_same_minute_comparison_in_both_directions(self):
        for history, event, expected in (
            ([200] * 5, 300, ((3, 1), (1.5, 0))),
            ([50] * 5, 200, ((2, 0), (4, 1))),
            ([70, 70, 100, 200, 200, 500, 500], 300, ((3, 1), (3, 1))),
        ):
            with self.subTest(history=history, event=event):
                result = self.compare(reversed(self.prior_volume(history)), event)
                self.assertEqual(tuple((s.volume_ratio, s.direction) for s in result.values()),
                                 expected)

    def test_unavailable_history_does_not_fall_back(self):
        history = self.prior_volume([100] * 5)
        prior, bar = history[-1]
        for invalid in (
            (prior, replace(bar, instrument="ES2")),
            (prior, replace(bar, end=bar.end - timedelta(minutes=1))),
            (prior, replace(bar, received=self.now)),
            (prior, replace(bar, delayed=True)),
            (prior, replace(bar, complete=False)),
            (self.session, self.bars("ES", 5000, 15)[-1]),
        ):
            with self.subTest(invalid=invalid):
                result = self.compare([*history[:-1], invalid])
                self.assertEqual(result["rolling_20_minute"].direction, 1)
                normalized = result["prior_session_same_minute"]
                self.assertEqual(normalized.flags, ("TIME_OF_DAY_HISTORY_UNAVAILABLE",))
                self.assertIsNone(normalized.volume_ratio)
        duplicate = self.compare([*history, history[0]])["prior_session_same_minute"]
        self.assertEqual(duplicate.flags, ("TIME_OF_DAY_HISTORY_UNAVAILABLE",))

    def test_prior_session_open_exposure_blocks_same_etf(self):
        prior = Session(self.session.opening - timedelta(days=1),
                        self.session.closing - timedelta(days=1))
        entry = PaperEntry(prior, prior.opening + timedelta(minutes=30), "SPY", "OLD")
        for close in (None, self.now + timedelta(seconds=1)):
            r = rank(self.signal(), [self.quote()], self.now,
                     entries=(replace(entry, closed_at=close),))
            self.assertEqual(r.flags, ("EXPOSURE_OPEN",))
        closed = replace(entry, closed_at=self.now - timedelta(seconds=1))
        self.assertEqual(len(rank(self.signal(), [self.quote()], self.now,
                                  entries=(closed,)).candidates), 1)

    def test_missing_duplicate_roll_and_future_arrival_block(self):
        futures = self.bars("ES", 5000, 15)
        etf = self.bars("SPY", 500, 1.5)
        futures[-2] = futures[-3]
        futures[-1] = replace(futures[-1], instrument="ES2", received=self.now + timedelta(seconds=1))
        s = detect("ES", futures, etf, self.session, self.now)
        self.assertEqual(set(s.flags), {"ES_BAR_GAP_OR_DUPLICATE", "ES_INSTRUMENT_CHANGE", "ES_NOT_AVAILABLE"})

    def test_delayed_and_stale_bars_block(self):
        futures = self.bars("ES", 5000, 15)
        etf = self.bars("SPY", 500, 1.5)
        futures[-1] = replace(futures[-1], delayed=True, received=self.end + timedelta(seconds=6))
        s = detect("ES", futures, etf, self.session, self.end + timedelta(seconds=11))
        self.assertEqual(set(s.flags), {"ES_FEED_LATENCY", "ES_UNVERIFIED_BAR", "ES_STALE", "SPY_STALE"})

    def test_ranks_after_costs_and_exposes_downside(self):
        q = self.quote()
        weaker = replace(q, contract="FIXTURE2", delta=.15)
        r = rank(self.signal(), [weaker, q], self.now)
        self.assertEqual([c.contract for c in r.candidates], ["FIXTURE1", "FIXTURE2"])
        c = r.candidates[0]
        self.assertEqual(c.entry_premium, Decimal("20.10"))
        self.assertEqual(c.max_loss, Decimal("20.75"))
        self.assertLess(c.adverse_pnl, 0)
        self.assertGreaterEqual(c.adverse_pnl, -float(c.max_loss))

    def test_rejects_expensive_crossed_illiquid_and_future_quotes(self):
        quotes = [
            self.quote(contract="PRICE", bid=Decimal(".28"), ask=Decimal(".30")),
            self.quote(contract="CROSSED", bid=Decimal(".21")),
            self.quote(contract="THIN", bid_size=0),
            self.quote(contract="FUTURE", received=self.now + timedelta(seconds=1)),
        ]
        r = rank(self.signal(), quotes, self.now)
        self.assertFalse(r.candidates)
        self.assertEqual(dict(r.rejected), {"PRICE": "PREMIUM_LIMIT", "CROSSED": "INVALID_MARKET",
                                           "THIN": "INSUFFICIENT_LIQUIDITY", "FUTURE": "QUOTE_UNAVAILABLE"})

    def test_paper_entry_cannot_add_to_open_exposure_or_exceed_daily_limit(self):
        s, q = self.signal(), self.quote()
        entries, _ = record_paper_entry(s, [q], self.now)
        self.assertEqual(len(entries), 1)
        same, blocked = record_paper_entry(s, [q], self.now, entries)
        self.assertIs(same, entries)
        self.assertEqual(blocked.flags, ("EXPOSURE_OPEN",))
        prior = tuple(PaperEntry(self.session, self.now - timedelta(seconds=60 - i),
                                 "QQQ", f"OLD{i}", self.now - timedelta(seconds=1))
                      for i in range(2))
        third, _ = record_paper_entry(s, [q], self.now, prior)
        self.assertEqual(len(third), 3)
        same, blocked = record_paper_entry(s, [q], self.now, third)
        self.assertIs(same, third)
        self.assertEqual(blocked.flags, ("DAILY_LIMIT",))


if __name__ == "__main__":
    unittest.main()

