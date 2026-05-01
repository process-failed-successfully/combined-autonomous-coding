import pytest
import sys
import argparse
from io import StringIO
from unittest.mock import patch

pytest.importorskip("argon2")

from shared.argon2_lab import run_argon2_lab_logic

class TestArgon2Cli:
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_hash(self, mock_stdout):
        args = argparse.Namespace(
            action="hash",
            password="testpassword",
            time_cost=2,
            memory_cost=10240,
            parallelism=2,
            hash_len=16
        )

        result = run_argon2_lab_logic(args)
        assert result is True
        output = mock_stdout.getvalue().strip()
        assert output.startswith("$argon2id$v=19$m=10240,t=2,p=2$")

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_verify_success(self, mock_stdout):
        # Generate a real hash first
        args_hash = argparse.Namespace(
            action="hash",
            password="testpassword",
            time_cost=2,
            memory_cost=10240,
            parallelism=2,
            hash_len=16
        )
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout_hash:
            run_argon2_lab_logic(args_hash)
            hash_str = mock_stdout_hash.getvalue().strip()

        # Verify it
        args_verify = argparse.Namespace(
            action="verify",
            password="testpassword",
            hash=hash_str
        )
        result = run_argon2_lab_logic(args_verify)
        assert result is True
        output = mock_stdout.getvalue().strip()
        assert "✅ Password is valid." in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_verify_failure(self, mock_stdout):
        # We need a valid argon2 hash to avoid exceptions during verify
        # E.g. testpassword
        hash_str = "$argon2id$v=19$m=10240,t=2,p=2$HkP9rQj/yF5z2/U9qL9Bjw$fB4r5bHq2p+rQ+9uXqY"

        args = argparse.Namespace(
            action="verify",
            password="wrongpassword",
            hash=hash_str
        )

        result = run_argon2_lab_logic(args)
        assert result is False
        output = mock_stdout.getvalue().strip()
        assert "❌ Invalid password." in output
