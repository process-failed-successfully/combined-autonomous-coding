import sys
from pathlib import Path
import json


class FaviconManager:
    """Manages generation of web favicons."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def generate(self, image_path: str, output_dir: str = ".") -> bool:
        """Generates standard favicons from an image."""
        try:
            from PIL import Image
        except ImportError:
            print("Error: Pillow library is required to generate favicons. Install it using 'pip install Pillow'.", file=sys.stderr)
            return False

        img_path = self.project_dir / image_path
        out_dir = self.project_dir / output_dir

        if not img_path.exists() or not img_path.is_file():
            print(f"Error: Source image '{img_path}' not found.", file=sys.stderr)
            return False

        try:
            with Image.open(str(img_path)) as original_img:
                img = original_img.copy().convert("RGBA")
                width, height = img.size

                if width != height:
                    print(f"Warning: Source image is not square ({width}x{height}). Favicons may look distorted.", file=sys.stderr)

                if width < 512 or height < 512:
                    print(f"Error: Source image must be at least 512x512 pixels for high-quality generation. Provided image is {width}x{height}.", file=sys.stderr)
                    return False

                out_dir.mkdir(parents=True, exist_ok=True)

                # Generate favicon.ico
                ico_sizes = [(16, 16), (32, 32), (48, 48)]
                ico_path = out_dir / "favicon.ico"
                with open(str(ico_path), 'wb') as f:
                    img.copy().save(f, format='ICO', sizes=ico_sizes)
                print(f"✅ Generated {ico_path}")

                # Generate apple-touch-icon.png
                apple_size = (180, 180)
                apple_img = img.copy().resize(apple_size, Image.Resampling.LANCZOS)
                apple_path = out_dir / "apple-touch-icon.png"
                with open(str(apple_path), 'wb') as f:
                    apple_img.save(f, format='PNG')
                print(f"✅ Generated {apple_path}")

                # Generate favicon-32x32.png
                fav32_size = (32, 32)
                fav32_img = img.copy().resize(fav32_size, Image.Resampling.LANCZOS)
                fav32_path = out_dir / "favicon-32x32.png"
                with open(str(fav32_path), 'wb') as f:
                    fav32_img.save(f, format='PNG')
                print(f"✅ Generated {fav32_path}")

                # Generate favicon-16x16.png
                fav16_size = (16, 16)
                fav16_img = img.copy().resize(fav16_size, Image.Resampling.LANCZOS)
                fav16_path = out_dir / "favicon-16x16.png"
                with open(str(fav16_path), 'wb') as f:
                    fav16_img.save(f, format='PNG')
                print(f"✅ Generated {fav16_path}")

                # Generate android-chrome-192x192.png
                android192_size = (192, 192)
                android192_img = img.copy().resize(android192_size, Image.Resampling.LANCZOS)
                android192_path = out_dir / "android-chrome-192x192.png"
                with open(str(android192_path), 'wb') as f:
                    android192_img.save(f, format='PNG')
                print(f"✅ Generated {android192_path}")

                # Generate android-chrome-512x512.png
                android512_size = (512, 512)
                android512_img = img.copy().resize(android512_size, Image.Resampling.LANCZOS)
                android512_path = out_dir / "android-chrome-512x512.png"
                with open(str(android512_path), 'wb') as f:
                    android512_img.save(f, format='PNG')
                print(f"✅ Generated {android512_path}")

                # Generate site.webmanifest
                manifest = {
                    "name": "App Name",
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
                manifest_path = out_dir / "site.webmanifest"
                with open(str(manifest_path), 'w') as f:
                    json.dump(manifest, f, indent=4)
                print(f"✅ Generated {manifest_path}")

            return True
        except Exception as e:
            print(f"Error generating favicons: {e}", file=sys.stderr)
            return False

    def html(self) -> str:
        """Returns standard HTML tags for favicons."""
        snippet = """<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="manifest" href="/site.webmanifest">"""
        return snippet


def run_favicon_lab_logic(args) -> bool:
    manager = FaviconManager(args.project_dir)

    if args.action == "generate":
        if not hasattr(args, 'image') or not args.image:
            print("Error: --image is required for generate action.", file=sys.stderr)
            return False
        output_dir = getattr(args, 'output', ".")
        return manager.generate(args.image, output_dir)
    elif args.action == "html":
        print(manager.html())
        return True
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        return False
