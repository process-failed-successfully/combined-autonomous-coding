from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Label, Button, Input, Select, TabbedContent, TabPane, RichLog
from textual import on
from shared.color_lab import Color


class ColorLabTab(Container):
    """Tab for Color Lab operations."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Color Lab[/bold]", classes="welcome-text")

            with TabbedContent(id="cl-tabs"):
                with TabPane("Contrast", id="cl-tab-contrast"):
                    with Vertical(classes="stat-box"):
                        yield Label("Foreground Color:")
                        yield Input(placeholder="#FFFFFF or rgb(255,255,255)", id="cl-contrast-fg", value="#FFFFFF")
                        yield Label("Background Color:")
                        yield Input(placeholder="#000000 or rgb(0,0,0)", id="cl-contrast-bg", value="#000000")
                        yield Button("Check Contrast", id="btn-cl-contrast", variant="primary")
                        yield RichLog(id="cl-contrast-result", wrap=True, highlight=False, markup=True)

                with TabPane("Palette", id="cl-tab-palette"):
                    with Vertical(classes="stat-box"):
                        yield Label("Base Color:")
                        yield Input(placeholder="#3498db", id="cl-palette-base", value="#3498db")
                        yield Label("Algorithm:")
                        yield Select.from_values(
                            ["complementary", "analogous", "triadic", "tetradic", "monochromatic"],
                            id="cl-palette-algo", value="complementary"
                        )
                        yield Button("Generate Palette", id="btn-cl-palette", variant="primary")
                        yield RichLog(id="cl-palette-result", wrap=True, highlight=False, markup=True)

                with TabPane("Blindness", id="cl-tab-blindness"):
                    with Vertical(classes="stat-box"):
                        yield Label("Color to Simulate:")
                        yield Input(placeholder="#e74c3c", id="cl-blind-color", value="#e74c3c")
                        yield Button("Simulate", id="btn-cl-blind", variant="primary")
                        yield RichLog(id="cl-blind-result", wrap=True, highlight=False, markup=True)

                with TabPane("Mix", id="cl-tab-mix"):
                    with Vertical(classes="stat-box"):
                        yield Label("Color 1:")
                        yield Input(placeholder="#000000", id="cl-mix-c1", value="#000000")
                        yield Label("Color 2:")
                        yield Input(placeholder="#FFFFFF", id="cl-mix-c2", value="#FFFFFF")
                        yield Label("Weight (0.0 to 1.0):")
                        yield Input(placeholder="0.5", id="cl-mix-weight", value="0.5")
                        yield Button("Mix Colors", id="btn-cl-mix", variant="primary")
                        yield RichLog(id="cl-mix-result", wrap=True, highlight=False, markup=True)

                with TabPane("Gradient", id="cl-tab-gradient"):
                    with Vertical(classes="stat-box"):
                        yield Label("Start Color:")
                        yield Input(placeholder="#ff0000", id="cl-grad-c1", value="#ff0000")
                        yield Label("End Color:")
                        yield Input(placeholder="#0000ff", id="cl-grad-c2", value="#0000ff")
                        yield Label("Steps:")
                        yield Input(placeholder="5", id="cl-grad-steps", value="5")
                        yield Button("Generate Gradient", id="btn-cl-grad", variant="primary")
                        yield RichLog(id="cl-grad-result", wrap=True, highlight=False, markup=True)

                with TabPane("Converter", id="cl-tab-converter"):
                    with Vertical(classes="stat-box"):
                        yield Label("Color to Convert:")
                        yield Input(placeholder="#2ecc71", id="cl-convert-color", value="#2ecc71")
                        yield Button("Convert", id="btn-cl-convert", variant="primary")
                        yield RichLog(id="cl-convert-result", wrap=True, highlight=False, markup=True)

    @on(Button.Pressed, "#btn-cl-contrast")
    def on_contrast(self) -> None:
        fg_str = self.query_one("#cl-contrast-fg", Input).value
        bg_str = self.query_one("#cl-contrast-bg", Input).value
        log = self.query_one("#cl-contrast-result", RichLog)
        log.clear()

        try:
            fg = Color(fg_str)
            bg = Color(bg_str)
            ratio = fg.contrast_ratio(bg)

            # Swatches
            log.write(f"Foreground: [bold {fg.hex} on {bg.hex}] Text Preview [/] ({fg.hex})")
            log.write(f"Background: [bold {bg.hex} on {fg.hex}] Text Preview [/] ({bg.hex})")
            log.write(f"\nContrast Ratio: [bold cyan]{ratio:.2f}:1[/bold cyan]")

            # WCAG Ratings
            def grade(r, size="normal"):
                aa = 4.5 if size == "normal" else 3.0
                aaa = 7.0 if size == "normal" else 4.5
                if r >= aaa:
                    return "[green]AAA (Pass)[/green]"
                if r >= aa:
                    return "[green]AA (Pass)[/green]"
                return "[red]Fail[/red]"

            log.write(f"Normal Text: {grade(ratio, 'normal')}")
            log.write(f"Large Text:  {grade(ratio, 'large')}")

        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-cl-palette")
    def on_palette(self) -> None:
        base_str = self.query_one("#cl-palette-base", Input).value
        algo = self.query_one("#cl-palette-algo", Select).value or "complementary"
        log = self.query_one("#cl-palette-result", RichLog)
        log.clear()

        try:
            base = Color(base_str)
            palette = base.palette(algo)

            log.write(f"[bold]Palette: {algo.capitalize()}[/bold]")
            for i, c in enumerate(palette):
                marker = "(Base)" if c.hex == base.hex else ""
                # Determine text color for readability on swatch
                text_col = "black" if c.luminance > 0.5 else "white"
                log.write(f"[{text_col} on {c.hex}] {c.hex} {marker} [/{text_col} on {c.hex}]")

        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-cl-blind")
    def on_blindness(self) -> None:
        col_str = self.query_one("#cl-blind-color", Input).value
        log = self.query_one("#cl-blind-result", RichLog)
        log.clear()

        try:
            c = Color(col_str)

            def render_swatch(col, label):
                text_col = "black" if col.luminance > 0.5 else "white"
                log.write(f"[{text_col} on {col.hex}] {label:<15} {col.hex} [/{text_col} on {col.hex}]")

            render_swatch(c, "Original")
            log.write("")  # Spacer

            for type in ["protanopia", "deuteranopia", "tritanopia"]:
                sim = c.simulate_blindness(type)
                render_swatch(sim, type.capitalize())

        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-cl-mix")
    def on_mix(self) -> None:
        c1_str = self.query_one("#cl-mix-c1", Input).value
        c2_str = self.query_one("#cl-mix-c2", Input).value
        weight_str = self.query_one("#cl-mix-weight", Input).value
        log = self.query_one("#cl-mix-result", RichLog)
        log.clear()

        try:
            c1 = Color(c1_str)
            c2 = Color(c2_str)
            weight = float(weight_str)
            result = c1.mix(c2, weight)

            def render_swatch(col, label):
                text_col = "black" if col.luminance > 0.5 else "white"
                log.write(f"[{text_col} on {col.hex}] {label:<15} {col.hex} [/{text_col} on {col.hex}]")

            render_swatch(c1, "Color 1")
            render_swatch(c2, "Color 2")
            log.write("")  # Spacer
            render_swatch(result, f"Result ({int(weight*100):.0f}%)")

        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-cl-grad")
    def on_gradient(self) -> None:
        c1_str = self.query_one("#cl-grad-c1", Input).value
        c2_str = self.query_one("#cl-grad-c2", Input).value
        steps_str = self.query_one("#cl-grad-steps", Input).value
        log = self.query_one("#cl-grad-result", RichLog)
        log.clear()

        try:
            c1 = Color(c1_str)
            c2 = Color(c2_str)
            steps = int(steps_str)
            colors = c1.gradient(c2, steps)

            def render_swatch(col, label):
                text_col = "black" if col.luminance > 0.5 else "white"
                log.write(f"[{text_col} on {col.hex}] {label:<15} {col.hex} [/{text_col} on {col.hex}]")

            log.write(f"[bold]Gradient ({steps} steps)[/bold]")
            for i, c in enumerate(colors):
                render_swatch(c, f"Step {i+1}")

        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-cl-convert")
    def on_convert(self) -> None:
        col_str = self.query_one("#cl-convert-color", Input).value
        log = self.query_one("#cl-convert-result", RichLog)
        log.clear()

        try:
            c = Color(col_str)
            text_col = "black" if c.luminance > 0.5 else "white"
            log.write(f"[{text_col} on {c.hex}]   Swatch   [/{text_col} on {c.hex}]")

            log.write(f"[bold]HEX:[/bold]  {c.hex}")
            log.write(f"[bold]RGB:[/bold]  {c.rgb}")

            h, s, light = c.hsl
            log.write(f"[bold]HSL:[/bold]  hsl({h:.1f}, {s:.1f}%, {light:.1f}%)")

            cmyk = c.cmyk
            log.write(f"[bold]CMYK:[/bold] cmyk({cmyk[0]}%, {cmyk[1]}%, {cmyk[2]}%, {cmyk[3]}%)")

        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")
