from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, Select, TabbedContent, TabPane, TextArea, Checkbox, RichLog
from shared.csv2html_lab import Csv2HtmlManager
import asyncio


class Csv2HtmlLabTab(Container):
    """Tab for CSV to HTML conversion."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = Csv2HtmlManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]CSV to HTML Lab[/bold]", classes="welcome-text")

            with Horizontal():
                with Vertical(classes="stat-box", id="csv-input-col"):
                    yield Label("Input CSV:")
                    yield TextArea(id="csv-input")
                    with Horizontal():
                        yield Label("Delimiter:", classes="label")
                        yield Input(value=",", id="csv-delimiter", classes="small-input")
                        yield Checkbox("Has Header", id="csv-has-header", value=True)
                    with Horizontal():
                        yield Label("Table ID:", classes="label")
                        yield Input(placeholder="my-table", id="html-table-id")
                        yield Label("Class:", classes="label")
                        yield Input(placeholder="table table-striped", id="html-table-class")
                    yield Button("Convert", id="btn-convert-csv2html", variant="primary")
                    yield Button("Clear", id="btn-clear-csv2html")

                with Vertical(classes="stat-box", id="html-output-col"):
                    yield Label("[bold]Result[/bold]")
                    yield TextArea(id="html-output", read_only=True, language="html")
                    yield RichLog(id="csv2html-log", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-convert-csv2html":
            await self.convert()
        elif event.button.id == "btn-clear-csv2html":
            self.clear()

    async def convert(self) -> None:
        csv_data = self.query_one("#csv-input", TextArea).text
        log = self.query_one("#csv2html-log", RichLog)
        output = self.query_one("#html-output", TextArea)

        if not csv_data.strip():
            log.write("[bold yellow]No input CSV provided.[/bold yellow]")
            return

        delimiter = self.query_one("#csv-delimiter", Input).value or ","
        has_header = self.query_one("#csv-has-header", Checkbox).value
        table_id = self.query_one("#html-table-id", Input).value
        table_class = self.query_one("#html-table-class", Input).value

        log.clear()
        self.notify("Converting...")

        try:
            res = await asyncio.to_thread(
                self.manager.convert,
                csv_data,
                delimiter,
                has_header,
                table_class,
                table_id
            )

            output.text = res
            log.write("[bold green]Conversion successful![/bold green]")
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify("Conversion failed.", severity="error")

    def clear(self) -> None:
        self.query_one("#csv-input", TextArea).text = ""
        self.query_one("#html-output", TextArea).text = ""
        self.query_one("#csv-delimiter", Input).value = ","
        self.query_one("#html-table-id", Input).value = ""
        self.query_one("#html-table-class", Input).value = ""
        self.query_one("#csv2html-log", RichLog).clear()
