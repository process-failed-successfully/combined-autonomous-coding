from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, DataTable, Input, Select, TextArea, TabbedContent, TabPane
from textual import on
from shared.ssh_lab import SshLabManager


class SshLabTab(Container):
    """
    SSH Lab Tab for managing SSH keys and config.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = SshLabManager()
        self.selected_key_name: Optional[str] = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]SSH Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # --- Keys Tab ---
                with TabPane("Keys", id="ssh-tab-keys"):
                    with Horizontal():
                        # Left Pane: List
                        with Vertical(id="ssh-keys-list-container", classes="stat-box"):
                            yield Label("[bold]SSH Keys[/bold]")
                            yield DataTable(id="ssh-keys-table")

                            with Horizontal():
                                yield Button("Refresh", id="btn-ssh-refresh", variant="default")
                                # yield Button("New Key", id="btn-ssh-new-key-dialog", variant="primary") # Just use the form below

                        # Right Pane: Details
                        with Vertical(id="ssh-key-details-container"):
                            yield Label("[bold]Key Details[/bold]")
                            yield Label("Select a key to view details.", id="ssh-key-header")

                            yield Label("Fingerprint:")
                            yield Label("", id="ssh-key-fingerprint", classes="value")

                            yield Label("Public Key:")
                            yield TextArea(id="ssh-key-public", read_only=True)

                            with Horizontal(id="ssh-key-actions"):
                                yield Button("Delete Key", id="btn-ssh-delete", variant="error", disabled=True)

                    # New Key Form (Hidden by default or separate section? Let's put it in a container that we can toggle or just show)
                    with Vertical(id="ssh-new-key-form", classes="stat-box"):
                        yield Label("[bold]Generate New Key[/bold]")
                        with Horizontal():
                            yield Select.from_values(["ed25519", "rsa"], id="ssh-gen-type", value="ed25519")
                            yield Input(placeholder="Bits (e.g. 4096 for RSA)...", id="ssh-gen-bits", value="4096")

                        with Horizontal():
                            yield Input(placeholder="Filename (e.g. id_ed25519_new)...", id="ssh-gen-filename")
                            yield Input(placeholder="Comment (e.g. email)...", id="ssh-gen-comment")

                        yield Button("Generate", id="btn-ssh-generate", variant="success")

                # --- Config Tab ---
                with TabPane("Config", id="ssh-tab-config"):
                    with Horizontal():
                        # Left: Config List
                        with Vertical(classes="stat-box"):
                            yield Label("[bold]Defined Hosts[/bold]")
                            yield DataTable(id="ssh-hosts-table")
                            yield Button("Refresh Config", id="btn-ssh-refresh-config", variant="default")

                        # Right: Add Host Form
                        with Vertical(classes="stat-box"):
                            yield Label("[bold]Add Host[/bold]")
                            yield Input(placeholder="Host Alias (e.g. myserver)...", id="ssh-cfg-host")
                            yield Input(placeholder="HostName (IP or Domain)...", id="ssh-cfg-hostname")
                            yield Input(placeholder="User...", id="ssh-cfg-user")
                            yield Input(placeholder="IdentityFile (optional)...", id="ssh-cfg-identity")
                            yield Button("Add Host", id="btn-ssh-add-host", variant="primary")

    def on_mount(self) -> None:
        # Keys Table
        keys_table = self.query_one("#ssh-keys-table", DataTable)
        keys_table.cursor_type = "row"
        keys_table.add_columns("Name", "Has Pub?")

        # Hosts Table
        hosts_table = self.query_one("#ssh-hosts-table", DataTable)
        hosts_table.cursor_type = "row"
        hosts_table.add_columns("Host", "HostName", "User")

        self.load_keys()
        self.load_hosts()

    # --- Keys Logic ---

    def load_keys(self) -> None:
        table = self.query_one("#ssh-keys-table", DataTable)
        table.clear()

        keys = self.manager.list_keys()
        for k in keys:
            pub_str = "Yes" if k['has_pub'] else "No"
            table.add_row(k['name'], pub_str, key=k['name'])

    @on(Button.Pressed, "#btn-ssh-refresh")
    def on_refresh_keys(self) -> None:
        self.load_keys()
        self.notify("Keys refreshed.")

    @on(DataTable.RowSelected, "#ssh-keys-table")
    def on_key_selected(self, event: DataTable.RowSelected) -> None:
        key_name = event.row_key.value
        self.selected_key_name = key_name
        self.load_key_details(key_name)
        self.query_one("#btn-ssh-delete").disabled = False

    def load_key_details(self, key_name: str) -> None:
        self.query_one("#ssh-key-header", Label).update(f"[bold]{key_name}[/bold]")

        # Fingerprint
        fp_res = self.manager.get_fingerprint(key_name)
        if fp_res["success"]:
            self.query_one("#ssh-key-fingerprint", Label).update(fp_res["fingerprint"])
        else:
            self.query_one("#ssh-key-fingerprint", Label).update(f"[red]{fp_res.get('error')}[/red]")

        # Public Key
        pub_content = self.manager.read_public_key(key_name)
        if pub_content:
            self.query_one("#ssh-key-public", TextArea).text = pub_content
        else:
            self.query_one("#ssh-key-public", TextArea).text = "Public key not found."

    @on(Button.Pressed, "#btn-ssh-generate")
    def on_generate_key(self) -> None:
        ktype = self.query_one("#ssh-gen-type", Select).value
        filename = self.query_one("#ssh-gen-filename", Input).value
        comment = self.query_one("#ssh-gen-comment", Input).value

        # Bits logic
        bits_str = self.query_one("#ssh-gen-bits", Input).value
        bits = 4096
        if bits_str and bits_str.isdigit():
            bits = int(bits_str)

        if not filename:
            self.notify("Filename required.", severity="error")
            return

        self.notify(f"Generating {ktype} key...", severity="information")

        # Run in thread if needed, but keygen is usually fast enough for TUI
        res = self.manager.generate_key(ktype, bits, comment, filename)

        if res["success"]:
            self.notify(f"Key generated: {filename}")
            self.load_keys()
            # Clear inputs
            self.query_one("#ssh-gen-filename", Input).value = ""
        else:
            self.notify(f"Error: {res.get('error')}", severity="error")

    @on(Button.Pressed, "#btn-ssh-delete")
    def on_delete_key(self) -> None:
        if not self.selected_key_name:
            return

        if self.manager.delete_key(self.selected_key_name):
            self.notify(f"Deleted {self.selected_key_name}")
            self.selected_key_name = None
            self.load_keys()
            # Reset Details
            self.query_one("#ssh-key-header", Label).update("Select a key.")
            self.query_one("#ssh-key-fingerprint", Label).update("")
            self.query_one("#ssh-key-public", TextArea).text = ""
            self.query_one("#btn-ssh-delete").disabled = True
        else:
            self.notify("Failed to delete key.", severity="error")

    # --- Config Logic ---

    def load_hosts(self) -> None:
        table = self.query_one("#ssh-hosts-table", DataTable)
        table.clear()

        hosts = self.manager.list_hosts()
        for h in hosts:
            table.add_row(
                h.get('Host', ''),
                h.get('HostName', ''),
                h.get('User', '')
            )

    @on(Button.Pressed, "#btn-ssh-refresh-config")
    def on_refresh_config(self) -> None:
        self.load_hosts()
        self.notify("Config refreshed.")

    @on(Button.Pressed, "#btn-ssh-add-host")
    def on_add_host(self) -> None:
        host = self.query_one("#ssh-cfg-host", Input).value
        hostname = self.query_one("#ssh-cfg-hostname", Input).value
        user = self.query_one("#ssh-cfg-user", Input).value
        identity = self.query_one("#ssh-cfg-identity", Input).value

        if not host or not hostname or not user:
            self.notify("Host, HostName, and User are required.", severity="error")
            return

        if self.manager.add_host(host, hostname, user, identity if identity else None):
            self.notify(f"Host '{host}' added.")
            self.load_hosts()
            # Clear inputs
            self.query_one("#ssh-cfg-host", Input).value = ""
            self.query_one("#ssh-cfg-hostname", Input).value = ""
            self.query_one("#ssh-cfg-user", Input).value = ""
            self.query_one("#ssh-cfg-identity", Input).value = ""
        else:
            self.notify("Failed to add host.", severity="error")
