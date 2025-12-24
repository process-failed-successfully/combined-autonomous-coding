import os
import json
import time
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import platformdirs
import psutil
from rich.console import Console

console = Console()


class SessionManager:
    def __init__(self):
        self.data_dir = Path(platformdirs.user_data_dir("combined-autonomous-coding")) / "sessions"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir = Path(platformdirs.user_log_dir("combined-autonomous-coding"))
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, name: str) -> Path:
        return self.data_dir / f"{name}.json"

    def list_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                # Check if process is still running
                pid = data.get("pid")
                if pid and not self._is_process_running(pid):
                    data["status"] = "dead"
                else:
                    data["status"] = "running"

                sessions.append(data)
            except Exception:
                continue
        return sessions

    def _is_process_running(self, pid: int) -> bool:
        if not psutil.pid_exists(pid):
            return False
        try:
            p = psutil.Process(pid)
            if p.status() == psutil.STATUS_ZOMBIE:
                return False
            return True
        except psutil.NoSuchProcess:
            return False

    def start_session(self, name: str, command: List[str], detached: bool = False):
        if self._get_session_path(name).exists():
            # Check if it's actually running
            with open(self._get_session_path(name), "r") as f:
                existing = json.load(f)
            if self._is_process_running(existing["pid"]):
                raise ValueError(f"Session '{name}' is already running.")
            else:
                # Cleanup dead session
                self._get_session_path(name).unlink()

        log_file = self.logs_dir / f"{name}.log"

        # Prepare environment
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        if detached:
            # Open log file for writing
            with open(log_file, "w") as f_out:
                process = subprocess.Popen(
                    command,
                    stdout=f_out,
                    stderr=subprocess.STDOUT,
                    env=env,
                    start_new_session=True  # Detach from terminal
                )

            session_data = {
                "name": name,
                "pid": process.pid,
                "start_time": time.time(),
                "command": command,
                "log_file": str(log_file),
                "type": "detached"
            }

            with open(self._get_session_path(name), "w") as f:
                json.dump(session_data, f)

            return session_data
        else:
            # Interactive mode - Stream to console
            # We don't save session state for interactive runs unless requested,
            # but usually interactive runs are blocking.
            try:
                process_interactive = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=env,
                    text=True,
                    bufsize=1
                )

                # Stream output
                assert process_interactive.stdout is not None
                for line in process_interactive.stdout:
                    print(line, end="")

                process_interactive.wait()
                return process_interactive.returncode
            except KeyboardInterrupt:
                process_interactive.terminate()
                return 1

    def stop_session(self, name: str):
        path = self._get_session_path(name)
        if not path.exists():
            return False, "Session not found"

        with open(path, "r") as f:
            data = json.load(f)

        pid = data.get("pid")
        msg = "Session file removed (was dead)"

        if self._is_process_running(pid):
            try:
                p = psutil.Process(pid)
                p.terminate()
                try:
                    p.wait(timeout=5)
                except psutil.TimeoutExpired:
                    p.kill()
                    p.wait(timeout=2)
                msg = "Stopped"
            except Exception as e:
                if self._is_process_running(pid):
                    return False, str(e)

        # Cleanup file
        if path.exists():
            path.unlink()
        return True, msg

    def get_log_path(self, name: str) -> Optional[Path]:
        path = self._get_session_path(name)
        if not path.exists():
            return None
        with open(path, "r") as f:
            data = json.load(f)
        return Path(data["log_file"])
