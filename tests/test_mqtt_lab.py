import unittest
from unittest.mock import MagicMock, patch

from shared.mqtt_lab import MqttLabManager


class TestMqttLabManager(unittest.TestCase):
    def setUp(self):
        # Create a mock for the mqtt module
        self.mock_mqtt_module = MagicMock()
        self.mock_mqtt_module.MQTT_ERR_SUCCESS = 0
        self.mock_mqtt_module.Client.return_value = MagicMock()

        # Patch the 'mqtt' variable in shared.mqtt_lab
        self.patcher = patch("shared.mqtt_lab.mqtt", self.mock_mqtt_module)
        self.mock_mqtt = self.patcher.start()

        # Re-instantiate manager to ensure it picks up any changes if needed
        # (though it uses self.mqtt which is global, so patch applies)
        self.manager = MqttLabManager()

        # Mock connected state
        self.manager.connected = True
        self.mock_client = self.mock_mqtt.Client.return_value
        self.manager.client = self.mock_client

    def tearDown(self):
        self.patcher.stop()

    def test_connect(self):
        self.manager.connected = False
        self.manager.client = None

        mock_instance = self.mock_mqtt.Client.return_value

        def connect_side_effect(host, port, keepalive):
            if mock_instance.on_connect:
                mock_instance.on_connect(mock_instance, None, None, 0)

        mock_instance.connect.side_effect = connect_side_effect

        result = self.manager.connect("test", 1883)
        self.assertTrue(result)
        self.assertTrue(self.manager.connected)
        mock_instance.connect.assert_called_with("test", 1883, 60)

    def test_subscribe(self):
        self.mock_client.subscribe.return_value = (0, 1)  # (result, mid)

        result = self.manager.subscribe("test/topic", 1)

        self.assertTrue(result)
        self.mock_client.subscribe.assert_called_with("test/topic", 1)

    def test_publish(self):
        mock_info = MagicMock()
        mock_info.is_published.return_value = True
        self.mock_client.publish.return_value = mock_info

        result = self.manager.publish("test/topic", "payload", 2, True)

        self.assertTrue(result)
        self.mock_client.publish.assert_called_with("test/topic", "payload", 2, True)
        mock_info.wait_for_publish.assert_called()

    def test_message_handling(self):
        # Create a mock message
        msg = MagicMock()
        msg.topic = "test/topic"
        msg.payload = b"Hello"
        msg.qos = 0
        msg.retain = False

        # Test internal list
        self.manager._on_message(self.mock_client, None, msg)
        messages = self.manager.get_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["payload"], "Hello")

        # Test callback
        callback_mock = MagicMock()
        self.manager.on_message_callback = callback_mock
        self.manager._on_message(self.mock_client, None, msg)

        callback_mock.assert_called()
        args = callback_mock.call_args[0][0]
        self.assertEqual(args["topic"], "test/topic")
        self.assertEqual(args["payload"], "Hello")

    def test_import_error_handling(self):
        # Stop the default patcher first to simulate no paho
        self.patcher.stop()

        with patch("shared.mqtt_lab.mqtt", None):
            mgr = MqttLabManager()
            self.assertFalse(mgr.is_available())
            self.assertFalse(mgr.connect("localhost", 1883))

        # Restart patcher for tearDown (optional but good practice if tearDown relied on it)
        self.patcher.start()


if __name__ == "__main__":
    unittest.main()
