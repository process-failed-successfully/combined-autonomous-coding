import shutil
import os
import subprocess
from pathlib import Path
from rich.console import Console
import docker
from typing import List, Tuple, Callable
import platformdirs

console = Console()


class PreFlightCheck:
    def __init__(self):
        self.console = console

    def check_docker(self) -> bool:
        """Check if Docker is running and available."""
        try:
            client = docker.from_env()
            client.ping()
            return True
        except docker.errors.DockerException as e:
            self.console.print(f"[dim red]Docker Error: {str(e)}[/dim red]")
            return False
        except Exception as e:
            self.console.print(f"[dim red]Unexpected Docker Error: {str(e)}[/dim red]")
            return False

    def check_docker_compose(self) -> bool:
        """Check if docker-compose is installed."""
        return shutil.which("docker-compose") is not None

    def check_git(self) -> bool:
        """Check if git is installed."""
        return shutil.which("git") is not None

    def check_git_repo(self) -> bool:
        """Check if current directory is a git repo."""
        return os.path.isdir(".git")

    def check_workspace_clean(self) -> bool:
        """Check if git workspace is clean (warns but doesn't fail)."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                self.console.print("[yellow]! Workspace has uncommitted changes[/yellow]")
                # We return True because we don't want to block execution, just warn
                return True
            return True
        except Exception:
            return False  # Git error

    def check_and_fix_directories(self) -> bool:
        """Check and create necessary directories."""
        dirs = [
            Path(platformdirs.user_data_dir("combined-autonomous-coding")) / "sessions",
            Path(platformdirs.user_log_dir("combined-autonomous-coding"))
        ]

        for d in dirs:
            try:
                if not d.exists():
                    d.mkdir(parents=True, exist_ok=True)
                    self.console.print(f"[dim]Created directory: {d}[/dim]")

                # Check write permissions
                test_file = d / ".test_write"
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                self.console.print(f"[red]Directory error {d}: {e}[/red]")
                return False
        return True

    def run_checks(self) -> bool:
        """Run all checks and return True if all pass."""
        checks: List[Tuple[str, Callable[[], bool]]] = [
            ("Docker Daemon", self.check_docker),
            ("Docker Compose", self.check_docker_compose),
            ("Git Installed", self.check_git),
            ("Git Repository", self.check_git_repo),
            ("Workspace Clean", self.check_workspace_clean),
            ("Directories", self.check_and_fix_directories),
        ]

        all_passed = True

        with self.console.status("[bold green]Running pre-flight checks...") as status:
            for name, check_func in checks:
                status.update(f"[bold green]Checking {name}...")
                if check_func():
                    self.console.print(f"[green]✓ {name} passed[/green]")
                else:
                    self.console.print(f"[red]✗ {name} failed[/red]")
                    if name in ["Docker Daemon", "Docker Compose", "Git Installed"]:
                        all_passed = False
                    # Workspace clean and directories might not be critical blocks depending on policy
                    # But for now let's assume Directory fail is critical, Workspace is not (it returns True anyway)
                    if name == "Directories":
                        all_passed = False

        return all_passed
