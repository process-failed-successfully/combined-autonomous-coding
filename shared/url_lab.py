import urllib.parse
import sys
import json
from typing import Dict, Any, List, Optional

class UrlLabManager:
    """Manages URL parsing, building, and manipulation."""

    def parse(self, url: str) -> Dict[str, Any]:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        # Flatten params if single value
        simple_params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}

        return {
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "path": parsed.path,
            "params": parsed.params,
            "query": parsed.query,
            "fragment": parsed.fragment,
            "query_params": simple_params,
            "hostname": parsed.hostname,
            "port": parsed.port,
            "username": parsed.username,
            "password": parsed.password,
        }

    def encode(self, text: str) -> str:
        return urllib.parse.quote(text)

    def decode(self, text: str) -> str:
        return urllib.parse.unquote(text)

    def join(self, base: str, path: str) -> str:
        return urllib.parse.urljoin(base, path)

    def update_params(self, url: str, add: Optional[Dict[str, str]] = None, remove: Optional[List[str]] = None) -> str:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)

        if remove:
            for key in remove:
                params.pop(key, None)

        if add:
            for k, v in add.items():
                # urllib.parse.parse_qs returns list of values, so we should respect that or replace
                # Here we replace/add as a list
                params[k] = [v]

        # Re-encode query
        new_query = urllib.parse.urlencode(params, doseq=True)

        # Rebuild URL
        return urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))

    def normalize(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)

        # Lowercase scheme and netloc
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove default ports
        if scheme == 'http' and netloc.endswith(':80'):
            netloc = netloc[:-3]
        elif scheme == 'https' and netloc.endswith(':443'):
            netloc = netloc[:-4]

        # Sort query params
        params = urllib.parse.parse_qs(parsed.query)
        # sort by key
        sorted_items = sorted(params.items())
        # sort values for each key to be deterministic
        sorted_items = [(k, sorted(v)) for k, v in sorted_items]

        sorted_query = urllib.parse.urlencode(sorted_items, doseq=True)

        # Remove empty fragments
        fragment = parsed.fragment
        # Some normalizers remove empty fragment, some keep it if present.
        # Let's remove it if empty string to be cleaner.
        if not fragment:
            fragment = ''

        return urllib.parse.urlunparse((
            scheme,
            netloc,
            parsed.path,
            parsed.params,
            sorted_query,
            fragment
        ))

def run_url_lab_logic(args):
    """CLI handler for URL Lab."""
    manager = UrlLabManager()

    if args.action == "parse":
        if not args.url:
            print("Error: URL required.", file=sys.stderr)
            return False

        result = manager.parse(args.url)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"--- URL Parse: {args.url} ---")
            for k, v in result.items():
                if v is not None and v != "":
                    if isinstance(v, dict):
                         print(f"{k:<15}: {json.dumps(v)}")
                    else:
                         print(f"{k:<15}: {v}")

    elif args.action == "encode":
        if not args.text:
             # Try stdin
            if not sys.stdin.isatty():
                args.text = sys.stdin.read().strip()
            else:
                print("Error: Text required.", file=sys.stderr)
                return False
        print(manager.encode(args.text))

    elif args.action == "decode":
        if not args.text:
             # Try stdin
            if not sys.stdin.isatty():
                args.text = sys.stdin.read().strip()
            else:
                print("Error: Text required.", file=sys.stderr)
                return False
        print(manager.decode(args.text))

    elif args.action == "join":
        if not args.base or not args.path:
            print("Error: Base URL and path required.", file=sys.stderr)
            return False
        print(manager.join(args.base, args.path))

    elif args.action == "params":
        if not args.url:
            print("Error: URL required.", file=sys.stderr)
            return False

        add_params = {}
        if args.add:
            for item in args.add:
                if "=" in item:
                    k, v = item.split("=", 1)
                    add_params[k] = v

        remove_params = args.remove if args.remove else []

        print(manager.update_params(args.url, add=add_params, remove=remove_params))

    elif args.action == "normalize":
        if not args.url:
            print("Error: URL required.", file=sys.stderr)
            return False
        print(manager.normalize(args.url))

    return True
