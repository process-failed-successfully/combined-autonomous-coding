import sys
import json
from pathlib import Path
from typing import Any, Union


class BencodeManager:
    """
    Manages encoding and decoding of Bencode data (used in BitTorrent).
    """

    def __init__(self):
        pass

    def decode(self, data: bytes) -> Any:
        """
        Decodes a bencoded byte string into a Python object.
        """
        def _decode(b: bytes, index: int) -> tuple[Any, int]:
            if index >= len(b):
                raise ValueError("Unexpected end of data")

            char = b[index:index+1]

            if char == b'i':
                end = b.find(b'e', index)
                if end == -1:
                    raise ValueError("Unterminated integer")
                val = int(b[index+1:end])
                return val, end + 1

            elif char == b'l':
                lst = []
                index += 1
                while b[index:index+1] != b'e':
                    val, index = _decode(b, index)
                    lst.append(val)
                return lst, index + 1

            elif char == b'd':
                dct = {}
                index += 1
                while b[index:index+1] != b'e':
                    key, index = _decode(b, index)
                    if not isinstance(key, bytes):
                        raise ValueError("Dictionary keys must be strings (bytes)")
                    val, index = _decode(b, index)
                    # Try to decode keys as utf-8 strings for easier usage in JSON
                    try:
                        k_str = key.decode('utf-8')
                    except UnicodeDecodeError:
                        # Fallback for keys that aren't valid utf-8
                        k_str = key.hex()
                    dct[k_str] = val
                return dct, index + 1

            elif char.isdigit():
                colon = b.find(b':', index)
                if colon == -1:
                    raise ValueError("Unterminated string length")
                length = int(b[index:colon])
                start = colon + 1
                end = start + length
                if end > len(b):
                    raise ValueError("String length exceeds data size")

                string_bytes = b[start:end]
                # For decoding, we return bytes because bencode strings often contain binary data (like info_hash)
                # But if we want a human readable output, we might try to decode
                # To maintain structure integrity for encoding back, we should return bytes.
                return string_bytes, end
            else:
                raise ValueError(f"Invalid bencode format at index {index}: {char}")

        res, _ = _decode(data, 0)
        return res

    def encode(self, data: Any) -> bytes:
        """
        Encodes a Python object into a bencoded byte string.
        """
        if isinstance(data, int):
            return b'i' + str(data).encode('utf-8') + b'e'
        elif isinstance(data, str):
            encoded = data.encode('utf-8')
            return str(len(encoded)).encode('utf-8') + b':' + encoded
        elif isinstance(data, bytes):
            return str(len(data)).encode('utf-8') + b':' + data
        elif isinstance(data, list):
            res = b'l'
            for item in data:
                res += self.encode(item)
            res += b'e'
            return res
        elif isinstance(data, dict):
            res = b'd'
            # Bencode dictionaries must be sorted lexicographically by key
            sorted_keys = sorted(data.keys())
            for key in sorted_keys:
                res += self.encode(key)
                res += self.encode(data[key])
            res += b'e'
            return res
        else:
            raise TypeError(f"Unsupported type for bencoding: {type(data)}")

    def json_ready(self, data: Any) -> Any:
        """
        Converts bytes in decoded bencode data to hex or strings so it can be serialized to JSON.
        """
        if isinstance(data, bytes):
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError:
                return data.hex()
        elif isinstance(data, list):
            return [self.json_ready(item) for item in data]
        elif isinstance(data, dict):
            return {k: self.json_ready(v) for k, v in data.items()}
        else:
            return data

    def load_file(self, path: Union[str, Path]) -> Any:
        with open(path, 'rb') as f:
            data = f.read()
        return self.decode(data)


def run_bencode_lab_logic(args):
    """CLI Entry point for Bencode Lab."""
    manager = BencodeManager()

    if args.action == "decode":
        try:
            if args.input == "-":
                # Wait, sys.stdin.read() returns string, we need bytes.
                data = sys.stdin.buffer.read()
            else:
                path = Path(args.input)
                if not path.exists():
                    print(f"Error: File not found {args.input}", file=sys.stderr)
                    sys.exit(1)
                data = path.read_bytes()

            decoded = manager.decode(data)
            json_safe = manager.json_ready(decoded)
            print(json.dumps(json_safe, indent=2))
        except Exception as e:
            print(f"Error decoding bencode: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "encode":
        try:
            if args.input == "-":
                data = sys.stdin.read()
            else:
                path = Path(args.input)
                if not path.exists():
                    print(f"Error: File not found {args.input}", file=sys.stderr)
                    sys.exit(1)
                data = path.read_text(encoding='utf-8')

            parsed = json.loads(data)
            encoded = manager.encode(parsed)

            if args.output:
                Path(args.output).write_bytes(encoded)
                print(f"✅ Encoded data saved to {args.output}")
            else:
                # Print to stdout
                sys.stdout.buffer.write(encoded)
        except Exception as e:
            print(f"Error encoding bencode: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
