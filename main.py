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
import time
from collections import deque
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = None


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
from shared.issues import _run_issues_logic
from agents.gemini import run_autonomous_agent as run_gemini, GeminiAgent
from agents.shared.sprint import run_sprint as run_sprint
from agents.cursor import run_autonomous_agent as run_cursor, CursorAgent
from agents.local import run_autonomous_agent as run_local, LocalAgent
from agents.openrouter import run_autonomous_agent as run_openrouter, OpenRouterAgent
from shared.shell import InteractiveShell
from shared.commands import run_why
from shared.onboarding import run_onboard_logic
from shared.ask import run_ask_logic
from shared.cli import run_do_logic
from shared.playground import PlaygroundManager
from shared.debug import run_debug_logic
from shared.mutate import run_mutate
from shared.code_review import run_code_review_logic
from shared.summarize import run_summarize_logic
from shared.security import SecurityAuditor
from shared.dockerizer import Dockerizer
from shared.verify import run_verify_logic
from shared.polish import run_polish_logic
from shared.health import run_health_check
from shared.work_session import WorkSessionManager
import json
import yaml
import platformdirs
from dataclasses import asdict, is_dataclass
from datetime import datetime

# Agent Definitions
AVAILABLE_AGENTS = {
    "gemini": "Uses Google's Gemini model via the official API.",
    "cursor": "Interacts with the Cursor IDE's AI features.",
    "local": "Runs a local model (e.g., Ollama).",
    "openrouter": "Uses a model from the OpenRouter API.",
}

if FileSystemEventHandler:
    class CommandEventHandler(FileSystemEventHandler):
        def __init__(self, command, project_dir):
            self.command = command
            self.project_dir = project_dir

        def on_modified(self, event):
            if event.is_directory:
                return
            print(f"File modified: {event.src_path}. Running command: {' '.join(self.command)}")
            subprocess.run(self.command, cwd=self.project_dir)

def run_onboard(args):
    """Runs the onboarding wizard."""
    run_onboard_logic(args.project_dir)
    sys.exit(0)

def run_secrets(args):
    """Manages encrypted secrets."""
    from shared.secrets import SecretsManager
    project_dir = args.project_dir.resolve()
    manager = SecretsManager(project_dir)

    try:
        if args.action == "init":
            if manager.generate_key(force=args.force):
                print(f"✅ Generated new encryption key at {manager.key_path}")
            else:
                print(f"ℹ️  Key already exists at {manager.key_path}. Use --force to overwrite.")

        elif args.action == "set":
            if not args.name or not args.value:
                print("Error: Name and value required.", file=sys.stderr)
                sys.exit(1)
            manager.set_secret(args.name, args.value)
            print(f"✅ Secret '{args.name}' set.")

        elif args.action == "get":
            val = manager.get_secret(args.name)
            if val is not None:
                print(val)
            else:
                print(f"❌ Secret '{args.name}' not found.", file=sys.stderr)
                sys.exit(1)

        elif args.action == "list":
            secrets = manager.list_secrets()
            if secrets:
                print("--- Secrets ---")
                for s in secrets:
                    print(f"  - {s}")
            else:
                print("No secrets found.")

        elif args.action == "delete":
            if manager.delete_secret(args.name):
                print(f"✅ Secret '{args.name}' deleted.")
            else:
                print(f"❌ Secret '{args.name}' not found.", file=sys.stderr)
                sys.exit(1)

        elif args.action == "run":
            cmd_list = args.command_args
            if cmd_list and cmd_list[0] == "--":
                cmd_list = cmd_list[1:]

            if not cmd_list:
                print("Error: Command required.", file=sys.stderr)
                sys.exit(1)

            # Decrypt secrets and inject into env
            env = manager.get_env_with_secrets()

            # Execute command
            # We use os.execvpe to replace the current process
            cmd = cmd_list[0]
            cmd_args = cmd_list
            try:
                os.execvpe(cmd, cmd_args, env)
            except FileNotFoundError:
                print(f"❌ Command not found: {cmd}", file=sys.stderr)
                sys.exit(1)
            except OSError as e:
                print(f"❌ Error executing command: {e}", file=sys.stderr)
                sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

def run_session(args):
    """Manages work sessions."""
    project_dir = args.project_dir.resolve()
    manager = WorkSessionManager(project_dir)

    if args.action == "new":
        if not args.name:
            print("Error: Name required for 'new' action.", file=sys.stderr)
            sys.exit(1)
        try:
            session = manager.create(args.name, args.description or "")
            print(f"✅ Created session: {session.name}")
            print(f"   Files: {len(session.files)}")
            print(f"   Notes: {len(session.notes)}")
        except FileExistsError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "load":
        if not args.name:
            print("Error: Name required for 'load' action.", file=sys.stderr)
            sys.exit(1)
        try:
            manager.set_active_session(args.name)
            print(f"✅ Loaded session: {args.name}")
        except FileNotFoundError:
            print(f"❌ Session '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "list":
        sessions = manager.list_sessions()
        if not sessions:
            print("No sessions found.")
        else:
            active = manager.get_active_session()
            print("--- Available Sessions ---")
            for s in sessions:
                marker = "*" if active and active.name == s["name"] else " "
                print(f"{marker} {s['name']:<20} {s['updated_at'][:16]}   {s['description']}")

    elif args.action == "info":
        name = args.name
        if not name:
            active = manager.get_active_session()
            if active:
                name = active.name
            else:
                print("Error: No active session. Please specify a name or load a session.", file=sys.stderr)
                sys.exit(1)

        session = manager.load_session(name)
        if not session:
            print(f"❌ Session '{name}' not found.", file=sys.stderr)
            sys.exit(1)

        print(f"--- Session: {session.name} ---")
        print(f"Created: {session.created_at}")
        print(f"Updated: {session.updated_at}")
        print(f"Description: {session.description}")
        print("\nFiles:")
        for f in session.files:
            print(f"  - {f}")
        print("\nNotes:")
        for n in session.notes:
            print(f"  {n}")

    elif args.action == "add":
        if not args.file:
            print("Error: File required.", file=sys.stderr)
            sys.exit(1)

        target_session = args.name
        if not target_session:
            active = manager.get_active_session()
            if active:
                target_session = active.name
            else:
                 print("Error: No active session. Specify name with --name.", file=sys.stderr)
                 sys.exit(1)

        try:
            manager.add_file(target_session, args.file)
            print(f"✅ Added {args.file} to session '{target_session}'")
        except FileNotFoundError:
             print(f"❌ Session '{target_session}' not found.", file=sys.stderr)
             sys.exit(1)

    elif args.action == "remove":
        if not args.file:
            print("Error: File required.", file=sys.stderr)
            sys.exit(1)

        target_session = args.name
        if not target_session:
            active = manager.get_active_session()
            if active:
                target_session = active.name
            else:
                 print("Error: No active session. Specify name with --name.", file=sys.stderr)
                 sys.exit(1)

        try:
            manager.remove_file(target_session, args.file)
            print(f"✅ Removed {args.file} from session '{target_session}'")
        except FileNotFoundError:
             print(f"❌ Session '{target_session}' not found.", file=sys.stderr)
             sys.exit(1)

    elif args.action == "note":
        if not args.note:
             print("Error: Note text required.", file=sys.stderr)
             sys.exit(1)

        target_session = args.name
        if not target_session:
            active = manager.get_active_session()
            if active:
                target_session = active.name
            else:
                 print("Error: No active session. Specify name with --name.", file=sys.stderr)
                 sys.exit(1)

        try:
            manager.add_note(target_session, args.note)
            print(f"✅ Added note to session '{target_session}'")
        except FileNotFoundError:
             print(f"❌ Session '{target_session}' not found.", file=sys.stderr)
             sys.exit(1)

    elif args.action == "stop":
        manager.stop_session()
        print("✅ Session stopped.")

    elif args.action == "delete":
        if not args.name:
            print("Error: Name required.", file=sys.stderr)
            sys.exit(1)

        if manager.delete_session(args.name):
            print(f"✅ Deleted session '{args.name}'")
        else:
            print(f"❌ Session '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)

def run_playground(args):
    """Manages the agent playground."""
    project_dir = args.project_dir.resolve()
    manager = PlaygroundManager(project_dir)

    if args.action == "create":
        name = args.name or "scratch.py"
        path = manager.create(name)
        print(f"✅ Created playground file: {path}")
        print(f"Run it with: {sys.argv[0]} playground run {path.name}")

    elif args.action == "run":
        if not args.name:
            print("Error: Name required for 'run' action.", file=sys.stderr)
            sys.exit(1)
        success = manager.run(args.name)
        sys.exit(0 if success else 1)

    elif args.action == "list":
        files = manager.list_files()
        if not files:
            print("Playground is empty.")
        else:
            print("--- Playground Files ---")
            for f in files:
                print(f"  - {f.name}")

    elif args.action == "delete":
        if not args.name:
            print("Error: Name required for 'delete' action.", file=sys.stderr)
            sys.exit(1)
        if manager.delete(args.name):
            print(f"✅ Deleted {args.name}")
        else:
            print(f"❌ File {args.name} not found.")
            sys.exit(1)

    sys.exit(0)

def run_init(args):
    """Runs an interactive setup wizard for a new project."""
    import subprocess
    import shutil

    project_dir = args.project_dir.resolve()
    print("--- Interactive Project Initialization ---")
    print(f"This wizard will set up your project in: {project_dir}\n")

    # --- Step 1: Git Repository Check ---
    print("--- [1/4] Git Repository ---")
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Warning: 'git' command not found. It's highly recommended to use version control.")
    elif (project_dir / ".git").is_dir():
        print("✅ Git repository already exists.")
    else:
        print("No Git repository found.")
        if not args.yes:
            confirm_git = input("Do you want to initialize a new Git repository? [Y/n]: ").strip().lower()
        if args.yes or confirm_git in ['y', '']:
            try:
                project_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run([git_path, "init", "-b", "main", str(project_dir)], check=True, capture_output=True)
                print("✅ Successfully initialized a new Git repository.")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                stderr = getattr(e, 'stderr', str(e))
                if isinstance(stderr, bytes): stderr = stderr.decode()
                print(f"❌ Error initializing Git repository: {stderr}")

    # --- Step 2: .gitignore ---
    print("\n--- [2/4] .gitignore file ---")
    gitignore_path = project_dir / ".gitignore"
    if gitignore_path.exists():
        print("✅ .gitignore file already exists.")
    else:
        print("No .gitignore file found.")
        if not args.yes:
            confirm_gitignore = input("Do you want to create a Python-focused .gitignore file? [Y/n]: ").strip().lower()
        if args.yes or confirm_gitignore in ['y', '']:
            try:
                gitignore_content = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Agent artifacts
.agent_trash/
.agent_archives/
.agent_db.sqlite
.agent_run_id
.agent_history
.agent_branch
worktrees/
final_metrics.txt
dashboard_state.json
"""
                gitignore_path.write_text(gitignore_content.strip())
                print("✅ Created a .gitignore file.")
            except IOError as e:
                print(f"❌ Error creating .gitignore file: {e}")

    # --- Step 3: app_spec.txt ---
    print("\n--- [3/4] Application Specification ---")
    spec_path = project_dir / "app_spec.txt"
    if spec_path.exists():
        print(f"✅ Application spec file already exists: {spec_path.name}")
        if not args.yes:
             overwrite_spec = input("Do you want to overwrite it? [y/N]: ").strip().lower()
             if overwrite_spec != 'y':
                 spec_path = None # Skip writing

    if spec_path:
        print("Please describe the application you want to build.")
        print("Be detailed. The more information you provide, the better the agent will perform.")
        print("Press Enter twice to save and continue.")

        spec_lines = []
        try:
            while True:
                line = input("> ")
                if not line and len(spec_lines) > 0 and spec_lines[-1] == "":
                    # Two consecutive empty lines
                    spec_lines.pop() # Remove the last empty line
                    break
                spec_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            print("\nSkipping spec creation.")
            spec_lines = []

        if spec_lines:
            try:
                spec_path.write_text("\n".join(spec_lines))
                print(f"✅ Saved application specification to {spec_path.name}")
            except IOError as e:
                print(f"❌ Error writing to {spec_path.name}: {e}")

    # --- Step 4: Next Steps ---
    print("\n--- [4/4] Next Steps ---")
    print("✅ Project initialization complete!")
    print("\nYou're ready to start working with the agent. Here are some common next steps:")
    executable_name = os.path.basename(sys.argv[0])
    print(f"  - To start the agent and build your app:")
    print(f"    {executable_name} --spec app_spec.txt")
    print(f"  - To see all available commands:")
    print(f"    {executable_name} --help")
    print(f"  - For a detailed health check of your environment:")
    print(f"    {executable_name} doctor")

    sys.exit(0)


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

from shared.cli_utils import _run_history_graph_logic

def run_history_graph(args):
    """Displays a graph of historical metrics."""
    graph_output = _run_history_graph_logic(
        project_dir=args.project_dir,
        metric=args.metric,
        limit=args.limit
    )
    print(graph_output)
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


RECOMMENDED_MODELS = {
    "gemini": [
        {"model": "gemini-1.5-pro-latest", "description": "Most capable model, multi-modal, large context.", "recommended": True},
        {"model": "gemini-1.5-flash-latest", "description": "Fast and cost-effective, multi-modal.", "recommended": False},
        {"model": "gemini-1.0-pro", "description": "Previous generation, balanced performance.", "recommended": False},
    ],
    "cursor": [
        {"model": "claude-3.5-sonnet", "description": "Strong performance, good for complex reasoning.", "recommended": True},
        {"model": "gpt-4o", "description": "Fast, multi-modal, high performance.", "recommended": False},
        {"model": "claude-3-opus", "description": "Most powerful Claude model for highly complex tasks.", "recommended": False},
    ],
    "openrouter": [
        {"model": "anthropic/claude-3.5-sonnet", "description": "Top-tier model, good for reasoning.", "recommended": True},
        {"model": "openai/gpt-4o", "description": "Flagship OpenAI model, multi-modal.", "recommended": False},
        {"model": "google/gemini-flash-1.5", "description": "Fast and efficient model from Google.", "recommended": False},
        {"model": "mistralai/mistral-large", "description": "Flagship model from Mistral AI.", "recommended": False},
    ],
    "local": [
        {"model": "ollama/llama3", "description": "High-performing open source model.", "recommended": True},
        {"model": "ollama/codellama", "description": "Specialized for code generation.", "recommended": False},
    ]
}

def run_models(args):
    """Prints a list of recommended models for each agent."""
    agent_filter = args.agent

    if agent_filter and agent_filter not in RECOMMENDED_MODELS:
        print(f"❌ Error: Agent '{agent_filter}' not found. Use 'list-agents' to see available agents.", file=sys.stderr)
        sys.exit(1)

    print("--- Recommended Models ---")

    for agent_name, models in RECOMMENDED_MODELS.items():
        if agent_filter and agent_name != agent_filter:
            continue

        print(f"\n# {agent_name.capitalize()} Agent")
        header = f"  {'Model Name':<30} | {'Description'}"
        print(header)
        print(f"  {'-'*30}-+-{'-'*40}")

        for model_info in models:
            rec_marker = " (recommended)" if model_info["recommended"] else ""
            print(f"  {model_info['model']:<30} | {model_info['description']}{rec_marker}")
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

    # --- GitHub Configuration ---
    print("\n--- GitHub Integration (optional) ---")
    github_token = get_input("GitHub Personal Access Token", existing_config.get('github_token'))
    github_host = get_input("GitHub Host (e.g., github.my-company.com for Enterprise)", existing_config.get('github_host'))

    if github_token:
        existing_config['github_token'] = github_token
    if github_host:
        existing_config['github_host'] = github_host

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
        # Set file permissions to 600 (owner read/write only) to protect secrets
        os.chmod(config_path, 0o600)
        print(f"\n✅ Configuration saved successfully to {config_path}")
    except Exception as e:
        print(f"\n❌ Error saving configuration: {e}")


def run_prune(args):
    """
    Identifies and removes unused code and dependencies.
    """
    from shared.prune import PruneManager

    project_dir = args.project_dir.resolve()
    print(f"--- Project Prune (Cleanup) in: {project_dir} ---")

    manager = PruneManager(project_dir)

    types = []
    if args.types:
        types = [t.strip() for t in args.types.split(",")]

    manager.prune_interactive(dry_run=args.dry_run, yes=args.yes, types=types)
    sys.exit(0)


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


def _discard_interactive(project_dir, git_path):
    """Handles the interactive discard logic."""
    print(f"--- Interactive Discard in: {project_dir} ---")
    try:
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        changes = [line for line in status_result.stdout.splitlines() if line]
        if not changes:
            print("✅ No uncommitted changes to discard.")
            sys.exit(0)

        print("Select files to discard (e.g., 1 3 4), or press Enter to cancel:")
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
            files_to_discard = [all_files[i] for i in indices if 0 <= i < len(all_files)]
            if not files_to_discard:
                print("No valid files selected. Aborting.")
                sys.exit(0)
            return files_to_discard
        except ValueError:
            print("❌ Invalid input. Please enter numbers separated by spaces.", file=sys.stderr)
            sys.exit(1)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Error checking git status: {e}", file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        sys.exit(0)
    return []


def _discard_files(project_dir, git_path, files_to_discard, yes=False):
    """Handles discarding a specific list of files."""
    print(f"--- Discarding specified files in: {project_dir} ---")
    status_result = subprocess.run(
        [git_path, "-C", str(project_dir), "status", "--porcelain"],
        capture_output=True, text=True, check=True
    )
    all_untracked_files = {
        line[3:] for line in status_result.stdout.strip().split('\n') if line.startswith('??')
    }

    tracked_to_discard = [f for f in files_to_discard if f not in all_untracked_files]
    untracked_to_discard = [f for f in files_to_discard if f in all_untracked_files]

    status_of_selection = subprocess.run(
        [git_path, "-C", str(project_dir), "status", "--porcelain", "--"] + files_to_discard,
        capture_output=True, text=True
    )
    final_discard_list = [line[3:] for line in status_of_selection.stdout.strip().split('\n') if line.strip()]

    if not final_discard_list:
        print("✅ No uncommitted changes to discard for the specified files.")
        sys.exit(0)

    print("\nThe following files will be discarded:")
    for f in final_discard_list:
        print(f"  - {f}")

    if not yes:
        confirm = input("\nAre you sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print("\nDiscarding files...")
    try:
        if tracked_to_discard:
            cmd = [git_path, "-C", str(project_dir), "checkout", "HEAD", "--"] + tracked_to_discard
            subprocess.run(cmd, check=True, capture_output=True)
        if untracked_to_discard:
            cmd = [git_path, "-C", str(project_dir), "clean", "-f", "--"] + untracked_to_discard
            subprocess.run(cmd, check=True, capture_output=True)
        print("✅ Specified files have been discarded.")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode().strip() if e.stderr else str(e)
        print(f"❌ Error during discard: {stderr}", file=sys.stderr)
        sys.exit(1)


def _discard_all(project_dir, git_path, yes=False):
    """Handles discarding all uncommitted changes."""
    print(f"--- Discarding ALL uncommitted changes in: {project_dir} ---")
    try:
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if not status_result.stdout.strip():
            print("  ✅ No uncommitted changes to discard.")
            sys.exit(0)

        print("\nUncommitted changes (will be discarded):")
        for line in status_result.stdout.strip().split('\n'):
            print(f"  {line}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Error checking git status: {e}", file=sys.stderr)
        sys.exit(1)

    if not yes:
        confirm = input("\nAre you sure you want to discard ALL uncommitted changes? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    # Stash changes before discarding to allow for recovery
    print("\nStashing changes before discarding...")
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        stash_message = f"agent-discard-stash-{timestamp}"
        # Use -u to include untracked files
        subprocess.run(
            [git_path, "-C", str(project_dir), "stash", "push", "-u", "-m", stash_message],
            check=True, capture_output=True, text=True
        )
        print(f"✅ Changes stashed safely. To recover, use the 'undo' command.")
    except subprocess.CalledProcessError as e:
        # It's possible there are no changes to stash if only ignored files are present
        if "No local changes to save" not in e.stderr:
            print(f"❌ Error while stashing changes: {e.stderr}", file=sys.stderr)
            print("Aborting discard to prevent data loss.", file=sys.stderr)
            sys.exit(1)

    print("\nCleaning working directory...")
    try:
        subprocess.run(
            [git_path, "-C", str(project_dir), "reset", "--hard", "HEAD"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        subprocess.run(
            [git_path, "-C", str(project_dir), "clean", "-fd"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✅ Discard complete. Working directory is now clean.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        if isinstance(stderr, bytes):
            stderr = stderr.decode().strip()
        print(f"❌ Error during discard: {stderr}", file=sys.stderr)
        sys.exit(1)


def run_undo(args):
    """Restores uncommitted changes that were stashed by the 'discard' command."""
    project_dir = args.project_dir.resolve()
    git_path = shutil.which("git")

    if not git_path or not (project_dir / ".git").is_dir():
        print("❌ Error: Not a git repository. Cannot run undo.", file=sys.stderr)
        sys.exit(1)

    print(f"--- Searching for stashed discards in: {project_dir} ---")

    try:
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "stash", "list"],
            capture_output=True, text=True, check=True
        )
        stashes = result.stdout.strip().split('\n')
        discard_stashes = [s for s in stashes if "agent-discard-stash" in s]

        if not discard_stashes:
            print("No stashed discards found to undo.")
            sys.exit(0)

        print("Please select a discard to undo (press Enter to cancel):")
        for i, stash in enumerate(discard_stashes):
            print(f"  [{i+1}] {stash}")

        selection = input("> ").strip()
        if not selection:
            print("Aborted.")
            sys.exit(0)

        choice_index = int(selection) - 1
        if 0 <= choice_index < len(discard_stashes):
            stash_to_apply = discard_stashes[choice_index].split(':')[0]
            print(f"\nRestoring selected stash: {stash_to_apply}...")
            subprocess.run(
                [git_path, "-C", str(project_dir), "stash", "pop", stash_to_apply],
                check=True
            )
            print("✅ Undo complete. Your changes have been restored.")
            sys.exit(0)
        else:
            print("❌ Invalid selection.", file=sys.stderr)
            sys.exit(1)

    except (ValueError, IndexError):
        print("❌ Invalid input. Please enter a valid number.", file=sys.stderr)
        sys.exit(1)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        print(f"❌ Error during undo process: {stderr}", file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        sys.exit(0)


def run_discard(args):
    """Discards uncommitted changes for specified files or for the entire repository."""
    project_dir = args.project_dir.resolve()

    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot discard changes.", file=sys.stderr)
        sys.exit(1)

    if args.files and args.interactive:
        print("❌ Error: Cannot use --interactive mode when specifying individual files.", file=sys.stderr)
        sys.exit(1)

    files_to_discard = args.files
    if args.interactive:
        files_to_discard = _discard_interactive(project_dir, git_path)

    if files_to_discard:
        _discard_files(project_dir, git_path, files_to_discard, args.yes)
    else:
        _discard_all(project_dir, git_path, args.yes)

    sys.exit(0)


def _find_commit_by_run_id(project_dir: Path, git_path: str, run_id: str) -> str | None:
    """Searches the git log for a commit associated with a Run ID."""
    try:
        # Search the entire commit history for the Run ID in the message body
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "log", "--all", f"--grep=Run ID: {run_id}", "--format=%H"],
            capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            # Return the first commit hash found
            return result.stdout.strip().split('\n')[0]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return None


def run_rollback(args):
    """Reverts all commits associated with a specific agent Run ID."""
    project_dir = args.project_dir.resolve()
    run_id = args.run_id

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot rollback.", file=sys.stderr)
        sys.exit(1)

    # Check for uncommitted changes
    try:
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if status_result.stdout.strip():
            print("❌ Error: Your repository has uncommitted changes.", file=sys.stderr)
            print("Please commit or stash them before using rollback.", file=sys.stderr)
            sys.exit(1)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Error checking git status: {e}", file=sys.stderr)
        sys.exit(1)

    # Resolve Run ID
    if not run_id or run_id == "last":
        history_file = project_dir / ".agent_history"
        if not history_file.exists():
            print("❌ Error: No agent history found.", file=sys.stderr)
            sys.exit(1)

        try:
            with open(history_file, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
            if not lines:
                print("❌ Error: Agent history is empty.", file=sys.stderr)
                sys.exit(1)
            run_id = lines[-1]
            print(f"Rolling back last run: {run_id}")
        except IOError as e:
            print(f"❌ Error reading history file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Rolling back run: {run_id}")

    # Find commits associated with Run ID
    print("Searching for commits...")
    try:
        # We look for "Run ID: <run_id>" in the commit message body
        # git log --grep="Run ID: <run_id>" --format="%H"
        # This returns commits in reverse chronological order (newest first).
        # We want to revert them in that order.
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "log", "--grep", f"Run ID: {run_id}", "--format=%H"],
            capture_output=True, text=True, check=True
        )
        commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError as e:
        print(f"❌ Error searching git log: {e}", file=sys.stderr)
        sys.exit(1)

    if not commits:
        print(f"✅ No commits found for Run ID '{run_id}'. Nothing to rollback.")
        sys.exit(0)

    print(f"Found {len(commits)} commit(s) to revert:")
    for c in commits:
        print(f"  - {c[:7]}")

    if not args.yes:
        confirm = input("\nAre you sure you want to revert these commits? This will create new revert commits. [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print("\nReverting commits...")
    reverted_count = 0
    try:
        # Iterate through commits (already newest first) and revert them
        for commit_hash in commits:
            print(f"  Reverting {commit_hash[:7]}...")
            # Use --no-edit to skip editor launch.
            revert_cmd = [git_path, "-C", str(project_dir), "revert", "--no-edit", commit_hash]

            revert_result = subprocess.run(revert_cmd, capture_output=True, text=True)

            if revert_result.returncode != 0:
                print(f"❌ Error reverting commit {commit_hash[:7]}:", file=sys.stderr)
                print(revert_result.stderr, file=sys.stderr)
                print("\nConflict detected or error occurred. Aborting rollback sequence.", file=sys.stderr)
                print("You may need to resolve the conflict manually or run 'git revert --abort'.", file=sys.stderr)
                sys.exit(1)

            reverted_count += 1

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n✅ Successfully reverted {reverted_count} commit(s).")
    sys.exit(0)


def run_cherry_pick(args):
    """Applies the changes from a specific commit onto the current branch."""
    project_dir = args.project_dir.resolve()
    target = args.target

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot cherry-pick.", file=sys.stderr)
        sys.exit(1)

    # --- Target Resolution: Commit Hash vs. Run ID ---
    original_target = target
    # First, check if the target is a valid git object (commit, tag, etc.)
    is_git_ref = False
    try:
        check_commit_result = subprocess.run(
            [git_path, "-C", str(project_dir), "cat-file", "-t", target],
            capture_output=True, text=True
        )
        if check_commit_result.returncode == 0 and check_commit_result.stdout.strip() == "commit":
            is_git_ref = True
    except Exception:
        pass  # Ignore errors, we'll handle the 'not found' case below

    if not is_git_ref:
        print(f"'{target}' is not a known git commit. Assuming it is a Run ID and searching history...")
        commit_hash = _find_commit_by_run_id(project_dir, git_path, target)
        if commit_hash:
            print(f"✅ Found commit '{commit_hash[:7]}' associated with Run ID '{target}'.")
            target = commit_hash
        else:
            print(f"❌ Error: Could not find a git commit for target '{original_target}'.", file=sys.stderr)
            print("Please provide a valid commit hash or a Run ID from the agent's history.", file=sys.stderr)
            sys.exit(1)

    # --- Execute Cherry-Pick ---
    print(f"--- Applying commit {target[:7]} onto the current branch ---")
    try:
        # Use --no-commit to allow the user to inspect the changes before committing
        cmd = [git_path, "-C", str(project_dir), "cherry-pick", "--no-commit", target]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(result.stdout)
            print(f"\n✅ Successfully cherry-picked commit {target[:7]}.")
            sys.exit(0)
        else:
            print("❌ Error: Cherry-pick failed.", file=sys.stderr)
            print("This is likely due to a merge conflict.", file=sys.stderr)
            print("\n--- Git Output ---", file=sys.stderr)
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            print("------------------", file=sys.stderr)
            print("\nPlease resolve the conflicts in your editor and then run:", file=sys.stderr)
            print(f"  git cherry-pick --continue", file=sys.stderr)
            print("\nTo abort the cherry-pick and return to the previous state, run:", file=sys.stderr)
            print(f"  git cherry-pick --abort", file=sys.stderr)
            sys.exit(1)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        if isinstance(stderr, bytes):
            stderr = stderr.decode().strip()
        print(f"❌ An unexpected error occurred: {stderr}", file=sys.stderr)
        sys.exit(1)


def run_rewind(args):
    """Resets the project to a previous state (git commit)."""
    project_dir = args.project_dir.resolve()
    target = args.target
    original_target = target  # Keep a copy for error messages

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot rewind.", file=sys.stderr)
        sys.exit(1)

    try:
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if status_result.stdout.strip():
            print("❌ Error: Your repository has uncommitted changes.", file=sys.stderr)
            print("Please commit or stash them before using rewind.", file=sys.stderr)
            sys.exit(1)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Error checking git status: {e}", file=sys.stderr)
        sys.exit(1)


    # --- Interactive Mode ---
    if not target:
        print(f"--- Interactive Rewind in: {project_dir} ---")
        try:
            log_result = subprocess.run(
                [git_path, "-C", str(project_dir), "log", "--oneline", "--pretty=format:%h|%s|%cr", "-n", "15"],
                capture_output=True, text=True, check=True
            )
            commits = [line.split('|') for line in log_result.stdout.strip().split('\n')]
            if not commits or not commits[0]:
                print("No commits found in the repository.")
                sys.exit(0)

            print("Select a commit to rewind to (press Enter to cancel):")
            for i, (hash, subject, time) in enumerate(commits):
                print(f"  [{i+1}] {hash} - {subject} ({time})")

            selection = input("> ").strip()
            if not selection:
                print("Aborted.")
                sys.exit(0)

            try:
                index = int(selection) - 1
                if 0 <= index < len(commits):
                    target = commits[index][0]
                else:
                    print("❌ Invalid selection.", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print("❌ Invalid input. Please enter a number.", file=sys.stderr)
                sys.exit(1)

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"❌ Error getting git log: {e}", file=sys.stderr)
            sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)
    else:
        # --- Target Resolution: Commit Hash vs. Run ID ---
        # First, check if the target is a valid git object (commit, tag, etc.)
        is_git_ref = False
        try:
            check_ref_result = subprocess.run(
                [git_path, "-C", str(project_dir), "show-ref", "--verify", f"refs/heads/{target}"],
                capture_output=True, text=True
            )
            if check_ref_result.returncode == 0:
                is_git_ref = True
            else:
                # Also check if it's a commit hash
                check_commit_result = subprocess.run(
                    [git_path, "-C", str(project_dir), "cat-file", "-t", target],
                    capture_output=True, text=True
                )
                if check_commit_result.returncode == 0 and check_commit_result.stdout.strip() == "commit":
                    is_git_ref = True
        except Exception:
            pass  # Ignore errors, we'll handle the 'not found' case below

        if not is_git_ref:
            print(f"'{target}' is not a known git reference. Assuming it is a Run ID and searching history...")
            commit_hash = _find_commit_by_run_id(project_dir, git_path, target)
            if commit_hash:
                print(f"✅ Found commit '{commit_hash[:7]}' associated with Run ID '{target}'.")
                target = commit_hash
            else:
                print(f"❌ Error: Could not find a git commit for Run ID '{target}'.", file=sys.stderr)
                print("Please provide a valid commit hash, reference, or a Run ID from the agent's history.", file=sys.stderr)
                sys.exit(1)


    # --- Confirmation and Execution ---
    print(f"\nThis will perform a 'git reset --hard' to '{target}'.")
    print("This action is destructive and will discard all commits made after this point.")
    if not args.yes:
        confirm = input("Are you absolutely sure you want to proceed? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    print(f"\nRewinding to {target}...")
    try:
        # Step 1: Clean any ignored files that might be lingering
        subprocess.run(
            [git_path, "-C", str(project_dir), "clean", "-fdx"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # Step 2: Reset to the target commit
        subprocess.run(
            [git_path, "-C", str(project_dir), "reset", "--hard", target],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✅ Rewind complete.")
        print("Project state has been reset.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        if isinstance(stderr, bytes):
            stderr = stderr.decode().strip()
        print(f"❌ Error during rewind: {stderr}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


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


from shared.cli_utils import (
    get_project_summary,
    get_suggestions,
    _run_enhanced_status_logic,
    _run_tree_logic,
    _run_report_logic,
    _run_dashboard_logic,
    _run_blame_logic,
    _run_next_logic,
    _run_context_show_logic,
    _run_context_analyze_logic,
    _find_metrics_file,
    _parse_metrics,
)

def run_release(args):
    """Manages the release process."""
    from shared.release import (
        get_latest_tag,
        get_commits_since_tag,
        determine_next_version,
        generate_changelog,
        bump_version_file,
        parse_current_version
    )

    project_dir = args.project_dir.resolve()

    # 1. Get current status
    latest_tag = get_latest_tag(project_dir)
    print(f"--- Release Management: {project_dir.name} ---")
    print(f"Latest tag: {latest_tag or 'None'}")

    commits = get_commits_since_tag(project_dir, latest_tag)
    print(f"Commits since tag: {len(commits)}")

    current_version = parse_current_version(project_dir)
    # If no current version in file, fallback to tag
    if not current_version and latest_tag:
        current_version = latest_tag.lstrip("v")

    print(f"Current version (file/tag): {current_version or '0.0.0'}")

    # 2. Determine bump
    if args.force_version:
        next_version = args.force_version
        print(f"Next version (forced): {next_version}")
    else:
        next_version = determine_next_version(current_version, commits)
        print(f"Next version (calculated): {next_version}")

    if next_version == current_version and not args.force_version:
        print("No version bump required based on commits.")
        if not args.yes:
            sys.exit(0)

    # 3. Generate Changelog
    changelog = generate_changelog(commits, next_version)

    if args.action == "plan":
        print("\n--- Plan: Changelog Preview ---")
        print(changelog)
        print("\n--- Plan: Actions ---")
        print(f"1. Update version to {next_version} in config files.")
        print(f"2. Create git tag v{next_version}.")
        sys.exit(0)

    elif args.action == "apply":
        if args.dry_run:
            print("[Dry Run] Would update files and create tag.")
            sys.exit(0)

        print("\n--- Applying Release ---")

        # Bump files
        modified = bump_version_file(project_dir, next_version)
        if modified:
            print(f"Updated version in: {', '.join(modified)}")
            # Commit these changes
            subprocess.run(["git", "-C", str(project_dir), "add"] + modified, check=True)
            subprocess.run(["git", "-C", str(project_dir), "commit", "-m", f"chore: bump version to {next_version}"], check=True)
            print("Committed version bump.")

        # Create tag
        tag_name = f"v{next_version}"
        if not args.no_changelog:
             # Use changelog as tag message
             # Write to temp file for safety
             import tempfile
             with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tf:
                 tf.write(changelog)
                 tf_path = tf.name

             try:
                 subprocess.run(["git", "-C", str(project_dir), "tag", "-a", tag_name, "-F", tf_path], check=True)
             finally:
                 os.unlink(tf_path)
        else:
             subprocess.run(["git", "-C", str(project_dir), "tag", tag_name], check=True)

        print(f"✅ Created tag: {tag_name}")
        print("Don't forget to push: git push --follow-tags")
        sys.exit(0)


async def run_bisect(args):
    """Runs smart bisect."""
    from shared.bisect import run_bisect_logic, analyze_commit

    project_dir = args.project_dir.resolve()

    if args.action == "run":
        if not args.good or not args.bad or not args.command:
             print("Error: --good, --bad, and --command are required for 'run' action.", file=sys.stderr)
             sys.exit(1)

        success = await run_bisect_logic(
            project_dir=project_dir,
            good_commit=args.good,
            bad_commit=args.bad,
            run_command=args.command,
            agent_type=args.agent,
            model=args.model,
            verbose=args.verbose,
            no_analysis=args.no_analysis
        )
        sys.exit(0 if success else 1)

    elif args.action == "analyze":
        if not args.commit:
             print("Error: Commit hash required for analysis.", file=sys.stderr)
             sys.exit(1)

        description = args.bug_description or "A regression was reported on this commit."
        print(f"--- Analyzing Commit: {args.commit} ---")
        analysis = await analyze_commit(
            project_dir=project_dir,
            commit_hash=args.commit,
            bug_description=description,
            agent_type=args.agent,
            model=args.model,
            verbose=args.verbose
        )
        print("\n" + analysis)
        sys.exit(0)


def run_map(args):
    """Generates a code map."""
    from shared.map import _run_map_logic
    _run_map_logic(args.project_dir, args.format, args.focus)
    sys.exit(0)

def run_architecture(args):
    """Checks the project architecture against defined rules."""
    from shared.architecture import check_architecture

    project_dir = args.project_dir.resolve()
    print(f"--- Checking Architecture in: {project_dir} ---")

    rules = []

    # 1. Try to load from specific rules file
    if args.rules and Path(args.rules).exists():
        try:
            with open(args.rules, 'r') as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, list):
                    rules = loaded
                elif isinstance(loaded, dict) and "architecture_rules" in loaded:
                    rules = loaded["architecture_rules"]
                else:
                    print(f"❌ Error: Invalid format in rules file {args.rules}. Expected list or dict with 'architecture_rules'.", file=sys.stderr)
                    sys.exit(1)
            print(f"Loaded rules from {args.rules}")
        except Exception as e:
            print(f"❌ Error loading rules file: {e}", file=sys.stderr)
            sys.exit(1)

    # 2. Try to load from agent_config.yaml (if no specific rules file provided or additive?)
    # For now, if rules file is provided, use it. If not, look in config.
    elif not rules:
        from shared.config_loader import load_config_from_file
        config = load_config_from_file()
        if "architecture_rules" in config:
            rules = config["architecture_rules"]
            print("Loaded rules from agent configuration.")

    if not rules:
        print("⚠️  No architecture rules found. Please define 'architecture_rules' in agent_config.yaml or provide a --rules file.")
        print("Example rule format:")
        print("  - source: \"shared/**\"")
        print("    deny: \"agents/**\"")
        sys.exit(0)

    violations = check_architecture(project_dir, rules)

    if violations:
        print(f"\n❌ Found {len(violations)} architecture violation(s):")
        for v in violations:
            print(f"  - {v['source']} imports {v['imported']}")
            print(f"    Rule: {v['rule']}")
        sys.exit(1)
    else:
        print("\n✅ No architecture violations found.")
        sys.exit(0)

def run_analytics(args):
    """Runs project analytics."""
    if args.type == "git":
        from shared.analytics import _run_analytics_git_logic
        _run_analytics_git_logic(args.project_dir)
    elif args.type == "code":
        print(_run_context_analyze_logic(args.project_dir))
    elif args.type == "complexity":
        from shared.complexity import _run_analytics_complexity_logic
        _run_analytics_complexity_logic(args.project_dir)
    sys.exit(0)

def run_duplication(args):
    """Runs the code duplication detector."""
    from shared.duplication import _run_duplication_logic
    _run_duplication_logic(
        project_dir=args.project_dir,
        min_tokens=args.min_tokens,
        files=args.files,
        ignore=args.ignore
    )
    sys.exit(0)

def run_unused(args):
    """Runs the unused code detector."""
    from shared.unused import _run_unused_logic
    _run_unused_logic(
        project_dir=args.project_dir,
        files=args.files,
        ignore=args.ignore
    )
    sys.exit(0)

def run_risk(args):
    """Runs the risk analysis (hotspots)."""
    from shared.risk_analysis import _run_risk_logic
    _run_risk_logic(
        project_dir=args.project_dir,
        limit=args.limit
    )
    sys.exit(0)

def run_impact(args):
    """Runs the predictive impact analysis."""
    from shared.impact import run_impact_logic
    run_impact_logic(
        project_dir=args.project_dir,
        json_output=args.json
    )
    sys.exit(0)

def run_a11y(args):
    """Runs the accessibility scanner."""
    from shared.a11y import _run_a11y_logic
    _run_a11y_logic(
        project_dir=args.project_dir,
        files=args.files,
        ignore=args.ignore,
        output_format=args.format
    )
    sys.exit(0)

def run_license(args):
    """Checks dependency license compliance."""
    from shared.dependencies import DependencyAnalyzer

    analyzer = DependencyAnalyzer(args.project_dir)
    data = analyzer.scan()

    allow_list = args.allow.split(",") if args.allow else None
    deny_list = args.deny.split(",") if args.deny else None

    results = analyzer.check_licenses(data, allow_list=allow_list, deny_list=deny_list)

    if args.action == "list":
        print(f"\n--- License Report for {args.project_dir} ---")
        print(f"  {'Package':<30} | {'License':<20} | {'Status':<10}")
        print("  " + "-" * 70)
        for item in results:
            pkg = item["package"]
            lic = item["license"]
            status = item["status"]

            # Truncate if too long
            if len(pkg) > 30: pkg = pkg[:27] + "..."
            if len(lic) > 20: lic = lic[:17] + "..."

            print(f"  {pkg:<30} | {lic:<20} | {status:<10}")

    elif args.action == "check":
        violations = [r for r in results if r["status"] == "VIOLATION"]
        if not violations:
            print("✅ No license violations found.")
            sys.exit(0)
        else:
            print(f"❌ Found {len(violations)} license violation(s):")
            for v in violations:
                print(f"  - {v['package']} ({v['license']}): {v['message']}")
            sys.exit(1)

    sys.exit(0)

def run_deps(args):
    """Generates a dependency graph or updates dependencies."""
    from shared.dependencies import _run_deps_logic, DependencyAnalyzer, DependencyUpdater

    if args.update:
        # 1. Scan and check for updates
        print("Scanning project and checking for updates...")
        analyzer = DependencyAnalyzer(args.project_dir)
        data = analyzer.scan()
        data = analyzer.check_updates(data)

        # 2. Collect outdated packages
        outdated_list = []
        for lang, files in data.items():
            for file_info in files:
                source = file_info["source"]
                file_path = args.project_dir / source
                for dep in file_info.get("dependencies", []):
                    if dep.get("outdated"):
                        outdated_list.append({
                            "lang": lang,
                            "file": file_path,
                            "name": dep["name"],
                            "current": dep.get("version", ""),
                            "latest": dep.get("latest", ""),
                            "type": dep.get("type", "prod")
                        })

        if not outdated_list:
            print("✅ All dependencies are up to date.")
            sys.exit(0)

        # 3. Interactive Selection
        print("\n--- Outdated Dependencies ---")
        for i, item in enumerate(outdated_list):
            print(f"[{i+1}] {item['name']} ({item['lang']}): {item['current']} -> {item['latest']} (in {item['file'].name})")

        print("\nEnter numbers to update (e.g., '1 3 5'), 'a' for all, or Enter to cancel.")
        try:
            selection = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)

        to_update = []
        if selection == 'a':
            to_update = outdated_list
        elif selection:
            try:
                indices = [int(x) - 1 for x in selection.split()]
                for idx in indices:
                    if 0 <= idx < len(outdated_list):
                        to_update.append(outdated_list[idx])
            except ValueError:
                print("Invalid input.")
                sys.exit(1)
        else:
            print("Aborted.")
            sys.exit(0)

        if not to_update:
            print("No valid packages selected.")
            sys.exit(0)

        # 4. Perform Updates
        updater = DependencyUpdater(args.project_dir)
        print(f"\nUpdating {len(to_update)} packages...")

        for item in to_update:
            print(f"Updating {item['name']}...")
            success = updater.update_dependency(
                item['file'],
                item['name'],
                item['latest'],
                item['type']
            )
            if success:
                print(f"✅ Updated {item['name']}")
            else:
                print(f"❌ Failed to update {item['name']}")

        sys.exit(0)

    print(_run_deps_logic(args.project_dir, args.format, args.check))
    sys.exit(0)

async def run_optimize(args):
    """Runs the optimization logic."""
    from shared.optimize import OptimizationManager

    project_dir = args.project_dir.resolve()
    manager = OptimizationManager(project_dir)

    success = await manager.optimize(
        script_path=Path(args.script),
        args=args.args,
        agent_type=args.agent,
        model=args.model
    )
    sys.exit(0 if success else 1)


def run_knowledge(args):
    """Manages the agent's knowledge base."""
    from shared.database import init_db
    from shared.knowledge import KnowledgeManager
    from rich.console import Console
    from rich.table import Table

    # Ensure DB is initialized
    config_dir = args.project_dir.resolve()
    config_dir.mkdir(parents=True, exist_ok=True)
    init_db(config_dir / ".agent_db.sqlite")

    manager = KnowledgeManager()
    console = Console()

    if args.action == "list":
        items = manager.list_knowledge(category=args.category)
        if not items:
            console.print("No knowledge items found.", style="yellow")
            sys.exit(0)

        table = Table(title=f"Agent Knowledge ({args.category if args.category else 'All'})")
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Source", style="green")
        table.add_column("Content", style="white")

        for item in items:
            table.add_row(str(item.id), item.category, item.source_agent, item.content)

        console.print(table)

    elif args.action == "add":
        if not args.content:
            console.print("Error: Content is required for 'add' action.", style="red")
            sys.exit(1)

        item = manager.add_knowledge(args.content, category=args.category, source="user")
        console.print(f"[green]Added knowledge item #{item.id}[/green]")

    elif args.action == "delete":
        if not args.id:
             console.print("Error: ID is required for 'delete' action.", style="red")
             sys.exit(1)

        if manager.delete_knowledge(int(args.id)):
            console.print(f"[green]Deleted knowledge item #{args.id}[/green]")
        else:
            console.print(f"[red]Item #{args.id} not found.[/red]")

    elif args.action == "questions":
        questions = manager.get_questions(status=args.status)
        if not questions:
            console.print(f"No {args.status} questions found.", style="yellow")
            sys.exit(0)

        table = Table(title=f"Agent Questions ({args.status})")
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Source", style="green")
        table.add_column("Question", style="white")
        if args.status == "answered":
             table.add_column("Answer", style="yellow")

        for q in questions:
            row = [str(q.id), q.source_agent, q.question]
            if args.status == "answered":
                row.append(q.answer)
            table.add_row(*row)

        console.print(table)

    elif args.action == "answer":
         if not args.id or not args.answer:
              console.print("Error: ID and Answer are required.", style="red")
              sys.exit(1)

         if manager.answer_question(int(args.id), args.answer):
              console.print(f"[green]Answered question #{args.id}[/green]")
         else:
              console.print(f"[red]Question #{args.id} not found.[/red]")

    elif args.action == "graph":
        from shared.knowledge_graph import generate_knowledge_graph
        result = generate_knowledge_graph(
            project_dir=args.project_dir,
            output_format=args.format,
            output_file=Path(args.output) if args.output else None
        )
        print(result)

    sys.exit(0)


async def run_ask(args):
    """Queries the codebase using the configured agent."""
    # Setup logging
    logger, _ = setup_logger(name="ask_logger", log_file=None, verbose=args.verbose, console_output=True)

    success = await run_ask_logic(
        query=args.query,
        project_dir=args.project_dir,
        agent_type=args.agent,
        model=args.model,
        files=args.files,
        verbose=args.verbose
    )
    sys.exit(0 if success else 1)


async def run_do(args):
    """Translates natural language to shell commands."""
    # Setup logging
    logger, _ = setup_logger(name="do_logger", log_file=None, verbose=args.verbose, console_output=True)

    success = await run_do_logic(
        instruction=args.instruction,
        project_dir=args.project_dir,
        agent_type=args.agent,
        model=args.model,
        verbose=args.verbose,
        yes=args.yes
    )
    sys.exit(0 if success else 1)


async def run_debug(args):
    """Executes a command and uses AI to debug if it fails."""
    # Setup logging
    logger, _ = setup_logger(name="debug_logger", log_file=None, verbose=args.verbose, console_output=True)

    if not args.command_to_run:
        print("Error: No command provided to debug.", file=sys.stderr)
        sys.exit(1)

    success = await run_debug_logic(
        command_list=args.command_to_run,
        project_dir=args.project_dir,
        agent_type=args.agent,
        model=args.model,
        verbose=args.verbose
    )
    sys.exit(0 if success else 1)


async def run_code_review(args):
    """Runs an AI-powered code review."""
    # Setup logging
    logger, _ = setup_logger(name="review_logger", log_file=None, verbose=args.verbose, console_output=True)

    success = await run_code_review_logic(
        project_dir=args.project_dir,
        files=args.files,
        diff=args.diff,
        agent_type=args.agent,
        model=args.model,
        verbose=args.verbose
    )
    sys.exit(0 if success else 1)


async def run_summarize(args):
    """Summarizes git changes using AI."""
    # Setup logging
    logger, _ = setup_logger(name="summarize_logger", log_file=None, verbose=args.verbose, console_output=True)

    success = await run_summarize_logic(
        project_dir=args.project_dir,
        target=args.target,
        agent_type=args.agent,
        model=args.model,
        verbose=args.verbose
    )
    sys.exit(0 if success else 1)


def run_context(args):
    """Displays an analysis of the agent's context."""
    if args.action == "show":
        context_output = _run_context_show_logic(project_dir=args.project_dir)
        print(context_output)
    elif args.action == "analyze":
        context_output = _run_context_analyze_logic(project_dir=args.project_dir)
        print(context_output)
    sys.exit(0)

def run_next(args):
    """Analyzes the project and executes the next logical command upon confirmation."""
    success = _run_next_logic(project_dir=args.project_dir)
    sys.exit(0 if success else 1)

def run_blame(args):
    """Shows the agent Run ID or author for each line of a file."""
    blame_output = _run_blame_logic(project_dir=args.project_dir, filepath=args.filepath)
    print(blame_output)
    if "❌ Error" in blame_output:
        sys.exit(1)
    sys.exit(0)


def run_smart_search(args):
    """Runs a smart semantic search using BM25."""
    from shared.smart_search import SmartSearchEngine

    project_dir = args.project_dir.resolve()
    print(f"--- Smart Search in: {project_dir} ---")
    print(f"Indexing codebase... (this might take a moment)")

    engine = SmartSearchEngine(project_dir)
    engine.index(file_pattern=args.files)

    print(f"Indexed {engine.num_docs} documents.")
    print(f"Searching for: '{args.query}'")

    results = engine.search(args.query, limit=args.limit)

    if not results:
        print("✅ No relevant results found.")
        sys.exit(0)

    print(f"\nFound {len(results)} relevant results:\n")

    for i, res in enumerate(results):
        print(f"[{i+1}] \033[1m{res['file']}\033[0m (Score: {res['score']:.2f})")
        print(f"    \033[90m{res['snippet']}\033[0m") # Gray snippet
        print()

    sys.exit(0)


def run_search(args):
    """Searches the codebase for a pattern."""
    from shared.search import search_codebase

    project_dir = args.project_dir.resolve()

    print(f"--- Searching in: {project_dir} ---")
    print(f"Pattern: {args.pattern}")

    try:
        results = search_codebase(
            project_dir,
            args.pattern,
            file_pattern=args.files,
            case_sensitive=args.case_sensitive,
            is_regex=args.regex,
            context_lines=args.context
        )
    except Exception as e:
        print(f"❌ Error during search: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("✅ No matches found.")
        sys.exit(0)

    # Group by file for cleaner output
    results_by_file = {}
    for res in results:
        f = res['file']
        if f not in results_by_file:
            results_by_file[f] = []
        results_by_file[f].append(res)

    for file_path, matches in results_by_file.items():
        print(f"\n📄 \033[1m{file_path}\033[0m") # Bold filename
        for m in matches:
            # Context before
            for ctx in m['context_before']:
                print(f"    \033[90m{ctx}\033[0m") # Gray context

            # Match
            # Highlight the pattern in the content?
            # Simple highlight if not regex or complex
            content = m['content']
            # We skip highlighting for now to avoid messiness with regex matches
            print(f"  \033[32m{m['line']}\033[0m: {content}") # Green line num

            # Context after
            for ctx in m['context_after']:
                print(f"    \033[90m{ctx}\033[0m")

    print(f"\nFound {len(results)} matches in {len(results_by_file)} files.")
    sys.exit(0)


def run_replace(args):
    """Replaces text in the codebase."""
    from shared.replace import replace_in_codebase

    project_dir = args.project_dir.resolve()

    print(f"--- Replacing in: {project_dir} ---")
    print(f"Pattern: {args.pattern}")
    print(f"Replacement: {args.replacement}")
    if args.dry_run:
        print("(Dry Run - No changes will be saved)")

    try:
        stats = replace_in_codebase(
            project_dir,
            args.pattern,
            args.replacement,
            file_pattern=args.files,
            case_sensitive=args.case_sensitive,
            is_regex=args.regex,
            dry_run=args.dry_run
        )
    except Exception as e:
        print(f"❌ Error during replace: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nMatched files: {stats['files_matched']}")
    print(f"Files changed: {stats['files_changed']}")
    print(f"Replacements:  {stats['replacements_count']}")

    if stats["diffs"]:
        print("\n--- Diffs ---")
        for file, diff in stats["diffs"].items():
            print(f"📄 {file}")
            print(diff)
            print("-" * 20)

    if args.dry_run and stats['files_changed'] > 0:
        print("\nTo apply these changes, run the command again without --dry-run")

    sys.exit(0)


def run_todos(args):
    """Scans the project for TODO comments."""
    from shared.todos import scan_todos, get_todo_blame

    project_dir = args.project_dir.resolve()
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else None

    if not args.json:
        print(f"--- Scanning for TODOs in: {project_dir} ---")
        if tags:
            print(f"Tags: {', '.join(tags)}")

    try:
        todos = scan_todos(project_dir, tags=tags)
    except Exception as e:
        print(f"❌ Error scanning for TODOs: {e}", file=sys.stderr)
        sys.exit(1)

    if not todos:
        print("✅ No TODOs found.")
        sys.exit(0)

    # Process results (blame if requested)
    if args.blame:
        print("Fetching git blame information (this might take a moment)...")
        for todo in todos:
            blame_info = get_todo_blame(project_dir, todo['file'], todo['line'])
            todo['author'] = blame_info.get('author', 'Unknown')
            todo['date'] = blame_info.get('date', 'Unknown')

    # Output formatting
    if args.json:
        print(json.dumps(todos, indent=2))
        sys.exit(0)

    # Console output
    # Group by file
    todos_by_file = {}
    for todo in todos:
        file_path = todo['file']
        if file_path not in todos_by_file:
            todos_by_file[file_path] = []
        todos_by_file[file_path].append(todo)

    for file_path, file_todos in sorted(todos_by_file.items()):
        print(f"\n📄 {file_path}")
        for todo in file_todos:
            line_str = str(todo['line']).rjust(4)
            tag_str = todo['tag'].ljust(5)
            text = todo['text']

            blame_str = ""
            if args.blame:
                author = todo.get('author', 'Unknown')
                date = todo.get('date', 'Unknown')
                blame_str = f" [{author}, {date}]"

            print(f"  {line_str}: {tag_str} {text}{blame_str}")

    print(f"\nFound {len(todos)} item(s).")
    sys.exit(0)


def run_stash(args):
    """Manages git stashes for the project."""
    project_dir = args.project_dir.resolve()

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path or not (project_dir / ".git").is_dir():
        print("❌ Error: Not a git repository. Cannot manage stashes.", file=sys.stderr)
        sys.exit(1)

    # --- Action Dispatcher ---
    if args.action == "push":
        _stash_push(args, git_path, project_dir)
    elif args.action == "list":
        _stash_list(args, git_path, project_dir)
    elif args.action == "pop":
        _stash_pop(args, git_path, project_dir)
    elif args.action == "drop":
        _stash_drop(args, git_path, project_dir)

def _stash_push(args, git_path, project_dir):
    """Stashes uncommitted changes."""
    print(f"--- Stashing changes in: {project_dir} ---")
    try:
        # Check if there's anything to stash
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if not status_result.stdout.strip():
            print("✅ No changes to stash.")
            sys.exit(0)

        cmd = [git_path, "-C", str(project_dir), "stash", "push", "-u"]
        if args.message:
            cmd.extend(["-m", args.message])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error stashing changes: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        print("✅ Changes stashed successfully.")
        _stash_list(args, git_path, project_dir, count=1) # Show the latest stash

    except subprocess.CalledProcessError as e:
        print(f"❌ An error occurred: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def _stash_list(args, git_path, project_dir, count=None):
    """Lists all available stashes."""
    print(f"--- Stashes in: {project_dir} ---")
    try:
        cmd = [git_path, "-C", str(project_dir), "stash", "list"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        stashes = result.stdout.strip().split('\n')
        if not stashes or not stashes[0]:
            print("No stashes found.")
            return []

        if count:
            stashes = stashes[:count]

        for stash in stashes:
            print(f"  {stash}")
        return stashes

    except subprocess.CalledProcessError as e:
        print(f"❌ Error listing stashes: {e.stderr}", file=sys.stderr)
        return []

def _stash_pop(args, git_path, project_dir):
    """Interactively applies and removes a stash."""
    stashes = _stash_list(args, git_path, project_dir)
    if not stashes:
        sys.exit(0)

    try:
        selection_str = input(f"\nEnter the number of the stash to pop (0-{len(stashes)-1}), or press Enter to cancel: ").strip()
        if not selection_str:
            print("Aborted.")
            sys.exit(0)

        selection = int(selection_str)
        if not (0 <= selection < len(stashes)):
            print("❌ Invalid selection.", file=sys.stderr)
            sys.exit(1)

        stash_ref = f"stash@{{{selection}}}"
        print(f"\nPopping {stash_ref}...")

        result = subprocess.run(
            [git_path, "-C", str(project_dir), "stash", "pop", str(selection)],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"❌ Error popping stash: {result.stderr}", file=sys.stderr)
            if result.stdout:
                print(f"Output:\n{result.stdout}")
            sys.exit(1)

        print(f"✅ Stash {stash_ref} popped successfully.")
        if result.stdout:
            print(result.stdout)

    except (ValueError, IndexError):
        print("❌ Invalid input. Please enter a valid number.", file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        sys.exit(0)

def _stash_drop(args, git_path, project_dir):
    """Interactively deletes a stash."""
    stashes = _stash_list(args, git_path, project_dir)
    if not stashes:
        sys.exit(0)

    try:
        selection_str = input(f"\nEnter the number of the stash to drop (0-{len(stashes)-1}), or press Enter to cancel: ").strip()
        if not selection_str:
            print("Aborted.")
            sys.exit(0)

        selection = int(selection_str)
        if not (0 <= selection < len(stashes)):
            print("❌ Invalid selection.", file=sys.stderr)
            sys.exit(1)

        stash_ref = f"stash@{{{selection}}}"

        if not args.yes:
            confirm = input(f"Are you sure you want to delete {stash_ref}? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        print(f"\nDropping {stash_ref}...")
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "stash", "drop", str(selection)],
            check=True, capture_output=True, text=True
        )

        print(f"✅ Stash {stash_ref} dropped successfully.")
        print(result.stdout.strip())

    except (ValueError, IndexError):
        print("❌ Invalid input. Please enter a valid number.", file=sys.stderr)
        sys.exit(1)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        print(f"❌ Error dropping stash: {stderr}", file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        sys.exit(0)


def run_report(args):
    """Generates a summary report for a specific agent run."""
    success = _run_report_logic(
        run_id=args.run_id,
        output_path=args.output,
        project_dir=args.project_dir
    )
    sys.exit(0 if success else 1)

def run_dashboard(args):
    """Displays a comprehensive dashboard of the project's status."""
    dashboard_text = _run_dashboard_logic(project_dir=args.project_dir)
    print(dashboard_text)
    sys.exit(0)

def run_tree(args):
    """Displays a tree view of the project directory."""
    tree_output = _run_tree_logic(
        project_dir=args.project_dir,
        depth=args.depth,
        full=args.full
    )
    print(tree_output)
    sys.exit(0)


def run_summary(args):
    """Displays a high-level summary of the project's status."""
    print("Warning: The 'summary' command is deprecated and will be removed in a future version. "
          "Please use the 'status' command instead.", file=sys.stderr)
    summary_text = get_project_summary(project_dir=args.project_dir)
    print(summary_text)
    sys.exit(0)


def run_suggest(args):
    """Analyzes the project and suggests the next logical commands to run."""
    suggestions = get_suggestions(project_dir=args.project_dir)
    if not suggestions:
        print("✅ Project is in a clean state. No specific actions to suggest.")
        print("   - To start a new task, run the agent with a --spec or --jira-ticket.")
        sys.exit(0)

    print("--- Suggested Next Steps ---")
    print("Based on the current project state, here are some suggested commands:\n")
    for suggestion in suggestions:
        print(f"👉 {suggestion['command']}")
        print(f"   Reason: {suggestion['reason']}\n")
    sys.exit(0)


def run_status(args):
    """Displays the current status of the agent project."""
    status_text = _run_enhanced_status_logic(project_dir=args.project_dir)
    print(status_text)
    sys.exit(0)


def run_glance(args):
    """Displays a compact, high-level overview of the project's status."""
    project_dir = args.project_dir.resolve()

    # 1. Get Workflow Stage
    stage_key = get_workflow_stage(project_dir)
    stage_info = WORKFLOW_STAGES.get(stage_key, {"name": "Unknown"})

    # 2. Get Git Status Summary (brief)
    git_path = shutil.which("git")
    git_summary = "Git not found"
    if git_path and (project_dir / ".git").is_dir():
        try:
            result = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
            if not changes:
                git_summary = "✅ Clean"
            else:
                untracked = sum(1 for line in changes if line.startswith('??'))
                tracked_changes = [line for line in changes if not line.startswith('??')]
                staged = sum(1 for line in tracked_changes if line and line[0] != ' ')
                unstaged = sum(1 for line in tracked_changes if line and len(line) > 1 and line[1] != ' ')
                summary_parts = []
                if staged: summary_parts.append(f"{staged} staged")
                if unstaged: summary_parts.append(f"{unstaged} unstaged")
                if untracked: summary_parts.append(f"{untracked} untracked")
                git_summary = f"⚠️ {', '.join(summary_parts)}"
        except (subprocess.CalledProcessError, FileNotFoundError):
            git_summary = "Error checking status"

    # 3. Get Next Suggested Action
    suggestions = get_suggestions(project_dir, limit=1)
    next_action = suggestions[0]['command'] if suggestions else "No specific suggestion."

    # --- Formatting the Output ---
    # Use ANSI escape codes for color and boldness
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    CYAN_BOLD = BOLD + CYAN

    print(f"{BOLD}--- Project Glance: {project_dir.name} ---{ENDC}")
    print(f"  {CYAN_BOLD}Stage{ENDC}:     {stage_info['name']}")
    print(f"  {CYAN_BOLD}Git Status{ENDC}: {git_summary}")
    print(f"  {CYAN_BOLD}Next Step{ENDC}:  `{next_action}`")


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
                    # Read first line for timestamp
                    first_line_raw = f.readline()
                    first_line = first_line_raw.strip()

                    if not first_line:
                        print("  Log file is empty.")
                    else:
                        timestamp = first_line.split(" - ")[0] if " - " in first_line else "[No Timestamp]"
                        print(f"  Timestamp: {timestamp}")
                        print("  Log Summary (last 5 lines):")

                        # Reset to beginning to get full tail to correctly capture the last 5 lines
                        # even if the file is short or the first line is part of the last 5.
                        f.seek(0)
                        last_lines = deque((line.strip() for line in f if line.strip()), maxlen=5)
                        for line in last_lines:
                            print(f"    {line}")

            except Exception as e:
                print(f"  Error reading log file: {e}")
        else:
            print("  Log file not found.")

def run_history(args):
    """Displays a history of agent runs for the project."""
    _run_history_logic(project_dir=args.project_dir)
    sys.exit(0)


def _run_last_logic(project_dir):
    """The core logic for displaying a summary of the last agent run."""
    print(f"--- Summary of Last Run: {project_dir} ---")

    # 1. Get the last run ID
    history_file = project_dir / ".agent_history"
    if not history_file.exists():
        print("No agent run history found for this project.")
        return False

    try:
        with open(history_file, "r") as f:
            run_ids = [line.strip() for line in f if line.strip()]
        if not run_ids:
            print("History is empty.")
            return False
        last_run_id = run_ids[-1]
        print(f"Last Run ID: {last_run_id}")
    except IOError as e:
        print(f"Error reading history file: {e}", file=sys.stderr)
        return False

    # 2. Display Metrics
    metrics_file = _find_metrics_file(last_run_id, project_dir)
    if metrics_file:
        metrics = _parse_metrics(metrics_file)
        # Reuse the display table but with a different title
        _display_metrics_table(metrics, f"Performance Metrics")
    else:
        print("\n--- Performance Metrics ---")
        print("No metrics file found for the last run.")

    # 3. Display QA Summary
    print("\n--- QA Summary ---")
    qa_summary_file = project_dir / "qa_summary.txt"
    if qa_summary_file.exists():
        try:
            summary_content = qa_summary_file.read_text().strip()
            print(summary_content)
        except IOError as e:
            print(f"Error reading qa_summary.txt: {e}")
    else:
        print("No QA summary found for the last run.")

    # 4. Display Log Summary
    print("\n--- Log Summary (Last 10 lines) ---")
    repo_root = Path(__file__).parent
    log_file = repo_root / f"agents/logs/{last_run_id}.log"
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                last_lines = deque((line.strip() for line in f if line.strip()), maxlen=10)
                for line in last_lines:
                    print(f"  {line}")
        except IOError as e:
            print(f"Error reading log file: {e}")
    else:
        print("Log file not found.")

    return True

def run_last(args):
    """Displays a summary of the last agent run."""
    success = _run_last_logic(project_dir=args.project_dir)
    sys.exit(0 if success else 1)


def run_last_run_id(args):
    """Prints the ID of the last agent run to stdout."""
    project_dir = args.project_dir.resolve()
    history_file = project_dir / ".agent_history"

    if not history_file.exists():
        # Using stderr for errors to not pollute stdout, which is meant for the ID
        print("No agent run history found for this project.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(history_file, "r") as f:
            run_ids = [line.strip() for line in f if line.strip()]
        if not run_ids:
            print("History is empty.", file=sys.stderr)
            sys.exit(1)
        last_run_id = run_ids[-1]
        print(last_run_id)  # Print the ID to stdout
        sys.exit(0)
    except IOError as e:
        print(f"Error reading history file: {e}", file=sys.stderr)
        sys.exit(1)


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


def run_diff(args):
    """Shows a detailed, colorized diff of uncommitted changes or a specific commit."""
    project_dir = args.project_dir.resolve()
    target = args.target

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot show diff.", file=sys.stderr)
        sys.exit(1)

    # --- Logic ---
    try:
        if not target:
            # Case 1: Show uncommitted changes
            print(f"--- Uncommitted Changes (HEAD): {project_dir} ---")
            cmd = [git_path, "-C", str(project_dir), "diff", "--color=always", "HEAD"]
            # Use subprocess.run without capturing output to stream directly
            result = subprocess.run(cmd)
            sys.exit(result.returncode)

        # Case 2: Target is provided (Run ID or commit hash)
        original_target = target
        # Check if it's a known git reference first
        is_git_ref = subprocess.run(
            [git_path, "-C", str(project_dir), "rev-parse", "--verify", f"{target}^{{commit}}"],
            capture_output=True, text=True
        ).returncode == 0

        if not is_git_ref:
            # If not a direct git ref, assume it's a Run ID
            commit_hash = _find_commit_by_run_id(project_dir, git_path, target)
            if not commit_hash:
                print(f"❌ Error: Target '{original_target}' is not a valid commit or Run ID.", file=sys.stderr)
                sys.exit(1)
            target = commit_hash
            print(f"--- Showing diff for Run ID '{original_target}' (Commit: {target[:7]}) ---")
        else:
            print(f"--- Showing diff for Commit: {target} ---")

        # Use 'git show' which nicely formats the commit info and the diff
        cmd = [git_path, "-C", str(project_dir), "show", "--color=always", target]
        result = subprocess.run(cmd)
        sys.exit(result.returncode)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        if isinstance(stderr, bytes): stderr = stderr.decode().strip()
        print(f"❌ An error occurred: {stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def _run_log_logic(project_dir, count=None):
    """The core logic for displaying the git commit history."""
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        return False

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot show log.", file=sys.stderr)
        return False

    print(f"--- Git Commit History: {project_dir} ---")
    try:
        cmd = [
            git_path,
            "-C", str(project_dir),
            "log",
            "--color=always",
            "--graph",
            "--pretty=format:%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset",
            "--abbrev-commit",
        ]
        if count is not None:
            cmd.extend(["-n", str(count)])

        result = subprocess.run(cmd)

        if result.returncode != 0:
            print(f"\n❌ Error: git log command failed with exit code {result.returncode}.", file=sys.stderr)
            return False

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        return False
    return True

def run_log(args):
    """Displays the git commit history for the project."""
    success = _run_log_logic(project_dir=args.project_dir, count=args.count)
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
                if lines is not None:
                    # To preserve original behavior (filter applied AFTER selecting last N lines):
                    # We must read the last N lines of the file, then filter.
                    # This means we use deque on the raw file, then apply filter.
                    log_lines = deque(f, maxlen=lines)
                else:
                    # Iterator to avoid loading full file
                    log_lines = f

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


def run_help(args):
    """Displays a structured and user-friendly help message."""
    # ANSI escape codes for formatting
    BOLD = '\033[1m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    ENDC = '\033[0m'

    def print_header(title):
        print(f"\n{BOLD}{CYAN}--- {title} ---{ENDC}")

    def print_command(name, description):
        print(f"  {YELLOW}{name:<20}{ENDC} {description}")

    executable_name = os.path.basename(sys.argv[0])
    print(f"{BOLD}Combined Autonomous Coding Agent{ENDC}")
    print("A unified CLI for running and managing autonomous coding agents.")
    print(f"\n{BOLD}Usage:{ENDC} {executable_name} [command] [options]")
    print(f"       {executable_name} --spec <spec_file> [options]  (to run the agent)")

    print_header("Getting Started")
    print_command("init", "Run an interactive setup wizard for a new project.")
    print_command("setup", "Install project dependencies based on the detected project type.")
    print_command("configure", "Create or update the global agent_config.yaml file.")
    print_command("doctor", "Run a health check on your environment and configuration.")
    print_command("list-agents", "List the available agent types (e.g., gemini, cursor).")
    print_command("models", "List recommended models for each agent type.")
    print_command("validate", "Validate the agent configuration file.")

    print_header("Core Commands")
    print_command("(run agent)", f"The default action. Use `main.py --spec <file>` to start.")
    print_command("plan", "Generate a feature plan from a spec file without executing code.")
    print_command("test", "Automatically detect project type and run tests.")
    print_command("lint", "Automatically detect project type and run a linter.")
    print_command("format", "Automatically detect project type and format code.")

    print_header("Inspection & History")
    print_command("status", "Show a detailed overview of the project's current status.")
    print_command("dashboard", "Display a comprehensive project dashboard.")
    print_command("history", "Show the history of agent runs for the project.")
    print_command("last", "Show a detailed summary of the very last agent run.")
    print_command("log", "Show the git commit history in a formatted view.")
    print_command("logs", "Show agent logs with filtering and real-time follow options.")
    print_command("tree", "Display a tree view of the project directory.")
    print_command("report", "Generate a Markdown summary report for a specific run.")
    print_command("blame", "Show which agent Run ID was responsible for each line in a file.")
    print_command("benchmark", "Analyze and compare performance metrics from different runs.")

    print_header("Git & Workflow")
    print_command("commit", "Stage all changes and create a commit, with interactive prompts.")
    print_command("push", "Safely push the current feature branch to the remote.")
    print_command("pull", "Safely pull the latest changes from the remote.")
    print_command("pr", "Manage GitHub pull requests for the project.")
    print_command("feature", "A guided workflow for branch -> commit -> push -> pr.")
    print_command("diff", "Show a detailed diff of uncommitted changes or a specific commit.")
    print_command("stash", "Stash uncommitted changes for later use.")
    print_command("discard", "Safely discard uncommitted changes by stashing them first.")
    print_command("undo", "Restore changes that were previously discarded.")
    print_command("rewind", "Reset the project state to a previous git commit or Run ID.")
    print_command("workflow", "Manually manage the agent's workflow state (e.g., advance to QA).")

    print_header("Artifact & Sprint Management")
    print_command("artifacts", "Manage trashed and archived agent-generated files.")
    print_command("snapshot", "Create and diff non-destructive snapshots of agent artifacts.")
    print_command("sprint", "Observe and manage the progress of a multi-agent sprint.")
    print_command("worktrees", "Manage git worktrees for concurrent sprint tasks.")

    print_header("Utilities")
    print_command("why", "Explain what a command does and why you might use it.")
    print_command("suggest", "Suggest the next logical command(s) based on project state.")
    print_command("shell", "Start an interactive shell with all commands available.")
    print_command("tui", "Start the interactive Textual User Interface (TUI).")
    print_command("show-config", "Show the final, resolved configuration that will be used for a run.")
    print_command("help", "Show this help message.")

    print(f"\nFor detailed options on a specific command, run: {executable_name} [command] --help")
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


def run_completion():
    """Prints the argcomplete shell script."""
    if argcomplete:
        executable_name = os.path.basename(sys.argv[0])
        print(argcomplete.shellcode([executable_name]))
        sys.exit(0)
    else:
        print("argcomplete is not installed. Please install it with 'pip install argcomplete'.", file=sys.stderr)
        sys.exit(1)




def _format_duration(seconds: float) -> str:
    """Formats seconds into a human-readable string (m s)."""
    seconds = float(seconds)
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes)}m {seconds:.2f}s"


PRICING_MODELS = {
    "gemini-1.5-pro": {"input": 3.50, "output": 10.50},  # Per 1M tokens
    "gemini-1.5-flash": {"input": 0.35, "output": 1.05},
    "claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    "gpt-4o": {"input": 5.00, "output": 15.00},
    "unknown": {"input": 0.0, "output": 0.0},
}

def run_cost(args):
    """Estimates the cost of the agent run based on token usage."""
    run_id = args.run_id
    project_dir = args.project_dir.resolve()

    if not run_id:
        # Default to latest run
        metrics_file = project_dir / "final_metrics.txt"
        if not metrics_file.exists():
             # Try history
             history_file = project_dir / ".agent_history"
             if history_file.exists():
                 try:
                     with open(history_file, "r") as f:
                         run_ids = [line.strip() for line in f if line.strip()]
                     if run_ids:
                         run_id = run_ids[-1]
                 except IOError:
                     pass

        if not run_id and not metrics_file.exists():
             print("❌ Error: Could not determine Run ID or find metrics file.", file=sys.stderr)
             sys.exit(1)

    if run_id:
        metrics_file = _find_metrics_file(run_id, project_dir)
        if not metrics_file:
            print(f"❌ Error: Could not find metrics for Run ID: {run_id}", file=sys.stderr)
            sys.exit(1)

    metrics = _parse_metrics(metrics_file)
    if not metrics:
        print("❌ Error: Metrics file is empty or could not be parsed.", file=sys.stderr)
        sys.exit(1)

    print(f"--- Cost Estimate for Run: {metrics.get('Run ID', 'Unknown')} ---")

    model = metrics.get("Model", "unknown")
    # Clean up model string (sometimes it has extra info or is "auto")
    pricing = PRICING_MODELS.get(model, None)
    if not pricing:
        # fuzzy match?
        for key in PRICING_MODELS:
            if key in model:
                pricing = PRICING_MODELS[key]
                break

    if not pricing:
        print(f"⚠️  Warning: No pricing model found for '{model}'. Using $0.00.")
        pricing = {"input": 0.0, "output": 0.0}
    else:
        print(f"Model: {model} (Pricing: ${pricing['input']}/1M in, ${pricing['output']}/1M out)")

    # Extract detailed usage if available (from our new parser logic)
    # We stored breakdowns as `llm_tokens_total__{model}__{type}`

    input_tokens = 0
    output_tokens = 0

    # Try to find breakdown keys
    for key, value in metrics.items():
        if key.startswith("llm_tokens_total__"):
            parts = key.split("__")
            if len(parts) == 3:
                # _, model_label, type_label = parts
                type_label = parts[2]
                if type_label == "input":
                    input_tokens += value
                elif type_label == "output":
                    output_tokens += value

    # Fallback to total if breakdown not found (e.g. legacy metrics)
    total_tokens = metrics.get("LLM Tokens Used", 0)
    if input_tokens == 0 and output_tokens == 0 and total_tokens > 0:
        print("⚠️  Detailed input/output breakdown not available. Assuming 75% input, 25% output.")
        input_tokens = total_tokens * 0.75
        output_tokens = total_tokens * 0.25

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost

    print(f"\nUsage:")
    print(f"  Input Tokens:  {int(input_tokens):,}")
    print(f"  Output Tokens: {int(output_tokens):,}")
    print(f"  Total Tokens:  {int(input_tokens + output_tokens):,}")

    print(f"\nEstimated Cost:")
    print(f"  Input:  ${input_cost:.4f}")
    print(f"  Output: ${output_cost:.4f}")
    print(f"  Total:  ${total_cost:.4f}")

    sys.exit(0)


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


def run_branch(args):
    """Manages the agent's dedicated feature branch."""
    project_dir = args.project_dir.resolve()
    git_path = shutil.which("git")
    branch_file = project_dir / ".agent_branch"

    if not git_path or not (project_dir / ".git").is_dir():
        print("❌ Error: Not a git repository. Cannot manage branches.", file=sys.stderr)
        sys.exit(1)

    action = args.action
    branch_name = args.branch_name

    current_agent_branch = branch_file.read_text().strip() if branch_file.exists() else None

    if action == "create":
        if not branch_name:
            print("❌ Error: 'create' action requires a branch name.", file=sys.stderr)
            sys.exit(1)
        try:
            print(f"Creating and checking out new branch: {branch_name}")
            subprocess.run([git_path, "-C", str(project_dir), "checkout", "-b", branch_name], check=True, capture_output=True)
            branch_file.write_text(branch_name)
            print(f"✅ Agent branch set to '{branch_name}'.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().strip()
            print(f"❌ Error creating branch: {stderr}", file=sys.stderr)
            sys.exit(1)

    elif action == "checkout":
        if not branch_name:
            print("❌ Error: 'checkout' action requires a branch name.", file=sys.stderr)
            sys.exit(1)
        try:
            print(f"Checking out branch: {branch_name}")
            subprocess.run([git_path, "-C", str(project_dir), "checkout", branch_name], check=True, capture_output=True)
            branch_file.write_text(branch_name)
            print(f"✅ Agent branch set to '{branch_name}'.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().strip()
            print(f"❌ Error checking out branch: {stderr}", file=sys.stderr)
            sys.exit(1)

    elif action == "status":
        if current_agent_branch:
            print(f"Agent is currently working on branch: '{current_agent_branch}'")
        else:
            print("Agent is not configured to use a specific branch. Using default behavior.")

    elif action == "merge":
        if not current_agent_branch:
            print("❌ Error: No agent branch is set. Nothing to merge.", file=sys.stderr)
            sys.exit(1)

        main_branch = "main"
        try:
            subprocess.run([git_path, "-C", str(project_dir), "checkout", main_branch], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            if "did not match any file(s) known to git" in e.stderr:
                main_branch = "master" # Fallback to master
                try:
                    subprocess.run([git_path, "-C", str(project_dir), "checkout", main_branch], check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as e2:
                    stderr = e2.stderr.strip()
                    print(f"❌ Error checking out '{main_branch}': {stderr}", file=sys.stderr)
                    sys.exit(1)
            else:
                stderr = e.stderr.strip()
                print(f"❌ Error checking out '{main_branch}': {stderr}", file=sys.stderr)
                sys.exit(1)

        print(f"Merging '{current_agent_branch}' into '{main_branch}'...")
        try:
            subprocess.run([git_path, "-C", str(project_dir), "merge", current_agent_branch], check=True, capture_output=True)
            print("✅ Merge successful.")
            if not args.keep_branch:
                print(f"Deleting branch '{current_agent_branch}'...")
                subprocess.run([git_path, "-C", str(project_dir), "branch", "-d", current_agent_branch], check=True, capture_output=True)
                branch_file.unlink()
                print("✅ Branch deleted and agent branch config removed.")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().strip()
            print(f"❌ Error during merge: {stderr}", file=sys.stderr)
            print("Please resolve conflicts manually.")
            sys.exit(1)

    elif action == "list":
        print("--- Agent-Related Branches ---")
        if current_agent_branch:
            print(f"  * {current_agent_branch} (active)")
        try:
            result = subprocess.run([git_path, "-C", str(project_dir), "branch", "--list"], capture_output=True, text=True, check=True)
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line.startswith("*"):
                    line = line[2:]
                if line != current_agent_branch:
                    print(f"    {line}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error listing branches: {e.stderr}", file=sys.stderr)

    sys.exit(0)


def run_recipes(args):
    """Manages and runs agent recipes."""
    from shared.recipes import RecipeManager

    project_dir = args.project_dir.resolve()
    manager = RecipeManager(project_dir)

    if args.action == "list":
        recipes = manager.list_recipes()
        if not recipes:
            print("No recipes found.")
            sys.exit(0)
        print("--- Available Recipes ---")
        for name, steps in recipes.items():
            print(f"\n🏷️  {name}")
            for i, step in enumerate(steps):
                print(f"  {i+1}. {step}")
        sys.exit(0)

    elif args.action == "show":
        if not args.name:
             print("Error: Name required for 'show' action.", file=sys.stderr)
             sys.exit(1)
        steps = manager.get_recipe(args.name)
        if not steps:
            print(f"Recipe '{args.name}' not found.", file=sys.stderr)
            sys.exit(1)
        print(f"--- Recipe: {args.name} ---")
        for i, step in enumerate(steps):
            print(f"  {i+1}. {step}")
        sys.exit(0)

    elif args.action == "run":
        if not args.name:
             print("Error: Name required for 'run' action.", file=sys.stderr)
             sys.exit(1)
        success = manager.run_recipe(args.name, dry_run=args.dry_run)
        sys.exit(0 if success else 1)

    elif args.action == "delete":
        if not args.name:
             print("Error: Name required for 'delete' action.", file=sys.stderr)
             sys.exit(1)
        if manager.delete_recipe(args.name):
            print(f"✅ Deleted recipe '{args.name}'.")
        else:
             print(f"Recipe '{args.name}' not found.", file=sys.stderr)
             sys.exit(1)

    elif args.action == "create":
        print("--- Create New Recipe ---")
        name = args.name
        if not name:
            name = input("Recipe name: ").strip()
        if not name:
            print("Aborted.")
            sys.exit(1)

        print(f"Enter commands for recipe '{name}' (one per line).")
        print("Enter an empty line to finish.")
        steps = []
        while True:
            cmd = input(f"Step {len(steps)+1}> ").strip()
            if not cmd:
                break
            steps.append(cmd)

        if not steps:
            print("No steps provided. Aborted.")
            sys.exit(1)

        if manager.add_recipe(name, steps):
            print(f"✅ Recipe '{name}' created successfully.")
        else:
            print("❌ Error saving recipe.")
            sys.exit(1)


def run_hooks(args):
    """Manages git hooks for the project."""
    from shared.hooks import install_pre_commit_hook, uninstall_pre_commit_hook, run_hooks_logic

    project_dir = args.project_dir.resolve()

    if args.action == "install":
        success = install_pre_commit_hook(project_dir)
        sys.exit(0 if success else 1)
    elif args.action == "uninstall":
        success = uninstall_pre_commit_hook(project_dir)
        sys.exit(0 if success else 1)
    elif args.action == "run":
        success = run_hooks_logic(project_dir)
        sys.exit(0 if success else 1)
    sys.exit(0)


def run_git(args):
    """Acts as a proxy to run git commands within a specified task's worktree."""
    project_dir = args.project_dir.resolve()
    task_id = args.task
    git_command = args.git_args

    if not task_id:
        print("❌ Error: The '--task' argument is required.", file=sys.stderr)
        sys.exit(1)

    if not git_command:
        print("❌ Error: No git command provided.", file=sys.stderr)
        sys.exit(1)

    worktree_name = f"sprint-task-{task_id}"
    worktree_path = project_dir / "worktrees" / worktree_name

    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found.", file=sys.stderr)
        sys.exit(1)

    if not worktree_path.is_dir():
        print(f"❌ Error: Worktree for task '{task_id}' not found at '{worktree_path}'.", file=sys.stderr)
        sys.exit(1)

    full_command = [git_path] + git_command

    try:
        # Execute the command from within the worktree directory, capturing output.
        result = subprocess.run(
            full_command,
            cwd=worktree_path,
            capture_output=True,
            text=True
        )
        # Print the captured output
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        # Exit with the same code as the git command
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(f"❌ Error: Command '{full_command[0]}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def run_test(args):
    """Detects the project type and runs the appropriate test command."""
    project_dir = args.project_dir.resolve()
    passthrough_args = args.test_args

    print(f"--- Running tests in: {project_dir} ---")

    # --- Project Detection ---
    command_base = []

    # 1. Node.js Project
    if (project_dir / "package.json").exists():
        print("Detected Node.js project.")
        # Prefer specific package managers if lock files exist
        if (project_dir / "yarn.lock").exists():
            command_base = ["yarn", "test"]
        elif (project_dir / "pnpm-lock.yaml").exists():
            command_base = ["pnpm", "test"]
        else:
            command_base = ["npm", "test"]

    # 2. Python Project
    elif (project_dir / "pyproject.toml").exists() or (project_dir / "requirements.txt").exists():
        print("Detected Python project.")
        # Prefer pytest if available
        if shutil.which("pytest"):
            command_base = ["pytest"]
        else:
            command_base = [sys.executable, "-m", "unittest", "discover"]

    # 3. Go Project
    elif (project_dir / "go.mod").exists():
        print("Detected Go project.")
        command_base = ["go", "test", "./..."]

    # --- Command Construction & Execution ---
    if not command_base:
        print("❌ Error: Could not detect a recognizable project type (Node.js, Python, Go).", file=sys.stderr)
        print("  Please ensure the project has a `package.json`, `pyproject.toml`, `requirements.txt`, or `go.mod` file.", file=sys.stderr)
        sys.exit(1)

    # Construct the full command
    full_command = command_base
    if passthrough_args:
        # npm requires a '--' separator before passing args to the script
        if command_base == ["npm", "test"]:
            full_command.append("--")
        full_command.extend(passthrough_args)


    print(f"Executing command: {' '.join(full_command)}")
    try:
        # Stream the output directly and run in the target project directory
        result = subprocess.run(full_command, cwd=project_dir)
        # Exit with the same code as the test runner
        sys.exit(result.returncode)

    except FileNotFoundError:
        print(f"❌ Error: Command '{full_command[0]}' not found. Is it installed and in your PATH?", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user.")
        sys.exit(130) # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"❌ An unexpected error occurred while running tests: {e}", file=sys.stderr)
        sys.exit(1)


def run_lint(args):
    """Detects the project type and runs the appropriate linter."""
    project_dir = args.project_dir.resolve()
    passthrough_args = args.lint_args
    is_fix_mode = args.fix

    print(f"--- Running linters in: {project_dir} ---")

    # --- Project Detection ---
    command_base = []
    fix_flags = []

    # 1. Node.js Project
    if (project_dir / "package.json").exists():
        print("Detected Node.js project.")
        # Assumes a 'lint' script is defined in package.json
        # E.g., "lint": "eslint ."
        # E.g., "lint:fix": "eslint . --fix"
        if is_fix_mode:
            # Check for a dedicated fix script first
            try:
                with open(project_dir / "package.json", 'r') as f:
                    package_data = json.load(f)
                    if "lint:fix" in package_data.get("scripts", {}):
                         command_base = ["npm", "run", "lint:fix"]
                    else:
                         command_base = ["npm", "run", "lint"]
                         fix_flags = ["--", "--fix"]
            except (IOError, json.JSONDecodeError):
                 command_base = ["npm", "run", "lint"]
                 fix_flags = ["--", "--fix"]

        else:
            command_base = ["npm", "run", "lint"]

    # 2. Python Project
    elif (project_dir / "pyproject.toml").exists() or (project_dir / "requirements.txt").exists():
        print("Detected Python project.")
        if shutil.which("ruff"):
            command_base = ["ruff", "check", "."]
            if is_fix_mode:
                fix_flags = ["--fix"]
        elif shutil.which("flake8"):
            command_base = ["flake8", "."]
            if is_fix_mode:
                print("Warning: --fix is not supported by flake8. Ignoring.", file=sys.stderr)
        elif shutil.which("pylint"):
            # Pylint is harder to auto-configure well, but we can try
            command_base = ["pylint", str(project_dir)]
            if is_fix_mode:
                print("Warning: --fix is not supported by pylint. Ignoring.", file=sys.stderr)
        else:
             print("Warning: No Python linter (ruff, flake8, pylint) found in PATH.", file=sys.stderr)

    # --- Command Construction & Execution ---
    if not command_base:
        print("❌ Error: Could not detect a recognizable project type or find a suitable linter.", file=sys.stderr)
        sys.exit(1)

    # Construct the full command
    full_command = command_base + (fix_flags if is_fix_mode else []) + passthrough_args

    print(f"Executing command: {' '.join(full_command)}")
    try:
        # Stream the output directly and run in the target project directory
        result = subprocess.run(full_command, cwd=project_dir)
        sys.exit(result.returncode)

    except FileNotFoundError:
        print(f"❌ Error: Command '{full_command[0]}' not found. Is it installed and in your PATH?", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nLinting process interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ An unexpected error occurred while running linter: {e}", file=sys.stderr)
        sys.exit(1)


def run_format(args):
    """Detects the project type and runs the appropriate code formatter."""
    project_dir = args.project_dir.resolve()
    passthrough_args = args.format_args
    is_check_mode = args.check

    print(f"--- Running code formatter in: {project_dir} ---")

    # --- Project Detection ---
    command_base = []
    check_flags = []

    # 1. Python Project
    if (project_dir / "pyproject.toml").exists() or (project_dir / "setup.py").exists():
        print("Detected Python project.")
        if shutil.which("black"):
            command_base = ["black", "."]
            if is_check_mode:
                check_flags = ["--check"]
        else:
            print("Warning: Python formatter 'black' not found in PATH.", file=sys.stderr)

    # 2. Node.js Project (assuming Prettier)
    elif (project_dir / "package.json").exists():
        print("Detected Node.js project.")
        # Assumes prettier is installed locally or globally
        prettier_executable = None
        local_prettier = project_dir / "node_modules" / ".bin" / "prettier"
        if local_prettier.exists():
            prettier_executable = str(local_prettier)
        elif shutil.which("prettier"):
            prettier_executable = "prettier"
        elif shutil.which("npx"):
            prettier_executable = "npx prettier"


        if prettier_executable:
            command_base = [prettier_executable, "."]
            if is_check_mode:
                check_flags = ["--check"]
            else:
                check_flags = ["--write"] # Prettier's equivalent of formatting
        else:
            print("Warning: Node.js formatter 'prettier' not found.", file=sys.stderr)


    # --- Command Construction & Execution ---
    if not command_base:
        print("❌ Error: Could not detect a recognizable project type or find a suitable formatter.", file=sys.stderr)
        sys.exit(1)

    # Construct the full command
    full_command = command_base + check_flags + passthrough_args

    print(f"Executing command: {' '.join(full_command)}")
    try:
        # Stream the output directly and run in the target project directory
        result = subprocess.run(full_command, cwd=project_dir)
        sys.exit(result.returncode)

    except FileNotFoundError:
        print(f"❌ Error: Command '{full_command[0]}' not found. Is it installed and in your PATH?", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nFormatting process interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ An unexpected error occurred while running formatter: {e}", file=sys.stderr)
        sys.exit(1)


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


def run_config(args):
    """Manages agent configuration settings."""
    config_dir = Path(platformdirs.user_config_dir("combined-autonomous-coding"))
    config_path = config_dir / "agent_config.yaml"
    config_dir.mkdir(parents=True, exist_ok=True)

    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        else:
            config_data = {}
    except (IOError, yaml.YAMLError) as e:
        print(f"❌ Error reading configuration file: {e}", file=sys.stderr)
        return 1

    action = args.action
    key = args.key
    value = args.value

    if action == "list":
        print("--- Current Agent Configuration ---")
        if not config_data:
            print("Configuration is empty.")
        else:
            print(yaml.dump(config_data, indent=2, sort_keys=True))

    elif action == "get":
        if not key:
            print("❌ Error: 'get' action requires a key.", file=sys.stderr)
            return 1

        # Handle nested keys if necessary, e.g., 'jira.url'
        keys = key.split('.')
        current_level = config_data
        for k in keys:
            if isinstance(current_level, dict) and k in current_level:
                current_level = current_level[k]
            else:
                print(f"Key '{key}' not found in configuration.", file=sys.stderr)
                return 1

        print(current_level)

    elif action == "set":
        if not key or value is None:
            print("❌ Error: 'set' action requires a key and a value.", file=sys.stderr)
            return 1

        # Handle nested keys
        keys = key.split('.')
        current_level = config_data
        for i, k in enumerate(keys[:-1]):
            if k not in current_level or not isinstance(current_level.get(k), dict):
                current_level[k] = {}
            current_level = current_level[k]

        # Attempt to parse value as a number or boolean
        if value.lower() == 'true':
            parsed_value = True
        elif value.lower() == 'false':
            parsed_value = False
        else:
            try:
                # Try parsing as integer, then float
                parsed_value = int(value)
            except ValueError:
                try:
                    parsed_value = float(value)
                except ValueError:
                    parsed_value = value # Keep as string

        current_level[keys[-1]] = parsed_value

        try:
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, indent=2, sort_keys=True)
            os.chmod(config_path, 0o600)
            print(f"✅ Set '{key}' to '{parsed_value}'.")
        except (IOError, yaml.YAMLError) as e:
            print(f"❌ Error writing configuration file: {e}", file=sys.stderr)
            return 1

    return 0


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

    # Subparser for 'config'
    parser_config = subparsers.add_parser("config", help="Manage agent configuration settings")
    parser_config.add_argument("action", choices=["get", "set", "list"], help="Action to perform")
    parser_config.add_argument("key", nargs="?", help="The configuration key to get or set (e.g., 'model', 'jira.url')")
    parser_config.add_argument("value", nargs="?", help="The value to set for the specified key")

    parser_validate = subparsers.add_parser("validate", help="Validate the agent_config.yaml file")
    parser_list_agents = subparsers.add_parser("list-agents", help="List available agents")
    parser_show_config = subparsers.add_parser("show-config", help="Show the final resolved configuration and exit")

    # Subparser for 'models'
    parser_models = subparsers.add_parser("models", help="List recommended models for each agent")
    parser_models.add_argument(
        "-a", "--agent",
        choices=list(RECOMMENDED_MODELS.keys()),
        help="Filter models for a specific agent.",
    )

    # Subparser for 'doctor'
    parser_doctor = subparsers.add_parser("doctor", help="Run a comprehensive health check on the environment")
    parser_doctor.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check (default: current directory)",
    )

    # Subparser for 'init'
    parser_init = subparsers.add_parser("init", help="Run an interactive setup wizard for a new project")
    parser_init.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to initialize (default: current directory)",
    )
    parser_init.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip all confirmation prompts",
    )

    # Subparser for 'status'
    # Subparser for 'glance'
    parser_glance = subparsers.add_parser("glance", help="Show a compact, high-level overview of the project status")
    parser_glance.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check status for (default: current directory)",
    )

    # Subparser for 'status'
    parser_status = subparsers.add_parser("status", help="Show the current status of the agent project")
    parser_status.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check status for (default: current directory)",
    )

    # Subparser for 'dashboard'
    parser_dashboard = subparsers.add_parser("dashboard", help="Show a comprehensive dashboard of the project status")
    parser_dashboard.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to display the dashboard for (default: current directory)",
    )

    # Subparser for 'summary'
    parser_summary = subparsers.add_parser("summary", help="Show a high-level summary of the agent project")
    parser_summary.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to summarize (default: current directory)",
    )

    # Subparser for 'suggest'
    parser_suggest = subparsers.add_parser("suggest", help="Suggest next logical commands based on project state")
    parser_suggest.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to analyze (default: current directory)",
    )

    # Subparser for 'history'
    parser_history = subparsers.add_parser("history", help="Show the history of agent runs for the project")
    parser_history.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check history for (default: current directory)",
    )

    # Subparser for 'last'
    parser_last = subparsers.add_parser("last", help="Show a summary of the last agent run.")
    parser_last.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check (default: current directory)",
    )

    # Subparser for 'last-run-id'
    parser_last_run_id = subparsers.add_parser("last-run-id", help="Print the ID of the last agent run to stdout.")
    parser_last_run_id.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check (default: current directory)",
    )

    # Subparser for 'diff-summary'
    parser_diff_summary = subparsers.add_parser("diff-summary", help="Show a summary of uncommitted git changes")
    parser_diff_summary.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to check for changes (default: current directory)",
    )

    # Subparser for 'diff' (git diff)
    parser_diff = subparsers.add_parser("diff", help="Show a detailed diff of uncommitted changes or a specific commit")
    parser_diff.add_argument(
        "target",
        nargs="?",
        help="Optional: A git commit hash or agent Run ID to diff against.",
    )
    parser_diff.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to show the diff for (default: current directory)",
    )

    # Subparser for 'log' (git log)
    parser_log = subparsers.add_parser("log", help="Show the git commit history for the project")
    parser_log.add_argument(
        "-n", "--count",
        type=int,
        help="Number of recent commits to display.",
    )
    parser_log.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to show the log for (default: current directory)",
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

    # Subparser for 'discard'
    parser_discard = subparsers.add_parser("discard", help="Discard uncommitted changes to specified files or all files")
    parser_discard.add_argument(
        "files",
        nargs="*",
        help="Specific file(s) to discard. If not provided, all uncommitted changes will be discarded.",
    )
    parser_discard.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to discard changes in (default: current directory)",
    )
    parser_discard.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactively select which files to discard.",
    )
    parser_discard.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )
    # Subparser for 'undo'
    parser_undo = subparsers.add_parser("undo", help="Undo a 'discard' operation by restoring the stashed changes.")
    parser_undo.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to run undo in (default: current directory)",
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


    # Subparser for 'rewind'
    parser_rewind = subparsers.add_parser("rewind", help="Reset the project to a previous state (git commit)")
    parser_rewind.add_argument(
        "target",
        nargs="?",
        help="The git commit hash, reference (e.g., HEAD~2), or Run ID to rewind to. Launches interactive mode if omitted.",
    )
    parser_rewind.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to rewind (default: current directory)",
    )
    parser_rewind.add_argument(
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

    # Subparser for 'tree'
    parser_tree = subparsers.add_parser("tree", help="Show a tree view of the project directory")
    parser_tree.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to display (default: current directory)",
    )
    parser_tree.add_argument(
        "--depth",
        type=int,
        help="Limit the depth of the directory traversal.",
    )
    parser_tree.add_argument(
        "--full",
        action="store_true",
        help="Show all files, including those ignored by Git.",
    )

    # --- New 'completion' command ---
    parser_completion = subparsers.add_parser(
        "completion",
        help="Display shell completion scripts. To install, use: 'eval \"$(main.py completion)\"'",
    )

    # --- New 'cost' command ---
    parser_cost = subparsers.add_parser(
        "cost",
        help="Estimate the cost of an agent run based on token usage."
    )
    parser_cost.add_argument(
        "run_id",
        nargs="?",
        help="The Run ID to estimate. If omitted, uses the latest run.",
    )
    parser_cost.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
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

    # --- New 'branch' command ---
    parser_branch = subparsers.add_parser(
        "branch",
        help="Manage a dedicated feature branch for the agent to work on."
    )
    parser_branch.add_argument(
        "action",
        choices=["create", "checkout", "status", "merge", "list"],
        help="Action to perform.",
    )
    parser_branch.add_argument(
        "branch_name",
        nargs="?",
        help="The name of the branch to create or checkout.",
    )
    parser_branch.add_argument(
        "--keep-branch",
        action="store_true",
        help="Do not delete the branch after a successful merge.",
    )
    parser_branch.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'mutate' command ---
    parser_mutate = subparsers.add_parser(
        "mutate",
        help="Run mutation testing to evaluate test suite quality."
    )
    parser_mutate.add_argument(
        "target_file",
        help="The file to mutate."
    )
    parser_mutate.add_argument(
        "--test-command",
        help="Custom test command (e.g. 'pytest tests/'). If omitted, auto-detected."
    )
    parser_mutate.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'history-graph' command ---
    parser_history_graph = subparsers.add_parser(
        "history-graph",
        help="Visualize agent history as a graph."
    )
    parser_history_graph.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_history_graph.add_argument(
        "-m", "--metric",
        choices=["tokens", "duration", "errors", "iterations"],
        default="tokens",
        help="The metric to visualize (default: tokens)."
    )
    parser_history_graph.add_argument(
        "-l", "--limit",
        type=int,
        default=10,
        help="Number of recent runs to show (default: 10)."
    )

    # --- New 'test' command ---
    parser_test = subparsers.add_parser(
        "test",
        help="Automatically detect and run tests for the project."
    )
    # --- New 'report' command ---
    parser_report = subparsers.add_parser(
        "report",
        help="Generate a summary report for a specific agent run."
    )
    parser_report.add_argument(
        "run_id",
        help="The Run ID to generate the report for.",
    )
    parser_report.add_argument(
        "-o", "--output",
        type=Path,
        help="Path to save the Markdown report file. If omitted, prints to console.",
    )
    parser_report.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the run occurred.",
    )
    parser_test.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to run tests in (default: current directory).",
    )
    parser_test.add_argument(
        "test_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass through to the underlying test runner (e.g., specific files, flags).",
    )

    # --- New 'lint' command ---
    parser_lint = subparsers.add_parser(
        "lint",
        help="Automatically detect and run linters for the project."
    )
    parser_lint.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to run linters in (default: current directory).",
    )
    parser_lint.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to automatically fix linting issues.",
    )
    parser_lint.add_argument(
        "lint_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass through to the underlying linter (e.g., specific files, flags).",
    )

    # --- New 'format' command ---
    parser_format = subparsers.add_parser(
        "format",
        help="Automatically detect and format code for the project."
    )
    parser_format.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to format (default: current directory).",
    )
    parser_format.add_argument(
        "--check",
        action="store_true",
        help="Run the formatter in check-only mode (dry run).",
    )
    parser_format.add_argument(
        "format_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass through to the underlying formatter (e.g., specific files, flags).",
    )

    # --- New 'hooks' command ---
    parser_hooks = subparsers.add_parser(
        "hooks",
        help="Manage git hooks (pre-commit) for the project."
    )
    hooks_subparsers = parser_hooks.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Hooks 'install' action
    parser_hooks_install = hooks_subparsers.add_parser(
        "install",
        help="Install the agent's pre-commit hook."
    )
    parser_hooks_install.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # Hooks 'uninstall' action
    parser_hooks_uninstall = hooks_subparsers.add_parser(
        "uninstall",
        help="Uninstall the agent's pre-commit hook."
    )
    parser_hooks_uninstall.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # Hooks 'run' action
    parser_hooks_run = hooks_subparsers.add_parser(
        "run",
        help="Manually run the hooks checks."
    )
    parser_hooks_run.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'recipes' command ---
    parser_recipes = subparsers.add_parser(
        "recipes",
        aliases=["macro"],
        help="Manage and run agent recipes (sequences of commands)."
    )
    parser_recipes.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    recipes_subparsers = parser_recipes.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Recipes 'list'
    recipes_subparsers.add_parser("list", help="List available recipes.")

    # Recipes 'show'
    parser_recipes_show = recipes_subparsers.add_parser("show", help="Show steps in a recipe.")
    parser_recipes_show.add_argument("name", help="Name of the recipe.")

    # Recipes 'run'
    parser_recipes_run = recipes_subparsers.add_parser("run", help="Execute a recipe.")
    parser_recipes_run.add_argument("name", help="Name of the recipe.")
    parser_recipes_run.add_argument("--dry-run", action="store_true", help="Print commands without executing.")

    # Recipes 'create'
    parser_recipes_create = recipes_subparsers.add_parser("create", help="Create a new recipe interactively.")
    parser_recipes_create.add_argument("name", nargs="?", help="Name of the recipe.")

    # Recipes 'delete'
    parser_recipes_delete = recipes_subparsers.add_parser("delete", help="Delete a recipe.")
    parser_recipes_delete.add_argument("name", help="Name of the recipe.")

    # --- New 'git' command ---
    parser_git = subparsers.add_parser(
        "git",
        help="Run git commands within a specific task's worktree."
    )
    parser_git.add_argument(
        "-t", "--task",
        required=True,
        help="The task ID corresponding to the worktree."
    )
    parser_git.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory where the worktrees are located.",
    )
    parser_git.add_argument(
        "git_args",
        nargs=argparse.REMAINDER,
        help="The git command and its arguments to run.",
    )

    # --- New 'push' command ---
    parser_push = subparsers.add_parser(
        "push",
        help="Push the current feature branch to the remote repository with safety checks."
    )
    parser_push.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to run the push command in (default: current directory).",
    )

    # --- New 'pull' command ---
    parser_pull = subparsers.add_parser(
        "pull",
        help="Pull the latest changes from the remote repository with safety checks."
    )
    parser_pull.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to run the pull command in (default: current directory).",
    )

    # --- New 'patch' command ---
    parser_patch = subparsers.add_parser(
        "patch",
        help="Apply a patch from a file or stdin."
    )
    parser_patch.add_argument(
        "patch_file",
        nargs="?",
        help="The path to the .patch file. If omitted, reads from stdin."
    )
    parser_patch.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory).",
    )
    parser_patch.add_argument(
        "-R", "--reverse",
        action="store_true",
        help="Apply the patch in reverse (unpatch)."
    )

    # --- New 'issues' command ---
    parser_issues = subparsers.add_parser(
        "issues",
        help="List and manage GitHub issues."
    )
    parser_issues.add_argument(
        "--state",
        choices=["open", "closed", "all"],
        default="open",
        help="Filter issues by state (default: open)."
    )
    parser_issues.add_argument(
        "--assignee",
        help="Filter by assignee (username, 'none', or '*')."
    )
    parser_issues.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Enable interactive mode to select an issue and start working."
    )
    parser_issues.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_issues.add_argument(
        "--profile",
        type=str,
        help="Select a configuration profile from agent_config.yaml.",
    )

    # --- New 'pr' command ---
    parser_pr = subparsers.add_parser(
        "pr",
        help="Manage GitHub pull requests for the project."
    )
    pr_subparsers = parser_pr.add_subparsers(
        dest="action",
        required=True,
        help="Specify pr action"
    )

    # PR 'create' action
    parser_pr_create = pr_subparsers.add_parser(
        "create",
        help="Create a new pull request on GitHub."
    )
    parser_pr_create.add_argument(
        "--title",
        required=True,
        help="The title of the pull request."
    )
    parser_pr_create.add_argument(
        "--body",
        default="",
        help="The body content of the pull request."
    )
    parser_pr_create.add_argument(
        "--base",
        default="main",
        help="The base branch to merge into (default: main)."
    )
    parser_pr_create.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'commit' command ---
    parser_commit = subparsers.add_parser(
        "commit",
        help="Stage all changes and create a git commit with safety checks."
    )
    parser_commit.add_argument(
        "-m", "--message",
        required=False,
        help="The commit message. If not provided, an interactive prompt will be shown."
    )
    parser_commit.add_argument(
        "--run-tests",
        action="store_true",
        help="Run project tests before committing. If tests fail, the commit is aborted."
    )
    parser_commit.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to run the commit command in (default: current directory).",
    )

    # --- New 'feature' command ---
    parser_feature = subparsers.add_parser(
        "feature",
        help="Run a guided workflow for a new feature: branch -> commit -> push -> pr."
    )
    parser_feature.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory for the feature.",
    )

    # --- New 'interact' command ---
    parser_interact = subparsers.add_parser(
        "interact",
        help="Start an interactive session to run common commands."
    )
    parser_interact.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory for the interactive session.",
    )

    # --- New 'profile' command ---
    parser_profile = subparsers.add_parser(
        "profile",
        help="Manage configuration profiles."
    )
    parser_profile.add_argument(
        "action",
        choices=["list", "create", "show", "delete"],
        help="Action to perform on profiles.",
    )
    parser_profile.add_argument(
        "profile_name",
        nargs="?",
        help="The name of the profile to create, show, or delete.",
    )
    parser_profile.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts for 'delete' action.",
    )

    # --- New 'watch' command ---
    parser_watch = subparsers.add_parser(
        "watch",
        help="Watch for file changes and run a command."
    )
    parser_watch.add_argument(
        "watch_command",
        nargs=argparse.REMAINDER,
        help="The command to run when a file changes.",
    )
    parser_watch.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to watch.",
    )

    # --- New 'why' command ---
    parser_why = subparsers.add_parser(
        "why",
        help="Explain what a command does and why you might use it."
    )
    parser_why.add_argument(
        "command_name",
        nargs="?",
        help="The command you want an explanation for.",
    )

    # --- New 'next' command ---
    parser_next = subparsers.add_parser(
        "next",
        help="Suggest and execute the next logical command in the workflow."
    )
    parser_next.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to analyze (default: current directory).",
    )

    # --- New 'optimize' command ---
    parser_optimize = subparsers.add_parser(
        "optimize",
        help="Profile a Python script and suggest AI-driven optimizations."
    )
    parser_optimize.add_argument(
        "script",
        help="The Python script to optimize."
    )
    parser_optimize.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the script."
    )
    parser_optimize.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_optimize.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_optimize.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)."
    )

    # --- New 'prune' command ---
    parser_prune = subparsers.add_parser(
        "prune",
        help="Identify and remove unused code and dependencies."
    )
    parser_prune.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_prune.add_argument(
        "--types",
        type=str,
        help="Comma-separated list of types to prune (deps, files). Default: all."
    )
    parser_prune.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without making changes."
    )
    parser_prune.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt."
    )

    # --- New 'debug' command ---
    parser_debug = subparsers.add_parser(
        "debug",
        help="Execute a command and ask the agent to explain failures."
    )
    parser_debug.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_debug.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_debug.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_debug.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)."
    )
    parser_debug.add_argument(
        "command_to_run",
        nargs=argparse.REMAINDER,
        help="The command to execute and debug.",
    )

    # --- New 'blame' command ---
    parser_blame = subparsers.add_parser(
        "blame",
        help="Show the agent Run ID or author for each line of a file, similar to git blame."
    )
    parser_blame.add_argument(
        "filepath",
        type=Path,
        help="The path to the file to blame.",
    )
    parser_blame.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory).",
    )

    # --- New 'knowledge' command ---
    parser_knowledge = subparsers.add_parser(
        "knowledge",
        help="Manage the agent's knowledge base and questions."
    )
    knowledge_subparsers = parser_knowledge.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Knowledge 'list' action
    parser_knowledge_list = knowledge_subparsers.add_parser("list", help="List knowledge items.")
    parser_knowledge_list.add_argument("--category", help="Filter by category.")
    parser_knowledge_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Knowledge 'add' action
    parser_knowledge_add = knowledge_subparsers.add_parser("add", help="Add a knowledge item.")
    parser_knowledge_add.add_argument("content", help="The knowledge content.")
    parser_knowledge_add.add_argument("--category", default="GENERAL_NOTE", help="Category (default: GENERAL_NOTE).")
    parser_knowledge_add.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Knowledge 'delete' action
    parser_knowledge_delete = knowledge_subparsers.add_parser("delete", help="Delete a knowledge item.")
    parser_knowledge_delete.add_argument("id", type=int, help="The ID of the item to delete.")
    parser_knowledge_delete.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Knowledge 'questions' action
    parser_knowledge_questions = knowledge_subparsers.add_parser("questions", help="List agent questions.")
    parser_knowledge_questions.add_argument("--status", default="pending", choices=["pending", "answered"], help="Filter by status.")
    parser_knowledge_questions.add_argument("-i", "--interactive", action="store_true", help="Interactively answer questions.")
    parser_knowledge_questions.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Knowledge 'answer' action
    parser_knowledge_answer = knowledge_subparsers.add_parser("answer", help="Answer a specific question.")
    parser_knowledge_answer.add_argument("id", type=int, help="The ID of the question.")
    parser_knowledge_answer.add_argument("answer", help="The answer text.")
    parser_knowledge_answer.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Knowledge 'graph' action
    parser_knowledge_graph = knowledge_subparsers.add_parser("graph", help="Visualize knowledge graph.")
    parser_knowledge_graph.add_argument("--format", choices=["html", "mermaid", "json"], default="html", help="Output format (default: html).")
    parser_knowledge_graph.add_argument("-o", "--output", help="Output file path.")
    parser_knowledge_graph.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")


    # --- New 'ask' command ---
    parser_ask = subparsers.add_parser(
        "ask",
        help="Ask a question about the codebase."
    )
    parser_ask.add_argument(
        "query",
        help="The question to ask."
    )
    parser_ask.add_argument(
        "--files",
        nargs="*",
        help="Specific files to include in the context."
    )
    parser_ask.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_ask.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_ask.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_ask.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to analyze (default: current directory)."
    )

    # --- New 'do' command ---
    parser_do = subparsers.add_parser(
        "do",
        help="Translate a natural language instruction to a shell command."
    )
    parser_do.add_argument(
        "instruction",
        help="The natural language instruction (e.g. 'undo last commit')."
    )
    parser_do.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_do.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_do.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Execute the suggested command without confirmation."
    )
    parser_do.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_do.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)."
    )

    # --- New 'code-review' command ---
    parser_code_review = subparsers.add_parser(
        "code-review",
        help="Request an AI code review of specific files or git diffs."
    )
    parser_code_review.add_argument(
        "files",
        nargs="*",
        help="Specific files to review. If omitted, defaults to reviewing uncommitted changes."
    )
    parser_code_review.add_argument(
        "--diff",
        action="store_true",
        help="Include git diff (HEAD) in the review. Implied if no files are provided."
    )
    parser_code_review.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_code_review.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_code_review.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_code_review.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)."
    )

    # --- New 'summarize' command ---
    parser_summarize = subparsers.add_parser(
        "summarize",
        aliases=["explain"],
        help="Summarize git changes using AI."
    )
    parser_summarize.add_argument(
        "target",
        nargs="?",
        help="The git target to summarize (commit hash, range, or omitted for uncommitted changes)."
    )
    parser_summarize.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_summarize.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_summarize.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_summarize.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)."
    )

    # --- New 'context' command ---
    parser_context = subparsers.add_parser(
        "context",
        help="Analyze the file context that the agent will use."
    )
    parser_context.add_argument(
        "action",
        choices=["show", "analyze"],
        help="Action to perform: 'show' a detailed tree view with sizes, or 'analyze' by file type.",
    )
    parser_context.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to analyze (default: current directory).",
    )

    # --- New 'todos' command ---
    parser_todos = subparsers.add_parser(
        "todos",
        help="Scan the codebase for TODO, FIXME, and other task tags."
    )
    parser_todos.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to scan (default: current directory).",
    )
    parser_todos.add_argument(
        "--tags",
        type=str,
        help="Comma-separated list of tags to search for (e.g., 'TODO,FIXME').",
    )
    parser_todos.add_argument(
        "--blame",
        action="store_true",
        help="Use git blame to identify the author and date of each TODO (slower).",
    )
    parser_todos.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format.",
    )

    # --- New 'search' command ---
    parser_search = subparsers.add_parser(
        "search",
        help="Search the codebase for a text pattern."
    )
    parser_search.add_argument(
        "pattern",
        help="The text or regex pattern to search for."
    )
    parser_search.add_argument(
        "--files",
        help="Glob pattern to filter files (e.g., '*.py')."
    )
    parser_search.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Enable case-sensitive search."
    )
    parser_search.add_argument(
        "--regex",
        action="store_true",
        help="Treat pattern as a regular expression."
    )
    parser_search.add_argument(
        "-C", "--context",
        type=int,
        default=0,
        help="Number of context lines to show."
    )
    parser_search.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to search (default: current directory)."
    )

    # --- New 'smart-search' command ---
    parser_smart_search = subparsers.add_parser(
        "smart-search",
        aliases=["ssearch"],
        help="Search the codebase using relevance ranking (BM25)."
    )
    parser_smart_search.add_argument(
        "query",
        help="The search query (keywords)."
    )
    parser_smart_search.add_argument(
        "--files",
        help="Glob pattern to filter files (e.g., '*.py')."
    )
    parser_smart_search.add_argument(
        "-l", "--limit",
        type=int,
        default=10,
        help="Number of results to show (default: 10)."
    )
    parser_smart_search.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # --- New 'replace' command ---
    parser_replace = subparsers.add_parser(
        "replace",
        help="Find and replace text in the codebase."
    )
    parser_replace.add_argument(
        "pattern",
        help="The text or regex pattern to search for."
    )
    parser_replace.add_argument(
        "replacement",
        help="The text to replace matches with."
    )
    parser_replace.add_argument(
        "--files",
        help="Glob pattern to filter files (e.g., '*.py')."
    )
    parser_replace.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Enable case-sensitive match."
    )
    parser_replace.add_argument(
        "--regex",
        action="store_true",
        help="Treat pattern as a regular expression."
    )
    parser_replace.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without applying them."
    )
    parser_replace.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory)."
    )

    # --- New 'stash' command ---
    parser_stash = subparsers.add_parser(
        "stash",
        help="Stash away uncommitted changes for later use."
    )
    parser_stash.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory).",
    )
    stash_subparsers = parser_stash.add_subparsers(
        dest="action",
        required=True,
        help="Specify stash action"
    )
    # Stash 'push' action
    parser_stash_push = stash_subparsers.add_parser("push", help="Stash all uncommitted changes (including untracked).")
    parser_stash_push.add_argument("-m", "--message", help="Optional descriptive message for the stash.")
    # Stash 'list' action
    parser_stash_list = stash_subparsers.add_parser("list", help="List all stashes in the repository.")
    # Stash 'pop' action
    parser_stash_pop = stash_subparsers.add_parser("pop", help="Interactively select a stash to apply and remove.")
    # Stash 'drop' action
    parser_stash_drop = stash_subparsers.add_parser("drop", help="Interactively select a stash to delete.")
    parser_stash_drop.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )

    # --- New 'onboard' command ---
    parser_onboard = subparsers.add_parser(
        "onboard",
        help="Run an interactive onboarding wizard for new developers."
    )
    parser_onboard.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'session' command ---
    parser_session = subparsers.add_parser(
        "session",
        help="Manage work sessions (context, files, notes)."
    )
    session_subparsers = parser_session.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Session 'new'
    parser_sess_new = session_subparsers.add_parser("new", help="Create a new session.")
    parser_sess_new.add_argument("name", help="Name of the session.")
    parser_sess_new.add_argument("-d", "--description", help="Optional description.")
    parser_sess_new.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'load'
    parser_sess_load = session_subparsers.add_parser("load", help="Load (activate) a session.")
    parser_sess_load.add_argument("name", help="Name of the session.")
    parser_sess_load.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'list'
    parser_sess_list = session_subparsers.add_parser("list", help="List all sessions.")
    parser_sess_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'info'
    parser_sess_info = session_subparsers.add_parser("info", help="Show info for a session.")
    parser_sess_info.add_argument("name", nargs="?", help="Name of the session (defaults to active).")
    parser_sess_info.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'add' (file)
    parser_sess_add = session_subparsers.add_parser("add", help="Add a file to a session.")
    parser_sess_add.add_argument("file", help="Path to the file.")
    parser_sess_add.add_argument("-n", "--name", help="Session name (defaults to active).")
    parser_sess_add.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'remove' (file)
    parser_sess_rem = session_subparsers.add_parser("remove", help="Remove a file from a session.")
    parser_sess_rem.add_argument("file", help="Path to the file.")
    parser_sess_rem.add_argument("-n", "--name", help="Session name (defaults to active).")
    parser_sess_rem.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'note'
    parser_sess_note = session_subparsers.add_parser("note", help="Add a note to a session.")
    parser_sess_note.add_argument("note", help="The note content.")
    parser_sess_note.add_argument("-n", "--name", help="Session name (defaults to active).")
    parser_sess_note.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'stop'
    parser_sess_stop = session_subparsers.add_parser("stop", help="Stop (deactivate) the current session.")
    parser_sess_stop.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Session 'delete'
    parser_sess_del = session_subparsers.add_parser("delete", help="Delete a session.")
    parser_sess_del.add_argument("name", help="Name of the session.")
    parser_sess_del.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # --- New 'secrets' command ---
    parser_secrets = subparsers.add_parser(
        "secrets",
        help="Manage encrypted secrets (API keys, passwords)."
    )
    secrets_subparsers = parser_secrets.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Secrets 'init'
    parser_sec_init = secrets_subparsers.add_parser("init", help="Generate encryption key.")
    parser_sec_init.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_sec_init.add_argument("-f", "--force", action="store_true", help="Overwrite existing key.")

    # Secrets 'set'
    parser_sec_set = secrets_subparsers.add_parser("set", help="Set a secret.")
    parser_sec_set.add_argument("name", help="Secret name.")
    parser_sec_set.add_argument("value", help="Secret value.")
    parser_sec_set.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Secrets 'get'
    parser_sec_get = secrets_subparsers.add_parser("get", help="Get a secret.")
    parser_sec_get.add_argument("name", help="Secret name.")
    parser_sec_get.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Secrets 'list'
    parser_sec_list = secrets_subparsers.add_parser("list", help="List secret names.")
    parser_sec_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Secrets 'delete'
    parser_sec_del = secrets_subparsers.add_parser("delete", help="Delete a secret.")
    parser_sec_del.add_argument("name", help="Secret name.")
    parser_sec_del.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Secrets 'run'
    parser_sec_run = secrets_subparsers.add_parser("run", help="Run a command with secrets in environment.")
    parser_sec_run.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")
    parser_sec_run.add_argument("command_args", nargs=argparse.REMAINDER, help="The command to run (use -- before command).")

    # --- New 'playground' command ---
    parser_playground = subparsers.add_parser(
        "playground",
        help="Manage a safe scratchpad for code experiments."
    )
    playground_subparsers = parser_playground.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Playground 'create'
    parser_pg_create = playground_subparsers.add_parser("create", help="Create a new playground file.")
    parser_pg_create.add_argument("name", nargs="?", default="scratch.py", help="Name of the file (default: scratch.py).")
    parser_pg_create.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Playground 'run'
    parser_pg_run = playground_subparsers.add_parser("run", help="Run a playground file.")
    parser_pg_run.add_argument("name", help="Name of the file to run.")
    parser_pg_run.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Playground 'list'
    parser_pg_list = playground_subparsers.add_parser("list", help="List playground files.")
    parser_pg_list.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Playground 'delete'
    parser_pg_delete = playground_subparsers.add_parser("delete", help="Delete a playground file.")
    parser_pg_delete.add_argument("name", help="Name of the file to delete.")
    parser_pg_delete.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # --- New 'help' command ---
    parser_help = subparsers.add_parser("help", help="Show a structured and user-friendly help message.")

    # --- New 'cherry-pick' command ---
    parser_cherry_pick = subparsers.add_parser(
        "cherry-pick",
        help="Apply the changes from a specific commit or Run ID onto the current branch."
    )
    parser_cherry_pick.add_argument(
        "target",
        help="The git commit hash or agent Run ID to apply.",
    )
    parser_cherry_pick.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory).",
    )

    # --- New 'rollback' command ---
    parser_rollback = subparsers.add_parser(
        "rollback",
        help="Revert all commits associated with a specific agent Run ID."
    )
    parser_rollback.add_argument(
        "run_id",
        nargs="?",
        default="last",
        help="The agent Run ID to rollback (default: last run).",
    )
    parser_rollback.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory (default: current directory).",
    )
    parser_rollback.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )

    # --- New 'analytics' command ---
    parser_analytics = subparsers.add_parser(
        "analytics",
        help="Display project analytics (git stats, code stats)."
    )
    analytics_subparsers = parser_analytics.add_subparsers(
        dest="type",
        required=True,
        help="Type of analytics to run"
    )

    # Analytics 'git' action
    parser_analytics_git = analytics_subparsers.add_parser(
        "git",
        help="Show Git analytics (contributors, hotspots, activity)."
    )
    parser_analytics_git.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # Analytics 'code' action
    parser_analytics_code = analytics_subparsers.add_parser(
        "code",
        help="Show code file statistics (count, size, type)."
    )
    parser_analytics_code.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # Analytics 'complexity' action
    parser_analytics_complexity = analytics_subparsers.add_parser(
        "complexity",
        help="Show code complexity analysis (cyclomatic complexity)."
    )
    parser_analytics_complexity.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'deps' command ---
    parser_deps = subparsers.add_parser(
        "deps",
        help="Visualize project dependencies (Tree, Mermaid, JSON)."
    )
    parser_deps.add_argument(
        "--format",
        choices=["tree", "mermaid", "json"],
        default="tree",
        help="Output format (default: tree)."
    )
    parser_deps.add_argument(
        "--check",
        action="store_true",
        help="Check online registries for updates.",
    )
    parser_deps.add_argument(
        "--update",
        action="store_true",
        help="Interactively check and update dependencies.",
    )
    parser_deps.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'duplication' command ---
    parser_duplication = subparsers.add_parser(
        "duplication",
        help="Scan for code duplication (Copy-Paste Detector)."
    )
    parser_duplication.add_argument(
        "--min-tokens",
        type=int,
        default=50,
        help="Minimum number of tokens to consider a duplicate (default: 50)."
    )
    parser_duplication.add_argument(
        "--files",
        type=str,
        help="Comma-separated glob patterns to include (e.g. '*.py')."
    )
    parser_duplication.add_argument(
        "--ignore",
        type=str,
        help="Comma-separated glob patterns to ignore."
    )
    parser_duplication.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to scan."
    )

    # --- New 'unused' command ---
    parser_unused = subparsers.add_parser(
        "unused",
        help="Scan for potentially unused code (dead code)."
    )
    parser_unused.add_argument(
        "--files",
        type=str,
        help="Glob pattern to include (e.g. '*.py')."
    )
    parser_unused.add_argument(
        "--ignore",
        type=str,
        help="Comma-separated patterns to ignore."
    )
    parser_unused.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to scan."
    )

    # --- New 'risk' command ---
    parser_risk = subparsers.add_parser(
        "risk",
        help="Identify high-risk files based on complexity and churn (Hotspots)."
    )
    parser_risk.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to analyze."
    )
    parser_risk.add_argument(
        "-l", "--limit",
        type=int,
        default=20,
        help="Number of files to show (default: 20)."
    )

    # --- New 'impact' command ---
    parser_impact = subparsers.add_parser(
        "impact",
        help="Predictively analyze the impact of changes (dependency graph)."
    )
    parser_impact.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to analyze."
    )
    parser_impact.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format."
    )

    # --- New 'a11y' command ---
    parser_a11y = subparsers.add_parser(
        "a11y",
        help="Scan for accessibility issues (HTML, JSX, Vue)."
    )
    parser_a11y.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to scan."
    )
    parser_a11y.add_argument(
        "--files",
        type=str,
        help="Glob pattern to include (e.g. '*.html')."
    )
    parser_a11y.add_argument(
        "--ignore",
        type=str,
        help="Comma-separated patterns to ignore."
    )
    parser_a11y.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)."
    )

    # --- New 'license' command ---
    parser_license = subparsers.add_parser(
        "license",
        help="Check dependency license compliance."
    )
    parser_license.add_argument(
        "action",
        choices=["check", "list"],
        help="Action to perform."
    )
    parser_license.add_argument(
        "--allow",
        type=str,
        help="Comma-separated list of allowed licenses (e.g., 'MIT,Apache-2.0')."
    )
    parser_license.add_argument(
        "--deny",
        type=str,
        help="Comma-separated list of denied licenses (e.g., 'GPL-3.0')."
    )
    parser_license.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'bisect' command ---
    parser_bisect = subparsers.add_parser(
        "bisect",
        help="Automate regression finding with git bisect and AI analysis."
    )
    bisect_subparsers = parser_bisect.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Bisect 'run' action
    parser_bisect_run = bisect_subparsers.add_parser(
        "run",
        help="Run an automated git bisect session."
    )
    parser_bisect_run.add_argument(
        "--good",
        required=True,
        help="A known good commit hash or reference."
    )
    parser_bisect_run.add_argument(
        "--bad",
        required=True,
        help="A known bad commit hash or reference."
    )
    parser_bisect_run.add_argument(
        "--test-command",
        required=True,
        dest="test_command",
        help="The shell command to run for testing (exit 0 for good, non-zero for bad)."
    )
    parser_bisect_run.add_argument(
        "--no-analysis",
        action="store_true",
        help="Skip the AI analysis of the bad commit."
    )
    # Common agent args
    parser_bisect_run.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use for analysis (default: gemini)."
    )
    parser_bisect_run.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_bisect_run.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_bisect_run.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # Bisect 'analyze' action
    parser_bisect_analyze = bisect_subparsers.add_parser(
        "analyze",
        help="Analyze a specific commit for a bug."
    )
    parser_bisect_analyze.add_argument(
        "commit",
        help="The commit hash to analyze."
    )
    parser_bisect_analyze.add_argument(
        "--bug-description",
        help="Description of the bug or failure."
    )
    parser_bisect_analyze.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_bisect_analyze.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_bisect_analyze.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser_bisect_analyze.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # --- New 'map' command ---
    parser_map = subparsers.add_parser(
        "map",
        help="Visualize the project's internal structure (files, classes, functions)."
    )
    parser_map.add_argument(
        "--format",
        choices=["mermaid", "json", "text"],
        default="mermaid",
        help="Output format (default: mermaid)."
    )
    parser_map.add_argument(
        "--focus",
        type=str,
        help="Focus on a specific file or module pattern."
    )
    parser_map.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )

    # --- New 'architecture' command ---
    parser_arch = subparsers.add_parser(
        "architecture",
        aliases=["arch"],
        help="Validate project architecture against rules."
    )
    parser_arch.add_argument(
        "--rules",
        type=str,
        help="Path to a YAML file containing architecture rules."
    )
    parser_arch.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )

    # --- New 'release' command ---
    parser_release = subparsers.add_parser(
        "release",
        help="Manage releases (version bump, changelog, tagging)."
    )
    parser_release.add_argument(
        "action",
        choices=["plan", "apply"],
        default="plan",
        nargs="?",
        help="Action to perform (default: plan)."
    )
    parser_release.add_argument(
        "--force-version",
        type=str,
        help="Manually specify the next version.",
    )
    parser_release.add_argument(
        "--no-changelog",
        action="store_true",
        help="Do not use the generated changelog for the tag message.",
    )
    parser_release.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the apply action.",
    )
    parser_release.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_release.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation if no bump detected.",
    )

    # --- New 'review' command ---
    parser_review = subparsers.add_parser(
        "review",
        help="Run an interactive QA review of the agent's completed work."
    )
    parser_review.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to review.",
    )

    # --- New 'env' command ---
    parser_env = subparsers.add_parser(
        "env",
        help="Manage environment variables (.env files)."
    )
    env_subparsers = parser_env.add_subparsers(
        dest="action",
        required=True,
        help="Action to perform."
    )

    # Env 'init'
    parser_env_init = env_subparsers.add_parser("init", help="Initialize .env and .env.example.")
    parser_env_init.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Env 'check'
    parser_env_check = env_subparsers.add_parser("check", help="Check sync status between .env and .env.example.")
    parser_env_check.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Env 'sync'
    parser_env_sync = env_subparsers.add_parser("sync", help="Synchronize keys between .env and .env.example.")
    parser_env_sync.add_argument("-i", "--interactive", action="store_true", help="Interactively fill values.")
    parser_env_sync.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # Env 'generate'
    parser_env_generate = env_subparsers.add_parser("generate", help="Generate a secure secret for a key.")
    parser_env_generate.add_argument("key", help="The environment variable key.")
    parser_env_generate.add_argument("-l", "--length", type=int, default=32, help="Length of the secret (default: 32).")
    parser_env_generate.add_argument("-p", "--project-dir", type=Path, default=Path("."), help="Project directory.")

    # --- New 'setup' command ---
    parser_setup = subparsers.add_parser(
        "setup",
        help="Detect the project type and install its dependencies."
    )
    parser_setup.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to set up (default: current directory).",
    )

    # --- New 'dockerize' command ---
    parser_dockerize = subparsers.add_parser(
        "dockerize",
        help="Generate Dockerfile and docker-compose.yml for the project."
    )
    parser_dockerize.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_dockerize.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing files.",
    )
    parser_dockerize.add_argument(
        "--dry-run",
        action="store_true",
        help="Print contents without writing files.",
    )

    # --- New 'cicd' command ---
    parser_cicd = subparsers.add_parser(
        "cicd",
        help="Generate CI/CD pipeline configuration files."
    )
    parser_cicd.add_argument(
        "--platform",
        choices=["github", "gitlab"],
        default="github",
        help="Target CI/CD platform (default: github)."
    )
    parser_cicd.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_cicd.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing files.",
    )
    parser_cicd.add_argument(
        "--dry-run",
        action="store_true",
        help="Print contents without writing files.",
    )

    # --- New 'verify' command ---
    parser_verify = subparsers.add_parser(
        "verify",
        help="Run comprehensive project verification (Lint, Type, Security, Test)."
    )
    parser_verify.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_verify.add_argument(
        "--check",
        type=str,
        help="Comma-separated list of checks to run (lint, type, security, test, all). Default: all.",
    )
    parser_verify.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to auto-fix issues (e.g. format code).",
    )
    parser_verify.add_argument(
        "-o", "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )

    # --- New 'health' command ---
    parser_health = subparsers.add_parser(
        "health",
        help="Calculate the overall health score of the project."
    )
    parser_health.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_health.add_argument(
        "--format",
        choices=["text", "html", "json"],
        default="text",
        help="Output format (default: text)."
    )
    parser_health.add_argument(
        "-o", "--output",
        type=str,
        help="Output file path (optional)."
    )

    # --- New 'security' command ---
    parser_security = subparsers.add_parser(
        "security",
        help="Audit the project for security issues (SAST, secrets, dependencies)."
    )
    parser_security.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory to scan (default: current directory).",
    )
    parser_security.add_argument(
        "--scan-type",
        choices=["all", "sast", "secrets", "deps"],
        default="all",
        help="Type of scan to perform (default: all).",
    )
    parser_security.add_argument(
        "--severity",
        choices=["low", "medium", "high"],
        default="low",
        help="Minimum severity level to report (default: low).",
    )
    parser_security.add_argument(
        "-o", "--output",
        type=str,
        help="Path to save the security report (JSON).",
    )

    # --- New 'docstring' command ---
    parser_docstring = subparsers.add_parser(
        "docstring",
        help="Manage Python docstrings (check and generate)."
    )
    parser_docstring.add_argument(
        "action",
        choices=["check", "generate"],
        help="Action to perform."
    )
    parser_docstring.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_docstring.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use for generation (default: gemini)."
    )
    parser_docstring.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_docstring.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt for 'generate' action."
    )

    # --- New 'refactor' command ---
    parser_refactor = subparsers.add_parser(
        "refactor",
        help="Refactor a file using AI based on a natural language instruction."
    )
    parser_refactor.add_argument(
        "file",
        help="The file to refactor."
    )
    parser_refactor.add_argument(
        "instruction",
        help="The refactoring instruction (e.g., 'Extract the login logic into a separate function')."
    )
    parser_refactor.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_refactor.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_refactor.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_refactor.add_argument(
        "--diff-only",
        action="store_true",
        help="Show the diff but do not apply changes.",
    )
    parser_refactor.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )

    # --- New 'polish' command ---
    parser_polish = subparsers.add_parser(
        "polish",
        help="Proactively find and refactor code quality issues (e.g. complexity)."
    )
    parser_polish.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_polish.add_argument(
        "-t", "--threshold",
        type=int,
        default=10,
        help="Complexity threshold to trigger refactoring (default: 10).",
    )
    parser_polish.add_argument(
        "-l", "--limit",
        type=int,
        default=1,
        help="Maximum number of files to polish in one run (default: 1).",
    )
    parser_polish.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_polish.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_polish.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts (auto-confirm refactor plan).",
    )

    # --- New 'resolve' command ---
    parser_resolve = subparsers.add_parser(
        "resolve",
        help="Interactively resolve TODO/FIXME comments using AI."
    )
    parser_resolve.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_resolve.add_argument(
        "--no-interactive",
        dest="interactive",
        action="store_false",
        help="Disable interactive selection.",
    )
    parser_resolve.set_defaults(interactive=True)
    parser_resolve.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_resolve.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_resolve.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )

    # --- New 'resolve-conflicts' command ---
    parser_resolve_conflicts = subparsers.add_parser(
        "resolve-conflicts",
        aliases=["fix-conflicts"],
        help="Resolve git merge conflicts using AI."
    )
    parser_resolve_conflicts.add_argument(
        "files",
        nargs="*",
        help="Specific files to resolve."
    )
    parser_resolve_conflicts.add_argument(
        "--all",
        action="store_true",
        help="Scan and resolve all files with conflicts."
    )
    parser_resolve_conflicts.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory.",
    )
    parser_resolve_conflicts.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_resolve_conflicts.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )
    parser_resolve_conflicts.add_argument(
        "--diff",
        action="store_true",
        help="Show diff before applying.",
    )
    parser_resolve_conflicts.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )
    parser_resolve_conflicts.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )

    # --- New 'generate-tests' command ---
    parser_gentest = subparsers.add_parser(
        "generate-tests",
        aliases=["gentest"],
        help="Generate unit tests for a specific file."
    )
    parser_gentest.add_argument(
        "file",
        help="The source file to generate tests for."
    )
    parser_gentest.add_argument(
        "-o", "--output",
        help="The output path for the test file (optional)."
    )
    parser_gentest.add_argument(
        "-f", "--framework",
        default="pytest",
        help="The testing framework to use (default: pytest)."
    )
    parser_gentest.add_argument(
        "-p", "--project-dir",
        type=Path,
        default=Path("."),
        help="The project directory."
    )
    parser_gentest.add_argument(
        "-a", "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        default="gemini",
        help="Which agent to use (default: gemini)."
    )
    parser_gentest.add_argument(
        "-m", "--model",
        type=str,
        help="Model to use (overrides default)."
    )

    # --- New 'mock' command ---
    parser_mock = subparsers.add_parser(
        "mock",
        help="Generate realistic mock data from a JSON spec."
    )
    parser_mock.add_argument(
        "--spec",
        type=Path,
        required=True,
        help="Path to the JSON specification file."
    )
    parser_mock.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of records to generate (default: 10)."
    )
    parser_mock.add_argument(
        "--format",
        choices=["json", "csv", "sql"],
        default="json",
        help="Output format (default: json)."
    )
    parser_mock.add_argument(
        "--output",
        type=Path,
        help="Output file path."
    )
    parser_mock.add_argument(
        "--table",
        default="table",
        help="Table name for SQL output."
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    return parser.parse_args(argv)


def run_profile(args):
    """Manages configuration profiles."""
    config_dir = Path(platformdirs.user_config_dir("combined-autonomous-coding"))
    config_path = config_dir / "agent_config.yaml"
    config_dir.mkdir(parents=True, exist_ok=True)

    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        else:
            config_data = {}
    except (IOError, yaml.YAMLError) as e:
        print(f"❌ Error reading configuration file: {e}", file=sys.stderr)
        sys.exit(1)

    # Ensure the 'profiles' key exists
    if 'profiles' not in config_data or not isinstance(config_data.get('profiles'), dict):
        config_data['profiles'] = {}

    action = args.action
    profile_name = args.profile_name

    # --- LIST action ---
    if action == "list":
        print("--- Available Profiles ---")
        profiles = config_data.get('profiles', {})
        if not profiles:
            print("No profiles found.")
        else:
            for name in profiles.keys():
                print(f"  - {name}")
        sys.exit(0)

    # --- SHOW action ---
    elif action == "show":
        if not profile_name:
            print("❌ Error: 'show' action requires a profile name.", file=sys.stderr)
            sys.exit(1)

        profile_data = config_data.get('profiles', {}).get(profile_name)
        if not profile_data:
            print(f"❌ Error: Profile '{profile_name}' not found.", file=sys.stderr)
            sys.exit(1)

        print(f"--- Configuration for Profile: {profile_name} ---")
        print(yaml.dump(profile_data, indent=2, sort_keys=True))
        sys.exit(0)

    # --- DELETE action ---
    elif action == "delete":
        if not profile_name:
            print("❌ Error: 'delete' action requires a profile name.", file=sys.stderr)
            sys.exit(1)

        if profile_name not in config_data.get('profiles', {}):
            print(f"❌ Error: Profile '{profile_name}' not found.", file=sys.stderr)
            sys.exit(1)

        if not args.yes:
            confirm = input(f"Are you sure you want to delete the profile '{profile_name}'? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        del config_data['profiles'][profile_name]

        try:
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, indent=2, sort_keys=True)
            os.chmod(config_path, 0o600)
            print(f"✅ Profile '{profile_name}' deleted successfully.")
        except (IOError, yaml.YAMLError) as e:
            print(f"❌ Error writing configuration file: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # --- CREATE action ---
    elif action == "create":
        if not profile_name:
            print("❌ Error: 'create' action requires a profile name.", file=sys.stderr)
            sys.exit(1)

        if profile_name in config_data.get('profiles', {}):
            print(f"❌ Error: Profile '{profile_name}' already exists.", file=sys.stderr)
            sys.exit(1)

        print(f"--- Creating New Profile: {profile_name} ---")
        print("Please provide the settings for this profile. Press Enter to skip a setting.")

        # Re-use the interactive input logic from run_configure
        def get_input(prompt, default_value=None):
            if default_value:
                prompt_text = f"{prompt} [{default_value}]: "
            else:
                prompt_text = f"{prompt}: "
            user_input = input(prompt_text).strip()
            return user_input or default_value

        new_profile_data = {}

        # Core settings
        new_profile_data['model'] = get_input("Model name (e.g., gemini-1.5-pro-latest)")
        new_profile_data['agent'] = get_input("Default agent (gemini, cursor, etc.)")

        # Jira
        print("\n--- Jira Integration (optional) ---")
        jira_url = get_input("Jira URL")
        if jira_url:
            new_profile_data['jira'] = {
                'url': jira_url,
                'email': get_input("Jira Email"),
                'token': get_input("Jira API Token"),
            }

        # Clean up empty values
        new_profile_data = {k: v for k, v in new_profile_data.items() if v}

        config_data['profiles'][profile_name] = new_profile_data

        try:
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, indent=2, sort_keys=True)
            os.chmod(config_path, 0o600)
            print(f"\n✅ Profile '{profile_name}' created successfully.")
        except (IOError, yaml.YAMLError) as e:
            print(f"\n❌ Error writing configuration file: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)


def run_watch(args):
    """Watches for file changes and runs a command."""
    project_dir = args.project_dir.resolve()
    command_to_run = args.watch_command

    if Observer is None:
        print("Error: watchdog library not found. Please install it with 'pip install watchdog'", file=sys.stderr)
        sys.exit(1)

    print(f"--- Watching for file changes in: {project_dir} ---")
    print(f"--- Press Ctrl+C to stop ---")

    event_handler = CommandEventHandler(command_to_run, project_dir)
    observer = Observer()
    observer.schedule(event_handler, project_dir, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    sys.exit(0)


def run_feature(args):
    """Runs a guided workflow for creating a feature branch, committing, pushing, and creating a PR."""
    project_dir = args.project_dir.resolve()
    print("--- Guided Feature Workflow ---")
    print("This will walk you through: branch -> commit -> push -> pr.")

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path or not (project_dir / ".git").is_dir():
        print("❌ Error: Not a git repository. Cannot start feature workflow.", file=sys.stderr)
        sys.exit(1)

    try:
        # --- Step 1: Create Branch ---
        print("\n--- [1/4] Create Branch ---")
        branch_name = input("Enter the new branch name: ").strip()
        if not branch_name:
            print("Branch name cannot be empty. Aborting.")
            sys.exit(1)

        branch_args = argparse.Namespace(
            action="create",
            branch_name=branch_name,
            project_dir=project_dir,
            keep_branch=False # Not used in create
        )
        try:
            run_branch(branch_args)
        except SystemExit as e:
            if e.code != 0:
                print("❌ Branch creation failed. Aborting workflow.", file=sys.stderr)
                sys.exit(1)

        # --- Step 2: Commit ---
        print("\n--- [2/4] Commit Changes ---")
        print("This will stage and commit all current changes.")
        commit_message = input("Enter the commit message: ").strip()
        if not commit_message:
            print("Commit message cannot be empty. Aborting.")
            sys.exit(1)

        commit_args = argparse.Namespace(
            message=commit_message,
            run_tests=False, # For simplicity, don't run tests in this guided flow
            project_dir=project_dir
        )
        try:
            run_commit(commit_args)
        except SystemExit as e:
            if e.code != 0:
                print("❌ Commit failed. Aborting workflow.", file=sys.stderr)
                # We should checkout the original branch or offer to. For now, we just exit.
                sys.exit(1)

        # --- Step 3: Push ---
        print("\n--- [3/4] Push to Remote ---")
        confirm_push = input(f"Push the branch '{branch_name}' to the remote repository? [Y/n]: ").strip().lower()
        if confirm_push not in ['y', '']:
            print("Push skipped. Aborting workflow.")
            sys.exit(0)

        push_args = argparse.Namespace(project_dir=project_dir)
        try:
            run_push(push_args)
        except SystemExit as e:
            if e.code != 0:
                print("❌ Push failed. Aborting workflow.", file=sys.stderr)
                sys.exit(1)

        # --- Step 4: Create Pull Request ---
        print("\n--- [4/4] Create Pull Request ---")
        confirm_pr = input("Create a pull request on GitHub? [Y/n]: ").strip().lower()
        if confirm_pr not in ['y', '']:
            print("Pull request creation skipped.")
            print("\n✅ Workflow complete up to push.")
            sys.exit(0)

        pr_title = input(f"PR Title [{commit_message}]: ").strip() or commit_message
        pr_body = input("PR Body (optional): ").strip()
        base_branch = input("Base branch [main]: ").strip() or "main"

        pr_args = argparse.Namespace(
            action="create",
            title=pr_title,
            body=pr_body,
            base=base_branch,
            project_dir=project_dir,
            profile=getattr(args, 'profile', None)
        )

        # We need to call _pr_create directly to avoid its sys.exit() and to pass config
        file_config = load_config_from_file(profile=getattr(args, 'profile', None))
        config = argparse.Namespace(
            github_token=os.environ.get("GITHUB_TOKEN") or file_config.get("github_token"),
            github_host=file_config.get("github_host")
        )

        try:
            _pr_create(pr_args, config)
        except SystemExit as e:
            if e.code != 0:
                print("❌ Pull request creation failed.", file=sys.stderr)
                sys.exit(1)

        print("\n🎉 Feature workflow completed successfully!")
        sys.exit(0)

    except (KeyboardInterrupt, EOFError):
        print("\n\nWorkflow aborted by user.")
        sys.exit(1)


def run_review(args):
    """Runs an interactive QA review of the agent's work."""
    project_dir = args.project_dir.resolve()
    print("--- Interactive QA Review ---")
    print(f"Project Directory: {project_dir}")

    completed_file = project_dir / "COMPLETED"
    qa_passed_file = project_dir / "QA_PASSED"

    # 1. Check if there is work to review
    if not completed_file.exists():
        print("✅ No agent work is currently marked as 'COMPLETED'. Nothing to review.")
        sys.exit(0)

    if qa_passed_file.exists():
        print("✅ Agent work has already been reviewed and passed QA. Ready for manager sign-off.")
        sys.exit(0)

    print("\n[1/3] Work is marked as COMPLETED. Proceeding with review...")

    # 2. Run tests automatically
    print("\n[2/3] Running project tests...")
    test_args = argparse.Namespace(project_dir=project_dir, test_args=[])
    try:
        # We call the test function but catch SystemExit to check the result
        run_test(test_args)
    except SystemExit as e:
        if e.code != 0:
            print("\n❌ Tests failed. The agent's work is not ready for review.", file=sys.stderr)
            print("Aborting review. The agent will be notified of the test failure on its next run.", file=sys.stderr)
            # The 'COMPLETED' file is left so the agent knows it failed this step.
            sys.exit(1)

    print("✅ Tests passed successfully.")

    # 3. Show diff and ask for user approval
    print("\n[3/3] Displaying changes for review...")

    # Use existing diff logic
    try:
        diff_args = argparse.Namespace(target=None, project_dir=project_dir)
        run_diff(diff_args)
    except SystemExit:
        # run_diff will exit, which is fine. If there are no changes, it prints a message.
        pass
    except Exception as e:
        print(f"Warning: Could not display diff. {e}", file=sys.stderr)


    print("\n--- Decision ---")
    print("Do you approve these changes?")
    try:
        confirm = input("Approve and advance to manager review? [y/N]: ").strip().lower()
        if confirm == 'y':
            print("\n✅ Approved. Creating QA_PASSED file for manager review.")
            qa_passed_file.touch()
            # Optionally write a small summary
            qa_summary = f"Human QA passed at {datetime.now().isoformat()}"
            (project_dir / "qa_summary.txt").write_text(qa_summary)
            print("Workflow advanced. The Manager agent can now perform final sign-off.")
            sys.exit(0)
        else:
            print("\n❌ Rejected. Removing COMPLETED file to signal the agent to continue work.")
            completed_file.unlink()
            print("The agent will now re-evaluate the project on its next run.")
            sys.exit(0)
    except (KeyboardInterrupt, EOFError):
        print("\nReview aborted. No changes made to workflow state.")
        sys.exit(1)


async def run_generate_tests(args):
    """Generates tests for a specific file."""
    from shared.test_generator import TestGenerator

    project_dir = args.project_dir.resolve()
    target_file = Path(args.file).resolve()

    output_file = Path(args.output).resolve() if args.output else None

    generator = TestGenerator(project_dir)
    success = await generator.generate_tests(
        target_file=target_file,
        output_file=output_file,
        framework=args.framework,
        agent_type=args.agent,
        model=args.model
    )
    sys.exit(0 if success else 1)


async def run_refactor(args):
    """Refactors a file based on an instruction."""
    from shared.refactor import RefactorManager

    project_dir = args.project_dir.resolve()
    target_file = Path(args.file)
    if not target_file.is_absolute():
        target_file = project_dir / target_file

    if not target_file.exists():
        print(f"❌ Error: File '{target_file}' not found.", file=sys.stderr)
        sys.exit(1)

    manager = RefactorManager(project_dir)
    print(f"--- Refactoring {target_file.name} ---")
    print(f"Instruction: {args.instruction}")

    try:
        result = await manager.refactor_file(
            target_file=target_file,
            instruction=args.instruction,
            agent_type=args.agent,
            model=args.model
        )
    except Exception as e:
        print(f"❌ Error during refactoring: {e}", file=sys.stderr)
        sys.exit(1)

    if not result["changed"]:
        print("✅ No changes were deemed necessary by the agent.")
        sys.exit(0)

    print("\n--- Proposed Changes ---")
    print(result["diff"])

    if args.diff_only:
        sys.exit(0)

    if not args.yes:
        confirm = input("\nDo you want to apply these changes? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    manager.apply_changes(target_file, result["new_content"])
    print(f"\n✅ Successfully updated {target_file.name}")
    sys.exit(0)


async def run_polish(args):
    """Polishes code by proactively refactoring based on metrics."""
    project_dir = args.project_dir.resolve()

    success = await run_polish_logic(
        project_dir=project_dir,
        agent_type=args.agent,
        model=args.model,
        threshold=args.threshold,
        limit=args.limit,
        yes=args.yes
    )
    sys.exit(0 if success else 1)


async def run_resolve(args):
    """Resolves a TODO item using AI."""
    from shared.resolve import run_resolve_logic

    project_dir = args.project_dir.resolve()

    success = await run_resolve_logic(
        project_dir=project_dir,
        agent_type=args.agent,
        model=args.model,
        interactive=args.interactive,
        yes=args.yes
    )
    sys.exit(0 if success else 1)


async def run_resolve_conflicts(args):
    """Resolves merge conflicts using AI."""
    from shared.conflict_resolver import ConflictResolver

    project_dir = args.project_dir.resolve()
    resolver = ConflictResolver(project_dir)

    # Identify files
    files_to_resolve = []
    if args.files:
        files_to_resolve = [project_dir / f for f in args.files]
    elif args.all:
        print("Scanning for conflicted files...")
        files_to_resolve = resolver.find_conflicted_files()
    else:
        print("Error: Please specify files to resolve or use --all.")
        sys.exit(1)

    if not files_to_resolve:
        print("✅ No conflicted files found.")
        sys.exit(0)

    print(f"Found {len(files_to_resolve)} file(s) with conflicts.")

    for file_path in files_to_resolve:
        print(f"\n--- Resolving: {file_path.name} ---")
        try:
            result = await resolver.resolve_file(
                target_file=file_path,
                agent_type=args.agent,
                model=args.model
            )

            if result["resolved"]:
                print("✅ Resolution successful.")
                if args.diff:
                     import difflib
                     diff = difflib.unified_diff(
                        result["original_content"].splitlines(),
                        result["resolved_content"].splitlines(),
                        fromfile=f"a/{file_path.name}",
                        tofile=f"b/{file_path.name}",
                        lineterm=""
                     )
                     print("\n".join(diff))

                if not args.yes:
                     confirm = input("Apply changes? [y/N]: ").strip().lower()
                     if confirm != 'y':
                         print("Skipped.")
                         continue

                resolver.apply_resolution(file_path, result["resolved_content"])
                print(f"Saved changes to {file_path.name}")
            else:
                print(f"❌ Failed to resolve {file_path.name}: {result.get('message', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()

    sys.exit(0)


async def run_docstring(args):
    """Manages Python docstrings."""
    from shared.docstring import DocstringManager

    project_dir = args.project_dir.resolve()
    manager = DocstringManager(project_dir)

    print(f"--- Docstring Manager in: {project_dir} ---")

    if args.action == "check":
        print("Scanning for missing docstrings...")
        items = manager.scan()
        if not items:
            print("✅ No missing docstrings found.")
            sys.exit(0)

        print(f"Found {len(items)} missing docstrings:")
        # Group by file
        items_by_file = {}
        for item in items:
            p = str(item["file"].relative_to(project_dir))
            if p not in items_by_file:
                items_by_file[p] = []
            items_by_file[p].append(item)

        for p in sorted(items_by_file.keys()):
            print(f"\n📄 {p}")
            for item in items_by_file[p]:
                print(f"  - Line {item['lineno']}: {item['type']} '{item['name']}'")

        print(f"\nTotal: {len(items)} missing.")
        sys.exit(1) # Exit 1 to indicate issues found (like lint)

    elif args.action == "generate":
        print("Scanning for missing docstrings...")
        items = manager.scan()
        if not items:
            print("✅ No missing docstrings found.")
            sys.exit(0)

        print(f"Found {len(items)} items to document.")
        if not args.yes:
            confirm = input("Do you want to generate and apply docstrings for these items? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        print("\nStarting generation (this may take a while)...")
        count = await manager.generate_and_apply(
            items,
            agent_type=args.agent,
            model=args.model
        )
        print(f"\n✅ Successfully generated and applied {count} docstrings.")
        sys.exit(0)


def run_security(args):
    """Runs security checks on the project."""
    project_dir = args.project_dir.resolve()
    print(f"--- Running Security Audit in: {project_dir} ---")
    print(f"Scan Type: {args.scan_type}")
    print(f"Severity Threshold: {args.severity}")

    auditor = SecurityAuditor(project_dir)
    findings = auditor.run_all(scan_type=args.scan_type, severity=args.severity)

    if args.output:
        output_path = Path(args.output)
        try:
            with open(output_path, 'w') as f:
                json.dump(findings, f, indent=2)
            print(f"\n✅ Report saved to {output_path}")
        except IOError as e:
            print(f"\n❌ Error saving report: {e}", file=sys.stderr)

    if not findings:
        print("\n✅ No security issues found.")
        sys.exit(0)

    print(f"\n⚠️  Found {len(findings)} security issue(s):")

    # Sort findings by severity (HIGH > MEDIUM > LOW > UNKNOWN)
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "UNKNOWN": 3}
    findings.sort(key=lambda x: severity_order.get(str(x.get("severity", "UNKNOWN")).upper(), 3))

    for i, finding in enumerate(findings):
        sev = str(finding.get('severity', 'UNKNOWN')).upper()
        ftype = finding.get('type', 'generic').upper()
        desc = finding.get('description', 'No description')
        file_path = finding.get('file', 'N/A')
        line = finding.get('line', 0)

        # Color coding
        sev_color = ""
        if sev == "HIGH":
            sev_color = "\033[91m" # Red
        elif sev == "MEDIUM":
            sev_color = "\033[93m" # Yellow
        elif sev == "LOW":
            sev_color = "\033[94m" # Blue
        reset = "\033[0m"

        print(f"\n[{i+1}] {sev_color}{sev}{reset} [{ftype}] {desc}")
        print(f"    File: {file_path}:{line}")
        if finding.get('snippet'):
            print(f"    Snippet: {finding['snippet'].strip()}")

    # Exit with error if high severity issues found
    if any(str(f.get('severity')).upper() == "HIGH" for f in findings):
        sys.exit(1)

    sys.exit(0)


def run_verify(args):
    """Runs verification checks (lint, type, security, tests)."""
    checks = args.check.split(",") if args.check else None
    success = run_verify_logic(
        project_dir=args.project_dir,
        checks=checks,
        fix=args.fix,
        output_format=args.output
    )
    sys.exit(0 if success else 1)


def run_cicd(args):
    """Generates CI/CD configuration files."""
    from shared.cicd import CICDGenerator

    project_dir = args.project_dir.resolve()
    print(f"--- Generating CI/CD configuration for: {project_dir} ---")

    generator = CICDGenerator(project_dir)
    project_type = generator.detect_project_type()

    if project_type == "unknown":
        print("❌ Error: Could not detect project type (Python, Node, Go).")
        sys.exit(1)

    print(f"Detected project type: {project_type}")
    print(f"Target platform: {args.platform}")

    generated_files = generator.generate(args.platform)

    if args.dry_run:
        print("\n[Dry Run] The following files would be generated:\n")
        for filename, content in generated_files.items():
            print(f"--- {filename} ---")
            print(content)
            print("-" * 20 + "\n")
        sys.exit(0)

    for filename, content in generated_files.items():
        file_path = project_dir / filename
        if file_path.exists() and not args.force:
            print(f"⚠️  Skipping {filename} (already exists). Use --force to overwrite.")
            continue

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            print(f"✅ Generated {filename}")
        except IOError as e:
            print(f"❌ Error writing {filename}: {e}", file=sys.stderr)

    sys.exit(0)


def run_dockerize(args):
    """Generates Docker configuration files for the project."""
    project_dir = args.project_dir.resolve()
    print(f"--- Dockerizing project in: {project_dir} ---")

    dockerizer = Dockerizer(project_dir)
    project_type = dockerizer.detect_project_type()

    if project_type == "unknown":
        print("❌ Error: Could not detect project type (Python, Node, Go).")
        print("   Ensure you have a requirements.txt, package.json, or go.mod file.")
        sys.exit(1)

    print(f"Detected project type: {project_type}")

    # Files to generate
    files_to_generate = {
        "Dockerfile": dockerizer.generate_dockerfile(project_type),
        "docker-compose.yml": dockerizer.generate_docker_compose(project_type),
        ".dockerignore": dockerizer.generate_dockerignore(project_type)
    }

    generated_files = []

    if args.dry_run:
        print("\n[Dry Run] The following files would be generated:\n")
        for filename, content in files_to_generate.items():
            print(f"--- {filename} ---")
            print(content)
            print("-" * 20 + "\n")
        sys.exit(0)

    for filename, content in files_to_generate.items():
        file_path = project_dir / filename
        if file_path.exists() and not args.force:
            print(f"⚠️  Skipping {filename} (already exists). Use --force to overwrite.")
            continue

        try:
            file_path.write_text(content)
            generated_files.append(filename)
            print(f"✅ Generated {filename}")
        except IOError as e:
            print(f"❌ Error writing {filename}: {e}", file=sys.stderr)

    if generated_files:
        print(f"\n🎉 Successfully dockerized! You can now run:")
        print(f"  docker-compose up --build")
    else:
        print("\nNo files were generated (they might already exist).")

    sys.exit(0)


def run_env(args):
    """Manages environment variables."""
    from shared.env_manager import EnvManager

    project_dir = args.project_dir.resolve()
    manager = EnvManager(project_dir)
    print(f"--- Environment Manager in: {project_dir} ---")

    if args.action == "init":
        success, msg = manager.init()
        if success:
            print(f"✅ {msg}")
        else:
            print(f"ℹ️  {msg}")

    elif args.action == "check":
        is_valid, missing_env, missing_example = manager.check()
        if is_valid:
            print("✅ .env and .env.example are in sync.")
        else:
            print("⚠️  Issues found:")
            if missing_env:
                print(f"  Missing in .env: {', '.join(missing_env)}")
            if missing_example:
                print(f"  Missing in .env.example: {', '.join(missing_example)}")
            sys.exit(1)

    elif args.action == "sync":
        print("Syncing .env and .env.example...")
        success, msg = manager.sync(interactive=args.interactive)
        print(f"✅ {msg}")

    elif args.action == "generate":
        secret = manager.generate_secret(args.key, length=args.length)
        print(f"✅ Generated secret for '{args.key}'.")
        print(f"  Value: {secret}")

    sys.exit(0)


def run_setup(args):
    """Detects the project type and installs dependencies."""
    project_dir = args.project_dir.resolve()
    print(f"--- Setting up project in: {project_dir} ---")

    command_base = []

    # 1. Node.js Project (check for lockfiles first)
    if (project_dir / "pnpm-lock.yaml").exists() and shutil.which("pnpm"):
        print("Detected pnpm project.")
        command_base = ["pnpm", "install"]
    elif (project_dir / "yarn.lock").exists() and shutil.which("yarn"):
        print("Detected yarn project.")
        command_base = ["yarn", "install"]
    elif (project_dir / "package-lock.json").exists() and shutil.which("npm"):
        print("Detected npm project.")
        command_base = ["npm", "install"]
    elif (project_dir / "package.json").exists():
        if shutil.which("pnpm"):
            print("Detected Node.js project. Using pnpm.")
            command_base = ["pnpm", "install"]
        elif shutil.which("yarn"):
            print("Detected Node.js project. Using yarn.")
            command_base = ["yarn", "install"]
        elif shutil.which("npm"):
            print("Detected Node.js project. Using npm.")
            command_base = ["npm", "install"]

    # 2. Python Project
    elif (project_dir / "requirements.txt").exists():
        print("Detected Python project.")
        command_base = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        # Also install dev requirements if they exist
        if (project_dir / "requirements-dev.txt").exists():
            print("Found requirements-dev.txt, installing dev dependencies...")
            dev_command = [sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"]
            try:
                # Run this command first
                result = subprocess.run(dev_command, cwd=project_dir)
                if result.returncode != 0:
                     print(f"❌ Error installing dev dependencies. Aborting further setup.", file=sys.stderr)
                     sys.exit(result.returncode)
            except Exception as e:
                print(f"❌ An unexpected error occurred while installing dev dependencies: {e}", file=sys.stderr)
                sys.exit(1)


    # 3. Go Project
    elif (project_dir / "go.mod").exists():
        print("Detected Go project.")
        command_base = ["go", "mod", "tidy"]

    # --- Command Execution ---
    if not command_base:
        print("❌ Error: Could not detect a recognizable project type for setup.", file=sys.stderr)
        print("  Please ensure the project has a `package.json`, `requirements.txt`, or `go.mod` file.", file=sys.stderr)
        sys.exit(1)

    print(f"Executing command: {' '.join(command_base)}")
    try:
        result = subprocess.run(command_base, cwd=project_dir)
        if result.returncode == 0:
            print("✅ Setup complete.")
        else:
            print(f"❌ Setup command failed with exit code {result.returncode}.", file=sys.stderr)
        sys.exit(result.returncode)

    except FileNotFoundError:
        print(f"❌ Error: Command '{command_base[0]}' not found. Is it installed and in your PATH?", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup process interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ An unexpected error occurred during setup: {e}", file=sys.stderr)
        sys.exit(1)


def run_interact(args):
    """Starts an interactive session to guide the user through common commands."""
    project_dir = args.project_dir.resolve()
    print("--- Interactive Session ---")
    print(f"Project Directory: {project_dir}")
    print("Type a number to select a command, or 'q' to quit.")

    # A map of menu items to the function and args they will call
    menu_items = {
        "1": {"text": "Show project status", "func": run_status, "args": {"project_dir": project_dir}},
        "2": {"text": "Run tests", "func": run_test, "args": {"project_dir": project_dir, "test_args": []}},
        "3": {"text": "Run linter", "func": run_lint, "args": {"project_dir": project_dir, "fix": False, "lint_args": []}},
        "4": {"text": "Format code", "func": run_format, "args": {"project_dir": project_dir, "check": False, "format_args": []}},
        "5": {"text": "Commit changes", "func": run_commit}, # Special handling
        "6": {"text": "Suggest next step", "func": run_suggest, "args": {"project_dir": project_dir}},
    }

    while True:
        print("\n--- Main Menu ---")
        for key, value in menu_items.items():
            print(f"  [{key}] {value['text']}")
        print("  [q] Quit")

        try:
            choice = input("> ").strip().lower()
            if choice == 'q':
                print("Exiting interactive session.")
                break

            if choice in menu_items:
                item = menu_items[choice]
                print(f"\n--- Running: {item['text']} ---")
                try:
                    # Special handling for commit as it requires a message
                    if item["func"] == run_commit:
                        message = input("Enter commit message: ").strip()
                        if message:
                            # Construct the args namespace for the command
                            commit_args = argparse.Namespace(
                                message=message,
                                run_tests=False,
                                project_dir=project_dir
                            )
                            run_commit(commit_args)
                        else:
                            print("Commit message cannot be empty. Aborting.")
                    else:
                        # Construct the args namespace for the command
                        command_args = argparse.Namespace(**item["args"])
                        item["func"](command_args)
                except SystemExit as e:
                    if e.code != 0:
                        print(f"--- Command finished with an error (exit code: {e.code}) ---", file=sys.stderr)
                    else:
                        print(f"--- Command finished successfully ---")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}", file=sys.stderr)
            else:
                print("Invalid choice, please try again.")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting interactive session.")
            break
    sys.exit(0)


def run_push(args):
    """Handles the git push command with safety checks."""
    import shutil
    import subprocess

    project_dir = args.project_dir.resolve()
    print(f"--- Pushing feature branch in: {project_dir} ---")

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot push.", file=sys.stderr)
        sys.exit(1)

    try:
        # Check for uncommitted changes
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if status_result.stdout.strip():
            print("❌ Error: You have uncommitted changes. Please commit or stash them before pushing.", file=sys.stderr)
            sys.exit(1)

        # 1. Get the current branch name
        from shared.git import get_current_branch
        branch_name = get_current_branch(project_dir)

        if not branch_name:
            print("❌ Error: Could not determine the current branch name.", file=sys.stderr)
            sys.exit(1)

        print(f"Current branch is '{branch_name}'.")

        # 2. Safety check for restricted branches
        restricted_branches = ["main", "master"]
        if branch_name.lower() in restricted_branches:
            print(f"❌ Error: Pushing directly to the protected branch '{branch_name}' is not allowed.", file=sys.stderr)
            print("Please create a feature branch to push your changes.", file=sys.stderr)
            sys.exit(1)

        # 3. Execute the push command
        print(f"Pushing branch '{branch_name}' to remote 'origin'...")
        push_cmd = [git_path, "-C", str(project_dir), "push", "-u", "origin", branch_name]

        # We stream the output directly to the user's console
        push_result = subprocess.run(push_cmd, text=True)

        if push_result.returncode == 0:
            print("\n✅ Push successful.")
            sys.exit(0)
        else:
            print(f"\n❌ Git push command failed with exit code {push_result.returncode}.", file=sys.stderr)
            # Git's own error messages will be printed to stderr by subprocess.run
            sys.exit(push_result.returncode)

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else str(e)
        print(f"❌ An error occurred: {stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def run_pull(args):
    """Handles the git pull command with safety checks."""
    import shutil
    import subprocess

    project_dir = args.project_dir.resolve()
    print(f"--- Pulling latest changes in: {project_dir} ---")

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot pull.", file=sys.stderr)
        sys.exit(1)

    try:
        # Check for uncommitted changes
        status_result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if status_result.stdout.strip():
            print("❌ Error: You have uncommitted changes. Please commit or stash them before pulling.", file=sys.stderr)
            sys.exit(1)

        # Execute the pull command
        print(f"Pulling latest changes...")
        pull_cmd = [git_path, "-C", str(project_dir), "pull"]

        # We stream the output directly to the user's console
        pull_result = subprocess.run(pull_cmd, text=True)

        if pull_result.returncode == 0:
            print("\n✅ Pull successful.")
            sys.exit(0)
        else:
            print(f"\n❌ Git pull command failed with exit code {pull_result.returncode}.", file=sys.stderr)
            # Git's own error messages will be printed to stderr by subprocess.run
            sys.exit(pull_result.returncode)

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else str(e)
        print(f"❌ An error occurred: {stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def run_patch(args):
    """Applies a patch from a file or stdin."""
    import subprocess
    import sys
    import shutil

    project_dir = args.project_dir.resolve()

    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot apply patch.", file=sys.stderr)
        sys.exit(1)

    cmd = [git_path, "-C", str(project_dir), "apply"]
    if args.reverse:
        cmd.append("--reverse")

    patch_content = None
    if args.patch_file:
        print(f"--- Applying patch from file: {args.patch_file} ---")
        patch_path = Path(args.patch_file)
        if not patch_path.is_file():
            print(f"❌ Error: Patch file not found at '{patch_path}'", file=sys.stderr)
            sys.exit(1)
        try:
            patch_content = patch_path.read_text()
        except IOError as e:
            print(f"❌ Error reading patch file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("--- Applying patch from stdin ---")
        try:
            patch_content = sys.stdin.read()
        except Exception as e:
            print(f"❌ Error reading from stdin: {e}", file=sys.stderr)
            sys.exit(1)

    if not patch_content:
        print("❌ Error: No patch content provided.", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(
            cmd,
            input=patch_content,
            text=True,
            capture_output=True
        )
        if result.returncode != 0:
            print("❌ Error applying patch:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)

        print("✅ Patch applied successfully.")
        sys.exit(0)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        print(f"❌ An error occurred during patch process: {stderr}", file=sys.stderr)
        sys.exit(1)


def _pr_create(args, config):
    """Helper function to create a pull request."""
    import shutil
    import subprocess
    import requests
    from shared.git import get_current_branch
    from shared.github_client import GitHubClient

    project_dir = args.project_dir.resolve()
    print(f"--- Creating Pull Request in: {project_dir} ---")

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path or not (project_dir / ".git").is_dir():
        print("❌ Error: Not a git repository.", file=sys.stderr)
        sys.exit(1)

    if not config.github_token:
        print("❌ Error: GitHub token not found. Please set GITHUB_TOKEN environment variable or run 'configure' to set 'github_token'.", file=sys.stderr)
        sys.exit(1)

    try:
        # 1. Get current branch
        current_branch = get_current_branch(project_dir)
        if not current_branch or current_branch in ["main", "master"]:
            print("❌ Error: You must be on a feature branch to create a pull request.", file=sys.stderr)
            sys.exit(1)
        print(f"  - On branch: {current_branch}")

        # 2. Check if the branch is pushed to remote
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "ls-remote", "--exit-code", "--heads", "origin", current_branch],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print("❌ Error: Your branch has not been pushed to the remote repository.", file=sys.stderr)
            print("  Please run 'push' first.", file=sys.stderr)
            sys.exit(1)

        # 3. Create GitHub client and PR
        client = GitHubClient(token=config.github_token, host=config.github_host or "github.com")
        print("  - Creating pull request...")
        pr_data = client.create_pull_request(
            project_dir=project_dir,
            title=args.title,
            body=args.body,
            head_branch=current_branch,
            base_branch=args.base
        )

        print("\n✅ Pull request created successfully!")
        print(f"   URL: {pr_data['html_url']}")

    except (subprocess.CalledProcessError, ValueError, requests.exceptions.RequestException) as e:
        print(f"❌ An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

def run_pr(args):
    """Handles the creation of GitHub pull requests."""
    file_config = load_config_from_file(profile=getattr(args, 'profile', None))
    config = argparse.Namespace(
        github_token=os.environ.get("GITHUB_TOKEN") or file_config.get("github_token"),
        github_host=file_config.get("github_host")
    )

    if args.action == "create":
        _pr_create(args, config)
    else:
        print(f"Unknown pr action: {args.action}", file=sys.stderr)
        sys.exit(1)


def run_commit(args):
    """Handles the git commit command with safety checks."""
    import shutil
    import subprocess

    project_dir = args.project_dir.resolve()
    commit_message = args.message

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot commit.", file=sys.stderr)
        sys.exit(1)

    # --- Run tests if requested ---
    if args.run_tests:
        print("--- Running tests before commit ---")
        test_args = argparse.Namespace(project_dir=project_dir, test_args=[])
        try:
            run_test(test_args)
        except SystemExit as e:
            if e.code != 0:
                print("\n❌ Tests failed. Commit aborted.", file=sys.stderr)
                sys.exit(1)
        print("✅ Tests passed. Proceeding with commit.")

    # --- Stage all changes ---
    print("--- Staging all changes ---")
    try:
        subprocess.run([git_path, "-C", str(project_dir), "add", "-A"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error staging files: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    # --- Check if there's anything to commit ---
    check_staged_result = subprocess.run([git_path, "-C", str(project_dir), "diff", "--cached", "--quiet"], capture_output=True)
    if check_staged_result.returncode == 0:
        print("✅ No changes staged for commit.")
        sys.exit(0)

    # --- Interactive Commit Message Generation ---
    if not commit_message:
        try:
            print("--- Interactive Commit ---")
            print("Please provide the details for your commit message.")

            commit_type = input("Commit type (e.g., feat, fix, chore, docs): ").strip()
            while not commit_type:
                print("Commit type cannot be empty.")
                commit_type = input("Commit type: ").strip()

            scope = input("Scope (optional, e.g., cli, agent): ").strip()
            short_description = input("Short description (max 72 chars): ").strip()
            while not short_description:
                print("Short description cannot be empty.")
                short_description = input("Short description: ").strip()

            body = input("Body (optional, press Enter to skip): ").strip()
            is_breaking_change = input("Is this a breaking change? [y/N]: ").strip().lower() == 'y'
            breaking_change_description = ""
            if is_breaking_change:
                breaking_change_description = input("Describe the breaking change: ").strip()

            # Assemble the commit message
            header = f"{commit_type}"
            if scope:
                header += f"({scope})"
            header += f": {short_description}"

            commit_message = header
            if body:
                commit_message += f"\n\n{body}"
            if breaking_change_description:
                commit_message += f"\n\nBREAKING CHANGE: {breaking_change_description}"

            print("\n--- Generated Commit Message ---")
            print(commit_message)
            print("------------------------------")
            confirm = input("Confirm commit? [Y/n]: ").strip().lower()
            if confirm not in ['y', '']:
                print("Commit aborted.")
                sys.exit(0)

        except (KeyboardInterrupt, EOFError):
            print("\nCommit aborted by user.")
            sys.exit(1)

    # --- Create the commit ---
    print(f"--- Creating commit ---")
    try:
        commit_cmd = [git_path, "-C", str(project_dir), "commit", "-m", commit_message]
        commit_result = subprocess.run(commit_cmd, check=True, capture_output=True, text=True)
        print(commit_result.stdout.strip())
        print("\n✅ Commit created successfully.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"❌ Git commit command failed:", file=sys.stderr)
        print(e.stdout, file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(e.returncode)


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


def _worktree_show_logic(args, git_path, project_dir, worktrees_base_dir):
    """Helper function to show a comprehensive dashboard for a worktree."""
    import subprocess
    import json

    if not args.worktree_name:
        print("❌ Error: 'show' action requires a worktree name.", file=sys.stderr)
        return False

    worktree_name = args.worktree_name
    worktree_path = (worktrees_base_dir / worktree_name).resolve()
    if not worktree_path.is_dir():
        print(f"❌ Error: Worktree '{worktree_name}' not found at '{worktree_path}'.", file=sys.stderr)
        return False

    print(f"--- Dashboard for Worktree: {worktree_name} ---")

    # 1. Get Core Information (Path, Branch)
    branch_name = "N/A"
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
                        if branch_ref:
                             branch_name = branch_ref.replace("refs/heads/", "")
                        break
                current_worktree = {}
            else:
                key, value = line.split(" ", 1)
                current_worktree[key] = value
        if branch_name == "N/A" and current_worktree: # Check last block
             path = Path(current_worktree.get("worktree", ""))
             if path.resolve() == worktree_path.resolve():
                 branch_ref = current_worktree.get("branch", "")
                 if branch_ref:
                     branch_name = branch_ref.replace("refs/heads/", "")

    except subprocess.CalledProcessError as e:
        print(f"❌ Warning: Could not determine branch for worktree: {e.stderr}", file=sys.stderr)

    print(f"  Path:   {worktree_path}")
    print(f"  Branch: {branch_name}")

    # 2. Get Sprint Task Context
    sprint_plan_path = project_dir / "sprint_plan.json"
    if sprint_plan_path.exists():
        try:
            with open(sprint_plan_path, 'r') as f:
                plan = json.load(f)
            tasks = plan.get("tasks", [])
            # Assuming worktree name is sprint-task-<id>
            if "sprint-task-" in worktree_name:
                task_id = worktree_name.split("sprint-task-")[-1]
                task = next((t for t in tasks if t.get("id") == task_id), None)
                if task:
                    print("\n--- Sprint Task Info ---")
                    print(f"  Title: {task.get('title', 'N/A')}")
                    print(f"  Description: {task.get('description', 'N/A')}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Warning: Could not read or parse sprint_plan.json: {e}", file=sys.stderr)

    # 3. Get Git Status
    print("\n--- Git Status ---")
    try:
        result = subprocess.run(
            [git_path, "-C", str(worktree_path), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            print("  Uncommitted changes:")
            for line in result.stdout.strip().split('\n'):
                # Don't strip leading whitespace as it breaks alignment
                print(f"    {line}")
        else:
            print("  ✅ Worktree is clean (no uncommitted changes).")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting worktree status: {e.stderr}", file=sys.stderr)

    # 4. Get Diff Summary
    print("\n--- Diff Summary (vs HEAD) ---")
    try:
        result = subprocess.run(
            [git_path, "-C", str(worktree_path), "diff", "--stat", "HEAD"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"❌ Error running git diff: {result.stderr}", file=sys.stderr)
        elif not result.stdout.strip():
            print("  ✅ No differences with HEAD.")
        else:
            # Indent the output for better readability
            for line in result.stdout.strip().split('\n'):
                print(f"  {line.strip()}")
    except Exception as e:
        print(f"❌ An unexpected error occurred during diff: {e}", file=sys.stderr)

    return True


def _worktree_show(args, git_path, project_dir, worktrees_base_dir):
    """Entry point for the 'show' command that calls the logic and exits."""
    success = _worktree_show_logic(args, git_path, project_dir, worktrees_base_dir)
    sys.exit(0 if success else 1)


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
        _worktree_show(args, git_path, project_dir, worktrees_base_dir)

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

    # Handle `knowledge` command
    if args.command == "knowledge":
        run_knowledge(args)
        return

    # Handle `ask` command
    if args.command == "ask":
        await run_ask(args)
        return

    # Handle `do` command
    if args.command == "do":
        await run_do(args)
        return

    # Handle `optimize` command
    if args.command == "optimize":
        await run_optimize(args)
        return

    # Handle `debug` command
    if args.command == "debug":
        await run_debug(args)
        return

    # Handle `code-review` command
    if args.command == "code-review":
        await run_code_review(args)
        return

    # Handle `summarize` command
    if args.command in ["summarize", "explain"]:
        await run_summarize(args)
        return

    # Handle `init` command
    if args.command == "init":
        run_init(args)
        return

    # Handle `onboard` command
    if args.command == "onboard":
        run_onboard(args)
        return

    # Handle `session` command
    if args.command == "session":
        run_session(args)
        return

    # Handle `secrets` command
    if args.command == "secrets":
        run_secrets(args)
        return

    # Handle `playground` command
    if args.command == "playground":
        run_playground(args)
        return

    # Handle `completion` command
    if args.command == "completion":
        run_completion()
        return

    # Handle `plan` command
    if args.command == "plan":
        await run_plan(args)
        return

    # Handle `config` command
    if args.command == "config":
        sys.exit(run_config(args))

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

    # Handle `prune` command
    if args.command == "prune":
        run_prune(args)
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

    # Handle `rewind` command
    if args.command == "rewind":
        run_rewind(args)
        return

    # Handle `discard` command
    if args.command == "discard":
        run_discard(args)
        return

    # Handle `undo` command
    if args.command == "undo":
        run_undo(args)
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

    # Handle `models` command
    if args.command == "models":
        run_models(args)
        return

    # Handle `glance` command
    if args.command == "glance":
        run_glance(args)
        return

    # Handle `status` command
    if args.command == "status":
        run_status(args)
        return

    # Handle `dashboard` command
    if args.command == "dashboard":
        run_dashboard(args)
        return

    # Handle `summary` command
    if args.command == "summary":
        run_summary(args)
        return

    # Handle `suggest` command
    if args.command == "suggest":
        run_suggest(args)
        return

    # Handle `history` command
    if args.command == "history":
        run_history(args)
        return

    if args.command == "last":
        run_last(args)
        return

    if args.command == "last-run-id":
        run_last_run_id(args)
        return

    if args.command == "diff-summary":
        run_diff_summary(args)
        return

    if args.command == "diff":
        run_diff(args)
        return

    if args.command == "log":
        run_log(args)
        return

    if args.command == "logs":
        run_logs(args)
        return

    # Handle `workflow` command
    if args.command == "workflow":
        run_workflow(args)
        return

    # Handle `cost` command
    if args.command == "cost":
        run_cost(args)
        return

    # Handle `benchmark` command
    if args.command == "benchmark":
        run_benchmark(args)
        return

    # Handle `sprint` command
    if args.command == "sprint":
        run_sprint_command(args)
        return

    if args.command == "branch":
        run_branch(args)
        return

    if args.command == "mutate":
        run_mutate(
            project_dir=args.project_dir,
            target_file=args.target_file,
            test_command=args.test_command
        )
        return

    if args.command == "test":
        run_test(args)
        return

    if args.command == "lint":
        run_lint(args)
        return

    if args.command == "format":
        run_format(args)
        return

    if args.command == "hooks":
        run_hooks(args)
        return

    if args.command in ["recipes", "macro"]:
        run_recipes(args)
        return

    if args.command == "git":
        run_git(args)
        return

    # Handle `history-graph` command
    if args.command == "history-graph":
        run_history_graph(args)
        return

    if args.command == "tree":
        run_tree(args)
        return
    if args.command == "report":
        run_report(args)
        return

    if args.command == "push":
        run_push(args)
        return

    if args.command == "pull":
        run_pull(args)
        return

    if args.command == "patch":
        run_patch(args)
        return

    if args.command == "issues":
        _run_issues_logic(args)
        return

    if args.command == "pr":
        run_pr(args)
        return

    if args.command == "commit":
        run_commit(args)
        return

    if args.command == "feature":
        run_feature(args)
        return

    if args.command == "interact":
        run_interact(args)
        return

    if args.command == "profile":
        run_profile(args)
        return

    if args.command == "watch":
        run_watch(args)
        return

    if args.command == "why":
        run_why(args)
        return

    if args.command == "blame":
        run_blame(args)
        return

    if args.command == "stash":
        run_stash(args)
        return

    if args.command == "next":
        run_next(args)
        return

    if args.command == "context":
        run_context(args)
        return

    if args.command == "search":
        run_search(args)
        return

    if args.command in ["smart-search", "ssearch"]:
        run_smart_search(args)
        return

    if args.command == "replace":
        run_replace(args)
        return

    if args.command == "todos":
        run_todos(args)
        return

    if args.command == "review":
        run_review(args)
        return

    if args.command == "env":
        run_env(args)
        return

    if args.command == "setup":
        run_setup(args)
        return

    if args.command == "dockerize":
        run_dockerize(args)
        return

    if args.command == "cicd":
        run_cicd(args)
        return

    if args.command == "verify":
        run_verify(args)
        return

    # Handle `health` command
    if args.command == "health":
        run_health_check(args.project_dir, output_format=args.format, output_file=args.output)
        return

    if args.command == "security":
        run_security(args)
        return

    if args.command == "help":
        run_help(args)
        return

    if args.command == "cherry-pick":
        run_cherry_pick(args)
        return

    if args.command == "rollback":
        run_rollback(args)
        return

    if args.command == "analytics":
        run_analytics(args)
        return

    if args.command == "deps":
        run_deps(args)
        return

    if args.command == "duplication":
        run_duplication(args)
        return

    if args.command == "unused":
        run_unused(args)
        return

    if args.command == "risk":
        run_risk(args)
        return

    if args.command == "impact":
        run_impact(args)
        return

    if args.command == "a11y":
        run_a11y(args)
        return

    if args.command == "license":
        run_license(args)
        return

    if args.command == "bisect":
        await run_bisect(args)
        return

    if args.command == "map":
        run_map(args)
        return

    if args.command in ["architecture", "arch"]:
        run_architecture(args)
        return

    if args.command == "release":
        run_release(args)
        return

    if args.command == "docstring":
        await run_docstring(args)
        return

    if args.command == "refactor":
        await run_refactor(args)
        return

    if args.command == "polish":
        await run_polish(args)
        return

    if args.command == "resolve":
        await run_resolve(args)
        return

    if args.command in ["resolve-conflicts", "fix-conflicts"]:
        await run_resolve_conflicts(args)
        return

    if args.command in ["generate-tests", "gentest"]:
        await run_generate_tests(args)
        return

    # Handle `mock` command
    if args.command == "mock":
        from shared.mock_data import run_mock_logic
        success = run_mock_logic(
            spec_path=args.spec,
            count=args.count,
            output_format=args.format,
            output_file=args.output,
            table_name=args.table
        )
        sys.exit(0 if success else 1)

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
