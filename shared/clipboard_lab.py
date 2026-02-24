import sys
import subprocess
import shutil
import json
import os
import time
from pathlib import Path
from typing import List, Optional

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False
    pyperclip = None

class ClipboardManager:
    """Manages clipboard operations and history."""

    def __init__(self, project_dir: Path = Path(".")):
        self.project_dir = project_dir
        self.history_file = self.project_dir / ".clipboard_history.json"
        self.history_limit = 50

    def _get_platform_cmd(self, action: str):
        if sys.platform == "darwin":
            return "pbcopy" if action == "copy" else "pbpaste"
        elif sys.platform == "win32":
            # Windows clip only supports copy from stdin.
            # Paste needs powershell Get-Clipboard
            return "clip" if action == "copy" else "powershell"
        else:
            # Linux - check for xclip or wl-copy
            if os.environ.get("WAYLAND_DISPLAY"):
                return "wl-copy" if action == "copy" else "wl-paste"
            if shutil.which("xclip"):
                return "xclip" if action == "copy" else "xclip"
            if shutil.which("xsel"):
                return "xsel" if action == "copy" else "xsel"
        return None

    def copy_to_system(self, text: str) -> bool:
        """Copies text to system clipboard."""
        if HAS_PYPERCLIP:
            try:
                pyperclip.copy(text)
                self.add_to_history(text)
                return True
            except Exception:
                pass # Fallback

        # Subprocess fallback
        cmd_name = self._get_platform_cmd("copy")
        if not cmd_name:
            return False

        try:
            input_bytes = text.encode("utf-8")
            if sys.platform == "darwin":
                subprocess.run(["pbcopy"], input=input_bytes, check=True)
            elif sys.platform == "win32":
                subprocess.run(["clip"], input=input_bytes, check=True)
            else:
                # Linux
                if cmd_name == "wl-copy":
                    subprocess.run(["wl-copy"], input=input_bytes, check=True)
                elif cmd_name == "xclip":
                    subprocess.run(["xclip", "-selection", "clipboard"], input=input_bytes, check=True)
                elif cmd_name == "xsel":
                    subprocess.run(["xsel", "-b", "-i"], input=input_bytes, check=True)

            self.add_to_history(text)
            return True
        except Exception as e:
            print(f"Clipboard copy error: {e}", file=sys.stderr)
            return False

    def paste_from_system(self) -> Optional[str]:
        """Gets text from system clipboard."""
        if HAS_PYPERCLIP:
            try:
                return pyperclip.paste()
            except Exception:
                pass

        cmd_name = self._get_platform_cmd("paste")
        if not cmd_name:
            return None

        try:
            if sys.platform == "darwin":
                res = subprocess.run(["pbpaste"], capture_output=True, check=True)
                return res.stdout.decode("utf-8")
            elif sys.platform == "win32":
                res = subprocess.run(["powershell", "-command", "Get-Clipboard"], capture_output=True, check=True)
                return res.stdout.decode("utf-8").strip() # powershell adds newline
            else:
                if cmd_name == "wl-paste":
                    res = subprocess.run(["wl-paste"], capture_output=True, check=True)
                    return res.stdout.decode("utf-8")
                elif cmd_name == "xclip":
                    res = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, check=True)
                    return res.stdout.decode("utf-8")
                elif cmd_name == "xsel":
                    res = subprocess.run(["xsel", "-b", "-o"], capture_output=True, check=True)
                    return res.stdout.decode("utf-8")
        except Exception:
            return None
        return None

    def add_to_history(self, text: str) -> None:
        if not text:
            return

        history = self.get_history()
        # Remove duplicates (move to top)
        history = [item for item in history if item["text"] != text]

        history.insert(0, {
            "text": text,
            "timestamp": time.time()
        })

        self._save_history(history[:self.history_limit])

    def get_history(self) -> List[dict]:
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_history(self, history: List[dict]) -> None:
        try:
            with open(self.history_file, "w") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

    def clear_history(self) -> None:
        if self.history_file.exists():
            self.history_file.unlink()

def run_clipboard_lab_logic(args):
    manager = ClipboardManager(args.project_dir)

    if args.action == "copy":
        text = None
        if args.text:
            text = args.text
        elif args.file:
            path = Path(args.file)
            if path.exists():
                text = path.read_text()
            else:
                print(f"File not found: {args.file}", file=sys.stderr)
                sys.exit(1)
        else:
            # Read stdin
            if not sys.stdin.isatty():
                try:
                    text = sys.stdin.read()
                except Exception:
                    pass

        if text:
            if manager.copy_to_system(text):
                print("Copied to clipboard.")
            else:
                print("Failed to copy to clipboard.", file=sys.stderr)
                sys.exit(1)
        else:
            print("No text to copy.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "paste":
        text = manager.paste_from_system()
        if text:
            print(text)
        else:
            print("Clipboard empty or inaccessible.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "history":
        history = manager.get_history()
        if not history:
            print("History empty.")
        else:
            print("--- Clipboard History ---")
            for i, item in enumerate(history):
                content = item['text'].replace('\n', '\\n')
                if len(content) > 60:
                    content = content[:57] + "..."
                print(f"{i+1:2} | {content}")

    elif args.action == "clear":
        manager.clear_history()
        print("History cleared.")
