"""
CBOR Lab
===========

Provides utilities for CBOR (Concise Binary Object Representation) encoding and decoding.
"""

import sys
import json
import cbor2

class CborManager:
    """Manages CBOR operations (encode/decode)."""

    @staticmethod
    def decode(data: bytes):
        """Decodes CBOR data into Python objects."""
        try:
            return cbor2.loads(data)
        except Exception as e:
            raise ValueError(f"Invalid CBOR data: {e}")

    @staticmethod
    def encode(obj) -> bytes:
        """Encodes a Python object to CBOR."""
        try:
            return cbor2.dumps(obj)
        except Exception as e:
            raise TypeError(f"Cannot encode object to CBOR: {e}")

def run_cbor_lab_logic(args):
    """CLI logic for cbor-lab."""
    manager = CborManager()

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
            print(f"Error decoding CBOR: {e}", file=sys.stderr)
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
            print(f"Error encoding CBOR: {e}", file=sys.stderr)
            return False

    return True
