import tempfile
import qrcode
from pathlib import Path

text_to_encode = "https://example.com/test_decode"
with tempfile.TemporaryDirectory() as tmpdir:
    img_path = Path(tmpdir) / "test_decode.png"
    img = qrcode.make(text_to_encode)
    with open(str(img_path), "wb") as f:
        img.save(f)
    print("exists:", img_path.exists())

    import cv2
    image = cv2.imread(str(img_path))
    print("cv2 read:", type(image), image is not None)
