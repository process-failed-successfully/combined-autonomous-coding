import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from textual.app import App, ComposeResult
from textual.widgets import Input
from shared.tui_kafka import KafkaLabTab
import sys

class KafkaTestApp(App):
    def compose(self) -> ComposeResult:
        yield KafkaLabTab()

class TestKafkaLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_compose_kafka_missing(self):
        # Test when kafka is not available
        with patch("shared.tui_kafka.KafkaLabManager") as MockManager:
            instance = MockManager.return_value
            instance.is_available.return_value = False

            app = KafkaTestApp()
            async with app.run_test() as pilot:
                # Should show error message
                labels = app.query("Label")
                found = False
                for label in labels:
                    if "Kafka Library Not Found" in str(label.render()):
                        found = True
                        break
                self.assertTrue(found)

    async def test_compose_kafka_available(self):
        with patch("shared.tui_kafka.KafkaLabManager") as MockManager:
            instance = MockManager.return_value
            instance.is_available.return_value = True
            instance.list_topics.return_value = ["topic1", "topic2"]

            app = KafkaTestApp()
            async with app.run_test() as pilot:
                # Check sidebar
                sidebar = app.query_one("#kafka-sidebar")
                self.assertIsNotNone(sidebar)

                instance.list_topics.assert_called()

    async def test_create_topic(self):
        with patch("shared.tui_kafka.KafkaLabManager") as MockManager:
            instance = MockManager.return_value
            instance.is_available.return_value = True
            instance.create_topic.return_value = True

            app = KafkaTestApp()
            async with app.run_test() as pilot:
                # Set value directly
                app.query_one("#kafka-new-topic-input", Input).value = "test"

                # Call method directly to avoid UI event race conditions in test environment
                tab = app.query_one(KafkaLabTab)
                await tab.create_topic()

                instance.create_topic.assert_called_with("test")

    async def test_produce_message(self):
        with patch("shared.tui_kafka.KafkaLabManager") as MockManager:
            instance = MockManager.return_value
            instance.is_available.return_value = True
            instance.produce.return_value = True

            app = KafkaTestApp()
            async with app.run_test() as pilot:
                # Select a topic first (simulate selection)
                tab = app.query_one(KafkaLabTab)
                # Manually trigger selection logic
                tab.query_one("#lbl-kafka-target-topic").update("topic1")
                # Also enable the button, as the listener would
                tab.query_one("#btn-kafka-send").disabled = False

                await pilot.click("#kafka-produce-key")
                await pilot.press("k")
                await pilot.click("#kafka-produce-value")
                await pilot.press("v")

                await pilot.click("#btn-kafka-send")
                await pilot.pause()
                await asyncio.sleep(0.1)

                instance.produce.assert_called_with("topic1", "v", "k")

if __name__ == "__main__":
    unittest.main()
