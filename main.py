#!/usr/bin/env python3
"""
Combined Autonomous Coding Agent
================================

Main entry point for running autonomous coding agents (Gemini or Cursor).
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path

from shared.config import Config
from shared.logger import setup_logger
from shared.git import ensure_git_safe

# Import agent runners
# We import these lazily or handled via dispatch to avoid circular deps if any,
# though structure should be clean.
from agents.gemini import run_autonomous_agent as run_gemini
from agents.gemini import run_sprint as run_sprint
from agents.cursor import run_autonomous_agent as run_cursor



def parse_args():
    parser = argparse.ArgumentParser(description="Autonomous Coding Agent")

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("."),
        help="Directory where the project will be created/modified (default: current directory)"
    )

    parser.add_argument(
        "--agent",
        choices=["gemini", "cursor"],
        default="gemini",
        help="Which agent to use (default: gemini)"
    )

    parser.add_argument(
        "--model",
        type=str,
        help="Model to use (overrides default)"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        help="Maximum number of agent iterations"
    )

    parser.add_argument(
        "--spec",
        type=Path,
        help="Path to app_spec.txt (required for new projects)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--verify-creation",
        action="store_true",
        help="Run verification test (dummy mode)"
    )

    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output"
    )

    # Manager Arguments
    parser.add_argument(
        "--manager-frequency",
        type=int,
        default=10,
        help="How often the manager agent runs (default: 10 iterations)"
    )

    parser.add_argument(
        "--manager-model",
        type=str,
        help="Model to use for the manager agent"
    )

    parser.add_argument(
        "--manager-first",
        action="store_true",
        help="Run the manager agent before the first coding session"
    )

    # Reviewer Arguments
    parser.add_argument(
        "--reviewer-frequency",
        type=int,
        default=5,
        help="How often the technical reviewer runs (default: 5 iterations)"
    )

    parser.add_argument(
        "--reviewer-model",
        type=str,
        help="Model to use for the reviewer agent"
    )

    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable the standalone dashboard server (enabled by default)"
    )

    parser.add_argument(
        "--dashboard-only",
        action="store_true",
        help="Run ONLY the dashboard server (no agent)"
    )

    parser.add_argument(
        "--dashboard-url",
        default="http://localhost:7654",
        help="URL of the dashboard server (default: http://localhost:7654)"
    )

    parser.add_argument(
        "--login",
        action="store_true",
        help="Run the agent in login/authentication mode (exit after login)"
    )

    # Sprint Arguments
    parser.add_argument(
        "--sprint",
        action="store_true",
        help="Run in Sprint Mode (Concurrent Agents)"
    )

    parser.add_argument(
        "--max-agents",
        type=int,
        help="Maximum number of simultaneous agents in Sprint Mode"
    )

    parser.add_argument(
        "--timeout",
        type=float,
        help="Timeout in seconds for agent execution (default: 600.0)"
    )

    return parser.parse_args()


async def main():
    args = parse_args()

    # Dashboard Mode (Legacy - Removed)
    if args.dashboard_only:
        print("Error: The legacy dashboard has been removed. Please use 'make monitor-up' to access Grafana.")
        sys.exit(1)

    # Legacy dashboard auto-start logic is removed.
    # The Grafana stack runs separately via Docker Compose.

    # Initialize Agent Client
    from shared.agent_client import AgentClient
    from shared.utils import generate_agent_id

    project_name = os.environ.get("PROJECT_NAME")
    if not project_name:
        project_name = args.project_dir.resolve().name

    # Read spec content for ID generation
    spec_content = ""
    if args.spec and args.spec.exists():
        try:
             spec_content = args.spec.read_text()
        except Exception as e:
             # We can't log yet, so print to stderr
             print(f"Warning: Could not read spec file for ID generation: {e}", file=sys.stderr)

    # Generate deterministic ID
    agent_id = generate_agent_id(project_name, spec_content, args.agent)

    # Setup Logger
    # We prioritize logging to agents/logs relative to the repo root
    # This ensures it aligns with the Promtail mount
    repo_root = Path(__file__).parent
    agents_log_dir = repo_root / "agents/logs"
    agents_log_dir.mkdir(parents=True, exist_ok=True)

    if args.dashboard_only:
        log_file = agents_log_dir / "dashboard_server.log"
    else:
        # Agent ID now contains the full unique name including format: {agent}_agent_{project}_{hash}
        log_file = agents_log_dir / f"{agent_id}.log"

    logger = setup_logger(log_file=log_file, verbose=args.verbose)

    if not args.dashboard_only:
        logger.info(
            f"Starting {args.agent.capitalize()} Agent on {args.project_dir}")
        logger.info(f"Generated Agent ID: {agent_id}")

    client = AgentClient(agent_id=agent_id, dashboard_url=args.dashboard_url)

    # Create Config
    config = Config(
        project_dir=args.project_dir,
        agent_type=args.agent,
        model=args.model,
        max_iterations=args.max_iterations,
        verbose=args.verbose,
        stream_output=not args.no_stream,
        spec_file=args.spec,
        verify_creation=args.verify_creation,
        manager_frequency=args.manager_frequency,
        manager_model=args.manager_model,
        run_manager_first=args.manager_first,
        login_mode=args.login,
        reviewer_frequency=args.reviewer_frequency,
        reviewer_model=args.reviewer_model,
        timeout=args.timeout if args.timeout else 600.0 # Default fallback if not specified, though Config has its own default
    )

    # Function to resolve spec file
    if args.spec is None:
        default_spec = args.project_dir / "app_spec.txt"
        if default_spec.exists():
            args.spec = default_spec
            logger.info(f"Using default spec file: {args.spec}")

    # Check spec requirement for fresh projects
    # We check if feature list exists to determine if it's a fresh run
    is_fresh = not config.feature_list_path.exists()
    if is_fresh and not args.spec:
        logger.error(
            "Error: --spec argument is required for new projects! (or place 'app_spec.txt' in directory)")
        sys.exit(1)

    # Git Safety
    # Ensure we are on a safe branch before starting any agent work
    ensure_git_safe(args.project_dir)

    # Dispatch
    try:
        if config.sprint_mode:
            logger.info("Running in SPRINT MODE")
            await run_sprint(config, agent_client=client)
            return

        if args.agent == "gemini":
            await run_gemini(config, agent_client=client)
        elif args.agent == "cursor":
            await run_cursor(config, agent_client=client)
    except KeyboardInterrupt:
        logger.info("\nExecution interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
