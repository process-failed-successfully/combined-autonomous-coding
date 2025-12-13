"""
Prompt Loading Utilities for Gemini
===================================
"""

import shutil
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent.parent / "shared" / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = PROMPTS_DIR / f"{name}.md"
    return prompt_path.read_text()


def get_initializer_prompt() -> str:
    """Load the initializer prompt."""
    return load_prompt("initializer_prompt")


def get_coding_prompt() -> str:
    """Load the coding agent prompt."""
    return load_prompt("coding_prompt")


def get_manager_prompt() -> str:
    """Load the manager agent prompt."""
    return load_prompt("manager_prompt")


def get_sprint_planner_prompt() -> str:
    """Load the sprint planner prompt."""
    return load_prompt("sprint_planner_prompt")


def get_sprint_worker_prompt() -> str:
    """Load the sprint worker prompt."""
    return load_prompt("sprint_worker_prompt")



def copy_spec_to_project(
        project_dir: Path,
        custom_spec_path: Path = None) -> None:
    """Copy the app spec file into the project directory for the agent to read."""
    spec_source = custom_spec_path if custom_spec_path else PROMPTS_DIR / "app_spec.txt"
    spec_dest = project_dir / "app_spec.txt"
    if not spec_dest.exists():
        if spec_source.exists():
            shutil.copy(spec_source, spec_dest)
            print("Copied app_spec.txt to project directory")
        else:
            print(f"Warning: Spec file not found at {spec_source}")
