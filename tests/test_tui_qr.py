# tests/test_tui_qr.py
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.tui_qr import QrLabTab
from textual.widgets import Input, Select, TextArea, Checkbox

class TestQrLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = QrLabTab(self.project_dir)

    async def test_get_content_text(self):
        # Mock query_one
        def mock_query_one(selector, type_cls=None):
            if selector == "#qr-input-tabs":
                m = MagicMock()
                m.active = "qr-tab-text"
                return m
            if selector == "#qr-text-content":
                m = MagicMock(spec=TextArea)
                m.text = "Hello QR"
                return m
            return MagicMock()

        with patch.object(self.tab, "query_one", side_effect=mock_query_one):
            content = self.tab.get_content()
            self.assertEqual(content, "Hello QR")

    async def test_get_content_wifi(self):
        def mock_query_one(selector, type_cls=None):
            if selector == "#qr-input-tabs":
                m = MagicMock()
                m.active = "qr-tab-wifi"
                return m
            if selector == "#qr-wifi-ssid":
                m = MagicMock(spec=Input)
                m.value = "MyNet"
                return m
            if selector == "#qr-wifi-pass":
                m = MagicMock(spec=Input)
                m.value = "1234"
                return m
            if selector == "#qr-wifi-type":
                m = MagicMock(spec=Select)
                m.value = "WPA"
                return m
            if selector == "#qr-wifi-hidden":
                m = MagicMock(spec=Checkbox)
                m.value = False
                return m
            return MagicMock()

        with patch.object(self.tab, "query_one", side_effect=mock_query_one):
            content = self.tab.get_content()
            # We rely on QRLabManager logic which is already tested, checking basic output
            self.assertIn("WIFI:S:MyNet", content)

    @patch("shared.tui_qr.QRLabManager")
    async def test_generate_preview(self, mock_mgr_cls):
        mock_mgr = mock_mgr_cls.return_value
        mock_mgr.generate_ascii.return_value = "## ASCII ##"

        # Re-initialize tab to use mock manager
        self.tab.manager = mock_mgr

        # Mock get_content
        with patch.object(self.tab, "get_content", return_value="test"):
            # Mock UI elements
            mock_log = MagicMock()

            def mock_query_one(selector, type_cls=None):
                if selector == "#qr-preview-log": return mock_log
                if selector == "#qr-correction":
                    m = MagicMock()
                    m.value = "L"
                    return m
                if selector == "#qr-box-size":
                    m = MagicMock()
                    m.value = "10"
                    return m
                if selector == "#qr-border":
                    m = MagicMock()
                    m.value = "4"
                    return m
                if selector == "#qr-input-tabs":
                    m = MagicMock()
                    m.active = "qr-tab-text"
                    return m
                return MagicMock()

            with patch.object(self.tab, "query_one", side_effect=mock_query_one):
                # We also need to mock self.app or notify since it might be called
                with patch.object(self.tab, "notify") as mock_notify:
                    self.tab.generate_preview()

                    mock_mgr.generate_ascii.assert_called_once()
                    mock_log.clear.assert_called_once()
                    mock_log.write.assert_called_with("## ASCII ##")
                    mock_notify.assert_called_with("Preview generated.")
