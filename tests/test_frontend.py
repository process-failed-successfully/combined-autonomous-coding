import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.frontend import FrontendVerifier

class TestFrontendVerifier(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.verifier = FrontendVerifier(self.project_dir)

    @patch("shared.frontend.FrontendVerifier.setup", return_value=True)
    @patch("shared.frontend.sync_playwright")
    def test_capture_snapshot(self, mock_playwright, mock_setup):
        # Mock Playwright context manager
        mock_p = MagicMock()
        mock_playwright.return_value.__enter__.return_value = mock_p

        mock_browser = MagicMock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_page = MagicMock()
        mock_browser.new_page.return_value = mock_page

        url = "http://example.com"
        name = "test_snap"

        path = self.verifier.capture_snapshot(url, name)

        # Verify Playwright calls
        mock_p.chromium.launch.assert_called_once()
        mock_page.goto.assert_called_with(url)
        mock_page.screenshot.assert_called_once()

        expected_path = self.verifier.snapshots_dir / "test_snap_current.png"
        self.assertEqual(path, expected_path)

    @patch("shared.frontend.FrontendVerifier.setup", return_value=True)
    @patch("shared.frontend.Image")
    @patch("shared.frontend.ImageChops")
    @patch("shared.frontend.ImageStat")
    def test_verify_match(self, mock_stat, mock_chops, mock_image, mock_setup):
        # Mock paths existence
        with patch("pathlib.Path.exists", return_value=True):
            # Mock Image.open
            mock_img = MagicMock()
            mock_img.convert.return_value = mock_img
            mock_img.size = (100, 100)
            mock_image.open.return_value = mock_img

            # Mock diff
            mock_diff = MagicMock()
            mock_chops.difference.return_value = mock_diff

            # Mock stat (perfect match)
            mock_stat_obj = MagicMock()
            mock_stat_obj.mean = [0, 0, 0] # 0 difference
            mock_stat.Stat.return_value = mock_stat_obj

            result = self.verifier.verify("test_snap")

            self.assertTrue(result["success"])
            self.assertTrue(result["match"])
            self.assertEqual(result["diff_score"], 0.0)

    @patch("shared.frontend.FrontendVerifier.setup", return_value=True)
    @patch("shared.frontend.Image")
    @patch("shared.frontend.ImageChops")
    @patch("shared.frontend.ImageStat")
    def test_verify_mismatch(self, mock_stat, mock_chops, mock_image, mock_setup):
        with patch("pathlib.Path.exists", return_value=True):
            mock_img = MagicMock()
            mock_img.convert.return_value = mock_img
            mock_img.size = (100, 100)
            mock_image.open.return_value = mock_img

            mock_diff = MagicMock()
            mock_chops.difference.return_value = mock_diff

            # Mock stat (mismatch)
            mock_stat_obj = MagicMock()
            mock_stat_obj.mean = [50, 50, 50]
            mock_stat.Stat.return_value = mock_stat_obj

            result = self.verifier.verify("test_snap")

            self.assertTrue(result["success"])
            self.assertFalse(result["match"])
            self.assertGreater(result["diff_score"], 0.0)

    def test_approve_current(self):
        name = "test_approve"
        paths = self.verifier._get_paths(name)

        with patch("pathlib.Path.exists", return_value=True):
            with patch("shutil.copy") as mock_copy:
                success = self.verifier.approve_current(name)
                self.assertTrue(success)
                # Check args
                args, _ = mock_copy.call_args
                self.assertEqual(str(args[0]), str(paths["current"]))
                self.assertEqual(str(args[1]), str(paths["baseline"]))

if __name__ == "__main__":
    unittest.main()
