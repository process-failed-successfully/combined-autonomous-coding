import unittest
from pathlib import Path
from unittest.mock import patch
from shared.architecture import check_architecture


class TestArchitecture(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

    @patch("shared.architecture.ImpactAnalyzer")
    def test_check_architecture_clean(self, MockAnalyzer):
        # Setup mock analyzer
        analyzer_instance = MockAnalyzer.return_value
        # dependencies: file -> set of imports
        analyzer_instance.dependencies = {
            "shared/utils.py": {"shared/constants.py"},
            "agents/gemini.py": {"shared/utils.py"}
        }

        rules = [
            {"source": "shared/*", "deny": "agents/*"}
        ]

        violations = check_architecture(self.project_dir, rules)
        self.assertEqual(len(violations), 0)

    @patch("shared.architecture.ImpactAnalyzer")
    def test_check_architecture_violation(self, MockAnalyzer):
        analyzer_instance = MockAnalyzer.return_value
        analyzer_instance.dependencies = {
            "shared/utils.py": {"agents/gemini.py"},  # Violation!
            "agents/gemini.py": {"shared/utils.py"}
        }

        rules = [
            {"source": "shared/*", "deny": "agents/*"}
        ]

        violations = check_architecture(self.project_dir, rules)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["source"], "shared/utils.py")
        self.assertEqual(violations[0]["imported"], "agents/gemini.py")

    @patch("shared.architecture.ImpactAnalyzer")
    def test_check_architecture_multiple_violations(self, MockAnalyzer):
        analyzer_instance = MockAnalyzer.return_value
        analyzer_instance.dependencies = {
            "shared/utils.py": {"agents/gemini.py"},  # Violation
            "ui/tui.py": {"agents/local.py"}  # Violation (ui shouldn't import agents)
        }

        rules = [
            {"source": "shared/*", "deny": "agents/*"},
            {"source": "ui/*", "deny": "agents/*"}
        ]

        violations = check_architecture(self.project_dir, rules)
        self.assertEqual(len(violations), 2)

    @patch("shared.architecture.ImpactAnalyzer")
    def test_check_architecture_wildcards(self, MockAnalyzer):
        analyzer_instance = MockAnalyzer.return_value
        analyzer_instance.dependencies = {
            "shared/sub/utils.py": {"agents/gemini.py"},
        }

        # 'shared/*' matches 'shared/sub/utils.py' because fnmatch matches against the string
        # wait, fnmatch('shared/sub/utils.py', 'shared/*') -> False because * doesn't match / usually in shell but python fnmatch is simpler?
        # Python fnmatch: "The fnmatch() function matches file names strings."
        # It treats / as just a character. * matches everything.

        rules = [
            {"source": "shared/*", "deny": "agents/*"}
        ]

        violations = check_architecture(self.project_dir, rules)
        self.assertEqual(len(violations), 1)


if __name__ == "__main__":
    unittest.main()
