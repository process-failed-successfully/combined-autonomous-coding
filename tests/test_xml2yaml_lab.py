import pytest
from shared.xml2yaml_lab import Xml2YamlManager, run_xml2yaml_lab_logic


class DummyArgs:
    def __init__(self, action=None, input=None, output=None, tui=False):
        self.action = action
        self.input = input
        self.output = output
        self.tui = tui


def test_xml_to_yaml():
    manager = Xml2YamlManager()
    xml_input = "<root><child>value</child></root>"
    expected_yaml = "root:\n  child: value\n"

    result = manager.convert_xml_to_yaml(xml_input)
    assert result == expected_yaml


def test_yaml_to_xml():
    manager = Xml2YamlManager()
    yaml_input = "root:\n  child: value\n"
    # Depending on ElementTree implementation, spacing might vary slightly.
    # But it should contain <root> and <child>value</child>
    result = manager.convert_yaml_to_xml(yaml_input)
    assert "<root>" in result
    assert "<child>value</child>" in result


def test_invalid_xml():
    manager = Xml2YamlManager()
    with pytest.raises(ValueError, match="XML Parse Error"):
        manager.convert_xml_to_yaml("<root><child>value</root>")  # Missing closing tag for child


def test_invalid_yaml():
    manager = Xml2YamlManager()
    with pytest.raises(ValueError, match="YAML Parse Error"):
        manager.convert_yaml_to_xml("root:\n  child: value\n   invalid_indent: true")


def test_cli_logic_xml2yaml(tmp_path, capsys):
    xml_file = tmp_path / "input.xml"
    xml_file.write_text("<root><item>test</item></root>")

    args = DummyArgs(action="xml2yaml", input=str(xml_file))
    success = run_xml2yaml_lab_logic(args)
    assert success is True

    captured = capsys.readouterr()
    assert "root:\n  item: test" in captured.out


def test_cli_logic_yaml2xml(tmp_path, capsys):
    yaml_file = tmp_path / "input.yaml"
    yaml_file.write_text("root:\n  item: test\n")

    args = DummyArgs(action="yaml2xml", input=str(yaml_file))
    success = run_xml2yaml_lab_logic(args)
    assert success is True

    captured = capsys.readouterr()
    assert "<root>" in captured.out
    assert "<item>test</item>" in captured.out


def test_cli_logic_output_file(tmp_path):
    yaml_file = tmp_path / "input.yaml"
    yaml_file.write_text("root:\n  item: test\n")
    out_file = tmp_path / "output.xml"

    args = DummyArgs(action="yaml2xml", input=str(yaml_file), output=str(out_file))
    success = run_xml2yaml_lab_logic(args)
    assert success is True

    assert out_file.exists()
    content = out_file.read_text()
    assert "<root>" in content
    assert "<item>test</item>" in content
