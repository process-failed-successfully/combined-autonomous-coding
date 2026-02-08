import pytest
from pathlib import Path
from shared.docs_generator import DocsGenerator

def test_init_docs(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    generator = DocsGenerator(project_dir)
    generator.init_docs()

    assert (project_dir / "docs").exists()
    assert (project_dir / "docs" / "index.md").exists()
    assert (project_dir / "docs" / "conf.yaml").exists()

    # Check content
    index_content = (project_dir / "docs" / "index.md").read_text()
    assert "# Project Documentation" in index_content

def test_convert_markdown(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    generator = DocsGenerator(project_dir)

    md_text = """# Header 1
## Header 2
**bold**
*italic*
- list item
"""
    html = generator._convert_markdown(md_text)

    assert "<h1>Header 1</h1>" in html
    assert "<h2>Header 2</h2>" in html
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html
    assert "<ul>" in html
    assert "<li>list item</li>" in html

def test_extract_docstrings(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    generator = DocsGenerator(project_dir)

    py_file = project_dir / "test.py"
    py_file.write_text('''
def my_func():
    """This is a docstring."""
    pass

class MyClass:
    """Class docstring."""
    pass
''')

    docs = generator._extract_docstrings(py_file)

    assert len(docs) == 2
    assert docs[0]["name"] == "my_func"
    assert docs[0]["doc"] == "This is a docstring."
    assert docs[1]["name"] == "MyClass"
    assert docs[1]["doc"] == "Class docstring."

def test_build_site(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    generator = DocsGenerator(project_dir)

    # Init
    generator.init_docs()

    # Create a dummy python file
    (project_dir / "shared").mkdir()
    (project_dir / "shared" / "utils.py").write_text('''
def util_func():
    """Utility function."""
    pass
''')

    # Build
    success = generator.build_site()

    assert success
    assert (project_dir / "site").exists()
    assert (project_dir / "site" / "index.html").exists()
    assert (project_dir / "site" / "api.html").exists()
    # Check new filename format
    assert (project_dir / "site" / "api" / "shared_utils.html").exists()

    # Check API content
    api_html = (project_dir / "site" / "api" / "shared_utils.html").read_text()
    assert "Utility function." in api_html

def test_build_site_collision(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    generator = DocsGenerator(project_dir)
    generator.init_docs()

    # shared/utils.py
    (project_dir / "shared").mkdir()
    (project_dir / "shared" / "utils.py").write_text('''
def shared_func():
    """Shared func."""
    pass
''')

    # agents/utils.py
    (project_dir / "agents").mkdir()
    (project_dir / "agents" / "utils.py").write_text('''
def agent_func():
    """Agent func."""
    pass
''')

    generator.build_site()

    assert (project_dir / "site" / "api" / "shared_utils.html").exists()
    assert (project_dir / "site" / "api" / "agents_utils.html").exists()

    shared_html = (project_dir / "site" / "api" / "shared_utils.html").read_text()
    agent_html = (project_dir / "site" / "api" / "agents_utils.html").read_text()

    assert "Shared func." in shared_html
    assert "Agent func." in agent_html
