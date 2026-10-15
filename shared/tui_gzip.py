from pathlib import Path
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Input, Label, TextArea, Checkbox, Select
from shared.gzip_lab import GzipLabManager

class GzipLabTab(Container):
    """Tab for Gzip compression and decompression."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = GzipLabManager()

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="p-4"):
            yield Label("[bold]Gzip Lab (Compress/Decompress)[/bold]", classes="welcome-text")

            with Container(classes="border p-4 mb-4"):
                yield Label("Mode:", classes="mb-2")
                yield Select(
                    [("String/Text", "string"), ("File", "file")],
                    value="string",
                    id="gzip-mode",
                    classes="mb-4"
                )

                # String mode UI
                with Container(id="gzip-string-container"):
                    yield Label("Input Text (or Encoded Payload to Decompress):")
                    yield TextArea(id="gzip-text-input", classes="mb-4", language="text")
                    yield Horizontal(
                        Checkbox("Base64 Output/Input (instead of Hex)", id="gzip-base64", value=True),
                        Select(
                            [(str(i), i) for i in range(1, 10)],
                            value=9,
                            id="gzip-level",
                            classes="ml-4"
                        ),
                        classes="mb-4"
                    )
                    yield Horizontal(
                        Button("Compress", id="btn-gzip-compress", variant="primary"),
                        Button("Decompress", id="btn-gzip-decompress", variant="warning"),
                        classes="mb-4"
                    )
                    yield Label("Result:")
                    yield TextArea(id="gzip-text-output", classes="mb-4", language="text", read_only=True)

                # File mode UI
                with Container(id="gzip-file-container", classes="hidden"):
                    yield Label("Input File Path:")
                    yield Input(placeholder="/path/to/input", id="gzip-file-input", classes="mb-4")
                    yield Label("Output File Path (Optional):")
                    yield Input(placeholder="/path/to/output", id="gzip-file-output", classes="mb-4")

                    yield Horizontal(
                        Select(
                            [(str(i), i) for i in range(1, 10)],
                            value=9,
                            id="gzip-file-level",
                            classes="mr-4"
                        ),
                        classes="mb-4"
                    )
                    yield Horizontal(
                        Button("Compress File", id="btn-gzip-file-compress", variant="primary"),
                        Button("Decompress File", id="btn-gzip-file-decompress", variant="warning"),
                        classes="mb-4"
                    )
                    yield Label("Status:")
                    yield Label("", id="gzip-file-status", classes="text-muted")

    @on(Select.Changed, "#gzip-mode")
    def on_mode_changed(self, event: Select.Changed) -> None:
        mode = event.value
        string_container = self.query_one("#gzip-string-container")
        file_container = self.query_one("#gzip-file-container")

        if mode == "string":
            string_container.remove_class("hidden")
            file_container.add_class("hidden")
        else:
            string_container.add_class("hidden")
            file_container.remove_class("hidden")

    @on(Button.Pressed, "#btn-gzip-compress")
    def compress_string(self) -> None:
        input_text = self.query_one("#gzip-text-input", TextArea).text
        output_area = self.query_one("#gzip-text-output", TextArea)
        use_base64 = self.query_one("#gzip-base64", Checkbox).value
        level = self.query_one("#gzip-level", Select).value

        if not input_text:
            output_area.text = "Error: Input text is empty."
            return

        try:
            compressed = self.manager.compress_bytes(input_text.encode("utf-8"), level=int(str(level)))
            if use_base64:
                import base64
                output_area.text = base64.b64encode(compressed).decode("ascii")
            else:
                output_area.text = compressed.hex()
        except Exception as e:
            output_area.text = f"Error compressing: {e}"

    @on(Button.Pressed, "#btn-gzip-decompress")
    def decompress_string(self) -> None:
        input_text = self.query_one("#gzip-text-input", TextArea).text.strip()
        output_area = self.query_one("#gzip-text-output", TextArea)
        use_base64 = self.query_one("#gzip-base64", Checkbox).value

        if not input_text:
            output_area.text = "Error: Input text is empty."
            return

        try:
            if use_base64:
                import base64
                data = base64.b64decode(input_text)
            else:
                data = bytes.fromhex(input_text)

            decompressed = self.manager.decompress_bytes(data)
            output_area.text = decompressed.decode("utf-8", errors="replace")
        except Exception as e:
            output_area.text = f"Error decompressing: {e}"

    @on(Button.Pressed, "#btn-gzip-file-compress")
    def compress_file(self) -> None:
        input_path_str = self.query_one("#gzip-file-input", Input).value
        output_path_str = self.query_one("#gzip-file-output", Input).value
        status_label = self.query_one("#gzip-file-status", Label)
        level = self.query_one("#gzip-file-level", Select).value

        if not input_path_str:
            status_label.update("[red]Error: Input file path is required.[/red]")
            return

        input_path = Path(input_path_str)
        if not input_path.exists() or not input_path.is_file():
            status_label.update(f"[red]Error: Input file not found or is not a file: {input_path}[/red]")
            return

        output_path = Path(output_path_str) if output_path_str else Path(str(input_path) + ".gz")

        try:
            self.manager.compress_file(input_path, output_path, level=int(str(level)))
            status_label.update(f"[green]Successfully compressed to: {output_path}[/green]")
        except Exception as e:
            status_label.update(f"[red]Error compressing file: {e}[/red]")

    @on(Button.Pressed, "#btn-gzip-file-decompress")
    def decompress_file(self) -> None:
        input_path_str = self.query_one("#gzip-file-input", Input).value
        output_path_str = self.query_one("#gzip-file-output", Input).value
        status_label = self.query_one("#gzip-file-status", Label)

        if not input_path_str:
            status_label.update("[red]Error: Input file path is required.[/red]")
            return

        input_path = Path(input_path_str)
        if not input_path.exists() or not input_path.is_file():
            status_label.update(f"[red]Error: Input file not found or is not a file: {input_path}[/red]")
            return

        if output_path_str:
            output_path = Path(output_path_str)
        else:
            if str(input_path).endswith(".gz"):
                output_path = Path(str(input_path)[:-3])
            else:
                output_path = Path(str(input_path) + ".out")

        try:
            self.manager.decompress_file(input_path, output_path)
            status_label.update(f"[green]Successfully decompressed to: {output_path}[/green]")
        except Exception as e:
            status_label.update(f"[red]Error decompressing file: {e}[/red]")
