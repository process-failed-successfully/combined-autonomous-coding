import pytest
from unittest.mock import patch, MagicMock


# Create a mock for AgentTUI to prevent actually trying to render in tests
mock_agent_tui = MagicMock()
mock_agent_tui.return_value.run = MagicMock()
mock_agent_tui.return_value.run_async = MagicMock()


@pytest.mark.asyncio
async def test_sql_lab_tui_launch():
    """Test that 'sql-lab tui' launches the TUI with tab-sql."""
    test_args = ["main.py", "sql-lab", "tui"]
    with patch('sys.argv', test_args):
        import main
        with patch('main.run_tui') as mock_run_tui:
            with patch('sys.exit'):
                try:
                    await main.main()
                except SystemExit:
                    pass
                mock_run_tui.assert_called_once()
                args, kwargs = mock_run_tui.call_args
                assert kwargs.get('start_tab') == 'tab-sql'


@pytest.mark.asyncio
async def test_dns_lab_tui_launch():
    """Test that 'dns-lab tui' launches the TUI with tab-dns."""
    test_args = ["main.py", "dns-lab", "tui"]
    with patch('sys.argv', test_args):
        import main
        with patch('main.run_tui') as mock_run_tui:
            with patch('sys.exit'):
                try:
                    await main.main()
                except SystemExit:
                    pass
                mock_run_tui.assert_called_once()
                args, kwargs = mock_run_tui.call_args
                assert kwargs.get('start_tab') == 'tab-dns'


@pytest.mark.asyncio
async def test_jwt_lab_tui_launch():
    """Test that 'jwt-lab tui' launches the TUI with tab-jwt."""
    test_args = ["main.py", "jwt-lab", "tui"]
    with patch('sys.argv', test_args):
        import main
        with patch('main.run_tui') as mock_run_tui:
            with patch('sys.exit'):
                try:
                    await main.main()
                except SystemExit:
                    pass
                mock_run_tui.assert_called_once()
                args, kwargs = mock_run_tui.call_args
                assert kwargs.get('start_tab') == 'tab-jwt'
