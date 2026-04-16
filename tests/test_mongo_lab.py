import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.mongo_lab import MongoLabManager  # noqa: E402


class TestMongoLabManager:
    @pytest.fixture
    def mock_mongo(self):
        with patch('shared.mongo_lab.pymongo') as mock_pymongo:
            # Mock the client
            mock_client = MagicMock()
            mock_pymongo.MongoClient.return_value = mock_client

            with patch('shared.mongo_lab.pymongo', mock_pymongo):
                yield mock_client

    def test_connect_success(self, mock_mongo):
        manager = MongoLabManager()
        assert manager.connect() is True
        mock_mongo.admin.command.assert_called_with('ismaster')

    def test_connect_fail(self):
        with patch('shared.mongo_lab.pymongo') as mock_pymongo:
            mock_pymongo.errors.ConnectionFailure = Exception
            mock_pymongo.MongoClient.side_effect = Exception("Connection failed")

            with patch('shared.mongo_lab.pymongo', mock_pymongo):
                manager = MongoLabManager()
                assert manager.connect() is False

    def test_list_dbs(self, mock_mongo):
        manager = MongoLabManager()
        manager.connect()
        mock_mongo.list_database_names.return_value = ["admin", "local", "mydb"]

        dbs = manager.list_dbs()
        assert "mydb" in dbs
        assert len(dbs) == 3

    def test_list_cols(self, mock_mongo):
        manager = MongoLabManager()
        manager.connect()

        mock_db = MagicMock()
        mock_mongo.__getitem__.return_value = mock_db
        mock_db.list_collection_names.return_value = ["users", "posts"]

        cols = manager.list_cols("mydb")
        assert "users" in cols
        assert len(cols) == 2

    def test_find(self, mock_mongo):
        manager = MongoLabManager()
        manager.connect()

        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_cursor = MagicMock()

        mock_mongo.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col
        mock_col.find.return_value = mock_cursor
        mock_cursor.limit.return_value = [{"name": "Alice"}, {"name": "Bob"}]

        docs = manager.find("mydb", "users")
        assert len(docs) == 2
        assert docs[0]["name"] == "Alice"

    def test_insert(self, mock_mongo):
        manager = MongoLabManager()
        manager.connect()

        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_result = MagicMock()
        mock_result.inserted_id = "507f1f77bcf86cd799439011"

        mock_mongo.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col
        mock_col.insert_one.return_value = mock_result

        inserted_id = manager.insert("mydb", "users", {"name": "Charlie"})
        assert inserted_id == "507f1f77bcf86cd799439011"
        mock_col.insert_one.assert_called_with({"name": "Charlie"})

    def test_delete(self, mock_mongo):
        manager = MongoLabManager()
        manager.connect()

        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_result = MagicMock()
        mock_result.deleted_count = 5

        mock_mongo.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col
        mock_col.delete_many.return_value = mock_result

        count = manager.delete("mydb", "users", {"age": {"$gt": 30}})
        assert count == 5
        mock_col.delete_many.assert_called_with({"age": {"$gt": 30}})
