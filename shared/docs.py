import subprocess # nosec
from pathlib import Path
import sys

class DocsManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def init_site(self, site_name: str = "Documentation", theme: str = "readthedocs") -> bool:
        """Initializes a new MkDocs site."""
        try:
            # Create mkdocs.yml
            config_path = self.project_dir / "mkdocs.yml"
            if config_path.exists():
                print(f"Error: {config_path} already exists.", file=sys.stderr)
                return False

            content = f"""site_name: {site_name}
theme: {theme}
nav:
  - Home: index.md
"""
            config_path.write_text(content)

            # Create docs directory and index.md
            docs_dir = self.project_dir / "docs"
            docs_dir.mkdir(exist_ok=True)

            index_path = docs_dir / "index.md"
            if not index_path.exists():
                index_path.write_text(f"# {site_name}\n\nWelcome to the documentation for {site_name}.")

            return True
        except Exception as e:
            print(f"Error initializing site: {e}", file=sys.stderr)
            return False

    def build_site(self) -> bool:
        """Builds the static site."""
        try:
            subprocess.run(["mkdocs", "build"], cwd=self.project_dir, check=True) # nosec
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error building site: {e}", file=sys.stderr)
            return False
        except FileNotFoundError:
            print("Error: 'mkdocs' command not found. Please install it with 'pip install mkdocs'.", file=sys.stderr)
            return False

    def serve_site(self, port: int = 8000, host: str = "127.0.0.1") -> None:
        """Serves the site locally."""
        try:
            print(f"Serving documentation on http://{host}:{port}")
            subprocess.run(["mkdocs", "serve", "--dev-addr", f"{host}:{port}"], cwd=self.project_dir, check=True) # nosec
        except subprocess.CalledProcessError as e:
            print(f"Error serving site: {e}", file=sys.stderr)
        except FileNotFoundError:
            print("Error: 'mkdocs' command not found. Please install it with 'pip install mkdocs'.", file=sys.stderr)
        except KeyboardInterrupt:
            print("\nStopped serving.")
