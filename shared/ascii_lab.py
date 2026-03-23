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


    # 5x5 Font for A-Z, 0-9, and Space
    FONT_5x5 = {
        'A': [" ### ", "#   #", "#####", "#   #", "#   #"],
        'B': ["#### ", "#   #", "#### ", "#   #", "#### "],
        'C': [" ####", "#    ", "#    ", "#    ", " ####"],
        'D': ["#### ", "#   #", "#   #", "#   #", "#### "],
        'E': ["#####", "#    ", "#### ", "#    ", "#####"],
        'F': ["#####", "#    ", "#### ", "#    ", "#    "],
        'G': [" ####", "#    ", "# ###", "#   #", " ####"],
        'H': ["#   #", "#   #", "#####", "#   #", "#   #"],
        'I': ["#####", "  #  ", "  #  ", "  #  ", "#####"],
        'J': ["#####", "   # ", "   # ", "#  # ", " ##  "],
        'K': ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
        'L': ["#    ", "#    ", "#    ", "#    ", "#####"],
        'M': ["#   #", "## ##", "# # #", "#   #", "#   #"],
        'N': ["#   #", "##  #", "# # #", "#  ##", "#   #"],
        'O': [" ### ", "#   #", "#   #", "#   #", " ### "],
        'P': ["#### ", "#   #", "#### ", "#    ", "#    "],
        'Q': [" ### ", "#   #", "#   #", "#  ##", " ####"],
        'R': ["#### ", "#   #", "#### ", "#  # ", "#   #"],
        'S': [" ####", "#    ", " ### ", "    #", "#### "],
        'T': ["#####", "  #  ", "  #  ", "  #  ", "  #  "],
        'U': ["#   #", "#   #", "#   #", "#   #", " ### "],
        'V': ["#   #", "#   #", "#   #", " # # ", "  #  "],
        'W': ["#   #", "#   #", "# # #", "## ##", "#   #"],
        'X': ["#   #", " # # ", "  #  ", " # # ", "#   #"],
        'Y': ["#   #", " # # ", "  #  ", "  #  ", "  #  "],
        'Z': ["#####", "   # ", "  #  ", " #   ", "#####"],
        '0': [" ### ", "#  ##", "# # #", "##  #", " ### "],
        '1': ["  #  ", " ##  ", "  #  ", "  #  ", " ### "],
        '2': [" ####", "    #", " ### ", "#    ", "#####"],
        '3': ["#####", "   # ", " ### ", "   # ", "#####"],
        '4': ["   # ", "  ## ", " # # ", "#####", "   # "],
        '5': ["#####", "#    ", "#### ", "    #", "#### "],
        '6': [" ### ", "#    ", "#### ", "#   #", " ### "],
        '7': ["#####", "    #", "   # ", "  #  ", " #   "],
        '8': [" ### ", "#   #", " ### ", "#   #", " ### "],
        '9': [" ### ", "#   #", " ####", "    #", " ### "],
        ' ': ["     ", "     ", "     ", "     ", "     "],
        '.': ["     ", "     ", "     ", "     ", "  #  "],
        '!': ["  #  ", "  #  ", "  #  ", "     ", "  #  "],
        '?': [" ### ", "    #", "  ## ", "     ", "  #  "],
        '-': ["     ", "     ", "#####", "     ", "     "],
        '_': ["     ", "     ", "     ", "     ", "#####"],
        '+': ["     ", "  #  ", "#####", "  #  ", "     "],
        '=': ["     ", "#####", "     ", "#####", "     "],
    }

    def generate_text_banner(self, text: str, char: str = "#") -> str:
        """
        Generates an ASCII art banner using a 5x5 block font.
        """
        text = text.upper()
        lines = ["", "", "", "", ""]
        for letter in text:
            pattern = self.FONT_5x5.get(letter, self.FONT_5x5['?'])
            for i in range(5):
                lines[i] += pattern[i].replace('#', char) + "  "
        return "\n".join(lines)

    def generate_ascii_table(self) -> str:
        """
        Generates a formatted ASCII table showing Decimal, Hex, Octal, and Char for 0-127.
        """
        lines = []
        lines.append(f"{'Dec':<5} | {'Hex':<5} | {'Oct':<5} | {'Char':<15}")
        lines.append("-" * 38)

        for i in range(128):
            hex_val = f"0x{i:02X}"
            oct_val = f"0o{i:03o}"

            # Handle special control characters
            if i < 32 or i == 127:
                controls = {
                    0: "NUL (null)", 1: "SOH (start of heading)", 2: "STX (start of text)",
                    3: "ETX (end of text)", 4: "EOT (end of transmission)", 5: "ENQ (enquiry)",
                    6: "ACK (acknowledge)", 7: "BEL (bell)", 8: "BS  (backspace)",
                    9: "TAB (horizontal tab)", 10: "LF  (NL line feed)", 11: "VT  (vertical tab)",
                    12: "FF  (NP form feed)", 13: "CR  (carriage return)", 14: "SO  (shift out)",
                    15: "SI  (shift in)", 16: "DLE (data link escape)", 17: "DC1 (device control 1)",
                    18: "DC2 (device control 2)", 19: "DC3 (device control 3)", 20: "DC4 (device control 4)",
                    21: "NAK (negative ack)", 22: "SYN (synchronous idle)", 23: "ETB (end of trans. block)",
                    24: "CAN (cancel)", 25: "EM  (end of medium)", 26: "SUB (substitute)",
                    27: "ESC (escape)", 28: "FS  (file separator)", 29: "GS  (group separator)",
                    30: "RS  (record separator)", 31: "US  (unit separator)", 127: "DEL (delete)"
                }
                char_repr = controls.get(i, f"CTRL-{i}")
            else:
                char_repr = chr(i)

            lines.append(f"{i:<5} | {hex_val:<5} | {oct_val:<5} | {char_repr:<15}")

        return "\n".join(lines)


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

    file_path = Path(args.file) if hasattr(args, 'file') and args.file else None

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

        elif args.action == "text":
            result = manager.generate_text_banner(args.text, char=args.char)
            print(result)

        elif args.action == "table":
            result = manager.generate_ascii_table()
            print(result)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
