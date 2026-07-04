from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Static, RichLog, TabbedContent, TabPane, DataTable
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.memcached_lab import MemcachedLabManager


class MemcachedLabTab(Container):
    """Tab for Memcached operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = MemcachedLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Memcached Lab[/bold]", classes="welcome-text")

            # Connection Bar
            with Horizontal(id="memcached-conn-bar", classes="stat-box"):
                yield Label("Host:", classes="label-inline")
                yield Input("localhost", id="input-memcached-host", classes="input-small")
                yield Label("Port:", classes="label-inline")
                yield Input("11211", id="input-memcached-port", type="integer", classes="input-small")
                yield Button("Connect", id="btn-memcached-connect", variant="primary")
                yield Static("Not connected", id="lbl-memcached-status", classes="status-label")

            with TabbedContent(id="tabs-memcached"):
                # Basic Ops Tab
                with TabPane("Operations"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Input(placeholder="Key...", id="input-memcached-key", classes="input-wide")
                            yield Button("GET", id="btn-memcached-get", variant="success")
                            yield Button("DEL", id="btn-memcached-del", variant="error")

                        with Horizontal():
                            yield Input(placeholder="Value...", id="input-memcached-value", classes="input-wide")
                            yield Label("TTL:", classes="label-inline")
                            yield Input("0", id="input-memcached-ex", type="integer", classes="input-small")
                            yield Button("SET", id="btn-memcached-set", variant="warning")

                        with Horizontal():
                            yield Button("Flush DB", id="btn-memcached-flush", variant="error")

                        yield Label("[bold]Output:[/bold]")
                        yield RichLog(id="log-memcached-ops", wrap=True, highlight=True, markup=True)

                # Stats Tab
                with TabPane("Stats"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Button("Refresh Stats", id="btn-memcached-stats", variant="primary")

                        yield DataTable(id="table-memcached-stats")

    def on_mount(self) -> None:
        # Configure DataTable
        dt = self.query_one("#table-memcached-stats", DataTable)
        dt.add_column("Key", width=30)
        dt.add_column("Value")

    def _update_manager(self) -> None:
        """Updates the manager config from inputs."""
        host = self.query_one("#input-memcached-host", Input).value.strip() or "localhost"
        port_val = self.query_one("#input-memcached-port", Input).value.strip()
        port = int(port_val) if port_val.isdigit() else 11211

        # Only recreate if changed
        if not self.manager or self.manager.host != host or self.manager.port != port:
             self.manager = MemcachedLabManager(host=host, port=port)

    @on(Button.Pressed, "#btn-memcached-connect")
    def on_connect(self) -> None:
        self._update_manager()
        lbl = self.query_one("#lbl-memcached-status", Static)
        if self.manager.connect():
            lbl.update("[bold green]✅ Connected[/bold green]")
            self.notify("Connected to Memcached")
        else:
            lbl.update("[bold red]❌ Connection Failed[/bold red]")
            self.notify("Connection failed. See stderr for details.", severity="error")

    @on(Button.Pressed, "#btn-memcached-get")
    def on_get(self) -> None:
        self._update_manager()
        key = self.query_one("#input-memcached-key", Input).value.strip()
        log = self.query_one("#log-memcached-ops", RichLog)

        if not key:
            self.notify("Key required.", severity="warning")
            return

        val = self.manager.get(key)
        if val is not None:
            log.write(f"[green]GET {key}[/green] -> {val}")
        else:
            log.write(f"[yellow]GET {key}[/yellow] -> (nil)")

    @on(Button.Pressed, "#btn-memcached-set")
    def on_set(self) -> None:
        self._update_manager()
        key = self.query_one("#input-memcached-key", Input).value.strip()
        val = self.query_one("#input-memcached-value", Input).value.strip()
        ex_val = self.query_one("#input-memcached-ex", Input).value.strip()
        log = self.query_one("#log-memcached-ops", RichLog)

        if not key or not val:
            self.notify("Key and Value required.", severity="warning")
            return

        ex = int(ex_val) if ex_val.isdigit() else 0

        if self.manager.set(key, val, ex=ex):
            log.write(f"[green]SET {key}[/green] -> STORED")
        else:
            log.write(f"[red]SET {key}[/red] -> NOT_STORED")

    @on(Button.Pressed, "#btn-memcached-del")
    def on_del(self) -> None:
        self._update_manager()
        key = self.query_one("#input-memcached-key", Input).value.strip()
        log = self.query_one("#log-memcached-ops", RichLog)

        if not key:
            self.notify("Key required.", severity="warning")
            return

        if self.manager.delete(key):
            log.write(f"[green]DEL {key}[/green] -> DELETED")
        else:
             log.write(f"[yellow]DEL {key}[/yellow] -> NOT_FOUND/ERROR")

    @on(Button.Pressed, "#btn-memcached-flush")
    def on_flush(self) -> None:
        self._update_manager()
        log = self.query_one("#log-memcached-ops", RichLog)

        if self.manager.flush():
            log.write("[green]FLUSH[/green] -> OK")
            self.notify("Database flushed.")
        else:
            log.write("[red]FLUSH[/red] -> FAILED")

    @on(Button.Pressed, "#btn-memcached-stats")
    def on_stats(self) -> None:
        self._update_manager()
        dt = self.query_one("#table-memcached-stats", DataTable)
        dt.clear()

        stats = self.manager.stats()
        if not stats:
            self.notify("Failed to get stats or not connected.", severity="error")
            return

        for k, v in sorted(stats.items()):
            dt.add_row(k, v)
        self.notify("Stats refreshed.")
