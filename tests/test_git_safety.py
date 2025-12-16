import pytest
import shutil
from pathlib import Path
from subprocess import CalledProcessError, run
import logging

from shared.git import ensure_git_safe, assert_safe_branch, run_git

# Setup logger
logger = logging.getLogger(__name__)

@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Initialize git
    run(["git", "init"], cwd=repo_dir, check=True)
    run(["git", "config", "user.email", "you@example.com"], cwd=repo_dir, check=True)
    run(["git", "config", "user.name", "Your Name"], cwd=repo_dir, check=True)
    run(["git", "branch", "-M", "main"], cwd=repo_dir, check=True)
    
    # Create initial commit
    (repo_dir / "README.md").write_text("Test Repo")
    run(["git", "add", "."], cwd=repo_dir, check=True)
    run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True)
    
    return repo_dir

def test_assert_safe_branch_raises_on_main(temp_git_repo):
    """Test that assert_safe_branch raises an error when on main."""
    # Ensure checking out main
    run(["git", "checkout", "main"], cwd=temp_git_repo, check=True)
    
    with pytest.raises(RuntimeError, match="CRITICAL SECURITY ERROR: Agent is on protected branch 'main'"):
        assert_safe_branch(temp_git_repo)

def test_assert_safe_branch_passes_on_feature_branch(temp_git_repo):
    """Test that assert_safe_branch passes on a feature branch."""
    run(["git", "checkout", "-b", "feature/test-branch"], cwd=temp_git_repo, check=True)
    
    # Should not raise
    assert_safe_branch(temp_git_repo)

def test_ensure_git_safe_switches_branch(temp_git_repo):
    """Test that ensure_git_safe switches away from main."""
    # Ensure on main
    run(["git", "checkout", "main"], cwd=temp_git_repo, check=True)
    
    ensure_git_safe(temp_git_repo)
    
    # Verify we are on a timestamped branch
    result = run(["git", "branch", "--show-current"], cwd=temp_git_repo, capture_output=True, text=True, check=True)
    current_branch = result.stdout.strip()
    
    assert current_branch.startswith("agent/session-")
    assert current_branch != "main"
    
    # Verify it passes safety check
    assert_safe_branch(temp_git_repo)
