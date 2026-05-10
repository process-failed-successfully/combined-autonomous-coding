import json
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Input, Button, RichLog, Select, Checkbox, TabbedContent, TabPane
from textual import on
from shared.cookie_lab import CookieLabManager

class CookieLabTab(Container):
    """Tab for Cookie parsing and generation."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = CookieLabManager()

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Parse
            with Vertical(id="cookie-parse-container", classes="stat-box"):
                yield Label("[bold]Parse Cookie[/bold]")
                yield Label("Cookie String:")
                yield Input(placeholder="session_id=123; Secure; HttpOnly", id="cookie-parse-input")
                yield Button("Parse", id="btn-cookie-parse", variant="primary")
                yield Label("Output:")
                yield RichLog(id="cookie-parse-log", wrap=True, highlight=True, markup=True)

            # Right Pane: Generate
            with Vertical(id="cookie-gen-container", classes="stat-box"):
                yield Label("[bold]Generate Cookie[/bold]")
                with Horizontal():
                    with Vertical():
                        yield Label("Name:")
                        yield Input(placeholder="session_id", id="cookie-gen-name")
                    with Vertical():
                        yield Label("Value:")
                        yield Input(placeholder="123", id="cookie-gen-value")

                with Horizontal():
                    with Vertical():
                        yield Label("Domain:")
                        yield Input(placeholder="example.com", id="cookie-gen-domain")
                    with Vertical():
                        yield Label("Path:")
                        yield Input(placeholder="/", id="cookie-gen-path")

                with Horizontal():
                    with Vertical():
                        yield Label("Max-Age (seconds):")
                        yield Input(placeholder="3600", id="cookie-gen-max-age", type="integer")
                    with Vertical():
                        yield Label("Expires (RFC 1123):")
                        yield Input(placeholder="Wed, 21 Oct 2015 07:28:00 GMT", id="cookie-gen-expires")

                with Horizontal():
                    yield Checkbox("Secure", id="cookie-gen-secure")
                    yield Checkbox("HttpOnly", id="cookie-gen-httponly")

                yield Label("SameSite:")
                yield Select.from_values(["Strict", "Lax", "None", ""], id="cookie-gen-samesite", value="")

                yield Button("Generate", id="btn-cookie-generate", variant="success")
                yield Label("Output:")
                yield RichLog(id="cookie-gen-log", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-cookie-parse")
    def on_parse(self, event: Button.Pressed) -> None:
        cookie_string = self.query_one("#cookie-parse-input", Input).value
        log = self.query_one("#cookie-parse-log", RichLog)
        log.clear()

        if not cookie_string:
            self.notify("Please enter a cookie string to parse.", severity="warning")
            return

        try:
            results = self.manager.parse(cookie_string)
            log.write(json.dumps(results, indent=2))
        except Exception as e:
            log.write(f"[red]Error parsing cookie: {e}[/red]")
            self.notify("Failed to parse cookie.", severity="error")

    @on(Button.Pressed, "#btn-cookie-generate")
    def on_generate(self, event: Button.Pressed) -> None:
        name = self.query_one("#cookie-gen-name", Input).value
        value = self.query_one("#cookie-gen-value", Input).value
        domain = self.query_one("#cookie-gen-domain", Input).value
        path = self.query_one("#cookie-gen-path", Input).value
        max_age = self.query_one("#cookie-gen-max-age", Input).value
        expires = self.query_one("#cookie-gen-expires", Input).value
        secure = self.query_one("#cookie-gen-secure", Checkbox).value
        httponly = self.query_one("#cookie-gen-httponly", Checkbox).value
        samesite = self.query_one("#cookie-gen-samesite", Select).value

        log = self.query_one("#cookie-gen-log", RichLog)
        log.clear()

        if not name or not value:
            self.notify("Name and Value are required.", severity="warning")
            return

        try:
            result = self.manager.generate(
                name=name,
                value=value,
                domain=domain if domain else None,
                path=path if path else None,
                max_age=max_age if max_age else None,
                expires=expires if expires else None,
                secure=secure,
                httponly=httponly,
                samesite=samesite if samesite else None
            )
            log.write(result)
        except Exception as e:
            log.write(f"[red]Error generating cookie: {e}[/red]")
            self.notify("Failed to generate cookie.", severity="error")
