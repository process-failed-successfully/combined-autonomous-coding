import urllib.parse
import json
import sys
import requests
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

    def extract(self, url: str, component: str) -> str:
        parsed = urllib.parse.urlparse(url)
        if component == "scheme":
            return parsed.scheme
        elif component == "netloc":
            return parsed.netloc
        elif component == "path":
            return parsed.path
        elif component == "query":
            return parsed.query
        elif component == "fragment":
            return parsed.fragment
        elif component == "port":
            try:
                return str(parsed.port) if parsed.port is not None else ""
            except ValueError:
                return ""
        elif component == "hostname":
            return parsed.hostname if parsed.hostname else ""
        else:
            raise ValueError(f"Unknown component: {component}")

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

    def diff(self, url1: str, url2: str) -> Dict[str, Any]:
        """Compares two URLs and returns the differences."""
        p1 = self.parse(url1)
        p2 = self.parse(url2)
        diff_result = {}

        for key in ["scheme", "netloc", "path", "fragment"]:
            if p1[key] != p2[key]:
                diff_result[key] = {"url1": p1[key], "url2": p2[key]}

        q1 = p1["query_params"]
        q2 = p2["query_params"]

        added = {k: q2[k] for k in q2 if k not in q1}
        removed = {k: q1[k] for k in q1 if k not in q2}
        changed = {k: {"url1": q1[k], "url2": q2[k]} for k in q1 if k in q2 and q1[k] != q2[k]}

        if added or removed or changed:
            diff_result["query_params"] = {}
            if added:
                diff_result["query_params"]["added"] = added
            if removed:
                diff_result["query_params"]["removed"] = removed
            if changed:
                diff_result["query_params"]["changed"] = changed

        return diff_result

    def unshorten(self, url: str) -> Dict[str, Any]:
        """Resolves a URL following redirects and returns the final URL and trace."""
        try:
            # We use HEAD first to avoid downloading body content if possible
            # We set a timeout and a user-agent to look like a normal client
            headers = {"User-Agent": "CombinedAutonomousCodingAgent/1.0"}
            response = requests.head(url, allow_redirects=True, timeout=10, headers=headers)

            # If the server doesn't support HEAD or throws an error on HEAD, fallback to GET
            if response.status_code >= 400 and response.status_code != 404:
                response = requests.get(url, allow_redirects=True, timeout=10, headers=headers, stream=True)

            trace = []
            for resp in response.history:
                trace.append({
                    "url": resp.url,
                    "status_code": resp.status_code,
                    "reason": resp.reason
                })

            trace.append({
                "url": response.url,
                "status_code": response.status_code,
                "reason": response.reason
            })

            return {
                "initial_url": url,
                "final_url": response.url,
                "status_code": response.status_code,
                "redirects": len(response.history),
                "trace": trace
            }
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to unshorten URL: {e}")


def run_url_lab_logic(args):
    """CLI handler for URL Lab."""
    manager = UrlLabManager()

    if args.action == "parse":
        result = manager.parse(args.url)
        print(json.dumps(result, indent=2))

    elif args.action == "extract":
        try:
            print(manager.extract(args.url, args.component))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

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

    elif args.action == "unshorten":
        try:
            result = manager.unshorten(args.url)
            print(json.dumps(result, indent=2))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "diff":
        result = manager.diff(args.url1, args.url2)
        print(json.dumps(result, indent=2))

    sys.exit(0)
