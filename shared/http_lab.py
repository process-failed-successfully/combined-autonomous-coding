import sys
import json
import requests
import time
import shlex
import argparse
from typing import Dict, Any, Optional, List
from pathlib import Path
from urllib.parse import urlparse

class HttpLabManager:
    """
    Manages HTTP requests and response handling.
    """

    def request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        Executes an HTTP request.
        """
        if not url.startswith("http"):
            url = "http://" + url

        try:
            start_time = time.time()
            response = requests.request(method, url, **kwargs)
            elapsed = time.time() - start_time

            return {
                "status_code": response.status_code,
                "reason": response.reason,
                "headers": dict(response.headers),
                "body": response.text,
                "json": self._try_parse_json(response),
                "elapsed": elapsed,
                "url": response.url,
                "ok": response.ok,
                "is_redirect": response.is_redirect,
                "cookies": response.cookies.get_dict(),
                "encoding": response.encoding
            }
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def _try_parse_json(self, response):
        try:
            return response.json()
        except ValueError:
            return None

    def parse_curl(self, curl_cmd: str) -> Optional[Dict[str, Any]]:
        """Parses a curl command and extracts method, url, headers, and body."""
        try:
            tokens = shlex.split(curl_cmd)
        except ValueError:
            return None

        if not tokens:
            return None

        # Remove 'curl' command itself if present
        if tokens[0].lower() == 'curl':
            tokens = tokens[1:]

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('url_pos', nargs='?')
        parser.add_argument('--url', dest='url_named')
        parser.add_argument('-X', '--request', dest='method')
        parser.add_argument('-H', '--header', dest='headers', action='append', default=[])
        parser.add_argument('-d', '--data', '--data-raw', '--data-binary', '--data-ascii', dest='data')
        parser.add_argument('-u', '--user', dest='auth')
        parser.add_argument('-A', '--user-agent', dest='user_agent')
        parser.add_argument('-I', '--head', action='store_true')

        import contextlib
        import io
        try:
            # parse_known_args doesn't exit on unknown args usually, but if it hits something like -h it might.
            with contextlib.redirect_stderr(io.StringIO()):
                args, unknown = parser.parse_known_args(tokens)
        except SystemExit:
            return None

        url = args.url_named or args.url_pos
        if not url:
            # Fallback for URLs not caught (e.g. at the end with options before it)
            for u in unknown:
                if u.startswith('http://') or u.startswith('https://'):
                    url = u
                    break

        method = args.method
        if not method:
            if args.data is not None:
                method = 'POST'
            elif args.head:
                method = 'HEAD'
            else:
                method = 'GET'
        else:
            method = method.upper()

        headers = {}
        for h in args.headers:
            if ':' in h:
                k, v = h.split(':', 1)
                headers[k.strip()] = v.strip()

        # Handle User-Agent
        if args.user_agent:
            headers['User-Agent'] = args.user_agent

        # Basic auth
        if args.auth:
            import base64
            auth_str = base64.b64encode(args.auth.encode()).decode('utf-8')
            headers['Authorization'] = f'Basic {auth_str}'

        return {
            'url': url or '',
            'method': method,
            'headers': headers,
            'data': args.data,
        }

    def generate_curl(self, method: str, url: str, headers: Optional[Dict[str, str]] = None, data: Optional[Any] = None, json_data: Optional[Any] = None) -> str:
        """Generates a curl command string from request parameters."""
        command = ["curl", "-X", method.upper()]

        if not url.startswith("http"):
            url = "http://" + url
        command.append(f'"{url}"')

        if headers:
            for k, v in headers.items():
                # Avoid quoting inside quote
                escaped_v = str(v).replace('"', '\\"')
                command.append(f'-H "{k}: {escaped_v}"')

        if json_data is not None:
            if not headers or "Content-Type" not in [k.title() for k in headers.keys()]:
                 command.append('-H "Content-Type: application/json"')
            json_str = json.dumps(json_data)
            escaped_json = json_str.replace("'", "'\\''")
            command.append(f"-d '{escaped_json}'")
        elif data is not None:
            escaped_data = str(data).replace("'", "'\\''")
            command.append(f"-d '{escaped_data}'")

        return " ".join(command)

def run_http_lab_logic(args):
    """
    CLI logic for Http Lab.
    """
    manager = HttpLabManager()

    if getattr(args, "curl", None):
        parsed = manager.parse_curl(args.curl)
        if not parsed:
            print("Error parsing curl command.", file=sys.stderr)
            sys.exit(1)
        method = parsed.get("method", "GET")
        url = parsed.get("url", "")
        headers = parsed.get("headers", {})
        data = parsed.get("data", None)
        json_data = None
        # Handle parsed json data correctly if content-type is json
        if data and headers.get("Content-Type", "").startswith("application/json"):
            try:
                json_data = json.loads(data)
                data = None
            except Exception:
                pass
    else:
        method = args.method
        url = args.url
        if not url:
            print("Error: Target URL is required unless using --curl.", file=sys.stderr)
            sys.exit(1)
        # Parse headers
        headers = {}
        if args.header:
            for h in args.header:
                if ":" in h:
                    k, v = h.split(":", 1)
                    headers[k.strip()] = v.strip()
                else:
                    pass

        # Parse JSON body
        json_data = None
        if args.json:
            try:
                json_data = json.loads(args.json)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON body: {e}", file=sys.stderr)
                sys.exit(1)
        data = args.data

    if getattr(args, "to_curl", False):
        curl_cmd = manager.generate_curl(method, url, headers=headers, data=data, json_data=json_data)
        print(curl_cmd)
        sys.exit(0)

    # Prepare kwargs
    kwargs = {
        "headers": headers,
        "timeout": getattr(args, "timeout", 10.0),
        "allow_redirects": getattr(args, "follow", False),
        "verify": not getattr(args, "no_verify", False),
    }

    if data:
        kwargs["data"] = data
    if json_data:
        kwargs["json"] = json_data
    if getattr(args, "proxy", None):
        kwargs["proxies"] = {"http": args.proxy, "https": args.proxy}

    print(f"--- HTTP {method.upper()} {url} ---")
    if getattr(args, "verbose", False):
        print(f"Headers: {headers}")
        if data:
            print(f"Data: {data}")
        if json_data:
            print(f"JSON: {json_data}")

    result = manager.request(method, url, **kwargs)

    if "error" in result:
        print(f"❌ Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    # Output Handling
    status_code = result['status_code']
    reason = result['reason']
    elapsed = result['elapsed']

    # Colorize Status Code
    try:
        from rich.console import Console
        from rich.syntax import Syntax
        from rich.table import Table
        from rich.panel import Panel
        from rich import box
        console = Console()
        use_rich = True
    except ImportError:
        console = None
        use_rich = False

    status_color = "green" if 200 <= status_code < 300 else \
                   "yellow" if 300 <= status_code < 400 else \
                   "red"

    if use_rich:
        console.print(f"Status: [{status_color}]{status_code} {reason}[/{status_color}]  (Time: {elapsed:.3f}s)")
    else:
        print(f"Status: {status_code} {reason}  (Time: {elapsed:.3f}s)")

    if getattr(args, "verbose", False):
        print(f"Final URL: {result['url']}")

    # Headers
    if use_rich:
        table = Table(title="Response Headers", box=box.SIMPLE, show_header=True, header_style="bold magenta")
        table.add_column("Header", style="cyan")
        table.add_column("Value")
        for k, v in result['headers'].items():
            table.add_row(k, v)
        console.print(table)
    else:
        print("\n--- Headers ---")
        for k, v in result['headers'].items():
            print(f"{k}: {v}")

    # Body
    if getattr(args, "output", None):
        try:
            with open(args.output, "w", encoding=result.get("encoding", "utf-8") or "utf-8") as f:
                f.write(result["body"])
            print(f"\n✅ Body saved to {args.output}")
        except Exception as e:
            print(f"\n❌ Error saving output: {e}", file=sys.stderr)
    else:
        print("\n--- Body ---")
        if result['json'] and use_rich:
            try:
                # Pretty print JSON with syntax highlighting
                formatted_json = json.dumps(result['json'], indent=2)
                syntax = Syntax(formatted_json, "json", theme="monokai", line_numbers=False)
                console.print(syntax)
            except Exception:
                print(result['body'])
        elif result['json']:
             print(json.dumps(result['json'], indent=2))
        else:
            print(result['body'])

    sys.exit(0 if result['ok'] else 1)
