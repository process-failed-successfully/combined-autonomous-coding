import unittest
from unittest.mock import patch, MagicMock
from shared.notifications import NotificationManager
from shared.config import Config
from pathlib import Path

class TestNotificationManager(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock(spec=Config)
        self.config.slack_webhook_url = "https://hooks.slack.com/services/test"
        self.config.discord_webhook_url = "https://discord.com/api/webhooks/test"
        self.config.notification_settings = {
            "iteration": False,
            "manager": True,
            "human_in_loop": True,
            "project_completion": True,
            "error": True, 
        }
        self.notifier = NotificationManager(self.config)

    def test_should_notify_enabled(self):
        """Test that _should_notify returns True when enabled in config."""
        self.assertTrue(self.notifier._should_notify("manager", "slack"))
        self.assertTrue(self.notifier._should_notify("error", "discord"))

    def test_should_notify_disabled(self):
        """Test that _should_notify returns False when disabled in config."""
        self.assertFalse(self.notifier._should_notify("iteration", "slack"))

    def test_should_notify_default(self):
        """Test that _should_notify falls back to defaults if not in config."""
        # Create a config with empty notification settings
        empty_config = MagicMock(spec=Config)
        empty_config.notification_settings = {}
        empty_config.slack_webhook_url = "url"
        notifier = NotificationManager(empty_config)
        
        # Default for manager is True
        self.assertTrue(notifier._should_notify("manager", "slack"))
        # Default for iteration is False
        self.assertFalse(notifier._should_notify("iteration", "slack"))

    @patch("requests.post")
    def test_send_slack_no_webhook(self, mock_post):
        """Test that send_slack does nothing if webhook URL is missing."""
        self.config.slack_webhook_url = None
        self.notifier.send_slack("Test message")
        mock_post.assert_not_called()

    @patch("requests.post")
    def test_send_slack(self, mock_post):
        """Test sending a message to Slack."""
        self.notifier.send_slack("Test message")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], self.config.slack_webhook_url)
        self.assertEqual(kwargs["json"], {"text": "Test message"})

    @patch("requests.post")
    def test_send_discord(self, mock_post):
        """Test sending a message to Discord."""
        self.notifier.send_discord("Test message")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], self.config.discord_webhook_url)
        self.assertEqual(kwargs["json"], {"content": "Test message"})

    @patch("shared.notifications.NotificationManager.send_slack")
    @patch("shared.notifications.NotificationManager.send_discord")
    def test_notify_routing(self, mock_discord, mock_slack):
        """Test that notify calls the correct send methods based on settings."""
        # Enable iteration for this test to verify it sends
        self.config.notification_settings["iteration"] = True
        
        self.notifier.notify("iteration", "Iteration finished")
        
        mock_slack.assert_called_once()
        mock_discord.assert_called_once()

    @patch("shared.notifications.NotificationManager.send_slack")
    @patch("shared.notifications.NotificationManager.send_discord")
    def test_notify_routing_disabled(self, mock_discord, mock_slack):
        """Test that notify does NOT calls send methods if disabled."""
        # Iteration is False by default in our setup
        self.config.notification_settings["iteration"] = False
        
        self.notifier.notify("iteration", "Iteration finished")
        
        mock_slack.assert_not_called()
        mock_discord.assert_not_called()

if __name__ == "__main__":
    unittest.main()
