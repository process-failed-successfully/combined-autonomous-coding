"""
Stego Lab
=========

Utilities for basic image steganography (hiding text inside image LSBs).
"""

import sys
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class StegoLabManager:
    """Manages steganography operations (encode and decode)."""

    def __init__(self):
        self._check_pil()

    def _check_pil(self):
        if not HAS_PIL:
            raise ImportError("Pillow library is not installed. Please run: pip install Pillow")

    def _str_to_bin(self, text: str) -> str:
        """Converts a string to a binary string."""
        return ''.join(format(ord(i), '08b') for i in text)

    def _bin_to_str(self, binary: str) -> str:
        """Converts a binary string to a normal string."""
        chars = []
        for i in range(0, len(binary), 8):
            byte = binary[i:i+8]
            if byte == '00000000':
                break
            chars.append(chr(int(byte, 2)))
        return ''.join(chars)

    def encode(self, image_path: Path, text: str, output_path: Path) -> bool:
        """Hides the text in the LSB of the image and saves it to output_path."""
        if not image_path.exists():
            raise FileNotFoundError(f"File not found: {image_path}")

        if not text:
            raise ValueError("Text to encode cannot be empty.")

        # Append a null terminator so we know where the string ends during decoding
        binary_data = self._str_to_bin(text) + '00000000'
        data_len = len(binary_data)

        try:
            with Image.open(image_path) as img:
                # Ensure image has an alpha channel or is RGB (convert to RGBA to be safe)
                encoded_img = img.convert("RGBA")
                pixels = encoded_img.load()

                width, height = encoded_img.size
                max_bytes = width * height * 4  # RGBA has 4 channels

                if data_len > max_bytes:
                    raise ValueError(f"Text is too large to hide in this image. Needs {data_len} bits, but image can only hold {max_bytes} bits.")

                data_index = 0
                for y in range(height):
                    for x in range(width):
                        if data_index < data_len:
                            pixel = list(pixels[x, y])

                            # Modify each channel (R, G, B, A)
                            for i in range(4):
                                if data_index < data_len:
                                    # Clear LSB and set to the bit of the data
                                    bit = int(binary_data[data_index])
                                    pixel[i] = (pixel[i] & ~1) | bit
                                    data_index += 1

                            pixels[x, y] = tuple(pixel)

                        if data_index >= data_len:
                            break
                    if data_index >= data_len:
                        break

                # Save as PNG to avoid compression loss which would destroy the LSBs
                encoded_img.save(output_path, "PNG")
                return True
        except Exception as e:
            raise ValueError(f"Error encoding image: {e}")

    def decode(self, image_path: Path) -> str:
        """Extracts the hidden text from the LSB of the image."""
        if not image_path.exists():
            raise FileNotFoundError(f"File not found: {image_path}")

        try:
            with Image.open(image_path) as img:
                encoded_img = img.convert("RGBA")
                pixels = encoded_img.load()

                width, height = encoded_img.size
                binary_data = []

                for y in range(height):
                    for x in range(width):
                        pixel = list(pixels[x, y])
                        for i in range(4):
                            # Extract the LSB
                            binary_data.append(str(pixel[i] & 1))

                # Now convert the binary data to a string, stopping at the null terminator
                binary_str = ''.join(binary_data)
                return self._bin_to_str(binary_str)
        except Exception as e:
            raise ValueError(f"Error decoding image: {e}")


def run_stego_lab_logic(args) -> bool:
    """CLI logic for Stego Lab."""

    if hasattr(args, "action") and args.action == "tui":
        from shared.tui import AgentTUI
        print("Launching Stego Lab TUI...")
        app = AgentTUI(project_dir=args.project_dir, start_tab="tab-stego")
        app.run()
        return True

    try:
        manager = StegoLabManager()
    except ImportError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False

    image_path = Path(args.image)

    try:
        if args.action == "encode":
            if not getattr(args, "text", None):
                print("❌ Error: --text is required for encoding.", file=sys.stderr)
                return False
            if not getattr(args, "output", None):
                print("❌ Error: --output is required for encoding.", file=sys.stderr)
                return False
            output_path = Path(args.output)

            print(f"Encoding text into {image_path.name}...")
            manager.encode(image_path, args.text, output_path)
            print(f"✅ Success! Encoded image saved to {output_path}")

        elif args.action == "decode":
            print(f"Decoding text from {image_path.name}...")
            text = manager.decode(image_path)
            print(f"✅ Extracted Text:\n{text}")

        return True
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False
