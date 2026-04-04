from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Button, Input, Label, Select, TabbedContent, TabPane, TextArea, Checkbox
from textual import on
from shared.password_lab import PasswordLabManager


class PasswordLabTab(Container):
    """Tab for Password operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = PasswordLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Password Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Generator
                with TabPane("Generator"):
                    with Vertical(classes="stat-box"):
                        yield Label("Length:")
                        yield Input(value="16", id="pwd-gen-length")
                        yield Checkbox("Uppercase", value=True, id="pwd-gen-upper")
                        yield Checkbox("Lowercase", value=True, id="pwd-gen-lower")
                        yield Checkbox("Digits", value=True, id="pwd-gen-digits")
                        yield Checkbox("Symbols", value=True, id="pwd-gen-symbols")
                        yield Button("Generate Password", id="btn-pwd-gen", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Generated Password[/bold]")
                        yield TextArea(id="pwd-gen-output", read_only=True)

                # Passphrase
                with TabPane("Passphrase"):
                    with Vertical(classes="stat-box"):
                        yield Label("Words:")
                        yield Input(value="4", id="pwd-passphrase-words")
                        yield Label("Separator:")
                        yield Input(value="-", id="pwd-passphrase-separator")
                        yield Button("Generate Passphrase", id="btn-pwd-passphrase", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Generated Passphrase[/bold]")
                        yield TextArea(id="pwd-passphrase-output", read_only=True)

                # Strength Checker
                with TabPane("Checker"):
                    with Vertical(classes="stat-box"):
                        yield Label("Password:")
                        yield Input(password=True, id="pwd-chk-input")
                        yield Button("Check Strength", id="btn-pwd-chk", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Strength Analysis[/bold]")
                        yield TextArea(id="pwd-chk-output", read_only=True)

                # Hasher
                with TabPane("Hasher"):
                    with Vertical(classes="stat-box"):
                        yield Label("Password:")
                        yield Input(password=True, id="pwd-hash-input")
                        yield Label("Algorithm:")
                        yield Select.from_values(["scrypt", "pbkdf2"], id="pwd-hash-algo", value="scrypt")
                        yield Label("Salt (Optional):")
                        yield Input(id="pwd-hash-salt")
                        yield Button("Hash Password", id="btn-pwd-hash", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Hash Output[/bold]")
                        yield TextArea(id="pwd-hash-output", read_only=True)

    @on(Button.Pressed, "#btn-pwd-gen")
    def on_generate_password(self, event: Button.Pressed) -> None:
        try:
            length = int(self.query_one("#pwd-gen-length", Input).value)
        except ValueError:
            self.query_one("#pwd-gen-output", TextArea).text = "Error: Invalid length."
            return

        use_upper = self.query_one("#pwd-gen-upper", Checkbox).value
        use_lower = self.query_one("#pwd-gen-lower", Checkbox).value
        use_digits = self.query_one("#pwd-gen-digits", Checkbox).value
        use_symbols = self.query_one("#pwd-gen-symbols", Checkbox).value

        try:
            pwd = self.manager.generate(
                length=length,
                use_upper=use_upper,
                use_lower=use_lower,
                use_digits=use_digits,
                use_symbols=use_symbols
            )
            strength = self.manager.check_strength(pwd)
            output = f"Password: {pwd}Entropy: {strength['entropy']} bits"
            self.query_one("#pwd-gen-output", TextArea).text = output
        except Exception as e:
            self.query_one("#pwd-gen-output", TextArea).text = f"Error: {e}"

    @on(Button.Pressed, "#btn-pwd-passphrase")
    def on_generate_passphrase(self, event: Button.Pressed) -> None:
        try:
            words = int(self.query_one("#pwd-passphrase-words", Input).value)
        except ValueError:
            self.query_one("#pwd-passphrase-output", TextArea).text = "Error: Invalid word count."
            return

        separator = self.query_one("#pwd-passphrase-separator", Input).value

        try:
            pwd = self.manager.generate_passphrase(words=words, separator=separator)
            strength = self.manager.check_strength(pwd)
            output = f"Passphrase: {pwd}\nEntropy: {strength['entropy']} bits"
            self.query_one("#pwd-passphrase-output", TextArea).text = output
        except Exception as e:
            self.query_one("#pwd-passphrase-output", TextArea).text = f"Error: {e}"

    @on(Button.Pressed, "#btn-pwd-chk")
    def on_check_strength(self, event: Button.Pressed) -> None:
        pwd = self.query_one("#pwd-chk-input", Input).value
        if not pwd:
            self.query_one("#pwd-chk-output", TextArea).text = "Error: Please enter a password."
            return

        try:
            res = self.manager.check_strength(pwd)
            score_display = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]
            score_idx = min(res['score'], 4)

            output = f"Score: {score_display[score_idx]} ({res['score']}/4)\n"
            output += f"Entropy: {res['entropy']} bits\n"
            output += f"Length: {res['length']}\n"

            if res['feedback']:
                output += "\nFeedback:\n"
                for item in res['feedback']:
                    output += f"  - {item}\n"

            self.query_one("#pwd-chk-output", TextArea).text = output
        except Exception as e:
            self.query_one("#pwd-chk-output", TextArea).text = f"Error: {e}"

    @on(Button.Pressed, "#btn-pwd-hash")
    def on_hash_password(self, event: Button.Pressed) -> None:
        pwd = self.query_one("#pwd-hash-input", Input).value
        if not pwd:
            self.query_one("#pwd-hash-output", TextArea).text = "Error: Please enter a password."
            return

        algo = self.query_one("#pwd-hash-algo", Select).value
        salt = self.query_one("#pwd-hash-salt", Input).value
        if not salt:
            salt = None

        try:
            hashed = self.manager.hash_password(pwd, algo=algo, salt=salt)
            self.query_one("#pwd-hash-output", TextArea).text = hashed
        except Exception as e:
            self.query_one("#pwd-hash-output", TextArea).text = f"Error: {e}"
