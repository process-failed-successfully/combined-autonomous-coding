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
    print("size:", img_path.stat().st_size)
