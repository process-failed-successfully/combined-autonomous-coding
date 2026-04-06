from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, Label, TextArea, TabPane
import yaml
from shared.csv2yaml_lab import Csv2YamlManager

class Csv2YamlTab(TabPane):
    """TUI Tab for converting CSV to YAML."""

    def __init__(self):
        super().__init__("CSV -> YAML", id="tab-csv2yaml")
        self.manager = Csv2YamlManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-4"):
            yield Label("CSV to YAML Converter", classes="text-xl text-bold mb-4")

            with Horizontal(classes="mb-2 h-auto"):
                yield Label("Delimiter:", classes="mt-2 mr-2")
                yield Input(value=",", id="csv2yaml-delimiter", classes="w-16")

            with Horizontal(classes="mb-4 h-1fr"):
                with Vertical(classes="w-1fr mr-2"):
                    yield Label("Input (CSV):")
                    yield TextArea(id="csv2yaml-input")

                with Vertical(classes="w-1fr ml-2"):
                    yield Label("Output (YAML):")
                    yield TextArea(id="csv2yaml-output", read_only=True)

            with Horizontal(classes="h-auto"):
                yield Button("Convert", id="btn-convert-csv2yaml", variant="primary")
                yield Button("Clear", id="btn-clear-csv2yaml", variant="error", classes="ml-2")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-convert-csv2yaml":
            self.convert_csv()
        elif event.button.id == "btn-clear-csv2yaml":
            self.query_one("#csv2yaml-input", TextArea).text = ""
            self.query_one("#csv2yaml-output", TextArea).text = ""

    def convert_csv(self) -> None:
        csv_text = self.query_one("#csv2yaml-input", TextArea).text
        delimiter = self.query_one("#csv2yaml-delimiter", Input).value or ","

        if not csv_text.strip():
            self.query_one("#csv2yaml-output", TextArea).text = ""
            return

        try:
            yaml_data = self.manager.convert(csv_text, delimiter=delimiter)
            yaml_str = yaml.dump(yaml_data, sort_keys=False, allow_unicode=True)
            self.query_one("#csv2yaml-output", TextArea).text = yaml_str
        except Exception as e:
            self.query_one("#csv2yaml-output", TextArea).text = f"Error parsing CSV:\n{e}"
