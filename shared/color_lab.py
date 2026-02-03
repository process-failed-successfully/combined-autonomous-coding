import re
import math
from typing import Tuple, Dict, Any, List, Optional
import sys

class ColorLabManager:
    """Manages color operations: conversion, contrast, palette, and blindness simulation."""

    def parse_color(self, color_input: str) -> Tuple[int, int, int]:
        """Parses a color string into an RGB tuple (0-255)."""
        color_input = color_input.strip().lower()

        # Hex
        clean_input = color_input
        if color_input.startswith("#"):
            clean_input = color_input[1:]

        # Check if it is a valid hex string (len 3 or 6, all hex digits)
        if all(c in "0123456789abcdef" for c in clean_input):
            if len(clean_input) == 3:
                clean_input = "".join([c * 2 for c in clean_input])
            if len(clean_input) == 6:
                try:
                    return (int(clean_input[0:2], 16), int(clean_input[2:4], 16), int(clean_input[4:6], 16))
                except ValueError:
                    pass

        # RGB function or CSV
        if color_input.startswith("rgb"):
            match = re.search(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", color_input)
            if match:
                return (int(match.group(1)), int(match.group(2)), int(match.group(3)))

        # Simple CSV: 255,0,0
        if "," in color_input and "hsl" not in color_input:
            parts = color_input.split(",")
            if len(parts) == 3:
                try:
                    return (int(parts[0]), int(parts[1]), int(parts[2]))
                except ValueError:
                    pass

        # HSL
        if color_input.startswith("hsl"):
            match = re.search(r"hsl\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)", color_input)
            if match:
                h, s, l = int(match.group(1)), int(match.group(2)), int(match.group(3))
                return self._hsl_to_rgb(h, s, l)

        raise ValueError(f"Unsupported color format: {color_input}")

    def convert_format(self, rgb: Tuple[int, int, int]) -> Dict[str, str]:
        """Returns Hex, RGB, and HSL representations."""
        r, g, b = rgb
        hex_val = f"#{r:02x}{g:02x}{b:02x}"
        rgb_val = f"rgb({r}, {g}, {b})"
        h, s, l = self._rgb_to_hsl(r, g, b)
        hsl_val = f"hsl({h}, {s}%, {l}%)"

        return {
            "hex": hex_val,
            "rgb": rgb_val,
            "hsl": hsl_val
        }

    def calculate_contrast(self, color1: str, color2: str) -> Dict[str, Any]:
        """Calculates contrast ratio and WCAG compliance."""
        c1 = self.parse_color(color1)
        c2 = self.parse_color(color2)

        lum1 = self._get_relative_luminance(c1)
        lum2 = self._get_relative_luminance(c2)

        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)

        ratio = (lighter + 0.05) / (darker + 0.05)
        ratio = round(ratio, 2)

        aa_large = ratio >= 3.0
        aa_normal = ratio >= 4.5
        aaa_large = ratio >= 4.5
        aaa_normal = ratio >= 7.0

        return {
            "ratio": ratio,
            "AA": "Pass" if aa_normal else ("Pass (Large Text)" if aa_large else "Fail"),
            "AAA": "Pass" if aaa_normal else ("Pass (Large Text)" if aaa_large else "Fail"),
            "color1": self.convert_format(c1)["hex"],
            "color2": self.convert_format(c2)["hex"]
        }

    def simulate_blindness(self, color: str, blindness_type: str) -> Dict[str, str]:
        """Simulates color blindness using LMS Daltonization approach."""
        rgb = self.parse_color(color)
        r, g, b = rgb

        # Standard Transformation Matrices (Simplified approximations)
        # Based on color matrix values often found in CVD simulation libraries

        if blindness_type.lower() == "protanopia":
            # Red-blind
            # 0.567, 0.433, 0.0
            # 0.558, 0.442, 0.0
            # 0.0, 0.242, 0.758
            nr = 0.567 * r + 0.433 * g + 0.0 * b
            ng = 0.558 * r + 0.442 * g + 0.0 * b
            nb = 0.0 * r + 0.242 * g + 0.758 * b

        elif blindness_type.lower() == "deuteranopia":
            # Green-blind
            # 0.625, 0.375, 0.0
            # 0.7, 0.3, 0.0
            # 0.0, 0.3, 0.7
            nr = 0.625 * r + 0.375 * g + 0.0 * b
            ng = 0.7 * r + 0.3 * g + 0.0 * b
            nb = 0.0 * r + 0.3 * g + 0.7 * b

        elif blindness_type.lower() == "tritanopia":
            # Blue-blind
            # 0.95, 0.05, 0.0
            # 0.0, 0.433, 0.567
            # 0.0, 0.475, 0.525
            nr = 0.95 * r + 0.05 * g + 0.0 * b
            ng = 0.0 * r + 0.433 * g + 0.567 * b
            nb = 0.0 * r + 0.475 * g + 0.525 * b

        else:
            raise ValueError(f"Unknown blindness type: {blindness_type}")

        # Clamp values
        nr = min(255, max(0, int(nr)))
        ng = min(255, max(0, int(ng)))
        nb = min(255, max(0, int(nb)))

        simulated_rgb = (nr, ng, nb)
        return self.convert_format(simulated_rgb)

    def generate_palette(self, color: str, scheme: str) -> List[Dict[str, str]]:
        """Generates a color palette."""
        rgb = self.parse_color(color)
        h, s, l = self._rgb_to_hsl(*rgb)

        colors = []

        if scheme == "complementary":
            # Seed + Opposite
            colors.append((h, s, l))
            colors.append(((h + 180) % 360, s, l))

        elif scheme == "analogous":
            # Seed + +/- 30 degrees
            colors.append(((h - 30) % 360, s, l))
            colors.append((h, s, l))
            colors.append(((h + 30) % 360, s, l))

        elif scheme == "triadic":
            # Seed + 120 + 240
            colors.append((h, s, l))
            colors.append(((h + 120) % 360, s, l))
            colors.append(((h + 240) % 360, s, l))

        elif scheme == "monochromatic":
            # Variations in lightness
            colors.append((h, s, max(0, l - 20)))
            colors.append((h, s, l))
            colors.append((h, s, min(100, l + 20)))

        else:
            raise ValueError(f"Unknown scheme: {scheme}")

        results = []
        for ch, cs, cl in colors:
            crgb = self._hsl_to_rgb(ch, cs, cl)
            results.append(self.convert_format(crgb))

        return results

    # --- Private Helpers ---

    def _get_relative_luminance(self, rgb: Tuple[int, int, int]) -> float:
        """Calculates relative luminance for WCAG contrast."""
        r, g, b = [x / 255.0 for x in rgb]

        def linearize(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        R = linearize(r)
        G = linearize(g)
        B = linearize(b)

        return 0.2126 * R + 0.7152 * G + 0.0722 * B

    def _rgb_to_hsl(self, r: int, g: int, b: int) -> Tuple[int, int, int]:
        r, g, b = r / 255.0, g / 255.0, b / 255.0

        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx - mn

        h = 0
        s = 0
        l = (mx + mn) / 2

        if df == 0:
            h = 0
            s = 0
        else:
            s = df / (2 - mx - mn) if l > 0.5 else df / (mx + mn)

            if mx == r:
                h = (g - b) / df + (6 if g < b else 0)
            elif mx == g:
                h = (b - r) / df + 2
            elif mx == b:
                h = (r - g) / df + 4
            h /= 6

        return round(h * 360), round(s * 100), round(l * 100)

    def _hsl_to_rgb(self, h: int, s: int, l: int) -> Tuple[int, int, int]:
        h, s, l = h / 360.0, s / 100.0, l / 100.0

        if s == 0:
            r = g = b = l
        else:
            def hue_to_rgb(p, q, t):
                if t < 0: t += 1
                if t > 1: t -= 1
                if t < 1/6: return p + (q - p) * 6 * t
                if t < 1/2: return q
                if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                return p

            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q

            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)

        return round(r * 255), round(g * 255), round(b * 255)


def run_color_lab_logic(args) -> bool:
    """CLI logic for Color Lab."""
    manager = ColorLabManager()

    try:
        if args.action == "convert":
            if not args.color:
                print("Error: --color required.")
                return False
            result = manager.convert_format(manager.parse_color(args.color))
            print("--- Color Conversion ---")
            print(f"Hex: {result['hex']}")
            print(f"RGB: {result['rgb']}")
            print(f"HSL: {result['hsl']}")

        elif args.action == "contrast":
            if not args.color1 or not args.color2:
                print("Error: --color1 and --color2 required.")
                return False
            result = manager.calculate_contrast(args.color1, args.color2)
            print("--- Contrast Check ---")
            print(f"Colors: {result['color1']} vs {result['color2']}")
            print(f"Ratio:  {result['ratio']}:1")
            print(f"AA:     {result['AA']}")
            print(f"AAA:    {result['AAA']}")

        elif args.action == "blindness":
            if not args.color or not args.type:
                print("Error: --color and --type required.")
                return False
            result = manager.simulate_blindness(args.color, args.type)
            print(f"--- Blindness Simulation ({args.type}) ---")
            print(f"Original:  {args.color}")
            print(f"Simulated: {result['hex']} | {result['rgb']}")

        elif args.action == "palette":
            if not args.color or not args.scheme:
                print("Error: --color and --scheme required.")
                return False
            palette = manager.generate_palette(args.color, args.scheme)
            print(f"--- Palette Generation ({args.scheme}) ---")
            for i, c in enumerate(palette):
                print(f"Color {i+1}: {c['hex']} | {c['rgb']} | {c['hsl']}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False
