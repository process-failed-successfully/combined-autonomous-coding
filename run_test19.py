import sys
import tempfile
import qrcode
from pathlib import Path

text_to_encode = "https://example.com/test_decode"
with tempfile.TemporaryDirectory() as tmpdir:
    img_path = Path(tmpdir) / "test_decode.png"
    img = qrcode.make(text_to_encode)

    # Intentionally do not write the file yet
    import cv2
    image = cv2.imread(str(img_path))
    print("cv2 read before write:", image is not None)

    with open(str(img_path), "wb") as f:
        img.save(f)
    print("cv2 read after write:", cv2.imread(str(img_path)) is not None)

    # Try opening it via builtins.open patch?
    # Some other test might be mocking `builtins.open` so `img.save(str(img_path))` doesn't actually write to disk!
