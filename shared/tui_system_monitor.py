import psutil
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, DataTable, Button, Static, Digits
from textual.reactive import reactive
from shared.charts import draw_ascii_bar_chart

class SystemMonitorTab(Container):
    """Tab for monitoring system resources."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.paused = False
        self.process_cache = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]System Monitor[/bold]", classes="welcome-text")

            # Stats Header
            with Horizontal(classes="stat-box"):
                with Vertical(classes="monitor-stat"):
                    yield Label("CPU Usage")
                    yield Digits("0.0", id="cpu-digits")
                    yield Static("", id="cpu-bar")

                with Vertical(classes="monitor-stat"):
                    yield Label("Memory Usage")
                    yield Digits("0.0", id="mem-digits")
                    yield Static("", id="mem-bar")

                with Vertical(classes="monitor-stat"):
                    yield Label("Disk Usage")
                    yield Digits("0.0", id="disk-digits")
                    yield Static("", id="disk-bar")

            # Process List
            with Vertical(classes="stat-box", id="process-container"):
                with Horizontal():
                    yield Label("[bold]Top Processes (CPU)[/bold]")
                    yield Button("Pause", id="btn-pause-monitor", variant="warning")

                yield DataTable(id="process-table")

    def on_mount(self) -> None:
        table = self.query_one("#process-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("PID", "Name", "User", "CPU %", "Mem %")

        # Start update loop
        self.set_interval(2.0, self.update_stats)
        self.update_stats()

    def update_stats(self) -> None:
        if self.paused:
            return

        # CPU
        cpu_pct = psutil.cpu_percent()
        self.query_one("#cpu-digits", Digits).update(f"{cpu_pct:.1f}")
        self.query_one("#cpu-bar", Static).update(draw_ascii_bar_chart({"CPU": cpu_pct}, "", width=20))

        # Memory
        mem = psutil.virtual_memory()
        self.query_one("#mem-digits", Digits).update(f"{mem.percent:.1f}")
        self.query_one("#mem-bar", Static).update(draw_ascii_bar_chart({"Mem": mem.percent}, "", width=20))

        # Disk
        disk = psutil.disk_usage('/')
        self.query_one("#disk-digits", Digits).update(f"{disk.percent:.1f}")
        self.query_one("#disk-bar", Static).update(draw_ascii_bar_chart({"Disk": disk.percent}, "", width=20))

        # Processes
        self.update_processes()

    def update_processes(self) -> None:
        table = self.query_one("#process-table", DataTable)
        table.clear()

        current_procs = {}
        for p in psutil.process_iter():
            current_procs[p.pid] = p

        # Prune dead processes from cache
        self.process_cache = {pid: proc for pid, proc in self.process_cache.items() if pid in current_procs}

        procs_data = []
        for pid, p in current_procs.items():
            # Use cached object if available to ensure cpu_percent works (needs delta)
            if pid in self.process_cache:
                proc_obj = self.process_cache[pid]
            else:
                proc_obj = p
                self.process_cache[pid] = p
                try:
                    proc_obj.cpu_percent() # Initialize state
                except Exception:
                    pass

            try:
                with proc_obj.oneshot():
                    cpu = proc_obj.cpu_percent()
                    name = proc_obj.name()
                    username = proc_obj.username()
                    mem = proc_obj.memory_percent()

                procs_data.append({
                    'pid': pid,
                    'name': name,
                    'username': username,
                    'cpu_percent': cpu,
                    'memory_percent': mem
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Sort by CPU
        procs_data.sort(key=lambda x: x['cpu_percent'], reverse=True)

        for p in procs_data[:15]:
            table.add_row(
                str(p['pid']),
                p['name'],
                p['username'] or "N/A",
                f"{p['cpu_percent']:.1f}",
                f"{p['memory_percent']:.1f}"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pause-monitor":
            self.paused = not self.paused
            event.button.label = "Resume" if self.paused else "Pause"
            event.button.variant = "success" if self.paused else "warning"
