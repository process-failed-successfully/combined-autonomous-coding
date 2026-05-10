import unittest
from unittest.mock import MagicMock, patch
from shared.amqp_lab import AmqpLabManager

class TestAmqpLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = AmqpLabManager()

    @patch("shared.amqp_lab.pika")
    def test_declare_queue(self, mock_pika):
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        result = self.manager.declare_queue("test_queue")
        self.assertTrue(result)
        mock_channel.queue_declare.assert_called_once_with(queue="test_queue", durable=True)
        mock_connection.close.assert_called_once()

    @patch("shared.amqp_lab.pika")
    def test_publish(self, mock_pika):
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        result = self.manager.publish("test_exchange", "test_key", "test_body")
        self.assertTrue(result)
        mock_channel.basic_publish.assert_called_once()
        kwargs = mock_channel.basic_publish.call_args[1]
        self.assertEqual(kwargs['exchange'], "test_exchange")
        self.assertEqual(kwargs['routing_key'], "test_key")
        self.assertEqual(kwargs['body'], "test_body")
        mock_connection.close.assert_called_once()

    @patch("shared.amqp_lab.pika")
    def test_consume_messages(self, mock_pika):
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        # Simulate two messages, then empty
        mock_method1 = MagicMock(routing_key="rk1", exchange="ex1", delivery_tag=1)
        mock_method2 = MagicMock(routing_key="rk2", exchange="ex2", delivery_tag=2)

        mock_channel.basic_get.side_effect = [
            (mock_method1, MagicMock(), b"body1"),
            (mock_method2, MagicMock(), b"body2"),
            (None, None, None)
        ]

        messages = list(self.manager.consume_messages("test_queue", limit=0))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["body"], "body1")
        self.assertEqual(messages[1]["routing_key"], "rk2")

if __name__ == "__main__":
    unittest.main()
