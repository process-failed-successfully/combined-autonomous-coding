from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Input, Static, TabPane
from textual import work

from shared.currency_lab import CurrencyLabManager

class CurrencyLabTab(TabPane):
    """TUI Tab for Currency Lab."""

    def __init__(self):
        super().__init__("Currency", id="tab-currency-lab")
        self.manager = CurrencyLabManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-4"):
            yield Static("Currency Converter", classes="text-xl text-bold mb-4")

            with Horizontal(classes="mb-2 h-auto"):
                yield Input(placeholder="Amount (e.g. 100)", id="currency-amount", classes="w-1-3")
                yield Input(placeholder="From (e.g. USD)", id="currency-from", classes="w-1-3 ml-2")
                yield Input(placeholder="To (e.g. EUR)", id="currency-to", classes="w-1-3 ml-2")

            with Horizontal(classes="mb-4 h-auto"):
                yield Button("Convert", id="btn-currency-convert", variant="primary")
                yield Button("List Currencies", id="btn-currency-list", classes="ml-4")

            yield Static(id="currency-result", classes="mt-4 border p-2")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-currency-convert":
            self.action_convert()
        elif event.button.id == "btn-currency-list":
            self.action_list()

    @work(exclusive=True, thread=True)
    def action_convert(self) -> None:
        amount_input = self.query_one("#currency-amount", Input).value
        from_input = self.query_one("#currency-from", Input).value
        to_input = self.query_one("#currency-to", Input).value
        result_display = self.query_one("#currency-result", Static)

        if not amount_input or not from_input or not to_input:
            self.app.call_from_thread(result_display.update, "Error: All fields are required.")
            return

        try:
            amount = float(amount_input)
        except ValueError:
            self.app.call_from_thread(result_display.update, "Error: Amount must be a valid number.")
            return

        self.app.call_from_thread(result_display.update, "Converting...")
        try:
            result = self.manager.convert(amount, from_input, to_input)
            self.app.call_from_thread(result_display.update, result)
        except Exception as e:
            self.app.call_from_thread(result_display.update, f"Error: {e}")

    @work(exclusive=True, thread=True)
    def action_list(self) -> None:
        result_display = self.query_one("#currency-result", Static)
        self.app.call_from_thread(result_display.update, "Fetching currencies...")

        try:
            currencies = self.manager.list_currencies()
            if not currencies:
                self.app.call_from_thread(result_display.update, "Failed to load currencies.")
                return

            import textwrap
            wrapped = textwrap.fill(", ".join(currencies), width=100)
            self.app.call_from_thread(result_display.update, f"Supported Currencies:\n{wrapped}")
        except Exception as e:
            self.app.call_from_thread(result_display.update, f"Error: {e}")
