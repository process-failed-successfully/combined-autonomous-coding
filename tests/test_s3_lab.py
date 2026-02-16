import unittest
from unittest.mock import MagicMock, patch
import sys
import io
import types
import argparse
import os

# Mock boto3 if not installed
if 'boto3' not in sys.modules:
    mock_boto3 = types.ModuleType('boto3')
    mock_boto3.Session = MagicMock()
    mock_boto3.client = MagicMock()
    mock_boto3.resource = MagicMock()
    sys.modules['boto3'] = mock_boto3

    mock_botocore = types.ModuleType('botocore')
    mock_exceptions = types.ModuleType('botocore.exceptions')
    class ClientError(Exception): pass
    class NoCredentialsError(Exception): pass
    mock_exceptions.ClientError = ClientError
    mock_exceptions.NoCredentialsError = NoCredentialsError
    mock_botocore.exceptions = mock_exceptions
    sys.modules['botocore'] = mock_botocore
    sys.modules['botocore.exceptions'] = mock_exceptions

from shared import s3_lab

# Ensure we are using the mocks and HAS_BOTO3 is True
if 'boto3' in sys.modules:
    s3_lab.boto3 = sys.modules['boto3']
    s3_lab.ClientError = sys.modules['botocore.exceptions'].ClientError
    s3_lab.NoCredentialsError = sys.modules['botocore.exceptions'].NoCredentialsError
    s3_lab.HAS_BOTO3 = True

from shared.s3_lab import S3LabManager, run_s3_lab_logic

class TestS3Lab(unittest.TestCase):
    def setUp(self):
        self.mock_session = MagicMock()
        self.mock_client = MagicMock()
        self.mock_resource = MagicMock()

        # Patch boto3.Session
        self.patcher_session = patch('boto3.Session', return_value=self.mock_session)
        self.mock_cls_session = self.patcher_session.start()

        self.mock_session.client.return_value = self.mock_client
        self.mock_session.resource.return_value = self.mock_resource

        self.manager = S3LabManager()

    def tearDown(self):
        self.patcher_session.stop()

    def test_list_buckets(self):
        self.mock_client.list_buckets.return_value = {
            "Buckets": [
                {"Name": "bucket1", "CreationDate": "2023-01-01"},
                {"Name": "bucket2", "CreationDate": "2023-01-02"}
            ]
        }

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.manager.list_buckets()
            output = mock_stdout.getvalue()
            self.assertIn("bucket1", output)
            self.assertIn("bucket2", output)

    def test_list_objects(self):
        self.mock_client.get_paginator.return_value.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "file1.txt", "Size": 100, "LastModified": "2023-01-01"},
                    {"Key": "folder/file2.txt", "Size": 200, "LastModified": "2023-01-02"}
                ]
            }
        ]

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.manager.list_objects("my-bucket")
            output = mock_stdout.getvalue()
            self.assertIn("file1.txt", output)
            self.assertIn("folder/file2.txt", output)

    def test_create_bucket(self):
        self.manager.create_bucket("new-bucket", "us-west-1")
        self.mock_client.create_bucket.assert_called_with(
            Bucket="new-bucket",
            CreateBucketConfiguration={"LocationConstraint": "us-west-1"}
        )

    def test_delete_bucket(self):
        self.manager.delete_bucket("old-bucket")
        self.mock_client.delete_bucket.assert_called_with(Bucket="old-bucket")

    @patch('os.path.exists', return_value=True)
    def test_upload_file(self, mock_exists):
        self.manager.upload_file("bucket", "key", "local/path")
        self.mock_client.upload_file.assert_called_with("local/path", "bucket", "key")

    def test_download_file(self):
        self.manager.download_file("bucket", "key", "local/path")
        self.mock_client.download_file.assert_called_with("bucket", "key", "local/path")

    def test_delete_object(self):
        self.manager.delete_object("bucket", "key")
        self.mock_client.delete_object.assert_called_with(Bucket="bucket", Key="key")

    def test_presign_url(self):
        self.mock_client.generate_presigned_url.return_value = "https://s3.amazonaws.com/bucket/key?signature"

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.manager.presign_url("bucket", "key")
            output = mock_stdout.getvalue()
            self.assertIn("https://s3.amazonaws.com/bucket/key?signature", output)

    def test_cli_ls(self):
        args = argparse.Namespace(
            action="ls",
            bucket="my-bucket",
            prefix=None,
            endpoint_url=None,
            profile=None,
            region=None
        )
        self.mock_client.get_paginator.return_value.paginate.return_value = [{}] # Empty bucket

        with patch('sys.stdout', new_callable=io.StringIO):
            run_s3_lab_logic(args)

        self.mock_client.get_paginator.assert_called_with("list_objects_v2")

    def test_cli_cp_upload(self):
        args = argparse.Namespace(
            action="cp",
            src="local.txt",
            dest="s3://bucket/remote.txt",
            endpoint_url=None,
            profile=None,
            region=None
        )

        with patch('os.path.exists', return_value=True):
            run_s3_lab_logic(args)

        self.mock_client.upload_file.assert_called_with("local.txt", "bucket", "remote.txt")

    def test_cli_cp_download(self):
        args = argparse.Namespace(
            action="cp",
            src="s3://bucket/remote.txt",
            dest="local.txt",
            endpoint_url=None,
            profile=None,
            region=None
        )

        run_s3_lab_logic(args)

        self.mock_client.download_file.assert_called_with("bucket", "remote.txt", "local.txt")

if __name__ == '__main__':
    unittest.main()
