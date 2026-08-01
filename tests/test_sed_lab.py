import unittest
from shared.sed_lab import SedLabManager

class TestSedLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = SedLabManager()

    def test_evaluate_success(self):
        result = self.manager.evaluate("apple orange apple", "s/apple/banana/g")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "banana orange banana")

    def test_evaluate_invalid_script(self):
        result = self.manager.evaluate("test data", "s/test/data/x") # invalid flag x
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_evaluate_empty_input(self):
        result = self.manager.evaluate("", "")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Empty input and script")

    def test_evaluate_empty_script(self):
        result = self.manager.evaluate("data", "   ")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Empty SED script provided")

if __name__ == '__main__':
    unittest.main()
