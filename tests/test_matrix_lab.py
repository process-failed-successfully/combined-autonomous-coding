import unittest
from shared.matrix_lab import MatrixLabManager

class TestMatrixLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = MatrixLabManager()

    def test_parse_matrix_json_style(self):
        text = "[[1, 2], [3, 4]]"
        expected = [[1.0, 2.0], [3.0, 4.0]]
        self.assertEqual(self.manager.parse_matrix(text), expected)

    def test_parse_matrix_text_style(self):
        text = """
        1 2
        3 4
        """
        expected = [[1.0, 2.0], [3.0, 4.0]]
        self.assertEqual(self.manager.parse_matrix(text), expected)

    def test_parse_matrix_comma_style(self):
        text = """
        1, 2
        3, 4
        """
        expected = [[1.0, 2.0], [3.0, 4.0]]
        self.assertEqual(self.manager.parse_matrix(text), expected)

    def test_parse_invalid_dimensions(self):
        text = "[[1, 2], [3]]"
        with self.assertRaises(ValueError):
            self.manager.parse_matrix(text)

    def test_add(self):
        A = [[1, 2], [3, 4]]
        B = [[5, 6], [7, 8]]
        expected = [[6, 8], [10, 12]]
        self.assertEqual(self.manager.add(A, B), expected)

    def test_add_mismatch(self):
        A = [[1, 2]]
        B = [[1, 2], [3, 4]]
        with self.assertRaises(ValueError):
            self.manager.add(A, B)

    def test_subtract(self):
        A = [[5, 6], [7, 8]]
        B = [[1, 2], [3, 4]]
        expected = [[4, 4], [4, 4]]
        self.assertEqual(self.manager.subtract(A, B), expected)

    def test_multiply(self):
        A = [[1, 2], [3, 4]]
        B = [[2, 0], [1, 2]]
        # 1*2 + 2*1 = 4
        # 1*0 + 2*2 = 4
        # 3*2 + 4*1 = 10
        # 3*0 + 4*2 = 8
        expected = [[4, 4], [10, 8]]
        self.assertEqual(self.manager.multiply(A, B), expected)

    def test_scalar_multiply(self):
        A = [[1, 2], [3, 4]]
        k = 2
        expected = [[2, 4], [6, 8]]
        self.assertEqual(self.manager.scalar_multiply(A, k), expected)

    def test_transpose(self):
        A = [[1, 2], [3, 4], [5, 6]]
        expected = [[1, 3, 5], [2, 4, 6]]
        self.assertEqual(self.manager.transpose(A), expected)

    def test_determinant(self):
        A = [[1, 2], [3, 4]]
        # 1*4 - 2*3 = -2
        self.assertEqual(self.manager.determinant(A), -2)

    def test_determinant_3x3(self):
        A = [[6, 1, 1], [4, -2, 5], [2, 8, 7]]
        # Det = 6(-14 - 40) - 1(28 - 10) + 1(32 - -4)
        # = 6(-54) - 18 + 36
        # = -324 - 18 + 36 = -306
        self.assertEqual(self.manager.determinant(A), -306)

if __name__ == '__main__':
    unittest.main()
