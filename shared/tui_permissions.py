from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Checkbox, Input, Label, Static
from textual import on
from shared.permissions_lab import PermissionsManager


class PermissionsLabTab(Container):
    """Tab for Unix Permissions (Chmod) Calculator."""

    DEFAULT_CSS = """
    PermissionsLabTab {
        layout: vertical;
        height: 100%;
        padding: 1;
    }

    .perm-group {
        border: solid $accent;
        padding: 1;
        margin: 1;
        width: 30%;
    }

    .perm-header {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    .stat-box {
        border: solid $secondary;
        padding: 1;
        margin: 1;
        height: auto;
    }

    #perm-result-container {
        margin-top: 1;
        height: auto;
    }

    .result-label {
        width: 15;
        text-align: right;
        padding-right: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = PermissionsManager()
        self.updating_ui = False  # Flag to prevent event loops

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Permissions Lab (Chmod Calculator)[/bold]", classes="welcome-text")

            # Calculator Section
            with Horizontal(id="perm-calculator"):
                # Owner Group
                with Vertical(classes="perm-group"):
                    yield Label("Owner (u)", classes="perm-header")
                    yield Checkbox("Read (4)", id="chk-u-r", value=True)
                    yield Checkbox("Write (2)", id="chk-u-w", value=True)
                    yield Checkbox("Execute (1)", id="chk-u-x", value=True)

                # Group Group
                with Vertical(classes="perm-group"):
                    yield Label("Group (g)", classes="perm-header")
                    yield Checkbox("Read (4)", id="chk-g-r", value=True)
                    yield Checkbox("Write (2)", id="chk-g-w", value=False)
                    yield Checkbox("Execute (1)", id="chk-g-x", value=True)

                # Other Group
                with Vertical(classes="perm-group"):
                    yield Label("Other (o)", classes="perm-header")
                    yield Checkbox("Read (4)", id="chk-o-r", value=True)
                    yield Checkbox("Write (2)", id="chk-o-w", value=False)
                    yield Checkbox("Execute (1)", id="chk-o-x", value=True)

            # Result/Input Section
            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Octal (e.g. 755):")
                    yield Input(value="755", id="input-perm-octal", max_length=3)

                with Vertical():
                    yield Label("Symbolic (e.g. rwxr-xr-x):")
                    yield Input(value="rwxr-xr-x", id="input-perm-symbolic", max_length=9)

            # File Operations
            with Vertical(classes="stat-box"):
                yield Label("[bold]File Operations[/bold]")
                with Horizontal():
                    yield Label("Path:", classes="result-label")
                    yield Input(placeholder="/path/to/file", id="input-perm-path")

                with Horizontal():
                    yield Button("Load from File", id="btn-perm-load", variant="primary")
                    yield Button("Apply to File", id="btn-perm-apply", variant="error")

                yield Label("", id="lbl-perm-status")

    @on(Checkbox.Changed)
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if self.updating_ui:
            return
        self.recalculate_from_checkboxes()

    @on(Input.Changed, "#input-perm-octal")
    def on_octal_changed(self, event: Input.Changed) -> None:
        if self.updating_ui:
            return

        val = event.value
        if len(val) == 3 and val.isdigit():
            # Validate ranges (0-7)
            if all(0 <= int(d) <= 7 for d in val):
                self.update_checkboxes_from_octal(val)

    @on(Input.Changed, "#input-perm-symbolic")
    def on_symbolic_changed(self, event: Input.Changed) -> None:
        if self.updating_ui:
            return

        val = event.value
        if len(val) == 9:
            # Basic validation
            valid_chars = set("rwx-")
            if all(c in valid_chars for c in val):
                self.update_checkboxes_from_symbolic(val)

    @on(Button.Pressed, "#btn-perm-load")
    def on_load_file(self) -> None:
        path = self.query_one("#input-perm-path", Input).value
        if not path:
            self.notify("Path is empty.", severity="warning")
            return

        res = self.manager.get_permissions(path)
        status_lbl = self.query_one("#lbl-perm-status", Label)

        if "error" in res:
            status_lbl.update(f"[red]Error: {res['error']}[/red]")
            self.notify("Failed to load permissions.", severity="error")
        else:
            octal = res["octal"]
            symbolic = res["symbolic"]

            # Update inputs and checkboxes
            self.updating_ui = True
            try:
                self.query_one("#input-perm-octal", Input).value = octal
                self.query_one("#input-perm-symbolic", Input).value = symbolic
            finally:
                self.updating_ui = False

            # This will trigger update of checkboxes because we set inputs?
            # No, Input.Changed is emitted when value changes programmatically too in Textual?
            # Actually, modifying .value usually triggers Changed event.
            # So I wrapped it in updating_ui=True.

            # Now I need to explicitly update checkboxes because I suppressed the event handling
            self.update_checkboxes_from_octal(octal)

            status_lbl.update(f"[green]Loaded: {octal} ({symbolic})[/green]")
            self.notify("Permissions loaded.")

    @on(Button.Pressed, "#btn-perm-apply")
    def on_apply_file(self) -> None:
        path = self.query_one("#input-perm-path", Input).value
        octal = self.query_one("#input-perm-octal", Input).value

        if not path:
            self.notify("Path is empty.", severity="error")
            return

        status_lbl = self.query_one("#lbl-perm-status", Label)

        if self.manager.set_permissions(path, octal):
            status_lbl.update(f"[green]Applied {octal} to {path}[/green]")
            self.notify(f"Permissions set to {octal}.")
        else:
            status_lbl.update(f"[red]Failed to set permissions.[/red]")
            self.notify("Failed to set permissions.", severity="error")

    def recalculate_from_checkboxes(self) -> None:
        # Owner
        ur = self.query_one("#chk-u-r", Checkbox).value
        uw = self.query_one("#chk-u-w", Checkbox).value
        ux = self.query_one("#chk-u-x", Checkbox).value

        # Group
        gr = self.query_one("#chk-g-r", Checkbox).value
        gw = self.query_one("#chk-g-w", Checkbox).value
        gx = self.query_one("#chk-g-x", Checkbox).value

        # Other
        _or = self.query_one("#chk-o-r", Checkbox).value
        ow = self.query_one("#chk-o-w", Checkbox).value
        ox = self.query_one("#chk-o-x", Checkbox).value

        od = self.manager.to_octal(ur, uw, ux)
        gd = self.manager.to_octal(gr, gw, gx)
        ood = self.manager.to_octal(_or, ow, ox)

        octal_str = f"{od}{gd}{ood}"

        osym = self.manager.to_symbolic(ur, uw, ux)
        gsym = self.manager.to_symbolic(gr, gw, gx)
        oosym = self.manager.to_symbolic(_or, ow, ox)

        symbolic_str = f"{osym}{gsym}{oosym}"

        self.updating_ui = True
        try:
            self.query_one("#input-perm-octal", Input).value = octal_str
            self.query_one("#input-perm-symbolic", Input).value = symbolic_str
        finally:
            self.updating_ui = False

    def update_checkboxes_from_octal(self, octal_str: str) -> None:
        if len(octal_str) != 3:
            return

        try:
            o_owner = int(octal_str[0])
            o_group = int(octal_str[1])
            o_other = int(octal_str[2])

            ur, uw, ux = self.manager.from_octal(o_owner)
            gr, gw, gx = self.manager.from_octal(o_group)
            _or, ow, ox = self.manager.from_octal(o_other)

            self.updating_ui = True
            try:
                self.query_one("#chk-u-r", Checkbox).value = ur
                self.query_one("#chk-u-w", Checkbox).value = uw
                self.query_one("#chk-u-x", Checkbox).value = ux

                self.query_one("#chk-g-r", Checkbox).value = gr
                self.query_one("#chk-g-w", Checkbox).value = gw
                self.query_one("#chk-g-x", Checkbox).value = gx

                self.query_one("#chk-o-r", Checkbox).value = _or
                self.query_one("#chk-o-w", Checkbox).value = ow
                self.query_one("#chk-o-x", Checkbox).value = ox

                # Update symbolic too
                osym = self.manager.to_symbolic(ur, uw, ux)
                gsym = self.manager.to_symbolic(gr, gw, gx)
                oosym = self.manager.to_symbolic(_or, ow, ox)
                self.query_one("#input-perm-symbolic", Input).value = f"{osym}{gsym}{oosym}"

            finally:
                self.updating_ui = False

        except ValueError:
            pass

    def update_checkboxes_from_symbolic(self, symbolic_str: str) -> None:
        if len(symbolic_str) != 9:
            return

        # rwxr-xr-x
        # 012345678

        def parse_triplet(s):
            return s[0] == 'r', s[1] == 'w', s[2] == 'x'

        ur, uw, ux = parse_triplet(symbolic_str[0:3])
        gr, gw, gx = parse_triplet(symbolic_str[3:6])
        _or, ow, ox = parse_triplet(symbolic_str[6:9])

        self.updating_ui = True
        try:
            self.query_one("#chk-u-r", Checkbox).value = ur
            self.query_one("#chk-u-w", Checkbox).value = uw
            self.query_one("#chk-u-x", Checkbox).value = ux

            self.query_one("#chk-g-r", Checkbox).value = gr
            self.query_one("#chk-g-w", Checkbox).value = gw
            self.query_one("#chk-g-x", Checkbox).value = gx

            self.query_one("#chk-o-r", Checkbox).value = _or
            self.query_one("#chk-o-w", Checkbox).value = ow
            self.query_one("#chk-o-x", Checkbox).value = ox

            # Update octal too
            od = self.manager.to_octal(ur, uw, ux)
            gd = self.manager.to_octal(gr, gw, gx)
            ood = self.manager.to_octal(_or, ow, ox)
            self.query_one("#input-perm-octal", Input).value = f"{od}{gd}{ood}"

        finally:
            self.updating_ui = False
