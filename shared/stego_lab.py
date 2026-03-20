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

    def _get_data(self, img):
        """Helper to get pixel data avoiding deprecation warnings if possible."""
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            data = list(img.getdata())
            # On certain older Python/Pillow combinations, list(img.getdata()) may return empty.
            if not data and img.width > 0 and img.height > 0:
                data = [img.getpixel((x, y)) for y in range(img.height) for x in range(img.width)]
            return data

    def hide(self, image_path: str, secret_message: str, output_path: str) -> bool:
        """Hides a secret message in an image using LSB steganography."""
        img = Image.open(image_path)
        img = img.convert("RGB")

        # Encode the message into binary, and append a terminator
        binary_message = ''.join(format(ord(char), '08b') for char in secret_message)
        binary_message += '1111111111111110'

        data = self._get_data(img)

        if len(binary_message) > len(data) * 3:
            raise ValueError("Message is too large to fit in this image.")

        new_data = []
        data_index = 0

        for pixel in data:
            r, g, b = pixel

            if data_index < len(binary_message):
                r = (r & ~1) | int(binary_message[data_index])
                data_index += 1
            if data_index < len(binary_message):
                g = (g & ~1) | int(binary_message[data_index])
                data_index += 1
            if data_index < len(binary_message):
                b = (b & ~1) | int(binary_message[data_index])
                data_index += 1

            new_data.append((r, g, b))

        img.putdata(new_data)
        img.save(output_path)
        return True

    def extract(self, image_path: str) -> str:
        """Extracts a hidden message from an image."""
        img = Image.open(image_path)
        img = img.convert("RGB")
        data = self._get_data(img)

        binary_message = ""
        for pixel in data:
            r, g, b = pixel
            binary_message += str(r & 1)
            binary_message += str(g & 1)
            binary_message += str(b & 1)

        # Search for the terminator
        terminator = '1111111111111110'
        terminator_index = binary_message.find(terminator)

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
