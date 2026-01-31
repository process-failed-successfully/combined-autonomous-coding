import unittest
from shared.logic_lab import LogicLabManager

class TestLogicLab(unittest.TestCase):
    def setUp(self):
        self.manager = LogicLabManager()

    def test_simple_and(self):
        res = self.manager.generate_truth_table("A and B")
        self.assertIsNone(res["error"])
        self.assertEqual(res["variables"], ["a", "b"])
        self.assertEqual(len(res["rows"]), 4)
        # Check specific row: T, T -> T
        row_tt = next(r for r in res["rows"] if r["values"]["a"] and r["values"]["b"])
        self.assertTrue(row_tt["result"])
        # Check T, F -> F
        row_tf = next(r for r in res["rows"] if r["values"]["a"] and not r["values"]["b"])
        self.assertFalse(row_tf["result"])

    def test_operators(self):
        # !A || B
        res = self.manager.generate_truth_table("!A || B")
        self.assertIsNone(res["error"])
        self.assertEqual(res["variables"], ["a", "b"])
        # F, F -> T (!F is T, T or F is T)
        row_ff = next(r for r in res["rows"] if not r["values"]["a"] and not r["values"]["b"])
        self.assertTrue(row_ff["result"])

    def test_xor(self):
        # A xor B
        res = self.manager.generate_truth_table("A xor B")
        self.assertIsNone(res["error"])
        # T, T -> F
        row_tt = next(r for r in res["rows"] if r["values"]["a"] and r["values"]["b"])
        self.assertFalse(row_tt["result"])
        # T, F -> T
        row_tf = next(r for r in res["rows"] if r["values"]["a"] and not r["values"]["b"])
        self.assertTrue(row_tf["result"])

    def test_empty(self):
        res = self.manager.generate_truth_table("")
        self.assertTrue(res["error"])

    def test_syntax_error(self):
        res = self.manager.generate_truth_table("A and")
        self.assertTrue(res["error"])

    def test_unsafe_input(self):
        res = self.manager.generate_truth_table("__import__('os')")
        self.assertTrue(res["error"])

if __name__ == "__main__":
    unittest.main()
