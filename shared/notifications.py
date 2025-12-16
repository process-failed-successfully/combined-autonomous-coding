import logging
import requests
from shared.config import Config

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages notifications to external services (Slack, Discord)."""

    def __init__(self, config: Config):
        self.config = config
        # Default settings: Enable Manager, Human, Completion. Disable others.
        self.default_settings = {
            "iteration": False,
            "manager": True,
            "human_in_loop": True,
            "project_completion": True,
            "error": False,
            "agent_start": True,
            "agent_stop": True,
            "sprint_start": False,
            "sprint_task_complete": False,
            "sprint_complete": True,
        }

    def _should_notify(self, event_type: str, platform: str) -> bool:
        """Check if notification is enabled for the event and platform."""
        # 1. Check override in config
        if self.config.notification_settings:
            event_settings = self.config.notification_settings.get(event_type)

            # If explicit boolean (True/False), use it for all platforms
            if isinstance(event_settings, bool):
                return event_settings

            # If it's a dictionary, check specific platform
            if isinstance(event_settings, dict):
                return event_settings.get(platform, False)

        # 2. Fallback to default
        return self.default_settings.get(event_type, False)

    def send_slack(self, message: str) -> None:
        """Send a message to Slack."""
        webhook_url = self.config.slack_webhook_url
        if not webhook_url:
            return

        try:
            payload = {"text": message}
            if self.config.agent_id:
                payload["username"] = self.config.agent_id
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    def send_discord(self, message: str) -> None:
        """Send a message to Discord."""
        webhook_url = self.config.discord_webhook_url
        if not webhook_url:
            return

        try:
            payload = {"content": message}
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

    def notify(self, event_type: str, message: str, **kwargs) -> None:
        """
        Send notification to all enabled platforms.

        Args:
            event_type: One of 'iteration', 'manager', 'human_in_loop', 'project_completion', 'error'
            message: The message content
        """
        prefix = f"[{event_type.upper().replace('_', ' ')}] "
        full_message = f"{prefix}{message}"

        if self._should_notify(event_type, "slack"):
            self.send_slack(full_message)

        if self._should_notify(event_type, "discord"):
            self.send_discord(full_message)
