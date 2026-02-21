import pytest
import ast
from shared.ast_lab import ASTLabManager

def test_parse_code_valid():
    manager = ASTLabManager()
    code = "def foo(): pass"
    tree = manager.parse_code(code)
    assert isinstance(tree, ast.Module)
    assert len(tree.body) == 1
    assert isinstance(tree.body[0], ast.FunctionDef)
    assert tree.body[0].name == "foo"

def test_parse_code_invalid():
    manager = ASTLabManager()
    code = "def foo( pass"
    with pytest.raises(ValueError) as exc:
        manager.parse_code(code)
    assert "Syntax Error" in str(exc.value)

def test_node_to_dict():
    manager = ASTLabManager()
    code = "x = 1"
    tree = manager.parse_code(code)
    # tree.body[0] is Assign
    node = tree.body[0]

    data = manager.node_to_dict(node)
    assert data["type"] == "Assign"
    assert "fields" in data
    assert "targets" in data["fields"]
    assert "value" in data["fields"]

    # Check recursion
    value_node = data["fields"]["value"]
    assert value_node["type"] == "Constant"
    # value is a field in Constant
    assert value_node["fields"]["value"] == 1

def test_dump_tree():
    manager = ASTLabManager()
    code = "x=1"
    dump = manager.dump_tree(code)
    assert "Assign" in dump
    assert "Constant" in dump
