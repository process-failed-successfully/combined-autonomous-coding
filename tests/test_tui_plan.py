import unittest
from pathlib import Path
from shared.tui import PlanTab

class TestTuiPlan(unittest.TestCase):
    def test_plan_tab_init(self):
        tab = PlanTab(Path("."))
        self.assertIsInstance(tab, PlanTab)
        self.assertEqual(tab.spec_file, Path("app_spec.txt"))
        self.assertEqual(tab.feature_file, Path("feature_list.json"))

if __name__ == "__main__":
    unittest.main()
