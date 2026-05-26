from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, TextArea, Select, Label
from textual.binding import Binding
from shared.jsonl_lab import JsonlManager

class JsonlLabTab(Static):
    """TUI tab for Jsonl Lab."""

    BINDINGS = [
        Binding("ctrl+r", "run_action", "Run", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = JsonlManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="jsonl-container", classes="p-1"):
            yield Static("JSON Lines Converter & Validator", classes="text-bold text-center p-1 bg-primary text-primary-content")

            with Horizontal(classes="h-auto p-1 border-b border-primary"):
                yield Label("Action:", classes="p-1 mt-1")
                yield Select(
                    [("JSON to JSON Lines", "json2jsonl"),
                     ("JSON Lines to JSON", "jsonl2json"),
                     ("Validate JSON Lines", "validate")],
                    value="json2jsonl",
                    id="jsonl-action-select",
                    classes="w-1-3 m-1"
                )
                yield Button("Run (Ctrl+R)", id="jsonl-run-btn", variant="primary", classes="m-1")

            with Horizontal(classes="h-full"):
                with Vertical(classes="w-1-2 p-1 border-r border-primary h-full"):
                    yield Label("Input:", classes="text-bold mb-1")
                    yield TextArea(id="jsonl-input-ta", classes="h-full")

                with Vertical(classes="w-1-2 p-1 h-full"):
                    yield Label("Output/Result:", classes="text-bold mb-1")
                    yield TextArea(id="jsonl-output-ta", classes="h-full", read_only=True)

            yield Static("", id="jsonl-status", classes="p-1 h-auto")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "jsonl-run-btn":
            await self.action_run_action()

    async def action_run_action(self) -> None:
        action_select = self.query_one("#jsonl-action-select", Select)
        input_ta = self.query_one("#jsonl-input-ta", TextArea)
        output_ta = self.query_one("#jsonl-output-ta", TextArea)
        status_static = self.query_one("#jsonl-status", Static)

        action = action_select.value
        input_text = input_ta.text.strip()

        if action == Select.BLANK or not isinstance(action, str):
            status_static.update("[red]Please select an action.[/red]")
            return

        if not input_text:
            status_static.update("[yellow]Input is empty.[/yellow]")
            output_ta.text = ""
            return

        try:
            if action == "json2jsonl":
                result = self.manager.json_to_jsonl(input_text)
                output_ta.text = result
                output_ta.language = "json" # Just for basic syntax highlighting
                status_static.update("[green]Conversion to JSON Lines successful.[/green]")
            elif action == "jsonl2json":
                result = self.manager.jsonl_to_json(input_text)
                output_ta.text = result
                output_ta.language = "json"
                status_static.update("[green]Conversion to JSON successful.[/green]")
            elif action == "validate":
                is_valid, msg = self.manager.validate_jsonl(input_text)
                if is_valid:
                    output_ta.text = "Valid JSON Lines."
                    status_static.update(f"[green]{msg}[/green]")
                else:
                    output_ta.text = f"Invalid JSON Lines:\n{msg}"
                    status_static.update(f"[red]{msg}[/red]")
            else:
                status_static.update(f"[red]Unknown action: {action}[/red]")
                return

        except Exception as e:
            output_ta.text = ""
            status_static.update(f"[red]Error: {e}[/red]")
