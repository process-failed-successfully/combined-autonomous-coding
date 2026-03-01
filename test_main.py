import argparse
from unittest.mock import patch
from pathlib import Path


def test_main():
    with patch('sys.exit') as mock_exit:
        with patch('shared.base64_lab.run_base64_lab_logic') as mock_logic:
            mock_logic.return_value = True
            from main import run_base64_lab
            run_base64_lab(argparse.Namespace())
            mock_exit.assert_called_once_with(0)


def test_mock_tui():
    with patch('sys.exit') as mock_exit:
        with patch('shared.tui.AgentTUI') as MockAgentTUI:
            from main import run_mock

            mock_app_instance = MockAgentTUI.return_value
            args = argparse.Namespace(action="tui", project_dir=Path("."))

            run_mock(args)

            MockAgentTUI.assert_called_once_with(project_dir=args.project_dir, start_tab="tab-mock-data")
            mock_app_instance.run.assert_called_once()
            mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    test_main()
    test_mock_tui()
    print("Main test passed")
