"""
Struct Lab
==========

Utilities for binary data manipulation using Python's struct module.
Includes hex dump, packing, unpacking, and size calculation.
"""

import sys
import struct
import binascii
from pathlib import Path
from typing import List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class StructLabManager:
    """Manages struct operations."""

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def calc_size(self, fmt: str) -> int:
        """Calculates the size of a struct format."""
        try:
            return struct.calcsize(fmt)
        except struct.error as e:
            raise ValueError(f"Invalid format string: {e}")

    def hex_dump(self, file_path: Path, offset: int = 0, length: Optional[int] = None) -> None:
        """Prints a hex dump of the file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            if offset > 0:
                f.seek(offset)

            data = f.read(length if length is not None else -1)

        if not data:
            console.print("No data to display.")
            return

        table = Table(title=f"Hex Dump: {file_path.name}", show_header=True, header_style="bold magenta")
        table.add_column("Offset", style="dim", width=8)
        table.add_column("Hex", justify="left", width=48) # 16 bytes * 3 chars
        table.add_column("ASCII", justify="left", width=16)

        chunk_size = 16
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)

            # Pad hex part if chunk is less than 16 bytes
            if len(chunk) < chunk_size:
                hex_part += "   " * (chunk_size - len(chunk))

            table.add_row(f"{offset + i:08x}", hex_part, ascii_part)

        console.print(table)

    def unpack(self, fmt: str, file_path: Path, offset: int = 0) -> None:
        """Unpacks binary data from a file according to format."""
        size = self.calc_size(fmt)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            f.seek(offset)
            data = f.read(size)

        if len(data) < size:
            raise ValueError(f"Not enough data to unpack. Expected {size} bytes, got {len(data)}.")

        try:
            unpacked = struct.unpack(fmt, data)
        except struct.error as e:
            raise ValueError(f"Unpack failed: {e}")

        console.print(Panel(f"[bold]Unpack Result[/bold] (Format: '{fmt}', Size: {size} bytes)"))
        for i, val in enumerate(unpacked):
            console.print(f"[{i}]: {val!r}")

    def pack(self, fmt: str, values: List[str], output_path: Path) -> None:
        """Packs values into a binary file according to format."""
        # Simple type inference
        parsed_values = []
        for v in values:
            try:
                # Try int
                parsed_values.append(int(v))
            except ValueError:
                try:
                    # Try float
                    parsed_values.append(float(v))
                except ValueError:
                    # Default to encoded bytes
                    parsed_values.append(v.encode("utf-8"))

        try:
            packed_data = struct.pack(fmt, *parsed_values)
        except struct.error as e:
            raise ValueError(f"Pack failed: {e}\nEnsure values match the format string types.")

        with open(output_path, "wb") as f:
            f.write(packed_data)

        console.print(f"[green]✅ Packed {len(packed_data)} bytes to {output_path}[/green]")


def run_struct_lab_logic(args):
    """Entry point for struct lab CLI."""
    manager = StructLabManager(args.project_dir)

    try:
        if args.action == "calc":
            size = manager.calc_size(args.format)
            console.print(f"Size of '{args.format}': [bold]{size} bytes[/bold]")

        elif args.action == "hex":
            manager.hex_dump(
                Path(args.file),
                offset=args.offset,
                length=args.length
            )

        elif args.action == "unpack":
            manager.unpack(
                args.format,
                Path(args.file),
                offset=args.offset
            )

        elif args.action == "pack":
            manager.pack(
                args.format,
                args.values,
                Path(args.output)
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
