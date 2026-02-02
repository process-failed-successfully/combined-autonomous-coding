"""
Color Lab
=========

Utilities for WCAG contrast checking, color palette generation,
blindness simulation, and format conversion.
"""

import sys
import colorsys
import math
from typing import List, Tuple, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

console = Console()

class Color:
    """Represents a color and provides conversion/utility methods."""

    def __init__(self, value: str):
        self.r, self.g, self.b = self._parse(value)

    def _parse(self, value: str) -> Tuple[int, int, int]:
        """Parses hex or rgb string to (r, g, b) tuple."""
        value = value.strip().lower()
        if value.startswith("#"):
            value = value.lstrip("#")
            if len(value) == 3:
                value = "".join([c*2 for c in value])
            if len(value) != 6:
                raise ValueError(f"Invalid hex color: #{value}")
            return tuple(int(value[i:i+2], 16) for i in (0, 2, 4)) # type: ignore
        elif value.startswith("rgb"):
            # extremely basic rgb parsing
            parts = value.replace("rgb(", "").replace(")", "").split(",")
            if len(parts) != 3:
                raise ValueError("Invalid RGB format")
            return tuple(int(p.strip()) for p in parts) # type: ignore
        else:
            # try interpreting as hex without hash
            try:
                if len(value) == 6:
                    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4)) # type: ignore
            except ValueError:
                pass
            raise ValueError(f"Unknown color format: {value}")

    @property
    def hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    @property
    def rgb(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    @property
    def hsl(self) -> Tuple[float, float, float]:
        # colorsys uses 0-1 for RGB, and returns 0-1 for HSL
        h, l, s = colorsys.rgb_to_hls(self.r/255, self.g/255, self.b/255)
        return (h * 360, s * 100, l * 100)

    @property
    def luminance(self) -> float:
        """Calculates relative luminance (WCAG 2.x)."""
        def adjust(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * adjust(self.r) + 0.7152 * adjust(self.g) + 0.0722 * adjust(self.b)

    def contrast_ratio(self, other: 'Color') -> float:
        """Calculates contrast ratio with another color (1 to 21)."""
        l1 = self.luminance
        l2 = other.luminance
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    def simulate_blindness(self, type: str) -> 'Color':
        """
        Simulates color blindness.
        Using the Brettel et al. (1997) algorithm approximations.
        """
        # Linearize RGB
        def remove_gamma(c):
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

        r = remove_gamma(self.r / 255.0)
        g = remove_gamma(self.g / 255.0)
        b = remove_gamma(self.b / 255.0)

        # Matrices from online resources adapting Brettel et al / Viénot et al
        if type == "protanopia": # Red-blind
            # Protanopia projection
            # 0.567, 0.433, 0
            # 0.558, 0.442, 0
            # 0, 0.242, 0.758
            nr = 0.567 * r + 0.433 * g + 0.0 * b
            ng = 0.558 * r + 0.442 * g + 0.0 * b
            nb = 0.0 * r + 0.242 * g + 0.758 * b
        elif type == "deuteranopia": # Green-blind
            # Deuteranopia projection
            # 0.625, 0.375, 0
            # 0.7, 0.3, 0
            # 0, 0.3, 0.7
            nr = 0.625 * r + 0.375 * g + 0.0 * b
            ng = 0.7 * r + 0.3 * g + 0.0 * b
            nb = 0.0 * r + 0.3 * g + 0.7 * b
        elif type == "tritanopia": # Blue-blind
            # Tritanopia projection
            # 0.95, 0.05, 0
            # 0, 0.433, 0.567
            # 0, 0.475, 0.525
            nr = 0.95 * r + 0.05 * g + 0.0 * b
            ng = 0.0 * r + 0.433 * g + 0.567 * b
            nb = 0.0 * r + 0.475 * g + 0.525 * b
        else:
            return self

        # Apply Gamma
        def apply_gamma(c):
            return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055

        # Clamp and convert back
        fr = min(255, max(0, int(apply_gamma(nr) * 255)))
        fg = min(255, max(0, int(apply_gamma(ng) * 255)))
        fb = min(255, max(0, int(apply_gamma(nb) * 255)))

        return Color(f"rgb({fr},{fg},{fb})")

    def palette(self, type: str) -> List['Color']:
        """Generates a palette based on this color."""
        h, s, l = self.hsl
        # H is 0-360, S, L are 0-100

        # Helper to create Color from HSL
        def from_hsl(h, s, l):
            h = h % 360
            r, g, b = colorsys.hls_to_rgb(h/360, l/100, s/100)
            return Color(f"rgb({int(r*255)},{int(g*255)},{int(b*255)})")

        if type == "complementary":
            return [self, from_hsl(h + 180, s, l)]
        elif type == "analogous":
            return [
                from_hsl(h - 30, s, l),
                self,
                from_hsl(h + 30, s, l)
            ]
        elif type == "triadic":
            return [
                self,
                from_hsl(h + 120, s, l),
                from_hsl(h + 240, s, l)
            ]
        elif type == "tetradic":
            return [
                self,
                from_hsl(h + 90, s, l),
                from_hsl(h + 180, s, l),
                from_hsl(h + 270, s, l)
            ]
        elif type == "monochromatic":
            return [
                from_hsl(h, s, max(0, l - 30)),
                from_hsl(h, s, max(0, l - 15)),
                self,
                from_hsl(h, s, min(100, l + 15)),
                from_hsl(h, s, min(100, l + 30)),
            ]
        return [self]


def _print_color_swatch(color: Color, label: str = ""):
    """Prints a color swatch using rich."""
    hex_val = color.hex
    rgb_val = color.rgb

    # Determine text color based on background luminance for readability
    text_color = "black" if color.luminance > 0.5 else "white"

    style = f"bold {text_color} on {hex_val}"
    console.print(f"[{style}] {label:<15} {hex_val} | RGB{rgb_val} [/{style}]")


def run_color_lab_logic(action: str, **kwargs):
    """Entry point for color lab logic."""
    try:
        if action == "check":
            c1 = Color(kwargs["color1"])
            c2 = Color(kwargs["color2"])
            ratio = c1.contrast_ratio(c2)

            console.print(Panel(f"[bold]Contrast Check[/bold]"))
            _print_color_swatch(c1, "Foreground")
            _print_color_swatch(c2, "Background")

            console.print(f"\nContrast Ratio: [bold cyan]{ratio:.2f}:1[/bold cyan]")

            # WCAG Ratings
            def grade(r, size="normal"):
                aa = 4.5 if size == "normal" else 3.0
                aaa = 7.0 if size == "normal" else 4.5
                if r >= aaa: return "[green]AAA (Pass)[/green]"
                if r >= aa: return "[green]AA (Pass)[/green]"
                return "[red]Fail[/red]"

            table = Table(title="WCAG 2.1 Compliance")
            table.add_column("Text Size", style="cyan")
            table.add_column("Level AA", style="magenta")
            table.add_column("Level AAA", style="magenta")

            table.add_row("Normal Text", grade(ratio, "normal"), grade(ratio, "normal",))
            table.add_row("Large Text (18pt+)", grade(ratio, "large"), grade(ratio, "large"))

            console.print(table)

        elif action == "palette":
            base = Color(kwargs["base"])
            algo = kwargs.get("algorithm", "complementary")
            palette = base.palette(algo)

            console.print(Panel(f"[bold]Palette: {algo.capitalize()}[/bold]"))
            for i, c in enumerate(palette):
                marker = "(Base)" if c.hex == base.hex else ""
                _print_color_swatch(c, f"Color {i+1} {marker}")

        elif action == "simulate":
            c = Color(kwargs["color"])
            console.print(Panel(f"[bold]Color Blindness Simulation[/bold]"))

            _print_color_swatch(c, "Original")

            for type in ["protanopia", "deuteranopia", "tritanopia"]:
                sim = c.simulate_blindness(type)
                _print_color_swatch(sim, type.capitalize())

        elif action == "convert":
            c = Color(kwargs["color"])
            console.print(Panel(f"[bold]Color Conversion[/bold]"))
            _print_color_swatch(c, "Swatch")

            table = Table()
            table.add_column("Format", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("HEX", c.hex)
            table.add_row("RGB", str(c.rgb))
            h, s, l = c.hsl
            table.add_row("HSL", f"hsl({h:.1f}, {s:.1f}%, {l:.1f}%)")

            console.print(table)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error: {e}[/red]")
        sys.exit(1)
