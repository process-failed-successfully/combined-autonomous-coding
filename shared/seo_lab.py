import sys
import json
import urllib.request
import urllib.error
import urllib.parse
from html.parser import HTMLParser
from typing import List, Dict, Any, Optional

class SeoAnalyzer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stats = {
            "title": {"exists": False, "length": 0, "text": ""},
            "meta_description": {"exists": False, "length": 0, "content": ""},
            "h1": {"count": 0, "texts": []},
            "h2": {"count": 0},
            "h3": {"count": 0},
            "images": {"total": 0, "missing_alt": 0, "details": []},
            "links": {"total": 0, "internal": 0, "external": 0, "broken": 0},
            "canonical": {"exists": False, "href": ""},
            "viewport": {"exists": False, "content": ""},
            "robots": {"exists": False, "content": ""},
            "og_tags": {"title": False, "description": False, "image": False},
            "twitter_tags": {"card": False},
            "structured_data": False
        }
        self.in_title = False
        self.current_h1_text = ""
        self.in_h1 = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag = tag.lower()

        if tag == "title":
            self.in_title = True
            self.stats["title"]["exists"] = True

        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            property_ = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")

            if name == "description":
                self.stats["meta_description"]["exists"] = True
                self.stats["meta_description"]["content"] = content
                self.stats["meta_description"]["length"] = len(content)
            elif name == "viewport":
                self.stats["viewport"]["exists"] = True
                self.stats["viewport"]["content"] = content
            elif name == "robots":
                self.stats["robots"]["exists"] = True
                self.stats["robots"]["content"] = content
            elif name == "twitter:card":
                self.stats["twitter_tags"]["card"] = True

            if property_ == "og:title":
                self.stats["og_tags"]["title"] = True
            elif property_ == "og:description":
                self.stats["og_tags"]["description"] = True
            elif property_ == "og:image":
                self.stats["og_tags"]["image"] = True

        elif tag == "h1":
            self.stats["h1"]["count"] += 1
            self.in_h1 = True
            self.current_h1_text = ""
        elif tag == "h2":
            self.stats["h2"]["count"] += 1
        elif tag == "h3":
            self.stats["h3"]["count"] += 1

        elif tag == "img":
            self.stats["images"]["total"] += 1
            alt = attrs_dict.get("alt", "")
            src = attrs_dict.get("src", "")
            if not alt:
                self.stats["images"]["missing_alt"] += 1
                self.stats["images"]["details"].append({"src": src, "error": "Missing alt attribute"})
            elif len(alt) < 5:  # Arbitrary threshold for "meaningful" alt text
                self.stats["images"]["details"].append({"src": src, "warning": "Alt text might be too short", "alt": alt})

        elif tag == "a":
            self.stats["links"]["total"] += 1
            href = attrs_dict.get("href", "")
            if href.startswith("http"):
                self.stats["links"]["external"] += 1
            elif href.startswith("/") or href.startswith("#") or href.startswith("."):
                self.stats["links"]["internal"] += 1
            # Simple broken link heuristic (empty href)
            if not href:
                 self.stats["links"]["broken"] += 1

        elif tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            if rel == "canonical":
                self.stats["canonical"]["exists"] = True
                self.stats["canonical"]["href"] = attrs_dict.get("href", "")

        elif tag == "script":
            type_ = attrs_dict.get("type", "")
            if type_ == "application/ld+json":
                self.stats["structured_data"] = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        elif tag == "h1":
            self.in_h1 = False
            if self.current_h1_text:
                self.stats["h1"]["texts"].append(self.current_h1_text.strip())

    def handle_data(self, data):
        if self.in_title:
            self.stats["title"]["text"] += data
            self.stats["title"]["length"] += len(data)
        if self.in_h1:
            self.current_h1_text += data

class SeoLabManager:
    def analyze(self, html_content: str) -> Dict[str, Any]:
        analyzer = SeoAnalyzer()
        analyzer.feed(html_content)
        return analyzer.stats

    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.analyze(content)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

    def analyze_url(self, url: str) -> Dict[str, Any]:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            print(f"Error: URL scheme '{parsed.scheme}' not supported. Only http and https are allowed.", file=sys.stderr)
            sys.exit(1)

        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            )
            with urllib.request.urlopen(req) as response:  # nosec B310
                content = response.read().decode('utf-8')
            return self.analyze(content)
        except Exception as e:
            print(f"Error fetching URL: {e}", file=sys.stderr)
            sys.exit(1)

    def generate_report(self, stats: Dict[str, Any], output_format: str = "text"):
        if output_format == "json":
            print(json.dumps(stats, indent=2))
            return

        print("--- SEO Analysis Report ---")

        # Title
        title = stats["title"]
        print(f"\n[Title Tag]")
        if title["exists"]:
            print(f"  ✅ Found: {title['text'][:50]}..." if len(title['text']) > 50 else f"  ✅ Found: {title['text']}")
            print(f"  Length: {title['length']} characters")
            if title['length'] < 30:
                print("  ⚠️  Warning: Title might be too short (recommended 30-60 chars).")
            elif title['length'] > 60:
                print("  ⚠️  Warning: Title might be too long (recommended 30-60 chars).")
            else:
                print("  ✅ Length is optimal.")
        else:
            print("  ❌ Missing <title> tag!")

        # Meta Description
        desc = stats["meta_description"]
        print(f"\n[Meta Description]")
        if desc["exists"]:
            print(f"  ✅ Found: {desc['content'][:50]}..." if len(desc['content']) > 50 else f"  ✅ Found: {desc['content']}")
            print(f"  Length: {desc['length']} characters")
            if desc['length'] < 50:
                print("  ⚠️  Warning: Description might be too short (recommended 50-160 chars).")
            elif desc['length'] > 160:
                print("  ⚠️  Warning: Description might be too long (recommended 50-160 chars).")
            else:
                print("  ✅ Length is optimal.")
        else:
            print("  ❌ Missing meta description!")

        # Headings
        h1 = stats["h1"]
        print(f"\n[Headings]")
        if h1["count"] == 0:
            print("  ❌ Missing <h1> tag! (Critical for SEO)")
        elif h1["count"] > 1:
            print(f"  ⚠️  Warning: Found {h1['count']} <h1> tags. Usually strictly one per page is recommended.")
            for t in h1['texts']:
                print(f"    - {t}")
        else:
            print(f"  ✅ Found 1 <h1> tag: {h1['texts'][0]}")

        print(f"  H2 Tags: {stats['h2']['count']}")
        print(f"  H3 Tags: {stats['h3']['count']}")

        # Images
        imgs = stats["images"]
        print(f"\n[Images]")
        print(f"  Total: {imgs['total']}")
        if imgs["missing_alt"] > 0:
            print(f"  ❌ Missing Alt Text: {imgs['missing_alt']} images")
            for detail in imgs['details']:
                if 'error' in detail:
                    print(f"    - {detail['src'] or 'Unknown Source'}")
        else:
            print("  ✅ All images have alt text.")

        # Links
        links = stats["links"]
        print(f"\n[Links]")
        print(f"  Total: {links['total']}")
        print(f"  Internal: {links['internal']}")
        print(f"  External: {links['external']}")
        if links['broken'] > 0:
             print(f"  ⚠️  Found {links['broken']} potentially broken links (empty href).")

        # Technical
        print(f"\n[Technical]")
        print(f"  Canonical Link: {'✅ Found' if stats['canonical']['exists'] else '❌ Missing'}")
        print(f"  Viewport Meta:  {'✅ Found' if stats['viewport']['exists'] else '❌ Missing'}")
        print(f"  Robots Meta:    {'✅ Found' if stats['robots']['exists'] else '❌ Missing'}")
        print(f"  Structured Data: {'✅ Found' if stats['structured_data'] else '❌ Missing'}")

        # Social
        print(f"\n[Social Tags]")
        og = stats["og_tags"]
        print(f"  Open Graph Title:       {'✅' if og['title'] else '❌'}")
        print(f"  Open Graph Description: {'✅' if og['description'] else '❌'}")
        print(f"  Open Graph Image:       {'✅' if og['image'] else '❌'}")
        print(f"  Twitter Card:           {'✅' if stats['twitter_tags']['card'] else '❌'}")

        # Final Score (Simple Calculation)
        score = 100
        if not stats["title"]["exists"]: score -= 20
        if not stats["meta_description"]["exists"]: score -= 15
        if h1["count"] == 0: score -= 20
        if h1["count"] > 1: score -= 10
        if imgs["missing_alt"] > 0: score -= 10
        if not stats["viewport"]["exists"]: score -= 10
        if not stats["canonical"]["exists"]: score -= 5

        score = max(0, score)
        color = ""
        if score >= 90: color = "✅"
        elif score >= 70: color = "⚠️"
        else: color = "❌"

        print(f"\n{color} SEO Score: {score}/100")

def run_seo_lab_logic(args):
    manager = SeoLabManager()

    if args.url:
        print(f"Analyzing URL: {args.url}...")
        stats = manager.analyze_url(args.url)
    elif args.file:
        print(f"Analyzing File: {args.file}...")
        stats = manager.analyze_file(args.file)
    else:
        print("Error: Please provide --url or --file.", file=sys.stderr)
        sys.exit(1)

    manager.generate_report(stats, args.format)
    sys.exit(0)
