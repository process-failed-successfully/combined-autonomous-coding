
from shared.risk_analysis import RiskAnalyzer, _run_risk_logic
import unittest
from unittest.mock import patch
from pathlib import Path
import sys
import io

# Ensure shared modules can be imported
sys.path.append(str(Path.cwd()))


class TestRiskAnalyzer(unittest.TestCase):
    @patch('shared.risk_analysis.analyze_project_complexity')
    @patch('shared.risk_analysis.get_git_hotspots')
    def test_analyze(self, mock_get_git_hotspots, mock_analyze_project_complexity):
        # Setup mocks
        mock_analyze_project_complexity.return_value = [
            {'file': 'a.py', 'complexity': 10},
            {'file': 'a.py', 'complexity': 5},  # Total 15
            {'file': 'b.py', 'complexity': 2},
            {'file': 'c.py', 'complexity': 0},
        ]

        # [(file, count)]
        mock_get_git_hotspots.return_value = [
            ('a.py', 10),
            ('b.py', 5),
            ('c.py', 1),
            ('d.py', 20),  # No complexity data (non-python or simple)
        ]

        analyzer = RiskAnalyzer(Path('.'))
        results = analyzer.analyze(limit=10)

        # Expected:
        # a.py: Comp=15, Churn=10 -> Score=150
        # b.py: Comp=2, Churn=5 -> Score=10
        # c.py: Comp=0, Churn=1 -> Score=0 (Should be excluded)
        # d.py: Comp=0 (default), Churn=20 -> Score=0 (Excluded)

        self.assertEqual(len(results), 2)

        # Check sorting (descending score)
        self.assertEqual(results[0]['file'], 'a.py')
        self.assertEqual(results[0]['score'], 150)
        self.assertEqual(results[0]['complexity'], 15)
        self.assertEqual(results[0]['churn'], 10)

        self.assertEqual(results[1]['file'], 'b.py')
        self.assertEqual(results[1]['score'], 10)

    @patch('shared.risk_analysis.analyze_project_complexity')
    @patch('shared.risk_analysis.get_git_hotspots')
    def test_run_risk_logic_output(self, mock_get_git_hotspots, mock_analyze_project_complexity):
        mock_analyze_project_complexity.return_value = [{'file': 'a.py', 'complexity': 10}]
        mock_get_git_hotspots.return_value = [('a.py', 5)]

        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            _run_risk_logic(Path('.'))
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("Risk Analysis (Hotspots)", output)
        self.assertIn("a.py", output)
        self.assertIn("50", output)  # Score 10*5


if __name__ == '__main__':
    unittest.main()
