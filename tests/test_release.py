import unittest
from pathlib import Path
import tempfile
import json
from shared.release import (
    determine_next_version,
    generate_changelog,
    bump_version_file,
    parse_current_version
)


class TestRelease(unittest.TestCase):

    def test_determine_next_version(self):
        # Initial version
        self.assertEqual(determine_next_version(None, []), "0.1.0")

        # No bump
        commits = [
            {"subject": "docs: update readme", "body": ""}
        ]
        self.assertEqual(determine_next_version("1.0.0", commits), "1.0.0")

        # Patch bump
        commits = [
            {"subject": "fix: bug fix", "body": ""}
        ]
        self.assertEqual(determine_next_version("1.0.0", commits), "1.0.1")

        # Minor bump
        commits = [
            {"subject": "feat: new feature", "body": ""}
        ]
        self.assertEqual(determine_next_version("1.0.0", commits), "1.1.0")

        # Major bump (BREAKING CHANGE in body)
        commits = [
            {"subject": "feat: big change", "body": "BREAKING CHANGE: api removed"}
        ]
        self.assertEqual(determine_next_version("1.0.0", commits), "2.0.0")

        # Major bump (BREAKING CHANGE in subject)
        commits = [
            {"subject": "feat!: big change", "body": "BREAKING CHANGE: api removed"}
        ]
        self.assertEqual(determine_next_version("1.0.0", commits), "2.0.0")

        # Precedence: Major > Minor > Patch
        commits = [
            {"subject": "fix: bug fix", "body": ""},
            {"subject": "feat: new feature", "body": ""},
            {"subject": "chore: cleanup", "body": "BREAKING CHANGE: boom"}
        ]
        self.assertEqual(determine_next_version("1.0.0", commits), "2.0.0")

    def test_generate_changelog(self):
        commits = [
            {"subject": "fix: bug fix", "body": "", "hash": "abcdef1"},
            {"subject": "feat: new feature", "body": "", "hash": "1234567"},
            {"subject": "docs: update readme", "body": "", "hash": "7890abc"}
        ]
        new_version = "1.1.0"
        changelog = generate_changelog(commits, new_version)

        self.assertIn("# v1.1.0", changelog)
        self.assertIn("## Features", changelog)
        self.assertIn("- feat: new feature (1234567)", changelog)
        self.assertIn("## Bug Fixes", changelog)
        self.assertIn("- fix: bug fix (abcdef1)", changelog)
        self.assertIn("## Other Changes", changelog)
        self.assertIn("- docs: update readme (7890abc)", changelog)

    def test_bump_version_file_package_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pkg_json = project_dir / "package.json"
            pkg_json.write_text(json.dumps({"name": "test", "version": "1.0.0"}))

            modified = bump_version_file(project_dir, "1.1.0")

            self.assertIn("package.json", modified)
            content = json.loads(pkg_json.read_text())
            self.assertEqual(content["version"], "1.1.0")

    def test_bump_version_file_pyproject_toml(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pyproject = project_dir / "pyproject.toml"
            pyproject.write_text('[tool.poetry]\nname = "test"\nversion = "1.0.0"\n')

            modified = bump_version_file(project_dir, "1.1.0")

            self.assertIn("pyproject.toml", modified)
            content = pyproject.read_text()
            self.assertIn('version = "1.1.0"', content)

    def test_parse_current_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            pkg_json = project_dir / "package.json"
            pkg_json.write_text(json.dumps({"version": "1.2.3"}))

            version = parse_current_version(project_dir)
            self.assertEqual(version, "1.2.3")


if __name__ == '__main__':
    unittest.main()
