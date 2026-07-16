import sys
import subprocess
import os
import time
from pathlib import Path

class CrontabLabManager:
    """Manages reading, writing, clearing, and backing up system crontabs."""

    def __init__(self, backup_dir: Path = Path.home() / ".local" / "share" / "combined_autonomous_coding" / "crontab_backups"):
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def read_crontab(self) -> str:
        """Reads the current user's crontab."""
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if "no crontab for" in e.stderr.lower() or e.returncode == 1:
                return "" # Empty crontab
            raise RuntimeError(f"Failed to read crontab: {e.stderr}")

    def write_crontab(self, content: str) -> bool:
        """Writes the given content to the user's crontab."""
        content_bytes = content.encode("utf-8")
        if not content.endswith("\n"):
            content_bytes += b"\n"

        try:
            process = subprocess.Popen(
                ["crontab", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(input=content_bytes)

            if process.returncode != 0:
                raise RuntimeError(f"Failed to write crontab: {stderr.decode('utf-8')}")
            return True
        except Exception as e:
            raise RuntimeError(f"Error writing crontab: {str(e)}")

    def clear_crontab(self) -> bool:
        """Clears the user's crontab."""
        try:
            subprocess.run(["crontab", "-r"], capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            if "no crontab for" in e.stderr.lower():
                return True # Already empty
            raise RuntimeError(f"Failed to clear crontab: {e.stderr}")

    def backup_crontab(self) -> str:
        """Backs up the current crontab to the backup directory."""
        content = self.read_crontab()
        if not content:
            raise RuntimeError("No crontab to backup.")

        timestamp = int(time.time())
        backup_file = self.backup_dir / f"crontab_backup_{timestamp}.txt"
        backup_file.write_text(content)
        return str(backup_file)

    def restore_crontab(self, filepath: str) -> bool:
        """Restores the crontab from a given file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Backup file not found: {filepath}")

        content = path.read_text()
        return self.write_crontab(content)

    def list_backups(self) -> list[str]:
        """Lists all available backups in the backup directory."""
        backups = list(self.backup_dir.glob("crontab_backup_*.txt"))
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return [str(b) for b in backups]

def run_crontab_lab_logic(args) -> bool:
    """CLI logic for Crontab Lab."""
    manager = CrontabLabManager()

    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching Crontab Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-crontab")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if getattr(args, '_in_event_loop', False) or (loop and loop.is_running()):
            asyncio.ensure_future(app.run_async())
            return True
        else:
            app.run()
            sys.exit(0)
            return True

    action = getattr(args, "action", None)

    try:
        if action == "list":
            content = manager.read_crontab()
            if content:
                print(content)
            else:
                print("No crontab for current user.")

        elif action == "edit":
            if not getattr(args, "file", None):
                print("Error: --file is required for edit action.", file=sys.stderr)
                return False

            path = Path(args.file)
            if not path.exists():
                print(f"Error: File not found: {args.file}", file=sys.stderr)
                return False

            content = path.read_text()
            if manager.write_crontab(content):
                print("Successfully updated crontab.")

        elif action == "clear":
            if manager.clear_crontab():
                print("Successfully cleared crontab.")

        elif action == "backup":
            try:
                filepath = manager.backup_crontab()
                print(f"Backup saved to: {filepath}")
            except Exception as e:
                print(f"Error backing up: {e}", file=sys.stderr)
                return False

        elif action == "restore":
            if not getattr(args, "file", None):
                print("Error: --file is required for restore action.", file=sys.stderr)
                return False

            if manager.restore_crontab(args.file):
                print(f"Successfully restored crontab from: {args.file}")

        else:
            print(f"Unknown action: {action}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    return True
