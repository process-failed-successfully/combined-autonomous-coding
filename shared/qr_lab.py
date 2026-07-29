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

    def decode_image(self, image_path: Path) -> list[str]:
        """Decodes QR code(s) from an image file."""
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            import cv2
        except ImportError:
            raise ImportError("opencv-python-headless is required for decoding QR codes. Run 'pip install opencv-python-headless'.")

        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to read image at {image_path}")

        detector = cv2.QRCodeDetector()
        # Use detectAndDecodeMulti to find all QR codes
        ret, decoded_info, points, straight_qrcode = detector.detectAndDecodeMulti(image)

        if not ret or not decoded_info:
            return []

        # decoded_info is a tuple of strings
        # Filter out empty strings which can happen if a QR code is detected but fails decoding
        return [info for info in decoded_info if info]

    def generate_ascii(self, text: str, **kwargs) -> str:
        """Generates an ASCII string representation of the QR code."""
        qr = self._create_qr(text, **kwargs)

        # Capture stdout to string
        import io
        f = io.StringIO()
        qr.print_ascii(out=f, tty=True)
        return f.getvalue()

    def _create_qr(self, text: str, **kwargs):
        self._check_dependency()
        err_corr = kwargs.get("error_correction", qrcode.constants.ERROR_CORRECT_L)
        if kwargs.get("logo"):
            err_corr = qrcode.constants.ERROR_CORRECT_H
        qr = qrcode.QRCode(
            version=kwargs.get("version", 1),
            error_correction=err_corr,
            box_size=kwargs.get("box_size", 10),
            border=kwargs.get("border", 4),
        )
        qr.add_data(text)
        qr.make(fit=True)
        return qr

    def _create_image(self, qr, **kwargs):
        fill_color = kwargs.get("fill_color", "black")
        back_color = kwargs.get("back_color", "white")
        logo = kwargs.get("logo")
        drawer_name = kwargs.get("drawer")
        color_mask_name = kwargs.get("color_mask")

        if logo or drawer_name or color_mask_name:
            import qrcode.image.styledpil
            from qrcode.image.styles.moduledrawers.pil import (
                SquareModuleDrawer, CircleModuleDrawer, RoundedModuleDrawer,
                VerticalBarsDrawer, HorizontalBarsDrawer
            )
            from qrcode.image.styles.colormasks import (
                SolidFillColorMask, RadialGradiantColorMask, SquareGradiantColorMask,
                HorizontalGradiantColorMask, VerticalGradiantColorMask
            )
            from PIL import ImageColor

            fg = ImageColor.getrgb(fill_color)
            bg = ImageColor.getrgb(back_color)

            # Mask
            mask_obj = SolidFillColorMask(back_color=bg, front_color=fg)
            if color_mask_name == "radial":
                mask_obj = RadialGradiantColorMask(back_color=bg, center_color=fg, edge_color=bg)
            elif color_mask_name == "square":
                mask_obj = SquareGradiantColorMask(back_color=bg, center_color=fg, edge_color=bg)
            elif color_mask_name == "horizontal":
                mask_obj = HorizontalGradiantColorMask(back_color=bg, left_color=fg, right_color=bg)
            elif color_mask_name == "vertical":
                mask_obj = VerticalGradiantColorMask(back_color=bg, top_color=fg, bottom_color=bg)

            # Drawer
            drawer_obj = SquareModuleDrawer()
            if drawer_name == "circle":
                drawer_obj = CircleModuleDrawer()
            elif drawer_name == "rounded":
                drawer_obj = RoundedModuleDrawer()
            elif drawer_name == "vertical":
                drawer_obj = VerticalBarsDrawer()
            elif drawer_name == "horizontal":
                drawer_obj = HorizontalBarsDrawer()

            return qr.make_image(
                image_factory=qrcode.image.styledpil.StyledPilImage,
                module_drawer=drawer_obj,
                color_mask=mask_obj,
                embeded_image_path=logo
            )

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

    def generate_vcard(self, first_name: str, last_name: str = "", org: str = "", title: str = "", phone: str = "", email: str = "", url: str = "") -> str:
        """Generates a VCard string."""
        lines = [
            "BEGIN:VCARD",
            "VERSION:3.0"
        ]

        name = first_name
        if last_name:
            name = f"{first_name} {last_name}"
            lines.append(f"N:{last_name};{first_name};;;")
        else:
            lines.append(f"N:;{first_name};;;")

        lines.append(f"FN:{name}")

        if org:
            lines.append(f"ORG:{org}")
        if title:
            lines.append(f"TITLE:{title}")
        if phone:
            lines.append(f"TEL:{phone}")
        if email:
            lines.append(f"EMAIL:{email}")
        if url:
            lines.append(f"URL:{url}")

        lines.append("END:VCARD")

        return "\n".join(lines)


def run_qr_lab_logic(args):
    """Entry point for QR lab CLI."""
    try:
        manager = QRLabManager()

        kwargs = {}
        if hasattr(args, "logo") and args.logo:
            kwargs["logo"] = args.logo
        if hasattr(args, "drawer") and args.drawer:
            kwargs["drawer"] = args.drawer
        if hasattr(args, "color_mask") and getattr(args, "color_mask"):
            kwargs["color_mask"] = getattr(args, "color_mask")
        if hasattr(args, "fill_color") and args.fill_color:
            kwargs["fill_color"] = args.fill_color
        if hasattr(args, "back_color") and args.back_color:
            kwargs["back_color"] = args.back_color

        if args.action == "decode":
            img_path = Path(args.image)
            results = manager.decode_image(img_path)

            if not results:
                console.print(f"[yellow]No QR codes detected in {img_path}[/yellow]")
            else:
                console.print(f"[green]Successfully decoded {len(results)} QR code(s):[/green]")
                for i, result in enumerate(results):
                    console.print(Panel(f"[bold]{result}[/bold]", title=f"QR Code {i+1}"))

        elif args.action == "gen":
            output = Path(args.output) if args.output else None
            manager.generate(args.text, output_path=output, **kwargs)

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
                manager.generate(wifi_str, output_path=output, **kwargs)
            else:
                # For console, we print the string too so user verifies
                console.print(f"WiFi Config: [dim]{wifi_str}[/dim]")
                manager.generate(wifi_str, **kwargs)

        elif args.action == "email":
            email_str = manager.generate_email(args.to, args.subject, args.body)
            output = Path(args.output) if args.output else None
            if output:
                manager.generate(email_str, output_path=output, **kwargs)
            else:
                console.print(f"Email Config: [dim]{email_str}[/dim]")
                manager.generate(email_str, **kwargs)

        elif args.action == "sms":
            sms_str = manager.generate_sms(args.phone, args.message)
            output = Path(args.output) if args.output else None
            if output:
                manager.generate(sms_str, output_path=output, **kwargs)
            else:
                console.print(f"SMS Config: [dim]{sms_str}[/dim]")
                manager.generate(sms_str, **kwargs)

        elif args.action == "geo":
            geo_str = manager.generate_geo(args.lat, args.lon)
            output = Path(args.output) if args.output else None
            if output:
                manager.generate(geo_str, output_path=output, **kwargs)
            else:
                console.print(f"Geo Config: [dim]{geo_str}[/dim]")
                manager.generate(geo_str, **kwargs)

        elif args.action == "vcard":
            vcard_str = manager.generate_vcard(
                first_name=args.first_name,
                last_name=args.last_name,
                org=args.org,
                title=args.title,
                phone=args.phone,
                email=args.email,
                url=args.url
            )
            output = Path(args.output) if args.output else None
            if output:
                manager.generate(vcard_str, output_path=output, **kwargs)
            else:
                console.print(f"VCard Config:\n[dim]{vcard_str}[/dim]")
                manager.generate(vcard_str, **kwargs)

        elif args.action == "tui":
            from shared.tui import AgentTUI
            import asyncio
            app = AgentTUI(project_dir=Path.cwd(), initial_tab="tab-qr")
            asyncio.run(app.run_async())

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
