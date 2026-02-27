import unittest
import pandas as pd
import tempfile
import os
import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.parquet_lab import ParquetLabManager, run_parquet_lab_logic

class TestParquetLab(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.test_dir.name)
        self.manager = ParquetLabManager(self.project_dir)

        # Create sample data
        self.data = [
            {"id": 1, "name": "Alice", "age": 30, "city": "New York"},
            {"id": 2, "name": "Bob", "age": 25, "city": "Los Angeles"},
            {"id": 3, "name": "Charlie", "age": 35, "city": "Chicago"}
        ]
        self.parquet_path = self.project_dir / "test.parquet"

        # Save sample data using pandas directly to ensure valid input
        df = pd.DataFrame(self.data)
        df.to_parquet(self.parquet_path, index=False)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_read_parquet(self):
        """Test reading a parquet file."""
        result = self.manager.read_parquet(self.parquet_path)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "Alice")
        self.assertEqual(result[1]["age"], 25)

    def test_save_parquet(self):
        """Test saving data to a parquet file."""
        new_path = self.project_dir / "output.parquet"
        self.manager.save_parquet(self.data, new_path)

        self.assertTrue(new_path.exists())
        # Verify content
        result = self.manager.read_parquet(new_path)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[2]["city"], "Chicago")

    def test_get_info(self):
        """Test getting file info."""
        info = self.manager.get_info(self.parquet_path)
        self.assertEqual(info["rows"], 3)
        self.assertEqual(info["columns"], 4)
        self.assertIn("name", info["column_names"])
        self.assertIn("age", info["column_names"])

    def test_get_schema(self):
        """Test getting file schema."""
        schema = self.manager.get_schema(self.parquet_path)
        # Type strings might vary by pandas version/system (e.g. int64 vs int32), just check keys existence
        self.assertIn("id", schema)
        self.assertIn("name", schema)
        self.assertIn("age", schema)
        self.assertIn("city", schema)

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        with self.assertRaises(FileNotFoundError):
            self.manager.read_parquet("nonexistent.parquet")

    def test_cli_convert_to_csv(self):
        """Test the CLI logic for converting parquet to CSV with format inference."""
        output_csv = self.project_dir / "converted.csv"

        args = argparse.Namespace(
            project_dir=self.project_dir,
            action="convert",
            file=str(self.parquet_path),
            output=str(output_csv),
            format="table" # Default format, should trigger inference
        )

        # Capture stdout to prevent cluttering output
        with patch('sys.stdout', new_callable=MagicMock):
            run_parquet_lab_logic(args)

        self.assertTrue(output_csv.exists())
        # Basic check if it's a CSV
        with open(output_csv, 'r') as f:
            header = f.readline().strip()
            self.assertEqual(header, "id,name,age,city")

    def test_cli_convert_to_json(self):
        """Test the CLI logic for converting parquet to JSON with format inference."""
        output_json = self.project_dir / "converted.json"

        args = argparse.Namespace(
            project_dir=self.project_dir,
            action="convert",
            file=str(self.parquet_path),
            output=str(output_json),
            format="table"
        )

        with patch('sys.stdout', new_callable=MagicMock):
            run_parquet_lab_logic(args)

        self.assertTrue(output_json.exists())
        import json
        with open(output_json, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data), 3)
            self.assertEqual(data[0]['name'], 'Alice')

if __name__ == "__main__":
    unittest.main()
