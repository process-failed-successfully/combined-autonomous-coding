"""
BSON Lab
===========

Provides utilities for BSON (Binary JSON) encoding and decoding.
"""

import sys
import json

try:
    import bson
    HAS_BSON = True
except ImportError:
    HAS_BSON = False


class BsonManager:
    """Manages BSON operations (encode/decode)."""

    @staticmethod
    def decode(data: bytes):
        """Decodes BSON data into Python objects."""
        if not HAS_BSON:
            raise ValueError("bson library is not installed")
        try:
            return bson.loads(data)
        except Exception as e:
            raise ValueError(f"Invalid BSON data: {e}")

    @staticmethod
    def encode(obj) -> bytes:
        """Encodes a Python object to BSON."""
        if not HAS_BSON:
            raise TypeError("bson library is not installed")
        try:
            return bson.dumps(obj)
        except Exception as e:
            raise TypeError(f"Cannot encode object to BSON: {e}")


def run_bson_lab_logic(args):
    """CLI logic for bson-lab."""
    if not HAS_BSON:
        print("Error: The 'bson' library is not installed. Please install it using 'pip install bson'.", file=sys.stderr)
        return False

    manager = BsonManager()

    # Read input from stdin if not provided
    input_data = getattr(args, "input", None)
    if not input_data and not sys.stdin.isatty():
        input_data = sys.stdin.read().strip()

    if not input_data:
        print("Error: No input provided.", file=sys.stderr)
        return False

    if args.action == "decode":
        try:
            # For CLI we can accept hex or bytes representation
            if input_data.startswith("0x") or input_data.startswith("0X"):
                data_bytes = bytes.fromhex(input_data[2:])
            else:
                # If it's pure hex string without 0x
                try:
                    data_bytes = bytes.fromhex(input_data)
                except ValueError:
                    # Fallback to direct bytes
                    data_bytes = input_data.encode('utf-8', errors='surrogateescape')

            decoded = manager.decode(data_bytes)

            # Helper to handle bytes output in JSON
            class BytesEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, bytes):
                        try:
                            return obj.decode('utf-8')
                        except UnicodeDecodeError:
                            return repr(obj)
                    return super().default(obj)

            print(json.dumps(decoded, indent=2, cls=BytesEncoder))
            return True
        except Exception as e:
            print(f"Error decoding BSON: {e}", file=sys.stderr)
            return False

    elif args.action == "encode":
        try:
            obj = json.loads(input_data)
            encoded = manager.encode(obj)

            if getattr(args, "hex", False):
                print(encoded.hex())
            else:
                # Try to decode to utf-8 to print to terminal safely
                try:
                    print(encoded.decode('utf-8'))
                except UnicodeDecodeError:
                    print(encoded)  # Will print b'...'
            return True
        except json.JSONDecodeError:
            print("Error: Input for 'encode' must be valid JSON.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error encoding BSON: {e}", file=sys.stderr)
            return False

    return True
