"""
EXIF Lab
========

Utilities for reading and removing EXIF metadata from images using Pillow (PIL).
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ExifManager:
    """Manages EXIF metadata operations for images."""

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def _check_pil(self):
        if not HAS_PIL:
            raise ImportError("Pillow library is not installed. Please run: pip install Pillow")

    def read(self, input_path: Path) -> Dict[str, Any]:
        """Reads EXIF metadata from an image."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        exif_data = {}
        with Image.open(input_path) as img:
            exif = img.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value

        return exif_data

    def remove(self, input_path: Path, output_path: Path) -> Path:
        """Removes EXIF metadata from an image and saves it to a new file."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        with Image.open(input_path) as img:
            # Extract just the pixel data and ignore the info dictionary (which contains EXIF)
            # To be efficient and avoid getdata which loads everything into memory,
            # create a new image and paste the original into it.
            image_without_exif = Image.new(img.mode, img.size)
            image_without_exif.paste(img)

            # Preserve the original format if possible, otherwise use the suffix
            format = img.format if img.format else output_path.suffix.lstrip('.').upper()
            if format == 'JPG':
                format = 'JPEG'

            try:
                # specifically exclude exif data
                image_without_exif.save(output_path, format=format, exif=b"")
            except Exception:
                # Fallback to saving without explicit format
                image_without_exif.save(output_path, exif=b"")

        return output_path


def run_exif_lab_logic(args) -> bool:
    """Entry point for EXIF Lab CLI."""
    manager = ExifManager(getattr(args, 'project_dir', None))

    try:
        if args.action == "read":
            input_path = Path(args.input)
            exif_data = manager.read(input_path)

            if not exif_data:
                print(f"No EXIF data found in {input_path.name}")
                return True

            print(f"--- EXIF Data for {input_path.name} ---")
            for key, value in exif_data.items():
                if isinstance(value, bytes) and len(value) > 50:
                    val_str = f"<{len(value)} bytes>"
                elif isinstance(value, tuple) and len(value) > 10:
                    val_str = f"<{len(value)} items>"
                else:
                    val_str = str(value)
                print(f"{key}: {val_str}")

        elif args.action == "remove":
            input_path = Path(args.input)
            output_path = Path(args.output) if args.output else input_path.with_name(f"no_exif_{input_path.name}")

            manager.remove(input_path, output_path)
            print(f"✅ Image saved without EXIF data to {output_path}")

        return True

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
