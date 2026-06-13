import sys
import urllib.request
import urllib.error
import defusedxml.ElementTree as ET
from typing import List, Dict, Any, Union

class SitemapManager:
    """Manager for fetching and parsing XML sitemaps."""

    def fetch(self, url: str) -> str:
        """Fetches the sitemap.xml from the specified URL."""
        if not (url.startswith("http://") or url.startswith("https://")):
            return "Error: Only http:// and https:// URLs are allowed."

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req) as response:  # nosec B310
                return response.read().decode('utf-8')
        except urllib.error.URLError as e:
            return f"Error fetching {url}: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

    def parse(self, content: str) -> Dict[str, Any]:
        """Parses the given sitemap XML content.
        Returns a dict indicating type ('sitemapindex' or 'urlset') and the list of URLs."""
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            return {"error": f"Failed to parse XML: {e}"}

        # XML tags in sitemaps are typically namespaced, e.g., {http://www.sitemaps.org/schemas/sitemap/0.9}urlset
        # We can handle namespaces by stripping them or using wildcard search.

        tag_name = root.tag.split('}', 1)[-1] if '}' in root.tag else root.tag

        results = []
        if tag_name == 'sitemapindex':
            for sitemap in root:
                # Check with and without namespace if first attempt fails
                loc_text = None
                for child in sitemap:
                    child_tag = child.tag.split('}', 1)[-1] if '}' in child.tag else child.tag
                    if child_tag == 'loc':
                        loc_text = child.text
                        break

                if loc_text:
                    results.append({"type": "sitemap", "loc": loc_text})
            return {"type": "sitemapindex", "urls": results}

        elif tag_name == 'urlset':
            for url_elem in root:
                loc_text = None
                for child in url_elem:
                    child_tag = child.tag.split('}', 1)[-1] if '}' in child.tag else child.tag
                    if child_tag == 'loc':
                        loc_text = child.text
                        break

                if loc_text:
                    results.append({"type": "url", "loc": loc_text})
            return {"type": "urlset", "urls": results}

        else:
            return {"error": f"Unknown root tag: {tag_name}"}

def run_sitemap_lab_logic(args) -> bool:
    """CLI logic for the sitemap-lab command."""
    if args.action == "fetch":
        manager = SitemapManager()
        content = manager.fetch(args.url)
        print(content)
        return True

    elif args.action == "parse":
        if not args.file and not args.content:
            print("Error: must provide --file or --content", file=sys.stderr)
            return False

        content = args.content
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except IOError as e:
                print(f"Error reading {args.file}: {e}", file=sys.stderr)
                return False

        manager = SitemapManager()
        result = manager.parse(content)

        if "error" in result:
            print(result["error"], file=sys.stderr)
            return False

        print(f"Sitemap type: {result.get('type')}")
        print(f"Total URLs found: {len(result.get('urls', []))}")
        for item in result.get('urls', []):
            print(f"- {item.get('loc')}")

        return True

    return False
