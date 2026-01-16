import sys

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
    "security": "Use this to run a security audit on your codebase. It scans for common vulnerabilities using Bandit and provides actionable suggestions for fixes.",
    "why": "Use this command to find out what another command does. For example, `why status`."
}

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
