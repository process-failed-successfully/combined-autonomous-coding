"""
Subresource Integrity (SRI) Lab
===============================

Computes SRI hashes (sha256, sha384, sha512) for web assets from local files or URLs.
Generates the corresponding HTML `<script>` or `<link>` tags.
"""

import argparse
import base64
import hashlib
import sys
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple


class SriManager:
    """Manages computation of Subresource Integrity hashes."""

    def __init__(self):
        pass

    def fetch_content(self, source: str) -> bytes:
        """Fetches content from a URL or reads from a local file path."""
        if source.startswith("http://") or source.startswith("https://"):
            try:
                # Add a generic User-Agent to avoid immediate 403 blocks from some CDNs
                req = urllib.request.Request(
                    source,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                )
                with urllib.request.urlopen(req) as response: # nosec B310
                    return response.read()
            except Exception as e:
                raise ValueError(f"Failed to fetch URL: {e}")
        else:
            path = Path(source)
            if not path.exists():
                raise ValueError(f"File not found: {source}")
            try:
                return path.read_bytes()
            except Exception as e:
                raise ValueError(f"Failed to read file: {e}")

    def compute_hashes(self, content: bytes) -> Dict[str, str]:
        """Computes base64-encoded sha256, sha384, and sha512 digests."""
        algorithms = {
            'sha256': hashlib.sha256,
            'sha384': hashlib.sha384,
            'sha512': hashlib.sha512
        }

        results = {}
        for algo_name, algo_func in algorithms.items():
            digest = algo_func(content).digest()
            b64_hash = base64.b64encode(digest).decode('utf-8')
            results[algo_name] = f"{algo_name}-{b64_hash}"

        return results

    def generate_html_tag(self, source: str, integrity_hash: str) -> str:
        """Generates the appropriate HTML tag based on the file extension."""
        source_lower = source.lower()
        if source_lower.endswith(".css"):
            return f'<link rel="stylesheet" href="{source}" integrity="{integrity_hash}" crossorigin="anonymous">'
        else:
            # Default to script tag for .js or unknown types
            return f'<script src="{source}" integrity="{integrity_hash}" crossorigin="anonymous"></script>'


def run_sri_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for SRI Lab."""
    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching SRI Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-sri")
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

    manager = SriManager()

    source = getattr(args, "source", None)
    if not source:
        print("Error: A source (file path or URL) is required. Use --source or launch the TUI with --tui.", file=sys.stderr)
        sys.exit(1)

    algo = getattr(args, "algo", "sha384").lower()
    if algo not in ["sha256", "sha384", "sha512"]:
        print(f"Error: Unsupported algorithm '{algo}'. Valid options: sha256, sha384, sha512.", file=sys.stderr)
        sys.exit(1)

    try:
        content = manager.fetch_content(source)
        hashes = manager.compute_hashes(content)

        integrity_hash = hashes[algo]
        html_tag = manager.generate_html_tag(source, integrity_hash)

        print(f"Algorithm: {algo}")
        print(f"Integrity: {integrity_hash}")
        print(f"\nHTML Tag:\n{html_tag}")

        if getattr(args, "all", False):
            print("\nAll Hashes:")
            for a, h in hashes.items():
                print(f"  {a}: {h}")

        return True

    except Exception as e:
        print(f"Error generating SRI: {e}", file=sys.stderr)
        sys.exit(1)
