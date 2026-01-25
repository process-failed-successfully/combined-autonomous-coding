import os
import shutil
import http.server
import socketserver
import markdown
import yaml
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from shared.health import HealthCalculator
from shared.logger import setup_logger

logger, _ = setup_logger("docs_manager")

class DocsManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.docs_dir = self.project_dir / "docs"
        self.site_dir = self.project_dir / "site"
        self.conf_path = self.docs_dir / "conf.yaml"

    def init(self) -> bool:
        """Initializes the documentation structure."""
        if not self.docs_dir.exists():
            self.docs_dir.mkdir()
            print(f"✅ Created directory: {self.docs_dir}")

        # Create default index.md
        index_path = self.docs_dir / "index.md"
        if not index_path.exists():
            content = f"""# Documentation for {self.project_dir.name}

Welcome to the project documentation.

## Contents

- [Dashboard](dashboard.html) - Project Health & Status
- [ADRs](adrs.html) - Architecture Decision Records
- [Change Log](changelog.html)

## Modules

Add your module documentation here.
"""
            index_path.write_text(content)
            print(f"✅ Created: {index_path}")

        # Create conf.yaml
        if not self.conf_path.exists():
            conf = {
                "site_name": self.project_dir.name,
                "nav": [
                    {"Home": "index.html"},
                    {"Dashboard": "dashboard.html"},
                    {"ADRs": "adrs.html"},
                ]
            }
            with open(self.conf_path, "w") as f:
                yaml.dump(conf, f, sort_keys=False)
            print(f"✅ Created: {self.conf_path}")

        return True

    def build(self) -> bool:
        """Builds the static documentation site."""
        print(f"--- Building Documentation for {self.project_dir.name} ---")

        # Load config
        config = {}
        if self.conf_path.exists():
            with open(self.conf_path, "r") as f:
                config = yaml.safe_load(f) or {}

        site_name = config.get("site_name", self.project_dir.name)
        nav = config.get("nav", [])

        # Prepare site directory
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)
        self.site_dir.mkdir()

        # 1. Convert docs/*.md
        md = markdown.Markdown(extensions=['fenced_code', 'tables', 'toc'])

        # Collect all markdown files to process
        files_to_process = []

        # Docs folder
        if self.docs_dir.exists():
            for md_file in self.docs_dir.glob("*.md"):
                files_to_process.append((md_file, md_file.name.replace(".md", ".html")))

        # Root files (README, CHANGELOG)
        for root_file in ["README.md", "CHANGELOG.md", "SECURITY.md"]:
            path = self.project_dir / root_file
            if path.exists():
                files_to_process.append((path, root_file.lower().replace(".md", ".html")))

        # Process Markdown files
        for src_path, dest_name in files_to_process:
            self._render_page(src_path, dest_name, site_name, nav, md)

        # 2. Generate Dashboard
        self._generate_dashboard(site_name, nav)

        # 3. Generate ADR Index
        self._generate_adr_index(site_name, nav)

        # 4. Copy static assets if any (images)
        # For now, just simplistic copy of images in docs
        if self.docs_dir.exists():
            for img in self.docs_dir.glob("*.png"):
                shutil.copy(img, self.site_dir / img.name)
            for img in self.docs_dir.glob("*.jpg"):
                shutil.copy(img, self.site_dir / img.name)

        print(f"✅ Documentation built in: {self.site_dir}")
        return True

    def _render_page(self, src_path: Path, dest_name: str, site_name: str, nav: List[Dict], md: markdown.Markdown):
        """Renders a single markdown file to HTML."""
        try:
            text = src_path.read_text(encoding="utf-8")
            html_content = md.convert(text)
            page_title = dest_name.replace(".html", "").replace("-", " ").title()

            # Simple template
            full_html = self._get_template(site_name, page_title, nav, html_content)

            (self.site_dir / dest_name).write_text(full_html, encoding="utf-8")
            print(f"  - Rendered {dest_name}")
        except Exception as e:
            print(f"❌ Error rendering {src_path.name}: {e}", file=sys.stderr)

    def _generate_dashboard(self, site_name: str, nav: List[Dict]):
        """Generates the Health Dashboard."""
        print("  - Generating Dashboard...")

        # Calculate Health
        calc = HealthCalculator(self.project_dir)
        calc.calculate()

        # Generate HTML fragment
        report_file = self.site_dir / "temp_report.html"
        calc.generate_html_report(report_file)

        # Read the generated report
        report_content = report_file.read_text(encoding="utf-8")

        # Extract body content (simplistic approach)
        start_body = report_content.find("<body>") + 6
        end_body = report_content.find("</body>")
        if start_body > 5 and end_body > start_body:
            inner_content = report_content[start_body:end_body]
            # Strip the container div from the report to fit our layout better if needed,
            # or just inject styles.
            # The report has its own styles in <head>. We should extract styles too.
            start_style = report_content.find("<style>")
            end_style = report_content.find("</style>") + 8
            styles = report_content[start_style:end_style] if start_style > 0 else ""

            final_content = f"{styles}\n{inner_content}"
        else:
            final_content = report_content

        # Clean up temp file
        report_file.unlink()

        full_html = self._get_template(site_name, "Dashboard", nav, final_content)
        (self.site_dir / "dashboard.html").write_text(full_html, encoding="utf-8")

    def _generate_adr_index(self, site_name: str, nav: List[Dict]):
        """Generates the ADR index page."""
        print("  - Generating ADR Index...")
        adr_dir = self.project_dir / "docs/adr"
        if not adr_dir.exists():
            content = "<p>No ADR directory found (docs/adr).</p>"
        else:
            adrs = sorted(list(adr_dir.glob("*.md")))
            if not adrs:
                content = "<p>No ADRs found.</p>"
            else:
                list_items = ""
                md = markdown.Markdown()
                for adr in adrs:
                    # Parse title from first line
                    text = adr.read_text(encoding="utf-8")
                    title = adr.name
                    lines = text.splitlines()
                    for line in lines:
                        if line.startswith("# "):
                            title = line[2:].strip()
                            break

                    # Render ADR to its own file
                    dest_name = f"adr-{adr.name.replace('.md', '.html')}"
                    self._render_page(adr, dest_name, site_name, nav, md)

                    list_items += f"<li><a href='{dest_name}'>{title}</a> <span style='color:#666'>({adr.name})</span></li>"

                content = f"<h1>Architecture Decision Records</h1><ul>{list_items}</ul>"

        full_html = self._get_template(site_name, "ADRs", nav, content)
        (self.site_dir / "adrs.html").write_text(full_html, encoding="utf-8")

    def _get_template(self, site_name: str, page_title: str, nav: List[Dict], content: str) -> str:
        """Returns the HTML template with content injected."""

        nav_html = ""
        for item in nav:
            for label, link in item.items():
                active = 'class="active"' if page_title.lower() in label.lower() or (label == "Home" and page_title == "Index") else ''
                nav_html += f'<a href="{link}" {active}>{label}</a>'

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title} - {site_name}</title>
    <style>
        :root {{
            --bg-color: #0d1117;
            --text-color: #c9d1d9;
            --link-color: #58a6ff;
            --border-color: #30363d;
            --header-bg: #161b22;
            --sidebar-bg: #0d1117;
            --code-bg: #161b22;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            display: flex;
            min-height: 100vh;
        }}
        .sidebar {{
            width: 250px;
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            padding: 20px;
            flex-shrink: 0;
        }}
        .sidebar h2 {{
            margin-top: 0;
            color: var(--text-color);
        }}
        .nav-links {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .nav-links a {{
            color: var(--text-color);
            text-decoration: none;
            padding: 8px 12px;
            border-radius: 6px;
            transition: background 0.2s;
        }}
        .nav-links a:hover {{
            background-color: var(--border-color);
        }}
        .nav-links a.active {{
            background-color: #1f6feb;
            color: #fff;
        }}
        .main-content {{
            flex-grow: 1;
            padding: 40px;
            max-width: 900px;
            line-height: 1.6;
        }}
        h1, h2, h3, h4 {{ border-bottom: 1px solid var(--border-color); padding-bottom: 0.3em; }}
        a {{ color: var(--link-color); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        code {{ background-color: var(--code-bg); padding: 0.2em 0.4em; border-radius: 3px; font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace; }}
        pre {{ background-color: var(--code-bg); padding: 16px; border-radius: 6px; overflow: auto; }}
        pre code {{ background-color: transparent; padding: 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid var(--border-color); padding: 8px; text-align: left; }}
        th {{ background-color: var(--header-bg); }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>{site_name}</h2>
        <div class="nav-links">
            {nav_html}
        </div>
        <div style="margin-top: 20px; font-size: 0.8em; color: #8b949e;">
            Generated {datetime.now().strftime('%Y-%m-%d')}
        </div>
    </div>
    <div class="main-content">
        {content}
    </div>
</body>
</html>
"""

    def serve(self, port: int = 8000):
        """Serves the documentation site."""
        if not self.site_dir.exists():
            print("❌ Site directory not found. Run 'build' first.")
            return

        os.chdir(self.site_dir)

        Handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"✅ Serving docs at http://localhost:{port}")
            print("Press Ctrl+C to stop.")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nStopping server.")
