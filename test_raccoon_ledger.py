"""H-011 reference arithmetic only; all examples synthetic, no feeds or stores."""
import copy
import unittest
from decimal import Decimal
from raccoon_ledger import calculate, calculator_view, NOTICE


def inputs(**changes):
    values = dict(premium="1.00", contracts="2", stop_percent="15",
                  target_percent="20", tick="0.01", entry_fees="0.00", exit_fees="0.00")
    values.update(changes)
    return values


class LedgerCalculatorTests(unittest.TestCase):
    def test_default_reference_levels_and_standard_multiplier(self):
        result = calculate(**inputs())
        self.assertEqual(result.stop_premium, Decimal("0.85"))
        self.assertEqual(result.target_premium, Decimal("1.20"))
        self.assertEqual(result.entry_cost, Decimal("200.00"))
        self.assertEqual(result.stop_pnl, Decimal("-30.00"))
        self.assertEqual(result.target_pnl, Decimal("40.00"))

    def test_total_position_entry_and_exit_fees_are_subtracted_once(self):
        result = calculate(**inputs(entry_fees="1.30", exit_fees="1.30"))
        self.assertEqual(result.entry_cost, Decimal("201.30"))
        self.assertEqual(result.stop_pnl, Decimal("-32.60"))
        self.assertEqual(result.target_pnl, Decimal("37.40"))

    def test_adjustable_percentages(self):
        result = calculate(**inputs(premium="2.50", stop_percent="10", target_percent="30"))
        self.assertEqual((result.stop_premium, result.target_premium),
                         (Decimal("2.25"), Decimal("3.25")))

    def test_tick_rounds_both_reference_levels_toward_entry(self):
        result = calculate(**inputs(premium="1.05", tick="0.05"))
        self.assertEqual((result.stop_premium, result.target_premium),
                         (Decimal("0.90"), Decimal("1.25")))
        self.assertEqual((result.stop_pnl, result.target_pnl),
                         (Decimal("-30.00"), Decimal("40.00")))
        self.assertEqual(result.stop_change_percent, Decimal("-14.29"))
        self.assertEqual(result.target_change_percent, Decimal("19.05"))

    def test_ten_cent_tick_and_binary_float_sensitive_input(self):
        result = calculate(**inputs(premium="0.30", tick="0.01"))
        self.assertEqual((result.stop_premium, result.target_premium),
                         (Decimal("0.26"), Decimal("0.36")))
        result = calculate(**inputs(premium="2.00", tick="0.10"))
        self.assertEqual((result.stop_premium, result.target_premium),
                         (Decimal("1.70"), Decimal("2.40")))

    def test_zero_negative_nonfinite_or_malformed_premium_is_rejected(self):
        for value in ("", "0", "-1", "NaN", "Infinity", "1e3", "$1", "1,000", "bad", True, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate(**inputs(premium=value))

    def test_contracts_require_positive_whole_numbers_within_display_limit(self):
        for value in ("0", "-1", "1.5", "1.0", "NaN", "100001", True, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate(**inputs(contracts=value))

    def test_malformed_percentages_and_extreme_sizes_rejected(self):
        for name, value in (("stop_percent","0"),("stop_percent","100"),
                            ("target_percent","0"),("target_percent","1000.01"),
                            ("target_percent","Infinity"),("premium","1000000.01"),
                            ("premium","1"*200),("stop_percent","0.000000001")):
            with self.subTest(name=name,value=value), self.assertRaises(ValueError):
                calculate(**inputs(**{name:value}))

    def test_fee_cents_finiteness_and_nonnegative_validation(self):
        for field in ("entry_fees", "exit_fees"):
            for value in ("-1", "NaN", "Infinity", "0.001", "100000000.01", ""):
                with self.subTest(field=field,value=value), self.assertRaises(ValueError):
                    calculate(**inputs(**{field:value}))

    def test_unsupported_tick_and_off_tick_entry_rejected(self):
        for values in (dict(tick="0"),dict(tick="0.03"),dict(tick="NaN"),
                       dict(premium="1.03",tick="0.05")):
            with self.subTest(values=values), self.assertRaises(ValueError):
                calculate(**inputs(**values))

    def test_tiny_percentage_cannot_produce_collapsed_reference_levels(self):
        for values in (dict(premium="0.01"),dict(stop_percent="0.01"),
                       dict(target_percent="0.01")):
            with self.subTest(values=values), self.assertRaises(ValueError):
                calculate(**inputs(**values))

    def test_maximum_supported_values_stay_finite_and_exact(self):
        result = calculate(**inputs(premium="1000000", contracts="100000",
                                    stop_percent="99", target_percent="1000"))
        self.assertTrue(result.entry_cost.is_finite())
        self.assertTrue(result.target_pnl.is_finite())
        self.assertEqual(result.entry_cost, Decimal("10000000000000.00"))

    def test_explicit_fee_estimate_can_make_target_net_pnl_negative(self):
        result = calculate(**inputs(entry_fees="30", exit_fees="30"))
        self.assertEqual(result.target_pnl, Decimal("-20.00"))

    def test_caller_decimal_context_cannot_change_reference_calculations(self):
        from decimal import Inexact, localcontext
        with localcontext() as context:
            context.prec = 2
            context.traps[Inexact] = True
            result = calculate(**inputs(premium="1.05", tick="0.05",
                                        entry_fees="1.30", exit_fees="1.30"))
            self.assertEqual(result.stop_pnl, Decimal("-32.60"))
            view = calculator_view(inputs(premium="1.05", tick="0.05",
                                          entry_fees="1.30", exit_fees="1.30"))
            self.assertIn("-$32.60", view["stop"])
            self.assertEqual(context.prec, 2)
            self.assertTrue(context.traps[Inexact])

    def test_input_preservation_and_determinism(self):
        values = inputs()
        before = copy.deepcopy(values)
        self.assertEqual(calculate(**values), calculate(**values))
        self.assertEqual(values, before)

    def test_invalid_edit_clears_old_display_values_and_preserves_notice(self):
        valid = calculator_view(inputs())
        invalid = calculator_view(inputs(premium=""))
        self.assertTrue(valid["valid"])
        self.assertFalse(invalid["valid"])
        self.assertEqual(invalid["stop"], "—")
        self.assertEqual(invalid["target"], "—")
        self.assertEqual(invalid["entry_cost"], "—")
        self.assertTrue(invalid["error"])
        self.assertEqual(invalid["notice"], NOTICE)

    def test_view_shows_fee_basis_adjusted_percentages_and_reference_wording(self):
        view = calculator_view(inputs(premium="1.05",tick="0.05"))
        self.assertIn("$0.90", view["stop"])
        self.assertIn("-14.29%", view["stop"])
        self.assertIn("$1.25", view["target"])
        self.assertIn("+19.05%", view["target"])
        self.assertIn("reference", view["notice"].lower())
        self.assertIn("no automatic", view["notice"].lower())
        self.assertIn("100", view["notice"])
        self.assertIn("fees", view["fee_basis"].lower())


if __name__ == "__main__":
    unittest.main()
