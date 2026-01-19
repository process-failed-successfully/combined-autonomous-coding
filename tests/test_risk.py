import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import shutil
import xml.etree.ElementTree as ET
from shared.risk_analysis import RiskAnalyzer

class TestRiskAnalyzer(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.xml_path = self.test_dir / "coverage.xml"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_dummy_coverage_xml(self, content):
        with open(self.xml_path, 'w') as f:
            f.write(content)

    def test_load_coverage_success(self):
        xml_content = """
        <coverage>
            <packages>
                <package>
                    <classes>
                        <class filename="test_file.py">
                            <lines>
                                <line number="1" hits="1"/>
                                <line number="5" hits="0"/>
                            </lines>
                        </class>
                    </classes>
                </package>
            </packages>
        </coverage>
        """
        self.create_dummy_coverage_xml(xml_content)
        analyzer = RiskAnalyzer(self.test_dir, self.xml_path)
        self.assertTrue(analyzer.load_coverage())
        self.assertIn("test_file.py", analyzer.coverage_data)
        self.assertEqual(analyzer.coverage_data["test_file.py"][1], 1)
        self.assertEqual(analyzer.coverage_data["test_file.py"][5], 0)

    def test_is_line_covered(self):
        xml_content = """
        <coverage>
            <packages>
                <package>
                    <classes>
                        <class filename="foo/bar.py">
                            <lines>
                                <line number="10" hits="1"/>
                                <line number="20" hits="0"/>
                            </lines>
                        </class>
                    </classes>
                </package>
            </packages>
        </coverage>
        """
        self.create_dummy_coverage_xml(xml_content)
        analyzer = RiskAnalyzer(self.test_dir, self.xml_path)
        analyzer.load_coverage()

        # Exact match
        self.assertTrue(analyzer.is_line_covered("foo/bar.py", 10))
        self.assertFalse(analyzer.is_line_covered("foo/bar.py", 20))
        self.assertFalse(analyzer.is_line_covered("foo/bar.py", 99))

        # Fuzzy/Suffix match (often coverage XML has relative paths differently than complexity analysis)
        self.assertTrue(analyzer.is_line_covered("/abs/path/to/foo/bar.py", 10))

    @patch("shared.risk_analysis.analyze_project_complexity")
    def test_calculate_risk(self, mock_complexity):
        # Setup Complexity Data
        mock_complexity.return_value = [
            {"file": "main.py", "function": "complex_func", "complexity": 20, "lineno": 10},
            {"file": "utils.py", "function": "simple_func", "complexity": 1, "lineno": 5},
            {"file": "utils.py", "function": "covered_complex_func", "complexity": 15, "lineno": 50},
        ]

        # Setup Coverage Data
        # main.py:10 -> NOT Covered (hits=0)
        # utils.py:5 -> Covered (hits=1)
        # utils.py:50 -> Covered (hits=1)
        xml_content = """
        <coverage>
            <packages>
                <package>
                    <classes>
                        <class filename="main.py">
                            <lines>
                                <line number="10" hits="0"/>
                            </lines>
                        </class>
                        <class filename="utils.py">
                            <lines>
                                <line number="5" hits="1"/>
                                <line number="50" hits="1"/>
                            </lines>
                        </class>
                    </classes>
                </package>
            </packages>
        </coverage>
        """
        self.create_dummy_coverage_xml(xml_content)
        analyzer = RiskAnalyzer(self.test_dir, self.xml_path)
        analyzer.load_coverage()

        results = analyzer.calculate_risk()

        # complex_func: 20 * 1.0 = 20.0
        # covered_complex_func: 15 * 0.1 = 1.5
        # simple_func: 1 * 0.1 = 0.1

        self.assertEqual(len(results), 3)

        res_complex = next(r for r in results if r["function"] == "complex_func")
        self.assertAlmostEqual(res_complex["risk_score"], 20.0)

        res_covered = next(r for r in results if r["function"] == "covered_complex_func")
        self.assertAlmostEqual(res_covered["risk_score"], 1.5)

        res_simple = next(r for r in results if r["function"] == "simple_func")
        self.assertAlmostEqual(res_simple["risk_score"], 0.1)

if __name__ == "__main__":
    unittest.main()
