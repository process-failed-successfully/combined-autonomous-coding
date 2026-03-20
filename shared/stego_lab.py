import sys
import argparse
from pathlib import Path

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

class StegoManager:
    """Manages LSB (Least Significant Bit) steganography operations."""

    def __init__(self):
        pass

    def _encode_length(self, length: int) -> str:
        """Encodes the length as a 32-bit binary string."""
        return format(length, '032b')

    def _decode_length(self, bin_str: str) -> int:
        """Decodes a 32-bit binary string to an integer."""
        return int(bin_str, 2)

    def _text_to_bin(self, text: str) -> str:
        """Converts text to a binary string using UTF-8."""
        byte_data = text.encode('utf-8')
        return ''.join(format(b, '08b') for b in byte_data)

    def _bin_to_text(self, bin_str: str) -> str:
        """Converts a binary string back to text using UTF-8."""
        byte_array = bytearray()
        for i in range(0, len(bin_str), 8):
            byte = bin_str[i:i+8]
            if len(byte) == 8:
                byte_array.append(int(byte, 2))
        return byte_array.decode('utf-8', errors='replace')

    def hide_text(self, image_path: str, text: str, output_path: str) -> bool:
        """Hides text inside an image using LSB steganography."""
        if not HAS_PILLOW:
            raise RuntimeError("Pillow library is required for steganography.")

        img = Image.open(image_path)
        img = img.convert('RGB')
        pixels = img.load()

        width, height = img.size

        # Convert text to binary
        binary_text = self._text_to_bin(text)
        text_length = len(binary_text)

        # Prefix with 32-bit length
        encoded_data = self._encode_length(text_length) + binary_text

        if len(encoded_data) > width * height * 3:
            raise ValueError("Text is too large to hide in this image.")

        data_idx = 0
        for y in range(height):
            for x in range(width):
                if data_idx >= len(encoded_data):
                    break

                r, g, b = pixels[x, y]

                # Modify R
                if data_idx < len(encoded_data):
                    r = (r & ~1) | int(encoded_data[data_idx])
                    data_idx += 1

                # Modify G
                if data_idx < len(encoded_data):
                    g = (g & ~1) | int(encoded_data[data_idx])
                    data_idx += 1

                # Modify B
                if data_idx < len(encoded_data):
                    b = (b & ~1) | int(encoded_data[data_idx])
                    data_idx += 1

                pixels[x, y] = (r, g, b)

            if data_idx >= len(encoded_data):
                break

        # Save the new image as PNG to avoid compression loss
        img.save(output_path, "PNG")
        return True

    def extract_text(self, image_path: str) -> str:
        """Extracts hidden text from an image."""
        if not HAS_PILLOW:
            raise RuntimeError("Pillow library is required for steganography.")

        img = Image.open(image_path)
        img = img.convert('RGB')
        pixels = img.load()

        width, height = img.size
        binary_data = ""

        # First extract the 32-bit length
        length_extracted = False
        text_length = 0

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]

                binary_data += str(r & 1)
                if not length_extracted and len(binary_data) == 32:
                    text_length = self._decode_length(binary_data)
                    length_extracted = True
                    binary_data = ""

                if length_extracted and len(binary_data) >= text_length:
                    return self._bin_to_text(binary_data[:text_length])

                binary_data += str(g & 1)
                if not length_extracted and len(binary_data) == 32:
                    text_length = self._decode_length(binary_data)
                    length_extracted = True
                    binary_data = ""

                if length_extracted and len(binary_data) >= text_length:
                    return self._bin_to_text(binary_data[:text_length])

                binary_data += str(b & 1)
                if not length_extracted and len(binary_data) == 32:
                    text_length = self._decode_length(binary_data)
                    length_extracted = True
                    binary_data = ""

                if length_extracted and len(binary_data) >= text_length:
                    return self._bin_to_text(binary_data[:text_length])

        return ""


def run_stego_lab_logic(args: argparse.Namespace) -> bool:
    if not HAS_PILLOW:
        print("Error: Pillow library is not installed. Please install it with 'pip install Pillow'.", file=sys.stderr)
        return False

    manager = StegoManager()

    if getattr(args, "action", None) == "hide":
        if not getattr(args, "image", None) or not getattr(args, "text", None) or not getattr(args, "output", None):
            print("Error: --image, --text, and --output are required for 'hide' action.", file=sys.stderr)
            return False

        try:
            manager.hide_text(args.image, args.text, args.output)
            print(f"Text successfully hidden in {args.output}")
            return True
        except Exception as e:
            print(f"Error hiding text: {e}", file=sys.stderr)
            return False

    elif getattr(args, "action", None) == "extract":
        if not getattr(args, "image", None):
            print("Error: --image is required for 'extract' action.", file=sys.stderr)
            return False

        try:
            extracted = manager.extract_text(args.image)
            if extracted:
                print(extracted)
            else:
                print("No text could be extracted or the hidden text was empty.")
            return True
        except Exception as e:
            print(f"Error extracting text: {e}", file=sys.stderr)
            return False

    return False
