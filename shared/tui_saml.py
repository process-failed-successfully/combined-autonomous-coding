from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, Checkbox, TextArea
from textual import on
from shared.saml_lab import SamlLabManager


class SamlLabTab(Container):
    """Tab for SAML Lab operations."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]SAML Lab[/bold]", classes="welcome-text")

            with Vertical(classes="stat-box"):
                yield Label("Input SAML String (AuthnRequest, Response, etc.):")

                # We use a TextArea so users can paste large multiline SAML chunks easily
                yield TextArea(id="saml-input", show_line_numbers=True)

                with Horizontal():
                    yield Checkbox("Deflate (zlib) decompression (Required for HTTP-Redirect binding)", id="saml-inflate-chk", value=True)

                yield Button("Decode & Parse", id="btn-saml-decode", variant="primary")

                yield Label("Decoded Result:")
                yield TextArea(id="saml-result", show_line_numbers=True, read_only=True)

    @on(Button.Pressed, "#btn-saml-decode")
    def on_decode(self) -> None:
        manager = SamlLabManager()
        saml_str = self.query_one("#saml-input", TextArea).text.strip()
        inflate = self.query_one("#saml-inflate-chk", Checkbox).value
        result_area = self.query_one("#saml-result", TextArea)

        if not saml_str:
            self.notify("Please provide a SAML string.", severity="error")
            return

        try:
            result = manager.decode(saml_str, inflate=inflate)
            result_area.text = result
            self.notify("SAML Decoded successfully.", severity="information")
        except Exception as e:
            result_area.text = f"Error decoding SAML:\n\n{str(e)}"
            self.notify("SAML Decode failed.", severity="error")
