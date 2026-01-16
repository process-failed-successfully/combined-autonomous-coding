import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
import os

from shared.git import clone_repo

class TestGitSecurity(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_repo = Path(self.test_dir) / "dummy_source"
        self.setup_dummy_repo(self.source_repo)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def setup_dummy_repo(self, path: Path):
        path.mkdir(parents=True)
        subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.DEVNULL)
        # Add a file
        (path / "README.md").write_text("dummy")
        subprocess.run(["git", "add", "."], cwd=path, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=path, check=True, stdout=subprocess.DEVNULL)

    def test_clone_repo_argument_injection(self):
        """
        Test that clone_repo is not vulnerable to argument injection.
        We pass '--bare' as the URL. If injected, it would create a bare repo in the current directory.
        With the fix, it should try to clone a repo named '--bare' and fail.
        """
        # We need to run this from a clean directory to check for artifact creation
        # But clone_repo uses subprocess.run without explicit cwd (so it inherits CWD)
        # We should change CWD to a temp dir for this test to avoid polluting repo

        original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        try:
            # Attempt to exploit argument injection
            # If vulnerable: executes `git clone --bare source_repo` (clones source_repo to source_repo.git in CWD)
            # If secure: executes `git clone -- --bare source_repo` (tries to clone repo named '--bare' into source_repo dir)

            # Note: clone_repo(url, dest_path)
            # url="--bare"
            # dest_path=self.source_repo

            success = clone_repo("--bare", self.source_repo)

            # Secure behavior: clone fails because repo '--bare' does not exist
            self.assertFalse(success, "clone_repo should fail when URL starts with dash")

            # Check for artifact
            artifact = Path("dummy_source.git")
            self.assertFalse(artifact.exists(), "clone_repo allowed argument injection (bare repo created)")

        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    unittest.main()
