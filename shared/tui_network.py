import asyncio
from pathlib import Path
from typing import Dict, Any, List

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, ListView, ListItem, Input, Button, DataTable, RichLog, Static
from textual import on

from shared.network import NetworkBuilder

class NetworkTab(Container):
    """Tab for visualizing codebase network (Imports & Authors)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.nodes = {}
        self.edges = []
        self.adj_in = {}
        self.adj_out = {}

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Node List
            with Vertical(id="net-list-container", classes="stat-box"):
                yield Label("[bold]Nodes (Files & Authors)[/bold]")
                yield Input(placeholder="Filter nodes...", id="net-filter")
                yield ListView(id="net-node-list")
                yield Button("Refresh", id="btn-net-refresh", variant="default")

            # Right Pane: Details
            with Vertical(id="net-details-container"):
                yield Label("[bold]Node Details[/bold]")
                yield Label("Select a node to view details.", id="net-header")

                with Horizontal():
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Outgoing (Imports / Edits)[/bold]")
                        yield ListView(id="net-out-list")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Incoming (Used By / Edited By)[/bold]")
                        yield ListView(id="net-in-list")

    def on_mount(self) -> None:
        self.load_graph()

    def load_graph(self) -> None:
        self.notify("Building network graph...")
        # Run in background
        asyncio.create_task(self._build_graph())

    async def _build_graph(self) -> None:
        builder = NetworkBuilder(self.project_dir)

        try:
            # We need to run this in thread because it uses subprocess (git) and IO
            def do_work():
                map_data = builder.add_file_nodes()
                builder.add_import_edges(map_data)
                builder.add_git_history(limit=50, include_authors=True)
                return builder

            await asyncio.to_thread(do_work)

            self.nodes = builder.nodes
            self.edges = builder.edges
            self._process_graph()
            self._update_list()
            self.notify("Graph built successfully.")

        except Exception as e:
            self.notify(f"Error building graph: {e}", severity="error")

    def _process_graph(self) -> None:
        self.adj_in = {nid: [] for nid in self.nodes}
        self.adj_out = {nid: [] for nid in self.nodes}

        for edge in self.edges:
            src = edge["from"]
            dst = edge["to"]

            if src in self.nodes and dst in self.nodes:
                self.adj_out[src].append(edge)
                self.adj_in[dst].append(edge)

    def _update_list(self, filter_text: str = "") -> None:
        list_view = self.query_one("#net-node-list", ListView)
        list_view.clear()

        # Sort nodes by group then label
        sorted_nodes = sorted(self.nodes.values(), key=lambda x: (x.get("group", ""), x.get("label", "")))

        for node in sorted_nodes:
            label = node["label"]
            group = node.get("group", "file")

            if filter_text and filter_text.lower() not in label.lower():
                continue

            icon = "📄" if group == "file" else "👤" if group == "author" else "❓"
            display = f"{icon} {label}"

            item = ListItem(Label(display))
            item.node_id = node["id"] # Store ID
            list_view.append(item)

    @on(Input.Changed, "#net-filter")
    def on_filter(self, event: Input.Changed) -> None:
        self._update_list(event.value)

    @on(Button.Pressed, "#btn-net-refresh")
    def on_refresh(self) -> None:
        self.load_graph()

    @on(ListView.Selected, "#net-node-list")
    def on_node_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "node_id"):
            self.show_details(event.item.node_id)

    def show_details(self, node_id: str) -> None:
        node = self.nodes.get(node_id)
        if not node:
            return

        header = self.query_one("#net-header", Label)
        group = node.get("group", "file").capitalize()
        header.update(f"[bold]{group}: {node['label']}[/bold]")

        # Outgoing
        out_list = self.query_one("#net-out-list", ListView)
        out_list.clear()

        for edge in self.adj_out.get(node_id, []):
            target_id = edge["to"]
            target = self.nodes.get(target_id)
            if target:
                icon = "📄" if target.get("group") == "file" else "👤"
                rel = edge.get("title", "connects to")
                # Format: "connects to -> 📄 target.py"
                out_list.append(ListItem(Label(f"{rel} -> {icon} {target['label']}")))

        # Incoming
        in_list = self.query_one("#net-in-list", ListView)
        in_list.clear()

        for edge in self.adj_in.get(node_id, []):
            src_id = edge["from"]
            src = self.nodes.get(src_id)
            if src:
                icon = "📄" if src.get("group") == "file" else "👤"
                rel = edge.get("title", "connects from")
                # Format: "📄 source.py -> connects from"
                in_list.append(ListItem(Label(f"{icon} {src['label']} -> {rel}")))
