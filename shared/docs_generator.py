import os
import shutil
import ast
import re
import http.server
import socketserver
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DocsGenerator:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.docs_dir = self.project_dir / "docs"
        self.site_dir = self.project_dir / "site"
        self.api_dir = self.site_dir / "api"
        self.conf_file = self.docs_dir / "conf.yaml"

    def init_docs(self):
        """Initializes the docs structure."""
        if not self.docs_dir.exists():
            self.docs_dir.mkdir(parents=True)
            print(f"Created directory: {self.docs_dir}")

        index_md = self.docs_dir / "index.md"
        if not index_md.exists():
            content = """# Project Documentation

Welcome to the documentation for your project!

## Overview

This project is... (add description here)

## Getting Started

1. Install dependencies
2. Run the application
"""
            index_md.write_text(content)
            print(f"Created file: {index_md}")

        if not self.conf_file.exists():
            content = """site_name: My Project
theme_color: #3498db
"""
            self.conf_file.write_text(content)
            print(f"Created file: {self.conf_file}")

        print("✅ Documentation initialized. Run 'docs build' to generate the site.")

    def build_site(self):
        """Builds the static site."""
        if not self.docs_dir.exists():
            print("Error: 'docs' directory not found. Run 'docs init' first.")
            return False

        # Clean site dir
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)
        self.site_dir.mkdir()
        self.api_dir.mkdir()

        # 1. Convert Markdown to HTML
        for md_file in self.docs_dir.glob("*.md"):
            html_content = self._convert_markdown(md_file.read_text())
            output_file = self.site_dir / md_file.with_suffix(".html").name
            self._write_html_page(output_file, md_file.stem.capitalize(), html_content)
            print(f"Generated: {output_file.relative_to(self.project_dir)}")

        # 2. Generate API Docs
        self._generate_api_docs()

        print("✅ Site built successfully.")
        return True

    def serve_site(self, port: int = 8000):
        """Serves the static site."""
        if not self.site_dir.exists():
            print("Error: 'site' directory not found. Run 'docs build' first.")
            return

        os.chdir(self.site_dir)

        # Allow reusing address
        socketserver.TCPServer.allow_reuse_address = True

        with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"Serving at http://localhost:{port}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nServer stopped.")

    def _convert_markdown(self, text: str) -> str:
        """Converts basic Markdown to HTML using regex."""
        # Headers
        text = re.sub(r'^# (.*$)', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*$)', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.*$)', r'<h3>\1</h3>', text, flags=re.MULTILINE)

        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

        # Italic
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)

        # Code blocks (basic)
        text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', text, flags=re.DOTALL)

        # Inline code
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)

        # Lists (unordered)
        lines = text.split('\n')
        in_list = False
        new_lines = []
        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    new_lines.append('<ul>')
                    in_list = True
                new_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list:
                    new_lines.append('</ul>')
                    in_list = False
                new_lines.append(line)
        if in_list:
             new_lines.append('</ul>')

        text = '\n'.join(new_lines)

        # Simple paragraph wrapper
        final_lines = []
        for line in text.split('\n'):
            if line.strip() and not line.strip().startswith('<'):
                final_lines.append(f'<p>{line}</p>')
            else:
                final_lines.append(line)

        return '\n'.join(final_lines)

    def _generate_api_docs(self):
        """Scans Python files and generates API documentation."""
        api_index_content = "<h1>API Reference</h1><ul>"

        # Ignored directories
        ignored = {'.git', '.venv', 'venv', '__pycache__', 'site', 'docs', 'tests'}

        seen_files = set()

        for root, dirs, files in os.walk(self.project_dir):
            # Filter ignored dirs in place
            dirs[:] = [d for d in dirs if d not in ignored]

            for file in files:
                if not file.endswith(".py") or file == "__init__.py":
                    continue

                file_path = Path(root) / file

                try:
                    rel_path = file_path.relative_to(self.project_dir)
                except ValueError:
                    continue

                if rel_path in seen_files:
                    continue
                seen_files.add(rel_path)

                doc_info = self._extract_docstrings(file_path)
                if doc_info:
                    # Generate unique filename: shared/utils.py -> shared_utils.html
                    safe_name = str(rel_path.with_suffix('')).replace(os.sep, '_') + ".html"
                    html_file = self.api_dir / safe_name

                    self._write_api_page(html_file, str(rel_path), doc_info)
                    api_index_content += f'<li><a href="api/{html_file.name}">{rel_path}</a></li>'

        api_index_content += "</ul>"

        # Write API Index
        self._write_html_page(self.site_dir / "api.html", "API Reference", api_index_content)

    def _extract_docstrings(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extracts docstrings from classes and functions."""
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except Exception:
            return []

        items = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node)
                if doc:
                    items.append({
                        "name": node.name,
                        "type": type(node).__name__,
                        "doc": doc,
                        "lineno": node.lineno
                    })
        return items

    def _write_html_page(self, output_file: Path, title: str, content: str):
        """Writes a full HTML page with layout."""
        # Simple CSS
        css = """
        body { font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; margin: 0; padding: 0; color: #333; }
        header { background: #2c3e50; color: white; padding: 1rem 2rem; }
        header a { color: white; text-decoration: none; margin-right: 1rem; }
        .container { max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        h1, h2, h3 { color: #2c3e50; }
        pre { background: #f4f4f4; padding: 1rem; overflow-x: auto; border-radius: 4px; }
        code { font-family: monospace; background: #eee; padding: 0.2rem 0.4rem; border-radius: 3px; }
        .api-item { border-bottom: 1px solid #eee; padding-bottom: 1rem; margin-bottom: 1rem; }
        .api-type { font-size: 0.8rem; text-transform: uppercase; color: #7f8c8d; font-weight: bold; }
        .api-name { font-size: 1.2rem; font-weight: bold; color: #2980b9; }
        """

        # Navigation
        nav = """
        <nav>
            <a href="index.html">Home</a>
            <a href="api.html">API Reference</a>
        </nav>
        """

        # Correct links for API subpages
        if output_file.parent.name == "api":
             nav = """
            <nav>
                <a href="../index.html">Home</a>
                <a href="../api.html">API Reference</a>
            </nav>
            """

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Documentation</title>
    <style>{css}</style>
</head>
<body>
    <header>
        {nav}
    </header>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""
        output_file.write_text(full_html, encoding="utf-8")

    def _write_api_page(self, output_file: Path, source_file: str, items: List[Dict[str, Any]]):
        """Generates an HTML page for API docs of a single file."""
        content = f"<h1>API: {source_file}</h1>"

        for item in items:
            doc_html = item['doc'].replace('\n', '<br>')
            content += f"""
            <div class="api-item">
                <div class="api-type">{item['type'].replace('Def', '')}</div>
                <div class="api-name">{item['name']}</div>
                <div class="api-doc">{doc_html}</div>
            </div>
            """

        self._write_html_page(output_file, f"API - {source_file}", content)
