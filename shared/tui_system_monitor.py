import psutil
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, DataTable, Button
from textual.containers import Container, Horizontal, Vertical

class SystemMonitorTab(Container):
    """Tab for monitoring system resources (CPU, RAM, Processes)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.timer = None

    def compose(self) -> ComposeResult:
        with Vertical():
            # Top Stats Row
            with Horizontal(classes="stat-box", id="sys-monitor-stats"):
                yield Label("CPU: [loading...]", id="lbl-cpu")
                yield Label("Memory: [loading...]", id="lbl-memory")
                yield Label("Disk: [loading...]", id="lbl-disk")
                yield Button("Refresh", id="btn-refresh-monitor", variant="default")

            # Process Table
            with Vertical(classes="stat-box", id="sys-monitor-procs"):
                yield Label("[bold]Top Processes (by CPU)[/bold]")
                yield DataTable(id="proc-table")

    def on_mount(self) -> None:
        # Init Table
        table = self.query_one("#proc-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("PID", "Name", "User", "CPU %", "Mem %")

        # Initial Update
        self.update_stats()

        # Start Timer (2s)
        self.timer = self.set_interval(2.0, self.update_stats)

    def on_unmount(self) -> None:
        if self.timer:
            self.timer.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-monitor":
            self.update_stats()

    def make_bar(self, percentage: float, width: int = 15) -> str:
        """Creates a simple ASCII progress bar."""
        # Clamp percentage 0-100
        percentage = max(0.0, min(100.0, percentage))
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)

        # Color coding
        color = "green"
        if percentage > 60: color = "yellow"
        if percentage > 85: color = "red"

        return f"[{color}]{bar}[/{color}] {percentage:.1f}%"

    def update_stats(self) -> None:
        # 1. System Stats
        try:
            # CPU
            cpu_pct = psutil.cpu_percent(interval=None)
            self.query_one("#lbl-cpu", Label).update(f"CPU: {self.make_bar(cpu_pct)}")

            # Memory
            mem = psutil.virtual_memory()
            self.query_one("#lbl-memory", Label).update(f"RAM: {self.make_bar(mem.percent)} ({self.bytes_to_human(mem.used)}/{self.bytes_to_human(mem.total)})")

            # Disk
            disk = psutil.disk_usage('/')
            self.query_one("#lbl-disk", Label).update(f"Disk (/): {self.make_bar(disk.percent)}")

        except Exception as e:
            self.notify(f"Error fetching stats: {e}", severity="error")

        # 2. Processes
        try:
            table = self.query_one("#proc-table", DataTable)

            # Fetch processes
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    # process_iter yields Process objects. calling info dict is safer.
                    # We accept that cpu_percent might be 0.0 on first call for some modes, but psutil handles interval=None by using last call time.
                    # Since we call this periodically, it should be fine.
                    procs.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            # Sort by CPU
            procs.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)

            # Update Table (Top 15)
            table.clear()
            for p in procs[:15]:
                pid = str(p['pid'])
                name = p['name']
                user = p['username'] or "?"
                cpu = f"{p['cpu_percent']:.1f}"
                mem = f"{p['memory_percent']:.1f}"

                table.add_row(pid, name, user, cpu, mem, key=pid)

        except Exception as e:
            self.notify(f"Error listing processes: {e}", severity="error")

    def bytes_to_human(self, n: int) -> str:
        symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = float(n) / prefix[s]
                return f"{value:.1f}{s}"
        return f"{n}B"
