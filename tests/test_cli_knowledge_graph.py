import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import argparse

# Import the function to test
# main.py is a script, so we might need to import it carefully or extract the logic.
# Since run_knowledge is defined in main.py, we can import it.
# However, main.py has global code that runs on import if not guarded (it is guarded with if __name__ == "__main__":).
# But it imports a lot of stuff.

# Let's try importing run_knowledge from main
from main import run_knowledge

class TestCliKnowledgeGraph(unittest.TestCase):

    @patch('shared.knowledge_graph.generate_knowledge_graph')
    @patch('rich.console.Console.print')
    @patch('shared.database.init_db')
    def test_run_knowledge_graph_defaults(self, mock_init_db, mock_print, mock_generate):
        """Test 'knowledge graph' with default arguments."""

        # Mock args
        args = argparse.Namespace(
            action="graph",
            format="html",
            output=None,
            project_dir=Path("/tmp/test_project")
        )

        # Setup mock return
        mock_generate.return_value = "Graph generated successfully"

        # Execute
        with self.assertRaises(SystemExit) as cm:
            run_knowledge(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify
        mock_generate.assert_called_once_with(
            project_dir=Path("/tmp/test_project").resolve(),
            output_format="html",
            output_file=None
        )
        mock_print.assert_any_call("[green]Graph generated successfully[/green]")

    @patch('shared.knowledge_graph.generate_knowledge_graph')
    @patch('rich.console.Console.print')
    @patch('shared.database.init_db')
    def test_run_knowledge_graph_options(self, mock_init_db, mock_print, mock_generate):
        """Test 'knowledge graph' with specific options."""

        args = argparse.Namespace(
            action="graph",
            format="mermaid",
            output="graph.mmd",
            project_dir=Path("/tmp/test_project")
        )

        mock_generate.return_value = "Mermaid saved"

        with self.assertRaises(SystemExit) as cm:
            run_knowledge(args)
        self.assertEqual(cm.exception.code, 0)

        mock_generate.assert_called_once_with(
            project_dir=Path("/tmp/test_project").resolve(),
            output_format="mermaid",
            output_file=Path("graph.mmd").resolve()
        )
        mock_print.assert_any_call("[green]Mermaid saved[/green]")

    @patch('shared.knowledge_graph.generate_knowledge_graph')
    @patch('rich.console.Console.print')
    @patch('shared.database.init_db')
    def test_run_knowledge_graph_error(self, mock_init_db, mock_print, mock_generate):
        """Test 'knowledge graph' handling exceptions."""

        args = argparse.Namespace(
            action="graph",
            format="html",
            output=None,
            project_dir=Path("/tmp/test_project")
        )

        # Simulate error
        mock_generate.side_effect = Exception("Test Error")

        # Execute and expect exit code 1
        with self.assertRaises(SystemExit) as cm:
            run_knowledge(args)

        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_any_call("[red]Error generating graph: Test Error[/red]")

if __name__ == '__main__':
    unittest.main()
