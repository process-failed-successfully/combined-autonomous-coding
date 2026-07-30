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

    from shared.qr_lab import QRLabManager
    m = QRLabManager()
    print("qr results:", m.decode_image(img_path))
