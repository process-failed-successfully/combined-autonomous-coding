from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Select, TabbedContent, TabPane
from textual import on
from shared.semver_lab import SemVer, SemVerLabManager

class SemVerTab(Container):
    """Tab for SemVer Lab."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = SemVerLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]SemVer Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # --- Parse & Bump ---
                with TabPane("Parse & Bump"):
                    with Vertical(classes="stat-box"):
                        yield Label("Input Version:")
                        yield Input(placeholder="e.g. 1.2.3", id="sv-input")

                        yield Label("Actions:")
                        with Horizontal():
                            yield Button("Parse", id="btn-sv-parse", variant="primary")
                            yield Button("Major", id="btn-sv-major", variant="warning")
                            yield Button("Minor", id="btn-sv-minor", variant="warning")
                            yield Button("Patch", id="btn-sv-patch", variant="warning")

                        with Horizontal():
                            yield Button("Pre-release", id="btn-sv-pre", variant="default")
                            yield Input(placeholder="id (alpha)", id="sv-pre-id", classes="small-input")

                    yield Label("[bold]Result[/bold]")
                    yield RichLog(id="sv-log", wrap=True, markup=True)

                # --- Compare ---
                with TabPane("Compare"):
                    with Vertical(classes="stat-box"):
                        with Horizontal():
                            yield Input(placeholder="Version 1", id="sv-v1")
                            yield Select.from_values(["==", "!=", ">", "<", ">=", "<="], id="sv-op", value="==")
                            yield Input(placeholder="Version 2", id="sv-v2")

                        yield Button("Compare", id="btn-sv-compare", variant="primary")

                    yield Label("", id="sv-compare-result", classes="big-result")

                # --- Range (Satisfies) ---
                with TabPane("Range"):
                    with Vertical(classes="stat-box"):
                        yield Label("Version:")
                        yield Input(placeholder="e.g. 1.2.3", id="sv-range-ver")
                        yield Label("Range / Constraint:")
                        yield Input(placeholder="e.g. >=1.0.0", id="sv-range-const")
                        yield Button("Check", id="btn-sv-satisfies", variant="primary")

                    yield Label("", id="sv-range-result", classes="big-result")

    @on(Button.Pressed)
    def on_button_click(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-sv-parse":
            self.do_parse()
        elif event.button.id in ["btn-sv-major", "btn-sv-minor", "btn-sv-patch", "btn-sv-pre"]:
            part = event.button.id.replace("btn-sv-", "")
            if part == "pre": part = "prerelease"
            self.do_bump(part)
        elif event.button.id == "btn-sv-compare":
            self.do_compare()
        elif event.button.id == "btn-sv-satisfies":
            self.do_satisfies()

    def do_parse(self) -> None:
        ver = self.query_one("#sv-input", Input).value
        log = self.query_one("#sv-log", RichLog)
        log.clear()

        result = self.manager.parse(ver)
        if result["valid"]:
            log.write(f"[green]Valid SemVer:[/green] {result['version']}")
            log.write(f"Major: {result['major']}")
            log.write(f"Minor: {result['minor']}")
            log.write(f"Patch: {result['patch']}")
            log.write(f"Pre:   {result['prerelease']}")
            log.write(f"Build: {result['build']}")
        else:
            log.write(f"[red]Invalid:[/red] {result['error']}")

    def do_bump(self, part: str) -> None:
        ver = self.query_one("#sv-input", Input).value
        pre_id = self.query_one("#sv-pre-id", Input).value or "alpha"
        log = self.query_one("#sv-log", RichLog)

        try:
            new_ver = self.manager.bump(ver, part, pre_id)
            # Update input with new version for chaining
            self.query_one("#sv-input", Input).value = new_ver
            log.write(f"[blue]Bumped {part}:[/blue] {ver} -> [bold green]{new_ver}[/bold green]")
        except ValueError as e:
            log.write(f"[red]Error:[/red] {e}")

    def do_compare(self) -> None:
        v1 = self.query_one("#sv-v1", Input).value
        v2 = self.query_one("#sv-v2", Input).value
        op = self.query_one("#sv-op", Select).value
        lbl = self.query_one("#sv-compare-result", Label)

        try:
            res = self.manager.compare(v1, op, v2)
            color = "green" if res else "red"
            text = "TRUE" if res else "FALSE"
            lbl.update(f"Result: [{color}]{text}[/{color}]")
        except ValueError as e:
            lbl.update(f"[red]Error: {e}[/red]")

    def do_satisfies(self) -> None:
        ver = self.query_one("#sv-range-ver", Input).value
        rng = self.query_one("#sv-range-const", Input).value
        lbl = self.query_one("#sv-range-result", Label)

        # Manually calling simple logic since manager.satisfies isn't exposed directly
        # but run_semver_lab_logic has it implemented via parsing.
        # Let's import regex
        import re
        match = re.match(r"^([<>]=?|==?|!=)\s*(.*)$", rng.strip())
        if match:
            op, target = match.groups()
            try:
                res = self.manager.compare(ver, op, target)
                color = "green" if res else "red"
                text = "Satisfied" if res else "Not Satisfied"
                lbl.update(f"[{color}]{text}[/{color}]")
            except ValueError as e:
                lbl.update(f"[red]Error: {e}[/red]")
        else:
            lbl.update("[yellow]Only simple ranges supported (e.g. >=1.0.0)[/yellow]")
