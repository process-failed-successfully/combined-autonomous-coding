"""
Barcode Lab
===========

Utilities for generating 1D barcodes using the python-barcode library.
"""

import sys
from pathlib import Path
from rich.console import Console

try:
    import barcode
    from barcode.writer import ImageWriter
    HAS_BARCODE = True
except ImportError:
    HAS_BARCODE = False

console = Console()

class BarcodeLabManager:
    """Manages 1D barcode operations."""

    def __init__(self):
        pass

    def _check_dependency(self):
        if not HAS_BARCODE:
            raise ImportError("python-barcode library is not installed. Please run: pip install python-barcode")

    def get_supported_formats(self):
        """Returns a list of supported barcode formats."""
        self._check_dependency()
        return barcode.PROVIDED_BARCODES

    def generate(self, data: str, barcode_type: str, output_path: Path):
        """Generates a barcode image and saves it to the specified path."""
        self._check_dependency()

        if barcode_type not in barcode.PROVIDED_BARCODES:
            raise ValueError(f"Unsupported barcode type: {barcode_type}. Supported types: {', '.join(barcode.PROVIDED_BARCODES)}")

        try:
            # We use ImageWriter to save it as an image (PNG by default)
            barcode_class = barcode.get_barcode_class(barcode_type)
            # Instantiating the barcode with the data
            code = barcode_class(data, writer=ImageWriter())

            # Using actual_path = bc.save(...) dynamically returns the file path to prevent CI filesystem inconsistencies.
            actual_path = code.save(str(output_path))
            return True, f"Barcode saved to {actual_path}"
        except Exception as e:
            return False, str(e)

    def validate(self, data: str, barcode_type: str):
        """Validates if the given data is valid for the specified barcode type."""
        self._check_dependency()

        if barcode_type not in barcode.PROVIDED_BARCODES:
             return False, f"Unsupported barcode type: {barcode_type}."

        try:
             barcode_class = barcode.get_barcode_class(barcode_type)
             # The constructor typically validates the data and raises an exception if invalid.
             _ = barcode_class(data)
             return True, "Data is valid for this barcode type."
        except barcode.errors.BarcodeError as e:
             return False, str(e)
        except Exception as e:
             return False, str(e)

def run_barcode_lab_logic(args):
    """CLI logic for Barcode Lab."""
    manager = BarcodeLabManager()

    try:
        if args.action == "list":
            formats = manager.get_supported_formats()
            console.print("[bold]Supported Barcode Formats:[/bold]")
            for fmt in formats:
                console.print(f"  - {fmt}")

        elif args.action == "generate":
            if not args.data or not args.type or not args.output:
                console.print("[red]Error: --data, --type, and --output are required for 'generate'.[/red]")
                sys.exit(1)

            success, msg = manager.generate(args.data, args.type, Path(args.output))
            if success:
                console.print(f"[green]✅ {msg}[/green]")
            else:
                console.print(f"[red]❌ Error generating barcode: {msg}[/red]")
                sys.exit(1)

        elif args.action == "validate":
             if not args.data or not args.type:
                 console.print("[red]Error: --data and --type are required for 'validate'.[/red]")
                 sys.exit(1)

             success, msg = manager.validate(args.data, args.type)
             if success:
                 console.print(f"[green]✅ {msg}[/green]")
             else:
                 console.print(f"[red]❌ {msg}[/red]")
                 sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
