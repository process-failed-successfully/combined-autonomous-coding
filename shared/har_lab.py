import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

class HarLabManager:
    """Manages HAR (HTTP Archive) file parsing and processing."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def _parse_har(self, har_file: Path) -> Dict[str, Any]:
        """Parses a HAR file and returns the loaded JSON data."""
        if not har_file.exists():
            raise FileNotFoundError(f"HAR file not found: {har_file}")

        try:
            with open(har_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'log' not in data or 'entries' not in data['log']:
                raise ValueError("Invalid HAR file structure. Missing 'log' or 'entries'.")
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse HAR file: {e}")

    def summarize(self, har_file: Path) -> List[Dict[str, Any]]:
        """Returns a summary of requests in the HAR file."""
        data = self._parse_har(har_file)
        entries = data['log']['entries']

        summary = []
        for entry in entries:
            req = entry.get('request', {})
            res = entry.get('response', {})

            summary.append({
                "method": req.get('method', 'UNKNOWN'),
                "url": req.get('url', ''),
                "status": res.get('status', 0),
                "time": entry.get('time', 0.0),
                "content_type": res.get('content', {}).get('mimeType', 'N/A'),
                "size": res.get('content', {}).get('size', 0)
            })

        return summary

    def extract_urls(self, har_file: Path, filter_method: Optional[str] = None) -> List[str]:
        """Extracts all requested URLs from the HAR file, optionally filtered by method."""
        data = self._parse_har(har_file)
        entries = data['log']['entries']

        urls = []
        for entry in entries:
            req = entry.get('request', {})
            method = req.get('method', '').upper()

            if filter_method and method != filter_method.upper():
                continue

            url = req.get('url')
            if url:
                urls.append(url)

        return urls

    def generate_curl(self, har_file: Path, entry_index: int = 0) -> str:
        """Generates a curl command for a specific entry in the HAR file."""
        data = self._parse_har(har_file)
        entries = data['log']['entries']

        if not entries:
            raise ValueError("HAR file contains no entries.")

        if entry_index < 0 or entry_index >= len(entries):
            raise IndexError(f"Entry index {entry_index} out of bounds. Must be between 0 and {len(entries)-1}.")

        req = entries[entry_index].get('request', {})
        method = req.get('method', 'GET')
        url = req.get('url', '')

        curl_cmd = f"curl -X {method} '{url}'"

        # Add headers
        for header in req.get('headers', []):
            name = header.get('name')
            value = header.get('value')
            if name and value:
                # Escape single quotes in header values
                value_escaped = value.replace("'", "'\\''")
                curl_cmd += f" \\\n  -H '{name}: {value_escaped}'"

        # Add post data if present
        post_data = req.get('postData', {})
        text = post_data.get('text')

        if text:
            # Escape single quotes in body
            text_escaped = text.replace("'", "'\\''")
            curl_cmd += f" \\\n  -d '{text_escaped}'"

        return curl_cmd

def run_har_lab_logic(args) -> None:
    """CLI logic for Har Lab."""
    # Ensure project_dir exists as a Path
    project_dir = getattr(args, 'project_dir', Path("."))
    if isinstance(project_dir, str):
        project_dir = Path(project_dir)

    manager = HarLabManager(project_dir)

    if args.action == "summary":
        if not args.file:
            print("Error: --file argument is required for 'summary'.", file=sys.stderr)
            sys.exit(1)

        try:
            summary = manager.summarize(Path(args.file))
            print(f"--- HAR Summary: {args.file} ---")
            print(f"Total Requests: {len(summary)}\n")

            # Find max lengths for formatting
            max_method = max([len(s['method']) for s in summary] + [6])
            max_status = 6
            max_time = max([len(f"{s['time']:.0f}ms") for s in summary] + [6])

            # Print header
            header = f"{'Method':<{max_method}} | {'Status':<{max_status}} | {'Time':<{max_time}} | URL"
            print(header)
            print("-" * len(header))

            # Print rows
            for s in summary:
                time_str = f"{s['time']:.0f}ms"
                print(f"{s['method']:<{max_method}} | {s['status']:<{max_status}} | {time_str:<{max_time}} | {s['url']}")

            sys.exit(0)
        except Exception as e:
            print(f"Error processing HAR file: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "urls":
        if not args.file:
            print("Error: --file argument is required for 'urls'.", file=sys.stderr)
            sys.exit(1)

        try:
            urls = manager.extract_urls(Path(args.file), filter_method=getattr(args, 'method', None))
            for url in urls:
                print(url)
            sys.exit(0)
        except Exception as e:
            print(f"Error processing HAR file: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "curl":
        if not args.file:
            print("Error: --file argument is required for 'curl'.", file=sys.stderr)
            sys.exit(1)

        index = getattr(args, 'index', 0)
        try:
            curl_cmd = manager.generate_curl(Path(args.file), entry_index=index)
            print(curl_cmd)
            sys.exit(0)
        except Exception as e:
            print(f"Error generating curl command: {e}", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)
