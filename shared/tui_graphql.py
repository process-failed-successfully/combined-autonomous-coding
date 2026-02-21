from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, TextArea, Tree, TabbedContent, TabPane
from rich.syntax import Syntax
import json
import asyncio

from shared.graphql_lab import GraphQLLabManager

class GraphQLLabTab(Container):
    """Tab for GraphQL interaction."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]GraphQL Lab[/bold]", classes="welcome-text")

            # Top Bar: URL & Actions
            with Horizontal(classes="stat-box"):
                yield Label("Endpoint:", classes="label")
                yield Input(placeholder="https://example.com/graphql", id="gql-url-input")
                yield Button("Send Query", id="btn-gql-send", variant="primary")
                yield Button("Introspect", id="btn-gql-introspect", variant="warning")

            # Headers (Optional)
            with Vertical(classes="stat-box"):
                yield Label("Headers (JSON):")
                yield Input(placeholder='{"Authorization": "Bearer ..."}', id="gql-headers-input")

            # Main Split
            with Horizontal():
                # Left: Editors
                with Vertical(id="gql-editors-container"):
                    with TabbedContent():
                        with TabPane("Query/Mutation"):
                            yield TextArea("# Enter query here", id="gql-query-editor", language="graphql")
                        with TabPane("Variables"):
                            yield TextArea("{}", id="gql-vars-editor", language="json")

                # Right: Response & Schema
                with Vertical(id="gql-results-container"):
                    with TabbedContent():
                        with TabPane("Response"):
                            yield RichLog(id="gql-response-log", wrap=True, highlight=True, markup=True)
                        with TabPane("Schema"):
                            yield Tree("Schema", id="gql-schema-tree")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-gql-send":
            await self.action_send()
        elif event.button.id == "btn-gql-introspect":
            await self.action_introspect()

    def get_manager(self):
        url = self.query_one("#gql-url-input", Input).value
        headers_str = self.query_one("#gql-headers-input", Input).value
        headers = {}
        if headers_str:
            try:
                headers = json.loads(headers_str)
            except json.JSONDecodeError:
                self.notify("Invalid JSON in headers", severity="error")
                return None

        if not url:
            self.notify("URL required", severity="error")
            return None

        return GraphQLLabManager(url, headers)

    async def action_send(self):
        manager = self.get_manager()
        if not manager:
            return

        query = self.query_one("#gql-query-editor", TextArea).text
        vars_str = self.query_one("#gql-vars-editor", TextArea).text
        variables = {}
        if vars_str:
            try:
                variables = json.loads(vars_str)
            except json.JSONDecodeError:
                self.notify("Invalid JSON in variables", severity="error")
                return

        log = self.query_one("#gql-response-log", RichLog)
        log.clear()
        log.write("Sending request...")

        # Run in thread
        try:
            result = await asyncio.to_thread(manager.execute, query, variables)

            log.clear()
            status = result.get("status_code", 0)
            color = "green" if result.get("ok") else "red"
            log.write(f"Status: [{color}]{status}[/{color}]  Time: {result.get('elapsed', 0):.3f}s")

            if "json" in result:
                log.write(Syntax(json.dumps(result["json"], indent=2), "json", theme="monokai"))
            elif "body" in result:
                log.write(result["body"])
            elif "error" in result:
                log.write(f"[bold red]Error: {result['error']}[/bold red]")

        except Exception as e:
            log.write(f"[bold red]Exception: {e}[/bold red]")

    async def action_introspect(self):
        manager = self.get_manager()
        if not manager:
            return

        self.notify("Introspecting schema...")
        tree = self.query_one("#gql-schema-tree", Tree)
        tree.clear()
        tree.root.label = "Schema (Loading...)"

        try:
            result = await asyncio.to_thread(manager.introspect)

            if not result.get("ok"):
                self.notify(f"Introspection failed: {result.get('error')}", severity="error")
                tree.root.label = "Schema (Failed)"
                if "error" in result:
                    tree.root.add(f"[red]{result['error']}[/red]")
                return

            data = result.get("json", {}).get("data", {}).get("__schema", {})
            tree.root.label = "Schema"

            # Types
            types_node = tree.root.add("Types")
            for t in sorted(data.get("types", []), key=lambda x: x["name"]):
                if not t["name"].startswith("__"):
                    types_node.add(f"[{t['kind']}] {t['name']}")

            # Directives
            directives_node = tree.root.add("Directives")
            for d in sorted(data.get("directives", []), key=lambda x: x["name"]):
                directives_node.add(f"@{d['name']}")

            self.notify("Schema loaded.")

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            tree.root.label = "Schema (Error)"
