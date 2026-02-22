from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Input, Button, TextArea, RichLog
from textual import on
from shared.graphql_lab import GraphQLLabManager
import json
import asyncio
from rich.syntax import Syntax

class GraphQLLabTab(Container):
    """Tab for GraphQL experimentation."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]GraphQL Lab[/bold]", classes="welcome-text")

            # Configuration
            with Horizontal(classes="stat-box"):
                yield Label("URL:", classes="label")
                yield Input(placeholder="https://api.example.com/graphql", id="gql-url")

            with Horizontal(classes="stat-box"):
                yield Label("Headers (JSON):", classes="label")
                yield Input(placeholder='{"Authorization": "Bearer ..."}', id="gql-headers")

            # Editors
            with Horizontal(id="gql-editors-container"):
                with Vertical(classes="stat-box"):
                    yield Label("Query / Mutation")
                    yield TextArea(id="gql-query-editor")

                with Vertical(classes="stat-box"):
                    yield Label("Variables (JSON)")
                    yield TextArea(id="gql-vars-editor", language="json")

            # Actions
            with Horizontal(classes="stat-box"):
                yield Button("Execute", id="btn-gql-execute", variant="primary")
                yield Button("Introspect Schema", id="btn-gql-introspect", variant="warning")

            # Results
            with VerticalScroll(id="gql-results-container", classes="stat-box"):
                yield Label("[bold]Result[/bold]")
                yield RichLog(id="gql-result-log", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-gql-execute")
    async def on_execute(self) -> None:
        await self.run_action("execute")

    @on(Button.Pressed, "#btn-gql-introspect")
    async def on_introspect(self) -> None:
        await self.run_action("introspect")

    async def run_action(self, action: str) -> None:
        url = self.query_one("#gql-url", Input).value
        if not url:
            self.notify("URL required.", severity="error")
            return

        headers_str = self.query_one("#gql-headers", Input).value
        headers = {}
        if headers_str:
            try:
                headers = json.loads(headers_str)
            except json.JSONDecodeError:
                self.notify("Invalid Headers JSON.", severity="error")
                return

        query = self.query_one("#gql-query-editor", TextArea).text
        variables_str = self.query_one("#gql-vars-editor", TextArea).text
        variables = None
        if variables_str:
            try:
                variables = json.loads(variables_str)
            except json.JSONDecodeError:
                self.notify("Invalid Variables JSON.", severity="error")
                return

        if action == "execute" and not query:
             self.notify("Query required.", severity="error")
             return

        self.manager = GraphQLLabManager(url, headers)

        log = self.query_one("#gql-result-log", RichLog)
        log.clear()
        log.write(f"Running {action} on {url}...")
        self.notify(f"{action.capitalize()} started...")

        result = {}
        try:
            if action == "execute":
                result = await asyncio.to_thread(self.manager.execute, query, variables)
            else:
                result = await asyncio.to_thread(self.manager.introspect)
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify("Error occurred.", severity="error")
            return

        status = result.get("status_code", 0)
        color = "green" if result.get("ok") else "red"
        log.write(f"Status: [{color}]{status}[/{color}]")

        if "elapsed" in result:
            log.write(f"Time: {result['elapsed']:.3f}s")

        if "error" in result:
            log.write(f"[bold red]Error:[/bold red] {result['error']}")

        if "json" in result:
            formatted = json.dumps(result["json"], indent=2)
            log.write(Syntax(formatted, "json", theme="monokai"))
        elif "body" in result:
            log.write(result["body"])

        self.notify("Complete.")
