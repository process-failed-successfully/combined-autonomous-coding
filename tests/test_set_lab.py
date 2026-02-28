import unittest
from unittest.mock import patch, MagicMock
import sys
from shared.set_lab import SetLabManager, run_set_lab_logic
import argparse

class TestSetLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = SetLabManager()

    def test_union(self):
        result = self.manager.process_sets(["a", "b"], ["b", "c"], "union")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], ["a", "b", "c"])

    def test_intersection(self):
        result = self.manager.process_sets(["a", "b"], ["b", "c"], "intersection")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], ["b"])

    def test_difference(self):
        result = self.manager.process_sets(["a", "b"], ["b", "c"], "difference")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], ["a"])

    def test_symmetric_difference(self):
        result = self.manager.process_sets(["a", "b"], ["b", "c"], "symmetric_difference")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], ["a", "c"])

    def test_subset(self):
        result = self.manager.process_sets(["a"], ["a", "b"], "subset")
        self.assertTrue(result["success"])
        self.assertTrue(result["is_boolean"])
        self.assertEqual(result["result"], ["True"])

    def test_superset(self):
        result = self.manager.process_sets(["a", "b"], ["a"], "superset")
        self.assertTrue(result["success"])
        self.assertTrue(result["is_boolean"])
        self.assertEqual(result["result"], ["True"])

    def test_ignore_case(self):
        result = self.manager.process_sets(["A", "b"], ["B", "c"], "intersection", ignore_case=True)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["result"]), 1)
        self.assertEqual(result["result"][0].lower(), "b")

    def test_trim_whitespace(self):
        result = self.manager.process_sets([" a ", "b"], ["b  ", "c"], "intersection", trim_whitespace=True)
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], ["b"])

class TestSetLabCli(unittest.TestCase):
    @patch("sys.stdout")
    def test_run_set_lab_logic(self, mock_stdout):
        args = argparse.Namespace(
            set1="a,b",
            set2="b,c",
            file1=None,
            file2=None,
            operation="union",
            ignore_case=False,
            trim_whitespace=False
        )
        try:
            run_set_lab_logic(args)
        except SystemExit:
            pass
