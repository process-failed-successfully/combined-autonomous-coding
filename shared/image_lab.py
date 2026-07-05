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
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
    from PIL.ExifTags import TAGS
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

    def read_exif(self, filepath: Path) -> dict[str | int, Any]:
        """Reads EXIF data from an image."""
        self._check_pil()
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        exif_data = {}
        with Image.open(filepath) as img:
            # getexif() is available in newer Pillow versions
            if hasattr(img, "getexif"):
                exif = img.getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif_data[tag] = value

        return exif_data

    def remove_exif(self, input_path: Path, output_path: Path) -> Path:
        """Removes EXIF data from an image and saves it without massive memory overhead."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        with Image.open(input_path) as img:
            # Copy all info except EXIF to preserve ICC profiles and other metadata
            info = img.info.copy()
            info.pop('exif', None)

            # Convert to RGB if needed to save to JPEG
            fmt = img.format if img.format else output_path.suffix.lstrip(".").upper()
            if fmt == "JPG":
                fmt = "JPEG"

            if fmt == "JPEG" and img.mode in ("RGBA", "P"):
                # Saving as JPEG doesn't support RGBA or P
                out_img = img.convert("RGB")
            else:
                out_img = img

            # Save the image without EXIF, but preserving other metadata
            # For most formats in PIL, omit the 'exif' kwarg or explicitly pass None
            out_img.save(output_path, format=fmt, **{str(k): v for k, v in info.items()})

        return output_path

    def convert(self, input_path: Path, output_path: Path, format: Optional[str] = None, **kwargs) -> Path:
        """Converts an image to a different format."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        with Image.open(input_path) as img:
            # Convert mode if necessary (e.g., RGBA to RGB for JPEG)
            target_format = format or (output_path.suffix.lstrip(".").upper() if output_path.suffix else None)

            if target_format == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB") # type: ignore

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

    def apply_filter(self, input_path: Path, output_path: Path, filter_type: str) -> Path:
        """Applies a filter to an image."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        filters = {
            "blur": ImageFilter.BLUR,
            "contour": ImageFilter.CONTOUR,
            "detail": ImageFilter.DETAIL,
            "edge_enhance": ImageFilter.EDGE_ENHANCE,
            "emboss": ImageFilter.EMBOSS,
            "sharpen": ImageFilter.SHARPEN,
            "smooth": ImageFilter.SMOOTH,
        }

        if filter_type not in filters:
            raise ValueError(f"Unknown filter type: {filter_type}")

        with Image.open(input_path) as img:
            filtered_img = img.filter(filters[filter_type])
            filtered_img.save(output_path)

        return output_path

    def crop(self, input_path: Path, output_path: Path, left: int, top: int, right: int, bottom: int) -> Path:
        """Crops an image."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        with Image.open(input_path) as img:
            cropped_img = img.crop((left, top, right, bottom))
            cropped_img.save(output_path)

        return output_path

    def rotate(self, input_path: Path, output_path: Path, degrees: float, expand: bool = False) -> Path:
        """Rotates an image."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        with Image.open(input_path) as img:
            rotated_img = img.rotate(degrees, expand=expand)
            rotated_img.save(output_path)

        return output_path

    def flip(self, input_path: Path, output_path: Path, direction: str) -> Path:
        """Flips an image horizontally or vertically."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        with Image.open(input_path) as img:
            if direction == "horizontal":
                flipped_img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif direction == "vertical":
                flipped_img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            else:
                raise ValueError("Direction must be 'horizontal' or 'vertical'")

            flipped_img.save(output_path)

        return output_path

    def add_watermark(self, input_path: Path, output_path: Path, text: str, position: str = "bottom-right") -> Path:
        """Adds a text watermark to an image."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        with Image.open(input_path) as img:
            # Need to convert to RGBA to support text transparency potentially, but RGB is okay for basic
            if img.mode != 'RGBA':
                img = img.convert('RGBA') # type: ignore

            # Make a blank image for the text, initialized to transparent text color
            txt = Image.new('RGBA', img.size, (255,255,255,0))

            # get a font
            try:
                # Basic scaling attempt
                font = ImageFont.load_default()
            except IOError:
                font = ImageFont.load_default()

            draw = ImageDraw.Draw(txt)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            padding = 10

            if position == "bottom-right":
                x = img.width - text_width - padding
                y = img.height - text_height - padding
            elif position == "bottom-left":
                x = padding
                y = img.height - text_height - padding
            elif position == "top-right":
                x = img.width - text_width - padding
                y = padding
            elif position == "top-left":
                x = padding
                y = padding
            elif position == "center":
                x = (img.width - text_width) / 2
                y = (img.height - text_height) / 2
            else:
                x = padding
                y = padding

            # White text with semi-transparency (alpha=128)
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 128))

            # Combine
            watermarked = Image.alpha_composite(img, txt)

            # Convert back to RGB for saving if it's JPEG
            if output_path.suffix.lower() in ['.jpg', '.jpeg']:
                watermarked = watermarked.convert('RGB')

            watermarked.save(output_path)

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

    def hide_message(self, input_path: Path, output_path: Path, message: str) -> Path:
        """Hides a secret message in an image using LSB steganography."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        # Append null terminator to mark end of message
        message += "\0"

        # Convert message to bits (UTF-8)
        binary_message = ''.join(format(byte, '08b') for byte in message.encode('utf-8'))
        message_len = len(binary_message)

        with Image.open(input_path) as img:
            img = img.convert("RGB") # type: ignore  # Ensure RGB
            width, height = img.size
            pixels = list(img.getdata())

            if len(pixels) * 3 < message_len:
                raise ValueError(f"Image is too small to hold the message. Capacity: {len(pixels) * 3} bits, Message: {message_len} bits")

            new_pixels = []
            idx = 0

            for pixel in pixels:
                if idx < message_len:
                    r, g, b = pixel

                    # Modify R
                    if idx < message_len:
                        r = (r & ~1) | int(binary_message[idx])
                        idx += 1

                    # Modify G
                    if idx < message_len:
                        g = (g & ~1) | int(binary_message[idx])
                        idx += 1

                    # Modify B
                    if idx < message_len:
                        b = (b & ~1) | int(binary_message[idx])
                        idx += 1

                    new_pixels.append((r, g, b))
                else:
                    new_pixels.append(pixel)

            new_img = Image.new(img.mode, img.size)
            new_img.putdata(new_pixels)

            # Enforce PNG
            if output_path.suffix.lower() != '.png':
                output_path = output_path.with_suffix('.png')
                console.print("[yellow]Warning: Output format forced to PNG to preserve message.[/yellow]")

            new_img.save(output_path, "PNG")

        return output_path

    def reveal_message(self, input_path: Path) -> str:
        """Reveals a secret message from an image."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        with Image.open(input_path) as img:
            img = img.convert("RGB") # type: ignore
            pixels = list(img.getdata())

            binary_message = ""
            for pixel in pixels:
                r, g, b = pixel
                binary_message += str(r & 1)
                binary_message += str(g & 1)
                binary_message += str(b & 1)

            # Convert bits to bytes then string
            extracted_bytes = bytearray()
            for i in range(0, len(binary_message), 8):
                byte = binary_message[i:i+8]
                if byte == "00000000":
                    break
                if len(byte) == 8:
                    try:
                        extracted_bytes.append(int(byte, 2))
                    except ValueError:
                        break  # Stop if conversion fails

            return extracted_bytes.decode('utf-8', errors='replace')


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

        elif args.action == "filter":
            output = Path(args.output)
            manager.apply_filter(
                Path(args.input),
                output,
                filter_type=args.filter_type
            )
            console.print(f"[green]✅ Filtered image saved to {output}[/green]")

        elif args.action == "crop":
            output = Path(args.output)
            manager.crop(
                Path(args.input),
                output,
                left=args.left,
                top=args.top,
                right=args.right,
                bottom=args.bottom
            )
            console.print(f"[green]✅ Cropped image saved to {output}[/green]")

        elif args.action == "rotate":
            output = Path(args.output)
            manager.rotate(
                Path(args.input),
                output,
                degrees=args.degrees,
                expand=args.expand
            )
            console.print(f"[green]✅ Rotated image saved to {output}[/green]")

        elif args.action == "flip":
            output = Path(args.output)
            manager.flip(
                Path(args.input),
                output,
                direction=args.direction
            )
            console.print(f"[green]✅ Flipped image saved to {output}[/green]")

        elif args.action == "watermark":
            output = Path(args.output)
            manager.add_watermark(
                Path(args.input),
                output,
                text=args.text,
                position=args.position
            )
            console.print(f"[green]✅ Watermarked image saved to {output}[/green]")

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

        elif args.action == "exif":
            exif_data = manager.read_exif(Path(args.file))
            if not exif_data:
                console.print("[yellow]No EXIF data found in this image.[/yellow]")
            else:
                console.print(Panel(f"[bold]EXIF Data: {Path(args.file).name}[/bold]"))
                table = Table(show_header=False)
                for key, value in exif_data.items():
                    # Handle overly long binary values or tuples gracefully
                    if isinstance(value, bytes) and len(value) > 50:
                        val_str = f"<{len(value)} bytes>"
                    elif isinstance(value, tuple) and len(value) > 10:
                        val_str = f"<{len(value)} items>"
                    else:
                        val_str = str(value)
                    table.add_row(str(key), val_str)
                console.print(table)

        elif args.action == "remove-exif":
            output = Path(args.output)
            manager.remove_exif(Path(args.input), output)
            console.print(f"[green]✅ Image without EXIF saved to {output}[/green]")

        elif args.action == "hide":
            output = Path(args.output)
            message = args.message
            if not message:
                # Try reading from stdin
                if not sys.stdin.isatty():
                    message = sys.stdin.read().strip()
                else:
                    message = input("Enter message to hide: ")

            if not message:
                console.print("[red]Error: Message is empty.[/red]")
                sys.exit(1)

            final_path = manager.hide_message(Path(args.input), output, message)
            console.print(f"[green]✅ Message hidden in {final_path}[/green]")

        elif args.action == "reveal":
            message = manager.reveal_message(Path(args.input))
            if message:
                console.print(Panel(message, title="Hidden Message"))
            else:
                console.print("[yellow]No hidden message found (or it was empty).[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
