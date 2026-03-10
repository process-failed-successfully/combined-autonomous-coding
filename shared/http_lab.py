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

    def generate_curl(self, method: str, url: str, headers: Optional[Dict[str, str]] = None, data: Optional[str] = None) -> str:
        """Generates a curl command string from request parameters."""
        cmd = ["curl", "-X", method.upper()]

        if headers:
            for k, v in headers.items():
                cmd.append(f"-H \"{k}: {v}\"")

        if data:
            # Escape single quotes and wrap in single quotes to prevent shell expansion
            escaped_data = data.replace("'", "'\\''")
            cmd.append(f"-d '{escaped_data}'")

        # Handle the case where url might not be complete (e.g., when first typing in the TUI)
        if url:
            if not url.startswith("http"):
                url = "http://" + url
            cmd.append(f"\"{url}\"")
        else:
            cmd.append("\"\"")

        return " ".join(cmd)

def run_http_lab_logic(args):
    """
    CLI logic for Http Lab.
    """
    manager = HttpLabManager()

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

    # Prepare kwargs
    kwargs = {
        "headers": headers,
        "timeout": args.timeout,
        "allow_redirects": args.follow,
        "verify": not args.no_verify,
    }

    if args.data:
        kwargs["data"] = args.data
    if json_data:
        kwargs["json"] = json_data
    if args.proxy:
        kwargs["proxies"] = {"http": args.proxy, "https": args.proxy}

    print(f"--- HTTP {args.method.upper()} {args.url} ---")
    if args.verbose:
        print(f"Headers: {headers}")
        if args.data:
            print(f"Data: {args.data}")
        if json_data:
            print(f"JSON: {json_data}")

    result = manager.request(args.method, args.url, **kwargs)

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

    if args.verbose:
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
    if args.output:
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
