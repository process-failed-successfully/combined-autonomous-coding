import unittest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from shared.license_lab import LicenseLabManager

class TestLicenseLab(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = LicenseLabManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_list_licenses(self):
        licenses = self.manager.list_licenses()
        self.assertIn("mit", licenses)
        self.assertIn("apache-2.0", licenses)
        self.assertIn("unlicense", licenses)

    def test_get_license_details(self):
        details = self.manager.get_license_details("mit")
        self.assertEqual(details["name"], "MIT License")
        self.assertIn("Commercial use", details["permissions"])

    def test_generate_license_content(self):
        content = self.manager.generate_license_content("mit", "John Doe", "2024")
        self.assertIn("Copyright (c) 2024 John Doe", content)
        self.assertIn("MIT License", content)

    def test_generate_license_file(self):
        output_path = self.test_dir / "LICENSE"
        success = self.manager.generate_license_file("mit", "Jane Doe", "2025", output_path)
        self.assertTrue(success)
        self.assertTrue(output_path.exists())
        content = output_path.read_text()
        self.assertIn("Copyright (c) 2025 Jane Doe", content)

    @patch("shared.license_lab.DependencyAnalyzer")
    def test_check_dependencies(self, mock_analyzer_cls):
        mock_instance = mock_analyzer_cls.return_value
        mock_instance.scan.return_value = {"python": []}
        mock_instance.check_licenses.return_value = [{"package": "requests", "status": "OK"}]

        results = self.manager.check_dependencies()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["package"], "requests")
        mock_instance.scan.assert_called_once()
        mock_instance.check_licenses.assert_called_once()

if __name__ == "__main__":
    unittest.main()
