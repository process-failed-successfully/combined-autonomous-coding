import argparse
import base64
import gzip
import sys
from pathlib import Path


class GzipLabManager:
    """Manages gzip compression and decompression operations."""

    def compress_bytes(self, data: bytes, level: int = 9) -> bytes:
        """Compresses bytes using gzip."""
        return gzip.compress(data, compresslevel=level)

    def decompress_bytes(self, data: bytes) -> bytes:
        """Decompresses gzip bytes."""
        return gzip.decompress(data)

    def compress_file(self, input_path: Path, output_path: Path, level: int = 9) -> None:
        """Compresses a file using gzip."""
        with open(input_path, "rb") as f_in:
            with gzip.open(output_path, "wb", compresslevel=level) as f_out:
                while True:
                    chunk = f_in.read(8192)
                    if not chunk:
                        break
                    f_out.write(chunk)

    def decompress_file(self, input_path: Path, output_path: Path) -> None:
        """Decompresses a gzip file."""
        with gzip.open(input_path, "rb") as f_in:
            with open(output_path, "wb") as f_out:
                while True:
                    chunk = f_in.read(8192)
                    if not chunk:
                        break
                    f_out.write(chunk)


def run_gzip_lab_logic(args: argparse.Namespace) -> bool:
    try:
        manager = GzipLabManager()

        if getattr(args, "action", None) == "compress":
            if getattr(args, "string", None):
                text = args.string.encode("utf-8")
                compressed = manager.compress_bytes(text, level=args.level)
                if args.base64:
                    print(base64.b64encode(compressed).decode("ascii"))
                else:
                    print(compressed.hex())
            elif getattr(args, "file", None):
                input_path = Path(args.file)
                output_path = Path(args.output) if getattr(args, "output", None) else Path(str(input_path) + ".gz")
                manager.compress_file(input_path, output_path, level=args.level)
                print(f"Compressed file saved to {output_path}")
            else:
                print("Error: must provide either --string or --file to compress", file=sys.stderr)
                return False

        elif getattr(args, "action", None) == "decompress":
            if getattr(args, "string", None):
                if args.base64:
                    try:
                        data = base64.b64decode(args.string)
                    except Exception as e:
                        print(f"Error decoding base64: {e}", file=sys.stderr)
                        return False
                else:
                    try:
                        data = bytes.fromhex(args.string)
                    except Exception as e:
                        print(f"Error decoding hex: {e}", file=sys.stderr)
                        return False

                decompressed = manager.decompress_bytes(data)
                print(decompressed.decode("utf-8", errors="replace"))
            elif getattr(args, "file", None):
                input_path = Path(args.file)
                output_path_str = str(input_path)
                if output_path_str.endswith(".gz"):
                    default_output = output_path_str[:-3]
                else:
                    default_output = output_path_str + ".out"

                output_path = Path(args.output) if getattr(args, "output", None) else Path(default_output)
                manager.decompress_file(input_path, output_path)
                print(f"Decompressed file saved to {output_path}")
            else:
                print("Error: must provide either --string or --file to decompress", file=sys.stderr)
                return False
        else:
            print("Error: invalid action", file=sys.stderr)
            return False

        return True
    except Exception as e:
        print(f"Error processing gzip: {e}", file=sys.stderr)
        return False
