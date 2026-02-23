from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Checkbox, Input, Label, ListItem, ListView, RichLog, TextArea
from textual import on

from shared.grpc_lab import GrpcLabManager
import asyncio


class GrpcLabTab(Container):
    """Tab for gRPC Lab interactions."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = GrpcLabManager()
        self.selected_service = None
        self.selected_method = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Config & Services
            with Vertical(id="grpc-left-pane", classes="stat-box"):
                yield Label("[bold]Configuration[/bold]")
                yield Input(placeholder="Host (e.g. localhost:50051)", id="grpc-host")
                yield Checkbox("Plaintext", id="grpc-plaintext", value=True)
                yield Input(placeholder="Authority (optional)", id="grpc-authority")
                yield Button("List Services", id="btn-grpc-list-services", variant="primary")

                yield Label("[bold]Services[/bold]")
                yield ListView(id="grpc-service-list")

            # Center Pane: Methods & Describe
            with Vertical(id="grpc-center-pane", classes="stat-box"):
                yield Label("[bold]Methods[/bold]")
                yield ListView(id="grpc-method-list")

                yield Label("[bold]Description[/bold]")
                yield RichLog(id="grpc-describe-log", wrap=True, highlight=True, markup=True)

            # Right Pane: Call
            with Vertical(id="grpc-right-pane", classes="stat-box"):
                yield Label("[bold]Call Method[/bold]")
                yield Label("Request Data (JSON):")
                yield TextArea(id="grpc-request-data", language="json")
                yield Button("Execute Call", id="btn-grpc-call", variant="success", disabled=True)

                yield Label("[bold]Response[/bold]")
                yield RichLog(id="grpc-response-log", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-grpc-list-services":
            await self.list_services()
        elif event.button.id == "btn-grpc-call":
            await self.call_method()

    async def list_services(self) -> None:
        host = self.query_one("#grpc-host", Input).value
        plaintext = self.query_one("#grpc-plaintext", Checkbox).value
        authority = self.query_one("#grpc-authority", Input).value

        if not host:
            self.notify("Host required.", severity="error")
            return

        self.notify("Listing services...")
        list_view = self.query_one("#grpc-service-list", ListView)
        list_view.clear()

        # Clear downstream
        self.query_one("#grpc-method-list", ListView).clear()
        self.query_one("#grpc-describe-log", RichLog).clear()

        try:
            services = await asyncio.to_thread(
                self.manager.list_services, host, plaintext, authority
            )
            for s in services:
                list_view.append(ListItem(Label(s), name=s))
            self.notify(f"Found {len(services)} services.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            self.query_one("#grpc-describe-log", RichLog).write(f"[red]Error: {e}[/red]")

    @on(ListView.Selected, "#grpc-service-list")
    async def on_service_selected(self, event: ListView.Selected) -> None:
        if not event.item:
            return

        # ListItem name was set to service name
        service = event.item.name
        self.selected_service = service
        if not service:
            # Fallback if name attribute fails (Textual < 0.29 might handle name differently on append)
            # Try to get label
            label = event.item.query_one(Label)
            service = str(label.renderable)
            self.selected_service = service

        await self.list_methods(service)
        await self.describe_symbol(service)

    async def list_methods(self, service: str) -> None:
        host = self.query_one("#grpc-host", Input).value
        plaintext = self.query_one("#grpc-plaintext", Checkbox).value
        authority = self.query_one("#grpc-authority", Input).value

        list_view = self.query_one("#grpc-method-list", ListView)
        list_view.clear()

        try:
            methods = await asyncio.to_thread(
                self.manager.list_methods, host, service, plaintext, authority
            )
            for m in methods:
                list_view.append(ListItem(Label(m), name=m))
        except Exception as e:
            self.notify(f"Error fetching methods: {e}", severity="error")

    async def describe_symbol(self, symbol: str) -> None:
        host = self.query_one("#grpc-host", Input).value
        plaintext = self.query_one("#grpc-plaintext", Checkbox).value
        authority = self.query_one("#grpc-authority", Input).value

        log = self.query_one("#grpc-describe-log", RichLog)
        log.clear()

        try:
            desc = await asyncio.to_thread(
                self.manager.describe, host, symbol, plaintext, authority
            )
            log.write(desc)
        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")

    @on(ListView.Selected, "#grpc-method-list")
    async def on_method_selected(self, event: ListView.Selected) -> None:
        if not event.item:
            return

        method = event.item.name
        if not method:
            label = event.item.query_one(Label)
            method = str(label.renderable)

        self.selected_method = method
        self.query_one("#btn-grpc-call").disabled = False
        self.notify(f"Selected method: {method}")
        await self.describe_symbol(method)

    async def call_method(self) -> None:
        if not self.selected_method:
            return

        host = self.query_one("#grpc-host", Input).value
        plaintext = self.query_one("#grpc-plaintext", Checkbox).value
        authority = self.query_one("#grpc-authority", Input).value
        data = self.query_one("#grpc-request-data", TextArea).text

        log = self.query_one("#grpc-response-log", RichLog)
        log.clear()
        log.write(f"Calling {self.selected_method}...")

        try:
            response = await asyncio.to_thread(
                self.manager.call, host, self.selected_method, data, plaintext, authority
            )
            log.write(response)
            self.notify("Call executed.")
        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")
            self.notify("Call failed.", severity="error")
