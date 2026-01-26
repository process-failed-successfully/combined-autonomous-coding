import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.html_dashboard import generate_html_dashboard

class TestHtmlDashboard(unittest.TestCase):
    @patch("shared.html_dashboard.get_workflow_stage")
    @patch("shared.html_dashboard.CostCalculator")
    @patch("shared.html_dashboard.SecurityAuditor")
    @patch("shared.html_dashboard.NetworkBuilder")
    @patch("shared.html_dashboard.get_suggestions")
    def test_generate_html_dashboard(self, mock_suggestions, mock_network, mock_security, mock_cost, mock_stage):
        # Setup mocks
        mock_stage.return_value = "IN_PROGRESS"

        # Cost Mock
        mock_cost_instance = mock_cost.return_value
        mock_cost_instance.calculate_total_cost.return_value = {
            "total_cost": 12.34,
            "details": [
                {"model": "gpt-4o", "total_cost": 10.00},
                {"model": "gemini-1.5-pro", "total_cost": 2.34}
            ]
        }

        # Security Mock
        mock_security_instance = mock_security.return_value
        mock_security_instance.run_all.return_value = [
            {"severity": "HIGH", "type": "secret", "description": "AWS Key found", "file": "config.py", "line": 10},
            {"severity": "LOW", "type": "style", "description": "Missing docstring", "file": "utils.py"}
        ]

        # Network Mock
        mock_network_instance = mock_network.return_value
        mock_network_instance.to_json.return_value = {
            "nodes": [{"id": 1, "label": "main.py"}],
            "edges": []
        }

        # Suggestions Mock
        mock_suggestions.return_value = [
            {"reason": "Uncommitted changes", "command": "git status"}
        ]

        # Run
        project_dir = Path("/tmp/test_project")
        # We don't need to create the directory, just pass the path

        html = generate_html_dashboard(project_dir)

        # Verify
        self.assertIn("Project Dashboard - test_project", html)
        self.assertIn("In Progress", html)
        self.assertIn("$12.3400", html)
        self.assertIn("AWS Key found", html)
        self.assertIn("gpt-4o", html)
        self.assertIn("gemini-1.5-pro", html)
        self.assertIn("Uncommitted changes", html)

        # Check for embedded JS data
        self.assertIn('"nodes": [{"id": 1, "label": "main.py"}]', html)

if __name__ == '__main__':
    unittest.main()
