"""Synthetic, network-free futures radar regression tests."""
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from futures_spike_radar import Bar, Option, PaperEntry, Session, detect, rank, record_paper_entry


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
