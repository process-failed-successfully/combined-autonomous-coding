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
from typing import List, Any, Optional, Tuple, Dict
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

    def get_hex_dump(self, file_path: Path, offset: int = 0, length: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Returns a hex dump of the file as a list of dicts.
        Each dict has 'offset', 'hex', 'ascii'.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            if offset > 0:
                f.seek(offset)
            data = f.read(length if length is not None else -1)

        if not data:
            return []

        rows = []
        chunk_size = 16
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)

            # Pad hex part if chunk is less than 16 bytes
            if len(chunk) < chunk_size:
                hex_part += "   " * (chunk_size - len(chunk))

            rows.append({
                "offset": f"{offset + i:08x}",
                "hex": hex_part,
                "ascii": ascii_part
            })

        return rows

    def hex_dump(self, file_path: Path, offset: int = 0, length: Optional[int] = None) -> None:
        """Prints a hex dump of the file."""
        rows = self.get_hex_dump(file_path, offset, length)

        if not rows:
            console.print("No data to display.")
            return

        table = Table(title=f"Hex Dump: {file_path.name}", show_header=True, header_style="bold magenta")
        table.add_column("Offset", style="dim", width=8)
        table.add_column("Hex", justify="left", width=48) # 16 bytes * 3 chars
        table.add_column("ASCII", justify="left", width=16)

        for row in rows:
            table.add_row(row["offset"], row["hex"], row["ascii"])

        console.print(table)

    def unpack_data(self, fmt: str, file_path: Path, offset: int = 0) -> Tuple[Any, ...]:
        """Unpacks binary data from a file according to format and returns tuple."""
        size = self.calc_size(fmt)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            f.seek(offset)
            data = f.read(size)

        if len(data) < size:
            raise ValueError(f"Not enough data to unpack. Expected {size} bytes, got {len(data)}.")

        try:
            return struct.unpack(fmt, data)
        except struct.error as e:
            raise ValueError(f"Unpack failed: {e}")

    def unpack(self, fmt: str, file_path: Path, offset: int = 0) -> None:
        """Unpacks binary data from a file according to format and prints result."""
        try:
            # We calculate size just for display purposes here since unpack_data does it internally too
            size = self.calc_size(fmt)
            unpacked = self.unpack_data(fmt, file_path, offset)

            console.print(Panel(f"[bold]Unpack Result[/bold] (Format: '{fmt}', Size: {size} bytes)"))
            for i, val in enumerate(unpacked):
                console.print(f"[{i}]: {val!r}")

        except Exception as e:
            # Propagate or handle error. Since unpack_data raises ValueError, we can let it bubble up
            # or print it here if we want to match previous behavior strictly, but previous behavior
            # raised ValueError too. The calling cli wrapper handles exceptions.
            raise

    def pack_data(self, fmt: str, values: List[str], output_path: Path) -> int:
        """
        Packs values into a binary file according to format.
        Returns number of bytes written.
        """
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

        return len(packed_data)

    def pack(self, fmt: str, values: List[str], output_path: Path) -> None:
        """Packs values into a binary file according to format and prints result."""
        bytes_written = self.pack_data(fmt, values, output_path)
        console.print(f"[green]✅ Packed {bytes_written} bytes to {output_path}[/green]")


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
