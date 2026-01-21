import unittest
import tempfile
import shutil
from pathlib import Path
from shared.impact import ImpactAnalyzer

class TestImpactAnalyzerParallel(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Create 60 python files
        # file_0.py imports file_1
        # ...
        for i in range(60):
            p = self.project_dir / f"file_{i}.py"
            if i < 59:
                # We need to make sure it resolves correctly.
                # In build_graph, absolute imports are resolved.
                # "import file_1" -> file_1.py in root.
                content = f"import file_{i+1}\n"
            else:
                content = ""
            p.write_text(content)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_build_graph_parallel(self):
        analyzer = ImpactAnalyzer(self.project_dir)
        # Ensure we trigger parallel path
        # build_graph will populate files_map then check length
        analyzer.build_graph()

        self.assertGreaterEqual(len(analyzer.files_map), 50)

        # Check dependencies
        # file_0 -> file_1
        # Note: dependency values are relative paths strings in this implementation
        expected_dep = "file_1.py"
        self.assertIn(expected_dep, analyzer.dependencies["file_0.py"])

        # Check reverse dependencies
        # file_1 <- file_0
        self.assertIn("file_0.py", analyzer.reverse_dependencies[expected_dep])

    def test_build_graph_serial(self):
        # Setup fewer files to trigger serial path
        # 10 files
        for p in self.project_dir.glob("file_*.py"):
            p.unlink()

        for i in range(10):
            p = self.project_dir / f"file_{i}.py"
            if i < 9:
                content = f"import file_{i+1}\n"
            else:
                content = ""
            p.write_text(content)

        analyzer = ImpactAnalyzer(self.project_dir)
        analyzer.build_graph()

        self.assertLess(len(analyzer.files_map), 50)

        # Check dependencies
        expected_dep = "file_1.py"
        self.assertIn(expected_dep, analyzer.dependencies["file_0.py"])

if __name__ == "__main__":
    unittest.main()
