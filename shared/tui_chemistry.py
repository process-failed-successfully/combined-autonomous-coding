from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, Grid
from textual.widgets import Label, Button, Input, Static, Header, Footer
from textual.reactive import reactive
from textual import on
from shared.chemistry_lab import ChemistryLabManager, ELEMENTS

class ElementButton(Button):
    """A button representing a chemical element in the periodic table."""

    def __init__(self, element_data: dict, **kwargs):
        super().__init__(label=element_data["symbol"], **kwargs)
        self.element_data = element_data
        self.tooltip = f"{element_data['name']} ({element_data['mass']})"

        # Determine color based on category
        cat = element_data["category"]
        if "alkali" in cat: self.classes = "alkali"
        elif "noble" in cat: self.classes = "noble"
        elif "halogen" in cat: self.classes = "halogen"
        elif "transition" in cat: self.classes = "transition"
        elif "lanthanide" in cat: self.classes = "lanthanide"
        elif "actinide" in cat: self.classes = "actinide"
        else: self.classes = "other"

class ChemistryLabTab(Container):
    """A TUI tab for the Chemistry Lab (Periodic Table & Calculator)."""

    CSS = """
    #periodic-table {
        layout: grid;
        grid-size: 18 10;
        grid-gutter: 1;
        padding: 1;
        width: 100%;
        height: 60%;
        border: solid green;
    }

    ElementButton {
        width: 100%;
        height: 100%;
        min-width: 3;
        content-align: center middle;
    }

    .alkali { background: #ff6b6b; }
    .noble { background: #51cf66; }
    .transition { background: #339af0; }
    .lanthanide { background: #fcc419; }
    .actinide { background: #ff922b; }
    .other { background: #adb5bd; }

    #chem-details-pane {
        width: 100%;
        height: 20%;
        border: solid blue;
        padding: 1;
        margin-top: 1;
    }

    #chem-calculator-pane {
        width: 100%;
        height: 20%;
        border: solid yellow;
        padding: 1;
        margin-top: 1;
    }

    .chem-info-label {
        width: 1fr;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = ChemistryLabManager()
        self.selected_element = None

    def compose(self) -> ComposeResult:
        yield Label("[bold]Chemistry Lab - Periodic Table[/bold]", classes="welcome-text")

        # Periodic Table Grid
        with Container(id="periodic-table"):
            # We need to place elements in correct grid positions (1-18 columns, 1-7+ rows)
            # This is tricky because the grid layout in Textual fills sequentially or needs explicit row/col spanning?
            # Standard Grid layout fills cells. We can use placeholders for empty spaces.

            # Simple approach: Create a list of 18x10 widgets, mostly placeholders (Static("")),
            # and insert ElementButtons where appropriate.

            # Map (period, group) to element
            grid_map = {}
            for num, data in ELEMENTS.items():
                p = data["period"]
                g = data["group"]
                # Lanthanides/Actinides logic:
                # La-Lu (57-71) are period 6, technically group 3 spot, but usually shown below.
                # Ac-Lr (89-103) are period 7, group 3 spot.

                # Let's use a standard wide layout.
                # Periods 1-7. Lanthanides at row 8, Actinides at row 9.

                row = p
                col = g

                if 57 <= num <= 71:
                    row = 8
                    col = num - 57 + 4 # Shift to center roughly
                elif 89 <= num <= 103:
                    row = 9
                    col = num - 89 + 4

                grid_map[(row, col)] = data

            for r in range(1, 11): # Rows 1 to 10
                for c in range(1, 19): # Cols 1 to 18
                    if (r, c) in grid_map:
                        data = grid_map[(r, c)]
                        yield ElementButton(data, id=f"elem-{data['symbol']}")
                    else:
                        yield Static("", classes="empty-cell")

        # Details Pane
        with Vertical(id="chem-details-pane"):
            yield Label("[bold]Element Details[/bold]")
            with Horizontal():
                yield Label("Symbol: -", id="chem-detail-symbol", classes="chem-info-label")
                yield Label("Name: -", id="chem-detail-name", classes="chem-info-label")
                yield Label("Number: -", id="chem-detail-number", classes="chem-info-label")
                yield Label("Mass: -", id="chem-detail-mass", classes="chem-info-label")
                yield Label("Category: -", id="chem-detail-category", classes="chem-info-label")

        # Calculator Pane
        with Vertical(id="chem-calculator-pane"):
            yield Label("[bold]Molar Mass Calculator[/bold]")
            with Horizontal():
                yield Input(placeholder="Enter formula (e.g. H2O, C6H12O6)...", id="chem-calc-input")
                yield Button("Calculate", id="chem-calc-btn", variant="primary")
            yield Label("Result: -", id="chem-calc-result")

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if isinstance(event.button, ElementButton):
            self.show_element_details(event.button.element_data)
        elif event.button.id == "chem-calc-btn":
            self.calculate_mass()

    def show_element_details(self, data: dict) -> None:
        self.selected_element = data
        self.query_one("#chem-detail-symbol", Label).update(f"Symbol: [bold]{data['symbol']}[/bold]")
        self.query_one("#chem-detail-name", Label).update(f"Name: {data['name']}")
        # We stored atomic_number in map key but not in value by default in ELEMENTS dict,
        # but Manager adds it. Here we have raw dict.
        # Let's find number from ELEMENTS (inefficient but fine for small set)
        num = next((k for k, v in ELEMENTS.items() if v == data), "?")

        self.query_one("#chem-detail-number", Label).update(f"Number: {num}")
        self.query_one("#chem-detail-mass", Label).update(f"Mass: {data['mass']}")
        self.query_one("#chem-detail-category", Label).update(f"Category: {data['category']}")

    def calculate_mass(self) -> None:
        formula = self.query_one("#chem-calc-input", Input).value
        if not formula:
            return

        result = self.manager.calculate_molar_mass(formula)
        label = self.query_one("#chem-calc-result", Label)

        if isinstance(result, str): # Error
            label.update(f"Result: [red]{result}[/red]")
        else:
            label.update(f"Result: [green]{result:.4f} g/mol[/green]")
