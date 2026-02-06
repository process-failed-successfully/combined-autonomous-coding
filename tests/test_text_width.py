import unittest
from shared.text_width import calculate_text_width

class TestTextWidth(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(calculate_text_width(""), 0)
        self.assertEqual(calculate_text_width(None), 0)

    def test_single_chars(self):
        self.assertEqual(calculate_text_width("i"), 3)
        self.assertEqual(calculate_text_width("M"), 10)
        self.assertEqual(calculate_text_width(" "), 4)

    def test_variable_width(self):
        # "iii" (3*3=9) vs "MMM" (3*10=30)
        width_i = calculate_text_width("iii")
        width_m = calculate_text_width("MMM")
        self.assertLess(width_i, width_m)
        self.assertEqual(width_i, 9)
        self.assertEqual(width_m, 30)

    def test_unknown_char(self):
        # Default width is 7
        self.assertEqual(calculate_text_width("€"), 7)

    def test_mixed_string(self):
        # "Test" -> T(7) + e(7) + s(6) + t(4) = 24
        self.assertEqual(calculate_text_width("Test"), 24)

if __name__ == '__main__':
    unittest.main()
