import ast
from typing import Any, List, Sequence, Union


Matrix = List[List[Union[int, float]]]
InputMatrix = Sequence[Sequence[Union[int, float]]]


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
                pass  # Fallback to text parsing

        # Text parsing
        rows: Matrix = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            # Split by comma or space
            try:
                # Replace commas with spaces to handle "1, 2" format
                parts = line.replace(",", " ").split()
                row: List[Union[int, float]] = [float(p) for p in parts]
                rows.append(row)
            except ValueError:
                raise ValueError(f"Invalid matrix format at line: {line}")

        if self._validate_matrix(rows):
            return rows
        raise ValueError("Invalid matrix dimensions (inconsistent row lengths).")

    def _validate_matrix(self, matrix: Any) -> bool:
        if not isinstance(matrix, list):
            return False
        if not matrix:
            return True
        if not isinstance(matrix[0], list):
            return False

        row_len = len(matrix[0])
        for row in matrix:
            if not isinstance(row, list) or len(row) != row_len:
                return False
            # Check elements are numbers
            for x in row:
                if not isinstance(x, (int, float)):
                    return False
        return True

    def add(self, A: InputMatrix, B: InputMatrix) -> Matrix:
        if len(A) != len(B) or len(A[0]) != len(B[0]):
            raise ValueError("Matrices must have the same dimensions for addition.")

        result: Matrix = []
        for i in range(len(A)):
            row: List[Union[int, float]] = []
            for j in range(len(A[0])):
                row.append(A[i][j] + B[i][j])
            result.append(row)
        return result

    def subtract(self, A: InputMatrix, B: InputMatrix) -> Matrix:
        if len(A) != len(B) or len(A[0]) != len(B[0]):
            raise ValueError("Matrices must have the same dimensions for subtraction.")

        result: Matrix = []
        for i in range(len(A)):
            row: List[Union[int, float]] = []
            for j in range(len(A[0])):
                row.append(A[i][j] - B[i][j])
            result.append(row)
        return result

    def multiply(self, A: InputMatrix, B: InputMatrix) -> Matrix:
        """Matrix multiplication (dot product)."""
        rows_A = len(A)
        cols_A = len(A[0])
        rows_B = len(B)
        cols_B = len(B[0])

        if cols_A != rows_B:
            raise ValueError(f"Incompatible dimensions for multiplication: {rows_A}x{cols_A} and {rows_B}x{cols_B}")

        # Initialize result matrix with zeros
        result: Matrix = [[0.0 for _ in range(cols_B)] for _ in range(rows_A)]

        for i in range(rows_A):
            for j in range(cols_B):
                for k in range(cols_A):
                    # We cast to float because result is initialized as float
                    val = result[i][j]
                    result[i][j] = val + (A[i][k] * B[k][j])
        return result

    def scalar_multiply(self, A: InputMatrix, k: float) -> Matrix:
        result: Matrix = []
        for i in range(len(A)):
            row = [x * k for x in A[i]]
            result.append(row)
        return result

    def transpose(self, A: InputMatrix) -> Matrix:
        if not A:
            return []
        return [list(x) for x in zip(*A)]

    def determinant(self, A: InputMatrix) -> float:
        if len(A) != len(A[0]):
            raise ValueError("Determinant requires a square matrix.")

        n = len(A)
        if n == 1:
            return A[0][0]
        if n == 2:
            return A[0][0] * A[1][1] - A[0][1] * A[1][0]

        # Recursive expansion (not efficient for large matrices but fine for a lab)
        det = 0.0
        for c in range(n):
            det += ((-1) ** c) * A[0][c] * self.determinant(self._minor(A, 0, c))
        return det

    def _minor(self, A: InputMatrix, i: int, j: int) -> Matrix:
        return [list(row[:j]) + list(row[j + 1:]) for k, row in enumerate(A) if k != i]


def run_matrix_lab_logic(args):
    """CLI logic for Matrix Lab."""
    # This is mainly for CLI usage if we added it, but mostly we use TUI.
    # We can implement basic CLI operations here.
    # We expect args to have operation and maybe matrix strings?
    # For now, just placeholder or simple test.
    print("Matrix Lab Logic Loaded.")
