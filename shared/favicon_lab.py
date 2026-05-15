import json
from pathlib import Path
import warnings

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class FaviconManager:
    """Manages generation of web favicons and manifest files."""

    def __init__(self):
        if not PILLOW_AVAILABLE:
            warnings.warn("Pillow is required for FaviconLab. Install it with `pip install Pillow`.", ImportWarning)

    def generate(self, image_path: str, output_dir: str = ".") -> bool:
        """
        Generates standard favicons from an input image.
        Returns True if successful, False otherwise.
        """
        if not PILLOW_AVAILABLE:
            print("Error: Pillow library is not installed.")
            return False

        try:
            img_path = Path(image_path)
            if not img_path.exists():
                print(f"Error: Image not found at {image_path}")
                return False

            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            with Image.open(img_path) as img:
                # Convert to RGBA if it isn't (for transparency support in PNG/ICO)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                # Generate standard PNGs
                sizes = {
                    "apple-touch-icon.png": (180, 180),
                    "android-chrome-192x192.png": (192, 192),
                    "android-chrome-512x512.png": (512, 512),
                    "favicon-32x32.png": (32, 32),
                    "favicon-16x16.png": (16, 16),
                }

                for filename, size in sizes.items():
                    resized_img = img.resize(size, Image.Resampling.LANCZOS)
                    resized_img.save(out_dir / filename, format="PNG")

                # Generate favicon.ico using a copy as per memory instructions
                # "When saving images in ICO format with multiple sizes using Pillow... operate on a copy of the image (img.copy())."
                ico_copy = img.copy()
                if max(ico_copy.size) < 48:
                    ico_copy = ico_copy.resize((48, 48), Image.Resampling.LANCZOS)
                with open(str(out_dir / "favicon.ico"), "wb") as f:
                    ico_copy.save(
                        f,
                        format="ICO",
                        sizes=[(16, 16), (32, 32), (48, 48)]
                    )

            # Generate site.webmanifest
            manifest = {
                "name": "My Application",
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
            with open(out_dir / "site.webmanifest", "w") as f:
                json.dump(manifest, f, indent=4)

            return True

        except Exception as e:
            print(f"Error generating favicons: {e}")
            return False

    def html(self) -> str:
        """Returns standard HTML tags for the generated favicons."""
        return """\
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="shortcut icon" href="/favicon.ico">"""
