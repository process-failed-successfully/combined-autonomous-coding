import unittest
from unittest.mock import MagicMock, patch
import argparse
from shared.k8s_lab import run_k8s_lab_logic, K8sLabManager

class TestK8sLab(unittest.TestCase):
    @patch('shared.k8s_lab.K8sLabManager')
    def test_pods_action(self, MockManager):
        instance = MockManager.return_value
        instance.check_kubectl.return_value = True

        args = argparse.Namespace(action="pods", namespace="default")
        run_k8s_lab_logic(args)

        instance.list_pods.assert_called_with("default")

    @patch('shared.k8s_lab.K8sLabManager')
    def test_logs_action(self, MockManager):
        instance = MockManager.return_value
        instance.check_kubectl.return_value = True

        args = argparse.Namespace(action="logs", pod="mypod", namespace="default", tail=50)
        run_k8s_lab_logic(args)

        instance.run_logs.assert_called_with("mypod", "default", 50)

    @patch('shared.k8s_lab.K8sLabManager')
    def test_check_kubectl_fail(self, MockManager):
        instance = MockManager.return_value
        instance.check_kubectl.return_value = False

        args = argparse.Namespace(action="pods")
        with self.assertRaises(SystemExit):
            run_k8s_lab_logic(args)

if __name__ == '__main__':
    unittest.main()
