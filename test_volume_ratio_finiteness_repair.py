"""Focused H-007 numerical-safety boundaries; synthetic only, no IO adapters."""
import copy
import json
import math
import sys
import unittest

from test_extreme_numeric_output import synthetic_rows, snapshot, nonfinite_paths


class VolumeRatioFinitenessRepairTests(unittest.TestCase):
    def result_for_volumes(self, prior, current):
        rows = synthetic_rows(False)
        for row in rows[:-1]:
            row["volume"] = prior
        rows[-1]["volume"] = current
        before = copy.deepcopy(rows)
        result = snapshot(rows)
        self.assertEqual(rows, before)
        self.assertEqual(nonfinite_paths(result), [])
        json.dumps(result, allow_nan=False)
        return result

    def assert_overflow_abstention(self, result):
        self.assertEqual(result["signal"], "NO TRADE")
        self.assertEqual(result["reasons"], ["VOLUME_RATIO_OVERFLOW"])
        self.assertEqual(result["data_quality"]["issues"], ["VOLUME_RATIO_OVERFLOW"])
        self.assertEqual(result["data_quality"]["status"], "READY")
        self.assertEqual(result["observations"]["indicator_status"], "EVALUATED")
        self.assertIsNone(result["observations"]["volume_ratio"])

    def test_h006_overflow_is_unavailable_with_explicit_abstention(self):
        result = self.result_for_volumes(1e-200, 1e200)
        self.assert_overflow_abstention(result)

    def test_largest_finite_ratio_is_not_clipped_or_rejected(self):
        result = self.result_for_volumes(1.0, sys.float_info.max)
        self.assertEqual(result["observations"]["volume_ratio"], sys.float_info.max)
        self.assertNotIn("VOLUME_RATIO_OVERFLOW", result["reasons"])

    def test_ratio_above_float_max_fails_closed_without_a_finite_cap(self):
        result = self.result_for_volumes(0.5, sys.float_info.max)
        self.assert_overflow_abstention(result)

    def test_smallest_positive_baseline_overflow_is_handled(self):
        result = self.result_for_volumes(math.ulp(0.0), 1.0)
        self.assert_overflow_abstention(result)

    def test_zero_baseline_preserves_existing_missing_ratio_reason(self):
        result = self.result_for_volumes(0.0, 1.0)
        self.assertIsNone(result["observations"]["volume_ratio"])
        self.assertIn("ZERO_VOLUME_BASELINE", result["reasons"])
        self.assertNotIn("VOLUME_RATIO_OVERFLOW", result["reasons"])

    def test_zero_current_volume_preserves_finite_zero_ratio(self):
        result = self.result_for_volumes(1.0, 0.0)
        self.assertEqual(result["observations"]["volume_ratio"], 0.0)
        self.assertEqual(result["signal"], "NO TRADE")
        self.assertIn("VOLUME_NOT_CONFIRMED", result["reasons"])
        self.assertNotIn("VOLUME_RATIO_OVERFLOW", result["reasons"])


if __name__ == "__main__":
    unittest.main()
