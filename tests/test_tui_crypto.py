import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

# Handle Textual dependency: use real if available (CI), mock if not (Local)
try:
    import textual
    from textual.widgets import TextArea, Input, Select, RichLog, Button
except ImportError:
    # Create Mocks for sys.modules
    mock_textual = MagicMock()
    sys.modules["textual"] = mock_textual

    mock_app = MagicMock()
    sys.modules["textual.app"] = mock_app

    mock_containers = MagicMock()
    mock_containers.Container = MagicMock
    mock_containers.Horizontal = MagicMock
    mock_containers.Vertical = MagicMock
    sys.modules["textual.containers"] = mock_containers

    mock_widgets = MagicMock()
    mock_button = MagicMock()
    mock_button.Pressed = MagicMock()
    mock_widgets.Button = mock_button
    mock_widgets.Input = MagicMock()
    mock_widgets.Label = MagicMock()
    mock_widgets.RichLog = MagicMock()
    mock_widgets.Select = MagicMock()
    mock_widgets.TabbedContent = MagicMock()
    mock_widgets.TabPane = MagicMock()
    mock_widgets.TextArea = MagicMock()
    sys.modules["textual.widgets"] = mock_widgets

    # Assign local aliases
    TextArea = mock_widgets.TextArea
    Input = mock_widgets.Input
    Select = mock_widgets.Select
    RichLog = mock_widgets.RichLog
    Button = mock_widgets.Button

from shared.tui_crypto import CryptoLabTab

class TestCryptoLabTab(unittest.TestCase):
    def setUp(self):
        with patch('shared.tui_crypto.CryptoLabManager') as MockManager:
            self.tab = CryptoLabTab()
            self.mock_manager = self.tab.manager

        self.tab.query_one = MagicMock()
        self.tab.notify = MagicMock()

        self.mock_text_area = MagicMock()
        self.mock_input = MagicMock()
        self.mock_select = MagicMock()

        def query_one_side_effect(selector, type=None):
            if "input" in selector:
                if "rand-len" in selector: return self.mock_input
                return self.mock_text_area
            if "output" in selector:
                return self.mock_text_area
            if "algo" in selector or "type" in selector:
                return self.mock_select
            if "key" in selector:
                return self.mock_input
            if "len" in selector: # e.g. crypto-rand-len
                return self.mock_input

            return MagicMock()

        self.tab.query_one.side_effect = query_one_side_effect

    def test_do_hash(self):
        self.mock_text_area.text = "secret"
        self.mock_select.value = "sha256"
        self.mock_manager.hash_data.return_value = "hashed_value"

        self.tab.do_hash()

        self.mock_manager.hash_data.assert_called_with("secret", "sha256")
        self.assertEqual(self.mock_text_area.text, "hashed_value")
        self.tab.notify.assert_called_with("Hash calculated.")

    def test_do_gen_key(self):
        self.mock_manager.generate_key.return_value = b"new_key"

        self.tab.do_gen_key()

        self.mock_manager.generate_key.assert_called()
        self.assertEqual(self.mock_input.value, "new_key")
        self.tab.notify.assert_called_with("Key generated.")

    def test_do_encrypt(self):
        self.mock_input.value = "key"
        self.mock_text_area.text = "secret"
        self.mock_manager.encrypt_data.return_value = b"encrypted"

        self.tab.do_encrypt()

        self.mock_manager.encrypt_data.assert_called_with("secret", b"key")
        self.assertEqual(self.mock_text_area.text, "encrypted")
        self.tab.notify.assert_called_with("Encrypted.")

    def test_do_decrypt(self):
        self.mock_input.value = "key"
        self.mock_text_area.text = "encrypted"
        self.mock_manager.decrypt_data.return_value = b"decrypted"

        self.tab.do_decrypt()

        self.mock_manager.decrypt_data.assert_called_with(b"encrypted", b"key")
        self.assertEqual(self.mock_text_area.text, "decrypted")
        self.tab.notify.assert_called_with("Decrypted.")

    def test_do_random(self):
        self.mock_input.value = "32"
        self.mock_select.value = "hex"
        self.mock_manager.generate_random.return_value = "random_val"

        self.tab.do_random()

        self.mock_manager.generate_random.assert_called_with(32, "hex")
        self.assertEqual(self.mock_text_area.text, "random_val")
        self.tab.notify.assert_called_with("Generated.")

if __name__ == '__main__':
    unittest.main()
