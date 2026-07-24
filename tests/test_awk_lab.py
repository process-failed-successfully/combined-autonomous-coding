import unittest
from shared.awk_lab import AwkLabManager

class TestAwkLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = AwkLabManager()
        self.text_data = "apple 10\nbanana 20\ncherry 30\n"

    def test_evaluate_success(self):
        result = self.manager.evaluate(self.text_data, "{print $2}")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "10\n20\n30\n")

    def test_evaluate_sum(self):
        result = self.manager.evaluate(self.text_data, "{sum += $2} END {print sum}")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "60\n")

    def test_evaluate_filter(self):
        result = self.manager.evaluate(self.text_data, "$2 > 15 {print $1}")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "banana\ncherry\n")

    def test_evaluate_empty_input_and_script(self):
        result = self.manager.evaluate("", "")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Empty input and script")

    def test_evaluate_empty_script(self):
        result = self.manager.evaluate(self.text_data, "")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Empty AWK script provided")

    def test_evaluate_invalid_script(self):
        result = self.manager.evaluate(self.text_data, "{print $2")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("awk:", result["error"])
