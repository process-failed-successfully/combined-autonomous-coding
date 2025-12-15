"""
Shared Configuration Module
===========================

Centralized configuration management for the Combined Autonomous Coding agent.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Default Constants
DEFAULT_MODEL_GEMINI = "auto"
DEFAULT_MODEL_CURSOR = "auto"
DEFAULT_AUTO_CONTINUE_DELAY = 3
DEFAULT_MAX_CONSECUTIVE_ERRORS = 3
DEFAULT_GEMINI_TIMEOUT = 600.0
DEFAULT_CURSOR_TIMEOUT = 600.0
DEFAULT_BASH_TIMEOUT = 120.0


@dataclass
class Config:
    """Application Configuration."""

    project_dir: Path
    agent_type: str = "gemini"  # 'gemini' or 'cursor'
    model: Optional[str] = None
    max_iterations: Optional[int] = None
    auto_continue_delay: int = DEFAULT_AUTO_CONTINUE_DELAY
    max_consecutive_errors: int = DEFAULT_MAX_CONSECUTIVE_ERRORS
    timeout: float = DEFAULT_GEMINI_TIMEOUT  # Generic timeout for the active agent
    bash_timeout: float = DEFAULT_BASH_TIMEOUT
    verbose: bool = False
    stream_output: bool = True
    spec_file: Optional[Path] = None
    verify_creation: bool = False

    # Sprint Configuration
    sprint_mode: bool = False
    max_agents: int = 1
    sprint_id: Optional[str] = None

    # Manager Configuration
    manager_frequency: int = 10
    manager_model: Optional[str] = None
    run_manager_first: bool = False
    login_mode: bool = False

    def __post_init__(self):
        if self.model is None:
            if self.agent_type == "gemini":
                self.model = DEFAULT_MODEL_GEMINI
            elif self.agent_type == "cursor":
                self.model = DEFAULT_MODEL_CURSOR

    @property
    def feature_list_path(self) -> Path:
        return self.project_dir / "feature_list.json"

    @property
    def progress_file_path(self) -> Path:
        # We can use a shared progress file or specific ones.
        # To maintain compatibility with existing prompts, we might need specific names
        # or update the prompts to use a generic name.
        # For now, let's stick to agent-specific names to match current
        # prompts.
        if self.agent_type == "gemini":
            return self.project_dir / "gemini_progress.txt"
        else:
            return self.project_dir / "cursor_progress.txt"
