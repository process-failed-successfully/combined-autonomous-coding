import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from shared.cli import run_do_logic


@pytest.mark.asyncio
@patch("shared.cli.subprocess.run")
@patch("builtins.input", side_effect=['e', 'n'])
@patch("shared.cli.GeminiAgent")
async def test_run_do_logic_explain_then_no(mock_agent_class, mock_input, mock_subprocess_run):
    """
    Tests the interactive 'explain' feature in the 'do' command.
    Mocks user input: first 'e' (explain), then 'n' (do not run).
    Verifies that the agent is asked to explain the command, and the command is not executed.
    """
    project_dir = Path(".")

    # Mock the agent instance and its run_agent_session method
    mock_agent_instance = MagicMock()
    mock_agent_class.return_value = mock_agent_instance

    # We need an async mock for run_agent_session
    mock_agent_instance.run_agent_session = AsyncMock(side_effect=[
        # 1. First call is generating the command
        ("done", "ls -la", []),
        # 2. Second call is generating the explanation (triggered by 'e')
        ("done", "This lists all files in long format.", [])
    ])

    result = await run_do_logic(
        instruction="list files",
        project_dir=project_dir,
        agent_type="gemini",
        yes=False
    )

    # The function should return True (completed interactive loop gracefully without crashing)
    # The final action was 'n', meaning it didn't run, but that's an abort which returns True in current logic.
    assert result is True

    # Verify agent was called twice: once for command, once for explanation
    assert mock_agent_instance.run_agent_session.call_count == 2

    # Verify subprocess.run was NEVER called because we answered 'n'
    mock_subprocess_run.assert_not_called()


@pytest.mark.asyncio
@patch("shared.cli.subprocess.run")
@patch("builtins.input", side_effect=['e', 'y'])
@patch("shared.cli.GeminiAgent")
async def test_run_do_logic_explain_then_yes(mock_agent_class, mock_input, mock_subprocess_run):
    """
    Tests the interactive 'explain' feature in the 'do' command.
    Mocks user input: first 'e' (explain), then 'y' (run).
    Verifies that the command IS executed after explanation.
    """
    project_dir = Path(".")

    mock_agent_instance = MagicMock()
    mock_agent_class.return_value = mock_agent_instance

    mock_agent_instance.run_agent_session = AsyncMock(side_effect=[
        # 1. Generate command
        ("done", "echo hello", []),
        # 2. Generate explanation
        ("done", "It prints hello", [])
    ])

    # Mock subprocess.run to return success
    mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="hello\n", stderr="")

    result = await run_do_logic(
        instruction="say hello",
        project_dir=project_dir,
        agent_type="gemini",
        yes=False
    )

    assert result is True
    assert mock_agent_instance.run_agent_session.call_count == 2
    mock_subprocess_run.assert_called_once()
