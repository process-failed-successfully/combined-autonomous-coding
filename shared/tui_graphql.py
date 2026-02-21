from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, Input, TextArea, RichLog, Tree, TabbedContent, TabPane
from textual import on
from rich.syntax import Syntax
import json
import asyncio

from shared.graphql_lab import GraphQLLabManager

class GraphQLLabTab(Container):
    """Tab for GraphQL interaction."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Config & Schema
            with Vertical(id="graphql-left-pane", classes="stat-box"):
                yield Label("[bold]Configuration[/bold]")
                yield Label("Endpoint URL:")
                yield Input(placeholder="https://api.example.com/graphql", id="graphql-url")
                yield Label("Headers (Key:Value, ...):")
                yield Input(placeholder="Authorization: Bearer token", id="graphql-headers")

                yield Button("Introspect Schema", id="btn-graphql-introspect", variant="warning")

                yield Label("[bold]Schema Explorer[/bold]")
                yield Tree("Schema", id="graphql-schema-tree")

            # Right Pane: Query & Response
            with Vertical(id="graphql-right-pane"):
                with TabbedContent():
                    with TabPane("Query"):
                        with Vertical(classes="stat-box"):
                            yield Label("Operation (Query/Mutation):")
                            # Text Area for Query
                            yield TextArea(id="graphql-query-editor", language="graphql", show_line_numbers=True)

                            yield Label("Variables (JSON):")
                            yield TextArea(id="graphql-var-editor", language="json")

                            yield Button("Execute", id="btn-graphql-execute", variant="primary")

                    with TabPane("Response"):
                        yield RichLog(id="graphql-response-log", wrap=True, highlight=True, markup=True)

    def _get_manager(self) -> GraphQLLabManager:
        url = self.query_one("#graphql-url", Input).value
        headers_str = self.query_one("#graphql-headers", Input).value

        headers = {}
        if headers_str:
            parts = headers_str.split(",")
            for part in parts:
                if ":" in part:
                    k, v = part.split(":", 1)
                    headers[k.strip()] = v.strip()

        return GraphQLLabManager(url, headers)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-graphql-execute":
            await self.execute_query()
        elif event.button.id == "btn-graphql-introspect":
            await self.introspect_schema()

    async def execute_query(self) -> None:
        url = self.query_one("#graphql-url", Input).value
        if not url:
            self.notify("URL required.", severity="error")
            return

        query = self.query_one("#graphql-query-editor", TextArea).text
        if not query:
            self.notify("Query required.", severity="error")
            return

        var_text = self.query_one("#graphql-var-editor", TextArea).text
        variables = None
        if var_text.strip():
            try:
                variables = json.loads(var_text)
            except json.JSONDecodeError as e:
                self.notify(f"Invalid Variables JSON: {e}", severity="error")
                return

        log = self.query_one("#graphql-response-log", RichLog)
        log.clear()
        log.write("[bold]Executing request...[/bold]")

        self.notify("Executing GraphQL query...")

        # Run in thread
        manager = self._get_manager()

        def do_execute():
            return manager.execute(query, variables)

        try:
            result = await asyncio.to_thread(do_execute)

            status = result["status_code"]
            color = "green" if result["ok"] else "red"
            log.write(f"Status: [{color}]{status}[/{color}] (Time: {result.get('elapsed', 0):.3f}s)")

            if "error" in result:
                log.write(f"[bold red]Error:[/bold red] {result['error']}")

            if "json" in result:
                log.write(Syntax(json.dumps(result["json"], indent=2), "json", theme="monokai"))
            elif "body" in result:
                log.write(result["body"])

        except Exception as e:
            log.write(f"[bold red]Exception:[/bold red] {e}")
            self.notify(f"Error: {e}", severity="error")

    async def introspect_schema(self) -> None:
        url = self.query_one("#graphql-url", Input).value
        if not url:
            self.notify("URL required.", severity="error")
            return

        self.notify("Introspecting schema...")
        tree = self.query_one("#graphql-schema-tree", Tree)
        tree.clear()
        tree.root.label = f"Schema ({url})"

        manager = self._get_manager()

        def do_introspect():
            return manager.introspect()

        try:
            result = await asyncio.to_thread(do_introspect)

            if not result["ok"]:
                self.notify(f"Introspection failed: {result.get('status_code')}", severity="error")
                return

            data = result.get("json", {})
            schema = data.get("data", {}).get("__schema")

            if not schema:
                self.notify("No schema found in response.", severity="error")
                return

            self.populate_schema_tree(tree, schema)
            self.notify("Schema loaded.")

        except Exception as e:
            self.notify(f"Introspection error: {e}", severity="error")

    def populate_schema_tree(self, tree: Tree, schema: dict) -> None:
        tree.root.expand()

        # Root Types
        query_type = schema.get("queryType", {}).get("name")
        mutation_type = schema.get("mutationType", {})
        mutation_type_name = mutation_type.get("name") if mutation_type else None

        types = schema.get("types", [])
        types_map = {t["name"]: t for t in types}

        # Query Node
        if query_type and query_type in types_map:
            q_node = tree.root.add("[bold blue]Query[/bold blue]", expand=True)
            self._add_fields(q_node, types_map[query_type])

        # Mutation Node
        if mutation_type_name and mutation_type_name in types_map:
            m_node = tree.root.add("[bold orange1]Mutation[/bold orange1]", expand=False)
            self._add_fields(m_node, types_map[mutation_type_name])

        # All Types Node
        all_types = tree.root.add("[bold]All Types[/bold]", expand=False)
        for t in sorted(types, key=lambda x: x["name"]):
            if t["name"].startswith("__"): continue
            # Skip root types to avoid duplication if desired, but listing all is fine
            kind = t.get("kind", "OBJECT")
            t_node = all_types.add(f"[{kind}] {t['name']}")
            # Ideally we would add fields here too on expand, but for now simple listing

    def _add_fields(self, parent_node, type_def):
        fields = type_def.get("fields", [])
        if not fields:
            return

        for f in sorted(fields, key=lambda x: x["name"]):
            name = f["name"]
            type_ref = f.get("type", {})
            type_name = self._get_type_name(type_ref)

            # Add args if any
            args = f.get("args", [])
            args_str = ""
            if args:
                args_list = []
                for arg in args:
                    arg_type = self._get_type_name(arg.get("type", {}))
                    args_list.append(f"{arg['name']}: {arg_type}")
                args_str = f"({', '.join(args_list)})"

            label = f"[green]{name}[/green]{args_str}: [cyan]{type_name}[/cyan]"
            parent_node.add(label)

    def _get_type_name(self, type_ref):
        if not type_ref:
            return "Unknown"

        kind = type_ref.get("kind")
        name = type_ref.get("name")
        of_type = type_ref.get("ofType")

        if kind == "NON_NULL":
            return f"{self._get_type_name(of_type)}!"
        elif kind == "LIST":
            return f"[{self._get_type_name(of_type)}]"
        else:
            return name if name else "Unknown"
