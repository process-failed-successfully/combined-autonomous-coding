"""
Plan Logic Module
=================

Contains logic for generating project plans (feature lists) from specifications.
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Optional

from shared.config import Config
from shared.logger import setup_logger
from shared.config_loader import ensure_config_exists, load_config_from_file
from agents.gemini.agent import GeminiAgent
from agents.cursor.agent import CursorAgent
from agents.local.agent import LocalAgent
from agents.openrouter.agent import OpenRouterAgent

async def run_plan_logic(
    project_dir: Path,
    spec_file: Optional[Path] = None,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    verbose: bool = False
) -> bool:
    """
    Generates a feature plan from a spec file without executing it.
    Returns True if successful.
    """
    # Setup logger if not already set up (safe to call multiple times)
    # But in TUI, logging might conflict with Textual.
    # We should assume logger is configured or use a specific one.
    # For now, we'll rely on the existing logger setup or set up a file logger if needed.
    # setup_logger might print to console, which is bad for TUI.
    # We should avoid setup_logger if running in TUI.
    # TUI sets up its own logging interception usually.

    # We'll skip setup_logger here and assume caller handles it or we log to a file.
    # If called from CLI, main.py sets it up.

    if not spec_file or not spec_file.exists():
        # Try to find default app_spec.txt
        default_spec = project_dir / "app_spec.txt"
        if default_spec.exists():
            spec_file = default_spec
        else:
            return False

    # Load config
    ensure_config_exists()
    file_config = load_config_from_file() or {}

    # Helper to resolve config
    def resolve(arg_val, key, default):
        if arg_val is not None:
            return arg_val
        return file_config.get(key, default)

    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=resolve(model, "model", None),
        spec_file=spec_file,
        verbose=verbose,
        max_iterations=1,
        stream_output=False, # Important for TUI
    )

    project_name = os.environ.get("PROJECT_NAME", project_dir.resolve().name)

    from shared.utils import generate_agent_id
    try:
        spec_content = spec_file.read_text()
        agent_id = generate_agent_id(project_name, spec_content, agent_type)
        config.agent_id = agent_id
    except Exception:
        config.agent_id = generate_agent_id(project_name, "", agent_type)

    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }
    agent_class = agent_class_map.get(agent_type)

    if not agent_class:
        return False

    agent = agent_class(config)

    try:
        plan_generated = await agent.run_planning_session()
        return plan_generated
    except Exception:
        return False
