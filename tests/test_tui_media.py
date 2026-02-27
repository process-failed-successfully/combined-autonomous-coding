import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys

# Mock textual app for widget testing context
from textual.app import App
from shared.tui_media import MediaLabTab

class TestMediaLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_shutil_which = patch('shutil.which').start()
        self.mock_shutil_which.return_value = "/bin/ffmpeg"

        # Patch MediaLabManager to avoid actual calls
        self.mock_manager_cls = patch('shared.tui_media.MediaLabManager').start()
        self.mock_manager = self.mock_manager_cls.return_value

    async def asyncTearDown(self):
        patch.stopall()

    async def test_mount_checks_ffmpeg(self):
        self.mock_shutil_which.return_value = None

        class TestApp(App):
            def compose(self):
                yield MediaLabTab(Path("."))

        app = TestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(MediaLabTab)
            self.assertTrue(tab.disabled)

    async def test_file_selection_updates_info(self):
        class TestApp(App):
            def compose(self):
                yield MediaLabTab(Path("."))

        app = TestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(MediaLabTab)

            # Mock get_info return
            self.mock_manager.get_info.return_value = {
                "format": {"duration": "120", "size": "1048576"},
                "streams": [{"codec_type": "video", "codec_name": "h264"}]
            }

            # Simulate file selection
            mock_path = Path("test.mp4")
            # We bypass the directory tree event and call load_file_info directly
            tab.selected_file = mock_path
            tab.load_file_info(mock_path)

            # Verify manager called
            self.mock_manager.get_info.assert_called_with(mock_path)

            # Verify buttons enabled
            tab.enable_buttons(True)
            self.assertFalse(tab.query_one("#btn-media-convert").disabled)

    async def test_run_convert(self):
        class TestApp(App):
            def compose(self):
                yield MediaLabTab(Path("."))

        app = TestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(MediaLabTab)
            tab.selected_file = Path("test.mp4")

            # Set input
            tab.query_one("#media-convert-output").value = "out.mp4"

            # Mock async run task
            tab._run_task = AsyncMock()

            await tab.run_convert()

            tab._run_task.assert_called()
            args = tab._run_task.call_args
            self.assertEqual(args[0][0], self.mock_manager.convert)

    async def test_run_resize(self):
        class TestApp(App):
            def compose(self):
                yield MediaLabTab(Path("."))

        app = TestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(MediaLabTab)
            tab.selected_file = Path("test.mp4")

            # Set inputs
            tab.query_one("#media-resize-output").value = "resized.mp4"
            tab.query_one("#media-resize-width").value = "100"
            tab.query_one("#media-resize-height").value = "200"

            # Mock async run task
            tab._run_task = AsyncMock()

            await tab.run_resize()

            tab._run_task.assert_called()
            args = tab._run_task.call_args
            self.assertEqual(args[0][0], self.mock_manager.resize)
            # Check kwargs
            self.assertEqual(args[1]['width'], 100)
            self.assertEqual(args[1]['height'], 200)

    async def test_run_trim(self):
        class TestApp(App):
            def compose(self):
                yield MediaLabTab(Path("."))

        app = TestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(MediaLabTab)
            tab.selected_file = Path("test.mp4")

            # Set inputs
            tab.query_one("#media-trim-output").value = "trimmed.mp4"
            tab.query_one("#media-trim-start").value = "00:00:10"
            tab.query_one("#media-trim-end").value = "00:00:20"

            # Mock async run task
            tab._run_task = AsyncMock()

            await tab.run_trim()

            tab._run_task.assert_called()
            args = tab._run_task.call_args
            self.assertEqual(args[0][0], self.mock_manager.trim)
            self.assertEqual(args[1]['start'], "00:00:10")
            self.assertEqual(args[1]['end'], "00:00:20")

    async def test_run_audio(self):
        class TestApp(App):
            def compose(self):
                yield MediaLabTab(Path("."))

        app = TestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(MediaLabTab)
            tab.selected_file = Path("test.mp4")

            # Set inputs
            tab.query_one("#media-audio-output").value = "audio.mp3"

            # Mock async run task
            tab._run_task = AsyncMock()

            await tab.run_audio()

            tab._run_task.assert_called()
            args = tab._run_task.call_args
            self.assertEqual(args[0][0], self.mock_manager.extract_audio)

if __name__ == '__main__':
    unittest.main()
