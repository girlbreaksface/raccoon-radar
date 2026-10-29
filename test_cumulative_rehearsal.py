"""Bounded cumulative synthetic rehearsal; original PR source/fixtures stay unchanged."""
import copy
from dataclasses import replace
from decimal import getcontext
import hashlib
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

import canonical_candles as canonical
import pinned_timezone_bridge as bridge
import raccoon_scanner_successor as scanner
from test_canonical_candles import example, ny_example, reseal


class CumulativeRehearsalTests(unittest.TestCase):
    def test_root_scanner_matches_exact_pinned_fixture_after_checkout_newlines(self):
        root = Path(__file__).parent
        fixture = (root / "tests/canonicalizer_fixtures/pr31_successor.py.txt").read_bytes()
        expected = "5e6e2b647ff6f763c356e34a1adde2b375470d2f00ff6811fc37e74d2b718a29"
        self.assertEqual(hashlib.sha256(fixture).hexdigest(), expected)
        # Git for Windows can use CRLF working-tree text. Git blob hashes are
        # independently verified in the evidence manifest; this check explicitly
        # compares universal-newline source, never changes either file.
        text = (root / "raccoon_scanner_successor.py").read_text(encoding="utf-8")
        self.assertEqual(text.encode("utf-8"), fixture)

    def test_root_scanner_and_bridge_utc_bullish_bearish_mixed_parity(self):
        for direction in ("BULLISH", "BEARISH", "MIXED"):
            with self.subTest(direction=direction):
                b, c, r = example()
                if direction != "BULLISH":
                    rows = tuple(replace(o, values=(
                        (200-i, 202-i, 199-i, 201-i, 100) if direction == "BEARISH"
                        else (100, 101, 99, 100, 100)))
                        for i, o in enumerate(b.observations))
                    b = reseal(b, rows)
                report = canonical.canonicalize(b, c, r)
                args = canonical.to_pr31_arguments(report)
                before = copy.deepcopy(args)
                direct = scanner.assess(**args)
                bridged = bridge.evaluate(report)
                self.assertEqual(bridge.consumer_dict(bridged), direct)
                self.assertEqual(direct["bias"], direction)
                self.assertEqual(bridged.eligible, direction != "MIXED")
                self.assertEqual(args, before)
                self.assertEqual(direct["action"], "WAIT")

    def test_new_york_root_definition_pinned_rules_and_call_order_isolation(self):
        b, c, r = ny_example("2026-10-23")
        report = canonical.canonicalize(b, c, r)
        args = bridge._arguments(report)
        before = copy.deepcopy((b, c, r, args))
        decimal_before = repr(getcontext())
        original_zone = scanner.ZoneInfo
        # Isolated definition namespace, not mutation of root scanner globals.
        namespace = {"__name__": "synthetic_rehearsal_root_reference"}
        exec(compile(Path(scanner.__file__).read_bytes(), scanner.__file__, "exec"), namespace)
        def pinned(name):
            self.assertEqual(name, c.calendar.timezone)
            rule = next(rule for rule in c.time_rules if rule.name == name)
            return ZoneInfo.from_file(BytesIO(rule.data), key=name)
        namespace["ZoneInfo"] = pinned
        expected = namespace["assess"](**args)
        self.assertTrue(expected["eligible"])
        for order in (("utc", "ny", "utc", "ny"), ("ny", "utc", "ny", "utc")):
            for mode in order:
                result = bridge.evaluate(report if mode == "ny" else canonical.canonicalize(*example()))
                if mode == "ny":
                    self.assertEqual(bridge.consumer_dict(result), expected)
                self.assertEqual(result.action, "WAIT")
        with self.assertRaises(ValueError):
            canonical.to_pr31_arguments(report)
        self.assertIs(scanner.ZoneInfo, original_zone)
        self.assertIs(canonical.ZoneInfo, ZoneInfo)
        self.assertEqual(repr(getcontext()), decimal_before)
        self.assertEqual((b, c, r, args), before)

    def test_invalid_canonical_inputs_do_not_reach_either_numeric_entry(self):
        b, c, r = example()
        cases = (
            (b, replace(c, authorities=()), r),
            (reseal(b, b.observations[:-1]), c, r),
            (reseal(b, b.observations + (b.observations[-1],)), c, r),
            (reseal(b, b.observations[:-1] +
                (replace(b.observations[-1], available_at=None),)), c, r),
        )
        for data, context, request in cases:
            with self.subTest(case=canonical.identity((data, context, request))):
                with patch.object(scanner, "assess", side_effect=AssertionError("Root called")), \
                     patch.object(bridge.kernel, "assess", side_effect=AssertionError("Kernel called")):
                    report = canonical.canonicalize(data, context, request)
                    self.assertFalse(report.eligible)
                    with self.assertRaises(ValueError):
                        canonical.to_pr31_arguments(report)
                    result = bridge.evaluate(report)
                    self.assertFalse(result.eligible)
                    self.assertEqual(result.action, "WAIT")
