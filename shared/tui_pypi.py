import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog
from textual.message import Message

from shared.pypi_lab import PyPiLabManager


class PypiLabTab(Container):
    """Tab for PyPI Lab Operations (Info, Releases, Dependencies, Files)."""

    def __init__(self):
        super().__init__()
        self.pypi_manager = PyPiLabManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="pypi-lab-container", classes="lab-container"):
            yield Label("[bold]PyPI Lab[/bold]", classes="welcome-text")
            yield Label("Search and inspect packages from the Python Package Index.")

            with Horizontal(id="pypi-input-row", classes="input-row"):
                yield Input(placeholder="Enter package name (e.g., requests)", id="pypi-package-input")
                yield Input(placeholder="Version (optional, e.g., 2.31.0)", id="pypi-version-input")

            with Horizontal(id="pypi-buttons-row", classes="button-row"):
                yield Button("Get Info", id="btn-pypi-info", variant="primary")
                yield Button("List Releases", id="btn-pypi-releases", variant="success")
                yield Button("Get Dependencies", id="btn-pypi-deps", variant="warning")
                yield Button("List Files", id="btn-pypi-files", variant="default")

            yield Label("Output:")
            yield RichLog(id="pypi-log", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-pypi-info":
            await self.run_info()
        elif event.button.id == "btn-pypi-releases":
            await self.run_releases()
        elif event.button.id == "btn-pypi-deps":
            await self.run_deps()
        elif event.button.id == "btn-pypi-files":
            await self.run_files()

    async def run_info(self) -> None:
        package = self.query_one("#pypi-package-input", Input).value
        log = self.query_one("#pypi-log", RichLog)

        if not package:
            log.write("[red]Please enter a package name.[/red]")
            return

        log.write(f"\n[bold cyan]Fetching info for '{package}'...[/bold cyan]")
        try:
            info = await asyncio.to_thread(self.pypi_manager.get_info, package)
            log.write(f"[bold]Name:[/bold] {info.get('name')}")
            log.write(f"[bold]Version:[/bold] {info.get('version')}")
            log.write(f"[bold]Summary:[/bold] {info.get('summary')}")
            log.write(f"[bold]Author:[/bold] {info.get('author')}")
            log.write(f"[bold]License:[/bold] {info.get('license')}")
            log.write(f"[bold]Home:[/bold] {info.get('home_page')}")
            log.write(f"[bold]PyPI URL:[/bold] {info.get('package_url')}")
            if info.get('project_urls'):
                log.write("[bold]Links:[/bold]")
                for k, v in info['project_urls'].items():
                    log.write(f"  {k}: {v}")
        except ValueError as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            if hasattr(self.app, "notify"):
                self.app.notify(str(e), severity="error")
        except Exception as e:
            log.write(f"[bold red]An unexpected error occurred:[/bold red] {e}")
            if hasattr(self.app, "notify"):
                self.app.notify("Failed to fetch info.", severity="error")

    async def run_releases(self) -> None:
        package = self.query_one("#pypi-package-input", Input).value
        log = self.query_one("#pypi-log", RichLog)

        if not package:
            log.write("[red]Please enter a package name.[/red]")
            return

        log.write(f"\n[bold cyan]Fetching releases for '{package}'...[/bold cyan]")
        try:
            releases = await asyncio.to_thread(self.pypi_manager.get_releases, package)
            if not releases:
                log.write("No releases found.")
                return

            sorted_versions = []
            for ver, files in releases.items():
                date = "Unknown"
                if files:
                    date = files[0].get("upload_time", "Unknown")[:10]
                sorted_versions.append((ver, date))

            sorted_versions.sort(key=lambda x: x[1], reverse=True)

            log.write(f"[bold]Releases ({len(sorted_versions)}):[/bold]")
            for ver, date in sorted_versions:
                log.write(f"  {date} : {ver}")
        except ValueError as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            if hasattr(self.app, "notify"):
                self.app.notify(str(e), severity="error")
        except Exception as e:
            log.write(f"[bold red]An unexpected error occurred:[/bold red] {e}")
            if hasattr(self.app, "notify"):
                self.app.notify("Failed to fetch releases.", severity="error")

    async def run_deps(self) -> None:
        package = self.query_one("#pypi-package-input", Input).value
        version = self.query_one("#pypi-version-input", Input).value
        log = self.query_one("#pypi-log", RichLog)

        if not package:
            log.write("[red]Please enter a package name.[/red]")
            return

        version_str = version if version else "latest"
        log.write(f"\n[bold cyan]Fetching dependencies for '{package}' ({version_str})...[/bold cyan]")
        try:
            deps = await asyncio.to_thread(self.pypi_manager.get_dependencies, package, version if version else None)
            if not deps:
                log.write("No dependencies listed (or requires_dist is empty).")
                return

            log.write(f"[bold]Dependencies ({len(deps)}):[/bold]")
            for d in deps:
                log.write(f"  - {d}")
        except ValueError as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            if hasattr(self.app, "notify"):
                self.app.notify(str(e), severity="error")
        except Exception as e:
            log.write(f"[bold red]An unexpected error occurred:[/bold red] {e}")
            if hasattr(self.app, "notify"):
                self.app.notify("Failed to fetch dependencies.", severity="error")

    async def run_files(self) -> None:
        package = self.query_one("#pypi-package-input", Input).value
        version = self.query_one("#pypi-version-input", Input).value
        log = self.query_one("#pypi-log", RichLog)

        if not package:
            log.write("[red]Please enter a package name.[/red]")
            return

        version_str = version if version else "latest"
        log.write(f"\n[bold cyan]Fetching files for '{package}' ({version_str})...[/bold cyan]")
        try:
            files = await asyncio.to_thread(self.pypi_manager.get_files, package, version if version else None)
            if not files:
                log.write("No files found.")
                return

            log.write(f"[bold]Files ({len(files)}):[/bold]")
            for f in files:
                size_mb = f.get('size', 0) / 1024 / 1024
                log.write(f"  - {f.get('filename')} ({f.get('packagetype')}) - {size_mb:.2f} MB")
                log.write(f"    URL: {f.get('url')}")
                log.write(f"    SHA256: {f.get('digests', {}).get('sha256')}")
        except ValueError as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            if hasattr(self.app, "notify"):
                self.app.notify(str(e), severity="error")
        except Exception as e:
            log.write(f"[bold red]An unexpected error occurred:[/bold red] {e}")
            if hasattr(self.app, "notify"):
                self.app.notify("Failed to fetch files.", severity="error")
