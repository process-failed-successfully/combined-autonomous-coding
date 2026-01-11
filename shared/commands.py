import sys
import os
import subprocess
import shlex
from pathlib import Path
from .cli_utils import get_suggestions

COMMAND_DESCRIPTIONS = {
    "configure": "Use this command to run an interactive wizard that helps you create or update your `agent_config.yaml` file. It's the easiest way to set up API keys for services like Jira, GitHub, Slack, and Discord.",
    "config": "Use this to quickly view, set, or list key-value settings in your `agent_config.yaml` from the command line, without needing to open the file.",
    "validate": "Use this to check that your `agent_config.yaml` file is correctly formatted and doesn't have any obvious errors before you run the agent.",
    "doctor": "Use this to run a full health check on your environment. It checks your configuration, dependencies like Git, API connectivity, and file permissions to diagnose potential problems.",
    "init": "Use this to start a new project. It runs an interactive wizard to initialize a Git repository, create a standard `.gitignore` file, and generate an `app_spec.txt` file for your project requirements.",
    "status": "Use this to get a detailed, color-coded dashboard of your project's current state, including the workflow stage, recent agent activity, and a summary of uncommitted Git changes.",
    "glance": "Use this for a quick, compact overview of the project's status, showing the current workflow stage, a one-line Git summary, and the next suggested command.",
    "dashboard": "Use this for a comprehensive overview of the project, including workflow status, git status, last run summary, and suggested next commands.",
    "suggest": "Use this command when you're not sure what to do next. It analyzes the project's state and recommends the most logical command to run.",
    "next": "Analyzes the project's state, suggests the most logical next action, and executes it upon your confirmation. It acts as a CLI copilot to streamline your workflow.",
    "history": "Use this to see a list of all the agent runs for the current project, including their Run IDs and a summary of the final log entries.",
    "last": "Use this to quickly see a summary of the very last agent run, including its performance metrics, QA summary, and the last few log lines.",
    "last-run-id": "Use this when you need to programmatically get the ID of the last agent run, for use in scripts or other commands.",
    "log": "Use this to view the Git commit history for the project in a nicely formatted, graphical way. It's a wrapper around `git log`.",
    "logs": "Use this to view the detailed agent logs for a specific run. You can tail the logs in real-time (`-f`), filter them (`-g`), or just view the last few lines (`-n`).",
    "diff": "Use this to see what has changed. Without arguments, it shows uncommitted changes. With a commit hash or Run ID, it shows the changes made in that specific commit.",
    "diff-summary": "Use this to get a quick summary of uncommitted file changes, similar to `git diff --stat`.",
    "clean": "Use this to move all agent-generated files (like logs, metrics, and marker files) into a timestamped folder within the `.agent_trash/` directory. Use `--archive` to save them to `.agent_archives/` instead.",
    "discard": "Use this to revert uncommitted changes in your working directory. It safely stashes your changes first, so you can recover them with the `undo` command.",
    "undo": "Use this to recover changes that were previously discarded with the `discard` command by restoring a stash.",
    "rewind": "Use this to reset your project to a previous state. You can specify a Git commit or an agent Run ID to return to, but be careful as this is a destructive action.",
    "artifacts": "Use this as a powerful, unified command to manage generated files. You can `list`, `restore`, `clear`, `inspect`, or `diff` items in either the `trash` or `archive`.",
    "plan": "Use this for a 'dry run' of the agent's planning phase. It will generate the `feature_list.json` based on your spec file without executing any code.",
    "test": "Use this to automatically detect the project type (Python, Node.js, etc.) and run its test suite.",
    "lint": "Use this to automatically detect and run the appropriate linter (e.g., Ruff, Flake8, ESLint) on your codebase.",
    "format": "Use this to automatically format your code using standard tools like Black or Prettier.",
    "commit": "Use this to stage all changes and create a commit. It can guide you through writing a Conventional Commit message interactively.",
    "push": "Use this as a safe alternative to `git push`. It prevents you from pushing to protected branches like `main` and ensures your workspace is clean.",
    "pull": "Use this as a safe alternative to `git pull`. It prevents pulling if you have uncommitted changes, avoiding accidental merge conflicts.",
    "pr": "Use this to manage GitHub Pull Requests. The `pr create` subcommand helps you create a new PR from your current branch.",
    "feature": "Use this to run a guided workflow for creating a new feature, which walks you through creating a branch, committing, pushing, and creating a pull request.",
    "branch": "Use this to manage a dedicated feature branch for the agent to work on, allowing you to `create`, `checkout`, `merge`, and `list` branches.",
    "profile": "Use this to manage different configuration profiles (e.g., for different projects or models) within your global `agent_config.yaml`.",
    "tui": "Use this to launch a terminal-based user interface that provides a real-time, interactive dashboard for monitoring and managing the agent.",
    "shell": "Use this to start an interactive shell where you can run all the agent's CLI commands without repeatedly typing the script name.",
    "why": "Use this command to find out what another command does. For example, `why status`."
}


def run_next(args):
    """Analyzes the project and executes the next logical command."""
    project_dir = args.project_dir.resolve()

    print("--- Determining next step... ---")
    suggestions = get_suggestions(project_dir=project_dir, limit=1)

    if not suggestions:
        print("✅ Project is in a clean state. No specific action to suggest.")
        print("   - To start a new task, run the agent with a --spec or --jira-ticket.")
        sys.exit(0)

    # Take the top suggestion
    suggestion = suggestions[0]
    command_to_run_str = suggestion['command']
    reason = suggestion['reason']

    print(f"\nSuggested command: `{command_to_run_str}`")
    print(f"Reason: {reason}")

    if not args.yes:
        confirm = input("\nExecute this command? [Y/n]: ").strip().lower()
        if confirm not in ['y', '']:
            print("Aborted.")
            sys.exit(0)

    command_parts = shlex.split(command_to_run_str)[1:]

    # Get the repo root to find main.py
    repo_root = Path(__file__).parent.parent
    main_py_path = repo_root / "main.py"

    if not main_py_path.exists():
        print(f"❌ Error: Could not find main entry point at '{main_py_path}'", file=sys.stderr)
        sys.exit(1)

    full_command = [sys.executable, str(main_py_path)] + command_parts

    print(f"\nExecuting: {' '.join(full_command)}\n")
    try:
        # Use subprocess.run without capturing output to stream directly
        result = subprocess.run(full_command, cwd=project_dir)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(f"❌ Error: Command '{full_command[0]}' not found.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCommand execution interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ An unexpected error occurred while running command: {e}", file=sys.stderr)
        sys.exit(1)


def run_why(args):
    """Explains what a command does and why you might use it."""
    command_name = args.command_name

    if not command_name:
        print("--- Why, oh why? ---")
        print("This command explains what other commands do and why you might use them.")
        print("\nUsage: why <command_name>\n")
        print("For example: `why status` or `why discard`\n")
        print("--- Available Commands ---")

        # Determine the longest command name for alignment
        if COMMAND_DESCRIPTIONS:
            max_len = max(len(cmd) for cmd in COMMAND_DESCRIPTIONS.keys())
            for cmd, desc in sorted(COMMAND_DESCRIPTIONS.items()):
                # Just print the first sentence.
                short_desc = desc.split('.')[0] + '.'
                print(f"  {cmd:<{max_len + 2}} {short_desc}")
        sys.exit(0)

    description = COMMAND_DESCRIPTIONS.get(command_name)

    if description:
        # Use textwrap for nice formatting
        import textwrap
        print(f"--- What is `{command_name}`? ---")
        wrapped_description = textwrap.fill(description, width=80)
        print(wrapped_description)
    else:
        print(f"❌ Error: Command '{command_name}' not found or has no explanation.")
        print("   Run 'why' without arguments to see all available explanations.")
        sys.exit(1)
    sys.exit(0)

def run_commands(args):
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
    print_command("commands", "Show this help message.")

    print(f"\nFor detailed options on a specific command, run: {executable_name} [command] --help")
    sys.exit(0)
