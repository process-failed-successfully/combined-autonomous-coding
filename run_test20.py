import tempfile
import qrcode
from pathlib import Path
from unittest.mock import patch

text_to_encode = "https://example.com/test_decode"
with tempfile.TemporaryDirectory() as tmpdir:
    img_path = Path(tmpdir) / "test_decode.png"
    img = qrcode.make(text_to_encode)

    import builtins
    original_open = builtins.open

    def my_open(*args, **kwargs):
        print(f"Opening: {args}, {kwargs}")
        return original_open(*args, **kwargs)

    with patch("builtins.open", side_effect=my_open):
        with open(str(img_path), "wb") as f:
            img.save(f)
        import cv2
        image = cv2.imread(str(img_path))
        print("cv2 read:", type(image), image is not None)
