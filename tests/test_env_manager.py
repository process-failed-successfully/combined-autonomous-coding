import unittest
import shutil
import tempfile
from pathlib import Path
from shared.env_manager import EnvManager


class TestEnvManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = EnvManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_init(self):
        success, msg = self.manager.init()
        self.assertTrue(success)
        self.assertTrue((self.test_dir / ".env").exists())
        self.assertTrue((self.test_dir / ".env.example").exists())

        # Test idempotency
        success, msg = self.manager.init()
        self.assertFalse(success)
        self.assertEqual(msg, "Already initialized.")

    def test_gitignore_update(self):
        gitignore = self.test_dir / ".gitignore"
        gitignore.write_text("*.pyc\n")

        self.manager.init()

        content = gitignore.read_text()
        self.assertIn(".env", content)

    def test_check_sync(self):
        self.manager.init()

        env_path = self.test_dir / ".env"
        example_path = self.test_dir / ".env.example"

        env_path.write_text("KEY1=val1\nKEY2=val2")
        example_path.write_text("KEY1=\nKEY3=")

        is_valid, missing_in_env, missing_in_example = self.manager.check()
        self.assertFalse(is_valid)
        self.assertIn("KEY3", missing_in_env)
        self.assertIn("KEY2", missing_in_example)

        # Sync
        self.manager.sync(interactive=False)

        is_valid, missing_in_env, missing_in_example = self.manager.check()
        self.assertTrue(is_valid)
        self.assertEqual(len(missing_in_env), 0)
        self.assertEqual(len(missing_in_example), 0)

        # Check content
        env_content = env_path.read_text()
        self.assertIn("KEY3=", env_content)

        example_content = example_path.read_text()
        self.assertIn("KEY2=", example_content)

    def test_generate_secret(self):
        self.manager.init()

        key = "SECRET_KEY"
        secret = self.manager.generate_secret(key)

        self.assertTrue(len(secret) > 20)

        content = (self.test_dir / ".env").read_text()
        self.assertIn(f"{key}={secret}", content)

        # Update existing
        new_secret = self.manager.generate_secret(key)
        self.assertNotEqual(secret, new_secret)
        content = (self.test_dir / ".env").read_text()
        self.assertIn(f"{key}={new_secret}", content)
        self.assertNotIn(f"{key}={secret}", content)

    def test_check_strict(self):
        self.manager.init()
        (self.test_dir / ".env").write_text("EXTRA=1")
        (self.test_dir / ".env.example").touch()

        is_valid, _, missing_example = self.manager.check()
        self.assertFalse(is_valid)
        self.assertIn("EXTRA", missing_example)

    def test_sync_newline(self):
        self.manager.init()
        # Create env without newline
        with open(self.test_dir / ".env", "w") as f:
            f.write("KEY1=VAL1")

        # Create example with missing key
        with open(self.test_dir / ".env.example", "w") as f:
            f.write("KEY1=\nKEY2=")

        self.manager.sync(interactive=False)

        env_content = (self.test_dir / ".env").read_text()
        self.assertIn("KEY1=VAL1\nKEY2=", env_content)


if __name__ == "__main__":
    unittest.main()
