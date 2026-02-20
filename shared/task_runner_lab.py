import json
import re
import tomlkit
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Task:
    source: str
    name: str
    command: str
    file_path: str
    script_key: str = ""

class TaskRunnerManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def list_tasks(self) -> List[Task]:
        tasks = []
        tasks.extend(self._scan_makefile())
        tasks.extend(self._scan_package_json())
        tasks.extend(self._scan_pyproject_toml())
        return tasks

    def _scan_makefile(self) -> List[Task]:
        tasks = []
        makefile_path = self.project_dir / "Makefile"
        if not makefile_path.exists():
            return []

        try:
            content = makefile_path.read_text(encoding="utf-8", errors="replace")
            # Simple regex for targets like "target:" or "target: dependency"
            # Avoiding .PHONY targets if possible, but listing them is fine.
            matches = re.finditer(r"^([a-zA-Z0-9_-]+):", content, re.MULTILINE)
            for match in matches:
                target = match.group(1)
                if target != ".PHONY":
                    tasks.append(Task(
                        source="Makefile",
                        name=target,
                        command=f"make {target}",
                        file_path=str(makefile_path),
                        script_key=target
                    ))
        except Exception:
            pass
        return tasks

    def _scan_package_json(self) -> List[Task]:
        tasks = []
        # Check root and ui/ directory
        paths = [self.project_dir / "package.json", self.project_dir / "ui" / "package.json"]

        for path in paths:
            if not path.exists():
                continue

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    scripts = data.get("scripts", {})

                    # Determine runner (npm, yarn, pnpm)
                    runner = "npm"
                    if (path.parent / "yarn.lock").exists():
                        runner = "yarn"
                    elif (path.parent / "pnpm-lock.yaml").exists():
                        runner = "pnpm"

                    for name, cmd in scripts.items():
                        # If in subdirectory, we need to cd or use --prefix?
                        # Ideally we run from that directory.
                        # For display, we might want to qualify the name if it's not root.
                        display_name = name
                        if path.parent != self.project_dir:
                            display_name = f"{path.parent.name}:{name}"

                        # Actual execution command will need to handle CWD
                        tasks.append(Task(
                            source=f"{runner} ({path.parent.name})",
                            name=display_name,
                            command=cmd,
                            file_path=str(path),
                            script_key=name
                        ))
            except Exception:
                pass
        return tasks

    def _scan_pyproject_toml(self) -> List[Task]:
        tasks = []
        path = self.project_dir / "pyproject.toml"
        if not path.exists():
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = tomlkit.load(f)

            # Poetry Scripts
            tool = data.get("tool", {})
            if isinstance(tool, dict):
                poetry = tool.get("poetry", {})
                if isinstance(poetry, dict):
                    scripts = poetry.get("scripts", {})
                    if isinstance(scripts, dict):
                        for name, cmd in scripts.items():
                            tasks.append(Task(
                                source="poetry",
                                name=name,
                                command=f"poetry run {name}",
                                file_path=str(path),
                                script_key=name
                            ))

            # Standard project.scripts (PEP 621)
            # These are usually installed entry points, but can be treated as tasks if invoked via python -m
            # But let's stick to what's runnable in dev.

        except Exception:
            pass
        return tasks

    def run_task(self, task: Task, on_output=None) -> int:
        """
        Runs a task synchronously (blocking).
        For TUI, this should be wrapped in a thread.
        """
        cwd = Path(task.file_path).parent

        # Construct command
        cmd_to_run = task.command

        if "npm" in task.source or "yarn" in task.source or "pnpm" in task.source:
            # Determine runner from source string
            runner = task.source.split()[0]
            # Use script_key if available, else try parsing name (fallback)
            script_name = task.script_key if task.script_key else task.name.split(":")[-1]
            cmd_to_run = f"{runner} run {script_name}"

        elif task.source == "Makefile":
            # Command is already "make target"
            pass

        elif task.source == "poetry":
            # Command is already "poetry run name"
            pass

        try:
            process = subprocess.Popen(
                cmd_to_run,
                shell=True,  # nosec B602: Necessary for running user-defined tasks
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            if on_output:
                for line in process.stdout:
                    on_output(line.rstrip())

            process.wait()
            return process.returncode
        except Exception as e:
            if on_output:
                on_output(f"Error starting process: {e}")
            return -1
