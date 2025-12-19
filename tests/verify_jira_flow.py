
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
from shared.utils import sanitize_url
from shared.github_client import GitHubClient

def test_sanitize_url():
    """Test that tokens are masked in URLs."""
    token_url = "https://x-access-token:ghp_123456789@github.com/owner/repo.git"
    sanitized = sanitize_url(token_url)
    assert "ghp_123456789" not in sanitized
    assert "https://****@github.com/owner/repo.git" == sanitized
    print("Verification Test Success: sanitize_url masks tokens.")

def test_repo_parsing():
    """Test robust repository parsing from URLs."""
    gh = GitHubClient(token="mock")
    tests = [
        ("https://github.com/owner/repo.git", ("github.com", "owner", "repo")),
        ("https://github.com/owner/repo", ("github.com", "owner", "repo")),
        ("git@github.com:owner/repo.git", ("github.com", "owner", "repo")),
        ("https://token@git.example.net/owner/repo.git", ("git.example.net", "owner", "repo")),
        ("git@git.internal.com:owner/repo", ("git.internal.com", "owner", "repo")),
    ]
    for url, expected in tests:
        res = gh.get_repo_info_from_remote(url)
        assert res == expected
    print("Verification Test Success: Robust repo parsing handles custom GHE domains.")

def test_ghe_api_base():
    """Test that API base is correctly set for GHE."""
    gh_com = GitHubClient(host="github.com")
    assert gh_com.api_base == "https://api.github.com"
    
    gh_ghe = GitHubClient(host="git.example.net")
    assert gh_ghe.api_base == "https://git.example.net/api/v3"
    print("Verification Test Success: GHE API base is correctly determined.")

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
        mock_gh.get_repo_info_from_remote.return_value = ("github.com", "owner", "repo")
        mock_gh.get_repo_metadata.return_value = {"default_branch": "master"}
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
    test_sanitize_url()
    test_repo_parsing()
    test_ghe_api_base()
    asyncio.run(test_complete_jira_ticket_success())
