import sys
import argparse
from pathlib import Path

class HexdumpManager:
    """Manager for generating Hex Dumps of data."""

    def hexdump(self, data: bytes, offset: int = 0, length: int = -1) -> str:
        """
        Generates a canonical hex+ASCII dump of the provided bytes.

        Args:
            data: The bytes to dump.
            offset: The starting byte offset to label the first row.
            length: The maximum number of bytes to dump (-1 for all).

        Returns:
            A string containing the formatted hexdump.
        """
        if not isinstance(data, bytes):
            return "Error: Data must be bytes."

        if length >= 0:
            data = data[:length]

        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]

            # Format offset
            hex_offset = f"{offset + i:08x}"

            # Format hex bytes
            hex_chunks = []
            for j in range(0, 16, 8):
                sub_chunk = chunk[j:j+8]
                hex_str = " ".join(f"{b:02x}" for b in sub_chunk)
                if hex_str:
                    hex_chunks.append(hex_str)

            hex_part = "  ".join(hex_chunks)
            # Pad hex part to align ascii part
            hex_part = f"{hex_part:<48}" if len(chunk) < 16 else hex_part

            # Format ascii bytes
            ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)

            lines.append(f"{hex_offset}  {hex_part}  |{ascii_part}|")

        # Append the final size offset
        if data:
            lines.append(f"{offset + len(data):08x}")

        return "\n".join(lines)

def run_hexdump_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for the Hexdump Lab."""
    manager = HexdumpManager()

    try:
        data = b""
        if getattr(args, "file", None):
            p = Path(args.file)
            if not p.is_file():
                print(f"Error: File '{args.file}' not found.", file=sys.stderr)
                return False

            with open(p, "rb") as f:
                if args.offset > 0:
                    f.seek(args.offset)
                if args.length >= 0:
                    data = f.read(args.length)
                else:
                    data = f.read()
        elif getattr(args, "text", None):
            # Encode string as utf-8
            text_data = args.text.encode("utf-8")
            start = max(0, args.offset)
            if args.length >= 0:
                data = text_data[start:start + args.length]
            else:
                data = text_data[start:]
        else:
            # Try to read from stdin if no file or text provided
            if not sys.stdin.isatty():
                stdin_data = sys.stdin.buffer.read()
                start = max(0, args.offset)
                if args.length >= 0:
                    data = stdin_data[start:start + args.length]
                else:
                    data = stdin_data[start:]
            else:
                print("Error: Must provide --file, --text, or pipe data to stdin.", file=sys.stderr)
                return False

        if not data:
            print("No data to dump.", file=sys.stderr)
            return True

        result = manager.hexdump(data, offset=args.offset)
        print(result)
        return True

    except Exception as e:
        print(f"Error generating hexdump: {e}", file=sys.stderr)
        return False
