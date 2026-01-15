import subprocess
import time
import sys
import os
import shutil
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = None

# List of directories to ignore
IGNORED_DIRS = [
    ".git",
    "__pycache__",
    ".agent_trash",
    ".agent_archives",
    "worktrees",
    "node_modules",
    ".pytest_cache",
    ".tox",
    "build",
    "dist",
    ".idea",
    ".vscode",
]

def _determine_default_command(project_dir):
    """Detects the project type and returns the default test command."""
    # Python project
    if (project_dir / "requirements.txt").exists() or (project_dir / "pyproject.toml").exists():
        if shutil.which("pytest"):
            return ["pytest"]
        else:
            return [sys.executable, "-m", "unittest", "discover"]
    # Node.js project
    elif (project_dir / "package.json").exists():
        if (project_dir / "pnpm-lock.yaml").exists():
            return ["pnpm", "test"]
        elif (project_dir / "yarn.lock").exists():
            return ["yarn", "test"]
        else:
            return ["npm", "test"]
    # Go project
    elif (project_dir / "go.mod").exists():
        return ["go", "test", "./..."]
    return None

if FileSystemEventHandler:
    class CommandEventHandler(FileSystemEventHandler):
        def __init__(self, command, project_dir):
            self.project_dir = project_dir
            self.command = command if command else _determine_default_command(project_dir)

            if not self.command:
                print("❌ Error: Could not determine a default command for this project type.", file=sys.stderr)
                print("Please specify a command to run, e.g., 'watch my_test_script.sh'", file=sys.stderr)
                sys.exit(1)

            print(f"Initial run: {' '.join(self.command)}")
            subprocess.run(self.command, cwd=self.project_dir)

        def _is_ignored(self, path):
            """Check if the path is in an ignored directory."""
            try:
                # Resolve the path to handle symlinks and normalize it
                resolved_path = Path(path).resolve()
                # Check if any part of the path is in the ignored list
                return any(part in IGNORED_DIRS for part in resolved_path.parts)
            except (FileNotFoundError, RuntimeError):
                # File may not exist if event is deletion of a symlink
                return True

        def on_any_event(self, event):
            """Handle any file system event."""
            if event.is_directory or self._is_ignored(event.src_path):
                return

            # Use a more descriptive message
            print(f"Changes detected: {event.src_path}. Running: {' '.join(self.command)}")
            subprocess.run(self.command, cwd=self.project_dir)

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
        print("\n--- Stopped watching files ---")
    observer.join()
    sys.exit(0)
