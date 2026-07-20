from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, Label, Markdown
from textual.widgets import TabPane
from shared.osv_lab import OsvLabManager


class OsvLabTab(TabPane):
    """TUI Tab for OSV Lab."""

    def __init__(self):
        super().__init__("OSV Lab", id="tab-osv-lab")
        self.manager = OsvLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Open Source Vulnerability (OSV) Query", classes="header")

            with Horizontal(classes="input-row"):
                yield Input(id="osv-pkg", placeholder="Package (e.g. jinja2)")
                yield Input(id="osv-ecosystem", placeholder="Ecosystem (e.g. PyPI)")
                yield Input(id="osv-version", placeholder="Version (Optional)")

            yield Button("Query OSV", id="osv-btn", variant="primary")
            yield Markdown(id="osv-results")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "osv-btn":
            pkg = self.query_one("#osv-pkg", Input).value.strip()
            eco = self.query_one("#osv-ecosystem", Input).value.strip()
            ver = self.query_one("#osv-version", Input).value.strip()

            results = self.query_one("#osv-results", Markdown)

            if not pkg or not eco:
                await results.update("**Error:** Package and Ecosystem are required.")
                return

            await results.update(f"Querying OSV for {pkg} ({eco})...")

            try:
                # We do this synchronously in the handler for simplicity,
                # but ideally it should use a worker.
                res = self.manager.query_package(pkg, eco, ver if ver else None)

                if "error" in res:
                    await results.update(f"**Error querying OSV API:** {res['error']}")
                    return

                vulns = res.get("vulns", [])

                if not vulns:
                    msg = f"✅ No known vulnerabilities found for {pkg} ({eco})"
                    if ver:
                        msg += f" version {ver}."
                    else:
                        msg += "."
                    await results.update(msg)
                    return

                md_content = f"⚠️ **Found {len(vulns)} vulnerabilities for {pkg} ({eco})**\n\n"

                for vuln in vulns:
                    md_content += f"```text\n{self.manager.format_vulnerability(vuln)}\n```\n\n"

                await results.update(md_content)

            except Exception as e:
                await results.update(f"**Exception:** {e}")
