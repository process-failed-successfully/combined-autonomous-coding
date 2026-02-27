import sys
import os
import subprocess
import threading
import select
import time
from pathlib import Path
from typing import Optional, Callable

# pty is only available on Unix
try:
    import pty
    import termios
    import struct
    import fcntl
    HAS_PTY = True
except ImportError:
    HAS_PTY = False

class ShellLabManager:
    """
    Manages a persistent shell session using pty (pseudo-terminal).
    """

    def __init__(self, project_dir: Path = Path("."), shell: str = "/bin/bash"):
        self.project_dir = project_dir
        self.shell = shell or os.environ.get("SHELL", "/bin/bash")
        self.master_fd = None
        self.process = None
        self.thread = None
        self.running = False
        self.on_output = None

    def start_shell(self, on_output: Callable[[str], None]) -> None:
        """
        Starts the shell process.
        """
        if not HAS_PTY:
            raise RuntimeError("Shell Lab requires a Unix-like environment (pty support).")

        self.on_output = on_output

        # Fork the process
        pid, fd = pty.fork()

        if pid == 0:
            # Child process
            try:
                os.chdir(str(self.project_dir))
                # Execute the shell
                os.execlp(self.shell, self.shell)
            except Exception as e:
                print(f"Error starting shell: {e}")
                sys.exit(1)
        else:
            # Parent process
            self.master_fd = fd
            self.running = True
            self.process = pid  # Store PID to wait later if needed (though pty handles wait differently)

            # Start reader thread
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()

    def _read_loop(self):
        """
        Reads from the master file descriptor and invokes the callback.
        """
        try:
            while self.running:
                # Use select to wait for data with a timeout to allow checking self.running
                r, _, _ = select.select([self.master_fd], [], [], 0.1)
                if self.master_fd in r:
                    data = os.read(self.master_fd, 1024)
                    if not data:
                        break # EOF

                    if self.on_output:
                        # Decode bytes to string (replace errors to be safe)
                        text = data.decode("utf-8", errors="replace")
                        self.on_output(text)
        except OSError:
            pass # FD probably closed
        finally:
            self.running = False

    def write(self, data: str) -> None:
        """
        Writes data to the shell (stdin).
        """
        if self.master_fd and self.running:
            os.write(self.master_fd, data.encode("utf-8"))

    def resize(self, rows: int, cols: int) -> None:
        """
        Resizes the terminal window.
        """
        if self.master_fd and self.running:
            try:
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
            except Exception:
                pass

    def close(self) -> None:
        """
        Terminates the shell.
        """
        self.running = False
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None

        # We could also kill the process explicitly if needed
        # but closing the master fd usually signals SIGHUP/EOF to the shell

def run_shell_lab_logic(args):
    """
    CLI Handler for Shell Lab (interactive mode).
    """
    if hasattr(args, "tui") and args.tui:
        from shared.tui import AgentTUI
        print("Launching Shell Lab TUI...")
        root = Path(args.project_dir).resolve() if getattr(args, 'project_dir', None) else Path.cwd()
        app = AgentTUI(project_dir=root, start_tab="tab-shell-lab")
        app.run()
        return

    print("Shell Lab CLI mode requires TUI for full experience.")
    print("Use --tui or run via the main TUI interface.")
    sys.exit(0)
