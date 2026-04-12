import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.mongo_lab import MongoLabManager  # noqa: E402


class TestMongoLabManager:
    @pytest.fixture
    def mock_pymongo(self):
        with patch('shared.mongo_lab.pymongo') as mock_pymongo_module:
            with patch('shared.mongo_lab.ObjectId') as mock_object_id:
                mock_client = MagicMock()
                mock_pymongo_module.MongoClient.return_value = mock_client
                mock_object_id.return_value = "mocked_object_id"
                yield mock_client

    def test_connect_success(self, mock_pymongo):
        manager = MongoLabManager()
        assert manager.connect() is True
        mock_pymongo.admin.command.assert_called_once_with('ping')

    def test_connect_fail(self):
        with patch('shared.mongo_lab.pymongo') as mock_pymongo_module:
            mock_pymongo_module.MongoClient.side_effect = Exception("Connection failed")
            manager = MongoLabManager()
            assert manager.connect() is False

    def test_list_dbs(self, mock_pymongo):
        manager = MongoLabManager()
        manager.connect()
        mock_pymongo.list_database_names.return_value = ["db1", "db2"]
        assert manager.list_dbs() == ["db1", "db2"]

    def test_list_cols(self, mock_pymongo):
        manager = MongoLabManager()
        manager.connect()
        mock_db = MagicMock()
        mock_pymongo.__getitem__.return_value = mock_db
        mock_db.list_collection_names.return_value = ["col1", "col2"]

        cols = manager.list_cols("mydb")
        assert cols == ["col1", "col2"]
        mock_pymongo.__getitem__.assert_called_with("mydb")

    def test_find(self, mock_pymongo):
        manager = MongoLabManager()
        manager.connect()
        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_cursor = MagicMock()

        mock_pymongo.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col
        mock_col.find.return_value = mock_cursor
        mock_cursor.limit.return_value = [{"a": 1}, {"b": 2}]

        docs = manager.find("mydb", "mycol", {"a": 1})
        assert docs == [{"a": 1}, {"b": 2}]
        mock_col.find.assert_called_with({"a": 1})
        mock_cursor.limit.assert_called_with(100)

    def test_insert(self, mock_pymongo):
        manager = MongoLabManager()
        manager.connect()
        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_result = MagicMock()
        mock_result.inserted_id = "12345"

        mock_pymongo.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col
        mock_col.insert_one.return_value = mock_result

        doc_id = manager.insert("mydb", "mycol", {"a": 1})
        assert doc_id == "12345"
        mock_col.insert_one.assert_called_with({"a": 1})

    def test_delete(self, mock_pymongo):
        manager = MongoLabManager()
        manager.connect()
        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_result = MagicMock()
        mock_result.deleted_count = 1

        mock_pymongo.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col
        mock_col.delete_one.return_value = mock_result

        success = manager.delete("mydb", "mycol", "12345")
        assert success is True
        mock_col.delete_one.assert_called_with({"_id": "mocked_object_id"})
