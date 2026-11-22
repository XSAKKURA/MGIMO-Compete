"""Регрессии финансовых развилок; запуск из любой папки."""
import json
import unittest
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tools"))
from economics import calculate


class EconomicsTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((PROJECT / "demo/inputs.json").read_text(encoding="utf-8"))
        self.scenario = self.data["scenarios"]["main"]

    def test_base_scenarios(self):
        for name, exposure, delta in [('main', 24400, 430000), ('weak', 12200, -58000)]:
            actual = calculate(self.data, self.data["scenarios"][name])
            self.assertEqual((actual["exposure"], actual["contribution"]), (exposure, delta))
            self.assertEqual(sum(actual["quarterly"]), delta)

    def test_replacement_without_new_split(self):
        self.scenario.pop("quarterly_direct_cost")
        self.scenario["annual_direct_cost"] = 700000
        result = calculate(self.data, self.scenario)
        self.assertEqual(result["profit"], 278910000)
        self.assertEqual(result["required_paid_months"], 13400)
        self.assertIsNone(result["quarterly"])

    def test_different_totals_require_reconciliation(self):
        self.scenario["annual_direct_cost"] = 700000
        with self.assertRaises(ValueError):
            calculate(self.data, self.scenario)

    def test_december_only_one_month(self):
        self.scenario["cohorts"] = [[12, 100]]
        self.assertEqual(calculate(self.data, self.scenario)["exposure"], 100)

    def test_zero_exposure_and_invalid_month(self):
        self.scenario["cohorts"] = []
        self.assertIsNone(calculate(self.data, self.scenario)["required_delta"])
        self.scenario["cohorts"] = [[13, 100]]
        with self.assertRaises(ValueError):
            calculate(self.data, self.scenario)


if __name__ == "__main__":
    unittest.main()
