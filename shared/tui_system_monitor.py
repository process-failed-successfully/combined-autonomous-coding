import psutil
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Digits, ProgressBar, DataTable

class SystemMonitorTab(Container):
    """Tab for monitoring system resources."""

    def __init__(self, project_dir=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self._procs_cache = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]System Monitor[/bold]", classes="welcome-text")

            # CPU & Memory Row
            with Horizontal(classes="stat-box"):
                with Vertical(classes="monitor-column"):
                    yield Label("CPU Usage")
                    yield Digits("0.0%", id="cpu-digits")
                    yield ProgressBar(total=100, show_eta=False, id="cpu-bar")

                with Vertical(classes="monitor-column"):
                    yield Label("Memory Usage")
                    yield Digits("0.0%", id="mem-digits")
                    yield ProgressBar(total=100, show_eta=False, id="mem-bar")
                    yield Label("", id="mem-details")

            # Disk & Network Row
            with Horizontal(classes="stat-box"):
                with Vertical(classes="monitor-column"):
                    yield Label("Disk Usage (Root)")
                    yield Digits("0.0%", id="disk-digits")
                    yield ProgressBar(total=100, show_eta=False, id="disk-bar")
                    yield Label("", id="disk-details")

                with Vertical(classes="monitor-column"):
                    yield Label("Network (Sent / Recv)")
                    yield Label("Sent: 0 B", id="net-sent")
                    yield Label("Recv: 0 B", id="net-recv")

            # Processes
            with Container(classes="stat-box"):
                yield Label("[bold]Top Processes (CPU)[/bold]")
                yield DataTable(id="proc-table")

    def on_mount(self) -> None:
        table = self.query_one("#proc-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("PID", "Name", "User", "CPU %", "Mem %", "Status")

        self.update_stats()
        self.set_interval(2.0, self.update_stats)

    def update_stats(self) -> None:
        # CPU
        cpu_pct = psutil.cpu_percent()
        self.query_one("#cpu-digits", Digits).update(f"{cpu_pct:.1f}%")
        self.query_one("#cpu-bar", ProgressBar).progress = cpu_pct

        # Memory
        mem = psutil.virtual_memory()
        self.query_one("#mem-digits", Digits).update(f"{mem.percent:.1f}%")
        self.query_one("#mem-bar", ProgressBar).progress = mem.percent
        self.query_one("#mem-details", Label).update(f"Used: {self._bytes2human(mem.used)} / Total: {self._bytes2human(mem.total)}")

        # Disk
        try:
            disk = psutil.disk_usage('/')
            self.query_one("#disk-digits", Digits).update(f"{disk.percent:.1f}%")
            self.query_one("#disk-bar", ProgressBar).progress = disk.percent
            self.query_one("#disk-details", Label).update(f"Free: {self._bytes2human(disk.free)} / Total: {self._bytes2human(disk.total)}")
        except Exception:
            pass

        # Network
        net = psutil.net_io_counters()
        self.query_one("#net-sent", Label).update(f"Sent: {self._bytes2human(net.bytes_sent)}")
        self.query_one("#net-recv", Label).update(f"Recv: {self._bytes2human(net.bytes_recv)}")

        # Processes
        self.update_processes()

    def update_processes(self) -> None:
        table = self.query_one("#proc-table", DataTable)

        current_pids = set()
        for p in psutil.process_iter():
            current_pids.add(p.pid)
            if p.pid not in self._procs_cache:
                self._procs_cache[p.pid] = p
                # Prime CPU counter
                try:
                    p.cpu_percent()
                except Exception:
                    pass

        # Remove dead
        for pid in list(self._procs_cache.keys()):
            if pid not in current_pids:
                del self._procs_cache[pid]

        # Collect info
        procs_info = []
        for pid, p in self._procs_cache.items():
            try:
                # Use oneshot for efficiency
                with p.oneshot():
                    cpu = p.cpu_percent()
                    mem = p.memory_percent()
                    info = {
                        'pid': pid,
                        'name': p.name(),
                        'username': p.username(),
                        'cpu': cpu,
                        'mem': mem,
                        'status': p.status()
                    }
                    procs_info.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except Exception:
                pass

        # Sort by CPU
        procs_info.sort(key=lambda x: x['cpu'], reverse=True)

        table.clear()
        for p in procs_info[:15]:
            table.add_row(
                str(p['pid']),
                p['name'],
                p['username'],
                f"{p['cpu']:.1f}",
                f"{p['mem']:.1f}",
                p['status']
            )

    def _bytes2human(self, n):
        # http://code.activestate.com/recipes/578019
        symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = float(n) / prefix[s]
                return '%.1f%s' % (value, s)
        return "%sB" % n
