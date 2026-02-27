import shutil
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

class OcrLabManager:
    """
    Manages OCR operations using pytesseract (Tesseract OCR).
    """

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")
        self.tesseract_cmd = shutil.which("tesseract")

    def _check_deps(self):
        if not HAS_OCR:
            raise ImportError("pytesseract or Pillow is not installed. Please run 'pip install pytesseract Pillow'.")
        if not self.tesseract_cmd:
            raise RuntimeError("tesseract executable not found. Please install Tesseract OCR.")

    def extract_text(self, image_path: Path, lang: Optional[str] = None) -> str:
        """
        Extracts text from an image.
        """
        self._check_deps()
        if not image_path.exists():
            raise FileNotFoundError(f"File not found: {image_path}")

        try:
            return pytesseract.image_to_string(Image.open(image_path), lang=lang)
        except Exception as e:
            raise RuntimeError(f"OCR failed: {e}")

    def get_data(self, image_path: Path, lang: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns detailed OCR data (boxes, confidences, etc.).
        """
        self._check_deps()
        if not image_path.exists():
            raise FileNotFoundError(f"File not found: {image_path}")

        try:
            return pytesseract.image_to_data(Image.open(image_path), lang=lang, output_type=pytesseract.Output.DICT)
        except Exception as e:
            raise RuntimeError(f"OCR data extraction failed: {e}")

    def get_languages(self) -> List[str]:
        """
        Returns a list of available Tesseract languages.
        """
        self._check_deps()
        try:
            return pytesseract.get_languages(config='')
        except Exception as e:
            raise RuntimeError(f"Failed to get languages: {e}")


def run_ocr_lab_logic(args):
    """
    CLI entry point for OCR Lab.
    """
    manager = OcrLabManager(getattr(args, 'project_dir', None))

    try:
        if args.action == "extract":
            if not args.file:
                print("Error: --file is required.", file=sys.stderr)
                sys.exit(1)

            text = manager.extract_text(Path(args.file), lang=args.lang)

            if args.output:
                Path(args.output).write_text(text, encoding="utf-8")
                print(f"✅ Text extracted to {args.output}")
            else:
                print(text)

        elif args.action == "data":
            if not args.file:
                print("Error: --file is required.", file=sys.stderr)
                sys.exit(1)

            data = manager.get_data(Path(args.file), lang=args.lang)

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print(f"✅ Data saved to {args.output}")
            else:
                print(json.dumps(data, indent=2))

        elif args.action == "langs":
            langs = manager.get_languages()
            print("Available Languages:")
            for l in langs:
                print(f"  - {l}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
