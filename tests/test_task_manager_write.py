import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import tempfile
import shutil
import json

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from shared.task_manager import TaskManager, Task

class TestTaskManagerWrite(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()
        self.feature_file = self.project_dir / "feature_list.json"

        # Initialize with empty features
        self.feature_file.write_text(json.dumps({"features": []}))

        with patch("shared.task_manager.load_config_from_file") as mock_load:
            mock_load.return_value = {}
            self.manager = TaskManager(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_fetch_features(self):
        # Setup initial state
        data = {
            "features": [
                {"id": "feat_1", "title": "Feature 1", "description": "Desc 1", "passes": True},
                {"id": "feat_2", "title": "Feature 2", "description": "Desc 2", "passes": False}
            ]
        }
        self.feature_file.write_text(json.dumps(data))

        tasks = self.manager.fetch_features()
        self.assertEqual(len(tasks), 2)

        t1 = next(t for t in tasks if t.id == "feat_1")
        self.assertEqual(t1.source, "feature")
        self.assertEqual(t1.status, "Done")

        t2 = next(t for t in tasks if t.id == "feat_2")
        self.assertEqual(t2.status, "Pending")

    def test_add_feature(self):
        self.manager.add_feature("New Feature", "Description")

        content = json.loads(self.feature_file.read_text())
        features = content["features"]
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0]["title"], "New Feature")
        self.assertEqual(features[0]["description"], "Description")
        self.assertEqual(features[0]["passes"], False)
        self.assertTrue(features[0]["id"]) # Should generate an ID

    def test_update_feature_status(self):
        data = {
            "features": [
                {"id": "feat_1", "title": "Feature 1", "description": "Desc 1", "passes": False}
            ]
        }
        self.feature_file.write_text(json.dumps(data))

        # Mark as Done
        success = self.manager.update_feature_status("feat_1", "Done")
        self.assertTrue(success)

        content = json.loads(self.feature_file.read_text())
        self.assertTrue(content["features"][0]["passes"])

        # Mark as Pending
        self.manager.update_feature_status("feat_1", "Pending")
        content = json.loads(self.feature_file.read_text())
        self.assertFalse(content["features"][0]["passes"])

    def test_delete_feature(self):
        data = {
            "features": [
                {"id": "feat_1", "title": "Feature 1", "description": "Desc 1", "passes": False},
                {"id": "feat_2", "title": "Feature 2", "description": "Desc 2", "passes": True}
            ]
        }
        self.feature_file.write_text(json.dumps(data))

        success = self.manager.delete_feature("feat_1")
        self.assertTrue(success)

        content = json.loads(self.feature_file.read_text())
        self.assertEqual(len(content["features"]), 1)
        self.assertEqual(content["features"][0]["id"], "feat_2")

    def test_update_missing_feature(self):
        success = self.manager.update_feature_status("missing", "Done")
        self.assertFalse(success)

    def test_delete_missing_feature(self):
        success = self.manager.delete_feature("missing")
        self.assertFalse(success)

if __name__ == "__main__":
    unittest.main()
