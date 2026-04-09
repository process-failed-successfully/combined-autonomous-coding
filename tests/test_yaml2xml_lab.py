import pytest

from shared.yaml2xml_lab import Yaml2XmlManager

@pytest.fixture
def manager():
    return Yaml2XmlManager()

def test_convert_simple_dict(manager):
    yaml_data = "name: John Doe\nage: 30"
    xml_output = manager.convert(yaml_data)

    assert "<?xml" in xml_output
    assert "<root>" in xml_output
    assert "<name>John Doe</name>" in xml_output
    assert "<age>30</age>" in xml_output

def test_convert_list(manager):
    yaml_data = "fruits:\n  - Apple\n  - Banana"
    xml_output = manager.convert(yaml_data)

    assert "<fruits>" in xml_output
    assert "<item>Apple</item>" in xml_output
    assert "<item>Banana</item>" in xml_output

def test_convert_nested_dict(manager):
    yaml_data = "user:\n  name: Alice\n  address:\n    city: Paris"
    xml_output = manager.convert(yaml_data)

    assert "<user>" in xml_output
    assert "<name>Alice</name>" in xml_output
    assert "<address>" in xml_output
    assert "<city>Paris</city>" in xml_output
    assert "</address>" in xml_output
    assert "</user>" in xml_output

def test_convert_custom_root(manager):
    yaml_data = "status: ok"
    xml_output = manager.convert(yaml_data, root_name="response")

    assert "<response>" in xml_output
    assert "<status>ok</status>" in xml_output

def test_invalid_yaml(manager):
    invalid_yaml = "name: John\n  age: 30" # Bad indentation
    with pytest.raises(ValueError):
        manager.convert(invalid_yaml)

def test_empty_yaml(manager):
    xml_output = manager.convert("")
    assert "<root/>" in xml_output or "<root></root>" in xml_output

def test_list_of_dicts(manager):
    yaml_data = "users:\n  - name: Bob\n  - name: Charlie"
    xml_output = manager.convert(yaml_data)

    # It should have <item><name>Bob</name></item>
    assert "<users>" in xml_output
    assert "<item>" in xml_output
    assert "<name>Bob</name>" in xml_output
    assert "<name>Charlie</name>" in xml_output
