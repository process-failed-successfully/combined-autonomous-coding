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
from shared.config_loader import load_config_from_file, ensure_config_exists

# Import agent runners
# We import these lazily or handled via dispatch to avoid circular deps if any,
# though structure should be clean.
from agents.gemini import run_autonomous_agent as run_gemini
from agents.shared.sprint import run_sprint as run_sprint
from agents.cursor import run_autonomous_agent as run_cursor
from agents.local import run_autonomous_agent as run_local
from agents.openrouter import run_autonomous_agent as run_openrouter


def parse_args():
    parser = argparse.ArgumentParser(description="Autonomous Coding Agent")

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("."),
        help="Directory where the project will be created/modified (default: current directory)",
    )

    parser.add_argument(
        "--agent",
        choices=["gemini", "cursor", "local", "openrouter"],
        default="gemini",
        help="Which agent to use (default: gemini)",
    )

    parser.add_argument("--model", type=str, help="Model to use (overrides default)")

    parser.add_argument(
        "--max-iterations", type=int, help="Maximum number of agent iterations"
    )

    parser.add_argument(
        "--spec", type=Path, help="Path to app_spec.txt (required for new projects)"
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    parser.add_argument(
        "--verify-creation",
        action="store_true",
        help="Run verification test (dummy mode)",
    )

    parser.add_argument(
        "--no-stream", action="store_true", help="Disable streaming output"
    )

    # Manager Arguments
    parser.add_argument(
        "--manager-frequency",
        type=int,
        help="How often the manager agent runs (default: 10 iterations)",
    )

    parser.add_argument(
        "--manager-model", type=str, help="Model to use for the manager agent"
    )

    parser.add_argument(
        "--manager-first",
        action="store_true",
        help="Run the manager agent before the first coding session",
    )

    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable the standalone dashboard server (enabled by default)",
    )

    parser.add_argument(
        "--dashboard-only",
        action="store_true",
        help="Run ONLY the dashboard server (no agent)",
    )

    parser.add_argument(
        "--dashboard-url",
        default="http://localhost:7654",
        help="URL of the dashboard server (default: http://localhost:7654)",
    )

    parser.add_argument(
        "--login",
        action="store_true",
        help="Run the agent in login/authentication mode (exit after login)",
    )

    # Sprint Arguments
    parser.add_argument(
        "--sprint", action="store_true", help="Run in Sprint Mode (Concurrent Agents)"
    )

    parser.add_argument(
        "--max-agents",
        type=int,
        help="Maximum number of simultaneous agents in Sprint Mode",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        help="Timeout in seconds for agent execution (default: 600.0)",
    )

    parser.add_argument(
        "--max-error-wait",
        type=float,
        help="Maximum wait time in seconds for agent error backoff (default: 600.0)",
    )

    parser.add_argument(
        "--jira-ticket",
        type=str,
        help="Jira ticket ID to work on (e.g., PROJ-123)",
    )

    parser.add_argument(
        "--jira-label",
        type=str,
        help="Jira label to search for (picks first 'To Do' ticket)",
    )

    parser.add_argument(
        "--dind",
        "--docker-in-docker",
        action="store_true",
        help="Enable Docker-in-Docker support (mounts docker socket)",
    )

    return parser.parse_args()


async def main():
    args = parse_args()

    # Dashboard Mode (Legacy - Removed)
    if args.dashboard_only:
        print(
            "Error: The legacy dashboard has been removed. Please use 'make monitor-up' to access Grafana."
        )
        sys.exit(1)

    # Legacy dashboard auto-start logic is removed.
    # The Grafana stack runs separately via Docker Compose.

    # Initialize Agent Client
    from shared.agent_client import AgentClient
    from shared.utils import generate_agent_id

    project_name = os.environ.get("PROJECT_NAME")
    if not project_name:
        project_name = args.project_dir.resolve().name

    # Load Configuration from File
    # Priority resolved in config_loader: ./ > XDG > Legacy
    ensure_config_exists()
    file_config = load_config_from_file()

    # Helper to resolve configuration priority: CLI > Config File > Default
    def resolve(cli_arg, config_key, default_val):
        if cli_arg is not None:
            return cli_arg
        if config_key in file_config:
            return file_config[config_key]
        return default_val

    # Create Config
    config = Config(
        project_dir=args.project_dir,
        agent_id=None,  # Placeholder, set later
        agent_type=args.agent,
        model=resolve(args.model, "model", None),
        max_iterations=resolve(args.max_iterations, "max_iterations", None),
        verbose=args.verbose,
        stream_output=not args.no_stream,
        spec_file=args.spec,
        verify_creation=args.verify_creation,

        # Manager
        manager_frequency=resolve(args.manager_frequency, "manager_frequency", 10),
        manager_model=resolve(args.manager_model, "manager_model", None),
        run_manager_first=args.manager_first,
        login_mode=args.login or file_config.get("login_mode", False),

        timeout=resolve(args.timeout, "timeout", 600.0),
        max_error_wait=resolve(args.max_error_wait, "max_error_wait", 600.0),

        # Sprint
        sprint_mode=args.sprint or file_config.get("sprint_mode", False),
        max_agents=resolve(args.max_agents, "max_agents", 1),

        # Notifications
        slack_webhook_url=file_config.get("slack_webhook_url"),
        discord_webhook_url=file_config.get("discord_webhook_url"),
        notification_settings=file_config.get("notification_settings"),

        # Docker-in-Docker
        dind_enabled=args.dind or file_config.get("dind_enabled", False),
    )

    # Load Jira Config
    from shared.config import JiraConfig
    jira_cfg_data = file_config.get("jira", {})
    jira_env_url = os.environ.get("JIRA_URL")
    jira_env_email = os.environ.get("JIRA_EMAIL")
    jira_env_token = os.environ.get("JIRA_TOKEN")

    if jira_env_url:
        jira_cfg_data["url"] = jira_env_url
    if jira_env_email:
        jira_cfg_data["email"] = jira_env_email
    if jira_env_token:
        jira_cfg_data["token"] = jira_env_token

    if args.jira_ticket or args.jira_label:
        if not jira_cfg_data:
            print("Error: Jira arguments provided but no Jira configuration found (config file or env vars).", file=sys.stderr)
            print("Please set JIRA_URL, JIRA_EMAIL, JIRA_TOKEN or configure agent_config.yaml", file=sys.stderr)
            sys.exit(1)
        config.jira = JiraConfig(**jira_cfg_data)

    # Correction for boolean flags initialized with 'store_true' (default False)
    if file_config.get("run_manager_first"):
        config.run_manager_first = True

    # SETUP LOGGER (Moved earlier to support logging during Jira fetch)
    repo_root = Path(__file__).parent
    agents_log_dir = repo_root / "agents/logs"
    agents_log_dir.mkdir(parents=True, exist_ok=True)

    # We need a temp ID for logging before we know the real agent_id (which might come from Jira)
    # But for now, we can use a generic one or wait.
    # Let's setup a basic console logger first?
    # existing setup_logger requires a file. We will update it later.

    # JIRA LOGIC
    jira_client = None
    # jira_ticket = None  # Unused
    jira_spec_content = ""

    if config.jira and (args.jira_ticket or args.jira_label):
        from shared.jira_client import JiraClient

        try:
            jira_client = JiraClient(config.jira)

            if args.jira_ticket:
                issue = jira_client.get_issue(args.jira_ticket)
            elif args.jira_label:
                issue = jira_client.get_first_todo_by_label(args.jira_label)

            if issue:
                # jira_ticket = issue  # Unused
                print(f"Working on Jira Ticket: {issue.key} - {issue.fields.summary}")

                # Parse Description (for context only)
                desc = issue.fields.description or ""

                # Construct Spec
                jira_spec_content = f"JIRA TICKET {issue.key}\nSUMMARY: {issue.fields.summary}\nDESCRIPTION:\n{desc}"
                config.jira_ticket_key = issue.key
                config.jira_spec_content = jira_spec_content
                project_name = issue.key

                # Transition to In Progress (default 'Start' status)
                start_status = config.jira.status_map.get("start", "In Progress") if config.jira.status_map else "In Progress"
                jira_client.transition_issue(issue.key, start_status)

            else:
                print("No suitable Jira ticket found.")
                sys.exit(0)

        except Exception as e:
            print(f"Jira Integration Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Read spec content for ID generation
    spec_content = ""
    if jira_spec_content:
        spec_content = jira_spec_content
    elif args.spec and args.spec.exists():
        try:
            spec_content = args.spec.read_text()
        except Exception as e:
            print(f"Warning: Could not read spec file for ID generation: {e}", file=sys.stderr)

    # Generate deterministic ID
    agent_id = generate_agent_id(project_name, spec_content, args.agent)
    config.agent_id = agent_id

    if args.dashboard_only:
        log_file = agents_log_dir / "dashboard_server.log"
    else:
        log_file = agents_log_dir / f"{agent_id}.log"

    # Configure Root Logger to capture all module logs (e.g. shared.git)
    logger = setup_logger(name="", log_file=log_file, verbose=args.verbose)

    if not args.dashboard_only:
        logger.info(f"Starting {args.agent.capitalize()} Agent on {args.project_dir}")
        logger.info(f"Generated Agent ID: {agent_id}")

    client = AgentClient(agent_id=agent_id, dashboard_url=args.dashboard_url)

    # Check spec requirement for fresh projects (Updated for Jira)
    is_fresh = not config.feature_list_path.exists()
    if is_fresh and not args.spec and not jira_spec_content:
        logger.error(
            "Error: --spec argument or --jira-ticket is required for new projects!"
        )
        sys.exit(1)

    # Git Safety
    # Ensure we are on a safe branch before starting any agent work
    jira_key = config.jira_ticket_key if config.jira else None
    ensure_git_safe(args.project_dir, ticket_key=jira_key)

    # Git Authentication (Env Var Check)
    git_token = os.environ.get("GIT_TOKEN")
    if git_token:
        from shared.git import configure_git_auth
        git_host = os.environ.get("GIT_HOST", "github.com")
        git_user = os.environ.get("GIT_USERNAME", "x-access-token")
        configure_git_auth(git_token, git_host, git_user)

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
        elif args.agent == "local":
            await run_local(config, agent_client=client)
        elif args.agent == "openrouter":
            await run_openrouter(config, agent_client=client)
    except KeyboardInterrupt:
        logger.info("\nExecution interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)

    # Post-Execution Cleanup
    # If project is signed off, run the completion flow and cleaner
    if (config.project_dir / "PROJECT_SIGNED_OFF").exists():
        # Final safety check for Jira completion (in case iteration loop didn't hit it)
        if config.jira and config.jira_ticket_key:
            from shared.workflow import complete_jira_ticket
            await complete_jira_ticket(config)

        logger.info("Project signed off. Finalizing...")
        # note: the autonomous loop itself now handles triggering the cleaner agent
        # if cleanup_report.txt is missing.


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
