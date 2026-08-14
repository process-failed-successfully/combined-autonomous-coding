from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Button, TextArea, Select, Checkbox, DataTable
from textual import on

from shared.extract_lab import ExtractLabManager

class ExtractLabTab(ScrollableContainer):
    """TUI Tab for Extract Lab."""

    def __init__(self, project_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = ExtractLabManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="tab-content"):
            yield Label("[bold]Extract Lab (IoC Extractor)[/bold] - Extract IPs, URLs, Emails, Hashes, and more from text", classes="tab-title")

            with Horizontal(classes="action-bar"):
                yield Button("Extract", id="btn-extract", variant="primary")
                yield Button("Clear", id="btn-extract-clear", variant="warning")

            with Horizontal(classes="options-bar"):
                types = [("All", "all")] + [(t.upper(), t) for t in self.manager.get_supported_types()]
                yield Select(types, value="all", id="extract-type-select", prompt="Select Extraction Type")
                yield Checkbox("Unique Results", value=True, id="extract-unique-checkbox")

            with Horizontal():
                with Vertical(classes="panel"):
                    yield Label("Input Text:")
                    yield TextArea(id="extract-input-area")

                with Vertical(classes="panel"):
                    yield Label("Extracted Results:")
                    yield TextArea(id="extract-output-area", read_only=True)

    @on(Button.Pressed, "#btn-extract")
    def do_extract(self) -> None:
        input_area = self.query_one("#extract-input-area", TextArea)
        text = input_area.text

        if not text.strip():
            self.app.notify("Input text is required.", severity="error")
            return

        extract_type = self.query_one("#extract-type-select", Select).value
        unique = self.query_one("#extract-unique-checkbox", Checkbox).value

        try:
            output_area = self.query_one("#extract-output-area", TextArea)
            if extract_type == "all":
                results = self.manager.extract_all(text, unique=unique)
                if not results:
                    output_area.text = "No matches found."
                else:
                    lines = []
                    for k, v in results.items():
                        lines.append(f"--- {k.upper()} ({len(v)}) ---")
                        lines.extend(v)
                        lines.append("")
                    output_area.text = "\n".join(lines)
            else:
                results = self.manager.extract(text, extract_type, unique=unique)
                if not results:
                    output_area.text = f"No {extract_type.upper()} matches found."
                else:
                    output_area.text = "\n".join(results)

            self.app.notify("Extraction complete.")
        except Exception as e:
            self.app.notify(f"Error during extraction: {e}", severity="error")

    @on(Button.Pressed, "#btn-extract-clear")
    def clear_all(self) -> None:
        self.query_one("#extract-input-area", TextArea).text = ""
        self.query_one("#extract-output-area", TextArea).text = ""
        self.app.notify("Fields cleared.")
