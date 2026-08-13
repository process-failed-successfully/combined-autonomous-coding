import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os

# Ensure we can import from shared
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.pdf_lab import PDFLabManager

class TestPDFLabManager(unittest.TestCase):
    def setUp(self):
        # Patch pypdf in shared.pdf_lab
        self.pypdf_patcher = patch('shared.pdf_lab.pypdf')
        self.mock_pypdf = self.pypdf_patcher.start()

        # Ensure the module thinks pypdf is available
        self.manager = PDFLabManager()

    def tearDown(self):
        self.pypdf_patcher.stop()

    def test_get_info(self):
        mock_reader = MagicMock()
        mock_reader.metadata = {"/Title": "Test PDF", "/Author": "Tester"}
        self.mock_pypdf.PdfReader.return_value = mock_reader

        info = self.manager.get_info("dummy.pdf")
        self.assertEqual(info, {"/Title": "Test PDF", "/Author": "Tester"})
        self.mock_pypdf.PdfReader.assert_called_with("dummy.pdf")

    def test_extract_text(self):
        mock_reader = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"
        # Mock pages as list access
        mock_reader.pages = [mock_page1, mock_page2]
        self.mock_pypdf.PdfReader.return_value = mock_reader

        # Test full extraction
        text = self.manager.extract_text("dummy.pdf")
        self.assertIn("Page 1 content", text)
        self.assertIn("Page 2 content", text)

        # Test range
        text_range = self.manager.extract_text("dummy.pdf", page_start=1)
        self.assertNotIn("Page 1 content", text_range)
        self.assertIn("Page 2 content", text_range)

    def test_merge_pdfs(self):
        mock_writer = MagicMock()
        self.mock_pypdf.PdfWriter.return_value = mock_writer

        inputs = ["file1.pdf", "file2.pdf"]
        output = "merged.pdf"
        self.manager.merge_pdfs(output, inputs)

        self.assertEqual(mock_writer.append.call_count, 2)
        mock_writer.write.assert_called_with(output)
        mock_writer.close.assert_called_once()

    def test_encrypt(self):
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_reader.pages = [mock_page, mock_page]
        self.mock_pypdf.PdfReader.return_value = mock_reader

        mock_writer = MagicMock()
        self.mock_pypdf.PdfWriter.return_value = mock_writer

        with patch("builtins.open", mock_open()) as mock_file:
            self.manager.encrypt("input.pdf", "output.pdf", "secret")

            self.mock_pypdf.PdfReader.assert_called_with("input.pdf")
            self.assertEqual(mock_writer.add_page.call_count, 2)
            mock_writer.encrypt.assert_called_with("secret")
            mock_file.assert_called_with("output.pdf", "wb")
            mock_writer.write.assert_called()
            mock_writer.close.assert_called()

    def test_decrypt(self):
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader.is_encrypted = True
        mock_reader.decrypt.return_value = True
        self.mock_pypdf.PdfReader.return_value = mock_reader

        mock_writer = MagicMock()
        self.mock_pypdf.PdfWriter.return_value = mock_writer

        with patch("builtins.open", mock_open()) as mock_file:
            self.manager.decrypt("input.pdf", "output.pdf", "secret")

            self.mock_pypdf.PdfReader.assert_called_with("input.pdf")
            mock_reader.decrypt.assert_called_with("secret")
            self.assertEqual(mock_writer.add_page.call_count, 1)
            mock_file.assert_called_with("output.pdf", "wb")
            mock_writer.write.assert_called()
            mock_writer.close.assert_called()

    def test_decrypt_not_encrypted(self):
        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        self.mock_pypdf.PdfReader.return_value = mock_reader

        with self.assertRaises(ValueError):
            self.manager.decrypt("input.pdf", "output.pdf", "secret")

    def test_decrypt_wrong_password(self):
        mock_reader = MagicMock()
        mock_reader.is_encrypted = True
        mock_reader.decrypt.return_value = False
        self.mock_pypdf.PdfReader.return_value = mock_reader

        with self.assertRaises(ValueError):
            self.manager.decrypt("input.pdf", "output.pdf", "wrong")

    def test_split_pdf(self):
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_reader.pages = [mock_page, mock_page] # 2 pages
        self.mock_pypdf.PdfReader.return_value = mock_reader

        mock_writer = MagicMock()
        self.mock_pypdf.PdfWriter.return_value = mock_writer

        # Mock Path.mkdir to avoid filesystem operations
        with patch('shared.pdf_lab.Path.mkdir') as mock_mkdir, \
             patch("builtins.open", mock_open()) as mock_file:

            generated = self.manager.split_pdf("dummy.pdf", "output_dir")

            mock_mkdir.assert_called()
            self.assertEqual(len(generated), 2)
            self.assertEqual(mock_writer.add_page.call_count, 2)
            self.assertEqual(mock_writer.write.call_count, 2)

if __name__ == '__main__':
    unittest.main()
