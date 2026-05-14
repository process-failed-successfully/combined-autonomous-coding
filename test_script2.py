from shared.favicon_lab import FaviconManager
from pathlib import Path
import tempfile
from PIL import Image

tmp = Path(tempfile.mkdtemp())
img_path = tmp / "test_logo.png"
img = Image.new('RGB', (100, 100), color='red')
img.save(img_path)

manager = FaviconManager()
output_dir = tmp / "out"

result = manager.generate(str(img_path), str(output_dir))
print(f"Result: {result}")
