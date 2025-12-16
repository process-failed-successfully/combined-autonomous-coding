import unittest
from unittest.mock import patch, MagicMock
from shared.notifications import NotificationManager
from shared.config import Config


class TestNotificationManager(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock(spec=Config)
        self.config.notification_settings = {}
        self.config.slack_webhook_url = None
        self.config.discord_webhook_url = None
        self.manager = NotificationManager(self.config)

    def test_should_notify_default(self):
        # Default for agent_start is True
        self.assertTrue(self.manager._should_notify("agent_start", "slack"))
        # Default for iteration is False
        self.assertFalse(self.manager._should_notify("iteration", "slack"))

    def test_should_notify_override_all_platforms(self):
        # Config overrides iteration to True for all
        self.config.notification_settings = {"iteration": True}
        self.assertTrue(self.manager._should_notify("iteration", "slack"))
        self.assertTrue(self.manager._should_notify("iteration", "discord"))

    def test_should_notify_override_specific_platform(self):
        # Config overrides iteration: true for slack, false for discord
        self.config.notification_settings = {"iteration": {"slack": True, "discord": False}}
        self.assertTrue(self.manager._should_notify("iteration", "slack"))
        self.assertFalse(self.manager._should_notify("iteration", "discord"))

    @patch("requests.post")
    def test_notify_slack(self, mock_post):
        self.config.slack_webhook_url = "http://slack.test"
        self.config.notification_settings = {"agent_start": True}

        self.manager.notify("agent_start", "Hello")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://slack.test")
        self.assertIn("[AGENT START] Hello", kwargs['json']['text'])

    @patch("requests.post")
    def test_notify_discord(self, mock_post):
        self.config.discord_webhook_url = "http://discord.test"
        self.config.notification_settings = {"agent_start": True}

        self.manager.notify("agent_start", "Hello")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://discord.test")
        self.assertIn("[AGENT START] Hello", kwargs['json']['content'])

    @patch("requests.post")
    def test_notify_both(self, mock_post):
        self.config.slack_webhook_url = "http://slack.test"
        self.config.discord_webhook_url = "http://discord.test"
        self.config.notification_settings = {"agent_start": True}

        self.manager.notify("agent_start", "Hello")

        self.assertEqual(mock_post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
