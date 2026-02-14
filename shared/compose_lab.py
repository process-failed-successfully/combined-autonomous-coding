import subprocess
import sys
import json
from typing import List, Optional

try:
    from rich.console import Console
    from rich.table import Table
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

class ComposeLabManager:
    """Manages Docker Compose operations."""

    def __init__(self, project_dir: str = "."):
        self.project_dir = project_dir
        if HAS_RICH:
            self.console = Console()
        else:
            self.console = None

    def _run_compose(self, cmd_args: List[str], capture_output=True) -> subprocess.CompletedProcess:
        """Runs a docker compose command."""
        base_cmd = ["docker", "compose"]
        full_cmd = base_cmd + cmd_args

        # We run in the project directory where docker-compose.yml likely resides
        return subprocess.run(
            full_cmd,
            cwd=self.project_dir,
            capture_output=capture_output,
            text=True
        )

    def up(self, detached: bool = True, build: bool = False, services: Optional[List[str]] = None) -> bool:
        """Start services."""
        cmd = ["up"]
        if detached:
            cmd.append("-d")
        if build:
            cmd.append("--build")

        if services:
            cmd.extend(services)

        print(f"Starting services in {self.project_dir}...")
        result = self._run_compose(cmd, capture_output=False) # Stream output for 'up'
        return result.returncode == 0

    def down(self, volumes: bool = False, remove_orphans: bool = False) -> bool:
        """Stop and remove resources."""
        cmd = ["down"]
        if volumes:
            cmd.append("-v")
        if remove_orphans:
            cmd.append("--remove-orphans")

        print(f"Stopping services in {self.project_dir}...")
        result = self._run_compose(cmd, capture_output=False)
        return result.returncode == 0

    def ps(self, all: bool = False) -> None:
        """List containers."""
        cmd = ["ps", "--format", "json"]
        if all:
            cmd.append("-a")

        result = self._run_compose(cmd)

        if result.returncode != 0:
            print(f"Error listing containers: {result.stderr}")
            return

        try:
            # Try parsing as a single JSON object (list or dict)
            parsed = json.loads(result.stdout.strip())
            if isinstance(parsed, list):
                containers = parsed
            elif isinstance(parsed, dict):
                containers = [parsed]
            else:
                containers = []
        except json.JSONDecodeError:
            # Fallback: Try parsing as JSON lines (NDJSON)
            containers = []
            try:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        containers.append(json.loads(line))
            except json.JSONDecodeError:
                print("Error parsing Docker Compose output.")
                print(result.stdout)
                return

        if not containers:
            print("No containers found for this compose project.")
            return

        if HAS_RICH:
            table = Table(title=f"Compose Services ({self.project_dir})")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Service", style="magenta")
            table.add_column("State", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Ports", style="white")

            for c in containers:
                # Docker Compose V2 JSON format differs slightly depending on version
                # Typically: Name, Service, State, Status, Publishers (ports)
                name = c.get("Name", "")
                service = c.get("Service", "")
                state = c.get("State", "")
                status = c.get("Status", "")

                ports = c.get("Publishers", [])
                port_str = ""
                if ports:
                    port_list = []
                    for p in ports:
                        if isinstance(p, dict):
                            port_list.append(f"{p.get('PublishedPort')}:{p.get('TargetPort')}")
                    port_str = ", ".join(port_list)

                table.add_row(name, service, state, status, port_str)

            self.console.print(table)
        else:
             print(f"{'Name':<20} | {'Service':<15} | {'State':<10} | {'Status'}")
             print("-" * 60)
             for c in containers:
                 print(f"{c.get('Name',''):<20} | {c.get('Service',''):<15} | {c.get('State',''):<10} | {c.get('Status','')}")


    def logs(self, services: Optional[List[str]] = None, tail: int = 100, follow: bool = False) -> None:
        """View output from containers."""
        cmd = ["logs"]
        if follow:
            cmd.append("-f")
        else:
            cmd.append(f"--tail={tail}")

        if services:
            cmd.extend(services)

        # We don't capture output for logs, we stream it
        try:
            self._run_compose(cmd, capture_output=False)
        except KeyboardInterrupt:
            print("\nLogs stopped.")

    def stop(self, services: Optional[List[str]] = None) -> bool:
        """Stop services."""
        cmd = ["stop"]
        if services:
            cmd.extend(services)
        result = self._run_compose(cmd)
        if result.returncode == 0:
            print("✅ Services stopped.")
            return True
        else:
            print(f"❌ Error stopping services: {result.stderr}")
            return False

    def start(self, services: Optional[List[str]] = None) -> bool:
        """Start services."""
        cmd = ["start"]
        if services:
            cmd.extend(services)
        result = self._run_compose(cmd)
        if result.returncode == 0:
            print("✅ Services started.")
            return True
        else:
            print(f"❌ Error starting services: {result.stderr}")
            return False

    def restart(self, services: Optional[List[str]] = None) -> bool:
        """Restart services."""
        cmd = ["restart"]
        if services:
            cmd.extend(services)
        result = self._run_compose(cmd)
        if result.returncode == 0:
            print("✅ Services restarted.")
            return True
        else:
            print(f"❌ Error restarting services: {result.stderr}")
            return False

    def build(self, services: Optional[List[str]] = None, no_cache: bool = False) -> bool:
        """Build or rebuild services."""
        cmd = ["build"]
        if no_cache:
            cmd.append("--no-cache")
        if services:
            cmd.extend(services)

        result = self._run_compose(cmd, capture_output=False)
        return result.returncode == 0

    def pull(self, services: Optional[List[str]] = None) -> bool:
        """Pull service images."""
        cmd = ["pull"]
        if services:
            cmd.extend(services)
        result = self._run_compose(cmd, capture_output=False)
        return result.returncode == 0

    def exec(self, service: str, command: List[str]) -> None:
        """Execute a command in a running container."""
        cmd = ["exec", service] + command
        try:
            subprocess.run(["docker", "compose"] + cmd, cwd=self.project_dir, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error executing command: {e}")

def run_compose_lab_logic(args):
    """CLI Entry point for Compose Lab."""
    # Resolve project dir from args if available, or current dir
    project_dir = getattr(args, 'project_dir', ".")
    manager = ComposeLabManager(project_dir=str(project_dir))

    if args.action == "up":
        manager.up(detached=args.detach, build=args.build, services=args.services)

    elif args.action == "down":
        manager.down(volumes=args.volumes, remove_orphans=args.remove_orphans)

    elif args.action in ["ps", "list"]:
        manager.ps(all=args.all)

    elif args.action == "logs":
        manager.logs(services=args.services, tail=args.tail, follow=args.follow)

    elif args.action == "stop":
        manager.stop(services=args.services)

    elif args.action == "start":
        manager.start(services=args.services)

    elif args.action == "restart":
        manager.restart(services=args.services)

    elif args.action == "build":
        manager.build(services=args.services, no_cache=args.no_cache)

    elif args.action == "pull":
        manager.pull(services=args.services)

    elif args.action == "exec":
        if not args.service or not args.command_args:
            print("Error: Service and command are required.", file=sys.stderr)
            sys.exit(1)
        manager.exec(args.service, args.command_args)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
