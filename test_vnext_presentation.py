"""Offline presentation regression checks; the original engine tests are untouched."""
import unittest
from raccoon_radar_vnext_1_1 import indicator, cell_view
from raccoon_replay_viewer import ViewerModel
from synthetic_replay_demo import SCENARIOS
from pinned_timezone_bridge import consumer_dict


class PresentationTests(unittest.TestCase):
    def test_rounding_is_display_only(self):
        model = ViewerModel()
        cell = model.result.points[34].cells[0]
        before = consumer_dict(cell.evidence)
        self.assertEqual(cell_view(cell)[2][0][1], "131.00")
        self.assertEqual(cell_view(cell)[2][1][1], "125.39")
        self.assertEqual(before, consumer_dict(cell.evidence))
        self.assertIn(before["observations"]["ema9"], model.text())
        self.assertEqual(indicator("1.23456789"), "1.2346")
        for value in (None, "NaN", "Infinity", "bad", True):
            self.assertEqual(indicator(value), "UNAVAILABLE")

    def test_every_scenario_and_cutoff_preserves_results(self):
        for scenario, _ in SCENARIOS:
            model = ViewerModel(scenario)
            before = repr(model.result)
            for minute in range(1, 41):
                model.seek(minute)
                for cell in model.result.points[model.index].cells:
                    title, color, values = cell_view(cell)
                    self.assertEqual(len(values), 4)
                    self.assertEqual(cell.action, "WAIT")
                    if cell.state != "CANDIDATE":
                        self.assertEqual(color, "#f3c773")
            self.assertEqual(repr(model.result), before)


if __name__ == "__main__":
    unittest.main()
