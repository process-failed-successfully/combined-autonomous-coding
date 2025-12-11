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

# Import agent runners
# We import these lazily or handled via dispatch to avoid circular deps if any,
# though structure should be clean.
from agents.gemini import run_autonomous_agent as run_gemini
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

    return parser.parse_args()


async def main():
    args = parse_args()

    # Dashboard Mode
    # By default we start the dashboard unless explicitly disabled
    if args.dashboard_only:
        # Exclusive Mode: Start server and block
        from ui.server import start_server
        try:
            start_server(port=7654)
            # Block forever
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)
        except OSError as e:
            # If port is busy in exclusive mode, it's an error
            print(f"Error starting dashboard: {e}")
            sys.exit(1)

    if not args.no_dashboard:
        # Default Mode: Try to start server, but proceed if it fails (graceful
        # degradation)
        try:
            from ui.server import start_server
            # We start it in foreground for this mode, or keep main alive
            server, _ = start_server(port=7654)
            # Server runs in daemon thread, so we can proceed to run agent.
        except OSError:
            # Assume port is busy, meaning dashboard is already running
            pass

    # Setup Logger
    # We might want to log to a file in the project directory, but we need to
    # ensure it exists first
    args.project_dir.mkdir(parents=True, exist_ok=True)

    if args.dashboard_only:
        log_file = args.project_dir / "dashboard_server.log"
    else:
        log_file = args.project_dir / f"{args.agent}_agent_debug.log"

    logger = setup_logger(log_file=log_file, verbose=args.verbose)

    if args.dashboard_only:
        logger.info("Starting Dashboard Server on port 7654")
    else:
        logger.info(
            f"Starting {args.agent.capitalize()} Agent on {args.project_dir}")

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
        login_mode=args.login
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

    # Initialize Agent Client
    from shared.agent_client import AgentClient

    project_name = os.environ.get("PROJECT_NAME")
    if not project_name:
        project_name = args.project_dir.resolve().name

    agent_id = f"{args.agent}-{project_name}"
    client = AgentClient(agent_id=agent_id, dashboard_url=args.dashboard_url)

    # Dispatch
    try:
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
