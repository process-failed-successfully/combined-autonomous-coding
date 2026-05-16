import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class FaviconManager:
    """Manages generation of favicons and web manifests."""

    def __init__(self):
        if not PILLOW_AVAILABLE:
            print("Warning: Pillow library is not installed. Image generation will not work.", file=sys.stderr)
            print("Please install it with: pip install Pillow", file=sys.stderr)

    def generate(self, source_image: str, output_dir: str, background_color: str = "#ffffff", theme_color: str = "#ffffff", app_name: str = "My App") -> bool:
        """Generates standard favicon sizes and manifest.json from a source image."""
        if not PILLOW_AVAILABLE:
            return False

        src_path = Path(source_image)
        out_path = Path(output_dir)

        if not src_path.is_file():
            print(f"Error: Source image '{source_image}' does not exist.", file=sys.stderr)
            return False

        out_path.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(src_path) as img:
                # Need RGBA for transparency handling if we need to paste on background,
                # but for standard favicons we just resize.
                img = img.convert("RGBA")

                sizes = [16, 32, 48, 192, 512]

                # Generate ICO (usually contains 16, 32, 48)
                ico_sizes = [(s, s) for s in [16, 32, 48]]
                img_ico = img.copy().convert('RGBA')
                ico_path = out_path / "favicon.ico"

                # Pillow requires base image for ICO to be at least as large as the largest size requested
                # If the source image is smaller than 48x48, we should resize it first.
                max_ico_size = max(s for s, _ in ico_sizes)
                if img_ico.width < max_ico_size or img_ico.height < max_ico_size:
                    img_ico = img_ico.resize((max_ico_size, max_ico_size), Image.Resampling.LANCZOS)

                with open(str(ico_path), 'wb') as f:
                     img_ico.save(f, format='ICO', sizes=ico_sizes)

                # Generate PNGs
                for size in [192, 512]:
                    resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    png_path = out_path / f"android-chrome-{size}x{size}.png"
                    with open(str(png_path), 'wb') as f:
                        resized.save(f, format='PNG')

                # Apple Touch Icon
                apple_img = img.copy().convert("RGBA")
                # Apple touch icons typically have a solid background, but we'll just resize for simplicity
                # unless a background is specifically requested (could add later).
                apple_resized = apple_img.resize((180, 180), Image.Resampling.LANCZOS)
                apple_path = out_path / "apple-touch-icon.png"
                with open(str(apple_path), 'wb') as f:
                     apple_resized.save(f, format='PNG')

                # 32x32 and 16x16 standard pngs
                for size in [16, 32]:
                    resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    png_path = out_path / f"favicon-{size}x{size}.png"
                    with open(str(png_path), 'wb') as f:
                        resized.save(f, format='PNG')

            # Generate manifest.json
            manifest = {
                "name": app_name,
                "short_name": app_name,
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
                "theme_color": theme_color,
                "background_color": background_color,
                "display": "standalone"
            }

            manifest_path = out_path / "site.webmanifest"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            return True

        except Exception as e:
            print(f"Error generating favicons: {e}", file=sys.stderr)
            return False

    def html(self) -> str:
        """Returns the HTML tags to include in the <head> section."""
        tags = [
            '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">',
            '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">',
            '<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">',
            '<link rel="manifest" href="/site.webmanifest">'
        ]
        return "\n".join(tags)

def run_favicon_lab_logic(args) -> bool:
    """CLI logic for the Favicon Lab."""
    manager = FaviconManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        # Start TUI directly or delegate to main's TUI runner
        return True

    if args.action == "generate":
        if not getattr(args, "source", None) or not getattr(args, "output", None):
            print("Error: --source and --output are required for generate action.", file=sys.stderr)
            return False

        success = manager.generate(
            args.source,
            args.output,
            background_color=getattr(args, "bg_color", "#ffffff"),
            theme_color=getattr(args, "theme_color", "#ffffff"),
            app_name=getattr(args, "app_name", "My App")
        )
        if success:
            print(f"Favicons generated successfully in {args.output}")
        return success

    elif args.action == "html":
        print(manager.html())
        return True

    return False
