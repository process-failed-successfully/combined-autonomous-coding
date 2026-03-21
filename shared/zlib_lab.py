import argparse
import base64
import gzip
import sys
import zlib


class ZlibLabManager:
    """Manages Zlib encoding, decoding, compression, and decompression operations."""

    def compress(self, data: bytes, format: str = "zlib", level: int = -1) -> bytes:
        if format == "zlib":
            return zlib.compress(data, level)
        elif format == "deflate":
            # wbits=-15 suppresses the zlib header and trailer, producing raw deflate output
            compressor = zlib.compressobj(level, zlib.DEFLATED, -15)
            return compressor.compress(data) + compressor.flush()
        elif format == "gzip":
            return gzip.compress(data, compresslevel=level if level != -1 else 9)
        else:
            raise ValueError(f"Unknown format: {format}")

    def decompress(self, data: bytes, format: str = "zlib") -> bytes:
        if format == "zlib":
            return zlib.decompress(data)
        elif format == "deflate":
            # wbits=-15 suppresses the zlib header
            return zlib.decompress(data, -15)
        elif format == "gzip":
            return gzip.decompress(data)
        else:
            raise ValueError(f"Unknown format: {format}")


def run_zlib_lab_logic(args: argparse.Namespace) -> bool:
    try:
        manager = ZlibLabManager()

        if getattr(args, "compress", None) is not None:
            text = args.compress.encode("utf-8")
            compressed = manager.compress(text, format=args.format)
            if args.base64:
                print(base64.b64encode(compressed).decode("ascii"))
            else:
                print(compressed.hex())
        elif getattr(args, "decompress", None) is not None:
            if args.base64:
                try:
                    data = base64.b64decode(args.decompress)
                except Exception as e:
                    print(f"Error decoding base64: {e}", file=sys.stderr)
                    return False
            else:
                try:
                    data = bytes.fromhex(args.decompress)
                except Exception as e:
                    print(f"Error decoding hex: {e}", file=sys.stderr)
                    return False

            decompressed = manager.decompress(data, format=args.format)
            print(decompressed.decode("utf-8"))
        else:
            print("Error: must provide either --compress, --decompress, or --tui", file=sys.stderr)
            return False

        return True
    except Exception as e:
        print(f"Error processing zlib: {e}", file=sys.stderr)
        return False
