import json
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, TextArea, Select, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from rich.syntax import Syntax

from shared.jwt_lab import JWTManager

class JwtLabTab(Container):
    """Tab for experimenting with JWT (JSON Web Tokens)."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]JWT Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                with TabPane("Decode"):
                    yield Label("Paste JWT Token:")
                    yield TextArea(id="jwt-decode-input", language="text", show_line_numbers=False)
                    yield Button("Decode", id="btn-jwt-decode", variant="primary")

                    yield Label("[bold]Decoded Header[/bold]")
                    yield RichLog(id="jwt-decode-header", wrap=True, highlight=True, markup=True, height=5)

                    yield Label("[bold]Decoded Payload[/bold]")
                    yield RichLog(id="jwt-decode-payload", wrap=True, highlight=True, markup=True)

                with TabPane("Sign"):
                    yield Label("Payload (JSON):")
                    yield TextArea(id="jwt-sign-payload", language="json", show_line_numbers=True)

                    with Horizontal(classes="stat-box"):
                        yield Label("Secret:")
                        yield Input(placeholder="Secret key...", id="jwt-sign-secret", password=True)
                        yield Label("Algo:")
                        yield Select.from_values(["HS256"], id="jwt-sign-algo", value="HS256")

                    yield Button("Sign Token", id="btn-jwt-sign", variant="success")

                    yield Label("[bold]Generated Token[/bold]")
                    yield TextArea(id="jwt-sign-output", read_only=True, show_line_numbers=False)

                with TabPane("Verify"):
                    yield Label("JWT Token:")
                    yield TextArea(id="jwt-verify-token", language="text", show_line_numbers=False)

                    with Horizontal(classes="stat-box"):
                        yield Label("Secret:")
                        yield Input(placeholder="Secret key...", id="jwt-verify-secret", password=True)

                    yield Button("Verify Signature", id="btn-jwt-verify", variant="warning")

                    yield Label("[bold]Result[/bold]")
                    yield RichLog(id="jwt-verify-result", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-jwt-decode")
    def on_decode(self) -> None:
        token = self.query_one("#jwt-decode-input", TextArea).text.strip()
        header_log = self.query_one("#jwt-decode-header", RichLog)
        payload_log = self.query_one("#jwt-decode-payload", RichLog)

        header_log.clear()
        payload_log.clear()

        if not token:
            header_log.write("[red]Error: Token required.[/red]")
            return

        try:
            decoded = JWTManager.decode_token(token)

            header_json = json.dumps(decoded["header"], indent=2)
            payload_json = json.dumps(decoded["payload"], indent=2)

            header_log.write(Syntax(header_json, "json", theme="monokai"))
            payload_log.write(Syntax(payload_json, "json", theme="monokai"))

        except Exception as e:
            header_log.write(f"[bold red]Error decoding token:[/bold red] {e}")

    @on(Button.Pressed, "#btn-jwt-sign")
    def on_sign(self) -> None:
        payload_text = self.query_one("#jwt-sign-payload", TextArea).text
        secret = self.query_one("#jwt-sign-secret", Input).value
        algo = self.query_one("#jwt-sign-algo", Select).value or "HS256"
        output = self.query_one("#jwt-sign-output", TextArea)

        if not payload_text or not secret:
            self.notify("Payload and Secret required.", severity="error")
            return

        try:
            payload = json.loads(payload_text)
            token = JWTManager.sign_token(payload, secret, algo=algo)
            output.text = token
            self.notify("Token generated.")
        except json.JSONDecodeError:
            self.notify("Invalid JSON payload.", severity="error")
        except Exception as e:
            self.notify(f"Error signing token: {e}", severity="error")

    @on(Button.Pressed, "#btn-jwt-verify")
    def on_verify(self) -> None:
        token = self.query_one("#jwt-verify-token", TextArea).text.strip()
        secret = self.query_one("#jwt-verify-secret", Input).value
        result_log = self.query_one("#jwt-verify-result", RichLog)

        result_log.clear()

        if not token or not secret:
            result_log.write("[red]Token and Secret required.[/red]")
            return

        try:
            JWTManager.verify_token(token, secret)
            result_log.write("[bold green]✅ Signature Verified[/bold green]")
            # Optionally show decoded content too
            decoded = JWTManager.decode_token(token)
            result_log.write(Syntax(json.dumps(decoded["payload"], indent=2), "json", theme="monokai"))

        except Exception as e:
            result_log.write(f"[bold red]❌ Verification Failed:[/bold red] {e}")
