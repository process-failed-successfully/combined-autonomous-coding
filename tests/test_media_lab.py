import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import json

# Import the module to test
# We need to make sure shared is in path, which it typically is in tests
from shared.media_lab import MediaLabManager, run_media_lab_logic

class TestMediaLabManager(unittest.TestCase):

    def setUp(self):
        # Mock shutil.which to simulate ffmpeg installed
        self.patcher_which = patch("shutil.which")
        self.mock_which = self.patcher_which.start()
        self.mock_which.side_effect = lambda cmd: f"/usr/bin/{cmd}"

        # Mock subprocess.run
        self.patcher_run = patch("subprocess.run")
        self.mock_run = self.patcher_run.start()

        self.manager = MediaLabManager()

    def tearDown(self):
        self.patcher_which.stop()
        self.patcher_run.stop()

    def test_init_checks_deps(self):
        """Test that init checks for binaries."""
        # Reset side effect to return None to test failure
        self.mock_which.side_effect = lambda cmd: None
        # Re-init should fail checks if we call methods
        mgr = MediaLabManager()
        # _check_ffmpeg is called by methods, not init
        # so we test specific method call failure
        with self.assertRaises(SystemExit):
            mgr._check_ffmpeg()

    @patch("pathlib.Path.exists", return_value=True)
    def test_get_info(self, mock_exists):
        """Test get_info calls ffprobe correctly."""
        # Setup mock output
        fake_info = {"format": {"duration": "10.0"}, "streams": []}
        self.mock_run.return_value.stdout = json.dumps(fake_info)
        self.mock_run.return_value.returncode = 0

        info = self.manager.get_info(Path("test.mp4"))

        self.assertEqual(info, fake_info)
        self.mock_run.assert_called_once()
        args = self.mock_run.call_args[0][0]
        self.assertIn("ffprobe", args[0])
        self.assertIn("-print_format", args)
        self.assertIn("json", args)
        self.assertIn("test.mp4", args[-1])

    @patch("pathlib.Path.exists", return_value=True)
    def test_convert(self, mock_exists):
        """Test convert calls ffmpeg correctly."""
        self.manager.convert(Path("input.mov"), Path("output.mp4"))

        self.mock_run.assert_called_once()
        args = self.mock_run.call_args[0][0]
        self.assertIn("ffmpeg", args[0])
        self.assertIn("-i", args)
        self.assertIn("input.mov", args)
        self.assertEqual(args[-1], "output.mp4")

    @patch("pathlib.Path.exists", return_value=True)
    def test_resize(self, mock_exists):
        """Test resize calls ffmpeg with scale filter."""
        self.manager.resize(Path("in.mp4"), Path("out.mp4"), width=640, height=480)

        args = self.mock_run.call_args[0][0]
        self.assertIn("-vf", args)
        self.assertIn("scale=640:480", args)

    @patch("pathlib.Path.exists", return_value=True)
    def test_extract_audio(self, mock_exists):
        """Test extract_audio."""
        self.manager.extract_audio(Path("video.mp4"), Path("audio.mp3"))

        args = self.mock_run.call_args[0][0]
        self.assertIn("-vn", args)
        self.assertIn("libmp3lame", args) # inferred from extension

    @patch("pathlib.Path.exists", return_value=True)
    def test_trim(self, mock_exists):
        """Test trim."""
        self.manager.trim(Path("full.mp4"), Path("cut.mp4"), start="00:00:10", end="00:00:20")

        args = self.mock_run.call_args[0][0]
        self.assertIn("-ss", args)
        self.assertIn("00:00:10", args)
        self.assertIn("-to", args)
        self.assertIn("00:00:20", args)

class TestMediaLabCLI(unittest.TestCase):

    @patch("shared.media_lab.MediaLabManager")
    def test_run_logic_convert(self, MockManager):
        """Test CLI logic wiring."""
        mock_mgr_instance = MockManager.return_value

        args = MagicMock()
        args.action = "convert"
        args.input = "in.mov"
        args.output = "out.mp4"
        args.project_dir = Path(".")

        run_media_lab_logic(args)

        mock_mgr_instance.convert.assert_called_with(Path("in.mov"), Path("out.mp4"))

if __name__ == "__main__":
    unittest.main()
