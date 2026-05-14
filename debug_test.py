import os
import sys
from pathlib import Path
from PIL import Image

try:
    from shared.favicon_lab import FaviconManager
    manager = FaviconManager()

    import tempfile
    tmp = Path(tempfile.mkdtemp())
    img_path = tmp / "test_logo.png"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(img_path)

    out_dir = tmp / "out"
    print(f"Calling generate with {img_path} and {out_dir}")
    res = manager.generate(str(img_path), str(out_dir))
    print(f"Result: {res}")
except Exception as e:
    import traceback
    traceback.print_exc()
