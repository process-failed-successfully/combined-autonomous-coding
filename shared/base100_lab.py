import sys

def base100_encode(data: bytes) -> str:
    """Encodes bytes into Base100 (emoji string)."""
    return "".join(chr(b + 128000) for b in data)

def base100_decode(text: str) -> bytes:
    """Decodes a Base100 emoji string back to bytes."""
    try:
        return bytes(ord(c) - 128000 for c in text)
    except ValueError as e:
        raise ValueError(f"Invalid Base100 string: {e}")

def run_base100_lab_logic(args):
    """CLI logic for base100-lab."""
    if getattr(args, "encode", None):
        text_bytes = args.encode.encode('utf-8')
        try:
            encoded = base100_encode(text_bytes)
            print(encoded)
            return True
        except Exception as e:
            print(f"Error encoding to Base100: {e}", file=sys.stderr)
            return False

    elif getattr(args, "decode", None):
        try:
            decoded_bytes = base100_decode(args.decode)
            print(decoded_bytes.decode('utf-8', errors='replace'))
            return True
        except Exception as e:
            print(f"Error decoding Base100: {e}", file=sys.stderr)
            return False

    print("Please specify --encode or --decode.", file=sys.stderr)
    return False
