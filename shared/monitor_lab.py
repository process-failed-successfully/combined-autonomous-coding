import psutil
import time
import sys
import os
import signal
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

class MonitorLabManager:
    """
    Manages system monitoring and process management.
    """

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Returns system statistics: CPU, Memory, Disk.
        """
        cpu_pct = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu": cpu_pct,
            "memory": {
                "percent": mem.percent,
                "used": mem.used,
                "total": mem.total,
                "free": mem.available
            },
            "disk": {
                "percent": disk.percent,
                "used": disk.used,
                "total": disk.total,
                "free": disk.free
            }
        }

    def get_processes(self, sort_by: str = "cpu", limit: int = 20, filter_pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Returns a list of running processes.
        """
        procs = []

        # 1. Collect Process objects
        process_objs = []
        for p in psutil.process_iter():
            try:
                # First call to cpu_percent to initialize
                p.cpu_percent()
                process_objs.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # 2. Wait for CPU interval
        time.sleep(0.1)

        # 3. Retrieve info
        for p in process_objs:
            try:
                with p.oneshot():
                    p_info = p.as_dict(attrs=['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status'])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

            if filter_pattern and filter_pattern.lower() not in p_info['name'].lower():
                continue

            procs.append(p_info)

        # Sort
        if sort_by == "cpu":
            procs.sort(key=lambda x: x.get('cpu_percent', 0.0), reverse=True)
        elif sort_by == "memory":
            procs.sort(key=lambda x: x.get('memory_percent', 0.0), reverse=True)
        elif sort_by == "pid":
            procs.sort(key=lambda x: x.get('pid', 0))
        elif sort_by == "name":
            procs.sort(key=lambda x: x.get('name', "").lower())

        return procs[:limit]

    def kill_process(self, pid: int, signal_type: int = signal.SIGTERM) -> bool:
        """
        Kills a process by PID.
        """
        try:
            p = psutil.Process(pid)
            p.send_signal(signal_type)
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"Error killing process {pid}: {e}", file=sys.stderr)
            return False

def _bytes_to_human(n: int) -> str:
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return f"{value:.1f}{s}"
    return f"{n}B"

def _make_bar(percentage: float, width: int = 20) -> str:
    # Simple ASCII bar for raw output if needed, but we use rich mostly
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return bar

def run_monitor_lab_logic(args):
    """
    CLI logic for Monitor Lab.
    """
    manager = MonitorLabManager()
    console = Console()

    if args.action == "stats":
        stats = manager.get_system_stats()

        # CPU
        cpu_color = "green"
        if stats['cpu'] > 60: cpu_color = "yellow"
        if stats['cpu'] > 85: cpu_color = "red"

        # Memory
        mem_pct = stats['memory']['percent']
        mem_color = "green"
        if mem_pct > 60: mem_color = "yellow"
        if mem_pct > 85: mem_color = "red"

        # Disk
        disk_pct = stats['disk']['percent']
        disk_color = "green"
        if disk_pct > 60: disk_color = "yellow"
        if disk_pct > 85: disk_color = "red"

        table = Table(title="System Statistics", box=None)
        table.add_column("Resource", style="bold cyan")
        table.add_column("Usage", style="bold")
        table.add_column("Details")

        table.add_row(
            "CPU",
            f"[{cpu_color}]{stats['cpu']:.1f}%[/{cpu_color}]",
            _make_bar(stats['cpu'])
        )
        table.add_row(
            "Memory",
            f"[{mem_color}]{mem_pct:.1f}%[/{mem_color}]",
            f"{_bytes_to_human(stats['memory']['used'])} / {_bytes_to_human(stats['memory']['total'])}"
        )
        table.add_row(
            "Disk",
            f"[{disk_color}]{disk_pct:.1f}%[/{disk_color}]",
            f"{_bytes_to_human(stats['disk']['used'])} / {_bytes_to_human(stats['disk']['total'])}"
        )

        console.print(table)

    elif args.action == "procs":
        procs = manager.get_processes(
            sort_by=args.sort,
            limit=args.limit,
            filter_pattern=args.filter
        )

        table = Table(title=f"Top Processes (by {args.sort})")
        table.add_column("PID", style="cyan", justify="right")
        table.add_column("Name", style="bold white")
        table.add_column("User", style="magenta")
        table.add_column("CPU %", justify="right")
        table.add_column("Mem %", justify="right")
        table.add_column("Status")

        for p in procs:
            cpu = p.get('cpu_percent', 0.0)
            mem = p.get('memory_percent', 0.0)

            cpu_style = "green"
            if cpu > 50: cpu_style = "yellow"
            if cpu > 80: cpu_style = "red"

            table.add_row(
                str(p['pid']),
                p['name'],
                p.get('username', '?'),
                f"[{cpu_style}]{cpu:.1f}[/{cpu_style}]",
                f"{mem:.1f}",
                p.get('status', '?')
            )

        console.print(table)

    elif args.action == "kill":
        if args.pid:
            pids = [args.pid]
        elif args.filter:
            procs = manager.get_processes(filter_pattern=args.filter, limit=100)
            if not procs:
                console.print(f"[yellow]No processes found matching '{args.filter}'.[/yellow]")
                sys.exit(0)

            table = Table(title=f"Processes matching '{args.filter}'")
            table.add_column("PID")
            table.add_column("Name")
            for p in procs:
                table.add_row(str(p['pid']), p['name'])
            console.print(table)

            confirm = input(f"Kill these {len(procs)} processes? [y/N]: ").lower().strip()
            if confirm != 'y':
                console.print("Aborted.")
                sys.exit(0)
            pids = [p['pid'] for p in procs]
        else:
            console.print("[red]Error: Must specify --pid or --filter.[/red]")
            sys.exit(1)

        for pid in pids:
            if manager.kill_process(pid):
                console.print(f"[green]Process {pid} killed.[/green]")
            else:
                console.print(f"[red]Failed to kill process {pid}.[/red]")

    elif args.action == "watch":
        try:
            with Live(console=console, screen=True, refresh_per_second=1) as live:
                while True:
                    # Generate layout
                    layout = Layout()
                    layout.split_column(
                        Layout(name="stats", size=6),
                        Layout(name="procs")
                    )

                    # Stats
                    stats = manager.get_system_stats()
                    stats_table = Table(box=None, expand=True)
                    stats_table.add_column("CPU")
                    stats_table.add_column("Memory")
                    stats_table.add_column("Disk")

                    cpu_bar = f"{stats['cpu']:.1f}% " + _make_bar(stats['cpu'], 10)
                    mem_bar = f"{stats['memory']['percent']:.1f}% " + _make_bar(stats['memory']['percent'], 10)
                    disk_bar = f"{stats['disk']['percent']:.1f}% " + _make_bar(stats['disk']['percent'], 10)

                    stats_table.add_row(cpu_bar, mem_bar, disk_bar)
                    layout["stats"].update(Panel(stats_table, title="System Stats"))

                    # Procs
                    procs = manager.get_processes(sort_by=args.sort or "cpu", limit=args.limit or 20, filter_pattern=args.filter)
                    proc_table = Table(expand=True, box=None)
                    proc_table.add_column("PID", justify="right", style="cyan")
                    proc_table.add_column("Name", style="white")
                    proc_table.add_column("User", style="magenta")
                    proc_table.add_column("CPU %", justify="right")
                    proc_table.add_column("Mem %", justify="right")

                    for p in procs:
                        cpu = p.get('cpu_percent', 0.0)
                        proc_table.add_row(
                            str(p['pid']),
                            p['name'],
                            p.get('username', '?'),
                            f"{cpu:.1f}",
                            f"{p.get('memory_percent', 0.0):.1f}"
                        )

                    layout["procs"].update(Panel(proc_table, title=f"Top Processes ({args.sort or 'cpu'})"))

                    live.update(layout)
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
