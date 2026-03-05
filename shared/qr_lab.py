"""
QR Lab
======

Utilities for QR code generation using the qrcode library.
"""

import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel

try:
    import qrcode
    import qrcode.constants
    HAS_QR = True
except ImportError:
    HAS_QR = False

console = Console()


class QRLabManager:
    """Manages QR code operations."""

    def __init__(self):
        pass

    def _check_dependency(self):
        if not HAS_QR:
            raise ImportError("qrcode library is not installed. Please run: pip install qrcode")

    def generate(self, text: str, output_path: Optional[Path] = None, **kwargs) -> None:
        """
        Generates a QR code.
        If output_path is provided, saves to file.
        Otherwise, prints ASCII representation to console.
        """
        qr = self._create_qr(text, **kwargs)

        if output_path:
            # Image generation
            img = self._create_image(qr, **kwargs)
            img.save(output_path)
            console.print(f"[green]✅ QR code saved to {output_path}[/green]")
        else:
            # ASCII generation
            console.print(Panel(f"QR Code for: [bold]{text}[/bold]", title="QR Lab"))
            qr.print_ascii(tty=True)

    def generate_image(self, text: str, **kwargs):
        """Generates a PIL image object for the QR code."""
        qr = self._create_qr(text, **kwargs)
        return self._create_image(qr, **kwargs)

    def generate_ascii(self, text: str, **kwargs) -> str:
        """Generates an ASCII string representation of the QR code."""
        qr = self._create_qr(text, **kwargs)

        # Capture stdout to string
        import io
        f = io.StringIO()
        qr.print_ascii(out=f, tty=False)
        return f.getvalue()

    def _create_qr(self, text: str, **kwargs):
        self._check_dependency()
        qr = qrcode.QRCode(
            version=kwargs.get("version", 1),
            error_correction=kwargs.get("error_correction", qrcode.constants.ERROR_CORRECT_L),
            box_size=kwargs.get("box_size", 10),
            border=kwargs.get("border", 4),
        )
        qr.add_data(text)
        qr.make(fit=True)
        return qr

    def _create_image(self, qr, **kwargs):
        fill_color = kwargs.get("fill_color", "black")
        back_color = kwargs.get("back_color", "white")
        return qr.make_image(fill_color=fill_color, back_color=back_color)

    def generate_wifi(self, ssid: str, password: Optional[str] = None, security_type: str = "WPA", hidden: bool = False) -> str:
        """Generates WiFi configuration string."""
        # Format: WIFI:S:<SSID>;T:<WPA|WEP|>;P:<password>;H:<true|false|>;;

        # Escape special characters in SSID and Password
        def escape(s):
            if not s:
                return ""
            return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace(":", "\\:")

        esc_ssid = escape(ssid)
        esc_pass = escape(password)

        if not password:
            security_type = "nopass"

        return f"WIFI:S:{esc_ssid};T:{security_type};P:{esc_pass};H:{str(hidden).lower()};;"

    def generate_email(self, to: str, subject: str = "", body: str = "") -> str:
        """Generates Email (mailto) string."""
        # mailto:user@example.com?subject=foo&body=bar
        from urllib.parse import quote

        uri = f"mailto:{to}"
        params = []
        if subject:
            params.append(f"subject={quote(subject)}")
        if body:
            params.append(f"body={quote(body)}")

        if params:
            uri += "?" + "&".join(params)

        return uri

    def generate_sms(self, phone: str, message: str = "") -> str:
        """Generates SMS string."""
        # sms:+1234567890:Message
        # Note: formatting varies by OS (iOS uses &body=, Android often just :body)
        # Using common format: sms:number?body=message
        from urllib.parse import quote
        uri = f"sms:{phone}"
        if message:
            uri += f"?body={quote(message)}"
        return uri

    def generate_geo(self, lat: float, lon: float) -> str:
        """Generates Geo URI."""
        return f"geo:{lat},{lon}"


def run_qr_lab_logic(args):
    """Entry point for QR lab CLI."""
    try:
        manager = QRLabManager()

        if args.action == "gen":
            output = Path(args.output) if args.output else None
            manager.generate(
                args.text,
                output_path=output,
                fill_color=args.fill_color,
                back_color=args.back_color
            )

        elif args.action == "wifi":
            wifi_str = manager.generate_wifi(
                args.ssid,
                args.password,
                args.type,
                args.hidden
            )

            output = Path(args.output) if args.output else None

            if output:
                console.print(f"Generating WiFi QR Code for SSID: [bold]{args.ssid}[/bold]")
                manager.generate(wifi_str, output_path=output)
            else:
                # For console, we print the string too so user verifies
                console.print(f"WiFi Config: [dim]{wifi_str}[/dim]")
                manager.generate(wifi_str)

        elif args.action == "email":
            email_str = manager.generate_email(args.to, args.subject, args.body)
            output = Path(args.output) if args.output else None
            if output:
                manager.generate(email_str, output_path=output)
            else:
                console.print(f"Email Config: [dim]{email_str}[/dim]")
                manager.generate(email_str)

        elif args.action == "sms":
            sms_str = manager.generate_sms(args.phone, args.message)
            output = Path(args.output) if args.output else None
            if output:
                manager.generate(sms_str, output_path=output)
            else:
                console.print(f"SMS Config: [dim]{sms_str}[/dim]")
                manager.generate(sms_str)

        elif args.action == "geo":
            geo_str = manager.generate_geo(args.lat, args.lon)
            output = Path(args.output) if args.output else None
            if output:
                manager.generate(geo_str, output_path=output)
            else:
                console.print(f"Geo Config: [dim]{geo_str}[/dim]")
                manager.generate(geo_str)

        elif args.action == "tui":
            from shared.tui import AgentTUI
            import asyncio
            app = AgentTUI(project_dir=Path.cwd(), initial_tab="tab-qr")
            asyncio.run(app.run_async())

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
