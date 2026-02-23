import os
import requests
import sys
from pathlib import Path
from typing import List, Dict, Optional

class RFCLabManager:
    """Manages searching and fetching IETF RFCs."""

    RFC_INDEX_URL = "https://www.rfc-editor.org/rfc-index.txt"
    RFC_URL_TEMPLATE = "https://www.rfc-editor.org/rfc/rfc{number}.txt"

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")
        self.cache_dir = self.project_dir / ".rfc_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.cache_dir / "rfc-index.txt"

    def update_index(self, force: bool = False) -> bool:
        """Downloads the latest RFC index."""
        if self.index_path.exists() and not force:
            return True

        try:
            print(f"Downloading RFC index from {self.RFC_INDEX_URL}...")
            response = requests.get(self.RFC_INDEX_URL, timeout=30)
            response.raise_for_status()
            self.index_path.write_text(response.text, encoding="utf-8", errors="replace")
            return True
        except requests.RequestException as e:
            print(f"Error downloading index: {e}", file=sys.stderr)
            return False

    def search(self, query: str) -> List[Dict[str, str]]:
        """Searches the local index for RFCs matching the query."""
        if not self.index_path.exists():
            print("Index not found. Attempting to download...")
            if not self.update_index():
                return []

        query = query.lower()
        results = []

        try:
            content = self.index_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"Error reading index: {e}", file=sys.stderr)
            return []

        # The index format is roughly:
        # 0001 Host Software. S. Crocker. April 1969. (Format: TXT=21254 bytes) (Status: UNKNOWN) (DOI: 10.17487/RFC0001)

        for line in content.splitlines():
            if not line.strip(): continue
            if query in line.lower():
                parts = line.split(" ", 1)
                if len(parts) == 2 and parts[0].isdigit():
                    number = parts[0]
                    title = parts[1]
                    results.append({"number": number, "title": title, "line": line})

        return results

    def get_rfc(self, number: str) -> Optional[str]:
        """Fetches the content of a specific RFC."""
        # Normalize number
        clean_number = number.lower().replace("rfc", "").strip()

        cache_file = self.cache_dir / f"rfc{clean_number}.txt"
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8", errors="replace")

        url = self.RFC_URL_TEMPLATE.format(number=clean_number)
        print(f"Downloading RFC {clean_number} from {url}...")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 404:
                print(f"RFC {clean_number} not found (404).", file=sys.stderr)
                return None
            response.raise_for_status()
            content = response.text
            cache_file.write_text(content, encoding="utf-8", errors="replace")
            return content
        except requests.RequestException as e:
            print(f"Error downloading RFC {clean_number}: {e}", file=sys.stderr)
            return None

def run_rfc_lab_logic(args):
    """CLI Entry point for RFC Lab."""
    manager = RFCLabManager(args.project_dir)

    if args.action == "search":
        if not args.query:
            print("Error: --query required.", file=sys.stderr)
            sys.exit(1)

        results = manager.search(args.query)
        if not results:
            print("No results found.")
        else:
            print(f"Found {len(results)} RFCs:")
            for r in results:
                # Truncate title if too long
                title = r['title']
                if len(title) > 80:
                    title = title[:77] + "..."
                print(f"RFC {r['number']}: {title}")

    elif args.action == "read":
        if not args.number:
            print("Error: --number required.", file=sys.stderr)
            sys.exit(1)

        content = manager.get_rfc(args.number)
        if content:
            # Try to use pager
            import shutil
            import subprocess
            if shutil.which("less") and sys.stdout.isatty():
                try:
                    subprocess.run(["less"], input=content.encode("utf-8"))
                except Exception:
                    print(content)
            else:
                print(content)
        else:
            sys.exit(1)

    elif args.action == "update":
        if manager.update_index(force=True):
            print("✅ RFC index updated successfully.")
        else:
            sys.exit(1)
