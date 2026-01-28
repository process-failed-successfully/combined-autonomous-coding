import shutil
import tempfile
from pathlib import Path
import unittest
import json
from shared.tour import TourManager, Tour, TourStep

class TestTourManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.manager = TourManager(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_create_tour(self):
        tour_path = self.manager.create_tour("my-tour")
        self.assertTrue(tour_path.exists())
        self.assertEqual(tour_path.name, "my-tour.json")

        content = json.loads(tour_path.read_text())
        self.assertEqual(content["title"], "my-tour")
        self.assertEqual(content["steps"], [])

    def test_create_tour_duplicate(self):
        self.manager.create_tour("test")
        with self.assertRaises(FileExistsError):
            self.manager.create_tour("test")

    def test_add_step(self):
        self.manager.create_tour("walkthrough")

        # Create a dummy file to point to
        dummy_file = self.project_dir / "src/main.py"
        dummy_file.parent.mkdir(parents=True)
        dummy_file.touch()

        self.manager.add_step("walkthrough", str(dummy_file), 10, "Intro")

        tour = self.manager.get_tour("walkthrough")
        self.assertEqual(len(tour.steps), 1)
        self.assertEqual(tour.steps[0].file, "src/main.py")
        self.assertEqual(tour.steps[0].line, 10)
        self.assertEqual(tour.steps[0].description, "Intro")

    def test_list_tours(self):
        self.manager.create_tour("alpha")
        self.manager.create_tour("beta")

        tours = self.manager.list_tours()
        self.assertEqual(tours, ["alpha", "beta"])

    def test_delete_tour(self):
        self.manager.create_tour("temp")
        self.assertTrue(self.manager.delete_tour("temp"))
        self.assertFalse(self.manager.delete_tour("temp")) # Already deleted

    def test_get_tour_not_found(self):
        self.assertIsNone(self.manager.get_tour("missing"))

if __name__ == '__main__':
    unittest.main()
