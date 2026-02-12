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
        self._check_dependency()

    def _check_dependency(self):
        if not HAS_QR:
            raise ImportError("qrcode library is not installed. Please run: pip install qrcode")

    def generate(self, text: str, output_path: Optional[Path] = None, **kwargs) -> None:
        """
        Generates a QR code.
        If output_path is provided, saves to file.
        Otherwise, prints ASCII representation to console.
        """
        qr = qrcode.QRCode(
            version=kwargs.get("version", 1),
            error_correction=kwargs.get("error_correction", qrcode.constants.ERROR_CORRECT_L),
            box_size=kwargs.get("box_size", 10),
            border=kwargs.get("border", 4),
        )
        qr.add_data(text)
        qr.make(fit=True)

        if output_path:
            # Image generation
            fill_color = kwargs.get("fill_color", "black")
            back_color = kwargs.get("back_color", "white")
            img = qr.make_image(fill_color=fill_color, back_color=back_color)
            img.save(output_path)
            console.print(f"[green]✅ QR code saved to {output_path}[/green]")
        else:
            # ASCII generation
            console.print(Panel(f"QR Code for: [bold]{text}[/bold]", title="QR Lab"))
            qr.print_ascii(tty=True)

    def generate_wifi(self, ssid: str, password: Optional[str] = None, security_type: str = "WPA", hidden: bool = False) -> str:
        """Generates WiFi configuration string."""
        # Format: WIFI:S:<SSID>;T:<WPA|WEP|>;P:<password>;H:<true|false|>;;

        # Escape special characters in SSID and Password
        def escape(s):
            if not s: return ""
            return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace(":", "\\:")

        esc_ssid = escape(ssid)
        esc_pass = escape(password)

        if not password:
            security_type = "nopass"

        return f"WIFI:S:{esc_ssid};T:{security_type};P:{esc_pass};H:{str(hidden).lower()};;"

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

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
