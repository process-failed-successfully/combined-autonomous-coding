"""
Bencode Lab
===========

Provides utilities for Bencode encoding and decoding (used by BitTorrent).
"""

import sys


class BencodeManager:
    """Manages Bencode operations (encode/decode)."""

    @staticmethod
    def decode(data: bytes):
        """Decodes bencoded data."""
        def decode_next(data, index):
            if index >= len(data):
                raise ValueError("Unexpected end of data")

            char = data[index:index+1]

            # Integer: i<digits>e
            if char == b'i':
                end_idx = data.find(b'e', index + 1)
                if end_idx == -1:
                    raise ValueError("Invalid integer: missing 'e'")
                try:
                    num_str = data[index + 1:end_idx].decode('ascii')
                    if num_str.startswith('-0') or (num_str.startswith('0') and len(num_str) > 1):
                        raise ValueError("Invalid integer format")
                    return int(num_str), end_idx + 1
                except ValueError as e:
                    raise ValueError(f"Invalid integer: {e}")

            # List: l<contents>e
            elif char == b'l':
                index += 1
                result = []
                while index < len(data) and data[index:index+1] != b'e':
                    item, index = decode_next(data, index)
                    result.append(item)
                if index >= len(data) or data[index:index+1] != b'e':
                    raise ValueError("Invalid list: missing 'e'")
                return result, index + 1

            # Dictionary: d<contents>e
            elif char == b'd':
                index += 1
                result = {}
                while index < len(data) and data[index:index+1] != b'e':
                    key, index = decode_next(data, index)
                    if not isinstance(key, bytes):
                        raise ValueError("Dictionary key must be a string")

                    try:
                        key_str = key.decode('utf-8')
                    except UnicodeDecodeError:
                        key_str = repr(key)  # Fallback if key is not valid UTF-8

                    value, index = decode_next(data, index)
                    result[key_str] = value
                if index >= len(data) or data[index:index+1] != b'e':
                    raise ValueError("Invalid dictionary: missing 'e'")
                return result, index + 1

            # String: <length>:<contents>
            elif char.isdigit():
                colon_idx = data.find(b':', index)
                if colon_idx == -1:
                    raise ValueError("Invalid string: missing ':'")
                try:
                    length = int(data[index:colon_idx].decode('ascii'))
                    if length < 0:
                        raise ValueError("String length cannot be negative")
                except ValueError:
                    raise ValueError("Invalid string length")

                start_str = colon_idx + 1
                end_str = start_str + length
                if end_str > len(data):
                    raise ValueError("String length exceeds data length")
                return data[start_str:end_str], end_str

            else:
                raise ValueError(f"Invalid bencode character: {char!r} at index {index}")

        result, index = decode_next(data, 0)
        if index != len(data):
            # Warning or ignore trailing data
            pass
        return result

    @staticmethod
    def encode(obj) -> bytes:
        """Encodes an object to bencode."""
        if isinstance(obj, int):
            if isinstance(obj, bool):
                obj = int(obj)
            return f"i{obj}e".encode('ascii')
        elif isinstance(obj, str):
            encoded = obj.encode('utf-8')
            return f"{len(encoded)}:".encode('ascii') + encoded
        elif isinstance(obj, bytes):
            return f"{len(obj)}:".encode('ascii') + obj
        elif isinstance(obj, list) or isinstance(obj, tuple):
            return b"l" + b"".join(BencodeManager.encode(item) for item in obj) + b"e"
        elif isinstance(obj, dict):
            # Keys must be strings, sorted lexicographically by their encoded form
            # But according to spec, dictionary keys must be sorted as raw strings (bytes).
            encoded_items = []
            for k, v in obj.items():
                if isinstance(k, str):
                    encoded_key = BencodeManager.encode(k)
                elif isinstance(k, bytes):
                    encoded_key = f"{len(k)}:".encode('ascii') + k
                else:
                    raise ValueError("Dictionary keys must be strings or bytes")
                encoded_val = BencodeManager.encode(v)
                encoded_items.append((encoded_key, encoded_val))

            encoded_items.sort(key=lambda x: x[0])

            result = b"d"
            for k, v in encoded_items:
                result += k + v
            result += b"e"
            return result
        else:
            raise TypeError(f"Cannot encode type: {type(obj)}")


def run_bencode_lab_logic(args):
    """CLI logic for bencode-lab."""
    manager = BencodeManager()

    # Read input from stdin if not provided
    input_data = args.input
    if not input_data and not sys.stdin.isatty():
        input_data = sys.stdin.read().strip()

    if not input_data:
        print("Error: No input provided.", file=sys.stderr)
        return False

    if args.action == "decode":
        try:
            import json

            # Bencode strings are bytes, so we need a custom JSON encoder for the output
            class BytesEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, bytes):
                        try:
                            return obj.decode('utf-8')
                        except UnicodeDecodeError:
                            return repr(obj)
                    return super().default(obj)

            # For CLI we can accept string or hex
            if input_data.startswith("0x") or input_data.startswith("0X"):
                data_bytes = bytes.fromhex(input_data[2:])
            else:
                data_bytes = input_data.encode('utf-8', errors='surrogateescape')

            decoded = manager.decode(data_bytes)
            print(json.dumps(decoded, indent=2, cls=BytesEncoder))
            return True
        except Exception as e:
            print(f"Error decoding: {e}", file=sys.stderr)
            return False

    elif args.action == "encode":
        try:
            import json
            obj = json.loads(input_data)
            encoded = manager.encode(obj)

            if args.hex:
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
            print(f"Error encoding: {e}", file=sys.stderr)
            return False

    return True
