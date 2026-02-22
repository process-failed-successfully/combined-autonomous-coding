import unittest
from unittest.mock import MagicMock, patch, call
from argparse import Namespace
import sys
import io

from shared.mqtt_lab import run_mqtt_lab_logic

class TestMqttLabCLI(unittest.TestCase):
    def setUp(self):
        # Patch stdout to capture output
        self.capturedOutput = io.StringIO()
        self.patcher_stdout = patch('sys.stdout', new=self.capturedOutput)
        self.patcher_stdout.start()

        # Patch MqttLabManager class
        self.patcher_manager = patch('shared.mqtt_lab.MqttLabManager')
        self.MockManager = self.patcher_manager.start()
        self.mock_manager_instance = self.MockManager.return_value

        # Default behavior: available and connects
        self.mock_manager_instance.is_available.return_value = True
        self.mock_manager_instance.connect.return_value = True

    def tearDown(self):
        self.patcher_stdout.stop()
        self.patcher_manager.stop()

    def test_mqtt_not_available(self):
        self.mock_manager_instance.is_available.return_value = False
        args = Namespace(action="check", host="localhost", port=1883, username=None, password=None)
        result = run_mqtt_lab_logic(args)
        self.assertFalse(result)

    def test_check_connect_success(self):
        args = Namespace(action="check", host="localhost", port=1883, username="user", password="pass")
        result = run_mqtt_lab_logic(args)

        self.assertTrue(result)
        self.mock_manager_instance.connect.assert_called_with("localhost", 1883, username="user", password="pass")
        self.mock_manager_instance.disconnect.assert_called()
        self.assertIn("Successfully connected", self.capturedOutput.getvalue())

    def test_check_connect_fail(self):
        self.mock_manager_instance.connect.return_value = False
        args = Namespace(action="check", host="localhost", port=1883, username=None, password=None)
        result = run_mqtt_lab_logic(args)

        self.assertFalse(result)
        self.assertIn("Failed to connect", self.capturedOutput.getvalue())

    def test_pub_success(self):
        self.mock_manager_instance.publish.return_value = True
        args = Namespace(action="pub", host="localhost", port=1883, username=None, password=None,
                         topic="test/topic", message="payload", qos=1, retain=False)
        result = run_mqtt_lab_logic(args)

        self.assertTrue(result)
        self.mock_manager_instance.connect.assert_called()
        self.mock_manager_instance.publish.assert_called_with("test/topic", "payload", qos=1, retain=False)
        self.mock_manager_instance.disconnect.assert_called()

    def test_sub_loop(self):
        self.mock_manager_instance.subscribe.return_value = True

        # Mock get_messages to return some messages then nothing
        msg1 = {"topic": "t1", "payload": "p1", "timestamp": 1600000000}
        msg2 = {"topic": "t1", "payload": "p2", "timestamp": 1600000001}

        self.mock_manager_instance.get_messages.side_effect = [
            [], # Initial call
            [msg1], # First iteration
            [msg1, msg2] # Second iteration
        ]

        # Mock time.sleep to raise KeyboardInterrupt after a few calls to break the loop
        with patch('time.sleep', side_effect=[None, None, KeyboardInterrupt]):
            args = Namespace(action="sub", host="localhost", port=1883, username=None, password=None,
                             topic="test/topic", qos=0)
            result = run_mqtt_lab_logic(args)

        self.assertTrue(result)
        self.mock_manager_instance.subscribe.assert_called_with("test/topic", qos=0)
        self.assertIn("p1", self.capturedOutput.getvalue())
        self.assertIn("p2", self.capturedOutput.getvalue())
        self.mock_manager_instance.disconnect.assert_called()

if __name__ == '__main__':
    unittest.main()
