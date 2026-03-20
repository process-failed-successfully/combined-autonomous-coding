"""
Stego Lab
=========

Utilities for LSB steganography in images using Pillow (PIL).
"""

import sys
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class StegoManager:
    """Manages LSB steganography operations for images."""

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def _check_pil(self):
        if not HAS_PIL:
            raise ImportError("Pillow library is not installed. Please run: pip install Pillow")

    def hide(self, input_path: Path, output_path: Path, message: str) -> Path:
        """Hides a secret message in an image using LSB steganography."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        # Append null terminator to mark end of message
        message += "\0"

        # Convert message to bits (UTF-8)
        binary_message = ''.join(format(byte, '08b') for byte in message.encode('utf-8'))
        message_len = len(binary_message)

        with Image.open(input_path) as img:
            img = img.convert("RGB")  # Ensure RGB
            width, height = img.size

            # Avoid list(img.getdata()) for memory efficiency
            pixel_access = img.load()

            if width * height * 3 < message_len:
                raise ValueError(f"Image is too small to hold the message. Capacity: {width * height * 3} bits, Message: {message_len} bits")

            idx = 0

            # Iterate using coordinates (x, y)
            for y in range(height):
                for x in range(width):
                    if idx < message_len:
                        r, g, b = pixel_access[x, y]

                        # Modify R
                        if idx < message_len:
                            r = (r & ~1) | int(binary_message[idx])
                            idx += 1

                        # Modify G
                        if idx < message_len:
                            g = (g & ~1) | int(binary_message[idx])
                            idx += 1

                        # Modify B
                        if idx < message_len:
                            b = (b & ~1) | int(binary_message[idx])
                            idx += 1

                        pixel_access[x, y] = (r, g, b)
                    else:
                        break
                if idx >= message_len:
                    break

            # Enforce PNG
            if output_path.suffix.lower() != '.png':
                output_path = output_path.with_suffix('.png')
                print("Warning: Output format forced to PNG to preserve message.")

            img.save(output_path, "PNG")

        return output_path

    def extract(self, input_path: Path) -> str:
        """Extracts a secret message from an image."""
        self._check_pil()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        with Image.open(input_path) as img:
            img = img.convert("RGB")
            width, height = img.size
            pixel_access = img.load()

            binary_message = ""
            for y in range(height):
                for x in range(width):
                    r, g, b = pixel_access[x, y]
                    binary_message += str(r & 1)
                    binary_message += str(g & 1)
                    binary_message += str(b & 1)

                    # Optimization: Check if we have formed a null byte every few pixels
                    if len(binary_message) % 8 == 0 and len(binary_message) >= 8:
                        if binary_message[-8:] == "00000000":
                            break
                if len(binary_message) % 8 == 0 and len(binary_message) >= 8 and binary_message[-8:] == "00000000":
                    break

            # Convert bits to bytes then string
            extracted_bytes = bytearray()
            for i in range(0, len(binary_message), 8):
                byte = binary_message[i:i+8]
                if byte == "00000000":
                    break
                if len(byte) == 8:
                    try:
                        extracted_bytes.append(int(byte, 2))
                    except ValueError:
                        break  # Stop if conversion fails

            return extracted_bytes.decode('utf-8', errors='replace')


def run_stego_lab_logic(args):
    """Entry point for Stego Lab CLI."""
    manager = StegoManager(args.project_dir)

    try:
        if args.action == "hide":
            output = Path(args.output)
            message = args.message
            if not message:
                # Try reading from stdin
                if not sys.stdin.isatty():
                    message = sys.stdin.read().strip()
                else:
                    message = input("Enter message to hide: ")

            if not message:
                print("Error: Message is empty.", file=sys.stderr)
                sys.exit(1)

            final_path = manager.hide(Path(args.input), output, message)
            print(f"Message hidden in {final_path}")

        elif args.action == "extract":
            message = manager.extract(Path(args.input))
            if message:
                print(f"--- Hidden Message ---\n{message}\n----------------------")
            else:
                print("No hidden message found (or it was empty).")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
