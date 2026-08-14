import json
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Input, Button, Static, TabbedContent, TabPane, DataTable, RichLog, TextArea
from textual import on
from rich.syntax import Syntax

from shared.elastic_lab import ElasticLabManager


class ElasticLabTab(Container):
    """Tab for Elasticsearch operations."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = ElasticLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Elasticsearch Lab[/bold]", classes="welcome-text")

            # Connection Bar
            with Horizontal(id="elastic-conn-bar", classes="stat-box"):
                yield Label("URL:", classes="input-label")
                yield Input("http://localhost:9200", id="input-elastic-url", classes="input-wide")
                yield Button("Connect", id="btn-elastic-connect", variant="primary")
                yield Static("Not connected", id="lbl-elastic-status", classes="status-label")

            with TabbedContent(id="tabs-elastic"):
                # Info & Health Tab
                with TabPane("Info/Health", id="tab-elastic-info"):
                    with Horizontal():
                        yield Button("Get Cluster Info", id="btn-elastic-info", variant="success")
                        yield Button("Get Cluster Health", id="btn-elastic-health", variant="primary")
                    yield RichLog(id="log-elastic-info", wrap=True, highlight=True, markup=True)

                # Indices Tab
                with TabPane("Indices", id="tab-elastic-indices"):
                    yield Button("Refresh Indices", id="btn-elastic-refresh-indices", variant="primary")
                    yield DataTable(id="table-elastic-indices")

                # Search Tab
                with TabPane("Search", id="tab-elastic-search"):
                    yield Label("Index Name:")
                    yield Input(placeholder="e.g. my-index", id="input-elastic-index", classes="input-wide")
                    yield Label("Query (JSON string):")
                    yield TextArea(
                        '{"query": {"match_all": {}}}',
                        id="input-elastic-query",
                        language="json",
                        classes="input-wide"
                    )
                    yield Button("Search", id="btn-elastic-search", variant="success")
                    yield RichLog(id="log-elastic-search", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        # Setup DataTable for Indices
        dt = self.query_one("#table-elastic-indices", DataTable)
        dt.add_columns("Health", "Status", "Index", "Docs", "Size")

    @on(Button.Pressed, "#btn-elastic-connect")
    def on_connect_pressed(self, event: Button.Pressed) -> None:
        url = self.query_one("#input-elastic-url", Input).value.strip() or "http://localhost:9200"
        self.manager = ElasticLabManager(host=url)
        lbl = self.query_one("#lbl-elastic-status", Static)

        if self.manager.connect():
            lbl.update("[green]Connected[/green]")
            if hasattr(self.app, "notify"):
                self.app.notify("Connected to Elasticsearch")
        else:
            lbl.update("[red]Connection Failed[/red]")
            if hasattr(self.app, "notify"):
                self.app.notify("Failed to connect", severity="error")

    @on(Button.Pressed, "#btn-elastic-info")
    def on_info_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one("#log-elastic-info", RichLog)
        info = self.manager.info()

        if info:
            json_str = json.dumps(info, indent=2)
            log.write(Syntax(json_str, "json", theme="monokai", word_wrap=True))
        else:
            log.write("[red]Failed to get cluster info.[/red]")

    @on(Button.Pressed, "#btn-elastic-health")
    def on_health_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one("#log-elastic-info", RichLog)
        health = self.manager.health()

        if health:
            json_str = json.dumps(health, indent=2)
            log.write(Syntax(json_str, "json", theme="monokai", word_wrap=True))
        else:
            log.write("[red]Failed to get cluster health.[/red]")

    @on(Button.Pressed, "#btn-elastic-refresh-indices")
    def on_refresh_indices_pressed(self, event: Button.Pressed) -> None:
        dt = self.query_one("#table-elastic-indices", DataTable)
        dt.clear()

        indices = self.manager.indices()
        if indices:
            for idx in indices:
                dt.add_row(
                    idx.get("health", "?"),
                    idx.get("status", "?"),
                    idx.get("index", "?"),
                    idx.get("docs.count", "0"),
                    idx.get("store.size", "0b")
                )
        else:
            if hasattr(self.app, "notify"):
                self.app.notify("No indices found or failed to fetch indices.", severity="warning")

    @on(Button.Pressed, "#btn-elastic-search")
    def on_search_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one("#log-elastic-search", RichLog)
        index = self.query_one("#input-elastic-index", Input).value.strip()
        query = self.query_one("#input-elastic-query", TextArea).text.strip()

        if not index:
            log.write("[red]Error: Index name is required.[/red]")
            return

        result = self.manager.search(index, query)

        if result:
            json_str = json.dumps(result, indent=2)
            log.write(Syntax(json_str, "json", theme="monokai", word_wrap=True))
        else:
            log.write("[red]Search failed.[/red]")
