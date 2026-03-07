"""
Barcode Lab
===========

Utilities for standard 1D barcode generation.
"""

import sys
from pathlib import Path
from typing import List, Optional

try:
    import barcode
    from barcode.writer import ImageWriter, SVGWriter
    HAS_BARCODE = True
except ImportError:
    HAS_BARCODE = False


class BarcodeLabManager:
    """Manages barcode generation operations."""

    def __init__(self):
        pass

    def _check_dependency(self):
        if not HAS_BARCODE:
            raise ImportError("python-barcode library is not installed. Please run: pip install python-barcode")

    def list_formats(self) -> List[str]:
        """Returns a list of supported barcode formats."""
        self._check_dependency()
        return barcode.PROVIDED_BARCODES

    def generate(self, data: str, fmt: str = 'code128', output_path: Optional[Path] = None, svg: bool = False, **kwargs) -> str:
        """
        Generates a barcode.
        If output_path is provided, saves to file.
        Returns the path to the saved file or a success message.
        """
        self._check_dependency()

        fmt = fmt.lower()
        if fmt not in barcode.PROVIDED_BARCODES:
            raise ValueError(f"Unsupported barcode format: {fmt}. Supported formats: {', '.join(barcode.PROVIDED_BARCODES)}")

        try:
            barcode_class = barcode.get_barcode_class(fmt)

            writer = SVGWriter() if svg else ImageWriter()

            # python-barcode's generate expects to write to a file-like object or save directly
            # it also handles appending .svg or .png implicitly if we use save()

            bc = barcode_class(data, writer=writer)

            if output_path:
                # remove extension if present as save() adds it
                base_path = str(output_path)

                # Check for mocked objects masquerading as strings during tests
                if "MagicMock" in base_path:
                     raise RuntimeError(f"Detected MagicMock in output path: {base_path}. Aborting save to prevent garbage files.")

                if svg and base_path.endswith('.svg'):
                    base_path = base_path[:-4]
                elif not svg and base_path.endswith('.png'):
                    base_path = base_path[:-4]

                actual_path = bc.save(base_path)
                return f"Barcode saved to {actual_path}"
            else:
                # If no path, we'll save it to a default name in the current directory
                default_name = f"barcode_{fmt}_{data}"
                actual_path = bc.save(default_name)
                return f"Barcode saved to {actual_path}"

        except Exception as e:
            raise RuntimeError(f"Failed to generate barcode: {e}")

    def validate(self, data: str, fmt: str) -> bool:
        """
        Validates if the given data can be encoded in the specified format.
        """
        self._check_dependency()
        fmt = fmt.lower()
        if fmt not in barcode.PROVIDED_BARCODES:
            return False

        try:
            barcode_class = barcode.get_barcode_class(fmt)
            barcode_class(data)
            return True
        except Exception:
            return False


def run_barcode_lab_logic(args) -> bool:
    """CLI handler for Barcode Lab."""
    manager = BarcodeLabManager()

    try:
        manager._check_dependency()
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    if args.action == "list":
        formats = manager.list_formats()
        print("Supported Barcode Formats:")
        for fmt in formats:
            print(f"  - {fmt}")
        return True

    elif args.action == "generate":
        if not args.data:
            print("Error: Data is required for generation.", file=sys.stderr)
            return False

        output_path = Path(args.output) if args.output else None

        try:
            result = manager.generate(args.data, fmt=args.format, output_path=output_path, svg=args.svg)
            print(result)
            return True
        except Exception as e:
            print(f"Error generating barcode: {e}", file=sys.stderr)
            return False

    elif args.action == "validate":
        if not args.data or not args.format:
            print("Error: Data and format are required for validation.", file=sys.stderr)
            return False

        is_valid = manager.validate(args.data, args.format)
        if is_valid:
            print(f"✅ '{args.data}' is valid for format {args.format}.")
            return True
        else:
            print(f"❌ '{args.data}' is NOT valid for format {args.format}.")
            return False

    return False
