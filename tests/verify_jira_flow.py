
import asyncio
import logging
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock dependencies before importing our code
import sys
from unittest.mock import MagicMock
sys.modules['shared.telemetry'] = MagicMock()
sys.modules['shared.notifications'] = MagicMock()
sys.modules['jira'] = MagicMock()
sys.modules['requests'] = MagicMock()

from shared.config import Config, JiraConfig
from shared.workflow import complete_jira_ticket

async def test_complete_jira_ticket_success():
    """Test that completion flow handles git and jira calls correctly."""
    project_dir = Path("./test_project_verify")
    project_dir.mkdir(exist_ok=True)
    
    jira_cfg = JiraConfig(url="http://test", email="test@test", token="token")
    config = Config(
        project_dir=project_dir,
        jira=jira_cfg,
        jira_ticket_key="PROJ-123"
    )
    
    # Mock subprocess.run for git calls
    with patch("subprocess.run") as mock_run, \
         patch("shared.workflow.push_branch") as mock_push, \
         patch("shared.workflow.JiraClient") as mock_jira_client, \
         patch("shared.workflow.GitHubClient") as mock_gh_client:
        
        mock_push.return_value = True
        
        # Setup GitHub collaborator info
        mock_gh = MagicMock()
        mock_gh_client.return_value = mock_gh
        mock_gh.get_repo_info_from_remote.return_value = ("owner", "repo")
        mock_gh.create_pr.return_value = "https://github.com/PR-123"
        
        # Setup git remote/branch mocks
        mock_run_result = MagicMock()
        mock_run_result.stdout = "https://github.com/owner/repo.git\n"
        mock_run_result_branch = MagicMock()
        mock_run_result_branch.stdout = "agent/feature\n"
        mock_run.side_effect = [mock_run_result, mock_run_result_branch]
        
        # Setup Jira client
        mock_jira = MagicMock()
        mock_jira_client.return_value = mock_jira
        
        success = await complete_jira_ticket(config)
        
        assert success is True
        mock_push.assert_called_once()
        mock_gh.create_pr.assert_called_once()
        mock_jira.transition_issue.assert_called_once_with("PROJ-123", "Code Review")
        mock_jira.add_comment.assert_called_once()
        print("Verification Test Success: complete_jira_ticket flows correctly.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_complete_jira_ticket_success())
