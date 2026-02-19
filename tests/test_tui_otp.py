import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import time

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Input, Label, ProgressBar
from shared.tui_otp import OtpLabTab

class TestOtpLabTab(unittest.TestCase):
    def setUp(self):
        # Patch OtpLabManager
        self.patcher = patch('shared.tui_otp.OtpLabManager')
        self.MockManager = self.patcher.start()
        self.mock_manager_instance = self.MockManager.return_value

        # Instantiate tab
        # We need to mock container init if it does heavy lifting, but Textual Container is lightweight usually.
        # However, calling super().__init__ might require an App context if not careful.
        # But here we just want to test logic methods.

        # We might need to mock set_interval on the instance since it's called in on_mount
        # But we are testing methods directly, not on_mount unless we call it.

        with patch('textual.containers.Container.__init__', return_value=None):
             self.tab = OtpLabTab()
             self.tab.manager = self.mock_manager_instance
             self.tab.current_secret = ""
             self.tab.timer = None

        # Mock methods provided by Textual Widget/Container
        self.tab.query_one = MagicMock()
        self.tab.notify = MagicMock()
        self.tab.set_interval = MagicMock()

        # Mock Widgets
        self.mock_input = MagicMock()
        self.mock_label = MagicMock()
        self.mock_progress = MagicMock()

        # Setup query_one side effect
        def query_one_side_effect(selector, type=None):
            # Specific matches first
            if "display" in selector and "code" in selector:
                return self.mock_label

            if "result" in selector:
                return self.mock_label

            if "progress" in selector:
                return self.mock_progress

            # Catch-all for inputs
            if "input" in selector or "secret" in selector or "issuer" in selector or "label" in selector or "url" in selector or "code" in selector:
                return self.mock_input

            return MagicMock()

        self.tab.query_one.side_effect = query_one_side_effect

    def tearDown(self):
        self.patcher.stop()

    def test_generate_new_secret(self):
        # Setup
        self.mock_manager_instance.generate_secret.return_value = "JBSWY3DPEHPK3PXP"
        self.mock_manager_instance.generate_url.return_value = "otpauth://totp/MyApp:user?secret=..."

        # Mock Input values
        self.mock_input.value = "test_value" # Default for read

        # Execute
        self.tab.generate_new_secret()

        # Verify
        self.assertEqual(self.tab.current_secret, "JBSWY3DPEHPK3PXP")
        self.mock_manager_instance.generate_secret.assert_called()
        self.mock_manager_instance.generate_url.assert_called()
        self.tab.notify.assert_called_with("New secret generated.")

        # Verify UI updates
        # Check if query_one was called for secret input
        self.tab.query_one.assert_any_call("#otp-gen-secret", Input)

    def test_verify_code_valid(self):
        # Setup
        self.mock_input.value = "some_value" # Secret and Code
        self.mock_manager_instance.verify_totp.return_value = True

        # Execute
        self.tab.verify_code()

        # Verify
        self.mock_manager_instance.verify_totp.assert_called()
        self.mock_label.update.assert_called() # Should update result label
        self.assertIn("VALID", self.mock_label.update.call_args[0][0])

    def test_verify_code_invalid(self):
        # Setup
        self.mock_input.value = "some_value"
        self.mock_manager_instance.verify_totp.return_value = False

        # Execute
        self.tab.verify_code()

        # Verify
        self.assertIn("INVALID", self.mock_label.update.call_args[0][0])

    def test_update_timer(self):
        # Setup
        self.tab.current_secret = "SECRET"
        self.mock_manager_instance.generate_totp.return_value = "123456"

        # Mock Label renderable (current value)
        self.mock_label.renderable = "000000"

        # Mock time.time
        with patch('time.time', return_value=100.5):
            self.tab.update_timer()

        # Verify Progress Bar update
        # 100.5 % 30 = 10.5
        # Remaining = 30 - 10.5 = 19.5
        self.mock_progress.update.assert_called_with(total=30, progress=19.5)

        # Verify Code update
        self.mock_manager_instance.generate_totp.assert_called_with("SECRET")
        self.mock_label.update.assert_called_with("123456")

if __name__ == '__main__':
    unittest.main()
