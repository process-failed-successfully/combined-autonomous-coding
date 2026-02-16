import sys
import subprocess
import shutil
from typing import List, Dict, Optional, Union

class TmuxManager:
    """
    Manages tmux sessions, windows, and panes via CLI.
    """
    def __init__(self):
        self.tmux_path = shutil.which("tmux")

    def _run_command(self, args: List[str]) -> subprocess.CompletedProcess:
        if not self.tmux_path:
            raise FileNotFoundError("tmux is not installed or not in PATH.")

        try:
            return subprocess.run(
                [self.tmux_path] + args,
                capture_output=True,
                text=True,
                check=False
            )
        except Exception as e:
            raise RuntimeError(f"Error executing tmux command: {e}")

    def list_sessions(self) -> List[Dict[str, str]]:
        """
        Lists all running tmux sessions.
        """
        # Format: session_name:window_count:created:attached
        cmd = ["list-sessions", "-F", "#{session_name}:#{session_windows}:#{session_created}:#{session_attached}"]
        result = self._run_command(cmd)

        if result.returncode != 0:
            if "no server running" in result.stderr:
                return []
            return []

        sessions = []
        for line in result.stdout.strip().split('\n'):
            if not line: continue
            parts = line.split(':')
            if len(parts) >= 4:
                sessions.append({
                    "name": parts[0],
                    "windows": parts[1],
                    "created": parts[2],
                    "attached": parts[3] == "1"
                })
        return sessions

    def new_session(self, session_name: str, command: Optional[str] = None) -> bool:
        """
        Creates a new detached session.
        """
        cmd = ["new-session", "-d", "-s", session_name]
        if command:
            cmd.append(command)

        result = self._run_command(cmd)
        return result.returncode == 0

    def kill_session(self, target: str) -> bool:
        """
        Kills a session.
        """
        cmd = ["kill-session", "-t", target]
        result = self._run_command(cmd)
        return result.returncode == 0

    def attach_session(self, target: str):
        """
        Attaches to a session (interactive).
        Note: This replaces the current process.
        """
        if not self.tmux_path:
            raise FileNotFoundError("tmux is not installed.")

        import os
        os.execv(self.tmux_path, [self.tmux_path, "attach-session", "-t", target])

    def list_windows(self, target_session: str) -> List[Dict[str, str]]:
        """
        Lists windows in a session.
        """
        # Format: window_index:window_name:window_active
        cmd = ["list-windows", "-t", target_session, "-F", "#{window_index}:#{window_name}:#{window_active}"]
        result = self._run_command(cmd)

        if result.returncode != 0:
            return []

        windows = []
        for line in result.stdout.strip().split('\n'):
            if not line: continue
            parts = line.split(':')
            if len(parts) >= 3:
                windows.append({
                    "index": parts[0],
                    "name": parts[1],
                    "active": parts[2] == "1"
                })
        return windows

    def new_window(self, target_session: str, window_name: Optional[str] = None, command: Optional[str] = None) -> bool:
        """
        Creates a new window in a session.
        """
        cmd = ["new-window", "-t", target_session]
        if window_name:
            cmd.extend(["-n", window_name])
        if command:
            cmd.append(command)

        result = self._run_command(cmd)
        return result.returncode == 0

    def send_keys(self, target: str, keys: str) -> bool:
        """
        Sends keys to a target pane/window/session.
        """
        cmd = ["send-keys", "-t", target, keys, "C-m"]
        result = self._run_command(cmd)
        return result.returncode == 0

    def capture_pane(self, target: str, lines: Optional[int] = None) -> str:
        """
        Captures the content of a pane.
        """
        cmd = ["capture-pane", "-p", "-t", target]
        if lines:
            cmd.extend(["-S", f"-{lines}"])

        result = self._run_command(cmd)
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"
        return result.stdout

def run_tmux_lab_logic(args):
    """
    CLI entry point for Tmux Lab.
    """
    manager = TmuxManager()

    if not manager.tmux_path:
        print("❌ Error: 'tmux' is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)

    if args.action == "list":
        sessions = manager.list_sessions()
        if not sessions:
            print("No active tmux sessions.")
        else:
            print(f"{'Name':<20} | {'Windows':<8} | {'Attached':<10}")
            print("-" * 45)
            for s in sessions:
                attached = "Yes" if s['attached'] else "No"
                print(f"{s['name']:<20} | {s['windows']:<8} | {attached:<10}")
        sys.exit(0)

    elif args.action == "new":
        if not args.name:
            print("Error: --name is required for 'new' action.", file=sys.stderr)
            sys.exit(1)

        success = manager.new_session(args.name, args.command_str)
        if success:
            print(f"✅ Created session '{args.name}'")
        else:
            print(f"❌ Failed to create session '{args.name}'.", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    elif args.action == "kill":
        if not args.target:
            print("Error: --target is required for 'kill' action.", file=sys.stderr)
            sys.exit(1)

        success = manager.kill_session(args.target)
        if success:
            print(f"✅ Killed session '{args.target}'")
        else:
            print(f"❌ Failed to kill session '{args.target}'.", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    elif args.action == "attach":
        if not args.target:
            print("Error: --target is required for 'attach' action.", file=sys.stderr)
            sys.exit(1)

        # This will replace the current process
        manager.attach_session(args.target)

    elif args.action == "send":
        if not args.target or not args.keys:
            print("Error: --target and --keys are required for 'send' action.", file=sys.stderr)
            sys.exit(1)

        success = manager.send_keys(args.target, args.keys)
        if success:
            print(f"✅ Sent keys to '{args.target}'")
        else:
            print(f"❌ Failed to send keys to '{args.target}'.", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    elif args.action == "capture":
        if not args.target:
            print("Error: --target is required for 'capture' action.", file=sys.stderr)
            sys.exit(1)

        output = manager.capture_pane(args.target, args.lines)
        print(output)
        sys.exit(0)

    elif args.action == "windows":
        if not args.target:
            print("Error: --target (session) is required for 'windows' action.", file=sys.stderr)
            sys.exit(1)

        windows = manager.list_windows(args.target)
        if not windows:
            print(f"No windows found in session '{args.target}'.")
        else:
            print(f"--- Windows in '{args.target}' ---")
            for w in windows:
                active = "*" if w['active'] else " "
                print(f"{active} [{w['index']}] {w['name']}")
        sys.exit(0)

    elif args.action == "window": # new window
        if not args.target: # target session
            print("Error: --target (session) is required for 'window' action.", file=sys.stderr)
            sys.exit(1)

        success = manager.new_window(args.target, args.name, args.command_str)
        if success:
            print(f"✅ Created window in '{args.target}'")
        else:
            print(f"❌ Failed to create window in '{args.target}'.", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
