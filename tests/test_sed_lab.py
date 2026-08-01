import unittest
from shared.sed_lab import SedLabManager

class TestSedLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = SedLabManager()
        self.text_data = "apple 10\nbanana 20\ncherry 30\n"

    def test_evaluate_success(self):
        result = self.manager.evaluate(self.text_data, "s/apple/orange/")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "orange 10\nbanana 20\ncherry 30\n")

    def test_evaluate_delete(self):
        result = self.manager.evaluate(self.text_data, "/banana/d")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "apple 10\ncherry 30\n")

    def test_evaluate_empty_input_and_script(self):
        result = self.manager.evaluate("", "")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Empty input and script")

    def test_evaluate_empty_script(self):
        result = self.manager.evaluate(self.text_data, "")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Empty SED script provided")

    def test_evaluate_invalid_script(self):
        result = self.manager.evaluate(self.text_data, "s/apple/orange")
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("sed:", result["error"])
