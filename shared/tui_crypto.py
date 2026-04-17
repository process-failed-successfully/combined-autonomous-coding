from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, Select, TabbedContent, TabPane, TextArea
from shared.crypto_lab import CryptoLabManager


class CryptoLabTab(Container):
    """Tab for Cryptographic operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = CryptoLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Crypto Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Hashing
                with TabPane("Hashing"):
                    with Vertical(classes="stat-box"):
                        yield Label("Input (Text):")
                        yield TextArea(id="crypto-hash-input")
                        yield Label("Algorithm:")
                        yield Select.from_values(["md5", "sha1", "sha256", "sha512"], id="crypto-hash-algo", value="sha256")
                        yield Button("Calculate Hash", id="btn-crypto-hash", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Hash Output[/bold]")
                        yield TextArea(id="crypto-hash-output", read_only=True)

                # HMAC
                with TabPane("HMAC"):
                    with Vertical(classes="stat-box"):
                        yield Label("Input (Text):")
                        yield TextArea(id="crypto-hmac-input")
                        yield Label("Key:")
                        yield Input(id="crypto-hmac-key")
                        yield Label("Algorithm:")
                        yield Select.from_values(["md5", "sha1", "sha256", "sha512"], id="crypto-hmac-algo", value="sha256")
                        yield Button("Generate HMAC", id="btn-crypto-hmac", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]HMAC Output[/bold]")
                        yield TextArea(id="crypto-hmac-output", read_only=True)

                # Encrypt
                with TabPane("Encrypt"):
                    with Horizontal(classes="stat-box"):
                        with Vertical():
                            yield Label("Key (Fernet):")
                            yield Input(placeholder="Generate or paste key...", id="crypto-enc-key")
                            yield Button("Generate Key", id="btn-crypto-gen-key", variant="warning")

                    with Vertical(classes="stat-box"):
                        yield Label("Input Text:")
                        yield TextArea(id="crypto-enc-input")
                        yield Button("Encrypt", id="btn-crypto-encrypt", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Encrypted Output (Base64)[/bold]")
                        yield TextArea(id="crypto-enc-output", read_only=True)

                # Decrypt
                with TabPane("Decrypt"):
                    with Horizontal(classes="stat-box"):
                        with Vertical():
                            yield Label("Key (Fernet):")
                            yield Input(placeholder="Paste key...", id="crypto-dec-key")

                    with Vertical(classes="stat-box"):
                        yield Label("Encrypted Text (Base64):")
                        yield TextArea(id="crypto-dec-input")
                        yield Button("Decrypt", id="btn-crypto-decrypt", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Decrypted Output[/bold]")
                        yield TextArea(id="crypto-dec-output", read_only=True)

                # Asymmetric (RSA)
                with TabPane("Asymmetric (RSA)"):
                    with Horizontal(classes="stat-box"):
                        with Vertical():
                            yield Button("Generate RSA Keypair", id="btn-crypto-rsa-gen", variant="warning")
                    with Horizontal(classes="stat-box"):
                        with Vertical():
                            yield Label("Private Key (PEM):")
                            yield TextArea(id="crypto-rsa-priv")
                        with Vertical():
                            yield Label("Public Key (PEM):")
                            yield TextArea(id="crypto-rsa-pub")
                    with Horizontal(classes="stat-box"):
                        with Vertical():
                            yield Label("Input Text:")
                            yield TextArea(id="crypto-rsa-input")
                            with Horizontal():
                                yield Button("Encrypt (uses Pub)", id="btn-crypto-rsa-enc", variant="primary")
                                yield Button("Decrypt (uses Priv)", id="btn-crypto-rsa-dec", variant="primary")
                                yield Button("Sign (uses Priv)", id="btn-crypto-rsa-sign", variant="primary")
                                yield Button("Verify (uses Pub)", id="btn-crypto-rsa-verify", variant="primary")
                    with Horizontal(classes="stat-box"):
                        with Vertical():
                            yield Label("Signature (Base64) (for Verify):")
                            yield TextArea(id="crypto-rsa-signature")
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Output (Text or Base64)[/bold]")
                        yield TextArea(id="crypto-rsa-output", read_only=True)

                # Random
                with TabPane("Random"):
                    with Horizontal(classes="stat-box"):
                        with Vertical():
                            yield Label("Length:")
                            yield Input(placeholder="32", id="crypto-rand-len", type="integer", value="32")
                        with Vertical():
                            yield Label("Type:")
                            yield Select.from_values(["hex", "base64", "uuid", "int"], id="crypto-rand-type", value="hex")

                    yield Button("Generate", id="btn-crypto-rand", variant="success")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Output[/bold]")
                        yield TextArea(id="crypto-rand-output", read_only=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-crypto-hash":
            self.do_hash()
        elif event.button.id == "btn-crypto-hmac":
            self.do_hmac()
        elif event.button.id == "btn-crypto-gen-key":
            self.do_gen_key()
        elif event.button.id == "btn-crypto-encrypt":
            self.do_encrypt()
        elif event.button.id == "btn-crypto-decrypt":
            self.do_decrypt()
        elif event.button.id == "btn-crypto-rand":
            self.do_random()
        elif event.button.id == "btn-crypto-rsa-gen":
            self.do_rsa_gen()
        elif event.button.id == "btn-crypto-rsa-enc":
            self.do_rsa_enc()
        elif event.button.id == "btn-crypto-rsa-dec":
            self.do_rsa_dec()
        elif event.button.id == "btn-crypto-rsa-sign":
            self.do_rsa_sign()
        elif event.button.id == "btn-crypto-rsa-verify":
            self.do_rsa_verify()

    def do_hash(self) -> None:
        text = self.query_one("#crypto-hash-input", TextArea).text
        algo = self.query_one("#crypto-hash-algo", Select).value or "sha256"
        out = self.query_one("#crypto-hash-output", TextArea)

        if not text:
            self.notify("Input required.", severity="error")
            return

        try:
            res = self.manager.hash_data(text, str(algo))
            out.text = res
            self.notify("Hash calculated.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def do_hmac(self) -> None:
        text = self.query_one("#crypto-hmac-input", TextArea).text
        key = self.query_one("#crypto-hmac-key", Input).value
        algo = self.query_one("#crypto-hmac-algo", Select).value or "sha256"
        out = self.query_one("#crypto-hmac-output", TextArea)

        if not text or not key:
            self.notify("Input and Key required.", severity="error")
            return

        try:
            res = self.manager.hmac_data(text, key, str(algo))
            out.text = res
            self.notify("HMAC calculated.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def do_gen_key(self) -> None:
        key = self.manager.generate_key()
        self.query_one("#crypto-enc-key", Input).value = key.decode("utf-8")
        self.notify("Key generated.")

    def do_encrypt(self) -> None:
        key_str = self.query_one("#crypto-enc-key", Input).value
        text = self.query_one("#crypto-enc-input", TextArea).text
        out = self.query_one("#crypto-enc-output", TextArea)

        if not key_str or not text:
            self.notify("Key and Input required.", severity="error")
            return

        try:
            key = key_str.encode("utf-8")
            res = self.manager.encrypt_data(text, key)
            out.text = res.decode("utf-8")
            self.notify("Encrypted.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def do_decrypt(self) -> None:
        key_str = self.query_one("#crypto-dec-key", Input).value
        text = self.query_one("#crypto-dec-input", TextArea).text
        out = self.query_one("#crypto-dec-output", TextArea)

        if not key_str or not text:
            self.notify("Key and Input required.", severity="error")
            return

        try:
            key = key_str.encode("utf-8")
            # Input text is likely base64 encoded bytes string
            data = text.encode("utf-8")
            res = self.manager.decrypt_data(data, key)
            out.text = res.decode("utf-8")
            self.notify("Decrypted.")
        except Exception as e:
            out.text = f"Error: {e}"
            self.notify("Decryption failed.", severity="error")

    def do_random(self) -> None:
        length_str = self.query_one("#crypto-rand-len", Input).value
        type_val = self.query_one("#crypto-rand-type", Select).value or "hex"
        out = self.query_one("#crypto-rand-output", TextArea)

        try:
            length = int(length_str) if length_str else 32
            res = self.manager.generate_random(length, str(type_val))
            out.text = res
            self.notify("Generated.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def do_rsa_gen(self) -> None:
        try:
            priv, pub = self.manager.generate_rsa_keypair()
            self.query_one("#crypto-rsa-priv", TextArea).text = priv.decode("utf-8")
            self.query_one("#crypto-rsa-pub", TextArea).text = pub.decode("utf-8")
            self.notify("RSA Keypair generated.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def do_rsa_enc(self) -> None:
        pub = self.query_one("#crypto-rsa-pub", TextArea).text
        text = self.query_one("#crypto-rsa-input", TextArea).text
        out = self.query_one("#crypto-rsa-output", TextArea)

        if not pub or not text:
            self.notify("Public key and input required.", severity="error")
            return

        try:
            import base64
            res = self.manager.rsa_encrypt(text, pub.encode("utf-8"))
            out.text = base64.b64encode(res).decode("utf-8")
            self.notify("Encrypted.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def do_rsa_dec(self) -> None:
        priv = self.query_one("#crypto-rsa-priv", TextArea).text
        text = self.query_one("#crypto-rsa-input", TextArea).text
        out = self.query_one("#crypto-rsa-output", TextArea)

        if not priv or not text:
            self.notify("Private key and input required.", severity="error")
            return

        try:
            import base64
            data = base64.b64decode(text.strip())
            res = self.manager.rsa_decrypt(data, priv.encode("utf-8"))
            out.text = res.decode("utf-8")
            self.notify("Decrypted.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def do_rsa_sign(self) -> None:
        priv = self.query_one("#crypto-rsa-priv", TextArea).text
        text = self.query_one("#crypto-rsa-input", TextArea).text
        out = self.query_one("#crypto-rsa-output", TextArea)

        if not priv or not text:
            self.notify("Private key and input required.", severity="error")
            return

        try:
            import base64
            res = self.manager.rsa_sign(text, priv.encode("utf-8"))
            out.text = base64.b64encode(res).decode("utf-8")
            self.notify("Signed.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def do_rsa_verify(self) -> None:
        pub = self.query_one("#crypto-rsa-pub", TextArea).text
        text = self.query_one("#crypto-rsa-input", TextArea).text
        sig_text = self.query_one("#crypto-rsa-signature", TextArea).text.strip()
        if not pub or not text or not sig_text:
            self.notify("Public key, input text, and signature required.", severity="error")
            return

        try:
            import base64
            sig = base64.b64decode(sig_text)
            is_valid = self.manager.rsa_verify(text, sig, pub.encode("utf-8"))
            if is_valid:
                self.notify("Signature is VALID.", severity="information")
            else:
                self.notify("Signature is INVALID.", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
