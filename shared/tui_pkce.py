from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import TabPane, Button, Input, Label, RadioSet, RadioButton, Static
from textual.reactive import reactive
from shared.pkce_lab import PkceManager

class PkceLabTab(TabPane):
    """A TUI component for PKCE (Proof Key for Code Exchange) operations."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__("PKCE Lab", *args, **kwargs)
        self.manager = PkceManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="panel"):
            yield Label("PKCE Code Verifier & Challenge Generator", classes="title")

            with Horizontal(classes="input-row"):
                yield Button("Generate Verifier", id="btn-generate-verifier", variant="primary")

            yield Label("Code Verifier:", classes="section-label")
            yield Input(id="input-verifier", placeholder="Enter or generate a code verifier...")

            yield Label("Challenge Method:", classes="section-label")
            with RadioSet(id="radio-method"):
                yield RadioButton("S256 (Recommended)", id="method-s256", value=True)
                yield RadioButton("Plain", id="method-plain")

            yield Label("Code Challenge:", classes="section-label")
            challenge_input = Input(id="input-challenge", placeholder="Generated code challenge...")
            challenge_input.disabled = True
            yield challenge_input

            with Horizontal(classes="input-row"):
                yield Button("Verify Challenge", id="btn-verify", variant="success")

            yield Static("", id="lbl-result", classes="result-label")

    def on_mount(self) -> None:
        self.action_generate_verifier()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-generate-verifier":
            self.action_generate_verifier()
        elif event.button.id == "btn-verify":
            self.action_verify()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input-verifier":
            self.update_challenge()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self.update_challenge()

    def action_generate_verifier(self) -> None:
        verifier = self.manager.generate_verifier(128)
        self.query_one("#input-verifier", Input).value = verifier
        # update_challenge will be called automatically due to input change
        self.query_one("#lbl-result", Static).update("")

    def get_selected_method(self) -> str:
        method_radio = self.query_one("#radio-method", RadioSet)
        if method_radio.pressed_button and method_radio.pressed_button.id == "method-plain":
            return "plain"
        return "S256"

    def update_challenge(self) -> None:
        verifier = self.query_one("#input-verifier", Input).value
        method = self.get_selected_method()

        if not verifier:
            self.query_one("#input-challenge", Input).value = ""
            return

        try:
            challenge = self.manager.generate_challenge(verifier, method)
            self.query_one("#input-challenge", Input).value = challenge
            self.query_one("#lbl-result", Static).update("")
        except Exception as e:
            self.query_one("#lbl-result", Static).update(f"[red]Error: {e}[/red]")

    def action_verify(self) -> None:
        verifier = self.query_one("#input-verifier", Input).value
        challenge = self.query_one("#input-challenge", Input).value
        method = self.get_selected_method()

        lbl_result = self.query_one("#lbl-result", Static)

        if not verifier or not challenge:
            lbl_result.update("[red]Verifier and Challenge are both required.[/red]")
            return

        try:
            is_valid = self.manager.verify(verifier, challenge, method)
            if is_valid:
                lbl_result.update("[green]Valid! Challenge matches the Verifier.[/green]")
            else:
                lbl_result.update("[red]Invalid! Challenge does not match the Verifier.[/red]")
        except Exception as e:
            lbl_result.update(f"[red]Error: {e}[/red]")
