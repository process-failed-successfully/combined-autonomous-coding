from shared.mime_lab import MimeLabManager


class TestMimeLabManager:
    def setup_method(self):
        self.manager = MimeLabManager()

    def test_lookup_by_extension(self):
        assert self.manager.lookup_by_extension('.json') == 'application/json'
        assert self.manager.lookup_by_extension('json') == 'application/json'  # Should auto-add dot
        assert self.manager.lookup_by_extension('.txt') == 'text/plain'
        assert self.manager.lookup_by_extension('.unknown123') is None

    def test_lookup_by_mime(self):
        exts = self.manager.lookup_by_mime('application/json')
        assert '.json' in exts

        exts_yaml = self.manager.lookup_by_mime('application/yaml')
        assert '.yaml' in exts_yaml or '.yml' in exts_yaml

        assert self.manager.lookup_by_mime('unknown/mimetype') == []

    def test_detect_file_with_magic_number(self, tmp_path):
        # Create a fake PNG file
        png_file = tmp_path / "fake.png"
        with open(png_file, "wb") as f:
            f.write(b'\x89PNG\r\n\x1a\n')  # PNG magic number

        result = self.manager.detect_file(png_file)
        assert result['best_guess'] == 'image/png'
        assert result['magic_based'] == 'image/png'
        assert result['extension_based'] == 'image/png'
        assert result['confidence'] == 'High'

    def test_detect_file_conflict(self, tmp_path):
        # Create a file with PNG magic number but .txt extension
        fake_txt = tmp_path / "fake.txt"
        with open(fake_txt, "wb") as f:
            f.write(b'\x89PNG\r\n\x1a\n')  # PNG magic number

        result = self.manager.detect_file(fake_txt)
        assert result['magic_based'] == 'image/png'
        assert result['extension_based'] == 'text/plain'
        assert result['confidence'] == 'Low (Conflict)'
        assert result['best_guess'] == 'image/png'  # Magic number takes precedence

    def test_detect_file_zip_based(self, tmp_path):
        # Create a fake DOCX file (ZIP magic number)
        docx_file = tmp_path / "document.docx"
        with open(docx_file, "wb") as f:
            f.write(b'PK\x03\x04')  # ZIP magic number

        result = self.manager.detect_file(docx_file)
        assert result['extension_based'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        # Because magic number matches ZIP, and extension is a known ZIP-based format, it should upgrade
        assert result['magic_based'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        assert result['best_guess'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

    def test_detect_file_no_magic_number(self, tmp_path):
        # Create a plain text file
        txt_file = tmp_path / "plain.txt"
        with open(txt_file, "w") as f:
            f.write("Hello, World!")

        result = self.manager.detect_file(txt_file)
        # It's plain text, doesn't match our specific magic numbers perfectly unless we added a broad one
        # but it shouldn't crash and should fallback to extension
        assert result['extension_based'] == 'text/plain'
        assert result['best_guess'] == 'text/plain'
        # Confidence is Medium if only extension matched
        assert result['confidence'] == 'Medium'
