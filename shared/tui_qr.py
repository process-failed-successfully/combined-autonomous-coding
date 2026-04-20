import io
import os
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, Input, TabbedContent, TabPane, Select, RichLog, Checkbox, TextArea
from textual import on

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
except ImportError:
    # Fallback constants if qrcode not installed (though manager handles check)
    ERROR_CORRECT_L = 1
    ERROR_CORRECT_M = 0
    ERROR_CORRECT_Q = 3
    ERROR_CORRECT_H = 2

from shared.qr_lab import QRLabManager


class QrLabTab(Container):
    """Tab for QR Code Generation."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = QRLabManager()

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Configuration
            with Vertical(id="qr-config-container", classes="stat-box"):
                yield Label("[bold]QR Code Configuration[/bold]")

                with TabbedContent(id="qr-input-tabs"):
                    with TabPane("Text", id="qr-tab-text"):
                        yield Label("Content:")
                        yield TextArea(id="qr-text-content")

                    with TabPane("Wi-Fi", id="qr-tab-wifi"):
                        yield Label("SSID:")
                        yield Input(placeholder="Network Name", id="qr-wifi-ssid")
                        yield Label("Password:")
                        yield Input(placeholder="Password", id="qr-wifi-pass", password=True)
                        yield Checkbox("Hidden Network", id="qr-wifi-hidden")
                        yield Label("Security:")
                        yield Select.from_values(["WPA", "WEP", "nopass"], id="qr-wifi-type", value="WPA")

                    with TabPane("Email", id="qr-tab-email"):
                        yield Label("To:")
                        yield Input(placeholder="user@example.com", id="qr-email-to")
                        yield Label("Subject:")
                        yield Input(placeholder="Subject", id="qr-email-subject")
                        yield Label("Body:")
                        yield TextArea(id="qr-email-body")

                    with TabPane("SMS", id="qr-tab-sms"):
                        yield Label("Phone Number:")
                        yield Input(placeholder="+1234567890", id="qr-sms-phone")
                        yield Label("Message:")
                        yield TextArea(id="qr-sms-msg")

                    with TabPane("Geo", id="qr-tab-geo"):
                        yield Label("Latitude:")
                        yield Input(placeholder="37.7749", id="qr-geo-lat")
                        yield Label("Longitude:")
                        yield Input(placeholder="-122.4194", id="qr-geo-lon")

                    with TabPane("VCard", id="qr-tab-vcard"):
                        yield Label("First Name:")
                        yield Input(placeholder="Jane", id="qr-vcard-first")
                        yield Label("Last Name:")
                        yield Input(placeholder="Doe", id="qr-vcard-last")
                        yield Label("Organization:")
                        yield Input(placeholder="Company Inc.", id="qr-vcard-org")
                        yield Label("Title:")
                        yield Input(placeholder="Software Engineer", id="qr-vcard-title")
                        yield Label("Phone:")
                        yield Input(placeholder="+1234567890", id="qr-vcard-phone")
                        yield Label("Email:")
                        yield Input(placeholder="jane@example.com", id="qr-vcard-email")
                        yield Label("URL:")
                        yield Input(placeholder="https://example.com", id="qr-vcard-url")

                yield Label("Settings:")
                with Horizontal():
                    yield Label("Correction:")
                    yield Select.from_values(["L", "M", "Q", "H"], id="qr-correction", value="L")

                with Horizontal():
                    yield Label("Box Size:")
                    yield Input(value="10", id="qr-box-size", type="integer")
                    yield Label("Border:")
                    yield Input(value="4", id="qr-border", type="integer")

                with Horizontal():
                    yield Label("Filename:")
                    yield Input(placeholder="qr_code.png", id="qr-filename")

                with Horizontal():
                    yield Button("Generate Preview", id="btn-qr-preview", variant="primary")
                    yield Button("Save PNG", id="btn-qr-save", variant="success")

            # Right Pane: Preview
            with Vertical(id="qr-preview-container"):
                yield Label("[bold]ASCII Preview[/bold]")
                yield RichLog(id="qr-preview-log", wrap=False, highlight=False, markup=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-qr-preview":
            self.generate_preview()
        elif event.button.id == "btn-qr-save":
            self.save_png()

    def get_content(self) -> str:
        """Constructs the content string based on active tab."""
        tabs = self.query_one("#qr-input-tabs", TabbedContent)
        active_tab = tabs.active

        if active_tab == "qr-tab-text":
            return self.query_one("#qr-text-content", TextArea).text

        elif active_tab == "qr-tab-wifi":
            ssid = self.query_one("#qr-wifi-ssid", Input).value
            pwd = self.query_one("#qr-wifi-pass", Input).value
            sec = self.query_one("#qr-wifi-type", Select).value or "WPA"
            hidden = self.query_one("#qr-wifi-hidden", Checkbox).value
            return self.manager.generate_wifi(ssid, pwd, sec, hidden)

        elif active_tab == "qr-tab-email":
            to = self.query_one("#qr-email-to", Input).value
            subj = self.query_one("#qr-email-subject", Input).value
            body = self.query_one("#qr-email-body", TextArea).text
            return self.manager.generate_email(to, subj, body)

        elif active_tab == "qr-tab-sms":
            phone = self.query_one("#qr-sms-phone", Input).value
            msg = self.query_one("#qr-sms-msg", TextArea).text
            return self.manager.generate_sms(phone, msg)

        elif active_tab == "qr-tab-geo":
            try:
                lat = float(self.query_one("#qr-geo-lat", Input).value)
                lon = float(self.query_one("#qr-geo-lon", Input).value)
                return self.manager.generate_geo(lat, lon)
            except ValueError:
                self.notify("Invalid coordinates.", severity="error")
                return ""

        elif active_tab == "qr-tab-vcard":
            first = self.query_one("#qr-vcard-first", Input).value
            if not first:
                self.notify("First Name is required for VCard.", severity="error")
                return ""
            last = self.query_one("#qr-vcard-last", Input).value
            org = self.query_one("#qr-vcard-org", Input).value
            title = self.query_one("#qr-vcard-title", Input).value
            phone = self.query_one("#qr-vcard-phone", Input).value
            email = self.query_one("#qr-vcard-email", Input).value
            url = self.query_one("#qr-vcard-url", Input).value
            return self.manager.generate_vcard(
                first_name=first, last_name=last, org=org, title=title, phone=phone, email=email, url=url
            )

        return ""

    def get_qr_kwargs(self) -> dict:
        """Returns kwargs for QR generation."""
        ecc_map = {"L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M, "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H}
        ecc_val = self.query_one("#qr-correction", Select).value or "L"

        try:
            box_size = int(self.query_one("#qr-box-size", Input).value)
        except ValueError:
            box_size = 10

        try:
            border = int(self.query_one("#qr-border", Input).value)
        except ValueError:
            border = 4

        return {
            "error_correction": ecc_map.get(ecc_val, ERROR_CORRECT_L),
            "box_size": box_size,
            "border": border
        }

    def generate_preview(self) -> None:
        content = self.get_content()
        if not content:
            self.notify("No content to encode.", severity="warning")
            return

        kwargs = self.get_qr_kwargs()

        try:
            ascii_art = self.manager.generate_ascii(content, **kwargs)
            log = self.query_one("#qr-preview-log", RichLog)
            log.clear()
            # Font handling in terminals can be tricky for QR blocks, but ASCII works generally
            log.write(ascii_art)
            self.notify("Preview generated.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def save_png(self) -> None:
        content = self.get_content()
        if not content:
            self.notify("No content to encode.", severity="warning")
            return

        kwargs = self.get_qr_kwargs()

        filename = self.query_one("#qr-filename", Input).value
        if not filename:
            filename = "qr_code.png"

        path = self.project_dir / filename

        try:
            img = self.manager.generate_image(content, **kwargs)
            img.save(path)
            self.notify(f"Saved to {path}")
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error")
