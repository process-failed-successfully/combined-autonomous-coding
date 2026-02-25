import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.test_lab import TestLabManager

class TestTestLabManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = TestLabManager(self.project_dir)

    @patch("subprocess.run")
    def test_collect_tests_success(self, mock_run):
        # Mock successful pytest --collect-only output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="tests/test_foo.py::test_bar\ntests/test_foo.py::TestClass::test_baz\n",
            stderr=""
        )

        tree = self.manager.collect_tests()

        # Verify tree structure
        self.assertEqual(tree["name"], "root")
        self.assertEqual(len(tree["children"]), 1)

        # tests dir
        tests_node = tree["children"][0]
        self.assertEqual(tests_node["name"], "tests")
        self.assertEqual(tests_node["type"], "directory")
        self.assertEqual(len(tests_node["children"]), 1)

        # test_foo.py
        file_node = tests_node["children"][0]
        self.assertEqual(file_node["name"], "test_foo.py")
        self.assertEqual(file_node["type"], "file")
        self.assertEqual(file_node["id"], "tests/test_foo.py")
        self.assertEqual(len(file_node["children"]), 2)

        # test_bar
        test_bar = file_node["children"][0]
        self.assertEqual(test_bar["name"], "test_bar")
        self.assertEqual(test_bar["type"], "test")
        self.assertEqual(test_bar["id"], "tests/test_foo.py::test_bar")

        # TestClass
        test_class = file_node["children"][1]
        self.assertEqual(test_class["name"], "TestClass")
        self.assertEqual(test_class["type"], "suite")

        # test_baz inside TestClass
        test_baz = test_class["children"][0]
        self.assertEqual(test_baz["name"], "test_baz")
        self.assertEqual(test_baz["type"], "test")
        self.assertEqual(test_baz["id"], "tests/test_foo.py::TestClass::test_baz")

    @patch("subprocess.run")
    def test_collect_tests_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Collection failed"
        )

        result = self.manager.collect_tests()
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Collection failed")

    @patch("subprocess.run")
    def test_run_tests_specific(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="1 passed",
            stderr=""
        )

        node_id = "tests/test_foo.py::test_bar"
        result = self.manager.run_tests(node_id)

        self.assertTrue(result["success"])
        self.assertEqual(result["output"], "1 passed")

        # Check if pytest called with node_id
        args, _ = mock_run.call_args
        command = args[0]
        self.assertIn(node_id, command)
        self.assertIn("-v", command)

    @patch("subprocess.run")
    def test_run_tests_all(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="10 passed",
            stderr=""
        )

        result = self.manager.run_tests()

        self.assertTrue(result["success"])

        # Check command structure
        args, _ = mock_run.call_args
        command = args[0]
        # Should not contain any specific node path, just flags
        self.assertNotIn("::", str(command))

if __name__ == "__main__":
    unittest.main()
