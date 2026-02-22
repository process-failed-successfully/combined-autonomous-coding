import unittest
from unittest.mock import MagicMock, patch
from shared.kafka_lab import KafkaLabManager

class TestKafkaLabManager(unittest.TestCase):
    def setUp(self):
        # We don't instantiate here if we want to mock properly in tests,
        # but the manager init is simple.
        self.manager = KafkaLabManager()

    @patch("shared.kafka_lab.kafka") # Make _check_kafka return True
    @patch("shared.kafka_lab.KafkaConsumer")
    def test_list_topics(self, mock_consumer_cls, mock_kafka):
        mock_consumer = mock_consumer_cls.return_value
        mock_consumer.topics.return_value = {"topic1", "topic2"}

        topics = self.manager.list_topics()
        self.assertEqual(topics, ["topic1", "topic2"])
        mock_consumer.close.assert_called_once()

    @patch("shared.kafka_lab.kafka")
    @patch("shared.kafka_lab.KafkaConsumer")
    def test_describe_topic(self, mock_consumer_cls, mock_kafka):
        mock_consumer = mock_consumer_cls.return_value
        mock_consumer.partitions_for_topic.return_value = {0, 1, 2}

        info = self.manager.describe_topic("test-topic")
        self.assertEqual(info["topic"], "test-topic")
        self.assertEqual(info["count"], 3)
        self.assertEqual(set(info["partitions"]), {0, 1, 2})

    @patch("shared.kafka_lab.kafka")
    @patch("shared.kafka_lab.NewTopic")
    @patch("shared.kafka_lab.KafkaAdminClient")
    def test_create_topic(self, mock_admin_cls, mock_new_topic, mock_kafka):
        mock_admin = mock_admin_cls.return_value

        result = self.manager.create_topic("new-topic")
        self.assertTrue(result)
        mock_admin.create_topics.assert_called_once()
        mock_admin.close.assert_called_once()

    @patch("shared.kafka_lab.kafka")
    @patch("shared.kafka_lab.KafkaProducer")
    def test_produce(self, mock_producer_cls, mock_kafka):
        mock_producer = mock_producer_cls.return_value
        mock_future = MagicMock()
        mock_producer.send.return_value = mock_future

        mock_record_metadata = MagicMock()
        mock_record_metadata.partition = 0
        mock_record_metadata.offset = 10
        mock_future.get.return_value = mock_record_metadata

        result = self.manager.produce("topic", "value", "key")
        self.assertTrue(result)
        mock_producer.send.assert_called_once()
        mock_producer.close.assert_called_once()

    @patch("shared.kafka_lab.kafka")
    @patch("shared.kafka_lab.KafkaConsumer")
    def test_consume_messages(self, mock_consumer_cls, mock_kafka):
        mock_consumer = mock_consumer_cls.return_value

        # Simulate poll returning messages then empty
        msg1 = MagicMock()
        msg1.partition = 0
        msg1.offset = 1
        msg1.key = b"key"
        msg1.value = b"value"
        msg1.timestamp = 12345

        # poll returns Dict[TopicPartition, List[ConsumerRecord]]
        mock_consumer.poll.side_effect = [
            { "tp": [msg1] },
            {}
        ]

        messages = list(self.manager.consume_messages("topic", limit=1))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["value"], b"value")
        self.assertEqual(messages[0]["key"], b"key")

if __name__ == "__main__":
    unittest.main()
