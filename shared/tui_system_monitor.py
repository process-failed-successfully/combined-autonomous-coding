import psutil
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, DataTable, ProgressBar


class SystemMonitorTab(Container):
    """Tab for monitoring system resources (CPU, Memory, Processes)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.interval = 2.0  # seconds

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]System Monitor[/bold]", classes="welcome-text")

            # Metrics
            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("CPU Usage")
                    yield ProgressBar(id="cpu-progress", total=100, show_eta=False)
                    yield Label("0%", id="cpu-label")

                with Vertical():
                    yield Label("Memory Usage")
                    yield ProgressBar(id="mem-progress", total=100, show_eta=False)
                    yield Label("0%", id="mem-label")

                with Vertical():
                    yield Label("Disk Usage")
                    yield ProgressBar(id="disk-progress", total=100, show_eta=False)
                    yield Label("0%", id="disk-label")

            # Process List
            with Container(classes="stat-box"):
                yield Label("[bold]Top Processes (by CPU)[/bold]")
                yield DataTable(id="proc-table")

    def on_mount(self) -> None:
        table = self.query_one("#proc-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("PID", "Name", "User", "CPU %", "Mem %")

        # Start update timer
        self.update_timer = self.set_interval(self.interval, self.update_stats)
        self.update_stats()

    def on_unmount(self) -> None:
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()

    def update_stats(self) -> None:
        # CPU
        cpu = psutil.cpu_percent()
        self.query_one("#cpu-progress", ProgressBar).progress = cpu
        self.query_one("#cpu-label", Label).update(f"{cpu:.1f}%")

        # Memory
        mem = psutil.virtual_memory()
        self.query_one("#mem-progress", ProgressBar).progress = mem.percent
        self.query_one("#mem-label", Label).update(f"{mem.percent:.1f}% ({self._bytes_to_human(mem.used)} / {self._bytes_to_human(mem.total)})")

        # Disk
        disk = psutil.disk_usage("/")
        self.query_one("#disk-progress", ProgressBar).progress = disk.percent
        self.query_one("#disk-label", Label).update(f"{disk.percent:.1f}%")

        # Processes
        table = self.query_one("#proc-table", DataTable)
        table.clear()

        procs = []
        # Fetch process info
        for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                # Force CPU percent calculation (requires interval or previous call)
                # We call it with interval=None (non-blocking)
                # Note: First call returns 0.0. Subsequent calls return avg since last call.
                p.info['cpu_percent'] = p.cpu_percent(interval=None)
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Sort by CPU
        procs.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)

        for p in procs[:15]:  # Top 15
            table.add_row(
                str(p['pid']),
                p['name'],
                p['username'] or "-",
                f"{p['cpu_percent']:.1f}",
                f"{p['memory_percent']:.1f}"
            )

    def _bytes_to_human(self, n):
        symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = float(n) / prefix[s]
                return f'{value:.1f}{s}'
        return f"{n}B"
