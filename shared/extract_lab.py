import re
import sys
import argparse
from typing import Dict, List, Any

class ExtractLabManager:
    """Manages the extraction of Indicators of Compromise (IoCs)."""

    def __init__(self):
        # Compiled regexes for IoC extraction
        self.ip_regex = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        self.url_regex = re.compile(r'https?://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d{1,5})?(?:/[^\s]*)?')
        self.email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.hash_md5_regex = re.compile(r'\b[a-fA-F0-9]{32}\b')
        self.hash_sha1_regex = re.compile(r'\b[a-fA-F0-9]{40}\b')
        self.hash_sha256_regex = re.compile(r'\b[a-fA-F0-9]{64}\b')

    def extract_iocs(self, text: str) -> Dict[str, List[str]]:
        """Extracts IPs, URLs, Emails, and Hashes from the given text."""
        ips = list(set(self.ip_regex.findall(text)))
        urls = list(set(self.url_regex.findall(text)))
        emails = list(set(self.email_regex.findall(text)))

        md5s = list(set(self.hash_md5_regex.findall(text)))
        sha1s = list(set(self.hash_sha1_regex.findall(text)))
        sha256s = list(set(self.hash_sha256_regex.findall(text)))

        hashes = list(set(md5s + sha1s + sha256s))

        return {
            "ips": ips,
            "urls": urls,
            "emails": emails,
            "hashes": hashes
        }


def run_extract_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for Extract Lab."""
    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        from pathlib import Path
        print("Launching Extract Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-extract")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
            sys.exit(0)
        return True

    manager = ExtractLabManager()

    text_input = getattr(args, "text", None)

    if not text_input:
        if not sys.stdin.isatty():
            text_input = sys.stdin.read()
        else:
            print("Error: --text argument is required when not piping.", file=sys.stderr)
            sys.exit(1)

    results = manager.extract_iocs(text_input)

    # Output formatting
    print("--- Extracted IoCs ---")
    if results["ips"]:
        print(f"IPs ({len(results['ips'])}):")
        for ip in results["ips"]:
            print(f"  - {ip}")

    if results["urls"]:
        print(f"URLs ({len(results['urls'])}):")
        for url in results["urls"]:
            print(f"  - {url}")

    if results["emails"]:
        print(f"Emails ({len(results['emails'])}):")
        for email in results["emails"]:
            print(f"  - {email}")

    if results["hashes"]:
        print(f"Hashes ({len(results['hashes'])}):")
        for h in results["hashes"]:
            print(f"  - {h}")

    if not any(results.values()):
        print("No IoCs found.")

    sys.exit(0)
