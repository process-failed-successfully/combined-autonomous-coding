import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Input, Button, RichLog, TextArea
from shared.tui_magnet import MagnetLabTab


class TestMagnetLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tab = MagnetLabTab()
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def test_parse_empty(self):
        input_widget = MagicMock(spec=Input)
        input_widget.value = ""

        log_widget = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#magnet-parse-input": return input_widget
            if selector == "#magnet-parse-result": return log_widget
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        event = MagicMock()
        event.button.id = "btn-magnet-parse"
        await self.tab.on_button_pressed(event)

        self.tab.notify.assert_called_with("Please enter a Magnet URI.", severity="error")

    async def test_parse_success(self):
        input_widget = MagicMock(spec=Input)
        input_widget.value = "magnet:?xt=urn:btih:test"

        log_widget = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#magnet-parse-input": return input_widget
            if selector == "#magnet-parse-result": return log_widget
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        event = MagicMock()
        event.button.id = "btn-magnet-parse"
        await self.tab.on_button_pressed(event)

        log_widget.write.assert_called()
        args, _ = log_widget.write.call_args
        self.assertIn("urn:btih:test", args[0])

    async def test_build_success(self):
        xt_input = MagicMock(spec=Input)
        xt_input.value = "urn:btih:test"

        dn_input = MagicMock(spec=Input)
        dn_input.value = "test_name"

        tr_input = MagicMock(spec=TextArea)
        tr_input.text = "http://tracker"

        log_widget = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#magnet-build-xt": return xt_input
            if selector == "#magnet-build-dn": return dn_input
            if selector == "#magnet-build-tr": return tr_input
            if selector == "#magnet-build-result": return log_widget
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        event = MagicMock()
        event.button.id = "btn-magnet-build"
        await self.tab.on_button_pressed(event)

        log_widget.write.assert_called()
        args, _ = log_widget.write.call_args
        self.assertIn("magnet:?", args[0])
        self.assertIn("xt=urn%3Abtih%3Atest", args[0])
        self.assertIn("dn=test_name", args[0])

    @patch('shared.tui_magnet.MagnetLabManager')
    async def test_from_torrent_success(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.from_torrent.return_value = {
            "success": True,
            "uri": "magnet:?xt=urn:btih:test",
            "info_hash": "test",
            "name": "testname",
            "trackers": ["http://test"]
        }

        self.tab.manager = mock_instance

        path_input = MagicMock(spec=Input)
        path_input.value = "/path/to/test.torrent"

        log_widget = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#magnet-torrent-path": return path_input
            if selector == "#magnet-torrent-result": return log_widget
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        event = MagicMock()
        event.button.id = "btn-magnet-torrent"
        await self.tab.on_button_pressed(event)

        self.assertTrue(log_widget.write.called)

if __name__ == "__main__":
    unittest.main()
