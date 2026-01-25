import os
import sys
import shutil
import json
import subprocess
from pathlib import Path
from typing import Tuple, Optional, List

class ServeManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def detect_config(self) -> Tuple[List[str], int]:
        """
        Detects the start command and default port based on project files.
        Returns: (command_list, port)
        """
        # 1. Node.js
        if (self.project_dir / "package.json").exists():
            return self._detect_node()

        # 2. Python
        if (self.project_dir / "requirements.txt").exists() or \
           (self.project_dir / "pyproject.toml").exists() or \
           (self.project_dir / "app.py").exists() or \
           (self.project_dir / "main.py").exists() or \
           (self.project_dir / "manage.py").exists():
            return self._detect_python()

        # 3. Go
        if (self.project_dir / "go.mod").exists():
            return ["go", "run", "."], 8080

        # 4. Static
        if (self.project_dir / "index.html").exists():
            return [sys.executable, "-m", "http.server"], 8000

        # Fallback
        return [], 0

    def _detect_node(self) -> Tuple[List[str], int]:
        pkg_manager = "npm"
        if shutil.which("pnpm") and (self.project_dir / "pnpm-lock.yaml").exists():
            pkg_manager = "pnpm"
        elif shutil.which("yarn") and (self.project_dir / "yarn.lock").exists():
            pkg_manager = "yarn"

        try:
            with open(self.project_dir / "package.json") as f:
                data = json.load(f)
                scripts = data.get("scripts", {})
                if "dev" in scripts:
                    return [pkg_manager, "run", "dev"], 3000
                if "start" in scripts:
                    return [pkg_manager, "start"], 3000
        except Exception:
            pass

        # Fallback if no scripts found or error
        return [pkg_manager, "start"], 3000

    def _detect_python(self) -> Tuple[List[str], int]:
        # Django
        if (self.project_dir / "manage.py").exists():
            return [sys.executable, "manage.py", "runserver"], 8000

        # Read requirements if available for heuristics
        reqs = ""
        if (self.project_dir / "requirements.txt").exists():
            try:
                reqs = (self.project_dir / "requirements.txt").read_text()
            except Exception:
                pass

        # FastAPI
        if "fastapi" in reqs or "uvicorn" in reqs:
            # Try to find app file
            if (self.project_dir / "main.py").exists():
                return ["uvicorn", "main:app", "--reload"], 8000
            if (self.project_dir / "app.py").exists():
                return ["uvicorn", "app:app", "--reload"], 8000

        # Flask
        if "flask" in reqs:
            return ["flask", "run"], 5000

        # Generic
        if (self.project_dir / "main.py").exists():
            return [sys.executable, "main.py"], 8000
        if (self.project_dir / "app.py").exists():
            return [sys.executable, "app.py"], 8000

        return [sys.executable, "-m", "http.server"], 8000

    def start(self, port: Optional[int] = None, host: str = "127.0.0.1", command: Optional[str] = None, dry_run: bool = False) -> bool:
        if command:
            import shlex
            cmd_list = shlex.split(command)
            target_port = port or 8000 # Fallback if manual command
        else:
            cmd_list, detected_port = self.detect_config()
            target_port = port or detected_port

        if not cmd_list:
            print("❌ Could not detect a valid start command for this project.")
            return False

        # Apply port override if supported by the command (heuristics)
        # This is tricky because different tools use different flags.
        # We'll just print info about the expected port.

        # For http.server, we can append port
        if cmd_list == [sys.executable, "-m", "http.server"]:
            cmd_list.append(str(target_port))
            cmd_list.extend(["-b", host])

        # For Django
        elif "manage.py" in cmd_list and "runserver" in cmd_list:
             # replace 8000 with target
             cmd_list.append(f"{host}:{target_port}")

        # For Uvicorn
        elif "uvicorn" in cmd_list[0]:
             cmd_list.extend(["--port", str(target_port), "--host", host])

        # For Flask
        elif "flask" in cmd_list[0]:
             cmd_list.extend(["--port", str(target_port), "--host", host])

        # Node usually passes port via env PORT=...
        env = os.environ.copy()
        env["PORT"] = str(target_port)
        env["HOST"] = host

        print(f"--- Starting Server ---")
        print(f"Command: {' '.join(cmd_list)}")
        print(f"Port: {target_port}")
        print(f"Host: {host}")

        if dry_run:
            return True

        try:
            # We use Popen to let it run. In a CLI tool we typically wait, but 'serve' blocks.
            process = subprocess.Popen(cmd_list, cwd=self.project_dir, env=env) # nosec
            process.wait()
        except KeyboardInterrupt:
            print("\nStopped by user.")
            if 'process' in locals():
                process.terminate()
        except FileNotFoundError:
             print(f"❌ Command not found: {cmd_list[0]}")
             return False
        except Exception as e:
             print(f"❌ Error: {e}")
             return False

        return True
