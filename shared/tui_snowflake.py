from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label, Input, RichLog
from textual import on

from shared.snowflake_lab import SnowflakeManager

class SnowflakeLabTab(Vertical):
    """A tab for Snowflake Lab utilities."""

    def compose(self) -> ComposeResult:
        yield Label("Snowflake Lab", id="snowflake-lab-header", classes="text-bold welcome-text")

        with Horizontal():
            # Parse Section
            with Vertical(classes="stat-box"):
                yield Label("[bold]Parse Snowflake ID[/bold]")
                yield Label("Snowflake ID:")
                yield Input(placeholder="e.g. 175928847299117063", id="snowflake-parse-input")
                yield Label("Epoch (ms) [Default: Twitter]:")
                yield Input(placeholder="1288834974657", id="snowflake-parse-epoch")
                yield Button("Parse", id="btn-snowflake-parse", variant="primary")
                yield Label("Result:")
                yield RichLog(id="snowflake-parse-result", wrap=True, markup=True)

            # Generate Section
            with Vertical(classes="stat-box"):
                yield Label("[bold]Generate Snowflake IDs[/bold]")
                with Horizontal():
                    with Vertical():
                        yield Label("Worker ID (0-31):")
                        yield Input(value="1", id="snowflake-gen-worker")
                    with Vertical():
                        yield Label("Datacenter ID (0-31):")
                        yield Input(value="1", id="snowflake-gen-datacenter")
                with Horizontal():
                    with Vertical():
                        yield Label("Epoch (ms):")
                        yield Input(value="1288834974657", id="snowflake-gen-epoch")
                    with Vertical():
                        yield Label("Count:")
                        yield Input(value="1", id="snowflake-gen-count")

                yield Button("Generate", id="btn-snowflake-generate", variant="success")
                yield Label("Result:")
                yield RichLog(id="snowflake-gen-result", wrap=True, markup=True)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn-snowflake-parse":
            self.parse_snowflake()
        elif button_id == "btn-snowflake-generate":
            self.generate_snowflakes()

    def parse_snowflake(self) -> None:
        sf_input = self.query_one("#snowflake-parse-input", Input).value.strip()
        epoch_input = self.query_one("#snowflake-parse-epoch", Input).value.strip()
        result_log = self.query_one("#snowflake-parse-result", RichLog)

        result_log.clear()

        if not sf_input:
            result_log.write("[red]Please enter a Snowflake ID.[/red]")
            return

        try:
            snowflake_int = int(sf_input)
        except ValueError:
            result_log.write("[red]Invalid Snowflake ID. Must be an integer.[/red]")
            return

        epoch = SnowflakeManager.DEFAULT_EPOCH
        if epoch_input:
            try:
                epoch = int(epoch_input)
            except ValueError:
                result_log.write("[red]Invalid epoch. Must be an integer.[/red]")
                return

        manager = SnowflakeManager(epoch=epoch)
        info = manager.parse(snowflake_int)

        if not info["valid"]:
            result_log.write(f"[red]Error: {info['error']}[/red]")
            return

        result_log.write(f"[bold green]Valid Snowflake ID[/bold green]")
        result_log.write(f"[bold]Timestamp:[/bold] {info['timestamp']} ({info['datetime']})")
        result_log.write(f"[bold]Datacenter ID:[/bold] {info['datacenter_id']}")
        result_log.write(f"[bold]Worker ID:[/bold] {info['worker_id']}")
        result_log.write(f"[bold]Sequence:[/bold] {info['sequence']}")

    def generate_snowflakes(self) -> None:
        worker_input = self.query_one("#snowflake-gen-worker", Input).value.strip()
        datacenter_input = self.query_one("#snowflake-gen-datacenter", Input).value.strip()
        epoch_input = self.query_one("#snowflake-gen-epoch", Input).value.strip()
        count_input = self.query_one("#snowflake-gen-count", Input).value.strip()

        result_log = self.query_one("#snowflake-gen-result", RichLog)
        result_log.clear()

        try:
            worker_id = int(worker_input) if worker_input else 1
            datacenter_id = int(datacenter_input) if datacenter_input else 1
            epoch = int(epoch_input) if epoch_input else SnowflakeManager.DEFAULT_EPOCH
            count = int(count_input) if count_input else 1
        except ValueError:
            result_log.write("[red]Invalid input. All fields must be integers.[/red]")
            return

        manager = SnowflakeManager(epoch=epoch)

        try:
            results = manager.generate(count=count, worker_id=worker_id, datacenter_id=datacenter_id)
            for res in results:
                result_log.write(str(res))
        except Exception as e:
            result_log.write(f"[red]Error generating IDs: {e}[/red]")
