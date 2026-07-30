import tempfile
import qrcode
from pathlib import Path
from unittest.mock import patch, MagicMock

text_to_encode = "https://example.com/test_decode"
with tempfile.TemporaryDirectory() as tmpdir:
    img_path = Path(tmpdir) / "test_decode.png"
    img = qrcode.make(text_to_encode)
    with open(str(img_path), "wb") as f:
        img.save(f)

    from shared.qr_lab import QRLabManager
    m = QRLabManager()
    with patch('shared.qr_lab.cv2.imread') as mock_imread:
        m.decode_image(img_path)
