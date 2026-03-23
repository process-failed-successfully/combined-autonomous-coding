import argparse
import base64
import sys
import brotli

class BrotliLabManager:
    """Manages Brotli compression and decompression operations."""

    def compress(self, data: bytes, quality: int = 11) -> bytes:
        """
        Compresses the given data using Brotli.
        Quality ranges from 0 to 11 (11 is default and highest compression).
        """
        return brotli.compress(data, quality=quality)

    def decompress(self, data: bytes) -> bytes:
        """
        Decompresses the given Brotli-compressed data.
        """
        return brotli.decompress(data)

def run_brotli_lab_logic(args: argparse.Namespace) -> bool:
    try:
        manager = BrotliLabManager()

        if getattr(args, "compress", None) is not None:
            text = args.compress.encode("utf-8")
            compressed = manager.compress(text, quality=args.quality)
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
        print(f"Error processing brotli: {e}", file=sys.stderr)
        return False
