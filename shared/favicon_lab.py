import os
import sys
import argparse
from pathlib import Path

class FaviconManager:
    def __init__(self):
        try:
            from PIL import Image
            self.Image = Image
            self.pillow_available = True
        except ImportError:
            self.Image = None
            self.pillow_available = False

    def check_dependency(self):
        if not self.pillow_available:
            return False, "Pillow is not installed. Please install it with 'pip install Pillow'."
        return True, ""

    def generate(self, input_path: str, output_dir: str):
        ok, msg = self.check_dependency()
        if not ok:
            return False, msg

        in_p = Path(input_path)
        out_d = Path(output_dir)

        if not in_p.exists():
            return False, f"Input image not found: {input_path}"

        try:
            out_d.mkdir(parents=True, exist_ok=True)
            with self.Image.open(in_p) as img:
                # Need a base image large enough for standard sizes, e.g. 512x512
                # We'll work on a copy to avoid mutating the original
                base_img = img.copy().convert("RGBA")

                # Generate favicon.ico (multi-size)
                # Pillow requires the image to be at least as large as the largest requested size
                # So we resize to 48x48 first for the ICO, or just use a 256x256 base
                ico_sizes = [(16, 16), (32, 32), (48, 48)]
                ico_base = base_img.resize((48, 48), self.Image.Resampling.LANCZOS)
                ico_base.save(out_d / "favicon.ico", format="ICO", sizes=ico_sizes)

                # Generate PNGs
                sizes = {
                    "favicon-16x16.png": (16, 16),
                    "favicon-32x32.png": (32, 32),
                    "apple-touch-icon.png": (180, 180),
                    "android-chrome-192x192.png": (192, 192),
                    "android-chrome-512x512.png": (512, 512)
                }

                for filename, size in sizes.items():
                    resized = base_img.resize(size, self.Image.Resampling.LANCZOS)
                    resized.save(out_d / filename, format="PNG")

            # Generate site.webmanifest
            manifest_content = """{
    "name": "",
    "short_name": "",
    "icons": [
        {
            "src": "/android-chrome-192x192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/android-chrome-512x512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ],
    "theme_color": "#ffffff",
    "background_color": "#ffffff",
    "display": "standalone"
}"""
            (out_d / "site.webmanifest").write_text(manifest_content)

            return True, f"Successfully generated favicons in {output_dir}"

        except Exception as e:
            return False, f"Error generating favicons: {e}"

    def get_html(self):
        return """<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="manifest" href="/site.webmanifest">"""

def run_favicon_lab_logic(args):
    action = getattr(args, "action", None)

    if action == "html":
        manager = FaviconManager()
        print(manager.get_html())
        return True

    if action == "generate":
        if not getattr(args, "input", None):
            print("Error: --input is required for generate action.", file=sys.stderr)
            return False

        output_dir = getattr(args, "output", ".")
        if not output_dir:
            output_dir = "."

        manager = FaviconManager()
        success, msg = manager.generate(args.input, output_dir)
        if success:
            print(msg)
            return True
        else:
            print(f"Error: {msg}", file=sys.stderr)
            return False

    print("Error: Unknown action.", file=sys.stderr)
    return False
