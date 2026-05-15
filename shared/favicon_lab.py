"""
Favicon Lab
===========

Utilities for generating favicons for web applications.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class FaviconManager:
    """Manages favicon generation and HTML tag creation."""

    def __init__(self):
        if not HAS_PIL:
            raise ImportError("Pillow library is not installed. Please run: pip install Pillow")

    def generate(self, input_image: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Generates standard favicon files in the output directory.

        Args:
            input_image: Path to the source image (preferably 512x512 PNG).
            output_dir: Directory to save the generated favicons.

        Returns:
            Dict with status and paths of generated files.
        """
        try:
            if not input_image.exists():
                raise FileNotFoundError(f"Input image not found: {input_image}")

            output_dir.mkdir(parents=True, exist_ok=True)
            generated_files = []

            with Image.open(input_image) as img:
                # Ensure it's in RGBA mode for transparency support
                if img.mode != "RGBA":
                    img = img.convert("RGBA")

                # Generate favicon.ico (multi-resolution: 16x16, 32x32, 48x48)
                ico_path = output_dir / "favicon.ico"
                icon_sizes = [(16, 16), (32, 32), (48, 48)]
                img_ico = img.copy()
                img_ico = img_ico.resize((48, 48), resample=Image.Resampling.LANCZOS)
                img_ico.save(ico_path, format="ICO", sizes=icon_sizes)
                generated_files.append(str(ico_path))

                # Generate Apple Touch Icon (180x180)
                # Recommended to have a solid background, but we keep transparency or flatten depending on source.
                # For simplicity, we just resize.
                apple_path = output_dir / "apple-touch-icon.png"
                img_apple = img.resize((180, 180), resample=Image.Resampling.LANCZOS)
                img_apple.save(apple_path, format="PNG")
                generated_files.append(str(apple_path))

                # Generate standard size PNGs (32x32, 16x16)
                png_sizes = [(32, 32), (16, 16)]
                for size in png_sizes:
                    png_path = output_dir / f"favicon-{size[0]}x{size[1]}.png"
                    img_png = img.resize(size, resample=Image.Resampling.LANCZOS)
                    img_png.save(png_path, format="PNG")
                    generated_files.append(str(png_path))

                # Generate Android Chrome Icons
                android_sizes = [(192, 192), (512, 512)]
                for size in android_sizes:
                    android_path = output_dir / f"android-chrome-{size[0]}x{size[1]}.png"
                    img_android = img.resize(size, resample=Image.Resampling.LANCZOS)
                    img_android.save(android_path, format="PNG")
                    generated_files.append(str(android_path))

                # Generate site.webmanifest
                manifest_path = output_dir / "site.webmanifest"
                manifest_data = {
                    "name": "App",
                    "short_name": "App",
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
                }
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest_data, f, indent=4)
                generated_files.append(str(manifest_path))

            return {
                "success": True,
                "output_dir": str(output_dir),
                "generated_files": generated_files
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_html_tags(self) -> str:
        """Returns standard HTML tags for favicons."""
        tags = [
            '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">',
            '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">',
            '<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">',
            '<link rel="manifest" href="/site.webmanifest">'
        ]
        return "\n".join(tags)
