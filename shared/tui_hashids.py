from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Static, Label
from textual.reactive import reactive
from textual import on

from shared.hashids_lab import HashidsLabManager, HAS_HASHIDS


class HashidsLabTab(Container):
    """TUI tab for Hashids Lab operations."""

    def compose(self) -> ComposeResult:
        with Vertical(id="hashids-container", classes="lab-container"):
            yield Label("Hashids Configuration", classes="section-title")

            with Horizontal(id="hashids-config"):
                with Vertical(classes="input-group"):
                    yield Label("Salt (Optional)")
                    yield Input(id="hashids-salt", placeholder="e.g. My Secret Salt")
                with Vertical(classes="input-group"):
                    yield Label("Min Length")
                    yield Input(id="hashids-min-length", placeholder="0", type="number", value="0")
                with Vertical(classes="input-group"):
                    yield Label("Alphabet (Optional)")
                    yield Input(id="hashids-alphabet", placeholder="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")

            yield Label("Encode / Decode", classes="section-title")

            with Horizontal(id="hashids-action"):
                with Vertical(classes="input-group", id="hashids-left-panel"):
                    yield Label("Numbers to Encode (Space Separated)")
                    yield Input(id="hashids-numbers", placeholder="1 2 3")
                    yield Button("Encode", id="btn-hashids-encode", variant="primary")

                with Vertical(classes="input-group", id="hashids-right-panel"):
                    yield Label("Hashid to Decode")
                    yield Input(id="hashids-hash", placeholder="jR")
                    yield Button("Decode", id="btn-hashids-decode", variant="primary")

            yield Label("Result", classes="section-title")
            yield Static("", id="hashids-output", classes="output-box")


    def _get_manager(self) -> HashidsLabManager | None:
        """Helper to construct HashidsLabManager with current config inputs."""
        if not HAS_HASHIDS:
            self.query_one("#hashids-output", Static).update("Error: hashids library not installed. Please install it using 'pip install hashids'.")
            return None

        salt = self.query_one("#hashids-salt", Input).value
        min_length_str = self.query_one("#hashids-min-length", Input).value
        alphabet = self.query_one("#hashids-alphabet", Input).value

        min_length = 0
        if min_length_str:
            try:
                min_length = int(min_length_str)
            except ValueError:
                self.query_one("#hashids-output", Static).update("Error: Min Length must be an integer.")
                return None

        try:
            return HashidsLabManager(salt=salt, min_length=min_length, alphabet=alphabet)
        except ValueError as e:
            self.query_one("#hashids-output", Static).update(f"Error initializing Hashids: {e}")
            return None


    @on(Button.Pressed, "#btn-hashids-encode")
    def handle_encode(self, event: Button.Pressed) -> None:
        """Handles encoding."""
        manager = self._get_manager()
        if not manager:
            return

        numbers_str = self.query_one("#hashids-numbers", Input).value
        if not numbers_str:
             self.query_one("#hashids-output", Static).update("Error: Please provide numbers to encode.")
             return

        try:
             numbers = [int(n) for n in numbers_str.strip().split()]
        except ValueError:
             self.query_one("#hashids-output", Static).update("Error: Numbers to encode must be space-separated integers.")
             return

        try:
             result = manager.encode(numbers)
             self.query_one("#hashids-output", Static).update(f"Encoded:\n[bold green]{result}[/bold green]")
        except ValueError as e:
             self.query_one("#hashids-output", Static).update(f"Error: {e}")


    @on(Button.Pressed, "#btn-hashids-decode")
    def handle_decode(self, event: Button.Pressed) -> None:
        """Handles decoding."""
        manager = self._get_manager()
        if not manager:
            return

        hash_str = self.query_one("#hashids-hash", Input).value
        if not hash_str:
             self.query_one("#hashids-output", Static).update("Error: Please provide a hashid to decode.")
             return

        try:
             result = manager.decode(hash_str)
             if not result:
                  self.query_one("#hashids-output", Static).update("Error: Could not decode. Check your salt and alphabet configuration.")
             else:
                  self.query_one("#hashids-output", Static).update(f"Decoded:\n[bold green]{' '.join(map(str, result))}[/bold green]")
        except ValueError as e:
             self.query_one("#hashids-output", Static).update(f"Error: {e}")
