import unittest
from unittest.mock import patch, MagicMock
from shared.docker_manager import DockerManager
import subprocess
import json

class TestDockerManager(unittest.TestCase):
    def setUp(self):
        self.manager = DockerManager()

    @patch("subprocess.run")
    def test_list_containers(self, mock_run):
        # Mock successful output
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"ID":"123","Image":"test"}\n{"ID":"456","Image":"prod"}'

        containers = self.manager.list_containers()
        self.assertEqual(len(containers), 2)
        self.assertEqual(containers[0]["ID"], "123")
        self.assertEqual(containers[1]["Image"], "prod")

        # Mock empty output
        mock_run.return_value.stdout = ""
        containers = self.manager.list_containers()
        self.assertEqual(len(containers), 0)

        # Mock error
        mock_run.side_effect = subprocess.CalledProcessError(1, ["docker"])
        containers = self.manager.list_containers()
        self.assertEqual(len(containers), 0)

    @patch("subprocess.run")
    def test_list_images(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"ID":"img1","Repository":"repo1"}'

        images = self.manager.list_images()
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["Repository"], "repo1")
        mock_run.assert_called_with(["docker", "images", "--format", "{{json .}}"], check=True, capture_output=True, text=True)

    @patch("subprocess.run")
    def test_start_container(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertTrue(self.manager.start_container("123"))
        mock_run.assert_called_with(["docker", "start", "123"], check=True, capture_output=True)

        mock_run.side_effect = subprocess.CalledProcessError(1, ["docker"])
        self.assertFalse(self.manager.start_container("123"))

    @patch("subprocess.run")
    def test_remove_container(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertTrue(self.manager.remove_container("123", force=True))
        mock_run.assert_called_with(["docker", "rm", "-f", "123"], check=True, capture_output=True)

    @patch("subprocess.run")
    def test_remove_image(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertTrue(self.manager.remove_image("img1", force=False))
        mock_run.assert_called_with(["docker", "rmi", "img1"], check=True, capture_output=True)

    @patch("subprocess.run")
    def test_prune_containers(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertTrue(self.manager.prune_containers())
        mock_run.assert_called_with(["docker", "container", "prune", "-f"], check=True, capture_output=True)

    @patch("subprocess.run")
    def test_prune_images(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertTrue(self.manager.prune_images())
        mock_run.assert_called_with(["docker", "image", "prune", "-f"], check=True, capture_output=True)

    @patch("subprocess.run")
    def test_get_logs(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "log line 1\n"
        mock_run.return_value.stderr = "log line 2\n"

        logs = self.manager.get_logs("123", tail=50)
        self.assertIn("log line 1", logs)
        self.assertIn("log line 2", logs)
        mock_run.assert_called_with(["docker", "logs", "--tail", "50", "123"], check=True, capture_output=True, text=True)

    @patch("subprocess.run")
    def test_inspect_container(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '[{"Id": "123", "State": {"Running": true}}]'

        data = self.manager.inspect_container("123")
        self.assertIsNotNone(data)
        self.assertEqual(data["Id"], "123")
        self.assertTrue(data["State"]["Running"])

    @patch("subprocess.run")
    def test_get_stats(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"Name":"test","CPUPerc":"0.1%"}'

        stats = self.manager.get_stats("123")
        self.assertIsNotNone(stats)
        self.assertEqual(stats["Name"], "test")
        mock_run.assert_called_with(["docker", "stats", "--no-stream", "--format", "{{json .}}", "123"], check=True, capture_output=True, text=True)

if __name__ == "__main__":
    unittest.main()
