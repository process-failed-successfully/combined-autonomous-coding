from pathlib import Path
import psutil
from textual.app import ComposeResult
from textual.widgets import Label, DataTable, Sparkline, ProgressBar
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.timer import Timer

class SystemMonitorTab(Container):
    """Tab for monitoring system resources."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.cpu_history = [0.0] * 60
        self.memory_history = [0.0] * 60
        self.timer: Timer | None = None
        self.procs = {}  # Cache for process objects: {pid: Process}

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]System Monitor[/bold]", classes="welcome-text")

            # Gauges
            with Grid(id="monitor-gauges", classes="stat-box"):
                with Vertical():
                    yield Label("CPU Usage")
                    yield ProgressBar(id="pb-cpu", total=100, show_eta=False)
                    yield Label("0%", id="lbl-cpu-val")

                with Vertical():
                    yield Label("Memory Usage")
                    yield ProgressBar(id="pb-mem", total=100, show_eta=False)
                    yield Label("0%", id="lbl-mem-val")

                with Vertical():
                    yield Label("Disk Usage")
                    yield ProgressBar(id="pb-disk", total=100, show_eta=False)
                    yield Label("0%", id="lbl-disk-val")

            # History
            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("CPU History")
                    yield Sparkline(self.cpu_history, summary_function=max, id="spark-cpu")
                with Vertical():
                    yield Label("Memory History")
                    yield Sparkline(self.memory_history, summary_function=max, id="spark-mem")

            # Process Table
            with Vertical(classes="stat-box"):
                yield Label("[bold]Top Processes[/bold]")
                yield DataTable(id="proc-table")

    def on_mount(self) -> None:
        table = self.query_one("#proc-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("PID", "Name", "CPU %", "Memory %")

        # Initial update
        self.update_stats()

        # Start timer (1s)
        self.timer = self.set_interval(1.0, self.update_stats)

    def on_unmount(self) -> None:
        if self.timer:
            self.timer.stop()

    def update_stats(self) -> None:
        # CPU
        cpu_percent = psutil.cpu_percent()
        self.cpu_history.append(cpu_percent)
        self.cpu_history.pop(0)

        self.query_one("#pb-cpu", ProgressBar).update(total=100, progress=cpu_percent)
        self.query_one("#lbl-cpu-val", Label).update(f"{cpu_percent:.1f}%")
        self.query_one("#spark-cpu", Sparkline).data = self.cpu_history

        # Memory
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        self.memory_history.append(mem_percent)
        self.memory_history.pop(0)

        self.query_one("#pb-mem", ProgressBar).update(total=100, progress=mem_percent)
        self.query_one("#lbl-mem-val", Label).update(f"{mem_percent:.1f}% ({mem.used / (1024**3):.1f} GB / {mem.total / (1024**3):.1f} GB)")
        self.query_one("#spark-mem", Sparkline).data = self.memory_history

        # Disk (Project Dir)
        try:
            disk = psutil.disk_usage(str(self.project_dir.resolve()))
            self.query_one("#pb-disk", ProgressBar).update(total=100, progress=disk.percent)
            self.query_one("#lbl-disk-val", Label).update(f"{disk.percent:.1f}% ({disk.free / (1024**3):.1f} GB Free)")
        except Exception:
            self.query_one("#lbl-disk-val", Label).update("N/A")

        # Processes
        self.update_processes()

    def update_processes(self) -> None:
        table = self.query_one("#proc-table", DataTable)

        # Update process cache
        current_pids = []
        for p in psutil.process_iter(['pid']):
            try:
                pid = p.info['pid']
                current_pids.append(pid)
                if pid not in self.procs:
                    self.procs[pid] = p
                    # Initialize cpu_percent (returns 0.0 first time)
                    try:
                        p.cpu_percent()
                    except Exception:
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Remove dead processes
        for pid in list(self.procs.keys()):
            if pid not in current_pids:
                del self.procs[pid]

        # Get stats
        proc_stats = []
        for pid, p in self.procs.items():
            try:
                # Use oneshot for efficiency
                with p.oneshot():
                    cpu = p.cpu_percent()
                    mem = p.memory_percent()
                    name = p.name()
                    proc_stats.append({
                        'pid': pid,
                        'name': name,
                        'cpu': cpu,
                        'mem': mem
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Remove dead process
                if pid in self.procs:
                    del self.procs[pid]

        # Sort by CPU
        top_procs = sorted(proc_stats, key=lambda x: x['cpu'], reverse=True)[:5]

        table.clear()
        for p in top_procs:
            table.add_row(
                str(p['pid']),
                p['name'],
                f"{p['cpu']:.1f}",
                f"{p['mem']:.1f}"
            )
