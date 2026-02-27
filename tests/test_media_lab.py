import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.media_lab import MediaLabManager

class TestMediaLabManager(unittest.TestCase):
    def setUp(self):
        self.mock_shutil_which = patch('shutil.which').start()
        self.mock_subprocess_run = patch('subprocess.run').start()
        self.manager = MediaLabManager()

    def tearDown(self):
        patch.stopall()

    def test_init_checks_dependencies(self):
        # Default behavior: deps exist
        self.mock_shutil_which.return_value = "/usr/bin/ffmpeg"
        mgr = MediaLabManager()
        self.assertEqual(mgr.ffmpeg_bin, "/usr/bin/ffmpeg")

    def test_check_ffmpeg_raises(self):
        self.manager.ffmpeg_bin = None
        with self.assertRaisesRegex(RuntimeError, "ffmpeg not found"):
            self.manager._check_ffmpeg()

    def test_check_ffprobe_raises(self):
        self.manager.ffprobe_bin = None
        with self.assertRaisesRegex(RuntimeError, "ffprobe not found"):
            self.manager._check_ffprobe()

    def test_get_info(self):
        self.manager.ffprobe_bin = "/bin/ffprobe"
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        self.mock_subprocess_run.return_value.stdout = '{"format": {"duration": "10"}}'

        info = self.manager.get_info(mock_path)
        self.assertEqual(info["format"]["duration"], "10")
        self.mock_subprocess_run.assert_called()

    def test_convert(self):
        self.manager.ffmpeg_bin = "/bin/ffmpeg"
        mock_input = MagicMock(spec=Path)
        mock_input.exists.return_value = True
        mock_output = MagicMock(spec=Path)

        self.manager.convert(mock_input, mock_output)

        # Verify ffmpeg called with correct args
        args = self.mock_subprocess_run.call_args[0][0]
        self.assertIn("-i", args)
        self.assertIn(str(mock_output), args)

    def test_resize(self):
        self.manager.ffmpeg_bin = "/bin/ffmpeg"
        mock_input = MagicMock(spec=Path)
        mock_input.exists.return_value = True
        mock_output = MagicMock(spec=Path)

        self.manager.resize(mock_input, mock_output, width=100, height=200)

        args = self.mock_subprocess_run.call_args[0][0]
        self.assertIn("-vf", args)
        self.assertIn("scale=100:200", args)

    def test_extract_audio(self):
        self.manager.ffmpeg_bin = "/bin/ffmpeg"
        mock_input = MagicMock(spec=Path)
        mock_input.exists.return_value = True
        mock_output = MagicMock(spec=Path)
        mock_output.suffix = ".mp3"

        self.manager.extract_audio(mock_input, mock_output)

        args = self.mock_subprocess_run.call_args[0][0]
        self.assertIn("-vn", args)
        self.assertIn("libmp3lame", args)

    def test_trim(self):
        self.manager.ffmpeg_bin = "/bin/ffmpeg"
        mock_input = MagicMock(spec=Path)
        mock_input.exists.return_value = True
        mock_output = MagicMock(spec=Path)

        self.manager.trim(mock_input, mock_output, start="00:00:10", end="00:00:20")

        args = self.mock_subprocess_run.call_args[0][0]
        self.assertIn("-ss", args)
        self.assertIn("00:00:10", args)
        self.assertIn("-to", args)
        self.assertIn("00:00:20", args)

if __name__ == '__main__':
    unittest.main()
