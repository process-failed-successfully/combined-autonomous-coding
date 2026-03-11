import re

with open("tests/test_tui_pattern.py", "r") as f:
    content = f.read()

# Mock ProcessExplorerTab globally for the tests because it creates a background task loop and queries things that are missing when the agent app is mocked in test runs.
import_str = "from shared.tui_pattern import PatternLabTab\n"
patch_str = "from shared.tui_pattern import PatternLabTab\nfrom textual.widgets import Static\n"

content = content.replace(import_str, patch_str)

setup_str = "        start_patch('shared.tui_knowledge_graph.KnowledgeManager')\n"
mock_str = """        start_patch('shared.tui_knowledge_graph.KnowledgeManager')
        start_patch('shared.tui.ProcessExplorerTab', side_effect=lambda *args, **kwargs: Static("Mock ProcessExplorer Tab", id="tab-process-explorer"))
"""
content = content.replace(setup_str, mock_str)

with open("tests/test_tui_pattern.py", "w") as f:
    f.write(content)
