import unittest
from unittest.mock import MagicMock, patch
import sys
import io
import types
import argparse

# Mock kafka if not installed
if 'kafka' not in sys.modules:
    mock_kafka = types.ModuleType('kafka')
    mock_kafka.KafkaConsumer = MagicMock()
    mock_kafka.KafkaProducer = MagicMock()
    mock_kafka.KafkaAdminClient = MagicMock()
    mock_kafka.admin = types.ModuleType('kafka.admin')
    mock_kafka.admin.NewTopic = MagicMock()
    mock_kafka.errors = types.ModuleType('kafka.errors')
    class KafkaError(Exception): pass
    mock_kafka.errors.KafkaError = KafkaError
    sys.modules['kafka'] = mock_kafka
    sys.modules['kafka.admin'] = mock_kafka.admin
    sys.modules['kafka.errors'] = mock_kafka.errors

from shared import kafka_lab
# Patch if necessary to force using our mock
if kafka_lab.kafka is None:
    kafka_lab.kafka = sys.modules['kafka']
    kafka_lab.KafkaConsumer = sys.modules['kafka'].KafkaConsumer
    kafka_lab.KafkaProducer = sys.modules['kafka'].KafkaProducer
    kafka_lab.KafkaAdminClient = sys.modules['kafka'].KafkaAdminClient
    kafka_lab.NewTopic = sys.modules['kafka'].admin.NewTopic
    kafka_lab.KafkaError = sys.modules['kafka'].errors.KafkaError

from shared.kafka_lab import KafkaLabManager, run_kafka_lab_logic

class TestKafkaLab(unittest.TestCase):
    def setUp(self):
        # We need to patch the classes inside shared.kafka_lab where they are imported
        # But we already injected them into the module namespace via the check above if missing.
        # If they were present, we need to patch them.

        self.mock_consumer = MagicMock()
        self.mock_producer = MagicMock()
        self.mock_admin = MagicMock()

        self.patcher_consumer = patch('shared.kafka_lab.KafkaConsumer', return_value=self.mock_consumer)
        self.patcher_producer = patch('shared.kafka_lab.KafkaProducer', return_value=self.mock_producer)
        self.patcher_admin = patch('shared.kafka_lab.KafkaAdminClient', return_value=self.mock_admin)

        self.mock_cls_consumer = self.patcher_consumer.start()
        self.mock_cls_producer = self.patcher_producer.start()
        self.mock_cls_admin = self.patcher_admin.start()

        self.manager = KafkaLabManager()

    def tearDown(self):
        self.patcher_consumer.stop()
        self.patcher_producer.stop()
        self.patcher_admin.stop()

    def test_list_topics(self):
        self.mock_consumer.topics.return_value = {"topic1", "topic2"}
        topics = self.manager.list_topics()
        self.assertEqual(topics, ["topic1", "topic2"])
        self.mock_cls_consumer.assert_called()
        self.mock_consumer.close.assert_called()

    def test_create_topic(self):
        self.assertTrue(self.manager.create_topic("new-topic"))
        self.mock_cls_admin.assert_called()
        self.mock_admin.create_topics.assert_called()
        self.mock_admin.close.assert_called()

    def test_produce(self):
        future = MagicMock()
        future.get.return_value = MagicMock(partition=0, offset=1)
        self.mock_producer.send.return_value = future

        self.assertTrue(self.manager.produce("topic", "message"))
        self.mock_cls_producer.assert_called()
        self.mock_producer.send.assert_called()
        self.mock_producer.close.assert_called()

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_consume(self, mock_stdout):
        # Mock message iterator
        msg = MagicMock()
        msg.topic = "topic"
        msg.partition = 0
        msg.offset = 0
        msg.key = None
        msg.value = "test-message"

        self.mock_consumer.__iter__.return_value = [msg]

        self.manager.consume("topic")
        self.assertIn("test-message", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_list(self, mock_stdout):
        args = argparse.Namespace(action="list", bootstrap="localhost:9092")
        self.mock_consumer.topics.return_value = {"topic1"}

        try:
            run_kafka_lab_logic(args)
        except SystemExit:
            self.fail("run_kafka_lab_logic raised SystemExit unexpectedly!")

        self.assertIn("topic1", mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
