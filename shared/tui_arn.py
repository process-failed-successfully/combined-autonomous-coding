from pathlib import Path
from typing import Dict, Any

from textual.app import ComposeResult
from textual.widgets import Label, Input, Button, RichLog
from textual.containers import Vertical, Horizontal, Container, VerticalScroll

from shared.arn_lab import ArnLabManager

class ArnLabTab(Container):
    """Tab for ARN Lab (Parsing and Constructing Amazon Resource Names)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ArnLabManager()

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]ARN Lab[/bold]", classes="welcome-text")

            # Parse Section
            with Vertical(classes="stat-box"):
                yield Label("[bold]Parse ARN[/bold]")
                with Horizontal():
                    yield Input(placeholder="e.g. arn:aws:s3:::my_corporate_bucket", id="arn-parse-input")
                    yield Button("Parse", id="btn-arn-parse", variant="primary")
                yield RichLog(id="arn-parse-output", markup=True, highlight=True, wrap=True)

            # Construct Section
            with Vertical(classes="stat-box"):
                yield Label("[bold]Construct ARN[/bold]")
                with Horizontal():
                    yield Input(placeholder="Partition (default: aws)", id="arn-construct-partition", value="aws")
                    yield Input(placeholder="Service (e.g. s3)", id="arn-construct-service")
                with Horizontal():
                    yield Input(placeholder="Region (e.g. us-east-1)", id="arn-construct-region")
                    yield Input(placeholder="Account ID (e.g. 123456789012)", id="arn-construct-account")
                with Horizontal():
                    yield Input(placeholder="Resource (e.g. my_bucket)", id="arn-construct-resource")
                    yield Button("Construct", id="btn-arn-construct", variant="success")
                yield RichLog(id="arn-construct-output", markup=True, highlight=True, wrap=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-arn-parse":
            self.parse_arn()
        elif event.button.id == "btn-arn-construct":
            self.construct_arn()

    def parse_arn(self) -> None:
        arn_input = self.query_one("#arn-parse-input", Input).value.strip()
        log = self.query_one("#arn-parse-output", RichLog)
        log.clear()

        if not arn_input:
            self.notify("ARN input is required.", severity="error")
            return

        result = self.manager.parse(arn_input)
        if result["success"]:
            log.write("[bold green]Parse Successful:[/bold green]")
            for key, value in result.items():
                if key != "success" and value is not None:
                    log.write(f"  [bold cyan]{key}[/bold cyan]: {value}")
        else:
            log.write(f"[bold red]Error:[/bold red] {result['error']}")

    def construct_arn(self) -> None:
        service = self.query_one("#arn-construct-service", Input).value.strip()
        resource = self.query_one("#arn-construct-resource", Input).value.strip()
        partition = self.query_one("#arn-construct-partition", Input).value.strip() or "aws"
        region = self.query_one("#arn-construct-region", Input).value.strip()
        account = self.query_one("#arn-construct-account", Input).value.strip()

        log = self.query_one("#arn-construct-output", RichLog)
        log.clear()

        if not service or not resource:
            self.notify("Service and Resource are required.", severity="error")
            return

        result = self.manager.construct(
            service=service,
            resource=resource,
            partition=partition,
            region=region,
            account_id=account
        )

        if result["success"]:
            log.write("[bold green]Constructed ARN:[/bold green]")
            log.write(result["arn"])

            # Auto-populate the parse input for convenience
            parse_input = self.query_one("#arn-parse-input", Input)
            parse_input.value = result["arn"]
        else:
            log.write(f"[bold red]Error:[/bold red] {result['error']}")
