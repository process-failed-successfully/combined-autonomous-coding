import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.health import HealthCalculator

class TestHealthCalculator(unittest.TestCase):
    def setUp(self):
        self.mock_project_dir = MagicMock(spec=Path)
        self.mock_project_dir.resolve.return_value = self.mock_project_dir
        self.mock_project_dir.name = "test_project"
        self.calc = HealthCalculator(self.mock_project_dir)

    @patch("shared.health.run_tests")
    def test_check_tests_passing(self, mock_run_tests):
        mock_run_tests.return_value = {
            "success": True,
            "stdout": "TOTAL 100 10 90%",
            "stderr": ""
        }
        self.calc._check_tests()
        self.assertEqual(self.calc.scores["tests"], 38.0) # 20 base + (0.9 * 20) = 38
        self.assertTrue(self.calc.details["tests"]["passed"])

    @patch("shared.health.run_tests")
    def test_check_tests_failing(self, mock_run_tests):
        mock_run_tests.return_value = {
            "success": False,
            "stdout": "",
            "stderr": "Error"
        }
        self.calc._check_tests()
        self.assertEqual(self.calc.scores["tests"], 0)
        self.assertFalse(self.calc.details["tests"]["passed"])

    @patch("shared.health.run_lint")
    def test_check_lint(self, mock_run_lint):
        # Mock output with 3 errors
        mock_run_lint.return_value = {
            "success": False,
            "stdout": "./file.py:1:1: E101 indentation\n./file.py:2:1: E102 indentation\n./file.py:3:1: F401 unused",
            "stderr": ""
        }
        self.calc._check_lint()
        # 3 errors -> deduction of 3. Max score 20. Result 17.
        self.assertEqual(self.calc.scores["lint"], 17)
        self.assertEqual(self.calc.details["lint"]["issues"], 3)

    @patch("shared.health.run_security_scan")
    def test_check_security(self, mock_run_security):
        # Mock output with 1 high, 1 medium
        mock_run_security.return_value = {
            "success": False,
            "stdout": "High: 1\nMedium: 1\nLow: 0",
            "stderr": ""
        }
        self.calc._check_security()
        # Deduction: (1*10) + (1*3) = 13. Max score 20. Result 7.
        self.assertEqual(self.calc.scores["security"], 7)
        self.assertEqual(self.calc.details["security"]["high"], 1)

    @patch("shared.health.DependencyAnalyzer")
    def test_check_dependencies(self, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        # Mock scan data with 2 outdated deps
        mock_analyzer.scan.return_value = {}
        mock_analyzer.check_updates.return_value = {
            "python": [
                {
                    "dependencies": [
                        {"name": "a", "outdated": True},
                        {"name": "b", "outdated": True},
                        {"name": "c", "outdated": False}
                    ]
                }
            ]
        }

        self.calc._check_dependencies()
        # Deduction: 2. Max score 10. Result 8.
        self.assertEqual(self.calc.scores["dependencies"], 8)
        self.assertEqual(self.calc.details["dependencies"]["outdated"], 2)

    @patch("shared.health.analyze_project_complexity")
    def test_check_complexity(self, mock_analyze):
        # Mock results: avg complexity 6, 1 high risk (>10)
        mock_analyze.return_value = [
            {"complexity": 2},
            {"complexity": 4},
            {"complexity": 12}, # High risk
            {"complexity": 6}
        ]
        # Avg = (2+4+12+6)/4 = 6.0

        self.calc._check_complexity()

        # Max score 10
        # Deduction for avg > 5: (6.0 - 5) = 1.0
        # Deduction for high risk: 1 * 2 = 2.0
        # Total deduction = 3.0
        # Result = 7.0
        self.assertEqual(self.calc.scores["complexity"], 7.0)
        self.assertEqual(self.calc.details["complexity"]["high_risk"], 1)
        self.assertEqual(self.calc.details["complexity"]["average"], 6.0)

    def test_grade_calculation(self):
        # Manually set scores
        self.calc.scores = {
            "tests": 40,
            "lint": 20,
            "security": 20,
            "dependencies": 10,
            "complexity": 10
        }
        # Total 100
        report = self.calc.run() # This will re-run checks if we don't mock internal methods, but we can check grade logic if we mock run

        # We'll just instantiate a fresh calculator and mock the internal methods
        calc = HealthCalculator(self.mock_project_dir)
        calc._check_tests = lambda: calc.scores.update({"tests": 40})
        calc._check_lint = lambda: calc.scores.update({"lint": 20})
        calc._check_security = lambda: calc.scores.update({"security": 20})
        calc._check_dependencies = lambda: calc.scores.update({"dependencies": 10})
        calc._check_complexity = lambda: calc.scores.update({"complexity": 10})

        report = calc.run()
        self.assertEqual(report["grade"], "A+")
        self.assertEqual(report["score"], 100)

        # Test lower grade
        calc = HealthCalculator(self.mock_project_dir)
        calc._check_tests = lambda: calc.scores.update({"tests": 20}) # Fail tests but maybe some points? Actually check logic
        # If tests fail score is 0 usually. Let's say tests passed but 0 coverage -> 20pts
        calc._check_lint = lambda: calc.scores.update({"lint": 10})
        calc._check_security = lambda: calc.scores.update({"security": 10})
        calc._check_dependencies = lambda: calc.scores.update({"dependencies": 5})
        calc._check_complexity = lambda: calc.scores.update({"complexity": 5})
        # Total: 50
        report = calc.run()
        self.assertEqual(report["grade"], "D")

if __name__ == '__main__':
    unittest.main()
