import urllib.parse
import json
import sys
from typing import Any, Dict, List, Optional

class UrlLabManager:
    """Manages URL parsing, manipulation, and normalization."""

    def parse(self, url: str) -> Dict[str, Any]:
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)
        return {
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "path": parsed.path,
            "params": parsed.params,
            "query": parsed.query,
            "fragment": parsed.fragment,
            "query_params": query_params
        }

    def encode(self, text: str) -> str:
        return urllib.parse.quote(text)

    def decode(self, text: str) -> str:
        return urllib.parse.unquote(text)

    def encode_plus(self, text: str) -> str:
        return urllib.parse.quote_plus(text)

    def decode_plus(self, text: str) -> str:
        return urllib.parse.unquote_plus(text)


    def join(self, base: str, paths: List[str]) -> str:
        url = base
        for path in paths:
            url = urllib.parse.urljoin(url, path)
        return url

    def params(self, url: str, mode: str, key: Optional[str] = None, value: Optional[str] = None) -> str:
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)

        if mode == "list":
            return json.dumps(query_params, indent=2)

        if mode == "get":
            if not key:
                raise ValueError("Key required for 'get' mode")
            return json.dumps(query_params.get(key, []), indent=2)

        if mode == "add":
            if not key or value is None:
                raise ValueError("Key and value required for 'add' mode")
            current = query_params.get(key, [])
            current.append(value)
            query_params[key] = current

        elif mode == "set":
            if not key or value is None:
                raise ValueError("Key and value required for 'set' mode")
            query_params[key] = [value]

        elif mode == "remove":
            if not key:
                raise ValueError("Key required for 'remove' mode")
            if key in query_params:
                del query_params[key]

        # Reconstruct URL
        # Note: parse_qs returns dict with lists. urlencode handles this with doseq=True.
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urllib.parse.urlunparse(new_parsed)

    def normalize(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        # 1. Lowercase scheme and netloc
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # 2. Sort query params
        query_params = urllib.parse.parse_qs(parsed.query)
        # Sort items by key, then sort values
        sorted_items = sorted((k, sorted(v)) for k, v in query_params.items())
        sorted_query = urllib.parse.urlencode(sorted_items, doseq=True)

        # 3. Remove default ports
        if scheme == 'http' and netloc.endswith(':80'):
            netloc = netloc[:-3]
        elif scheme == 'https' and netloc.endswith(':443'):
            netloc = netloc[:-4]

        # 4. Remove empty fragments? Optional. Keeping it simple.

        new_parsed = parsed._replace(scheme=scheme, netloc=netloc, query=sorted_query)
        return urllib.parse.urlunparse(new_parsed)

def run_url_lab_logic(args):
    """CLI handler for URL Lab."""
    manager = UrlLabManager()

    if args.action == "parse":
        result = manager.parse(args.url)
        print(json.dumps(result, indent=2))

    elif args.action == "encode":
        print(manager.encode(args.text))

    elif args.action == "decode":
        print(manager.decode(args.text))

    elif args.action == "encode-plus":
        print(manager.encode_plus(args.text))

    elif args.action == "decode-plus":
        print(manager.decode_plus(args.text))


    elif args.action == "join":
        # args.paths is a list
        print(manager.join(args.base, args.paths))

    elif args.action == "params":
        try:
            # args.mode, args.key, args.value are expected from CLI
            val = args.value if hasattr(args, 'value') else None
            key = args.key if hasattr(args, 'key') else None
            print(manager.params(args.url, args.mode, key, val))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "normalize":
        print(manager.normalize(args.url))

    sys.exit(0)
