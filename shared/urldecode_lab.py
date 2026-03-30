import urllib.parse
import sys


def run_urldecode_lab_logic(args) -> bool:
    """CLI handler for UrlDecode Lab."""
    if hasattr(args, 'text') and args.text is not None:
        print(urllib.parse.unquote(args.text))
        return True
    else:
        print("Error: No text specified. Use --text.", file=sys.stderr)
        return False
