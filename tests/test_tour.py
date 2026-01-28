import unittest
import tempfile
import shutil
import json
from pathlib import Path
from shared.tour import TourManager, Tour, TourStep

class TestTourManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.manager = TourManager(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_create_tour(self):
        success = self.manager.create_tour("test_tour", "Test Title", "Test Description")
        self.assertTrue(success)

        tour_path = self.project_dir / ".tours" / "test_tour.json"
        self.assertTrue(tour_path.exists())

        with open(tour_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["title"], "Test Title")
            self.assertEqual(data["description"], "Test Description")
            self.assertEqual(data["steps"], [])

    def test_create_duplicate_tour(self):
        self.manager.create_tour("test_tour", "Title 1", "Desc 1")
        success = self.manager.create_tour("test_tour", "Title 2", "Desc 2")
        self.assertFalse(success)

    def test_add_step(self):
        self.manager.create_tour("test_tour", "Test Title", "Test Description")

        # Create dummy file
        dummy_file = self.project_dir / "src" / "main.py"
        dummy_file.parent.mkdir(parents=True, exist_ok=True)
        dummy_file.touch()

        success = self.manager.add_step("test_tour", str(dummy_file), 10, "Step Description")
        self.assertTrue(success)

        tour = self.manager.get_tour("test_tour")
        self.assertEqual(len(tour.steps), 1)
        self.assertEqual(tour.steps[0].file, "src/main.py")
        self.assertEqual(tour.steps[0].line, 10)
        self.assertEqual(tour.steps[0].description, "Step Description")

    def test_list_tours(self):
        self.manager.create_tour("tour_a", "Title A", "Desc A")
        self.manager.create_tour("tour_b", "Title B", "Desc B")

        tours = self.manager.list_tours()
        self.assertEqual(tours, ["tour_a", "tour_b"])

    def test_delete_tour(self):
        self.manager.create_tour("test_tour", "Test Title", "Test Description")
        self.assertTrue((self.project_dir / ".tours" / "test_tour.json").exists())

        success = self.manager.delete_tour("test_tour")
        self.assertTrue(success)
        self.assertFalse((self.project_dir / ".tours" / "test_tour.json").exists())

    def test_get_nonexistent_tour(self):
        tour = self.manager.get_tour("non_existent")
        self.assertIsNone(tour)

if __name__ == '__main__':
    unittest.main()
