import base64
import os
import argparse
import sys
from typing import Dict, Any, Optional

class Base64ImgLabManager:
    """Manages encoding images to Base64 and decoding Base64 to images."""

    def encode_image(self, file_path: str) -> Dict[str, Any]:
        """Encodes an image file to a Base64 string."""
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        try:
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return {"success": True, "result": encoded_string}
        except Exception as e:
            return {"success": False, "error": f"Error encoding image: {str(e)}"}

    def decode_image(self, base64_string: str, output_path: str) -> Dict[str, Any]:
        """Decodes a Base64 string to an image file."""
        if not base64_string:
            return {"success": False, "error": "Base64 string cannot be empty."}

        if not output_path:
            return {"success": False, "error": "Output path must be provided."}

        try:
            # Handle data URI scheme if present (e.g., data:image/png;base64,...)
            if "," in base64_string:
                prefix, base64_data = base64_string.split(",", 1)
                if not prefix.startswith("data:"):
                    base64_data = base64_string # Not a valid data URI, assume it's raw
            else:
                base64_data = base64_string

            image_data = base64.b64decode(base64_data)

            with open(output_path, "wb") as image_file:
                image_file.write(image_data)

            return {"success": True, "result": output_path}
        except Exception as e:
            return {"success": False, "error": f"Error decoding base64: {str(e)}"}


def run_base64img_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for base64img-lab."""
    manager = Base64ImgLabManager()

    if getattr(args, "encode", None):
        result = manager.encode_image(args.encode)
        if result["success"]:
            if getattr(args, "output", None):
                try:
                    with open(args.output, "w") as f:
                        f.write(result["result"])
                    print(f"✅ Base64 string saved to {args.output}")
                except Exception as e:
                    print(f"❌ Error saving output: {e}", file=sys.stderr)
                    return False
            else:
                print(result["result"])
            return True
        else:
            print(f"❌ {result['error']}", file=sys.stderr)
            return False

    elif getattr(args, "decode", None):
        output_path = getattr(args, "output", None)
        if not output_path:
            print("❌ Error: --output is required when decoding.", file=sys.stderr)
            return False

        # check if it's a file path or raw base64 string
        # using the memory instruction: check length first
        base64_input = args.decode
        if len(base64_input) < 1000:
            if os.path.exists(base64_input) and os.path.isfile(base64_input):
                try:
                    with open(base64_input, "r") as f:
                        base64_input = f.read().strip()
                except Exception as e:
                    print(f"❌ Error reading file: {e}", file=sys.stderr)
                    return False

        result = manager.decode_image(base64_input, output_path)
        if result["success"]:
            print(f"✅ Image saved to {output_path}")
            return True
        else:
            print(f"❌ {result['error']}", file=sys.stderr)
            return False

    else:
        print("❌ Error: Must provide either --encode or --decode.", file=sys.stderr)
        return False
