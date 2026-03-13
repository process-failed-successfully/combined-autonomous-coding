import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import urllib.parse


class HarLabManager:
    """
    Manages HTTP Archive (.har) files: summarization and cURL conversion.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def load_har(self, filepath: Path) -> Dict[str, Any]:
        """Loads and parses a HAR file."""
        if not filepath.exists():
            raise FileNotFoundError(f"HAR file not found: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Basic validation
                if "log" not in data or "entries" not in data["log"]:
                    raise ValueError("Invalid HAR format: Missing 'log' or 'entries' key.")
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}")

    def summarize(self, har_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a summary of the HAR file."""
        entries = har_data.get("log", {}).get("entries", [])

        total_requests = len(entries)
        total_size_bytes = 0
        methods = {}
        statuses = {}
        domains = {}

        for entry in entries:
            req = entry.get("request", {})
            res = entry.get("response", {})

            # Method
            method = req.get("method", "UNKNOWN")
            methods[method] = methods.get(method, 0) + 1

            # Status
            status = res.get("status", 0)
            statuses[status] = statuses.get(status, 0) + 1

            # Domain
            url = req.get("url", "")
            if url:
                parsed_url = urllib.parse.urlparse(url)
                domain = parsed_url.netloc
                domains[domain] = domains.get(domain, 0) + 1

            # Size
            size = res.get("bodySize", 0)
            if size > 0:
                total_size_bytes += size

        return {
            "total_requests": total_requests,
            "total_size_bytes": total_size_bytes,
            "methods": methods,
            "statuses": statuses,
            "domains": domains
        }

    def entry_to_curl(self, entry: Dict[str, Any]) -> str:
        """Converts a single HAR entry to a cURL command."""
        req = entry.get("request", {})
        method = req.get("method", "GET")
        url = req.get("url", "")
        headers = req.get("headers", [])
        post_data = req.get("postData", {})

        command = ["curl", "-X", method, f"'{url}'"]

        for header in headers:
            name = header.get("name")
            value = header.get("value")
            # Don't include pseudo-headers (like :authority in HTTP/2)
            if name and not name.startswith(":"):
                # Escape single quotes in header values
                escaped_value = value.replace("'", "'\\''")
                command.append(f"-H '{name}: {escaped_value}'")

        if post_data and post_data.get("text"):
            text = post_data.get("text")
            escaped_text = text.replace("'", "'\\''")
            command.append(f"-d '{escaped_text}'")

        return " ".join(command)

    def extract_urls(self, har_data: Dict[str, Any]) -> List[str]:
        """Extracts all URLs from the HAR file."""
        entries = har_data.get("log", {}).get("entries", [])
        urls = [entry.get("request", {}).get("url", "") for entry in entries if entry.get("request", {}).get("url")]
        return urls


def run_har_lab_logic(args) -> bool:
    """CLI logic for HAR Lab."""

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        import asyncio
        try:
            # Only import TUI if needed
            from shared.tui import AgentTUI
        except ImportError:
            # Fallback for missing deps during tests
            AgentTUI = None

        if AgentTUI:
            print("Launching HAR Lab TUI...")
            app = AgentTUI(project_dir=args.project_dir, start_tab="tab-har")
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                asyncio.ensure_future(app.run_async())
            else:
                app.run()
        sys.exit(0)

    manager = HarLabManager(args.project_dir)

    try:
        if not args.file:
            print("Error: --file is required.", file=sys.stderr)
            return False

        filepath = Path(args.file)
        data = manager.load_har(filepath)

        action = getattr(args, "action", None)

        if action == "summary":
            summary = manager.summarize(data)
            print(json.dumps(summary, indent=2))
            return True

        elif action == "urls":
            urls = manager.extract_urls(data)
            for url in urls:
                print(url)
            return True

        elif action == "curl":
            entries = data.get("log", {}).get("entries", [])
            index = getattr(args, "index", 0)

            if index < 0 or index >= len(entries):
                print(f"Error: Index out of bounds (0-{len(entries)-1}).", file=sys.stderr)
                return False

            curl_cmd = manager.entry_to_curl(entries[index])
            print(curl_cmd)
            return True

        else:
            print(f"Error: Unknown action {action}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
