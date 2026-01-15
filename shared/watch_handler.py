
import subprocess
import time
from pathlib import Path
import sys

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = None

# Directories to ignore
IGNORE_DIRS = [".git", "__pycache__", "node_modules", ".agent_trash", ".agent_archives", "build", "dist"]

class CommandEventHandler(FileSystemEventHandler):
    def __init__(self, command, project_dir):
        self.command = command
        self.project_dir = project_dir
        self.last_run = 0
        self.debounce_period = 1  # seconds

    def _should_ignore(self, path_str: str) -> bool:
        """Check if the path should be ignored."""
        path = Path(path_str)
        # Use parts for robust path checking
        return any(part in IGNORE_DIRS for part in path.parts)

    def on_any_event(self, event):
        """Handle any file system event."""
        # Limit to one run per debounce period
        current_time = time.time()
        if current_time - self.last_run < self.debounce_period:
            return

        if self._should_ignore(event.src_path):
            return

        if event.is_directory:
            return

        print(f"Change detected: {event.src_path}. Running command: {' '.join(self.command)}")
        subprocess.run(self.command, cwd=self.project_dir)
        self.last_run = time.time()


def start_watcher(project_dir: Path, command: list):
    if Observer is None:
        print("Error: watchdog library not found. Please install it with 'pip install watchdog'", file=sys.stderr)
        return

    print(f"--- Watching for file changes in: {project_dir} ---")

    # --- Run on Start ---
    print(f"Running command on start: {' '.join(command)}")
    subprocess.run(command, cwd=project_dir)

    print(f"--- Press Ctrl+C to stop ---")

    event_handler = CommandEventHandler(command, project_dir)
    observer = Observer()
    observer.schedule(event_handler, project_dir, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
