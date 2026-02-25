import sys
import time
import shutil
from pathlib import Path
from typing import Optional, List

try:
    from PIL import Image, ImageSequence
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None
    ImageSequence = None

class AsciiLabManager:
    """
    Manages ASCII art generation and animation from images.
    """

    CHARSETS = {
        "standard": "@%#*+=-:. ",
        "simple": "#+-. ",
        "blocks": "█▓▒░ ",
        "binary": "01 ",
        "matrix": "M@TRIX ",
        "numbers": "84210 "
    }

    def _check_pil(self):
        if not HAS_PIL:
            raise ImportError("Pillow library is not installed. Please run: pip install Pillow")

    def convert_image_to_ascii(self, image_path: Path, width: int = 100, charset: str = "standard", inverse: bool = False) -> str:
        """
        Converts a single image to an ASCII string.
        """
        self._check_pil()
        if not image_path.exists():
            raise FileNotFoundError(f"File not found: {image_path}")

        chars = self.CHARSETS.get(charset, self.CHARSETS["standard"])
        if inverse:
            chars = chars[::-1]

        try:
            with Image.open(image_path) as img:
                return self._process_frame(img, width, chars)
        except Exception as e:
            raise ValueError(f"Error processing image: {e}")

    def _process_frame(self, img, width: int, chars: str) -> str:
        """
        Internal helper to process a single PIL Image object.
        """
        # Calculate height (aspect ratio correction: chars are approx 2x tall)
        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio * 0.5)

        # Resize
        resized_img = img.resize((width, height), Image.Resampling.LANCZOS)

        # Grayscale
        grayscale_img = resized_img.convert("L")

        # Map pixels to chars
        pixels = grayscale_img.getdata()
        new_pixels = [chars[pixel * (len(chars) - 1) // 255] for pixel in pixels]

        # Construct string
        ascii_image = ""
        for i in range(0, len(new_pixels), width):
            ascii_image += "".join(new_pixels[i:i+width]) + "\n"

        return ascii_image

    def play_gif(self, gif_path: Path, width: int = 100, charset: str = "standard", inverse: bool = False, fps_override: Optional[float] = None):
        """
        Plays a GIF as an ASCII animation in the terminal.
        """
        self._check_pil()
        if not gif_path.exists():
            raise FileNotFoundError(f"File not found: {gif_path}")

        chars = self.CHARSETS.get(charset, self.CHARSETS["standard"])
        if inverse:
            chars = chars[::-1]

        try:
            with Image.open(gif_path) as img:
                # Check if animated
                if not getattr(img, "is_animated", False):
                    print("Image is not animated. Showing single frame.")
                    print(self._process_frame(img, width, chars))
                    return

                # Pre-process frames to avoid lag during playback
                frames = []
                durations = []

                print("Processing frames...", end="", flush=True)
                for frame in ImageSequence.Iterator(img):
                    ascii_frame = self._process_frame(frame.copy(), width, chars)
                    frames.append(ascii_frame)
                    # Duration is in milliseconds
                    duration = frame.info.get('duration', 100)
                    durations.append(duration / 1000.0)
                print(" Done!")

                try:
                    while True:
                        for i, frame in enumerate(frames):
                            # Clear screen (ANSI)
                            print("\033[H\033[J", end="")
                            print(frame)

                            delay = durations[i]
                            if fps_override:
                                delay = 1.0 / fps_override

                            time.sleep(delay)
                except KeyboardInterrupt:
                    print("\nStopped.")

        except Exception as e:
            raise ValueError(f"Error playing GIF: {e}")

def run_ascii_lab_logic(args):
    """
    CLI entry point for Ascii Lab.
    """
    manager = AsciiLabManager()

    file_path = Path(args.file)

    try:
        if args.action == "image":
            result = manager.convert_image_to_ascii(
                file_path,
                width=args.width,
                charset=args.charset,
                inverse=args.inverse
            )
            print(result)

        elif args.action == "play":
            manager.play_gif(
                file_path,
                width=args.width,
                charset=args.charset,
                inverse=args.inverse,
                fps_override=args.fps
            )

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
