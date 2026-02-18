import unittest
from unittest.mock import patch, MagicMock
from shared.notify_lab import NotifyLabManager


class TestNotifyLab(unittest.TestCase):
    def setUp(self):
        self.manager = NotifyLabManager(
            slack_url="https://hooks.slack.com/services/test",
            discord_url="https://discord.com/api/webhooks/test"
        )

    @patch("platform.system")
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_send_desktop_linux(self, mock_run, mock_which, mock_system):
        mock_system.return_value = "linux"
        mock_which.return_value = "/usr/bin/notify-send"

        result = self.manager.send_desktop("Title", "Message")

        self.assertTrue(result)
        mock_run.assert_called_with(["/usr/bin/notify-send", "Title", "Message"], check=True)

    @patch("platform.system")
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_send_desktop_macos(self, mock_run, mock_which, mock_system):
        mock_system.return_value = "darwin"
        mock_which.return_value = "/usr/bin/osascript"

        result = self.manager.send_desktop("Title", "Message")

        self.assertTrue(result)
        expected_script = 'display notification "Message" with title "Title"'
        mock_run.assert_called_with(["/usr/bin/osascript", "-e", expected_script], check=True)

    @patch("requests.post")
    def test_send_slack(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        result = self.manager.send_slack("Message")

        self.assertTrue(result)
        mock_post.assert_called_with(
            "https://hooks.slack.com/services/test",
            json={"text": "Message"},
            timeout=5
        )

    @patch("requests.post")
    def test_send_discord(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        result = self.manager.send_discord("Message")

        self.assertTrue(result)
        mock_post.assert_called_with(
            "https://discord.com/api/webhooks/test",
            json={"content": "Message"},
            timeout=5
        )

    @patch("requests.post")
    def test_send_slack_fail(self, mock_post):
        mock_post.side_effect = Exception("Connection error")

        result = self.manager.send_slack("Message")

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
