import urllib.parse
import sys


def run_urlencode_lab_logic(args) -> bool:
    """CLI handler for UrlEncode Lab."""
    if hasattr(args, 'encode') and args.encode:
        print(urllib.parse.quote(args.encode))
        return True
    elif hasattr(args, 'decode') and args.decode:
        print(urllib.parse.unquote(args.decode))
        return True
    else:
        print("Error: No action specified. Use --encode or --decode.", file=sys.stderr)
        return False
