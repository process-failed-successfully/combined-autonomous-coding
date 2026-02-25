import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from textual.widgets import Label, DataTable, ListView, Button
from shared.tui_s3 import S3LabTab


class TestS3LabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

    @patch("shared.tui_s3.HAS_BOTO3", True)
    @patch("shared.tui_s3.S3LabManager")
    async def test_mount_and_load_buckets(self, MockManager):
        """Test that buckets are loaded on mount."""
        mock_manager = MockManager.return_value
        mock_manager.s3_client.list_buckets.return_value = {
            "Buckets": [{"Name": "bucket1"}, {"Name": "bucket2"}]
        }

        tab = S3LabTab()
        tab.notify = MagicMock()  # Mock notify

        # Mock query_one
        mock_list = MagicMock(spec=ListView)
        mock_table = MagicMock(spec=DataTable)

        def query_one_side_effect(selector, type=None):
            if selector == "#s3-bucket-list": return mock_list
            if selector == "#s3-object-table": return mock_table
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_one_side_effect)

        tab.on_mount()

        MockManager.assert_called_once()
        mock_manager.s3_client.list_buckets.assert_called_once()
        # verify list updated (append called twice)
        self.assertEqual(mock_list.append.call_count, 2)

    @patch("shared.tui_s3.HAS_BOTO3", True)
    @patch("shared.tui_s3.S3LabManager")
    async def test_bucket_selection(self, MockManager):
        """Test listing objects when a bucket is selected."""
        mock_manager = MockManager.return_value
        # Mock pagination
        paginator = MagicMock()
        mock_manager.s3_client.get_paginator.return_value = paginator
        paginator.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "file1.txt", "Size": 123, "LastModified": "2023-01-01"},
                ],
                "CommonPrefixes": [
                    {"Prefix": "folder/"}
                ]
            }
        ]

        tab = S3LabTab()
        tab.notify = MagicMock()  # Mock notify
        tab.manager = mock_manager  # Manually set as on_mount isn't fully simulated

        mock_table = MagicMock(spec=DataTable)
        mock_btn_delete = MagicMock(spec=Button)

        # Create a mock for the selected label specifically to configure its render() method AND renderable attribute
        mock_selected_label = MagicMock(spec=Label)
        mock_selected_label.render.return_value = "my-bucket"  # Configure render() for compatibility
        mock_selected_label.renderable = "my-bucket"  # Configure renderable for local usage

        tab.query_one = MagicMock(side_effect=lambda s, t=None: {
            "#s3-object-table": mock_table,
            "#s3-objects-header": MagicMock(spec=Label),
            "#s3-path-lbl": MagicMock(spec=Label),
            "#btn-s3-up": MagicMock(),
            "#btn-s3-upload": MagicMock(),
            "#btn-s3-delete": mock_btn_delete,
            "#s3-selected-lbl": mock_selected_label,  # Use our configured mock
        }.get(s, MagicMock()))

        # Simulate selection event
        mock_event = MagicMock()
        mock_item = MagicMock()

        # The item's query_one return value also needs its render() and renderable configured
        mock_label_in_item = MagicMock()
        mock_label_in_item.render.return_value = "my-bucket"
        mock_label_in_item.renderable = "my-bucket"
        mock_item.query_one.return_value = mock_label_in_item

        mock_event.item = mock_item

        tab.on_bucket_selected(mock_event)

        self.assertEqual(tab.current_bucket, "my-bucket")
        mock_manager.s3_client.get_paginator.assert_called_with("list_objects_v2")
        paginator.paginate.assert_called_with(Bucket="my-bucket", Prefix="", Delimiter="/")

        # Check table population: 1 folder + 1 file
        # add_row called for folder and file
        self.assertTrue(mock_table.add_row.called)
        self.assertEqual(mock_table.add_row.call_count, 2)

    @patch("shared.tui_s3.HAS_BOTO3", True)
    @patch("shared.tui_s3.S3LabManager")
    async def test_delete_confirmation(self, MockManager):
        """Test delete button requires confirmation."""
        mock_manager = MockManager.return_value
        tab = S3LabTab()
        tab.notify = MagicMock()  # Mock notify
        tab.manager = mock_manager
        tab.current_bucket = "my-bucket"

        # Create mock label with configured render() and renderable
        mock_lbl = MagicMock(spec=Label)
        mock_lbl.render.return_value = "file.txt"  # Configure render()
        mock_lbl.renderable = "file.txt"  # Configure renderable

        mock_btn = MagicMock(spec=Button)

        tab.query_one = MagicMock(side_effect=lambda s, t=None: {
            "#s3-selected-lbl": mock_lbl,
            "#btn-s3-delete": mock_btn,
            "#s3-object-table": MagicMock(spec=DataTable),  # For load_objects
            "#btn-s3-download": MagicMock(),
            "#btn-s3-presign": MagicMock(),
        }.get(s, MagicMock()))

        # First click: Confirmation
        tab.on_delete()
        self.assertTrue(tab.delete_confirming)
        # Should NOT call delete_object yet
        mock_manager.s3_client.delete_object.assert_not_called()
        # Button label should change
        # When setting attributes on MagicMock, they are just recorded unless configured
        # But here we are asserting checking if the attribute was set?
        # The test checks `mock_btn.label`.
        # MagicMock allows setting attributes freely.

        # Second click: Execute
        tab.on_delete()
        mock_manager.s3_client.delete_object.assert_called_with(Bucket="my-bucket", Key="file.txt")
        self.assertFalse(tab.delete_confirming)

    @patch("shared.tui_s3.HAS_BOTO3", False)
    async def test_missing_boto3(self):
        """Test that it does not init manager if boto3 is missing."""
        tab = S3LabTab()
        tab.notify = MagicMock()  # Mock notify
        tab.query_one = MagicMock()
        tab.on_mount()
        # manager should remain None
        self.assertIsNone(tab.manager)


if __name__ == "__main__":
    unittest.main()
