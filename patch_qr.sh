#!/bin/bash
patch -p1 << 'PATCH_EOF'
--- a/tests/test_qr_lab.py
+++ b/tests/test_qr_lab.py
@@ -78,13 +78,14 @@

     def test_decode_image(self):
         import tempfile
+        import qrcode

         text_to_encode = "https://example.com/test_decode"

         with tempfile.TemporaryDirectory() as tmpdir:
             img_path = Path(tmpdir) / "test_decode.png"
             # Generate the image directly bypassing the CLI wrapper method
-            img = self.manager.generate_image(text_to_encode)
+            img = qrcode.make(text_to_encode)
             img.save(str(img_path))

             # Assert file exists
PATCH_EOF
