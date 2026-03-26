from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, TextArea, TabbedContent, TabPane, DataTable
from shared.pgp_lab import PGPLabManager


class PGPLabTab(Container):
    """TUI tab for PGP Lab."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = PGPLabManager()

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Keys", id="pane-pgp-keys"):
                yield Vertical(
                    Horizontal(
                        Input(placeholder="Real Name", id="pgp-gen-name", classes="pgp-input"),
                        Input(placeholder="Email", id="pgp-gen-email", classes="pgp-input"),
                        Input(placeholder="Passphrase", id="pgp-gen-passphrase", password=True, classes="pgp-input"),
                        Button("Generate Key", id="pgp-gen-btn", variant="primary"),
                        classes="pgp-controls"
                    ),
                    Button("Refresh Keys", id="pgp-refresh-btn"),
                    DataTable(id="pgp-keys-table")
                )
            with TabPane("Encrypt / Decrypt", id="pane-pgp-crypto"):
                yield Vertical(
                    TextArea(id="pgp-crypto-input", classes="pgp-area"),
                    Horizontal(
                        Input(placeholder="Recipients (comma separated emails)", id="pgp-encrypt-recipients", classes="pgp-input"),
                        Button("Encrypt", id="pgp-encrypt-btn", variant="primary"),
                        Input(placeholder="Passphrase (for decrypt)", id="pgp-decrypt-passphrase", password=True, classes="pgp-input"),
                        Button("Decrypt", id="pgp-decrypt-btn", variant="error"),
                        classes="pgp-controls"
                    ),
                    TextArea(id="pgp-crypto-output", read_only=True, classes="pgp-area")
                )
            with TabPane("Sign / Verify", id="pane-pgp-sign"):
                yield Vertical(
                    TextArea(id="pgp-sign-input", classes="pgp-area"),
                    Horizontal(
                        Input(placeholder="Key ID (for sign)", id="pgp-sign-keyid", classes="pgp-input"),
                        Input(placeholder="Passphrase", id="pgp-sign-passphrase", password=True, classes="pgp-input"),
                        Button("Sign", id="pgp-sign-btn", variant="primary"),
                        Button("Verify", id="pgp-verify-btn", variant="success"),
                        classes="pgp-controls"
                    ),
                    TextArea(id="pgp-sign-output", read_only=True, classes="pgp-area")
                )

    def on_mount(self) -> None:
        table = self.query_one("#pgp-keys-table", DataTable)
        table.add_columns("Type", "Key ID", "Fingerprint", "UIDs")
        self.refresh_keys()

    def refresh_keys(self) -> None:
        table = self.query_one("#pgp-keys-table", DataTable)
        table.clear()
        try:
            keys = self.manager.list_keys()
            for key in keys:
                uids = ", ".join(key.get('uids', []))
                table.add_row(key.get('type', ''), key.get('keyid', ''), key.get('fingerprint', ''), uids)
        except Exception as e:
            self.app.notify(f"Failed to list keys: {e}", severity="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "pgp-refresh-btn":
            self.refresh_keys()

        elif event.button.id == "pgp-gen-btn":
            name = self.query_one("#pgp-gen-name", Input).value
            email = self.query_one("#pgp-gen-email", Input).value
            passphrase = self.query_one("#pgp-gen-passphrase", Input).value

            if not name or not email or not passphrase:
                self.app.notify("Name, email, and passphrase are required.", severity="error")
                return

            self.app.notify("Generating key, please wait...", severity="information")
            # In a real app this should run async or in a worker to not block the UI
            try:
                fingerprint = self.manager.generate_key(name, email, passphrase)
                if fingerprint:
                    self.app.notify(f"Key generated: {fingerprint}", severity="information")
                    self.refresh_keys()
                else:
                    self.app.notify("Failed to generate key.", severity="error")
            except Exception as e:
                self.app.notify(f"Error generating key: {e}", severity="error")

        elif event.button.id == "pgp-encrypt-btn":
            data = self.query_one("#pgp-crypto-input", TextArea).text
            recipients_str = self.query_one("#pgp-encrypt-recipients", Input).value

            if not data or not recipients_str:
                self.app.notify("Data and recipients are required.", severity="error")
                return

            recipients = [r.strip() for r in recipients_str.split(',') if r.strip()]
            try:
                encrypted = self.manager.encrypt(data, recipients)
                if encrypted:
                    self.query_one("#pgp-crypto-output", TextArea).text = encrypted
                else:
                    self.app.notify("Encryption failed.", severity="error")
            except Exception as e:
                self.app.notify(f"Encryption error: {e}", severity="error")

        elif event.button.id == "pgp-decrypt-btn":
            data = self.query_one("#pgp-crypto-input", TextArea).text
            passphrase = self.query_one("#pgp-decrypt-passphrase", Input).value

            if not data or not passphrase:
                self.app.notify("Data and passphrase are required.", severity="error")
                return

            try:
                decrypted = self.manager.decrypt(data, passphrase)
                if decrypted:
                    self.query_one("#pgp-crypto-output", TextArea).text = decrypted
                else:
                    self.app.notify("Decryption failed.", severity="error")
            except Exception as e:
                self.app.notify(f"Decryption error: {e}", severity="error")

        elif event.button.id == "pgp-sign-btn":
            data = self.query_one("#pgp-sign-input", TextArea).text
            keyid = self.query_one("#pgp-sign-keyid", Input).value
            passphrase = self.query_one("#pgp-sign-passphrase", Input).value

            if not data or not keyid or not passphrase:
                self.app.notify("Data, key ID, and passphrase are required.", severity="error")
                return

            try:
                signed = self.manager.sign(data, keyid, passphrase)
                if signed:
                    self.query_one("#pgp-sign-output", TextArea).text = signed
                else:
                    self.app.notify("Signing failed.", severity="error")
            except Exception as e:
                self.app.notify(f"Signing error: {e}", severity="error")

        elif event.button.id == "pgp-verify-btn":
            data = self.query_one("#pgp-sign-input", TextArea).text

            if not data:
                self.app.notify("Signed data is required.", severity="error")
                return

            try:
                fingerprint = self.manager.verify(data)
                if fingerprint:
                    self.query_one("#pgp-sign-output", TextArea).text = f"✅ Valid signature from: {fingerprint}"
                else:
                    self.query_one("#pgp-sign-output", TextArea).text = "❌ Invalid signature."
            except Exception as e:
                self.app.notify(f"Verification error: {e}", severity="error")
