from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Input, Select, Button, DataTable
from textual import on
from shared.unit_lab import UnitLabManager


class UnitLabTab(Container):
    """Tab for Unit Conversion."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = UnitLabManager()
        self.current_category = "length"  # Default

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]Unit Converter[/bold]", classes="welcome-text")

            with Container(classes="stat-box"):
                yield Label("Category:")
                yield Select([], id="unit-category-select", prompt="Select Category")

            with Container(classes="stat-box"):
                with Horizontal():
                    with Vertical():
                        yield Label("Value:")
                        yield Input(placeholder="Enter value...", id="unit-value-input", type="number")

                    with Vertical():
                        yield Label("From:")
                        yield Select([], id="unit-from-select", prompt="From Unit")

                    with Vertical():
                        yield Label(" ")  # Spacer
                        yield Button("⇄", id="btn-unit-swap", variant="default")

                    with Vertical():
                        yield Label("To:")
                        yield Select([], id="unit-to-select", prompt="To Unit")

            with Container(classes="stat-box"):
                yield Label("Result:")
                yield Label("", id="unit-result-label", classes="value")

            with Container(classes="stat-box"):
                yield Label("[bold]Reference Table (1 unit)[/bold]")
                yield DataTable(id="unit-ref-table")

    def on_mount(self) -> None:
        # Populate Categories
        cats = self.manager.get_categories()
        cat_select = self.query_one("#unit-category-select", Select)
        cat_select.set_options([(c.capitalize(), c) for c in cats])

        # Set default
        if cats:
            cat_select.value = "length"

        # Setup Table
        table = self.query_one("#unit-ref-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Unit", "Value")

    @on(Select.Changed, "#unit-category-select")
    def on_category_changed(self, event: Select.Changed) -> None:
        cat = event.value
        if not isinstance(cat, str):
            return

        self.current_category = cat
        units = self.manager.get_units_in_category(cat)
        options = [(u, u) for u in units]

        from_sel = self.query_one("#unit-from-select", Select)
        to_sel = self.query_one("#unit-to-select", Select)

        from_sel.set_options(options)
        to_sel.set_options(options)

        # Set defaults if possible
        if units:
            # Try to set sensible defaults? or just first and second
            from_sel.value = units[0]
            if len(units) > 1:
                to_sel.value = units[1]
            else:
                to_sel.value = units[0]

        self.update_result()
        self.update_reference_table()

    @on(Input.Changed, "#unit-value-input")
    def on_input_changed(self) -> None:
        self.update_result()

    @on(Select.Changed, "#unit-from-select")
    def on_from_changed(self) -> None:
        self.update_result()
        self.update_reference_table()

    @on(Select.Changed, "#unit-to-select")
    def on_to_changed(self) -> None:
        self.update_result()

    @on(Button.Pressed, "#btn-unit-swap")
    def on_swap(self) -> None:
        from_sel = self.query_one("#unit-from-select", Select)
        to_sel = self.query_one("#unit-to-select", Select)

        val_from = from_sel.value
        val_to = to_sel.value

        from_sel.value = val_to
        to_sel.value = val_from  # Triggers on_changed -> update_result

    def update_result(self) -> None:
        val_str = self.query_one("#unit-value-input", Input).value
        from_unit = self.query_one("#unit-from-select", Select).value
        to_unit = self.query_one("#unit-to-select", Select).value
        lbl = self.query_one("#unit-result-label", Label)

        if not val_str or not isinstance(from_unit, str) or not isinstance(to_unit, str):
            lbl.update("---")
            return

        try:
            val = float(val_str)
        except ValueError:
            lbl.update("Invalid Number")
            return

        res = self.manager.convert(val, from_unit, to_unit)

        # Color the result if it's an error
        if res.startswith("Error"):
            lbl.update(f"[red]{res}[/red]")
        else:
            lbl.update(f"[bold green]{res} {to_unit}[/bold green]")

    def update_reference_table(self) -> None:
        from_unit = self.query_one("#unit-from-select", Select).value
        if not isinstance(from_unit, str):
            return

        table = self.query_one("#unit-ref-table", DataTable)
        table.clear()

        units = self.manager.get_units_in_category(self.current_category)

        # Calculate 1 from_unit -> all others
        for u in units:
            res = self.manager.convert(1, from_unit, u)
            table.add_row(u, res)
