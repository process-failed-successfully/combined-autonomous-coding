import sys

try:
    from PIL import Image
except ImportError:
    Image = None


class StegoManager:
    """Manages steganography operations to hide and extract text from images."""

    def __init__(self):
        if Image is None:
            raise ImportError(
                "The 'Pillow' library is required for Stego Lab. "
                "Please install it."
            )

    def hide(self, image_path: str, secret_message: str, output_path: str) -> bool:
        """Hides a secret message in an image using LSB steganography."""
        img = Image.open(image_path)
        img = img.convert("RGB")

        # Encode the message into binary, and append a terminator
        binary_message = ''.join(format(ord(char), '08b') for char in secret_message)
        binary_message += '1111111111111110'

        width, height = img.size
        capacity = width * height * 3

        if len(binary_message) > capacity:
            raise ValueError("Message is too large to fit in this image.")

        pixels = img.load()
        data_index = 0

        for y in range(height):
            for x in range(width):
                if data_index >= len(binary_message):
                    break

                r, g, b = pixels[x, y]

                if data_index < len(binary_message):
                    r = (r & ~1) | int(binary_message[data_index])
                    data_index += 1
                if data_index < len(binary_message):
                    g = (g & ~1) | int(binary_message[data_index])
                    data_index += 1
                if data_index < len(binary_message):
                    b = (b & ~1) | int(binary_message[data_index])
                    data_index += 1

                pixels[x, y] = (r, g, b)

            if data_index >= len(binary_message):
                break

        img.save(output_path)
        return True

    def extract(self, image_path: str) -> str:
        """Extracts a hidden message from an image."""
        img = Image.open(image_path)
        img = img.convert("RGB")

        width, height = img.size
        pixels = img.load()

        binary_message = ""
        terminator = '1111111111111110'
        terminator_index = -1

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                binary_message += str(r & 1)
                binary_message += str(g & 1)
                binary_message += str(b & 1)

                if len(binary_message) >= len(terminator):
                    idx = binary_message.rfind(terminator, max(0, len(binary_message) - len(terminator) - 3))
                    if idx != -1:
                        terminator_index = idx
                        break

            if terminator_index != -1:
                break

        if terminator_index == -1:
            raise ValueError("No hidden message found or corrupted data.")

        binary_message = binary_message[:terminator_index]

        secret_message = ""
        for i in range(0, len(binary_message), 8):
            byte = binary_message[i:i + 8]
            if len(byte) == 8:
                secret_message += chr(int(byte, 2))

        return secret_message


def run_stego_lab_logic(args):
    """CLI logic for the Stego Lab."""
    try:
        manager = StegoManager()
    except ImportError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.action == "hide":
        if not getattr(args, 'image', None) or not getattr(args, 'message', None) or not getattr(args, 'output', None):
            print(
                "❌ Error: --image, --message, and --output are required for 'hide'.",
                file=sys.stderr
            )
            sys.exit(1)

        try:
            manager.hide(args.image, args.message, args.output)
            print(f"✅ Message hidden successfully in {args.output}")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error hiding message: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "extract":
        if not getattr(args, 'image', None):
            print("❌ Error: --image is required for 'extract'.", file=sys.stderr)
            sys.exit(1)

        try:
            message = manager.extract(args.image)
            print(f"✅ Extracted Message: {message}")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error extracting message: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"❌ Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
