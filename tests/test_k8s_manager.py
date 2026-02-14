import unittest
from unittest.mock import MagicMock, patch
import json
from shared.k8s_manager import K8sManager

class TestK8sManager(unittest.TestCase):
    def setUp(self):
        self.manager = K8sManager()

    @patch('shutil.which')
    def test_check_kubectl_installed(self, mock_which):
        mock_which.return_value = '/usr/bin/kubectl'
        self.manager = K8sManager()
        self.assertTrue(self.manager.check_kubectl_installed())

        mock_which.return_value = None
        self.manager = K8sManager()
        self.assertFalse(self.manager.check_kubectl_installed())

    @patch('subprocess.run')
    def test_get_version(self, mock_run):
        mock_run.return_value.stdout = json.dumps({"clientVersion": {"gitVersion": "v1.20.0"}})
        self.manager.kubectl_path = "/usr/bin/kubectl"
        version = self.manager.get_version()
        self.assertEqual(version["clientVersion"]["gitVersion"], "v1.20.0")

    @patch('subprocess.run')
    def test_list_pods(self, mock_run):
        mock_run.return_value.stdout = json.dumps({"items": [{"metadata": {"name": "pod1"}}]})
        self.manager.kubectl_path = "/usr/bin/kubectl"
        pods = self.manager.list_pods()
        self.assertEqual(len(pods), 1)
        self.assertEqual(pods[0]["metadata"]["name"], "pod1")

        # Test namespace
        self.manager.list_pods("default")
        args = mock_run.call_args[0][0]
        self.assertIn("-n", args)
        self.assertIn("default", args)

    @patch('subprocess.run')
    def test_list_contexts(self, mock_run):
        mock_data = {
            "contexts": [{"name": "ctx1"}, {"name": "ctx2"}],
            "current-context": "ctx1"
        }
        mock_run.return_value.stdout = json.dumps(mock_data)
        self.manager.kubectl_path = "/usr/bin/kubectl"
        contexts = self.manager.list_contexts()
        self.assertEqual(len(contexts), 2)
        self.assertTrue(contexts[0]["current"])
        self.assertFalse(contexts[1]["current"])

if __name__ == '__main__':
    unittest.main()
