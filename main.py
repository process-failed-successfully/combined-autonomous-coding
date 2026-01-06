#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
"""
Combined Autonomous Coding Agent
================================

Main entry point for running autonomous coding agents (Gemini or Cursor).
"""

import argparse
import asyncio
try:
    import argcomplete
except ImportError:
    argcomplete = None
import sys
import os
import shutil
import subprocess
from pathlib import Path

from shared.config import Config
from shared.logger import setup_logger
from shared.git import ensure_git_safe
from shared.config_loader import load_config_from_file, ensure_config_exists

# Import agent runners
# We import these lazily or handled via dispatch to avoid circular deps if any,
# though structure should be clean.
try:
    from shared.jira_client import JiraClient
except ImportError:
    JiraClient = None
from agents.gemini import run_autonomous_agent as run_gemini, GeminiAgent
from agents.shared.sprint import run_sprint as run_sprint
from agents.cursor import run_autonomous_agent as run_cursor, CursorAgent
from agents.local import run_autonomous_agent as run_local, LocalAgent
from agents.openrouter import run_autonomous_agent as run_openrouter, OpenRouterAgent
from shared.shell import InteractiveShell
import json
import yaml
import platformdirs
from dataclasses import asdict, is_dataclass

# Agent Definitions
AVAILABLE_AGENTS = {
    "gemini": "Uses Google's Gemini model via the official API.",
    "cursor": "Interacts with the Cursor IDE's AI features.",
    "local": "Runs a local model (e.g., Ollama).",
    "openrouter": "Uses a model from the OpenRouter API.",
}


def run_validate():
    """Validates the agent_config.yaml file."""
    print("--- Validating Agent Configuration ---")
    errors = []

    from shared.config_loader import get_config_path, load_config_from_file
    config_path = get_config_path()

    if not config_path or not config_path.exists():
        print("❌ Configuration file (agent_config.yaml) not found in any of the searched paths.")
        print("   Searched in ./, ~/.config/combined-autonomous-coding/, and ~/.gemini/")
        sys.exit(1)

    print(f"Found configuration file at: {config_path}")

    try:
        config_data = load_config_from_file()
    except Exception as e:
        print(f"❌ Error loading or parsing YAML from {config_path}: {e}")
        sys.exit(1)

    # Jira Validation
    if 'jira' in config_data:
        jira_config = config_data['jira']
        if not isinstance(jira_config, dict):
            errors.append("Jira config ('jira') must be a dictionary.")
        else:
            required_jira_keys = ['url', 'email', 'token']
            for key in required_jira_keys:
                if key not in jira_config or not jira_config.get(key):
                    errors.append(f"Jira config in {config_path} is missing required key or value: '{key}'")

    # Notification Validation (check for non-empty strings)
    if 'slack_webhook_url' in config_data and config_data.get('slack_webhook_url'):
        url = config_data['slack_webhook_url']
        if not isinstance(url, str) or not url.startswith("https://hooks.slack.com/"):
            errors.append(f"Invalid Slack webhook URL format in {config_path}.")

    if 'discord_webhook_url' in config_data and config_data.get('discord_webhook_url'):
        url = config_data['discord_webhook_url']
        if not isinstance(url, str) or not url.startswith("https://discord.com/api/webhooks/"):
            errors.append(f"Invalid Discord webhook URL format in {config_path}.")

    # Type checks for other common keys
    type_checks = {
        'model': str, 'max_iterations': int, 'manager_frequency': int,
        'manager_model': str, 'timeout': (int, float), 'max_error_wait': (int, float),
        'max_agents': int, 'dind_enabled': bool, 'run_manager_first': bool,
        'notification_settings': dict,
    }
    for key, expected_type in type_checks.items():
        if key in config_data and config_data.get(key) is not None and not isinstance(config_data[key], expected_type):
            errors.append(f"'{key}' has incorrect type in {config_path}. Expected {expected_type}, got {type(config_data[key]).__name__}.")

    if errors:
        print(f"\n❌ Configuration validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\n✅ Configuration is valid!")
        sys.exit(0)


def run_doctor(args):
    """Runs a comprehensive health check on the environment."""
    import shutil
    import requests

    print("--- Running Environment Health Check (Doctor) ---")
    project_dir = args.project_dir.resolve()
    all_checks_passed = True
    error_messages = []

    # 1. Configuration File Check
    print("\n[1] Checking Configuration File...")
    from shared.config_loader import get_config_path, load_config_from_file
    config_path = get_config_path()
    config_data = {}

    if not config_path or not config_path.exists():
        print("  ❌ Configuration file (agent_config.yaml) not found.")
        all_checks_passed = False
    else:
        print(f"  ✅ Found configuration file at: {config_path}")
        try:
            # Re-using validation logic from run_validate without exiting
            config_data = load_config_from_file() or {}
            validation_errors = []
            if 'jira' in config_data:
                jira_config = config_data.get('jira', {})
                if not all(k in jira_config and jira_config[k] for k in ['url', 'email', 'token']):
                    validation_errors.append("Jira config is missing required values for 'url', 'email', or 'token'.")

            if config_data.get('slack_webhook_url') and not str(config_data['slack_webhook_url']).startswith("https://hooks.slack.com/"):
                validation_errors.append("Invalid Slack webhook URL format.")

            if config_data.get('discord_webhook_url') and not str(config_data['discord_webhook_url']).startswith("https://discord.com/api/webhooks/"):
                validation_errors.append("Invalid Discord webhook URL format.")

            if validation_errors:
                all_checks_passed = False
                for err in validation_errors:
                    print(f"  ❌ {err}")
                    error_messages.append(f"Config validation: {err}")
            else:
                print("  ✅ Configuration file format appears valid.")
        except yaml.YAMLError as e:
            print(f"  ❌ Error parsing YAML configuration: {e}")
            all_checks_passed = False
            error_messages.append(f"Config parsing error: {e}")
        except Exception as e:
            print(f"  ❌ Error loading or parsing configuration: {e}")
            all_checks_passed = False
            error_messages.append(f"Config loading error: {e}")

    # 2. Dependency Checks (Git)
    print("\n[2] Checking Dependencies...")
    if shutil.which("git"):
        print("  ✅ Git executable found.")
    else:
        print("  ❌ Git executable not found. Git is required for version control.")
        all_checks_passed = False
        error_messages.append("Dependency check: Git not found.")

    # 3. Connectivity Checks
    print("\n[3] Checking API Connectivity...")
    # Jira Connectivity
    if 'jira' in config_data and all(k in config_data['jira'] for k in ['url', 'email', 'token']):
        print("  - Checking Jira connection...")
        try:
            from shared.jira_client import JiraClient
            from shared.config import JiraConfig
            jira_config = JiraConfig(**config_data['jira'])
            jira_client = JiraClient(jira_config)
            jira_client.check_connection()
            print("    ✅ Jira connection successful.")
        except Exception as e:
            print(f"    ❌ Jira connection failed: {e}")
            all_checks_passed = False
            error_messages.append(f"Jira connection: {e}")
    else:
        print("  - Jira not configured, skipping check.")

    # Webhook Connectivity (using requests to avoid heavy deps)
    for service, url_key in [("Slack", "slack_webhook_url"), ("Discord", "discord_webhook_url")]:
        webhook_url = config_data.get(url_key)
        if webhook_url:
            print(f"  - Checking {service} webhook...")
            try:
                response = requests.head(webhook_url, timeout=5)
                # Most webhooks will return 405 for HEAD but it confirms reachability. 200 is also fine.
                if response.status_code in [200, 405]:
                    print(f"    ✅ {service} webhook is reachable.")
                else:
                    print(f"    ❌ {service} webhook returned status {response.status_code}.")
                    all_checks_passed = False
                    error_messages.append(f"{service} webhook check failed with status {response.status_code}.")
            except requests.RequestException as e:
                print(f"    ❌ Could not connect to {service} webhook: {e}")
                all_checks_passed = False
                error_messages.append(f"{service} webhook connection error: {e}")
        else:
            print(f"  - {service} not configured, skipping check.")

    # 4. Permissions Check
    print("\n[4] Checking File System Permissions...")
    try:
        if not project_dir.exists():
            project_dir.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Project directory created at: {project_dir}")

        if os.access(project_dir, os.W_OK):
            print(f"  ✅ Project directory is writable: {project_dir}")
        else:
            print(f"  ❌ Project directory is not writable: {project_dir}")
            all_checks_passed = False
            error_messages.append(f"Permissions: Project directory '{project_dir}' not writable.")
    except Exception as e:
        print(f"  ❌ Error checking permissions for {project_dir}: {e}")
        all_checks_passed = False
        error_messages.append(f"Permissions check error: {e}")

    # Final Summary
    print("\n--- Health Check Summary ---")
    if all_checks_passed:
        print("✅ All checks passed. Your environment is ready!")
        sys.exit(0)
    else:
        print(f"❌ Found {len(error_messages)} issue(s). Please review the errors above.")
        sys.exit(1)


def run_show_config(config):
    """Prints the final resolved configuration as JSON and exits."""
    from shared.utils import EnhancedJSONEncoder
    print(json.dumps(config, cls=EnhancedJSONEncoder, indent=2, sort_keys=True))
    sys.exit(0)


def run_list_agents():
    """Prints a list of available agents and their descriptions."""
    print("--- Available Agents ---")
    # Find the longest agent name for alignment
    max_len = max(len(name) for name in AVAILABLE_AGENTS.keys())

    for name, description in AVAILABLE_AGENTS.items():
        # Format with padding for alignment
        print(f"  {name.ljust(max_len)} : {description}")
    sys.exit(0)


def run_configure():
    """Interactively create or update the agent_config.yaml file."""
    print("--- Agent Configuration ---")

    # Use XDG path as the primary location
    config_dir = Path(platformdirs.user_config_dir("combined-autonomous-coding"))
    config_path = config_dir / "agent_config.yaml"

    config_dir.mkdir(parents=True, exist_ok=True)

    # Load existing config if it exists
    existing_config: dict = {}
    if config_path.exists():
        print(f"Loading existing configuration from: {config_path}")
        with open(config_path, 'r') as f:
            existing_config = yaml.safe_load(f) or {}
    else:
        print(f"Creating new configuration file at: {config_path}")

    # Helper for user input
    def get_input(prompt, default_value=None):
        if default_value:
            prompt_text = f"{prompt} [{default_value}]: "
        else:
            prompt_text = f"{prompt}: "

        user_input = input(prompt_text).strip()
        return user_input or default_value

    # --- JIRA Configuration ---
    print("\n--- Jira Integration (optional) ---")
    jira_config = existing_config.get('jira', {})

    jira_url = get_input("Jira URL (e.g., https://your-domain.atlassian.net)", jira_config.get('url'))
    if jira_url:
        jira_email = get_input("Jira Email", jira_config.get('email'))
        jira_token = get_input("Jira API Token", jira_config.get('token'))

        updated_jira_config = {
            'url': jira_url,
            'email': jira_email,
            'token': jira_token
        }
        if 'status_map' in jira_config:
            updated_jira_config['status_map'] = jira_config['status_map']

        existing_config['jira'] = updated_jira_config
    elif 'jira' in existing_config:
        del existing_config['jira']

    # --- Notifications ---
    print("\n--- Notifications (optional) ---")
    slack_url = get_input("Slack Webhook URL", existing_config.get('slack_webhook_url'))
    discord_url = get_input("Discord Webhook URL", existing_config.get('discord_webhook_url'))

    if slack_url:
        existing_config['slack_webhook_url'] = slack_url
    if discord_url:
        existing_config['discord_webhook_url'] = discord_url

    # Clean up empty keys
    final_config = {k: v for k, v in existing_config.items() if v}

    # --- Save Configuration ---
    try:
        with open(config_path, 'w') as f:
            yaml.dump(final_config, f, sort_keys=False, indent=2)
        print(f"\n✅ Configuration saved successfully to {config_path}")
    except Exception as e:
        print(f"\n❌ Error saving configuration: {e}")


def run_clean(args):
    """Moves or removes agent-generated artifacts from the project directory."""
    import shutil
    from datetime import datetime

    project_dir = args.project_dir.resolve()
    is_force_delete = args.force
    is_archive = args.archive
    is_list = args.list

    # Determine action and destination
    if is_list:
        action_desc = "Listing"
    elif is_force_delete:
        action_desc = "Permanently DELETING"
        log_verb = "Cleaning"
        dest_base_dir_name = None
        dest_dir_prefix = None
        completion_message = "\n✅ Clean complete."
    elif is_archive:
        action_desc = "Archiving"
        log_verb = "Archiving"
        dest_base_dir_name = ".agent_archives"
        dest_dir_prefix = "archive"
        completion_message = "\n✅ Archive complete. Artifacts moved to {dest_dir_display_path}"
    else:  # Default is trash
        action_desc = "Moving to trash"
        log_verb = "Trashing"
        dest_base_dir_name = ".agent_trash"
        dest_dir_prefix = "trash"
        completion_message = "\n✅ Trash complete. Artifacts moved to {dest_dir_display_path}"

    print(f"--- {action_desc} artifacts in project directory: {project_dir} ---")

    # List of agent-generated files and directories to be cleaned
    artifacts_to_clean = [
        ".agent_db.sqlite",
        "COMPLETED",
        "QA_PASSED",
        "PROJECT_SIGNED_OFF",
        "feature_list.json",
        "qa_summary.txt",
        "reviewer_report.txt",
        "cleanup_report.txt",
        "final_metrics.txt",
        "temp_files.txt",
        "dashboard_state.json",
        "worktrees/",  # Directory
    ]

    # Find artifacts in the project directory
    existing_artifacts = []
    for artifact in artifacts_to_clean:
        path = project_dir / artifact
        if path.exists():
            existing_artifacts.append(path)

    # Also include the log file from the last run
    run_id_file = project_dir / ".agent_run_id"
    log_file_path = None
    if run_id_file.exists():
        run_id = run_id_file.read_text().strip()
        repo_root = Path(__file__).parent
        log_file_path = repo_root / f"agents/logs/{run_id}.log"
        if log_file_path.exists():
            # Add the log file to be cleaned
            existing_artifacts.append(log_file_path)

    if not existing_artifacts:
        print("No agent-generated artifacts found to clean.")
        sys.exit(0)

    # If --list is used, just print the files and exit
    if is_list:
        print("The following agent-generated artifacts would be cleaned:")
        for path in existing_artifacts:
            try:
                display_path = path.relative_to(project_dir)
            except ValueError:
                repo_root = Path(__file__).parent
                try:
                    display_path = f"(from repo root) {path.relative_to(repo_root)}"
                except ValueError:
                    display_path = path
            print(f"  - {display_path}")
        sys.exit(0)

    # Prepare destination directory path if needed
    dest_dir = None
    dest_dir_display_path = None
    if not is_force_delete:
        dest_base_dir = project_dir / dest_base_dir_name
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest_dir = dest_base_dir / f"{dest_dir_prefix}-{timestamp}"
        dest_dir_display_path = dest_dir.relative_to(project_dir)

    action_verb = "permanently DELETED" if is_force_delete else f"MOVED to {dest_dir_display_path}"
    print(f"The following agent-generated files and directories will be {action_verb}:")
    for path in existing_artifacts:
        try:
            display_path = path.relative_to(project_dir)
        except ValueError:
            # The path is not inside the project directory (e.g., agent log file)
            repo_root = Path(__file__).parent
            try:
                display_path = f"(from repo root) {path.relative_to(repo_root)}"
            except ValueError:
                display_path = path  # Absolute path as a fallback
        print(f"  - {display_path}")

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print(f"\n{log_verb} artifacts...")

    # Create destination directory now that we have confirmation
    if not is_force_delete and dest_dir:
        dest_dir.mkdir(parents=True, exist_ok=True)

    for path in existing_artifacts:
        try:
            if is_force_delete:
                if path.is_file():
                    path.unlink()
                    print(f"Deleted file: {path.relative_to(project_dir)}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    print(f"Deleted directory: {path.relative_to(project_dir)}")
            else:
                dest = dest_dir / path.name
                shutil.move(str(path), str(dest))
                print(f"Moved to {dest_dir_prefix}: {path.relative_to(project_dir)}")
        except OSError as e:
            print(f"Error processing {path}: {e}", file=sys.stderr)

    if not is_force_delete:
        print(completion_message.format(dest_dir_display_path=dest_dir.relative_to(project_dir)))
    else:
        print(completion_message)
    sys.exit(0)


def run_archive(args):
    """Archives agent-generated artifacts to a timestamped directory."""
    print("Warning: The 'archive' command is deprecated and will be removed in a future version. "
          "Use 'clean --archive' instead.", file=sys.stderr)
    import shutil
    from datetime import datetime

    project_dir = args.project_dir.resolve()
    print(f"--- Archiving artifacts in project directory: {project_dir} ---")

    # List of agent-generated files and directories to be archived
    artifacts_to_archive = [
        ".agent_db.sqlite",
        "COMPLETED",
        "QA_PASSED",
        "PROJECT_SIGNED_OFF",
        "feature_list.json",
        "qa_summary.txt",
        "reviewer_report.txt",
        "cleanup_report.txt",
        "final_metrics.txt",
        "temp_files.txt",
        "dashboard_state.json",
        "worktrees/",  # Directory
    ]

    existing_artifacts = []
    for artifact in artifacts_to_archive:
        path = project_dir / artifact
        if path.exists():
            existing_artifacts.append(path)

    if not existing_artifacts:
        print("No agent-generated artifacts found to archive.")
        sys.exit(0)

    # Create archive directory
    archive_base_dir = project_dir / ".agent_archives"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_dir = archive_base_dir / f"archive-{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    print(f"Archiving to: {archive_dir}")

    for path in existing_artifacts:
        try:
            dest = archive_dir / path.name
            shutil.move(str(path), str(dest))
            print(f"Archived: {path.relative_to(project_dir)}")
        except OSError as e:
            print(f"Error archiving {path}: {e}", file=sys.stderr)

    print(f"\n✅ Archiving complete. Artifacts moved to {archive_dir.relative_to(project_dir)}")
    sys.exit(0)


def _snapshot_create(args):
    """Helper function to create a snapshot."""
    import shutil
    from datetime import datetime

    project_dir = args.project_dir.resolve()
    snapshot_name = args.name
    archive_base_dir = project_dir / ".agent_archives"

    # Define the name of the snapshot directory
    if snapshot_name:
        snapshot_dir_name = snapshot_name
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        snapshot_dir_name = f"snapshot-{timestamp}"

    snapshot_dir = archive_base_dir / snapshot_dir_name

    print(f"--- Creating snapshot of artifacts in: {project_dir} ---")

    # List of key agent-generated files to be snapshotted
    artifacts_to_snapshot = [
        "feature_list.json",
        "qa_summary.txt",
        "reviewer_report.txt",
        "final_metrics.txt",
        "dashboard_state.json",
    ]

    # Find artifacts that actually exist in the project directory
    existing_artifacts = []
    for artifact in artifacts_to_snapshot:
        path = project_dir / artifact
        if path.exists():
            existing_artifacts.append(path)

    # Also include the log file from the last run, if it exists
    run_id_file = project_dir / ".agent_run_id"
    if run_id_file.exists():
        run_id = run_id_file.read_text().strip()
        repo_root = Path(__file__).parent
        log_file_path = repo_root / f"agents/logs/{run_id}.log"
        if log_file_path.exists():
            existing_artifacts.append(log_file_path)

    if not existing_artifacts:
        print("No key agent-generated artifacts found to snapshot.")
        sys.exit(0)

    if snapshot_dir.exists():
        print(f"❌ Error: A snapshot named '{snapshot_dir_name}' already exists in .agent_archives.")
        print("Please choose a different name or remove the existing one.")
        sys.exit(1)

    print(f"Snapshot will be saved to: .agent_archives/{snapshot_dir_name}")
    print("The following artifacts will be copied:")
    for path in existing_artifacts:
        try:
            display_path = path.relative_to(project_dir)
        except ValueError:
            repo_root = Path(__file__).parent
            display_path = f"(from repo root) {path.relative_to(repo_root)}"
        print(f"  - {display_path}")

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print("\nCreating snapshot...")
    try:
        archive_base_dir.mkdir(exist_ok=True)
        snapshot_dir.mkdir()

        for path in existing_artifacts:
            dest = snapshot_dir / path.name
            if path.is_file():
                shutil.copy2(path, dest)
            elif path.is_dir():
                shutil.copytree(path, dest)
        print(f"Copied {len(existing_artifacts)} artifact(s).")

    except OSError as e:
        print(f"❌ Error creating snapshot: {e}", file=sys.stderr)
        if snapshot_dir.exists():
            shutil.rmtree(snapshot_dir)
        sys.exit(1)

    print(f"\n✅ Snapshot '{snapshot_dir_name}' created successfully.")
    sys.exit(0)


def _snapshot_diff(args):
    """Helper function to diff a snapshot against the current project state."""
    project_dir = args.project_dir.resolve()
    snapshot_name = args.name
    archive_base_dir = project_dir / ".agent_archives"
    snapshot_dir = archive_base_dir / snapshot_name

    if not snapshot_name:
        print("❌ Error: 'snapshot diff' requires a snapshot name.", file=sys.stderr)
        sys.exit(1)

    if not snapshot_dir.is_dir():
        print(f"❌ Error: Snapshot '{snapshot_name}' not found in '{archive_base_dir}'.", file=sys.stderr)
        sys.exit(1)

    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Diff functionality requires Git.", file=sys.stderr)
        sys.exit(1)

    print(f"--- Diffing current project against snapshot: {snapshot_name} ---")

    try:
        # Using --no-index to compare paths on the filesystem directly
        # --ignore-cr-at-eol helps with cross-platform line ending differences
        # --ignore-space-change ignores changes in the amount of whitespace
        cmd = [
            git_path, "diff", "--no-index", "--color=always",
            "--ignore-cr-at-eol", "--ignore-space-change",
            str(snapshot_dir), str(project_dir)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # git diff exits with 1 if there are differences, 0 if not.
        if result.returncode == 0:
            print("✅ No differences found.")
        else:
            print(result.stdout)
            # You can also print stderr if you want to see potential git warnings/errors
            if result.stderr:
                print("\n--- Git Errors/Warnings ---", file=sys.stderr)
                print(result.stderr, file=sys.stderr)

    except Exception as e:
        print(f"❌ An unexpected error occurred during diff: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


def run_snapshot(args):
    """Dispatches snapshot actions."""
    if args.action == "create":
        _snapshot_create(args)
    elif args.action == "diff":
        _snapshot_diff(args)


def _artifacts_list(base_dir, mode):
    """Generic helper function to list archives or trash."""
    title = "Archives" if mode == 'archive' else "Trash"
    print(f"--- {title} in: {base_dir} ---")
    try:
        archives = sorted([d for d in base_dir.iterdir() if d.is_dir()], reverse=True)
    except OSError as e:
        print(f"Error reading {mode} directory: {e}", file=sys.stderr)
        sys.exit(1)

    if not archives:
        print(f"{mode.capitalize()} is empty.")
        sys.exit(0)

    for i, archive_dir in enumerate(archives):
        latest_marker = " (latest)" if i == 0 else ""
        print(f"\n[{i+1}] {archive_dir.name}{latest_marker}")
        try:
            contents = list(archive_dir.iterdir())
            if not contents:
                print("    (empty)")
            else:
                # Always list all contents first
                for item in contents:
                    is_dir = "/ (dir)" if item.is_dir() else ""
                    print(f"    - {item.name}{is_dir}")

                # If a log file exists, show a summary
                log_file = next((item for item in contents if item.suffix == '.log'), None)
                if log_file:
                    print("    --- Log Summary (last 15 lines) ---")
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            for line in lines[-15:]:
                                stripped_line = line.strip()
                                if stripped_line:
                                    print(f"      {stripped_line}")
                    except Exception as e:
                        print(f"      [Error reading log summary: {e}]")
        except OSError as e:
            print(f"    Error reading archive contents: {e}", file=sys.stderr)
    sys.exit(0)


def _artifacts_restore(args, base_dir, mode):
    """Generic helper function to restore from trash or an archive."""
    import shutil
    project_dir = args.project_dir.resolve()
    print(f"--- Restoring from {mode} in: {project_dir} ---")
    archive_to_restore = None
    try:
        archives = sorted([d for d in base_dir.iterdir() if d.is_dir()], reverse=True)
        if not archives:
            print(f"{mode.capitalize()} is empty. Nothing to restore.")
            sys.exit(0)

        if args.archive_name:
            target_path = base_dir / args.archive_name
            if not target_path.is_dir():
                print(f"❌ Error: {mode.capitalize()} '{args.archive_name}' not found.")
                sys.exit(1)
            archive_to_restore = target_path
        else:
            print(f"Please select a {mode} archive to restore:")
            for i, archive_dir in enumerate(archives):
                print(f"  [{i+1}] {archive_dir.name}")

            while True:
                try:
                    selection = input(f"Enter number (1-{len(archives)}): ").strip()
                    if not selection:
                        print("Aborted.")
                        sys.exit(0)
                    choice_index = int(selection) - 1
                    if 0 <= choice_index < len(archives):
                        archive_to_restore = archives[choice_index]
                        break
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                except (EOFError, KeyboardInterrupt):
                    print("\nAborted.")
                    sys.exit(0)

    except (OSError, ValueError) as e:
        print(f"Error accessing {mode} archives: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Found archive to restore: {archive_to_restore.name}")

    artifacts = list(archive_to_restore.iterdir())
    if not artifacts:
        print("Archive is empty. Nothing to restore.")
        if mode == 'trash':
            archive_to_restore.rmdir()
            print(f"Removed empty archive: {archive_to_restore.name}")
        sys.exit(0)

    conflicts = [p.name for p in artifacts if (project_dir / p.name).exists()]
    if conflicts:
        print("\n❌ Error: The following files already exist in the project directory:", file=sys.stderr)
        for f in conflicts:
            print(f"  - {f}", file=sys.stderr)
        print("Please move or delete these conflicting files before running restore.", file=sys.stderr)
        sys.exit(1)

    restore_verb = "restored" if mode == 'trash' else "restored (copied)"
    print(f"\nThe following artifacts will be {restore_verb}:")
    for artifact in artifacts:
        print(f"  - {artifact.name}")

    if args.dry_run:
        print("\n-- DRY RUN --")
        print("The following actions would be taken:")
        action_verb = "MOVE" if mode == 'trash' else "COPY"
        for artifact in artifacts:
            print(f"  - {action_verb}: {artifact.name} from {mode} to project directory")
        if mode == 'trash':
            print(f"  - DELETE: Empty archive '{archive_to_restore.name}'")
        print("\nNo changes were made.")
        sys.exit(0)

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print("\nRestoring artifacts...")
    try:
        for artifact in artifacts:
            dest = project_dir / artifact.name
            if mode == 'trash':
                shutil.move(str(artifact), str(dest))
            else:  # archive mode
                if artifact.is_dir():
                    shutil.copytree(str(artifact), str(dest))
                else:
                    shutil.copy2(str(artifact), str(dest))
            print(f"Restored: {artifact.name}")
        if mode == 'trash':
            archive_to_restore.rmdir()
            print(f"Removed empty archive: {archive_to_restore.name}")
    except OSError as e:
        print(f"Error during restore: {e}", file=sys.stderr)
        sys.exit(1)

    if mode == 'trash':
        print("\n✅ Restore complete.")
    else:
        print("\n✅ Restore complete. Original archive remains untouched.")
    sys.exit(0)


def _artifacts_clear(args, base_dir, mode):
    """Generic helper function to clear trash or archives."""
    import shutil
    project_dir = args.project_dir.resolve()
    print(f"--- Clearing {mode} in: {project_dir} ---")
    if args.all:
        if args.dry_run:
            print("\n-- DRY RUN --")
            print(f"Would permanently delete the entire '{base_dir.name}' directory and all its contents.")
            print("\nNo changes were made.")
            sys.exit(0)
        if not args.yes:
            print(f"This will permanently delete the entire '{base_dir.name}' directory and all its contents.")
            confirm = input("Are you sure? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)
        try:
            shutil.rmtree(base_dir)
            print(f"✅ {mode.capitalize()} successfully emptied.")
        except OSError as e:
            print(f"Error emptying {mode}: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.archive_name:
        target_path = base_dir / args.archive_name
        if not target_path.is_dir():
            print(f"❌ Error: Archive '{args.archive_name}' not found.")
            sys.exit(1)

        if args.dry_run:
            print("\n-- DRY RUN --")
            print(f"Would permanently delete the archive: {args.archive_name}")
            print("\nNo changes were made.")
            sys.exit(0)
        if not args.yes:
            print(f"This will permanently delete the archive: {args.archive_name}")
            confirm = input("Are you sure? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)
        try:
            shutil.rmtree(target_path)
            print(f"✅ Archive '{args.archive_name}' deleted.")
        except OSError as e:
            print(f"Error deleting archive: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: 'clear' action requires either an archive name or the --all flag.")
        sys.exit(1)
    sys.exit(0)


def _artifacts_inspect(args, base_dir, mode):
    """Generic helper function to inspect trash or archives."""
    if not args.archive_name:
        print(f"❌ Error: 'inspect' action requires an archive name.", file=sys.stderr)
        sys.exit(1)

    archive_dir = base_dir / args.archive_name
    if not archive_dir.is_dir():
        print(f"❌ Error: Archive '{args.archive_name}' not found in {mode}.", file=sys.stderr)
        sys.exit(1)

    # Inspecting a specific file
    if args.file_name:
        file_path = archive_dir / args.file_name
        if not file_path.exists():
            print(f"❌ Error: File '{args.file_name}' not found in archive '{args.archive_name}'.", file=sys.stderr)
            sys.exit(1)
        if file_path.is_dir():
            print(f"❌ Error: '{args.file_name}' is a directory. Cannot inspect directories.", file=sys.stderr)
            sys.exit(1)

        print(f"--- Contents of {args.file_name} from {args.archive_name} ---")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                print(f.read())
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

    # Inspecting the whole archive (summary)
    else:
        print(f"--- Inspecting Archive: {archive_dir.name} ---")
        try:
            contents = sorted(list(archive_dir.iterdir()))
            if not contents:
                print("(empty)")
                sys.exit(0)

            for item in contents:
                print(f"\n--- File: {item.name} ---")
                if item.is_dir():
                    print("    (Directory)")
                    continue
                try:
                    with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = []
                        try:
                            for _ in range(10):
                                lines.append(next(f))
                        except StopIteration:
                            pass  # File has fewer than 10 lines, which is fine.

                        for line in lines:
                            print(f"    {line.strip()}")

                        # Check if there are more lines by trying to read one more.
                        try:
                            next(f)
                            print("    ...")
                        except StopIteration:
                            pass  # End of file, no more lines.
                except Exception:
                    print("    (Could not display preview - possibly a binary file)")

        except OSError as e:
            print(f"Error reading archive contents: {e}", file=sys.stderr)
            sys.exit(1)
    sys.exit(0)


def _artifacts_diff(args, base_dir, mode):
    """Generic helper function to diff a file in trash/archive with the project version."""
    import difflib

    project_dir = args.project_dir.resolve()
    archive_name = args.archive_name
    file_name = args.file_name

    if not archive_name or not file_name:
        print("❌ Error: 'diff' action requires an archive name and a file name.", file=sys.stderr)
        sys.exit(1)

    archive_dir = base_dir / archive_name
    if not archive_dir.is_dir():
        print(f"❌ Error: Archive '{archive_name}' not found in {mode}.", file=sys.stderr)
        sys.exit(1)

    stored_file_path = archive_dir / file_name
    if not stored_file_path.is_file():
        print(f"❌ Error: File '{file_name}' not found in archive '{archive_name}'.", file=sys.stderr)
        sys.exit(1)

    project_file_path = project_dir / file_name

    try:
        with open(stored_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            stored_lines = f.readlines()
    except Exception as e:
        print(f"Error reading {mode}d file: {e}", file=sys.stderr)
        sys.exit(1)

    if project_file_path.exists():
        try:
            with open(project_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                project_lines = f.readlines()
            from_file = f"a/{file_name}"
            to_file = f"b/{file_name}"
        except Exception as e:
            print(f"Error reading project file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        project_lines = []
        from_file = f"a/{file_name}"
        to_file = f"b/{file_name} (deleted)"

    diff = list(difflib.unified_diff(
        project_lines,
        stored_lines,
        fromfile=from_file,
        tofile=to_file,
    ))

    if not diff:
        print(f"✅ No differences found between the project version and the {mode}d version of '{file_name}'.")
        sys.exit(0)

    print(f"--- Diff for {file_name} ---")
    print(f"--- a/{file_name} (Project Version)")
    print(f"+++ b/{file_name} ({mode.capitalize()}d Version in {archive_name})")
    for line in diff[2:]:
        print(line, end="")

    sys.exit(0)

def run_artifacts(args, mode):
    """Manages agent artifacts (trash or archives)."""
    project_dir = args.project_dir.resolve()
    base_dir_name = ".agent_trash" if mode == 'trash' else ".agent_archives"
    base_dir = project_dir / base_dir_name

    if not base_dir.exists() or not base_dir.is_dir():
        print(f"{mode.capitalize()} directory ({base_dir_name}) not found. Nothing to do.")
        sys.exit(0)

    # Convert the Namespace object to a dictionary for easier handling
    args_dict = vars(args)

    if args.action == "list":
        _artifacts_list(base_dir, mode)
    elif args.action == "restore":
        _artifacts_restore(args, base_dir, mode)
    elif args.action == "clear":
        _artifacts_clear(args, base_dir, mode)
    elif args.action == "inspect":
        _artifacts_inspect(args, base_dir, mode)
    elif args.action == "diff":
        _artifacts_diff(args, base_dir, mode)

def run_archives(args):
    """Manages the agent archives directory."""
    print("Warning: The 'archives' command is deprecated. Use 'artifacts archive <action>' instead.", file=sys.stderr)
    # Re-package args for the new command structure
    new_args = argparse.Namespace(
        type='archive',
        action=args.action,
        archive_name=args.archive_name,
        file_name=args.file_name,
        project_dir=args.project_dir,
        all=args.all,
        yes=args.yes,
        dry_run=args.dry_run
    )
    run_artifacts(new_args, mode='archive')

def run_revert(args):
    """Discards uncommitted changes for specified files or for the entire repository."""
    import subprocess
    import shutil
    project_dir = args.project_dir.resolve()

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot revert.", file=sys.stderr)
        sys.exit(1)

    # Validate arguments
    if args.files and args.interactive:
        print("❌ Error: Cannot use --interactive mode when specifying individual files.", file=sys.stderr)
        sys.exit(1)

    files_to_revert = args.files

    # --- Mode 1: Interactive Revert ---
    if args.interactive:
        print(f"--- Interactive Revert in: {project_dir} ---")
        try:
            status_result = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            changes = [line for line in status_result.stdout.splitlines() if line]
            if not changes:
                print("✅ No uncommitted changes to revert.")
                sys.exit(0)

            print("Select files to revert (e.g., 1 3 4), or press Enter to cancel:")
            all_files = []
            for i, change in enumerate(changes):
                status, filename = change[:2], change[3:]
                all_files.append(filename)
                print(f"  [{i+1}] {status.strip()}: {filename}")

            selection = input("> ").strip()
            if not selection:
                print("Aborted.")
                sys.exit(0)

            try:
                indices = [int(i) - 1 for i in selection.split()]
                files_to_revert = [all_files[i] for i in indices if 0 <= i < len(all_files)]
            except ValueError:
                print("❌ Invalid input. Please enter numbers separated by spaces.", file=sys.stderr)
                sys.exit(1)

            if not files_to_revert:
                print("No valid files selected. Aborting.")
                sys.exit(0)

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"❌ Error checking git status: {e}", file=sys.stderr)
            sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)

    # --- Mode 2: Revert specific files (also used by interactive mode) ---
    if files_to_revert:
        print(f"--- Reverting specified files in: {project_dir} ---")

        # Get the status of all files in the repo to identify untracked files
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        all_untracked_files = {
            line[3:] for line in status_result.stdout.strip().split('\n') if line.startswith('??')
        }

        # Separate the user's list into files that are tracked vs. untracked
        tracked_to_revert = [f for f in files_to_revert if f not in all_untracked_files]
        untracked_to_revert = [f for f in files_to_revert if f in all_untracked_files]

        # Get the status of only the files the user wants to revert to confirm there are changes
        final_revert_list = []
        if files_to_revert:
            status_of_selection = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain", "--"] + files_to_revert,
                capture_output=True, text=True
            )
            final_revert_list = [line[3:] for line in status_of_selection.stdout.strip().split('\n') if line.strip()]

        if not final_revert_list:
            print("✅ No uncommitted changes to revert for the specified files.")
            sys.exit(0)

        print("\nThe following files will be reverted to their last committed state:")
        for f in final_revert_list:
            print(f"  - {f}")

        if not args.yes:
            confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        print("\nReverting files...")
        try:
            if tracked_to_revert:
                cmd = [git_path, "-C", str(project_dir), "checkout", "HEAD", "--"] + tracked_to_revert
                subprocess.run(cmd, check=True, capture_output=True)

            if untracked_to_revert:
                cmd = [git_path, "-C", str(project_dir), "clean", "-f", "--"] + untracked_to_revert
                subprocess.run(cmd, check=True, capture_output=True)

            print("✅ Specified files have been reverted.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().strip() if e.stderr else str(e)
            print(f"❌ Error during revert: {stderr}", file=sys.stderr)
            sys.exit(1)

    # --- Mode 3: Revert all changes (if no files and no interactive) ---
    elif not args.interactive:
        print(f"--- Reverting ALL uncommitted changes in: {project_dir} ---")
        try:
            status_result = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            if not status_result.stdout.strip():
                print("  ✅ No uncommitted changes to revert.")
                sys.exit(0)

            print("\nUncommitted changes (will be discarded):")
            for line in status_result.stdout.strip().split('\n'):
                print(f"  {line}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"❌ Error checking git status: {e}", file=sys.stderr)
            sys.exit(1)

        if not args.yes:
            confirm = input("\nAre you sure you want to discard ALL uncommitted changes? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        print("\nReverting changes...")
        try:
            subprocess.run(
                [git_path, "-C", str(project_dir), "reset", "--hard", "HEAD"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            subprocess.run(
                [git_path, "-C", str(project_dir), "clean", "-fd"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            print("✅ Revert complete. Working directory is now clean.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            stderr = getattr(e, 'stderr', str(e))
            if isinstance(stderr, bytes):
                stderr = stderr.decode().strip()
            print(f"❌ Error during revert: {stderr}", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)


def run_trash(args):
    """Manages the agent trash directory."""
    print("Warning: The 'trash' command is deprecated. Use 'artifacts trash <action>' instead.", file=sys.stderr)
    run_artifacts(args, mode='trash')


def run_empty_trash(args):
    """Permanently deletes the .agent_trash directory."""
    print("Warning: The 'empty-trash' command is deprecated and will be removed in a future version. "
          "Use 'trash clear --all' instead.", file=sys.stderr)
    import shutil
    project_dir = args.project_dir.resolve()
    trash_dir = project_dir / ".agent_trash"

    print(f"--- Permanently emptying trash in project: {project_dir} ---")

    if not trash_dir.exists() or not trash_dir.is_dir():
        print("Trash directory (.agent_trash) not found. Nothing to do.")
        sys.exit(0)

    # Count items for user confirmation
    trash_items = list(trash_dir.iterdir())
    if not trash_items:
        print("Trash directory is already empty.")
        # Also remove the empty .agent_trash directory itself
        try:
            trash_dir.rmdir()
            print("Removed empty .agent_trash directory.")
        except OSError as e:
            print(f"Could not remove empty .agent_trash directory: {e}", file=sys.stderr)
        sys.exit(0)

    print(f"The trash directory (.agent_trash) contains {len(trash_items)} item(s).")
    print("This action will permanently delete its contents.")

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print("\nEmptying trash...")
    try:
        shutil.rmtree(trash_dir)
        print("✅ Trash successfully emptied.")
    except OSError as e:
        print(f"Error while emptying trash: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


def run_restore(args):
    """Restores agent-generated artifacts from the most recent trash directory."""
    print("Warning: The 'restore' command is deprecated and will be removed in a future version. "
          "Use 'trash restore' instead.", file=sys.stderr)
    import shutil
    project_dir = args.project_dir.resolve()
    trash_base_dir = project_dir / ".agent_trash"

    print(f"--- Restoring artifacts in project: {project_dir} ---")

    if not trash_base_dir.exists() or not trash_base_dir.is_dir():
        print("Trash directory (.agent_trash) not found. Nothing to restore.")
        sys.exit(0)

    # Find the most recent trash directory (they are timestamped)
    try:
        latest_trash_dir = max(d for d in trash_base_dir.iterdir() if d.is_dir())
    except ValueError:
        print("No trash archives found in .agent_trash directory.")
        sys.exit(0)

    print(f"Found latest trash archive: {latest_trash_dir.name}")

    artifacts_to_restore = list(latest_trash_dir.iterdir())
    if not artifacts_to_restore:
        print("Trash archive is empty. Nothing to restore.")
        latest_trash_dir.rmdir() # Clean up empty dir
        print(f"Removed empty trash archive: {latest_trash_dir.name}")
        sys.exit(0)

    # Check for conflicts
    conflicting_files = []
    for artifact in artifacts_to_restore:
        destination_path = project_dir / artifact.name
        if destination_path.exists():
            conflicting_files.append(artifact.name)

    if conflicting_files:
        print("\n❌ Error: The following files already exist in the project directory:")
        for f in conflicting_files:
            print(f"  - {f}")
        print("Please move or delete these files manually before running restore.")
        sys.exit(1)

    print("\nThe following artifacts will be restored to the project directory:")
    for artifact in artifacts_to_restore:
        print(f"  - {artifact.name}")

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print("\nRestoring artifacts...")
    try:
        for artifact in artifacts_to_restore:
            dest = project_dir / artifact.name
            shutil.move(str(artifact), str(dest))
            print(f"Restored: {artifact.name}")

        # Clean up the now-empty trash directory
        latest_trash_dir.rmdir()
        print(f"Removed empty trash archive: {latest_trash_dir.name}")

    except OSError as e:
        print(f"Error during restore: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n✅ Restore complete.")
    sys.exit(0)


from shared.cli_utils import get_project_summary

def run_summary(args):
    """Displays a high-level summary of the project's status."""
    summary_text = get_project_summary(project_dir=args.project_dir)
    print(summary_text)
    sys.exit(0)


def _run_status_logic(project_dir):
    """The core logic for displaying the project status."""
    import subprocess
    import json
    project_dir = project_dir.resolve()
    print(f"--- Project Status: {project_dir} ---")

    # 1. Workflow Stage
    print("\n[ Workflow Stage ]")
    if (project_dir / "PROJECT_SIGNED_OFF").exists():
        print("  ✅ Project Signed Off: The project is complete and verified.")
    elif (project_dir / "QA_PASSED").exists():
        print("  🤔 QA Passed: Ready for final manager review and sign-off.")
    elif (project_dir / "COMPLETED").exists():
        print("  ⏳ Completed: Agent has finished coding, pending QA verification.")
    else:
        print("  🏃 In Progress: Agent is actively working or ready to start.")

    # 2. Feature Summary
    print("\n[ Feature Summary ]")
    feature_file = project_dir / "feature_list.json"
    if feature_file.exists():
        try:
            with open(feature_file, 'r') as f:
                features = json.load(f)
            if isinstance(features, list) and features:
                print(f"  Found {len(features)} features in feature_list.json:")
                for i, feature in enumerate(features[:5]):
                    print(f"    - {feature}")
                if len(features) > 5:
                    print("    ...")
            else:
                print("  feature_list.json is empty or invalid.")
        except json.JSONDecodeError:
            print("  Error: Could not parse feature_list.json.")
        except Exception as e:
            print(f"  An error occurred: {e}")
    else:
        print("  No feature_list.json found.")

    # 3. Last Agent Run
    print("\n[ Last Agent Run ]")
    run_id_file = project_dir / ".agent_run_id"
    if run_id_file.exists():
        run_id = run_id_file.read_text().strip()
        print(f"  Last Run ID: {run_id}")
        repo_root = Path(__file__).parent
        log_file_path = repo_root / f"agents/logs/{run_id}.log"
        try:
            display_path = log_file_path.relative_to(project_dir.parent)
        except ValueError:
            display_path = log_file_path

        if log_file_path.exists():
            try:
                with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    lines = all_lines[-5:]
                if lines:
                    print("  Log Snippet (last 5 lines):")
                    for line in lines:
                        print(f"    {line.strip()}")
                else:
                    print("  Log file is empty.")
            except Exception as e:
                print(f"  Error reading log file: {e}")
        else:
            print(f"  Log file not found at: {display_path}")
    else:
        print("  No .agent_run_id file found. Has the agent been run yet?")

    # 4. Git Status
    print("\n[ Git Status ]")
    try:
        git_path = "/usr/bin/git"
        check_repo = subprocess.run(
            [git_path, "-C", str(project_dir), "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True
        )
        if check_repo.returncode == 0 and check_repo.stdout.strip() == "true":
            result = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            if result.stdout:
                print("  Uncommitted changes detected:")
                for line in result.stdout.strip().split('\n'):
                    print(f"    {line}")
            else:
                print("  ✅ Working directory is clean.")
        else:
            print("  Directory is not a Git repository.")
    except FileNotFoundError:
        print("  Git not found. Cannot determine repository status.")
    except subprocess.CalledProcessError as e:
        print(f"  Error checking git status: {e.stderr}")
    except Exception as e:
        print(f"  An unexpected error occurred while checking git status: {e}")

def run_status(args):
    """Displays the current status of the agent project."""
    _run_status_logic(project_dir=args.project_dir)
    sys.exit(0)


def _run_history_logic(project_dir):
    """The core logic for displaying agent run history."""
    history_file = project_dir / ".agent_history"
    repo_root = Path(__file__).parent
    logs_dir = repo_root / "agents/logs"

    print(f"--- Agent Run History: {project_dir} ---")

    if not history_file.exists():
        print("No agent run history found for this project.")
        return

    try:
        with open(history_file, "r") as f:
            run_ids = [line.strip() for line in f if line.strip()]
    except IOError as e:
        print(f"Error reading history file: {e}", file=sys.stderr)
        return

    if not run_ids:
        print("History is empty.")
        return

    for i, run_id in enumerate(reversed(run_ids)):
        latest_marker = " (latest)" if i == 0 else ""
        print(f"\n[{len(run_ids)-i}] Run ID: {run_id}{latest_marker}")
        log_file = logs_dir / f"{run_id}.log"
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                first_line = lines[0].strip() if lines else ""
                timestamp = first_line.split(" - ")[0] if " - " in first_line else "[No Timestamp]"
                print(f"  Timestamp: {timestamp}")
                if lines:
                    print("  Log Summary (last 5 lines):")
                    last_lines = [line.strip() for line in lines if line.strip()][-5:]
                    for line in last_lines:
                        print(f"    {line}")
                else:
                    print("  Log file is empty.")
            except Exception as e:
                print(f"  Error reading log file: {e}")
        else:
            print("  Log file not found.")

def run_history(args):
    """Displays a history of agent runs for the project."""
    _run_history_logic(project_dir=args.project_dir)
    sys.exit(0)


def _run_diff_summary_logic(project_dir):
    """The core logic for displaying a git diff summary."""
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        return False

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot show diff summary.", file=sys.stderr)
        return False

    print(f"--- Diff Summary: {project_dir} ---")
    try:
        cmd = [git_path, "-C", str(project_dir), "diff", "--stat"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if not result.stdout.strip():
            print("✅ No uncommitted changes.")
        else:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip()
        print(f"❌ Error getting diff summary: {stderr}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        return False
    return True

def run_diff_summary(args):
    """Displays a summary of uncommitted git changes."""
    success = _run_diff_summary_logic(project_dir=args.project_dir)
    sys.exit(0 if success else 1)


import time
def _run_logs_logic(run_id=None, lines=None, follow=False, grep=None):
    """The core logic for displaying agent logs."""
    repo_root = Path(__file__).parent
    logs_dir = repo_root / "agents/logs"

    if not logs_dir.exists():
        print("Logs directory not found.")
        return False

    # --- Step 1: Determine which log file to use ---
    log_file = None
    if run_id:
        log_file = logs_dir / f"{run_id}.log"
        if not log_file.exists():
            print(f"Log file not found for Run ID: {run_id}")
            return False
    else:
        # If no run_id, we either list logs or operate on the latest one
        try:
            all_logs = sorted(logs_dir.glob('*.log'), key=lambda p: p.stat().st_mtime, reverse=True)
            # Default action: list logs
            if not all_logs and not (lines or follow or grep):
                print("--- Last 10 Agent Logs ---")
                print("No logs found.")
                print("\nUse 'logs <Run ID>' to view a specific log.")
                return True

            if not all_logs:
                print("No logs found to perform the action on.")
                return False

            # If any flags are present, use the latest log
            if lines or follow or grep:
                log_file = all_logs[0]
            else:
                # Default behavior: list the last 10 logs
                print("--- Last 10 Agent Logs ---")
                for i, log_f in enumerate(all_logs[:10]):
                    run_id_from_file = log_f.stem
                    latest_marker = " (latest)" if i == 0 else ""
                    print(f"  - {run_id_from_file}{latest_marker}")
                print("\nUse 'logs <Run ID>' or flags like --lines, --follow on the latest log.")
                return True
        except OSError as e:
            print(f"Error accessing logs directory: {e}", file=sys.stderr)
            return False

    # If we fall through, we have a log_file to process.
    if log_file:
        print(f"--- Displaying logs for: {log_file.name} ---")

    def print_filtered(line):
        if not grep or grep in line:
            print(line, end='')

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            # If not following, it's simple: read, filter, print.
            if not follow:
                log_lines = f.readlines()
                if lines is not None:
                    log_lines = log_lines[-lines:]
                for line in log_lines:
                    print_filtered(line)
                return True

            # If following, the logic is more complex.
            if lines is not None:
                # Print tail first
                all_lines = f.readlines()
                tail_lines = all_lines[-lines:]
                for line in tail_lines:
                    print_filtered(line)

            # Now, start following from the end of the file
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                print_filtered(line)

    except IOError as e:
        print(f"Error reading log file: {e}", file=sys.stderr)
        return False
    except KeyboardInterrupt:
        print("\n--- Stopped following log ---")
        return True

    return True

def run_logs(args):
    """Displays agent logs."""
    success = _run_logs_logic(
        run_id=args.run_id,
        lines=args.lines,
        follow=args.follow,
        grep=args.grep
    )
    sys.exit(0 if success else 1)


# --- Workflow Subcommand Helpers ---
from shared.cli_utils import get_workflow_stage, WORKFLOW_STAGES, WORKFLOW_ORDER

def _workflow_status(args):
    """Displays the current workflow status."""
    project_dir = args.project_dir.resolve()
    current_stage_key = get_workflow_stage(project_dir)
    current_stage = WORKFLOW_STAGES[current_stage_key]
    current_index = WORKFLOW_ORDER.index(current_stage_key)

    print(f"--- Workflow Status: {project_dir} ---")
    print(f"  Current Stage: {current_stage['name']}")

    if current_stage_key == "SIGNED_OFF":
        print("\n  Project is complete. No further workflow actions.")
    else:
        next_stage_key = WORKFLOW_ORDER[current_index + 1]
        next_stage = WORKFLOW_STAGES[next_stage_key]
        print(f"\n  Next action: 'workflow advance' to move to '{next_stage['name']}'.")


def _workflow_advance(args):
    """Advances the project to the next workflow stage."""
    project_dir = args.project_dir.resolve()
    current_stage_key = get_workflow_stage(project_dir)
    current_index = WORKFLOW_ORDER.index(current_stage_key)

    if current_stage_key == "SIGNED_OFF":
        print("Project is already at the final 'Signed Off' stage. Cannot advance further.")
        sys.exit(0)

    next_stage_key = WORKFLOW_ORDER[current_index + 1]
    next_stage = WORKFLOW_STAGES[next_stage_key]
    marker_file_path = project_dir / next_stage["file"]

    print(f"--- Advancing Workflow Stage ---")
    print(f"  Current stage: {WORKFLOW_STAGES[current_stage_key]['name']}")
    print(f"  Next stage:    {next_stage['name']}")
    print(f"  Action:        Create the marker file '{next_stage['file']}'")

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    try:
        marker_file_path.touch()
        print(f"\n✅ Successfully advanced workflow to '{next_stage['name']}'.")
    except OSError as e:
        print(f"\n❌ Error creating marker file: {e}", file=sys.stderr)
        sys.exit(1)


def _workflow_revert(args):
    """Reverts the project to the previous workflow stage."""
    project_dir = args.project_dir.resolve()
    current_stage_key = get_workflow_stage(project_dir)
    current_index = WORKFLOW_ORDER.index(current_stage_key)

    if current_stage_key == "IN_PROGRESS":
        print("Project is already at the initial 'In Progress' stage. Cannot revert further.")
        sys.exit(0)

    previous_stage_key = WORKFLOW_ORDER[current_index - 1]
    previous_stage = WORKFLOW_STAGES[previous_stage_key]
    marker_to_remove = WORKFLOW_STAGES[current_stage_key]["file"]
    marker_file_path = project_dir / marker_to_remove

    print(f"--- Reverting Workflow Stage ---")
    print(f"  Current stage:  {WORKFLOW_STAGES[current_stage_key]['name']}")
    print(f"  Previous stage: {previous_stage['name']}")
    print(f"  Action:         Delete the marker file '{marker_to_remove}'")

    if not args.yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    try:
        marker_file_path.unlink()
        print(f"\n✅ Successfully reverted workflow to '{previous_stage['name']}'.")
    except FileNotFoundError:
        print(f"\n- Warning: Marker file '{marker_to_remove}' was already missing.", file=sys.stderr)
        print(f"  Workflow is now effectively at the '{previous_stage['name']}' stage.")
    except OSError as e:
        print(f"\n❌ Error deleting marker file: {e}", file=sys.stderr)
        sys.exit(1)


def run_workflow(args):
    """Manages the agent's high-level workflow state."""
    if args.action == "status":
        _workflow_status(args)
    elif args.action == "advance":
        _workflow_advance(args)
    elif args.action == "revert":
        _workflow_revert(args)
    sys.exit(0)


def run_shell(args):
    """Starts the interactive shell."""
    shell = InteractiveShell(sys.modules[__name__])
    shell.cmdloop()
    sys.exit(0)


def run_tui(args):
    """Starts the Textual TUI."""
    try:
        from shared.tui import AgentTUI
        app = AgentTUI(project_dir=args.project_dir)
        app.run()
        sys.exit(0)
    except ImportError as e:
        print("Error: Could not import TUI dependencies. Please run 'pip install -r requirements-dev.txt'", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while running the TUI: {e}", file=sys.stderr)
        sys.exit(1)


def _find_metrics_file(run_id: str, project_dir: Path) -> Path | None:
    """Finds the final_metrics.txt file for a given run_id."""
    # 1. Check the main project directory
    metrics_file = project_dir / "final_metrics.txt"
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                content = f.read()
            if f"Run ID: {run_id}" in content:
                return metrics_file
        except IOError:
            pass

    # 2. Check archives and trash directories
    for base_dir_name in [".agent_archives", ".agent_trash"]:
        base_dir = project_dir / base_dir_name
        if base_dir.is_dir():
            for archive_dir in base_dir.iterdir():
                if archive_dir.is_dir():
                    metrics_file = archive_dir / "final_metrics.txt"
                    if metrics_file.exists():
                        try:
                            with open(metrics_file, 'r') as f:
                                content = f.read()
                            if f"Run ID: {run_id}" in content:
                                return metrics_file
                        except IOError:
                            continue
    return None


def _parse_metrics(metrics_file: Path) -> dict:
    """Parses a final_metrics.txt file into a dictionary."""
    metrics = {}
    try:
        with open(metrics_file, 'r') as f:
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    # Attempt to convert to float/int if possible
                    try:
                        if '.' in value:
                            metrics[key] = float(value)
                        else:
                            metrics[key] = int(value)
                    except ValueError:
                        metrics[key] = value
    except (IOError, FileNotFoundError) as e:
        print(f"Error reading metrics file {metrics_file}: {e}", file=sys.stderr)
        return {}
    return metrics


def _format_duration(seconds: float) -> str:
    """Formats seconds into a human-readable string (m s)."""
    seconds = float(seconds)
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes)}m {seconds:.2f}s"


def _display_metrics_table(metrics: dict, title: str):
    """Displays a formatted table of metrics."""
    print(f"--- {title} ---")
    if not metrics:
        print("No metrics available.")
        return

    # Key metrics to display in a specific order
    key_metrics = [
        "Run ID", "Agent Type", "Model", "Timestamp",
        "Total Execution Time (s)", "Total Iterations",
        "Total Errors", "LLM API Calls", "LLM Tokens Used"
    ]

    # Format values for display
    display_data = {}
    for key, value in metrics.items():
        if "Time" in key and isinstance(value, (int, float)):
            display_data[key] = _format_duration(value)
        else:
            display_data[key] = value

    max_key_len = max(len(k) for k in key_metrics if k in metrics)

    for key in key_metrics:
        if key in metrics:
            print(f"  {key.ljust(max_key_len)} : {display_data.get(key, 'N/A')}")

    # Display any other metrics that weren't in the key list
    other_metrics = {k: v for k, v in metrics.items() if k not in key_metrics}
    if other_metrics:
        print("\n  --- Other Metrics ---")
        max_other_len = max(len(k) for k in other_metrics)
        for key, value in other_metrics.items():
            print(f"  {key.ljust(max_other_len)} : {display_data.get(key, 'N/A')}")


def _benchmark_show(args):
    """Handles the 'benchmark show' action."""
    run_id = args.run_id
    project_dir = args.project_dir.resolve()

    if not run_id:
        # If no run_id, use the metrics from the current project directory
        metrics_file = project_dir / "final_metrics.txt"
        if not metrics_file.exists():
            print("❌ Error: final_metrics.txt not found in the current project directory.", file=sys.stderr)
            print("Please specify a Run ID.", file=sys.stderr)
            sys.exit(1)
        metrics = _parse_metrics(metrics_file)
        if not metrics.get("Run ID"):
             print("❌ Error: Could not determine Run ID from final_metrics.txt.", file=sys.stderr)
             sys.exit(1)
        run_id = metrics["Run ID"]
    else:
        metrics_file = _find_metrics_file(run_id, project_dir)
        if not metrics_file:
            print(f"❌ Error: Could not find metrics for Run ID: {run_id}", file=sys.stderr)
            sys.exit(1)
        metrics = _parse_metrics(metrics_file)

    _display_metrics_table(metrics, f"Metrics for Run: {run_id}")
    sys.exit(0)


def _benchmark_compare(args):
    """Handles the 'benchmark compare' action."""
    project_dir = args.project_dir.resolve()
    run_id_1, run_id_2 = args.run_id_1, args.run_id_2

    file1 = _find_metrics_file(run_id_1, project_dir)
    file2 = _find_metrics_file(run_id_2, project_dir)

    if not file1:
        print(f"❌ Error: Could not find metrics for Run ID: {run_id_1}", file=sys.stderr)
        sys.exit(1)
    if not file2:
        print(f"❌ Error: Could not find metrics for Run ID: {run_id_2}", file=sys.stderr)
        sys.exit(1)

    metrics1 = _parse_metrics(file1)
    metrics2 = _parse_metrics(file2)

    all_keys = sorted(list(set(metrics1.keys()) | set(metrics2.keys())))
    numeric_keys = [
        "Total Execution Time (s)", "Total Iterations", "Total Errors",
        "LLM API Calls", "LLM Tokens Used"
    ]

    print(f"--- Comparison: {run_id_1} vs {run_id_2} ---")
    header = f"{'Metric':<30} | {'Run: ' + run_id_1:<25} | {'Run: ' + run_id_2:<25} | {'Difference'}"
    print(header)
    print("-" * len(header))

    for key in all_keys:
        val1 = metrics1.get(key, "N/A")
        val2 = metrics2.get(key, "N/A")

        diff_str = ""
        if key in numeric_keys and isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            diff = val2 - val1
            is_improvement = (key != "Total Errors" and diff < 0) or (key == "Total Errors" and diff < 0)
            prefix = "✅ " if is_improvement else "🔻 "
            diff_str = f"{prefix}{diff:+.2f}"
            if "Time" in key:
                 val1_str = _format_duration(val1)
                 val2_str = _format_duration(val2)
                 diff_str = f"{prefix}{_format_duration(abs(diff))}"
            else:
                 val1_str = str(val1)
                 val2_str = str(val2)
        else:
            val1_str = str(val1)
            val2_str = str(val2)
            if val1_str != val2_str:
                diff_str = "(changed)"

        print(f"{key:<30} | {val1_str:<25} | {val2_str:<25} | {diff_str}")

    sys.exit(0)


def _benchmark_summary(args):
    """Handles the 'benchmark summary' action."""
    project_dir = args.project_dir.resolve()
    count = args.count
    history_file = project_dir / ".agent_history"

    if not history_file.exists():
        print("No .agent_history file found. Cannot generate summary.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(history_file, 'r') as f:
            run_ids = [line.strip() for line in f if line.strip()]
    except IOError:
        print("Error reading .agent_history file.", file=sys.stderr)
        sys.exit(1)

    print(f"--- Metrics Summary (Last {count} Runs) ---")

    metrics_list = []
    for run_id in reversed(run_ids):
        if len(metrics_list) >= count:
            break
        metrics_file = _find_metrics_file(run_id, project_dir)
        if metrics_file:
            metrics_list.append(_parse_metrics(metrics_file))

    if not metrics_list:
        print("No metrics found for any runs in the history.")
        sys.exit(0)

    # Define columns and their widths
    columns = {
        "Run ID": 20,
        "Agent": 10,
        "Time": 12,
        "Iterations": 10,
        "Errors": 8,
        "Tokens": 10,
    }
    header = (
        f"{'Run ID':<{columns['Run ID']}} | "
        f"{'Agent':<{columns['Agent']}} | "
        f"{'Time':<{columns['Time']}} | "
        f"{'Iterations':<{columns['Iterations']}} | "
        f"{'Errors':<{columns['Errors']}} | "
        f"{'Tokens':<{columns['Tokens']}}"
    )
    print(header)
    print("-" * len(header))

    for metrics in metrics_list:
        run_id = metrics.get("Run ID", "N/A")
        agent = metrics.get("Agent Type", "N/A")
        time_val = _format_duration(metrics.get("Total Execution Time (s)", 0))
        iters = metrics.get("Total Iterations", "N/A")
        errors = metrics.get("Total Errors", "N/A")
        tokens = metrics.get("LLM Tokens Used", "N/A")

        row = (
            f"{str(run_id):<{columns['Run ID']}} | "
            f"{str(agent):<{columns['Agent']}} | "
            f"{str(time_val):<{columns['Time']}} | "
            f"{str(iters):<{columns['Iterations']}} | "
            f"{str(errors):<{columns['Errors']}} | "
            f"{str(tokens):<{columns['Tokens']}}"
        )
        print(row)

    sys.exit(0)


def run_benchmark(args):
    """Dispatches benchmark actions."""
    if args.action == "show":
        _benchmark_show(args)
    elif args.action == "compare":
        _benchmark_compare(args)
    elif args.action == "summary":
        _benchmark_summary(args)


def _sprint_status(args):
    """Displays the status of the current sprint."""
    import json
    import subprocess
    import shutil

    project_dir = args.project_dir.resolve()
    sprint_plan_path = project_dir / "sprint_plan.json"

    if not sprint_plan_path.exists():
        print("❌ Error: sprint_plan.json not found. Are you in a sprint project?", file=sys.stderr)
        sys.exit(1)

    try:
        with open(sprint_plan_path, 'r') as f:
            plan = json.load(f)
        tasks = plan.get("tasks", [])
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Error reading or parsing sprint_plan.json: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"--- Sprint Status: {project_dir} ---")
    if plan.get("sprint_goal"):
        print(f"Goal: {plan['sprint_goal']}")

    if not tasks:
        print("\nNo tasks found in the sprint plan.")
        sys.exit(0)

    # Get worktree status
    active_worktrees = set()
    git_path = shutil.which("git")
    if git_path and (project_dir / ".git").is_dir():
        try:
            result = subprocess.run(
                [git_path, "-C", str(project_dir), "worktree", "list"],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) > 1 and "worktrees/" in parts[0]:
                    worktree_name = Path(parts[0]).name
                    active_worktrees.add(worktree_name)
        except subprocess.CalledProcessError:
            pass

    merged_branches = set()
    if git_path:
        try:
            main_branch = "main"
            try:
                subprocess.run([git_path, "-C", str(project_dir), "show-ref", "--verify", f"refs/heads/{main_branch}"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                main_branch = "master"

            result = subprocess.run(
                [git_path, "-C", str(project_dir), "branch", "--merged", main_branch],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.strip().split('\n'):
                branch_name = line.strip().lstrip('* ')
                if branch_name.startswith("sprint/task-"):
                    merged_branches.add(branch_name)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    print("\n--- Tasks ---")
    header = f"{'ID':<20} | {'Status':<15} | {'Title'}"
    print(header)
    print("-" * (len(header) + 5))

    for task in tasks:
        task_id = task.get("id")
        title = task.get("title", "No Title")
        worktree_name = f"sprint-task-{task_id}"
        branch_name = f"sprint/task-{task_id}"

        status = "Pending"
        if branch_name in merged_branches:
            status = "✅ Merged"
        elif worktree_name in active_worktrees:
            status = "🏃 In Progress"

        print(f"{task_id:<20} | {status:<15} | {title}")

    sys.exit(0)


def run_sprint_command(args):
    """Dispatches sprint actions."""
    if args.action == "status":
        _sprint_status(args)
        sys.exit(0)

    if not args.task_id:
        print("❌ Error: 'diff' and 'merge' actions require a task_id.", file=sys.stderr)
        sys.exit(1)

    worktree_name = f"sprint-task-{args.task_id}"

    mock_args = argparse.Namespace(
        worktree_name=worktree_name,
        project_dir=args.project_dir,
        yes=getattr(args, 'yes', False),
        force=False,
        clean=getattr(args, 'clean', False)
    )

    project_dir = args.project_dir.resolve()
    worktrees_base_dir = project_dir / "worktrees"
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found.", file=sys.stderr)
        sys.exit(1)

    if args.action == "diff":
        _worktree_diff(mock_args, git_path, worktrees_base_dir)
    elif args.action == "merge":
        _worktree_merge(mock_args, git_path, project_dir, worktrees_base_dir)


async def run_plan(args):
    """Generates a feature plan from a spec file without executing it."""
    # This is a stripped down version of the main() function's setup
    logger, _ = setup_logger(name="plan_logger", log_file=None, verbose=args.verbose, console_output=True)

    logger.info("--- Generating Agent Plan ---")

    # Basic validation
    if not args.spec or not Path(args.spec).exists():
        logger.error("❌ Error: A valid --spec file is required for the 'plan' command.")
        sys.exit(1)

    # Load config from file to respect profiles and base settings
    ensure_config_exists()
    file_config = load_config_from_file(profile=args.profile)

    def resolve(cli_arg, config_key, default_val):
        if cli_arg is not None:
            return cli_arg
        if config_key in file_config:
            return file_config[config_key]
        return default_val

    # Create a minimal config for planning
    config = Config(
        project_dir=args.project_dir,
        agent_type=args.agent,
        model=resolve(args.model, "model", None),
        spec_file=args.spec,
        verbose=args.verbose,
        # Force settings for planning mode
        max_iterations=1,
        stream_output=False,
    )

    project_name = os.environ.get("PROJECT_NAME", config.project_dir.resolve().name)

    from shared.utils import generate_agent_id
    try:
        spec_content = config.spec_file.read_text()
        agent_id = generate_agent_id(project_name, spec_content, args.agent)
        config.agent_id = agent_id
    except Exception as e:
        logger.warning(f"Could not generate agent ID: {e}")
        config.agent_id = generate_agent_id(project_name, "", args.agent)

    logger.info(f"Generating plan for spec: {config.spec_file}")
    logger.info(f"Using agent: {config.agent_type}, Model: {config.model or 'default'}")

    # Dispatch to the correct agent type
    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }
    agent_class = agent_class_map.get(config.agent_type)

    if not agent_class:
        logger.error(f"Unknown agent type: {config.agent_type}")
        sys.exit(1)

    agent = agent_class(config)

    try:
        # This method will be created in the next step
        plan_generated = await agent.run_planning_session()

        if plan_generated:
            feature_file = config.project_dir / "feature_list.json"
            if feature_file.exists():
                logger.info("\n--- Generated Plan (feature_list.json) ---")
                # Use print to avoid logger formatting for the JSON output
                print(feature_file.read_text())
                logger.info("------------------------------------")
                logger.info("✅ Plan generated successfully.")
            else:
                logger.error("\n❌ Agent finished but did not produce a plan (feature_list.json).")
        else:
            logger.error("\n❌ Agent failed to generate a plan.")

    except Exception as e:
        logger.error(f"An error occurred during planning: {e}", exc_info=True)
        sys.exit(1)

    sys.exit(0)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Autonomous Coding Agent")

    # Core Configuration
    core_group = parser.add_argument_group("Core Configuration")
    core_group.add_argument(
        "--profile",
        type=str,
        help="Select a configuration profile from agent_config.yaml.",
    )
    core_group.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="Directory where the project will be created/modified (default: current directory)",
    )
    core_group.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)",
    )
    core_group.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default). Can also be set via config.",
    )
    core_group.add_argument(
        "-s", "--spec",
        type=Path,
        help="Path to app_spec.txt (required for new projects)",
    )
    core_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    # Execution Control
    exec_group = parser.add_argument_group("Execution Control")
    exec_group.add_argument(
        "--max-iterations",
        type=int,
        help="Maximum number of agent iterations. Can also be set via config.",
    )
    exec_group.add_argument(
        "--timeout",
        type=float,
        help="Timeout in seconds for agent execution (default: 600.0). Can also be set via config.",
    )
    exec_group.add_argument(
        "--max-error-wait",
        type=float,
        help="Maximum wait time in seconds for agent error backoff (default: 600.0). Can also be set via config.",
    )
    exec_group.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output",
    )

    # Manager Agent
    manager_group = parser.add_argument_group("Manager Agent")
    manager_group.add_argument(
        "--manager-frequency",
        type=int,
        help="How often the manager agent runs (default: 10 iterations). Can also be set via config.",
    )
    manager_group.add_argument(
        "--manager-model",
        type=str,
        help="Model to use for the manager agent. Can also be set via config.",
    )
    manager_group.add_argument(
        "--manager-first",
        action="store_true",
        help="Run the manager agent before the first coding session",
    )

    # Dashboard
    dash_group = parser.add_argument_group("Dashboard")
    dash_group.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable the standalone dashboard server (enabled by default)",
    )
    dash_group.add_argument(
        "--dashboard-url",
        default="http://localhost:7654",
        help="URL of the dashboard server (default: http://localhost:7654)",
    )
    dash_group.add_argument(
        "--login",
        action="store_true",
        help="Run the agent in login/authentication mode (exit after login)",
    )

    # Sprint Mode
    sprint_group = parser.add_argument_group("Sprint Mode")
    sprint_group.add_argument(
        "--sprint",
        action="store_true",
        help="Run in Sprint Mode (Concurrent Agents)",
    )
    sprint_group.add_argument(
        "--max-agents",
        type=int,
        help="Maximum number of simultaneous agents in Sprint Mode. Can also be set via config.",
    )

    # Jira Integration
    jira_group = parser.add_argument_group("Jira Integration")
    jira_exclusive = jira_group.add_mutually_exclusive_group()
    jira_exclusive.add_argument(
        "--jira-ticket",
        type=str,
        help="Jira ticket ID to work on (e.g., PROJ-123)",
    )
    jira_exclusive.add_argument(
        "--jira-label",
        type=str,
        help="Jira label to search for (picks first 'To Do' ticket)",
    )

    # Advanced
    adv_group = parser.add_argument_group("Advanced")
    adv_group.add_argument(
        "--verify-creation",
        action="store_true",
        help="Run verification test (dummy mode)",
    )
    adv_group.add_argument(
        "--dind",
        "--docker-in-docker",
        action="store_true",
        help="Enable Docker-in-Docker support (mounts docker socket). Can also be set via config.",
    )
    adv_group.add_argument(
        "--dry-run",
        action="store_true",
        help="DEPRECATED: Use the 'show-config' command instead. Prints the final configuration and exits.",
    )

    # Subparsers for commands like 'configure'
    subparsers = parser.add_subparsers(dest="command", help="sub-command help")
    parser_configure = subparsers.add_parser("configure", help="Run interactive configuration setup")
    parser_validate = subparsers.add_parser("validate", help="Validate the agent_config.yaml file")
    parser_list_agents = subparsers.add_parser("list-agents", help="List available agents")
    parser_show_config = subparsers.add_parser("show-config", help="Show the final resolved configuration and exit")

    # Subparser for 'doctor'
    parser_doctor = subparsers.add_parser("doctor", help="Run a comprehensive health check on the environment")
    parser_doctor.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check (default: current directory)",
    )

    # Subparser for 'status'
    parser_status = subparsers.add_parser("status", help="Show the current status of the agent project")
    parser_status.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check status for (default: current directory)",
    )

    # Subparser for 'summary'
    parser_summary = subparsers.add_parser("summary", help="Show a high-level summary of the agent project")
    parser_summary.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to summarize (default: current directory)",
    )

    # Subparser for 'history'
    parser_history = subparsers.add_parser("history", help="Show the history of agent runs for the project")
    parser_history.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check history for (default: current directory)",
    )

    # Subparser for 'diff-summary'
    parser_diff_summary = subparsers.add_parser("diff-summary", help="Show a summary of uncommitted git changes")
    parser_diff_summary.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check for changes (default: current directory)",
    )

    # Subparser for 'logs'
    parser_logs = subparsers.add_parser("logs", help="Show agent logs with advanced filtering")
    parser_logs.add_argument(
        "run_id",
        nargs="?",
        help="The Run ID of the log to view. If omitted, lists recent logs or operates on the latest.",
    )
    parser_logs.add_argument(
        "-n", "--lines",
        type=int,
        help="Number of recent lines to display.",
    )
    parser_logs.add_argument(
        "-f", "--follow",
        action="store_true",
        help="Follow the log output in real-time.",
    )
    parser_logs.add_argument(
        "-g", "--grep",
        type=str,
        help="Filter log lines to only those containing this string.",
    )

    # Subparser for 'clean'
    parser_clean = subparsers.add_parser("clean", help="Move agent-generated artifacts to a trash directory")
    parser_clean.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to clean (default: current directory)",
    )
    parser_clean.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )
    clean_exclusive_group = parser_clean.add_mutually_exclusive_group()
    clean_exclusive_group.add_argument(
        "--force",
        action="store_true",
        help="Permanently delete artifacts instead of moving them to the trash directory",
    )
    clean_exclusive_group.add_argument(
        "--archive",
        action="store_true",
        help="Archive artifacts to the `.agent_archives/` directory instead of moving them to trash",
    )
    clean_exclusive_group.add_argument(
        "--list",
        action="store_true",
        help="List the artifacts that would be cleaned without taking any action",
    )

    # Subparser for 'archive'
    parser_archive = subparsers.add_parser("archive", help="Archive all agent-generated artifacts to a timestamped directory")
    parser_archive.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to clean (default: current directory)",
    )

    # Subparser for 'empty-trash'
    parser_empty_trash = subparsers.add_parser("empty-trash", help="DEPRECATED: Use 'trash clear --all' instead.")
    parser_empty_trash.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the trash is located (default: current directory)",
    )
    parser_empty_trash.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    # Subparser for 'restore'
    parser_restore = subparsers.add_parser("restore", help="DEPRECATED: Use 'trash restore' instead.")
    parser_restore.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the trash is located (default: current directory)",
    )
    parser_restore.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    # Subparser for 'trash'
    parser_trash = subparsers.add_parser("trash", help="Manage the agent trash directory")
    parser_trash.add_argument(
        "action",
        choices=["list", "restore", "clear", "inspect", "diff"],
        help="Action to perform on the trash",
    )
    parser_trash.add_argument(
        "archive_name",
        nargs="?",
        help="The name of the trash archive to restore, clear, or inspect (e.g., trash-2023-10-27_12-30-00)",
    )
    parser_trash.add_argument(
        "file_name",
        nargs="?",
        help="The name of the file to inspect within the archive (for 'inspect' action only)",
    )
    parser_trash.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the trash is located",
    )
    parser_trash.add_argument(
        "--all",
        action="store_true",
        help="Option for 'clear' action to remove all archives",
    )
    parser_trash.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts",
    )
    parser_trash.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes",
    )

    # Subparser for 'revert'
    parser_revert = subparsers.add_parser("revert", help="Discard uncommitted changes to specified files or all files")
    parser_revert.add_argument(
        "files",
        nargs="*",
        help="Specific file(s) to revert. If not provided, all uncommitted changes will be discarded.",
    )
    parser_revert.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to revert changes in (default: current directory)",
    )
    parser_revert.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactively select which files to revert.",
    )
    parser_revert.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    # Subparser for 'worktrees'
    parser_worktrees = subparsers.add_parser("worktrees", help="Manage agent-created git worktrees")
    parser_worktrees.add_argument(
        "action",
        choices=["list", "show", "clean", "revert", "create", "merge", "diff", "manage"],
        help="Action to perform on the worktrees",
    )
    parser_worktrees.add_argument(
        "worktree_name",
        nargs="?",
        help="The name of the worktree to create, show, or clean (e.g., 'agent-sprint-task-1')",
    )
    parser_worktrees.add_argument(
        "--branch",
        type=str,
        help="Specify a branch name to create for the worktree (for 'create' action)",
    )
    parser_worktrees.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the worktrees are located",
    )
    parser_worktrees.add_argument(
        "--force",
        action="store_true",
        help="Force removal of the worktree, even if it has uncommitted changes (for 'clean' action)",
    )
    parser_worktrees.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts (for 'clean' action)",
    )
    parser_worktrees.add_argument(
        "--clean",
        action="store_true",
        help="Remove the worktree after a successful merge (for 'merge' action)",
    )

    # Subparser for 'snapshot'
    parser_snapshot = subparsers.add_parser("snapshot", help="Manage snapshots of key agent artifacts")
    parser_snapshot.add_argument(
        "action",
        choices=["create", "diff"],
        help="Action to perform: 'create' a new snapshot or 'diff' against an existing one.",
    )
    parser_snapshot.add_argument(
        "name",
        nargs="?",
        help="Name of the snapshot. Optional for 'create', required for 'diff'.",
    )
    parser_snapshot.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)",
    )
    parser_snapshot.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt for 'create' action",
    )

    # Subparser for 'archives' - mirrors 'trash' but for .agent_archives/
    parser_archives = subparsers.add_parser("archives", help="Manage the agent archives directory")
    parser_archives.add_argument(
        "action",
        choices=["list", "restore", "clear", "inspect", "diff"],
        help="Action to perform on the archives",
    )
    parser_archives.add_argument(
        "archive_name",
        nargs="?",
        help="The name of the archive to restore, clear, or inspect",
    )
    parser_archives.add_argument(
        "file_name",
        nargs="?",
        help="The name of the file to inspect or diff within the archive",
    )
    parser_archives.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the archives are located",
    )
    parser_archives.add_argument(
        "--all",
        action="store_true",
        help="Option for 'clear' action to remove all archives",
    )
    parser_archives.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts",
    )
    parser_archives.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes",
    )

    # --- New 'artifacts' command ---
    parser_artifacts = subparsers.add_parser(
        "artifacts",
        help="Unified command to manage agent-generated artifacts (trash and archives)"
    )
    artifacts_subparsers = parser_artifacts.add_subparsers(
        dest="type",
        required=True,
        help="Specify artifact type"
    )

    def add_artifact_actions(subparser):
        """Helper to add common action arguments to trash/archive subparsers."""
        subparser.add_argument(
            "action",
            choices=["list", "restore", "clear", "inspect", "diff"],
            help="Action to perform on the artifacts",
        )
        subparser.add_argument(
            "archive_name",
            nargs="?",
            help="The name of the archive to restore, clear, or inspect",
        )
        subparser.add_argument(
            "file_name",
            nargs="?",
            help="The name of the file to inspect or diff within the archive",
        )
        subparser.add_argument(
            "-p", "--project-dir",
            type=Path,
            default=Path("."),
            help="The project directory where the artifacts are located",
        )
        subparser.add_argument(
            "--all",
            action="store_true",
            help="Option for 'clear' action to remove all archives",
        )
        subparser.add_argument(
            "-y", "--yes",
            action="store_true",
            help="Skip confirmation prompts",
        )
        subparser.add_argument(
            "-n", "--dry-run",
            action="store_true",
            help="Show what would be done without making any changes",
        )

    # Trash sub-command for 'artifacts'
    parser_artifacts_trash = artifacts_subparsers.add_parser(
        "trash",
        help="Manage the agent trash directory (.agent_trash)"
    )
    add_artifact_actions(parser_artifacts_trash)

    # Archive sub-command for 'artifacts'
    parser_artifacts_archive = artifacts_subparsers.add_parser(
        "archive",
        help="Manage the agent archives directory (.agent_archives)"
    )
    add_artifact_actions(parser_artifacts_archive)

    # --- New 'workflow' command ---
    parser_workflow = subparsers.add_parser(
        "workflow",
        help="Manually manage the agent's high-level workflow state (e.g., advancing from QA to Sign-off)."
    )
    parser_workflow.add_argument(
        "action",
        choices=["status", "advance", "revert"],
        help="Action to perform: 'status' to check, 'advance' to move forward, 'revert' to move back.",
    )
    parser_workflow.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to manage the workflow for (default: current directory)",
    )
    parser_workflow.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts for 'advance' or 'revert' actions.",
    )


    # --- New 'plan' command ---
    parser_plan = subparsers.add_parser(
        "plan",
        help="Generate a feature plan from a spec file without executing any code."
    )
    parser_plan.add_argument(
        "-s", "--spec",
        type=Path,
        required=True,
        help="Path to the application specification file (e.g., app_spec.txt).",
    )
    parser_plan.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="Directory where the plan file will be generated (default: current directory).",
    )
    parser_plan.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use for planning (default: gemini).",
    )
    parser_plan.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use for planning (overrides agent's default).",
    )
    parser_plan.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging during the planning phase.",
    )
    parser_plan.add_argument(
        "--profile",
        type=str,
        help="Select a configuration profile from agent_config.yaml.",
    )

    # Subparser for 'shell'
    parser_shell = subparsers.add_parser("shell", help="Start an interactive shell session")

    # Subparser for 'tui'
    parser_tui = subparsers.add_parser("tui", help="Start the interactive Textual TUI")
    parser_tui.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to view in the TUI (default: current directory)",
    )

    # --- New 'completion' command ---
    parser_completion = subparsers.add_parser(
        "completion",
        help="Display shell completion scripts. To install, use: 'eval \"$(main.py completion)\"'",
    )

    # --- New 'benchmark' command ---
    parser_benchmark = subparsers.add_parser(
        "benchmark",
        help="Analyze and compare performance metrics from agent runs."
    )
    benchmark_subparsers = parser_benchmark.add_subparsers(
        dest="action",
        required=True,
        help="Specify benchmark action"
    )

    # Benchmark 'show' action
    parser_benchmark_show = benchmark_subparsers.add_parser(
        "show",
        help="Display performance metrics for a specific agent run."
    )
    parser_benchmark_show.add_argument(
        "run_id",
        nargs="?",
        help="The Run ID to inspect. If omitted, shows metrics for the latest run in the current project.",
    )
    parser_benchmark_show.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the run occurred.",
    )

    # Benchmark 'compare' action
    parser_benchmark_compare = benchmark_subparsers.add_parser(
        "compare",
        help="Compare the performance metrics of two agent runs side-by-side."
    )
    parser_benchmark_compare.add_argument("run_id_1", help="The first Run ID for comparison.")
    parser_benchmark_compare.add_argument("run_id_2", help="The second Run ID for comparison.")
    parser_benchmark_compare.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the runs occurred.",
    )

    # Benchmark 'summary' action
    parser_benchmark_summary = benchmark_subparsers.add_parser(
        "summary",
        help="Display a summary table of metrics from recent agent runs."
    )
    parser_benchmark_summary.add_argument(
        "-n", "--count",
        type=int,
        default=10,
        help="Number of recent runs to include in the summary (default: 10).",
    )
    parser_benchmark_summary.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to generate the summary from.",
    )

    # --- New 'sprint' command ---
    parser_sprint = subparsers.add_parser(
        "sprint",
        help="Observe and manage sprint progress."
    )
    sprint_subparsers = parser_sprint.add_subparsers(
        dest="action",
        required=True,
        help="Specify sprint action"
    )

    # Sprint 'status' action
    parser_sprint_status = sprint_subparsers.add_parser(
        "status",
        help="Display the status of all tasks in the current sprint."
    )
    parser_sprint_status.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory for the sprint.",
    )

    # Sprint 'diff' action
    parser_sprint_diff = sprint_subparsers.add_parser(
        "diff",
        help="Show the git diff for a specific sprint task."
    )
    parser_sprint_diff.add_argument("task_id", help="The ID of the task to diff.")
    parser_sprint_diff.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory for the sprint.",
    )

    # Sprint 'merge' action
    parser_sprint_merge = sprint_subparsers.add_parser(
        "merge",
        help="Merge a completed sprint task back into the main branch."
    )
    parser_sprint_merge.add_argument("task_id", help="The ID of the task to merge.")
    parser_sprint_merge.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory for the sprint.",
    )
    parser_sprint_merge.add_argument(
        "--clean",
        action="store_true",
        help="Remove the worktree and branch after a successful merge.",
    )
    parser_sprint_merge.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts.",
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    return parser.parse_args(argv)


def _worktree_merge(args, git_path, project_dir, worktrees_base_dir):
    """Helper function to merge a worktree branch back into the main branch."""
    import subprocess

    if not args.worktree_name:
        print("❌ Error: 'merge' action requires a worktree name.", file=sys.stderr)
        sys.exit(1)

    worktree_name = args.worktree_name
    worktree_path = worktrees_base_dir / worktree_name
    if not worktree_path.is_dir():
        print(f"❌ Error: Worktree '{worktree_name}' not found at '{worktree_path}'.", file=sys.stderr)
        sys.exit(1)

    print(f"--- Merging worktree: {worktree_name} ---")

    # 1. Get the branch name associated with the worktree
    branch_name = None
    try:
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "worktree", "list", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        current_worktree: dict = {}
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                if current_worktree:
                    path = Path(current_worktree.get("worktree", ""))
                    if path.resolve() == worktree_path.resolve():
                        branch_ref = current_worktree.get("branch", "")
                        branch_name = branch_ref.split('/')[-1]
                        break
                current_worktree = {}
            else:
                key, value = line.split(" ", 1)
                current_worktree[key] = value
        if not branch_name and current_worktree: # Check last block
             path = Path(current_worktree.get("worktree", ""))
             if path.resolve() == worktree_path.resolve():
                 branch_ref = current_worktree.get("branch", "")
                 branch_name = branch_ref.split('/')[-1]

        if not branch_name:
            print(f"❌ Error: Could not determine branch for worktree '{worktree_name}'.", file=sys.stderr)
            sys.exit(1)
        print(f"  - Found worktree branch: {branch_name}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting worktree branch: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    # 2. Check for and commit uncommitted changes in the worktree
    try:
        status_result = subprocess.run(
            [git_path, "-C", str(worktree_path), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if status_result.stdout.strip():
            print("  - Uncommitted changes detected. Staging and committing...")
            # Add all changes
            subprocess.run(
                [git_path, "-C", str(worktree_path), "add", "."],
                check=True, capture_output=True
            )
            # Commit changes
            commit_message = f"Autocommit: Worktree merge for {worktree_name}"
            subprocess.run(
                [git_path, "-C", str(worktree_path), "commit", "-m", commit_message],
                check=True, capture_output=True
            )
            print(f"  - Created commit on branch '{branch_name}'.")
        else:
            print("  - No uncommitted changes in worktree.")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode().strip() if e.stderr else str(e)
        print(f"❌ Error committing changes in worktree: {stderr}", file=sys.stderr)
        sys.exit(1)

    # 3. Checkout main branch and merge
    # For simplicity, assuming 'main'. A more robust solution might detect the default branch.
    main_branch = "main"
    print(f"  - Checking out '{main_branch}' branch in main repository...")
    try:
        subprocess.run(
            [git_path, "-C", str(project_dir), "checkout", main_branch],
            check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        if "did not match any file(s) known to git" in e.stderr:
             main_branch = "master" # Fallback to master
             print(f"  - '{main_branch}' not found, trying 'master'...")
             try:
                 subprocess.run(
                     [git_path, "-C", str(project_dir), "checkout", main_branch],
                     check=True, capture_output=True, text=True
                 )
             except subprocess.CalledProcessError as e2:
                 stderr = e2.stderr.strip()
                 print(f"❌ Error checking out '{main_branch}': {stderr}", file=sys.stderr)
                 sys.exit(1)
        else:
             stderr = e.stderr.strip()
             print(f"❌ Error checking out '{main_branch}': {stderr}", file=sys.stderr)
             sys.exit(1)


    print(f"  - Merging branch '{branch_name}' into '{main_branch}'...")
    try:
        merge_result = subprocess.run(
            [git_path, "-C", str(project_dir), "merge", "--no-ff", branch_name],
            check=True, capture_output=True, text=True
        )
        print("  - Merge successful.")
        print("\n--- Merge Output ---")
        print(merge_result.stdout.strip())
        print("--------------------")

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip()
        print(f"❌ Error merging branch: {stderr}", file=sys.stderr)
        print("  - Merge conflict detected or another error occurred. Aborting merge.")
        # Attempt to abort the merge to leave the repo in a clean state
        subprocess.run([git_path, "-C", str(project_dir), "merge", "--abort"])
        sys.exit(1)

    # 4. Optionally clean up the worktree and branch
    if args.clean:
        print("\n--- Cleaning up worktree and branch ---")
        if not args.yes:
            confirm = input(f"This will remove the worktree '{worktree_name}' and delete the branch '{branch_name}'. Are you sure? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Cleanup aborted. Worktree and branch preserved.")
                print("\n✅ Merge complete.")
                sys.exit(0)

        # Remove worktree
        try:
            print(f"  - Removing worktree '{worktree_name}'...")
            subprocess.run(
                [git_path, "-C", str(project_dir), "worktree", "remove", worktree_name],
                check=True, capture_output=True, text=True
            )
            print(f"  - Successfully removed worktree.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.strip()
            print(f"❌ Error removing worktree: {stderr}", file=sys.stderr)
            # Don't exit, still try to delete branch

        # Delete branch
        try:
            print(f"  - Deleting branch '{branch_name}'...")
            subprocess.run(
                [git_path, "-C", str(project_dir), "branch", "-d", branch_name],
                check=True, capture_output=True, text=True
            )
            print(f"  - Successfully deleted branch.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.strip()
            print(f"❌ Error deleting branch: {stderr}", file=sys.stderr)
            sys.exit(1)

        print("\n✅ Merge and cleanup complete.")
    else:
        print("\n✅ Merge complete. Worktree and branch preserved.")

    sys.exit(0)


def _worktree_diff(args, git_path, worktrees_base_dir):
    """Helper function to show a diff of the worktree against the main repo's HEAD."""
    import subprocess

    if not args.worktree_name:
        print("❌ Error: 'diff' action requires a worktree name.", file=sys.stderr)
        sys.exit(1)

    worktree_name = args.worktree_name
    worktree_path = worktrees_base_dir / worktree_name
    if not worktree_path.is_dir():
        print(f"❌ Error: Worktree '{worktree_name}' not found at '{worktree_path}'.", file=sys.stderr)
        sys.exit(1)

    print(f"--- Diff for worktree: {worktree_name} (compared to main repo HEAD) ---")

    try:
        # We run 'diff' from within the worktree's directory.
        # This automatically compares the worktree's state against the main repo's HEAD.
        result = subprocess.run(
            [git_path, "-C", str(worktree_path), "diff", "HEAD"],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            # This could happen if git itself fails, which is unlikely here.
            print(f"❌ Error running git diff: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        if not result.stdout.strip():
            print("✅ No changes detected. Worktree is in sync with HEAD.")
        else:
            # Print the diff output directly
            print(result.stdout)

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode().strip() if e.stderr else str(e)
        print(f"❌ Error getting diff for worktree: {stderr}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


def _worktree_manage(args, git_path, project_dir, worktrees_base_dir):
    """Helper function for interactive worktree management."""
    import subprocess

    # 1. Get the list of worktrees
    try:
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "worktree", "list", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        worktrees = []
        current_worktree: dict = {}
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                if current_worktree:
                    worktree_path = Path(current_worktree.get("worktree", ""))
                    if worktrees_base_dir in worktree_path.parents:
                        worktrees.append(current_worktree)
                current_worktree = {}
            else:
                key, value = line.split(" ", 1)
                current_worktree[key] = value
        if current_worktree:
            worktree_path = Path(current_worktree.get("worktree", ""))
            if worktrees_base_dir in worktree_path.parents:
                worktrees.append(current_worktree)

        if not worktrees:
            print("No active agent worktrees found to manage.")
            sys.exit(0)

    except subprocess.CalledProcessError as e:
        print(f"❌ Error listing worktrees: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    # 2. Prompt user to select a worktree
    print("--- Interactive Worktree Management ---")
    print("Please select a worktree to manage:")
    for i, wt in enumerate(worktrees):
        path = Path(wt['worktree'])
        branch = wt.get('branch', 'detached HEAD').split('/')[-1]
        print(f"  [{i+1}] {path.name} (branch: {branch})")

    selected_worktree = None
    while True:
        try:
            selection = input(f"Enter number (1-{len(worktrees)}), or press Enter to cancel: ").strip()
            if not selection:
                print("Aborted.")
                sys.exit(0)
            choice_index = int(selection) - 1
            if 0 <= choice_index < len(worktrees):
                selected_worktree_path = Path(worktrees[choice_index]['worktree'])
                selected_worktree = selected_worktree_path.name
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)

    print(f"\nManaging worktree: {selected_worktree}")

    # 3. Display menu and get action
    actions = ["show", "diff", "merge", "revert", "clean"]
    while True:
        print("\nAvailable actions:")
        for i, action in enumerate(actions):
            print(f"  [{i+1}] {action.capitalize()}")

        try:
            action_selection = input(f"Select an action (1-{len(actions)}), or press Enter to exit: ").strip()
            if not action_selection:
                print("Exiting.")
                sys.exit(0)
            action_index = int(action_selection) - 1
            if 0 <= action_index < len(actions):
                selected_action = actions[action_index]
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            sys.exit(0)

    # 4. Execute the action
    mock_args = argparse.Namespace(
        worktree_name=selected_worktree,
        project_dir=project_dir,
        yes=False,
        force=False,
        clean=False,
    )

    print(f"\n--- Executing '{selected_action.upper()}' on '{selected_worktree}' ---")

    if selected_action == "show":
        worktree_path = worktrees_base_dir / selected_worktree
        try:
            result = subprocess.run(
                [git_path, "-C", str(worktree_path), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            if result.stdout.strip():
                print("Uncommitted changes:")
                for line in result.stdout.strip().split('\n'):
                    print(f"  {line}")
            else:
                print("✅ Worktree is clean.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error getting worktree status: {e.stderr}", file=sys.stderr)

    elif selected_action == "diff":
        _worktree_diff(mock_args, git_path, worktrees_base_dir)

    elif selected_action == "merge":
        print("For merge, you can choose to clean up the worktree afterwards.")
        clean_choice = input("Clean up worktree and branch after successful merge? [y/N]: ").strip().lower()
        mock_args.clean = (clean_choice == 'y')
        _worktree_merge(mock_args, git_path, project_dir, worktrees_base_dir)

    elif selected_action == "revert":
        worktree_path = worktrees_base_dir / selected_worktree
        try:
            status_result = subprocess.run(
                [git_path, "-C", str(worktree_path), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            if not status_result.stdout.strip():
                print("✅ No uncommitted changes to revert.")
            else:
                print("\nUncommitted changes (will be discarded):")
                for line in status_result.stdout.strip().split('\n'):
                    print(f"  {line}")

                confirm = input("\nAre you sure you want to discard ALL uncommitted changes in this worktree? [y/N]: ").strip().lower()
                if confirm == 'y':
                     print("\nReverting changes...")
                     subprocess.run(
                         [git_path, "-C", str(worktree_path), "reset", "--hard", "HEAD"],
                         check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                     )
                     subprocess.run(
                         [git_path, "-C", str(worktree_path), "clean", "-fd"],
                         check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                     )
                     print("✅ Revert complete. Worktree is now clean.")
                else:
                    print("Aborted.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().strip() if e.stderr else str(e)
            print(f"❌ Error during revert: {stderr}", file=sys.stderr)

    elif selected_action == "clean":
        print("This will remove the worktree. This can be forced if there are uncommitted changes.")
        force_choice = input("Force removal even with uncommitted changes? [y/N]: ").strip().lower()
        mock_args.force = (force_choice == 'y')
        confirm = input(f"Are you sure you want to remove the worktree '{selected_worktree}'? [y/N]: ").strip().lower()
        if confirm == 'y':
            try:
                cmd = [git_path, "-C", str(project_dir), "worktree", "remove"]
                if mock_args.force:
                    cmd.append("--force")
                cmd.append(selected_worktree)

                subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"✅ Removed worktree: {selected_worktree}")
            except subprocess.CalledProcessError as e:
                 stderr = e.stderr.strip()
                 print(f"❌ Error removing worktree '{selected_worktree}': {stderr}", file=sys.stderr)
        else:
            print("Aborted.")

    sys.exit(0)


def run_worktrees(args):
    """Manages agent-created git worktrees."""
    project_dir = args.project_dir.resolve()
    worktrees_base_dir = project_dir / "worktrees"

    # --- Pre-flight Checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot manage worktrees.", file=sys.stderr)
        sys.exit(1)

    # --- Action: create ---
    if args.action == "create":
        if not args.worktree_name:
            print("❌ Error: 'create' action requires a worktree name.", file=sys.stderr)
            sys.exit(1)

        worktree_path = worktrees_base_dir / args.worktree_name
        if worktree_path.exists():
            print(f"❌ Error: Worktree path '{worktree_path}' already exists.", file=sys.stderr)
            sys.exit(1)

        # If branch is not specified, it defaults to the worktree name
        branch_name = args.branch if args.branch else args.worktree_name

        # Ensure the base directory for worktrees exists
        worktrees_base_dir.mkdir(parents=True, exist_ok=True)

        print(f"--- Creating new worktree: {args.worktree_name} ---")
        print(f"  Directory: ./{worktree_path.relative_to(project_dir)}")
        print(f"  Branch:    {branch_name}")

        try:
            cmd = [git_path, "-C", str(project_dir), "worktree", "add", "-b", branch_name, str(worktree_path), "HEAD"]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"\n✅ Successfully created worktree '{args.worktree_name}' on branch '{branch_name}'.")

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.strip()
            print(f"❌ Error creating worktree: {stderr}", file=sys.stderr)
            # Clean up partial directory if git failed
            if worktree_path.exists():
                shutil.rmtree(worktree_path)
            sys.exit(1)
        sys.exit(0)

    # --- Action: list ---
    elif args.action == "list":
        print(f"--- Listing Agent Worktrees in: {worktrees_base_dir} ---")
        try:
            result = subprocess.run(
                [git_path, "-C", str(project_dir), "worktree", "list", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            worktrees = []
            current_worktree: dict = {}
            for line in result.stdout.strip().split('\n'):
                if not line.strip():  # End of a block
                    if current_worktree:
                        # Only list worktrees inside the agent's 'worktrees/' directory
                        worktree_path = Path(current_worktree.get("worktree", ""))
                        if worktrees_base_dir in worktree_path.parents:
                            worktrees.append(current_worktree)
                    current_worktree = {}
                else:
                    key, value = line.split(" ", 1)
                    current_worktree[key] = value

            # Append the last worktree if it exists
            if current_worktree:
                worktree_path = Path(current_worktree.get("worktree", ""))
                if worktrees_base_dir in worktree_path.parents:
                    worktrees.append(current_worktree)

            if not worktrees:
                print("No active agent worktrees found.")
                sys.exit(0)

            for wt in worktrees:
                path = Path(wt['worktree'])
                branch = wt.get('branch', 'detached HEAD').split('/')[-1]
                print(f"  - {path.name} (branch: {branch})")

        except subprocess.CalledProcessError as e:
            print(f"❌ Error listing worktrees: {e.stderr}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # --- Action: show ---
    elif args.action == "show":
        if not args.worktree_name:
            print("❌ Error: 'show' action requires a worktree name.", file=sys.stderr)
            sys.exit(1)
        worktree_path = worktrees_base_dir / args.worktree_name
        if not worktree_path.is_dir():
            print(f"❌ Error: Worktree '{args.worktree_name}' not found.", file=sys.stderr)
            sys.exit(1)

        print(f"--- Status for Worktree: {args.worktree_name} ---")
        try:
            result = subprocess.run(
                [git_path, "-C", str(worktree_path), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            if result.stdout.strip():
                print("Uncommitted changes:")
                for line in result.stdout.strip().split('\n'):
                    print(f"  {line}")
            else:
                print("✅ Worktree is clean.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error getting worktree status: {e.stderr}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # --- Action: revert ---
    elif args.action == "revert":
        if not args.worktree_name:
            print("❌ Error: 'revert' action requires a worktree name.", file=sys.stderr)
            sys.exit(1)
        worktree_path = worktrees_base_dir / args.worktree_name
        if not worktree_path.is_dir():
            print(f"❌ Error: Worktree '{args.worktree_name}' not found.", file=sys.stderr)
            sys.exit(1)

        print(f"--- Reverting uncommitted changes in worktree: {args.worktree_name} ---")
        try:
            status_result = subprocess.run(
                [git_path, "-C", str(worktree_path), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            if not status_result.stdout.strip():
                print("✅ No uncommitted changes to revert.")
                sys.exit(0)

            print("\nUncommitted changes (will be discarded):")
            for line in status_result.stdout.strip().split('\n'):
                print(f"  {line}")

            if not args.yes:
                confirm = input("\nAre you sure you want to discard ALL uncommitted changes in this worktree? [y/N]: ").strip().lower()
                if confirm != 'y':
                    print("Aborted.")
                    sys.exit(0)

            print("\nReverting changes...")
            subprocess.run(
                [git_path, "-C", str(worktree_path), "reset", "--hard", "HEAD"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            subprocess.run(
                [git_path, "-C", str(worktree_path), "clean", "-fd"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            print("✅ Revert complete. Worktree is now clean.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().strip() if e.stderr else str(e)
            print(f"❌ Error during revert: {stderr}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # --- Action: merge ---
    elif args.action == "merge":
        _worktree_merge(args, git_path, project_dir, worktrees_base_dir)

    # --- Action: diff ---
    elif args.action == "diff":
        _worktree_diff(args, git_path, worktrees_base_dir)

    # --- Action: manage (interactive) ---
    elif args.action == "manage":
        _worktree_manage(args, git_path, project_dir, worktrees_base_dir)

    # --- Action: clean ---
    elif args.action == "clean":
        worktrees_to_clean = []
        if args.worktree_name:
            # Clean a specific worktree
            path = worktrees_base_dir / args.worktree_name
            if not path.is_dir():
                print(f"❌ Error: Worktree '{args.worktree_name}' not found.", file=sys.stderr)
                sys.exit(1)
            worktrees_to_clean.append(args.worktree_name)
        else:
            # Clean all agent worktrees
            if worktrees_base_dir.is_dir():
                worktrees_to_clean = [d.name for d in worktrees_base_dir.iterdir() if d.is_dir()]

        if not worktrees_to_clean:
            print("No agent worktrees found to clean.")
            sys.exit(0)

        print("The following worktrees will be removed:")
        for name in worktrees_to_clean:
            print(f"  - {name}")

        if not args.yes:
            confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        print("\nCleaning worktrees...")
        for name in worktrees_to_clean:
            try:
                cmd = [git_path, "-C", str(project_dir), "worktree", "remove"]
                if args.force:
                    cmd.append("--force")
                cmd.append(name) # Can just be the name if it's in worktrees/ dir

                subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"✅ Removed worktree: {name}")

                # After successful removal via git, ensure the directory is gone
                worktree_dir = worktrees_base_dir / name
                if worktree_dir.exists():
                     print(f"Warning: Git removed worktree but directory '{worktree_dir}' still exists.", file=sys.stderr)

            except subprocess.CalledProcessError as e:
                # Try to parse the error
                stderr = e.stderr.strip()
                if "is not a working tree" in stderr:
                     # Git doesn't know about it, maybe it was partially deleted.
                     # Let's try to clean up the directory.
                    print(f"Git worktree '{name}' is in an inconsistent state. Attempting to clean up directory...")
                    worktree_dir = worktrees_base_dir / name
                    if worktree_dir.exists():
                         try:
                            shutil.rmtree(worktree_dir)
                            print(f"✅ Forcefully removed directory: {worktree_dir}")
                         except OSError as rm_e:
                            print(f"❌ Failed to remove directory {worktree_dir}: {rm_e}", file=sys.stderr)
                    else:
                         print(f"Directory for '{name}' not found, already clean.")
                else:
                    print(f"❌ Error removing worktree '{name}': {stderr}", file=sys.stderr)
        sys.exit(0)


async def main():
    args = parse_args()

    # Handle `shell` command
    if args.command == "shell":
        run_shell(args)
        return

    # Handle `tui` command
    if args.command == "tui":
        run_tui(args)
        return

    # Handle `completion` command
    if args.command == "completion":
        if argcomplete:
            print(argcomplete.shellcode([os.path.basename(sys.argv[0])]))
            sys.exit(0)
        else:
            print("argcomplete is not installed. Please install it with 'pip install argcomplete'.", file=sys.stderr)
            sys.exit(1)

    # Handle `plan` command
    if args.command == "plan":
        await run_plan(args)
        return

    # Handle `configure` command
    if args.command == "configure":
        run_configure()
        return

    # Handle `validate` command
    if args.command == "validate":
        run_validate()
        return

    # Handle `doctor` command
    if args.command == "doctor":
        run_doctor(args)
        return

    # Handle `clean` command
    if args.command == "clean":
        run_clean(args)
        return

    # Handle `archive` command
    if args.command == "archive":
        run_archive(args)
        return

    # Handle `empty-trash` command
    if args.command == "empty-trash":
        run_empty_trash(args)
        return

    # Handle `restore` command
    if args.command == "restore":
        run_restore(args)
        return

    # Handle `trash` command
    if args.command == "trash":
        run_trash(args)
        return

    # Handle `revert` command
    if args.command == "revert":
        run_revert(args)
        return

    # Handle `archives' command
    if args.command == "archives":
        run_archives(args)
        return

    # Handle `artifacts` command
    if args.command == "artifacts":
        run_artifacts(args, mode=args.type)
        return

    # Handle `worktrees` command
    if args.command == "worktrees":
        run_worktrees(args)
        return

    # Handle `snapshot` command
    if args.command == "snapshot":
        run_snapshot(args)
        return

    # Handle `list-agents` command
    if args.command == "list-agents":
        run_list_agents()
        return

    # Handle `status` command
    if args.command == "status":
        run_status(args)
        return

    # Handle `summary` command
    if args.command == "summary":
        run_summary(args)
        return

    # Handle `history` command
    if args.command == "history":
        run_history(args)
        return

    if args.command == "diff-summary":
        run_diff_summary(args)
        return

    if args.command == "logs":
        run_logs(args)
        return

    # Handle `workflow` command
    if args.command == "workflow":
        run_workflow(args)
        return

    # Handle `benchmark` command
    if args.command == "benchmark":
        run_benchmark(args)
        return

    # Handle `sprint` command
    if args.command == "sprint":
        run_sprint_command(args)
        return

    # Initialize Agent Client
    from shared.agent_client import AgentClient
    from shared.utils import generate_agent_id

    project_name = os.environ.get("PROJECT_NAME")
    if not project_name:
        project_name = args.project_dir.resolve().name

    # Load Configuration from File
    # Priority resolved in config_loader: ./ > XDG > Legacy
    ensure_config_exists()
    file_config = load_config_from_file(profile=args.profile)

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

    # Initialize Database
    from shared.database import init_db
    # Ensure project dir exists for DB creation
    config.project_dir.mkdir(parents=True, exist_ok=True)
    init_db(config.project_dir / ".agent_db.sqlite")

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

    # Handle `show-config` command and deprecated `--dry-run`
    if args.command == "show-config":
        run_show_config(config)

    if args.dry_run:
        print("Warning: --dry-run is deprecated. Please use the 'show-config' command instead.", file=sys.stderr)
        run_show_config(config)

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

    log_file = agents_log_dir / f"{agent_id}.log"

    # Configure Root Logger to capture all module logs (e.g. shared.git)
    logger, memory_handler = setup_logger(name="", log_file=log_file, verbose=args.verbose)

    logger.info(f"Starting {args.agent.capitalize()} Agent on {args.project_dir}")
    logger.info(f"Generated Agent ID: {agent_id}")

    # Append the current run ID to the history file
    try:
        history_file = config.project_dir / ".agent_history"
        with open(history_file, "a") as f:
            f.write(f"{agent_id}\n")
    except IOError as e:
        logger.warning(f"Could not write to history file {history_file}: {e}")

    client = AgentClient(agent_id=agent_id, dashboard_url=args.dashboard_url, memory_handler=memory_handler)

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
