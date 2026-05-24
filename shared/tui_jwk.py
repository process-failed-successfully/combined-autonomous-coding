from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea, Select, Input
from shared.jwk_lab import JwkManager
import json

class JwkLabTab(Container):
    """Tab for JWK Generator & Converter."""

    DEFAULT_CSS = """
    JwkLabTab {
        layout: vertical;
        height: 100%;
        overflow-y: auto;
    }

    .jwk-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    .jwk-box-horizontal {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
        layout: horizontal;
    }

    #jwk-output {
        height: 1fr;
    }

    #pem-input {
        height: 10;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]JWK Lab (Generate, PEM to JWK, JWK to PEM)[/bold]", classes="welcome-text")

            # Output Section
            with Vertical(classes="jwk-box"):
                yield Label("Output Area (JWK JSON or PEM):")
                yield TextArea(id="jwk-output", show_line_numbers=False)

            # Generate Section
            with Vertical(classes="jwk-box"):
                yield Label("[bold]Generate JWK[/bold]")
                with Horizontal():
                    yield Select((("RSA", "RSA"), ("EC", "EC")), id="gen-type", value="RSA")
                    yield Input(placeholder="RSA Size (e.g. 2048)", id="gen-size", value="2048")
                    yield Select((("P-256", "P-256"), ("P-384", "P-384"), ("P-521", "P-521")), id="gen-curve", value="P-256")
                    yield Input(placeholder="Key ID (kid)", id="gen-kid")
                yield Button("Generate", id="btn-jwk-generate", variant="primary")

            # PEM to JWK Section
            with Vertical(classes="jwk-box"):
                yield Label("[bold]Convert PEM to JWK[/bold]")
                yield TextArea(id="pem-input", show_line_numbers=False)
                with Horizontal():
                    yield Input(placeholder="Password (if encrypted)", id="pem-password", password=True)
                    yield Input(placeholder="Key ID (kid)", id="pem-kid")
                yield Button("PEM -> JWK", id="btn-jwk-pem2jwk", variant="success")

            # JWK to PEM Section
            with Vertical(classes="jwk-box"):
                yield Label("[bold]Convert JWK to PEM[/bold]")
                yield Label("Paste JWK JSON in Output Area, then click below.")
                yield Input(placeholder="Password (for encrypting private key PEM)", id="jwk-password", password=True)
                yield Button("JWK -> PEM", id="btn-jwk-jwk2pem", variant="warning")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-jwk-generate":
            self.generate_jwk()
        elif event.button.id == "btn-jwk-pem2jwk":
            self.pem_to_jwk()
        elif event.button.id == "btn-jwk-jwk2pem":
            self.jwk_to_pem()

    def generate_jwk(self) -> None:
        manager = JwkManager()
        key_type = self.query_one("#gen-type", Select).value
        size_val = self.query_one("#gen-size", Input).value
        curve_val = self.query_one("#gen-curve", Select).value
        kid_val = self.query_one("#gen-kid", Input).value
        output_area = self.query_one("#jwk-output", TextArea)

        try:
            if key_type == "RSA":
                size = int(size_val) if size_val else 2048
                key = manager.generate_rsa_key(key_size=size)
                jwk_dict = manager._rsa_to_jwk(key)
            else: # EC
                key = manager.generate_ec_key(curve_name=curve_val)
                jwk_dict = manager._ec_to_jwk(key)

            if kid_val:
                jwk_dict["kid"] = kid_val

            output_area.text = json.dumps(jwk_dict, indent=2)
            self.notify("JWK Generated.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def pem_to_jwk(self) -> None:
        manager = JwkManager()
        pem_text = self.query_one("#pem-input", TextArea).text
        password_val = self.query_one("#pem-password", Input).value
        kid_val = self.query_one("#pem-kid", Input).value
        output_area = self.query_one("#jwk-output", TextArea)

        if not pem_text.strip():
            self.notify("PEM input is empty.", severity="warning")
            return

        try:
            pwd = password_val if password_val else None
            jwk_dict = manager.pem_to_jwk(pem_text, password=pwd)
            if kid_val:
                jwk_dict["kid"] = kid_val

            output_area.text = json.dumps(jwk_dict, indent=2)
            self.notify("Converted PEM to JWK.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def jwk_to_pem(self) -> None:
        manager = JwkManager()
        jwk_text = self.query_one("#jwk-output", TextArea).text
        password_val = self.query_one("#jwk-password", Input).value
        output_area = self.query_one("#jwk-output", TextArea)

        if not jwk_text.strip():
            self.notify("Output Area (JWK) is empty.", severity="warning")
            return

        try:
            jwk_dict = json.loads(jwk_text)
            pwd = password_val if password_val else None
            pem_str = manager.jwk_to_pem(jwk_dict, password=pwd)
            output_area.text = pem_str
            self.notify("Converted JWK to PEM.")
        except json.JSONDecodeError as e:
            output_area.text = f"JSON Parse Error: {e}"
            self.notify("Invalid JSON in Output Area.", severity="error")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")
