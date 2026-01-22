import os
import shutil
import markdown  # type: ignore
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from shared.health import HealthCalculator
from shared.dependencies import DependencyAnalyzer

class SiteGenerator:
    """
    Generates a static HTML documentation website for the project.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.output_dir = self.project_dir / "site"
        self.pages: List[Dict[str, str]] = []

    def generate(self, output_dir: Optional[Path] = None):
        """Builds the static site."""
        if output_dir:
            self.output_dir = output_dir

        # Safety Check: Prevent deleting project root
        if self.output_dir.resolve() == self.project_dir.resolve():
            print(f"❌ Error: Output directory cannot be the project root.")
            return
        if self.output_dir.resolve() == Path(".").resolve():
            print(f"❌ Error: Output directory cannot be the current working directory.")
            return

        print(f"--- Generating Documentation Site in: {self.output_dir} ---")

        # Clean and Create Output Directory
        if self.output_dir.exists():
            # Safety Check: Only delete if it looks like a site directory we created (marker file)
            # or if it is empty.
            is_empty = not any(self.output_dir.iterdir())
            marker_file = self.output_dir / ".agent_site_root"

            if is_empty:
                pass # Safe to use
            elif marker_file.exists():
                # Safe to clean
                shutil.rmtree(self.output_dir)
                self.output_dir.mkdir(parents=True, exist_ok=True)
            else:
                print(f"❌ Error: Output directory '{self.output_dir}' is not empty and does not appear to be a generated site.")
                print("   Please use an empty directory or manually delete the existing one.")
                return
        else:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create marker file for future safety
        (self.output_dir / ".agent_site_root").touch()
        (self.output_dir / "css").mkdir(exist_ok=True)

        # 1. Generate Styles
        self._generate_css()

        # 2. Discover Markdown Files (Docs)
        self._scan_docs()

        # 3. Generate Dashboard Pages
        self._generate_dashboard_pages()

        # 4. Render All Pages
        for page in self.pages:
            self._render_page(page)

        print(f"✅ Site generated successfully at {self.output_dir}")
        print(f"   Run 'python3 main.py site serve' to preview.")

    def serve(self, port: int = 8000):
        """Serves the generated site locally."""
        if not self.output_dir.exists():
            print(f"❌ Site directory {self.output_dir} does not exist. Run 'generate' first.")
            return

        import http.server
        import socketserver

        os.chdir(self.output_dir)

        Handler = http.server.SimpleHTTPRequestHandler
        try:
            with socketserver.TCPServer(("", port), Handler) as httpd:
                print(f"🌍 Serving documentation at http://localhost:{port}")
                print("Press Ctrl+C to stop.")
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped server.")

    def _generate_css(self):
        """Creates the CSS file."""
        css_content = """
        :root {
            --primary-color: #3498db;
            --sidebar-bg: #2c3e50;
            --sidebar-text: #ecf0f1;
            --text-color: #333;
            --bg-color: #f9f9f9;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            display: flex;
            min-height: 100vh;
            color: var(--text-color);
            background: var(--bg-color);
        }
        .sidebar {
            width: 250px;
            background: var(--sidebar-bg);
            color: var(--sidebar-text);
            padding: 20px;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
        }
        .sidebar h2 {
            margin-top: 0;
            font-size: 1.2rem;
            border-bottom: 1px solid #34495e;
            padding-bottom: 10px;
        }
        .nav-link {
            display: block;
            color: #bdc3c7;
            text-decoration: none;
            padding: 8px 0;
            transition: color 0.2s;
        }
        .nav-link:hover, .nav-link.active {
            color: #fff;
            font-weight: bold;
        }
        .content {
            flex-grow: 1;
            padding: 40px;
            max-width: 900px;
            overflow-y: auto;
            background: #fff;
            box-shadow: 0 0 10px rgba(0,0,0,0.05);
        }
        h1, h2, h3 { color: #2c3e50; }
        code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px; font-family: monospace; }
        pre { background: #f0f0f0; padding: 15px; border-radius: 5px; overflow-x: auto; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f2f2f2; }
        .card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px; }
        .card { background: #fff; border: 1px solid #eee; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .card h3 { margin-top: 0; font-size: 1rem; color: #7f8c8d; }
        .card .value { font-size: 2rem; font-weight: bold; color: #2c3e50; }
        .status-pass { color: #2ecc71; }
        .status-fail { color: #e74c3c; }
        .status-warn { color: #f1c40f; }
        """
        (self.output_dir / "css" / "style.css").write_text(css_content)

    def _scan_docs(self):
        """Scans for markdown files."""
        # Add README
        readme_path = self.project_dir / "README.md"
        if readme_path.exists():
            self.pages.append({
                "title": "Overview",
                "filename": "index.html",
                "content": self._render_markdown(readme_path.read_text(errors="replace")),
                "group": "Documentation"
            })

        # Scan docs/ folder
        docs_dir = self.project_dir / "docs"
        if docs_dir.exists():
            for md_file in docs_dir.glob("*.md"):
                content = self._render_markdown(md_file.read_text(errors="replace"))
                title = md_file.stem.replace("-", " ").title()
                self.pages.append({
                    "title": title,
                    "filename": f"{md_file.stem}.html",
                    "content": content,
                    "group": "Documentation"
                })

    def _render_markdown(self, text: str) -> str:
        """Converts Markdown to HTML."""
        try:
            return markdown.markdown(text, extensions=['tables', 'fenced_code', 'codehilite'])
        except Exception:
            # Fallback if extensions fail
            return markdown.markdown(text)

    def _generate_dashboard_pages(self):
        """Generates dynamic dashboard pages."""

        # 1. Health Report
        calc = HealthCalculator(self.project_dir)
        try:
            calc.calculate()
            health_content = self._build_health_page(calc)
            self.pages.append({
                "title": "Project Health",
                "filename": "health.html",
                "content": health_content,
                "group": "Dashboards"
            })
        except Exception as e:
            print(f"Warning: Could not generate health report: {e}")

        # 2. Dependencies
        try:
            analyzer = DependencyAnalyzer(self.project_dir)
            data = analyzer.scan()
            dep_content = self._build_deps_page(data)
            self.pages.append({
                "title": "Dependencies",
                "filename": "dependencies.html",
                "content": dep_content,
                "group": "Dashboards"
            })
        except Exception as e:
            print(f"Warning: Could not generate dependencies report: {e}")

    def _build_health_page(self, calc: HealthCalculator) -> str:
        """Builds HTML content for the health page."""
        metrics = calc.metrics

        def get_status_class(score, max_score):
            percentage = (score / max_score) * 100
            if percentage >= 90: return "status-pass"
            if percentage >= 70: return "status-warn"
            return "status-fail"

        html_content = f"""
        <h1>Project Health Report</h1>
        <div class="card-grid">
            <div class="card">
                <h3>Overall Grade</h3>
                <div class="value">{calc.grade}</div>
                <div>Score: {calc.score:.0f}/100</div>
            </div>
            <div class="card">
                <h3>Tests</h3>
                <div class="value {get_status_class(metrics.get('test_score',0), 30)}">
                    {metrics.get('test_score', 0)}/30
                </div>
            </div>
            <div class="card">
                <h3>Linting</h3>
                <div class="value {get_status_class(metrics.get('lint_score',0), 20)}">
                    {metrics.get('lint_score', 0)}/20
                </div>
            </div>
             <div class="card">
                <h3>Security</h3>
                <div class="value {get_status_class(metrics.get('security_score',0), 20)}">
                    {metrics.get('security_score', 0)}/20
                </div>
            </div>
        </div>

        <h2>Issues</h2>
        """

        if calc.issues:
            html_content += "<ul>"
            for issue in calc.issues:
                html_content += f"<li>{issue}</li>"
            html_content += "</ul>"
        else:
            html_content += "<p>✅ No significant issues found.</p>"

        return html_content

    def _build_deps_page(self, data: Dict[str, Any]) -> str:
        """Builds HTML content for the dependencies page."""
        html_content = "<h1>Project Dependencies</h1>"

        for lang, files in data.items():
            html_content += f"<h2>{lang.capitalize()}</h2>"
            if not files:
                html_content += "<p>No dependencies found.</p>"
                continue

            for file_info in files:
                html_content += f"<h3>{file_info['source']}</h3>"
                html_content += "<table><thead><tr><th>Name</th><th>Version</th><th>Type</th></tr></thead><tbody>"
                for dep in file_info.get("dependencies", []):
                    html_content += f"<tr><td>{dep['name']}</td><td>{dep.get('version', '')}</td><td>{dep.get('type', 'prod')}</td></tr>"
                html_content += "</tbody></table>"

        return html_content

    def _render_page(self, page_data: Dict[str, str]):
        """Renders the final HTML file with the template."""

        # Build Sidebar
        sidebar_html = f"""
        <div class="sidebar">
            <h2>{self.project_dir.name}</h2>
            <nav>
        """

        # Group pages
        groups: Dict[str, List[Dict[str, str]]] = {}
        for p in self.pages:
            g = p.get("group", "Other")
            if g not in groups: groups[g] = []
            groups[g].append(p)

        for group, pages in groups.items():
            sidebar_html += f"<h3>{group}</h3>"
            for p in pages:
                active = 'active' if p == page_data else ''
                sidebar_html += f'<a href="{p["filename"]}" class="nav-link {active}">{p["title"]}</a>'

        sidebar_html += """
            </nav>
            <div style="margin-top: auto; font-size: 0.8rem; color: #7f8c8d;">
                Generated by AI Agent
            </div>
        </div>
        """

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_data['title']} - {self.project_dir.name}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    {sidebar_html}
    <div class="content">
        {page_data['content']}
    </div>
</body>
</html>
"""

        out_file = self.output_dir / page_data["filename"]
        out_file.write_text(full_html, encoding="utf-8")
