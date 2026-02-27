import ast
from typing import List, Union

Matrix = List[List[float]]

class MatrixLabManager:
    """
    Manages Matrix arithmetic operations.
    """

    def parse_matrix(self, text: str) -> Matrix:
        """
        Parses a matrix from a string.
        Supported formats:
        - JSON-like: [[1, 2], [3, 4]]
        - Space/newline separated:
          1 2
          3 4
        """
        text = text.strip()
        if not text:
            return []

        # Try evaluating as list of lists
        if text.startswith("["):
            try:
                # Use ast.literal_eval for safe evaluation
                matrix = ast.literal_eval(text)
                if self._validate_matrix(matrix):
                    return matrix
            except (ValueError, SyntaxError):
                pass # Fallback to text parsing

        # Text parsing
        rows = []
        for line in text.splitlines():
            line = line.strip()
            if not line: continue
            # Split by comma or space
            try:
                # Replace commas with spaces to handle "1, 2" format
                parts = line.replace(",", " ").split()
                row = [float(p) for p in parts]
                rows.append(row)
            except ValueError:
                raise ValueError(f"Invalid matrix format at line: {line}")

        if self._validate_matrix(rows):
            return rows
        raise ValueError("Invalid matrix dimensions (inconsistent row lengths).")

    def _validate_matrix(self, matrix: list) -> bool:
        if not isinstance(matrix, list): return False
        if not matrix: return True
        if not isinstance(matrix[0], list): return False

        row_len = len(matrix[0])
        for row in matrix:
            if not isinstance(row, list) or len(row) != row_len:
                return False
            # Check elements are numbers
            for x in row:
                if not isinstance(x, (int, float)):
                    return False
        return True

    def add(self, A: Matrix, B: Matrix) -> Matrix:
        if len(A) != len(B) or len(A[0]) != len(B[0]):
            raise ValueError("Matrices must have the same dimensions for addition.")

        result = []
        for i in range(len(A)):
            row = []
            for j in range(len(A[0])):
                row.append(A[i][j] + B[i][j])
            result.append(row)
        return result

    def subtract(self, A: Matrix, B: Matrix) -> Matrix:
        if len(A) != len(B) or len(A[0]) != len(B[0]):
            raise ValueError("Matrices must have the same dimensions for subtraction.")

        result = []
        for i in range(len(A)):
            row = []
            for j in range(len(A[0])):
                row.append(A[i][j] - B[i][j])
            result.append(row)
        return result

    def multiply(self, A: Matrix, B: Matrix) -> Matrix:
        """Matrix multiplication (dot product)."""
        rows_A = len(A)
        cols_A = len(A[0])
        rows_B = len(B)
        cols_B = len(B[0])

        if cols_A != rows_B:
            raise ValueError(f"Incompatible dimensions for multiplication: {rows_A}x{cols_A} and {rows_B}x{cols_B}")

        # Initialize result matrix with zeros
        result = [[0.0 for _ in range(cols_B)] for _ in range(rows_A)]

        for i in range(rows_A):
            for j in range(cols_B):
                for k in range(cols_A):
                    result[i][j] += A[i][k] * B[k][j]
        return result

    def scalar_multiply(self, A: Matrix, k: float) -> Matrix:
        result = []
        for i in range(len(A)):
            row = [x * k for x in A[i]]
            result.append(row)
        return result

    def transpose(self, A: Matrix) -> Matrix:
        if not A: return []
        return [list(x) for x in zip(*A)]

    def determinant(self, A: Matrix) -> float:
        if len(A) != len(A[0]):
            raise ValueError("Determinant requires a square matrix.")

        n = len(A)
        if n == 1:
            return A[0][0]
        if n == 2:
            return A[0][0]*A[1][1] - A[0][1]*A[1][0]

        # Recursive expansion (not efficient for large matrices but fine for a lab)
        det = 0
        for c in range(n):
            det += ((-1) ** c) * A[0][c] * self.determinant(self._minor(A, 0, c))
        return det

    def _minor(self, A: Matrix, i: int, j: int) -> Matrix:
        return [row[:j] + row[j+1:] for k, row in enumerate(A) if k != i]

def run_matrix_lab_logic(args):
    """CLI logic for Matrix Lab."""
    # This is mainly for CLI usage if we added it, but mostly we use TUI.
    # We can implement basic CLI operations here.
    import sys

    manager = MatrixLabManager()

    # We expect args to have operation and maybe matrix strings?
    # For now, just placeholder or simple test.
    print("Matrix Lab Logic Loaded.")
