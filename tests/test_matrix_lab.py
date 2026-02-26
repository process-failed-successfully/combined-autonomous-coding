import unittest
from shared.matrix_lab import MatrixLabManager

class TestMatrixLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = MatrixLabManager()

    def test_create(self):
        matrix = self.manager.create(2, 3, 1.0)
        self.assertEqual(len(matrix), 2)
        self.assertEqual(len(matrix[0]), 3)
        self.assertEqual(matrix[0][0], 1.0)

    def test_create_identity(self):
        matrix = self.manager.create_identity(3)
        self.assertEqual(matrix, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])

    def test_transpose(self):
        matrix = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        transposed = self.manager.transpose(matrix)
        self.assertEqual(transposed, [[1.0, 3.0, 5.0], [2.0, 4.0, 6.0]])

    def test_add(self):
        m1 = [[1.0, 2.0], [3.0, 4.0]]
        m2 = [[5.0, 6.0], [7.0, 8.0]]
        result = self.manager.add(m1, m2)
        self.assertEqual(result, [[6.0, 8.0], [10.0, 12.0]])

    def test_subtract(self):
        m1 = [[5.0, 6.0], [7.0, 8.0]]
        m2 = [[1.0, 2.0], [3.0, 4.0]]
        result = self.manager.subtract(m1, m2)
        self.assertEqual(result, [[4.0, 4.0], [4.0, 4.0]])

    def test_multiply(self):
        m1 = [[1.0, 2.0], [3.0, 4.0]]
        m2 = [[2.0, 0.0], [1.0, 2.0]]
        # 1*2 + 2*1 = 4, 1*0 + 2*2 = 4
        # 3*2 + 4*1 = 10, 3*0 + 4*2 = 8
        result = self.manager.multiply(m1, m2)
        self.assertEqual(result, [[4.0, 4.0], [10.0, 8.0]])

    def test_scale(self):
        matrix = [[1.0, 2.0], [3.0, 4.0]]
        result = self.manager.scale(matrix, 2.0)
        self.assertEqual(result, [[2.0, 4.0], [6.0, 8.0]])

    def test_determinant(self):
        # 2x2
        m2 = [[1.0, 2.0], [3.0, 4.0]] # 1*4 - 2*3 = -2
        self.assertAlmostEqual(self.manager.determinant(m2), -2.0)

        # 3x3
        m3 = [[6.0, 1.0, 1.0], [4.0, -2.0, 5.0], [2.0, 8.0, 7.0]]
        # det = 6*(-14 - 40) - 1*(28 - 10) + 1*(32 - -4)
        # = 6*(-54) - 18 + 36 = -324 - 18 + 36 = -306
        self.assertAlmostEqual(self.manager.determinant(m3), -306.0)

    def test_format_matrix(self):
        matrix = [[1.0, 2.0], [3.0, 4.0]]
        formatted = self.manager.format_matrix(matrix)
        self.assertIn("[ 1 2 ]", formatted)
        self.assertIn("[ 3 4 ]", formatted)

if __name__ == '__main__':
    unittest.main()
