import pytest
from shared.xml2toml_lab import Xml2TomlManager


def test_xml2toml_valid():
    manager = Xml2TomlManager()
    xml_input = """<?xml version="1.0"?>
<data>
    <item>1</item>
    <item>2</item>
    <name>Test</name>
</data>
"""
    result = manager.convert_xml_to_toml(xml_input)
    assert "Test" in result


def test_toml2xml_valid():
    manager = Xml2TomlManager()
    toml_input = """[data]
name = "Test"
"""
    result = manager.convert_toml_to_xml(toml_input)
    assert "<name>Test</name>" in result


def test_xml2toml_invalid():
    manager = Xml2TomlManager()
    with pytest.raises(ValueError):
        manager.convert_xml_to_toml("<invalid")


def test_toml2xml_invalid():
    manager = Xml2TomlManager()
    with pytest.raises(ValueError):
        manager.convert_toml_to_xml("invalid = ")


def test_run_xml2toml_lab_logic(monkeypatch, capsys):
    from shared.xml2toml_lab import run_xml2toml_lab_logic
    import argparse

    # Test valid xml2toml
    args = argparse.Namespace(action="xml2toml", input="<data></data>", output=None)
    assert run_xml2toml_lab_logic(args) is True

    # Test valid toml2xml
    args = argparse.Namespace(action="toml2xml", input="[data]", output=None)
    assert run_xml2toml_lab_logic(args) is True

    # Test invalid action
    args = argparse.Namespace(action="invalid", input="<data></data>", output=None)
    assert run_xml2toml_lab_logic(args) is False

    # Test invalid input
    args = argparse.Namespace(action="xml2toml", input="<invalid", output=None)
    assert run_xml2toml_lab_logic(args) is False

    # Test file output
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(delete=False) as f:
        pass

    try:
        args = argparse.Namespace(action="xml2toml", input="<data></data>", output=f.name)
        assert run_xml2toml_lab_logic(args) is True
        with open(f.name, "r") as tmp_f:
            assert "data =" in tmp_f.read()
    finally:
        os.remove(f.name)

    args = argparse.Namespace(action="toml2xml", input="data = 1", output=None)
    assert run_xml2toml_lab_logic(args) is True

    # Test valid lists and deeper structures
    manager = Xml2TomlManager()

    # XML to TOML with attributes and list
    xml_input = """<root>
        <items attr="val">
            <item>1</item>
            <item>2</item>
        </items>
    </root>"""
    toml_out = manager.convert_xml_to_toml(xml_input)
    assert 'attr = "val"' in toml_out

    # TOML to XML with list
    toml_input = """
    items = [1, 2, 3]
    """
    xml_out = manager.convert_toml_to_xml(toml_input)
    assert "<item>1</item>" in xml_out

    # TOML to XML with dict list
    toml_input = """
    [[items]]
    val = 1
    [[items]]
    val = 2
    """
    xml_out = manager.convert_toml_to_xml(toml_input)
    assert "<items>" in xml_out
    assert "<val>1</val>" in xml_out
