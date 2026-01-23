"""
Plan Logic
==========

Logic for the 'plan' command to generate a project plan from a specification.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List, Any

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

async def run_plan_logic(
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    verbose: bool = False,
    spec_file: Optional[str] = "app_spec.txt",
    capture_output: bool = False,
    profile: Optional[str] = None
) -> Any: # Returns bool normally, or (bool, str) if capture_output is True
    """
    Executes the 'plan' logic.

    Args:
        project_dir: The project root directory.
        agent_type: The type of agent to use.
        model: The model to use.
        verbose: Enable verbose logging.
        spec_file: The specification file to read.
        capture_output: If True, returns (success, message) instead of printing to stdout.
        profile: The configuration profile to use (not used directly here but compatible with signature).

    Returns:
        True if successful, False otherwise.
        If capture_output is True, returns (success: bool, message: str).
    """

    # Configure logging based on capture_output to prevent stdout interference in TUI
    if capture_output:
        # Create a string buffer for logs if capturing
        # But setup_logger usually handles global logging configuration.
        # For TUI, we might want to suppress console output from the logger
        # or redirect it. run_plan in main.py sets console_output=True.
        # Here we just rely on the existing logger configuration if called from main.
        # If called from TUI, we should be careful.
        pass

    spec_path = project_dir / (spec_file or "app_spec.txt")
    if not spec_path.exists():
        msg = f"Spec file not found: {spec_path}"
        logger.error(msg)
        if capture_output:
            return False, msg
        print(f"❌ {msg}", file=sys.stderr)
        return False

    try:
        spec_content = spec_path.read_text(encoding="utf-8")
    except Exception as e:
        msg = f"Error reading spec file: {e}"
        logger.error(msg)
        if capture_output:
            return False, msg
        print(f"❌ {msg}", file=sys.stderr)
        return False

    # Setup Config
    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=model,
        verbose=verbose,
        max_iterations=1, # Single shot for planning
        stream_output=not capture_output, # Disable streaming if capturing
    )

    # Initialize Agent
    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }

    agent_class = agent_class_map.get(agent_type)
    if not agent_class:
        msg = f"Unknown agent type: {agent_type}"
        logger.error(msg)
        if capture_output:
            return False, msg
        return False

    try:
        agent = agent_class(config)
    except Exception as e:
        msg = f"Failed to initialize agent: {e}"
        logger.error(msg)
        if capture_output:
            return False, msg
        return False

    # Construct Prompt
    # We want the agent to generate feature_list.json based on app_spec.txt
    prompt = f"""
You are a Senior Technical Project Manager.
Your task is to analyze the following application specification and generate a detailed feature list for development.

### PROJECT SPECIFICATION (app_spec.txt)
{spec_content}

### INSTRUCTIONS
1. Analyze the requirements deeply.
2. Break down the application into a list of distinct, testable features.
3. For each feature, provide:
   - A clear category (functional, style, security, etc.)
   - A description of what needs to be built.
   - A list of step-by-step verification steps (how to test it).
4. **CRITICAL**: You MUST output the result as a JSON file named `feature_list.json`.
5. Use the following format for `feature_list.json`:

```json
[
  {{
    "category": "functional",
    "description": "User login with email and password",
    "steps": [
      "Navigate to login page",
      "Enter valid credentials",
      "Click Submit",
      "Verify redirect to dashboard"
    ],
    "passes": false
  }},
  ...
]
```

6. Do NOT write any other code. Just generate the `feature_list.json` file.
7. Use the `write:feature_list.json` block or standard markdown code block for the file.

Generate the `feature_list.json` now.
"""

    if not capture_output:
        logger.info(f"Generating plan for spec: {spec_path.name}")
        logger.info(f"Using agent: {agent_type}, Model: {model or 'auto'}")

    try:
        # Run the agent session
        status, response, actions = await agent.run_agent_session(prompt)

        if status == "error":
            msg = f"Agent failed to generate a plan.\n {response}"
            logger.error(msg)
            if capture_output:
                return False, msg
            print(f"❌ {msg}", file=sys.stderr)
            return False

        # Check if feature_list.json was created
        feature_list_path = project_dir / "feature_list.json"
        if feature_list_path.exists():
            msg = f"Plan generated successfully: {feature_list_path}"
            logger.info(msg)
            if capture_output:
                return True, msg
            print(f"✅ {msg}")
            return True
        else:
            msg = "Agent finished but 'feature_list.json' was not found."
            logger.warning(msg)
            if capture_output:
                return False, msg
            print(f"⚠️  {msg}")
            return False

    except Exception as e:
        msg = f"Unexpected error running {agent_type.capitalize()}: {e}"
        logger.error(msg)
        if capture_output:
            return False, msg
        print(f"❌ {msg}", file=sys.stderr)
        return False
