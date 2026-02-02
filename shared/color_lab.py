import colorsys

class Color:
    def __init__(self, hex_code: str):
        self.hex = hex_code.lstrip('#').lower()
        if len(self.hex) == 3:
            self.hex = ''.join(c*2 for c in self.hex)
        if len(self.hex) != 6:
            raise ValueError(f"Invalid hex color: {hex_code}")

        self.r = int(self.hex[0:2], 16)
        self.g = int(self.hex[2:4], 16)
        self.b = int(self.hex[4:6], 16)

    @property
    def rgb(self):
        return (self.r, self.g, self.b)

    @property
    def hsl(self):
        # colorsys works with 0-1, so divide by 255
        h, l, s = colorsys.rgb_to_hls(self.r/255.0, self.g/255.0, self.b/255.0)
        return (h * 360, s * 100, l * 100) # Returns H(0-360), S(0-100), L(0-100)

    @property
    def luminance(self):
        # https://www.w3.org/TR/WCAG20/#relativeluminancedef
        def adjust(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * adjust(self.r) + 0.7152 * adjust(self.g) + 0.0722 * adjust(self.b)

    @staticmethod
    def from_hsl(h, s, l):
        # h: 0-360, s: 0-100, l: 0-100
        r, g, b = colorsys.hls_to_rgb(h/360.0, l/100.0, s/100.0)
        return Color(f"#{round(r*255):02x}{round(g*255):02x}{round(b*255):02x}")

class ColorLabManager:
    def check_contrast(self, hex1: str, hex2: str):
        c1 = Color(hex1)
        c2 = Color(hex2)

        l1 = c1.luminance
        l2 = c2.luminance

        if l1 > l2:
            ratio = (l1 + 0.05) / (l2 + 0.05)
        else:
            ratio = (l2 + 0.05) / (l1 + 0.05)

        return {
            "ratio": round(ratio, 2),
            "aa": "PASS" if ratio >= 4.5 else "FAIL",
            "aaa": "PASS" if ratio >= 7.0 else "FAIL",
            "aa_large": "PASS" if ratio >= 3.0 else "FAIL"
        }

    def generate_palette(self, hex_color: str, type: str):
        c = Color(hex_color)
        h, s, l = c.hsl
        palette = []

        if type == "complementary":
            palette.append(c)
            palette.append(Color.from_hsl((h + 180) % 360, s, l))

        elif type == "analogous":
            palette.append(Color.from_hsl((h - 30) % 360, s, l))
            palette.append(c)
            palette.append(Color.from_hsl((h + 30) % 360, s, l))

        elif type == "triadic":
            palette.append(c)
            palette.append(Color.from_hsl((h + 120) % 360, s, l))
            palette.append(Color.from_hsl((h + 240) % 360, s, l))

        elif type == "monochromatic":
            # Generate tints and shades
            palette.append(Color.from_hsl(h, s, max(0, l - 30)))
            palette.append(Color.from_hsl(h, s, max(0, l - 15)))
            palette.append(c)
            palette.append(Color.from_hsl(h, s, min(100, l + 15)))
            palette.append(Color.from_hsl(h, s, min(100, l + 30)))

        return [f"#{p.hex}" for p in palette]

    def simulate_blindness(self, hex_color: str, type: str):
        # Simple LMS matrix approximation
        # Source: https://github.com/mape/color-blindness-simulation
        c = Color(hex_color)
        r, g, b = c.r, c.g, c.b

        # Scaling for matrix math
        # Actually, let's use a simplified pre-calculated matrix approach for RGB
        # These are approximations.

        if type == "protanopia":
            # Red-blind
            nr = 0.567 * r + 0.433 * g + 0.0 * b
            ng = 0.558 * r + 0.442 * g + 0.0 * b
            nb = 0.0 * r + 0.242 * g + 0.758 * b
        elif type == "deuteranopia":
            # Green-blind
            nr = 0.625 * r + 0.375 * g + 0.0 * b
            ng = 0.7 * r + 0.3 * g + 0.0 * b
            nb = 0.0 * r + 0.3 * g + 0.7 * b
        elif type == "tritanopia":
            # Blue-blind
            nr = 0.95 * r + 0.05 * g + 0.0 * b
            ng = 0.0 * r + 0.433 * g + 0.567 * b
            nb = 0.0 * r + 0.475 * g + 0.525 * b
        elif type == "achromatopsia":
             # Monochromacy
             gray = 0.299 * r + 0.587 * g + 0.114 * b
             nr, ng, nb = gray, gray, gray
        else:
            return hex_color

        # Clamp
        nr = min(255, max(0, int(nr)))
        ng = min(255, max(0, int(ng)))
        nb = min(255, max(0, int(nb)))

        return f"#{nr:02x}{ng:02x}{nb:02x}"

    def convert(self, hex_color: str):
        c = Color(hex_color)
        h, s, l = c.hsl
        return {
            "hex": f"#{c.hex}",
            "rgb": f"rgb({c.r}, {c.g}, {c.b})",
            "hsl": f"hsl({int(h)}, {int(s)}%, {int(l)}%)"
        }
