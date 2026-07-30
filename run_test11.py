import tempfile
import qrcode
from pathlib import Path
from unittest.mock import patch

text_to_encode = "https://example.com/test_decode"
with tempfile.TemporaryDirectory() as tmpdir:
    img_path = Path(tmpdir) / "test_decode.png"
    img = qrcode.make(text_to_encode)
    with open(str(img_path), "wb") as f:
        img.save(f)

    print("exists:", img_path.exists())

    # Try importing something that might have mocked cv2 or builtins.open
    import tests.test_tui_qr
    import tests.test_qr_lab

    from shared.qr_lab import QRLabManager
    m = QRLabManager()

    import cv2
    image = cv2.imread(str(img_path))
    print("cv2 read:", type(image), image is not None)
