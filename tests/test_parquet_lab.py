import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import tempfile
import shutil

from shared.parquet_lab import ParquetLabManager

class TestParquetLabManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.manager = ParquetLabManager(self.project_dir)

        # Directly inject mocks for dependencies
        self.mock_pd = MagicMock()
        self.mock_pq = MagicMock()

        self.manager.pd = self.mock_pd
        self.manager.pq = self.mock_pq
        self.manager.pa = MagicMock()

        # Bypass _check_deps since we injected manually
        self.manager._check_deps = MagicMock()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('pathlib.Path.exists')
    def test_read_parquet_default(self, mock_exists):
        """Test reading parquet file without limit."""
        mock_exists.return_value = True

        mock_df = MagicMock()
        mock_df.to_string.return_value = "df_string_representation"
        self.mock_pd.read_parquet.return_value = mock_df

        result = self.manager.read_parquet(Path("test.parquet"))

        self.assertEqual(result, "df_string_representation")
        self.mock_pd.read_parquet.assert_called_once_with(Path("test.parquet"))

    @patch('pathlib.Path.exists')
    def test_read_parquet_with_limit(self, mock_exists):
        """Test reading parquet file with limit using iter_batches."""
        mock_exists.return_value = True

        mock_parquet_file = MagicMock()
        self.mock_pq.ParquetFile.return_value = mock_parquet_file

        # Setup iter_batches iterator logic
        mock_batch = MagicMock()
        mock_df = MagicMock()

        # When iter_batches is called, return an iterator that yields one batch
        mock_parquet_file.iter_batches.return_value = iter([mock_batch])

        mock_batch.to_pandas.return_value = mock_df

        mock_head_df = MagicMock()
        mock_df.head.return_value = mock_head_df
        mock_head_df.to_string.return_value = "limited_df_string"

        result = self.manager.read_parquet(Path("test.parquet"), limit=5)

        self.assertEqual(result, "limited_df_string")
        # Note: input arg is cast to str in the implementation
        self.mock_pq.ParquetFile.assert_called_once_with("test.parquet")
        mock_parquet_file.iter_batches.assert_called_once_with(batch_size=5)
        mock_df.head.assert_called_once_with(5)

    @patch('pathlib.Path.exists')
    def test_get_schema(self, mock_exists):
        """Test getting schema info."""
        mock_exists.return_value = True

        mock_file = MagicMock()
        self.mock_pq.ParquetFile.return_value = mock_file

        # Setup metadata
        mock_metadata = MagicMock()
        mock_metadata.num_rows = 100
        mock_metadata.num_columns = 2
        mock_metadata.num_row_groups = 1
        mock_metadata.format_version = "2.6"
        mock_metadata.serialized_size = 1024
        mock_file.metadata = mock_metadata

        # Setup schema
        mock_col1 = MagicMock()
        mock_col1.name = "col1"
        mock_col1.physical_type = "INT64"
        mock_col1.logical_type = "Integer"
        mock_col1.converted_type = "NONE"

        # MagicMock iteration
        mock_schema = MagicMock()
        mock_schema.__len__.return_value = 1
        mock_schema.__getitem__.return_value = mock_col1
        mock_file.schema = mock_schema

        info = self.manager.get_schema(Path("test.parquet"))

        self.assertEqual(info['num_rows'], 100)
        self.assertEqual(len(info['columns']), 1)
        self.assertEqual(info['columns'][0]['name'], "col1")

    @patch('pathlib.Path.exists')
    def test_convert_csv(self, mock_exists):
        """Test conversion to CSV."""
        mock_exists.return_value = True

        mock_df = MagicMock()
        self.mock_pd.read_parquet.return_value = mock_df

        input_path = Path("input.parquet")
        output_path = Path("output.csv")

        self.manager.convert(input_path, output_path, "csv")

        self.mock_pd.read_parquet.assert_called_once_with(input_path)
        mock_df.to_csv.assert_called_once_with(output_path, index=False)

    @patch('pathlib.Path.exists')
    def test_convert_json(self, mock_exists):
        """Test conversion to JSON."""
        mock_exists.return_value = True

        mock_df = MagicMock()
        self.mock_pd.read_parquet.return_value = mock_df

        input_path = Path("input.parquet")
        output_path = Path("output.json")

        self.manager.convert(input_path, output_path, "json")

        self.mock_pd.read_parquet.assert_called_once_with(input_path)
        mock_df.to_json.assert_called_once_with(output_path, orient="records", indent=2)

    def test_file_not_found(self):
        """Test FileNotFoundError is raised."""
        # Revert the bypass for this test to ensure normal logic flow is respected before deps check
        # Actually, file check happens AFTER deps check.
        # But we mock _check_deps anyway.

        with self.assertRaises(FileNotFoundError):
            self.manager.read_parquet(Path("nonexistent.parquet"))

if __name__ == '__main__':
    unittest.main()
