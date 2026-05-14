from pathlib import Path
from PIL import Image

p = Path("/tmp/test_logo.png")
img = Image.new('RGB', (512, 512), color='red')
img.save(p)
print("Exists:", p.exists())
