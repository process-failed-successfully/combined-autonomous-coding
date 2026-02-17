import unittest
from unittest.mock import MagicMock, patch
import sys
import io
import argparse
from shared.grpc_lab import GrpcLabManager, run_grpc_lab_logic

class TestGrpcLabManager(unittest.TestCase):

    def setUp(self):
        self.manager = GrpcLabManager()

    @patch('shutil.which')
    def test_check_grpcurl_installed(self, mock_which):
        mock_which.return_value = '/usr/bin/grpcurl'
        self.assertTrue(self.manager.check_grpcurl())

    @patch('shutil.which')
    def test_check_grpcurl_not_installed(self, mock_which):
        mock_which.return_value = None
        self.assertFalse(self.manager.check_grpcurl())

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_list_services(self, mock_run, mock_which):
        mock_which.return_value = '/usr/bin/grpcurl'

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "grpc.reflection.v1alpha.ServerReflection\nhelloworld.Greeter"
        mock_run.return_value = mock_result

        services = self.manager.list_services("localhost:50051", plaintext=True)

        self.assertEqual(len(services), 2)
        self.assertIn("helloworld.Greeter", services)

        # Verify call args
        mock_run.assert_called_with(
            ['/usr/bin/grpcurl', '-plaintext', 'localhost:50051', 'list'],
            capture_output=True, text=True, check=True
        )

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_list_methods(self, mock_run, mock_which):
        mock_which.return_value = '/usr/bin/grpcurl'

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "helloworld.Greeter.SayHello"
        mock_run.return_value = mock_result

        methods = self.manager.list_methods("localhost:50051", "helloworld.Greeter")

        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0], "helloworld.Greeter.SayHello")

        mock_run.assert_called_with(
            ['/usr/bin/grpcurl', 'localhost:50051', 'list', 'helloworld.Greeter'],
            capture_output=True, text=True, check=True
        )

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_describe(self, mock_run, mock_which):
        mock_which.return_value = '/usr/bin/grpcurl'

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "rpc SayHello ( .helloworld.HelloRequest ) returns ( .helloworld.HelloReply );"
        mock_run.return_value = mock_result

        desc = self.manager.describe("localhost:50051", "helloworld.Greeter.SayHello")

        self.assertIn("rpc SayHello", desc)

        mock_run.assert_called_with(
            ['/usr/bin/grpcurl', 'localhost:50051', 'describe', 'helloworld.Greeter.SayHello'],
            capture_output=True, text=True, check=True
        )

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_call_with_data(self, mock_run, mock_which):
        mock_which.return_value = '/usr/bin/grpcurl'

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{\n  "message": "Hello World"\n}'
        mock_run.return_value = mock_result

        data = {"name": "World"}
        result = self.manager.call("localhost:50051", "helloworld.Greeter.SayHello", data=data)

        self.assertIn("Hello World", result)

        mock_run.assert_called_with(
            ['/usr/bin/grpcurl', '-d', '{"name": "World"}', 'localhost:50051', 'helloworld.Greeter.SayHello'],
            capture_output=True, text=True, check=True
        )

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_call_with_authority(self, mock_run, mock_which):
        mock_which.return_value = '/usr/bin/grpcurl'

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'OK'
        mock_run.return_value = mock_result

        self.manager.call("localhost:50051", "Method", authority="auth.example.com")

        mock_run.assert_called_with(
            ['/usr/bin/grpcurl', '-authority', 'auth.example.com', 'localhost:50051', 'Method'],
            capture_output=True, text=True, check=True
        )

class TestRunGrpcLabLogic(unittest.TestCase):

    @patch('shared.grpc_lab.GrpcLabManager')
    def test_run_logic_missing_tool(self, MockManager):
        # Setup mock to simulate missing tool
        instance = MockManager.return_value
        instance.check_grpcurl.return_value = False

        args = argparse.Namespace(action="list")

        # Capture stderr to suppress output during test
        captured_stderr = io.StringIO()
        sys.stderr = captured_stderr

        with self.assertRaises(SystemExit) as cm:
            run_grpc_lab_logic(args)

        sys.stderr = sys.__stderr__
        self.assertEqual(cm.exception.code, 1)

    @patch('shared.grpc_lab.GrpcLabManager')
    def test_run_logic_list_services(self, MockManager):
        instance = MockManager.return_value
        instance.check_grpcurl.return_value = True
        instance.list_services.return_value = ["ServiceA", "ServiceB"]

        args = argparse.Namespace(
            action="list",
            host="localhost:50051",
            service=None,
            plaintext=False,
            authority=None
        )

        # Capture stdout
        captured_stdout = io.StringIO()
        sys.stdout = captured_stdout

        run_grpc_lab_logic(args)

        sys.stdout = sys.__stdout__
        output = captured_stdout.getvalue()

        self.assertIn("ServiceA", output)
        self.assertIn("ServiceB", output)
        instance.list_services.assert_called_with("localhost:50051", plaintext=False, authority=None)

    @patch('shared.grpc_lab.GrpcLabManager')
    def test_run_logic_call(self, MockManager):
        instance = MockManager.return_value
        instance.check_grpcurl.return_value = True
        instance.call.return_value = "Response"

        args = argparse.Namespace(
            action="call",
            host="localhost:50051",
            method="MethodA",
            data='{"foo":"bar"}',
            plaintext=True,
            authority=None
        )

        captured_stdout = io.StringIO()
        sys.stdout = captured_stdout

        run_grpc_lab_logic(args)

        sys.stdout = sys.__stdout__
        output = captured_stdout.getvalue()

        self.assertIn("Response", output)
        instance.call.assert_called_with("localhost:50051", "MethodA", data='{"foo":"bar"}', plaintext=True, authority=None)

if __name__ == '__main__':
    unittest.main()
