from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog, TabbedContent, TabPane
from textual.containers import Container, Vertical
import asyncio
from shared.finance_lab import FinanceLabManager


class FinanceLabTab(Container):
    """Tab for Financial calculations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = FinanceLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Finance Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Loan Pane
                with TabPane("Loan"):
                    with Vertical(classes="stat-box"):
                        yield Label("Loan Calculator")
                        yield Input(placeholder="Principal ($)", id="input-loan-principal")
                        yield Input(placeholder="Annual Rate (%)", id="input-loan-rate")
                        yield Input(placeholder="Term (Years)", id="input-loan-term")
                        yield Button("Calculate Loan", id="btn-calc-loan", variant="primary")
                        yield Label("[bold]Result[/bold]")
                        yield RichLog(id="log-loan-result", wrap=True, highlight=True, markup=True)

                # Compound Interest Pane
                with TabPane("Compound Interest"):
                    with Vertical(classes="stat-box"):
                        yield Label("Compound Interest Calculator")
                        yield Input(placeholder="Principal ($)", id="input-compound-principal")
                        yield Input(placeholder="Annual Rate (%)", id="input-compound-rate")
                        yield Input(placeholder="Time (Years)", id="input-compound-time")
                        yield Input(placeholder="Frequency (times/year, e.g. 12)", id="input-compound-freq")
                        yield Button("Calculate Compound Interest", id="btn-calc-compound", variant="primary")
                        yield Label("[bold]Result[/bold]")
                        yield RichLog(id="log-compound-result", wrap=True, highlight=True, markup=True)

                # NPV Pane
                with TabPane("NPV"):
                    with Vertical(classes="stat-box"):
                        yield Label("Net Present Value (NPV)")
                        yield Input(placeholder="Discount Rate (%)", id="input-npv-rate")
                        yield Input(placeholder="Cash Flows (comma separated)", id="input-npv-flows")
                        yield Button("Calculate NPV", id="btn-calc-npv", variant="primary")
                        yield Label("[bold]Result[/bold]")
                        yield RichLog(id="log-npv-result", wrap=True, highlight=True, markup=True)

                # ROI Pane
                with TabPane("ROI"):
                    with Vertical(classes="stat-box"):
                        yield Label("Return on Investment (ROI)")
                        yield Input(placeholder="Initial Investment ($)", id="input-roi-initial")
                        yield Input(placeholder="Final Value ($)", id="input-roi-final")
                        yield Button("Calculate ROI", id="btn-calc-roi", variant="primary")
                        yield Label("[bold]Result[/bold]")
                        yield RichLog(id="log-roi-result", wrap=True, highlight=True, markup=True)

                # Break-Even Pane
                with TabPane("Break-Even"):
                    with Vertical(classes="stat-box"):
                        yield Label("Break-Even Analysis")
                        yield Input(placeholder="Fixed Costs ($)", id="input-be-fixed")
                        yield Input(placeholder="Variable Cost per Unit ($)", id="input-be-variable")
                        yield Input(placeholder="Price per Unit ($)", id="input-be-price")
                        yield Button("Calculate Break-Even", id="btn-calc-be", variant="primary")
                        yield Label("[bold]Result[/bold]")
                        yield RichLog(id="log-be-result", wrap=True, highlight=True, markup=True)

                # Inflation Pane
                with TabPane("Inflation"):
                    with Vertical(classes="stat-box"):
                        yield Label("Inflation Calculator")
                        yield Input(placeholder="Initial Value ($)", id="input-inf-value")
                        yield Input(placeholder="Inflation Rate (%)", id="input-inf-rate")
                        yield Input(placeholder="Years", id="input-inf-years")
                        yield Button("Calculate Inflation", id="btn-calc-inf", variant="primary")
                        yield Label("[bold]Result[/bold]")
                        yield RichLog(id="log-inf-result", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-calc-loan":
            await self.calculate_loan()
        elif event.button.id == "btn-calc-compound":
            await self.calculate_compound()
        elif event.button.id == "btn-calc-npv":
            await self.calculate_npv()
        elif event.button.id == "btn-calc-roi":
            await self.calculate_roi()
        elif event.button.id == "btn-calc-be":
            await self.calculate_break_even()
        elif event.button.id == "btn-calc-inf":
            await self.calculate_inflation()

    def _get_float(self, input_id: str) -> float:
        val = self.query_one(f"#{input_id}", Input).value
        try:
            return float(val)
        except ValueError:
            raise ValueError(f"Invalid number in {input_id}")

    def _get_int(self, input_id: str) -> int:
        val = self.query_one(f"#{input_id}", Input).value
        try:
            return int(val)
        except ValueError:
            raise ValueError(f"Invalid integer in {input_id}")

    async def calculate_loan(self) -> None:
        log = self.query_one("#log-loan-result", RichLog)
        log.clear()
        try:
            principal = self._get_float("input-loan-principal")
            rate = self._get_float("input-loan-rate")
            term = self._get_int("input-loan-term")

            result = await asyncio.to_thread(self.manager.calculate_loan_payment, principal, rate, term)
            log.write(result)
        except ValueError:
            self.notify("Please enter valid numbers.", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    async def calculate_compound(self) -> None:
        log = self.query_one("#log-compound-result", RichLog)
        log.clear()
        try:
            principal = self._get_float("input-compound-principal")
            rate = self._get_float("input-compound-rate")
            time = self._get_int("input-compound-time")
            freq = self._get_int("input-compound-freq")

            result = await asyncio.to_thread(self.manager.calculate_compound_interest, principal, rate, time, freq)
            log.write(result)
        except ValueError:
            self.notify("Please enter valid numbers.", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    async def calculate_npv(self) -> None:
        log = self.query_one("#log-npv-result", RichLog)
        log.clear()
        try:
            rate = self._get_float("input-npv-rate")
            flows_str = self.query_one("#input-npv-flows", Input).value
            flows = [float(x.strip()) for x in flows_str.split(",")]

            result = await asyncio.to_thread(self.manager.calculate_npv, rate, flows)
            log.write(result)
        except ValueError:
            self.notify("Please enter valid numbers.", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    async def calculate_roi(self) -> None:
        log = self.query_one("#log-roi-result", RichLog)
        log.clear()
        try:
            initial = self._get_float("input-roi-initial")
            final = self._get_float("input-roi-final")

            result = await asyncio.to_thread(self.manager.calculate_roi, initial, final)
            log.write(result)
        except ValueError:
            self.notify("Please enter valid numbers.", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    async def calculate_break_even(self) -> None:
        log = self.query_one("#log-be-result", RichLog)
        log.clear()
        try:
            fixed = self._get_float("input-be-fixed")
            variable = self._get_float("input-be-variable")
            price = self._get_float("input-be-price")

            result = await asyncio.to_thread(self.manager.calculate_break_even, fixed, variable, price)
            log.write(result)
        except ValueError:
            self.notify("Please enter valid numbers.", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    async def calculate_inflation(self) -> None:
        log = self.query_one("#log-inf-result", RichLog)
        log.clear()
        try:
            value = self._get_float("input-inf-value")
            rate = self._get_float("input-inf-rate")
            years = self._get_int("input-inf-years")

            result = await asyncio.to_thread(self.manager.calculate_inflation, value, rate, years)
            log.write(result)
        except ValueError:
            self.notify("Please enter valid numbers.", severity="error")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
