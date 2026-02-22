from typing import Any, Optional
import asyncio
from textual.app import ComposeResult
from textual.widgets import Label, Button, DataTable, Input, RichLog, TabbedContent, TabPane, Select, Static
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.ollama_lab import OllamaLabManager

class OllamaLabTab(Container):
    """
    Ollama Lab Tab for managing local models.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = OllamaLabManager()
        self.selected_model: Optional[str] = None
        self.current_chat_response = ""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Local Model Lab (Ollama)[/bold]", classes="welcome-text")

            # Connection Status
            with Horizontal(classes="stat-box"):
                yield Label("Status: ", id="lbl-ollama-status")
                yield Button("Retry Connection", id="btn-ollama-retry", variant="default")

            with TabbedContent():
                # --- Models Tab ---
                with TabPane("Models", id="ollama-tab-models"):
                    with Horizontal():
                        # Left: List
                        with Vertical(id="ollama-list-container", classes="stat-box"):
                            yield Label("[bold]Installed Models[/bold]")
                            yield DataTable(id="ollama-models-table")
                            yield Button("Refresh", id="btn-ollama-refresh", variant="primary")

                        # Right: Details & Actions
                        with Vertical(id="ollama-details-container"):
                            yield Label("[bold]Model Details[/bold]")
                            yield RichLog(id="ollama-details-log", wrap=True, highlight=True, markup=True)

                            with Horizontal(classes="stat-box"):
                                yield Button("Delete Model", id="btn-ollama-delete", variant="error", disabled=True)
                                yield Button("Test in Chat", id="btn-ollama-test-chat", variant="success", disabled=True)

                # --- Pull Tab ---
                with TabPane("Pull", id="ollama-tab-pull"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Pull New Model[/bold]")
                        yield Label("Enter model name (e.g., llama3, mistral, codellama:7b)...")
                        with Horizontal():
                            yield Input(placeholder="Model Name...", id="ollama-pull-input")
                            yield Button("Pull", id="btn-ollama-pull", variant="warning")

                        yield RichLog(id="ollama-pull-log", wrap=True, highlight=True, markup=True)

                # --- Chat Tab ---
                with TabPane("Chat", id="ollama-tab-chat"):
                    with Vertical():
                        yield Label("[bold]Quick Chat Test[/bold]")
                        with Horizontal(classes="stat-box"):
                            yield Label("Model:")
                            yield Select([], id="ollama-chat-select")

                        # Chat History
                        yield RichLog(id="ollama-chat-log", wrap=True, highlight=True, markup=True)

                        # Active Response Area
                        yield Label("[bold]Current Response:[/bold]")
                        yield Static("", id="ollama-chat-active", markup=True)

                        with Horizontal(classes="stat-box"):
                            yield Input(placeholder="Message...", id="ollama-chat-input")
                            yield Button("Send", id="btn-ollama-send", variant="success")

    def on_mount(self) -> None:
        table = self.query_one("#ollama-models-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Name", "Size (GB)", "Modified")

        self.check_status()

    def check_status(self) -> None:
        is_connected = self.manager.check_connection()
        lbl = self.query_one("#lbl-ollama-status", Label)

        if is_connected:
            lbl.update(f"[green]Connected to {self.manager.base_url}[/green]")
            self.load_models()
        else:
            lbl.update(f"[red]Disconnected from {self.manager.base_url}[/red]")
            self.query_one("#ollama-models-table", DataTable).clear()

    def load_models(self) -> None:
        table = self.query_one("#ollama-models-table", DataTable)
        table.clear()

        # Populate select for chat
        select = self.query_one("#ollama-chat-select", Select)

        try:
            models = self.manager.list_models()
            options = []

            for m in models:
                name = m['name']
                size_gb = m.get('size', 0) / (1024**3)
                modified = m.get('modified_at', '')[:10]

                table.add_row(name, f"{size_gb:.2f}", modified, key=name)
                options.append((name, name))

            select.set_options(options)
            if options:
                select.value = options[0][0]

        except Exception as e:
            self.notify(f"Error loading models: {e}", severity="error")

    @on(Button.Pressed, "#btn-ollama-retry")
    def on_retry(self) -> None:
        self.check_status()

    @on(Button.Pressed, "#btn-ollama-refresh")
    def on_refresh(self) -> None:
        self.load_models()
        self.notify("Refreshed.")

    @on(DataTable.RowSelected, "#ollama-models-table")
    def on_model_selected(self, event: DataTable.RowSelected) -> None:
        name = event.row_key.value
        self.selected_model = name
        self.load_details(name)

        self.query_one("#btn-ollama-delete").disabled = False
        self.query_one("#btn-ollama-test-chat").disabled = False

    def load_details(self, name: str) -> None:
        log = self.query_one("#ollama-details-log", RichLog)
        log.clear()
        log.write(f"Loading info for {name}...")

        async def fetch_info():
            info = await asyncio.to_thread(self.manager.show_model_info, name)
            log.clear()
            if "error" in info:
                log.write(f"[red]{info['error']}[/red]")
            else:
                import json
                log.write(json.dumps(info, indent=2))

        asyncio.create_task(fetch_info())

    @on(Button.Pressed, "#btn-ollama-delete")
    def on_delete(self) -> None:
        if not self.selected_model:
            return

        model_name = self.selected_model
        async def do_delete():
            success = await asyncio.to_thread(self.manager.delete_model, model_name)
            if success:
                self.notify(f"Deleted {model_name}")
                self.selected_model = None
                self.load_models()
                self.query_one("#ollama-details-log", RichLog).clear()
                self.query_one("#btn-ollama-delete").disabled = True
                self.query_one("#btn-ollama-test-chat").disabled = True
            else:
                self.notify("Failed to delete model.", severity="error")

        asyncio.create_task(do_delete())

    @on(Button.Pressed, "#btn-ollama-test-chat")
    def on_test_chat(self) -> None:
        if not self.selected_model:
            return

        # Switch tabs
        self.query_one(TabbedContent).active = "ollama-tab-chat"
        self.query_one("#ollama-chat-select", Select).value = self.selected_model

    @on(Button.Pressed, "#btn-ollama-pull")
    async def on_pull(self) -> None:
        name = self.query_one("#ollama-pull-input", Input).value
        if not name:
            self.notify("Model name required.", severity="error")
            return

        log = self.query_one("#ollama-pull-log", RichLog)
        log.clear()
        log.write(f"Pulling {name}...")
        self.query_one("#btn-ollama-pull").disabled = True

        # Run pull in background task to update UI
        asyncio.create_task(self._pull_worker(name))

    async def _pull_worker(self, name: str) -> None:
        log = self.query_one("#ollama-pull-log", RichLog)

        try:
            def run_pull_sync():
                for update in self.manager.pull_model(name):
                    self.app.call_from_thread(self._handle_pull_update, update, log)

            await asyncio.to_thread(run_pull_sync)

            log.write("[bold green]Pull process finished.[/bold green]")
            self.load_models()

        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")
        finally:
            self.query_one("#btn-ollama-pull").disabled = False

    def _handle_pull_update(self, update: dict[str, Any], log: RichLog) -> None:
        if "error" in update:
            log.write(f"[red]{update['error']}[/red]")
            return

        status = update.get("status", "")
        completed = update.get("completed", 0)
        total = update.get("total", 0)

        msg = status
        if total > 0:
            percent = (completed / total) * 100
            msg += f" ({percent:.1f}%)"

        log.write(msg)

    @on(Button.Pressed, "#btn-ollama-send")
    async def on_send_chat(self) -> None:
        await self.send_chat()

    @on(Input.Submitted, "#ollama-chat-input")
    async def on_chat_enter(self) -> None:
        await self.send_chat()

    async def send_chat(self) -> None:
        msg_input = self.query_one("#ollama-chat-input", Input)
        message = msg_input.value
        model = self.query_one("#ollama-chat-select", Select).value

        if not message or not model:
            return

        log = self.query_one("#ollama-chat-log", RichLog)
        log.write(f"[bold blue]You:[/bold blue] {message}")
        msg_input.value = ""

        self.current_chat_response = ""
        self.query_one("#ollama-chat-active", Static).update("[italic]Thinking...[/italic]")

        asyncio.create_task(self._chat_worker(model, message))

    async def _chat_worker(self, model: str, message: str) -> None:
        log = self.query_one("#ollama-chat-log", RichLog)
        active_static = self.query_one("#ollama-chat-active", Static)

        def run_chat_sync():
            for chunk in self.manager.chat(model, message):
                self.app.call_from_thread(self._handle_chat_chunk, chunk, active_static)

        await asyncio.to_thread(run_chat_sync)

        # When done, write full response to log and clear active
        if self.current_chat_response:
             log.write(f"[bold green]{model}:[/bold green] {self.current_chat_response}")
             active_static.update("")
             self.current_chat_response = ""

    def _handle_chat_chunk(self, chunk: str, static_widget: Static) -> None:
        self.current_chat_response += chunk
        static_widget.update(self.current_chat_response)
