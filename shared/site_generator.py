import os
import shutil
import markdown
import json
import html
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from shared.health import HealthCalculator
from shared.dependencies import DependencyAnalyzer

DEFAULT_CSS = """
:root {
    --primary: #2563eb;
    --primary-hover: #1d4ed8;
    --bg: #ffffff;
    --text: #1f2937;
    --sidebar-bg: #f3f4f6;
    --border: #e5e7eb;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    margin: 0;
    padding: 0;
    display: flex;
    min-height: 100vh;
    color: var(--text);
    background: var(--bg);
}

.sidebar {
    width: 250px;
    background: var(--sidebar-bg);
    border-right: 1px solid var(--border);
    padding: 20px;
    display: flex;
    flex-direction: column;
    position: fixed;
    height: 100%;
    overflow-y: auto;
}

.sidebar h3 {
    margin-top: 0;
    margin-bottom: 20px;
    font-size: 1.2rem;
    color: var(--primary);
}

.nav-links {
    list-style: none;
    padding: 0;
    margin: 0;
}

.nav-links li {
    margin-bottom: 10px;
}

.nav-links a {
    text-decoration: none;
    color: var(--text);
    display: block;
    padding: 8px 12px;
    border-radius: 6px;
    transition: background 0.2s;
}

.nav-links a:hover, .nav-links a.active {
    background: #e5e7eb;
    color: var(--primary);
}

.content {
    flex: 1;
    margin-left: 250px; /* Width of sidebar */
    padding: 40px;
    max-width: 900px;
}

.content h1 {
    border-bottom: 2px solid var(--border);
    padding-bottom: 10px;
    margin-top: 0;
}

.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.card {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.card h3 {
    margin-top: 0;
    color: var(--primary);
}

.metric-value {
    font-size: 2rem;
    font-weight: bold;
}

code {
    background: #f3f4f6;
    padding: 2px 4px;
    border-radius: 4px;
    font-family: monospace;
}

pre {
    background: #1f2937;
    color: #f3f4f6;
    padding: 15px;
    border-radius: 8px;
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}

th, td {
    padding: 10px;
    border-bottom: 1px solid var(--border);
    text-align: left;
}

th {
    background: #f9fafb;
    font-weight: 600;
}

.badge {
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: bold;
    color: #fff;
}

.badge.pass { background: #10b981; }
.badge.fail { background: #ef4444; }
.badge.warn { background: #f59e0b; }

@media (max-width: 768px) {
    .sidebar {
        display: none; /* Simple mobile hide for now */
    }
    .content {
        margin-left: 0;
        padding: 20px;
    }
}
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {css}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</head>
<body>
    <nav class="sidebar">
        <h3>{project_name}</h3>
        <ul class="nav-links">
            {nav_links}
        </ul>
    </nav>
    <main class="content">
        {content}
    </main>
</body>
</html>
"""

class SiteGenerator:
    def __init__(self, project_dir: Path, output_dir: Path):
        self.project_dir = project_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.pages = []  # List of dicts {title, path, content}

    def build(self):
        """Orchestrates the site generation."""
        print(f"Building site for {self.project_dir.name}...")

        # 1. Clean/Create output dir
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True)

        # 2. Discover Content
        self.pages = self._discover_pages()

        # 3. Add Special Pages
        self.pages.insert(0, self._build_dashboard_page())
        self.pages.append(self._build_dependencies_page())

        # 4. Generate Nav HTML
        nav_html = self._generate_nav_html()

        # 5. Render Pages
        for page in self.pages:
            self._render_page(page, nav_html)

        print(f"✅ Site generated at: {self.output_dir}")

    def _discover_pages(self) -> List[Dict[str, Any]]:
        """Scans for markdown files."""
        pages = []

        # Check for README
        readme_path = self.project_dir / "README.md"
        if readme_path.exists():
            pages.append({
                "title": "Introduction",
                "filename": "index.html", # Overrides dashboard? No, let's make dashboard 'dashboard.html'
                "content_source": readme_path,
                "is_markdown": True
            })

        # Scan docs/ folder
        docs_dir = self.project_dir / "docs"
        if docs_dir.exists():
            for md_file in docs_dir.rglob("*.md"):
                rel_path = md_file.relative_to(docs_dir)
                # Create a flat list for now, simpler
                title = md_file.stem.replace("-", " ").title()
                filename = f"docs_{rel_path.with_suffix('.html').name}"
                pages.append({
                    "title": title,
                    "filename": filename,
                    "content_source": md_file,
                    "is_markdown": True
                })

        return pages

    def _build_dashboard_page(self) -> Dict[str, Any]:
        """Generates the Dashboard page using HealthCalculator."""
        calc = HealthCalculator(self.project_dir)
        calc.calculate()

        # Build HTML content for dashboard
        grade_color = "pass" if calc.grade in ["A", "B"] else "warn" if calc.grade == "C" else "fail"

        html_content = f"""
        <h1>Project Dashboard</h1>

        <div class="card-grid">
            <div class="card">
                <h3>Overall Grade</h3>
                <div class="metric-value badge {grade_color}" style="font-size: 3rem; text-align: center;">{calc.grade}</div>
                <div style="text-align: center; margin-top: 10px;">Score: {calc.score:.0f}/100</div>
            </div>

            <div class="card">
                <h3>Tests</h3>
                <div class="metric-value">{calc.metrics['test_score']}/30</div>
            </div>

            <div class="card">
                <h3>Linting</h3>
                <div class="metric-value">{calc.metrics['lint_score']}/20</div>
            </div>

            <div class="card">
                <h3>Complexity</h3>
                <div class="metric-value">{calc.metrics['complexity_score']}/20</div>
            </div>
             <div class="card">
                <h3>Security</h3>
                <div class="metric-value">{calc.metrics['security_score']}/20</div>
            </div>
        </div>

        <h2>Issues</h2>
        """

        if calc.issues:
            html_content += "<ul>"
            for issue in calc.issues:
                html_content += f"<li>{html.escape(issue)}</li>"
            html_content += "</ul>"
        else:
            html_content += "<p>✅ No significant issues found.</p>"

        # Security Table
        findings = calc.metrics.get("security_data", {}).get("findings", [])
        if findings:
            html_content += "<h2>Security Findings</h2><table><thead><tr><th>Severity</th><th>Description</th><th>Location</th></tr></thead><tbody>"
            for f in findings:
                 sev = f.get("severity", "UNKNOWN")
                 cls = "fail" if sev == "HIGH" else "warn" if sev == "MEDIUM" else "pass"
                 html_content += f"<tr><td><span class='badge {cls}'>{sev}</span></td><td>{html.escape(f.get('description',''))}</td><td>{f.get('file')}:{f.get('line')}</td></tr>"
            html_content += "</tbody></table>"

        return {
            "title": "Dashboard",
            "filename": "dashboard.html",
            "content_html": html_content,
            "is_markdown": False
        }

    def _build_dependencies_page(self) -> Dict[str, Any]:
        """Generates the Dependencies page."""
        analyzer = DependencyAnalyzer(self.project_dir)
        data = analyzer.scan()
        mermaid_graph = analyzer.generate_mermaid(data)

        html_content = f"""
        <h1>Dependencies</h1>
        <p>Visualizing project dependencies.</p>

        <div class="mermaid">
        {mermaid_graph}
        </div>

        <h2>List</h2>
        """

        for lang, files in data.items():
            if files:
                html_content += f"<h3>{lang.capitalize()}</h3><ul>"
                for f in files:
                    for dep in f["dependencies"]:
                        html_content += f"<li><strong>{dep['name']}</strong> ({dep.get('version', '')})</li>"
                html_content += "</ul>"

        return {
            "title": "Dependencies",
            "filename": "dependencies.html",
            "content_html": html_content,
            "is_markdown": False
        }

    def _generate_nav_html(self) -> str:
        """Generates the navigation list HTML."""
        links = []
        for page in self.pages:
            links.append(f'<li><a href="{page["filename"]}">{page["title"]}</a></li>')
        return "\n".join(links)

    def _render_page(self, page: Dict[str, Any], nav_html: str):
        """Renders a single page."""

        # Get Content
        content = ""
        if page.get("is_markdown") and "content_source" in page:
             try:
                 md_text = page["content_source"].read_text(encoding="utf-8", errors="replace")
                 # Convert MD to HTML
                 content = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
             except Exception as e:
                 content = f"<p>Error reading file: {e}</p>"
        else:
            content = page.get("content_html", "")

        # Highlight active link
        current_nav = nav_html.replace(f'href="{page["filename"]}"', f'href="{page["filename"]}" class="active"')

        # Fill Template
        full_html = TEMPLATE.format(
            title=f"{page['title']} - {self.project_dir.name}",
            project_name=self.project_dir.name,
            css=DEFAULT_CSS,
            nav_links=current_nav,
            content=content
        )

        # Write File
        out_path = self.output_dir / page["filename"]
        out_path.write_text(full_html, encoding="utf-8")

def run_site(args):
    """Entry point for site command."""
    out_dir = Path(args.output) if args.output else args.project_dir / "_site"
    generator = SiteGenerator(args.project_dir, out_dir)
    generator.build()
