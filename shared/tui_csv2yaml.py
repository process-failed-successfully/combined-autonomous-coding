from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Static, TextArea
from textual import on

from shared.csv2yaml_lab import Csv2YamlManager


class Csv2YamlTab(Container):
    """TUI Tab for converting CSV to YAML."""

    def __init__(self):
        super().__init__()
        self.manager = Csv2YamlManager()

    def compose(self) -> ComposeResult:
        yield Static("[bold]CSV to YAML Converter[/bold]", classes="tab-title")

        with Vertical():
            with Horizontal(id="csv2yaml-io-container"):
                with Vertical(classes="csv2yaml-pane"):
                    yield Static("Input CSV:", classes="label")
                    self.input_area = TextArea(language="csv", id="csv2yaml-input-ta")
                    yield self.input_area

                with Vertical(classes="csv2yaml-pane"):
                    yield Static("Output YAML:", classes="label")
                    self.output_area = TextArea(language="yaml", read_only=True, id="csv2yaml-output-ta")
                    yield self.output_area

            with Horizontal(id="csv2yaml-controls"):
                yield Button("Convert", id="csv2yaml-convert-btn", variant="primary")
                self.status_label = Static("", id="csv2yaml-status")
                yield self.status_label

    @on(Button.Pressed, "#csv2yaml-convert-btn")
    def on_convert(self) -> None:
        csv_data = self.input_area.text
        if not csv_data.strip():
            self.status_label.update("[red]Input is empty.[/red]")
            self.output_area.text = ""
            return

        try:
            yaml_str = self.manager.convert_csv_to_yaml(csv_data)
            self.output_area.text = yaml_str
            self.status_label.update("[green]Conversion successful.[/green]")
        except Exception as e:
            self.output_area.text = ""
            self.status_label.update(f"[red]Error:[/red] {e}")
