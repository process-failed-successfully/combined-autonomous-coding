from PIL import Image
import tempfile
import os

fd, path = tempfile.mkstemp(suffix=".png")
os.close(fd)

img = Image.new('RGB', (300, 300), color='white')
img.save(path)

img2 = Image.open(path)
img2 = img2.convert("RGB")
data = list(img2.getdata())
print("len data:", len(data))
print("len data * 3:", len(data) * 3)
