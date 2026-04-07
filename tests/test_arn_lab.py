import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
import sys

from shared.arn_lab import ArnLabManager, run_arn_lab_logic
from main import run_arn_lab

class TestArnLab(unittest.TestCase):
    def setUp(self):
        self.manager = ArnLabManager()

    def test_parse_valid_arn(self):
        result = self.manager.parse("arn:aws:s3:::my_corporate_bucket")
        self.assertTrue(result["success"])
        self.assertEqual(result["partition"], "aws")
        self.assertEqual(result["service"], "s3")
        self.assertIsNone(result["region"])
        self.assertIsNone(result["account_id"])
        self.assertEqual(result["resource"], "my_corporate_bucket")

    def test_parse_valid_arn_with_type(self):
        result = self.manager.parse("arn:aws:iam::123456789012:user/johndoe")
        self.assertTrue(result["success"])
        self.assertEqual(result["partition"], "aws")
        self.assertEqual(result["service"], "iam")
        self.assertIsNone(result["region"])
        self.assertEqual(result["account_id"], "123456789012")
        self.assertEqual(result["resource"], "user/johndoe")
        self.assertEqual(result["resource_type"], "user")
        self.assertEqual(result["resource_id"], "johndoe")

    def test_parse_valid_arn_colon_type(self):
        result = self.manager.parse("arn:aws:lambda:us-east-1:123456789012:function:my-func")
        self.assertTrue(result["success"])
        self.assertEqual(result["region"], "us-east-1")
        self.assertEqual(result["resource_type"], "function")
        self.assertEqual(result["resource_id"], "my-func")

    def test_parse_invalid_arn(self):
        result = self.manager.parse("not-an-arn")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_construct_valid(self):
        result = self.manager.construct(
            service="s3",
            resource="my_bucket"
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["arn"], "arn:aws:s3:::my_bucket")

    def test_construct_valid_complex(self):
        result = self.manager.construct(
            service="dynamodb",
            resource="table/my-table",
            partition="aws-cn",
            region="cn-north-1",
            account_id="123456789012"
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["arn"], "arn:aws-cn:dynamodb:cn-north-1:123456789012:table/my-table")

    def test_construct_missing_args(self):
        result = self.manager.construct(service="", resource="")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch('shared.arn_lab.ArnLabManager.parse')
    def test_cli_parse(self, mock_parse):
        mock_parse.return_value = {"success": True, "partition": "aws", "resource": "x"}
        args = argparse.Namespace(action="parse", arn="arn:aws:x:::x")
        with patch('sys.stdout'):
            with self.assertRaises(SystemExit) as cm:
                run_arn_lab_logic(args)
            self.assertEqual(cm.exception.code, 0)
            mock_parse.assert_called_once_with("arn:aws:x:::x")

    @patch('shared.arn_lab.ArnLabManager.construct')
    def test_cli_construct(self, mock_construct):
        mock_construct.return_value = {"success": True, "arn": "arn:aws:x:::y"}
        args = argparse.Namespace(
            action="construct",
            service="x",
            resource="y",
            partition=None,
            region=None,
            account=None
        )
        with patch('sys.stdout'):
            with self.assertRaises(SystemExit) as cm:
                run_arn_lab_logic(args)
            self.assertEqual(cm.exception.code, 0)
            mock_construct.assert_called_once_with(service="x", resource="y", partition="aws", region="", account_id="")

    def test_cli_parse_missing_arn(self):
        args = argparse.Namespace(action="parse", arn=None)
        with patch('sys.stderr'):
            with self.assertRaises(SystemExit) as cm:
                run_arn_lab_logic(args)
            self.assertEqual(cm.exception.code, 1)

    @patch('main.run_tui')
    def test_cli_tui(self, mock_run_tui):
        args = argparse.Namespace(action="tui")
        with patch('sys.stdout'):
            run_arn_lab(args)
            mock_run_tui.assert_called_once_with(args, start_tab="tab-arn")

if __name__ == '__main__':
    unittest.main()
