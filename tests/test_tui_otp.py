import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Input, Label, ProgressBar, Button
# Import the class under test
from shared.tui_otp import OtpLabTab


class TestOtpLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch OtpLabManager at the source where it is imported in tui_otp
        self.patcher = patch("shared.tui_otp.OtpLabManager")
        self.MockManager = self.patcher.start()

        # Instantiate the tab
        self.tab = OtpLabTab()
        self.mock_manager = self.MockManager.return_value
        # Ensure the tab uses our mock instance
        self.tab.manager = self.mock_manager

        # Mock Textual UI methods using patch.object to avoid mypy errors
        self.notify_patcher = patch.object(self.tab, 'notify')
        self.mock_notify = self.notify_patcher.start()

        self.query_one_patcher = patch.object(self.tab, 'query_one')
        self.mock_query_one = self.query_one_patcher.start()

        self.set_interval_patcher = patch.object(self.tab, 'set_interval')
        self.mock_set_interval = self.set_interval_patcher.start()

    async def asyncTearDown(self):
        self.patcher.stop()
        self.notify_patcher.stop()
        self.query_one_patcher.stop()
        self.set_interval_patcher.stop()
        if self.tab.timer:
            self.tab.timer.stop()

    def test_generate_secret_success(self):
        # Mock Inputs
        len_input = MagicMock(spec=Input)
        len_input.value = "20"
        res_input = MagicMock(spec=Input)

        def query_side_effect(selector, type=None):
            if selector == "#otp-gen-len":
                return len_input
            if selector == "#otp-gen-result":
                return res_input
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.generate_secret.return_value = "TESTSECRET"

        # Run
        self.tab.generate_secret()

        # Verify
        self.mock_manager.generate_secret.assert_called_with(20)
        self.assertEqual(res_input.value, "TESTSECRET")
        self.mock_notify.assert_called_with("Secret generated.")

    def test_generate_secret_invalid(self):
        # Mock Inputs
        len_input = MagicMock(spec=Input)
        len_input.value = "abc"

        def query_side_effect(selector, type=None):
            if selector == "#otp-gen-len":
                return len_input
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        # Run
        self.tab.generate_secret()

        # Verify
        self.mock_manager.generate_secret.assert_not_called()
        self.mock_notify.assert_called_with("Invalid length.", severity="error")

    def test_verify_code_valid(self):
        # Mock Inputs
        secret_input = MagicMock(spec=Input)
        secret_input.value = "SECRET"
        code_input = MagicMock(spec=Input)
        code_input.value = "123456"
        lbl = MagicMock(spec=Label)

        def query_side_effect(selector, type=None):
            if selector == "#otp-verify-secret":
                return secret_input
            if selector == "#otp-verify-code":
                return code_input
            if selector == "#otp-verify-result":
                return lbl
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        self.mock_manager.verify_totp.return_value = True

        # Run
        self.tab.verify_code()

        # Verify
        self.mock_manager.verify_totp.assert_called_with("SECRET", "123456")
        lbl.update.assert_called_with("[bold green]✅ VALID[/bold green]")

    def test_verify_code_invalid(self):
        # Mock Inputs
        secret_input = MagicMock(spec=Input)
        secret_input.value = "SECRET"
        code_input = MagicMock(spec=Input)
        code_input.value = "000000"
        lbl = MagicMock(spec=Label)

        def query_side_effect(selector, type=None):
            if selector == "#otp-verify-secret":
                return secret_input
            if selector == "#otp-verify-code":
                return code_input
            if selector == "#otp-verify-result":
                return lbl
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        self.mock_manager.verify_totp.return_value = False

        # Run
        self.tab.verify_code()

        # Verify
        lbl.update.assert_called_with("[bold red]❌ INVALID[/bold red]")

    def test_generate_url(self):
        # Mock Inputs
        secret_input = MagicMock(spec=Input)
        secret_input.value = "SECRET"
        label_input = MagicMock(spec=Input)
        label_input.value = "user"
        issuer_input = MagicMock(spec=Input)
        issuer_input.value = "app"
        res_input = MagicMock(spec=Input)

        def query_side_effect(selector, type=None):
            if selector == "#otp-url-secret":
                return secret_input
            if selector == "#otp-url-label":
                return label_input
            if selector == "#otp-url-issuer":
                return issuer_input
            if selector == "#otp-url-result":
                return res_input
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        self.mock_manager.generate_url.return_value = "otpauth://..."

        # Run
        self.tab.generate_url()

        # Verify
        self.mock_manager.generate_url.assert_called_with("SECRET", "user", "app")
        self.assertEqual(res_input.value, "otpauth://...")

    def test_start_monitoring(self):
        secret_input = MagicMock(spec=Input)
        secret_input.value = "SECRET"
        btn_monitor = MagicMock(spec=Button)
        btn_stop = MagicMock(spec=Button)

        def query_side_effect(selector, type=None):
            if selector == "#otp-code-secret":
                return secret_input
            if selector == "#btn-otp-monitor":
                return btn_monitor
            if selector == "#btn-otp-stop":
                return btn_stop
            # Mocks for update_totp called immediately
            if selector == "#otp-code-display":
                return MagicMock()
            if selector == "#otp-progress":
                return MagicMock()
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        # Run
        self.tab.start_monitoring()

        # Verify
        self.assertEqual(btn_monitor.disabled, True)
        self.assertEqual(btn_stop.disabled, False)
        self.assertEqual(secret_input.disabled, True)

        # Verify timer started
        self.mock_set_interval.assert_called_once()
        self.assertIsNotNone(self.tab.timer)

    def test_stop_monitoring(self):
        # Setup mock timer
        mock_timer = MagicMock()
        self.tab.timer = mock_timer

        btn_monitor = MagicMock(spec=Button)
        btn_stop = MagicMock(spec=Button)
        secret_input = MagicMock(spec=Input)
        lbl_display = MagicMock(spec=Label)
        progress = MagicMock(spec=ProgressBar)

        def query_side_effect(selector, type=None):
            if selector == "#btn-otp-monitor":
                return btn_monitor
            if selector == "#btn-otp-stop":
                return btn_stop
            if selector == "#otp-code-secret":
                return secret_input
            if selector == "#otp-code-display":
                return lbl_display
            if selector == "#otp-progress":
                return progress
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        # Run
        self.tab.stop_monitoring()

        # Verify
        mock_timer.stop.assert_called()
        self.assertIsNone(self.tab.timer)
        self.assertEqual(btn_monitor.disabled, False)
        self.assertEqual(btn_stop.disabled, True)
        self.assertEqual(secret_input.disabled, False)
        lbl_display.update.assert_called_with("------")
        progress.update.assert_called_with(total=30, progress=0)

    @patch('time.time')
    def test_update_totp(self, mock_time):
        mock_time.return_value = 100.5  # 30s interval -> 3 intervals + 10.5s remainder

        secret_input = MagicMock(spec=Input)
        secret_input.value = "SECRET"
        lbl_display = MagicMock(spec=Label)
        progress = MagicMock(spec=ProgressBar)

        def query_side_effect(selector, type=None):
            if selector == "#otp-code-secret":
                return secret_input
            if selector == "#otp-code-display":
                return lbl_display
            if selector == "#otp-progress":
                return progress
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        self.mock_manager.generate_totp.return_value = "123456"

        # Run
        self.tab.update_totp()

        # Verify
        self.mock_manager.generate_totp.assert_called_with("SECRET")
        # Remainder is 10.5. Remaining time = 30 - 10.5 = 19.5
        progress.update.assert_called_with(progress=19.5)
        args_list = lbl_display.update.call_args_list
        self.assertIn("123456", args_list[0][0][0])


if __name__ == "__main__":
    unittest.main()
