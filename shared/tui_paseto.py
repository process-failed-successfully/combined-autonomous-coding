import json
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Select, TabbedContent, TabPane, TextArea
from shared.paseto_lab import PasetoManager

class PasetoLabTab(Container):
    """Tab for PASETO operations (Decode, Sign, Verify)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = PasetoManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]PASETO Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Decode Pane
                with TabPane("Decode / Inspect"):
                    with Vertical(classes="stat-box"):
                        yield Label("PASETO Token:")
                        yield TextArea(id="paseto-decode-input")

                        yield Label("Key (optional, for full verification):")
                        yield Input(id="paseto-decode-key", password=True)

                        with Horizontal():
                            yield Label("Version:")
                            yield Select(
                                [("v1", 1), ("v2", 2), ("v3", 3), ("v4", 4)],
                                value=4,
                                id="paseto-decode-version"
                            )
                            yield Label("Purpose:")
                            yield Select(
                                [("local", "local"), ("public", "public")],
                                value="local",
                                id="paseto-decode-purpose"
                            )

                        yield Button("Decode", id="btn-paseto-decode", variant="primary")

                    with Horizontal():
                        with Vertical(classes="stat-box"):
                            yield Label("[bold]Payload[/bold]")
                            yield RichLog(id="paseto-decode-payload", wrap=True, highlight=True, markup=True)
                        with Vertical(classes="stat-box"):
                            yield Label("[bold]Footer[/bold]")
                            yield RichLog(id="paseto-decode-footer", wrap=True, highlight=True, markup=True)

                # Sign Pane
                with TabPane("Sign / Create"):
                    with Vertical(classes="stat-box"):
                        yield Label("Payload (JSON):")
                        yield TextArea(id="paseto-sign-payload", text='{"sub": "1234567890", "name": "John Doe", "iat": 1516239022}')

                        yield Label("Key Material (string/bytes):")
                        yield Input(id="paseto-sign-key", password=True, placeholder="e.g., 32-byte secret for v4.local")

                        yield Label("Footer (JSON, optional):")
                        yield Input(id="paseto-sign-footer")

                        with Horizontal():
                            yield Label("Version:")
                            yield Select(
                                [("v1", 1), ("v2", 2), ("v3", 3), ("v4", 4)],
                                value=4,
                                id="paseto-sign-version"
                            )
                            yield Label("Purpose:")
                            yield Select(
                                [("local", "local"), ("public", "public")],
                                value="local",
                                id="paseto-sign-purpose"
                            )

                        yield Button("Generate Token", id="btn-paseto-sign", variant="success")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Generated PASETO Token[/bold]")
                        yield TextArea(id="paseto-sign-output", read_only=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-paseto-decode":
            self._handle_decode()
        elif event.button.id == "btn-paseto-sign":
            self._handle_sign()

    def _handle_decode(self) -> None:
        token = self.query_one("#paseto-decode-input", TextArea).text.strip()
        key_input = self.query_one("#paseto-decode-key", Input).value.strip()
        version = self.query_one("#paseto-decode-version", Select).value
        purpose = self.query_one("#paseto-decode-purpose", Select).value

        payload_log = self.query_one("#paseto-decode-payload", RichLog)
        footer_log = self.query_one("#paseto-decode-footer", RichLog)

        payload_log.clear()
        footer_log.clear()

        if not token:
            payload_log.write("[red]Error: Token cannot be empty[/red]")
            return

        try:
            key = None
            if key_input:
                key = self.manager.create_key(version, purpose, key_input.encode('utf-8'))

            res = self.manager.decode_token(token, key=key)

            if key:
                 payload_log.write("[green]Token signature verified![/green]\n")
            else:
                 payload_log.write("[yellow]Token decoded without verification (structural only)[/yellow]\n")

            payload_log.write(f"Version: {res.get('version')}")
            payload_log.write(f"Purpose: {res.get('purpose')}")
            payload_log.write(json.dumps(res.get("payload", {}), indent=2))

            if res.get("footer"):
                footer_log.write(json.dumps(res.get("footer", {}), indent=2))
            else:
                footer_log.write("No footer present.")

        except Exception as e:
            payload_log.write(f"[red]Error decoding token: {e}[/red]")

    def _handle_sign(self) -> None:
        payload_text = self.query_one("#paseto-sign-payload", TextArea).text.strip()
        key_input = self.query_one("#paseto-sign-key", Input).value.strip()
        footer_text = self.query_one("#paseto-sign-footer", Input).value.strip()
        version = self.query_one("#paseto-sign-version", Select).value
        purpose = self.query_one("#paseto-sign-purpose", Select).value

        output = self.query_one("#paseto-sign-output", TextArea)

        if not payload_text:
            output.text = "Error: Payload cannot be empty."
            return

        if not key_input:
            output.text = "Error: Key material cannot be empty."
            return

        try:
            payload = json.loads(payload_text)
            footer = json.loads(footer_text) if footer_text else None

            key = self.manager.create_key(version, purpose, key_input.encode('utf-8'))
            token = self.manager.encode_token(payload, key, footer=footer)
            output.text = token
        except json.JSONDecodeError as e:
            output.text = f"JSON Parse Error: {e}"
        except Exception as e:
            output.text = f"Error signing token: {e}"


def run_tui():
    """Entry point for testing the PASETO TUI directly."""
    from textual.app import App
    class TuiApp(App):
        def compose(self) -> ComposeResult:
            yield PasetoLabTab()
    app = TuiApp()
    app.run()

async def run_tui_async():
    """Async entry point for launching from main app."""
    from textual.app import App
    class TuiApp(App):
        def compose(self) -> ComposeResult:
            yield PasetoLabTab()
    app = TuiApp()
    await app.run_async()

if __name__ == "__main__":
    run_tui()
