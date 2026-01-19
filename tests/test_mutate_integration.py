import unittest
from unittest.mock import MagicMock, patch, mock_open
from shared.mutate import MutationTester
from pathlib import Path

class TestMutationIntegration(unittest.TestCase):
    @patch("shared.mutate.subprocess.run")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.write_text")
    def test_run_mutation(self, mock_write, mock_read, mock_run):
        mock_read.return_value = "x = a + b"
        mock_run.return_value.returncode = 0 # Tests pass

        tester = MutationTester(Path("."), Path("test.py"))

        # Suppress console output
        with patch("shared.mutate.console.print"):
            tester.run()

        # Verify it found mutation and applied it
        # + -> -
        # It should write mutated code
        # Note: ast.unparse might format differently, so we check substring or relaxed match if needed.
        # "x = a - b" is standard formatting.

        # Verify write calls
        # 1. Mutated code
        # 2. Original code (restore)

        writes = [args[0][0] for args in mock_write.call_args_list]
        self.assertTrue(any("x = a - b" in w for w in writes))
        self.assertTrue(any("x = a + b" in w for w in writes))

        # It should run tests
        # 1. Baseline
        # 2. Mutation
        self.assertEqual(mock_run.call_count, 2)

if __name__ == '__main__':
    unittest.main()
