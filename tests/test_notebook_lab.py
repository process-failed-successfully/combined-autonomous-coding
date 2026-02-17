import unittest
import json
import shutil
from pathlib import Path
import tempfile
from shared.notebook_lab import NotebookLabManager

class TestNotebookLab(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = NotebookLabManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_notebook(self, name, cells, metadata=None):
        content = {
            "cells": cells,
            "metadata": metadata or {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                "language_info": {"name": "python", "version": "3.8"}
            },
            "nbformat": 4,
            "nbformat_minor": 5
        }
        path = self.test_dir / name
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(content, f)
        return path

    def test_list_notebooks(self):
        self.create_notebook("nb1.ipynb", [])
        self.create_notebook("nb2.ipynb", [])
        (self.test_dir / "other.txt").write_text("text")

        # Subdirectory
        sub = self.test_dir / "sub"
        sub.mkdir()
        self.create_notebook("sub/nb3.ipynb", [])

        notebooks = self.manager.list_notebooks()
        names = [p.name for p in notebooks]
        self.assertCountEqual(names, ["nb1.ipynb", "nb2.ipynb", "nb3.ipynb"])

    def test_inspect_notebook(self):
        cells = [
            {"cell_type": "markdown", "source": ["# Title"]},
            {"cell_type": "code", "source": ["print('hi')"], "outputs": []}
        ]
        path = self.create_notebook("test.ipynb", cells)

        info = self.manager.inspect_notebook(path)
        self.assertEqual(info['kernel'], "Python 3")
        self.assertEqual(info['language'], "python")
        self.assertEqual(info['cells']['code'], 1)
        self.assertEqual(info['cells']['markdown'], 1)
        self.assertEqual(info['cells']['total'], 2)

    def test_clean_notebook(self):
        cells = [
            {
                "cell_type": "code",
                "source": ["print('hello')"],
                "execution_count": 1,
                "outputs": [{"output_type": "stream", "text": ["hello\n"]}]
            }
        ]
        path = self.create_notebook("dirty.ipynb", cells)

        # Dry run
        changed = self.manager.clean_notebook(path, dry_run=True)
        self.assertTrue(changed)

        # Verify not changed on disk
        with open(path, 'r') as f:
            data = json.load(f)
        self.assertEqual(data['cells'][0]['execution_count'], 1)

        # Actual clean
        changed = self.manager.clean_notebook(path, dry_run=False)
        self.assertTrue(changed)

        with open(path, 'r') as f:
            data = json.load(f)
        self.assertIsNone(data['cells'][0]['execution_count'])
        self.assertEqual(data['cells'][0]['outputs'], [])

    def test_convert_to_script(self):
        cells = [
            {"cell_type": "markdown", "source": ["# Docs"]},
            {"cell_type": "code", "source": ["import os\n", "print(os.getcwd())"]},
            {"cell_type": "code", "source": ["!ls -la", "%pip install pandas"]}
        ]
        path = self.create_notebook("script.ipynb", cells)

        out_path = self.manager.convert_to_script(path)
        self.assertTrue(out_path.exists())

        content = out_path.read_text()
        self.assertIn("# %% [cell 1]", content)
        self.assertIn("import os", content)
        self.assertIn("# !ls -la", content) # Magic commented out
        self.assertIn("# %pip install pandas", content)

    def test_audit_notebook(self):
        # 1. Linear execution check (fail)
        # 2. Large output check (fail)
        # 3. Secret check (fail)

        large_text = "a" * 10005
        cells = [
            {
                "cell_type": "code",
                "source": ["x = 1"],
                "execution_count": 2,
                "outputs": []
            },
            {
                "cell_type": "code",
                "source": ["y = 2"],
                "execution_count": 1, # Out of order
                "outputs": []
            },
            {
                "cell_type": "code",
                "source": ["API_KEY = 'sk-1234567890abcdef12345678'"], # Secret
                "execution_count": 3,
                "outputs": [{"output_type": "stream", "text": [large_text]}] # Large output
            }
        ]
        path = self.create_notebook("audit.ipynb", cells)

        issues = self.manager.audit_notebook(path)
        issue_types = [i['type'] for i in issues]

        self.assertIn("Execution Order", issue_types)
        self.assertIn("Security Risk", issue_types)
        self.assertIn("Large Output", issue_types)

if __name__ == '__main__':
    unittest.main()
