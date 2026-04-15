import argparse
import base64
import sys
import zstandard as zstd

class ZstdLabManager:
    """Manages Zstandard compression and decompression operations."""

    def compress(self, data: bytes, level: int = 3) -> bytes:
        """
        Compresses the given data using Zstandard.
        Level typically ranges from 1 to 22 (default is 3).
        """
        compressor = zstd.ZstdCompressor(level=level)
        return compressor.compress(data)

    def decompress(self, data: bytes) -> bytes:
        """
        Decompresses the given Zstandard-compressed data.
        """
        decompressor = zstd.ZstdDecompressor()
        return decompressor.decompress(data)

def run_zstd_lab_logic(args: argparse.Namespace) -> bool:
    try:
        manager = ZstdLabManager()

        if getattr(args, "compress", None) is not None:
            text = args.compress.encode("utf-8")
            compressed = manager.compress(text, level=args.level)
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

            decompressed = manager.decompress(data)
            print(decompressed.decode("utf-8"))
        else:
            print("Error: must provide either --compress, --decompress, or --tui", file=sys.stderr)
            return False

        return True
    except Exception as e:
        print(f"Error processing zstd: {e}", file=sys.stderr)
        return False
