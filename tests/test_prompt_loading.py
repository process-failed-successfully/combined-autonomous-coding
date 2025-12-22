
import unittest
import sys
from pathlib import Path


# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock  # noqa: E402
sys.modules["prometheus_client"] = MagicMock()

from agents.shared import prompts as gemini_prompts  # noqa: E402


class TestPromptLoading(unittest.TestCase):
    """
    Verify that all prompt getter functions can successfully read the prompt files.
    This ensures that the files exist in the expected locations.
    """

    def test_gemini_prompts(self):
        """Test loading all Gemini/Shared prompts."""
        prompts = [
            gemini_prompts.get_initializer_prompt(),
            gemini_prompts.get_coding_prompt(),
            gemini_prompts.get_manager_prompt(),
            gemini_prompts.get_sprint_planner_prompt(),
            gemini_prompts.get_sprint_worker_prompt(),
            gemini_prompts.get_jira_initializer_prompt(),
            gemini_prompts.get_jira_manager_prompt(),
            gemini_prompts.get_jira_worker_prompt(),
        ]
        for p in prompts:
            self.assertTrue(len(p) > 0, "Prompt should not be empty")
            self.assertIsInstance(p, str)


if __name__ == "__main__":
    unittest.main()
