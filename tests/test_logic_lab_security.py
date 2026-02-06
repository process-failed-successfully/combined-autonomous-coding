from shared.logic_lab import LogicLabManager
import unittest

class TestLogicLab(unittest.TestCase):
    def test_basic_expression(self):
        manager = LogicLabManager()
        result = manager.generate_truth_table("A and B")
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["rows"]), 4)

        # Check specific row
        # A=True, B=True -> True
        row_tt = next(r for r in result["rows"] if r["values"]["a"] and r["values"]["b"])
        self.assertTrue(row_tt["result"])

        # A=True, B=False -> False
        row_tf = next(r for r in result["rows"] if r["values"]["a"] and not r["values"]["b"])
        self.assertFalse(row_tf["result"])

    def test_unsafe_expression(self):
        manager = LogicLabManager()
        # This currently returns syntax error because 'import' is a statement
        result = manager.generate_truth_table("import os")
        # Accept either explicit unsafe message or syntax error (which implies it failed to parse as expression)
        self.assertTrue("Syntax Error" in result["error"] or "Unsupported" in result["error"])

        # Try a valid expression but unsupported node (e.g. list comprehension if it parses)
        # [x for x in []]
        # logic_lab replaces '[' with nothing? no.
        result = manager.generate_truth_table("[1, 2]")
        # This parses as List, which is not in whitelist
        self.assertTrue("Unsupported" in result["error"])

    def test_complex_expression(self):
        manager = LogicLabManager()
        result = manager.generate_truth_table("(A or B) and not C")
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["rows"]), 8)

    def test_xor_expression(self):
        manager = LogicLabManager()
        result = manager.generate_truth_table("A xor B")
        self.assertIsNone(result["error"])

        # T xor F -> T
        row_tf = next(r for r in result["rows"] if r["values"]["a"] and not r["values"]["b"])
        self.assertTrue(row_tf["result"])

        # T xor T -> F
        row_tt = next(r for r in result["rows"] if r["values"]["a"] and r["values"]["b"])
        self.assertFalse(row_tt["result"])

if __name__ == "__main__":
    unittest.main()
