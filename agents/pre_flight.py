import shutil
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.status import Status
import docker
from typing import List, Tuple

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

    def run_checks(self) -> bool:
        """Run all checks and return True if all pass."""
        checks: List[Tuple[str, callable]] = [
            ("Docker Daemon", self.check_docker),
            ("Docker Compose", self.check_docker_compose),
            ("Git Installed", self.check_git),
            ("Git Repository", self.check_git_repo),
        ]

        all_passed = True
        
        with self.console.status("[bold green]Running pre-flight checks...") as status:
            for name, check_func in checks:
                status.update(f"[bold green]Checking {name}...")
                if check_func():
                    self.console.print(f"[green]✓ {name} passed[/green]")
                else:
                    self.console.print(f"[red]✗ {name} failed[/red]")
                    all_passed = False
        
        return all_passed
