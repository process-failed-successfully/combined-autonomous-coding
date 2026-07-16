from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Select, TabbedContent, TabPane, TextArea
import json
from shared.jwt_lab import JWTManager


class JwtLabTab(Container):
    """Tab for JWT operations (Decode, Sign, Verify)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = JWTManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]JWT Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Decode Pane
                with TabPane("Decode"):
                    with Vertical(classes="stat-box"):
                        yield Label("Token:")
                        yield TextArea(id="jwt-decode-input")
                        yield Button("Decode", id="btn-jwt-decode", variant="primary")

                    with Horizontal():
                        with Vertical(classes="stat-box"):
                            yield Label("[bold]Header[/bold]")
                            yield RichLog(id="jwt-decode-header", wrap=True, highlight=True, markup=True)
                        with Vertical(classes="stat-box"):
                            yield Label("[bold]Payload[/bold]")
                            yield RichLog(id="jwt-decode-payload", wrap=True, highlight=True, markup=True)

                # Sign Pane
                with TabPane("Sign"):
                    with Horizontal(classes="stat-box"):
                        with Vertical():
                            yield Label("Algorithm:")
                            yield Select.from_values(["HS256", "HS384", "HS512"], id="jwt-sign-algo", value="HS256")
                        with Vertical():
                            yield Label("Secret:")
                            yield Input(placeholder="Secret key...", id="jwt-sign-secret", password=True)

                    with Vertical(classes="stat-box"):
                        yield Label("Payload (JSON):")
                        yield TextArea('{"sub": "1234567890", "name": "John Doe", "iat": 1516239022}', id="jwt-sign-payload", language="json")
                        yield Button("Sign Token", id="btn-jwt-sign", variant="warning")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Generated Token[/bold]")
                        yield TextArea(id="jwt-sign-output", read_only=True)

                # Verify Pane
                with TabPane("Verify"):
                    with Vertical(classes="stat-box"):
                        yield Label("Token:")
                        yield TextArea(id="jwt-verify-token")
                        yield Label("Secret (HMAC/PEM):")
                        yield Input(placeholder="Secret key... (Leave empty if using JWKS)", id="jwt-verify-secret", password=True)
                        yield Label("Or JWKS URL:")
                        yield Input(placeholder="https://example.com/.well-known/jwks.json", id="jwt-verify-jwks-url")
                        yield Button("Verify Signature", id="btn-jwt-verify", variant="success")

                    yield Label("[bold]Verification Result[/bold]")
                    yield RichLog(id="jwt-verify-result", wrap=True, highlight=True, markup=True)

                # Crack Pane
                with TabPane("Crack"):
                    with Vertical(classes="stat-box"):
                        yield Label("Token:")
                        yield TextArea(id="jwt-crack-token")
                        yield Label("Wordlist Path:")
                        yield Input(placeholder="Path to wordlist file...", id="jwt-crack-wordlist")
                        yield Button("Crack Token", id="btn-jwt-crack", variant="error")

                    yield Label("[bold]Crack Result[/bold]")
                    yield RichLog(id="jwt-crack-result", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-jwt-decode":
            self.decode_token()
        elif event.button.id == "btn-jwt-sign":
            self.sign_token()
        elif event.button.id == "btn-jwt-verify":
            self.verify_token()
        elif event.button.id == "btn-jwt-crack":
            self.crack_token()

    def decode_token(self) -> None:
        token = self.query_one("#jwt-decode-input", TextArea).text.strip()
        header_log = self.query_one("#jwt-decode-header", RichLog)
        payload_log = self.query_one("#jwt-decode-payload", RichLog)

        header_log.clear()
        payload_log.clear()

        if not token:
            self.notify("Token required.", severity="error")
            return

        try:
            decoded = self.manager.decode_token(token)
            header_log.write(json.dumps(decoded["header"], indent=2))
            payload_log.write(json.dumps(decoded["payload"], indent=2))
            self.notify("Token decoded.")
        except Exception as e:
            self.notify(f"Error decoding token: {e}", severity="error")
            header_log.write(f"[red]Error: {e}[/red]")

    def sign_token(self) -> None:
        payload_text = self.query_one("#jwt-sign-payload", TextArea).text
        secret = self.query_one("#jwt-sign-secret", Input).value
        algo = self.query_one("#jwt-sign-algo", Select).value

        output_area = self.query_one("#jwt-sign-output", TextArea)
        output_area.text = ""

        if not secret:
            self.notify("Secret required.", severity="error")
            return

        # Explicit cast to str to satisfy mypy, though value should be str
        algo_str = str(algo) if algo else "HS256"

        try:
            payload = json.loads(payload_text)
            token = self.manager.sign_token(payload, secret, algo_str)
            output_area.text = token
            self.notify("Token signed.")
        except json.JSONDecodeError:
            self.notify("Invalid JSON payload.", severity="error")
        except Exception as e:
            self.notify(f"Error signing token: {e}", severity="error")

    def verify_token(self) -> None:
        token = self.query_one("#jwt-verify-token", TextArea).text.strip()
        secret = self.query_one("#jwt-verify-secret", Input).value.strip()
        jwks_url = self.query_one("#jwt-verify-jwks-url", Input).value.strip()
        result_log = self.query_one("#jwt-verify-result", RichLog)

        result_log.clear()

        if not token:
            self.notify("Token is required.", severity="error")
            return

        if not secret and not jwks_url:
            self.notify("Either Secret or JWKS URL is required.", severity="error")
            return

        try:
            decoded = self.manager.verify_token(token, secret=secret, jwks_url=jwks_url)
            result_log.write("[bold green]✅ Signature Verified[/bold green]")
            result_log.write("\n[bold]Header:[/bold]")
            result_log.write(json.dumps(decoded["header"], indent=2))
            result_log.write("\n[bold]Payload:[/bold]")
            result_log.write(json.dumps(decoded["payload"], indent=2))
            self.notify("Verification successful.")
        except Exception as e:
            result_log.write(f"[bold red]❌ Verification Failed: {e}[/bold red]")
            self.notify("Verification failed.", severity="error")

    def crack_token(self) -> None:
        token = self.query_one("#jwt-crack-token", TextArea).text.strip()
        wordlist = self.query_one("#jwt-crack-wordlist", Input).value.strip()
        result_log = self.query_one("#jwt-crack-result", RichLog)

        result_log.clear()

        if not token or not wordlist:
            self.notify("Token and Wordlist Path required.", severity="error")
            return

        try:
            secret = self.manager.crack_token(token, wordlist)
            if secret:
                result_log.write(f"[bold green]✅ CRACKED! Secret found: {secret}[/bold green]")
                self.notify("Token successfully cracked.")
            else:
                result_log.write("[bold red]❌ Failed to crack token. Secret not in wordlist.[/bold red]")
                self.notify("Token cracking failed.")
        except Exception as e:
            result_log.write(f"[bold red]❌ Error: {e}[/bold red]")
            self.notify(f"Error cracking token: {e}", severity="error")
