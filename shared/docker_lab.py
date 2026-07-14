import sys
import json
from typing import Optional, List, Dict
from shared.docker_manager import DockerManager

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

class DockerLabManager:
    def __init__(self):
        self.manager = DockerManager()
        if HAS_RICH:
            self.console = Console()
        else:
            self.console = None

    def list_containers(self):
        containers = self.manager.list_containers()
        if not containers:
            print("No containers found.")
            return

        if HAS_RICH:
            table = Table(title="Docker Containers")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Image", style="magenta")
            table.add_column("Command", style="green")
            table.add_column("Created", style="blue")
            table.add_column("Status", style="yellow")
            table.add_column("Ports", style="white")
            table.add_column("Names", style="bold white")

            for c in containers:
                table.add_row(
                    c.get("ID", "")[:12],
                    c.get("Image", ""),
                    c.get("Command", "")[:20] + "..." if len(c.get("Command", "")) > 20 else c.get("Command", ""),
                    c.get("CreatedAt", ""),
                    c.get("Status", ""),
                    c.get("Ports", ""),
                    c.get("Names", "")
                )
            self.console.print(table)
        else:
            # Fallback text output
            print(f"{'ID':<12} | {'Image':<20} | {'Status':<15} | {'Names'}")
            print("-" * 60)
            for c in containers:
                print(f"{c.get('ID', '')[:12]:<12} | {c.get('Image', '')[:20]:<20} | {c.get('Status', '')[:15]:<15} | {c.get('Names', '')}")

    def list_images(self):
        images = self.manager.list_images()
        if not images:
            print("No images found.")
            return

        if HAS_RICH:
            table = Table(title="Docker Images")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Repository", style="magenta")
            table.add_column("Tag", style="green")
            table.add_column("Created", style="blue")
            table.add_column("Size", style="yellow")

            for img in images:
                table.add_row(
                    img.get("ID", "")[:12],
                    img.get("Repository", ""),
                    img.get("Tag", ""),
                    img.get("CreatedAt", ""),
                    img.get("Size", "")
                )
            self.console.print(table)
        else:
            print(f"{'ID':<12} | {'Repository':<30} | {'Tag':<10} | {'Size'}")
            print("-" * 70)
            for img in images:
                print(f"{img.get('ID', '')[:12]:<12} | {img.get('Repository', '')[:30]:<30} | {img.get('Tag', '')[:10]:<10} | {img.get('Size', '')}")

    def inspect(self, container_id: str):
        data = self.manager.inspect_container(container_id)
        if not data:
            print(f"❌ Container '{container_id}' not found or error inspecting.")
            return

        if HAS_RICH:
            json_str = json.dumps(data, indent=2)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            self.console.print(Panel(syntax, title=f"Inspect: {container_id}", border_style="blue"))
        else:
            print(json.dumps(data, indent=2))

    def stats(self, container_id: str):
        data = self.manager.get_stats(container_id)
        if not data:
            print(f"❌ Could not get stats for '{container_id}'. Is it running?")
            return

        if HAS_RICH:
            table = Table(title=f"Stats: {container_id}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            # Map common stats fields
            fields = {
                "Name": "Name",
                "CPUPerc": "CPU %",
                "MemUsage": "Mem Usage",
                "MemPerc": "Mem %",
                "NetIO": "Net I/O",
                "BlockIO": "Block I/O",
                "PIDs": "PIDs"
            }

            for key, label in fields.items():
                if key in data:
                    table.add_row(label, str(data[key]))

            self.console.print(table)
        else:
            print(json.dumps(data, indent=2))

def run_docker_lab_logic(args):
    """
    CLI Entry point for Docker Lab.
    """
    if args.action == "tui":
        from main import run_tui
        print("Launching Docker Lab TUI...")
        run_tui(args, start_tab="tab-docker")
        return

    lab = DockerLabManager()

    if args.action in ["ps", "list"]:
        lab.list_containers()

    elif args.action == "images":
        lab.list_images()

    elif args.action == "start":
        if not args.container:
            print("Error: Container ID required.")
            sys.exit(1)
        if lab.manager.start_container(args.container):
            print(f"✅ Started container {args.container}")
        else:
            print(f"❌ Failed to start container {args.container}")
            sys.exit(1)

    elif args.action == "stop":
        if not args.container:
            print("Error: Container ID required.")
            sys.exit(1)
        if lab.manager.stop_container(args.container):
            print(f"✅ Stopped container {args.container}")
        else:
            print(f"❌ Failed to stop container {args.container}")
            sys.exit(1)

    elif args.action == "restart":
        if not args.container:
            print("Error: Container ID required.")
            sys.exit(1)
        if lab.manager.restart_container(args.container):
            print(f"✅ Restarted container {args.container}")
        else:
            print(f"❌ Failed to restart container {args.container}")
            sys.exit(1)

    elif args.action == "rm":
        if not args.container:
            print("Error: Container ID required.")
            sys.exit(1)
        if lab.manager.remove_container(args.container, force=args.force):
            print(f"✅ Removed container {args.container}")
        else:
            print(f"❌ Failed to remove container {args.container}")
            sys.exit(1)

    elif args.action == "rmi":
        if not args.image:
            print("Error: Image ID required.")
            sys.exit(1)
        if lab.manager.remove_image(args.image, force=args.force):
            print(f"✅ Removed image {args.image}")
        else:
            print(f"❌ Failed to remove image {args.image}")
            sys.exit(1)

    elif args.action == "prune":
        # Determine what to prune
        what = args.what or "all" # 'containers', 'images', 'all'

        if not args.force:
            confirm = input(f"Are you sure you want to prune {what} (stopped containers/unused images)? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                sys.exit(0)

        success = True
        if what in ["containers", "all"]:
            print("Pruning containers...")
            if lab.manager.prune_containers():
                print("✅ Pruned stopped containers.")
            else:
                print("❌ Failed to prune containers.")
                success = False

        if what in ["images", "all"]:
            print("Pruning images...")
            if lab.manager.prune_images():
                print("✅ Pruned unused images.")
            else:
                print("❌ Failed to prune images.")
                success = False

        if not success:
            sys.exit(1)

    elif args.action == "logs":
        if not args.container:
            print("Error: Container ID required.")
            sys.exit(1)
        print(f"--- Logs: {args.container} (Tail: {args.tail}) ---")
        print(lab.manager.get_logs(args.container, tail=args.tail))

    elif args.action == "inspect":
        if not args.container:
            print("Error: Container ID required.")
            sys.exit(1)
        lab.inspect(args.container)

    elif args.action == "stats":
        if not args.container:
            print("Error: Container ID required.")
            sys.exit(1)
        lab.stats(args.container)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
