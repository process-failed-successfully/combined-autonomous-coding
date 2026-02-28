import unittest
from pathlib import Path
from textual.app import App, ComposeResult
from shared.tui_toml import TomlLabTab
from textual.widgets import DirectoryTree, Tree, Input, Button
import tempfile
import os

class TomlApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield TomlLabTab(project_dir=self.project_dir)

class TestTomlLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_toml_lab_tab_rendering(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a sample TOML file
            sample_toml = temp_path / "test.toml"
            sample_toml.write_text('[package]\nname = "test"\nversion = "1.0"\n')

            app = TomlApp(temp_path)
            async with app.run_test() as pilot:
                tab = app.query_one(TomlLabTab)

                # Check initial render
                self.assertIsNotNone(tab.query_one("#toml-file-tree", DirectoryTree))
                self.assertIsNotNone(tab.query_one("#toml-tree", Tree))

                # Simulate loading file
                tab.load_file(sample_toml)
                await pilot.pause()

                self.assertEqual(tab.current_file, sample_toml)
                self.assertEqual(tab.current_data["package"]["name"], "test")

                # Verify tree structure loaded
                tree = tab.query_one("#toml-tree", Tree)
                self.assertGreater(len(tree.root.children), 0)

                # Simulate node selection
                package_node = None
                for child in tree.root.children:
                    if str(child.label).find("package") != -1:
                        package_node = child
                        break
                self.assertIsNotNone(package_node)

                # Select 'package.name' node
                name_node = None
                for child in package_node.children:
                    if str(child.label).find("name") != -1:
                        name_node = child
                        break

                self.assertIsNotNone(name_node)

                tab.on_node_selected(Tree.NodeSelected(name_node))
                await pilot.pause()

                # Check that path and value inputs updated
                path_input = tab.query_one("#toml-path-input", Input)
                value_input = tab.query_one("#toml-value-input", Input)

                self.assertEqual(path_input.value, "package.name")
                self.assertEqual(value_input.value, '"test"')

                # Change value and update
                value_input.value = '"new_test"'
                tab.on_update()
                await pilot.pause()

                self.assertEqual(tab.current_data["package"]["name"], "new_test")

                # Save file
                tab.on_save()
                await pilot.pause()

                saved_content = sample_toml.read_text()
                self.assertIn('name = "new_test"', saved_content)

if __name__ == "__main__":
    unittest.main()
