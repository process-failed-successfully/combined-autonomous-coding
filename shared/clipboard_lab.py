import json
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    pyperclip = None
    HAS_PYPERCLIP = False


class ClipboardManager:
    """Manages clipboard history and operations."""

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")
        self.history_file = self.project_dir / ".clipboard_history.json"
        self.history: List[Dict[str, Any]] = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_history(self) -> None:
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save clipboard history: {e}", file=sys.stderr)

    def add(self, content: str, source: str = "manual") -> None:
        """Adds content to clipboard history."""
        if not content:
            return

        # Deduplicate: if same as last item, just update timestamp
        if self.history and self.history[0]["content"] == content:
            self.history[0]["timestamp"] = time.time()
            self._save_history()
            return

        item = {
            "content": content,
            "timestamp": time.time(),
            "source": source
        }
        self.history.insert(0, item)

        # Limit history size (e.g. 50 items)
        if len(self.history) > 50:
            self.history = self.history[:50]

        self._save_history()

        # Try to sync to system clipboard
        if HAS_PYPERCLIP:
            try:
                pyperclip.copy(content)
            except Exception:
                pass  # Ignore system clipboard errors

    def get(self, index: int) -> Optional[str]:
        """Gets content at specific index (0 is latest)."""
        if 0 <= index < len(self.history):
            return self.history[index]["content"]
        return None

    def delete(self, index: int) -> bool:
        """Deletes item at index."""
        if 0 <= index < len(self.history):
            del self.history[index]
            self._save_history()
            return True
        return False

    def update(self, index: int, content: str) -> bool:
        """Updates item at index."""
        if 0 <= index < len(self.history):
            self.history[index]["content"] = content
            self.history[index]["timestamp"] = time.time()
            self._save_history()
            return True
        return False

    def list_history(self) -> List[Dict[str, Any]]:
        """Returns the full history."""
        return self.history

    def clear(self) -> None:
        """Clears history."""
        self.history = []
        self.history_file.unlink(missing_ok=True)

    def sync_system(self) -> bool:
        """
        Reads from system clipboard and adds to history if new.
        Returns True if something new was added.
        """
        if not HAS_PYPERCLIP:
            return False

        try:
            content = pyperclip.paste()
            if content:
                # Check if it's already the latest
                if not self.history or self.history[0]["content"] != content:
                    self.add(content, source="system")
                    return True
        except Exception:
            pass
        return False


def run_clipboard_lab_logic(args):
    """CLI Handler for Clipboard Lab."""
    # Ensure project_dir is available from args, defaulting to .
    project_dir = getattr(args, "project_dir", Path("."))
    manager = ClipboardManager(project_dir)

    if args.action == "add":
        if not args.content:
            # Try reading from stdin
            if not sys.stdin.isatty():
                content = sys.stdin.read().strip()
                if content:
                    manager.add(content, source="cli-pipe")
                    print("Added from stdin.")
                else:
                    print("Error: No content provided.", file=sys.stderr)
            else:
                print("Error: Content required.", file=sys.stderr)
        else:
            manager.add(args.content, source="cli")
            print("Added to clipboard history.")

    elif args.action == "list":
        # Check system clipboard first
        manager.sync_system()

        history = manager.list_history()
        if not history:
            print("Clipboard history is empty.")
            return

        print(f"--- Clipboard History ({len(history)} items) ---")
        for i, item in enumerate(history[:10]):  # Show top 10
            preview = item['content'].replace('\n', '\\n')
            if len(preview) > 60:
                preview = preview[:57] + "..."
            print(f"[{i}] {preview}")

    elif args.action == "get":
        content_item = manager.get(args.index)
        if content_item is not None:
            print(content_item)
        else:
            print(f"Error: Index {args.index} out of range.", file=sys.stderr)

    elif args.action == "clear":
        manager.clear()
        print("Clipboard history cleared.")

    elif args.action == "tui":
        from shared.tui import AgentTUI
        print("Launching Clipboard Lab TUI...")
        app = AgentTUI(project_dir=project_dir, start_tab="tab-clipboard")
        app.run()
