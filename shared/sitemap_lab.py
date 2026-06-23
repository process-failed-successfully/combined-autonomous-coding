import sys
import defusedxml.ElementTree as ET
import urllib.request
import urllib.error

class SitemapManager:
    """Manager for fetching and parsing XML sitemaps."""

    def fetch(self, url: str) -> str:
        """Fetches the sitemap from the specified URL."""
        if not (url.startswith("http://") or url.startswith("https://")):
            return "Error: Only http:// and https:// URLs are allowed."

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:  # nosec B310 - URL schemes are validated above
                return response.read().decode('utf-8')
        except urllib.error.URLError as e:
            return f"Error fetching {url}: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

    def parse(self, content: str) -> dict:
        """
        Parses sitemap XML content.
        Returns a dict with 'type' ('sitemapindex', 'urlset', or 'text') and a list of 'urls'.
        """
        content = content.strip()
        result = {"type": "unknown", "urls": []}

        if not content:
            return result

        # Heuristic for plain text sitemap
        if not content.startswith("<"):
            result["type"] = "text"
            result["urls"] = [{"loc": line.strip()} for line in content.splitlines() if line.strip()]
            return result

        try:
            root = ET.fromstring(content)
            # Handle XML namespaces by removing them for easier searching
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]

            if root.tag == "sitemapindex":
                result["type"] = "sitemapindex"
                for sitemap in root.findall("sitemap"):
                    loc = sitemap.find("loc")
                    if loc is not None and loc.text:
                        result["urls"].append({"loc": loc.text.strip()})

            elif root.tag == "urlset":
                result["type"] = "urlset"
                for url_elem in root.findall("url"):
                    loc = url_elem.find("loc")
                    if loc is not None and loc.text:
                        entry = {"loc": loc.text.strip()}
                        lastmod = url_elem.find("lastmod")
                        if lastmod is not None and lastmod.text:
                            entry["lastmod"] = lastmod.text.strip()
                        changefreq = url_elem.find("changefreq")
                        if changefreq is not None and changefreq.text:
                            entry["changefreq"] = changefreq.text.strip()
                        priority = url_elem.find("priority")
                        if priority is not None and priority.text:
                            entry["priority"] = priority.text.strip()
                        result["urls"].append(entry)
            else:
                result["type"] = "unknown"

        except ET.ParseError:
            result["type"] = "error"

        return result


def run_sitemap_lab_logic(args) -> bool:
    """CLI logic for the sitemap-lab command."""
    manager = SitemapManager()

    if args.action == "fetch":
        content = manager.fetch(args.url)
        print(content)
        return True

    elif args.action == "parse":
        content = ""
        if hasattr(args, "file") and args.file:
            try:
                with open(args.file, 'r') as f:
                    content = f.read()
            except IOError as e:
                print(f"Error reading {args.file}: {e}", file=sys.stderr)
                return False
        elif hasattr(args, "content") and args.content:
            content = args.content
        elif not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            print("Error: must provide --file, --content, or pipe via stdin", file=sys.stderr)
            return False

        parsed = manager.parse(content)

        if parsed["type"] == "error":
             print("Error parsing sitemap.", file=sys.stderr)
             return False

        print(f"Sitemap type: {parsed['type']}")
        print(f"Found {len(parsed['urls'])} URLs:")
        for url_data in parsed["urls"]:
            parts = [f"loc: {url_data['loc']}"]
            if "lastmod" in url_data:
                parts.append(f"lastmod: {url_data['lastmod']}")
            if "changefreq" in url_data:
                parts.append(f"changefreq: {url_data['changefreq']}")
            if "priority" in url_data:
                parts.append(f"priority: {url_data['priority']}")
            print(" | ".join(parts))

        return True

    return False
