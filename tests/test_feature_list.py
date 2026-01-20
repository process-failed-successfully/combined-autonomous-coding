import unittest
from pathlib import Path
import json
import tempfile
import shutil
from shared.feature_list import load_feature_list, save_feature_list

class TestFeatureList(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.file_path = self.test_dir / "feature_list.json"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_non_existent(self):
        features = load_feature_list(self.file_path)
        self.assertEqual(features, [])

    def test_load_empty(self):
        self.file_path.write_text("")
        features = load_feature_list(self.file_path)
        self.assertEqual(features, [])

    def test_load_invalid_json(self):
        self.file_path.write_text("{invalid")
        features = load_feature_list(self.file_path)
        self.assertEqual(features, [])

    def test_load_list_format(self):
        data = [{"id": "1", "title": "Legacy"}]
        self.file_path.write_text(json.dumps(data))
        features = load_feature_list(self.file_path)
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0]["title"], "Legacy")

    def test_load_dict_format(self):
        data = {"features": [{"id": "2", "title": "New"}]}
        self.file_path.write_text(json.dumps(data))
        features = load_feature_list(self.file_path)
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0]["title"], "New")

    def test_save_and_load(self):
        data = [{"id": "3", "title": "Saved"}]
        save_feature_list(self.file_path, data)

        # Check raw content
        content = json.loads(self.file_path.read_text())
        self.assertTrue(isinstance(content, dict))
        self.assertIn("features", content)

        # Check load
        loaded = load_feature_list(self.file_path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["title"], "Saved")

if __name__ == "__main__":
    unittest.main()
