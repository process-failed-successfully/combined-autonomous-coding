from typing import List, Union, Optional

class MatrixLabManager:
    """
    Manager for Matrix Laboratory operations.
    Handles basic matrix arithmetic and transformations.
    """

    def create(self, rows: int, cols: int, value: float = 0.0) -> List[List[float]]:
        """Creates a matrix of given size initialized with value."""
        return [[float(value) for _ in range(cols)] for _ in range(rows)]

    def create_identity(self, size: int) -> List[List[float]]:
        """Creates an identity matrix of size x size."""
        matrix = self.create(size, size, 0.0)
        for i in range(size):
            matrix[i][i] = 1.0
        return matrix

    def transpose(self, matrix: List[List[float]]) -> List[List[float]]:
        """Returns the transpose of the matrix."""
        if not matrix:
            return []
        rows = len(matrix)
        cols = len(matrix[0])
        return [[matrix[r][c] for r in range(rows)] for c in range(cols)]

    def add(self, matrix1: List[List[float]], matrix2: List[List[float]]) -> List[List[float]]:
        """Adds two matrices."""
        if len(matrix1) != len(matrix2) or len(matrix1[0]) != len(matrix2[0]):
            raise ValueError("Matrices must have the same dimensions for addition.")

        rows = len(matrix1)
        cols = len(matrix1[0])
        return [[matrix1[r][c] + matrix2[r][c] for c in range(cols)] for r in range(rows)]

    def subtract(self, matrix1: List[List[float]], matrix2: List[List[float]]) -> List[List[float]]:
        """Subtracts matrix2 from matrix1."""
        if len(matrix1) != len(matrix2) or len(matrix1[0]) != len(matrix2[0]):
            raise ValueError("Matrices must have the same dimensions for subtraction.")

        rows = len(matrix1)
        cols = len(matrix1[0])
        return [[matrix1[r][c] - matrix2[r][c] for c in range(cols)] for r in range(rows)]

    def multiply(self, matrix1: List[List[float]], matrix2: List[List[float]]) -> List[List[float]]:
        """Multiplies two matrices (matrix product)."""
        rows1 = len(matrix1)
        cols1 = len(matrix1[0])
        rows2 = len(matrix2)
        cols2 = len(matrix2[0])

        if cols1 != rows2:
            raise ValueError(f"Incompatible dimensions for multiplication: {rows1}x{cols1} and {rows2}x{cols2}")

        result = self.create(rows1, cols2, 0.0)
        for i in range(rows1):
            for j in range(cols2):
                for k in range(cols1):
                    result[i][j] += matrix1[i][k] * matrix2[k][j]
        return result

    def scale(self, matrix: List[List[float]], scalar: float) -> List[List[float]]:
        """Multiplies a matrix by a scalar."""
        rows = len(matrix)
        cols = len(matrix[0])
        return [[matrix[r][c] * scalar for c in range(cols)] for r in range(rows)]

    def determinant(self, matrix: List[List[float]]) -> float:
        """Calculates the determinant of a square matrix."""
        rows = len(matrix)
        cols = len(matrix[0])

        if rows != cols:
            raise ValueError("Determinant is only defined for square matrices.")

        if rows == 1:
            return matrix[0][0]

        if rows == 2:
            return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]

        det = 0.0
        for c in range(cols):
            sub_matrix = [row[:c] + row[c+1:] for row in matrix[1:]]
            sign = 1 if c % 2 == 0 else -1
            det += sign * matrix[0][c] * self.determinant(sub_matrix)

        return det

    def format_matrix(self, matrix: List[List[float]]) -> str:
        """Formats the matrix as a string for display."""
        if not matrix:
            return "[]"

        # Determine max width for alignment
        max_len = 0
        for row in matrix:
            for val in row:
                s = f"{val:.2f}"
                if s.endswith(".00"):
                    s = f"{int(val)}"
                max_len = max(max_len, len(s))

        lines = []
        for row in matrix:
            line_parts = []
            for val in row:
                s = f"{val:.2f}"
                if s.endswith(".00"):
                    s = f"{int(val)}"
                line_parts.append(f"{s:>{max_len}}")
            lines.append("[ " + " ".join(line_parts) + " ]")
        return "\n".join(lines)
