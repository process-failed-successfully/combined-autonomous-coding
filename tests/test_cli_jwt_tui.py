import pytest
from unittest.mock import patch, MagicMock
import sys

# Must import main module directly to test its execution path
import main

@pytest.mark.asyncio
async def test_jwt_lab_tui_command():
    test_args = ["main.py", "jwt-lab", "tui"]

    with patch("sys.argv", test_args):
        with patch("shared.tui.AgentTUI") as mock_tui:
            # sys.exit inside run_jwt_lab
            with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                mock_app_instance = mock_tui.return_value
                mock_app_instance.run_async = MagicMock()

                with pytest.raises(SystemExit):
                    await main.main()

                mock_tui.assert_called_once()
                kwargs = mock_tui.call_args.kwargs
                assert kwargs.get("start_tab") == "tab-jwt"
