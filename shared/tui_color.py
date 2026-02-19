from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Input, Button, DataTable, Static, TabbedContent, TabPane
from textual import on
from shared.color_lab import Color
from rich.text import Text
from rich.panel import Panel
from rich.style import Style

class ColorLabTab(Container):
    """Tab for interactive color experimentation."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.current_color = Color("#000000")
        self.bg_color = Color("#FFFFFF")

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]Color Lab[/bold]", classes="welcome-text")

            # Input Section
            with Container(classes="stat-box"):
                yield Label("Enter Color (Hex, RGB):")
                with Horizontal():
                    yield Input(placeholder="#000000 or rgb(0,0,0)", id="color-input")
                    yield Button("Analyze", id="btn-analyze-color", variant="primary")

            # Main Info & Swatch
            with Horizontal(classes="stat-box"):
                # Swatch
                with Vertical(id="color-swatch-container"):
                    yield Label("Swatch")
                    yield Static(id="color-swatch", classes="color-swatch-box")

                # Conversion Table
                with Vertical():
                    yield Label("Conversions")
                    yield DataTable(id="color-conversion-table")

            with TabbedContent():
                # Palette Generator
                with TabPane("Palettes"):
                    yield Label("Harmonies")
                    with Horizontal():
                        yield Button("Complementary", id="btn-pal-comp", variant="default")
                        yield Button("Analogous", id="btn-pal-ana", variant="default")
                        yield Button("Triadic", id="btn-pal-tri", variant="default")
                        yield Button("Tetradic", id="btn-pal-tetra", variant="default")
                        yield Button("Monochromatic", id="btn-pal-mono", variant="default")

                    yield Container(id="palette-container", classes="stat-box")

                # Contrast Checker
                with TabPane("Contrast"):
                    with Horizontal(classes="stat-box"):
                        with Vertical():
                            yield Label("Foreground (Current)")
                            yield Static(id="contrast-fg-swatch", classes="mini-swatch")
                        with Vertical():
                            yield Label("Background")
                            yield Input(placeholder="#FFFFFF", id="bg-color-input", value="#FFFFFF")
                            yield Button("Update BG", id="btn-update-bg")
                            yield Static(id="contrast-bg-swatch", classes="mini-swatch")

                    yield Label("Contrast Ratio", id="contrast-ratio-lbl")
                    yield DataTable(id="wcag-table")

                # Blindness Simulator
                with TabPane("Blindness Sim"):
                    with Horizontal(id="blindness-container"):
                        # Will be populated dynamically
                        pass

    def on_mount(self) -> None:
        # Setup tables
        conv_table = self.query_one("#color-conversion-table", DataTable)
        conv_table.add_columns("Format", "Value")

        wcag_table = self.query_one("#wcag-table", DataTable)
        wcag_table.add_columns("Level", "Normal Text", "Large Text")

        # Initial Load
        self.update_color(self.current_color)

    @on(Button.Pressed, "#btn-analyze-color")
    def on_analyze(self) -> None:
        val = self.query_one("#color-input", Input).value
        if not val:
            return
        try:
            c = Color(val)
            self.update_color(c)
        except ValueError:
            self.notify("Invalid color format.", severity="error")

    @on(Input.Submitted, "#color-input")
    def on_input_submitted(self) -> None:
        self.on_analyze()

    @on(Button.Pressed, "#btn-update-bg")
    def on_update_bg(self) -> None:
        val = self.query_one("#bg-color-input", Input).value
        if not val:
            return
        try:
            c = Color(val)
            self.bg_color = c
            self.update_contrast()
        except ValueError:
            self.notify("Invalid background color.", severity="error")

    def update_color(self, color: Color) -> None:
        self.current_color = color

        # 1. Update Swatch
        swatch = self.query_one("#color-swatch", Static)
        # We use rich panel with style
        text_color = "black" if color.luminance > 0.5 else "white"
        swatch.update(Panel(Text(f"\n{color.hex}\n", justify="center", style=f"bold {text_color}"), style=f"on {color.hex}"))

        # 2. Update Conversions
        table = self.query_one("#color-conversion-table", DataTable)
        table.clear()
        table.add_row("HEX", color.hex)
        table.add_row("RGB", str(color.rgb))
        h, s, l = color.hsl
        table.add_row("HSL", f"hsl({h:.1f}, {s:.1f}%, {l:.1f}%)")
        cmyk = color.cmyk
        table.add_row("CMYK", f"cmyk({cmyk[0]}%, {cmyk[1]}%, {cmyk[2]}%, {cmyk[3]}%)")
        table.add_row("Luminance", f"{color.luminance:.4f}")

        # 3. Update Contrast (Foreground)
        fg_swatch = self.query_one("#contrast-fg-swatch", Static)
        fg_swatch.update(Panel("", style=f"on {color.hex}"))
        self.update_contrast()

        # 4. Update Blindness Sim
        self.update_blindness()

        # 5. Clear Palette (user must click generate)
        self.query_one("#palette-container", Container).remove_children()

    def update_contrast(self) -> None:
        bg_swatch = self.query_one("#contrast-bg-swatch", Static)
        bg_swatch.update(Panel("", style=f"on {self.bg_color.hex}"))

        ratio = self.current_color.contrast_ratio(self.bg_color)
        lbl = self.query_one("#contrast-ratio-lbl", Label)

        color_markup = "green" if ratio >= 4.5 else "yellow" if ratio >= 3.0 else "red"
        lbl.update(f"Contrast Ratio: [bold {color_markup}]{ratio:.2f}:1[/]")

        # Update WCAG Table
        table = self.query_one("#wcag-table", DataTable)
        table.clear()

        def grade(r, size="normal"):
            aa = 4.5 if size == "normal" else 3.0
            aaa = 7.0 if size == "normal" else 4.5
            if r >= aaa: return "[green]AAA (Pass)[/green]"
            if r >= aa: return "[green]AA (Pass)[/green]"
            return "[red]Fail[/red]"

        table.add_row("AA (Min)", grade(ratio, "normal"), grade(ratio, "large"))
        table.add_row("AAA (Enhanced)", grade(ratio, "normal"), grade(ratio, "large"))

    def update_blindness(self) -> None:
        container = self.query_one("#blindness-container", Horizontal)
        container.remove_children()

        types = ["protanopia", "deuteranopia", "tritanopia"]
        for t in types:
            sim = self.current_color.simulate_blindness(t)
            text_color = "black" if sim.luminance > 0.5 else "white"

            # Create a mini container for each
            with Vertical(classes="blindness-box"):
                container.mount(Label(t.capitalize()))
                container.mount(Static(Panel(Text(f"\n{sim.hex}\n", justify="center", style=f"{text_color}"), style=f"on {sim.hex}"), classes="mini-swatch"))

    @on(Button.Pressed)
    def on_palette_btn(self, event: Button.Pressed) -> None:
        if not event.button.id.startswith("btn-pal-"):
            return

        algo = event.button.id.replace("btn-pal-", "")
        # map short code to full name if needed, but color_lab uses simple names
        if algo == "comp": algo = "complementary"
        elif algo == "ana": algo = "analogous"
        elif algo == "tri": algo = "triadic"
        elif algo == "tetra": algo = "tetradic"
        elif algo == "mono": algo = "monochromatic"

        palette = self.current_color.palette(algo)

        container = self.query_one("#palette-container", Container)
        container.remove_children()

        # Display palette
        row = Horizontal()
        container.mount(Label(f"[bold]{algo.capitalize()} Palette[/bold]"))
        container.mount(row)

        for c in palette:
            text_color = "black" if c.luminance > 0.5 else "white"
            row.mount(Static(Panel(Text(f"\n{c.hex}\n", justify="center", style=f"{text_color}"), style=f"on {c.hex}"), classes="palette-swatch"))
