from shared.qr_lab import QRLabManager
from pathlib import Path
import qrcode
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    img_path = Path(tmpdir) / "test.png"
    img = qrcode.make("test")
    with open(str(img_path), "wb") as f:
        img.save(f)

    m = QRLabManager()
    print(m.decode_image(img_path))
