from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, TextArea, Select, Switch
from textual import on

from shared.enc_lab import EncLabManager

class EncLabTab(Container):
    """
    Encoding Lab Tab for interactive text encoding/decoding.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = EncLabManager()

        self.algorithms = [
            ("Base64", "base64"),
            ("URL", "url"),
            ("HTML", "html"),
            ("Hex", "hex"),
            ("ROT13", "rot13")
        ]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Encoding Lab[/bold]", classes="welcome-text")

            with Horizontal(id="enc-controls-container", classes="stat-box"):
                with Vertical():
                    yield Label("Algorithm")
                    yield Select(self.algorithms, value="base64", id="enc-algorithm-select")

                with Vertical():
                    yield Label("Mode (Encode / Decode)")
                    with Horizontal():
                        yield Label("Encode", id="enc-mode-encode-label")
                        yield Switch(value=False, id="enc-mode-switch") # False = Encode, True = Decode
                        yield Label("Decode", id="enc-mode-decode-label")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Input[/bold]")
                    yield TextArea(id="enc-input", language="text")

                with Vertical(classes="stat-box"):
                    yield Label("[bold]Output[/bold]")
                    yield TextArea(id="enc-output", language="text", read_only=True)

    def on_mount(self) -> None:
        self._update_output()

    @on(Select.Changed, "#enc-algorithm-select")
    def on_algorithm_changed(self, event: Select.Changed) -> None:
        self._update_output()

    @on(Switch.Changed, "#enc-mode-switch")
    def on_mode_changed(self, event: Switch.Changed) -> None:
        self._update_output()

    @on(TextArea.Changed, "#enc-input")
    def on_input_changed(self, event: TextArea.Changed) -> None:
        self._update_output()

    def _update_output(self) -> None:
        try:
            algo_select = self.query_one("#enc-algorithm-select", Select)
            mode_switch = self.query_one("#enc-mode-switch", Switch)
            input_area = self.query_one("#enc-input", TextArea)
            output_area = self.query_one("#enc-output", TextArea)
        except Exception:
            return

        algo = algo_select.value
        is_decode = mode_switch.value
        text = input_area.text

        if not text:
            output_area.text = ""
            return

        try:
            if algo == "base64":
                result = self.manager.base64_process(text, decode=is_decode)
            elif algo == "url":
                result = self.manager.url_process(text, decode=is_decode)
            elif algo == "html":
                result = self.manager.html_process(text, decode=is_decode)
            elif algo == "hex":
                result = self.manager.hex_process(text, decode=is_decode)
            elif algo == "rot13":
                result = self.manager.rot13_process(text)
            else:
                result = "Unknown algorithm."

            output_area.text = result
        except ValueError as e:
            output_area.text = f"Error: {e}"
        except Exception as e:
            output_area.text = f"Unexpected Error: {e}"
