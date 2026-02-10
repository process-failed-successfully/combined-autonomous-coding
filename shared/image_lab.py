"""
Image Lab
=========

Utilities for image processing using Pillow (PIL).
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

console = Console()

class ImageLabManager:
    """Manages image operations."""

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def _check_pil(self):
        if not HAS_PIL:
            raise ImportError("Pillow library is not installed. Please run: pip install Pillow")

    def get_info(self, filepath: Path) -> Dict[str, Any]:
        """Returns metadata about an image."""
        self._check_pil()
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with Image.open(filepath) as img:
            return {
                "filename": filepath.name,
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
                "info": img.info
            }

    def convert(self, input_path: Path, output_path: Path, format: Optional[str] = None, **kwargs) -> Path:
        """Converts an image to a different format."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        with Image.open(input_path) as img:
            # Convert mode if necessary (e.g., RGBA to RGB for JPEG)
            target_format = format or (output_path.suffix.lstrip(".").upper() if output_path.suffix else None)

            if target_format == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            save_kwargs = {}
            if kwargs.get("quality") is not None:
                save_kwargs["quality"] = int(kwargs["quality"])

            img.save(output_path, format=target_format, **save_kwargs)

        return output_path

    def resize(self, input_path: Path, output_path: Path, width: Optional[int], height: Optional[int], maintain_aspect: bool = True) -> Path:
        """Resizes an image."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        with Image.open(input_path) as img:
            original_width, original_height = img.size

            if width is None and height is None:
                raise ValueError("At least one of width or height must be specified.")

            target_width = width
            target_height = height

            if maintain_aspect:
                if width is not None and height is None:
                    ratio = width / original_width
                    target_height = int(original_height * ratio)
                elif height is not None and width is None:
                    ratio = height / original_height
                    target_width = int(original_width * ratio)
                elif width is not None and height is not None:
                    # If both provided with maintain_aspect, fit within box (thumbnail behavior)
                    img.thumbnail((width, height))
                    img.save(output_path)
                    return output_path

            # Fallback for explicit dimensions or calculated ones
            if target_width is None: target_width = original_width
            if target_height is None: target_height = original_height

            resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            resized_img.save(output_path)

        return output_path

    def create_placeholder(self, output_path: Path, width: int, height: int, color: str = "#CCCCCC", text: Optional[str] = None, text_color: str = "black") -> Path:
        """Generates a placeholder image."""
        self._check_pil()

        try:
            img = Image.new("RGB", (width, height), color)
        except ValueError:
             # Fallback for named colors or invalid hex
             img = Image.new("RGB", (width, height), color)

        if text:
            draw = ImageDraw.Draw(img)
            # Try to load a default font, otherwise use simple
            try:
                # Basic scaling attempt
                fontsize = int(min(width, height) / 5)
                # This depends on system fonts, might fail. Fallback to default.
                # font = ImageFont.truetype("arial.ttf", fontsize)
                font = ImageFont.load_default()
            except IOError:
                font = ImageFont.load_default()

            # Center text
            # getbbox returns (left, top, right, bottom)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (width - text_width) / 2
            y = (height - text_height) / 2

            draw.text((x, y), text, fill=text_color, font=font)

        img.save(output_path)
        return output_path


def run_image_lab_logic(args):
    """Entry point for image lab CLI."""
    manager = ImageLabManager(args.project_dir)

    try:
        if args.action == "info":
            info = manager.get_info(Path(args.file))
            console.print(Panel(f"[bold]Image Info: {info['filename']}[/bold]"))

            table = Table(show_header=False)
            table.add_row("Format", info['format'])
            table.add_row("Mode", info['mode'])
            table.add_row("Dimensions", f"{info['width']} x {info['height']}")

            console.print(table)

        elif args.action == "convert":
            output = Path(args.output)
            manager.convert(Path(args.input), output, quality=args.quality)
            console.print(f"[green]✅ Converted image saved to {output}[/green]")

        elif args.action == "resize":
            output = Path(args.output)
            manager.resize(
                Path(args.input),
                output,
                width=args.width,
                height=args.height,
                maintain_aspect=not args.no_aspect
            )
            console.print(f"[green]✅ Resized image saved to {output}[/green]")

        elif args.action == "placeholder":
            output = Path(args.output)
            manager.create_placeholder(
                output,
                width=args.width,
                height=args.height,
                color=args.color,
                text=args.text,
                text_color=args.text_color
            )
            console.print(f"[green]✅ Placeholder saved to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
