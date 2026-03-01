import argparse
from unittest.mock import patch
from shared.base64_lab import run_base64_lab_logic

def test_main():
    with patch('sys.exit') as mock_exit:
        with patch('shared.base64_lab.run_base64_lab_logic') as mock_logic:
            mock_logic.return_value = True
            from main import run_base64_lab
            run_base64_lab(argparse.Namespace())
            mock_exit.assert_called_once_with(0)

if __name__ == "__main__":
    test_main()
    print("Main test passed")
