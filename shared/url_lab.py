import urllib.parse
import sys
from typing import List, Dict, Any, Optional

class UrlLabManager:
    """
    Manages URL Lab operations: parsing, encoding, decoding, joining, and query manipulation.
    """

    def parse(self, url: str) -> Dict[str, Any]:
        """
        Parses a URL into its components.
        """
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        # Flatten params for display if single value
        flat_params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}

        return {
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "path": parsed.path,
            "params": parsed.params,
            "query": parsed.query,
            "fragment": parsed.fragment,
            "query_params": flat_params
        }

    def encode(self, text: str) -> str:
        """
        URL-encodes a string.
        """
        return urllib.parse.quote(text)

    def decode(self, text: str) -> str:
        """
        URL-decodes a string.
        """
        return urllib.parse.unquote(text)

    def join(self, base: str, path: str) -> str:
        """
        Joins a base URL with a path.
        """
        return urllib.parse.urljoin(base, path)

    def update_query(self, url: str, add_params: List[str] = None, remove_params: List[str] = None) -> str:
        """
        Adds/Updates or removes query parameters from a URL.
        add_params: List of "key=value" strings.
        remove_params: List of "key" strings.
        """
        parsed = urllib.parse.urlparse(url)
        query_dict = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)

        if remove_params:
            for key in remove_params:
                if key in query_dict:
                    del query_dict[key]

        if add_params:
            for item in add_params:
                if "=" in item:
                    key, value = item.split("=", 1)
                    # We replace existing values with the new one (standard setter behavior)
                    # If user wants multiple values, they should add them separately?
                    # For simplicity, let's treat it as "set/replace".
                    # To support multiple values properly with parse_qs, we need to handle lists.
                    query_dict[key] = [value]
                else:
                    # Key without value
                    query_dict[item] = [""]

        # Rebuild query string
        new_query = urllib.parse.urlencode(query_dict, doseq=True)

        # Rebuild URL
        new_url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        return new_url

def run_url_lab_logic(args):
    """
    CLI logic for URL Lab.
    """
    manager = UrlLabManager()

    if args.action == "parse":
        result = manager.parse(args.url)
        print(f"--- URL Components ---")
        print(f"Original: {args.url}")
        print(f"Scheme:   {result['scheme']}")
        print(f"Netloc:   {result['netloc']}")
        print(f"Path:     {result['path']}")
        if result['params']:
            print(f"Params:   {result['params']}")
        if result['fragment']:
            print(f"Fragment: {result['fragment']}")

        if result['query_params']:
            print("\nQuery Parameters:")
            for k, v in result['query_params'].items():
                print(f"  {k}: {v}")
        else:
            print("\n(No query parameters)")

        sys.exit(0)

    elif args.action == "encode":
        print(manager.encode(args.text))
        sys.exit(0)

    elif args.action == "decode":
        print(manager.decode(args.text))
        sys.exit(0)

    elif args.action == "join":
        print(manager.join(args.base, args.path))
        sys.exit(0)

    elif args.action == "query":
        new_url = manager.update_query(
            args.url,
            add_params=args.add,
            remove_params=args.remove
        )
        print(new_url)
        sys.exit(0)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
