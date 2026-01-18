import pytest
from pathlib import Path
from shared.dependencies import DependencyAnalyzer

@pytest.fixture
def temp_project(tmp_path):
    """Creates a temporary project directory with dummy dependency files."""
    # requirements.txt
    (tmp_path / "requirements.txt").write_text(
        "flask==2.0.1\nrequests>=2.25.1\n# comment\nnumpy\n"
    )

    # package.json
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "^17.0.2"}, "devDependencies": {"jest": "^27.0.0"}}'
    )

    # pyproject.toml
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "test-project"
dependencies = [
    "django>=3.2",
    "gunicorn"
]

[tool.poetry.dependencies]
python = "^3.9"
fastapi = "^0.68.0"
        """
    )

    return tmp_path

def test_scan_python(temp_project):
    analyzer = DependencyAnalyzer(temp_project)
    result = analyzer.scan()

    python_deps = result["python"]
    assert len(python_deps) >= 2 # requirements.txt and pyproject.toml

    # Check requirements.txt parsing
    req_file = next(d for d in python_deps if d["source"] == "requirements.txt")
    deps = req_file["dependencies"]
    assert {"name": "flask", "version": "==2.0.1"} in deps
    assert {"name": "requests", "version": ">=2.25.1"} in deps
    assert {"name": "numpy", "version": ""} in deps

    # Check pyproject.toml parsing
    toml_file = next(d for d in python_deps if d["source"] == "pyproject.toml")
    toml_deps = toml_file["dependencies"]

    # Check poetry deps
    assert {"name": "fastapi", "version": "^0.68.0"} in toml_deps

    # Note: Our basic regex parser for [project.dependencies] might miss the list format
    # if strictly checking for 'name = version'.
    # Let's verify what it actually caught based on the implementation.
    # The implementation supports `dependencies = [` line skipping,
    # and then looks for strings.
    assert {"name": "django", "version": ">=3.2"} in toml_deps
    assert {"name": "gunicorn", "version": ""} in toml_deps

def test_scan_node(temp_project):
    analyzer = DependencyAnalyzer(temp_project)
    result = analyzer.scan()

    node_deps = result["node"]
    assert len(node_deps) == 1

    pkg_file = node_deps[0]
    assert pkg_file["source"] == "package.json"
    deps = pkg_file["dependencies"]

    assert {"name": "react", "version": "^17.0.2", "type": "prod"} in deps
    assert {"name": "jest", "version": "^27.0.0", "type": "dev"} in deps

def test_generate_tree(temp_project):
    analyzer = DependencyAnalyzer(temp_project)
    data = analyzer.scan()
    tree = analyzer.generate_tree(data)

    assert "📦 Python" in tree
    assert "flask ==2.0.1" in tree
    assert "📦 Node" in tree
    assert "react ^17.0.2 (prod)" in tree

def test_generate_mermaid(temp_project):
    analyzer = DependencyAnalyzer(temp_project)
    data = analyzer.scan()
    mermaid = analyzer.generate_mermaid(data)

    assert "graph TD" in mermaid
    assert "root --> lang_python[Python]" in mermaid
    assert "root --> lang_node[Node]" in mermaid
    assert "--> dep_node_0_react" in mermaid
